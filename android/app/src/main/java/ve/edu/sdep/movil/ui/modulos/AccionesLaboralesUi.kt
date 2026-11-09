package ve.edu.sdep.movil.ui.modulos

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import ve.edu.sdep.movil.datos.local.entidad.ContratoEntity
import ve.edu.sdep.movil.datos.local.entidad.IncidenciaEntity
import ve.edu.sdep.movil.dominio.modelo.Modulo
import java.time.LocalDate
import java.util.Locale

/**
 * Acciones de negocio de una ficha de incidencia o contrato.
 *
 * Solo se dibujan para los roles que el nodo autoriza (administrador y gestor)
 * y cuando hay vinculación con el escritorio. El servidor vuelve a comprobar
 * permisos y estado aunque la pantalla se equivoque.
 */
@Composable
fun TarjetaAccionesLaborales(
    modulo: Modulo?,
    incidencia: IncidenciaEntity?,
    contrato: ContratoEntity?,
    conectado: Boolean,
    puedeGestionar: Boolean,
    ejecutando: Boolean,
    alAprobar: (String?, Int?) -> Unit,
    alRechazar: (String?) -> Unit,
    alRenovar: (String, Double?, String?, String?) -> Unit,
    alTerminar: (String, String?, Boolean, String?) -> Unit,
) {
    val mostrarIncidente = modulo == Modulo.INCIDENCIAS &&
        incidencia?.estado == ESTADO_PENDIENTE
    val mostrarContrato = modulo == Modulo.CONTRATOS &&
        contrato != null && contrato.estado != ESTADO_TERMINADO
    if (modulo == null || !puedeGestionar || (!mostrarIncidente && !mostrarContrato)) return

    var dialogo by remember { mutableStateOf<Dialogo?>(null) }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer,
        ),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = "Acciones",
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSecondaryContainer,
            )
            Text(
                text = if (conectado) {
                    "La operación se ejecuta en el nodo central y actualiza esta ficha."
                } else {
                    "Conecte el teléfono con el sistema de escritorio para ejecutar esta acción."
                },
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSecondaryContainer,
            )
            if (conectado) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (mostrarIncidente) {
                        Button(
                            onClick = { dialogo = Dialogo.Aprobar },
                            enabled = !ejecutando,
                        ) { Text("Aprobar") }
                        OutlinedButton(
                            onClick = { dialogo = Dialogo.Rechazar },
                            enabled = !ejecutando,
                        ) { Text("Rechazar") }
                    }
                    if (mostrarContrato) {
                        if (contrato?.estado == ESTADO_VIGENTE) {
                            Button(
                                onClick = { dialogo = Dialogo.Renovar },
                                enabled = !ejecutando,
                            ) { Text("Renovar") }
                        }
                        OutlinedButton(
                            onClick = { dialogo = Dialogo.Terminar },
                            enabled = !ejecutando,
                        ) { Text("Terminar") }
                    }
                }
            }
        }
    }

    when (val accion = dialogo) {
        Dialogo.Aprobar -> incidencia?.let { actual ->
            DialogoAprobarIncidencia(
                incidencia = actual,
                alCerrar = { dialogo = null },
                alConfirmar = { comentarios, dias ->
                    dialogo = null
                    alAprobar(comentarios, dias)
                },
            )
        }

        Dialogo.Rechazar -> DialogoRechazarIncidencia(
            alCerrar = { dialogo = null },
            alConfirmar = { comentarios ->
                dialogo = null
                alRechazar(comentarios)
            },
        )

        Dialogo.Renovar -> contrato?.let { actual ->
            DialogoRenovarContrato(
                contrato = actual,
                alCerrar = { dialogo = null },
                alConfirmar = { fecha, salario, tipo, clausulas ->
                    dialogo = null
                    alRenovar(fecha, salario, tipo, clausulas)
                },
            )
        }

        Dialogo.Terminar -> contrato?.let { actual ->
            DialogoTerminarContrato(
                contrato = actual,
                alCerrar = { dialogo = null },
                alConfirmar = { motivo, fecha, liquidacion, metodo ->
                    dialogo = null
                    alTerminar(motivo, fecha, liquidacion, metodo)
                },
            )
        }

        null -> Unit
    }
}

