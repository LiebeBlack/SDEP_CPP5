package ve.edu.sdep.movil.ui.empleados

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Save
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.ui.comun.BarraSuperior
import ve.edu.sdep.movil.ui.comun.DialogoConfirmar
import ve.edu.sdep.movil.ui.modulos.etiquetaEstado

/**
 * Alta y edición de una ficha de personal.
 *
 * Repite los mismos bloques del formulario del escritorio en una sola columna
 * desplazable: en el teléfono no cabe un formulario de tres columnas, pero no
 * falta ningún campo de dominio. Al guardar, el repositorio escribe la ficha y
 * su operación de salida en la misma transacción; la red no se toca aquí.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PantallaEmpleado(
    sesion: Sesion,
    alVolver: () -> Unit,
    vistaModelo: EmpleadoViewModel = hiltViewModel(),
) {
    val estado by vistaModelo.estado.collectAsStateWithLifecycle()
    val barra = remember { SnackbarHostState() }
    var confirmarBaja by remember { mutableStateOf(false) }

    LaunchedEffect(estado.mensaje) {
        val texto = estado.mensaje ?: return@LaunchedEffect
        barra.showSnackbar(texto)
        vistaModelo.limpiarMensaje()
    }

    LaunchedEffect(estado.guardado, estado.dadoDeBaja) {
        if (estado.guardado || estado.dadoDeBaja) alVolver()
    }

    val permiso = if (estado.id == null) Permiso.CREAR else Permiso.EDITAR
    val puedeGuardar = sesion.puede(permiso)

    Scaffold(
        topBar = {
            BarraSuperior(
                titulo = if (estado.id == null) "Nuevo empleado" else "Editar empleado",
                alVolver = alVolver,
            )
        },
        snackbarHost = { SnackbarHost(barra) },
        floatingActionButton = {
            if (puedeGuardar) {
                ExtendedFloatingActionButton(
                    onClick = vistaModelo::guardar,
                    icon = { Icon(Icons.Filled.Save, contentDescription = null) },
                    text = { Text(if (estado.guardando) "Guardando…" else "Guardar") },
                )
            }
        },
    ) { relleno ->
        if (estado.cargando) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(relleno)
                    .padding(top = 48.dp),
            ) {
                CircularProgressIndicator(modifier = Modifier.padding(horizontal = 24.dp))
            }
            return@Scaffold
        }

        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(relleno),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 8.dp, bottom = 96.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            if (estado.error != null) {
                item {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.errorContainer,
                        ),
                    ) {
                        Text(
                            text = estado.error.orEmpty(),
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            modifier = Modifier.padding(14.dp),
                        )
                    }
                }
            }

            SECCIONES.forEach { seccion ->
                item(key = "seccion-${seccion.titulo}") {
                    Text(
                        text = seccion.titulo,
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(top = 6.dp),
                    )
                }
                items(seccion.campos, key = { "${seccion.titulo}-${it.clave}" }) { campo ->
                    CampoEmpleado(
                        campo = campo,
                        valor = estado.valores[campo.clave].orEmpty(),
                        habilitado = !estado.guardando && puedeGuardar,
                        alCambiar = { vistaModelo.cambiar(campo.clave, it) },
                    )
                }
            }

            if (estado.id != null) {
                item {
                    Spacer(Modifier.height(8.dp))
                    TextButton(
                        onClick = { confirmarBaja = true },
                        enabled = sesion.puede(Permiso.ELIMINAR) && !estado.guardando,
                    ) {
                        Text(
                            text = "Dar de baja la ficha",
                            color = MaterialTheme.colorScheme.error,
                        )
                    }
                }
            }
        }
    }

    if (confirmarBaja) {
        DialogoConfirmar(
            titulo = "Dar de baja",
            mensaje = "La ficha quedará inactiva y el cambio viajará al escritorio. " +
                "No se borra su historia.",
            textoConfirmar = "Dar de baja",
            alConfirmar = {
                confirmarBaja = false
                vistaModelo.darDeBaja()
            },
            alCancelar = { confirmarBaja = false },
        )
    }
}

@Composable
private fun CampoEmpleado(
    campo: CampoFormulario,
    valor: String,
    habilitado: Boolean,
    alCambiar: (String) -> Unit,
) {
    if (campo.tipo == TipoCampo.OPCION) {
        Column {
            Text(
                text = campo.etiqueta,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                campo.opciones.forEach { opcion ->
                    FilterChip(
                        selected = valor == opcion,
                        onClick = { alCambiar(opcion) },
                        enabled = habilitado,
                        label = { Text(etiquetaEstado(opcion)) },
                    )
                }
            }
        }
        return
    }

    OutlinedTextField(
        value = valor,
        onValueChange = alCambiar,
        enabled = habilitado,
        label = { Text(campo.etiqueta) },
        placeholder = if (campo.tipo == TipoCampo.FECHA) {
            { Text("AAAA-MM-DD") }
        } else {
            null
        },
        singleLine = campo.lineas == 1,
        minLines = campo.lineas,
        keyboardOptions = when (campo.tipo) {
            TipoCampo.DECIMAL -> KeyboardOptions(keyboardType = KeyboardType.Decimal)
            else -> KeyboardOptions.Default
        },
        modifier = Modifier.fillMaxWidth(),
    )
}

// ----------------------------------------------------------------------
// Composición del formulario
// ----------------------------------------------------------------------

private enum class TipoCampo { TEXTO, DECIMAL, FECHA, OPCION }

private data class CampoFormulario(
    val clave: String,
    val etiqueta: String,
    val tipo: TipoCampo = TipoCampo.TEXTO,
    val opciones: List<String> = emptyList(),
    val lineas: Int = 1,
)

private data class SeccionFormulario(
    val titulo: String,
    val campos: List<CampoFormulario>,
)

private val SECCIONES = listOf(
    SeccionFormulario(
        titulo = "Identificación",
        campos = listOf(
            CampoFormulario("nombres", "Nombres"),
            CampoFormulario("apellidos", "Apellidos"),
            CampoFormulario("cedula", "Cédula"),
            CampoFormulario("fechaNacimiento", "Fecha de nacimiento", TipoCampo.FECHA),
            CampoFormulario(
                "genero",
                "Género",
                TipoCampo.OPCION,
                listOf("masculino", "femenino", "otro"),
            ),
            CampoFormulario(
                "estadoCivil",
                "Estado civil",
                TipoCampo.OPCION,
                listOf("soltero", "casado", "divorciado", "viudo", "union_libre"),
            ),
            CampoFormulario("nacionalidad", "Nacionalidad"),
            CampoFormulario("peso", "Peso (kg)", TipoCampo.DECIMAL),
            CampoFormulario("altura", "Altura (m)", TipoCampo.DECIMAL),
            CampoFormulario("tipoSangre", "Tipo de sangre"),
        ),
    ),
    SeccionFormulario(
        titulo = "Contacto",
        campos = listOf(
            CampoFormulario("telefono", "Teléfono"),
            CampoFormulario("celular", "Celular"),
            CampoFormulario("email", "Correo"),
            CampoFormulario("direccion", "Dirección", lineas = 2),
            CampoFormulario("ciudad", "Ciudad"),
            CampoFormulario("estado", "Estado"),
            CampoFormulario("codigoPostal", "Código postal"),
        ),
    ),
    SeccionFormulario(
        titulo = "Relación laboral",
        campos = listOf(
            CampoFormulario(
                "tipoEmpleado",
                "Tipo de empleado",
                TipoCampo.OPCION,
                listOf("docente", "administrativo", "mantenimiento"),
            ),
            CampoFormulario("cargo", "Cargo"),
            CampoFormulario("departamento", "Departamento"),
            CampoFormulario("fechaContratacion", "Fecha de contratación", TipoCampo.FECHA),
            CampoFormulario("fechaTerminacion", "Fecha de terminación", TipoCampo.FECHA),
            CampoFormulario("salarioBase", "Salario base", TipoCampo.DECIMAL),
            CampoFormulario("tipoContratacion", "Tipo de contratación"),
        ),
    ),
    SeccionFormulario(
        titulo = "Formación",
        campos = listOf(
            CampoFormulario("nivelEducativo", "Nivel educativo"),
            CampoFormulario("especialidad", "Especialidad"),
            CampoFormulario("tituloObtenido", "Título obtenido"),
            CampoFormulario("tituloSecundaria", "Título de secundaria"),
        ),
    ),
    SeccionFormulario(
        titulo = "Datos bancarios",
        campos = listOf(
            CampoFormulario("institucionBancaria", "Institución bancaria"),
            CampoFormulario("numeroCuenta", "Número de cuenta"),
            CampoFormulario("tipoCuenta", "Tipo de cuenta"),
        ),
    ),
    SeccionFormulario(
        titulo = "Salud",
        campos = listOf(
            CampoFormulario("carnetDiscapacidad", "Carnet de discapacidad"),
            CampoFormulario("enfermedadesPreexistentes", "Enfermedades preexistentes", lineas = 2),
            CampoFormulario("alergiasMedicamentosas", "Alergias medicamentosas", lineas = 2),
            CampoFormulario("alergiasAlimentarias", "Alergias alimentarias", lineas = 2),
        ),
    ),
    SeccionFormulario(
        titulo = "Familia y emergencia",
        campos = listOf(
            CampoFormulario("hijos", "Hijos", lineas = 2),
            CampoFormulario("contactoEmergenciaNombre", "Contacto de emergencia"),
            CampoFormulario("contactoEmergenciaTelefono", "Teléfono de emergencia"),
            CampoFormulario("contactoEmergenciaRelacion", "Relación"),
        ),
    ),
    SeccionFormulario(
        titulo = "Notas",
        campos = listOf(
            CampoFormulario("observaciones", "Observaciones", lineas = 3),
        ),
    ),
)
