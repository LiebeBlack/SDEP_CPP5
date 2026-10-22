package ve.edu.sdep.movil.ui.modulos

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import ve.edu.sdep.movil.datos.local.dao.ConfiguracionDao
import ve.edu.sdep.movil.datos.local.dao.ContratoDao
import ve.edu.sdep.movil.datos.local.dao.DocumentoDao
import ve.edu.sdep.movil.datos.local.dao.EmpleadoDao
import ve.edu.sdep.movil.datos.local.dao.EstudianteDao
import ve.edu.sdep.movil.datos.local.dao.GradoDao
import ve.edu.sdep.movil.datos.local.dao.IncidenciaDao
import ve.edu.sdep.movil.datos.local.dao.MatriculaDao
import ve.edu.sdep.movil.datos.local.dao.NotaFinalDao
import ve.edu.sdep.movil.datos.local.dao.PagoDao
import ve.edu.sdep.movil.datos.local.dao.PeriodoAcademicoDao
import ve.edu.sdep.movil.datos.local.entidad.ContratoEntity
import ve.edu.sdep.movil.datos.local.entidad.DocumentoEntity
import ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity
import ve.edu.sdep.movil.datos.local.entidad.EstudianteEntity
import ve.edu.sdep.movil.datos.local.entidad.GradoEntity
import ve.edu.sdep.movil.datos.local.entidad.IncidenciaEntity
import ve.edu.sdep.movil.datos.local.entidad.MatriculaEntity
import ve.edu.sdep.movil.datos.local.entidad.NotaFinalEntity
import ve.edu.sdep.movil.datos.local.entidad.PagoEntity
import ve.edu.sdep.movil.datos.local.entidad.PeriodoAcademicoEntity
import ve.edu.sdep.movil.datos.local.entidad.ConfiguracionEntity
import javax.inject.Inject

/**
 * Fuente única de las vistas de consulta.
 *
 * Room ya expone cada tabla como ``Flow``: al llegar una operación del nodo
 * central (o al abrir la aplicación) la pantalla que esté abierta se vuelve a
 * pintar sola, sin botón de recargar y sin consultar la red. Este ViewModel
 * solo agrupa esos flujos en un [Catalogo] para que las pantallas no conozcan
 * los DAO ni las entidades.
 *
 * Se combinan en tres grupos porque ``combine`` admite hasta cinco flujos por
 * llamada; el resultado es el mismo: cualquier cambio en cualquiera de las
 * once tablas produce un catálogo nuevo.
 */
@HiltViewModel
class ModulosViewModel @Inject constructor(
    empleadoDao: EmpleadoDao,
    documentoDao: DocumentoDao,
    incidenciaDao: IncidenciaDao,
    contratoDao: ContratoDao,
    pagoDao: PagoDao,
    estudianteDao: EstudianteDao,
    periodoAcademicoDao: PeriodoAcademicoDao,
    gradoDao: GradoDao,
    matriculaDao: MatriculaDao,
    notaFinalDao: NotaFinalDao,
    configuracionDao: ConfiguracionDao,
) : ViewModel() {

    private data class GrupoPersonal(
        val empleados: List<EmpleadoEntity>,
        val documentos: List<DocumentoEntity>,
        val incidencias: List<IncidenciaEntity>,
    )

    private data class GrupoLaboral(
        val contratos: List<ContratoEntity>,
        val pagos: List<PagoEntity>,
        val estudiantes: List<EstudianteEntity>,
    )

    private data class GrupoAcademico(
        val periodos: List<PeriodoAcademicoEntity>,
        val grados: List<GradoEntity>,
        val matriculas: List<MatriculaEntity>,
        val notas: List<NotaFinalEntity>,
        val configuraciones: List<ConfiguracionEntity>,
    )

    private val personal = combine(
        empleadoDao.observarTodos(),
        documentoDao.observarTodos(),
        incidenciaDao.observarTodas(),
    ) { empleados, documentos, incidencias ->
        GrupoPersonal(empleados, documentos, incidencias)
    }

    private val laboral = combine(
        contratoDao.observarTodos(),
        pagoDao.observarTodos(),
        estudianteDao.observarTodos(),
    ) { contratos, pagos, estudiantes ->
        GrupoLaboral(contratos, pagos, estudiantes)
    }

    private val academico = combine(
        periodoAcademicoDao.observarTodos(),
        gradoDao.observarTodos(),
        matriculaDao.observarTodas(),
        notaFinalDao.observarTodas(),
        configuracionDao.observarTodas(),
    ) { periodos, grados, matriculas, notas, configuraciones ->
        GrupoAcademico(periodos, grados, matriculas, notas, configuraciones)
    }

    val catalogo: StateFlow<Catalogo> = combine(personal, laboral, academico) {
            personas, trabajo, academia ->
        Catalogo(
            Datos(
                empleados = personas.empleados,
                documentos = personas.documentos,
                incidencias = personas.incidencias,
                contratos = trabajo.contratos,
                pagos = trabajo.pagos,
                estudiantes = trabajo.estudiantes,
                periodos = academia.periodos,
                grados = academia.grados,
                matriculas = academia.matriculas,
                notas = academia.notas,
                configuraciones = academia.configuraciones,
            ),
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = Catalogo(Datos()),
    )
}
