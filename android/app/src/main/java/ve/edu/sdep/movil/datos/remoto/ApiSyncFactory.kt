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
 * Construye el cliente del nodo central para una configuración concreta.
 *
 * Retrofit fija la dirección base al crearse, así que el cliente se rehace
 * cuando cambian la URL, el token o el identificador del equipo (es decir, casi
 * nunca). Se guarda el último para no reconstruirlo en cada sincronización.
 *
 * Las cabeceras de autenticación se añaden aquí, en un interceptor, y no en
 * cada llamada: así ningún punto del código puede olvidarlas.
 */
@Singleton
class ApiSyncFactory @Inject constructor(
    private val clienteBase: OkHttpClient,
    private val json: Json,
) {

    private var cache: Cache? = null

    @Synchronized
    fun crear(configuracion: ConfiguracionSync): ProtocoloApi {
        val actual = cache
        if (actual != null && actual.clave == configuracion) return actual.api

        require(configuracion.completa) { "La configuración del nodo central está incompleta" }

        val cliente = clienteBase.newBuilder()
            .addInterceptor { cadena ->
                val peticion = cadena.request().newBuilder()
                    .header("Authorization", "Bearer ${configuracion.token}")
                    .header("X-Dispositivo", configuracion.equipo)
                    .header("Accept", "application/json")
                    .build()
                cadena.proceed(peticion)
            }
            .build()

        val api = Retrofit.Builder()
            .baseUrl(configuracion.urlNormalizada())
            .client(cliente)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(ProtocoloApi::class.java)

        cache = Cache(configuracion, api)
        return api
    }

    private data class Cache(val clave: ConfiguracionSync, val api: ProtocoloApi)
}
