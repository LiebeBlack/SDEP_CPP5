package ve.edu.sdep.movil.ui.modulos

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/**
 * Piezas compartidas por las pantallas de consulta.
 *
 * Todas leen el catálogo ya resuelto: no consultan la base ni la red. Así una
 * lista, una ficha y el panel se pintan con las mismas reglas de color y la
 * misma jerarquía tipográfica que el resto de la aplicación.
 */

/** Colores de fondo y contenido para cada intención de estado */
@Composable
fun coloresTono(tono: Tono): Pair<Color, Color> = when (tono) {
    Tono.NEUTRO -> MaterialTheme.colorScheme.surfaceVariant to
        MaterialTheme.colorScheme.onSurfaceVariant
    Tono.EXITO -> MaterialTheme.colorScheme.primaryContainer to
        MaterialTheme.colorScheme.onPrimaryContainer
    Tono.ALERTA -> MaterialTheme.colorScheme.tertiaryContainer to
        MaterialTheme.colorScheme.onTertiaryContainer
    Tono.ERROR -> MaterialTheme.colorScheme.errorContainer to
        MaterialTheme.colorScheme.onErrorContainer
}

/** Distintivo de estado de una fila (Activo, Vencido, Pendiente…) */
@Composable
fun EtiquetaTono(valor: String, tono: Tono) {
    val (fondo, contenido) = coloresTono(tono)
    Surface(color = fondo, contentColor = contenido, shape = MaterialTheme.shapes.small) {
        Text(
            text = valor,
            style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
        )
    }
}

/** Tarjeta de una fila de lista; toda la tarjeta abre la ficha */
@Composable
fun TarjetaFila(fila: FilaCatalogo, alAbrir: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = alAbrir),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = fila.titulo,
                    style = MaterialTheme.typography.titleSmall,
                    modifier = Modifier.weight(1f),
                )
                fila.etiqueta?.let { etiqueta ->
                    Spacer(Modifier.width(8.dp))
                    EtiquetaTono(etiqueta, fila.tono)
                }
            }

            if (fila.subtitulo.isNotBlank()) {
                Spacer(Modifier.height(3.dp))
                Text(
                    text = fila.subtitulo,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            if (!fila.nota.isNullOrBlank()) {
                Spacer(Modifier.height(3.dp))
                Text(
                    text = fila.nota,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
            }
        }
    }
}

/** Recuadro de una cifra del panel de control */
@Composable
fun TarjetaIndicador(indicador: IndicadorPanel, modificador: Modifier = Modifier) {
    val (fondo, contenido) = coloresTono(indicador.tono)
    Card(
        modifier = modificador,
        colors = CardDefaults.cardColors(containerColor = fondo),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(
                text = indicador.valor,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.SemiBold,
                color = contenido,
            )
            Spacer(Modifier.height(2.dp))
            Text(
                text = indicador.etiqueta,
                style = MaterialTheme.typography.labelMedium,
                color = contenido,
            )
        }
    }
}

/** Un par etiqueta/valor de una ficha, en dos líneas para no truncar */
@Composable
fun CampoDetalle(campo: CampoFicha) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            text = campo.etiqueta,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(text = campo.valor, style = MaterialTheme.typography.bodyMedium)
    }
}

/** Sección de una ficha: título, campos y, si la hay, una nota al pie */
@Composable
fun TarjetaSeccion(seccion: SeccionFicha) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(
                text = seccion.titulo,
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.primary,
            )
            seccion.campos.forEach { campo -> CampoDetalle(campo) }
            if (!seccion.parrafo.isNullOrBlank()) {
                Text(
                    text = seccion.parrafo,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
