package ve.edu.sdep.movil.ui.documentos

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity
import ve.edu.sdep.movil.datos.repositorio.DocumentosRepositorio
import ve.edu.sdep.movil.datos.repositorio.DocumentosRepositorio.PdfListo
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

/** Plantillas breves compatibles con los campos del procesador Markdown del servidor. */
val PLANTILLAS_CONSTANCIA = listOf(
    "Constancia de trabajo" to """# Constancia de trabajo

Se hace constar que **{{nombre_completo}}**, titular de la cédula **{{cedula}}**, presta servicios en {{institucion}} como {{cargo}}, adscrito(a) a {{departamento}}, desde {{fecha_contratacion}}.

Se expide a solicitud de la persona interesada, en fecha {{fecha_emision}}.""",
    "Constancia de ingresos" to """# Constancia laboral

{{institucion}} certifica que **{{nombre}}**, cédula **{{cedula}}**, desempeña el cargo de {{cargo}} en el departamento de {{departamento}}, con un salario mensual de **{{salario}}**.

La presente se expide en fecha {{fecha_emision}} para los fines que estime convenientes.""",
    "Constancia de antigüedad" to """# Constancia de antigüedad

Se certifica que **{{nombre_completo}}**, cédula **{{cedula}}**, labora como {{cargo}} en {{institucion}} desde {{fecha_contratacion}}.

Expedida el {{fecha_emision}}.""",
)

data class EstadoHerramientasPdf(
    val empleados: List<EmpleadoEntity> = emptyList(),
    val empleadoId: Long? = null,
    val plantillaIndice: Int = 0,
    val markdown: String = PLANTILLAS_CONSTANCIA.first().second,
    val pdf: PdfListo? = null,
    val cargando: Boolean = false,
    val mensaje: String? = null,
)

@HiltViewModel
class HerramientasPdfViewModel @Inject constructor(
    private val repositorio: DocumentosRepositorio,
) : ViewModel() {
    private val _estado = MutableStateFlow(EstadoHerramientasPdf())
    val estado: StateFlow<EstadoHerramientasPdf> = _estado.asStateFlow()

    private fun cargarEmpleados(cedula: String?, esTrabajador: Boolean) = viewModelScope.launch {
        val empleados = if (esTrabajador) {
            repositorio.empleadoVisiblePorCedula(cedula.orEmpty())?.let(::listOf).orEmpty()
        } else {
            repositorio.empleadosVisibles()
        }
        _estado.update { actual ->
            actual.copy(empleados = empleados, empleadoId = actual.empleadoId?.takeIf { id ->
                empleados.any { it.id == id }
            } ?: empleados.firstOrNull()?.id)
        }
    }

    fun seleccionarEmpleado(id: Long) = _estado.update {
        it.copy(empleadoId = id, pdf = null, mensaje = null)
    }

    fun seleccionarPlantilla(indice: Int) {
        val plantilla = PLANTILLAS_CONSTANCIA.getOrNull(indice) ?: return
        _estado.update { it.copy(plantillaIndice = indice, markdown = plantilla.second, mensaje = null) }
    }

    fun cambiarMarkdown(texto: String) = _estado.update { it.copy(markdown = texto, mensaje = null) }

    fun constancia(
        personalizada: Boolean,
        titulo: String = PLANTILLAS_CONSTANCIA.getOrNull(_estado.value.plantillaIndice)?.first ?: "Constancia de trabajo",
    ) = ejecutar {
        val id = empleadoSeleccionado() ?: error("Seleccione un empleado.")
        val markdown = _estado.value.markdown
        require(markdown.toByteArray(Charsets.UTF_8).size <= 65_536) {
            "La plantilla Markdown supera 64 KB."
        }
        repositorio.constancia(id, markdown, personalizada, titulo)
    }

    fun ficha() = ejecutar {
        val id = empleadoSeleccionado() ?: error("Seleccione un empleado.")
        repositorio.fichaPdf(id)
    }

    fun reporte(tipo: String, periodoInicio: String? = null, periodoFin: String? = null) = ejecutar {
        repositorio.reporte(tipo, periodoInicio, periodoFin)
    }

    fun subir(nombre: String, titulo: String, bytes: ByteArray) = ejecutar {
        val id = empleadoSeleccionado() ?: error("Seleccione un empleado.")
        repositorio.subirPdf(id, nombre, titulo, bytes)
    }

    fun limpiarPdf() = _estado.update { it.copy(pdf = null) }

    private fun empleadoSeleccionado(): Long? = _estado.value.empleadoId

    fun actualizarSesion(cedula: String?, esTrabajador: Boolean) {
        cargarEmpleados(cedula, esTrabajador)
    }

    private fun ejecutar(accion: suspend () -> Resultado<PdfListo>) {
        if (_estado.value.cargando) return
        viewModelScope.launch {
            _estado.update { it.copy(cargando = true, mensaje = null, pdf = null) }
            val resultado = try {
                accion()
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (error: Exception) {
                Resultado.Fallo(error.message ?: "No se pudo completar la operación.", error)
            }
            when (resultado) {
                is Resultado.Exito -> _estado.update {
                    it.copy(cargando = false, pdf = resultado.valor, mensaje = "PDF listo: ${resultado.valor.nombre}")
                }
                is Resultado.Fallo -> _estado.update {
                    it.copy(cargando = false, mensaje = resultado.mensaje)
                }
            }
        }
    }
}
