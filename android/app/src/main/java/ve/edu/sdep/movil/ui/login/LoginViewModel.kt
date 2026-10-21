package ve.edu.sdep.movil.ui.login

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
import ve.edu.sdep.movil.datos.repositorio.AutenticacionRepositorio
import ve.edu.sdep.movil.datos.repositorio.ConfiguracionRepositorio
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

/**
 * Estado del formulario de ingreso.
 *
 * Mientras el teléfono no esté vinculado al nodo central no hay nada que
 * autenticar: la pantalla pide primero la dirección, el equipo y el token que
 * entrega el administrador. Una vez guardados, el ingreso es contra la base
 * institucional (las mismas cuentas del escritorio).
 */
data class EstadoLogin(
    val cargando: Boolean = true,
    val usuario: String = "",
    val contrasena: String = "",
    /** Vinculación con el nodo central */
    val configCompleta: Boolean = false,
    val url: String = "",
    val equipo: String = "",
    val token: String = "",
    val guardandoConfig: Boolean = false,
    val error: String? = null,
    val ocupado: Boolean = false,
    val biometriaGuardada: Boolean = false,
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val autenticacion: AutenticacionRepositorio,
    private val configuracion: ConfiguracionRepositorio,
) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoLogin())
    val estado: StateFlow<EstadoLogin> = _estado.asStateFlow()

    init {
        viewModelScope.launch {
            val config = withContext(Dispatchers.IO) { configuracion.cargar(forzar = true) }
            val biometria = withContext(Dispatchers.IO) { autenticacion.hayCredencialBiometrica() }
            _estado.update {
                it.copy(
                    cargando = false,
                    configCompleta = config.completa,
                    url = config.url,
                    equipo = config.equipo,
                    token = config.token,
                    biometriaGuardada = biometria,
                )
            }
        }
    }

    fun cambiarUrl(valor: String) = _estado.update { it.copy(url = valor, error = null) }

    fun cambiarEquipo(valor: String) = _estado.update { it.copy(equipo = valor, error = null) }

    fun cambiarToken(valor: String) = _estado.update { it.copy(token = valor, error = null) }

    fun cambiarUsuario(valor: String) = _estado.update { it.copy(usuario = valor, error = null) }

    fun cambiarContrasena(valor: String) = _estado.update { it.copy(contrasena = valor, error = null) }

    fun registrarError(mensaje: String) = _estado.update { it.copy(error = mensaje, ocupado = false) }

    fun limpiarError() = _estado.update { it.copy(error = null) }

    /**
     * Relee si hay una credencial biométrica guardada.
     *
     * Se llama cada vez que se abre la pantalla: el usuario pudo activar la
     * huella en Ajustes después del último ingreso, o desactivarla.
     */
    fun refrescarBiometria() {
        viewModelScope.launch {
            val biometria = withContext(Dispatchers.IO) { autenticacion.hayCredencialBiometrica() }
            _estado.update { it.copy(biometriaGuardada = biometria) }
        }
    }

    /** Guarda la vinculación con el nodo central (dirección, equipo y token) */
    fun guardarConfiguracion() {
        val actual = _estado.value
        if (actual.guardandoConfig) return
        if (actual.url.isBlank()) {
            _estado.update { it.copy(error = "Escriba la dirección del nodo central.") }
            return
        }
        viewModelScope.launch {
            _estado.update { it.copy(guardandoConfig = true, error = null) }
            val guardado = configuracion.guardar(
                url = actual.url,
                equipo = actual.equipo,
                token = actual.token,
                activa = true,
                periodoMinutos = configuracion.periodoMinutos,
            )
            if (guardado) {
                val config = configuracion.actual()
                _estado.update {
                    it.copy(
                        guardandoConfig = false,
                        configCompleta = config.completa,
                        url = config.url,
                        equipo = config.equipo,
                        token = config.token,
                    )
                }
            } else {
                _estado.update {
                    it.copy(
                        guardandoConfig = false,
                        error = "No se pudo guardar de forma segura. Revise el almacenamiento del teléfono.",
                    )
                }
            }
        }
    }

    /** Ingreso con usuario y contraseña contra el nodo central */
    fun entrar(activarBiometria: Boolean) {
        val actual = _estado.value
        if (actual.ocupado) return
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true, error = null) }
            when (
                val resultado = autenticacion.entrar(
                    usuario = actual.usuario,
                    contrasena = actual.contrasena,
                    activarBiometria = activarBiometria,
                )
            ) {
                is Resultado.Exito -> _estado.update {
                    it.copy(
                        ocupado = false,
                        contrasena = "",
                        error = null,
                        biometriaGuardada = activarBiometria || it.biometriaGuardada,
                    )
                }

                is Resultado.Fallo -> _estado.update { it.copy(ocupado = false, error = resultado.mensaje) }
            }
        }
    }

    /** Se llama cuando el sensor biométrico ya confirmó al usuario */
    fun entrarConBiometria() {
        if (_estado.value.ocupado) return
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true, error = null) }
            when (val resultado = autenticacion.entrarConBiometria()) {
                is Resultado.Exito -> _estado.update { it.copy(ocupado = false) }
                is Resultado.Fallo -> _estado.update {
                    it.copy(ocupado = false, error = resultado.mensaje, biometriaGuardada = false)
                }
            }
        }
    }
}
