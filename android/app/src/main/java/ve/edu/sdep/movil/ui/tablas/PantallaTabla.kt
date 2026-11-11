package ve.edu.sdep.movil.ui.tablas

import androidx.compose.foundation.clickable
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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Inbox
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.MensajeVacio

/**
 * Lista de una tabla administrable que no tiene una pantalla propia en el
 * teléfono (períodos, grados, matrículas).
 *
 * Se refresca al volver del formulario, porque la escritura no pasa por un
 * `Flow` de Room: el motor genérico escribe con los DAO, pero esta lista lee
 * del espejo al entrar y al reanudar la pantalla.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaTabla(
    tabla: String,
    alVolver: () -> Unit,
    alCrear: () -> Unit,
    alEditar: (Long) -> Unit,
    vistaModelo: TablaViewModel = hiltViewModel(),
) {
    val estado by vistaModelo.estado.collectAsStateWithLifecycle()
    var consulta by rememberSaveable(tabla) { mutableStateOf("") }

    LaunchedEffect(tabla) { vistaModelo.cargar(tabla) }

    val ciclo = LocalLifecycleOwner.current
    DisposableEffect(ciclo, tabla) {
        val observador = LifecycleEventObserver { _, evento ->
            if (evento == Lifecycle.Event.ON_RESUME) vistaModelo.cargar(tabla, forzar = true)
        }
        ciclo.lifecycle.addObserver(observador)
        onDispose { ciclo.lifecycle.removeObserver(observador) }
    }

    val filtradas = remember(estado.filas, consulta) {
        vistaModelo.buscar(estado.filas, consulta)
    }

    Scaffold(
        topBar = {
            BarraSuperior(
                titulo = estado.titulo.ifBlank { "Registros" },
                alVolver = alVolver,
            )
        },
        floatingActionButton = {
            if (estado.puedeCrear) {
                ExtendedFloatingActionButton(
                    onClick = alCrear,
                    icon = { Icon(Icons.Filled.Add, contentDescription = null) },
                    text = { Text("Nuevo") },
                )
            }
        },
    ) { relleno ->
        val noDisponible = estado.noDisponible
        when {
            noDisponible != null -> MensajeVacio(
                icono = Icons.Filled.Lock,
                titulo = "Lista no disponible",
                detalle = noDisponible,
                modificador = Modifier.padding(relleno),
            )

            estado.cargando -> Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator()
            }

            else -> Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno),
            ) {
                OutlinedTextField(
                    value = consulta,
                    onValueChange = { consulta = it },
                    label = { Text("Buscar en ${estado.titulo.lowercase()}") },
                    singleLine = true,
                    leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
                    trailingIcon = {
                        if (consulta.isNotEmpty()) {
                            IconButton(onClick = { consulta = "" }) {
                                Icon(Icons.Filled.Close, contentDescription = "Limpiar")
                            }
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                )

                Text(
                    text = if (consulta.isBlank()) {
                        "${estado.filas.size} registro(s)"
                    } else {
                        "${filtradas.size} de ${estado.filas.size} coincidencia(s)"
                    },
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 2.dp),
                )

                if (filtradas.isEmpty()) {
                    MensajeVacio(
                        icono = Icons.Filled.Inbox,
                        titulo = if (consulta.isBlank()) "Sin registros" else "Sin coincidencias",
                        detalle = if (consulta.isBlank()) {
                            "El nodo central todavía no ha replicado registros de esta tabla " +
                                "en este teléfono."
                        } else {
                            "Pruebe con otro texto o limpie la búsqueda."
                        },
                    )
                } else {
                    LazyColumn(
                        modifier = Modifier.weight(1f),
                        contentPadding = PaddingValues(
                            start = 16.dp,
                            end = 16.dp,
                            top = 4.dp,
                            bottom = 96.dp,
                        ),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        items(filtradas, key = { it.id }, contentType = { "fila" }) { fila ->
                            Card(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable { alEditar(fila.id) },
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.surfaceContainerLow,
                                ),
                                elevation = CardDefaults.cardElevation(defaultElevation = 1.dp),
                            ) {
                                Column(
                                    modifier = Modifier.padding(16.dp),
                                    verticalArrangement = Arrangement.spacedBy(5.dp),
                                ) {
                                    Text(
                                        text = fila.titulo,
                                        style = MaterialTheme.typography.titleMedium,
                                        color = MaterialTheme.colorScheme.onSurface,
                                    )
                                    if (fila.subtitulo.isNotBlank()) {
                                        Text(
                                            text = fila.subtitulo,
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = MaterialTheme.colorScheme.primary,
                                        )
                                    }
                                    fila.detalles.forEach { (etiqueta, valor) ->
                                        Row(
                                            modifier = Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                                        ) {
                                            Text(
                                                text = etiqueta,
                                                style = MaterialTheme.typography.labelSmall,
                                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                            )
                                            Text(
                                                text = valor,
                                                style = MaterialTheme.typography.bodySmall,
                                                color = MaterialTheme.colorScheme.onSurface,
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
