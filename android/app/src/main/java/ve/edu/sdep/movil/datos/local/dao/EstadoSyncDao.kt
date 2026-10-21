package ve.edu.sdep.movil.datos.local.dao

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow
import ve.edu.sdep.movil.datos.local.entidad.EstadoSyncEntity

/** Estado persistente del cursor de sincronización */
@Dao
interface EstadoSyncDao {

    @Query("SELECT * FROM estado_sincronizacion WHERE id = 1")
    fun observar(): Flow<EstadoSyncEntity?>

    @Query("SELECT * FROM estado_sincronizacion WHERE id = 1")
    suspend fun obtener(): EstadoSyncEntity?

    @Upsert
    suspend fun guardar(estado: EstadoSyncEntity)
}
