package ve.edu.sdep.movil

import android.content.res.Configuration
import android.graphics.drawable.ColorDrawable
import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import dagger.hilt.android.AndroidEntryPoint
import ve.edu.sdep.movil.datos.preferencias.PreferenciasApariencia
import ve.edu.sdep.movil.ui.navegacion.NavegacionPrincipal
import ve.edu.sdep.movil.ui.tema.TemaSdep
import javax.inject.Inject

/**
 * Única actividad de la aplicación.
 *
 * Extiende ``AppCompatActivity`` (que ya es una ``FragmentActivity``) porque
 * ``BiometricPrompt`` necesita un ``FragmentManager`` y su diálogo está pensado
 * para el tema de AppCompat. Sigue siendo un ``ComponentActivity``, así que
 * Compose y Hilt funcionan igual.
 *
 * El tema se resuelve aquí, en la raíz: la preferencia del puesto (Sistema,
 * Claro u Oscuro) manda sobre el ajuste del teléfono y se aplica a toda la
 * aplicación sin recrear la actividad. Los iconos de las barras se invierten
 * con el tema elegido; si se dejaran como los fija el sistema, en un teléfono
 * en claro con la aplicación en oscuro la hora y los iconos quedarían negros
 * sobre fondo negro.
 */
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    @Inject
    lateinit var apariencia: PreferenciasApariencia

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // El fondo de la ventana se pinta antes de que Compose dibuje: con el
        // tema oscuro elegido y el teléfono en claro se veía un destello blanco
        // en cada arranque, que en un equipo lento dura casi un segundo.
        val sistemaOscuro =
            (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
                Configuration.UI_MODE_NIGHT_YES
        val fondo = if (apariencia.modo.value.esOscuro(sistemaOscuro)) {
            R.color.fondo_oscuro
        } else {
            R.color.fondo_claro
        }
        window.setBackgroundDrawable(ColorDrawable(ContextCompat.getColor(this, fondo)))
        enableEdgeToEdge()
        setContent {
            val modo by apariencia.modo.collectAsStateWithLifecycle()
            val oscuro = modo.esOscuro(isSystemInDarkTheme())

            SideEffect {
                WindowCompat.getInsetsController(window, window.decorView).apply {
                    isAppearanceLightStatusBars = !oscuro
                    isAppearanceLightNavigationBars = !oscuro
                }
            }

            TemaSdep(oscuro = oscuro) {
                NavegacionPrincipal()
            }
        }
    }
}
