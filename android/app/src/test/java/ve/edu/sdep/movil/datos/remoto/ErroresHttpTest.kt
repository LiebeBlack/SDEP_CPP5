package ve.edu.sdep.movil.datos.remoto

import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Response

class ErroresHttpTest {
    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun `el texto remoto se limpia y limita`() {
        val remoto = "Inicio" + '\u0001' + "a".repeat(600)
        val cuerpo = json.encodeToString(ErrorDto(remoto))
        val error = HttpException(
            Response.error<Any>(
                400,
                cuerpo.toResponseBody("application/json".toMediaType()),
            ),
        )

        val mensaje = error.mensajeDelServidor(json)

        assertEquals(500, mensaje?.length)
        assertEquals("Inicio" + "a".repeat(494), mensaje)
    }

    @Test
    fun `un cuerpo de error que no es JSON se descarta`() {
        val error = HttpException(
            Response.error<Any>(
                502,
                "<html>error proxy</html>".toResponseBody("text/html".toMediaType()),
            ),
        )

        assertNull(error.mensajeDelServidor(json))
    }
}
