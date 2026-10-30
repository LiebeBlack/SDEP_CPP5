package ve.edu.sdep.movil.ui.documentos

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity
import ve.edu.sdep.movil.datos.repositorio.DocumentosRepositorio
import ve.edu.sdep.movil.datos.repositorio.DocumentosRepositorio.PdfListo
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

/**
 * Plantillas listas para usar: una sola hoja, campos ya soportados por el
 * procesador (teléfono y nodo) y sin texto que el usuario deba completar a mano.
 */
val PLANTILLAS_CONSTANCIA = listOf(
    "Constancia de trabajo" to """# Constancia de trabajo

Se hace constar que **{{nombre_completo}}**, titular de la cédula **{{cedula}}**, presta servicios en {{institucion}} como {{cargo}}, adscrito(a) a {{departamento}}, desde {{fecha_contratacion}}.

Se expide a solicitud de la persona interesada, en fecha {{fecha_emision}}.""",
    "Constancia de ingresos" to """# Constancia de ingresos

{{institucion}} certifica que **{{nombre}}**, cédula **{{cedula}}**, desempeña el cargo de {{cargo}} en el departamento de {{departamento}}, con un salario mensual de **{{salario}}**.

La presente se expide en fecha {{fecha_emision}} para los fines que estime convenientes.""",
    "Constancia de antigüedad" to """# Constancia de antigüedad

Se certifica que **{{nombre_completo}}**, cédula **{{cedula}}**, labora como {{cargo}} en {{institucion}} desde {{fecha_contratacion}}.

Expedida el {{fecha_emision}}.""",
    "Constancia de servicio" to """# Constancia de servicio

Quien suscribe hace constar que **{{nombre_completo}}**, cédula **{{cedula}}**, se desempeña como {{cargo}} en el departamento de {{departamento}} de {{institucion}}, con categoría {{tipo_empleado}}, desde {{fecha_contratacion}}.

Constancia expedida el {{fecha_emision}}.""",
    "Carta de referencia laboral" to """# Carta de referencia laboral

A quien pueda interesar:

Por medio de la presente hago constar que conozco a **{{nombre_completo}}**, cédula **{{cedula}}**, quien presta servicios en {{institucion}} como {{cargo}} desde {{fecha_contratacion}}.

Durante ese tiempo ha demostrado responsabilidad, puntualidad y compromiso con sus funciones en el departamento de {{departamento}}.

Se extiende la presente referencia en fecha {{fecha_emision}}.""",
    "Constancia simple" to """# Constancia

Se hace constar que **{{nombre_completo}}**, cédula **{{cedula}}**, forma parte del personal de {{institucion}} en el cargo de {{cargo}}.

Constancia expedida el {{fecha_emision}}.""",
    "Constancia con antigüedad" to """# Constancia de trabajo

Se hace constar que **{{nombre_completo}}**, titular de la cédula **{{cedula}}**, presta servicios en {{institucion}} como {{cargo}} en el departamento de {{departamento}} desde el {{fecha_contratacion}}, con una antigüedad de **{{antiguedad}}**.

Se expide a los {{dia_emision}} días del mes de {{mes_emision}} de {{anio_emision}}.""",
    "Constancia de ingresos con monto en letras" to """# Constancia de ingresos

{{institucion}} certifica que **{{nombre_completo}}**, cédula **{{cedula}}**, desempeña el cargo de {{cargo}} con una remuneración mensual de **{{salario}}** ({{salario_letras}}).

La presente se expide en fecha {{fecha_emision_larga}} para los fines que estime convenientes.""",
    "Constancia de datos personales" to """# Constancia de datos personales

Se certifica que los datos que siguen corresponden a **{{nombre_completo}}**, cédula **{{cedula}}**, personal de {{institucion}}:

- Fecha de nacimiento: {{fecha_nacimiento}} ({{edad}})
- Estado civil: {{estado_civil}}
- Nacionalidad: {{nacionalidad}}
- Cargo: {{cargo}} · Departamento: {{departamento}}
- Teléfono: {{telefono}} · Correo: {{correo}}
- Dirección: {{direccion}}, {{ciudad}}, estado {{estado}}

Se expide a solicitud de la persona interesada el {{fecha_emision}}.""",
)

/**
 * Frases preestablecidas para completar una constancia sin escribirla desde
 * cero: se insertan en el cursor igual que los campos.
 */
val FRAGMENTOS_CONSTANCIA = listOf(
    "A quien pueda interesar" to "A quien pueda interesar:\n\n",
    "Para trámite bancario" to "La presente se expide para los trámites bancarios que el interesado deba realizar.",
    "Para trámite consular" to "La presente se expide para los trámites consulares y migratorios que la persona interesada deba realizar.",
    "Fines laborales" to "Esta constancia se expide únicamente para fines laborales y no sustituye una certificación de ingresos.",
    "Solicitud del interesado" to "Se expide a solicitud de la persona interesada, quien la recibe en señal de conformidad.",
    "Uso reservado de datos" to "Se solicita dar a esta constancia el uso reservado que corresponde a los datos personales en ella contenidos.",
    "Cierre con lugar y fecha" to "Se expide en {{ciudad}}, a los {{dia_emision}} días del mes de {{mes_emision}} de {{anio_emision}}.",
    "Cierre simple" to "Constancia expedida el {{fecha_emision_larga}}, para los fines que estime convenientes.",
)

