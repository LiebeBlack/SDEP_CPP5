package ve.edu.sdep.movil.datos.remoto

import kotlinx.serialization.json.Json
import retrofit2.HttpException

/**
 * Mensaje que redactó el nodo central para un rechazo HTTP.
 *
 * El servidor devuelve siempre `{"error": "..."}` y ese texto es el que ya
 * conoce el usuario del escritorio: «la cuenta está bloqueada», «intentos
 * restantes: 3», «la contraseña actual es incorrecta»… Antes el teléfono lo
 * descartaba y mostraba un genérico «Usuario o contraseña incorrectos» incluso
 * cuando el problema era un bloqueo o una cuenta desactivada, de modo que el
 * diagnóstico desde el móvil era imposible.
 *
 * Se lee el cuerpo una sola vez; un intermediario que devuelva HTML o un
 * cuerpo vacío cae en `null` y el llamador conserva su mensaje propio.
 */
fun HttpException.mensajeDelServidor(json: Json): String? = try {
    val cuerpo = response()?.errorBody()?.string()
    if (cuerpo.isNullOrBlank()) {
        null
    } else {
        json.decodeFromString(ErrorDto.serializer(), cuerpo).error.trim().ifEmpty { null }
    }
} catch (_: Throwable) {
    null
}
