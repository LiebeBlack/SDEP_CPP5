package ve.edu.sdep.movil.datos.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow
import ve.edu.sdep.movil.datos.local.entidad.*

/**
 * Acceso a las tablas espejo.
 *
 * Las lecturas que alimentan pantallas devuelven `Flow`: cada cambio local o
 * llegado de la red se refleja sin volver a pedir los datos. Las escrituras son
 * `suspend` y corren dentro de la transacción que abre el repositorio, junto
 * con la operación de la cola de salida.
 */
@Dao
interface IdentidadDao {

    @Query("SELECT idLocal FROM identidades WHERE tabla = :tabla AND uuid = :uuid LIMIT 1")
    suspend fun idLocalDe(tabla: String, uuid: String): Long?

    @Query("SELECT uuid FROM identidades WHERE tabla = :tabla AND idLocal = :idLocal LIMIT 1")
    suspend fun uuidDe(tabla: String, idLocal: Long): String?

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun vincular(identidad: IdentidadEntity)

    @Query("SELECT COUNT(*) FROM identidades")
    suspend fun contar(): Int
}

@Dao
interface OperacionEntradaDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun encolar(operacion: OperacionEntradaEntity)

    @Query("SELECT * FROM operaciones_entrada ORDER BY creadoEn LIMIT :limite")
    suspend fun pendientes(limite: Int = 100): List<OperacionEntradaEntity>

    @Query("SELECT COUNT(*) FROM operaciones_entrada")
    fun observarPendientes(): Flow<Int>

    @Query("DELETE FROM operaciones_entrada WHERE opId = :opId")
    suspend fun eliminar(opId: String)

    @Query("UPDATE operaciones_entrada SET intentos = intentos + 1 WHERE opId = :opId")
    suspend fun marcarIntento(opId: String)

    @Query(
        "DELETE FROM operaciones_entrada " +
            "WHERE intentos > 10 AND opId IN (:ids)",
    )
    suspend fun purgar(viejas: List<String>)
}

@Dao
interface SesionUsuarioDao {

    @Query("SELECT * FROM sesion_usuario WHERE id = 1 LIMIT 1")
    suspend fun obtener(): SesionUsuarioEntity?

    @Query("SELECT * FROM sesion_usuario WHERE id = 1 LIMIT 1")
    fun observar(): Flow<SesionUsuarioEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun guardar(sesion: SesionUsuarioEntity)

    @Query("DELETE FROM sesion_usuario")
    suspend fun limpiar()
}

// ----------------------------------------------------------------------
// Personal
// ----------------------------------------------------------------------
@Dao
interface EmpleadoDao {

    @Query("SELECT * FROM empleados WHERE activo = 1 ORDER BY apellidos, nombres")
    fun observarActivos(): Flow<List<EmpleadoEntity>>

    @Query("SELECT * FROM empleados ORDER BY apellidos, nombres")
    fun observarTodos(): Flow<List<EmpleadoEntity>>

