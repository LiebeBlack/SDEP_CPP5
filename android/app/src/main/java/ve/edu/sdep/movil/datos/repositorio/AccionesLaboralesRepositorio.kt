package ve.edu.sdep.movil.datos.repositorio

import androidx.room.withTransaction
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import retrofit2.HttpException
import ve.edu.sdep.movil.datos.local.BaseDatosSdep
import ve.edu.sdep.movil.datos.local.Espejo
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.dao.ContratoDao
import ve.edu.sdep.movil.datos.local.dao.IdentidadDao
import ve.edu.sdep.movil.datos.local.dao.IncidenciaDao
import ve.edu.sdep.movil.datos.local.dao.PagoDao
import ve.edu.sdep.movil.datos.local.entidad.ContratoEntity
import ve.edu.sdep.movil.datos.local.entidad.IdentidadEntity
import ve.edu.sdep.movil.datos.local.entidad.IncidenciaEntity
import ve.edu.sdep.movil.datos.local.entidad.PagoEntity
import ve.edu.sdep.movil.datos.remoto.ApiAcciones
import ve.edu.sdep.movil.datos.remoto.ApiSyncFactory
import ve.edu.sdep.movil.datos.remoto.mensajeDelServidor
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Resultado
import ve.edu.sdep.movil.sincronizacion.ProgramadorSync
import java.io.IOException
import java.time.LocalDate
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Acciones de negocio sobre incidencias y contratos.
 *
 * La regla de negocio no vive aquí: se envía la petición al nodo central, que
 * valida permisos, estados y cálculos con los mismos servicios del escritorio.
 * El teléfono solo traduce la fila local a su UUID global y, con la respuesta,
 * actualiza el espejo para que la ficha muestre el resultado sin esperar al
 * siguiente ciclo de sincronización.
 *
 * El id de Room es local y no se envía nunca al servidor: dos equipos pueden
 * tener el mismo número para filas distintas. Por eso las rutas usan
 * `sync_ids.uuid`, que es la identidad estable de la fila en toda la red.
 */
