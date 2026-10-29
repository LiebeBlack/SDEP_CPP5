package ve.edu.sdep.movil.datos.local.entidad

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Espejo local de las 12 tablas que replican los puestos de la intranet.
 *
 * El teléfono es un puesto más: Room guarda la copia de trabajo de las mismas
 * tablas que el escritorio, con las MISMAS columnas de dominio (el nombre de
 * columna lo fija [ColumnInfo] y coincide con el del modelo Python). Las fechas
 * son texto ISO («AAAA-MM-DD» o «AAAA-MM-DDTHH:MM:SS» en UTC), tal como las
 * serializa el protocolo, de modo que la comparación de orden funciona igual
 * que en el motor de mezcla del nodo central.
 *
 * Cada fila se vincula a su identidad global con [IdentidadEntity]: los ids
 * locales (autoincrementales) no significan nada en otro equipo, pero el UUID
 * sí, y por él se reconocen las ediciones cruzadas.
 */

// ----------------------------------------------------------------------
// Identidad global y operaciones recibidas
// ----------------------------------------------------------------------

/** Equivalencia entre el UUID global y el id local de una fila (como `sync_ids`) */
@Entity(
    tableName = "identidades",
    indices = [
        Index(value = ["tabla", "uuid"], unique = true),
        Index(value = ["tabla", "idLocal"], unique = true),
    ],
)
data class IdentidadEntity(
    val tabla: String,
    val uuid: String,
    val idLocal: Long,
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
)

/**
 * Operación recibida que aún no se puede aplicar (falta el registro padre).
 *
 * El cursor de sincronización avanza con cada página, así que una operación
 * cuya clave foránea todavía no existe en este equipo se guarda aquí y se
 * reintenta en cada ciclo, igual que las diferidas del agente de escritorio.
 */
@Entity(
    tableName = "operaciones_entrada",
    indices = [Index("filaUuid"), Index("creadoEn")],
)
data class OperacionEntradaEntity(
    @PrimaryKey val opId: String,
    val tabla: String,
    val filaUuid: String,
    val operacion: String,
    val payload: String,
    val creadoEn: Long,
    /**
     * Sello original del protocolo. Se conserva tal cual llegó: al reintentar,
     * la mezcla debe comparar el MISMO instante que declaró el emisor, no uno
     * redondeado a milisegundos.
     */
    @ColumnInfo(name = "creado_en_iso", defaultValue = "''") val creadoEnIso: String = "",
    val motivo: String?,
    val intentos: Int = 0,
)

/**
 * Sesión de usuario cacheada (metadatos; el token vive en la bóveda cifrada).
 *
 * Permite reabrir la app sin red dentro de la ventana de gracia con el
 * desbloqueo biométrico, y muestra de quién es la sesión al restaurarla.
 */
@Entity(tableName = "sesion_usuario")
data class SesionUsuarioEntity(
    @PrimaryKey val id: Int = 1,
    val usuario: String,
    val nombreCompleto: String?,
    val rol: String,
    /** Cédula del trabajador, necesaria para aislar también sin red. */
    val cedula: String? = null,
    val expiraEn: Long,
    val debeCambiarPassword: Boolean,
    val actualizadoEn: Long,
)

// ----------------------------------------------------------------------
// Personal
// ----------------------------------------------------------------------

