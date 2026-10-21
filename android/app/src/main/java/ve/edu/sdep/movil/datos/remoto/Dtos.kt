package ve.edu.sdep.movil.datos.remoto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

/**
 * Objetos del protocolo del nodo central.
 *
 * Los nombres viajan en «snake_case» porque así los define el servicio de
 * escritorio (``sync_agent``). El ``payload`` se envía y se recibe como **texto
 * JSON**, no como objeto: es la forma en que el servidor lo guarda en su log de
 * operaciones y la que devuelve al hacer «pull».
 */
@Serializable
data class OperacionDto(
    @SerialName("op_id") val opId: String,
    val tabla: String,
    @SerialName("fila_uuid") val filaUuid: String,
    val operacion: String,
    val payload: String,
    @SerialName("base_op_id") val baseOpId: String? = null,
    val dispositivo: String,
    val usuario: String? = null,
    @SerialName("creado_en") val creadoEn: String,
    val seq: Int = 0,
)

@Serializable
data class PushDto(
    val dispositivo: String,
    val ops: List<OperacionDto>,
)

@Serializable
data class RechazoDto(
    @SerialName("op_id") val opId: String,
    val motivo: String = "",
)

@Serializable
data class ConflictoRemotoDto(
    val tabla: String = "",
    @SerialName("fila_uuid") val filaUuid: String = "",
    val campo: String = "",
    @SerialName("valor_local") val valorLocal: JsonElement? = null,
    @SerialName("valor_remoto") val valorRemoto: JsonElement? = null,
    val ganador: String = "",
    val regla: String = "",
)

@Serializable
data class PushRespuestaDto(
    val aplicadas: List<String> = emptyList(),
    val rechazadas: List<RechazoDto> = emptyList(),
    val conflictos: List<ConflictoRemotoDto> = emptyList(),
    val cursor: Int = 0,
)

@Serializable
data class PullRespuestaDto(
    val ops: List<OperacionDto> = emptyList(),
    val cursor: Int = 0,
    @SerialName("hay_mas") val hayMas: Boolean = false,
    val maximo: Int = 0,
)

@Serializable
data class PingDto(
    val servidor: String = "",
    @SerialName("version_protocolo") val versionProtocolo: String = "",
    val hora: String = "",
    val tablas: List<String> = emptyList(),
)
