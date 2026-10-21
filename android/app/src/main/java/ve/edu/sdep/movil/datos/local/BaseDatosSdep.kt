package ve.edu.sdep.movil.datos.local

import androidx.room.Database
import androidx.room.RoomDatabase
import ve.edu.sdep.movil.datos.local.dao.ConflictoDao
import ve.edu.sdep.movil.datos.local.dao.EstadoSyncDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.dao.RegistroDao
import ve.edu.sdep.movil.datos.local.dao.UsuarioDao
import ve.edu.sdep.movil.datos.local.entidad.ConflictoEntity
import ve.edu.sdep.movil.datos.local.entidad.EstadoSyncEntity
import ve.edu.sdep.movil.datos.local.entidad.OperacionPendienteEntity
import ve.edu.sdep.movil.datos.local.entidad.RegistroEntity
import ve.edu.sdep.movil.datos.local.entidad.UsuarioEntity

/**
 * Base de datos local del teléfono.
 *
 * Cinco tablas: los registros, las cuentas, la cola de salida, el estado de la
 * sincronización y la bandeja de conflictos. No se guarda aquí ninguna copia
 * de los datos del escritorio que el teléfono no necesite: la app es un puesto
 * de captura, no un espejo de todo el sistema.
 *
 * El esquema está en la versión 1. Si en el futuro se añade una columna, hace
 * falta una migración explícita: ``exportSchema = false`` evita generar el JSON
 * del esquema, pero no autoriza a borrar los datos del usuario al actualizar.
 */
@Database(
    entities = [
        RegistroEntity::class,
        UsuarioEntity::class,
        OperacionPendienteEntity::class,
        EstadoSyncEntity::class,
        ConflictoEntity::class,
    ],
    version = 1,
    exportSchema = false,
)
abstract class BaseDatosSdep : RoomDatabase() {

    abstract fun registroDao(): RegistroDao
    abstract fun usuarioDao(): UsuarioDao
    abstract fun operacionDao(): OperacionDao
    abstract fun estadoSyncDao(): EstadoSyncDao
    abstract fun conflictoDao(): ConflictoDao
}
