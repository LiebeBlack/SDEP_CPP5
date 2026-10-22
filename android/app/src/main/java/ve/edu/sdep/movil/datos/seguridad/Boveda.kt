package ve.edu.sdep.movil.datos.seguridad

import android.annotation.SuppressLint
import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Almacén cifrado de los datos que no pueden quedar legibles en el teléfono.
 *
 * Usa EncryptedSharedPreferences: la clave maestra vive en el Keystore del
 * equipo (respaldado por hardware cuando existe) y los valores se cifran con
 * AES-256-GCM. Aquí se guardan el token del puesto y el token de desbloqueo
 * biométrico; las contraseñas no se guardan nunca, solo su derivación PBKDF2
 * en la base de datos.
 */
@Singleton
class Boveda @Inject constructor(
    @ApplicationContext private val contexto: Context,
) {

    private val preferencias: SharedPreferences? by lazy { abrir() }

    // ------------------------------------------------------------------
    // Configuración del nodo central
    // ------------------------------------------------------------------
    fun leerConfiguracion(): ConfiguracionAlmacenada = ConfiguracionAlmacenada(
        url = leer(CLAVE_URL).orEmpty(),
        equipo = leer(CLAVE_EQUIPO).orEmpty(),
        token = leer(CLAVE_TOKEN).orEmpty(),
        activa = leer(CLAVE_ACTIVA) == "true",
        periodoMinutos = leer(CLAVE_PERIODO)?.toIntOrNull() ?: 15,
    )

    fun guardarConfiguracion(
        url: String,
        equipo: String,
        token: String,
        activa: Boolean,
        periodoMinutos: Int,
    ): Boolean = escribir(
        mapOf(
            CLAVE_URL to url.trim(),
            CLAVE_EQUIPO to equipo.trim(),
            CLAVE_TOKEN to token.trim(),
            CLAVE_ACTIVA to activa.toString(),
            CLAVE_PERIODO to periodoMinutos.toString(),
        ),
    )

    // ------------------------------------------------------------------
    // Sesión de usuario (token emitido por el nodo central)
    // ------------------------------------------------------------------
    fun guardarSesionToken(token: String): Boolean = escribir(mapOf(CLAVE_SESION_TOKEN to token))

    fun leerSesionToken(): String? = leer(CLAVE_SESION_TOKEN)

    fun olvidarSesionToken(): Boolean = escribir(mapOf(CLAVE_SESION_TOKEN to ""))

    // ------------------------------------------------------------------
    // Identidad del último usuario
    // ------------------------------------------------------------------
    /**
     * Usuario al que pertenece el espejo local.
     *
     * Al entrar otra persona se borra el espejo completo antes de descargar
     * sus datos. Sin esta marca no se podría distinguir un cambio de usuario de
     * un simple reinicio de la app.
     */
    fun guardarUltimoUsuario(usuario: String): Boolean =
        escribir(mapOf(CLAVE_ULTIMO_USUARIO to usuario.trim()))

    fun leerUltimoUsuario(): String? = leer(CLAVE_ULTIMO_USUARIO)

    // ------------------------------------------------------------------
    // Desbloqueo biométrico
    // ------------------------------------------------------------------
    fun guardarCredencialBiometrica(usuario: String, token: String): Boolean = escribir(
        mapOf(CLAVE_BIO_USUARIO to usuario, CLAVE_BIO_TOKEN to token),
    )

    fun leerCredencialBiometrica(): ParBiometrico? {
        val usuario = leer(CLAVE_BIO_USUARIO) ?: return null
        val token = leer(CLAVE_BIO_TOKEN) ?: return null
        return ParBiometrico(usuario, token)
    }

    fun olvidarCredencialBiometrica(): Boolean = escribir(
        mapOf(CLAVE_BIO_USUARIO to "", CLAVE_BIO_TOKEN to ""),
    )

    // ------------------------------------------------------------------
    // Interno
    // ------------------------------------------------------------------
    private fun abrir(): SharedPreferences? = try {
        val maestra = MasterKey.Builder(contexto)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            contexto,
            ARCHIVO,
            maestra,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    } catch (error: Exception) {
        // Si el Keystore del equipo está dañado no se cae la aplicación: se
        // trabaja sin recordar credenciales y se avisa en la pantalla de ajustes.
        Log.e(TAG, "No se pudo abrir la bóveda cifrada", error)
        null
    }

    private fun leer(clave: String): String? =
        try {
            preferencias?.getString(clave, null)?.takeIf { it.isNotBlank() }
        } catch (error: Exception) {
            Log.e(TAG, "No se pudo leer $clave de la bóveda", error)
            null
        }

    // ``commit`` es intencional: la pantalla de ajustes solo puede decir
    // «guardado» cuando el token ya está en disco. Con ``apply`` la escritura
    // queda en segundo plano y un cierre inmediato de la app podría perder el
    // emparejamiento que el usuario acaba de confirmar.
    @SuppressLint("ApplySharedPref")
    private fun escribir(valores: Map<String, String>): Boolean {
        val destino = preferencias ?: return false
        return try {
            destino.edit().apply {
                valores.forEach { (clave, valor) -> putString(clave, valor) }
            }.commit()
        } catch (error: Exception) {
            Log.e(TAG, "No se pudo escribir en la bóveda", error)
            false
        }
    }

    data class ConfiguracionAlmacenada(
        val url: String,
        val equipo: String,
        val token: String,
        val activa: Boolean,
        val periodoMinutos: Int,
    )

    data class ParBiometrico(val usuario: String, val token: String)

    private companion object {
        const val TAG = "Boveda"
        const val ARCHIVO = "sdep_boveda"
        const val CLAVE_URL = "url_servidor"
        const val CLAVE_EQUIPO = "equipo"
        const val CLAVE_TOKEN = "token"
        const val CLAVE_ACTIVA = "sync_activa"
        const val CLAVE_PERIODO = "periodo_minutos"
        const val CLAVE_BIO_USUARIO = "bio_usuario"
        const val CLAVE_BIO_TOKEN = "bio_token"
        const val CLAVE_SESION_TOKEN = "sesion_token"
        const val CLAVE_ULTIMO_USUARIO = "ultimo_usuario"
    }
}
