package ve.edu.sdep.movil.ui.modulos

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import ve.edu.sdep.movil.datos.local.entidad.ContratoEntity
import ve.edu.sdep.movil.datos.local.entidad.IncidenciaEntity
import ve.edu.sdep.movil.datos.repositorio.AccionesLaboralesRepositorio
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Resultado
import javax.inject.Inject

/**
 * Estado de las acciones que se pueden ejecutar desde una ficha.
 *
 * La pantalla aporta el módulo y el id local; este ViewModel resuelve la fila
 * para decidir qué botones mostrar y llama al repositorio, que es quien habla
 * con el nodo central. Tras una acción correcta se vuelve a leer la fila para
 * ocultar la acción ya consumida y mostrar el estado nuevo.
 */
@HiltViewModel
class AccionesLaboralesViewModel @Inject constructor(
    private val repositorio: AccionesLaboralesRepositorio,
) : ViewModel() {

    data class Estado(
        val incidencia: IncidenciaEntity? = null,
        val contrato: ContratoEntity? = null,
        val conectado: Boolean = false,
        val cargando: Boolean = true,
        val ejecutando: Boolean = false,
        val mensaje: String? = null,
        val error: String? = null,
    )

    private val _estado = MutableStateFlow(Estado())
    val estado: StateFlow<Estado> = _estado.asStateFlow()

    private var cargadaPara: Pair<Modulo, Long>? = null

    fun cargar(modulo: Modulo?, id: Long, forzar: Boolean = false) {
        if (modulo != Modulo.INCIDENCIAS && modulo != Modulo.CONTRATOS) return
        if (id <= 0L) return
        if (!forzar && cargadaPara == (modulo to id)) return
        cargadaPara = modulo to id
        viewModelScope.launch {
            _estado.update { it.copy(cargando = true, error = null) }
            try {
                val conectado = repositorio.hayConexion()
                val incidencia = if (modulo == Modulo.INCIDENCIAS) {
                    repositorio.cargarIncidencia(id)
                } else {
                    null
                }
                val contrato = if (modulo == Modulo.CONTRATOS) {
                    repositorio.cargarContrato(id)
                } else {
                    null
                }
                _estado.update {
                    it.copy(
                        incidencia = incidencia,
                        contrato = contrato,
                        conectado = conectado,
                        cargando = false,
                    )
                }
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (error: Exception) {
                _estado.update {
                    it.copy(
                        cargando = false,
                        error = error.message
                            ?: "No se pudo preparar la ficha para ejecutar acciones.",
                    )
                }
            }
        }
    }

    fun aprobar(id: Long, comentarios: String?, diasAprobados: Int?) {
        ejecutar(Modulo.INCIDENCIAS, id, "Incidencia aprobada.") {
            repositorio.aprobarIncidencia(id, comentarios, diasAprobados)
        }
    }

    fun rechazar(id: Long, comentarios: String?) {
        ejecutar(Modulo.INCIDENCIAS, id, "Incidencia rechazada.") {
            repositorio.rechazarIncidencia(id, comentarios)
        }
    }

    fun renovar(
        id: Long,
        nuevaFechaFin: String,
        nuevoSalario: Double?,
        tipo: String?,
        clausulas: String?,
    ) {
        ejecutar(Modulo.CONTRATOS, id, "Contrato renovado.") {
            repositorio.renovarContrato(id, nuevaFechaFin, nuevoSalario, tipo, clausulas)
        }
    }

    fun terminar(
        id: Long,
        motivo: String,
        fechaTerminacion: String?,
        generarLiquidacion: Boolean,
        metodoPago: String?,
    ) {
        ejecutar(Modulo.CONTRATOS, id, "Contrato terminado y liquidación registrada.") {
            repositorio.terminarContrato(
                id = id,
                motivo = motivo,
                fechaTerminacion = fechaTerminacion,
                generarLiquidacion = generarLiquidacion,
                metodoPago = metodoPago,
            )
        }
    }

    fun limpiarMensaje() {
        _estado.update { it.copy(mensaje = null, error = null) }
    }

    private fun ejecutar(
        modulo: Modulo,
        id: Long,
        mensajeExito: String,
        accion: suspend () -> Resultado<Unit>,
    ) {
        if (_estado.value.ejecutando) return
        _estado.update { it.copy(ejecutando = true, error = null, mensaje = null) }
        viewModelScope.launch {
            val resultado = try {
                accion()
            } catch (cancelacion: CancellationException) {
                throw cancelacion
            } catch (error: Exception) {
                Resultado.Fallo(
                    error.message ?: "No se pudo completar la acción.",
                    error,
                )
            }
            when (resultado) {
                is Resultado.Exito -> {
                    _estado.update { it.copy(ejecutando = false, mensaje = mensajeExito) }
                    cargar(modulo, id, forzar = true)
                }

                is Resultado.Fallo -> _estado.update {
                    it.copy(ejecutando = false, error = resultado.mensaje)
                }
            }
        }
    }
}
