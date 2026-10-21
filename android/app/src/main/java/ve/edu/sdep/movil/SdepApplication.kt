package ve.edu.sdep.movil

import android.app.Application
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.repositorio.ConfiguracionRepositorio
import ve.edu.sdep.movil.sincronizacion.ProgramadorSync
import javax.inject.Inject

/**
 * Punto de entrada de la aplicación.
 *
 * WorkManager se inicializa a mano (el manifiesto elimina su inicializador
 * automático) para poder entregarle la fábrica de Hilt: sin eso, el trabajador
 * de sincronización no podría recibir el repositorio y fallaría al arrancar.
 *
 * Al iniciar se reprograma el trabajo periódico solo si la configuración está
 * activa y completa. Si el administrador desactivó la sincronización, no queda
 * un trabajo despertando al teléfono cada cuarto de hora sin motivo.
 */
@HiltAndroidApp
class SdepApplication : Application(), Configuration.Provider {

    @Inject
    lateinit var fabricaTrabajadores: HiltWorkerFactory

    @Inject
    lateinit var configuracion: ConfiguracionRepositorio

    @Inject
    lateinit var programador: ProgramadorSync

    private val alcance = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(fabricaTrabajadores)
            .build()

    override fun onCreate() {
        super.onCreate()
        alcance.launch {
            val actual = configuracion.cargar()
            if (actual.activa && actual.completa) {
                programador.programar(configuracion.periodoMinutos)
            } else {
                programador.cancelar()
            }
        }
    }
}
