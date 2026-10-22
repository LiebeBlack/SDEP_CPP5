package ve.edu.sdep.movil.ui.modulos

import ve.edu.sdep.movil.datos.local.entidad.ContratoEntity
import ve.edu.sdep.movil.datos.local.entidad.DocumentoEntity
import ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity
import ve.edu.sdep.movil.datos.local.entidad.EstudianteEntity
import ve.edu.sdep.movil.datos.local.entidad.GradoEntity
import ve.edu.sdep.movil.datos.local.entidad.IncidenciaEntity
import ve.edu.sdep.movil.datos.local.entidad.MatriculaEntity
import ve.edu.sdep.movil.datos.local.entidad.NotaFinalEntity
import ve.edu.sdep.movil.datos.local.entidad.PagoEntity
import ve.edu.sdep.movil.datos.local.entidad.PeriodoAcademicoEntity
import ve.edu.sdep.movil.datos.local.entidad.ConfiguracionEntity
import ve.edu.sdep.movil.dominio.modelo.Modulo
import java.text.NumberFormat
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import java.util.Locale

/**
 * Vista de solo lectura del espejo local.
 *
 * El teléfono replica las mismas doce tablas que el escritorio, así que la
 * consulta no necesita red: se lee Room y se traduce a filas de lista y a
 * fichas de detalle con las mismas etiquetas que usa el escritorio.
 *
 * Este archivo no decide nada de negocio. Los importes, los estados y las
 * fechas que muestra son los que el nodo central ya calculó y replicó; el
 * teléfono no reimplementa fórmulas de nómina ni reglas de contratación. Por
 * eso esta entrega es de consulta: no hay botones que escriban.
 */

// ----------------------------------------------------------------------
// Modelo de presentación
// ----------------------------------------------------------------------

/** Intención visual de una etiqueta de estado */
enum class Tono { NEUTRO, EXITO, ALERTA, ERROR }

/** Una fila de lista: lo mínimo para reconocer un registro de un vistazo */
data class FilaCatalogo(
    val id: Long,
    val titulo: String,
    val subtitulo: String = "",
    val nota: String? = null,
    val etiqueta: String? = null,
    val tono: Tono = Tono.NEUTRO,
)

/** Un par etiqueta/valor de una ficha */
data class CampoFicha(val etiqueta: String, val valor: String)

/** Un bloque de la ficha; puede traer campos, un párrafo o ambos */
data class SeccionFicha(
    val titulo: String,
    val campos: List<CampoFicha> = emptyList(),
    val parrafo: String? = null,
)

/** Detalle completo de una fila */
data class FichaCatalogo(
    val titulo: String,
    val subtitulo: String? = null,
    val secciones: List<SeccionFicha> = emptyList(),
)

/** Indicador del panel de control */
data class IndicadorPanel(
    val etiqueta: String,
    val valor: String,
    val tono: Tono = Tono.NEUTRO,
)

/** Aviso del panel que lleva a la ficha que lo origina */
data class AlertaPanel(
    val modulo: Modulo,
    val fila: FilaCatalogo,
)

/** Copia de las tablas replicadas en el instante en que se pintó la pantalla */
data class Datos(
    val empleados: List<EmpleadoEntity> = emptyList(),
    val documentos: List<DocumentoEntity> = emptyList(),
    val incidencias: List<IncidenciaEntity> = emptyList(),
    val contratos: List<ContratoEntity> = emptyList(),
    val pagos: List<PagoEntity> = emptyList(),
    val estudiantes: List<EstudianteEntity> = emptyList(),
    val periodos: List<PeriodoAcademicoEntity> = emptyList(),
    val grados: List<GradoEntity> = emptyList(),
    val matriculas: List<MatriculaEntity> = emptyList(),
    val notas: List<NotaFinalEntity> = emptyList(),
    val configuraciones: List<ConfiguracionEntity> = emptyList(),
)

// ----------------------------------------------------------------------
// Catálogo
// ----------------------------------------------------------------------

class Catalogo(val datos: Datos) {

    private val empleadosPorId: Map<Long, EmpleadoEntity> = datos.empleados.associateBy { it.id }
    private val estudiantesPorId: Map<Long, EstudianteEntity> =
        datos.estudiantes.associateBy { it.id }
    private val gradosPorId: Map<Long, GradoEntity> = datos.grados.associateBy { it.id }
    private val periodosPorId: Map<Long, PeriodoAcademicoEntity> =
        datos.periodos.associateBy { it.id }

    // ---- Nombres resueltos ---------------------------------------------

    private fun nombreEmpleado(id: Long): String =
        empleadosPorId[id]?.nombreCompleto ?: "Empleado n.º $id"

    private fun nombreEstudiante(id: Long): String =
        estudiantesPorId[id]?.nombreCompleto ?: "Estudiante n.º $id"

    private fun nombreGrado(id: Long): String =
        gradosPorId[id]?.nombreCompleto ?: "Grado n.º $id"

    private fun nombrePeriodo(id: Long): String =
        periodosPorId[id]?.nombre ?: "Período n.º $id"

    // ---- Listas ---------------------------------------------------------