@Composable
private fun DialogoAprobarIncidencia(
    incidencia: IncidenciaEntity,
    alCerrar: () -> Unit,
    alConfirmar: (String?, Int?) -> Unit,
) {
    var comentarios by remember { mutableStateOf("") }
    var dias by remember { mutableStateOf(incidencia.diasSolicitados.toString()) }
    var error by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = alCerrar,
        title = { Text("Aprobar incidencia") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "Días solicitados: ${incidencia.diasSolicitados}. " +
                        "Puede aprobar menos días si corresponde.",
                    style = MaterialTheme.typography.bodySmall,
                )
                OutlinedTextField(
                    value = dias,
                    onValueChange = { dias = it.filter(Char::isDigit) },
                    label = { Text("Días aprobados") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = comentarios,
                    onValueChange = { comentarios = it },
                    label = { Text("Comentarios (opcional)") },
                    minLines = 2,
                    modifier = Modifier.fillMaxWidth(),
                )
                error?.let {
                    Text(it, color = MaterialTheme.colorScheme.error)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                val numero = dias.toIntOrNull()
                if (numero == null || numero < 1 || numero > incidencia.diasSolicitados) {
                    error = "Indique un número de días entre 1 y ${incidencia.diasSolicitados}."
                } else {
                    alConfirmar(comentarios.trim().takeIf { it.isNotEmpty() }, numero)
                }
            }) { Text("Aprobar") }
        },
        dismissButton = { TextButton(onClick = alCerrar) { Text("Cancelar") } },
    )
}

@Composable
private fun DialogoRechazarIncidencia(
    alCerrar: () -> Unit,
    alConfirmar: (String?) -> Unit,
) {
    var comentarios by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = alCerrar,
        title = { Text("Rechazar incidencia") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    "La incidencia quedará rechazada y no se podrá aprobar después.",
                    style = MaterialTheme.typography.bodySmall,
                )
                OutlinedTextField(
                    value = comentarios,
                    onValueChange = { comentarios = it },
                    label = { Text("Motivo o comentarios (opcional)") },
                    minLines = 2,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = {
            TextButton(onClick = {
                alConfirmar(comentarios.trim().takeIf { it.isNotEmpty() })
            }) { Text("Rechazar") }
        },
        dismissButton = { TextButton(onClick = alCerrar) { Text("Cancelar") } },
    )
}

@Composable
private fun DialogoRenovarContrato(
    contrato: ContratoEntity,
    alCerrar: () -> Unit,
    alConfirmar: (String, Double?, String?, String?) -> Unit,
) {
    val finAnterior = runCatching { LocalDate.parse(contrato.fechaFin.orEmpty()) }.getOrNull()
    var fecha by remember {
        mutableStateOf(finAnterior?.plusDays(1)?.toString().orEmpty())
    }
    var salario by remember {
        mutableStateOf(String.format(Locale.US, "%.2f", contrato.salarioPactado))
    }
    var tipo by remember { mutableStateOf(contrato.tipo) }
    var clausulas by remember { mutableStateOf(contrato.clausulas.orEmpty()) }
    var error by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = alCerrar,
        title = { Text("Renovar contrato") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "Contrato ${contrato.numero}. Actualmente vence el " +
                        (contrato.fechaFin ?: "sin fecha") + ".",
                    style = MaterialTheme.typography.bodySmall,
                )
                OutlinedTextField(
                    value = fecha,
                    onValueChange = { fecha = it },
                    label = { Text("Nueva fecha de fin (AAAA-MM-DD)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = salario,
                    onValueChange = { salario = it },
                    label = { Text("Nuevo salario (opcional)") },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = tipo,
                    onValueChange = { tipo = it },
                    label = { Text("Tipo de contrato (opcional)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = clausulas,
                    onValueChange = { clausulas = it },
                    label = { Text("Cláusulas (opcional)") },
                    minLines = 2,
                    modifier = Modifier.fillMaxWidth(),
                )
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                val nuevaFecha = runCatching { LocalDate.parse(fecha.trim()) }.getOrNull()
                if (nuevaFecha == null) {
                    error = "Use una fecha válida con formato AAAA-MM-DD."
                } else if (finAnterior != null && !nuevaFecha.isAfter(finAnterior)) {
                    error = "La nueva fecha debe ser posterior al vencimiento actual."
                } else {
                    val salarioTexto = salario.trim().replace(',', '.')
                    val monto = salarioTexto.takeIf { it.isNotEmpty() }?.toDoubleOrNull()
                    if (salarioTexto.isNotEmpty() && (monto == null || !monto.isFinite() || monto <= 0.0)) {
                        error = "El salario debe ser un número mayor que cero."
                    } else {
                        alConfirmar(
                            nuevaFecha.toString(),
                            monto,
                            tipo.trim().takeIf { it.isNotEmpty() },
                            clausulas.trim().takeIf { it.isNotEmpty() },
                        )
                    }
                }
            }) { Text("Renovar") }
        },
        dismissButton = { TextButton(onClick = alCerrar) { Text("Cancelar") } },
    )
}

