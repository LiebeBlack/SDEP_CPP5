package ve.edu.sdep.movil.ui.modulos

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Inbox
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.MensajeVacio

/**
 * Lista de un módulo con búsqueda.
 *
 * El panel de control y la configuración institucional, que son pantallas del
 * escritorio, se rechazan aquí aunque se llegue por una ruta interna.
 *
 * El acceso se vuelve a comprobar aquí, no solo en el índice: una ruta se
 * puede abrir por enlace interno, y la misma matriz de permisos del escritorio
 * debe decidir también en ese caso. Si el rol no puede abrir el módulo se
 * muestra el aviso, nunca la lista.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaListaModulo(
    sesion: Sesion,
    rutaModulo: String,
    alVolver: () -> Unit,
    alAbrir: (Modulo, Long) -> Unit,
    alCrear: (() -> Unit)? = null,
    vistaModelo: ModulosViewModel = hiltViewModel(),
) {
    val modulo = Modulo.desde(rutaModulo)
    val soloEscritorio = modulo == Modulo.DASHBOARD || modulo == Modulo.CONFIGURACION

    if (modulo == null || !sesion.puedeAbrir(modulo) || soloEscritorio) {
        Scaffold(topBar = { BarraSuperior(titulo = "Módulo", alVolver = alVolver) }) { relleno ->
            MensajeVacio(
                icono = Icons.Filled.Lock,
                titulo = if (soloEscritorio) "Disponible solo en el escritorio" else "Módulo no disponible",
                detalle = if (soloEscritorio) {
                    "El panel de control y la configuración institucional son propias " +
                        "del software de escritorio. En el teléfono consulte los datos " +
                        "operativos desde Soluciones."
                } else {
                    "Su rol (${sesion.etiquetaRol}) no tiene acceso a este módulo. " +
                        "Si necesita consultarlo, pida al administrador que amplíe sus permisos."
                },
                modificador = Modifier.padding(relleno),
            )
        }
        return
    }

    val catalogo by vistaModelo.catalogo.collectAsStateWithLifecycle()

    Scaffold(
        topBar = { BarraSuperior(titulo = modulo.etiqueta, alVolver = alVolver) },
        floatingActionButton = {
            if (alCrear != null && sesion.puede(Permiso.CREAR)) {
                ExtendedFloatingActionButton(
                    onClick = alCrear,
                    icon = { Icon(Icons.Filled.Add, contentDescription = null) },
                    text = { Text("Nuevo") },
                )
            }
        },
    ) { relleno ->
        ContenidoLista(
            catalogo = catalogo,
            modulo = modulo,
            puedeEditar = sesion.puede(Permiso.EDITAR),
            modificador = Modifier
                .fillMaxSize()
                .padding(relleno),
            alAbrir = { id -> alAbrir(modulo, id) },
        )
    }
}

@Composable
private fun ContenidoLista(
    catalogo: Catalogo,
    modulo: Modulo,
    puedeEditar: Boolean,
    modificador: Modifier,
    alAbrir: (Long) -> Unit,
) {
    var consulta by rememberSaveable(modulo.ruta) { mutableStateOf("") }
    val filas = remember(catalogo, modulo, consulta) { catalogo.buscar(modulo, consulta) }
    val total = remember(catalogo, modulo) { catalogo.filas(modulo).size }

    Column(modifier = modificador) {
        OutlinedTextField(
            value = consulta,
            onValueChange = { consulta = it },
            label = { Text("Buscar en ${modulo.etiqueta.lowercase()}") },
            singleLine = true,
            leadingIcon = { Icon(Icons.Filled.Search, contentDescription = null) },
            trailingIcon = {
                if (consulta.isNotEmpty()) {
                    IconButton(onClick = { consulta = "" }) {
                        Icon(Icons.Filled.Close, contentDescription = "Limpiar búsqueda")
                    }
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
        )

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = if (consulta.isBlank()) {
                    "$total registro(s) · " + if (puedeEditar) "puede editar" else "solo consulta"
                } else {
                    "${filas.size} de $total coincidencia(s)"
                },
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(1f),
            )
        }

        if (filas.isEmpty()) {
            MensajeVacio(
                icono = Icons.Filled.Inbox,
                titulo = if (consulta.isBlank()) "Sin registros" else "Sin coincidencias",
                detalle = if (consulta.isBlank()) {
                    "El nodo central todavía no ha replicado registros de este módulo " +
                        "en este teléfono. Aparecerán en cuanto sincronice."
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
                items(filas, key = { it.id }) { fila ->
                    TarjetaFila(fila = fila, alAbrir = { alAbrir(fila.id) })
                }
            }
        }
    }
}
