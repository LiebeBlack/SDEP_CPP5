package ve.edu.sdep.movil.datos.repositorio

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ConfiguracionRepositorioTest {
    @Test
    fun `normaliza host y puerto HTTP`() {
        assertEquals("http://192.168.1.20:8765", normalizarUrlServidor("192.168.1.20:8765"))
        assertEquals("https://servidor.institucion", normalizarUrlServidor("https://servidor.institucion/"))
    }

    @Test
    fun `rechaza credenciales parametros rutas y puertos invalidos`() {
        listOf(
            "http://usuario:secreto@servidor:8765",
            "https://servidor:99999",
            "http://servidor:443",
            "http://servidor/ruta",
            "http://servidor/?token=secreto",
            "ftp://servidor:8765",
        ).forEach { assertNull(normalizarUrlServidor(it)) }
    }
}
