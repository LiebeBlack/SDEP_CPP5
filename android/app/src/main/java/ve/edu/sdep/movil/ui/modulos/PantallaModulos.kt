package ve.edu.sdep.movil.ui.modulos

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Dashboard
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.EventBusy
import androidx.compose.material.icons.filled.Gavel
import androidx.compose.material.icons.filled.Grade
import androidx.compose.material.icons.filled.Payments
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.comun.BarraSuperior

/**
 * Índice de módulos del sistema.
 *
 * Es la puerta a todas las funciones que el escritorio ofrece y que hasta
 * ahora el teléfono no mostraba. La lista se filtra con la misma matriz de
 * permisos que el escritorio ([Sesion.puedeAbrir]): un usuario ve exactamente
 * los módulos que vería en la PC, ni uno más. La captura de campo sigue
 * teniendo su propia pantalla de inicio, porque es el uso propio del puesto
 * móvil y ya está resuelta.
 *
 * El panel de control y la configuración institucional, que son pantallas del
 * escritorio, no se ofrecen aquí. Cada módulo abre su lista y su ficha, y la
 * escritura se hace con el formulario dinámico de la tabla, siempre que el rol
 * tenga el permiso de la acción.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaModulos(
    sesion: Sesion,
    alVolver: () -> Unit,
    alAbrir: (Modulo) -> Unit,
    vistaModelo: ModulosViewModel = hiltViewModel(),
) {
    val catalogo by vistaModelo.catalogo.collectAsStateWithLifecycle()
    val modulos = ORDEN_DE_MODULOS.filter { sesion.puedeAbrir(it) }

    Scaffold(topBar = { BarraSuperior(titulo = "Módulos", alVolver = alVolver) }) { relleno ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(relleno),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            item {
                Text(
                    text = "Sistema institucional",
                    style = MaterialTheme.typography.titleMedium,
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = "${sesion.nombre} · ${sesion.etiquetaRol}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            items(modulos, key = { it.name }) { modulo ->
                TarjetaModulo(
                    modulo = modulo,
                    conteo = conteo(catalogo, modulo),
                    alAbrir = { alAbrir(modulo) },
                )
            }

            item {
                NotaAlcance()
            }
        }
    }
}

@Composable
private fun TarjetaModulo(modulo: Modulo, conteo: Int?, alAbrir: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = alAbrir),
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Surface(
                color = MaterialTheme.colorScheme.primaryContainer,
                contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                shape = CircleShape,
            ) {
                Box(modifier = Modifier.size(42.dp), contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = iconoDe(modulo),
                        contentDescription = null,
                        modifier = Modifier.size(22.dp),
                    )
                }
            }
            Spacer(Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(text = modulo.etiqueta, style = MaterialTheme.typography.titleSmall)
                Spacer(Modifier.height(2.dp))
                Text(
                    text = descripcionDe(modulo),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (conteo != null) {
                Spacer(Modifier.width(10.dp))
                Text(
                    text = conteo.toString(),
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
            }
        }
    }
}

@Composable
private fun NotaAlcance() {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 6.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(
                text = "Trabajo sin conexión y permisos por rol",
                style = MaterialTheme.typography.titleSmall,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                text = "Estas pantallas leen la copia de trabajo del teléfono: funcionan " +
                    "sin red y se actualizan solas con cada sincronización. Según su rol " +
                    "verá solo los módulos y las acciones (crear, editar, eliminar) que le " +
                    "corresponden; el nodo central sigue siendo la autoridad final.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

/**
 * Orden de lectura: primero el panorama, después el personal y la operación
 * laboral, luego lo académico y al final la configuración del sistema. La
 * captura de campo no aparece porque es la pantalla de inicio.
 */
private val ORDEN_DE_MODULOS = listOf(
    Modulo.EMPLEADOS,
    Modulo.DOCUMENTOS,
    Modulo.INCIDENCIAS,
    Modulo.CONTRATOS,
    Modulo.NOMINA,
    Modulo.ESTUDIANTES,
    Modulo.NOTAS,
)

/** Cuántos registros tiene el módulo; null si el módulo no se cuenta */
private fun conteo(catalogo: Catalogo, modulo: Modulo): Int? = when (modulo) {
    Modulo.DASHBOARD -> catalogo.alertas().size
    Modulo.REGISTROS -> null
    else -> catalogo.filas(modulo).size
}

private fun descripcionDe(modulo: Modulo): String = when (modulo) {
    Modulo.DASHBOARD -> "Cifras del sistema y avisos que requieren atención"
    Modulo.EMPLEADOS -> "Fichas del personal: datos personales, laborales y de salud"
    Modulo.DOCUMENTOS -> "Legajo documental, vencimientos y archivos"
    Modulo.INCIDENCIAS -> "Permisos, reposos y ausencias con su aprobación"
    Modulo.CONTRATOS -> "Contratos, salarios y vigencias"
    Modulo.NOMINA -> "Recibos, devengos, deducciones y pagos pendientes"
    Modulo.ESTUDIANTES -> "Expediente, representantes y matrículas"
    Modulo.NOTAS -> "Períodos, grupos, promedios y calificaciones"
    Modulo.CONFIGURACION -> "Parámetros institucionales del sistema"
    Modulo.REGISTROS -> "Captura de campo de este puesto"
}

private fun iconoDe(modulo: Modulo): ImageVector = when (modulo) {
    Modulo.DASHBOARD -> Icons.Filled.Dashboard
    Modulo.EMPLEADOS -> Icons.Filled.Badge
    Modulo.DOCUMENTOS -> Icons.Filled.Description
    Modulo.INCIDENCIAS -> Icons.Filled.EventBusy
    Modulo.CONTRATOS -> Icons.Filled.Gavel
    Modulo.NOMINA -> Icons.Filled.Payments
    Modulo.ESTUDIANTES -> Icons.Filled.School
    Modulo.NOTAS -> Icons.Filled.Grade
    Modulo.CONFIGURACION -> Icons.Filled.Tune
    Modulo.REGISTROS -> Icons.Filled.Description
}
