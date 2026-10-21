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
 * En el primer arranque pide crear la cuenta administradora; después, usuario y
 * contraseña, con la opción de desbloquear con huella una vez que se habilitó.
 * La pantalla no navega: cuando la sesión se abre, la raíz de la aplicación
 * cambia sola.
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

                !estado.hayCuentas -> FormularioInicial(
                    estado = estado,
                    alCambiarNombre = vistaModelo::cambiarNombre,
                    alCambiarUsuario = vistaModelo::cambiarUsuario,
                    alCambiarContrasena = vistaModelo::cambiarContrasena,
                    alCambiarConfirmacion = vistaModelo::cambiarConfirmacion,
                    alCrear = vistaModelo::crearAdministrador,
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

@Composable
private fun FormularioInicial(
    estado: EstadoLogin,
    alCambiarNombre: (String) -> Unit,
    alCambiarUsuario: (String) -> Unit,
    alCambiarContrasena: (String) -> Unit,
    alCambiarConfirmacion: (String) -> Unit,
    alCrear: () -> Unit,
) {
    Text(
        text = "Configuración inicial",
        style = MaterialTheme.typography.titleMedium,
        fontWeight = FontWeight.SemiBold,
    )
    Spacer(Modifier.height(4.dp))
    Text(
        text = "Cree la cuenta administradora de este teléfono. Desde ella podrá " +
            "agregar editores, lectores y configurar la conexión con la intranet.",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        textAlign = TextAlign.Center,
    )

    Spacer(Modifier.height(20.dp))

    OutlinedTextField(
        value = estado.nombre,
        onValueChange = alCambiarNombre,
        label = { Text("Nombre y apellido") },
        singleLine = true,
        modifier = Modifier.fillMaxWidth(),
    )
    Spacer(Modifier.height(12.dp))
    OutlinedTextField(
        value = estado.usuario,
        onValueChange = alCambiarUsuario,
        label = { Text("Usuario") },
        supportingText = { Text("Letras, números, punto, guion o guion bajo") },
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
        ayuda = "Al menos 8 caracteres, con letras y números",
        imeAction = ImeAction.Next,
    )
    Spacer(Modifier.height(12.dp))
    CampoContrasena(
        valor = estado.confirmacion,
        alCambiar = alCambiarConfirmacion,
        etiqueta = "Repita la contraseña",
        imeAction = ImeAction.Done,
        alEnviar = alCrear,
    )

    MensajeError(estado.error)

    Spacer(Modifier.height(20.dp))
    Button(
        onClick = alCrear,
        enabled = !estado.ocupado,
        modifier = Modifier
            .fillMaxWidth()
            .height(52.dp),
    ) {
        if (estado.ocupado) {
            CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
        } else {
            Text("Crear cuenta administradora")
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
                    "Se guarda una llave cifrada, no su contraseña",
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
        text = "Las cuentas son de este teléfono. Si olvida la contraseña, un " +
            "administrador debe crearle otra cuenta desde Ajustes.",
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
