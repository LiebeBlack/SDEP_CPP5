package ve.edu.sdep.movil.ui.registros

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.repositorio.RegistroRepositorio
import ve.edu.sdep.movil.datos.repositorio.SesionRepositorio
import ve.edu.sdep.movil.dominio.modelo.EstadoSincronizacion
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

data class EstadoEditor(
    val cargando: Boolean = true,
    val esNuevo: Boolean = true,
    val titulo: String = "",
    val contenido: String = "",
    val categoria: String = "",
    val valor: String = "",
    val guardando: Boolean = false,
    val puedeEditar: Boolean = true,
    val puedeEliminar: Boolean = false,
    val actualizadoEn: Long? = null,
    val estadoSync: EstadoSincronizacion? = null,
)

sealed interface EventoEditor {
    data object Guardado : EventoEditor
    data object Eliminado : EventoEditor
    data class Error(val mensaje: String) : EventoEditor
}

@HiltViewModel
class EditorViewModel @Inject constructor(
    private val repositorio: RegistroRepositorio,
    sesionRepositorio: SesionRepositorio,
    savedStateHandle: SavedStateHandle,
) : ViewModel() {

    private val uuid: String? = savedStateHandle.get<String>("uuid")?.takeIf { it.isNotBlank() }
    private val sesion = sesionRepositorio.actual

    private val _estado = MutableStateFlow(
        EstadoEditor(
            cargando = uuid != null,
            esNuevo = uuid == null,
            puedeEditar = sesion?.puede(Permiso.CREAR) == true,
            puedeEliminar = sesion?.puede(Permiso.ELIMINAR) == true,
        ),
    )
    val estado: StateFlow<EstadoEditor> = _estado.asStateFlow()

    private val _eventos = MutableSharedFlow<EventoEditor>(extraBufferCapacity = 2)
    val eventos: SharedFlow<EventoEditor> = _eventos.asSharedFlow()

    init {
        if (uuid == null) {
            _estado.update { it.copy(cargando = false) }
        } else {
            viewModelScope.launch {
                val registro = repositorio.buscar(uuid)
                if (registro == null) {
                    _estado.update { it.copy(cargando = false) }
                    _eventos.emit(EventoEditor.Error("El registro ya no existe en este equipo."))
                } else {
                    _estado.update {
                        it.copy(
                            cargando = false,
                            titulo = registro.titulo,
                            contenido = registro.contenido,
                            categoria = registro.categoria,
                            valor = registro.valorTexto,
                            actualizadoEn = registro.actualizadoEn,
                            estadoSync = registro.estado,
                        )
                    }
                }
            }
        }
    }

    fun cambiarTitulo(valor: String) = _estado.update { it.copy(titulo = valor) }

    fun cambiarContenido(valor: String) = _estado.update { it.copy(contenido = valor) }

    fun cambiarCategoria(valor: String) = _estado.update { it.copy(categoria = valor) }

    fun cambiarValor(valor: String) = _estado.update { it.copy(valor = valor) }

    fun guardar() {
        val actual = _estado.value
        if (actual.guardando) return

        viewModelScope.launch {
            _estado.update { it.copy(guardando = true) }
            val numero = actual.valor.trim()
                .replace(',', '.')
                .takeIf { it.isNotEmpty() }
                ?.toDoubleOrNull()

            if (actual.valor.isNotBlank() && numero == null) {
                _estado.update { it.copy(guardando = false) }
                _eventos.emit(
                    EventoEditor.Error("El valor debe ser un número. Use el punto como separador decimal."),
                )
                return@launch
            }

            when (
                val resultado = repositorio.guardar(
                    uuid = uuid,
                    titulo = actual.titulo,
                    contenido = actual.contenido,
                    categoria = actual.categoria,
                    valor = numero,
                )
            ) {
                is Resultado.Exito -> {
                    _estado.update { it.copy(guardando = false) }
                    _eventos.emit(EventoEditor.Guardado)
                }

                is Resultado.Fallo -> {
                    _estado.update { it.copy(guardando = false) }
                    _eventos.emit(EventoEditor.Error(resultado.mensaje))
                }
            }
        }
    }

    fun eliminar() {
        val identidad = uuid ?: return
        if (!_estado.value.puedeEliminar) {
            viewModelScope.launch {
                _eventos.emit(EventoEditor.Error("Su rol no permite eliminar registros."))
            }
            return
        }
        viewModelScope.launch {
            _estado.update { it.copy(guardando = true) }
            when (val resultado = repositorio.eliminar(identidad)) {
                is Resultado.Exito -> {
                    _estado.update { it.copy(guardando = false) }
                    _eventos.emit(EventoEditor.Eliminado)
                }

                is Resultado.Fallo -> {
                    _estado.update { it.copy(guardando = false) }
                    _eventos.emit(EventoEditor.Error(resultado.mensaje))
                }
            }
        }
    }
}
