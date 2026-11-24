package ve.edu.sdep.movil.ui.modulos

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.OpenableColumns
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AttachFile
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import ve.edu.sdep.movil.datos.documentos.TipoAdjunto
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

/**
 * Tarjeta de adjunto de la ficha (documento o incidencia).
 *
 * Muestra el estado del archivo: nombre, huella y si el binario ya llegó a
 * este teléfono. Permite adjuntar o reemplazar el archivo desde el teléfono
 * (la cola de binarios lo sube al nodo central) y abrir o compartir el que
 * ya está disponible. La escritura pasa por el repositorio, que vuelve a
 * comprobar el permiso aunque el botón aparezca.
 */
@Composable
fun TarjetaAdjunto(
    estado: AdjuntosViewModel.Estado,
    puedeAdjuntar: Boolean,
    alAdjuntar: (nombre: String, mime: String?, bytes: ByteArray) -> Unit,
    alPedirContenido: (compartir: Boolean) -> Unit,
    alConsumirContenido: () -> Unit,
) {
    val contexto = LocalContext.current
    val alcance = rememberCoroutineScope()
    val adjunto = estado.adjunto

    val selector = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument(),
    ) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        alcance.launch {
            try {
                val (nombre, mime, bytes) = withContext(Dispatchers.IO) {
                    leerAdjuntoSeleccionado(contexto, uri)
                }
                val mimeVerificado = TipoAdjunto.verificar(nombre, mime, bytes)
                    ?: error("Formato no admitido o firma incompatible. Seleccione un PDF, JPEG o PNG con extensión y tipo compatibles.")
                alAdjuntar(nombre, mimeVerificado, bytes)
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (error: Exception) {
                // El error de lectura se informa sin bloquear la ficha.
                android.widget.Toast.makeText(
                    contexto,
                    error.message ?: "No se pudo leer el archivo seleccionado.",
                    android.widget.Toast.LENGTH_LONG,
                ).show()
            }
        }
    }
    val lanzarSelector = {
        selector.launch(arrayOf("*/*"))
        Unit
    }

    LaunchedEffect(estado.contenido) {
        val contenido = estado.contenido ?: return@LaunchedEffect
        val nombre = adjunto?.nombre ?: "adjunto"
        abrirAdjunto(
            contexto,
            nombre,
            adjunto?.mime,
            contenido,
            compartir = estado.compartirContenido,
        )
        alConsumirContenido()
    }

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Filled.AttachFile,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                )
                Text(
                    text = "Archivo adjunto",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.padding(start = 8.dp),
                )
            }
            when {
                estado.cargando -> CircularProgressIndicator(
                    modifier = Modifier.padding(vertical = 8.dp),
                )
                adjunto == null -> Text(
                    text = "El estado del adjunto no está disponible en este momento.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                adjunto.hash == null -> Column(
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                ) {
                    Text(
                        text = "Sin archivo adjunto.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    if (puedeAdjuntar) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            TextButton(
                                enabled = !estado.adjuntando,
                                onClick = lanzarSelector,
                            ) {
                                Text("Adjuntar archivo")
                            }
                            if (estado.adjuntando) {
                                CircularProgressIndicator(modifier = Modifier.padding(8.dp))
                            }
                        }
                    }
                }
                else -> {
                    Text(
                        text = adjunto.nombre ?: "Archivo adjunto",
                        style = MaterialTheme.typography.bodyLarge,
                    )
                    Text(
                        text = if (adjunto.disponible) {
                            "Disponible en este teléfono · ${tamanoLegible(adjunto.tamano)}"
                        } else {
                            "Anunciado por huella · aún no llegó a este teléfono " +
                                "(sincronice con el nodo central)"
                        },
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.outline,
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        if (puedeAdjuntar) {
                            TextButton(
                                enabled = !estado.adjuntando,
                                onClick = lanzarSelector,
                            ) {
                                Text(
                                    "Reemplazar archivo",
                                )
                            }
                            if (estado.adjuntando) {
                                CircularProgressIndicator(
                                    modifier = Modifier.padding(8.dp),
                                )
                            }
                        }
                        if (adjunto.disponible) {
                            TextButton(onClick = { alPedirContenido(false) }) { Text("Abrir") }
                            TextButton(onClick = { alPedirContenido(true) }) { Text("Compartir") }
                        }
                    }
                }
            }
        }
    }
}