@Entity(
    tableName = "empleados",
    indices = [Index(value = ["cedula"], unique = true), Index("apellidos"), Index("activo")],
)
data class EmpleadoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val nombres: String,
    val apellidos: String,
    val cedula: String,
    @ColumnInfo(name = "fecha_nacimiento") val fechaNacimiento: String? = null,
    val genero: String? = null,
    @ColumnInfo(name = "estado_civil") val estadoCivil: String? = null,
    val nacionalidad: String? = null,
    val peso: Double? = null,
    val altura: Double? = null,
    @ColumnInfo(name = "tipo_sangre") val tipoSangre: String? = null,
    @ColumnInfo(name = "foto_ruta") val fotoRuta: String? = null,
    val telefono: String? = null,
    val celular: String? = null,
    val email: String? = null,
    val direccion: String? = null,
    val ciudad: String? = null,
    val estado: String? = null,
    @ColumnInfo(name = "codigo_postal") val codigoPostal: String? = null,
    @ColumnInfo(name = "tipo_empleado") val tipoEmpleado: String,
    val cargo: String,
    val departamento: String,
    @ColumnInfo(name = "fecha_contratacion") val fechaContratacion: String,
    @ColumnInfo(name = "fecha_terminacion") val fechaTerminacion: String? = null,
    @ColumnInfo(name = "salario_base") val salarioBase: Double,
    val activo: Int = 1,
    @ColumnInfo(name = "nivel_educativo") val nivelEducativo: String? = null,
    val especialidad: String? = null,
    @ColumnInfo(name = "titulo_obtenido") val tituloObtenido: String? = null,
    @ColumnInfo(name = "titulo_secundaria") val tituloSecundaria: String? = null,
    @ColumnInfo(name = "institucion_bancaria") val institucionBancaria: String? = null,
    @ColumnInfo(name = "numero_cuenta") val numeroCuenta: String? = null,
    @ColumnInfo(name = "tipo_cuenta") val tipoCuenta: String? = null,
    @ColumnInfo(name = "carnet_discapacidad") val carnetDiscapacidad: String? = null,
    @ColumnInfo(name = "enfermedades_preexistentes") val enfermedadesPreexistentes: String? = null,
    @ColumnInfo(name = "alergias_medicamentosas") val alergiasMedicamentosas: String? = null,
    @ColumnInfo(name = "alergias_alimentarias") val alergiasAlimentarias: String? = null,
    @ColumnInfo(name = "tipo_contratacion") val tipoContratacion: String? = null,
    val hijos: String? = null,
    val observaciones: String? = null,
    @ColumnInfo(name = "contacto_emergencia_nombre") val contactoEmergenciaNombre: String? = null,
    @ColumnInfo(name = "contacto_emergencia_telefono") val contactoEmergenciaTelefono: String? = null,
    @ColumnInfo(name = "contacto_emergencia_relacion") val contactoEmergenciaRelacion: String? = null,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
) {
    val nombreCompleto: String get() = "$nombres $apellidos".trim()
}

@Entity(
    tableName = "documentos",
    indices = [Index("empleado_id"), Index("tipo_documento"), Index("activo")],
)
data class DocumentoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "empleado_id") val empleadoId: Long,
    @ColumnInfo(name = "tipo_documento") val tipoDocumento: String,
    val titulo: String,
    val descripcion: String? = null,
    @ColumnInfo(name = "numero_documento") val numeroDocumento: String? = null,
    @ColumnInfo(name = "fecha_emision") val fechaEmision: String? = null,
    @ColumnInfo(name = "fecha_vencimiento") val fechaVencimiento: String? = null,
    @ColumnInfo(name = "nombre_archivo") val nombreArchivo: String,
    @ColumnInfo(name = "ruta_archivo") val rutaArchivo: String = "",
    @ColumnInfo(name = "tamano_bytes") val tamanoBytes: Int? = null,
    @ColumnInfo(name = "tipo_mime") val tipoMime: String? = null,
    /** Hash del contenido en el almacén de binarios del nodo central */
    @ColumnInfo(name = "contenido_hash") val contenidoHash: String? = null,
    @ColumnInfo(name = "contenido_binario") val contenidoBinario: ByteArray? = null,
    val activo: Int = 1,
    val observaciones: String? = null,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
)

