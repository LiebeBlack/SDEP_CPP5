package ve.edu.sdep.movil.datos.local

import ve.edu.sdep.movil.dominio.modelo.Modulo

/**
 * Descripción de una columna tal como está en la base del teléfono.
 *
 * No hay una lista escrita a mano de los 150 campos del sistema: el esquema se
 * lee de la propia tabla (`PRAGMA table_info`), igual que haría una consola de
 * base de datos. Así, cuando el escritorio añade una columna y la replicación
 * la trae, el formulario del teléfono la muestra sin tocar código.
 */
enum class TipoCampo {
    TEXTO,
    TEXTO_LARGO,
    ENTERO,
    DECIMAL,
    FECHA,
    BOOLEANO,
    OPCION,
    FORANEA,
}

/** Una columna editable del formulario */
data class ColumnaTabla(
    val nombre: String,
    val etiqueta: String,
    val tipo: TipoCampo,
    val requerido: Boolean,
    val opciones: List<String> = emptyList(),
    val tablaForanea: String? = null,
)

/** Una fila de una tabla padre, para elegir una clave foránea */
data class OpcionTabla(val id: Long, val etiqueta: String)

/**
 * Catálogo de las tablas que el teléfono puede administrar.
 *
 * `configuraciones` queda fuera a propósito: es el panel del sistema y se
 * elimina del teléfono. `registros_moviles` tiene su propia pantalla de campo.
 */
object EsquemaTabla {

    /** Tablas con formulario genérico, en el orden en que se ofrecen */
    val TABLAS: List<String> = listOf(
        "empleados",
        "documentos",
        "incidencias",
        "contratos",
        "pagos",
        "estudiantes",
        "periodos_academicos",
        "grados",
        "matriculas",
        "notas_finales",
    )

    /** Título legible de una tabla */
    fun titulo(tabla: String): String = TITULOS[tabla] ?: tabla.replace('_', ' ')

    /** Tabla que administra un módulo del menú; null si el módulo es de escritorio */
    fun tablaDeModulo(modulo: Modulo): String? = when (modulo) {
        Modulo.EMPLEADOS -> "empleados"
        Modulo.DOCUMENTOS -> "documentos"
        Modulo.INCIDENCIAS -> "incidencias"
        Modulo.CONTRATOS -> "contratos"
        Modulo.NOMINA -> "pagos"
        Modulo.ESTUDIANTES -> "estudiantes"
        Modulo.NOTAS -> "notas_finales"
        // El panel de control y la configuración institucional son del escritorio.
        Modulo.DASHBOARD, Modulo.CONFIGURACION, Modulo.REGISTROS -> null
    }

    /** Módulo con el que se comprueba el acceso a una tabla */
    fun moduloDeTabla(tabla: String): Modulo? = when (tabla) {
        "empleados" -> Modulo.EMPLEADOS
        "documentos" -> Modulo.DOCUMENTOS
        "incidencias" -> Modulo.INCIDENCIAS
        "contratos" -> Modulo.CONTRATOS
        "pagos" -> Modulo.NOMINA
        "estudiantes" -> Modulo.ESTUDIANTES
        "notas_finales", "periodos_academicos", "grados", "matriculas" -> Modulo.NOTAS
        else -> null
    }

    /** Indica si la tabla se puede administrar desde el teléfono */
    fun esAdministrable(tabla: String): Boolean = tabla in TABLAS

