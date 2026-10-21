package ve.edu.sdep.movil.datos.repositorio

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import retrofit2.HttpException
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.dao.ConflictoDao
import ve.edu.sdep.movil.datos.local.dao.EstadoSyncDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.dao.RegistroDao
import ve.edu.sdep.movil.datos.local.entidad.ConflictoEntity
import ve.edu.sdep.movil.datos.local.entidad.EstadoSyncEntity
import ve.edu.sdep.movil.datos.local.entidad.OperacionPendienteEntity
import ve.edu.sdep.movil.datos.local.entidad.RegistroEntity
import ve.edu.sdep.movil.datos.remoto.ApiSyncFactory
import ve.edu.sdep.movil.datos.remoto.ConflictoRemotoDto
import ve.edu.sdep.movil.datos.remoto.OperacionDto
import ve.edu.sdep.movil.datos.remoto.ProtocoloApi
import ve.edu.sdep.movil.datos.remoto.PushDto
import ve.edu.sdep.movil.dominio.modelo.ConfiguracionSync
import ve.edu.sdep.movil.dominio.modelo.EstadoSincronizacion
import ve.edu.sdep.movil.dominio.modelo.Resultado
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Ciclo de sincronización.
 *
 * Se ejecuta con un solo candado: dos sincronizaciones simultáneas (la
 * periódica y el botón «Sincronizar ahora») no pueden pisarse.
 *
 * El orden es siempre el mismo y no es casual:
 *
 * 1. **Enviar** lo pendiente. El nodo central arbitra y le asigna ``seq``.
 * 2. **Recibir** las novedades posteriores al cursor.
 *
 * Al enviar primero, el servidor conoce la versión de este teléfono antes de
 * devolverle nada; al recibir después, el cursor avanza solo sobre operaciones
 * ya aplicadas.
 */
