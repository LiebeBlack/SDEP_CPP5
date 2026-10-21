package ve.edu.sdep.movil.datos.seguridad

import android.content.Context
import android.os.Build
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity

/**
 * Puerta biométrica del dispositivo.
 *
 * No guarda ni compara huellas: el sistema operativo hace esa parte. La app
 * solo recibe un «sí» o un «no» y, cuando es «sí», recupera de la bóveda cifrada
 * el token que permite abrir la sesión sin volver a escribir la contraseña.
 *
 * En Android 11 y posteriores se admite también el PIN, el patrón o la clave
 * del dispositivo como respaldo de la huella; en versiones anteriores se usa
 * la biometría disponible y se ofrece «Cancelar». El reconocimiento facial
 * funciona por la misma vía cuando el fabricante lo expone como biometría
 * fuerte.
 */
class AutenticadorBiometrico {

    private val autenticadores: Int
        get() = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            BiometricManager.Authenticators.BIOMETRIC_STRONG or
                BiometricManager.Authenticators.DEVICE_CREDENTIAL
        } else {
            BiometricManager.Authenticators.BIOMETRIC_WEAK
        }

    /** Indica si el equipo puede autenticar al usuario en este momento */
    fun disponible(contexto: Context): Boolean {
        val administrador = BiometricManager.from(contexto)
        return administrador.canAuthenticate(autenticadores) == BiometricManager.BIOMETRIC_SUCCESS
    }

    /**
     * Muestra el diálogo del sistema.
     *
     * @param alExito Se invoca en el hilo principal cuando la autenticación se
     *   completa; es el momento de recuperar el token de la bóveda.
     * @param alFallo Recibe un mensaje ya redactado para el usuario.
     */
    fun solicitar(
        actividad: FragmentActivity,
        titulo: String,
        subtitulo: String,
        alExito: () -> Unit,
        alFallo: (String) -> Unit,
    ) {
        val ejecutor = ContextCompat.getMainExecutor(actividad)
        val dialogo = BiometricPrompt(
            actividad,
            ejecutor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    super.onAuthenticationSucceeded(result)
                    alExito()
                }

                override fun onAuthenticationError(codigo: Int, mensaje: CharSequence) {
                    super.onAuthenticationError(codigo, mensaje)
                    alFallo(mensajeDeError(codigo, mensaje.toString()))
                }

                override fun onAuthenticationFailed() {
                    super.onAuthenticationFailed()
                    // Un intento fallido no cierra el diálogo: el sistema deja
                    // reintentar. Se informa sin interrumpir.
                    alFallo("No se reconoció la huella. Intente de nuevo.")
                }
            },
        )

        val constructor = BiometricPrompt.PromptInfo.Builder()
            .setTitle(titulo)
            .setSubtitle(subtitulo)
            .setAllowedAuthenticators(autenticadores)

        // En Android 10 y anteriores no se puede combinar con la credencial del
        // dispositivo, así que el botón negativo es obligatorio.
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.R) {
            constructor.setNegativeButtonText("Cancelar")
        }

        dialogo.authenticate(constructor.build())
    }

    private fun mensajeDeError(codigo: Int, mensajeDelSistema: String): String = when (codigo) {
        BiometricPrompt.ERROR_NEGATIVE_BUTTON,
        BiometricPrompt.ERROR_USER_CANCELED,
        BiometricPrompt.ERROR_CANCELED,
        -> "Cancelado."

        BiometricPrompt.ERROR_LOCKOUT,
        BiometricPrompt.ERROR_LOCKOUT_PERMANENT,
        -> "Demasiados intentos. Espere unos minutos o use su contraseña."

        BiometricPrompt.ERROR_NO_BIOMETRICS -> "Este equipo no tiene biometría configurada."

        BiometricPrompt.ERROR_HW_NOT_PRESENT,
        BiometricPrompt.ERROR_HW_UNAVAILABLE,
        -> "El sensor biométrico no está disponible en este momento."

        else -> mensajeDelSistema.ifBlank { "No se pudo completar la autenticación." }
    }
}