    /**
     * Filas de la lista de un módulo, ya ordenadas como en el escritorio.
     *
     * [Modulo.REGISTROS] no pasa por aquí: tiene su propia pantalla, y
     * [Modulo.DASHBOARD] se pinta con [indicadores] y [alertas].
     */
    fun filas(modulo: Modulo): List<FilaCatalogo> = when (modulo) {
        Modulo.DASHBOARD, Modulo.REGISTROS -> emptyList()
        Modulo.EMPLEADOS -> datos.empleados
            .sortedWith(compareBy({ it.apellidos.lowercase() }, { it.nombres.lowercase() }))
            .map { empleado ->
                FilaCatalogo(
                    id = empleado.id,
                    titulo = empleado.nombreCompleto,
                    subtitulo = "${empleado.cedula} · ${empleado.cargo}",
                    nota = empleado.departamento,
                    etiqueta = if (empleado.activo != 0) "Activo" else "Inactivo",
                    tono = if (empleado.activo != 0) Tono.EXITO else Tono.NEUTRO,
                )
            }

        Modulo.DOCUMENTOS -> datos.documentos.map { documento ->
            val vencimiento = vencimientoDocumento(documento)
            FilaCatalogo(
                id = documento.id,
                titulo = documento.titulo,
                subtitulo = "${etiquetaEstado(documento.tipoDocumento)} · " +
                    nombreEmpleado(documento.empleadoId),
                nota = documento.fechaVencimiento?.let { "Vence el ${fecha(it)}" }
                    ?: "Sin vencimiento",
                etiqueta = vencimiento?.first,
                tono = vencimiento?.second ?: Tono.NEUTRO,
            )
        }

        Modulo.INCIDENCIAS -> datos.incidencias.map { incidencia ->
            FilaCatalogo(
                id = incidencia.id,
                titulo = etiquetaEstado(incidencia.tipoIncidencia),
                subtitulo = nombreEmpleado(incidencia.empleadoId),
                nota = "${fecha(incidencia.fechaInicio)} → ${fecha(incidencia.fechaFin)} · " +
                    "${incidencia.diasSolicitados} día(s)",
                etiqueta = etiquetaEstado(incidencia.estado),
                tono = tonoIncidencia(incidencia.estado),
            )
        }

        Modulo.CONTRATOS -> datos.contratos.map { contrato ->
            val porVencer = vencimientoContrato(contrato)
            FilaCatalogo(
                id = contrato.id,
                titulo = "${contrato.numero} · ${contrato.cargo}",
                subtitulo = nombreEmpleado(contrato.empleadoId),
                nota = "${bolivares(contrato.salarioPactado)} · desde el " +
                    fecha(contrato.fechaInicio),
                etiqueta = porVencer?.first ?: etiquetaEstado(contrato.estado),
                tono = porVencer?.second ?: tonoContrato(contrato.estado),
            )
        }

        Modulo.NOMINA -> datos.pagos.map { pago ->
            FilaCatalogo(
                id = pago.id,
                titulo = nombreEmpleado(pago.empleadoId),
                subtitulo = "${etiquetaEstado(pago.tipoPago)} · " +
                    "${fecha(pago.periodoInicio)} → ${fecha(pago.periodoFin)}",
                nota = "Neto ${bolivares(pago.montoNeto)}",
                etiqueta = if (pago.pagado != 0) "Pagado" else "Pendiente",
                tono = if (pago.pagado != 0) Tono.EXITO else Tono.ALERTA,
            )
        }

        Modulo.ESTUDIANTES -> datos.estudiantes
            .sortedWith(compareBy({ it.apellidos.lowercase() }, { it.nombres.lowercase() }))
            .map { estudiante ->
                FilaCatalogo(
                    id = estudiante.id,
                    titulo = estudiante.nombreCompleto,
                    subtitulo = listOfNotNull(
                        estudiante.cedula,
                        etiquetaEstado(estudiante.nivel),
                    ).joinToString(" · "),
                    nota = estudiante.representante?.let { "Representante: $it" },
                    etiqueta = if (estudiante.activo != 0) "Activo" else "Inactivo",
                    tono = if (estudiante.activo != 0) Tono.EXITO else Tono.NEUTRO,
                )
            }

        Modulo.NOTAS -> datos.grados
            .sortedWith(compareBy({ nombrePeriodo(it.periodoId) }, { it.nivel }, { it.nombre }))
            .map { grado ->
                val notas = datos.notas.filter { it.gradoId == grado.id }
                val matriculados = datos.matriculas.count { it.gradoId == grado.id && it.activa != 0 }
                FilaCatalogo(
                    id = grado.id,
                    titulo = grado.nombreCompleto,
                    subtitulo = "${nombrePeriodo(grado.periodoId)} · " +
                        etiquetaEstado(grado.nivel),
                    nota = "$matriculados estudiante(s) · ${notas.size} nota(s) · " +
                        "promedio ${promedio(notas.map { it.calificacion })}",
                    etiqueta = periodosPorId[grado.periodoId]?.let {
                        etiquetaEstado(it.estado)
                    },
                    tono = if (periodosPorId[grado.periodoId]?.estado == "cerrado") {
                        Tono.NEUTRO
                    } else {
                        Tono.EXITO
                    },
                )
            }

        Modulo.CONFIGURACION -> datos.configuraciones.map { configuracion ->
            FilaCatalogo(
                id = configuracion.id,
                titulo = configuracion.clave,
                subtitulo = listOfNotNull(
                    configuracion.categoria?.let { etiquetaEstado(it) },
                    configuracion.tipoDato,
                ).joinToString(" · "),
                nota = configuracion.valor?.takeIf { it.isNotBlank() } ?: "Sin valor",
                etiqueta = if (configuracion.editable != 0) "Editable" else "Fijo",
                tono = if (configuracion.editable != 0) Tono.NEUTRO else Tono.ALERTA,
            )
        }
    }

