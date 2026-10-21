package ve.edu.sdep.movil.ui.sesion

import androidx.lifecycle.ViewModel
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.StateFlow
import ve.edu.sdep.movil.datos.repositorio.SesionRepositorio
import ve.edu.sdep.movil.dominio.modelo.Sesion
import javax.inject.Inject

/** Sesión abierta, observada por la navegación raíz */
@HiltViewModel
class SesionViewModel @Inject constructor(
    private val repositorio: SesionRepositorio,
) : ViewModel() {

    val sesion: StateFlow<Sesion?> = repositorio.sesion

    fun salir() {
        repositorio.cerrar()
    }
}
