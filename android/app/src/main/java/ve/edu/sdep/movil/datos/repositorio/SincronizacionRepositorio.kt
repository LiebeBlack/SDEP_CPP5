package ve.edu.sdep.movil.datos.repositorio

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerializationException
import ve.edu.sdep.movil.datos.local.AplicadorEspejo
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.dao.BlobPendienteDao
import ve.edu.sdep.movil.datos.local.dao.ConflictoDao
import ve.edu.sdep.movil.datos.local.dao.EstadoSyncDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.dao.RegistroDao
import ve.edu.sdep.movil.datos.local.entidad.BlobPendienteEntity
import ve.edu.sdep.movil.datos.local.entidad.ConflictoEntity
import ve.edu.sdep.movil.datos.local.entidad.EstadoSyncEntity
import ve.edu.sdep.movil.datos.local.entidad.OperacionPendienteEntity
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
 * Ciclo de sincronización con el nodo central.
 *
 * Se ejecuta con un solo candado: dos sincronizaciones simultáneas (la
 * periódica y el botón «Sincronizar ahora») no pueden pisarse.
 *
 * El orden es siempre el mismo y no es casual:
 *
 * 1. **Reintentar** las operaciones diferidas de ciclos anteriores (llegaron
 *    antes que su registro padre).
 * 2. **Enviar** lo pendiente. El nodo central arbitra y le asigna ``seq``.
 * 3. **Recibir** las novedades posteriores al cursor, aplicándolas con el
 *    mismo motor de mezcla campo a campo que usa el escritorio.
 * 4. **Bajar** los binarios anunciados por hash (documentos del legajo).
 *
 * Al enviar primero, el servidor conoce la versión de este teléfono antes de
 * devolverle nada; al recibir después, el cursor avanza solo sobre operaciones
 * ya procesadas.
 */
