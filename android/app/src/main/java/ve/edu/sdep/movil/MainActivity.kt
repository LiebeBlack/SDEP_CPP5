package ve.edu.sdep.movil

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import dagger.hilt.android.AndroidEntryPoint
import ve.edu.sdep.movil.ui.navegacion.NavegacionPrincipal
import ve.edu.sdep.movil.ui.tema.TemaSdep

/**
 * Única actividad de la aplicación.
 *
 * Extiende ``AppCompatActivity`` (que ya es una ``FragmentActivity``) porque
 * ``BiometricPrompt`` necesita un ``FragmentManager`` y su diálogo está pensado
 * para el tema de AppCompat. Sigue siendo un ``ComponentActivity``, así que
 * Compose y Hilt funcionan igual.
 */
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            TemaSdep {
                NavegacionPrincipal()
            }
        }
    }
}
