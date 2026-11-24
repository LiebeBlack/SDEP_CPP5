package ve.edu.sdep.movil.ui.modulos

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.repositorio.AdjuntosRepositorio
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

/**
 * Estado del adjunto de una ficha (documento o incidencia).
 *
 * La ficha aporta la tabla y el id local; este ViewModel consulta el
 * repositorio de adjuntos, que decide permisos y guarda contra el espejo.
 * `bytes` es el contenido listo para abrir o compartir; se consume al usarlo
 * para no conservar megas en el estado de la pantalla.
 */
@HiltViewModel
class AdjuntosViewModel @Inject constructor(
    private val adjuntos: AdjuntosRepositorio,
) : ViewModel() {

    data class Estado(
        val tabla: String? = null,
        val id: Long? = null,
        val adjunto: AdjuntosRepositorio.Adjunto? = null,
        val cargando: Boolean = true,
        val adjuntando: Boolean = false,
        val contenido: ByteArray? = null,
        val compartirContenido: Boolean = false,
        val mensaje: String? = null,
        val error: String? = null,
    )

    private val _estado = MutableStateFlow(Estado())
    val estado: StateFlow<Estado> = _estado.asStateFlow()

    private var cargadoPara: Pair<String, Long>? = null
    private var cargaJob: Job? = null

    fun cargar(tabla: String, id: Long) {
        if (cargadoPara == (tabla to id) && !_estado.value.cargando) return
        cargadoPara = tabla to id
        cargaJob?.cancel()
        _estado.update {
            it.copy(
                tabla = tabla,
                id = id,
                adjunto = null,
                cargando = true,
                adjuntando = false,
                contenido = null,
                compartirContenido = false,
                mensaje = null,
                error = null,
            )
        }
        cargaJob = viewModelScope.launch {
            when (val base = adjuntos.estado(tabla, id)) {
                is Resultado.Exito -> _estado.update {
                    if (it.tabla == tabla && it.id == id) it.copy(adjunto = base.valor, cargando = false)
                    else it
                }
                is Resultado.Fallo -> _estado.update {
                    if (it.tabla == tabla && it.id == id) it.copy(cargando = false, error = base.mensaje)
                    else it
                }
            }
        }
    }

    /** Adjunta o reemplaza el archivo de la ficha activa */
    fun adjuntar(nombre: String, mime: String?, bytes: ByteArray) {
        val tabla = _estado.value.tabla ?: return
        val id = _estado.value.id ?: return
        viewModelScope.launch {
            actualizarSiFicha(tabla, id) {
                it.copy(adjuntando = true, mensaje = null, error = null)
            }
            try {
                when (val r = adjuntos.adjuntar(tabla, id, nombre, mime, bytes)) {
                    is Resultado.Exito -> {
                        val nuevo = (adjuntos.estado(tabla, id) as? Resultado.Exito)?.valor
                        actualizarSiFicha(tabla, id) {
                            it.copy(
                                adjuntando = false,
                                adjunto = nuevo,
                                mensaje = "Archivo adjunto. Se sincronizará con el nodo central.",
                            )
                        }
                    }
                    is Resultado.Fallo -> actualizarSiFicha(tabla, id) {
                        it.copy(adjuntando = false, error = r.mensaje)
                    }
                }
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (error: Exception) {
                actualizarSiFicha(tabla, id) {
                    it.copy(
                        adjuntando = false,
                        error = error.message ?: "No se pudo adjuntar el archivo.",
                    )
                }
            }
        }
    }

    /** Trae el contenido local para abrir o compartir */
    fun pedirContenido(compartir: Boolean = false) {
        val tabla = _estado.value.tabla ?: return
        val id = _estado.value.id ?: return
        viewModelScope.launch {
            when (val r = adjuntos.contenido(tabla, id)) {
                is Resultado.Exito -> actualizarSiFicha(tabla, id) {
                    it.copy(
                        adjunto = r.valor.first,
                        contenido = r.valor.second,
                        compartirContenido = compartir,
                        error = null,
                    )
                }
                is Resultado.Fallo -> actualizarSiFicha(tabla, id) {
                    it.copy(error = r.mensaje)
                }
            }
        }
    }

    private fun actualizarSiFicha(
        tabla: String,
        id: Long,
        transformar: (Estado) -> Estado,
    ) {
        _estado.update { actual ->
            if (actual.tabla == tabla && actual.id == id) transformar(actual) else actual
        }
    }

    fun limpiarMensaje() = _estado.update { it.copy(mensaje = null) }

    fun limpiarError() = _estado.update { it.copy(error = null) }

    /** Libera el contenido ya mostrado; se vuelve a pedir si hace falta */
    fun consumirContenido() = _estado.update {
        it.copy(contenido = null, compartirContenido = false)
    }
}
