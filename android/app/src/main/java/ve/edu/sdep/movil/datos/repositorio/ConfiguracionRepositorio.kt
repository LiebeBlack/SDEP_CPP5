package ve.edu.sdep.movil.datos.repositorio

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import ve.edu.sdep.movil.R
import ve.edu.sdep.movil.datos.seguridad.Boveda
import ve.edu.sdep.movil.dominio.modelo.ConfiguracionSync
import java.util.concurrent.atomic.AtomicBoolean
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Configuración del nodo central visible para la interfaz.
 *
 * La lectura de la bóveda cifrada toca el Keystore y el disco, así que no se
 * hace en el constructor: se carga la primera vez que una pantalla la pide, en
 * un hilo de entrada/salida, y se mantiene en un ``StateFlow`` para que todas
 * las pantallas vean el mismo valor.
 */
@Singleton
class ConfiguracionRepositorio @Inject constructor(
    private val boveda: Boveda,
    private val contexto: Context,
) {

    private val _configuracion = MutableStateFlow(ConfiguracionSync())
    val configuracion: StateFlow<ConfiguracionSync> = _configuracion.asStateFlow()

    private val cargada = AtomicBoolean(false)
    private val candado = Any()

    /** Periodo de sincronización en minutos (15 por omisión) */
    var periodoMinutos: Int = 15
        private set

    suspend fun cargar(forzar: Boolean = false): ConfiguracionSync = withContext(Dispatchers.IO) {
        synchronized(candado) {
            if (forzar || !cargada.get()) {
                val almacenada = boveda.leerConfiguracion()
                // Si no hay configuración guardada, usar valores por defecto
                val url = if (almacenada.url.isBlank()) {
                    contexto.getString(R.string.default_server_url)
                } else {
                    almacenada.url
                }
                val equipo = if (almacenada.equipo.isBlank()) {
                    contexto.getString(R.string.default_device_id)
                } else {
                    almacenada.equipo
                }
                val token = if (almacenada.token.isBlank()) {
                    contexto.getString(R.string.default_device_token)
                } else {
                    almacenada.token
                }

                _configuracion.value = ConfiguracionSync(
                    url = url,
                    equipo = equipo,
                    token = token,
                    activa = almacenada.activa,
                )
                periodoMinutos = almacenada.periodoMinutos
                cargada.set(true)
            }
        }
        _configuracion.value
    }

    /** Valor ya cargado; no lee disco */
    fun actual(): ConfiguracionSync = _configuracion.value

    /**
     * Guarda la configuración.
     *
     * @return true si la bóveda cifrada pudo escribir los valores
     */
    suspend fun guardar(
        url: String,
        equipo: String,
        token: String,
        activa: Boolean,
        periodoMinutos: Int,
    ): Boolean = withContext(Dispatchers.IO) {
        val normalizada = normalizarUrl(url)
        val guardado = boveda.guardarConfiguracion(
            url = normalizada,
            equipo = equipo,
            token = token,
            activa = activa,
            periodoMinutos = periodoMinutos.coerceIn(15, 360),
        )
        if (guardado) {
            this@ConfiguracionRepositorio.periodoMinutos = periodoMinutos.coerceIn(15, 360)
            _configuracion.value = ConfiguracionSync(
                url = normalizada,
                equipo = equipo.trim(),
                token = token.trim(),
                activa = activa,
            )
        }
        guardado
    }

    /** Acepta «192.168.1.10:8765» y lo convierte en una URL utilizable */
    private fun normalizarUrl(url: String): String {
        var limpia = url.trim().trimEnd('/')
        if (limpia.isEmpty()) return ""
        if (!limpia.startsWith("http://") && !limpia.startsWith("https://")) {
            limpia = "http://$limpia"
        }
        return limpia
    }
}
