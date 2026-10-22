package ve.edu.sdep.movil.ui.empleados

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity
import ve.edu.sdep.movil.datos.repositorio.EmpleadoRepositorio
import ve.edu.sdep.movil.datos.repositorio.SesionRepositorio
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

/** Estado del formulario de una ficha de personal */
data class EstadoEmpleado(
    val id: Long? = null,
    val valores: Map<String, String> = emptyMap(),
    val activo: Int = 1,
    val cargando: Boolean = false,
    val guardando: Boolean = false,
    val error: String? = null,
    val mensaje: String? = null,
    val guardado: Boolean = false,
    val dadoDeBaja: Boolean = false,
    /** Un WORKER no puede cambiar la cédula que define su propio aislamiento. */
    val cedulaBloqueada: Boolean = false,
)

/**
 * Formulario de alta y edición de empleados.
 *
 * El ViewModel solo traduce texto a la entidad y llama al repositorio: las
 * validaciones de negocio y la transacción viven en la capa de datos, de modo
 * que una pantalla nueva no pueda saltarse las reglas.
 */
@HiltViewModel
class EmpleadoViewModel @Inject constructor(
    private val repositorio: EmpleadoRepositorio,
    private val sesionRepositorio: SesionRepositorio,
    savedStateHandle: SavedStateHandle,
) : ViewModel() {

    private val id: Long = savedStateHandle.get<Long>("id") ?: 0L
    private val trabajador = sesionRepositorio.actual?.esTrabajador == true
    private val cedulaSesion = sesionRepositorio.actual?.cedula.orEmpty()

    private val _estado = MutableStateFlow(
        EstadoEmpleado(
            id = id.takeIf { it > 0L },
            valores = if (trabajador) mapOf("cedula" to cedulaSesion) else emptyMap(),
            cargando = id > 0L,
            cedulaBloqueada = trabajador,
        ),
    )
    val estado: StateFlow<EstadoEmpleado> = _estado.asStateFlow()

    init {
        if (id > 0L) {
            viewModelScope.launch { cargar() }
        }
    }

    private suspend fun cargar() {
        val ficha = repositorio.cargar(id)
        if (ficha == null) {
            _estado.update {
                it.copy(
                    cargando = false,
                    error = "La ficha ya no está en este teléfono. Sincronice e intente de nuevo.",
                )
            }
            return
        }
        _estado.update {
            it.copy(
                valores = ficha.aValores(),
                activo = ficha.activo,
                cargando = false,
            )
        }
    }

    fun cambiar(clave: String, valor: String) {
        if (clave == "cedula" && trabajador) return
        _estado.update { actual ->
            actual.copy(valores = actual.valores + (clave to valor), error = null)
        }
    }

    fun guardar() {
        if (_estado.value.guardando || _estado.value.cargando) return
        _estado.update { it.copy(guardando = true, error = null) }
        viewModelScope.launch {
            when (val resultado = repositorio.guardar(_estado.value.id, _estado.value.aEntidad())) {
                is Resultado.Exito -> _estado.update {
                    it.copy(
                        id = resultado.valor,
                        guardando = false,
                        guardado = true,
                        mensaje = "Ficha guardada. Se enviará al escritorio en la próxima " +
                            "sincronización.",
                    )
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(guardando = false, error = resultado.mensaje)
                }
            }
        }
    }

    fun darDeBaja() {
        val actual = _estado.value
        val ficha = actual.id ?: return
        if (actual.guardando) return
        _estado.update { it.copy(guardando = true, error = null) }
        viewModelScope.launch {
            when (val resultado = repositorio.desactivar(ficha)) {
                is Resultado.Exito -> _estado.update {
                    it.copy(
                        guardando = false,
                        dadoDeBaja = true,
                        mensaje = "Ficha dada de baja. El escritorio recibirá el cambio.",
                    )
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(guardando = false, error = resultado.mensaje)
                }
            }
        }
    }

    fun limpiarMensaje() {
        _estado.update { it.copy(mensaje = null, error = null) }
    }
}

// ----------------------------------------------------------------------
// Traducción entre la ficha y el formulario
// ----------------------------------------------------------------------

private fun Map<String, String>.texto(clave: String): String? =
    this[clave]?.trim()?.takeIf { it.isNotEmpty() }

private fun Map<String, String>.decimal(clave: String): Double? =
    texto(clave)?.replace(',', '.')?.toDoubleOrNull()

