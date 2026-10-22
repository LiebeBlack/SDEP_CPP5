package ve.edu.sdep.movil.datos.remoto

import java.net.Inet4Address
import java.net.NetworkInterface
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

/**
 * Encuentra solo el nodo central de escritorio en la red local y se da de alta
 * como puesto, sin que nadie escriba una dirección ni un token.
 *
 * El camino tiene dos pasos, ambos sobre el mismo puerto fijo (8765):
 *
 * 1. **Descubrimiento** — se recorre la subred del teléfono haciendo `GET
 *    /api/v1/ping` a cada host con un tiempo de conexión corto. El nodo
 *    responde con su identidad (`servidor == "nodo-central-sincronizacion"`),
 *    así que cualquier otro equipo que conteste en ese puerto se descarta.
 * 2. **Alta** — al primer nodo que responde se le pide `POST
 *    /api/v1/auth/emparejar`, que devuelve el identificador de equipo y su
 *    token (solo se devuelven una vez; el servidor guarda el hash).
 *
 * El emparejamiento es abierto por decisión del propietario del sistema: no
 * exige código. La única red de seguridad en el servidor es el límite de
 * peticiones por IP; el login de usuario sigue exigiendo una cuenta real de la
 * base institucional.
 */
@Singleton
class Descubrimiento @Inject constructor(
    private val json: Json,
) {

    /**
     * Cliente aparte con tiempos cortos: el escaneo toca hasta 254 hosts, casi
     * todos muertos, y el cliente general espera 15 s por conexión. Con 400 ms
     * una subred completa se recorre en poco más de un segundo.
     */
    private val clienteEscaneo: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(400, TimeUnit.MILLISECONDS)
        .readTimeout(1_500, TimeUnit.MILLISECONDS)
        .callTimeout(2_500, TimeUnit.MILLISECONDS)
        .retryOnConnectionFailure(false)
        .build()

    /** Cliente normal para la alta (una sola petición ya contra un host vivo) */
    private val clienteAlta: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(3, TimeUnit.SECONDS)
        .readTimeout(8, TimeUnit.SECONDS)
        .callTimeout(12, TimeUnit.SECONDS)
        .build()

    /** Resultado de descubrir y darse de alta: los tres datos de la vinculación */
    data class Vinculo(
        val url: String,
        val equipo: String,
        val token: String,
    )

    /**
     * Busca el nodo en la subred del teléfono y devuelve la vinculación lista
     * para guardar.
     *
     * @return el vínculo, o null si no se encontró ningún nodo (red aislada,
     *         el escritorio apagado, o el emparejamiento cerrado allí).
     */
    suspend fun descubrir(): Vinculo? = withContext(Dispatchers.IO) {
        val candidatos = subredLocal() ?: return@withContext null
        val nodo = buscarNodo(candidatos) ?: return@withContext null
        val alta = solicitarAlta(nodo) ?: return@withContext null
        Vinculo(url = nodo, equipo = alta.dispositivoId, token = alta.token)
    }

    // ------------------------------------------------------------------
    // Descubrimiento
    // ------------------------------------------------------------------

    /** IP y prefijo /24 del teléfono, como lista de direcciones candidatas */
    private fun subredLocal(): List<String>? {
        val propia = direccionPropia() ?: return null
        val octetos = propia.address
        val base = "${octetos[0].toInt() and 0xff}.${octetos[1].toInt() and 0xff}.${octetos[2].toInt() and 0xff}"
        val mio = propia.hostAddress
        return (1..254)
            .map { "$base.$it" }
            .filter { it != mio }
    }

    private fun direccionPropia(): Inet4Address? {
        val interfaces = try {
            NetworkInterface.getNetworkInterfaces()
        } catch (_: Throwable) {
            return null
        } ?: return null
        for (interfaz in interfaces) {
            if (!interfaz.isUp || interfaz.isLoopback) continue
            for (direccion in interfaz.inetAddresses) {
                if (direccion is Inet4Address && !direccion.isLoopbackAddress && direccion.isSiteLocalAddress) {
                    return direccion
                }
            }
        }
        return null
    }

    /**
     * Devuelve la URL del primer host que responde como nodo central.
     *
     * Se lanzan varias sondas a la vez (acotadas por ``concision``) para no
     * tardar una eternidad; en cuanto uno responde, el resto se descartan.
     */
    private suspend fun buscarNodo(candidatos: List<String>): String? = coroutineScope {
        val urlEncontrada = java.util.concurrent.atomic.AtomicReference<String?>()
        candidatos
            .map { ip ->
                async {
                    // Alguien ya encontró el nodo: no seguir escaneando.
                    if (urlEncontrada.get() != null) return@async null
                    val url = "http://$ip:$PUERTO"
                    if (esNodoCentral(url)) {
                        urlEncontrada.compareAndSet(null, url)
                        url
                    } else {
                        null
                    }
                }
            }
            .awaitAll()
            .firstOrNull { it != null }
            ?: urlEncontrada.get()
    }

    private fun esNodoCentral(url: String): Boolean {
        return try {
            val peticion = Request.Builder()
                .url("$url/api/v1/ping")
                .get()
                .build()
            clienteEscaneo.newCall(peticion).execute().use { respuesta ->
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

    private suspend fun solicitarAlta(url: String): EmparejarRespuestaDto? {
        return try {
            val peticion = Request.Builder()
                .url("$url/api/v1/auth/emparejar")
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
    } catch (_: Throwable) {
        "Teléfono SDEP"
    }

    /** Cuerpo vacío para el POST de alta (sin payload) */
    private fun vacio(): okhttp3.RequestBody = ByteArray(0).toRequestBody(null)

    private companion object {
        /** Puerto fijo del nodo central (el mismo que abre el instalador) */
        const val PUERTO = 8765
        /** Identidad que devuelve ``ping`` y que descarta a otros servicios */
        const val IDENTIDAD_NODO = "nodo-central-sincronizacion"
    }
}
