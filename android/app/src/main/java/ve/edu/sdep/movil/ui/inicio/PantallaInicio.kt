package ve.edu.sdep.movil.ui.inicio

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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.EventBusy
import androidx.compose.material.icons.filled.Gavel
import androidx.compose.material.icons.filled.Grade
import androidx.compose.material.icons.filled.Payments
import androidx.compose.material.icons.filled.School
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.modulos.ModulosViewModel

/**
 * Portada de la aplicación: soluciones agrupadas por categoría.
 *
 * Ya no es el panel de control del escritorio ni la captura de campo: es un
 * índice de tareas. Cada tarjeta abre la lista del módulo (con alta y edición
 * si el rol lo permite), una tabla académica o la captura de campo. Las
 * tarjetas que el rol no puede abrir no se muestran.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaInicio(
    sesion: Sesion,
    alAbrirModulo: (Modulo) -> Unit,
    alAbrirTabla: (String) -> Unit,
    alCaptura: () -> Unit,
    alAjustes: () -> Unit,
    alConflictos: () -> Unit,
    alTodosLosModulos: () -> Unit,
    alHerramientasPdf: () -> Unit = {},
    vistaModelo: ModulosViewModel = hiltViewModel(),
) {
    val catalogo by vistaModelo.catalogo.collectAsStateWithLifecycle()
    val datos = catalogo.datos

    val categorias = remember(
        sesion, datos, alAbrirModulo, alAbrirTabla, alCaptura, alAjustes, alConflictos, alHerramientasPdf,
    ) {
        buildList {
            add(
                Categoria(
                    titulo = "Personal",
                    detalle = "Fichas, legajo documental y novedades del personal",
                    soluciones = listOfNotNull(
                        solucion(
                            sesion, Modulo.EMPLEADOS, "Empleados",
                            "Datos personales, laborales y de salud",
                            Icons.Filled.Badge, datos.empleados.size,
                        ) { alAbrirModulo(Modulo.EMPLEADOS) },
                        solucion(
                            sesion, Modulo.DOCUMENTOS, "Documentos",
                            "Legajo, vencimientos y archivos",
                            Icons.Filled.Description, datos.documentos.size,
                        ) { alAbrirModulo(Modulo.DOCUMENTOS) },
                        solucion(
                            sesion, Modulo.INCIDENCIAS, "Incidencias",
                            "Permisos, reposos y ausencias",
                            Icons.Filled.EventBusy, datos.incidencias.size,
                        ) { alAbrirModulo(Modulo.INCIDENCIAS) },
                        if (sesion.puedeAbrir(Modulo.EMPLEADOS) &&
                            (sesion.puede(ve.edu.sdep.movil.dominio.modelo.Permiso.REPORTAR) ||
                                (sesion.puedeAbrir(Modulo.DOCUMENTOS) &&
                                    sesion.puede(ve.edu.sdep.movil.dominio.modelo.Permiso.CREAR)))
                        ) {
                            Solucion(
                                titulo = "Constancias y PDF",
                                detalle = "Generar, cargar y compartir documentos del personal",
                                icono = Icons.Filled.Description,
                                conteo = null,
                                alAbrir = alHerramientasPdf,
                            )
                        } else null,
                    ),
                ),
            )
            add(
                Categoria(
                    titulo = "Académico",
                    detalle = "Estudiantes, calificaciones y estructura escolar",
                    soluciones = listOfNotNull(
                        solucion(
                            sesion, Modulo.ESTUDIANTES, "Estudiantes",
                            "Expediente y representantes",
                            Icons.Filled.School, datos.estudiantes.size,
                        ) { alAbrirModulo(Modulo.ESTUDIANTES) },
                        solucion(
                            sesion, Modulo.NOTAS, "Calificaciones",
                            "Notas por materia y grupo",
                            Icons.Filled.Grade, datos.notas.size,
                        ) { alAbrirModulo(Modulo.NOTAS) },
                        solucion(
                            sesion, Modulo.NOTAS, "Períodos",
                            "Apertura y cierre de períodos",
                            Icons.Filled.DateRange, datos.periodos.size,
                        ) { alAbrirTabla("periodos_academicos") },
                        solucion(
                            sesion, Modulo.NOTAS, "Grados",
                            "Grupos, secciones y niveles",
                            Icons.Filled.School, datos.grados.size,
                        ) { alAbrirTabla("grados") },
                        solucion(
                            sesion, Modulo.NOTAS, "Matrículas",
                            "Inscripción de estudiantes en grados",
                            Icons.Filled.Description, datos.matriculas.size,
                        ) { alAbrirTabla("matriculas") },
                    ),
                ),
            )
            add(
                Categoria(
                    titulo = "Administración",
                    detalle = "Relación laboral y pagos",
                    soluciones = listOfNotNull(
                        solucion(
                            sesion, Modulo.CONTRATOS, "Contratos",
                            "Vigencias, cargos y salarios pactados",
                            Icons.Filled.Gavel, datos.contratos.size,
                        ) { alAbrirModulo(Modulo.CONTRATOS) },
                        solucion(
                            sesion, Modulo.NOMINA, "Nómina",
                            "Recibos, deducciones y pagos",
                            Icons.Filled.Payments, datos.pagos.size,
                        ) { alAbrirModulo(Modulo.NOMINA) },
                    ),
                ),
            )
            add(
                Categoria(
                    titulo = "Trabajo de campo",
                    detalle = "Captura en el puesto y control de la sincronización",
                    soluciones = listOf(
                        Solucion(
                            titulo = "Captura de campo",
                            detalle = "Registrar una novedad desde el teléfono",
                            icono = Icons.Filled.Tune,
                            conteo = null,
                            alAbrir = alCaptura,
                        ),
                        Solucion(
                            titulo = "Conflictos",
                            detalle = "Valores que compitieron entre equipos",
                            icono = Icons.Filled.EventBusy,
                            conteo = null,
                            alAbrir = alConflictos,
                        ),
                        Solucion(
                            titulo = "Sincronización",
                            detalle = "Nodo central, cola de salida y conflictos",
                            icono = Icons.Filled.Settings,
                            conteo = null,
                            alAbrir = alAjustes,
                        ),
                    ),
                ),
            )
        }.filter { categoria -> categoria.soluciones.isNotEmpty() }
    }

    Scaffold(
        topBar = {
            BarraSuperior(
                titulo = "Soluciones",
                acciones = {
                    IconButton(onClick = alAjustes) {
                        Icon(Icons.Filled.Settings, contentDescription = "Sincronización")
                    }
                },
            )
        },
    ) { relleno ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(relleno),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 8.dp, bottom = 28.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            item {
                Text(
                    text = "Hola, ${sesion.nombre}",
                    style = MaterialTheme.typography.headlineSmall,
                )
                Spacer(Modifier.height(2.dp))
                Text(
                    text = "Rol: ${sesion.etiquetaRol} · soluciones disponibles en este teléfono",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.height(10.dp))
            }

            categorias.forEach { categoria ->
                item(key = "cat-${categoria.titulo}") {
                    Spacer(Modifier.height(6.dp))
                    Text(
                        text = categoria.titulo,
                        color = MaterialTheme.colorScheme.primary,
                        style = MaterialTheme.typography.titleMedium,
                    )
                    Text(
                        text = categoria.detalle,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                items(categoria.soluciones, key = { solucion ->
                    "${categoria.titulo}-${solucion.titulo}"
                }) { solucion ->
                    TarjetaSolucion(solucion, Modifier.fillMaxWidth())
                }
            }

            item {
                Spacer(Modifier.height(6.dp))
                TextButton(onClick = alTodosLosModulos, modifier = Modifier.fillMaxWidth()) {
                    Text("Ver todos los módulos")
                }
            }
        }
    }
}

@Composable
private fun TarjetaSolucion(solucion: Solucion, modificador: Modifier) {
    Card(modifier = modificador.clickable(onClick = solucion.alAbrir)) {
        Row(
            modifier = Modifier.padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Surface(
                color = MaterialTheme.colorScheme.primaryContainer,
                contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
                shape = CircleShape,
            ) {
                Box(modifier = Modifier.size(40.dp), contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = solucion.icono,
                        contentDescription = null,
                        modifier = Modifier.size(20.dp),
                    )
                }
            }
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(text = solucion.titulo, style = MaterialTheme.typography.titleSmall)
                Text(
                    text = solucion.detalle,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            solucion.conteo?.let { cantidad ->
                Spacer(Modifier.width(8.dp))
                Text(
                    text = cantidad.toString(),
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
            }
        }
    }
}

/** Construye una solución solo si el rol puede abrir el módulo */
private fun solucion(
    sesion: Sesion,
    modulo: Modulo,
    titulo: String,
    detalle: String,
    icono: ImageVector,
    conteo: Int,
    alAbrir: () -> Unit,
): Solucion? {
    if (!sesion.puedeAbrir(modulo)) return null
    return Solucion(titulo, detalle, icono, conteo, alAbrir)
}

private data class Solucion(
    val titulo: String,
    val detalle: String,
    val icono: ImageVector,
    val conteo: Int?,
    val alAbrir: () -> Unit,
)

private data class Categoria(
    val titulo: String,
    val detalle: String,
    val soluciones: List<Solucion>,
)