@Entity(
    tableName = "incidencias",
    indices = [Index("empleado_id"), Index("tipo_incidencia"), Index("estado")],
)
data class IncidenciaEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "empleado_id") val empleadoId: Long,
    @ColumnInfo(name = "tipo_incidencia") val tipoIncidencia: String,
    val estado: String,
    @ColumnInfo(name = "fecha_inicio") val fechaInicio: String,
    @ColumnInfo(name = "fecha_fin") val fechaFin: String,
    @ColumnInfo(name = "fecha_solicitud") val fechaSolicitud: String,
    @ColumnInfo(name = "fecha_aprobacion") val fechaAprobacion: String? = null,
    val motivo: String,
    val descripcion: String? = null,
    @ColumnInfo(name = "dias_solicitados") val diasSolicitados: Int,
    @ColumnInfo(name = "dias_aprobados") val diasAprobados: Int? = null,
    @ColumnInfo(name = "documento_soporte_nombre") val documentoSoporteNombre: String? = null,
    @ColumnInfo(name = "documento_soporte_ruta") val documentoSoporteRuta: String? = null,
    @ColumnInfo(name = "documento_soporte_hash") val documentoSoporteHash: String? = null,
    @ColumnInfo(name = "documento_soporte_binario") val documentoSoporteBinario: ByteArray? = null,
    @ColumnInfo(name = "aprobado_por") val aprobadoPor: String? = null,
    @ColumnInfo(name = "comentarios_aprobacion") val comentariosAprobacion: String? = null,
    @ColumnInfo(name = "afecta_nominas") val afectaNominas: Int = 1,
    @ColumnInfo(name = "descuento_dias") val descuentoDias: Double? = null,
    val observaciones: String? = null,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
)

@Entity(
    tableName = "contratos",
    indices = [Index(value = ["numero"], unique = true), Index("empleado_id"), Index("estado")],
)
data class ContratoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "empleado_id") val empleadoId: Long,
    val numero: String,
    val tipo: String,
    val estado: String,
    val cargo: String,
    val departamento: String? = null,
    @ColumnInfo(name = "salario_pactado") val salarioPactado: Double,
    @ColumnInfo(name = "horas_semanales") val horasSemanales: Int = 40,
    @ColumnInfo(name = "fecha_inicio") val fechaInicio: String,
    @ColumnInfo(name = "fecha_fin") val fechaFin: String? = null,
    @ColumnInfo(name = "renovacion_automatica") val renovacionAutomatica: Int = 0,
    /** UUID global del contrato que éste renueva (traducido a id local si existe) */
    @ColumnInfo(name = "contrato_anterior_id") val contratoAnteriorId: Long? = null,
    @ColumnInfo(name = "archivo_ruta") val archivoRuta: String? = null,
    val clausulas: String? = null,
    @ColumnInfo(name = "motivo_terminacion") val motivoTerminacion: String? = null,
    @ColumnInfo(name = "fecha_terminacion") val fechaTerminacion: String? = null,
    @ColumnInfo(name = "liquidacion_monto") val liquidacionMonto: Double = 0.0,
    @ColumnInfo(name = "aprobado_por") val aprobadoPor: String? = null,
    val observaciones: String? = null,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
)

// ----------------------------------------------------------------------
// Nómina
// ----------------------------------------------------------------------

@Entity(tableName = "pagos", indices = [Index("empleado_id"), Index("periodo_inicio"), Index("pagado")])
data class PagoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "empleado_id") val empleadoId: Long,
    @ColumnInfo(name = "tipo_pago") val tipoPago: String,
    @ColumnInfo(name = "metodo_pago") val metodoPago: String = "transferencia",
    @ColumnInfo(name = "periodo_inicio") val periodoInicio: String,
    @ColumnInfo(name = "periodo_fin") val periodoFin: String,
    @ColumnInfo(name = "fecha_pago") val fechaPago: String,
    @ColumnInfo(name = "monto_bruto") val montoBruto: Double,
    @ColumnInfo(name = "monto_neto") val montoNeto: Double,
    val descuentos: Double = 0.0,
    val bonificaciones: Double = 0.0,
    @ColumnInfo(name = "horas_extra") val horasExtra: Double = 0.0,
    @ColumnInfo(name = "salario_base") val salarioBase: Double,
    @ColumnInfo(name = "deduccion_seguro") val deduccionSeguro: Double = 0.0,
    @ColumnInfo(name = "deduccion_pension") val deduccionPension: Double = 0.0,
    @ColumnInfo(name = "deduccion_impuesto") val deduccionImpuesto: Double = 0.0,
    @ColumnInfo(name = "otras_deducciones") val otrasDeducciones: Double = 0.0,
    @ColumnInfo(name = "modalidad_calculo") val modalidadCalculo: String = "porcentaje",
    @ColumnInfo(name = "base_gravable") val baseGravable: Double = 0.0,
    @ColumnInfo(name = "horas_extra_diurnas") val horasExtraDiurnas: Double = 0.0,
    @ColumnInfo(name = "horas_extra_nocturnas") val horasExtraNocturnas: Double = 0.0,
    @ColumnInfo(name = "horas_extra_feriadas") val horasExtraFeriadas: Double = 0.0,
    val aguinaldo: Double = 0.0,
    @ColumnInfo(name = "bono_vacacional") val bonoVacacional: Double = 0.0,
    @ColumnInfo(name = "aporte_seguro_patronal") val aporteSeguroPatronal: Double = 0.0,
    @ColumnInfo(name = "aporte_pension_patronal") val aportePensionPatronal: Double = 0.0,
    @ColumnInfo(name = "isr_tramo") val isrTramo: String? = null,
    @ColumnInfo(name = "dias_laborados") val diasLaborados: Int? = null,
    @ColumnInfo(name = "dias_periodo") val diasPeriodo: Int? = null,
    val prorrateado: Int? = null,
    val descripcion: String? = null,
    @ColumnInfo(name = "referencia_pago") val referenciaPago: String? = null,
    val observaciones: String? = null,
    val pagado: Int = 0,
    @ColumnInfo(name = "fecha_registro_pago") val fechaRegistroPago: String? = null,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
)