    /** Filtra por cualquier texto visible de la fila; vacío devuelve todo */
    fun buscar(modulo: Modulo, texto: String): List<FilaCatalogo> {
        val filas = filas(modulo)
        if (texto.isBlank()) return filas
        return filas.filter { fila ->
            listOfNotNull(fila.titulo, fila.subtitulo, fila.nota, fila.etiqueta)
                .any { it.contains(texto, ignoreCase = true) }
        }
    }

    // ---- Fichas ---------------------------------------------------------

    /** Detalle de una fila; null si la fila ya no existe en el espejo */
    fun ficha(modulo: Modulo, id: Long): FichaCatalogo? = when (modulo) {
        Modulo.EMPLEADOS -> empleadosPorId[id]?.let(::fichaEmpleado)
        Modulo.DOCUMENTOS -> datos.documentos.firstOrNull { it.id == id }?.let(::fichaDocumento)
        Modulo.INCIDENCIAS -> datos.incidencias.firstOrNull { it.id == id }?.let(::fichaIncidencia)
        Modulo.CONTRATOS -> datos.contratos.firstOrNull { it.id == id }?.let(::fichaContrato)
        Modulo.NOMINA -> datos.pagos.firstOrNull { it.id == id }?.let(::fichaPago)
        Modulo.ESTUDIANTES -> estudiantesPorId[id]?.let(::fichaEstudiante)
        Modulo.NOTAS -> gradosPorId[id]?.let(::fichaGrado)
        Modulo.CONFIGURACION ->
            datos.configuraciones.firstOrNull { it.id == id }?.let(::fichaConfiguracion)
        Modulo.DASHBOARD, Modulo.REGISTROS -> null
    }

    private fun fichaEmpleado(empleado: EmpleadoEntity): FichaCatalogo = FichaCatalogo(
        titulo = empleado.nombreCompleto,
        subtitulo = "${empleado.cargo} · ${empleado.departamento}",
        secciones = listOfNotNull(
            SeccionFicha(
                titulo = "Datos personales",
                campos = listOf(
                    CampoFicha("Cédula", texto(empleado.cedula)),
                    CampoFicha("Nombres", texto(empleado.nombres)),
                    CampoFicha("Apellidos", texto(empleado.apellidos)),
                    CampoFicha("Fecha de nacimiento", fecha(empleado.fechaNacimiento)),
                    CampoFicha("Género", texto(empleado.genero)),
                    CampoFicha("Estado civil", texto(empleado.estadoCivil)),
                    CampoFicha("Nacionalidad", texto(empleado.nacionalidad)),
                    CampoFicha("Tipo de sangre", texto(empleado.tipoSangre)),
                    CampoFicha("Peso (kg)", numero(empleado.peso)),
                    CampoFicha("Altura (m)", numero(empleado.altura)),
                ),
            ),
            SeccionFicha(
                titulo = "Contacto",
                campos = listOf(
                    CampoFicha("Teléfono", texto(empleado.telefono)),
                    CampoFicha("Celular", texto(empleado.celular)),
                    CampoFicha("Correo", texto(empleado.email)),
                    CampoFicha("Dirección", texto(empleado.direccion)),
                    CampoFicha("Ciudad", texto(empleado.ciudad)),
                    CampoFicha("Estado", texto(empleado.estado)),
                    CampoFicha("Código postal", texto(empleado.codigoPostal)),
                ),
            ),
            SeccionFicha(
                titulo = "Relación laboral",
                campos = listOf(
                    CampoFicha("Tipo de empleado", etiquetaEstado(empleado.tipoEmpleado)),
                    CampoFicha("Cargo", texto(empleado.cargo)),
                    CampoFicha("Departamento", texto(empleado.departamento)),
                    CampoFicha("Fecha de contratación", fecha(empleado.fechaContratacion)),
                    CampoFicha("Fecha de terminación", fecha(empleado.fechaTerminacion)),
                    CampoFicha("Salario base", bolivares(empleado.salarioBase)),
                    CampoFicha("Tipo de contratación", texto(empleado.tipoContratacion)),
                    CampoFicha("Activo", siNo(empleado.activo)),
                ),
            ),
            SeccionFicha(
                titulo = "Formación",
                campos = listOf(
                    CampoFicha("Nivel educativo", texto(empleado.nivelEducativo)),
                    CampoFicha("Especialidad", texto(empleado.especialidad)),
                    CampoFicha("Título obtenido", texto(empleado.tituloObtenido)),
                    CampoFicha("Título de secundaria", texto(empleado.tituloSecundaria)),
                ),
            ),
            SeccionFicha(
                titulo = "Datos bancarios",
                campos = listOf(
                    CampoFicha("Institución", texto(empleado.institucionBancaria)),
                    CampoFicha("Número de cuenta", texto(empleado.numeroCuenta)),
                    CampoFicha("Tipo de cuenta", texto(empleado.tipoCuenta)),
                ),
            ),
            SeccionFicha(
                titulo = "Salud",
                campos = listOf(
                    CampoFicha("Carnet de discapacidad", texto(empleado.carnetDiscapacidad)),
                    CampoFicha("Enfermedades preexistentes", texto(empleado.enfermedadesPreexistentes)),
                    CampoFicha("Alergias medicamentosas", texto(empleado.alergiasMedicamentosas)),
                    CampoFicha("Alergias alimentarias", texto(empleado.alergiasAlimentarias)),
                ),
            ),
            SeccionFicha(
                titulo = "Familia y emergencia",
                campos = listOf(
                    CampoFicha("Hijos", texto(empleado.hijos)),
                    CampoFicha("Contacto de emergencia", texto(empleado.contactoEmergenciaNombre)),
                    CampoFicha("Teléfono de emergencia", texto(empleado.contactoEmergenciaTelefono)),
                    CampoFicha("Relación", texto(empleado.contactoEmergenciaRelacion)),
                ),
            ),
            SeccionFicha(
                titulo = "Observaciones",
                parrafo = empleado.observaciones?.takeIf { it.isNotBlank() }
                    ?.let { texto(it) } ?: "Sin observaciones registradas.",
            ),
            seccionAuditoria(empleado.creadoEn, empleado.actualizadoEn),
        ),
    )

