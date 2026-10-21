package ve.edu.sdep.movil.datos.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow
import ve.edu.sdep.movil.datos.local.entidad.UsuarioEntity

/** Cuentas que pueden entrar a la aplicación en este teléfono */
@Dao
interface UsuarioDao {

    /** Cantidad de cuentas: si es 0, la app pide crear la primera */
    @Query("SELECT COUNT(*) FROM usuarios")
    suspend fun contar(): Int

    @Query("SELECT * FROM usuarios WHERE usuario = :usuario COLLATE NOCASE LIMIT 1")
    suspend fun buscarPorUsuario(usuario: String): UsuarioEntity?

    @Query("SELECT * FROM usuarios WHERE id = :id LIMIT 1")
    suspend fun buscarPorId(id: Long): UsuarioEntity?

    @Query("SELECT * FROM usuarios WHERE tokenBiometricoHash = :hash LIMIT 1")
    suspend fun buscarPorTokenBiometrico(hash: String): UsuarioEntity?

    @Query("SELECT * FROM usuarios ORDER BY nombre")
    fun observarTodas(): Flow<List<UsuarioEntity>>

    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insertar(usuario: UsuarioEntity): Long

    @Update
    suspend fun actualizar(usuario: UsuarioEntity)

    @Query("UPDATE usuarios SET tokenBiometricoHash = :hash WHERE id = :id")
    suspend fun asignarTokenBiometrico(id: Long, hash: String?)

    @Query("SELECT COUNT(*) FROM usuarios WHERE rol = 'ADMIN' AND activo = 1")
    suspend fun contarAdministradores(): Int
}
