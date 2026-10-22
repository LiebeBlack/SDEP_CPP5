package ve.edu.sdep.movil.di

import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import ve.edu.sdep.movil.BuildConfig
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object ModuloRed {

    @Provides
    @Singleton
    fun json(): Json = Json {
        // El servidor puede añadir campos en versiones nuevas sin romper esta.
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = false
    }

    @Provides
    @Singleton
    fun clienteHttp(): OkHttpClient {
        val constructor = OkHttpClient.Builder()
            // Tiempos pensados para la Wi-Fi de un colegio: abrir conexión debe
            // fallar rápido (el escritorio cambió de IP o está apagado) sin
            // dejar el botón de ingreso girando 15 s. La lectura conserva 30 s
            // para una intranet lenta y el tope global impide que una petición
            // colgada (servidor que acepta y no responde) retenga la pantalla
            // para siempre.
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .callTimeout(90, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)

        if (BuildConfig.DEBUG) {
            val registro = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC
                // El token del equipo no debe quedar en el log del teléfono.
                redactHeader("Authorization")
            }
            constructor.addInterceptor(registro)
        }

        return constructor.build()
    }
}