/** Tamaño en una unidad legible, sin decimales absurdos */
internal fun tamanoLegible(bytes: Int): String = when {
    bytes <= 0 -> "0 B"
    bytes < 1024 -> "$bytes B"
    bytes < 1024 * 1024 -> "${(bytes + 512) / 1024} KB"
    else -> String.format("%.1f MB", bytes / (1024.0 * 1024.0))
}

/**
 * Lee el archivo elegido con el límite de 8 MB de esta interfaz móvil; el
 * nodo admite un límite configurable mayor. Un archivo superior a este límite
 * se rechaza antes de copiarlo al espejo.
 */
internal fun leerAdjuntoSeleccionado(
    contexto: Context,
    uri: Uri,
): Triple<String, String?, ByteArray> {
    val nombre = contexto.contentResolver.query(
        uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null,
    )?.use { cursor ->
        if (cursor.moveToFirst()) cursor.getString(0) else null
    } ?: "archivo"
    val mime = contexto.contentResolver.getType(uri)
    val bytes = contexto.contentResolver.openInputStream(uri)?.use { entrada ->
        val salida = java.io.ByteArrayOutputStream()
        val buffer = ByteArray(64 * 1024)
        var leidos = entrada.read(buffer)
        var total = 0
        while (leidos >= 0) {
            total += leidos
            if (total > MAX_BYTES_ADJUNTO) {
                error("El archivo supera el límite de 8 MB para la selección desde el teléfono.")
            }
            salida.write(buffer, 0, leidos)
            leidos = entrada.read(buffer)
        }
        salida.toByteArray()
    } ?: error("No se pudo leer el archivo seleccionado.")
    return Triple(nombre, mime, bytes)
}

/**
 * Abre o comparte el adjunto desde la caché, con el proveedor de archivos
 * privado del manifiesto: la aplicación receptora recibe un URI de lectura
 * efímera, nunca una ruta del sistema de archivos.
 */
internal suspend fun abrirAdjunto(
    contexto: Context,
    nombre: String,
    mime: String?,
    bytes: ByteArray,
    compartir: Boolean = false,
) {
    try {
        val nombreSeguro = nombreSeguroAdjunto(nombre)
        val archivo = withContext(Dispatchers.IO) {
            File(contexto.cacheDir, "documentos/$nombreSeguro").apply {
                parentFile?.mkdirs()
                writeBytes(bytes)
            }
        }
        val uri = FileProvider.getUriForFile(
            contexto, "${contexto.packageName}.archivos", archivo,
        )
        val tipo = mime?.takeIf { it.isNotBlank() } ?: TipoAdjunto.desdeNombre(nombre)
        val intent = if (compartir) {
            Intent(Intent.ACTION_SEND).apply {
                type = tipo
                putExtra(Intent.EXTRA_STREAM, uri)
                clipData = android.content.ClipData.newUri(
                    contexto.contentResolver, nombreSeguro, uri,
                )
            }
        } else {
            Intent(Intent.ACTION_VIEW).setDataAndType(uri, tipo)
        }
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        contexto.startActivity(
            Intent.createChooser(
                intent,
                if (compartir) "Compartir archivo" else "Abrir archivo",
            ),
        )
    } catch (cancelacion: CancellationException) {
        throw cancelacion
    } catch (error: Exception) {
        android.widget.Toast.makeText(
            contexto,
            error.message
                ?: "No hay una aplicación instalada capaz de abrir este archivo.",
            android.widget.Toast.LENGTH_LONG,
        ).show()
    }
}

/** Nombre sin ruta, con caracteres seguros y extensión conservada */
internal fun nombreSeguroAdjunto(nombre: String): String {
    val base = nombre.substringAfterLast('/').substringAfterLast('\\')
    val limpio = base
        .filter { it.isLetterOrDigit() || it in "._- ()" }
        .take(100)
        .trim()
    return limpio.takeUnless { it.isBlank() || it == "." || it == ".." } ?: "adjunto"
}

/** Límite de tamaño de los archivos seleccionados desde la interfaz móvil */
internal const val MAX_BYTES_ADJUNTO = 8 * 1024 * 1024
