package ve.edu.sdep.movil.dominio.modelo

/** Situación de un registro respecto al nodo central */
enum class EstadoSincronizacion(val etiqueta: String) {
    PENDIENTE("Pendiente de envío"),
    SINCRONIZADO("Sincronizado"),
    RECHAZADO("Rechazado por el servidor"),
    ;

    companion object {
        fun desde(valor: String?): EstadoSincronizacion =
            values().firstOrNull { it.name.equals(valor, ignoreCase = true) } ?: PENDIENTE
    }
}

/**
 * Registro de campo.
 *
 * Es la contraparte en el teléfono de ``registros_moviles`` en el sistema de
 * escritorio. ``uuid`` es la identidad global de la fila: se genera una sola vez
 * y viaja en todas las operaciones, de modo que el mismo registro creado aquí
 * no se duplica al llegar al nodo central.
 */
data class Registro(
    val uuid: String,
    val titulo: String,
    val contenido: String,
    val categoria: String,
    val valor: Double?,
    val creadoEn: Long,
    val actualizadoEn: Long,
    val estado: EstadoSincronizacion = EstadoSincronizacion.PENDIENTE,
    val eliminado: Boolean = false,
) {
    val valorTexto: String
        get() = valor?.let { if (it == it.toLong().toDouble()) it.toLong().toString() else it.toString() } ?: ""
}
