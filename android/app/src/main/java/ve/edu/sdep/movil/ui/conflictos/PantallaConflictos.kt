package ve.edu.sdep.movil.ui.conflictos

import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.History
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.datos.local.entidad.ConflictoEntity
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.MensajeVacio
import ve.edu.sdep.movil.ui.comun.fechaHora

/**
 * Conflictos detectados al sincronizar.
 *
 * No se resuelven aquí: el nodo central ya eligió un ganador con las marcas de
 * tiempo. Esta pantalla sirve para que el usuario **vea** qué se pisó y pueda
 * corregir el dato a mano si el valor conservado no es el que quería.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaConflictos(
    alVolver: () -> Unit,
    vistaModelo: ConflictosViewModel = hiltViewModel(),
) {
    val conflictos by vistaModelo.conflictos.collectAsStateWithLifecycle()
    val pendientes = conflictos.count { !it.revisado }

    Scaffold(
        topBar = {
            BarraSuperior(
                titulo = "Conflictos",
                alVolver = alVolver,
                acciones = {
                    if (pendientes > 0) {
                        TextButton(onClick = vistaModelo::marcarTodos) { Text("Marcar todos") }
                    }
                },
            )
        },
    ) { relleno ->
        if (conflictos.isEmpty()) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno),
                verticalArrangement = Arrangement.Center,
            ) {
                MensajeVacio(
                    icono = Icons.Filled.History,
                    titulo = "Sin conflictos",
                    detalle = "Cuando dos equipos cambien el mismo campo de un registro, " +
                        "el choque aparecerá aquí con el valor que se conservó.",
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                items(conflictos, key = { it.id }) { conflicto ->
                    TarjetaConflicto(
                        conflicto = conflicto,
                        alRevisar = { vistaModelo.marcarRevisado(conflicto.id) },
                    )
                }
            }
        }
    }
}

@Composable
private fun TarjetaConflicto(conflicto: ConflictoEntity, alRevisar: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = conflicto.titulo,
                    style = MaterialTheme.typography.titleSmall,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f),
                )
                if (conflicto.revisado) {
                    Icon(
                        imageVector = Icons.Filled.Check,
                        contentDescription = "Revisado",
                        tint = MaterialTheme.colorScheme.primary,
                    )
                } else {
                    IconButton(onClick = alRevisar) {
                        Icon(Icons.Filled.Check, contentDescription = "Marcar como revisado")
                    }
                }
            }

            Spacer(Modifier.height(4.dp))
            Text(
                text = "Campo: ${conflicto.campo}",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = "En este equipo: ${conflicto.valorLocal.ifBlank { "(vacío)" }}",
                style = MaterialTheme.typography.bodySmall,
            )
            Text(
                text = "Desde la red: ${conflicto.valorRemoto.ifBlank { "(vacío)" }}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = fechaHora(conflicto.momento),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.outline,
            )
        }
    }
}
