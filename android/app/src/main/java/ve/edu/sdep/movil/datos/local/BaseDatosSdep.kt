package ve.edu.sdep.movil.datos.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import ve.edu.sdep.movil.datos.local.dao.*
import ve.edu.sdep.movil.datos.local.entidad.*

/**
 * Base de datos local del teléfono.
 *
 * **Versión 2 — espejo completo del sistema.** Además de los registros de
 * campo, la cola de salida, el cursor y los conflictos, Room guarda ahora la
 * copia de trabajo de las 12 tablas replicadas (empleados, documentos,
 * incidencias, contratos, pagos, estudiantes, grados, matrículas, notas,
 * periodos, configuraciones e identidad global), de modo que todas las
 * pantallas leen sin red y los cambios viajan por la cola como en cualquier
 * otro puesto de la intranet.
 *
 * La migración [MIGRATION_1_2] conserva los datos de la versión 1 (registros
 * de campo, cola y cursor: nada de lo que el usuario escribió se pierde al
 * actualizar) y elimina la tabla `usuarios`: las cuentas ya no son locales,
 * se validan contra la base institucional.
 */
@Database(
    entities = [
        // v1 conservados
        RegistroEntity::class,
        OperacionPendienteEntity::class,
        EstadoSyncEntity::class,
        ConflictoEntity::class,
        // v2: espejo y sesión
        IdentidadEntity::class,
        OperacionEntradaEntity::class,
        SesionUsuarioEntity::class,
        EmpleadoEntity::class,
        DocumentoEntity::class,
        IncidenciaEntity::class,
        ContratoEntity::class,
        PagoEntity::class,
        EstudianteEntity::class,
        PeriodoAcademicoEntity::class,
        GradoEntity::class,
        MatriculaEntity::class,
        NotaFinalEntity::class,
        ConfiguracionEntity::class,
    ],
    version = 2,
    exportSchema = false,
)
abstract class BaseDatosSdep : RoomDatabase() {

    abstract fun registroDao(): RegistroDao
    abstract fun operacionDao(): OperacionDao
    abstract fun estadoSyncDao(): EstadoSyncDao
    abstract fun conflictoDao(): ConflictoDao

    abstract fun identidadDao(): IdentidadDao
    abstract fun operacionEntradaDao(): OperacionEntradaDao
    abstract fun sesionUsuarioDao(): SesionUsuarioDao
    abstract fun empleadoDao(): EmpleadoDao
    abstract fun documentoDao(): DocumentoDao
    abstract fun incidenciaDao(): IncidenciaDao
    abstract fun contratoDao(): ContratoDao
    abstract fun pagoDao(): PagoDao
    abstract fun estudianteDao(): EstudianteDao
    abstract fun periodoAcademicoDao(): PeriodoAcademicoDao
    abstract fun gradoDao(): GradoDao
    abstract fun matriculaDao(): MatriculaDao
    abstract fun notaFinalDao(): NotaFinalDao
    abstract fun configuracionDao(): ConfiguracionDao

