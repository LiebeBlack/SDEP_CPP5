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
import ve.edu.sdep.movil.datos.repositorio.ConectorNodo
import ve.edu.sdep.movil.datos.repositorio.ConfiguracionRepositorio
import ve.edu.sdep.movil.datos.repositorio.SesionRepositorio
import ve.edu.sdep.movil.datos.repositorio.SincronizacionRepositorio
import ve.edu.sdep.movil.dominio.modelo.Resultado
import ve.edu.sdep.movil.sincronizacion.ProgramadorSync
import javax.inject.Inject

data class EstadoAjustes(
    val cargando: Boolean = true,
    /** Hay vinculación completa con el sistema de escritorio */
    val conectado: Boolean = false,
    /** Se está buscando de nuevo el escritorio */
    val redescubriendo: Boolean = false,
    val servidor: String? = null,
    val urlServidor: String = "",
    val versionProtocolo: String? = null,
    val activa: Boolean = true,
    val periodoMinutos: Int = 15,
    val ocupado: Boolean = false,
    val probando: Boolean = false,
    val sincronizando: Boolean = false,
    val mensaje: String? = null,
    val esError: Boolean = false,
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
 * No hay dirección, equipo ni token editables: la vinculación con el escritorio
 * es automática. Aquí solo se muestra su estado, se puede volver a buscar el
 * equipo, activar o desactivar el envío automático y revisar la cola.
 */
@HiltViewModel
class AjustesViewModel @Inject constructor(
    private val configuracion: ConfiguracionRepositorio,
    private val conector: ConectorNodo,
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
                    conectado = config.completa,
                    urlServidor = config.url,
                    activa = if (config.completa) config.activa else true,
                    periodoMinutos = configuracion.periodoMinutos,
                    biometriaActiva = biometria,
                )
            }
            if (!config.completa) redescubrir()
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

    fun limpiarMensaje() = _estado.update { it.copy(mensaje = null) }

    fun registrarMensaje(mensaje: String, esError: Boolean = false) =
        _estado.update { it.copy(mensaje = mensaje, esError = esError) }

    /**
     * Vuelve a emparejar el teléfono, sin pedir la dirección ni el token.
     *
     * Se usa cuando el escritorio cambió de IP, se reinstaló o el token fue
     * revocado en él. Si la dirección actual ya no responde, el conector hace
     * el descubrimiento completo por difusión y subred.
     */
    fun redescubrir() {
        if (_estado.value.redescubriendo) return
        viewModelScope.launch {
            _estado.update { it.copy(redescubriendo = true, esError = false, mensaje = null) }
            when (val resultado = conector.revincular()) {
                is Resultado.Exito -> {
                    val config = resultado.valor
                    withContext(Dispatchers.IO) {
                        if (config.activa) programador.programar(configuracion.periodoMinutos)
                    }
                    _estado.update {
                        it.copy(
                            redescubriendo = false,
                            conectado = true,
                            urlServidor = config.url,
                            activa = config.activa,
                            periodoMinutos = configuracion.periodoMinutos,
                            mensaje = "Teléfono vinculado con el sistema de escritorio.",
                            esError = false,
                        )
                    }
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(
                        redescubriendo = false,
                        conectado = false,
                        mensaje = resultado.mensaje,
                        esError = true,
                    )
                }
            }
        }
    }

    /** Cambia el periodo con una opción predefinida, entre 15 y 360 minutos. */
    fun cambiarPeriodo(minutos: Int) {
        val nuevo = minutos.coerceIn(15, 360)
        if (_estado.value.periodoMinutos == nuevo || _estado.value.ocupado) return
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true) }
            if (!configuracion.cambiarPeriodo(nuevo)) {
                _estado.update {
                    it.copy(
                        ocupado = false,
                        mensaje = "No se pudo guardar el intervalo de sincronización.",
                        esError = true,
                    )
                }
                return@launch
            }
            if (_estado.value.activa) {
                withContext(Dispatchers.IO) { programador.programar(nuevo) }
            }
            _estado.update {
                it.copy(
                    ocupado = false,
                    periodoMinutos = nuevo,
                    mensaje = "Intervalo automático ajustado a $nuevo minutos.",
                    esError = false,
                )
            }
        }
    }

    /** Activa o desactiva el envío automático de inmediato (sin botón Guardar) */
    fun cambiarActiva(valor: Boolean) {
        val anterior = _estado.value.activa
        if (anterior == valor) return
        viewModelScope.launch {
            _estado.update { it.copy(activa = valor) }
            val guardado = configuracion.cambiarActiva(valor)
            if (!guardado) {
                _estado.update {
                    it.copy(
                        activa = anterior,
                        mensaje = "No se pudo guardar la preferencia de sincronización.",
                        esError = true,
                    )
                }
                return@launch
            }
            withContext(Dispatchers.IO) {
                if (valor) programador.programar(configuracion.periodoMinutos) else programador.cancelar()
            }
            _estado.update {
                it.copy(
                    mensaje = if (valor) {
                        "Sincronización automática activada."
                    } else {
                        "Sincronización automática desactivada."
                    },
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
            if (!_estado.value.conectado) {
                when (val conexion = conector.asegurarConexion(forzar = true)) {
                    is Resultado.Exito -> _estado.update {
                        it.copy(conectado = true, urlServidor = conexion.valor.url)
                    }

                    is Resultado.Fallo -> {
                        _estado.update {
                            it.copy(probando = false, mensaje = conexion.mensaje, esError = true)
                        }
                        return@launch
                    }
                }
            }
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
                            conectado = true,
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
            if (!_estado.value.conectado) {
                when (val conexion = conector.asegurarConexion(forzar = true)) {
                    is Resultado.Exito -> _estado.update {
                        it.copy(conectado = true, urlServidor = conexion.valor.url)
                    }

                    is Resultado.Fallo -> {
                        _estado.update {
                            it.copy(sincronizando = false, mensaje = conexion.mensaje, esError = true)
                        }
                        return@launch
                    }
                }
            }
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
