package ve.edu.sdep.movil.ui.formulario

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.local.ColumnaTabla
import ve.edu.sdep.movil.datos.local.EsquemaTabla
import ve.edu.sdep.movil.datos.local.OpcionTabla
import ve.edu.sdep.movil.datos.local.TipoCampo
import ve.edu.sdep.movil.datos.repositorio.SesionRepositorio
import ve.edu.sdep.movil.datos.repositorio.TablaRepositorio
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Resultado
import ve.edu.sdep.movil.sincronizacion.ProgramadorSync
import javax.inject.Inject

/**
 * Estado del formulario dinámico de una tabla.
 *
 * No conoce ninguna tabla concreta: pide las columnas al repositorio, pide la
 * fila si se está editando y guarda con el mismo motor genérico. Los permisos
 * se resuelven aquí para que la pantalla solo dibuje lo que el rol permite.
 */
@HiltViewModel
class FormularioViewModel @Inject constructor(
    private val repositorio: TablaRepositorio,
    private val sesionRepositorio: SesionRepositorio,
    private val programadorSync: ProgramadorSync,
) : ViewModel() {

    data class Estado(
        val tabla: String = "",
        val titulo: String = "",
        val id: Long? = null,
        val campos: List<ColumnaTabla> = emptyList(),
        val valores: Map<String, String> = emptyMap(),
        val opcionesForaneas: Map<String, List<OpcionTabla>> = emptyMap(),
        val cargando: Boolean = true,
        val guardando: Boolean = false,
        val error: String? = null,
        val guardado: Boolean = false,
        val eliminado: Boolean = false,
        val puedeEscribir: Boolean = false,
        val puedeEliminar: Boolean = false,
        val confirmarBorrado: Boolean = false,
        val noDisponible: String? = null,
    ) {
        val esAlta: Boolean get() = id == null
    }

    private val _estado = MutableStateFlow(Estado())
    val estado: StateFlow<Estado> = _estado.asStateFlow()

    /** Evita recargar dos veces la misma ficha al recomponer la pantalla */
    private var cargadaPara: Pair<String, Long?>? = null

    fun cargar(tabla: String, id: Long?) {
        if (cargadaPara == (tabla to id)) return
        cargadaPara = tabla to id
        viewModelScope.launch {
            _estado.update {
                it.copy(
                    tabla = tabla,
                    titulo = EsquemaTabla.titulo(tabla),
                    id = id,
                    cargando = true,
                    error = null,
                )
            }
            val sesion = sesionRepositorio.actual
            val modulo = EsquemaTabla.moduloDeTabla(tabla)
            if (sesion == null || modulo == null || !sesion.puedeAbrir(modulo)) {
                _estado.update {
                    it.copy(
                        cargando = false,
                        noDisponible = "Su rol no tiene acceso a este módulo.",
                    )
                }
                return@launch
            }
            val campos = repositorio.columnas(tabla)
            if (campos.isEmpty()) {
                _estado.update {
                    it.copy(cargando = false, noDisponible = "La tabla no admite edición.")
                }
                return@launch
            }
            val opciones = buildMap {
                campos.mapNotNull { campo -> campo.tablaForanea }.distinct().forEach { padre ->
                    put(padre, repositorio.opcionesForaneas(padre))
                }
            }
            val actual = id?.let { repositorio.cargar(tabla, it) }
            if (id != null && actual == null) {
                _estado.update {
                    it.copy(
                        cargando = false,
                        noDisponible = "El registro ya no existe en este equipo. " +
                            "Sincronice e intente de nuevo.",
                    )
                }
                return@launch
            }
            val valores = campos.associate { campo ->
                campo.nombre to (actual?.get(campo.nombre) ?: predeterminado(campo))
            }
            _estado.update {
                it.copy(
                    campos = campos,
                    valores = valores,
                    opcionesForaneas = opciones,
                    cargando = false,
                    puedeEscribir = sesion.puede(
                        if (id == null) Permiso.CREAR else Permiso.EDITAR,
                    ),
                    puedeEliminar = id != null && sesion.puede(Permiso.ELIMINAR),
                )
            }
        }
    }

    fun cambiar(campo: String, valor: String) {
        _estado.update { it.copy(valores = it.valores + (campo to valor), error = null) }
    }

    fun guardar() {
        val actual = _estado.value
        if (actual.guardando) return
        _estado.update { it.copy(guardando = true, error = null) }
        viewModelScope.launch {
            when (val resultado = repositorio.guardar(actual.tabla, actual.id, actual.valores)) {
                is Resultado.Exito -> {
                    // El cambio ya está en la cola: se pide el ciclo de subida
                    // sin esperar al periodo automático.
                    programadorSync.sincronizarAhora()
                    _estado.update { it.copy(guardando = false, guardado = true) }
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(guardando = false, error = resultado.mensaje)
                }
            }
        }
    }

    fun pedirConfirmacionBorrado() {
        _estado.update { it.copy(confirmarBorrado = true) }
    }

    fun cancelarBorrado() {
        _estado.update { it.copy(confirmarBorrado = false) }
    }

    fun eliminar() {
        val actual = _estado.value
        val id = actual.id ?: return
        _estado.update { it.copy(confirmarBorrado = false, guardando = true, error = null) }
        viewModelScope.launch {
            when (val resultado = repositorio.eliminar(actual.tabla, id)) {
                is Resultado.Exito -> {
                    programadorSync.sincronizarAhora()
                    _estado.update { it.copy(guardando = false, eliminado = true) }
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(guardando = false, error = resultado.mensaje)
                }
            }
        }
    }

    /** Valor inicial de un alta: los indicadores de estado nacen activos */
    private fun predeterminado(campo: ColumnaTabla): String = when {
        campo.tipo == TipoCampo.BOOLEANO ->
            if (campo.nombre == "activo" || campo.nombre == "activa") "1" else "0"

        else -> ""
    }
}
