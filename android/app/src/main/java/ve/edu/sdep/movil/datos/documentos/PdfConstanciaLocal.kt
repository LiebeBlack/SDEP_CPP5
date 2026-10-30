package ve.edu.sdep.movil.datos.documentos

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import java.io.ByteArrayOutputStream

/**
 * Constancia PDF armada en el propio teléfono.
 *
 * El nodo central sigue siendo la vía para el documento con folio y archivo en
 * el legajo, pero la mayoría de las solicitudes son «mi constancia de trabajo
 * con mis datos»: mandar la plantilla, esperar a que el servidor abra la base,
 * renderice con ReportLab y luego descargar el binario cuesta dos viajes de red
 * y un proceso completo en el escritorio. Aquí el mismo documento se compone
 * con el espejo local en decenas de milisegundos y funciona sin conexión, que
 * es lo que hace usable un equipo de gama baja.
 *
 * Renderiza el subconjunto de Markdown que ya acepta el servidor —títulos,
 * negritas, cursivas, viñetas y saltos de párrafo— y sustituye los mismos
 * marcadores `{{campo}}`, de modo que una plantilla se ve igual por las dos
 * vías.
 */
data class DatosConstancia(
    val institucion: String,
    val titulo: String,
    val valores: Map<String, String>,
)

/** Texto del formato institucional básico (mismo cuerpo que emite el nodo). */
const val PLANTILLA_INSTITUCIONAL = """El(la) que suscribe, en representación de {{institucion}}, hace constar que **{{nombre_completo}}**, portador(a) de la cédula de identidad N° **{{cedula}}**, labora en esta institución desde el **{{fecha_contratacion}}**.

Actualmente desempeña el cargo de **{{cargo}}** en el departamento de **{{departamento}}**, con una categoría de **{{tipo_empleado}}** y un salario mensual de **{{salario}}**.

Esta constancia se expide a solicitud de la persona interesada, en fecha {{fecha_emision}}, para los fines que estime convenientes."""

// Geometría de una hoja A4 en puntos (72 ppp): compartida por el compositor
// de párrafos y el control de páginas.
private const val ANCHO = 595
private const val ALTO = 842
private const val MARGEN_IZQ = 64f
private const val MARGEN_DER = 64f
private const val MARGEN_SUP = 60f
private const val MARGEN_INF = 72f

object PdfConstanciaLocal {

    private const val SANGRIA_VINETA = 18f

    private val MARCADOR = Regex("""\{\{?\s*([^}\s]{1,40})\s*\}?\}""")
    private val ENFASIS = Regex("""\*\*(.+?)\*\*|\*(.+?)\*""")
    private val ESPACIOS = Regex("""\s+""")

    /** Compone el PDF y devuelve sus bytes; nunca toca la red ni el disco. */
    fun generar(plantilla: String, datos: DatosConstancia): ByteArray {
        require(plantilla.isNotBlank()) { "La plantilla está vacía." }
        val documento = PdfDocument()
        try {
            val lienzo = Lienzo(documento)
            lienzo.abrir()
            cabecera(lienzo, datos)

            var lineasVacias = 0
            // El título ya se imprime en la cabecera: si la plantilla abre con un
            // encabezado igual (lo normal, porque su primer «#» es el título), se
            // omite para que no salga impreso dos veces.
            var primerEncabezado = true
            plantilla.split("\r\n", "\n").take(600).forEach { linea ->
                val limpia = linea.trim()
                when {
                    limpia.isEmpty() -> {
                        // Varios saltos seguidos no deben empujar el contenido
                        // fuera de la hoja: se limitan a un espaciado corto.
                        if (lineasVacias < 2) lienzo.y += 8f
                        lineasVacias++
                    }

                    limpia.startsWith("#") -> {
                        lineasVacias = 0
                        val nivel = limpia.takeWhile { it == '#' }.length.coerceIn(1, 3)
                        val texto = sustituir(limpia.drop(nivel).trim(), datos.valores)
                        val repetido = primerEncabezado &&
                            normalizarClave(texto) == normalizarClave(datos.titulo)
                        if (primerEncabezado) primerEncabezado = false
                        if (texto.isNotBlank() && !repetido) {
                            val tamano = when (nivel) {
                                1 -> 13.5f
                                2 -> 12.5f
                                else -> 11.5f
                            }
                            lienzo.y += if (nivel == 1) 6f else 4f
                            parrafo(lienzo, texto, tamano, negrita = true)
                            lienzo.y += 4f
                        }
                    }

                    limpia.startsWith("- ") || limpia.startsWith("* ") -> {
                        lineasVacias = 0
                        parrafo(
                            lienzo,
                            "• " + sustituir(limpia.drop(2).trim(), datos.valores),
                            11f,
                            negrita = false,
                            sangria = SANGRIA_VINETA,
                        )
                        lienzo.y += 2f
                    }

                    else -> {
                        lineasVacias = 0
                        parrafo(lienzo, sustituir(limpia, datos.valores), 11f, negrita = false)
                        lienzo.y += 5f
                    }
                }
            }

            if (!plantilla.contains("firma", ignoreCase = true)) firmas(lienzo)
            lienzo.cerrar()
            return ByteArrayOutputStream().also { documento.writeTo(it) }.toByteArray()
        } finally {
            documento.close()
        }
    }

