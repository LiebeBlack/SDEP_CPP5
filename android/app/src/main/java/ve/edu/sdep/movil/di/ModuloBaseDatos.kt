package ve.edu.sdep.movil.di

import android.content.Context
import androidx.room.Room
import androidx.room.RoomDatabase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import ve.edu.sdep.movil.datos.local.BaseDatosSdep
import ve.edu.sdep.movil.datos.local.dao.ConflictoDao
import ve.edu.sdep.movil.datos.local.dao.EstadoSyncDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.dao.RegistroDao
import ve.edu.sdep.movil.datos.local.dao.UsuarioDao
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object ModuloBaseDatos {

    @Provides
    @Singleton
    fun baseDatos(@ApplicationContext contexto: Context): BaseDatosSdep =
        Room.databaseBuilder(contexto, BaseDatosSdep::class.java, "sdep_movil.db")
            // WAL permite que la sincronización escriba mientras la pantalla
            // sigue leyendo: el usuario no ve congelarse la lista.
            .setJournalMode(RoomDatabase.JournalMode.WRITE_AHEAD_LOGGING)
            .build()

    @Provides
    fun registroDao(baseDatos: BaseDatosSdep): RegistroDao = baseDatos.registroDao()

    @Provides
    fun usuarioDao(baseDatos: BaseDatosSdep): UsuarioDao = baseDatos.usuarioDao()

    @Provides
    fun operacionDao(baseDatos: BaseDatosSdep): OperacionDao = baseDatos.operacionDao()

    @Provides
    fun estadoSyncDao(baseDatos: BaseDatosSdep): EstadoSyncDao = baseDatos.estadoSyncDao()

    @Provides
    fun conflictoDao(baseDatos: BaseDatosSdep): ConflictoDao = baseDatos.conflictoDao()
}
