package ve.edu.sdep.movil.datos.remoto

import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.Retrofit
import ve.edu.sdep.movil.dominio.modelo.ConfiguracionSync
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Construye los dos clientes del nodo central para una configuración concreta.
 *
 * * [protocolo] — el canal v1 (ping/push/pull/blob): solo lleva las cabeceras
 *   del equipo emparejado. Es el que replica datos.
 * * [acciones] — el canal v2 (auth/consultas/acciones/archivos): además lleva
 *   `X-Sesion` con el token de usuario; sin él el servidor responde 401.
 *
 * Retrofit fija la dirección base al crearse, así que los clientes se rehacen
 * cuando cambian la URL, el equipo, el token o la sesión. Se guarda el último
 * par para no reconstruirlo en cada llamada.
 *
 * Las cabeceras se añaden aquí, en un interceptor, y no en cada llamada: así
 * ningún punto del código puede olvidarlas.
 */
@Singleton
class ApiSyncFactory @Inject constructor(
    private val clienteBase: OkHttpClient,
    private val json: Json,
) {

    private var cacheProtocolo: CacheProtocolo? = null
    private var cacheAcciones: CacheAcciones? = null

    /** Cliente del protocolo de replicación (v1), con las cabeceras del equipo */
    @Synchronized
    fun protocolo(configuracion: ConfiguracionSync): ProtocoloApi {
        val actual = cacheProtocolo
        if (actual != null && actual.clave == configuracion) return actual.api

        require(configuracion.completa) { "La configuración del nodo central está incompleta" }

        val api = constructor(configuracion.urlNormalizada(), configuracion, sesion = null)
            .create(ProtocoloApi::class.java)

        cacheProtocolo = CacheProtocolo(configuracion, api)
        return api
    }

    /**
     * Cliente de acciones (v2).
     *
     * Para el **login** basta con la URL (el equipo puede estar sin emparejar
     * todavía); para el resto de rutas el servidor exige además la sesión.
     */
    @Synchronized
    fun acciones(configuracion: ConfiguracionSync, sesion: String? = null): ApiAcciones {
        val actual = cacheAcciones
        val clave = ClaveAcciones(configuracion.url, configuracion.equipo, configuracion.token, sesion)
        if (actual != null && actual.clave == clave) return actual.api

        require(configuracion.url.isNotBlank()) { "Falta la dirección del nodo central" }

        val api = constructor(configuracion.urlNormalizada(), configuracion, sesion)
            .create(ApiAcciones::class.java)

        cacheAcciones = CacheAcciones(clave, api)
        return api
    }

    private fun constructor(url: String, configuracion: ConfiguracionSync, sesion: String?) =
        Retrofit.Builder()
            .baseUrl(url)
            .client(
                clienteBase.newBuilder()
                    .addInterceptor { cadena ->
                        val peticion = cadena.request().newBuilder()
                            .header("Accept", "application/json")
                            // Las cabeceras del equipo solo viajan si están
                            // configuradas: el login puede ser el primer contacto.
                            .apply {
                                if (configuracion.token.isNotBlank()) {
                                    header("Authorization", "Bearer ${configuracion.token}")
                                }
                                if (configuracion.equipo.isNotBlank()) {
                                    header("X-Dispositivo", configuracion.equipo)
                                }
                                if (!sesion.isNullOrBlank()) {
                                    header("X-Sesion", sesion)
                                }
                                // Nombre visible del puesto para el alta por
                                // auto-emparejamiento: el servidor lo usa para
                                // etiquetar el dispositivo en su lista. Es
                                // inofensivo en el resto de rutas.
                                header("X-Nombre-Equipo", nombreEquipo)
                            }
                            .build()
                        cadena.proceed(peticion)
                    }
                    .build(),
            )
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()

    /**
     * Nombre visible del puesto, para el alta por auto-emparejamiento.
     *
     * Es el modelo del dispositivo, que el administrador reconoce al ver la
     * lista de equipos en el escritorio. No lleva datos personales. Se calcula
     * una sola vez: antes el interceptor leía las propiedades del sistema en
     * cada petición, incluso en los ciclos de sincronización en segundo plano.
     */
    private val nombreEquipo: String by lazy {
        try {
            "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}".trim()
        } catch (_: Throwable) {
            "Teléfono SDEP"
        }
    }

    private data class ClaveAcciones(val url: String, val equipo: String, val token: String, val sesion: String?)
    private data class CacheProtocolo(val clave: ConfiguracionSync, val api: ProtocoloApi)
    private data class CacheAcciones(val clave: ClaveAcciones, val api: ApiAcciones)
}