    /**
     * Columnas editables de una tabla, en el orden físico del esquema.
     *
     * Se omiten las columnas de control (id, sellos de tiempo), los binarios y
     * sus metadatos de transporte: el archivo viaja por el canal de binarios,
     * no dentro del formulario.
     */
    fun columnas(baseDatos: BaseDatosSdep, tabla: String): List<ColumnaTabla> {
        if (!esAdministrable(tabla)) return emptyList()
        val resultado = mutableListOf<ColumnaTabla>()
        val foraneas = Espejo.CLAVES_FORANEAS[tabla].orEmpty()
        val cursor = baseDatos.openHelper.readableDatabase.query("PRAGMA table_info($tabla)")
        cursor.use { fila ->
            while (fila.moveToNext()) {
                val nombre = fila.getString(fila.getColumnIndexOrThrow("name"))
                val tipoSql = fila.getString(fila.getColumnIndexOrThrow("type")).orEmpty()
                val noNulo = fila.getInt(fila.getColumnIndexOrThrow("notnull")) == 1
                val defecto = fila.getString(fila.getColumnIndexOrThrow("dflt_value"))
                if (nombre in OMITIDAS || nombre.endsWith("_binario") || nombre.endsWith("_hash")) {
                    continue
                }
                val opciones = OPCIONES["$tabla.$nombre"].orEmpty()
                val tablaForanea = foraneas[nombre]
                val tipo = when {
                    nombre in BOOLEANOS -> TipoCampo.BOOLEANO
                    tablaForanea != null -> TipoCampo.FORANEA
                    opciones.isNotEmpty() -> TipoCampo.OPCION
                    nombre.startsWith("fecha") || nombre.startsWith("periodo_") -> TipoCampo.FECHA
                    tipoSql.contains("INT", ignoreCase = true) -> TipoCampo.ENTERO
                    tipoSql.contains("REAL", ignoreCase = true) ||
                        tipoSql.contains("FLOA", ignoreCase = true) ||
                        tipoSql.contains("DOUB", ignoreCase = true) ||
                        tipoSql.contains("NUM", ignoreCase = true) -> TipoCampo.DECIMAL
                    nombre in LARGOS -> TipoCampo.TEXTO_LARGO
                    else -> TipoCampo.TEXTO
                }
                resultado += ColumnaTabla(
                    nombre = nombre,
                    etiqueta = ETIQUETAS[nombre] ?: nombre.replace('_', ' ')
                        .replaceFirstChar { it.uppercase() },
                    tipo = tipo,
                    // Un valor por omisión del esquema cubre la obligación.
                    requerido = noNulo && defecto == null,
                    opciones = opciones,
                    tablaForanea = tablaForanea,
                )
            }
        }
        return resultado
    }

    /** Columnas que el formulario no muestra: control interno y transporte de archivos */
    private val OMITIDAS = setOf(
        "id",
        "created_at",
        "updated_at",
        "ruta_archivo",
        "foto_ruta",
        "tamano_bytes",
        "tipo_mime",
        "documento_soporte_ruta",
        "documento_soporte_nombre",
    )

    /** Enteros que en realidad son sí/no */
    private val BOOLEANOS = setOf(
        "activo",
        "activa",
        "afecta_nominas",
        "pagado",
    )

    /** Textos largos: el formulario los muestra en varias líneas */
    private val LARGOS = setOf(
        "descripcion",
        "observaciones",
        "motivo",
        "direccion",
        "comentarios_aprobacion",
        "enfermedades_preexistentes",
        "alergias_medicamentosas",
        "alergias_alimentarias",
        "resolucion",
        "contenido",
    )

    private val TITULOS = mapOf(
        "empleados" to "Empleados",
        "documentos" to "Documentos",
        "incidencias" to "Incidencias",
        "contratos" to "Contratos",
        "pagos" to "Nómina",
        "estudiantes" to "Estudiantes",
        "periodos_academicos" to "Períodos académicos",
        "grados" to "Grados",
        "matriculas" to "Matrículas",
        "notas_finales" to "Calificaciones",
    )

    /**
     * Listas cerradas del modelo.
     *
     * Solo se declaran los campos que el escritorio valida contra un enum. El
     * resto son texto libre y el nodo central sigue siendo la autoridad.
     */
    private val OPCIONES: Map<String, List<String>> = mapOf(
        "empleados.tipo_empleado" to listOf("docente", "administrativo", "mantenimiento"),
        "empleados.genero" to listOf("masculino", "femenino", "otro"),
        "empleados.estado_civil" to listOf(
            "soltero", "casado", "divorciado", "viudo", "union_libre",
        ),
        "documentos.tipo_documento" to listOf(
            "cedula", "titulo", "reposo", "certificado", "expediente", "otro",
        ),
        "incidencias.tipo_incidencia" to listOf(
            "reposo_medico", "ausencia", "permiso", "vacaciones", "licencia",
        ),
        "incidencias.estado" to listOf("pendiente", "aprobado", "rechazado", "completado"),
        "contratos.tipo" to listOf("indefinido", "temporal", "obra", "pasantia"),
        "contratos.estado" to listOf("vigente", "renovado", "vencido", "terminado"),
        "pagos.tipo_pago" to listOf(
            "salario_base", "bonificacion", "descuento", "horas_extra", "comision", "liquidacion",
        ),
        "pagos.metodo_pago" to listOf("transferencia", "efectivo", "cheque", "deposito"),
        "periodos_academicos.estado" to listOf("abierto", "cerrado"),
        "grados.nivel" to listOf("inicial", "secundaria"),
        "estudiantes.nivel" to listOf("inicial", "secundaria"),
    )