    companion object {

        /**
         * v1 → v2: espejo completo y fin de las cuentas locales.
         *
         * Se crean las tablas nuevas con exactamente la forma que Room espera
         * (mismos nombres de columna, afinidades e índices) y se elimina
         * `usuarios`, cuyas contraseñas locales dejan de existir porque el
         * ingreso ahora se valida contra el nodo central.
         */
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                // Las cuentas locales se sustituyen por la base institucional
                db.execSQL("DROP TABLE IF EXISTS usuarios")

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS identidades (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "tabla TEXT NOT NULL, uuid TEXT NOT NULL, idLocal INTEGER NOT NULL)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS index_identidades_tabla_uuid " +
                        "ON identidades (tabla, uuid)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS index_identidades_tabla_idLocal " +
                        "ON identidades (tabla, idLocal)",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS operaciones_entrada (" +
                        "opId TEXT NOT NULL, tabla TEXT NOT NULL, filaUuid TEXT NOT NULL, " +
                        "operacion TEXT NOT NULL, payload TEXT NOT NULL, creadoEn INTEGER NOT NULL, " +
                        "motivo TEXT, intentos INTEGER NOT NULL, PRIMARY KEY(opId))",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_operaciones_entrada_filaUuid " +
                        "ON operaciones_entrada (filaUuid)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_operaciones_entrada_creadoEn " +
                        "ON operaciones_entrada (creadoEn)",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS sesion_usuario (" +
                        "id INTEGER NOT NULL, usuario TEXT NOT NULL, nombreCompleto TEXT, " +
                        "rol TEXT NOT NULL, expiraEn INTEGER NOT NULL, " +
                        "debeCambiarPassword INTEGER NOT NULL, actualizadoEn INTEGER NOT NULL, " +
                        "PRIMARY KEY(id))",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS empleados (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "nombres TEXT NOT NULL, apellidos TEXT NOT NULL, cedula TEXT NOT NULL, " +
                        "fecha_nacimiento TEXT, genero TEXT, estado_civil TEXT, nacionalidad TEXT, " +
                        "peso REAL, altura REAL, tipo_sangre TEXT, foto_ruta TEXT, " +
                        "telefono TEXT, celular TEXT, email TEXT, direccion TEXT, ciudad TEXT, " +
                        "estado TEXT, codigo_postal TEXT, " +
                        "tipo_empleado TEXT NOT NULL, cargo TEXT NOT NULL, departamento TEXT NOT NULL, " +
                        "fecha_contratacion TEXT NOT NULL, fecha_terminacion TEXT, " +
                        "salario_base REAL NOT NULL, activo INTEGER NOT NULL, " +
                        "nivel_educativo TEXT, especialidad TEXT, titulo_obtenido TEXT, " +
                        "titulo_secundaria TEXT, institucion_bancaria TEXT, numero_cuenta TEXT, " +
                        "tipo_cuenta TEXT, carnet_discapacidad TEXT, " +
                        "enfermedades_preexistentes TEXT, alergias_medicamentosas TEXT, " +
                        "alergias_alimentarias TEXT, tipo_contratacion TEXT, hijos TEXT, " +
                        "observaciones TEXT, contacto_emergencia_nombre TEXT, " +
                        "contacto_emergencia_telefono TEXT, contacto_emergencia_relacion TEXT, " +
                        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS index_empleados_cedula ON empleados (cedula)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_empleados_apellidos ON empleados (apellidos)",
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS index_empleados_activo ON empleados (activo)")

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS documentos (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "empleado_id INTEGER NOT NULL, tipo_documento TEXT NOT NULL, " +
                        "titulo TEXT NOT NULL, descripcion TEXT, numero_documento TEXT, " +
                        "fecha_emision TEXT, fecha_vencimiento TEXT, nombre_archivo TEXT NOT NULL, " +
                        "ruta_archivo TEXT NOT NULL, tamano_bytes INTEGER, tipo_mime TEXT, " +
                        "contenido_hash TEXT, contenido_binario BLOB, " +
                        "activo INTEGER NOT NULL, observaciones TEXT, " +
                        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_documentos_empleadoId " +
                        "ON documentos (empleadoId)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_documentos_tipoDocumento " +
                        "ON documentos (tipoDocumento)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_documentos_activo ON documentos (activo)",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS incidencias (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "empleado_id INTEGER NOT NULL, tipo_incidencia TEXT NOT NULL, " +
                        "estado TEXT NOT NULL, fecha_inicio TEXT NOT NULL, fecha_fin TEXT NOT NULL, " +
                        "fecha_solicitud TEXT NOT NULL, fecha_aprobacion TEXT, " +
                        "motivo TEXT NOT NULL, descripcion TEXT, " +
                        "dias_solicitados INTEGER NOT NULL, dias_aprobados INTEGER, " +
                        "documento_soporte_nombre TEXT, documento_soporte_ruta TEXT, " +
                        "documento_soporte_hash TEXT, documento_soporte_binario BLOB, " +
                        "aprobado_por TEXT, comentarios_aprobacion TEXT, " +
                        "afecta_nominas INTEGER NOT NULL, descuento_dias REAL, observaciones TEXT, " +
                        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_incidencias_empleadoId " +
                        "ON incidencias (empleadoId)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_incidencias_tipoIncidencia " +
                        "ON incidencias (tipoIncidencia)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_incidencias_estado ON incidencias (estado)",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS contratos (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "empleado_id INTEGER NOT NULL, numero TEXT NOT NULL, tipo TEXT NOT NULL, " +
                        "estado TEXT NOT NULL, cargo TEXT NOT NULL, departamento TEXT, " +
                        "salario_pactado REAL NOT NULL, horas_semanales INTEGER NOT NULL, " +
                        "fecha_inicio TEXT NOT NULL, fecha_fin TEXT, " +
                        "renovacion_automatica INTEGER NOT NULL, contrato_anterior_id INTEGER, " +
                        "archivo_ruta TEXT, clausulas TEXT, motivo_terminacion TEXT, " +
                        "fecha_terminacion TEXT, liquidacion_monto REAL NOT NULL, " +
                        "aprobado_por TEXT, observaciones TEXT, " +
                        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS index_contratos_numero ON contratos (numero)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_contratos_empleadoId ON contratos (empleadoId)",
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS index_contratos_estado ON contratos (estado)")

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS pagos (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "empleado_id INTEGER NOT NULL, tipo_pago TEXT NOT NULL, " +
                        "metodo_pago TEXT NOT NULL, periodo_inicio TEXT NOT NULL, " +
                        "periodo_fin TEXT NOT NULL, fecha_pago TEXT NOT NULL, " +
                        "monto_bruto REAL NOT NULL, monto_neto REAL NOT NULL, " +
                        "descuentos REAL NOT NULL, bonificaciones REAL NOT NULL, " +
                        "horas_extra REAL NOT NULL, salario_base REAL NOT NULL, " +
                        "deduccion_seguro REAL NOT NULL, deduccion_pension REAL NOT NULL, " +
                        "deduccion_impuesto REAL NOT NULL, otras_deducciones REAL NOT NULL, " +
                        "modalidad_calculo TEXT NOT NULL, base_gravable REAL NOT NULL, " +
                        "horas_extra_diurnas REAL NOT NULL, horas_extra_nocturnas REAL NOT NULL, " +
                        "horas_extra_feriadas REAL NOT NULL, aguinaldo REAL NOT NULL, " +
                        "bono_vacacional REAL NOT NULL, aporte_seguro_patronal REAL NOT NULL, " +
                        "aporte_pension_patronal REAL NOT NULL, isr_tramo TEXT, " +
                        "dias_laborados INTEGER, dias_periodo INTEGER, prorrateado INTEGER, " +
                        "descripcion TEXT, referencia_pago TEXT, observaciones TEXT, " +
                        "pagado INTEGER NOT NULL, fecha_registro_pago TEXT, " +
                        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_pagos_empleadoId ON pagos (empleadoId)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_pagos_periodoInicio ON pagos (periodo_inicio)",
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS index_pagos_pagado ON pagos (pagado)")

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS estudiantes (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "nombres TEXT NOT NULL, apellidos TEXT NOT NULL, cedula TEXT, " +
                        "fecha_nacimiento TEXT, genero TEXT, nivel TEXT NOT NULL, " +
                        "representante TEXT, telefono TEXT, telefono_representante TEXT, " +
                        "email TEXT, direccion TEXT, observaciones TEXT, activo INTEGER NOT NULL, " +
                        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS index_estudiantes_cedula " +
                        "ON estudiantes (cedula)",
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS index_estudiantes_nivel ON estudiantes (nivel)")
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_estudiantes_activo ON estudiantes (activo)",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS periodos_academicos (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "nombre TEXT NOT NULL, fecha_inicio TEXT, fecha_fin TEXT, " +
                        "estado TEXT NOT NULL, cerrado_en TEXT, cerrado_por TEXT, " +
                        "observaciones TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS index_periodos_academicos_nombre " +
                        "ON periodos_academicos (nombre)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_periodos_academicos_estado " +
                        "ON periodos_academicos (estado)",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS grados (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "periodo_id INTEGER NOT NULL, nivel TEXT NOT NULL, " +
                        "nombre TEXT NOT NULL, seccion TEXT NOT NULL, " +
                        "profesor_uuid TEXT, observaciones TEXT, " +
                        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS index_grados_periodoId ON grados (periodoId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_grados_nivel ON grados (nivel)")

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS matriculas (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "estudiante_id INTEGER NOT NULL, grado_id INTEGER NOT NULL, " +
                        "fecha_matricula TEXT NOT NULL, activa INTEGER NOT NULL, " +
                        "observaciones TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_matriculas_estudianteId " +
                        "ON matriculas (estudianteId)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_matriculas_gradoId ON matriculas (gradoId)",
                )
                db.execSQL("CREATE INDEX IF NOT EXISTS index_matriculas_activa ON matriculas (activa)")

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS notas_finales (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "estudiante_id INTEGER NOT NULL, grado_id INTEGER NOT NULL, " +
                        "materia TEXT NOT NULL, calificacion REAL NOT NULL, " +
                        "registrado_por TEXT, observaciones TEXT, " +
                        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS " +
                        "index_notas_finales_estudianteId_gradoId_materia " +
                        "ON notas_finales (estudianteId, gradoId, materia)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_notas_finales_gradoId " +
                        "ON notas_finales (gradoId)",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS configuraciones (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "clave TEXT NOT NULL, valor TEXT, descripcion TEXT, " +
                        "tipo_dato TEXT NOT NULL, categoria TEXT, editable INTEGER NOT NULL, " +
                        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS index_configuraciones_clave " +
                        "ON configuraciones (clave)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_configuraciones_categoria " +
                        "ON configuraciones (categoria)",
                )
            }
        }
    }
}