// ----------------------------------------------------------------------
// Académico
// ----------------------------------------------------------------------

@Entity(
    tableName = "estudiantes",
    indices = [Index(value = ["cedula"], unique = true), Index("nivel"), Index("activo")],
)
data class EstudianteEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val nombres: String,
    val apellidos: String,
    val cedula: String? = null,
    @ColumnInfo(name = "fecha_nacimiento") val fechaNacimiento: String? = null,
    val genero: String? = null,
    val nivel: String,
    val representante: String? = null,
    val telefono: String? = null,
    @ColumnInfo(name = "telefono_representante") val telefonoRepresentante: String? = null,
    val email: String? = null,
    val direccion: String? = null,
    val observaciones: String? = null,
    val activo: Int = 1,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
) {
    val nombreCompleto: String get() = "$nombres $apellidos".trim()
}

@Entity(
    tableName = "periodos_academicos",
    indices = [Index(value = ["nombre"], unique = true), Index("estado")],
)
data class PeriodoAcademicoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val nombre: String,
    @ColumnInfo(name = "fecha_inicio") val fechaInicio: String? = null,
    @ColumnInfo(name = "fecha_fin") val fechaFin: String? = null,
    val estado: String = "abierto",
    @ColumnInfo(name = "cerrado_en") val cerradoEn: String? = null,
    @ColumnInfo(name = "cerrado_por") val cerradoPor: String? = null,
    val observaciones: String? = null,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
)

@Entity(
    tableName = "grados",
    indices = [Index("periodo_id"), Index("nivel")],
)
data class GradoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "periodo_id") val periodoId: Long,
    val nivel: String,
    val nombre: String,
    val seccion: String = "A",
    /**
     * UUID global del docente asignado. Los usuarios NO se replican, así que
     * el nombre se resuelve contra el nodo central (`consultas/docentes`); el
     * campo es local y jamás viaja en un payload: este equipo no toca la
     * asignación de profesores.
     */
    @ColumnInfo(name = "profesor_uuid") val profesorUuid: String? = null,
    val observaciones: String? = null,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
) {
    val nombreCompleto: String get() = "$nombre $seccion".trim()
}

@Entity(
    tableName = "matriculas",
    // El escritorio garantiza una sola matrícula ACTIVA por (estudiante,
    // grado) con un índice parcial; Room no admite índices parciales, así que
    // aquí el índice es simple y la unicidad la aporta la clave natural al    // aplicar la operación remota (mismo comportamiento, distinta vía).
    indices = [Index("estudiante_id"), Index("grado_id"), Index("activa")],
)
data class MatriculaEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "estudiante_id") val estudianteId: Long,
    @ColumnInfo(name = "grado_id") val gradoId: Long,
    @ColumnInfo(name = "fecha_matricula") val fechaMatricula: String,
    val activa: Int = 1,
    val observaciones: String? = null,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
)

