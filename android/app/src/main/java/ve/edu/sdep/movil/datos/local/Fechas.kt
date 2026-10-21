package ve.edu.sdep.movil.datos.local

import java.time.Instant
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

/**
 * Conversión de fechas entre el teléfono y el protocolo.
 *
 * El sistema de escritorio guarda fechas UTC «ingenuas» (sin zona) en SQLite y
 * las serializa con ``isoformat()``. Por eso aquí se envía siempre
 * ``AAAA-MM-DDTHH:MM:SS`` en UTC, sin la «Z»: si se enviara con zona, el motor
 * de mezcla compararía cadenas con desplazamientos distintos y las marcas de
 * tiempo dejarían de ser comparables entre equipos.
 */
object Fechas {

    private val FORMATO = DateTimeFormatter.ISO_LOCAL_DATE_TIME

    /** Milisegundos desde la época a texto ISO 8601 en UTC sin zona */
    fun isoDesde(millis: Long): String =
        Instant.ofEpochMilli(millis)
            .atOffset(ZoneOffset.UTC)
            .toLocalDateTime()
            .format(FORMATO)

    /**
     * Texto ISO a milisegundos, aceptando las tres formas que pueden llegar:
     * con «Z», con desplazamiento horario o sin zona (UTC).
     */
    fun desdeIso(texto: String?): Long? {
        val limpio = texto?.trim().orEmpty()
        if (limpio.isEmpty()) return null
        return runCatching { Instant.parse(limpio).toEpochMilli() }.getOrNull()
            ?: runCatching { OffsetDateTime.parse(limpio).toInstant().toEpochMilli() }.getOrNull()
            ?: runCatching {
                LocalDateTime.parse(limpio.removeSuffix("Z")).toInstant(ZoneOffset.UTC).toEpochMilli()
            }.getOrNull()
    }

    /** Momento actual en UTC, sin zona, para enviarlo al servidor */
    fun ahoraIso(): String = isoDesde(System.currentTimeMillis())
}
