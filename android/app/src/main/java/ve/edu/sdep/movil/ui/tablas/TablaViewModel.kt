package ve.edu.sdep.movil.ui.tablas

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.local.EsquemaTabla
import ve.edu.sdep.movil.datos.repositorio.SesionRepositorio
import ve.edu.sdep.movil.datos.repositorio.TablaRepositorio
import ve.edu.sdep.movil.dominio.modelo.Permiso
import javax.inject.Inject

/**
 * Lista genérica de una tabla sin pantalla propia (períodos, grados,
 * matrículas). Lee las filas del espejo y las resume con las columnas
 * descriptivas que tenga la tabla, sin conocer su estructura.
 */
@HiltViewModel
class TablaViewModel @Inject constructor(
    private val repositorio: TablaRepositorio,
    private val sesionRepositorio: SesionRepositorio,
) : ViewModel() {

    data class Fila(val id: Long, val titulo: String, val subtitulo: String)

    data class Estado(
        val tabla: String = "",
        val titulo: String = "",
        val filas: List<Fila> = emptyList(),
        val cargando: Boolean = true,
        val puedeCrear: Boolean = false,
        val noDisponible: String? = null,
    )

    private val _estado = MutableStateFlow(Estado())
    val estado: StateFlow<Estado> = _estado.asStateFlow()

    private var tablaActual: String? = null

    fun cargar(tabla: String, forzar: Boolean = false) {
        if (!forzar && tablaActual == tabla && _estado.value.filas.isNotEmpty()) return
        tablaActual = tabla
        viewModelScope.launch {
            _estado.update {
                it.copy(tabla = tabla, titulo = EsquemaTabla.titulo(tabla), cargando = true)
            }
            val sesion = sesionRepositorio.actual
            val modulo = EsquemaTabla.moduloDeTabla(tabla)
            if (sesion == null || modulo == null || !sesion.puedeAbrir(modulo)) {
                _estado.update {
                    it.copy(
                        cargando = false,
                        noDisponible = "Su rol no tiene acceso a este módulo.",
                    )
                }
                return@launch
            }
            val columnas = repositorio.columnas(tabla)
            val filas = repositorio.listar(tabla).map { valores -> resumir(valores, columnas) }
            _estado.update {
                it.copy(
                    filas = filas,
                    cargando = false,
                    puedeCrear = sesion.puede(Permiso.CREAR),
                    noDisponible = null,
                )
            }
        }
    }

    /** Título y subtítulo de una fila a partir de sus columnas descriptivas */
    private fun resumir(
        valores: Map<String, String?>,
        columnas: List<ve.edu.sdep.movil.datos.local.ColumnaTabla>,
    ): Fila {
        val disponibles = columnas.map { it.nombre }.filter { nombre ->
            !valores[nombre].isNullOrBlank()
        }
        val id = valores["id"]?.toLongOrNull() ?: 0L
        val titulo = TITULO.mapNotNull { nombre ->
            if (nombre in disponibles) valores[nombre] else null
        }.joinToString(" ").trim().ifEmpty { "Registro #$id" }
        val subtitulo = SUBTITULO.firstNotNullOfOrNull { nombre ->
            if (nombre in disponibles) valores[nombre] else null
        }.orEmpty()
        return Fila(id = id, titulo = titulo, subtitulo = subtitulo)
    }

    private companion object {
        val TITULO = listOf("nombres", "apellidos", "titulo", "nombre", "numero", "materia")
        val SUBTITULO = listOf(
            "cedula", "cargo", "estado", "fecha_inicio", "fecha_matricula",
            "periodo_inicio", "descripcion", "numero",
        )
    }
}
