package ve.edu.sdep.movil.datos.preferencias

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Resolución del tema elegido en el puesto.
 *
 * «Sistema» sigue al teléfono; «Claro» y «Oscuro» lo ignoran. Un valor guardado
 * que ya no exista (por ejemplo de una versión anterior) no debe dejar la
 * aplicación sin tema: vuelve a «Sistema».
 */
class AparienciaTest {

    @Test
    fun `el modo elegido manda sobre el sistema`() {
        assertTrue(ModoApariencia.OSCURO.esOscuro(sistemaOscuro = false))
        assertFalse(ModoApariencia.CLARO.esOscuro(sistemaOscuro = true))
    }

    @Test
    fun `el modo sistema sigue al telefono`() {
        assertTrue(ModoApariencia.SISTEMA.esOscuro(sistemaOscuro = true))
        assertFalse(ModoApariencia.SISTEMA.esOscuro(sistemaOscuro = false))
    }

    @Test
    fun `un valor guardado desconocido vuelve a sistema`() {
        assertEquals(ModoApariencia.SISTEMA, ModoApariencia.desde(null))
        assertEquals(ModoApariencia.SISTEMA, ModoApariencia.desde("VIOLETA"))
        assertEquals(ModoApariencia.OSCURO, ModoApariencia.desde("oscuro"))
        // El nombre de la constante se acepta por compatibilidad: antes se
        // guardaba así y un usuario no debe perder su ajuste al actualizar.
        assertEquals(ModoApariencia.OSCURO, ModoApariencia.desde("OSCURO"))
    }

    @Test
    fun `cada modo guarda un codigo estable`() {
        assertEquals(ModoApariencia.entries.size, ModoApariencia.entries.map { it.codigo }.toSet().size)
        ModoApariencia.entries.forEach { modo ->
            assertEquals(modo, ModoApariencia.desde(modo.codigo))
        }
    }

    @Test
    fun `cada modo tiene etiqueta para el selector`() {
        ModoApariencia.entries.forEach { modo ->
            assertTrue("«${modo.name}» necesita etiqueta", modo.etiqueta.isNotBlank())
        }
    }
}