@Entity(
    tableName = "notas_finales",
    indices = [
        Index(value = ["estudiante_id", "grado_id", "materia"], unique = true),
        Index("grado_id"),
    ],
)
data class NotaFinalEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    @ColumnInfo(name = "estudiante_id") val estudianteId: Long,
    @ColumnInfo(name = "grado_id") val gradoId: Long,
    val materia: String,
    val calificacion: Double,
    @ColumnInfo(name = "registrado_por") val registradoPor: String? = null,
    val observaciones: String? = null,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
)

// ----------------------------------------------------------------------
// Configuración institucional
// ----------------------------------------------------------------------

// ----------------------------------------------------------------------
// Metadata de mezcla (espejo de sync_campos / sync_versiones /
// sync_ops_aplicadas / sync_blobs del agente de escritorio)
// ----------------------------------------------------------------------

/**
 * Última escritura conocida de un campo de una fila replicada.
 *
 * Es la base del motor de mezcla: cada operación que se aplica o se envía
 * deja aquí su marca (valor, operación, dispositivo y sello de tiempo), y la
 * siguiente comparación campo a campo decide quién gana con la misma regla
 * determinista que usa el nodo central.
 */
@Entity(
    tableName = "campos_remotos",
    indices = [
        Index(value = ["tabla", "fila_uuid", "campo"], unique = true),
        Index("fila_uuid"),
    ],
)
data class CampoRemotoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val tabla: String,
    @ColumnInfo(name = "fila_uuid") val filaUuid: String,
    val campo: String,
    /** Valor canónico del protocolo (JSON compacto con claves ordenadas) */
    val valor: String?,
    @ColumnInfo(name = "op_id") val opId: String,
    val dispositivo: String,
    /** ISO 8601 en UTC sin zona, comparable lexicográficamente */
    @ColumnInfo(name = "actualizado_en") val actualizadoEn: String,
)

/** Estado de una fila replicada: última operación y borrado vigente */
@Entity(
    tableName = "versiones_filas",
    indices = [Index(value = ["tabla", "fila_uuid"], unique = true)],
)
data class VersionFilaEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val tabla: String,
    @ColumnInfo(name = "fila_uuid") val filaUuid: String,
    @ColumnInfo(name = "ultimo_op_id") val ultimoOpId: String? = null,
    @ColumnInfo(name = "actualizado_en") val actualizadoEn: String? = null,
    val dispositivo: String? = null,
    val borrado: Int = 0,
    @ColumnInfo(name = "borrado_en") val borradoEn: String? = null,
    @ColumnInfo(name = "borrado_op_id") val borradoOpId: String? = null,
    @ColumnInfo(name = "borrado_dispositivo") val borradoDispositivo: String? = null,
)

/** Operaciones ya aplicadas desde la red: aplicación exactamente una vez */
@Entity(tableName = "ops_aplicadas")
data class OpAplicadaEntity(
    @PrimaryKey val opId: String,
    val tabla: String,
    @ColumnInfo(name = "aplicado_en") val aplicadoEn: Long,
)

/**
 * Binario pendiente de transferir por el canal de archivos del nodo central.
 *
 * El contenido nunca viaja en el payload: aquí solo queda qué hash hay que
 * bajar y para qué fila y columna sirve.
 */
@Entity(tableName = "blobs_pendientes")
data class BlobPendienteEntity(
    @PrimaryKey val hash: String,
    val tamano: Int = 0,
    val tabla: String,
    @ColumnInfo(name = "fila_uuid") val filaUuid: String,
    val columna: String,
    /** «entrada» = falta bajarlo; «salida» = falta subirlo */
    val direccion: String,
    val estado: String,
    val intentos: Int = 0,
    @ColumnInfo(name = "creado_en") val creadoEn: Long,
    @ColumnInfo(name = "actualizado_en") val actualizadoEn: Long,
)

@Entity(
    tableName = "configuraciones",
    indices = [Index(value = ["clave"], unique = true), Index("categoria")],
)
data class ConfiguracionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val clave: String,
    val valor: String? = null,
    val descripcion: String? = null,
    @ColumnInfo(name = "tipo_dato") val tipoDato: String = "string",
    val categoria: String? = null,
    val editable: Int = 1,
    @ColumnInfo(name = "created_at") val creadoEn: String = "",
    @ColumnInfo(name = "updated_at") val actualizadoEn: String = "",
)
