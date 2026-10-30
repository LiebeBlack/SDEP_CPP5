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
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AssistChip
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
    var editor by remember {
        mutableStateOf(androidx.compose.ui.text.input.TextFieldValue(estado.markdown))
    }
    // El título sale del propio documento: al elegir una plantilla es su nombre y
    // al escribir una propia es su primer encabezado. Ya no hay que teclearlo.
    val tituloDocumento = remember(estado.markdown, estado.plantillaIndice) {
        PLANTILLAS_CONSTANCIA.getOrNull(estado.plantillaIndice)?.first
            ?: tituloDesdeMarkdown(estado.markdown)
            ?: "Constancia personalizada"
    }
    val camposUsados = remember(estado.markdown) { clavesUsadas(estado.markdown) }
    // Los chips se ordenan solos: primero los campos que la plantilla ya usa y
    // después los que tienen dato en la ficha, para no recorrer 30 etiquetas a
    // ciegas. El resto conserva el orden del catálogo.
    val camposOrdenados = remember(estado.campos, camposUsados) {
        val usados = camposUsados.toSet()
        val posicion = estado.campos.withIndex().associate { (indice, campo) -> campo.clave to indice }
        estado.campos.sortedWith(
            compareByDescending<CampoConstancia> { it.clave in usados }
                .thenByDescending { !it.valor.isNullOrBlank() }
                .thenBy { posicion[it.clave] ?: Int.MAX_VALUE },
        )
    }
    val camposInvalidos = remember(estado.markdown) { clavesInvalidas(estado.markdown) }
    val markdownCorregido = remember(estado.markdown) { corregirCampos(estado.markdown) }
    LaunchedEffect(estado.markdown) {
        if (editor.text != estado.markdown) {
            editor = androidx.compose.ui.text.input.TextFieldValue(
                estado.markdown,
                selection = androidx.compose.ui.text.TextRange(estado.markdown.length),
            )
        }
    }

    /**
     * Inserta texto en el cursor. Con `bloque` se separa del párrafo anterior
     * para que las frases preestablecidas no queden pegadas a otra línea.
     */
    fun insertarTexto(texto: String, bloque: Boolean = false) {
        val seleccion = editor.selection
        val inicio = seleccion.min.coerceIn(0, editor.text.length)
        val fin = seleccion.max.coerceIn(inicio, editor.text.length)
        val antes = editor.text.take(inicio)
        val separador = if (bloque && antes.isNotBlank() && !antes.endsWith("\n")) "\n\n" else ""
        val token = separador + texto
        val nuevo = editor.text.replaceRange(inicio, fin, token)
        if (nuevo.toByteArray(Charsets.UTF_8).size > 65_536) {
            vistaModelo.errorSeleccionArchivo("La plantilla supera 64 KB.")
            return
        }
        editor = androidx.compose.ui.text.input.TextFieldValue(
            nuevo,
            selection = androidx.compose.ui.text.TextRange(inicio + token.length),
        )
        vistaModelo.cambiarMarkdown(nuevo)
    }

    fun insertarCampo(clave: String) = insertarTexto("{{$clave}}")
    val fechaInicioValida = remember(periodoInicio) { fechaIsoValida(periodoInicio) }
    val fechaFinValida = remember(periodoFin) { fechaIsoValida(periodoFin) }
    val periodoValido = remember(periodoInicio, periodoFin, fechaInicioValida, fechaFinValida) {
        fechaInicioValida && fechaFinValida &&
            !java.time.LocalDate.parse(periodoFin).isBefore(java.time.LocalDate.parse(periodoInicio))
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
        } else {
            vistaModelo.errorSeleccionArchivo("No se seleccionó una plantilla Markdown.")
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
        } else {
            vistaModelo.errorSeleccionArchivo("No se seleccionó ningún PDF.")
        }
    }
    LaunchedEffect(sesion.usuario, sesion.rol, sesion.cedula) {
        vistaModelo.actualizarSesion(sesion.usuario, sesion.rol.valor, sesion.cedula, sesion.esTrabajador)
        if (!sesion.puede(Permiso.CREAR)) {
            vistaModelo.limpiarPdf()
            tituloSubida = ""
        }
    }
    LaunchedEffect(estado.mensaje) {
        estado.mensaje?.let { snackbar.showSnackbar(it) }
    }
    LaunchedEffect(sesion.usuario, sesion.rol) {
        seccionActiva = when {
            puedeUsarPlantilla -> "constancia"
            puedeAdjuntar || puedeVerFicha || sesion.esTrabajador -> "legajo"
            accionesPdf.any { sesion.puedeAbrir(it.modulo) && sesion.puede(Permiso.REPORTAR) } -> "reportes"
            else -> ""
        }
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
            if (sesion.offline) {
                Text(
                    "Modo sin conexión: las constancias se generan igual en el teléfono; el folio del nodo y la carga al legajo esperan conexión.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.tertiary,
                )
            }
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
                        Button(onClick = { seccionActiva = clave }, modifier = Modifier.width(112.dp)) {
                            Text(titulo, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    } else {
                        OutlinedButton(onClick = { seccionActiva = clave }, modifier = Modifier.width(112.dp)) {
                            Text(titulo, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
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
                    Text(tituloDocumento, style = MaterialTheme.typography.titleLarge)
                    Text(
                        "Revisa y personaliza la plantilla; los datos de identidad y empleo se completan desde la ficha oficial.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    ExposedDropdownMenuBox(expanded = plantillaExpandida, onExpandedChange = { plantillaExpandida = it }) {
                        OutlinedTextField(
                            value = PLANTILLAS_CONSTANCIA.getOrNull(estado.plantillaIndice)?.first
                                ?: "Plantilla personalizada",
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Plantilla preconfigurada") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(plantillaExpandida) },
                            modifier = Modifier.fillMaxWidth().menuAnchor(),
                        )
                        ExposedDropdownMenu(expanded = plantillaExpandida, onDismissRequest = { plantillaExpandida = false }) {
                            PLANTILLAS_CONSTANCIA.forEachIndexed { indice, item ->
                                DropdownMenuItem(text = { Text(item.first) }, onClick = {
                                    vistaModelo.seleccionarPlantilla(indice)
                                    plantillaExpandida = false
                                })
                            }
                            DropdownMenuItem(
                                text = { Text("Plantilla personalizada actual") },
                                onClick = {
                                    vistaModelo.seleccionarPlantilla(-1)
                                    plantillaExpandida = false
                                },
                            )
                        }
                    }
                    OutlinedButton(
                        enabled = !estado.cargando && !estado.cargandoEmpleados,
                        onClick = {
                            vistaModelo.seleccionarPlantilla(-1)
                            selectorMarkdown.launch(arrayOf("text/markdown", "text/plain", "application/octet-stream"))
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text("Importar plantilla Markdown (.md)") }
                    if (estado.campos.isNotEmpty()) {
                        Text("Insertar campo", style = MaterialTheme.typography.titleSmall)
                        Row(
                            modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            camposOrdenados.forEach { campo ->
                                AssistChip(
                                    onClick = { insertarCampo(campo.clave) },
                                    label = { Text(campo.etiqueta) },
                                )
                            }
                        }
                    }
                    Text("Texto predefinido", style = MaterialTheme.typography.titleSmall)
                    Row(
                        modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        FRAGMENTOS_CONSTANCIA.forEach { (etiqueta, fragmento) ->
                            AssistChip(
                                onClick = { insertarTexto(fragmento, bloque = true) },
                                label = { Text(etiqueta) },
                            )
                        }
                    }
                    OutlinedTextField(
                        value = editor,
                        onValueChange = { nuevo ->
                            if (nuevo.text.toByteArray(Charsets.UTF_8).size <= 65_536) {
                                editor = nuevo
                                vistaModelo.cambiarMarkdown(nuevo.text)
                            }
                        },
                        label = { Text("Plantilla Markdown") },
                        supportingText = { Text("Toque un campo para insertarlo donde está el cursor · máximo 64 KB") },
                        minLines = 5,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    val usados = estado.campos.filter { it.clave in camposUsados }
                    if (usados.isNotEmpty()) {
                        Text("Datos que se completarán", style = MaterialTheme.typography.titleSmall)
                        usados.forEach { campo ->
                            Text(
                                "${campo.etiqueta}: ${campo.valor ?: "sin dato en la ficha"}",
                                style = MaterialTheme.typography.bodySmall,
                                color =
                                    if (campo.valor == null) MaterialTheme.colorScheme.error
                                    else MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    } else if (estado.campos.isNotEmpty()) {
                        Text(
                            "La plantilla no usa campos: fuera de las etiquetas que inserte, el texto queda tal cual.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.tertiary,
                        )
                    }
                    val faltantes = usados.filter { it.valor == null }
                    if (faltantes.isNotEmpty()) {
                        Text(
                            "Complete en la ficha antes de emitir: " +
                                faltantes.joinToString(", ") { it.etiqueta.lowercase() },
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.error,
                        )
                    }
                    if (camposInvalidos.isNotEmpty()) {
                        Text(
                            "Campos no reconocidos: " + camposInvalidos.joinToString(", ") { "{{$it}}" },
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.error,
                        )
                        if (markdownCorregido != estado.markdown) {
                            TextButton(
                                onClick = { vistaModelo.cambiarMarkdown(markdownCorregido) },
                            ) { Text("Corregir nombres de campos") }
                        }
                    }
                    Text(
                        "El documento incluirá el nombre institucional, datos laborales, fecha de emisión, firma y espacio para el sello. En el teléfono se compone al instante y sin conexión; el nodo añade el folio y lo archiva.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            modifier = Modifier.fillMaxWidth(),
                            enabled =
                                !estado.cargando &&
                                    estado.empleadoId != null &&
                                    estado.markdown.isNotBlank(),
                            onClick = {
                                vistaModelo.constanciaLocal(personalizada = true, titulo = tituloDocumento)
                            },
                        ) { Text("Generar en el teléfono · al instante") }
                        OutlinedButton(
                            modifier = Modifier.fillMaxWidth(),
                            enabled =
                                !estado.cargando &&
                                    estado.empleadoId != null &&
                                    estado.markdown.isNotBlank(),
                            onClick = {
                                vistaModelo.constancia(personalizada = true, titulo = tituloDocumento)
                            },
                        ) { Text("Emitir en el nodo y archivar en el legajo") }
                        TextButton(
                            modifier = Modifier.fillMaxWidth(),
                            enabled = !estado.cargando && estado.empleadoId != null,
                            onClick = { vistaModelo.constanciaLocal(personalizada = false, titulo = "Constancia de trabajo") },
                        ) { Text("Formato institucional básico") }
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
                        enabled =
                            !estado.cargando &&
                                !estado.cargandoEmpleados &&
                                estado.empleadoId != null &&
                                tituloSubida.isNotBlank(),
                        onClick = { selectorPdf.launch(arrayOf("application/pdf")) },
                    ) { Text("Seleccionar y adjuntar PDF · máximo 8 MB") }
                    if (puedeVerFicha) OutlinedButton(
                        modifier = Modifier.fillMaxWidth(),
                        enabled =
                            !estado.cargando &&
                                !estado.cargandoEmpleados &&
                                estado.empleadoId != null,
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
                                OutlinedButton(
                                    onClick = {
                                        val hoy = java.time.LocalDate.now()
                                        periodoInicio = hoy.withDayOfMonth(1).toString()
                                        periodoFin = hoy.toString()
                                    },
                                    modifier = Modifier.weight(1f),
                                ) { Text("Mes actual") }
                                OutlinedButton(
                                    onClick = {
                                        val hoy = java.time.LocalDate.now()
                                        val inicioMesPasado = hoy.minusMonths(1).withDayOfMonth(1)
                                        periodoInicio = inicioMesPasado.toString()
                                        periodoFin = inicioMesPasado.plusMonths(1).minusDays(1).toString()
                                    },
                                    modifier = Modifier.weight(1f),
                                ) { Text("Mes anterior") }
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
                                    isError = periodoInicio.isNotBlank() && !fechaInicioValida,
                                    supportingText = {
                                        if (periodoInicio.isNotBlank() && !fechaInicioValida) {
                                            Text("Fecha inválida; use AAAA-MM-DD")
                                        }
                                    },
                                    modifier = Modifier.fillMaxWidth(),
                                    singleLine = true,
                                )
                                OutlinedTextField(
                                    value = periodoFin,
                                    onValueChange = { periodoFin = it.take(10) },
                                    label = { Text("Hasta · AAAA-MM-DD") },
                                    isError = periodoFin.isNotBlank() && !fechaFinValida ||
                                        fechaInicioValida && fechaFinValida && !periodoValido,
                                    supportingText = {
                                        if (periodoFin.isNotBlank() && !fechaFinValida) {
                                            Text("Fecha inválida; use AAAA-MM-DD")
                                        } else if (fechaInicioValida && fechaFinValida && !periodoValido) {
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
                            enabled =
                                !estado.cargando &&
                                    !estado.cargandoEmpleados &&
                                    (accion.tipo != "planilla_nomina" || periodoValido),
                            onClick = {
                                if (accion.tipo == "planilla_nomina") {
                                    if (periodoValido) vistaModelo.reporte(accion.tipo, periodoInicio, periodoFin)
                                    else vistaModelo.errorSeleccionArchivo("La fecha final debe ser igual o posterior a la inicial.")
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
                        when {
                            pdf.archivado -> Text(
                                "Archivado en el legajo y en cola para sincronizar.",
                                color = MaterialTheme.colorScheme.primary,
                            )

                            pdf.local -> Text(
                                "Compuesto en este teléfono · sin conexión.",
                                color = MaterialTheme.colorScheme.primary,
                            )

                            else -> Text(
                                "Generado por el nodo central.",
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
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

private fun fechaIsoValida(texto: String): Boolean = runCatching {
    java.time.LocalDate.parse(texto).toString() == texto
}.getOrDefault(false)

private fun cargarMarkdown(contexto: Context, uri: Uri): String {
    val nombre = contexto.contentResolver.query(
        uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null,
    )?.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null }.orEmpty()
    require(nombre.endsWith(".md", ignoreCase = true)) { "Seleccione un archivo con extensión .md." }
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
    val max = 8L * 1024 * 1024
    val nombre = contexto.contentResolver.query(
        uri, arrayOf(android.provider.OpenableColumns.DISPLAY_NAME), null, null, null,
    )?.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null }
        ?.substringAfterLast('/')?.substringAfterLast('\\')
        ?.takeIf { it.isNotBlank() }
        ?.take(160)
        ?: "documento.pdf"
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

/**
 * Retira las copias de PDF que ya nadie va a abrir.
 *
 * Cada documento compartido deja su archivo en la caché para que la
 * aplicación receptora pueda leerlo. Sin límite, en un teléfono de gama baja
 * con poco almacenamiento se acumulan megas que el sistema termina reclamando
 * en el peor momento. La ventana de dos días cubre de sobra el uso real.
 */
private fun limpiarCachePdf(carpeta: File) {
    val limite = System.currentTimeMillis() - 2L * 24 * 60 * 60 * 1000
    runCatching {
        carpeta.listFiles()?.forEach { archivo ->
            if (archivo.isFile && archivo.lastModified() < limite) archivo.delete()
        }
    }
}

private suspend fun compartirPdf(contexto: Context, nombre: String, bytes: ByteArray, compartir: Boolean) {
    try {
        require(bytes.size >= 5 && bytes.copyOfRange(0, 5).decodeToString().startsWith("%PDF-")) {
            "El archivo no contiene un PDF válido."
        }
        val nombreBase = nombre.substringAfterLast('/').substringAfterLast('\\')
        val nombreSeguro = if (nombreBase.endsWith(".pdf", ignoreCase = true)) {
            val base = nombreBase.substringBeforeLast('.')
                .filter { it.isLetterOrDigit() || it in "._- " }
                .take(100)
                .trim()
                .ifBlank { "documento" }
            "$base.pdf"
        } else "documento.pdf"
        val archivo = withContext(Dispatchers.IO) {
            val carpeta = File(contexto.cacheDir, "documentos").apply { mkdirs() }
            limpiarCachePdf(carpeta)
            File(carpeta, nombreSeguro).apply { writeBytes(bytes) }
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
