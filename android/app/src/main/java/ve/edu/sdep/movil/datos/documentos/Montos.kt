package ve.edu.sdep.movil.datos.documentos

import java.time.LocalDate
import java.time.Period
import kotlin.math.floor
import kotlin.math.roundToInt

/*
 * Valores derivados de la ficha que las constancias piden en palabras.
 *
 * Es la misma lógica que aplica el nodo central al componer el PDF
 * (`src/utils/pdf_generator.py`): así la constancia hecha en el teléfono y la
 * emitida en el escritorio dicen exactamente lo mismo.
 */

private val MESES_LARGOS = listOf(
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

private val UNIDADES_TEXTO = listOf(
    "", "UNO", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE",
    "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISÉIS",
    "DIECISIETE", "DIECIOCHO", "DIECINUEVE", "VEINTE",
)

private val DECENAS_TEXTO = listOf(
    "", "", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA",
    "SESENTA", "SETENTA", "OCHENTA", "NOVENTA",
)

private val CENTENAS_TEXTO = listOf(
    "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
    "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS",
)

private val VEINTI_TEXTO = listOf(
    "VEINTIÚN", "VEINTIDÓS", "VEINTITRÉS", "VEINTICUATRO",
    "VEINTICINCO", "VEINTISÉIS", "VEINTISIETE", "VEINTIOCHO", "VEINTINUEVE",
)

/** Nombre del mes en palabras: 10 → «octubre». */
fun mesLargo(mes: Int): String = MESES_LARGOS[(mes - 1).coerceIn(0, 11)]

/** «30 de octubre de 2026». */
fun fechaLarga(fecha: LocalDate): String =
    "${fecha.dayOfMonth} de ${MESES_LARGOS[fecha.monthValue - 1]} de ${fecha.year}"

/** «30 de octubre de 2026» a partir de una fecha ISO; el texto original si no lo es. */
fun fechaLarga(fechaIso: String?): String {
    val limpio = fechaIso?.trim().orEmpty()
    if (limpio.length < 10) return limpio
    val fecha = runCatching { LocalDate.parse(limpio.take(10)) }.getOrNull() ?: return limpio
    return fechaLarga(fecha)
}

/** «7 años y 4 meses» entre la fecha ISO indicada y hoy (o `hasta`). */
fun antiguedadLegible(desdeIso: String?, hasta: LocalDate = LocalDate.now()): String {
    val limpio = desdeIso?.trim().orEmpty()
    if (limpio.length < 10) return ""
    val desde = runCatching { LocalDate.parse(limpio.take(10)) }.getOrNull() ?: return ""
    if (hasta.isBefore(desde)) return ""
    var meses = (hasta.year - desde.year) * 12 + (hasta.monthValue - desde.monthValue)
    if (hasta.dayOfMonth < desde.dayOfMonth) meses -= 1
    if (meses <= 0) return "menos de un mes"
    val anios = meses / 12
    val resto = meses % 12
    val partes = mutableListOf<String>()
    if (anios > 0) partes += "$anios ${if (anios == 1) "año" else "años"}"
    if (resto > 0) partes += "$resto ${if (resto == 1) "mes" else "meses"}"
    return partes.joinToString(" y ")
}

/** Años cumplidos a partir de la fecha de nacimiento ISO. */
fun edadEnAnios(fechaNacimientoIso: String?): Int? {
    val limpio = fechaNacimientoIso?.trim().orEmpty()
    if (limpio.length < 10) return null
    val nacimiento = runCatching { LocalDate.parse(limpio.take(10)) }.getOrNull() ?: return null
    val anios = Period.between(nacimiento, LocalDate.now()).years
    return anios.takeIf { it in 0..130 }
}

/**
 * Monto con su expresión en palabras: «MIL OCHOCIENTOS CINCUENTA BOLÍVARES CON
 * 00/100». La parte entera va en letras y los céntimos como fracción de 100,
 * que es la forma habitual de las constancias de ingresos venezolanas.
 */
fun montoEnLetras(monto: Double, moneda: String = "BOLÍVARES"): String {
    if (!monto.isFinite() || monto < 0) return ""
    var entero = floor(monto).toLong()
    var centimos = ((monto - entero) * 100).roundToInt()
    if (centimos == 100) {
        entero += 1
        centimos = 0
    }
    if (entero > 999_999_999L) return ""
    val letras = enteroEnLetras(entero).let { if (it.endsWith("UNO")) it.dropLast(1) else it }
    return "$letras $moneda CON ${centimos.toString().padStart(2, '0')}/100"
}

private fun hasta999(numero: Int): String {
    if (numero <= 0) return ""
    if (numero == 100) return "CIEN"
    val centenas = numero / 100
    val resto = numero % 100
    val partes = mutableListOf<String>()
    if (centenas > 0) partes += CENTENAS_TEXTO[centenas]
    when {
        resto in 1..20 -> partes += UNIDADES_TEXTO[resto]
        resto in 21..29 -> partes += VEINTI_TEXTO[resto - 21]
        else -> {
            val decenas = resto / 10
            val unidades = resto % 10
            if (decenas > 0) partes += DECENAS_TEXTO[decenas]
            if (unidades > 0) partes += "Y ${UNIDADES_TEXTO[unidades]}"
        }
    }
    return partes.filter { it.isNotBlank() }.joinToString(" ")
}

private fun enteroEnLetras(numero: Long): String {
    if (numero == 0L) return "CERO"
    val millones = (numero / 1_000_000).toInt()
    val resto = (numero % 1_000_000).toInt()
    val miles = resto / 1_000
    val unidades = resto % 1_000
    val partes = mutableListOf<String>()
    if (millones > 0) {
        partes += if (millones == 1) "UN MILLÓN" else "${hasta999(millones)} MILLONES"
    }
    if (miles > 0) {
        partes += if (miles == 1) "MIL" else "${hasta999(miles)} MIL"
    }
    if (unidades > 0) partes += hasta999(unidades)
    return partes.joinToString(" ")
}
