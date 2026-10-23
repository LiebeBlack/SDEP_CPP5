package ve.edu.sdep.movil.ui.ajustes

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.fragment.app.FragmentActivity
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.datos.remoto.PerfilDto
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.DialogoConfirmar
import ve.edu.sdep.movil.ui.comun.MensajeError

/**
 * Pantalla de perfil propio del usuario.
 *
 * Permite ver y editar nombre completo y cédula (obligatorio para rol
 * trabajador). El rol y el nombre de usuario son de solo lectura.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun UserProfileScreen(
    alVolver: () -> Unit,
    vistaModelo: UserProfileViewModel = hiltViewModel(),
) {
    val estado by vistaModelo.estado.collectAsStateWithLifecycle()
    val contexto = LocalContext.current
    val actividad = contexto as? FragmentActivity
    val barra = remember { SnackbarHostState() }

    var dialogoEdicion by remember { mutableStateOf(false) }
    var nombreEdicion by remember { mutableStateOf("") }
    var cedulaEdicion by remember { mutableStateOf("") }
    var confirmarDescartar by remember { mutableStateOf(false) }

    LaunchedEffect(estado.mensaje) {
        val texto = estado.mensaje ?: return@LaunchedEffect
        barra.showSnackbar(texto)
        vistaModelo.limpiarMensaje()
    }

    LaunchedEffect(estado.perfil) {
        val perfil = estado.perfil ?: return@LaunchedEffect
        nombreEdicion = perfil.nombre_completo ?: ""
        cedulaEdicion = perfil.cedula ?: ""
    }

    Scaffold(
        topBar = { BarraSuperior(titulo = "Mi perfil", alVolver = alVolver) },
        snackbarHost = { SnackbarHost(barra) },
    ) { relleno ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(relleno)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            if (estado.cargando) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                ) {
                    CircularProgressIndicator()
                }
            } else {
                TarjetaPerfil(estado.perfil)

                Spacer(Modifier.height(16.dp))

                if (!estado.editando) {
                    OutlinedButton(
                        onClick = {
                            vistaModelo.iniciarEdicion()
                            dialogoEdicion = true
                        },
                        modifier = Modifier.fillMaxWidth(),
                        leadingIcon = { Icon(Icons.Filled.Edit, contentDescription = null) },
                    ) {
                        Text("Editar perfil")
                    }
                }

                if (estado.perfilGuardado) {
                    Surface(
                        color = MaterialTheme.colorScheme.secondaryContainer,
                        shape = MaterialTheme.shapes.small,
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onSecondaryContainer,
                                modifier = Modifier.size(18.dp),
                            )
                            Spacer(Modifier.width(8.dp))
                            Text(
                                text = "Perfil guardado correctamente.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSecondaryContainer,
                            )
                        }
                    }
                }
            }

            MensajeError(estado.mensaje.takeIf { estado.esError })
        }

        if (dialogoEdicion) {
            DialogoEdicionPerfil(
                perfil = estado.perfil,
                nombre = nombreEdicion,
                cedula = cedulaEdicion,
                ocupado = estado.ocupado,
                alCambiarNombre = { nombreEdicion = it },
                alCambiarCedula = { cedulaEdicion = it },
                alGuardar = {
                    vistaModelo.guardarPerfil(nombreEdicion, cedulaEdicion)
                    dialogoEdicion = false
                },
                alCancelar = {
                    dialogoEdicion = false
                    vistaModelo.cancelarEdicion()
                },
            )
        }

        if (confirmarDescartar) {
            DialogoConfirmar(
                titulo = "Descartar cambios",
                mensaje = "Se perderán los cambios realizados en el perfil. ¿Desea continuar?",
                textoConfirmar = "Descartar",
                alConfirmar = {
                    confirmarDescartar = false
                    dialogoEdicion = false
                    vistaModelo.cancelarEdicion()
                    nombreEdicion = estado.perfil?.nombre_completo ?: ""
                    cedulaEdicion = estado.perfil?.cedula ?: ""
                },
                alCancelar = { confirmarDescartar = false },
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TarjetaPerfil(perfil: PerfilDto?) {
    if (perfil == null) return

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Perfil de usuario", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(Icons.Default.Person, contentDescription = null, modifier = Modifier.size(24.dp))
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = if (perfil.nombre_completo.isNotBlank()) perfil.nombre_completo else "Sin nombre",
                        style = MaterialTheme.typography.bodyLarge,
                    )
                    Text(
                        text = "${perfil.username} · ${perfil.rol.toUpperCase()}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(12.dp))

            FilaPerfil("Cédula", if (perfil.cedula.isNotBlank()) perfil.cedula else "Sin asignar")
            FilaPerfil("Rol", perfil.rol.toUpperCase())
            FilaPerfil("Estado", if (perfil.activo) "Activa" else "Inactiva")
            FilaPerfil(
                "Contraseña",
                if (perfil.debe_cambiar_password) "Requiere cambio" else "Vigente",
            )

            if (perfil.debe_cambiar_password) {
                Spacer(Modifier.height(8.dp))
                Surface(
                    color = MaterialTheme.colorScheme.errorContainer,
                    shape = MaterialTheme.shapes.small,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Row(
                        modifier = Modifier.padding(10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Warning,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onErrorContainer,
                            modifier = Modifier.size(18.dp),
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(
                            text = "Su contraseña debe ser cambiada. Use la opción de ajustes.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                        )
                    }
                }
            }

            if (perfil.cedula.isNullOrBlank() && perfil.rol == "user") {
                Spacer(Modifier.height(8.dp))
                Surface(
                    color = MaterialTheme.colorScheme.errorContainer,
                    shape = MaterialTheme.shapes.small,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Row(
                        modifier = Modifier.padding(10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            imageVector = Icons.Filled.Warning,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onErrorContainer,
                            modifier = Modifier.size(18.dp),
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(
                            text = "La cédula es obligatoria para su rol de trabajador. " +
                                "Complete su perfil para poder usar todas las funciones.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun FilaPerfil(etiqueta: String, valor: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = etiqueta,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(96.dp),
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = valor,
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.weight(1f),
        )
    }
}

/**
 * Diálogo para editar el perfil del usuario.
 */
@Composable
private fun DialogoEdicionPerfil(
    perfil: PerfilDto?,
    nombre: String,
    cedula: String,
    ocupado: Boolean,
    alCambiarNombre: (String) -> Unit,
    alCambiarCedula: (String) -> Unit,
    alGuardar: () -> Unit,
    alCancelar: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = { alCancelar() },
        title = { Text("Editar perfil") },
        text = {
            Column(modifier = Modifier.verticalScroll(rememberScrollState())) {
                Text(
                    text = "Complete sus datos personales. La cédula es obligatoria para " +
                        "usuarios con rol de trabajador.",
                    style = MaterialTheme.typography.bodySmall,
                )
                Spacer(Modifier.height(12.dp))

                OutlinedTextField(
                    value = nombre,
                    onValueChange = alCambiarNombre,
                    label = { Text("Nombre completo") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))

                OutlinedTextField(
                    value = cedula,
                    onValueChange = alCambiarCedula,
                    label = { Text("Cédula") },
                    supportingText = {
                        if (perfil?.rol == "user") {
                            Text("Obligatorio para trabajadores")
                        } else {
                            Text("Opcional")
                        }
                    },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = {
            TextButton(
                enabled = !ocupado,
                onClick = { alGuardar() },
            ) {
                if (ocupado) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Default.Save, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Guardar")
                }
            }
        },
        dismissButton = {
            TextButton(onClick = { alCancelar() }) { Text("Cancelar") }
        },
    )
}
