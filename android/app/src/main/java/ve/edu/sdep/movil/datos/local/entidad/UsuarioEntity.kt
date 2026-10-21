package ve.edu.sdep.movil.datos.local.entidad

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Cuenta de la aplicación.
 *
 * Se guarda la derivación PBKDF2 de la contraseña, nunca la contraseña. El
 * token biométrico se guarda también como hash: el valor en claro vive en la
 * bóveda cifrada y solo se usa para comprobar que el usuario que acaba de
 * autenticarse con el sensor es el mismo que activó esa comodidad.
 *
 * Las cuentas son locales de este teléfono. La tabla ``usuarios`` del sistema
 * de escritorio no se replica: cada puesto administra las suyas.
 */
@Entity(
    tableName = "usuarios",
    indices = [Index(value = ["usuario"], unique = true)],
)
data class UsuarioEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val nombre: String,
    val usuario: String,
    val hashContrasena: String,
    val rol: String,
    val activo: Boolean,
    val tokenBiometricoHash: String?,
    val creadoEn: Long,
)
