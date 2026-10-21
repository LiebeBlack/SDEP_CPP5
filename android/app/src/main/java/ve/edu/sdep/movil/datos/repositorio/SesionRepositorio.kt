package ve.edu.sdep.movil.datos.repositorio

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import ve.edu.sdep.movil.dominio.modelo.Sesion
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Sesión abierta.
 *
 * Vive solo en memoria: al cerrar la aplicación hay que volver a entrar. Es
 * deliberado. Los registros son datos personales y dejar la sesión abierta en
 * un teléfono que se presta o se pierde es un riesgo mayor que la molestia de
 * escribir la contraseña; para eso está el desbloqueo con huella.
 */
@Singleton
class SesionRepositorio @Inject constructor() {

    private val _sesion = MutableStateFlow<Sesion?>(null)
    val sesion: StateFlow<Sesion?> = _sesion.asStateFlow()

    /** Sesión actual, o null si nadie entró */
    val actual: Sesion? get() = _sesion.value

    fun iniciar(sesion: Sesion) {
        _sesion.value = sesion
    }

    fun cerrar() {
        _sesion.value = null
    }
}
