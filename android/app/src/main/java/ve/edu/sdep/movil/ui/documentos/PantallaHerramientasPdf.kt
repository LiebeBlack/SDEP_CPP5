package ve.edu.sdep.movil.ui.documentos

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import java.io.File

private data class AccionPdf(val titulo: String, val tipo: String, val modulo: ve.edu.sdep.movil.dominio.modelo.Modulo)

private val accionesPdf = listOf(
    AccionPdf("Listado de empleados", "reporte_empleados", ve.edu.sdep.movil.dominio.modelo.Modulo.EMPLEADOS),
    AccionPdf("Documentos vencidos y próximos", "reporte_vencimientos", ve.edu.sdep.movil.dominio.modelo.Modulo.DOCUMENTOS),
    AccionPdf("Reporte de incidencias", "reporte_incidencias", ve.edu.sdep.movil.dominio.modelo.Modulo.INCIDENCIAS),
    AccionPdf("Reporte de contratos", "reporte_contratos", ve.edu.sdep.movil.dominio.modelo.Modulo.CONTRATOS),
    AccionPdf("Planilla de nómina", "planilla_nomina", ve.edu.sdep.movil.dominio.modelo.Modulo.NOMINA),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaHerramientasPdf(
    sesion: Sesion,
    alVolver: () -> Unit,
    vistaModelo: HerramientasPdfViewModel = hiltViewModel(),
) {
    val estado by vistaModelo.estado.collectAsStateWithLifecycle()
    val contexto = LocalContext.current
    val alcance = rememberCoroutineScope()
    val snackbar = remember { SnackbarHostState() }
    var empleadoExpandido by rememberSaveable { mutableStateOf(false) }
    var plantillaExpandida by rememberSaveable { mutableStateOf(false) }
    var periodoInicio by rememberSaveable { mutableStateOf(java.time.LocalDate.now().withDayOfMonth(1).toString()) }
    var periodoFin by rememberSaveable { mutableStateOf(java.time.LocalDate.now().toString()) }
    var tituloSubida by rememberSaveable { mutableStateOf("") }
    var nombreDocumento by rememberSaveable { mutableStateOf("Constancia de trabajo") }
    val periodoValido = remember(periodoInicio, periodoFin) {
        runCatching {
            val desde = java.time.LocalDate.parse(periodoInicio)
            val hasta = java.time.LocalDate.parse(periodoFin)
            !hasta.isBefore(desde)
        }.getOrDefault(false)
    }
    val puedeEmitir = sesion.puedeAbrir(ve.edu.sdep.movil.dominio.modelo.Modulo.EMPLEADOS) &&
        sesion.puede(Permiso.REPORTAR)
    val puedeAdjuntar = sesion.puedeAbrir(ve.edu.sdep.movil.dominio.modelo.Modulo.DOCUMENTOS) &&
        sesion.puede(Permiso.CREAR)
    val puedeUsarPlantilla = puedeEmitir ||
        (sesion.esTrabajador && sesion.puedeAbrir(ve.edu.sdep.movil.dominio.modelo.Modulo.DOCUMENTOS) && sesion.puede(Permiso.CREAR))
    var seccionActiva by rememberSaveable {
        mutableStateOf(
            when {
                puedeUsarPlantilla -> "constancia"
                else -> "legajo"
            },
        )
    }
    val puedeVerFicha = puedeEmitir
    val selectorMarkdown = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) alcance.launch {
            try {
                vistaModelo.cambiarMarkdown(withContext(Dispatchers.IO) { cargarMarkdown(contexto, uri) })
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (error: Exception) {
                vistaModelo.errorSeleccionArchivo(error.message ?: "No se pudo leer la plantilla")
            }
        }
    }
    val selectorPdf = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) alcance.launch {
            try {
                val (nombre, contenido) = withContext(Dispatchers.IO) { cargarPdf(contexto, uri) }
                if (tituloSubida.isBlank()) tituloSubida = nombre.substringBeforeLast('.')
                vistaModelo.subir(nombre, tituloSubida.ifBlank { nombre.substringBeforeLast('.') }, contenido)
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (error: Exception) {
                vistaModelo.errorSeleccionArchivo(error.message ?: "No se pudo leer el PDF")
            }
        }
    }
    LaunchedEffect(sesion.usuario, sesion.rol, sesion.cedula) {
        vistaModelo.actualizarSesion(sesion.usuario, sesion.cedula, sesion.esTrabajador)
        if (!sesion.puede(Permiso.CREAR)) {
            vistaModelo.limpiarPdf()
            tituloSubida = ""
        }
    }
    LaunchedEffect(estado.mensaje) {
        estado.mensaje?.let { snackbar.showSnackbar(it) }
    }
    LaunchedEffect(sesion.usuario) {
        if (sesion.esTrabajador) seccionActiva = "constancia"
    }

    Scaffold(
        topBar = { BarraSuperior("Documentos de personal", alVolver) },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = MaterialTheme.shapes.large,
                color = MaterialTheme.colorScheme.primaryContainer,
                contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
            ) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Gestión documental", style = MaterialTheme.typography.headlineSmall)
                    Text(
                        "Emite constancias laborales, genera reportes y organiza los PDF del legajo.",
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    if (sesion.esTrabajador) {
                        Text("Acceso personal · ${sesion.nombre}", style = MaterialTheme.typography.labelLarge)
                    } else {
                        Text("Sesión: ${sesion.etiquetaRol}", style = MaterialTheme.typography.labelLarge)
                    }
                }
            }
            if (estado.cargando || estado.cargandoEmpleados) LinearProgressIndicator(Modifier.fillMaxWidth())
            val secciones = listOfNotNull(
                if (puedeUsarPlantilla) "constancia" to "Constancias" else null,
                if (puedeAdjuntar || puedeVerFicha || sesion.esTrabajador) "legajo" to "Legajo" else null,
                if (accionesPdf.any { sesion.puedeAbrir(it.modulo) && sesion.puede(Permiso.REPORTAR) }) "reportes" to "Reportes" else null,
            )
            LaunchedEffect(secciones, seccionActiva) {
                if (secciones.none { (clave, _) -> clave == seccionActiva }) {
                    seccionActiva = secciones.firstOrNull()?.first.orEmpty()
                }
            }
            Row(
                modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                secciones.forEach { (clave, titulo) ->
                    if (seccionActiva == clave) {
                        Button(onClick = { seccionActiva = clave }, modifier = Modifier.width(112.dp)) { Text(titulo) }
                    } else {
                        OutlinedButton(onClick = { seccionActiva = clave }, modifier = Modifier.width(112.dp)) { Text(titulo) }
                    }
                }
            }
            if (!sesion.esTrabajador && (puedeEmitir || puedeAdjuntar) && seccionActiva != "reportes") ExposedDropdownMenuBox(
                expanded = empleadoExpandido,
                onExpandedChange = { empleadoExpandido = it },
            ) {
                OutlinedTextField(
                    value = estado.empleados.firstOrNull { it.id == estado.empleadoId }?.let {
                        "${it.nombreCompleto} · ${it.cedula}"
                    } ?: if (estado.cargandoEmpleados) "Cargando empleados…" else "Sin empleados sincronizados",
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Empleado del legajo") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(empleadoExpandido) },
                    enabled = !estado.cargandoEmpleados && estado.empleados.isNotEmpty(),
                    modifier = Modifier.fillMaxWidth().menuAnchor(),
                )
                ExposedDropdownMenu(expanded = empleadoExpandido, onDismissRequest = { empleadoExpandido = false }) {
                    estado.empleados.forEach { empleado ->
                        DropdownMenuItem(
                            text = { Text("${empleado.nombreCompleto} · ${empleado.cedula}") },
                            onClick = { vistaModelo.seleccionarEmpleado(empleado.id); empleadoExpandido = false },
                        )
                    }
                }
            }
            if (puedeUsarPlantilla && seccionActiva == "constancia") Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Constancia de trabajo", style = MaterialTheme.typography.titleLarge)
                    Text(
                        "Previsualiza y personaliza la plantilla; los datos de identidad y empleo se completan desde la ficha oficial.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    ExposedDropdownMenuBox(expanded = plantillaExpandida, onExpandedChange = { plantillaExpandida = it }) {
                        OutlinedTextField(
                            value = if (estado.plantillaIndice < PLANTILLAS_CONSTANCIA.size) {
                                PLANTILLAS_CONSTANCIA[estado.plantillaIndice].first
                            } else "Plantilla personalizada",
                            onValueChange = {}, readOnly = true, label = { Text("Plantilla preconfigurada") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(plantillaExpandida) },
                            modifier = Modifier.fillMaxWidth().menuAnchor(),
                        )
                        ExposedDropdownMenu(expanded = plantillaExpandida, onDismissRequest = { plantillaExpandida = false }) {
                            PLANTILLAS_CONSTANCIA.forEachIndexed { indice, item ->
                                DropdownMenuItem(text = { Text(item.first) }, onClick = {
                                    nombreDocumento = item.first
                                    vistaModelo.seleccionarPlantilla(indice)
                                    plantillaExpandida = false
                                })
                            }
                        }
                    }
                    OutlinedButton(
                        enabled = !estado.cargando && !estado.cargandoEmpleados,
                        onClick = { selectorMarkdown.launch(arrayOf("text/markdown", "text/plain", "application/octet-stream")) },
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text("Importar plantilla Markdown (.md)") }
                    OutlinedTextField(
                        value = estado.markdown,
                        onValueChange = { texto ->
                            if (texto.toByteArray(Charsets.UTF_8).size <= 65_536) {
                                vistaModelo.cambiarMarkdown(texto)
                            }
                        },
                        label = { Text("Plantilla Markdown") },
                        supportingText = { Text("Campos: {{nombre}}, {{nombre_completo}}, {{cedula}}, {{cargo}}, {{departamento}}, {{salario}}, {{fecha_contratacion}}, {{fecha_emision}}, {{institucion}} · máximo 64 KB") },
                        minLines = 5,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Text(
                        "El documento incluirá el nombre institucional, datos laborales, fecha de emisión, firma y espacio para el sello.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            modifier = Modifier.fillMaxWidth(),
                        enabled = !estado.cargando && !estado.cargandoEmpleados && estado.empleadoId != null && estado.markdown.isNotBlank(),
                        onClick = {
                            nombreDocumento = PLANTILLAS_CONSTANCIA.getOrNull(estado.plantillaIndice)?.first ?: "Constancia personalizada"
                            vistaModelo.constancia(personalizada = true, titulo = nombreDocumento)
                        },
                        ) { Text("Generar ${nombreDocumento.lowercase()}") }
                        Button(
                            modifier = Modifier.fillMaxWidth(),
                        enabled = !estado.cargando && !estado.cargandoEmpleados && estado.empleadoId != null,
                        onClick = { vistaModelo.constancia(personalizada = false, titulo = "Constancia de trabajo") },
                        ) { Text("Usar formato institucional básico") }
                    }
                }
            }

            if ((puedeAdjuntar || puedeVerFicha || sesion.esTrabajador) && seccionActiva == "legajo") Card(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("Legajo documental", style = MaterialTheme.typography.titleLarge)
                    Text(
                        if (sesion.esTrabajador) "Los documentos se guardan únicamente en su ficha personal."
                        else "Adjunta documentos PDF o genera una ficha del empleado seleccionado.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    if (puedeAdjuntar) OutlinedTextField(
                        value = tituloSubida,
                        onValueChange = { tituloSubida = it.take(200) },
                        label = { Text("Título para el legajo") },
                        supportingText = { Text("Usa un nombre corto que ayude a encontrar el documento.") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                    )
                    if (puedeAdjuntar) Button(
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !estado.cargando && !estado.cargandoEmpleados && estado.empleadoId != null && tituloSubida.isNotBlank(),
                        onClick = { selectorPdf.launch(arrayOf("application/pdf")) },
                    ) { Text("Seleccionar y adjuntar PDF · máximo 8 MB") }
                    if (puedeVerFicha) OutlinedButton(
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !estado.cargando && !estado.cargandoEmpleados && estado.empleadoId != null,
                        onClick = { vistaModelo.ficha() },
                    ) { Text("Generar ficha del empleado") }
                    if (sesion.esTrabajador && estado.empleadoId == null && !estado.cargandoEmpleados) {
                        Text(
                            estado.mensaje ?: "No encontramos su ficha sincronizada. Sincronice los datos y vuelva a intentar.",
                            color = MaterialTheme.colorScheme.tertiary,
                        )
                    }
                }
            }

            val reportes = accionesPdf.filter { sesion.puedeAbrir(it.modulo) && sesion.puede(Permiso.REPORTAR) }
            if (reportes.isNotEmpty() && seccionActiva == "reportes") {
                Text("Reportes administrativos", style = MaterialTheme.typography.titleLarge)
                Text(
                    "Los documentos se generan en el nodo institucional con los permisos de su cuenta.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            reportes.filter { seccionActiva == "reportes" }.forEach { accion ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(accion.titulo, style = MaterialTheme.typography.titleMedium)
                        if (accion.tipo == "planilla_nomina") {
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                OutlinedButton(onClick = {
                                    val hoy = java.time.LocalDate.now()
                                    periodoInicio = hoy.withDayOfMonth(1).toString()
                                    periodoFin = hoy.toString()
                                }, modifier = Modifier.weight(1f)) { Text("Mes actual") }
                                OutlinedButton(onClick = {
                                    val hoy = java.time.LocalDate.now()
                                    val inicioMesPasado = hoy.minusMonths(1).withDayOfMonth(1)
                                    periodoInicio = inicioMesPasado.toString()
                                    periodoFin = inicioMesPasado.plusMonths(1).minusDays(1).toString()
                                }, modifier = Modifier.weight(1f)) { Text("Mes anterior") }
                            }
                            Text(
                                "Selecciona el período de nómina que se incluirá en la planilla.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                OutlinedTextField(
                                    value = periodoInicio,
                                    onValueChange = { periodoInicio = it.take(10) },
                                    label = { Text("Desde · AAAA-MM-DD") },
                                    isError = periodoInicio.isNotBlank() && !runCatching {
                                        java.time.LocalDate.parse(periodoInicio)
                                    }.isSuccess,
                                    supportingText = {
                                        if (periodoInicio.isNotBlank() && !runCatching {
                                                java.time.LocalDate.parse(periodoInicio)
                                            }.isSuccess
                                        ) Text("Fecha inválida; use AAAA-MM-DD")
                                    },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                )
                                OutlinedTextField(
                                    value = periodoFin,
                                    onValueChange = { periodoFin = it.take(10) },
                                    label = { Text("Hasta · AAAA-MM-DD") },
                                    isError = periodoFin.isNotBlank() && !runCatching {
                                        java.time.LocalDate.parse(periodoFin)
                                    }.isSuccess,
                                    supportingText = {
                                        if (periodoFin.isNotBlank() && !runCatching {
                                                java.time.LocalDate.parse(periodoFin)
                                            }.isSuccess
                                        ) Text("Fecha inválida; use AAAA-MM-DD")
                                        else if (periodoValido.not() && periodoInicio.isNotBlank() && periodoFin.isNotBlank()) {
                                            Text("La fecha final debe ser igual o posterior a la inicial")
                                        }
                                    },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                )
                            }
                        }
                        Button(
                            modifier = Modifier.fillMaxWidth(),
                            enabled = !estado.cargando && !estado.cargandoEmpleados && (accion.tipo != "planilla_nomina" || periodoValido),
                            onClick = {
                                if (accion.tipo == "planilla_nomina") {
                                    vistaModelo.reporte(accion.tipo, periodoInicio, periodoFin)
                                } else vistaModelo.reporte(accion.tipo)
                            },
                        ) { Text("Generar PDF") }
                    }
                }
            }

            estado.pdf?.let { pdf ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text("PDF listo", style = MaterialTheme.typography.titleMedium)
                        Text(pdf.nombre, style = MaterialTheme.typography.bodyMedium)
                        if (pdf.archivado) {
                            Text("Archivado en el legajo y en cola para sincronizar.", color = MaterialTheme.colorScheme.primary)
                        } else {
                            Text("Generado por el nodo central.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            OutlinedButton(
                                modifier = Modifier.weight(1f),
                                onClick = {
                                    alcance.launch { compartirPdf(contexto, pdf.nombre, pdf.contenido, compartir = false) }
                                },
                            ) { Text("Abrir / imprimir") }
                            if (sesion.puede(Permiso.CREAR) || sesion.puede(Permiso.REPORTAR)) {
                                OutlinedButton(
                                    modifier = Modifier.weight(1f),
                                    onClick = {
                                        alcance.launch { compartirPdf(contexto, pdf.nombre, pdf.contenido, compartir = true) }
                                    },
                                ) { Text("Compartir") }
                            }
                        }
                        TextButton(onClick = vistaModelo::limpiarPdf) { Text("Cerrar") }
                    }
                }
            }
            Spacer(Modifier.height(12.dp))
        }
    }
}

