package ve.edu.sdep.movil.ui.ajustes

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ve.edu.sdep.movil.datos.local.dao.ConflictoDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.repositorio.AutenticacionRepositorio
import ve.edu.sdep.movil.datos.repositorio.ConfiguracionRepositorio
import ve.edu.sdep.movil.datos.repositorio.SesionRepositorio
import ve.edu.sdep.movil.datos.repositorio.SincronizacionRepositorio
import ve.edu.sdep.movil.dominio.modelo.Resultado
import ve.edu.sdep.movil.dominio.modelo.Rol
import ve.edu.sdep.movil.sincronizacion.ProgramadorSync
import javax.inject.Inject

data class EstadoAjustes(
    val cargando: Boolean = true,
    val url: String = "",
    val equipo: String = "",
    val token: String = "",
    val activa: Boolean = true,
    val ocupado: Boolean = false,
    val probando: Boolean = false,
    val sincronizando: Boolean = false,
    val mensaje: String? = null,
    val esError: Boolean = false,
    val servidor: String? = null,
    val versionProtocolo: String? = null,
    val desfaseSegundos: Long? = null,
    val pendientes: Int = 0,
    val conflictos: Int = 0,
    val ultimaSync: Long? = null,
    val ultimoError: String? = null,
    val biometriaActiva: Boolean = false,
)

/**
 * Estado de la pantalla de ajustes.
 *
 * Reúne la configuración del nodo central, los contadores de la cola, la lista
 * de cuentas y la comodidad biométrica. Las escrituras se hacen en un hilo de
 * entrada/salida (la bóveda cifrada toca el Keystore) y el resultado se refleja
 * en el mismo flujo que lee la pantalla.
 */