    private fun fichaDocumento(documento: DocumentoEntity): FichaCatalogo {
        val tamano = documento.tamanoBytes
            ?.let { String.format(Locale.US, "%.1f KB", it / 1024.0) }
        val contenido = when {
            documento.contenidoBinario != null -> "Copia disponible en este teléfono."
            documento.contenidoHash != null -> "Se descarga desde el nodo central."
            else -> "El archivo solo existe en el puesto donde se cargó."
        }
        return FichaCatalogo(
            titulo = documento.titulo,
            subtitulo = "${etiquetaEstado(documento.tipoDocumento)} · " +
                nombreEmpleado(documento.empleadoId),
            secciones = listOf(
                SeccionFicha(
                    titulo = "Documento",
                    campos = listOf(
                        CampoFicha("Empleado", nombreEmpleado(documento.empleadoId)),
                        CampoFicha("Tipo", etiquetaEstado(documento.tipoDocumento)),
                        CampoFicha("Título", texto(documento.titulo)),
                        CampoFicha("Número", texto(documento.numeroDocumento)),
                        CampoFicha("Emisión", fecha(documento.fechaEmision)),
                        CampoFicha("Vencimiento", fecha(documento.fechaVencimiento)),
                        CampoFicha("Estado", if (documento.activo != 0) "Activo" else "Archivado"),
                    ),
                ),
                SeccionFicha(titulo = "Descripción", parrafo = texto(documento.descripcion)),
                SeccionFicha(
                    titulo = "Archivo",
                    campos = listOf(
                        CampoFicha("Nombre", texto(documento.nombreArchivo)),
                        CampoFicha("Tamaño", tamano ?: "—"),
                        CampoFicha("Tipo MIME", texto(documento.tipoMime)),
                        CampoFicha("Huella SHA-256", texto(documento.contenidoHash)),
                    ),
                    parrafo = contenido,
                ),
                SeccionFicha(
                    titulo = "Observaciones",
                    parrafo = texto(documento.observaciones),
                ),
                seccionAuditoria(documento.creadoEn, documento.actualizadoEn),
            ),
        )
    }

    private fun fichaIncidencia(incidencia: IncidenciaEntity): FichaCatalogo = FichaCatalogo(
        titulo = etiquetaEstado(incidencia.tipoIncidencia),
        subtitulo = "${nombreEmpleado(incidencia.empleadoId)} · " +
            etiquetaEstado(incidencia.estado),
        secciones = listOf(
            SeccionFicha(
                titulo = "Solicitud",
                campos = listOf(
                    CampoFicha("Empleado", nombreEmpleado(incidencia.empleadoId)),
                    CampoFicha("Tipo", etiquetaEstado(incidencia.tipoIncidencia)),
                    CampoFicha("Estado", etiquetaEstado(incidencia.estado)),
                    CampoFicha("Motivo", texto(incidencia.motivo)),
                    CampoFicha("Desde", fecha(incidencia.fechaInicio)),
                    CampoFicha("Hasta", fecha(incidencia.fechaFin)),
                    CampoFicha("Días solicitados", incidencia.diasSolicitados.toString()),
                ),
            ),
            SeccionFicha(titulo = "Descripción", parrafo = texto(incidencia.descripcion)),
            SeccionFicha(
                titulo = "Aprobación",
                campos = listOf(
                    CampoFicha("Fecha de solicitud", fecha(incidencia.fechaSolicitud)),
                    CampoFicha("Fecha de aprobación", fecha(incidencia.fechaAprobacion)),
                    CampoFicha("Días aprobados", incidencia.diasAprobados?.toString() ?: "—"),
                    CampoFicha("Aprobado por", texto(incidencia.aprobadoPor)),
                    CampoFicha("Comentarios", texto(incidencia.comentariosAprobacion)),
                ),
            ),
            SeccionFicha(
                titulo = "Efecto en nómina",
                campos = listOf(
                    CampoFicha("Afecta nóminas", siNo(incidencia.afectaNominas)),
                    CampoFicha("Descuento de días", numero(incidencia.descuentoDias)),
                ),
            ),
            SeccionFicha(
                titulo = "Soporte",
                campos = listOf(
                    CampoFicha("Archivo", texto(incidencia.documentoSoporteNombre)),
                    CampoFicha("Huella SHA-256", texto(incidencia.documentoSoporteHash)),
                ),
                parrafo = if (incidencia.documentoSoporteBinario != null) {
                    "La copia del soporte está en este teléfono."
                } else {
                    "El soporte se descarga desde el nodo central."
                },
            ),
            SeccionFicha(
                titulo = "Observaciones",
                parrafo = texto(incidencia.observaciones),
            ),
            seccionAuditoria(incidencia.creadoEn, incidencia.actualizadoEn),
        ),
    )

