package ve.edu.sdep.movil.datos.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow
import ve.edu.sdep.movil.datos.local.entidad.RegistroEntity

/**
 * Acceso a los registros.
 *
 * Las consultas de lectura devuelven ``Flow``: cada cambio se refleja en la
 * pantalla sin que esta tenga que pedir los datos de nuevo. Las escrituras son
 * suspendidas y se ejecutan dentro de la transacción que abre el repositorio,
 * junto con la operación de la cola de salida.
 */
@Dao
interface RegistroDao {

    /** Todos los registros vigentes, del más reciente al más antiguo */
    @Query("SELECT * FROM registros WHERE eliminado = 0 ORDER BY actualizadoEn DESC")
    fun observarActivos(): Flow<List<RegistroEntity>>

    /** Un registro por su identidad global */
    @Query("SELECT * FROM registros WHERE uuid = :uuid LIMIT 1")
    fun observarPorUuid(uuid: String): Flow<RegistroEntity?>

    /** Lectura puntual, para usarla dentro de una transacción */
    @Query("SELECT * FROM registros WHERE uuid = :uuid LIMIT 1")
    suspend fun buscarPorUuid(uuid: String): RegistroEntity?

    /** Todos los registros, incluidos los borrados: lo usa la mezcla */
    @Query("SELECT * FROM registros")
    suspend fun listarTodos(): List<RegistroEntity>

    /** Alta (o reemplazo completo) de un registro */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertar(registro: RegistroEntity)

    /** Modificación de un registro existente */
    @Update
    suspend fun actualizar(registro: RegistroEntity)

    /** Borrado físico; la app solo lo usa para purgar filas ya sincronizadas */
    @Query("DELETE FROM registros WHERE uuid = :uuid")
    suspend fun borrar(uuid: String)

    /** Elimina de forma definitiva los registros borrados que ya viajaron */
    @Query("DELETE FROM registros WHERE eliminado = 1 AND estado = 'SINCRONIZADO'")
    suspend fun purgarSincronizados()

    /** Registros con cambios aún no confirmados por el servidor */
    @Query("SELECT COUNT(*) FROM registros WHERE estado = 'PENDIENTE' AND eliminado = 0")
    fun observarPendientes(): Flow<Int>
}
