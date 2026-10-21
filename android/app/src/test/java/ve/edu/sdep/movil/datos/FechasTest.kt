package ve.edu.sdep.movil.datos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import ve.edu.sdep.movil.datos.local.Fechas

/**
 * El protocolo usa fechas UTC «ingenuas» (sin zona). Si el teléfono enviara
 * una «Z» o un desplazamiento, el motor de mezcla compararía marcas que no son
 * comparables y un equipo ganaría siempre los conflictos.
 */
class FechasTest {

    @Test
    fun `la ida y vuelta conserva el milisegundo`() {
        val momento = 1_790_000_000_123L
        val texto = Fechas.isoDesde(momento)
        assertEquals(momento, Fechas.desdeIso(texto))
    }

    @Test
    fun `el texto no lleva zona horaria`() {
        val texto = Fechas.isoDesde(0L)
        assertFalse(texto.contains("Z"))
        assertFalse(texto.contains("+"))
        assertTrue(texto.startsWith("1970-01-01T00:00"))
    }

    @Test
    fun `acepta las tres formas que puede devolver el servidor`() {
        val esperado = 1_600_000_000_000L
        assertEquals(esperado, Fechas.desdeIso("2020-09-13T12:26:40Z"))
        assertEquals(esperado, Fechas.desdeIso("2020-09-13T12:26:40+00:00"))
        assertEquals(esperado, Fechas.desdeIso("2020-09-13T12:26:40"))
    }

    @Test
    fun `un texto vacio o invalido no rompe la lectura`() {
        assertNull(Fechas.desdeIso(null))
        assertNull(Fechas.desdeIso(""))
        assertNull(Fechas.desdeIso("ayer"))
        assertNull(Fechas.desdeIso("2020-13-45T99:99:99"))
    }
}
