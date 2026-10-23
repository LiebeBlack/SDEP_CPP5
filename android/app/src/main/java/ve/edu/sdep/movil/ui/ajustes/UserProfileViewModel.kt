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
import ve.edu.sdep.movil.datos.repositorio.AutenticacionRepositorio
import ve.edu.sdep.movil.datos.remoto.ActualizarPerfilDto
import ve.edu.sdep.movil.datos.remoto.PerfilDto
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

/**
 * Estado del perfil propio del usuario.
 *
 * Permite ver y editar nombre completo, cédula (obligatorio para rol
 * trabajador) y visualizar rol y estado de la cuenta.
 */
data class EstadoPerfil(
    val cargando: Boolean = false,
    val perfil: PerfilDto? = null,
    val editando: Boolean = false,
    val ocupado: Boolean = false,
    val mensaje: String? = null,
    val esError: Boolean = false,
    val perfilGuardado: Boolean = false,
)

@HiltViewModel
class UserProfileViewModel @Inject constructor(
    private val autenticacion: AutenticacionRepositorio,
) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoPerfil())
    val estado: StateFlow<EstadoPerfil> = _estado.asStateFlow()

    /**
     * Carga el perfil del usuario autenticado desde el nodo central.
     */
    fun cargarPerfil() {
        viewModelScope.launch {
            _estado.update { it.copy(cargando = true, mensaje = null, esError = false) }
            when (val resultado = autenticacion.obtenerPerfil()) {
                is Resultado.Exito -> _estado.update {
                    it.copy(
                        cargando = false,
                        perfil = resultado.valor,
                        mensaje = null,
                        esError = false,
                    )
                }
                is Resultado.Fallo -> _estado.update {
                    it.copy(
                        cargando = false,
                        mensaje = resultado.mensaje,
                        esError = true,
                    )
                }
            }
        }
    }

    /**
     * Entra en modo edición del perfil.
     */
    fun iniciarEdicion() {
        _estado.update { it.copy(editando = true, mensaje = null, esError = false) }
    }

    /**
     * Cancela la edición y descarta cambios.
     */
    fun cancelarEdicion() {
        _estado.update { it.copy(editando = false, mensaje = null, esError = false) }
    }

    /**
     * Guarda los cambios del perfil (nombre completo y cédula).
     */
    fun guardarPerfil(nombreCompleto: String?, cedula: String?) {
        if (_estado.value.ocupado) return
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true, mensaje = null, esError = false) }
            val dto = ActualizarPerfilDto(
                nombre_completo = nombreCompleto?.trim()?.takeIf { it.isNotEmpty() },
                cedula = cedula?.trim()?.takeIf { it.isNotEmpty() },
            )
            when (val resultado = autenticacion.actualizarPerfil(dto)) {
                is Resultado.Exito -> _estado.update {
                    it.copy(
                        ocupado = false,
                        editando = false,
                        perfil = resultado.valor,
                        perfilGuardado = true,
                        mensaje = "Perfil actualizado correctamente.",
                        esError = false,
                    )
                }
                is Resultado.Fallo -> _estado.update {
                    it.copy(
                        ocupado = false,
                        mensaje = resultado.mensaje,
                        esError = true,
                    )
                }
            }
        }
    }

    fun limpiarMensaje() = _estado.update { it.copy(mensaje = null) }

    companion object {
        /** Mensaje de error cuando la cédula es obligatoria para el rol trabajador */
        const val CEDULA_OBLIGATORIA = "La cédula es obligatoria para cuentas de trabajador."
    }
}
