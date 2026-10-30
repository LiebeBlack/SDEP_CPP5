package ve.edu.sdep.movil.ui.modulos

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Formato de los valores que se muestran en las fichas.
 *
 * Es el mismo criterio del escritorio: fecha `dd/MM/yyyy`, números sin ceros
 * sobrantes y una raya para el dato vacío. Si el teléfono mostrara «null» o una
 * fecha ISO cruda, la ficha del empleado y la constancia que se genera después
 * no coincidirían con el resto del sistema.
 */
class FormatoTest {

    @Test
    fun `la fecha iso se muestra como en el escritorio`() {
        assertEquals("30/10/2026", fecha("2026-10-30"))
        // Una marca completa se recorta al día: la ficha no muestra la hora.
        assertEquals("30/10/2026", fecha("2026-10-30T18:45:00"))
        assertEquals("—", fecha(null))
        assertEquals("—", fecha("   "))
        // Un valor que no es fecha se muestra tal cual, sin lanzar.
        assertEquals("sin fecha", fecha("sin fecha"))
    }

    @Test
    fun `el momento conserva la hora`() {
        assertEquals("30/10/2026 18:45", momento("2026-10-30T18:45:00"))
        assertEquals("—", momento(""))
    }

    @Test
    fun `los numeros no arrastran ceros`() {
        assertEquals("85", numero(85.0))
        assertEquals("—", numero(null))
        assertTrue(numero(7.256).startsWith("7.2"))
    }

    @Test
    fun `el estado se lee con mayuscula inicial`() {
        assertEquals("Aprobada", etiquetaEstado("aprobada"))
        assertEquals("En revision", etiquetaEstado("en_revision"))
        assertEquals("—", etiquetaEstado(null))
    }

    @Test
    fun `el texto vacio se muestra como raya`() {
        assertEquals("Liceo Bolívar", texto("Liceo Bolívar"))
        assertEquals("—", texto("  "))
        assertEquals("—", texto(null))
    }

    @Test
    fun `el importe lleva el simbolo y los centimos`() {
        val monto = bolivares(1850.5)
        assertTrue("debe empezar con Bs.: $monto", monto.startsWith("Bs. "))
        assertTrue("debe llevar los céntimos: $monto", monto.trim().endsWith("50"))
    }
}
