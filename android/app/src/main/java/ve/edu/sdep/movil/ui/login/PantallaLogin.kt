package ve.edu.sdep.movil.ui.login

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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.fragment.app.FragmentActivity
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.datos.seguridad.AutenticadorBiometrico

/**
 * Puerta de entrada.
 *
 * Si el teléfono todavía no está vinculado al nodo central, la pantalla pide
 * primero los datos que entrega el administrador (dirección, equipo y token).
 * Con la vinculación lista, el ingreso es con usuario y contraseña de la base
 * institucional, con la opción de desbloquear con huella. La pantalla no
 * navega: cuando la sesión se abre, la raíz de la aplicación cambia sola.
 */
@Composable
fun PantallaLogin(vistaModelo: LoginViewModel = hiltViewModel()) {
    val estado by vistaModelo.estado.collectAsStateWithLifecycle()
    val contexto = LocalContext.current
    val actividad = contexto as? FragmentActivity
    val autenticador = remember { AutenticadorBiometrico() }
    val biometriaDisponible = remember(contexto) { autenticador.disponible(contexto) }
    var activarBiometria by rememberSaveable { mutableStateOf(false) }

    LaunchedEffect(Unit) { vistaModelo.refrescarBiometria() }

    fun pedirHuella() {
        if (actividad == null) {
            vistaModelo.registrarError("Este equipo no puede mostrar el diálogo biométrico.")
            return
        }
        autenticador.solicitar(
            actividad = actividad,
            titulo = "Desbloquear SDEP Móvil",
            subtitulo = "Confirme su identidad para entrar",
            alExito = { vistaModelo.entrarConBiometria() },
            alFallo = { mensaje -> vistaModelo.registrarError(mensaje) },
        )
    }

    Scaffold { relleno ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(relleno)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Encabezado()

            Spacer(Modifier.height(28.dp))

            when {
                estado.cargando -> Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 24.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    CircularProgressIndicator()
                }

                !estado.configCompleta -> FormularioVinculacion(
                    estado = estado,
                    alCambiarUrl = vistaModelo::cambiarUrl,
                    alCambiarEquipo = vistaModelo::cambiarEquipo,
                    alCambiarToken = vistaModelo::cambiarToken,
                    alGuardar = vistaModelo::guardarConfiguracion,
                    alDescubrir = vistaModelo::descubrirYVincular,
                )

                else -> FormularioIngreso(
                    estado = estado,
                    biometriaDisponible = biometriaDisponible,
                    activarBiometria = activarBiometria,
                    alCambiarActivacion = { activarBiometria = it },
                    alCambiarUsuario = vistaModelo::cambiarUsuario,
                    alCambiarContrasena = vistaModelo::cambiarContrasena,
                    alEntrar = { vistaModelo.entrar(activarBiometria) },
                    alEntrarConHuella = { pedirHuella() },
                )
            }
        }
    }
}

@Composable
private fun Encabezado() {
    Surface(
        color = MaterialTheme.colorScheme.primaryContainer,
        shape = MaterialTheme.shapes.extraLarge,
        modifier = Modifier.size(84.dp),
    ) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Icon(
                imageVector = Icons.Filled.Shield,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onPrimaryContainer,
                modifier = Modifier.size(44.dp),
            )
        }
    }
    Spacer(Modifier.height(16.dp))
    Text(
        text = "SDEP Móvil",
        style = MaterialTheme.typography.headlineMedium,
        fontWeight = FontWeight.SemiBold,
    )
    Spacer(Modifier.height(6.dp))
    Text(
        text = "Registros de campo sincronizados con el sistema de gestión de personal",
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        textAlign = TextAlign.Center,
    )
}

/**
 * Vinculación con el nodo central.
 *
 * Se muestra UNA sola vez (hasta que los tres datos queden guardados): son los
 * que el administrador entrega al dar de alta el teléfono como puesto más de
 * la intranet.
 */
@Composable
private fun FormularioVinculacion(
    estado: EstadoLogin,
    alCambiarUrl: (String) -> Unit,
    alCambiarEquipo: (String) -> Unit,
    alCambiarToken: (String) -> Unit,
    alGuardar: () -> Unit,
    alDescubrir: () -> Unit,
) {
    var tokenVisible by remember { mutableStateOf(false) }

    Text(
        text = "Conectarse al sistema de escritorio",
        style = MaterialTheme.typography.titleMedium,
        fontWeight = FontWeight.SemiBold,
    )
    Spacer(Modifier.height(4.dp))
    Text(
        text = if (estado.descubriendo) {
            "Buscando el sistema de escritorio en esta Wi-Fi…"
        } else {
            "Este teléfono se conecta al sistema de gestión de personal de la institución."
        },
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        textAlign = TextAlign.Center,
    )

    Spacer(Modifier.height(16.dp))

    // Botón de descubrimiento: mientras busca, se muestra el indicador; si
    // termina sin encontrar nada, se puede reintentar sin escribir la IP.
    OutlinedButton(
        onClick = alDescubrir,
        enabled = !estado.descubriendo,
        modifier = Modifier
            .fillMaxWidth()
            .height(52.dp),
    ) {
        if (estado.descubriendo) {
            CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
            Spacer(Modifier.size(8.dp))
            Text("Buscando…")
        } else {
            Text("Buscar el sistema automáticamente")
        }
    }

    Spacer(Modifier.height(16.dp))
    HorizontalDivider()
    Spacer(Modifier.height(16.dp))
    Text(
        text = "Escriba los datos a mano solo si no se encontró el equipo:",
        style = MaterialTheme.typography.labelMedium,
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
        enabled = !estado.descubriendo,
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Uri,
            imeAction = ImeAction.Next,
        ),
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(12.dp))
    OutlinedTextField(
        value = estado.equipo,
        onValueChange = alCambiarEquipo,
        label = { Text("Identificador del equipo") },
        supportingText = { Text("El mismo que devuelve el alta del puesto") },
        singleLine = true,
        enabled = !estado.descubriendo,
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(12.dp))
    OutlinedTextField(
        value = estado.token,
        onValueChange = alCambiarToken,
        label = { Text("Token del equipo") },
        supportingText = { Text("Se guarda cifrado en este teléfono") },
        singleLine = true,
        enabled = !estado.descubriendo,
        visualTransformation = if (tokenVisible) {
            VisualTransformation.None
        } else {
            PasswordVisualTransformation()
        },
        trailingIcon = {
            IconButton(onClick = { tokenVisible = !tokenVisible }) {
                Icon(
                    imageVector = if (tokenVisible) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                    contentDescription = if (tokenVisible) "Ocultar token" else "Mostrar token",
                )
            }
        },
        modifier = Modifier.fillMaxWidth(),
    )

    MensajeError(estado.error)

    Spacer(Modifier.height(20.dp))
    Button(
        onClick = alGuardar,
        enabled = !estado.guardandoConfig && !estado.descubriendo,
        modifier = Modifier
            .fillMaxWidth()
            .height(52.dp),
    ) {
        if (estado.guardandoConfig) {
            CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
        } else {
            Text("Guardar vinculación")
        }
    }
}