    /**
     * Sustituye los marcadores aceptando la misma tolerancia que el nodo:
     * mayúsculas, acentos y espacios no impiden encontrar el dato.
     */
    private fun sustituir(texto: String, valores: Map<String, String>): String =
        MARCADOR.replace(texto) { coincidencia ->
            val crudo = coincidencia.groupValues[1]
            val normalizado = normalizarClave(crudo)
            valores[crudo]
                ?: valores.entries.firstOrNull { normalizarClave(it.key) == normalizado }?.value
                ?: coincidencia.value
        }

    private fun normalizarClave(clave: String): String = java.text.Normalizer
        .normalize(clave.trim().lowercase(), java.text.Normalizer.Form.NFD)
        .replace(Regex("""\p{M}+"""), "")
        .replace(Regex("""[^a-z0-9_]+"""), "_")
        .trim('_')

    private fun cabecera(lienzo: Lienzo, datos: DatosConstancia) {
        val institucion = Paint().aplicar(11f, negrita = true, color = Color.rgb(70, 70, 70))
        lienzo.textoCentrado(datos.institucion.uppercase(), institucion, 11f * 1.35f)
        lienzo.y += 4f
        val titulo = Paint().aplicar(17f, negrita = true, color = Color.BLACK)
        lienzo.textoCentrado(datos.titulo.uppercase(), titulo, 17f * 1.35f)
        lienzo.y += 10f
        lienzo.linea()
        lienzo.y += 10f
    }

    private fun firmas(lienzo: Lienzo) {
        lienzo.asegurar(130f)
        lienzo.y += 36f
        val ancho = (ANCHO - MARGEN_IZQ - MARGEN_DER) / 2f
        val rotulo = Paint().aplicar(9f, negrita = false, color = Color.rgb(80, 80, 80))
        val etiqueta = Paint().aplicar(9f, negrita = true, color = Color.rgb(80, 80, 80))
        val yBase = lienzo.y
        lienzo.trazo(
            MARGEN_IZQ + 12f, yBase, MARGEN_IZQ + ancho - 24f, yBase,
            Paint().aplicar(8f).apply { color = Color.rgb(120, 120, 120) },
        )
        lienzo.trazo(
            MARGEN_IZQ + ancho + 12f, yBase, ANCHO - MARGEN_DER - 12f, yBase,
            Paint().aplicar(8f).apply { color = Color.rgb(120, 120, 120) },
        )
        lienzo.trazo(
            MARGEN_IZQ + ancho + 8f, yBase - 54f, ANCHO - MARGEN_DER - 24f, yBase - 8f,
            Paint().aplicar(8f).apply {
                color = Color.rgb(90, 90, 140)
                style = Paint.Style.STROKE
            },
        )
        lienzo.canvas.drawText("Firma autorizada", MARGEN_IZQ + 12f, yBase + 13f, etiqueta)
        lienzo.canvas.drawText("Sello institucional", MARGEN_IZQ + ancho + 12f, yBase + 13f, rotulo)
        lienzo.y = yBase + 30f
    }

    // ------------------------------------------------------------------
    // Composición de párrafos con ajuste de línea
    // ------------------------------------------------------------------

