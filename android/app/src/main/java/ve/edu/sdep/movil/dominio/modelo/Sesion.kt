package ve.edu.sdep.movil.dominio.modelo

/** Usuario que tiene la sesión abierta en este momento */
data class Sesion(
    val usuarioId: Long,
    val nombre: String,
    val usuario: String,
    val rol: Rol,
) {
    fun puede(permiso: Permiso): Boolean = PoliticaRoles.puede(rol, permiso)
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
