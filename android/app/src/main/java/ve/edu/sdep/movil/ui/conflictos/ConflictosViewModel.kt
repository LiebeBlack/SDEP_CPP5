package ve.edu.sdep.movil.ui.conflictos

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.local.dao.ConflictoDao
import ve.edu.sdep.movil.datos.local.entidad.ConflictoEntity
import javax.inject.Inject

@HiltViewModel
class ConflictosViewModel @Inject constructor(
    private val conflictoDao: ConflictoDao,
) : ViewModel() {

    val conflictos: StateFlow<List<ConflictoEntity>> = conflictoDao.observarTodos()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = emptyList(),
        )

    fun marcarRevisado(id: Long) {
        viewModelScope.launch { conflictoDao.marcarRevisado(id) }
    }

    fun marcarTodos() {
        viewModelScope.launch { conflictoDao.marcarTodosRevisados() }
    }

    fun limpiarRevisados() {
        viewModelScope.launch { conflictoDao.purgarRevisados() }
    }
}
