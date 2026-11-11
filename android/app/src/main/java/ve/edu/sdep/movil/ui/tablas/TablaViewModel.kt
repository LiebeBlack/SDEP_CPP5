package ve.edu.sdep.movil.ui.tablas

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.text.Normalizer
import java.util.Locale
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

    data class Fila(
        val id: Long,
        val titulo: String,
        val subtitulo: String,
        val detalles: List<Pair<String, String>> = emptyList(),
    )

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
    private var carga: Job? = null
    private var generacionCarga = 0

    /** Búsqueda local sin distinguir mayúsculas ni acentos en todos los datos visibles. */
    fun buscar(filas: List<Fila>, consulta: String): List<Fila> {
        val termino = normalizarBusqueda(consulta.trim())
        if (termino.isEmpty()) return filas
        return filas.filter { fila ->
            sequenceOf(fila.titulo, fila.subtitulo)
                .plus(fila.detalles.asSequence().flatMap { sequenceOf(it.first, it.second) })
                .any { normalizarBusqueda(it).contains(termino) }
        }
    }

    fun cargar(tabla: String, forzar: Boolean = false) {
        if (!forzar && tablaActual == tabla && _estado.value.filas.isNotEmpty()) return
        tablaActual = tabla
        val solicitud = ++generacionCarga
        carga?.cancel()
        carga = viewModelScope.launch {
            _estado.update {
                it.copy(
                    tabla = tabla,
                    titulo = EsquemaTabla.titulo(tabla),
                    cargando = true,
                    noDisponible = null,
                )
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
            val filas = try {
                val columnas = repositorio.columnas(tabla)
                repositorio.listar(tabla).map { valores -> resumir(tabla, valores, columnas) }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                if (solicitud == generacionCarga) {
                    _estado.update {
                        it.copy(
                            cargando = false,
                            noDisponible = "No se pudo leer la tabla en este teléfono. " +
                                "Vuelva a intentarlo tras la próxima sincronización.",
                        )
                    }
                }
                return@launch
            }
            if (solicitud != generacionCarga) return@launch
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

    /** Resumen descriptivo que respeta las columnas de cada tabla. */
    private fun resumir(
        tabla: String,
        valores: Map<String, String?>,
        columnas: List<ve.edu.sdep.movil.datos.local.ColumnaTabla>,
    ): Fila {
        val id = valores["id"]?.toLongOrNull() ?: 0L
        val tituloCampos = when (tabla) {
            "grados" -> listOf("nombre", "seccion")
            "periodos_academicos" -> listOf("nombre")
            "matriculas" -> listOf("estudiante_id", "grado_id")
            else -> listOf("nombres", "apellidos", "titulo", "numero", "materia")
        }
        val etiquetas = columnas.associate { it.nombre to it.etiqueta }
        val titulo = tituloCampos.mapNotNull { nombre ->
            val valor = valores[nombre]?.trim()?.takeIf(String::isNotEmpty) ?: return@mapNotNull null
            if (tabla == "matriculas") "${etiquetas[nombre] ?: nombre}: $valor" else valor
        }.joinToString(" · ").ifBlank { "Registro #$id" }
        val resumenCampos = when (tabla) {
            "grados" -> listOf("nivel", "periodo_id", "profesor_id")
            "periodos_academicos" -> listOf("fecha_inicio", "fecha_fin", "estado")
            "matriculas" -> listOf("fecha_matricula", "activa", "observaciones")
            else -> listOf("cedula", "cargo", "estado", "fecha_inicio", "fecha_matricula")
        }
        val disponibles = resumenCampos.mapNotNull { campo ->
            valores[campo]?.trim()?.takeIf(String::isNotEmpty)?.let { valor ->
                etiquetas[campo]?.let { etiqueta -> etiqueta to valor }
            }
        }
        val camposConsumidos = tituloCampos + resumenCampos
        val sensibles = setOf(
            "numero_cuenta", "enfermedades_preexistentes", "alergias_medicamentosas",
            "alergias_alimentarias", "carnet_discapacidad", "password_hash",
        )
        val detalles = columnas.asSequence()
            .filter { it.nombre !in camposConsumidos && it.nombre !in sensibles }
            .mapNotNull { columna ->
                valores[columna.nombre]?.trim()?.takeIf(String::isNotEmpty)
                    ?.let { columna.etiqueta to it }
            }
            .take(3)
            .toList()
        return Fila(
            id = id,
            titulo = titulo,
            subtitulo = disponibles.firstOrNull()?.let { (etiqueta, valor) -> "$etiqueta: $valor" }.orEmpty(),
            detalles = (disponibles.drop(1) + detalles).take(4),
        )
    }

    private fun normalizarBusqueda(texto: String): String = Normalizer
        .normalize(texto, Normalizer.Form.NFD)
        .replace(Regex("\\p{Mn}+"), "")
        .lowercase(Locale.ROOT)
}
