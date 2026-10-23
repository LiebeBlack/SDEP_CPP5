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
    @SerialName("acciones") val acciones: List<String> = emptyList(),
)

// ----------------------------------------------------------------------
// Protocolo 2: autenticación de usuario y consultas
// ----------------------------------------------------------------------

/** Credenciales de la base institucional; jamás se guardan en el teléfono */
@Serializable
data class LoginDto(
    val username: String,
    val password: String,
)

@Serializable
data class CambioPasswordDto(
    val actual: String? = null,
    val nueva: String,
)

/** Respuesta del login: el token de sesión y los datos de la cuenta */
@Serializable
data class SesionRespuestaDto(
    @SerialName("sesion_token") val sesionToken: String,
    val username: String = "",
    @SerialName("nombre_completo") val nombreCompleto: String? = null,
    val rol: String = "viewer",
    /** Cédula del trabajador; el nodo la devuelve y la app la usa para aislar */
    val cedula: String? = null,
    @SerialName("debe_cambiar_password") val debeCambiarPassword: Boolean = false,
    @SerialName("expira_en") val expiraEn: String? = null,
    @SerialName("vida_relativa_horas") val vidaRelativaHoras: Int = 12,
    /** Longitud mínima que exige el servidor para cambiar la contraseña */
    @SerialName("password_min_longitud") val passwordMinLongitud: Int = 6,
)

/** Estado de la sesión vigente (validación en línea) */
@Serializable
data class SesionInfoDto(
    val username: String = "",
    @SerialName("nombre_completo") val nombreCompleto: String? = null,
    val rol: String = "viewer",
    val cedula: String? = null,
    @SerialName("debe_cambiar_password") val debeCambiarPassword: Boolean = false,
    @SerialName("expira_en") val expiraEn: String? = null,
    @SerialName("password_min_longitud") val passwordMinLongitud: Int = 6,
)

@Serializable
data class CorrectoDto(val correcto: Boolean = true)

/**
 * Respuesta del auto-emparejamiento: el par que convierte a este teléfono en
 * un puesto más de la red. El servidor solo lo devuelve una vez; en su base
 * queda únicamente el hash del token.
 */
@Serializable
data class EmparejarRespuestaDto(
    @SerialName("dispositivo_id") val dispositivoId: String = "",
    val token: String = "",
)

/** Error del protocolo: el mismo cuerpo para todos los códigos HTTP */
@Serializable
data class ErrorDto(val error: String = "")

/** Panel de control: indicadores por bloque, filtrados por el rol */
@Serializable
data class DashboardDto(
    val rol: String = "",
    val usuario: String = "",
    val indicadores: Map<String, JsonElement> = emptyMap(),
)

@Serializable
data class AuditoriaDto(val eventos: List<JsonElement> = emptyList())

/** Cuenta de la institución (nunca viaja su hash) */
@Serializable
data class UsuarioRemotoDto(
    val id: Long = 0,
    val username: String = "",
    @SerialName("nombre_completo") val nombreCompleto: String? = null,
    val cedula: String? = null,
    val rol: String = "viewer",
    val activo: Int = 1,
    @SerialName("debe_cambiar_password") val debeCambiarPassword: Int = 0,
    val bloqueado: Int = 0,
    @SerialName("intentos_fallidos") val intentosFallidos: Int = 0,
    @SerialName("ultimo_login") val ultimoLogin: String? = null,
)

@Serializable
data class ListarUsuariosDto(val usuarios: List<UsuarioRemotoDto> = emptyList())

@Serializable
data class UsuarioRespuestaDto(val usuario: UsuarioRemotoDto? = null)

/** Perfil del usuario autenticado: datos editables y de solo lectura */
@Serializable
data class PerfilDto(
    val username: String = "",
    val nombre_completo: String? = null,
    val rol: String = "viewer",
    val cedula: String? = null,
    val activo: Boolean = false,
    val debe_cambiar_password: Boolean = false,
    val usuario_id: Int = 0,
)

/** Solicitud de actualización de perfil propio */
@Serializable
data class ActualizarPerfilDto(
    val nombre_completo: String? = null,
    val cedula: String? = null,
)

/** Documento generado en el servidor; se baja por el canal de binarios */
@Serializable
data class ArchivoDto(
    val hash: String = "",
    val tamano: Int = 0,
    val nombre: String? = null,
    val descarga: String? = null,
)

/** Docentes referenciados por los grados (usuarios no se replican) */
@Serializable
data class DocenteDto(
    val uuid: String = "",
    val nombre: String = "",
)
