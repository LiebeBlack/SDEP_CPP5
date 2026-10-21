package ve.edu.sdep.movil.datos.local.entidad

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Estado de la sincronización con el nodo central.
 *
 * Es una sola fila (``id = 1``). ``cursor`` es el último ``seq`` global
 * aplicado: el servidor devuelve las operaciones posteriores y el teléfono no
 * vuelve a pedir lo que ya tiene. ``servidor`` y ``versionProtocolo`` se
 * guardan tras cada prueba de conexión para mostrarlos en Ajustes.
 */
@Entity(tableName = "estado_sincronizacion")
data class EstadoSyncEntity(
    @PrimaryKey val id: Int = 1,
    val cursor: Int = 0,
    val ultimaSync: Long? = null,
    val ultimoError: String? = null,
    val registrosRecibidos: Int = 0,
    val servidor: String? = null,
    val versionProtocolo: String? = null,
    val desfaseSegundos: Long? = null,
)
