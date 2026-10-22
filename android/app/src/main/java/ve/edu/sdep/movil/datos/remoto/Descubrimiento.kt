package ve.edu.sdep.movil.datos.remoto

import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.Inet4Address
import java.net.InetAddress
import java.net.NetworkInterface
import java.nio.ByteBuffer
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.abs
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

/**
 * Encuentra solo el nodo central de escritorio en la red local y se da de alta
 * como puesto. El usuario no escribe ninguna dirección, equipo ni token.
 *
 * El camino tiene dos canales, en este orden:
 *
 * 1. **Difusión UDP** (puerto 8766) — el nodo responde con su puerto HTTP. Es
 *    inmediato y funciona aunque el servidor esté en otro segmento del mismo
 *    dominio de difusión.
 * 2. **Sondeo de la subred** — para redes donde la difusión está bloqueada.
 *    Se recorren las direcciones cercanas de cada interfaz IPv4, empezando por
 *    las que suelen usar los equipos (`.1`, `.100`, `.10`, `.2`, `.254`) y las
 *    más próximas a la propia. Los candidatos se prueban en lotes de 64, así
 *    que una red /24 se descarta en pocos segundos.
 *
 * Antes de emparejarse, la respuesta se confirma con `GET /api/v1/ping`: un
 * servicio cualquiera que ocupe el puerto no puede hacerse pasar por el nodo.
 */
