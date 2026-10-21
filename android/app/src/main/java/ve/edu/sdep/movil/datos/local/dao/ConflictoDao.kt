package ve.edu.sdep.movil.datos.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import kotlinx.coroutines.flow.Flow
import ve.edu.sdep.movil.datos.local.entidad.ConflictoEntity

/** Choques detectados al aplicar cambios del nodo central */
@Dao
interface ConflictoDao {

    @Insert
    suspend fun insertar(conflicto: ConflictoEntity)

    @Query("SELECT * FROM conflictos ORDER BY momento DESC")
    fun observarTodos(): Flow<List<ConflictoEntity>>

    @Query("SELECT COUNT(*) FROM conflictos WHERE revisado = 0")
    fun observarPendientes(): Flow<Int>

    @Query(
        "SELECT COUNT(*) FROM conflictos WHERE revisado = 0 AND filaUuid = :filaUuid",
    )
    suspend fun contarPendientesDe(filaUuid: String): Int

    @Query("UPDATE conflictos SET revisado = 1 WHERE id = :id")
    suspend fun marcarRevisado(id: Long)

    @Query("UPDATE conflictos SET revisado = 1")
    suspend fun marcarTodosRevisados()

    @Query("DELETE FROM conflictos WHERE revisado = 1")
    suspend fun purgarRevisados()
}