    private fun parrafo(
        lienzo: Lienzo,
        texto: String,
        tamano: Float,
        negrita: Boolean,
        sangria: Float = 0f,
    ) {
        val normal = Paint().aplicar(tamano, negrita)
        val negritaPaint = Paint().aplicar(tamano, true)
        val cursivaPaint = Paint().aplicar(tamano, false, italic = true)
        val negritaCursiva = Paint().aplicar(tamano, true, italic = true)
        fun pintura(negritaTramo: Boolean, cursivaTramo: Boolean): Paint = when {
            negritaTramo && cursivaTramo -> negritaCursiva
            negritaTramo -> negritaPaint
            cursivaTramo -> cursivaPaint
            else -> normal
        }

        val altoLinea = tamano * 1.55f
        val izquierda = MARGEN_IZQ + sangria
        val limite = ANCHO - MARGEN_DER
        val espacio = normal.measureText(" ")
        var x = izquierda

        lienzo.asegurar(altoLinea)
        for (tramo in tramos(texto)) {
            tramo.texto.split(ESPACIOS).filter { it.isNotEmpty() }.forEach { palabra ->
                val pintura = pintura(tramo.negrita, tramo.cursiva)
                val ancho = pintura.measureText(palabra)
                val avance = if (x > izquierda) espacio else 0f
                if (x + avance + ancho > limite && x > izquierda) {
                    lienzo.y += altoLinea
                    if (lienzo.y > ALTO - MARGEN_INF) {
                        lienzo.abrir()
                        lienzo.y = MARGEN_SUP
                    }
                    x = izquierda
                } else if (avance > 0f) {
                    x += avance
                }
                lienzo.canvas.drawText(palabra, x, lienzo.y, pintura)
                x += ancho
            }
        }
        lienzo.y += altoLinea
    }

    private data class Tramo(val texto: String, val negrita: Boolean, val cursiva: Boolean)

    private fun tramos(texto: String): List<Tramo> {
        val salida = ArrayList<Tramo>(8)
        var cursor = 0
        ENFASIS.findAll(texto).forEach { coincidencia ->
            if (coincidencia.range.first > cursor) {
                salida += Tramo(texto.substring(cursor, coincidencia.range.first), false, false)
            }
            if (coincidencia.groupValues[1].isNotEmpty()) {
                salida += Tramo(coincidencia.groupValues[1], true, false)
            } else {
                salida += Tramo(coincidencia.groupValues[2], false, true)
            }
            cursor = coincidencia.range.last + 1
        }
        if (cursor < texto.length) salida += Tramo(texto.substring(cursor), false, false)
        return salida.filter { it.texto.isNotEmpty() }
    }

    /** Controla la hoja actual, el pie de página y los saltos. */
    private class Lienzo(private val documento: PdfDocument) {
        private var pagina: PdfDocument.Page? = null
        private var numero = 0
        var y = MARGEN_SUP

        val canvas: Canvas get() = requireNotNull(pagina).canvas

        fun abrir() {
            cerrarHoja()
            numero++
            val info = PdfDocument.PageInfo.Builder(ANCHO, ALTO, numero).create()
            pagina = documento.startPage(info)
            y = MARGEN_SUP
        }

        fun cerrar() {
            cerrarHoja()
        }

        private fun cerrarHoja() {
            val actual = pagina ?: return
            val pie = Paint().aplicar(8.5f, color = Color.rgb(110, 110, 110))
            actual.canvas.drawText("Página $numero", ANCHO / 2f - pie.measureText("Página $numero") / 2f, ALTO - 34f, pie)
            documento.finishPage(actual)
            pagina = null
        }

        /** Abre otra hoja si el bloque siguiente no cabe completo. */
        fun asegurar(alto: Float) {
            if (y + alto > ALTO - MARGEN_INF) abrir()
        }

        fun linea() {
            trazo(MARGEN_IZQ, y, ANCHO - MARGEN_DER, y, Paint().aplicar(8f).apply { color = Color.rgb(90, 90, 140) })
        }

        fun trazo(desdeX: Float, desdeY: Float, hastaX: Float, hastaY: Float, pintura: Paint) {
            canvas.drawLine(desdeX, desdeY, hastaX, hastaY, pintura)
        }

        fun textoCentrado(texto: String, pintura: Paint, altoLinea: Float) {
            asegurar(altoLinea)
            canvas.drawText(texto, (ANCHO - pintura.measureText(texto)) / 2f, y, pintura)
            y += altoLinea
        }
    }
}

/** Pintura lista para dibujar texto con el tamaño, peso y color pedidos. */
private fun Paint.aplicar(
    tamano: Float,
    negrita: Boolean = false,
    color: Int = Color.BLACK,
    italic: Boolean = false,
): Paint = apply {
    isAntiAlias = true
    textSize = tamano
    this.color = color
    typeface = when {
        negrita && italic -> Typeface.create(Typeface.DEFAULT, Typeface.BOLD_ITALIC)
        negrita -> Typeface.DEFAULT_BOLD
        italic -> Typeface.create(Typeface.DEFAULT, Typeface.ITALIC)
        else -> Typeface.DEFAULT
    }
}