private fun cargarMarkdown(contexto: Context, uri: Uri): String {
    val nombre = contexto.contentResolver.query(
        uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null,
    )?.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null }.orEmpty()    require(nombre.endsWith(".md", ignoreCase = true)) { "Seleccione un archivo con extensión .md." }
    val texto = contexto.contentResolver.openInputStream(uri)?.use { input ->
        val salida = java.io.ByteArrayOutputStream()
        val buffer = ByteArray(4 * 1024)
        var total = 0
        while (true) {
            val leidos = input.read(buffer)
            if (leidos < 0) break
            total += leidos
            require(total <= 65_536) { "La plantilla Markdown supera 64 KB." }
            salida.write(buffer, 0, leidos)
        }
        salida.toByteArray().toString(Charsets.UTF_8)
    } ?: error("No se pudo leer la plantilla Markdown.")
    require(texto.isNotBlank()) { "La plantilla Markdown está vacía." }
    require(texto.toByteArray(Charsets.UTF_8).size <= 65_536) { "La plantilla Markdown supera 64 KB." }
    return texto
}

private fun cargarPdf(contexto: Context, uri: Uri): Pair<String, ByteArray> {
    val nombre = contexto.contentResolver.query(
        uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null,
    )?.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null }
        ?.substringAfterLast('/')?.substringAfterLast('\\')
        ?.takeIf { it.isNotBlank() }
        ?.take(160)
        ?: "documento.pdf"    val max = 8L * 1024 * 1024
    val bytes = contexto.contentResolver.openInputStream(uri)?.use { input ->
        val salida = java.io.ByteArrayOutputStream()
        val buffer = ByteArray(16 * 1024)
        var total = 0L
        while (true) {
            val leidos = input.read(buffer)
            if (leidos < 0) break
            total += leidos
            require(total <= max) { "El PDF supera el límite de 8 MB." }
            salida.write(buffer, 0, leidos)
        }
        salida.toByteArray()
    } ?: error("No se pudo leer el archivo seleccionado.")
    require(nombre.endsWith(".pdf", ignoreCase = true)) { "El archivo debe tener extensión PDF." }
    require(bytes.size >= 5 && bytes.copyOfRange(0, 5).decodeToString().startsWith("%PDF-")) {
        "El contenido seleccionado no parece un PDF válido."
    }
    return nombre to bytes
}

