package ve.edu.sdep.movil.sincronizacion

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Programa la sincronización periódica.
 *
 * Android no permite periodos menores de 15 minutos, que es justamente el
 * mínimo razonable para una intranet escolar. La política ``UPDATE`` conserva
 * el trabajo y solo cambia su periodo cuando el administrador lo ajusta, sin
 * duplicarlo ni reiniciar la cuenta atrás.
 */
@Singleton
class ProgramadorSync @Inject constructor(
    @ApplicationContext private val contexto: Context,
) {

    fun programar(periodoMinutos: Int = 15) {
        val minutos = periodoMinutos.coerceIn(MINIMO_MINUTOS, MAXIMO_MINUTOS).toLong()
        val solicitud = PeriodicWorkRequestBuilder<TrabajoSincronizacion>(minutos, TimeUnit.MINUTES)
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build(),
            )
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
            .build()

        WorkManager.getInstance(contexto).enqueueUniquePeriodicWork(
            NOMBRE_TRABAJO,
            ExistingPeriodicWorkPolicy.UPDATE,
            solicitud,
        )
    }

    fun cancelar() {
        WorkManager.getInstance(contexto).cancelUniqueWork(NOMBRE_TRABAJO)
    }

    companion object {
        private const val NOMBRE_TRABAJO = "sincronizacion_periodica"
        private const val MINIMO_MINUTOS = 15
        private const val MAXIMO_MINUTOS = 360
    }
}