    private fun fichaContrato(contrato: ContratoEntity): FichaCatalogo = FichaCatalogo(
        titulo = contrato.numero,
        subtitulo = "${contrato.cargo} · ${nombreEmpleado(contrato.empleadoId)}",
        secciones = listOf(
            SeccionFicha(
                titulo = "Contrato",
                campos = listOf(
                    CampoFicha("Número", texto(contrato.numero)),
                    CampoFicha("Empleado", nombreEmpleado(contrato.empleadoId)),
                    CampoFicha("Tipo", etiquetaEstado(contrato.tipo)),
                    CampoFicha("Estado", etiquetaEstado(contrato.estado)),
                    CampoFicha("Cargo", texto(contrato.cargo)),
                    CampoFicha("Departamento", texto(contrato.departamento)),
                    CampoFicha("Salario pactado", bolivares(contrato.salarioPactado)),
                    CampoFicha("Horas semanales", contrato.horasSemanales.toString()),
                ),
            ),
            SeccionFicha(
                titulo = "Vigencia",
                campos = listOf(
                    CampoFicha("Inicio", fecha(contrato.fechaInicio)),
                    CampoFicha("Fin", fecha(contrato.fechaFin)),
                    CampoFicha("Renovación automática", siNo(contrato.renovacionAutomatica)),
                    CampoFicha("Aprobado por", texto(contrato.aprobadoPor)),
                ),
            ),
            SeccionFicha(
                titulo = "Terminación",
                campos = listOf(
                    CampoFicha("Motivo", texto(contrato.motivoTerminacion)),
                    CampoFicha("Fecha", fecha(contrato.fechaTerminacion)),
                    CampoFicha("Liquidación", bolivares(contrato.liquidacionMonto)),
                ),
            ),
            SeccionFicha(titulo = "Cláusulas", parrafo = texto(contrato.clausulas)),
            SeccionFicha(
                titulo = "Observaciones",
                parrafo = texto(contrato.observaciones),
            ),
            seccionAuditoria(contrato.creadoEn, contrato.actualizadoEn),
        ),
    )

    private fun fichaPago(pago: PagoEntity): FichaCatalogo {
        val totalDescuentos = pago.deduccionSeguro + pago.deduccionPension +
            pago.deduccionImpuesto + pago.otrasDeducciones
        return FichaCatalogo(
            titulo = nombreEmpleado(pago.empleadoId),
            subtitulo = "${etiquetaEstado(pago.tipoPago)} · " +
                "${fecha(pago.periodoInicio)} → ${fecha(pago.periodoFin)}",
            secciones = listOf(
                SeccionFicha(
                    titulo = "Recibo",
                    campos = listOf(
                        CampoFicha("Empleado", nombreEmpleado(pago.empleadoId)),
                        CampoFicha("Tipo de pago", etiquetaEstado(pago.tipoPago)),
                        CampoFicha("Método", etiquetaEstado(pago.metodoPago)),
                        CampoFicha("Fecha de pago", fecha(pago.fechaPago)),
                        CampoFicha("Estado", if (pago.pagado != 0) "Pagado" else "Pendiente"),
                        CampoFicha("Referencia", texto(pago.referenciaPago)),
                    ),
                ),
                SeccionFicha(
                    titulo = "Devengos",
                    campos = listOf(
                        CampoFicha("Salario base", bolivares(pago.salarioBase)),
                        CampoFicha("Monto bruto", bolivares(pago.montoBruto)),
                        CampoFicha("Bonificaciones", bolivares(pago.bonificaciones)),
                        CampoFicha("Horas extra", bolivares(pago.horasExtra)),
                        CampoFicha("Horas extra diurnas", numero(pago.horasExtraDiurnas)),
                        CampoFicha("Horas extra nocturnas", numero(pago.horasExtraNocturnas)),
                        CampoFicha("Horas extra feriadas", numero(pago.horasExtraFeriadas)),
                        CampoFicha("Aguinaldo", bolivares(pago.aguinaldo)),
                        CampoFicha("Bono vacacional", bolivares(pago.bonoVacacional)),
                    ),
                ),
                SeccionFicha(
                    titulo = "Deducciones",
                    campos = listOf(
                        CampoFicha("Seguro social", bolivares(pago.deduccionSeguro)),
                        CampoFicha("Pensión", bolivares(pago.deduccionPension)),
                        CampoFicha("Impuesto sobre la renta", bolivares(pago.deduccionImpuesto)),
                        CampoFicha("Otras", bolivares(pago.otrasDeducciones)),
                        CampoFicha("Descuentos", bolivares(pago.descuentos)),
                        CampoFicha("Total deducciones", bolivares(totalDescuentos)),
                    ),
                ),
                SeccionFicha(
                    titulo = "Liquidación",
                    campos = listOf(
                        CampoFicha("Monto neto", bolivares(pago.montoNeto)),
                        CampoFicha("Días laborados", pago.diasLaborados?.toString() ?: "—"),
                        CampoFicha("Días del período", pago.diasPeriodo?.toString() ?: "—"),
                        CampoFicha("Prorrateado", siNo(pago.prorrateado ?: 0)),
                    ),
                ),
                SeccionFicha(
                    titulo = "Base de cálculo",
                    campos = listOf(
                        CampoFicha("Modalidad", etiquetaEstado(pago.modalidadCalculo)),
                        CampoFicha("Base gravable", bolivares(pago.baseGravable)),
                        CampoFicha("Tramo de ISR", texto(pago.isrTramo)),
                        CampoFicha("Aporte patronal al seguro", bolivares(pago.aporteSeguroPatronal)),
                        CampoFicha("Aporte patronal a pensión", bolivares(pago.aportePensionPatronal)),
                        CampoFicha("Registrado", fecha(pago.fechaRegistroPago)),
                    ),
                ),
                SeccionFicha(
                    titulo = "Notas",
                    campos = listOf(CampoFicha("Descripción", texto(pago.descripcion))),
                    parrafo = texto(pago.observaciones),
                ),
                seccionAuditoria(pago.creadoEn, pago.actualizadoEn),
            ),
        )
    }

