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
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material.icons.filled.SyncProblem
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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.fragment.app.FragmentActivity
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.BuildConfig
import ve.edu.sdep.movil.datos.seguridad.AutenticadorBiometrico
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.DialogoConfirmar
import ve.edu.sdep.movil.ui.comun.fechaHora

/**
 * Ajustes del puesto móvil.
 *
 * La conexión con el escritorio no se configura aquí: se establece sola y en
 * esta pantalla solo se ve su estado. Se puede volver a buscar el equipo,
 * probar la conexión, activar el envío automático y gestionar la huella y la
 * contraseña de la cuenta institucional.
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

    var dialogoPassword by remember { mutableStateOf(false) }
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
                alCambiarContrasena = { dialogoPassword = true },
                alSalir = { confirmarSalida = true },
            )

            TarjetaServidor(
                estado = estado,
                alRedescubrir = vistaModelo::redescubrir,
                alProbar = vistaModelo::probarConexion,
                alCambiarActiva = vistaModelo::cambiarActiva,
            )

            TarjetaSincronizacion(
                estado = estado,
                alSincronizar = vistaModelo::sincronizarAhora,
            )

            TarjetaConflictos(cantidad = estado.conflictos, alVer = alVerConflictos)

            if (dialogoPassword) {
                DialogoCambioPassword(
                    ocupado = estado.ocupado,
                    alCambiar = { actual, nueva, confirmacion ->
                        vistaModelo.cambiarPassword(actual, nueva, confirmacion)
                    },
                    alCerrar = { dialogoPassword = false },
                )
            }

            Spacer(Modifier.height(8.dp))
            Text(
                text = "SDEP Móvil ${BuildConfig.VERSION_NAME} · protocolo de sincronización 2",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.outline,
            )
        }
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
    alCambiarContrasena: () -> Unit,
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

            if (sesion.debeCambiarPassword) {
                Spacer(Modifier.height(10.dp))
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
                            text = "El administrador pidió restablecer su contraseña. " +
                                "Cámbiela antes de seguir trabajando.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                        )
                    }
                }
            }

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
                onClick = alCambiarContrasena,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Icon(Icons.Filled.Lock, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Cambiar contraseña")
            }

            Spacer(Modifier.height(8.dp))
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

/**
 * Estado del sistema de escritorio.
 *
 * No hay campos editables: el vínculo lo establece la aplicación. Si el
 * servidor cambió de IP o se reinstaló, «Buscar de nuevo» repite el
 * descubrimiento y el emparejamiento sin que haya que copiar ningún dato.
 */
@Composable
private fun TarjetaServidor(
    estado: EstadoAjustes,
    alRedescubrir: () -> Unit,
    alProbar: () -> Unit,
    alCambiarActiva: (Boolean) -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = if (estado.conectado) Icons.Filled.CheckCircle else Icons.Filled.SyncProblem,
                    contentDescription = null,
                    tint = if (estado.conectado) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.error
                    },
                    modifier = Modifier.size(20.dp),
                )
                Spacer(Modifier.width(8.dp))
                Text("Sistema de escritorio", style = MaterialTheme.typography.titleSmall)
            }
            Spacer(Modifier.height(6.dp))
            Text(
                text = when {
                    estado.redescubriendo -> "Buscando el sistema de escritorio en esta red…"
                    estado.conectado -> "Vinculado automáticamente. No hay nada que configurar."
                    else -> "Aún no se encontró. Compruebe que la aplicación de escritorio " +
                        "esté abierta y en la misma Wi-Fi."
                },
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            if (estado.conectado) {
                Spacer(Modifier.height(10.dp))
                HorizontalDivider()
                Spacer(Modifier.height(10.dp))
                if (estado.urlServidor.isNotBlank()) {
                    FilaDato("Equipo del sistema", estado.urlServidor)
                }
                val servidor = estado.servidor
                if (!servidor.isNullOrBlank()) {
                    FilaDato("Servicio", servidor)
                }
                val version = estado.versionProtocolo
                if (!version.isNullOrBlank()) {
                    FilaDato("Protocolo", version)
                }
                estado.desfaseSegundos?.let { desfase ->
                    val segundos = kotlin.math.abs(desfase)
                    Spacer(Modifier.height(4.dp))
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

            Spacer(Modifier.height(12.dp))
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
                Switch(
                    checked = estado.activa,
                    onCheckedChange = alCambiarActiva,
                    enabled = estado.conectado,
                )
            }

            Spacer(Modifier.height(12.dp))

            OutlinedButton(
                onClick = alRedescubrir,
                enabled = !estado.redescubriendo,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (estado.redescubriendo) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                } else {
                    Icon(Icons.Filled.Refresh, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Buscar de nuevo")
                }
            }

            Spacer(Modifier.height(8.dp))

            OutlinedButton(
                onClick = alProbar,
                enabled = !estado.probando && !estado.redescubriendo,
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

/**
 * Cambio de contraseña de la cuenta institucional.
 *
 * No se guarda nada local: la contraseña nueva viaja a la base institucional
 * a través del nodo central, que es quien la deriva y almacena.
 */
@Composable
private fun DialogoCambioPassword(
    ocupado: Boolean,
    alCambiar: (actual: String, nueva: String, confirmacion: String) -> Unit,
    alCerrar: () -> Unit,
) {
    var actual by remember { mutableStateOf("") }
    var nueva by remember { mutableStateOf("") }
    var confirmacion by remember { mutableStateOf("") }

    AlertDialog(
        onDismissRequest = alCerrar,
        title = { Text("Cambiar contraseña") },
        text = {
            Column(modifier = Modifier.verticalScroll(rememberScrollState())) {
                Text(
                    text = "La contraseña se actualiza en la base institucional: " +
                        "la misma que usa en el escritorio.",
                    style = MaterialTheme.typography.bodySmall,
                )
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = actual,
                    onValueChange = { actual = it },
                    label = { Text("Contraseña actual") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = nueva,
                    onValueChange = { nueva = it },
                    label = { Text("Contraseña nueva") },
                    supportingText = { Text("Al menos 8 caracteres, con letras y números") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(
                    value = confirmacion,
                    onValueChange = { confirmacion = it },
                    label = { Text("Repita la contraseña nueva") },
                    singleLine = true,
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = {
            TextButton(
                enabled = !ocupado,
                onClick = { alCambiar(actual, nueva, confirmacion) },
            ) {
                Text("Cambiar")
            }
        },
        dismissButton = {
            TextButton(onClick = alCerrar) { Text("Cancelar") }
        },
    )
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