@Composable
private fun DialogoTerminarContrato(
    contrato: ContratoEntity,
    alCerrar: () -> Unit,
    alConfirmar: (String, String?, Boolean, String?) -> Unit,
) {
    var motivo by remember { mutableStateOf("") }
    var fecha by remember { mutableStateOf(fechaTerminoInicial(contrato)) }
    var liquidacion by remember { mutableStateOf(true) }
    var metodo by remember { mutableStateOf("transferencia") }
    var error by remember { mutableStateOf<String?>(null) }

    AlertDialog(
        onDismissRequest = alCerrar,
        title = { Text("Terminar contrato") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    "El contrato ${contrato.numero} quedará terminado. " +
                        "La liquidación la calcula el nodo central.",
                    style = MaterialTheme.typography.bodySmall,
                )
                OutlinedTextField(
                    value = motivo,
                    onValueChange = { motivo = it },
                    label = { Text("Motivo de terminación") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = fecha,
                    onValueChange = { fecha = it },
                    label = { Text("Fecha de terminación (AAAA-MM-DD)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                OutlinedTextField(
                    value = metodo,
                    onValueChange = { metodo = it },
                    label = { Text("Método de pago de la liquidación") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Text(
                        "Registrar el pago de la liquidación",
                        modifier = Modifier.weight(1f),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    Switch(checked = liquidacion, onCheckedChange = { liquidacion = it })
                }
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                if (motivo.trim().isEmpty()) {
                    error = "El motivo de terminación es obligatorio."
                } else if (runCatching { LocalDate.parse(fecha.trim()) }.isFailure) {
                    error = "Use una fecha válida con formato AAAA-MM-DD."
                } else {
                    alConfirmar(
                        motivo.trim(),
                        fecha.trim().takeIf { it.isNotEmpty() },
                        liquidacion,
                        metodo.trim().takeIf { it.isNotEmpty() },
                    )
                }
            }) { Text("Terminar") }
        },
        dismissButton = { TextButton(onClick = alCerrar) { Text("Cancelar") } },
    )
}

private fun fechaTerminoInicial(contrato: ContratoEntity): String {
    val hoy = LocalDate.now()
    val inicio = runCatching { LocalDate.parse(contrato.fechaInicio) }.getOrNull()
    val fin = runCatching { LocalDate.parse(contrato.fechaFin.orEmpty()) }.getOrNull()
    return when {
        inicio != null && hoy.isBefore(inicio) -> inicio.toString()
        fin != null && hoy.isAfter(fin) -> fin.toString()
        else -> hoy.toString()
    }
}

private sealed interface Dialogo {
    data object Aprobar : Dialogo
    data object Rechazar : Dialogo
    data object Renovar : Dialogo
    data object Terminar : Dialogo
}

private const val ESTADO_PENDIENTE = "pendiente"
private const val ESTADO_VIGENTE = "vigente"
private const val ESTADO_TERMINADO = "terminado"
