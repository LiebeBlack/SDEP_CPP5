package ve.edu.sdep.movil.sincronizacion

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import ve.edu.sdep.movil.datos.repositorio.ConfiguracionRepositorio
import ve.edu.sdep.movil.datos.repositorio.SincronizacionRepositorio
import ve.edu.sdep.movil.dominio.modelo.Resultado

/**
 * Sincronización en segundo plano.
 *
 * WorkManager la ejecuta con red disponible, aunque la app esté cerrada, y
 * aplica espera creciente si el nodo central no responde. Un fallo de token no
 * se reintenta (no se arregla solo); un corte de red sí.
 */
@HiltWorker
class TrabajoSincronizacion @AssistedInject constructor(
    @Assisted contexto: Context,
    @Assisted parametros: WorkerParameters,
    private val sincronizacion: SincronizacionRepositorio,
    private val configuracion: ConfiguracionRepositorio,
) : CoroutineWorker(contexto, parametros) {

    override suspend fun doWork(): Result {
        val actual = configuracion.cargar()
        // Si el administrador desactivó la sincronización, no se gasta batería
        // ni se insiste contra un servicio que no corresponde.
        if (!actual.activa) return Result.success()

        return when (val resultado = sincronizacion.sincronizar()) {
            is Resultado.Exito -> Result.success()
            // Un fallo definitivo (token revocado, servidor mal configurado) no
            // debe devolver ``failure``: en un trabajo periódico eso lo cancelaría
            // para siempre. El error queda visible en Ajustes y el próximo ciclo
            // volverá a intentarlo cuando el administrador lo corrija.
            is Resultado.Fallo -> if (resultado.reintentable) Result.retry() else Result.success()
        }
    }
}
