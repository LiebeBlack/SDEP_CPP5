package ve.edu.sdep.movil.ui.registros

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.DialogoConfirmar
import ve.edu.sdep.movil.ui.comun.EtiquetaEstado
import ve.edu.sdep.movil.ui.comun.fechaHora

/**
 * Alta y edición de un registro.
 *
 * El mismo formulario sirve para los dos casos; lo que cambia es si trae un
 * identificador. Al guardar, el cambio queda en el teléfono y en la cola de
 * salida: no se espera a la red ni se pierde si el equipo se queda sin señal.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaEditor(
    alVolver: () -> Unit,
    vistaModelo: EditorViewModel = hiltViewModel(),
) {
    val estado by vistaModelo.estado.collectAsStateWithLifecycle()
    val barra = remember { SnackbarHostState() }
    var confirmarBorrado by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        vistaModelo.eventos.collect { evento ->
            when (evento) {
                EventoEditor.Guardado, EventoEditor.Eliminado -> alVolver()
                is EventoEditor.Error -> barra.showSnackbar(evento.mensaje)
            }
        }
    }

    Scaffold(
        topBar = {
            BarraSuperior(
                titulo = if (estado.esNuevo) "Nuevo registro" else "Editar registro",
                alVolver = alVolver,
                acciones = {
                    if (!estado.esNuevo && estado.puedeEliminar) {
                        IconButton(onClick = { confirmarBorrado = true }) {
                            Icon(Icons.Filled.Delete, contentDescription = "Eliminar")
                        }
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(barra) },
    ) { relleno ->
        if (estado.cargando) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center,
            ) {
                CircularProgressIndicator()
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno)
                    .imePadding()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 16.dp, vertical = 12.dp),
            ) {
                val sincronizacion = estado.estadoSync
                if (!estado.esNuevo && sincronizacion != null) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        EtiquetaEstado(estado = sincronizacion)
                        estado.actualizadoEn?.let { momento ->
                            Spacer(Modifier.size(10.dp))
                            Text(
                                text = "Modificado el ${fechaHora(momento)}",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                    Spacer(Modifier.height(12.dp))
                }

                OutlinedTextField(
                    value = estado.titulo,
                    onValueChange = vistaModelo::cambiarTitulo,
                    label = { Text("Título") },
                    supportingText = { Text("${estado.titulo.length}/200") },
                    singleLine = true,
                    enabled = estado.puedeEditar && !estado.guardando,
                    modifier = Modifier.fillMaxWidth(),
                )

                Spacer(Modifier.height(12.dp))

                OutlinedTextField(
                    value = estado.contenido,
                    onValueChange = vistaModelo::cambiarContenido,
                    label = { Text("Contenido o descripción") },
                    minLines = 6,
                    maxLines = 14,
                    enabled = estado.puedeEditar && !estado.guardando,
                    modifier = Modifier.fillMaxWidth(),
                )

                Spacer(Modifier.height(12.dp))

                OutlinedTextField(
                    value = estado.categoria,
                    onValueChange = vistaModelo::cambiarCategoria,
                    label = { Text("Categoría") },
                    supportingText = { Text("Por ejemplo: supervisión, inventario, visita") },
                    singleLine = true,
                    enabled = estado.puedeEditar && !estado.guardando,
                    modifier = Modifier.fillMaxWidth(),
                )

                Spacer(Modifier.height(12.dp))

                OutlinedTextField(
                    value = estado.valor,
                    onValueChange = vistaModelo::cambiarValor,
                    label = { Text("Valor numérico (opcional)") },
                    supportingText = { Text("Importe, cantidad o medición asociada al registro") },
                    singleLine = true,
                    enabled = estado.puedeEditar && !estado.guardando,
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Decimal,
                        imeAction = ImeAction.Done,
                    ),
                    modifier = Modifier.fillMaxWidth(),
                )

                Spacer(Modifier.height(24.dp))

                Button(
                    onClick = vistaModelo::guardar,
                    enabled = estado.puedeEditar && !estado.guardando,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                ) {
                    if (estado.guardando) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.onPrimary,
                        )
                    } else {
                        Text(if (estado.esNuevo) "Guardar registro" else "Guardar cambios")
                    }
                }

                Spacer(Modifier.height(12.dp))

                Text(
                    text = "El registro se guarda primero en este teléfono y viaja al " +
                        "nodo central en la próxima sincronización. Si no hay red, no se pierde.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )

                if (!estado.puedeEditar) {
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "Su rol es de solo consulta: puede ver el registro, no modificarlo.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error,
                    )
                }

                Spacer(Modifier.height(32.dp))
            }
        }
    }

    if (confirmarBorrado) {
        DialogoConfirmar(
            titulo = "Eliminar registro",
            mensaje = "El registro se desactivará aquí y en el nodo central. " +
                "No se borra del historial de operaciones, así que un administrador " +
                "puede auditar cuándo se eliminó.",
            alConfirmar = {
                confirmarBorrado = false
                vistaModelo.eliminar()
            },
            alCancelar = { confirmarBorrado = false },
        )
    }
}
