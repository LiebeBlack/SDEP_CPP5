package ve.edu.sdep.movil.ui.modulos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import ve.edu.sdep.movil.datos.documentos.TipoAdjunto

/** Reglas puras de selección, integridad y presentación de adjuntos Android. */
class AdjuntosUiTest {

    @Test
    fun `el nombre de archivo no conserva rutas`() {
        assertEquals("certificado.pdf", nombreSeguroAdjunto("C:\\usuarios\\ana\\certificado.pdf"))
        assertEquals("documento final.pdf", nombreSeguroAdjunto("/tmp/documento final.pdf"))
    }

    @Test
    fun `el nombre de archivo filtra caracteres de control y limita la longitud`() {
        assertEquals("miarchivo.pdf", nombreSeguroAdjunto("mi/archivo?.pdf"))
        assertEquals("adjunto", nombreSeguroAdjunto("../"))
        assertEquals(100, nombreSeguroAdjunto("a".repeat(120)).length)
    }

    @Test
    fun `el tamaño se expresa en unidades legibles`() {
        assertEquals("0 B", tamanoLegible(0))
        assertEquals("500 B", tamanoLegible(500))
        assertEquals("1 KB", tamanoLegible(1024))
        assertEquals("1.0 MB", tamanoLegible(1024 * 1024))
    }

    @Test
    fun `acepta pdf genuino y rechaza extension falsa`() {
        val pdf = "%PDF-1.7\ncontenido".encodeToByteArray()
        assertEquals("application/pdf", TipoAdjunto.verificar("legajo.pdf", "application/pdf", pdf))
        assertNull(TipoAdjunto.verificar("legajo.pdf", "application/pdf", "no es pdf".encodeToByteArray()))
        assertNull(TipoAdjunto.verificar("programa.exe", "application/pdf", pdf))
    }

    @Test
    fun `valida las firmas jpeg y png`() {
        val jpeg = byteArrayOf(0xFF.toByte(), 0xD8.toByte(), 0xFF.toByte(), 0x00)
        val png = byteArrayOf(0x89.toByte(), 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)
        assertEquals("image/jpeg", TipoAdjunto.verificar("foto.jpg", "image/jpeg", jpeg))
        assertEquals("image/png", TipoAdjunto.verificar("foto.png", "image/png", png))
        assertNull(TipoAdjunto.verificar("foto.png", "image/png", jpeg))
    }
}