    /** Etiquetas de cara al usuario; el resto se deriva del nombre de la columna */
    private val ETIQUETAS: Map<String, String> = mapOf(
        "nombres" to "Nombres",
        "apellidos" to "Apellidos",
        "cedula" to "Cédula",
        "fecha_nacimiento" to "Fecha de nacimiento",
        "genero" to "Género",
        "estado_civil" to "Estado civil",
        "nacionalidad" to "Nacionalidad",
        "peso" to "Peso (kg)",
        "altura" to "Altura (m)",
        "tipo_sangre" to "Tipo de sangre",
        "telefono" to "Teléfono",
        "celular" to "Celular",
        "email" to "Correo electrónico",
        "direccion" to "Dirección",
        "ciudad" to "Ciudad",
        "codigo_postal" to "Código postal",
        "tipo_empleado" to "Tipo de empleado",
        "cargo" to "Cargo",
        "departamento" to "Departamento",
        "fecha_contratacion" to "Fecha de contratación",
        "fecha_terminacion" to "Fecha de terminación",
        "salario_base" to "Salario base",
        "activo" to "Activo",
        "activa" to "Activa",
        "nivel_educativo" to "Nivel educativo",
        "especialidad" to "Especialidad",
        "titulo_obtenido" to "Título obtenido",
        "titulo_secundaria" to "Título de secundaria",
        "institucion_bancaria" to "Institución bancaria",
        "numero_cuenta" to "Número de cuenta",
        "tipo_cuenta" to "Tipo de cuenta",
        "carnet_discapacidad" to "Carnet de discapacidad",
        "enfermedades_preexistentes" to "Enfermedades preexistentes",
        "alergias_medicamentosas" to "Alergias medicamentosas",
        "alergias_alimentarias" to "Alergias alimentarias",
        "tipo_contratacion" to "Tipo de contratación",
        "hijos" to "Hijos",
        "observaciones" to "Observaciones",
        "contacto_emergencia_nombre" to "Contacto de emergencia",
        "contacto_emergencia_telefono" to "Teléfono de emergencia",
        "contacto_emergencia_relacion" to "Parentesco del contacto",
        "empleado_id" to "Empleado",
        "estudiante_id" to "Estudiante",
        "grado_id" to "Grado",
        "periodo_id" to "Período",
        "contrato_anterior_id" to "Contrato anterior",
        "tipo_documento" to "Tipo de documento",
        "titulo" to "Título",
        "descripcion" to "Descripción",
        "numero_documento" to "Número de documento",
        "fecha_emision" to "Fecha de emisión",
        "fecha_vencimiento" to "Fecha de vencimiento",
        "nombre_archivo" to "Nombre del archivo",
        "tipo_incidencia" to "Tipo de incidencia",
        "estado" to "Estado",
        "fecha_inicio" to "Fecha de inicio",
        "fecha_fin" to "Fecha de fin",
        "fecha_solicitud" to "Fecha de solicitud",
        "fecha_aprobacion" to "Fecha de aprobación",
        "motivo" to "Motivo",
        "dias_solicitados" to "Días solicitados",
        "dias_aprobados" to "Días aprobados",
        "aprobado_por" to "Aprobado por",
        "comentarios_aprobacion" to "Comentarios de aprobación",
        "afecta_nominas" to "Afecta nómina",
        "descuento_dias" to "Días de descuento",
        "numero" to "Número de contrato",
        "tipo" to "Tipo",
        "salario_pactado" to "Salario pactado",
        "periodo_inicio" to "Inicio del período",
        "periodo_fin" to "Fin del período",
        "monto_bruto" to "Monto bruto",
        "monto_neto" to "Monto neto",
        "deducciones" to "Deducciones",
        "bonificaciones" to "Bonificaciones",
        "horas_extra" to "Horas extra",
        "pagado" to "Pagado",
        "fecha_pago" to "Fecha de pago",
        "nombre" to "Nombre",
        "seccion" to "Sección",
        "nivel" to "Nivel",
        "materia" to "Materia",
        "calificacion" to "Calificación",
        "fecha_matricula" to "Fecha de matrícula",
        "representante" to "Representante",
        "representante_cedula" to "Cédula del representante",
        "representante_telefono" to "Teléfono del representante",
    )
}