private suspend fun compartirPdf(contexto: Context, nombre: String, bytes: ByteArray, compartir: Boolean) {
    try {
        require(bytes.size >= 5 && bytes.copyOfRange(0, 5).decodeToString().startsWith("%PDF-")) {
            "El archivo no contiene un PDF válido."
        }
        val nombreSeguro = nombre.substringAfterLast('/').substringAfterLast('\\')
            .filter { it.isLetterOrDigit() || it in "._- " }
            .take(120)
            .takeIf { it.endsWith(".pdf", ignoreCase = true) }
            ?: "documento.pdf"
        val archivo = withContext(Dispatchers.IO) {
            File(contexto.cacheDir, "documentos/$nombreSeguro").apply {
                parentFile?.mkdirs()
                writeBytes(bytes)
            }
        }
        val uri = FileProvider.getUriForFile(contexto, "${contexto.packageName}.archivos", archivo)
        val intent = if (compartir) {
            Intent(Intent.ACTION_SEND).apply {
                        type = "application/pdf"
                putExtra(Intent.EXTRA_STREAM, uri)
                clipData = android.content.ClipData.newUri(contexto.contentResolver, nombreSeguro, uri)
            }
        } else Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/pdf")
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        contexto.startActivity(Intent.createChooser(intent, if (compartir) "Compartir PDF" else "Abrir o imprimir PDF"))
    } catch (cancelacion: CancellationException) {
        throw cancelacion
    } catch (error: Exception) {
        android.widget.Toast.makeText(
            contexto,
            error.message ?: "No se pudo preparar el PDF. Compruebe que hay una aplicación compatible instalada.",
            android.widget.Toast.LENGTH_LONG,
        ).show()
    }
}
