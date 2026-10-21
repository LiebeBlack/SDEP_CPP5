package ve.edu.sdep.movil.ui.registros

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Registro
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.EtiquetaEstado
import ve.edu.sdep.movil.ui.comun.MensajeVacio
import ve.edu.sdep.movil.ui.comun.fechaHora
import ve.edu.sdep.movil.ui.comun.horaCorta

/**
 * Pantalla principal: lo que este puesto ha levantado, con su estado de envío.
 *
 * La lista se actualiza sola (Room expone un ``Flow``): al guardar un registro
 * y volver, aparece sin recargar. El filtro y la búsqueda se aplican en memoria
 * porque un puñado de registros de campo cabe de sobra en un teléfono.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaRegistros(
    sesion: Sesion,
    alNuevo: () -> Unit,
    alEditar: (String) -> Unit,
    alAjustes: () -> Unit,
    vistaModelo: RegistrosViewModel = hiltViewModel(),
) {
    val estado by vistaModelo.estado.collectAsStateWithLifecycle()
    val contadores by vistaModelo.contadores.collectAsStateWithLifecycle()
    val sincronizando by vistaModelo.sincronizando.collectAsStateWithLifecycle()
    val mensaje by vistaModelo.mensaje.collectAsStateWithLifecycle()
    val barra = remember { SnackbarHostState() }

    LaunchedEffect(mensaje) {
        val texto = mensaje ?: return@LaunchedEffect
        barra.showSnackbar(texto)
        vistaModelo.limpiarMensaje()
    }

    Scaffold(
        topBar = {
            BarraSuperior(
                titulo = "Registros",
                acciones = {
                    IconButton(onClick = alAjustes) {
                        Icon(Icons.Filled.Settings, contentDescription = "Ajustes")
                    }
                },
            )
        },
        floatingActionButton = {
            if (sesion.puede(Permiso.CREAR)) {
                ExtendedFloatingActionButton(
                    onClick = alNuevo,
                    icon = { Icon(Icons.Filled.Add, contentDescription = null) },
                    text = { Text("Nuevo") },
                )
            }
        },
        snackbarHost = { SnackbarHost(barra) },
    ) { relleno ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(relleno),
        ) {
            FilaSincronizacion(
                contadores = contadores,
                sincronizando = sincronizando,
                alSincronizar = vistaModelo::sincronizarAhora,
            )

            OutlinedTextField(
                value = estado.filtro,
                onValueChange = vistaModelo::buscar,
                label = { Text("Buscar por título o contenido") },
                singleLine = true,
                leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
                trailingIcon = {
                    if (estado.filtro.isNotEmpty()) {
                        IconButton(onClick = { vistaModelo.buscar("") }) {
                            Icon(Icons.Filled.Close, contentDescription = "Limpiar búsqueda")
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
            )

            if (estado.categorias.isNotEmpty()) {
                LazyRow(
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 16.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    item {
                        FilterChip(
                            selected = estado.categoriaSeleccionada.isEmpty(),
                            onClick = { vistaModelo.filtrarCategoria("") },
                            label = { Text("Todas") },
                        )
                    }
                    items(estado.categorias) { categoria ->
                        FilterChip(
                            selected = estado.categoriaSeleccionada == categoria,
                            onClick = { vistaModelo.filtrarCategoria(categoria) },
                            label = { Text(categoria) },
                        )
                    }
                }
            }

            if (estado.cargando) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 48.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    CircularProgressIndicator()
                }
            } else if (estado.registros.isEmpty()) {
                MensajeVacio(
                    icono = Icons.Filled.Description,
                    titulo = if (estado.filtro.isBlank() && estado.categoriaSeleccionada.isBlank()) {
                        "Todavía no hay registros"
                    } else {
                        "Sin coincidencias"
                    },
                    detalle = if (estado.filtro.isBlank() && estado.categoriaSeleccionada.isBlank()) {
                        if (sesion.puede(Permiso.CREAR)) {
                            "Use el botón «Nuevo» para levantar el primer registro de campo."
                        } else {
                            "Los registros sincronizados desde la intranet aparecerán aquí."
                        }
                    } else {
                        "Pruebe con otro texto o quite el filtro de categoría."
                    },
                )
            } else {
                LazyColumn(
                    contentPadding = androidx.compose.foundation.layout.PaddingValues(
                        start = 16.dp,
                        end = 16.dp,
                        top = 8.dp,
                        bottom = 96.dp,
                    ),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    items(estado.registros, key = { it.uuid }) { registro ->
                        TarjetaRegistro(registro = registro, alEditar = alEditar)
                    }
                }
            }
        }
    }
}

@Composable
private fun FilaSincronizacion(
    contadores: Contadores,
    sincronizando: Boolean,
    alSincronizar: () -> Unit,
) {
    val pendientes = contadores.pendientes
    Surface(color = MaterialTheme.colorScheme.surfaceVariant) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                imageVector = Icons.Filled.Sync,
                contentDescription = null,
                modifier = Modifier.size(18.dp),
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.width(8.dp))
            Column(modifier = Modifier.weight(1f)) {
                val cuando = contadores.ultimaSync?.let { "Última sincronización: ${horaCorta(it)}" }
                    ?: "Sin sincronizar"
                val cuantos = when (pendientes) {
                    0 -> "sin pendientes"
                    1 -> "1 cambio pendiente"
                    else -> "$pendientes cambios pendientes"
                }
                Text(
                    text = "$cuando · $cuantos",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                val error = contadores.ultimoError
                if (!error.isNullOrBlank()) {
                    Text(
                        text = error,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.error,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }
            if (sincronizando) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
            } else {
                TextButton(onClick = alSincronizar) { Text("Sincronizar") }
            }
        }
    }
}

@Composable
private fun TarjetaRegistro(registro: Registro, alEditar: (String) -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { alEditar(registro.uuid) },
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = registro.titulo,
                    style = MaterialTheme.typography.titleSmall,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.weight(1f),
                )
                EtiquetaEstado(estado = registro.estado)
            }

            Spacer(Modifier.height(4.dp))

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = registro.categoria,
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
                if (registro.valor != null) {
                    Spacer(Modifier.width(10.dp))
                    Text(
                        text = "Valor: ${registro.valorTexto}",
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            if (registro.contenido.isNotBlank()) {
                Spacer(Modifier.height(6.dp))
                Text(
                    text = registro.contenido,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }

            Spacer(Modifier.height(8.dp))
            Text(
                text = fechaHora(registro.actualizadoEn),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.outline,
            )
        }
    }
}
