package ve.edu.sdep.movil.ui.formulario

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.datos.local.ColumnaTabla
import ve.edu.sdep.movil.datos.local.TipoCampo
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.DialogoConfirmar
import ve.edu.sdep.movil.ui.comun.MensajeVacio

/**
 * Formulario único para todas las tablas del espejo.
 *
 * Cada control se elige a partir del tipo de la columna que devolvió el
 * esquema de SQLite: texto, número, fecha, sí/no, lista cerrada o selector de
 * registro padre. No hay una pantalla por módulo; el módulo es solo el título.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaFormulario(
    tabla: String,
    id: Long?,
    alVolver: () -> Unit,
    vistaModelo: FormularioViewModel = hiltViewModel(),
) {
    LaunchedEffect(tabla, id) { vistaModelo.cargar(tabla, id) }
    val estado by vistaModelo.estado.collectAsStateWithLifecycle()

    LaunchedEffect(estado.guardado, estado.eliminado) {
        if (estado.guardado || estado.eliminado) alVolver()
    }

    Scaffold(
        topBar = {
            BarraSuperior(
                titulo = if (estado.esAlta) {
                    "Nuevo · ${estado.titulo}"
                } else {
                    "Editar · ${estado.titulo}"
                },
                alVolver = alVolver,
                acciones = {
                    if (estado.puedeEscribir) {
                        TextButton(
                            onClick = { vistaModelo.guardar() },
                            enabled = !estado.guardando && !estado.cargando,
                        ) {
                            Text(if (estado.guardando) "Guardando…" else "Guardar")
                        }
                    }
                    if (estado.puedeEliminar) {
                        IconButton(
                            onClick = { vistaModelo.pedirConfirmacionBorrado() },
                            enabled = !estado.guardando,
                        ) {
                            Icon(Icons.Filled.Delete, contentDescription = "Eliminar")
                        }
                    }
                },
            )
        },
    ) { relleno ->
        val noDisponible = estado.noDisponible
        when {
            estado.cargando -> Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator()
            }

            noDisponible != null -> MensajeVacio(
                icono = Icons.Filled.Lock,
                titulo = "Formulario no disponible",
                detalle = noDisponible,
                modificador = Modifier.padding(relleno),
            )

            else -> LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                item {
                    Text(
                        text = if (estado.puedeEscribir) {
                            "Los cambios se guardan en el teléfono y viajan al nodo central " +
                                "en la próxima sincronización."
                        } else {
                            "Su rol permite consultar estos datos, no modificarlos."
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }

                estado.error?.let { mensaje ->
                    item {
                        Card(modifier = Modifier.fillMaxWidth()) {
                            Text(
                                text = mensaje,
                                color = MaterialTheme.colorScheme.error,
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.padding(14.dp),
                            )
                        }
                    }
                }

                items(estado.campos, key = { it.nombre }) { campo ->
                    CampoEditable(
                        campo = campo,
                        valor = estado.valores[campo.nombre].orEmpty(),
                        opcionesForaneas = estado.opcionesForaneas[campo.tablaForanea].orEmpty(),
                        habilitado = estado.puedeEscribir && !estado.guardando,
                        alCambiar = { valor -> vistaModelo.cambiar(campo.nombre, valor) },
                    )
                }

                item { Spacer(Modifier.height(24.dp)) }
            }
        }
    }

    if (estado.confirmarBorrado) {
        DialogoConfirmar(
            titulo = "Eliminar registro",
            mensaje = "El registro se dará de baja en este teléfono y la baja viajará " +
                "al nodo central. Esta acción no se puede deshacer desde el teléfono.",
            alConfirmar = { vistaModelo.eliminar() },
            alCancelar = { vistaModelo.cancelarBorrado() },
        )
    }
}

@Composable
private fun CampoEditable(
    campo: ColumnaTabla,
    valor: String,
    opcionesForaneas: List<ve.edu.sdep.movil.datos.local.OpcionTabla>,
    habilitado: Boolean,
    alCambiar: (String) -> Unit,
) {
    when (campo.tipo) {
        TipoCampo.BOOLEANO -> Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = campo.etiqueta,
                style = MaterialTheme.typography.bodyLarge,
                modifier = Modifier.weight(1f),
            )
            Switch(
                checked = valor == "1" || valor.equals("true", ignoreCase = true),
                onCheckedChange = { activo -> alCambiar(if (activo) "1" else "0") },
                enabled = habilitado,
            )
        }

        TipoCampo.OPCION -> Selector(
            etiqueta = campo.etiqueta,
            valor = valor,
            opciones = fieldOptions(campo.opciones, campo.requerido),
            habilitado = habilitado,
            alCambiar = alCambiar,
        )

        TipoCampo.FORANEA -> Selector(
            etiqueta = campo.etiqueta,
            valor = valor,
            opciones = opcionesForaneas.map { it.id.toString() to it.etiqueta } +
                if (campo.requerido) {
                    emptyList<Pair<String, String>>()
                } else {
                    listOf("" to "(sin valor)")
                },
            habilitado = habilitado,
            alCambiar = alCambiar,
        )

        else -> OutlinedTextField(
            value = valor,
            onValueChange = alCambiar,
            label = { Text(campo.etiqueta + if (campo.requerido) " *" else "") },
            enabled = habilitado,
            singleLine = campo.tipo != TipoCampo.TEXTO_LARGO,
            minLines = if (campo.tipo == TipoCampo.TEXTO_LARGO) 3 else 1,
            placeholder = if (campo.tipo == TipoCampo.FECHA) {
                { Text("AAAA-MM-DD") }
            } else {
                null
            },
            keyboardOptions = when (campo.tipo) {
                TipoCampo.ENTERO, TipoCampo.DECIMAL ->
                    KeyboardOptions(keyboardType = KeyboardType.Number)

                else -> KeyboardOptions.Default
            },
            modifier = Modifier.fillMaxWidth(),
        )
    }
}

@Composable
private fun Selector(
    etiqueta: String,
    valor: String,
    opciones: List<Pair<String, String>>,
    habilitado: Boolean,
    alCambiar: (String) -> Unit,
) {
    var abierto by remember { mutableStateOf(false) }
    val seleccionada = opciones.firstOrNull { it.first == valor }?.second
        ?: if (valor.isEmpty()) "(sin valor)" else valor

    Column(modifier = Modifier.fillMaxWidth()) {
        Text(text = etiqueta, style = MaterialTheme.typography.labelLarge)
        Spacer(Modifier.height(4.dp))
        Box {
            OutlinedButton(
                onClick = { abierto = true },
                enabled = habilitado,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(
                    text = seleccionada,
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.bodyLarge,
                )
                Icon(Icons.Filled.ArrowDropDown, contentDescription = null)
            }
            DropdownMenu(expanded = abierto, onDismissRequest = { abierto = false }) {
                opciones.forEach { (valorOpcion, textoOpcion) ->
                    DropdownMenuItem(
                        text = { Text(textoOpcion) },
                        onClick = {
                            abierto = false
                            alCambiar(valorOpcion)
                        },
                    )
                }
            }
        }
    }
}

/** Añade la opción vacía a las listas cerradas que no son obligatorias */
private fun fieldOptions(opciones: List<String>, requerido: Boolean): List<Pair<String, String>> {
    val base = opciones.map { it to it }
    return if (requerido) base else listOf("" to "(sin valor)") + base
}