/** Campos que el motor de plantillas reconoce, con la etiqueta que ve el usuario. */
data class CampoConstancia(val clave: String, val etiqueta: String, val valor: String?)

val CAMPOS_CONSTANCIA = listOf(
    "nombre_completo" to "Nombre completo",
    "nombre" to "Nombre",
    "nombres" to "Nombres",
    "apellidos" to "Apellidos",
    "cedula" to "Cédula",
    "cargo" to "Cargo",
    "departamento" to "Departamento",
    "tipo_empleado" to "Categoría",
    "tipo_contratacion" to "Tipo de contratación",
    "salario" to "Salario",
    "salario_letras" to "Salario en letras",
    "fecha_contratacion" to "Fecha de ingreso",
    "antiguedad" to "Antigüedad",
    "fecha_emision" to "Fecha de emisión",
    "fecha_emision_larga" to "Fecha de emisión en palabras",
    "dia_emision" to "Día de emisión",
    "mes_emision" to "Mes de emisión",
    "anio_emision" to "Año de emisión",
    "institucion" to "Institución",
    "fecha_nacimiento" to "Fecha de nacimiento",
    "edad" to "Edad",
    "genero" to "Género",
    "estado_civil" to "Estado civil",
    "nacionalidad" to "Nacionalidad",
    "telefono" to "Teléfono",
    "celular" to "Celular",
    "correo" to "Correo",
    "direccion" to "Dirección",
    "ciudad" to "Ciudad",
    "estado" to "Estado",
    "nivel_educativo" to "Nivel educativo",
    "especialidad" to "Especialidad",
    "titulo_obtenido" to "Título obtenido",
)

private val CLAVES_CONSTANCIA = CAMPOS_CONSTANCIA.map { it.first }.toSet()
private val MARCADOR = Regex("""\{\{?\s*([^}\s]{1,40})\s*\}?\}""")

/** Título que sugiere la propia plantilla: su primer encabezado. */
fun tituloDesdeMarkdown(markdown: String): String? = markdown.lineSequence()
    .map { it.trim() }
    .firstOrNull { it.startsWith("#") }
    ?.trimStart('#')
    ?.trim()
    ?.takeIf { it.isNotEmpty() }
    ?.take(120)

/** Claves válidas que la plantilla realmente usa, en orden de aparición. */
fun clavesUsadas(markdown: String): List<String> = MARCADOR.findAll(markdown)
    .map { it.groupValues[1] }
    .filter { it in CLAVES_CONSTANCIA }
    .distinct()
    .toList()

/**
 * Marcadores que el motor no va a sustituir tal como están escritos: incluye
 * los inventados y los que solo fallan por mayúsculas o acentos.
 */
fun clavesInvalidas(markdown: String): List<String> = MARCADOR.findAll(markdown)
    .map { it.groupValues[1] }
    .filter { it !in CLAVES_CONSTANCIA }
    .distinct()
    .toList()

/**
 * Reescribe los marcadores reconocibles a su forma exacta: `{{Cédula}}`,
 * `{{cedula }}` o `{{CÉDULA}}` pasan a `{{cedula}}`, que es lo que entienden
 * el teléfono y el nodo. Lo irreconocible se deja intacto.
 */
fun corregirCampos(markdown: String): String = MARCADOR.replace(markdown) { coincidencia ->
    val normalizada = normalizarClave(coincidencia.groupValues[1])
    if (normalizada in CLAVES_CONSTANCIA) "{{$normalizada}}" else coincidencia.value
}

