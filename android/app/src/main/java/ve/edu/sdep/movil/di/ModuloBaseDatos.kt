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
import ve.edu.sdep.movil.datos.local.dao.BlobPendienteDao
import ve.edu.sdep.movil.datos.local.dao.CampoRemotoDao
import ve.edu.sdep.movil.datos.local.dao.ConflictoDao
import ve.edu.sdep.movil.datos.local.dao.ConfiguracionDao
import ve.edu.sdep.movil.datos.local.dao.ContratoDao
import ve.edu.sdep.movil.datos.local.dao.DocumentoDao
import ve.edu.sdep.movil.datos.local.dao.EmpleadoDao
import ve.edu.sdep.movil.datos.local.dao.EstadoSyncDao
import ve.edu.sdep.movil.datos.local.dao.EstudianteDao
import ve.edu.sdep.movil.datos.local.dao.GradoDao
import ve.edu.sdep.movil.datos.local.dao.IdentidadDao
import ve.edu.sdep.movil.datos.local.dao.IncidenciaDao
import ve.edu.sdep.movil.datos.local.dao.MatriculaDao
import ve.edu.sdep.movil.datos.local.dao.NotaFinalDao
import ve.edu.sdep.movil.datos.local.dao.OpAplicadaDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.dao.OperacionEntradaDao
import ve.edu.sdep.movil.datos.local.dao.PagoDao
import ve.edu.sdep.movil.datos.local.dao.PeriodoAcademicoDao
import ve.edu.sdep.movil.datos.local.dao.RegistroDao
import ve.edu.sdep.movil.datos.local.dao.SesionUsuarioDao
import ve.edu.sdep.movil.datos.local.dao.VersionFilaDao
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
            // Sin la migración explícita, Room destruiría y recrearía la base
            // al actualizar, perdiendo la cola de salida y lo capturado sin red.
            .addMigrations(
                BaseDatosSdep.MIGRATION_1_2,
                BaseDatosSdep.MIGRATION_2_3,
            )
            .build()

    @Provides
    fun registroDao(baseDatos: BaseDatosSdep): RegistroDao = baseDatos.registroDao()

    @Provides
    fun operacionDao(baseDatos: BaseDatosSdep): OperacionDao = baseDatos.operacionDao()

    @Provides
    fun estadoSyncDao(baseDatos: BaseDatosSdep): EstadoSyncDao = baseDatos.estadoSyncDao()

    @Provides
    fun conflictoDao(baseDatos: BaseDatosSdep): ConflictoDao = baseDatos.conflictoDao()

    @Provides
    fun identidadDao(baseDatos: BaseDatosSdep): IdentidadDao = baseDatos.identidadDao()

    @Provides
    fun operacionEntradaDao(baseDatos: BaseDatosSdep): OperacionEntradaDao =
        baseDatos.operacionEntradaDao()

    @Provides
    fun sesionUsuarioDao(baseDatos: BaseDatosSdep): SesionUsuarioDao = baseDatos.sesionUsuarioDao()

    @Provides
    fun empleadoDao(baseDatos: BaseDatosSdep): EmpleadoDao = baseDatos.empleadoDao()

    @Provides
    fun documentoDao(baseDatos: BaseDatosSdep): DocumentoDao = baseDatos.documentoDao()

    @Provides
    fun incidenciaDao(baseDatos: BaseDatosSdep): IncidenciaDao = baseDatos.incidenciaDao()

    @Provides
    fun contratoDao(baseDatos: BaseDatosSdep): ContratoDao = baseDatos.contratoDao()

    @Provides
    fun pagoDao(baseDatos: BaseDatosSdep): PagoDao = baseDatos.pagoDao()

    @Provides
    fun estudianteDao(baseDatos: BaseDatosSdep): EstudianteDao = baseDatos.estudianteDao()

    @Provides
    fun periodoAcademicoDao(baseDatos: BaseDatosSdep): PeriodoAcademicoDao =
        baseDatos.periodoAcademicoDao()

    @Provides
    fun gradoDao(baseDatos: BaseDatosSdep): GradoDao = baseDatos.gradoDao()

    @Provides
    fun matriculaDao(baseDatos: BaseDatosSdep): MatriculaDao = baseDatos.matriculaDao()

    @Provides
    fun notaFinalDao(baseDatos: BaseDatosSdep): NotaFinalDao = baseDatos.notaFinalDao()

    @Provides
    fun configuracionDao(baseDatos: BaseDatosSdep): ConfiguracionDao = baseDatos.configuracionDao()

    @Provides
    fun campoRemotoDao(baseDatos: BaseDatosSdep): CampoRemotoDao = baseDatos.campoRemotoDao()

    @Provides
    fun versionFilaDao(baseDatos: BaseDatosSdep): VersionFilaDao = baseDatos.versionFilaDao()

    @Provides
    fun opAplicadaDao(baseDatos: BaseDatosSdep): OpAplicadaDao = baseDatos.opAplicadaDao()

    @Provides
    fun blobPendienteDao(baseDatos: BaseDatosSdep): BlobPendienteDao = baseDatos.blobPendienteDao()

    @Provides
    @Singleton
    fun contexto(@ApplicationContext contexto: Context): Context = contexto
}
