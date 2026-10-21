package ve.edu.sdep.movil.datos.local.entidad

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Operación en cola de salida.
 *
 * Se escribe **en la misma transacción** que el cambio del registro, igual que
 * el journal del agente de escritorio: si el cambio se confirma, la operación
 * existe; si se deshace, no se anuncia nada. Así el teléfono puede trabajar sin
 * red y nada de lo que el usuario escribió se pierde.
 *
 * ``payload`` es el objeto JSON del protocolo con **solo los campos tocados**
 * (en un alta, todos los no nulos). Enviar la fila completa en una edición
 * pisaría columnas que otro equipo cambió mientras tanto; el motor de mezcla
 * del nodo central decide campo por campo.
 */
@Entity(
    tableName = "operaciones_pendientes",
    indices = [Index("filaUuid"), Index("estado"), Index("creadoEn")],
)
data class OperacionPendienteEntity(
    @PrimaryKey val opId: String,
    val tabla: String,
    val filaUuid: String,
    val operacion: String,
    val payload: String,
    val creadoEn: Long,
    val dispositivo: String,
    val usuario: String?,
    val estado: String,
    val motivo: String?,
)