private fun EmpleadoEntity.aValores(): Map<String, String> = mapOf(
    "nombres" to nombres,
    "apellidos" to apellidos,
    "cedula" to cedula,
    "fechaNacimiento" to fechaNacimiento.orEmpty(),
    "genero" to genero.orEmpty(),
    "estadoCivil" to estadoCivil.orEmpty(),
    "nacionalidad" to nacionalidad.orEmpty(),
    "peso" to (peso?.toString().orEmpty()),
    "altura" to (altura?.toString().orEmpty()),
    "tipoSangre" to tipoSangre.orEmpty(),
    "telefono" to telefono.orEmpty(),
    "celular" to celular.orEmpty(),
    "email" to email.orEmpty(),
    "direccion" to direccion.orEmpty(),
    "ciudad" to ciudad.orEmpty(),
    "estado" to estado.orEmpty(),
    "codigoPostal" to codigoPostal.orEmpty(),
    "tipoEmpleado" to tipoEmpleado,
    "cargo" to cargo,
    "departamento" to departamento,
    "fechaContratacion" to fechaContratacion,
    "fechaTerminacion" to fechaTerminacion.orEmpty(),
    "salarioBase" to salarioBase.toString(),
    "nivelEducativo" to nivelEducativo.orEmpty(),
    "especialidad" to especialidad.orEmpty(),
    "tituloObtenido" to tituloObtenido.orEmpty(),
    "tituloSecundaria" to tituloSecundaria.orEmpty(),
    "institucionBancaria" to institucionBancaria.orEmpty(),
    "numeroCuenta" to numeroCuenta.orEmpty(),
    "tipoCuenta" to tipoCuenta.orEmpty(),
    "carnetDiscapacidad" to carnetDiscapacidad.orEmpty(),
    "enfermedadesPreexistentes" to enfermedadesPreexistentes.orEmpty(),
    "alergiasMedicamentosas" to alergiasMedicamentosas.orEmpty(),
    "alergiasAlimentarias" to alergiasAlimentarias.orEmpty(),
    "tipoContratacion" to tipoContratacion.orEmpty(),
    "hijos" to hijos.orEmpty(),
    "observaciones" to observaciones.orEmpty(),
    "contactoEmergenciaNombre" to contactoEmergenciaNombre.orEmpty(),
    "contactoEmergenciaTelefono" to contactoEmergenciaTelefono.orEmpty(),
    "contactoEmergenciaRelacion" to contactoEmergenciaRelacion.orEmpty(),
)

private fun EstadoEmpleado.aEntidad(): EmpleadoEntity {
    val v = valores
    return EmpleadoEntity(
        id = id ?: 0L,
        nombres = v.texto("nombres").orEmpty(),
        apellidos = v.texto("apellidos").orEmpty(),
        cedula = v.texto("cedula").orEmpty(),
        fechaNacimiento = v.texto("fechaNacimiento"),
        genero = v.texto("genero"),
        estadoCivil = v.texto("estadoCivil"),
        nacionalidad = v.texto("nacionalidad"),
        peso = v.decimal("peso"),
        altura = v.decimal("altura"),
        tipoSangre = v.texto("tipoSangre"),
        telefono = v.texto("telefono"),
        celular = v.texto("celular"),
        email = v.texto("email"),
        direccion = v.texto("direccion"),
        ciudad = v.texto("ciudad"),
        estado = v.texto("estado"),
        codigoPostal = v.texto("codigoPostal"),
        tipoEmpleado = v.texto("tipoEmpleado").orEmpty(),
        cargo = v.texto("cargo").orEmpty(),
        departamento = v.texto("departamento").orEmpty(),
        fechaContratacion = v.texto("fechaContratacion").orEmpty(),
        fechaTerminacion = v.texto("fechaTerminacion"),
        salarioBase = v.decimal("salarioBase") ?: 0.0,
        activo = activo,
        nivelEducativo = v.texto("nivelEducativo"),
        especialidad = v.texto("especialidad"),
        tituloObtenido = v.texto("tituloObtenido"),
        tituloSecundaria = v.texto("tituloSecundaria"),
        institucionBancaria = v.texto("institucionBancaria"),
        numeroCuenta = v.texto("numeroCuenta"),
        tipoCuenta = v.texto("tipoCuenta"),
        carnetDiscapacidad = v.texto("carnetDiscapacidad"),
        enfermedadesPreexistentes = v.texto("enfermedadesPreexistentes"),
        alergiasMedicamentosas = v.texto("alergiasMedicamentosas"),
        alergiasAlimentarias = v.texto("alergiasAlimentarias"),
        tipoContratacion = v.texto("tipoContratacion"),
        hijos = v.texto("hijos"),
        observaciones = v.texto("observaciones"),
        contactoEmergenciaNombre = v.texto("contactoEmergenciaNombre"),
        contactoEmergenciaTelefono = v.texto("contactoEmergenciaTelefono"),
        contactoEmergenciaRelacion = v.texto("contactoEmergenciaRelacion"),
    )
}
