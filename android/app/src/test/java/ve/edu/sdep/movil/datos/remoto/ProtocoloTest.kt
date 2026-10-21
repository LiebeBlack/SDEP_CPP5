package ve.edu.sdep.movil.datos.remoto

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * El contrato con ``sync_agent`` se juega en los nombres y en los tipos.
 *
 * El ``payload`` es una cadena JSON, no un objeto: el servidor lo guarda tal
 * cual en su log y lo devuelve igual al hacer «pull». Si aquí se enviara como
 * objeto, el nodo central almacenaría un diccionario donde espera texto.
 */
class ProtocoloTest {

    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = false
    }

    private fun operacion(payload: String = """{"uuid_movil":"abc"}""") = OperacionDto(
        opId = "op-1",
        tabla = "registros_moviles",
        filaUuid = "fila-1",
        operacion = "upsert",
        payload = payload,
        dispositivo = "movil-secretaria",
        usuario = "ana",
        creadoEn = "2026-10-21T12:00:00",
    )

    @Test
    fun `la operacion usa los nombres del protocolo`() {
        val texto = json.encodeToString(PushDto("movil-secretaria", listOf(operacion())))
        assertTrue(texto.contains("\"dispositivo\""))
        assertTrue(texto.contains("\"op_id\""))
        assertTrue(texto.contains("\"fila_uuid\""))
        assertTrue(texto.contains("\"creado_en\""))
        assertTrue(texto.contains("\"payload\":\"{\\\"uuid_movil\\\":\\\"abc\\\"}\""))
        assertFalse(texto.contains("\"tabla_movil\""))
    }

    @Test
    fun `el seq no se envia al empujar`() {
        val texto = json.encodeToString(PushDto("equipo", listOf(operacion())))
        assertFalse(texto.contains("\"seq\""))
    }

    @Test
    fun `la respuesta de pull conserva el payload como texto`() {
        val cuerpo = """
            {
              "ops": [
                {
                  "seq": 7,
                  "op_id": "op-remota",
                  "tabla": "registros_moviles",
                  "fila_uuid": "fila-1",
                  "operacion": "upsert",
                  "payload": "{\"titulo\":\"Visita\"}",
                  "dispositivo": "pc-direccion",
                  "usuario": "Luis",
                  "creado_en": "2026-10-21T12:00:00"
                }
              ],
              "cursor": 7,
              "hay_mas": false,
              "maximo": 7
            }
        """.trimIndent()

        val respuesta = json.decodeFromString<PullRespuestaDto>(cuerpo)
        assertEquals(1, respuesta.ops.size)
        assertEquals(7, respuesta.cursor)
        assertFalse(respuesta.hayMas)
        assertEquals("""{"titulo":"Visita"}""", respuesta.ops.first().payload)
        assertEquals("pc-direccion", respuesta.ops.first().dispositivo)
    }

    @Test
    fun `la respuesta de push admite rechazos y conflictos`() {
        val cuerpo = """
            {
              "aplicadas": ["op-1"],
              "rechazadas": [{"op_id": "op-2", "motivo": "tabla_no_sincronizable"}],
              "conflictos": [
                {
                  "tabla": "registros_moviles",
                  "fila_uuid": "fila-1",
                  "campo": "titulo",
                  "valor_local": "Uno",
                  "valor_remoto": "Dos",
                  "ganador": "remoto",
                  "regla": "escritura_mas_reciente"
                }
              ],
              "cursor": 42
            }
        """.trimIndent()

        val respuesta = json.decodeFromString<PushRespuestaDto>(cuerpo)
        assertEquals(listOf("op-1"), respuesta.aplicadas)
        assertEquals("op-2", respuesta.rechazadas.first().opId)
        assertEquals("titulo", respuesta.conflictos.first().campo)
        assertEquals(42, respuesta.cursor)
    }

    @Test
    fun `el ping admite la lista de tablas`() {
        val cuerpo = """
            {
              "servidor": "nodo-central-sincronizacion",
              "version_protocolo": "1",
              "hora": "2026-10-21T12:00:00",
              "tablas": ["empleados", "registros_moviles"]
            }
        """.trimIndent()

        val ping = json.decodeFromString<PingDto>(cuerpo)
        assertEquals("1", ping.versionProtocolo)
        assertTrue(ping.tablas.contains("registros_moviles"))
        assertEquals("2026-10-21T12:00:00", ping.hora)
    }
}
