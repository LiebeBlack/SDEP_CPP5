package ve.edu.sdep.movil.datos

import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import ve.edu.sdep.movil.datos.local.Espejo
import ve.edu.sdep.movil.datos.local.entidad.ConfiguracionEntity

/**
 * Reglas de compatibilidad del payload.
 *
 * El escritorio excluye de la replicación las preferencias del equipo
 * (`CLAVES_CONFIGURACION_LOCALES` en `sync_agent/registro.py`). El teléfono
 * debe aplicar exactamente la misma regla: si no, el modo oscuro de un puesto
 * se propagaría a toda la institución.
 */
class EspejoTest {

    private fun configuracion(clave: String, valor: String? = "x") = ConfiguracionEntity(
        clave = clave,
        valor = valor,
    )

    @Test
    fun `las preferencias del equipo no se anuncian`() {
        listOf(
            "apariencia_modo",
            "backup_enabled",
            "backup_interval_hours",
            "audit_enabled",
        ).forEach { clave ->
            assertTrue("«$clave» es local", Espejo.esConfiguracionLocal(clave))
            assertNull(
                "«$clave» no debe viajar",
                Espejo.payload("configuraciones", configuracion(clave), null, true),
            )
        }
    }

    @Test
    fun `los parametros del agente tampoco se anuncian`() {
        assertTrue(Espejo.esConfiguracionLocal("sync_cursor"))
        assertNull(
            Espejo.payload("configuraciones", configuracion("sync_cursor"), null, true),
        )
    }

    @Test
    fun `un parametro institucional si se anuncia`() {
        assertFalse(Espejo.esConfiguracionLocal("institucion_nombre"))
        val payload = Espejo.payload(
            "configuraciones",
            configuracion("institucion_nombre", "Liceo Bolívar"),
            null,
            true,
        )
        assertNotNull(payload)
        assertTrue(payload!!.containsKey("clave"))
        assertTrue(payload.containsKey("valor"))
    }
}
