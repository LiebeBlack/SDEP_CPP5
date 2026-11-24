package ve.edu.sdep.movil.datos.documentos

/**
 * Tipos admitidos para adjuntos capturados desde el teléfono.
 *
 * El proveedor de documentos de Android puede informar un MIME genérico o
 * incorrecto; por eso la extensión y la firma del contenido se contrastan.
 * Solo se aceptan PDF, JPEG y PNG, formatos que la institución ya maneja en
 * los expedientes digitalizados.
 */
object TipoAdjunto {

    private val firmasPdf = "%PDF-".encodeToByteArray()
    private val firmaPng = byteArrayOf(
        0x89.toByte(), 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    )

    /** Devuelve el MIME verificado o null si extensión/MIME y firma no concuerdan. */
    fun verificar(nombre: String, mimeDeclarado: String?, bytes: ByteArray): String? {
        if (bytes.isEmpty()) return null
        val extension = nombre.substringAfterLast('.', "").lowercase()
        val declarado = mimeDeclarado?.substringBefore(';')?.trim()?.lowercase()
        val tipoPorExtension = when (extension) {
            "pdf" -> "application/pdf"
            "jpg", "jpeg" -> "image/jpeg"
            "png" -> "image/png"
            else -> return null
        }
        val compatible = declarado.isNullOrBlank() ||
            declarado == "application/octet-stream" || declarado == tipoPorExtension ||
            (tipoPorExtension == "image/jpeg" && declarado == "image/jpg")
        if (!compatible) return null
        val firmaValida = when (tipoPorExtension) {
            "application/pdf" -> bytes.empiezaCon(firmasPdf)
            "image/png" -> bytes.empiezaCon(firmaPng)
            "image/jpeg" -> bytes.size >= 3 &&
                bytes[0] == 0xFF.toByte() && bytes[1] == 0xD8.toByte() && bytes[2] == 0xFF.toByte()
            else -> false
        }
        return tipoPorExtension.takeIf { firmaValida }
    }

    /** Infiere el MIME para mostrar un archivo recibido sin campo MIME en el protocolo. */
    fun desdeNombre(nombre: String?): String = when (
        nombre?.substringAfterLast('.', "")?.lowercase()
    ) {
        "pdf" -> "application/pdf"
        "jpg", "jpeg" -> "image/jpeg"
        "png" -> "image/png"
        else -> "application/octet-stream"
    }

    private fun ByteArray.empiezaCon(prefijo: ByteArray): Boolean =
        size >= prefijo.size && prefijo.indices.all { this[it] == prefijo[it] }
}
