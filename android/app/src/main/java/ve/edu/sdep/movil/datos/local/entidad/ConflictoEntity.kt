package ve.edu.sdep.movil.datos.local.entidad

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Choque entre una edición local pendiente y una escritura llegada del nodo.
 *
 * La app no arbitra: cuando detecta que el servidor trae un valor distinto para
 * un registro con cambios aún sin enviar, conserva lo local, deja la operación
 * en la cola (el nodo central decidirá con las marcas de tiempo) y anota aquí el
 * choque para que el usuario lo vea. Nada se descarta en silencio.
 */
@Entity(
    tableName = "conflictos",
    indices = [Index("filaUuid"), Index("revisado")],
)
data class ConflictoEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    /** Tabla del espejo donde ocurrió (vacío en los choques heredados) */
    @ColumnInfo(defaultValue = "''") val tabla: String = "",
    val filaUuid: String,
    val titulo: String,
    val campo: String,
    val valorLocal: String,
    val valorRemoto: String,
    /** «local» o «remoto»: qué escritura quedó vigente */
    @ColumnInfo(defaultValue = "''") val ganador: String = "",
    /** Regla del motor que decidió, para poder auditar la decisión */
    @ColumnInfo(defaultValue = "''") val regla: String = "",
    val momento: Long,
    val revisado: Boolean,
)