@Composable
private fun FormularioIngreso(
    estado: EstadoLogin,
    biometriaDisponible: Boolean,
    activarBiometria: Boolean,
    alCambiarActivacion: (Boolean) -> Unit,
    alCambiarUsuario: (String) -> Unit,
    alCambiarContrasena: (String) -> Unit,
    alEntrar: () -> Unit,
    alEntrarConHuella: () -> Unit,
) {
    Text(
        text = "Ingresar",
        style = MaterialTheme.typography.titleMedium,
        fontWeight = FontWeight.SemiBold,
    )
    Spacer(Modifier.height(20.dp))

    OutlinedTextField(
        value = estado.usuario,
        onValueChange = alCambiarUsuario,
        label = { Text("Usuario") },
        supportingText = { Text("La misma cuenta que usa en el escritorio") },
        singleLine = true,
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Ascii,
            imeAction = ImeAction.Next,
        ),
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(12.dp))
    CampoContrasena(
        valor = estado.contrasena,
        alCambiar = alCambiarContrasena,
        etiqueta = "Contraseña",
        imeAction = ImeAction.Done,
        alEnviar = alEntrar,
    )

    if (biometriaDisponible && !estado.biometriaGuardada) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Checkbox(checked = activarBiometria, onCheckedChange = alCambiarActivacion)
            Column {
                Text("Entrar con huella la próxima vez", style = MaterialTheme.typography.bodyMedium)
                Text(
                    text = "Se guarda una llave cifrada, no su contraseña",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }

    MensajeError(estado.error)

    Spacer(Modifier.height(20.dp))
    Button(
        onClick = alEntrar,
        enabled = !estado.ocupado,
        modifier = Modifier
            .fillMaxWidth()
            .height(52.dp),
    ) {
        if (estado.ocupado) {
            CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
        } else {
            Text("Entrar")
        }
    }

    if (biometriaDisponible && estado.biometriaGuardada) {
        Spacer(Modifier.height(12.dp))
        HorizontalDivider()
        Spacer(Modifier.height(12.dp))
        OutlinedButton(
            onClick = alEntrarConHuella,
            enabled = !estado.ocupado,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp),
        ) {
            Icon(Icons.Filled.Fingerprint, contentDescription = null)
            Spacer(Modifier.size(8.dp))
            Text("Entrar con huella")
        }
    }

    Spacer(Modifier.height(24.dp))
    Text(
        text = "Las cuentas son las de la institución, las mismas del escritorio. " +
            "Si olvida su contraseña, pida al administrador que la restablezca.",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        textAlign = TextAlign.Center,
    )
}

@Composable
private fun CampoContrasena(
    valor: String,
    alCambiar: (String) -> Unit,
    etiqueta: String,
    ayuda: String? = null,
    imeAction: ImeAction,
    alEnviar: () -> Unit = {},
) {
    var visible by remember { mutableStateOf(false) }
    OutlinedTextField(
        value = valor,
        onValueChange = alCambiar,
        label = { Text(etiqueta) },
        supportingText = if (ayuda != null) {
            { Text(ayuda) }
        } else {
            null
        },
        singleLine = true,
        visualTransformation = if (visible) {
            VisualTransformation.None
        } else {
            PasswordVisualTransformation()
        },
        keyboardOptions = KeyboardOptions(
            keyboardType = KeyboardType.Password,
            imeAction = imeAction,
        ),
        keyboardActions = KeyboardActions(onDone = { alEnviar() }),
        trailingIcon = {
            IconButton(onClick = { visible = !visible }) {
                Icon(
                    imageVector = if (visible) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                    contentDescription = if (visible) "Ocultar contraseña" else "Mostrar contraseña",
                )
            }
        },
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun MensajeError(mensaje: String?) {
    if (mensaje.isNullOrBlank()) return
    Spacer(Modifier.height(12.dp))
    Surface(
        color = MaterialTheme.colorScheme.errorContainer,
        shape = MaterialTheme.shapes.small,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(
            text = mensaje,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onErrorContainer,
            modifier = Modifier.padding(12.dp),
        )
    }
}
