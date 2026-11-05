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

    private val FORMATO = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss")

    /**
     * Milisegundos desde la época a texto ISO 8601 en UTC sin zona.
     *
     * Siempre se emiten los segundos y, si hay fracción, con seis dígitos
     * (como ``datetime.isoformat()`` de Python). Antes se usaba
     * ``ISO_LOCAL_DATE_TIME``, que omite los segundos en punto y la fracción
     * en cero: dos marcas del mismo ancho aparente podían ordenar mal al
     * compararse como texto en el motor de mezcla.
     */
    fun isoDesde(millis: Long): String {
        val fecha = Instant.ofEpochMilli(millis).atOffset(ZoneOffset.UTC).toLocalDateTime()
        val base = fecha.format(FORMATO)
        val nano = fecha.nano
        if (nano == 0) return base
        // Seis dígitos como Python; los milisegundos del epoch siempre son
        // múltiplos de 1.000.000 de nanosegundos.
        return base + "." + (nano / 1_000).toString().padStart(6, '0')
    }

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