@Singleton
class AccionesLaboralesRepositorio @Inject constructor(
    private val baseDatos: BaseDatosSdep,
    private val identidadDao: IdentidadDao,
    private val incidenciaDao: IncidenciaDao,
    private val contratoDao: ContratoDao,
    private val pagoDao: PagoDao,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
    private val apiFactory: ApiSyncFactory,
    private val json: Json,
    private val programador: ProgramadorSync,
) {

    suspend fun cargarIncidencia(id: Long): IncidenciaEntity? =
        withContext(Dispatchers.IO) { incidenciaDao.buscarPorId(id) }

    suspend fun cargarContrato(id: Long): ContratoEntity? =
        withContext(Dispatchers.IO) { contratoDao.buscarPorId(id) }

    suspend fun hayConexion(): Boolean = configuracionRepositorio.hayConfiguracion()

    suspend fun aprobarIncidencia(
        id: Long,
        comentarios: String?,
        diasAprobados: Int?,
    ): Resultado<Unit> {
        val actual = incidenciaDao.buscarPorId(id)
            ?: return Resultado.Fallo("La incidencia ya no está en este equipo.")
        if (actual.estado != ESTADO_PENDIENTE) {
            return Resultado.Fallo("Solo se pueden aprobar incidencias pendientes.")
        }
        if (diasAprobados != null && (diasAprobados < 1 || diasAprobados > actual.diasSolicitados)) {
            return Resultado.Fallo(
                "Los días aprobados deben estar entre 1 y ${actual.diasSolicitados}.",
            )
        }
        val contexto = when (val preparado = preparar("incidencias", id, Modulo.INCIDENCIAS)) {
            is Resultado.Exito -> preparado.valor
            is Resultado.Fallo -> return preparado
        }

        val cuerpo = buildJsonObject {
            comentarios?.trim()?.takeIf { it.isNotEmpty() }?.let { put("comentarios", it) }
            diasAprobados?.let { put("dias_aprobados", it) }
        }
        val respuesta = llamar { contexto.api.aprobarIncidencia(contexto.uuid, cuerpo) }
        val raiz = respuesta.valorExitoso()
            ?: return respuesta.comoFallo()
        val incidenciaRemota = raiz["incidencia"] as? JsonObject
        val actualizada = incidenciaRemota?.let { aplicarIncidencia(actual, it) }
            ?: actual.copy(
                estado = ESTADO_APROBADO,
                fechaAprobacion = LocalDate.now().toString(),
                aprobadoPor = sesionRepositorio.actual?.usuario,
                diasAprobados = diasAprobados ?: actual.diasSolicitados,
                comentariosAprobacion = comentarios?.trim()?.takeIf { it.isNotEmpty() },
                actualizadoEn = Fechas.ahoraIso(),
            )
        return reflejarLocal("La incidencia se aprobó en el nodo") {
            incidenciaDao.actualizar(actualizada)
        }
    }

    suspend fun rechazarIncidencia(id: Long, comentarios: String?): Resultado<Unit> {
        val actual = incidenciaDao.buscarPorId(id)
            ?: return Resultado.Fallo("La incidencia ya no está en este equipo.")
        if (actual.estado != ESTADO_PENDIENTE) {
            return Resultado.Fallo("Solo se pueden rechazar incidencias pendientes.")
        }
        val contexto = when (val preparado = preparar("incidencias", id, Modulo.INCIDENCIAS)) {
            is Resultado.Exito -> preparado.valor
            is Resultado.Fallo -> return preparado
        }

        val cuerpo = buildJsonObject {
            comentarios?.trim()?.takeIf { it.isNotEmpty() }?.let { put("comentarios", it) }
        }
        val respuesta = llamar { contexto.api.rechazarIncidencia(contexto.uuid, cuerpo) }
        val raiz = respuesta.valorExitoso()
            ?: return respuesta.comoFallo()
        val incidenciaRemota = raiz["incidencia"] as? JsonObject
        val actualizada = incidenciaRemota?.let { aplicarIncidencia(actual, it) }
            ?: actual.copy(
                estado = ESTADO_RECHAZADO,
                fechaAprobacion = LocalDate.now().toString(),
                aprobadoPor = sesionRepositorio.actual?.usuario,
                comentariosAprobacion = comentarios?.trim()?.takeIf { it.isNotEmpty() },
                actualizadoEn = Fechas.ahoraIso(),
            )
        return reflejarLocal("La incidencia se rechazó en el nodo") {
            incidenciaDao.actualizar(actualizada)
        }
    }

    suspend fun renovarContrato(
        id: Long,
        nuevaFechaFin: String,
        nuevoSalario: Double?,
        tipo: String?,
        clausulas: String?,
    ): Resultado<Unit> {
        val anterior = contratoDao.buscarPorId(id)
            ?: return Resultado.Fallo("El contrato ya no está en este equipo.")
        if (anterior.estado != ESTADO_VIGENTE) {
            return Resultado.Fallo("Solo se puede renovar un contrato vigente.")
        }
        val fin = fecha(nuevaFechaFin)
            ?: return Resultado.Fallo("Indique la nueva fecha de fin en formato AAAA-MM-DD.")
        val finAnterior = fecha(anterior.fechaFin)
            ?: return Resultado.Fallo("No se puede renovar un contrato sin fecha de vencimiento.")
        if (!fin.isAfter(finAnterior)) {
            return Resultado.Fallo("La nueva fecha de fin debe ser posterior a la anterior.")
        }
        if (nuevoSalario != null && (!nuevoSalario.isFinite() || nuevoSalario <= 0.0)) {
            return Resultado.Fallo("El nuevo salario debe ser mayor que cero.")
        }
        val contexto = when (val preparado = preparar("contratos", id, Modulo.CONTRATOS)) {
            is Resultado.Exito -> preparado.valor
            is Resultado.Fallo -> return preparado
        }

        val cuerpo = buildJsonObject {
            put("nueva_fecha_fin", fin.toString())
            nuevoSalario?.let { put("nuevo_salario", it) }
            tipo?.trim()?.takeIf { it.isNotEmpty() }?.let { put("tipo", it) }
            clausulas?.trim()?.takeIf { it.isNotEmpty() }?.let { put("clausulas", it) }
        }
        val respuesta = llamar { contexto.api.renovarContrato(contexto.uuid, cuerpo) }
        val raiz = respuesta.valorExitoso()
            ?: return respuesta.comoFallo()
        val contratoRemoto = raiz["contrato"] as? JsonObject
            ?: return Resultado.Fallo("El nodo no devolvió el contrato renovado.")
        val anteriorRemoto = raiz["anterior"] as? JsonObject

        return reflejarLocal("El contrato se renovó en el nodo") {
            baseDatos.withTransaction {
                if (anteriorRemoto != null) {
                    aplicarContrato(anterior, anteriorRemoto)
                } else {
                    contratoDao.actualizar(
                        anterior.copy(
                            estado = ESTADO_RENOVADO,
                            actualizadoEn = Fechas.ahoraIso(),
                        ),
                    )
                }
                val nuevo = contratoDesde(contratoRemoto, anterior)
                val insertado = contratoDao.insertar(nuevo)
                val idNuevo = if (insertado > 0L) {
                    insertado
                } else {
                    val existente = contratoDao.buscarPorNumero(nuevo.numero)
                        ?: error("No se pudo reflejar el contrato renovado en este equipo.")
                    contratoDao.actualizar(nuevo.copy(id = existente.id))
                    existente.id
                }
                val uuid = Espejo.texto(raiz, "fila_uuid")?.takeIf { it.isNotBlank() }
                if (uuid != null && identidadDao.uuidDe("contratos", idNuevo) == null) {
                    identidadDao.vincular(IdentidadEntity("contratos", uuid, idNuevo))
                }
            }
        }
    }

    suspend fun terminarContrato(
        id: Long,
        motivo: String,
        fechaTerminacion: String?,
        generarLiquidacion: Boolean,
        metodoPago: String?,
    ): Resultado<Unit> {
        val actual = contratoDao.buscarPorId(id)
            ?: return Resultado.Fallo("El contrato ya no está en este equipo.")
        if (actual.estado == ESTADO_TERMINADO) {
            return Resultado.Fallo("El contrato ya está terminado.")
        }
        val motivoLimpio = motivo.trim()
        if (motivoLimpio.isEmpty()) {
            return Resultado.Fallo("El motivo de terminación es obligatorio.")
        }
        val termino = fechaTerminacion?.trim()?.takeIf { it.isNotEmpty() }?.let { texto ->
            fecha(texto) ?: return Resultado.Fallo(
                "La fecha de terminación debe tener formato AAAA-MM-DD.",
            )
        }
        val inicio = fecha(actual.fechaInicio)
        val fin = fecha(actual.fechaFin)
        if (termino != null && inicio != null && termino.isBefore(inicio)) {
            return Resultado.Fallo("La terminación no puede ser anterior al inicio del contrato.")
        }
        if (termino != null && fin != null && termino.isAfter(fin)) {
            return Resultado.Fallo("La terminación no puede ser posterior al fin del contrato.")
        }
        val contexto = when (val preparado = preparar("contratos", id, Modulo.CONTRATOS)) {
            is Resultado.Exito -> preparado.valor
            is Resultado.Fallo -> return preparado
        }

        val cuerpo = buildJsonObject {
            put("motivo", motivoLimpio)
            termino?.let { put("fecha_terminacion", it.toString()) }
            put("generar_liquidacion", generarLiquidacion)
            metodoPago?.trim()?.takeIf { it.isNotEmpty() }?.let { put("metodo_pago", it) }
        }
        val respuesta = llamar { contexto.api.terminarContrato(contexto.uuid, cuerpo) }
        val raiz = respuesta.valorExitoso()
            ?: return respuesta.comoFallo()
        val resultado = raiz["resultado"] as? JsonObject ?: raiz
        val contratoRemoto = resultado["contrato"] as? JsonObject
            ?: return Resultado.Fallo("El nodo no devolvió el contrato terminado.")

        return reflejarLocal("El contrato se terminó en el nodo") {
            baseDatos.withTransaction {
                aplicarContrato(actual, contratoRemoto)
                (resultado["pago"] as? JsonObject)?.let { pagoRemoto ->
                    insertarPago(actual.empleadoId, pagoRemoto)
                }
            }
        }
    }

    // ------------------------------------------------------------------
    // Interno
    // ------------------------------------------------------------------

    private data class Contexto(val api: ApiAcciones, val uuid: String)

    private suspend fun preparar(tabla: String, id: Long, modulo: Modulo): Resultado<Contexto> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        if (!sesion.puedeAbrir(modulo)) {
            return Resultado.Fallo("Su rol no tiene acceso a este módulo.")
        }
        // El permiso global de edición no basta para el rol Usuario: el nodo
        // exige «update» sobre todo el módulo para aprobar o contratar.
        if (sesion.esTrabajador || !sesion.puede(Permiso.EDITAR)) {
            return Resultado.Fallo("Su rol no permite ejecutar esta acción.")
        }
        if (sesion.token.isBlank()) {
            return Resultado.Fallo("La sesión no tiene un token válido. Vuelva a entrar.")
        }
        val configuracion = configuracionRepositorio.cargar()
        if (!configuracion.completa) {
            return Resultado.Fallo(
                "Conecte el teléfono con el sistema de escritorio para ejecutar esta acción.",
            )
        }
        val uuid = identidadDao.uuidDe(tabla, id)
            ?: return Resultado.Fallo(
                "El registro aún no tiene identidad en el nodo central. Sincronice e intente de nuevo.",
            )
        return try {
            Resultado.Exito(Contexto(apiFactory.acciones(configuracion, sesion.token), uuid))
        } catch (cancelacion: CancellationException) {
            throw cancelacion
        } catch (error: Exception) {
            Resultado.Fallo(
                error.message ?: "No se pudo preparar la conexión con el nodo central.",
                error,
            )
        }
    }

    private suspend fun llamar(bloque: suspend () -> JsonElement): Resultado<JsonElement> =
        try {
            Resultado.Exito(bloque())
        } catch (cancelacion: CancellationException) {
            throw cancelacion
        } catch (error: HttpException) {
            val mensaje = error.mensajeDelServidor(json) ?: when (error.code()) {
                401, 403 -> "El nodo central denegó la acción por permisos o sesión."
                404 -> "El registro no existe en el nodo central. Sincronice e intente de nuevo."
                in 500..599 -> "El nodo central no pudo completar la acción."
                else -> "El nodo central rechazó la acción."
            }
            Resultado.Fallo(mensaje, error)
        } catch (error: IOException) {
            Resultado.Fallo(
                "No se pudo conectar con el sistema de escritorio. Revise la red e intente de nuevo.",
                error,
                reintentable = true,
            )
        } catch (error: Exception) {
            Resultado.Fallo(error.message ?: "No se pudo completar la acción.", error)
        }

    private fun aplicarIncidencia(actual: IncidenciaEntity, remota: JsonObject): IncidenciaEntity {
        val campos = sinForaneas(remota, "id", "empleado_id")
        return Espejo.aplicar("incidencias", actual, campos) as? IncidenciaEntity
            ?: actual.copy(
                estado = Espejo.texto(remota, "estado") ?: actual.estado,
                fechaAprobacion = Espejo.fecha(remota, "fecha_aprobacion"),
                diasAprobados = Espejo.entero(remota, "dias_aprobados"),
                aprobadoPor = Espejo.texto(remota, "aprobado_por"),
                comentariosAprobacion = Espejo.texto(remota, "comentarios_aprobacion"),
                actualizadoEn = Espejo.texto(remota, "updated_at") ?: Fechas.ahoraIso(),
            )
    }

    private suspend fun aplicarContrato(actual: ContratoEntity, remota: JsonObject) {
        val campos = sinForaneas(remota, "id", "empleado_id", "contrato_anterior_id")
        val actualizado = Espejo.aplicar("contratos", actual, campos) as? ContratoEntity ?: return
        contratoDao.actualizar(actualizado)
    }

    private fun contratoDesde(remota: JsonObject, anterior: ContratoEntity): ContratoEntity {
        val campos = sinForaneas(remota, "id", "empleado_id", "contrato_anterior_id")
        val base = Espejo.aplicar("contratos", null, campos) as? ContratoEntity
            ?: error("La respuesta no contiene un contrato válido.")
        return base.copy(
            id = 0,
            empleadoId = anterior.empleadoId,
            contratoAnteriorId = anterior.id,
            archivoRuta = null,
        )
    }

    private suspend fun insertarPago(empleadoId: Long, remota: JsonObject) {
        val campos = sinForaneas(remota, "id", "empleado_id")
        val base = Espejo.aplicar("pagos", null, campos) as? PagoEntity ?: return
        pagoDao.insertar(base.copy(id = 0, empleadoId = empleadoId))
    }

    private suspend fun reflejarLocal(
        accion: String,
        bloque: suspend () -> Unit,
    ): Resultado<Unit> = try {
        bloque()
        // WorkManager puede no estar disponible en un arranque muy temprano;
        // la acción ya quedó aplicada y el siguiente ciclo la recogerá.
        runCatching { programador.sincronizarAhora() }
        Resultado.Exito(Unit)
    } catch (cancelacion: CancellationException) {
        throw cancelacion
    } catch (error: Exception) {
        Resultado.Fallo(
            "$accion, pero no se pudo actualizar la copia local. " +
                "Sincronice para ver el resultado.",
            error,
        )
    }

    private fun sinForaneas(campos: JsonObject, vararg claves: String): JsonObject =
        JsonObject(campos.filterKeys { it !in claves })

    private fun fecha(valor: String?): LocalDate? =
        runCatching { LocalDate.parse(valor?.trim().orEmpty()) }.getOrNull()

    private fun Resultado<JsonElement>.valorExitoso(): JsonObject? =
        (this as? Resultado.Exito)?.valor as? JsonObject

    private fun Resultado<JsonElement>.comoFallo(): Resultado.Fallo =
        this as? Resultado.Fallo ?: Resultado.Fallo("El nodo devolvió una respuesta inesperada.")

    private companion object {
        const val ESTADO_PENDIENTE = "pendiente"
        const val ESTADO_APROBADO = "aprobado"
        const val ESTADO_RECHAZADO = "rechazado"
        const val ESTADO_VIGENTE = "vigente"
        const val ESTADO_RENOVADO = "renovado"
        const val ESTADO_TERMINADO = "terminado"
    }
}
