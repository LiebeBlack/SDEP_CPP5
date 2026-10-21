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
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

/**
 * Estado del formulario de ingreso.
 *
 * ``hayCuentas`` distingue el primer arranque (crear administrador) del uso
 * normal. Mientras se comprueba, ``cargando`` evita que la pantalla parpadee
 * entre un formulario y otro.
 */
data class EstadoLogin(
    val cargando: Boolean = true,
    val hayCuentas: Boolean = true,
    val nombre: String = "",
    val usuario: String = "",
    val contrasena: String = "",
    val confirmacion: String = "",
    val error: String? = null,
    val ocupado: Boolean = false,
    val biometriaGuardada: Boolean = false,
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val autenticacion: AutenticacionRepositorio,
) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoLogin())
    val estado: StateFlow<EstadoLogin> = _estado.asStateFlow()

    init {
        viewModelScope.launch {
            val hayCuentas = autenticacion.hayUsuarios()
            val biometria = withContext(Dispatchers.IO) { autenticacion.hayCredencialBiometrica() }
            _estado.update {
                it.copy(cargando = false, hayCuentas = hayCuentas, biometriaGuardada = biometria)
            }
        }
    }

    fun cambiarNombre(valor: String) = _estado.update { it.copy(nombre = valor, error = null) }

    fun cambiarUsuario(valor: String) = _estado.update { it.copy(usuario = valor, error = null) }

    fun cambiarContrasena(valor: String) = _estado.update { it.copy(contrasena = valor, error = null) }

    fun cambiarConfirmacion(valor: String) = _estado.update { it.copy(confirmacion = valor, error = null) }

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

    /** Alta de la cuenta administradora del primer arranque */
    fun crearAdministrador() {
        val actual = _estado.value
        if (actual.ocupado) return
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true, error = null) }
            val resultado = autenticacion.crearPrimerAdministrador(
                nombre = actual.nombre,
                usuario = actual.usuario,
                contrasena = actual.contrasena,
                confirmacion = actual.confirmacion,
            )
            when (resultado) {
                is Resultado.Exito -> _estado.update {
                    it.copy(ocupado = false, contrasena = "", confirmacion = "", hayCuentas = true)
                }

                is Resultado.Fallo -> _estado.update { it.copy(ocupado = false, error = resultado.mensaje) }
            }
        }
    }

    /** Ingreso con usuario y contraseña */
    fun entrar(activarBiometria: Boolean) {
        val actual = _estado.value
        if (actual.ocupado) return
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true, error = null) }
            when (val resultado = autenticacion.entrar(
                usuario = actual.usuario,
                contrasena = actual.contrasena,
                activarBiometria = activarBiometria,
            )) {
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
