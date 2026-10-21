package ve.edu.sdep.movil.datos.repositorio

import androidx.room.withTransaction
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import ve.edu.sdep.movil.datos.local.AplicadorEspejo
import ve.edu.sdep.movil.datos.local.BaseDatosSdep
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.dao.RegistroDao
import ve.edu.sdep.movil.datos.local.entidad.OperacionPendienteEntity
import ve.edu.sdep.movil.datos.local.entidad.RegistroEntity
import ve.edu.sdep.movil.dominio.modelo.EstadoSincronizacion
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Registro
import ve.edu.sdep.movil.dominio.modelo.Resultado
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Registros de campo, con escritura local primero.
 *
 * Cada alta, edición o borrado se guarda en Room **y** deja su operación en la
 * cola de salida dentro de la misma transacción. Si no hay red, el usuario
 * sigue trabajando y la operación espera; si la transacción falla, no queda ni
 * el dato ni la operación, de modo que nunca se anuncia al servidor algo que no
 * se guardó.
 *
 * En una edición se envían solo las columnas modificadas. Mandar la fila
 * completa pisaría los cambios que otro equipo hizo en columnas distintas; el
 * nodo central mezcla campo por campo y necesita saber qué tocó este teléfono.
 */
@Singleton
class RegistroRepositorio @Inject constructor(
    private val baseDatos: BaseDatosSdep,
    private val registroDao: RegistroDao,
    private val operacionDao: OperacionDao,
    private val aplicador: AplicadorEspejo,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
) {

    fun observarActivos(): Flow<List<Registro>> =
        registroDao.observarActivos().map { filas -> filas.map { it.aDominio() } }

    fun observar(uuid: String): Flow<Registro?> =
        registroDao.observarPorUuid(uuid).map { fila -> fila?.aDominio() }

    suspend fun buscar(uuid: String): Registro? =
        registroDao.buscarPorUuid(uuid)?.aDominio()

    /**
     * Crea (``uuid`` nulo) o modifica un registro.
     *
     * @return La identidad global del registro guardado
     */
    suspend fun guardar(
        uuid: String?,
        titulo: String,
        contenido: String,
        categoria: String,
        valor: Double?,
    ): Resultado<String> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")

        val permiso = if (uuid == null) Permiso.CREAR else Permiso.EDITAR
        if (!sesion.puede(permiso)) {
            val accion = if (uuid == null) "crear" else "editar"
            return Resultado.Fallo("El rol «${sesion.rol.etiqueta}» no permite $accion registros.")
        }

        val tituloLimpio = titulo.trim()
        if (tituloLimpio.isEmpty()) return Resultado.Fallo("El título es obligatorio.")
        if (tituloLimpio.length > 200) {
            return Resultado.Fallo("El título no puede superar los 200 caracteres.")
        }
        if (contenido.length > LIMITE_CONTENIDO) {
            return Resultado.Fallo("El contenido no puede superar los $LIMITE_CONTENIDO caracteres.")
        }

        val categoriaLimpia = categoria.trim().ifBlank { "general" }.take(60)
        val config = configuracionRepositorio.cargar()
        val equipo = config.equipo.ifBlank { "movil" }
        val ahora = System.currentTimeMillis()

        return baseDatos.withTransaction {
            val existente = uuid?.let { registroDao.buscarPorUuid(it) }
            if (uuid != null && existente == null) {
                return@withTransaction Resultado.Fallo("El registro ya no existe en este equipo.")
            }

            val identidad = existente?.uuid ?: UUID.randomUUID().toString()
            val esAlta = existente == null
            val momento = maxOf(ahora, (existente?.actualizadoEn ?: 0L) + 1L)

            val campos = mutableMapOf<String, JsonElement>()
            // La clave natural siempre viaja: permite al servidor reconocer la
            // fila aunque todavía no conozca su identidad.
            campos["uuid_movil"] = JsonPrimitive(identidad)

            if (esAlta || existente?.titulo != tituloLimpio) {
                campos["titulo"] = JsonPrimitive(tituloLimpio)
            }
            if (esAlta || existente?.contenido != contenido) {
                campos["contenido"] = JsonPrimitive(contenido)
            }
            if (esAlta || existente?.categoria != categoriaLimpia) {
                campos["categoria"] = JsonPrimitive(categoriaLimpia)
            }
            if (esAlta || existente?.valor != valor) {
                campos["valor"] = valor?.let { JsonPrimitive(it) } ?: JsonNull
            }

            // Sin cambios reales no se ensucia la cola ni se mueve la marca de
            // tiempo: un «guardar» sobre el mismo texto no genera tráfico.
            if (!esAlta && campos.size == 1) {
                return@withTransaction Resultado.Exito(identidad)
            }

            campos["actualizado_en"] = JsonPrimitive(Fechas.isoDesde(momento))
            if (esAlta) {
                campos["creado_en"] = JsonPrimitive(Fechas.isoDesde(ahora))
                campos["dispositivo"] = JsonPrimitive(equipo)
                campos["usuario"] = JsonPrimitive(sesion.usuario)
            }
            val payload = JsonObject(campos)

            val entidad = RegistroEntity(
                uuid = identidad,
                titulo = tituloLimpio,
                contenido = contenido,
                categoria = categoriaLimpia,
                valor = valor,
                creadoEn = existente?.creadoEn ?: ahora,
                actualizadoEn = momento,
                estado = EstadoSincronizacion.PENDIENTE.name,
                eliminado = false,
                dispositivo = existente?.dispositivo ?: equipo,
                usuario = sesion.usuario,
                ultimaSync = existente?.ultimaSync,
            )
            if (esAlta) registroDao.insertar(entidad) else registroDao.actualizar(entidad)

            operacionDao.encolar(
                OperacionPendienteEntity(
                    opId = opId,
                    tabla = TABLA,
                    filaUuid = identidad,
                    operacion = "upsert",
                    payload = payload.toString(),
                    creadoEn = momento,
                    dispositivo = equipo,
                    usuario = sesion.usuario,
                    estado = ESTADO_PENDIENTE,
                    motivo = null,
                ),
            )
            // Deja constancia de QUÉ escribió este teléfono y CUÁNDO: sin esas
            // marcas, una operación remota pisaría la edición local sin que el
            // motor de mezcla pudiera defenderla.
            aplicador.registrarLocal(
                tabla = TABLA,
                filaUuid = identidad,
                opId = opId,
                campos = payload,
                momentoIso = Fechas.isoDesde(momento),
                dispositivo = equipo,
            )
            Resultado.Exito(identidad)
        }
    }

    /**
     * Borra un registro.
     *
     * El borrado es lógico en el teléfono y viaja como operación ``delete``: el
     * nodo central desactiva la fila y conserva su rastro, igual que hace con
     * los registros creados en el escritorio.
     */
    suspend fun eliminar(uuid: String): Resultado<Unit> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        if (!sesion.puede(Permiso.ELIMINAR)) {
            return Resultado.Fallo("El rol «${sesion.rol.etiqueta}» no permite eliminar registros.")
        }

        val config = configuracionRepositorio.cargar()
        val equipo = config.equipo.ifBlank { "movil" }

        return baseDatos.withTransaction {
            val existente = registroDao.buscarPorUuid(uuid)
                ?: return@withTransaction Resultado.Fallo("El registro ya no existe en este equipo.")
            if (existente.eliminado) return@withTransaction Resultado.Exito(Unit)

            val momento = maxOf(System.currentTimeMillis(), existente.actualizadoEn + 1L)
            registroDao.insertar(
                existente.copy(
                    eliminado = true,
                    actualizadoEn = momento,
                    estado = EstadoSincronizacion.PENDIENTE.name,
                ),
            )
            val opId = UUID.randomUUID().toString()
            operacionDao.encolar(
                OperacionPendienteEntity(
                    opId = opId,
                    tabla = TABLA,
                    filaUuid = uuid,
                    operacion = "delete",
                    payload = JsonObject(mapOf<String, JsonElement>("uuid_movil" to JsonPrimitive(uuid))).toString(),
                    creadoEn = momento,
                    dispositivo = equipo,
                    usuario = sesion.usuario,
                    estado = ESTADO_PENDIENTE,
                    motivo = null,
                ),
            )
            // El borrado también deja su marca de versión: un编辑 posterior de
            // otro equipo solo lo levanta si es más reciente.
            aplicador.registrarLocal(
                tabla = TABLA,
                filaUuid = uuid,
                opId = opId,
                campos = jsonObjectVacio(),
                momentoIso = Fechas.isoDesde(momento),
                dispositivo = equipo,
                borrado = true,
            )
            Resultado.Exito(Unit)
        }
    }

    private fun RegistroEntity.aDominio(): Registro = Registro(
        uuid = uuid,
        titulo = titulo,
        contenido = contenido,
        categoria = categoria,
        valor = valor,
        creadoEn = creadoEn,
        actualizadoEn = actualizadoEn,
        estado = EstadoSincronizacion.desde(estado),
        eliminado = eliminado,
    )

    companion object {
        /** Tabla del sistema de escritorio donde aterrizan estos registros */
        const val TABLA = "registros_moviles"
        const val ESTADO_PENDIENTE = "PENDIENTE"
        const val LIMITE_CONTENIDO = 20_000
    }
}