    private fun fichaEstudiante(estudiante: EstudianteEntity): FichaCatalogo {
        val matriculas = datos.matriculas
            .filter { it.estudianteId == estudiante.id }
            .sortedByDescending { it.fechaMatricula }
        val notas = datos.notas.filter { it.estudianteId == estudiante.id }
        val matriculasTexto = if (matriculas.isEmpty()) {
            "Sin matrículas registradas."
        } else {
            matriculas.joinToString("\n") { matricula ->
                val estado = if (matricula.activa != 0) "activa" else "cerrada"
                "• ${nombreGrado(matricula.gradoId)} ($estado) · " +
                    "${fecha(matricula.fechaMatricula)}"
            }
        }
        val notasTexto = if (notas.isEmpty()) {
            "Sin calificaciones registradas."
        } else {
            notas.sortedBy { it.materia }.joinToString("\n") { nota ->
                "• ${nota.materia}: ${numero(nota.calificacion)}"
            }
        }
        return FichaCatalogo(
            titulo = estudiante.nombreCompleto,
            subtitulo = "${etiquetaEstado(estudiante.nivel)} · " +
                (estudiante.cedula ?: "sin cédula"),
            secciones = listOf(
                SeccionFicha(
                    titulo = "Datos del estudiante",
                    campos = listOf(
                        CampoFicha("Nombres", texto(estudiante.nombres)),
                        CampoFicha("Apellidos", texto(estudiante.apellidos)),
                        CampoFicha("Cédula", texto(estudiante.cedula)),
                        CampoFicha("Fecha de nacimiento", fecha(estudiante.fechaNacimiento)),
                        CampoFicha("Género", texto(estudiante.genero)),
                        CampoFicha("Nivel", etiquetaEstado(estudiante.nivel)),
                        CampoFicha("Estado", if (estudiante.activo != 0) "Activo" else "Inactivo"),
                    ),
                ),
                SeccionFicha(
                    titulo = "Contacto",
                    campos = listOf(
                        CampoFicha("Representante", texto(estudiante.representante)),
                        CampoFicha("Teléfono", texto(estudiante.telefono)),
                        CampoFicha("Teléfono del representante", texto(estudiante.telefonoRepresentante)),
                        CampoFicha("Correo", texto(estudiante.email)),
                        CampoFicha("Dirección", texto(estudiante.direccion)),
                    ),
                ),
                SeccionFicha(titulo = "Matrículas", parrafo = matriculasTexto),
                SeccionFicha(titulo = "Calificaciones", parrafo = notasTexto),
                SeccionFicha(
                    titulo = "Observaciones",
                    parrafo = texto(estudiante.observaciones),
                ),
                seccionAuditoria(estudiante.creadoEn, estudiante.actualizadoEn),
            ),
        )
    }

    private fun fichaGrado(grado: GradoEntity): FichaCatalogo {
        val periodo = periodosPorId[grado.periodoId]
        val matriculados = datos.matriculas.filter { it.gradoId == grado.id && it.activa != 0 }
        val notas = datos.notas.filter { it.gradoId == grado.id }
        val materias = notas.groupBy { it.materia }.toSortedMap()

        val secciones = buildList {
            add(
                SeccionFicha(
                    titulo = "Período",
                    campos = listOf(
                        CampoFicha("Período", texto(periodo?.nombre)),
                        CampoFicha("Estado", etiquetaEstado(periodo?.estado ?: "")),
                        CampoFicha("Inicio", fecha(periodo?.fechaInicio)),
                        CampoFicha("Fin", fecha(periodo?.fechaFin)),
                        CampoFicha("Cerrado el", fecha(periodo?.cerradoEn)),
                        CampoFicha("Cerrado por", texto(periodo?.cerradoPor)),
                    ),
                ),
            )
            add(
                SeccionFicha(
                    titulo = "Grupo",
                    campos = listOf(
                        CampoFicha("Nivel", etiquetaEstado(grado.nivel)),
                        CampoFicha("Nombre", texto(grado.nombre)),
                        CampoFicha("Sección", texto(grado.seccion)),
                        CampoFicha("Matriculados", matriculados.size.toString()),
                        CampoFicha("Notas registradas", notas.size.toString()),
                        CampoFicha("Promedio del grupo", promedio(notas.map { it.calificacion })),
                    ),
                ),
            )
            add(
                SeccionFicha(
                    titulo = "Promedio por materia",
                    campos = materias.map { (materia, lista) ->
                        CampoFicha(
                            materia,
                            "${promedio(lista.map { it.calificacion })} " +
                                "(${lista.size} nota(s))",
                        )
                    },
                    parrafo = if (materias.isEmpty()) "Sin calificaciones registradas." else null,
                ),
            )
            add(
                SeccionFicha(
                    titulo = "Estudiantes",
                    campos = matriculados.map { matricula ->
                        val propias = notas.filter { it.estudianteId == matricula.estudianteId }
                        CampoFicha(
                            nombreEstudiante(matricula.estudianteId),
                            "${promedio(propias.map { it.calificacion })} · " +
                                "${propias.size} materia(s)",
                        )
                    },
                    parrafo = if (matriculados.isEmpty()) {
                        "Todavía no hay estudiantes matriculados en este grupo."
                    } else {
                        null
                    },
                ),
            )
            add(seccionAuditoria(grado.creadoEn, grado.actualizadoEn))
        }

        return FichaCatalogo(
            titulo = grado.nombreCompleto,
            subtitulo = "${nombrePeriodo(grado.periodoId)} · " +
                etiquetaEstado(grado.nivel),
            secciones = secciones,
        )
    }

