package ve.edu.sdep.movil.ui.comun

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import ve.edu.sdep.movil.dominio.modelo.EstadoSincronizacion
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BarraSuperior(
    titulo: String,
    alVolver: (() -> Unit)? = null,
    acciones: @Composable RowScope.() -> Unit = {},
) {
    TopAppBar(
        title = { Text(titulo) },
        navigationIcon = {
            if (alVolver != null) {
                IconButton(onClick = alVolver) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Volver")
                }
            }
        },
        actions = acciones,
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = MaterialTheme.colorScheme.background,
        ),
    )
}

/** Distintivo del estado de sincronización de un registro */
@Composable
fun EtiquetaEstado(
    estado: EstadoSincronizacion,
    modificador: Modifier = Modifier,
) {
    val fondo = when (estado) {
        EstadoSincronizacion.PENDIENTE -> MaterialTheme.colorScheme.tertiaryContainer
        EstadoSincronizacion.SINCRONIZADO -> MaterialTheme.colorScheme.primaryContainer
        EstadoSincronizacion.RECHAZADO -> MaterialTheme.colorScheme.errorContainer
    }
    val contenido = when (estado) {
        EstadoSincronizacion.PENDIENTE -> MaterialTheme.colorScheme.onTertiaryContainer
        EstadoSincronizacion.SINCRONIZADO -> MaterialTheme.colorScheme.onPrimaryContainer
        EstadoSincronizacion.RECHAZADO -> MaterialTheme.colorScheme.onErrorContainer
    }
    Surface(color = fondo, contentColor = contenido, shape = MaterialTheme.shapes.small, modifier = modificador) {
        Text(
            text = estado.etiqueta,
            style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
        )
    }
}

@Composable
fun MensajeVacio(
    icono: ImageVector,
    titulo: String,
    detalle: String,
    modificador: Modifier = Modifier,
) {
    Column(
        modifier = modificador
            .fillMaxWidth()
            .padding(horizontal = 32.dp, vertical = 48.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(
            imageVector = icono,
            contentDescription = null,
            modifier = Modifier.size(56.dp),
            tint = MaterialTheme.colorScheme.outline,
        )
        Spacer(Modifier.height(12.dp))
        Text(titulo, style = MaterialTheme.typography.titleMedium, textAlign = TextAlign.Center)
        Spacer(Modifier.height(4.dp))
        Text(
            text = detalle,
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
fun DialogoConfirmar(
    titulo: String,
    mensaje: String,
    textoConfirmar: String = "Eliminar",
    alConfirmar: () -> Unit,
    alCancelar: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = alCancelar,
        title = { Text(titulo) },
        text = { Text(mensaje) },
        confirmButton = {
            TextButton(onClick = alConfirmar) {
                Text(textoConfirmar, color = MaterialTheme.colorScheme.error)
            }
        },
        dismissButton = {
            TextButton(onClick = alCancelar) { Text("Cancelar") }
        },
    )
}

// ----------------------------------------------------------------------
// Fechas
// ----------------------------------------------------------------------
private val ZONA = ZoneId.systemDefault()
private val IDIOMA = Locale.forLanguageTag("es-VE")
private val FORMATO_FECHA_HORA = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm", IDIOMA)
private val FORMATO_HORA = DateTimeFormatter.ofPattern("HH:mm", IDIOMA)
private val FORMATO_FECHA = DateTimeFormatter.ofPattern("dd/MM/yyyy", IDIOMA)

fun fechaHora(millis: Long): String =
    Instant.ofEpochMilli(millis).atZone(ZONA).format(FORMATO_FECHA_HORA)

fun horaCorta(millis: Long): String =
    Instant.ofEpochMilli(millis).atZone(ZONA).format(FORMATO_HORA)

fun fechaCorta(millis: Long): String =
    Instant.ofEpochMilli(millis).atZone(ZONA).format(FORMATO_FECHA)
