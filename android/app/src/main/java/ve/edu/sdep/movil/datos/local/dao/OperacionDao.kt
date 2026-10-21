package ve.edu.sdep.movil.datos.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow
import ve.edu.sdep.movil.datos.local.entidad.OperacionPendienteEntity

/** Cola de operaciones que esperan viajar al nodo central */
@Dao
interface OperacionDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun encolar(operacion: OperacionPendienteEntity)

    /** Lote más antiguo pendiente de envío */
    @Query(
        "SELECT * FROM operaciones_pendientes WHERE estado = 'PENDIENTE' " +
            "ORDER BY creadoEn, opId LIMIT :limite",
    )
    suspend fun pendientes(limite: Int): List<OperacionPendienteEntity>

    /** Operaciones sin enviar; alimenta el contador de la barra de estado */
    @Query("SELECT COUNT(*) FROM operaciones_pendientes WHERE estado = 'PENDIENTE'")
    fun observarPendientes(): Flow<Int>

    /** Indica si un registro tiene cambios locales sin confirmar */
    @Query(
        "SELECT COUNT(*) FROM operaciones_pendientes " +
            "WHERE filaUuid = :filaUuid AND estado = 'PENDIENTE'",
    )
    suspend fun pendientesDe(filaUuid: String): Int

    /** El servidor confirmó estas operaciones: ya no hay que reenviarlas */
    @Query("DELETE FROM operaciones_pendientes WHERE opId IN (:ids)")
    suspend fun eliminar(ids: List<String>)

    /** Operación aceptada por el servidor pero todavía no confirmada en lote */
    @Query("UPDATE operaciones_pendientes SET estado = 'ENVIADA' WHERE opId IN (:ids)")
    suspend fun marcarEnviadas(ids: List<String>)

    /** Operación rechazada: se conserva con el motivo para poder mostrarla */
    @Query(
        "UPDATE operaciones_pendientes SET estado = 'RECHAZADA', motivo = :motivo " +
            "WHERE opId = :opId",
    )
    suspend fun marcarRechazada(opId: String, motivo: String)

    /** Purgar las rechazadas antiguas para que la tabla no crezca sin fin */
    @Query("DELETE FROM operaciones_pendientes WHERE estado = 'RECHAZADA'")
    suspend fun purgarRechazadas()
}