    private fun fichaConfiguracion(configuracion: ConfiguracionEntity): FichaCatalogo =
        FichaCatalogo(
            titulo = configuracion.clave,
            subtitulo = configuracion.categoria?.let { etiquetaEstado(it) },
            secciones = listOf(
                SeccionFicha(
                    titulo = "Parámetro",
                    campos = listOf(
                        CampoFicha("Clave", texto(configuracion.clave)),
                        CampoFicha("Valor", texto(configuracion.valor)),
                        CampoFicha("Tipo de dato", texto(configuracion.tipoDato)),
                        CampoFicha("Categoría", texto(configuracion.categoria)),
                        CampoFicha("Editable", siNo(configuracion.editable)),
                    ),
                ),
                SeccionFicha(
                    titulo = "Descripción",
                    parrafo = texto(configuracion.descripcion),
                ),
                seccionAuditoria(configuracion.creadoEn, configuracion.actualizadoEn),
            ),
        )

    private fun seccionAuditoria(creado: String?, actualizado: String?): SeccionFicha =
        SeccionFicha(
            titulo = "Sincronización",
            campos = listOf(
                CampoFicha("Creado", momento(creado)),
                CampoFicha("Última actualización", momento(actualizado)),
            ),
            parrafo = "Los datos provienen del nodo central; este teléfono solo los consulta.",
        )

    // ---- Panel de control ----------------------------------------------

    fun indicadores(): List<IndicadorPanel> {
        val vencidos = datos.documentos.count { vencimientoDocumento(it)?.second == Tono.ERROR }
        val porVencer = datos.documentos.filter { vencimientoDocumento(it)?.second == Tono.ALERTA }
        return listOf(
            IndicadorPanel(
                etiqueta = "Empleados activos",
                valor = datos.empleados.count { it.activo != 0 }.toString(),
            ),
            IndicadorPanel(
                etiqueta = "Estudiantes activos",
                valor = datos.estudiantes.count { it.activo != 0 }.toString(),
            ),
            IndicadorPanel(
                etiqueta = "Documentos",
                valor = datos.documentos.count { it.activo != 0 }.toString(),
            ),
            IndicadorPanel(
                etiqueta = "Documentos vencidos",
                valor = vencidos.toString(),
                tono = if (vencidos > 0) Tono.ERROR else Tono.NEUTRO,
            ),
            IndicadorPanel(
                etiqueta = "Documentos por vencer",
                valor = porVencer.size.toString(),
                tono = if (porVencer.isNotEmpty()) Tono.ALERTA else Tono.NEUTRO,
            ),
            IndicadorPanel(
                etiqueta = "Incidencias pendientes",
                valor = datos.incidencias.count { it.estado == "pendiente" }.toString(),
                tono = if (datos.incidencias.any { it.estado == "pendiente" }) Tono.ALERTA
                else Tono.NEUTRO,
            ),
            IndicadorPanel(
                etiqueta = "Pagos pendientes",
                valor = datos.pagos.count { it.pagado == 0 }.toString(),
                tono = if (datos.pagos.any { it.pagado == 0 }) Tono.ALERTA else Tono.NEUTRO,
            ),
            IndicadorPanel(
                etiqueta = "Calificaciones",
                valor = datos.notas.size.toString(),
            ),
        )
    }