@HiltViewModel
class AjustesViewModel @Inject constructor(
    private val configuracion: ConfiguracionRepositorio,
    private val sincronizacion: SincronizacionRepositorio,
    private val autenticacion: AutenticacionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
    private val programador: ProgramadorSync,
    operacionDao: OperacionDao,
    conflictoDao: ConflictoDao,
) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoAjustes())
    val estado: StateFlow<EstadoAjustes> = _estado.asStateFlow()

    init {
        viewModelScope.launch {
            val config = configuracion.cargar(forzar = true)
            val biometria = withContext(Dispatchers.IO) { autenticacion.hayCredencialBiometrica() }
            _estado.update {
                it.copy(
                    cargando = false,
                    url = config.url,
                    equipo = config.equipo,
                    token = config.token,
                    activa = config.activa,
                    biometriaActiva = biometria,
                )
            }
        }

        viewModelScope.launch {
            operacionDao.observarPendientes().collect { pendientes ->
                _estado.update { it.copy(pendientes = pendientes) }
            }
        }

        viewModelScope.launch {
            conflictoDao.observarPendientes().collect { conflictos ->
                _estado.update { it.copy(conflictos = conflictos) }
            }
        }

        viewModelScope.launch {
            sincronizacion.observarEstado().collect { estadoSync ->
                _estado.update {
                    it.copy(
                        ultimaSync = estadoSync?.ultimaSync,
                        ultimoError = estadoSync?.ultimoError,
                        servidor = estadoSync?.servidor,
                        versionProtocolo = estadoSync?.versionProtocolo,
                        desfaseSegundos = estadoSync?.desfaseSegundos,
                    )
                }
            }
        }
    }

    fun cambiarUrl(valor: String) = _estado.update { it.copy(url = valor) }

    fun cambiarEquipo(valor: String) = _estado.update { it.copy(equipo = valor) }

    fun cambiarToken(valor: String) = _estado.update { it.copy(token = valor) }

    fun cambiarActiva(valor: Boolean) = _estado.update { it.copy(activa = valor) }

    fun limpiarMensaje() = _estado.update { it.copy(mensaje = null) }

    fun registrarMensaje(mensaje: String, esError: Boolean = false) =
        _estado.update { it.copy(mensaje = mensaje, esError = esError) }

    /** Guarda la configuración y reprograma (o cancela) el trabajo periódico */
    fun guardar() {
        val actual = _estado.value
        if (actual.ocupado) return
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true) }
            val guardado = configuracion.guardar(
                url = actual.url,
                equipo = actual.equipo,
                token = actual.token,
                activa = actual.activa,
                periodoMinutos = configuracion.periodoMinutos,
            )
            if (!guardado) {
                _estado.update {
                    it.copy(
                        ocupado = false,
                        mensaje = "No se pudo guardar de forma segura. Revise el almacenamiento del teléfono.",
                        esError = true,
                    )
                }
                return@launch
            }

            val config = configuracion.actual()
            withContext(Dispatchers.IO) {
                if (config.activa && config.completa) {
                    programador.programar(configuracion.periodoMinutos)
                } else {
                    programador.cancelar()
                }
            }

            _estado.update {
                it.copy(
                    ocupado = false,
                    mensaje = "Configuración guardada.",
                    esError = false,
                )
            }
        }
    }

    /** Prueba el servicio y muestra versión y desfase de reloj */
    fun probarConexion() {
        if (_estado.value.probando) return
        viewModelScope.launch {
            _estado.update { it.copy(probando = true) }
            when (val resultado = sincronizacion.probarConexion()) {
                is Resultado.Exito -> {
                    val detalle = resultado.valor
                    val desfase = detalle.desfaseSegundos?.let { segundos ->
                        if (kotlin.math.abs(segundos) <= 60) {
                            "Reloj sincronizado."
                        } else {
                            "El reloj del teléfono difiere ${kotlin.math.abs(segundos)} s del servidor."
                        }
                    } ?: "El servidor no informó su hora."
                    _estado.update {
                        it.copy(
                            probando = false,
                            mensaje = "Conexión correcta con ${detalle.servidor.ifBlank { "el nodo central" }} " +
                                "(protocolo ${detalle.versionProtocolo}). $desfase",
                            esError = false,
                        )
                    }
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(probando = false, mensaje = resultado.mensaje, esError = true)
                }
            }
        }
    }

    fun sincronizarAhora() {
        if (_estado.value.sincronizando) return
        viewModelScope.launch {
            _estado.update { it.copy(sincronizando = true) }
            when (val resultado = sincronizacion.sincronizar()) {
                is Resultado.Exito -> {
                    val resumen = resultado.valor
                    _estado.update {
                        it.copy(
                            sincronizando = false,
                            mensaje = "Enviados ${resumen.enviadas} y recibidos ${resumen.recibidas} cambios.",
                            esError = false,
                        )
                    }
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(sincronizando = false, mensaje = resultado.mensaje, esError = true)
                }
            }
        }
    }

    /** Se llama después de que el sensor confirmó la identidad */
    fun activarBiometria() {
        val sesion = sesionRepositorio.actual ?: return
        viewModelScope.launch {
            val ok = autenticacion.activarBiometria(sesion)
            _estado.update {
                it.copy(
                    biometriaActiva = ok,
                    mensaje = if (ok) {
                        "Desbloqueo con huella activado."
                    } else {
                        "No se pudo guardar la llave de desbloqueo."
                    },
                    esError = !ok,
                )
            }
        }
    }

    fun desactivarBiometria() {
        viewModelScope.launch {
            autenticacion.olvidarBiometria()
            _estado.update {
                it.copy(biometriaActiva = false, mensaje = "Desbloqueo con huella desactivado.", esError = false)
            }
        }
    }

    /**
     * Cambia la contraseña de la cuenta en la base institucional.
     *
     * La autoridad es el nodo central: aquí no se guarda ninguna contraseña.
     */
    fun cambiarPassword(actual: String, nueva: String, confirmacion: String) {
        if (_estado.value.ocupado) return
        if (nueva != confirmacion) {
            _estado.update { it.copy(mensaje = "Las contraseñas no coinciden.", esError = true) }
            return
        }
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true) }
            when (val resultado = autenticacion.cambiarPassword(actual, nueva)) {
                is Resultado.Exito -> _estado.update {
                    it.copy(
                        ocupado = false,
                        mensaje = "Contraseña actualizada.",
                        esError = false,
                    )
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(ocupado = false, mensaje = resultado.mensaje, esError = true)
                }
            }
        }
    }

    fun cerrarSesion() {
        viewModelScope.launch {
            autenticacion.cerrarSesion()
        }
    }
}