@Singleton
class Descubrimiento @Inject constructor(
    private val json: Json,
) {

    /** Resultado de descubrir y darse de alta: los tres datos de la vinculación */
    data class Vinculo(
        val url: String,
        val equipo: String,
        val token: String,
    )

    /**
     * Cliente de sondas con tiempos cortos: el sondeo toca cientos de hosts,
     * casi todos muertos. El cliente general espera 15 s por conexión, lo que
     * haría imposible recorrer una subred.
     */
    private val clienteSonda: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(350, TimeUnit.MILLISECONDS)
        .readTimeout(900, TimeUnit.MILLISECONDS)
        .callTimeout(1_200, TimeUnit.MILLISECONDS)
        .retryOnConnectionFailure(false)
        .build()

    /** Cliente normal para el alta (una sola petición ya contra un host vivo) */
    private val clienteAlta: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(3, TimeUnit.SECONDS)
        .readTimeout(8, TimeUnit.SECONDS)
        .callTimeout(12, TimeUnit.SECONDS)
        .build()

    /**
     * Busca el nodo y devuelve la vinculación lista para guardar.
     *
     * @param urlPreferida dirección ya conocida (de una vinculación anterior).
     *        Se prueba primero para tolerar que el servidor haya cambiado de
     *        puerto sin repetir el escaneo completo.
     * @return el vínculo, o null si no se encontró ningún nodo (red aislada,
     *         el escritorio apagado, o el emparejamiento cerrado allí).
     */
    suspend fun descubrir(urlPreferida: String? = null): Vinculo? = withContext(Dispatchers.IO) {
        val probadas = LinkedHashSet<String>()

        if (!urlPreferida.isNullOrBlank()) {
            val base = normalizar(urlPreferida)
            probadas.add(base)
            // Si el nodo responde pero rechaza el alta (emparejamiento
            // cerrado), se sigue buscando: puede haber otro nodo en la red y
            // no conviene quedarse con el primero que conteste.
            if (esNodoCentral(base)) vincular(base)?.let { return@withContext it }
        }

        for (url in buscarPorDifusion()) {
            if (!probadas.add(url)) continue
            if (esNodoCentral(url)) vincular(url)?.let { return@withContext it }
        }

        val nodo = buscarNodo(candidatosLocales()) ?: return@withContext null
        vincular(nodo)
    }

    /** Solo comprueba si una dirección conocida sigue siendo el nodo central */
    suspend fun verificar(url: String): Boolean = withContext(Dispatchers.IO) {
        esNodoCentral(normalizar(url))
    }

    private fun vincular(url: String): Vinculo? {
        val alta = solicitarAlta(url) ?: return null
        return Vinculo(url = url, equipo = alta.dispositivoId, token = alta.token)
    }

    // ------------------------------------------------------------------
    // Difusión UDP
    // ------------------------------------------------------------------

    /**
     * Pregunta por difusión y devuelve las URLs anunciadas.
     *
     * La respuesta incluye el puerto HTTP real del nodo; la IP se toma del
     * datagrama, no del contenido, para que el teléfono use la interfaz por la
     * que realmente llegó la respuesta (un equipo con varias tarjetas puede
     * anunciar una IP que no sea alcanzable desde el WiFi).
     */
    private fun buscarPorDifusion(): List<String> {
        val encontrados = LinkedHashSet<String>()
        val destinos = mutableSetOf<InetAddress>()
        try {
            destinos.add(InetAddress.getByName("255.255.255.255"))
            for (interfaz in NetworkInterface.getNetworkInterfaces() ?: return emptyList()) {
                if (!interfaz.isUp || interfaz.isLoopback) continue
                for (direccion in interfaz.interfaceAddresses) {
                    direccion.broadcast?.let { destinos.add(it) }
                }
            }
        } catch (_: Throwable) {
            return emptyList()
        }
        if (destinos.isEmpty()) return emptyList()

        val peticion = FIRMA_DIFUSION.toByteArray(Charsets.UTF_8)
        var socket: DatagramSocket? = null
        try {
            socket = DatagramSocket().apply {
                broadcast = true
                soTimeout = 250
            }
            for (destino in destinos) {
                try {
                    socket.send(
                        DatagramPacket(peticion, peticion.size, destino, PUERTO_DIFUSION),
                    )
                } catch (_: Throwable) {
                    // Una interfaz sin ruta de difusión no invalida las demás.
                }
            }

            val limite = System.currentTimeMillis() + ESPERA_DIFUSION_MS
            while (System.currentTimeMillis() < limite) {
                val buffer = ByteArray(2048)
                val paquete = DatagramPacket(buffer, buffer.size)
                try {
                    socket.receive(paquete)
                } catch (_: java.net.SocketTimeoutException) {
                    continue
                }
                val texto = String(paquete.data, 0, paquete.length, Charsets.UTF_8)
                val anuncio = try {
                    json.decodeFromString(DifusionNodoDto.serializer(), texto)
                } catch (_: Throwable) {
                    continue
                }
                if (anuncio.servidor != IDENTIDAD_NODO || anuncio.puerto !in 1..65535) continue
                val host = paquete.address?.hostAddress?.substringBefore('%') ?: continue
                encontrados.add("http://$host:${anuncio.puerto}")
            }
        } catch (_: Throwable) {
            // Sin red, sin permiso o difusión bloqueada: queda el sondeo HTTP.
        } finally {
            try {
                socket?.close()
            } catch (_: Throwable) {
                // Cierre defensivo.
            }
        }
        return encontrados.toList()
    }

    // ------------------------------------------------------------------
    // Sondeo de la subred
    // ------------------------------------------------------------------

    /**
     * Direcciones IPv4 cercanas de todas las interfaces activas.
     *
     * Se escanea la red real de la interfaz cuando es /24 o más pequeña; en
     * redes grandes (/16, /8) se limita al /24 de la propia dirección, que es
     * donde suele estar el servidor de la institución. El límite evita que un
     * teléfono en una red corporativa genere decenas de miles de conexiones.
     */
    private fun candidatosLocales(): List<String> {
        val cercanos = mutableListOf<String>()
        val vistos = LinkedHashSet<String>()
        try {
            for (interfaz in NetworkInterface.getNetworkInterfaces() ?: return emptyList()) {
                if (!interfaz.isUp || interfaz.isLoopback) continue
                for (direccion in interfaz.interfaceAddresses) {
                    val ip = direccion.address as? Inet4Address ?: continue
                    if (ip.isLoopbackAddress || ip.isLinkLocalAddress || !ip.isSiteLocalAddress) continue

                    val crudo = ByteBuffer.wrap(ip.address).int.toLong() and 0xFFFFFFFFL
                    val prefijoRed = direccion.networkPrefixLength.toInt().takeIf { it in 1..32 } ?: 24
                    val prefijo = prefijoRed.coerceIn(24, 30)
                    val total = 1 shl (32 - prefijo)
                    val base = crudo and ((0xFFFFFFFFL shl (32 - prefijo)) and 0xFFFFFFFFL)
                    val propio = (crudo and (total - 1L)).toInt()

                    val zona = (1 until total - 1)
                        .filter { it != propio }
                        .sortedWith(
                            compareBy(
                                { prioridad(it) },
                                { abs(it - propio) },
                                { it },
                            ),
                        )
                        .map { ipDe(base + it) }
                    for (candidato in zona) {
                        if (vistos.add(candidato)) cercanos.add(candidato)
                    }
                }
            }
        } catch (_: Throwable) {
            return emptyList()
        }

        // Prioriza las direcciones donde suelen estar los equipos y las más
        // cercanas al teléfono; el sondeo se corta al encontrar el nodo.
        return cercanos.take(MAX_CANDIDATOS)
    }

    private fun prioridad(host: Int): Int = when (host) {
        1 -> 0
        100 -> 1
        10 -> 2
        2 -> 3
        254 -> 4
        else -> 10
    }

    private fun ipDe(valor: Long): String =
        "${(valor ushr 24) and 0xFF}.${(valor ushr 16) and 0xFF}." +
            "${(valor ushr 8) and 0xFF}.${valor and 0xFF}"

    /**
     * Devuelve la URL del primer host que responde como nodo central.
     *
     * Los candidatos se prueban en lotes para no abrir cientos de conexiones a
     * la vez; en cuanto un lote encuentra el nodo, se deja de sondear.
     */
    private suspend fun buscarNodo(candidatos: List<String>): String? {
        for (lote in candidatos.chunked(TAMANO_LOTE_SONDEO)) {
            val encontrado = coroutineScope {
                lote.map { ip ->
                    async(Dispatchers.IO) {
                        val url = "http://$ip:$PUERTO"
                        if (esNodoCentral(url)) url else null
                    }
                }.awaitAll().firstOrNull { it != null }
            }
            if (encontrado != null) return encontrado
        }
        return null
    }

    private fun esNodoCentral(url: String): Boolean {
        return try {
            val peticion = Request.Builder()
                .url("${normalizar(url)}/api/v1/ping")
                .get()
                .build()
            clienteSonda.newCall(peticion).execute().use { respuesta ->
                if (!respuesta.isSuccessful) return false
                val cuerpo = respuesta.body?.string() ?: return false
                val ping = json.decodeFromString(PingDto.serializer(), cuerpo)
                ping.servidor == IDENTIDAD_NODO
            }
        } catch (_: Throwable) {
            false
        }
    }

    // ------------------------------------------------------------------
    // Alta
    // ------------------------------------------------------------------

    private fun solicitarAlta(url: String): EmparejarRespuestaDto? {
        return try {
            val peticion = Request.Builder()
                .url("${normalizar(url)}/api/v1/auth/emparejar")
                .header("X-Nombre-Equipo", nombreEquipo())
                .post(vacio())
                .build()
            clienteAlta.newCall(peticion).execute().use { respuesta ->
                if (!respuesta.isSuccessful) return null
                val cuerpo = respuesta.body?.string() ?: return null
                val alta = json.decodeFromString(EmparejarRespuestaDto.serializer(), cuerpo)
                alta.takeIf { it.dispositivoId.isNotBlank() && it.token.isNotBlank() }
            }
        } catch (_: Throwable) {
            null
        }
    }

    private fun nombreEquipo(): String = try {
        "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}".trim()
            .ifBlank { "Teléfono SDEP" }
    } catch (_: Throwable) {
        "Teléfono SDEP"
    }

    /** Acepta «192.168.1.10:8765» y lo convierte en una URL sin barra final */
    private fun normalizar(url: String): String {
        var limpia = url.trim().trimEnd('/')
        if (limpia.isEmpty()) return limpia
        if (!limpia.startsWith("http://") && !limpia.startsWith("https://")) {
            limpia = "http://$limpia"
        }
        return limpia
    }

    /** Cuerpo vacío para el POST de alta (sin payload) */
    private fun vacio(): okhttp3.RequestBody = ByteArray(0).toRequestBody(null)

    /** Respuesta de la difusión UDP: solo identidad y puerto, sin secretos */
    @Serializable
    private data class DifusionNodoDto(
        val servidor: String = "",
        @SerialName("version_protocolo") val versionProtocolo: String = "",
        val puerto: Int = 0,
        val nombre: String = "",
    )

    private companion object {
        /** Puerto fijo del nodo central (el mismo que abre el instalador) */
        const val PUERTO = 8765

        /** Puerto de difusión: no cambia aunque el HTTP se configure distinto */
        const val PUERTO_DIFUSION = 8766

        /** Firma de la petición de descubrimiento */
        const val FIRMA_DIFUSION = "SDEP/1 DESCUBRIR"

        /** Ventana total para escuchar respuestas de difusión */
        const val ESPERA_DIFUSION_MS = 1_200L

        /** Identidad que devuelve ``ping`` y que descarta a otros servicios */
        const val IDENTIDAD_NODO = "nodo-central-sincronizacion"

        /** Tope de direcciones a sondear (redes /16 o mayores) */
        const val MAX_CANDIDATOS = 600

        /** Sondas simultáneas por lote (OkHttp admite 64 por defecto) */
        const val TAMANO_LOTE_SONDEO = 64
    }
}
