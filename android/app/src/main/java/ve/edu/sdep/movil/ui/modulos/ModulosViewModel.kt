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
import ve.edu.sdep.movil.datos.repositorio.SesionRepositorio
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.dominio.modelo.normalizarCedula
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
    sesionRepositorio: SesionRepositorio,
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

    private data class GrupoCatalogo(
        val personal: GrupoPersonal,
        val laboral: GrupoLaboral,
        val academico: GrupoAcademico,
        val sesion: Sesion?,
    )

    private val personal = combine(
        empleadoDao.observarTodos(),
        documentoDao.observarParaListado(),
        incidenciaDao.observarParaListado(),
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

    val catalogo: StateFlow<Catalogo> = combine(
        combine(personal, laboral, academico) { personas, trabajo, academia ->
            Triple(personas, trabajo, academia)
        },
        sesionRepositorio.sesion,
    ) { grupos, sesion ->
        val (personas, trabajo, academia) = grupos
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
            ).visiblePara(sesion),
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = Catalogo(Datos()),
    )

    /**
     * Recorta el espejo a la frontera de la sesión.
     *
     * Las pantallas de consulta leen Room directamente (no pasan por
     * [TablaRepositorio]), así que el filtro de cédula tiene que aplicarse aquí
     * también. Sin él, una cuenta de trabajador podía ver en la lista todos los
     * empleados, documentos e incidencias del equipo aunque las escrituras ya
     * estuvieran restringidas. Los módulos institucionales (académico, nómina y
     * contratos) no se ofrecen al trabajador y aquí tampoco se exponen.
     */
    private fun Datos.visiblePara(sesion: Sesion?): Datos {
        if (sesion?.esTrabajador != true) return this
        val cedula = sesion.cedulaNormalizada
        val propios: List<EmpleadoEntity> = if (cedula.isBlank()) {
            emptyList()
        } else {
            empleados.filter { normalizarCedula(it.cedula) == cedula }
        }
        val idsPropios = propios.map { it.id }.toSet()
        return copy(
            empleados = propios,
            documentos = documentos.filter { it.empleadoId in idsPropios },
            incidencias = incidencias.filter { it.empleadoId in idsPropios },
            contratos = emptyList(),
            pagos = emptyList(),
            estudiantes = emptyList(),
            periodos = emptyList(),
            grados = emptyList(),
            matriculas = emptyList(),
            notas = emptyList(),
            configuraciones = emptyList(),
        )
    }
}
