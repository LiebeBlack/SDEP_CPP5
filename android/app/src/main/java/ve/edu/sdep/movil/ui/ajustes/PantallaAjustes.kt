package ve.edu.sdep.movil.ui.ajustes

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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.Group
import androidx.compose.material.icons.filled.PersonAdd
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.fragment.app.FragmentActivity
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.BuildConfig
import ve.edu.sdep.movil.datos.local.entidad.UsuarioEntity
import ve.edu.sdep.movil.datos.seguridad.AutenticadorBiometrico
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Rol
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.DialogoConfirmar
import ve.edu.sdep.movil.ui.comun.fechaHora

/**
 * Ajustes del puesto móvil.
 *
 * Aquí se empareja el teléfono con el nodo central (dirección, equipo y token),
 * se administran las cuentas locales y se revisa qué falta por sincronizar.
 * La configuración vive cifrada en el dispositivo; el token nunca se escribe
 * en un archivo legible ni se envía a nadie más que al propio nodo.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaAjustes(
    sesion: Sesion,
    alVolver: () -> Unit,
    alCerrarSesion: () -> Unit,
    alVerConflictos: () -> Unit,
    vistaModelo: AjustesViewModel = hiltViewModel(),
) {
    val estado by vistaModelo.estado.collectAsStateWithLifecycle()
    val contexto = LocalContext.current
    val actividad = contexto as? FragmentActivity
    val autenticador = remember { AutenticadorBiometrico() }
    val biometriaDisponible = remember(contexto) { autenticador.disponible(contexto) }
    val barra = remember { SnackbarHostState() }

    var dialogoCuenta by remember { mutableStateOf(false) }
    var confirmarSalida by remember { mutableStateOf(false) }

    LaunchedEffect(estado.mensaje) {
        val texto = estado.mensaje ?: return@LaunchedEffect
        barra.showSnackbar(texto)
        vistaModelo.limpiarMensaje()
    }

    fun pedirHuella() {
        if (actividad == null) {
            vistaModelo.registrarMensaje("Este equipo no puede mostrar el diálogo biométrico.", true)
            return
        }
        autenticador.solicitar(
            actividad = actividad,
            titulo = "Activar desbloqueo con huella",
            subtitulo = "Confirme su identidad para guardar la llave en este teléfono",
            alExito = vistaModelo::activarBiometria,
            alFallo = { mensaje -> vistaModelo.registrarMensaje(mensaje, true) },
        )
    }

    Scaffold(
        topBar = { BarraSuperior(titulo = "Ajustes", alVolver = alVolver) },
        snackbarHost = { SnackbarHost(barra) },
    ) { relleno ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(relleno)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            if (estado.cargando) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                ) {
                    CircularProgressIndicator()
                }
            }

            TarjetaCuenta(
                sesion = sesion,
                biometriaActiva = estado.biometriaActiva,
                biometriaDisponible = biometriaDisponible,
                alAlternarBiometria = { activar ->
                    if (activar) pedirHuella() else vistaModelo.desactivarBiometria()
                },
                alSalir = { confirmarSalida = true },
            )

            TarjetaConexion(
                estado = estado,
                alCambiarUrl = vistaModelo::cambiarUrl,
                alCambiarEquipo = vistaModelo::cambiarEquipo,
                alCambiarToken = vistaModelo::cambiarToken,
                alCambiarActiva = vistaModelo::cambiarActiva,
                alGuardar = vistaModelo::guardar,
                alProbar = vistaModelo::probarConexion,
            )

            TarjetaSincronizacion(
                estado = estado,
                alSincronizar = vistaModelo::sincronizarAhora,
            )

            TarjetaConflictos(cantidad = estado.conflictos, alVer = alVerConflictos)

            if (sesion.puede(Permiso.ADMINISTRAR_USUARIOS)) {
                TarjetaUsuarios(
                    usuarios = estado.usuarios,
                    alAgregar = { dialogoCuenta = true },
                )
            }

            Spacer(Modifier.height(8.dp))
            Text(
                text = "SDEP Móvil ${BuildConfig.VERSION_NAME} · protocolo de sincronización 1",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.outline,
            )
        }
    }

    if (dialogoCuenta) {
        DialogoNuevaCuenta(
            alCrear = { nombre, usuario, contrasena, confirmacion, rol ->
                vistaModelo.crearUsuario(nombre, usuario, contrasena, confirmacion, rol)
                dialogoCuenta = false
            },
            alCancelar = { dialogoCuenta = false },
        )
    }

    if (confirmarSalida) {
        DialogoConfirmar(
            titulo = "Cerrar sesión",
            mensaje = "Los cambios pendientes quedan guardados en el teléfono y se " +
                "enviarán con la próxima sincronización. Para volver a entrar necesitará " +
                "su contraseña o su huella.",
            textoConfirmar = "Cerrar sesión",
            alConfirmar = {
                confirmarSalida = false
                vistaModelo.cerrarSesion()
                alCerrarSesion()
            },
            alCancelar = { confirmarSalida = false },
        )
    }
}

// ----------------------------------------------------------------------
// Secciones
// ----------------------------------------------------------------------
@Composable
private fun TarjetaCuenta(
    sesion: Sesion,
    biometriaActiva: Boolean,
    biometriaDisponible: Boolean,
    alAlternarBiometria: (Boolean) -> Unit,
    alSalir: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Cuenta", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(8.dp))
            Text(sesion.nombre, style = MaterialTheme.typography.bodyLarge)
            Text(
                text = "${sesion.usuario} · ${sesion.rol.etiqueta}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(Icons.Filled.Fingerprint, contentDescription = null)
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    Text("Desbloqueo con huella", style = MaterialTheme.typography.bodyMedium)
                    Text(
                        text = when {
                            !biometriaDisponible -> "El sensor no está disponible en este equipo"
                            biometriaActiva -> "Activado: se guarda una llave cifrada, no la contraseña"
                            else -> "Entre sin escribir la contraseña"
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Switch(
                    checked = biometriaActiva,
                    onCheckedChange = alAlternarBiometria,
                    enabled = biometriaDisponible,
                )
            }

            Spacer(Modifier.height(12.dp))
            OutlinedButton(
                onClick = alSalir,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.AutoMirrored.Filled.Logout, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Cerrar sesión")
            }
        }
    }
}

@Composable
private fun TarjetaConexion(
    estado: EstadoAjustes,
    alCambiarUrl: (String) -> Unit,
    alCambiarEquipo: (String) -> Unit,
    alCambiarToken: (String) -> Unit,
    alCambiarActiva: (Boolean) -> Unit,
    alGuardar: () -> Unit,
    alProbar: () -> Unit,
) {
    var tokenVisible by remember { mutableStateOf(false) }

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Nodo central", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(4.dp))
            Text(
                text = "Datos que entrega el administrador al dar de alta este teléfono " +
                    "como un puesto más de la intranet.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(Modifier.height(12.dp))

            OutlinedTextField(
                value = estado.url,
                onValueChange = alCambiarUrl,
                label = { Text("Dirección del servidor") },
                placeholder = { Text("http://192.168.1.10:8765") },
                supportingText = { Text("IP o nombre del equipo y puerto del servicio") },
                singleLine = true,
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Uri,
                    imeAction = ImeAction.Next,
                ),
                modifier = Modifier.fillMaxWidth(),
            )

            Spacer(Modifier.height(10.dp))

            OutlinedTextField(
                value = estado.equipo,
                onValueChange = alCambiarEquipo,
                label = { Text("Identificador del equipo") },
                supportingText = { Text("El mismo que devuelve el alta del puesto") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )

            Spacer(Modifier.height(10.dp))

            OutlinedTextField(
                value = estado.token,
                onValueChange = alCambiarToken,
                label = { Text("Token del equipo") },
                supportingText = { Text("Se guarda cifrado en este teléfono") },
                singleLine = true,
                visualTransformation = if (tokenVisible) {
                    VisualTransformation.None
                } else {
                    PasswordVisualTransformation()
                },
                trailingIcon = {
                    IconButton(onClick = { tokenVisible = !tokenVisible }) {
                        Icon(
                            imageVector = if (tokenVisible) {
                                Icons.Filled.VisibilityOff
                            } else {
                                Icons.Filled.Visibility
                            },
                            contentDescription = if (tokenVisible) "Ocultar token" else "Mostrar token",
                        )
                    }
                },
                modifier = Modifier.fillMaxWidth(),
            )

            Spacer(Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("Sincronizar este equipo", style = MaterialTheme.typography.bodyMedium)
                    Text(
                        text = "Envío y recepción automáticos cada 15 minutos",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Switch(checked = estado.activa, onCheckedChange = alCambiarActiva)
            }

            Spacer(Modifier.height(12.dp))

            Button(
                onClick = alGuardar,
                enabled = !estado.ocupado,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (estado.ocupado) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(18.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary,
                    )
                } else {
                    Text("Guardar configuración")
                }
            }

            Spacer(Modifier.height(8.dp))

            OutlinedButton(
                onClick = alProbar,
                enabled = !estado.probando,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (estado.probando) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Filled.Sync, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Probar conexión")
                }
            }

            val servidor = estado.servidor
            if (!servidor.isNullOrBlank()) {
                Spacer(Modifier.height(8.dp))
                Text(
                    text = "$servidor · protocolo ${estado.versionProtocolo.orEmpty()}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                estado.desfaseSegundos?.let { desfase ->
                    val segundos = kotlin.math.abs(desfase)
                    Text(
                        text = if (segundos > 60) {
                            "Reloj desfasado ${segundos} s respecto al servidor: corríjalo antes de editar."
                        } else {
                            "Reloj sincronizado con el servidor."
                        },
                        style = MaterialTheme.typography.labelSmall,
                        color = if (segundos > 60) {
                            MaterialTheme.colorScheme.error
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        },
                    )
                }
            }
        }
    }
}

@Composable
private fun TarjetaSincronizacion(estado: EstadoAjustes, alSincronizar: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Sincronización", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(8.dp))

            FilaDato(
                etiqueta = "Última sincronización",
                valor = estado.ultimaSync?.let { fechaHora(it) } ?: "Nunca",
            )
            FilaDato(
                etiqueta = "Cambios pendientes",
                valor = estado.pendientes.toString(),
            )
            FilaDato(
                etiqueta = "Conflictos sin revisar",
                valor = estado.conflictos.toString(),
            )

            val error = estado.ultimoError
            if (!error.isNullOrBlank()) {
                Spacer(Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.Top) {
                    Icon(
                        imageVector = Icons.Filled.Warning,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.error,
                        modifier = Modifier.size(18.dp),
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        text = error,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
            }

            Spacer(Modifier.height(12.dp))
            OutlinedButton(
                onClick = alSincronizar,
                enabled = !estado.sincronizando,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (estado.sincronizando) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Filled.Sync, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Sincronizar ahora")
                }
            }
        }
    }
}

@Composable
private fun TarjetaConflictos(cantidad: Int, alVer: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(Icons.Filled.Warning, contentDescription = null)
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text("Conflictos de sincronización", style = MaterialTheme.typography.titleSmall)
                Text(
                    text = if (cantidad == 0) {
                        "No hay escrituras en disputa"
                    } else {
                        "$cantidad sin revisar"
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            TextButton(onClick = alVer) { Text("Revisar") }
        }
    }
}

@Composable
private fun TarjetaUsuarios(usuarios: List<UsuarioEntity>, alAgregar: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.Group, contentDescription = null)
                Spacer(Modifier.width(12.dp))
                Text(
                    text = "Cuentas de este teléfono",
                    style = MaterialTheme.typography.titleSmall,
                    modifier = Modifier.weight(1f),
                )
                IconButton(onClick = alAgregar) {
                    Icon(Icons.Filled.PersonAdd, contentDescription = "Agregar cuenta")
                }
            }

            if (usuarios.isEmpty()) {
                Text(
                    text = "Todavía no hay cuentas.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            } else {
                usuarios.forEach { usuario ->
                    HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(usuario.nombre, style = MaterialTheme.typography.bodyMedium)
                            Text(
                                text = "${usuario.usuario} · ${Rol.desde(usuario.rol).etiqueta}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                        if (!usuario.activo) {
                            Text(
                                text = "Inactiva",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.error,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FilaDato(etiqueta: String, valor: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 3.dp),
    ) {
        Text(
            text = etiqueta,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.weight(1f),
        )
        Text(valor, style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun DialogoNuevaCuenta(
    alCrear: (String, String, String, String, Rol) -> Unit,
    alCancelar: () -> Unit,
) {
    var nombre by remember { mutableStateOf("") }
    var usuario by remember { mutableStateOf("") }
    var contrasena by remember { mutableStateOf("") }
    var confirmacion by remember { mutableStateOf("") }
    var rol by remember { mutableStateOf(Rol.EDITOR) }

    AlertDialog(
        onDismissRequest = alCancelar,
        title = { Text("Nueva cuenta") },
        text = {
            Column(modifier = Modifier.verticalScroll(rememberScrollState())) {
                Text(
                    text = "La cuenta vive solo en este teléfono, como en cualquier " +
                        "puesto del sistema.",
                    style = MaterialTheme.typography.bodySmall,
                )
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = nombre,
                    onValueChange = { nombre = it },
                    label = { Text("Nombre y apellido") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = usuario,
                    onValueChange = { usuario = it },
                    label = { Text("Usuario") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = contrasena,
                    onValueChange = { contrasena = it },
                    label = { Text("Contraseña") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = confirmacion,
                    onValueChange = { confirmacion = it },
                    label = { Text("Repita la contraseña") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                )

                Spacer(Modifier.height(12.dp))
                Text("Rol", style = MaterialTheme.typography.labelLarge)
                Rol.values().forEach { opcion ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(
                            selected = rol == opcion,
                            onClick = { rol = opcion },
                        )
                        Column(modifier = Modifier.weight(1f)) {
                            Text(opcion.etiqueta, style = MaterialTheme.typography.bodyMedium)
                            Text(
                                text = opcion.descripcion,
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = { alCrear(nombre, usuario, contrasena, confirmacion, rol) },
            ) {
                Text("Crear cuenta")
            }
        },
        dismissButton = {
            TextButton(onClick = alCancelar) { Text("Cancelar") }
        },
    )
}
