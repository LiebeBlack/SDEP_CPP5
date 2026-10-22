package ve.edu.sdep.movil.datos.repositorio

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import ve.edu.sdep.movil.datos.seguridad.Boveda
import ve.edu.sdep.movil.dominio.modelo.ConfiguracionSync
import java.util.concurrent.atomic.AtomicBoolean
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Configuración del nodo central visible para la interfaz.
 *
 * No existe ningún valor por defecto inventado: la dirección, el equipo y el
 * token llegan del auto-emparejamiento y se guardan cifrados. Si todavía no
 * hay vinculación, ``completa`` es false y la aplicación vuelve a buscar el
 * escritorio; nunca muestra un formulario para que el usuario los escriba.
 *
 * La lectura de la bóveda toca el Keystore y el disco, así que no se hace en
 * el constructor: se carga la primera vez que una pantalla la pide, en un hilo
 * de entrada/salida, y se mantiene en un ``StateFlow``.
 */
@Singleton
class ConfiguracionRepositorio @Inject constructor(
    private val boveda: Boveda,
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
                _configuracion.value = ConfiguracionSync(
                    url = almacenada.url.trim().trimEnd('/'),
                    equipo = almacenada.equipo.trim(),
                    token = almacenada.token.trim(),
                    activa = almacenada.activa,
                )
                periodoMinutos = almacenada.periodoMinutos.coerceIn(15, 360)
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
        if (normalizada.isBlank() || equipo.isBlank() || token.isBlank()) return@withContext false
        val periodo = periodoMinutos.coerceIn(15, 360)
        val guardado = boveda.guardarConfiguracion(
            url = normalizada,
            equipo = equipo.trim(),
            token = token.trim(),
            activa = activa,
            periodoMinutos = periodo,
        )
        if (guardado) {
            this@ConfiguracionRepositorio.periodoMinutos = periodo
            _configuracion.value = ConfiguracionSync(
                url = normalizada,
                equipo = equipo.trim(),
                token = token.trim(),
                activa = activa,
            )
        }
        guardado
    }

    /** Activa o desactiva el envío automático sin tocar la vinculación */
    suspend fun cambiarActiva(activa: Boolean): Boolean {
        val actual = cargar()
        if (!actual.completa) return false
        return guardar(
            url = actual.url,
            equipo = actual.equipo,
            token = actual.token,
            activa = activa,
            periodoMinutos = periodoMinutos,
        )
    }

    /** ¿Hay vinculación completa con el nodo central? */
    suspend fun hayConfiguracion(): Boolean = cargar().completa

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
