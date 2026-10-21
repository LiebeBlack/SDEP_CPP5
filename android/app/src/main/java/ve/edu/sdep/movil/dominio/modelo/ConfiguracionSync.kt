package ve.edu.sdep.movil.dominio.modelo

/**
 * Datos de conexión con el nodo central del sistema de escritorio.
 *
 * Los entrega el administrador al dar de alta el teléfono como un puesto más:
 * la dirección del servicio, el identificador del dispositivo y el token. Sin
 * los tres, la app funciona sin conexión y las operaciones quedan en cola.
 */
data class ConfiguracionSync(
    val url: String = "",
    val equipo: String = "",
    val token: String = "",
    val activa: Boolean = false,
) {
    /** Indica si hay datos suficientes para intentar sincronizar */
    val completa: Boolean
        get() = url.isNotBlank() && equipo.isNotBlank() && token.isNotBlank()

    /** URL normalizada para Retrofit (siempre termina en «/») */
    fun urlNormalizada(): String {
        val limpia = url.trim().removeSuffix("/")
        return "$limpia/"
    }
}