    @Query("SELECT * FROM empleados WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): EmpleadoEntity?

    @Query("SELECT * FROM empleados WHERE id = :id LIMIT 1")
    fun observarPorId(id: Long): Flow<EmpleadoEntity?>

    @Query("SELECT * FROM empleados WHERE cedula = :cedula LIMIT 1")
    suspend fun buscarPorCedula(cedula: String): EmpleadoEntity?

    @Query(
        "SELECT * FROM empleados WHERE activo = 1 AND " +
            "(nombres LIKE '%' || :termino || '%' OR apellidos LIKE '%' || :termino || '%' " +
            "OR cedula LIKE '%' || :termino || '%' OR cargo LIKE '%' || :termino || '%') " +
            "ORDER BY apellidos, nombres",
    )
    fun buscar(termino: String): Flow<List<EmpleadoEntity>>

    @Query("SELECT COUNT(*) FROM empleados WHERE activo = 1")
    fun observarCantidad(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(empleado: EmpleadoEntity): Long

    @Query("DELETE FROM empleados WHERE id = :id")
    suspend fun borrar(id: Long)

    @Query("UPDATE empleados SET activo = 0 WHERE id = :id")
    suspend fun desactivar(id: Long)

    @Query("SELECT * FROM empleados ORDER BY apellidos")
    suspend fun listarTodos(): List<EmpleadoEntity>
}

@Dao
interface DocumentoDao {

    @Query("SELECT * FROM documentos WHERE activo = 1 ORDER BY fecha_vencimiento, titulo")
    fun observarTodos(): Flow<List<DocumentoEntity>>

    @Query("SELECT * FROM documentos WHERE empleadoId = :empleadoId AND activo = 1 ORDER BY titulo")
    fun observarPorEmpleado(empleadoId: Long): Flow<List<DocumentoEntity>>

    @Query("SELECT * FROM documentos WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): DocumentoEntity?

    @Query("SELECT * FROM documentos WHERE id = :id LIMIT 1")
    fun observarPorId(id: Long): Flow<DocumentoEntity?>

    @Query(
        "SELECT * FROM documentos WHERE activo = 1 AND fecha_vencimiento IS NOT NULL " +
            "AND fecha_vencimiento <= :limite ORDER BY fecha_vencimiento",
    )
    fun observarVencidos(limite: String): Flow<List<DocumentoEntity>>

    @Query("SELECT COUNT(*) FROM documentos WHERE activo = 1")
    fun observarCantidad(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(documento: DocumentoEntity): Long

    @Query("DELETE FROM documentos WHERE id = :id")
    suspend fun borrar(id: Long)

    @Query("UPDATE documentos SET contenidoBinario = :bytes WHERE id = :id")
    suspend fun guardarContenido(id: Long, bytes: ByteArray)
}

@Dao
interface IncidenciaDao {

    @Query("SELECT * FROM incidencias ORDER BY fecha_inicio DESC")
    fun observarTodas(): Flow<List<IncidenciaEntity>>

    @Query("SELECT * FROM incidencias WHERE estado = :estado ORDER BY fecha_inicio DESC")
    fun observarPorEstado(estado: String): Flow<List<IncidenciaEntity>>

    @Query("SELECT * FROM incidencias WHERE empleadoId = :empleadoId ORDER BY fecha_inicio DESC")
    fun observarPorEmpleado(empleadoId: Long): Flow<List<IncidenciaEntity>>

    @Query("SELECT * FROM incidencias WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): IncidenciaEntity?

    @Query("SELECT * FROM incidencias WHERE id = :id LIMIT 1")
    fun observarPorId(id: Long): Flow<IncidenciaEntity?>

    @Query("SELECT COUNT(*) FROM incidencias WHERE estado = 'pendiente'")
    fun observarPendientes(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(incidencia: IncidenciaEntity): Long

    @Query("DELETE FROM incidencias WHERE id = :id")
    suspend fun borrar(id: Long)
}

@Dao
interface ContratoDao {

    @Query("SELECT * FROM contratos ORDER BY fecha_inicio DESC")
    fun observarTodos(): Flow<List<ContratoEntity>>

    @Query("SELECT * FROM contratos WHERE estado = :estado ORDER BY fecha_fin")
    fun observarPorEstado(estado: String): Flow<List<ContratoEntity>>

    @Query("SELECT * FROM contratos WHERE empleadoId = :empleadoId ORDER BY fecha_inicio DESC")
    fun observarPorEmpleado(empleadoId: Long): Flow<List<ContratoEntity>>

    @Query(
        "SELECT * FROM contratos WHERE estado = 'vigente' AND fecha_fin IS NOT NULL " +
            "AND fecha_fin <= :limite ORDER BY fecha_fin",
    )
    fun observarPorVencer(limite: String): Flow<List<ContratoEntity>>

    @Query("SELECT * FROM contratos WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): ContratoEntity?

    @Query("SELECT * FROM contratos WHERE id = :id LIMIT 1")
    fun observarPorId(id: Long): Flow<ContratoEntity?>

    @Query("SELECT * FROM contratos WHERE numero = :numero LIMIT 1")
    suspend fun buscarPorNumero(numero: String): ContratoEntity?

    @Query("SELECT * FROM contratos WHERE estado = 'vigente' AND empleadoId = :empleadoId LIMIT 1")
    suspend fun vigenteDe(empleadoId: Long): ContratoEntity?

    @Query("SELECT COUNT(*) FROM contratos")
    fun observarCantidad(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(contrato: ContratoEntity): Long

    @Query("DELETE FROM contratos WHERE id = :id")
    suspend fun borrar(id: Long)
}

// ----------------------------------------------------------------------
// Nómina
// ----------------------------------------------------------------------
@Dao
interface PagoDao {

    @Query("SELECT * FROM pagos WHERE periodo_inicio >= :desde AND periodo_inicio <= :hasta ORDER BY fecha_pago DESC")
    fun observarPorPeriodo(desde: String, hasta: String): Flow<List<PagoEntity>>

    @Query("SELECT * FROM pagos ORDER BY periodo_inicio DESC, id DESC")
    fun observarTodos(): Flow<List<PagoEntity>>

    @Query("SELECT * FROM pagos WHERE empleadoId = :empleadoId ORDER BY periodo_inicio DESC")
    fun observarPorEmpleado(empleadoId: Long): Flow<List<PagoEntity>>

    @Query("SELECT * FROM pagos WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): PagoEntity?

    @Query("SELECT * FROM pagos WHERE id = :id LIMIT 1")
    fun observarPorId(id: Long): Flow<PagoEntity?>

    @Query("SELECT COUNT(*) FROM pagos WHERE pagado = 0")
    fun observarPendientes(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(pago: PagoEntity): Long

    @Query("DELETE FROM pagos WHERE id = :id")
    suspend fun borrar(id: Long)
}

// ----------------------------------------------------------------------
// Académico
// ----------------------------------------------------------------------
@Dao
interface EstudianteDao {

    @Query("SELECT * FROM estudiantes WHERE activo = 1 ORDER BY apellidos, nombres")
    fun observarActivos(): Flow<List<EstudianteEntity>>

    @Query("SELECT * FROM estudiantes ORDER BY apellidos, nombres")
    fun observarTodos(): Flow<List<EstudianteEntity>>

    @Query(
        "SELECT * FROM estudiantes WHERE activo = 1 AND " +
            "(nombres LIKE '%' || :termino || '%' OR apellidos LIKE '%' || :termino || '%' " +
            "OR cedula LIKE '%' || :termino || '%') ORDER BY apellidos, nombres",
    )
    fun buscar(termino: String): Flow<List<EstudianteEntity>>

    @Query("SELECT * FROM estudiantes WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): EstudianteEntity?

    @Query("SELECT * FROM estudiantes WHERE id = :id LIMIT 1")
    fun observarPorId(id: Long): Flow<EstudianteEntity?>

    @Query("SELECT * FROM estudiantes WHERE cedula = :cedula LIMIT 1")
    suspend fun buscarPorCedula(cedula: String): EstudianteEntity?

    @Query("SELECT COUNT(*) FROM estudiantes WHERE activo = 1")
    fun observarCantidad(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(estudiante: EstudianteEntity): Long

    @Query("DELETE FROM estudiantes WHERE id = :id")
    suspend fun borrar(id: Long)
}

@Dao
interface PeriodoAcademicoDao {

    @Query("SELECT * FROM periodos_academicos ORDER BY nombre DESC")
    fun observarTodos(): Flow<List<PeriodoAcademicoEntity>>

    @Query("SELECT * FROM periodos_academicos WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): PeriodoAcademicoEntity?

    @Query("SELECT * FROM periodos_academicos WHERE id = :id LIMIT 1")
    fun observarPorId(id: Long): Flow<PeriodoAcademicoEntity?>

    @Query("SELECT * FROM periodos_academicos WHERE nombre = :nombre LIMIT 1")
    suspend fun buscarPorNombre(nombre: String): PeriodoAcademicoEntity?

    @Query("SELECT * FROM periodos_academicos WHERE estado = 'abierto' ORDER BY nombre DESC LIMIT 1")
    suspend fun enCurso(): PeriodoAcademicoEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(periodo: PeriodoAcademicoEntity): Long

    @Query("DELETE FROM periodos_academicos WHERE id = :id")
    suspend fun borrar(id: Long)
}

@Dao
interface GradoDao {

    @Query("SELECT * FROM grados ORDER BY nivel, nombre, seccion")
    fun observarTodos(): Flow<List<GradoEntity>>

    @Query("SELECT * FROM grados WHERE periodoId = :periodoId ORDER BY nivel, nombre, seccion")
    fun observarPorPeriodo(periodoId: Long): Flow<List<GradoEntity>>

    @Query("SELECT * FROM grados WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): GradoEntity?

    @Query("SELECT * FROM grados WHERE id = :id LIMIT 1")
    fun observarPorId(id: Long): Flow<GradoEntity?>

    @Query(
        "SELECT * FROM grados WHERE periodoId = :periodoId AND nombre = :nombre " +
            "AND seccion = :seccion LIMIT 1",
    )
    suspend fun buscarPorClave(periodoId: Long, nombre: String, seccion: String): GradoEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(grado: GradoEntity): Long

    @Query("DELETE FROM grados WHERE id = :id")
    suspend fun borrar(id: Long)
}

@Dao
interface MatriculaDao {

    @Query("SELECT * FROM matriculas WHERE gradoId = :gradoId AND activa = 1 ORDER BY id")
    fun observarPorGrado(gradoId: Long): Flow<List<MatriculaEntity>>

    @Query("SELECT * FROM matriculas WHERE estudianteId = :estudianteId ORDER BY fecha_matricula DESC")
    fun observarPorEstudiante(estudianteId: Long): Flow<List<MatriculaEntity>>

    @Query("SELECT * FROM matriculas WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): MatriculaEntity?

    @Query(
        "SELECT * FROM matriculas WHERE estudianteId = :estudianteId AND gradoId = :gradoId " +
            "AND activa = 1 LIMIT 1",
    )
    suspend fun buscarActiva(estudianteId: Long, gradoId: Long): MatriculaEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(matricula: MatriculaEntity): Long

    @Query("DELETE FROM matriculas WHERE id = :id")
    suspend fun borrar(id: Long)
}

@Dao
interface NotaFinalDao {

    @Query("SELECT * FROM notas_finales WHERE gradoId = :gradoId ORDER BY materia")
    fun observarPorGrado(gradoId: Long): Flow<List<NotaFinalEntity>>

    @Query("SELECT * FROM notas_finales WHERE estudianteId = :estudianteId ORDER BY materia")
    fun observarPorEstudiante(estudianteId: Long): Flow<List<NotaFinalEntity>>

    @Query("SELECT * FROM notas_finales WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): NotaFinalEntity?

    @Query(
        "SELECT * FROM notas_finales WHERE estudianteId = :estudianteId AND gradoId = :gradoId " +
            "AND materia = :materia LIMIT 1",
    )
    suspend fun buscarPorClave(estudianteId: Long, gradoId: Long, materia: String): NotaFinalEntity?

    @Query("SELECT COUNT(*) FROM notas_finales")
    fun observarCantidad(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(nota: NotaFinalEntity): Long

    @Query("DELETE FROM notas_finales WHERE id = :id")
    suspend fun borrar(id: Long)
}

// ----------------------------------------------------------------------
// Configuración
// ----------------------------------------------------------------------
@Dao
interface ConfiguracionDao {

    @Query("SELECT * FROM configuraciones ORDER BY categoria, clave")
    fun observarTodas(): Flow<List<ConfiguracionEntity>>

    @Query("SELECT * FROM configuraciones WHERE categoria = :categoria ORDER BY clave")
    fun observarPorCategoria(categoria: String): Flow<List<ConfiguracionEntity>>

    @Query("SELECT * FROM configuraciones WHERE clave = :clave LIMIT 1")
    suspend fun buscarPorClave(clave: String): ConfiguracionEntity?

    @Query("SELECT valor FROM configuraciones WHERE clave = :clave LIMIT 1")
    suspend fun valor(clave: String): String?

    @Query("SELECT COUNT(*) FROM configuraciones")
    fun observarCantidad(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(configuracion: ConfiguracionEntity): Long

    @Query("DELETE FROM configuraciones WHERE id = :id")
    suspend fun borrar(id: Long)
}
