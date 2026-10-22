package ve.edu.sdep.movil.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import ve.edu.sdep.movil.datos.repositorio.AutenticacionRepositorio
import ve.edu.sdep.movil.datos.repositorio.ConectorNodo
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

/**
 * Estado de la pantalla de ingreso.
 *
 * No hay dirección, equipo ni token que mostrar: el teléfono encuentra el
 * sistema de escritorio solo y guarda la vinculación cifrada. La pantalla
 * únicamente pide usuario y contraseña.
 */
data class EstadoLogin(
    val cargando: Boolean = true,
    val usuario: String = "",
    val contrasena: String = "",
    /** Hay vinculación completa con el sistema de escritorio */
    val conectado: Boolean = false,
    /** La búsqueda del escritorio está en curso */
    val conectando: Boolean = false,
    val error: String? = null,
    val ocupado: Boolean = false,
    val biometriaGuardada: Boolean = false,
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val autenticacion: AutenticacionRepositorio,
    private val conector: ConectorNodo,
) : ViewModel() {

    private val _estado = MutableStateFlow(EstadoLogin())
    val estado: StateFlow<EstadoLogin> = _estado.asStateFlow()

    init {
        viewModelScope.launch {
            val biometria = withContext(Dispatchers.IO) { autenticacion.hayCredencialBiometrica() }
            // El formulario aparece de inmediato: la búsqueda del escritorio
            // corre en paralelo y se informa en la franja de estado. Así una
            // red lenta nunca deja al usuario mirando un indicador sin poder
            // escribir su usuario.
            _estado.update {
                it.copy(cargando = false, conectando = true, biometriaGuardada = biometria)
            }
            val config = conector.asegurarConexion()
            _estado.update {
                it.copy(
                    conectado = config is Resultado.Exito,
                    conectando = false,
                    error = (config as? Resultado.Fallo)?.mensaje,
                )
            }
            // Si no se encontró al primer intento, se sigue intentando en
            // segundo plano mientras el usuario escribe sus credenciales. La
            // espera interna del conector evita recorrer la red sin pausa.
            if (config is Resultado.Fallo) buscarNodoAutomaticamente()
        }
    }

    fun cambiarUsuario(valor: String) = _estado.update { it.copy(usuario = valor, error = null) }

    fun cambiarContrasena(valor: String) = _estado.update { it.copy(contrasena = valor, error = null) }

    fun registrarError(mensaje: String) = _estado.update { it.copy(error = mensaje, ocupado = false) }

    fun limpiarError() = _estado.update { it.copy(error = null) }

    /**
     * Relee si hay una credencial biométrica guardada.
     *
     * Se llama cada vez que se abre la pantalla: el usuario pudo activar la
     * huella en Ajustes después del último ingreso, o desactivarla.
     */
    fun refrescarBiometria() {
        viewModelScope.launch {
            val biometria = withContext(Dispatchers.IO) { autenticacion.hayCredencialBiometrica() }
            _estado.update { it.copy(biometriaGuardada = biometria) }
        }
    }

    /**
     * Vuelve a buscar el sistema de escritorio.
     *
     * Es el único «reintento» visible: no pide datos, solo repite el
     * descubrimiento por si el equipo se encendió después o cambió de IP.
     */
    fun reintentarConexion() {
        if (_estado.value.conectando) return
        viewModelScope.launch {
            _estado.update { it.copy(conectando = true, error = null, conectado = false) }
            when (val resultado = conector.asegurarConexion(forzar = true)) {
                is Resultado.Exito -> _estado.update {
                    it.copy(conectando = false, conectado = true, error = null)
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(conectando = false, conectado = false, error = resultado.mensaje)
                }
            }
        }
    }

    /**
     * Búsqueda silenciosa en segundo plano cuando la primera no encontró nada.
     *
     * No bloquea la pantalla ni muestra un formulario: si el escritorio se
     * abre unos segundos después, el ingreso queda listo sin que el usuario
     * haga nada.
     */
    private fun buscarNodoAutomaticamente() {
        viewModelScope.launch {
            repeat(INTENTOS_AUTOMATICOS) { intento ->
                if (_estado.value.conectado) return@launch
                // Espera creciente (4 s, 8 s, 12 s): cada reintento recorre la
                // red y enciende la radio, así que espaciarlos reduce el
                // consumo de batería sin dejar de encontrar el escritorio que
                // se abre unos segundos después.
                withContext(Dispatchers.IO) {
                    kotlinx.coroutines.delay(PAUSA_AUTOMATICA_MS * (intento + 1))
                }
                if (_estado.value.conectado) return@launch
                _estado.update { it.copy(conectando = true) }
                // Cada reintento busca de verdad: la espera creciente ya
                // separa los intentos y la franja muestra que sigue buscando.
                when (val resultado = conector.asegurarConexion(forzar = true)) {
                    is Resultado.Exito -> {
                        _estado.update {
                            it.copy(conectado = true, conectando = false, error = null)
                        }
                        return@launch
                    }

                    is Resultado.Fallo -> _estado.update {
                        it.copy(conectado = false, conectando = false, error = resultado.mensaje)
                    }
                }
            }
        }
    }

    /** Ingreso con usuario y contraseña de la base institucional */
    fun entrar(activarBiometria: Boolean) {
        val actual = _estado.value
        if (actual.ocupado) return
        if (actual.usuario.isBlank() || actual.contrasena.isEmpty()) {
            _estado.update { it.copy(error = "Escriba su usuario y su contraseña.") }
            return
        }
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true, error = null, conectando = !it.conectado) }

            // Sin vinculación no hay nada que autenticar: se busca el
            // escritorio en este mismo gesto, sin pedirle datos al usuario.
            val conexion = conector.asegurarConexion(forzar = true)
            if (conexion is Resultado.Fallo) {
                _estado.update {
                    it.copy(
                        ocupado = false,
                        conectando = false,
                        conectado = false,
                        error = conexion.mensaje,
                    )
                }
                return@launch
            }
            _estado.update { it.copy(conectado = true, conectando = false) }

            var resultado = autenticacion.entrar(
                usuario = actual.usuario,
                contrasena = actual.contrasena,
                activarBiometria = activarBiometria,
            )

            // Un fallo de red con una vinculación vieja suele significar que el
            // escritorio cambió de IP. Se renueva la vinculación y se reintenta
            // una sola vez, sin mostrar formularios.
            if (resultado is Resultado.Fallo && resultado.reintentable) {
                val renovada = conector.revincular()
                if (renovada is Resultado.Exito) {
                    resultado = autenticacion.entrar(
                        usuario = actual.usuario,
                        contrasena = actual.contrasena,
                        activarBiometria = activarBiometria,
                    )
                }
            }

            when (resultado) {
                is Resultado.Exito -> _estado.update {
                    it.copy(
                        ocupado = false,
                        conectando = false,
                        contrasena = "",
                        error = null,
                        biometriaGuardada = activarBiometria || it.biometriaGuardada,
                    )
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(ocupado = false, conectando = false, error = resultado.mensaje)
                }
            }
        }
    }

    /** Se llama cuando el sensor biométrico ya confirmó al usuario */
    fun entrarConBiometria() {
        if (_estado.value.ocupado) return
        viewModelScope.launch {
            _estado.update { it.copy(ocupado = true, error = null) }

            if (!_estado.value.conectado) {
                val conexion = conector.asegurarConexion(forzar = true)
                if (conexion is Resultado.Fallo) {
                    _estado.update {
                        it.copy(ocupado = false, error = conexion.mensaje)
                    }
                    return@launch
                }
                _estado.update { it.copy(conectado = true) }
            }

            var resultado = autenticacion.entrarConBiometria()
            if (resultado is Resultado.Fallo && resultado.reintentable) {
                val renovada = conector.revincular()
                if (renovada is Resultado.Exito) {
                    resultado = autenticacion.entrarConBiometria()
                }
            }

            when (resultado) {
                is Resultado.Exito -> _estado.update { it.copy(ocupado = false) }
                is Resultado.Fallo -> _estado.update {
                    it.copy(ocupado = false, error = resultado.mensaje, biometriaGuardada = false)
                }
            }
        }
    }

    private companion object {
        const val INTENTOS_AUTOMATICOS = 3
        const val PAUSA_AUTOMATICA_MS = 4_000L
    }
}
