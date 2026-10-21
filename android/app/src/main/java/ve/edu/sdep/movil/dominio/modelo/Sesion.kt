package ve.edu.sdep.movil.dominio.modelo

/**
 * Sesión de la aplicación.
 *
 * El usuario entra con las cuentas de la base institucional (las mismas del
 * escritorio) y el nodo central emite un token: aquí solo viven sus datos de
 * cara a la interfaz, nunca la contraseña.
 *
 * [offline] indica que la sesión se abrió sin red con el desbloqueo biométrico
 * dentro de la ventana de gracia: la app funciona en lectura y con cola de
 * salida, y el token se revalida contra el nodo central en cuanto haya red.
 */
data class Sesion(
    val usuario: String,
    val nombre: String,
    val rol: Rol,
    val token: String = "",
    val expiraEn: Long = 0L,
    val debeCambiarPassword: Boolean = false,
    val offline: Boolean = false,
) {
    fun puede(permiso: Permiso): Boolean = PoliticaRoles.tiene(rol, permiso)

    fun puedeAbrir(modulo: Modulo): Boolean = PoliticaRoles.puedeAbrir(rol, modulo)

    /** La sesión abierta sin red solo sirve dentro de su ventana de gracia */
    fun vigente(ahora: Long = System.currentTimeMillis()): Boolean =
        expiraEn <= 0L || ahora <= expiraEn

    val etiquetaRol: String get() = rol.etiqueta
}

/**
 * Resultado de una operación de la capa de datos.
 *
 * Se usa en lugar de lanzar excepciones hacia la interfaz: un fallo esperable
 * (token rechazado, sin red, contraseña incorrecta) es un dato que la pantalla
 * muestra, no un error que derribe la aplicación.
 */
sealed interface Resultado<out T> {
    data class Exito<T>(val valor: T) : Resultado<T>
    data class Fallo(
        val mensaje: String,
        val causa: Throwable? = null,
        val reintentable: Boolean = false,
    ) : Resultado<Nothing>
}

/** Devuelve el valor si la operación salió bien; null en caso contrario */
fun <T> Resultado<T>.valorONull(): T? = (this as? Resultado.Exito)?.valor

/** Devuelve el mensaje de error si la operación falló; null si salió bien */
fun <T> Resultado<T>.mensajeDeError(): String? = (this as? Resultado.Fallo)?.mensaje
