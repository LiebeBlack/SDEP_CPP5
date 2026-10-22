package ve.edu.sdep.movil.ui.modulos

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.SearchOff
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.MensajeVacio

/**
 * Ficha de detalle de una fila del espejo.
 *
 * Muestra todas las columnas que el escritorio enseña en su formulario, en el
 * mismo orden por bloques, pero sin campos editables: es una vista de consulta.
 * Si la fila desapareció (por ejemplo, se borró en otro puesto y la
 * sincronización la retiró), se avisa en lugar de mostrar una ficha a medias.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaFichaModulo(
    sesion: Sesion,
    rutaModulo: String,
    id: Long,
    alVolver: () -> Unit,
    alEditar: (() -> Unit)? = null,
    vistaModelo: ModulosViewModel = hiltViewModel(),
) {
    val modulo = Modulo.desde(rutaModulo)
    val catalogo by vistaModelo.catalogo.collectAsStateWithLifecycle()
    val ficha = remember(catalogo, modulo, id) { modulo?.let { catalogo.ficha(it, id) } }
    val permitido = modulo != null && sesion.puedeAbrir(modulo)

    Scaffold(
        topBar = {
            BarraSuperior(
                titulo = modulo?.etiqueta ?: "Detalle",
                alVolver = alVolver,
                acciones = {
                    if (alEditar != null) {
                        IconButton(onClick = alEditar) {
                            Icon(Icons.Filled.Edit, contentDescription = "Editar")
                        }
                    }
                },
            )
        },
    ) { relleno ->
        val actual = ficha
        when {
            !permitido -> MensajeVacio(
                icono = Icons.Filled.SearchOff,
                titulo = "Ficha no disponible",
                detalle = "Su rol no tiene acceso a este módulo.",
                modificador = Modifier.padding(relleno),
            )

            actual == null -> MensajeVacio(
                icono = Icons.Filled.SearchOff,
                titulo = "Registro no encontrado",
                detalle = "El registro ya no está en la copia de este teléfono. " +
                    "Puede que se haya eliminado en otro puesto; sincronice para confirmarlo.",
                modificador = Modifier.padding(relleno),
            )

            else -> LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                item { EncabezadoFicha(actual) }
                items(actual.secciones) { seccion -> TarjetaSeccion(seccion) }
            }
        }
    }
}

@Composable
private fun EncabezadoFicha(ficha: FichaCatalogo) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = ficha.titulo,
                style = MaterialTheme.typography.headlineSmall,
            )
            if (!ficha.subtitulo.isNullOrBlank()) {
                Spacer(Modifier.height(4.dp))
                Text(
                    text = ficha.subtitulo,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Spacer(Modifier.height(6.dp))
            Text(
                text = "Solo consulta · datos replicados del nodo central",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.outline,
            )
        }
    }
}
