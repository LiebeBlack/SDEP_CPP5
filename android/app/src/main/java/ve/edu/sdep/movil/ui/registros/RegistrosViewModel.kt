package ve.edu.sdep.movil.ui.registros

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.repositorio.RegistroRepositorio
import ve.edu.sdep.movil.datos.repositorio.SincronizacionRepositorio
import ve.edu.sdep.movil.dominio.modelo.Registro
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

data class EstadoLista(
    val registros: List<Registro> = emptyList(),
    val categorias: List<String> = emptyList(),
    val filtro: String = "",
    val categoriaSeleccionada: String = "",
    val cargando: Boolean = true,
)

data class Contadores(
    val pendientes: Int = 0,
    val ultimaSync: Long? = null,
    val ultimoError: String? = null,
)

@HiltViewModel
class RegistrosViewModel @Inject constructor(
    private val repositorio: RegistroRepositorio,
    private val sincronizacion: SincronizacionRepositorio,
    operacionDao: OperacionDao,
) : ViewModel() {

    private val consulta = MutableStateFlow("")
    private val categoria = MutableStateFlow("")

    val estado: StateFlow<EstadoLista> = combine(
        repositorio.observarActivos(),
        consulta,
        categoria,
    ) { registros, texto, seleccionada ->
        val filtrados = registros.filter { registro ->
            val coincideTexto = texto.isBlank() ||
                registro.titulo.contains(texto, ignoreCase = true) ||
                registro.contenido.contains(texto, ignoreCase = true)
            val coincideCategoria = seleccionada.isBlank() || registro.categoria == seleccionada
            coincideTexto && coincideCategoria
        }
        EstadoLista(
            registros = filtrados,
            categorias = registros.map { it.categoria }.distinct().sorted(),
            filtro = texto,
            categoriaSeleccionada = seleccionada,
            cargando = false,
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = EstadoLista(),
    )

    val contadores: StateFlow<Contadores> = combine(
        operacionDao.observarPendientes(),
        sincronizacion.observarEstado(),
    ) { pendientes, estadoSync ->
        Contadores(
            pendientes = pendientes,
            ultimaSync = estadoSync?.ultimaSync,
            ultimoError = estadoSync?.ultimoError,
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = Contadores(),
    )

    private val _sincronizando = MutableStateFlow(false)
    val sincronizando: StateFlow<Boolean> = _sincronizando.asStateFlow()

    private val _mensaje = MutableStateFlow<String?>(null)
    val mensaje: StateFlow<String?> = _mensaje.asStateFlow()

    fun buscar(texto: String) {
        consulta.value = texto
    }

    fun filtrarCategoria(valor: String) {
        categoria.value = if (categoria.value == valor) "" else valor
    }

    fun sincronizarAhora() {
        if (_sincronizando.value) return
        viewModelScope.launch {
            _sincronizando.value = true
            when (val resultado = sincronizacion.sincronizar()) {
                is Resultado.Exito -> {
                    val resumen = resultado.valor
                    _mensaje.value = if (resumen.enviadas == 0 && resumen.recibidas == 0) {
                        "Todo al día: no hay cambios pendientes."
                    } else {
                        "Enviados ${resumen.enviadas} y recibidos ${resumen.recibidas} cambios."
                    }
                }

                is Resultado.Fallo -> _mensaje.value = resultado.mensaje
            }
            _sincronizando.value = false
        }
    }

    fun limpiarMensaje() {
        _mensaje.value = null
    }
}
