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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Fingerprint
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.SyncProblem
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
import androidx.compose.material3.TextButton
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
 * La pantalla no tiene ninguna configuración de red: el teléfono busca el
 * sistema de escritorio por sí solo (difusión UDP y, si hace falta, sondeo de
 * la red) y se empareja. Cuando lo encuentra, el ingreso es con el usuario y la
 * contraseña de la base institucional, las mismas cuentas del escritorio, con
 * la opción de desbloquear con huella.
 *
 * Si el escritorio aún no aparece, se muestra un aviso y un botón para volver a
 * buscar; nunca campos de IP, equipo o token. La pantalla no navega: cuando la
 * sesión se abre, la raíz de la aplicación cambia sola.
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

            Spacer(Modifier.height(24.dp))

            EstadoConexion(
                estado = estado,
                alReintentar = vistaModelo::reintentarConexion,
            )

            Spacer(Modifier.height(20.dp))

            if (estado.cargando) {
                CircularProgressIndicator()
            } else {
                FormularioIngreso(
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
 * Estado de la vinculación automática.
 *
 * Nunca expone datos que el usuario deba completar: solo informa si el
 * escritorio ya está disponible, si se está buscando o si hay que reintentar.
 */
@Composable
private fun EstadoConexion(estado: EstadoLogin, alReintentar: () -> Unit) {
    when {
        estado.cargando || estado.conectando -> {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                Spacer(Modifier.width(10.dp))
                Text(
                    text = "Buscando el sistema de escritorio…",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        !estado.conectado -> {
            Surface(
                color = MaterialTheme.colorScheme.tertiaryContainer,
                shape = MaterialTheme.shapes.medium,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(14.dp)) {
                    Row(verticalAlignment = Alignment.Top) {
                        Icon(
                            imageVector = Icons.Filled.SyncProblem,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onTertiaryContainer,
                            modifier = Modifier.size(20.dp),
                        )
                        Spacer(Modifier.width(10.dp))
                        Text(
                            text = estado.error
                                ?: "Aún no se encontró el sistema de escritorio en esta red.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onTertiaryContainer,
                        )
                    }
                    TextButton(
                        onClick = alReintentar,
                        modifier = Modifier.align(Alignment.End),
                    ) {
                        Text("Volver a buscar")
                    }
                }
            }
        }

        else -> {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    imageVector = Icons.Filled.CheckCircle,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(16.dp),
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = "Sistema de escritorio disponible",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
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
        enabled = !estado.ocupado,
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
        habilitado = !estado.ocupado,
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

    // Los fallos de conexión ya se explican en la tarjeta superior; aquí solo
    // se muestran los del ingreso (usuario, contraseña, cuenta bloqueada).
    MensajeError(estado.error.takeIf { estado.conectado })

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
            Text(if (estado.conectado) "Entrar" else "Buscar y entrar")
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
    habilitado: Boolean = true,
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
        enabled = habilitado,
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