    /** Avisos accionables: vencimientos, incidencias abiertas y pagos por hacer */
    fun alertas(): List<AlertaPanel> {
        val documentos = datos.documentos.mapNotNull { documento ->
            val aviso = vencimientoDocumento(documento) ?: return@mapNotNull null
            AlertaPanel(
                modulo = Modulo.DOCUMENTOS,
                fila = FilaCatalogo(
                    id = documento.id,
                    titulo = documento.titulo,
                    subtitulo = nombreEmpleado(documento.empleadoId),
                    nota = documento.fechaVencimiento?.let { "Vence el ${fecha(it)}" },
                    etiqueta = aviso.first,
                    tono = aviso.second,
                ),
            )
        }
        val incidencias = datos.incidencias
            .filter { it.estado == "pendiente" }
            .map { incidencia ->
                AlertaPanel(
                    modulo = Modulo.INCIDENCIAS,
                    fila = FilaCatalogo(
                        id = incidencia.id,
                        titulo = etiquetaEstado(incidencia.tipoIncidencia),
                        subtitulo = nombreEmpleado(incidencia.empleadoId),
                        nota = "Solicitada el ${fecha(incidencia.fechaSolicitud)}",
                        etiqueta = "Pendiente",
                        tono = Tono.ALERTA,
                    ),
                )
            }
        val contratos = datos.contratos.mapNotNull { contrato ->
            val aviso = vencimientoContrato(contrato) ?: return@mapNotNull null
            AlertaPanel(
                modulo = Modulo.CONTRATOS,
                fila = FilaCatalogo(
                    id = contrato.id,
                    titulo = "${contrato.numero} · ${contrato.cargo}",
                    subtitulo = nombreEmpleado(contrato.empleadoId),
                    nota = contrato.fechaFin?.let { "Termina el ${fecha(it)}" },
                    etiqueta = aviso.first,
                    tono = aviso.second,
                ),
            )
        }
        val pagos = datos.pagos.filter { it.pagado == 0 }.map { pago ->
            AlertaPanel(
                modulo = Modulo.NOMINA,
                fila = FilaCatalogo(
                    id = pago.id,
                    titulo = nombreEmpleado(pago.empleadoId),
                    subtitulo = etiquetaEstado(pago.tipoPago),
                    nota = "Neto ${bolivares(pago.montoNeto)}",
                    etiqueta = "Pendiente",
                    tono = Tono.ALERTA,
                ),
            )
        }
        return (documentos + incidencias + contratos + pagos).take(40)
    }

    // ---- Reglas de presentación ----------------------------------------

    private fun vencimientoDocumento(documento: DocumentoEntity): Pair<String, Tono>? {
        val dias = diasHasta(documento.fechaVencimiento) ?: return null
        return when {
            dias < 0 -> "Vencido" to Tono.ERROR
            dias == 0L -> "Vence hoy" to Tono.ALERTA
            dias <= 30 -> "Vence en $dias d" to Tono.ALERTA
            else -> null
        }
    }

    private fun vencimientoContrato(contrato: ContratoEntity): Pair<String, Tono>? {
        if (contrato.estado != "vigente") return null
        val dias = diasHasta(contrato.fechaFin) ?: return null
        return when {
            dias < 0 -> "Vencido" to Tono.ERROR
            dias <= 30 -> "Vence en $dias d" to Tono.ALERTA
            else -> null
        }
    }

    private fun tonoIncidencia(estado: String): Tono = when (estado.lowercase()) {
        "aprobada", "pagada" -> Tono.EXITO
        "rechazada", "anulada" -> Tono.ERROR
        "pendiente" -> Tono.ALERTA
        else -> Tono.NEUTRO
    }

    private fun tonoContrato(estado: String): Tono = when (estado.lowercase()) {
        "vigente" -> Tono.EXITO
        "vencido", "terminado", "rescindido" -> Tono.ERROR
        else -> Tono.NEUTRO
    }
}

// ----------------------------------------------------------------------
// Utilidades de formato
// ----------------------------------------------------------------------

private val IDIOMA = Locale.forLanguageTag("es-VE")
private val FORMATO_FECHA_CORTA = DateTimeFormatter.ofPattern("dd/MM/yyyy", IDIOMA)
private val FORMATO_MOMENTO = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm", IDIOMA)

/** Importe en bolívares con el formato del escritorio */
fun bolivares(monto: Double): String {
    val formato = NumberFormat.getNumberInstance(IDIOMA)
    formato.minimumFractionDigits = 2
    formato.maximumFractionDigits = 2
    return "Bs. ${formato.format(monto)}"
}

/** Número sin ceros sobrantes (peso, altura, horas, calificaciones) */
fun numero(valor: Double?): String {
    if (valor == null) return "—"
    return if (valor % 1.0 == 0.0) valor.toLong().toString()
    else String.format(Locale.US, "%.2f", valor)
}

fun texto(valor: String?): String = valor?.takeIf { it.isNotBlank() } ?: "—"

private fun siNo(valor: Int): String = if (valor != 0) "Sí" else "No"

/** Fecha ISO (``AAAA-MM-DD`` o marca completa) al formato del escritorio */
fun fecha(valor: String?): String {
    val crudo = valor?.takeIf { it.isNotBlank() } ?: return "—"
    val soloFecha = crudo.take(10)
    return runCatching {
        LocalDate.parse(soloFecha).format(FORMATO_FECHA_CORTA)
    }.getOrDefault(crudo)
}

/** Marca de tiempo ISO con la hora, si la trae */
fun momento(valor: String?): String {
    val crudo = valor?.takeIf { it.isNotBlank() } ?: return "—"
    return runCatching {
        val limpio = crudo.replace("T", " ").take(16)
        java.time.LocalDateTime.parse(limpio.replace(" ", "T")).format(FORMATO_MOMENTO)
    }.getOrDefault(fecha(crudo))
}

/** «aprobada» → «Aprobada»; vacío se muestra como raya */
fun etiquetaEstado(valor: String?): String {
    val limpio = valor?.trim().orEmpty()
    if (limpio.isEmpty()) return "—"
    return limpio.replace('_', ' ').replaceFirstChar { it.uppercase() }
}

private fun diasHasta(iso: String?): Long? {
    val fecha = iso?.take(10)?.takeIf { it.isNotBlank() } ?: return null
    return runCatching {
        ChronoUnit.DAYS.between(LocalDate.now(), LocalDate.parse(fecha))
    }.getOrNull()
}

/** Promedio con un decimal; sin datos se muestra una raya */
private fun promedio(valores: List<Double>): String {
    if (valores.isEmpty()) return "—"
    return String.format(Locale.US, "%.1f", valores.average())
}