@Singleton
class SincronizacionRepositorio @Inject constructor(
    private val registroDao: RegistroDao,
    private val operacionDao: OperacionDao,
    private val estadoDao: EstadoSyncDao,
    private val conflictoDao: ConflictoDao,
    private val aplicador: AplicadorEspejo,
    private val blobDao: BlobPendienteDao,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val conector: ConectorNodo,
    private val apiFactory: ApiSyncFactory,
) {

    private val candado = Mutex()

    fun observarEstado(): Flow<EstadoSyncEntity?> = estadoDao.observar()

    /**
     * Envía y recibe. No se llama desde el hilo principal.
     *
     * Si el teléfono aún no está vinculado, intenta la vinculación automática
     * antes de rendirse. Si el nodo rechaza el token del equipo (401/403)
     * porque su base se recreó o el puesto fue revocado, vuelve a emparejarse
     * y repite el ciclo una sola vez: el usuario no tiene que escribir nada.
     */
    suspend fun sincronizar(): Resultado<ResumenSync> = candado.withLock {
        var configuracion = configuracionRepositorio.cargar()
        if (!configuracion.completa) {
            when (val conexion = conector.asegurarConexion(forzar = true)) {
                is Resultado.Exito -> configuracion = conexion.valor
                is Resultado.Fallo -> return@withLock Resultado.Fallo(
                    conexion.mensaje,
                    conexion.causa,
                    reintentable = true,
                )
            }
        }

        val primero = intentarCiclo(configuracion)
        if (primero is Resultado.Fallo && primero.esTokenRechazado()) {
            when (val renovada = conector.revincular()) {
                is Resultado.Exito -> return@withLock intentarCiclo(renovada.valor)
                is Resultado.Fallo -> return@withLock primero
            }
        }
        primero
    }

    /** Un ciclo completo con una configuración ya resuelta (puede lanzar) */
    private suspend fun intentarCiclo(configuracion: ConfiguracionSync): Resultado<ResumenSync> =
        // Todo el ciclo es E/S: red, disco y JSON. Sacarlo del hilo principal
        // evita que una sincronización larga congele la interfaz, y deja que el
        // grupo de hilos de IO use varios núcleos en las descargas.
        withContext(Dispatchers.IO) {
        val api = try {
            apiFactory.protocolo(configuracion)
        } catch (error: Exception) {
            return@withContext Resultado.Fallo(
                "La dirección del servidor no es válida: «${configuracion.url}».",
                error,
            )
        }

        try {
            // Las diferidas de otros ciclos pueden resolverse ahora que quizá
            // haya llegado su registro padre por otra vía.
            aplicador.reintentarDiferidas()
            val enviadas = enviarPendientes(api)
            val recibidas = recibirNovedades(api)
            val blobs = descargarBlobs(api)
            val ahora = System.currentTimeMillis()
            val previo = estadoDao.obtener() ?: EstadoSyncEntity()
            estadoDao.guardar(
                previo.copy(
                    ultimaSync = ahora,
                    ultimoError = null,
                    registrosRecibidos = previo.registrosRecibidos + recibidas,
                ),
            )
            Resultado.Exito(ResumenSync(enviadas, recibidas, ahora, blobs))
        } catch (error: retrofit2.HttpException) {
            val mensaje = mensajeDeHttp(error)
            registrarError(mensaje)
            Resultado.Fallo(
                mensaje,
                error,
                reintentable = error.code() == 401 ||
                    error.code() == 403 ||
                    error.code() == 429 ||
                    error.code() >= 500,
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
        } catch (error: kotlinx.coroutines.CancellationException) {
            // Cancelar (por ejemplo, al detener el trabajador) no es un fallo:
            // se propaga para que la corrutina termine de inmediato.
            throw error
        } catch (error: Exception) {
            val mensaje = "No se pudo completar la sincronización: " +
                "${error.message ?: "error inesperado"}."
            registrarError(mensaje)
            Resultado.Fallo(mensaje, error, reintentable = true)
        }
        }

    private fun Resultado.Fallo.esTokenRechazado(): Boolean {
        val codigo = (causa as? retrofit2.HttpException)?.code()
        return codigo == 401 || codigo == 403
    }

    /**
     * Comprueba el servicio sin enviar ni recibir datos.
     *
     * Devuelve la versión del protocolo y el desfase de reloj: un teléfono con
     * la hora muy adelantada ganaría todos los conflictos de mezcla, así que
     * conviene detectarlo aquí y no en producción.
     */
    suspend fun probarConexion(): Resultado<DetalleConexion> {
        var configuracion = configuracionRepositorio.cargar()
        if (!configuracion.completa) {
            when (val conexion = conector.asegurarConexion(forzar = true)) {
                is Resultado.Exito -> configuracion = conexion.valor
                is Resultado.Fallo -> return Resultado.Fallo(conexion.mensaje, conexion.causa, true)
            }
        }
        return try {
            val api = apiFactory.protocolo(configuracion)
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
        } catch (error: retrofit2.HttpException) {
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
    private suspend fun enviarPendientes(api: ProtocoloApi): Int {
        val configuracion = configuracionRepositorio.actual()
        var enviadas = 0
        var vueltas = 0
        while (vueltas < MAX_VUELTAS) {
            val lote = operacionDao.pendientes(TAMANO_LOTE)
            if (lote.isEmpty()) break

            val respuesta = api.enviar(PushDto(configuracion.equipo, lote.map { it.aDto() }))
            if (respuesta.aplicadas.isNotEmpty()) {
                operacionDao.eliminar(respuesta.aplicadas)
                marcarSincronizadas(lote.filter { it.opId in respuesta.aplicadas.toSet() })
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

    /** Los registros confirmados dejan de estar pendientes en la barra de estado */
    private suspend fun marcarSincronizadas(confirmadas: List<OperacionPendienteEntity>) {
        val ahora = System.currentTimeMillis()
        for (operacion in confirmadas) {
            if (operacion.tabla != TABLA_REGISTROS) continue
            val registro = registroDao.buscarPorUuid(operacion.filaUuid) ?: continue
            if (registro.estado == EstadoSincronizacion.PENDIENTE.name) {
                registroDao.insertar(
                    registro.copy(estado = EstadoSincronizacion.SINCRONIZADO.name, ultimaSync = ahora),
                )
            }
        }
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
                // Cada operación se aplica con el motor de mezcla completo.
                // Un fallo puntual no detiene el lote: se anota en la bandeja
                // y el cursor avanza para no volver a pedir esa operación.
                when (
                    val resultado = aplicador.aplicar(AplicadorEspejo.OperacionRemota.desde(operacion))
                ) {
                    is AplicadorEspejo.ResultadoAplicacion.Aplicada,
                    is AplicadorEspejo.ResultadoAplicacion.Diferida,
                    -> recibidas++

                    is AplicadorEspejo.ResultadoAplicacion.Error ->
                        registrarConflictoDeAplicacion(operacion, resultado.motivo)

                    else -> Unit
                }
                if (operacion.seq > cursor) cursor = operacion.seq
            }
            if (respuesta.cursor > cursor) cursor = respuesta.cursor
            guardarCursor(cursor)

            paginas++
            if (!respuesta.hayMas) break
        }
        return recibidas
    }

    // ------------------------------------------------------------------
    // Binarios
    // ------------------------------------------------------------------

    /**
     * Descarga los binarios anunciados en la última recepción.
     *
     * @return Cuántos archivos quedaron guardados con su hash verificado
     */
    private suspend fun descargarBlobs(api: ProtocoloApi): Int = coroutineScope {
        val pendientes = blobDao.pendientesDeEntrada(LIMITE_BLOBS_POR_CICLO)
        // Descargas en grupos pequeños: la red y el SHA-256 se reparten entre
        // varios hilos, pero la base sigue recibiendo escrituras acotadas.
        val descargas = pendientes.chunked(DESCARGAS_EN_PARALELO).flatMap { grupo ->
            grupo.map { blob -> async { descargarBlob(api, blob) } }.awaitAll()
        }
        descargas.count { it }
    }

    /** Baja y verifica un binario; nunca lanza hacia el ciclo */
    private suspend fun descargarBlob(api: ProtocoloApi, blob: BlobPendienteEntity): Boolean =
        try {
            // `use` cierra el cuerpo aunque falle la lectura: sin eso, cada
            // archivo dejaría una conexión abierta hasta el recolector.
            val contenido = api.descargarBlob(blob.hash).use { it.bytes() }
            if (aplicador.guardarContenidoDescargado(blob, contenido)) {
                true
            } else {
                // Contenido que no coincide con su hash: se marca como
                // sospechoso y no se vuelve a pedir sin revisión.
                marcarBlobFallido(blob.hash, blob.intentos)
                false
            }
        } catch (error: retrofit2.HttpException) {
            if (error.code() == 404) {
                // El nodo central no lo tiene (nadie lo subió): no se insiste
                // para siempre.
                marcarBlobFallido(blob.hash, blob.intentos)
            }
            false
        } catch (_: IOException) {
            // Sin red: se reintenta en el próximo ciclo
            false
        } catch (_: Exception) {
            marcarBlobFallido(blob.hash, blob.intentos)
            false
        }

    private suspend fun marcarBlobFallido(hash: String, intentosPrevios: Int) {
        val intentos = intentosPrevios + 1
        val estado = if (intentos >= MAX_INTENTOS_BLOB) "omitido" else "por_bajar"
        blobDao.marcarIntento(hash, estado)
    }

    // ------------------------------------------------------------------
    // Conflictos y errores
    // ------------------------------------------------------------------
    private suspend fun registrarConflictoRemoto(conflicto: ConflictoRemotoDto) {
        conflictoDao.insertar(
            ConflictoEntity(
                tabla = conflicto.tabla,
                filaUuid = conflicto.filaUuid,
                titulo = "${conflicto.tabla}/${conflicto.filaUuid.take(8)}",
                campo = conflicto.campo.ifBlank { "registro" },
                valorLocal = conflicto.valorLocal?.toString().orEmpty(),
                valorRemoto = conflicto.valorRemoto?.toString().orEmpty(),
                ganador = conflicto.ganador,
                regla = conflicto.regla,
                momento = System.currentTimeMillis(),
                revisado = false,
            ),
        )
    }

    private suspend fun registrarConflictoDeAplicacion(operacion: OperacionDto, motivo: String) {
        conflictoDao.insertar(
            ConflictoEntity(
                tabla = operacion.tabla,
                filaUuid = operacion.filaUuid,
                titulo = "(operación no aplicada)",
                campo = "error_aplicacion",
                valorLocal = operacion.opId,
                valorRemoto = motivo,
                ganador = "",
                regla = "error_al_aplicar",
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

    private fun mensajeDeHttp(error: retrofit2.HttpException): String = when (error.code()) {
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
        val blobs: Int = 0,
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
        const val TABLA_REGISTROS = "registros_moviles"
        const val TAMANO_LOTE = 200
        const val MAX_VUELTAS = 40
        const val MAX_PAGINAS = 50
        const val LIMITE_BLOBS_POR_CICLO = 10
        const val MAX_INTENTOS_BLOB = 5
        const val DESCARGAS_EN_PARALELO = 3
    }
}
