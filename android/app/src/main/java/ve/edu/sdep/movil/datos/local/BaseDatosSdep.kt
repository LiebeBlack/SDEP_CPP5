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
        // v2: metadata de mezcla (espejo de las tablas sync_* del escritorio)
        CampoRemotoEntity::class,
        VersionFilaEntity::class,
        OpAplicadaEntity::class,
        BlobPendienteEntity::class,
    ],
    version = 3,
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
    abstract fun campoRemotoDao(): CampoRemotoDao
    abstract fun versionFilaDao(): VersionFilaDao
    abstract fun opAplicadaDao(): OpAplicadaDao
    abstract fun blobPendienteDao(): BlobPendienteDao

    companion object {

        /**
         * v1 → v2: espejo completo y fin de las cuentas locales.
         *
         * Se crean las tablas nuevas con exactamente la forma que Room espera
         * (mismos nombres de columna, afinidades e índices) y se elimina
         * `usuarios`, cuyas contraseñas locales dejan de existir porque el
         * ingreso ahora se valida contra el nodo central.
         */
        /**
         * v2 → v3: la sesión cacheada guarda también la cédula.
         *
         * Sin ella, al reabrir sin red el aislamiento del WORKER no tendría
         * con qué comparar las filas del espejo. La columna es nullable para
         * no romper sesiones de cuentas administrativas.
         */
        val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE sesion_usuario ADD COLUMN cedula TEXT")
            }
        }

        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                // Las cuentas locales se sustituyen por la base institucional
                db.execSQL("DROP TABLE IF EXISTS usuarios")

                // La bandeja de conflictos gana contexto de mezcla en v2:
                // tabla, qué escritura ganó y con qué regla.
                db.execSQL("ALTER TABLE conflictos ADD COLUMN tabla TEXT NOT NULL DEFAULT ''")
                db.execSQL("ALTER TABLE conflictos ADD COLUMN ganador TEXT NOT NULL DEFAULT ''")
                db.execSQL("ALTER TABLE conflictos ADD COLUMN regla TEXT NOT NULL DEFAULT ''")

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
                        "creado_en_iso TEXT NOT NULL DEFAULT '', motivo TEXT, " +
                        "intentos INTEGER NOT NULL, PRIMARY KEY(opId))",
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
                    "CREATE INDEX IF NOT EXISTS index_documentos_empleado_id " +
                        "ON documentos (empleado_id)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_documentos_tipo_documento " +
                        "ON documentos (tipo_documento)",
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
                    "CREATE INDEX IF NOT EXISTS index_incidencias_empleado_id " +
                        "ON incidencias (empleado_id)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_incidencias_tipo_incidencia " +
                        "ON incidencias (tipo_incidencia)",
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
                    "CREATE INDEX IF NOT EXISTS index_contratos_empleado_id ON contratos (empleado_id)",
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
                    "CREATE INDEX IF NOT EXISTS index_pagos_empleado_id ON pagos (empleado_id)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_pagos_periodo_inicio ON pagos (periodo_inicio)",
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
                db.execSQL("CREATE INDEX IF NOT EXISTS index_grados_periodo_id ON grados (periodo_id)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_grados_nivel ON grados (nivel)")

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS matriculas (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "estudiante_id INTEGER NOT NULL, grado_id INTEGER NOT NULL, " +
                        "fecha_matricula TEXT NOT NULL, activa INTEGER NOT NULL, " +
                        "observaciones TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_matriculas_estudiante_id " +
                        "ON matriculas (estudiante_id)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_matriculas_grado_id ON matriculas (grado_id)",
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
                        "index_notas_finales_estudiante_id_grado_id_materia " +
                        "ON notas_finales (estudiante_id, grado_id, materia)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_notas_finales_grado_id " +
                        "ON notas_finales (grado_id)",
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

                // Metadata de mezcla: mismas columnas que las tablas sync_* del
                // agente de escritorio, para reproducir su motor campo a campo.
                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS campos_remotos (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "tabla TEXT NOT NULL, fila_uuid TEXT NOT NULL, campo TEXT NOT NULL, " +
                        "valor TEXT, op_id TEXT NOT NULL, dispositivo TEXT NOT NULL, " +
                        "actualizado_en TEXT NOT NULL)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS index_campos_remotos_tabla_fila_uuid_campo " +
                        "ON campos_remotos (tabla, fila_uuid, campo)",
                )
                db.execSQL(
                    "CREATE INDEX IF NOT EXISTS index_campos_remotos_fila_uuid " +
                        "ON campos_remotos (fila_uuid)",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS versiones_filas (" +
                        "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, " +
                        "tabla TEXT NOT NULL, fila_uuid TEXT NOT NULL, " +
                        "ultimo_op_id TEXT, actualizado_en TEXT, dispositivo TEXT, " +
                        "borrado INTEGER NOT NULL, borrado_en TEXT, borrado_op_id TEXT, " +
                        "borrado_dispositivo TEXT)",
                )
                db.execSQL(
                    "CREATE UNIQUE INDEX IF NOT EXISTS index_versiones_filas_tabla_fila_uuid " +
                        "ON versiones_filas (tabla, fila_uuid)",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS ops_aplicadas (" +
                        "opId TEXT NOT NULL, tabla TEXT NOT NULL, " +
                        "aplicado_en INTEGER NOT NULL, PRIMARY KEY(opId))",
                )

                db.execSQL(
                    "CREATE TABLE IF NOT EXISTS blobs_pendientes (" +
                        "hash TEXT NOT NULL, tamano INTEGER NOT NULL, tabla TEXT NOT NULL, " +
                        "fila_uuid TEXT NOT NULL, columna TEXT NOT NULL, " +
                        "direccion TEXT NOT NULL, estado TEXT NOT NULL, intentos INTEGER NOT NULL, " +
                        "creado_en INTEGER NOT NULL, actualizado_en INTEGER NOT NULL, " +
                        "PRIMARY KEY(hash))",
                )
            }
        }
    }
}