/** Quita acentos, mayúsculas y separadores: «Cédula» y «CÉDULA» → «cedula». */
private fun normalizarClave(clave: String): String {
    val sinAcentos = java.text.Normalizer
        .normalize(clave.trim().lowercase(), java.text.Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"), "")
    return sinAcentos.replace(Regex("[^a-z0-9_]+"), "_").trim('_')
}

data class EstadoHerramientasPdf(
    val empleados: List<EmpleadoEntity> = emptyList(),
    val empleadoId: Long? = null,
    val campos: List<CampoConstancia> = emptyList(),
    val plantillaIndice: Int = 0,
    val markdown: String = PLANTILLAS_CONSTANCIA.first().second,
    val pdf: PdfListo? = null,
    val cargando: Boolean = false,
    val cargandoEmpleados: Boolean = false,
    val mensaje: String? = null,
)

@HiltViewModel
class HerramientasPdfViewModel @Inject constructor(
    private val repositorio: DocumentosRepositorio,
) : ViewModel() {
    private val _estado = MutableStateFlow(EstadoHerramientasPdf())
    val estado: StateFlow<EstadoHerramientasPdf> = _estado.asStateFlow()
    private var solicitudEmpleados = 0
    private var claveSesion: String? = null
    private var accionJob: Job? = null
    private var camposJob: Job? = null

    private fun cargarEmpleados(cedula: String?, esTrabajador: Boolean) {
        val solicitud = ++solicitudEmpleados
        _estado.update {
            it.copy(
                empleados = emptyList(), empleadoId = null, pdf = null,
                cargandoEmpleados = true, mensaje = null,
            )
        }
        viewModelScope.launch {
            val empleados = try {
                if (esTrabajador) {
                    repositorio.empleadoVisiblePorCedula(cedula.orEmpty())?.let(::listOf).orEmpty()
                } else {
                    repositorio.empleadosVisibles()
                }
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (error: Exception) {
                if (solicitud == solicitudEmpleados) {
                    _estado.update {
                        it.copy(cargandoEmpleados = false, mensaje = error.message ?: "No se pudieron cargar los empleados.")
                    }
                }
                return@launch
            }
            if (solicitud != solicitudEmpleados) return@launch
            _estado.update { actual ->
                actual.copy(
                    empleados = empleados,
                    empleadoId = actual.empleadoId?.takeIf { id -> empleados.any { it.id == id } }
                        ?: empleados.firstOrNull()?.id,
                    cargandoEmpleados = false,
                )
            }
            cargarCampos(_estado.value.empleadoId)
        }
    }

    fun seleccionarEmpleado(id: Long) {
        _estado.update { it.copy(empleadoId = id, pdf = null, mensaje = null) }
        cargarCampos(id)
    }

    /** Resuelve los datos reales de la ficha para mostrarlos junto a la plantilla. */
    private fun cargarCampos(id: Long?) {
        camposJob?.cancel()
        if (id == null) {
            _estado.update { it.copy(campos = emptyList()) }
            return
        }
        camposJob = viewModelScope.launch {
            val datos = try {
                repositorio.datosConstancia(id)
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (_: Exception) {
                emptyMap()
            }
            _estado.update { actual ->
                if (actual.empleadoId != id) {
                    actual
                } else {
                    actual.copy(
                        campos = CAMPOS_CONSTANCIA.map { (clave, etiqueta) ->
                            CampoConstancia(clave, etiqueta, datos[clave]?.takeIf { it.isNotBlank() })
                        },
                    )
                }
            }
        }
    }

    fun seleccionarPlantilla(indice: Int) {
        if (indice == -1) {
            _estado.update { it.copy(plantillaIndice = -1, mensaje = null) }
            return
        }
        val plantilla = PLANTILLAS_CONSTANCIA.getOrNull(indice) ?: return
        _estado.update { it.copy(plantillaIndice = indice, markdown = plantilla.second, mensaje = null) }
    }

    fun cambiarMarkdown(texto: String) {
        if (texto.toByteArray(Charsets.UTF_8).size > 65_536) return
        _estado.update { it.copy(plantillaIndice = -1, markdown = texto, mensaje = null) }
    }

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

    /** Compone la constancia en el teléfono: sin red y sin ida y vuelta al nodo. */
    fun constanciaLocal(
        personalizada: Boolean,
        titulo: String = PLANTILLAS_CONSTANCIA.getOrNull(_estado.value.plantillaIndice)?.first ?: "Constancia de trabajo",
    ) = ejecutar {
        val id = empleadoSeleccionado() ?: error("Seleccione un empleado.")
        val markdown = _estado.value.markdown
        repositorio.constanciaLocal(id, markdown, personalizada, titulo)
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

    fun errorSeleccionArchivo(mensaje: String) {
        _estado.update { it.copy(mensaje = mensaje) }
    }

    private fun empleadoSeleccionado(): Long? = _estado.value.empleadoId

    fun actualizarSesion(usuario: String, rol: String, cedula: String?, esTrabajador: Boolean) {
        val nuevaClave = "$usuario|$rol|${cedula.orEmpty()}|$esTrabajador"
        if (nuevaClave == claveSesion) return
        claveSesion = nuevaClave
        accionJob?.cancel()
        accionJob = null
        _estado.update {
            it.copy(
                cargando = false,
                pdf = null,
                mensaje = null,
                campos = emptyList(),
                plantillaIndice = 0,
                markdown = PLANTILLAS_CONSTANCIA.first().second,
            )
        }
        cargarEmpleados(cedula, esTrabajador)
    }

    private fun ejecutar(accion: suspend () -> Resultado<PdfListo>) {
        if (_estado.value.cargando) return
        _estado.update { it.copy(cargando = true, mensaje = null, pdf = null) }
        accionJob = viewModelScope.launch {
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