@Singleton
class SincronizacionRepositorio @Inject constructor(
    private val registroDao: RegistroDao,
    private val operacionDao: OperacionDao,
    private val estadoDao: EstadoSyncDao,
    private val conflictoDao: ConflictoDao,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val apiFactory: ApiSyncFactory,
) {

    private val candado = Mutex()

    fun observarEstado(): Flow<EstadoSyncEntity?> = estadoDao.observar()

    /** Envía y recibe. No se llama desde el hilo principal. */
    suspend fun sincronizar(): Resultado<ResumenSync> = candado.withLock {
        val configuracion = configuracionRepositorio.cargar()
        if (!configuracion.completa) {
            return@withLock Resultado.Fallo(
                "Falta configurar la dirección, el equipo o el token del nodo central.",
            )
        }

        val api = try {
            apiFactory.crear(configuracion)
        } catch (error: Exception) {
            return@withLock Resultado.Fallo(
                "La dirección del servidor no es válida: «${configuracion.url}».",
                error,
            )
        }

        try {
            val enviadas = enviarPendientes(api, configuracion)
            val recibidas = recibirNovedades(api)
            val ahora = System.currentTimeMillis()
            val previo = estadoDao.obtener() ?: EstadoSyncEntity()
            estadoDao.guardar(
                previo.copy(
                    ultimaSync = ahora,
                    ultimoError = null,
                    registrosRecibidos = previo.registrosRecibidos + recibidas,
                ),
            )
            Resultado.Exito(ResumenSync(enviadas, recibidas, ahora))
        } catch (error: HttpException) {
            val mensaje = mensajeDeHttp(error)
            registrarError(mensaje)
            Resultado.Fallo(
                mensaje,
                error,
                reintentable = error.code() == 429 || error.code() >= 500,
            )
        } catch (error: IOException) {
            val mensaje = "Sin conexión con el nodo central. Los cambios quedan guardados " +
                "y se enviarán cuando vuelva la red."
            registrarError(mensaje)
            Resultado.Fallo(mensaje, error, reintentable = true)
        } catch (error: SerializationException) {
            val mensaje = "El servidor respondió algo que esta versión de la app no entiende. " +
                "Compruebe que el nodo central esté actualizado."
            registrarError(mensaje)
            Resultado.Fallo(mensaje, error)
        } catch (error: Exception) {
            val mensaje = "No se pudo completar la sincronización: ${error.message ?: "error inesperado"}."
            registrarError(mensaje)
            Resultado.Fallo(mensaje, error, reintentable = true)
        }
    }

    /**
     * Comprueba el servicio sin enviar ni recibir datos.
     *
     * Devuelve la versión del protocolo y el desfase de reloj: un teléfono con
     * la hora muy adelantada ganaría todos los conflictos de mezcla, así que
     * conviene detectarlo aquí y no en producción.
     */
    suspend fun probarConexion(): Resultado<DetalleConexion> {
        val configuracion = configuracionRepositorio.cargar()
        if (!configuracion.completa) {
            return Resultado.Fallo("Complete la dirección, el equipo y el token antes de probar.")
        }
        return try {
            val api = apiFactory.crear(configuracion)
            val ping = api.ping()
            val horaServidor = Fechas.desdeIso(ping.hora)
            val desfase = horaServidor?.let { (System.currentTimeMillis() - it) / 1000 }
            val previo = estadoDao.obtener() ?: EstadoSyncEntity()
            estadoDao.guardar(
                previo.copy(
                    servidor = ping.servidor,
                    versionProtocolo = ping.versionProtocolo,
                    desfaseSegundos = desfase,
                    ultimoError = null,
                ),
            )
            Resultado.Exito(
                DetalleConexion(
                    servidor = ping.servidor,
                    versionProtocolo = ping.versionProtocolo,
                    desfaseSegundos = desfase,
                    tablas = ping.tablas,
                ),
            )
        } catch (error: HttpException) {
            Resultado.Fallo(mensajeDeHttp(error), error)
        } catch (error: IOException) {
            Resultado.Fallo(
                "No se pudo contactar el nodo central en «${configuracion.url}». " +
                    "Compruebe que el servicio esté encendido y que el teléfono esté en la misma red.",
                error,
                reintentable = true,
            )
        } catch (error: Exception) {
            Resultado.Fallo("La prueba de conexión falló: ${error.message ?: "error inesperado"}.", error)
        }
    }

    // ------------------------------------------------------------------
    // Envío
    // ------------------------------------------------------------------
    private suspend fun enviarPendientes(
        api: ProtocoloApi,
        configuracion: ConfiguracionSync,
    ): Int {
        var enviadas = 0
        var vueltas = 0
        while (vueltas < MAX_VUELTAS) {
            val lote = operacionDao.pendientes(TAMANO_LOTE)
            if (lote.isEmpty()) break

            val respuesta = api.enviar(PushDto(configuracion.equipo, lote.map { it.aDto() }))
            if (respuesta.aplicadas.isNotEmpty()) {
                operacionDao.eliminar(respuesta.aplicadas)
            }
            respuesta.rechazadas.forEach { rechazo ->
                operacionDao.marcarRechazada(
                    rechazo.opId,
                    rechazo.motivo.ifBlank { "el servidor no indicó el motivo" },
                )
            }
            respuesta.conflictos.forEach { conflicto -> registrarConflictoRemoto(conflicto) }

            enviadas += respuesta.aplicadas.size
            vueltas++

            // Si el servidor no confirmó ni rechazó nada, insistir sería un
            // bucle inútil: se deja para el próximo ciclo.
            if (respuesta.aplicadas.isEmpty() && respuesta.rechazadas.isEmpty()) break
            if (lote.size < TAMANO_LOTE) break
        }
        return enviadas
    }

    // ------------------------------------------------------------------
    // Recepción
    // ------------------------------------------------------------------
    private suspend fun recibirNovedades(api: ProtocoloApi): Int {
        var recibidas = 0
        var cursor = estadoDao.obtener()?.cursor ?: 0
        var paginas = 0

        while (paginas < MAX_PAGINAS) {
            val respuesta = api.recibir(cursor, TAMANO_LOTE)

            if (respuesta.ops.isEmpty()) {
                if (respuesta.cursor > cursor) {
                    cursor = respuesta.cursor
                    guardarCursor(cursor)
                }
                break
            }

            for (operacion in respuesta.ops) {
                try {
                    aplicarOperacion(operacion)
                } catch (error: Exception) {
                    registrarConflictoDeAplicacion(operacion, error)
                }
                recibidas++
                if (operacion.seq > cursor) cursor = operacion.seq
            }
            if (respuesta.cursor > cursor) cursor = respuesta.cursor
            guardarCursor(cursor)

            paginas++
            if (!respuesta.hayMas) break
        }
        return recibidas
    }

    private suspend fun aplicarOperacion(operacion: OperacionDto) {
        // La app solo mantiene su propia tabla; las demás operaciones del
        // sistema se ignoran, pero el cursor sí avanza para no repedirlas.
        if (operacion.tabla != RegistroRepositorio.TABLA) return

        val local = registroDao.buscarPorUuid(operacion.filaUuid)
        val ahora = System.currentTimeMillis()

        // Hay cambios locales sin enviar: no se pisa lo que el usuario escribió.
        // La operación propia sigue en cola y el nodo central decidirá.
        if (operacionDao.pendientesDe(operacion.filaUuid) > 0) {
            conflictoDao.insertar(
                ConflictoEntity(
                    filaUuid = operacion.filaUuid,
                    titulo = local?.titulo ?: "(registro nuevo)",
                    campo = "edicion_local_pendiente",
                    valorLocal = "Cambios sin enviar",
                    valorRemoto = if (operacion.operacion == "delete") {
                        "Borrado en otro equipo"
                    } else {
                        "Edición en otro equipo"
                    },
                    momento = ahora,
                    revisado = false,
                ),
            )
            return
        }

        val momentoRemoto = Fechas.desdeIso(operacion.creadoEn) ?: ahora

        if (operacion.operacion == "delete") {
            if (local != null && !local.eliminado) {
                registroDao.insertar(
                    local.copy(
                        eliminado = true,
                        actualizadoEn = maxOf(local.actualizadoEn, momentoRemoto),
                        estado = EstadoSincronizacion.SINCRONIZADO.name,
                        ultimaSync = ahora,
                    ),
                )
            }
            return
        }

        val payload = runCatching { Json.parseToJsonElement(operacion.payload).jsonObject }
            .getOrNull() ?: return
        val texto: (String) -> String? = { campo ->
            payload[campo]?.jsonPrimitive?.contentOrNull
        }
        val numero: (String) -> Double? = { campo ->
            payload[campo]?.jsonPrimitive?.doubleOrNull
        }

        val actualizadoRemoto = Fechas.desdeIso(texto("actualizado_en")) ?: momentoRemoto
        if (local != null && actualizadoRemoto < local.actualizadoEn) {
            conflictoDao.insertar(
                ConflictoEntity(
                    filaUuid = operacion.filaUuid,
                    titulo = local.titulo,
                    campo = "escritura_antigua",
                    valorLocal = local.titulo,
                    valorRemoto = texto("titulo") ?: "(sin título)",
                    momento = ahora,
                    revisado = false,
                ),
            )
            return
        }

        registroDao.insertar(
            RegistroEntity(
                uuid = operacion.filaUuid,
                titulo = texto("titulo")?.takeIf { it.isNotBlank() }
                    ?: local?.titulo
                    ?: "(sin título)",
                contenido = texto("contenido") ?: local?.contenido ?: "",
                categoria = texto("categoria") ?: local?.categoria ?: "general",
                valor = if (payload.containsKey("valor")) numero("valor") else local?.valor,
                creadoEn = Fechas.desdeIso(texto("creado_en"))
                    ?: local?.creadoEn
                    ?: actualizadoRemoto,
                actualizadoEn = actualizadoRemoto,
                estado = EstadoSincronizacion.SINCRONIZADO.name,
                eliminado = false,
                dispositivo = texto("dispositivo") ?: local?.dispositivo ?: "remoto",
                usuario = texto("usuario") ?: local?.usuario ?: "remoto",
                ultimaSync = ahora,
            ),
        )
    }

    // ------------------------------------------------------------------
    // Conflictos y errores
    // ------------------------------------------------------------------
    private suspend fun registrarConflictoRemoto(conflicto: ConflictoRemotoDto) {
        val local = registroDao.buscarPorUuid(conflicto.filaUuid)
        conflictoDao.insertar(
            ConflictoEntity(
                filaUuid = conflicto.filaUuid,
                titulo = local?.titulo ?: "(registro remoto)",
                campo = conflicto.campo.ifBlank { "registro" },
                valorLocal = conflicto.valorLocal?.toString().orEmpty(),
                valorRemoto = conflicto.valorRemoto?.toString().orEmpty(),
                momento = System.currentTimeMillis(),
                revisado = false,
            ),
        )
    }

    private suspend fun registrarConflictoDeAplicacion(
        operacion: OperacionDto,
        error: Exception,
    ) {
        conflictoDao.insertar(
            ConflictoEntity(
                filaUuid = operacion.filaUuid,
                titulo = "(operación no aplicada)",
                campo = "error_aplicacion",
                valorLocal = operacion.opId,
                valorRemoto = error.message ?: error.javaClass.simpleName,
                momento = System.currentTimeMillis(),
                revisado = false,
            ),
        )
    }

    private suspend fun registrarError(mensaje: String) {
        val previo = estadoDao.obtener() ?: EstadoSyncEntity()
        estadoDao.guardar(previo.copy(ultimoError = mensaje))
    }

    /**
     * Persiste el cursor creando la fila si es la primera sincronización.
     *
     * Un ``UPDATE`` sobre una tabla vacía no habría guardado nada y el teléfono
     * volvería a pedir desde cero todas las operaciones en cada ciclo.
     */
    private suspend fun guardarCursor(cursor: Int) {
        val previo = estadoDao.obtener() ?: EstadoSyncEntity()
        estadoDao.guardar(previo.copy(cursor = cursor))
    }

    private fun mensajeDeHttp(error: HttpException): String = when (error.code()) {
        401, 403 -> "El token del equipo no es válido o fue revocado. " +
            "Pida al administrador que vuelva a dar de alta este teléfono."

        404 -> "La dirección no corresponde al nodo central (404). " +
            "Revise la dirección y el puerto del servidor."

        413 -> "El lote de cambios es demasiado grande. Intente de nuevo en unos minutos."

        429 -> "El servidor pidió esperar: se hicieron demasiadas peticiones seguidas."

        in 500..599 -> "El nodo central falló (${error.code()}). " +
            "Los cambios siguen guardados; se reintentará automáticamente."

        else -> "El servidor respondió ${error.code()}."
    }

    // ------------------------------------------------------------------
    // Tipos de resultado
    // ------------------------------------------------------------------
    data class ResumenSync(
        val enviadas: Int,
        val recibidas: Int,
        val momento: Long,
    )

    data class DetalleConexion(
        val servidor: String,
        val versionProtocolo: String,
        val desfaseSegundos: Long?,
        val tablas: List<String>,
    )

    private fun OperacionPendienteEntity.aDto(): OperacionDto = OperacionDto(
        opId = opId,
        tabla = tabla,
        filaUuid = filaUuid,
        operacion = operacion,
        payload = payload,
        dispositivo = dispositivo,
        usuario = usuario,
        creadoEn = Fechas.isoDesde(creadoEn),
    )

    private companion object {
        const val TAMANO_LOTE = 200
        const val MAX_VUELTAS = 40
        const val MAX_PAGINAS = 50
    }
}
