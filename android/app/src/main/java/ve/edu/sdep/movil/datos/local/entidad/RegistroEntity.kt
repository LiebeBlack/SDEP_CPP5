package ve.edu.sdep.movil.datos.local.entidad

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Registro de campo almacenado en el teléfono.
 *
 * ``uuid`` es la clave primaria y, a la vez, la identidad global de la fila en
 * el nodo central: se genera en el teléfono y no cambia nunca. Los sellos de
 * tiempo están en milisegundos desde la época para poder ordenar sin ambigüedad
 * y se convierten a ISO 8601 al enviarlos.
 *
 * ``estado`` no es un dato del registro sino su situación frente a la red
 * (pendiente, sincronizado o rechazado); sirve para que el usuario sepa qué
 * falta por llegar al sistema de escritorio.
 */
@Entity(
    tableName = "registros",
    indices = [
        Index("actualizadoEn"),
        Index("categoria"),
        Index("titulo"),
        Index("estado"),
    ],
)
data class RegistroEntity(
    @PrimaryKey val uuid: String,
    val titulo: String,
    val contenido: String,
    val categoria: String,
    val valor: Double?,
    val creadoEn: Long,
    val actualizadoEn: Long,
    val estado: String,
    val eliminado: Boolean,
    val dispositivo: String,
    val usuario: String,
    val ultimaSync: Long?,
)
