package ve.edu.sdep.movil.datos.repositorio

import androidx.room.withTransaction
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import ve.edu.sdep.movil.datos.local.AplicadorEspejo
import ve.edu.sdep.movil.datos.local.BaseDatosSdep
import ve.edu.sdep.movil.datos.local.Espejo
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.dao.EmpleadoDao
import ve.edu.sdep.movil.datos.local.dao.IdentidadDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity
import ve.edu.sdep.movil.datos.local.entidad.IdentidadEntity
import ve.edu.sdep.movil.datos.local.entidad.OperacionPendienteEntity
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Resultado
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Escritura de fichas de personal con la misma mecánica que el escritorio.
 *
 * Cada alta o edición se guarda en Room **y** deja su operación en la cola de
 * salida dentro de la misma transacción: si el guardado se confirma, la
 * operación existe; si se deshace, no se anuncia nada. El payload lleva solo
 * los campos tocados (o todos en un alta) y las claves foráneas como UUID, de
 * modo que el nodo central mezcla campo por campo sin pisar a otro puesto.
 *
 * El teléfono no inventa reglas de negocio: valida lo mismo que el modelo del
 * escritorio (campos obligatorios, longitudes y rangos) y delega el resto en el
 * nodo central, que sigue siendo la autoridad.
 */
@Singleton
class EmpleadoRepositorio @Inject constructor(
    private val baseDatos: BaseDatosSdep,
    private val empleadoDao: EmpleadoDao,
    private val identidadDao: IdentidadDao,
    private val operacionDao: OperacionDao,
    private val aplicador: AplicadorEspejo,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
) {

    /** Ficha completa para el formulario; null si ya no está en el espejo */
    suspend fun cargar(id: Long): EmpleadoEntity? = empleadoDao.buscarPorId(id)

    /**
     * Crea (``id`` nulo) o modifica una ficha.
     *
     * @return El id local de la ficha guardada
     */
    suspend fun guardar(id: Long?, datos: EmpleadoEntity): Resultado<Long> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        val permiso = if (id == null) Permiso.CREAR else Permiso.EDITAR
        if (!sesion.puede(permiso)) {
            val accion = if (id == null) "crear" else "editar"
            return Resultado.Fallo("El rol «${sesion.rol.etiqueta}» no permite $accion fichas.")
        }
        validar(datos)?.let { return Resultado.Fallo(it) }

        val equipo = configuracionRepositorio.cargar().equipo.ifBlank { "movil" }

        return try {
            baseDatos.withTransaction {
                val existente = id?.let { empleadoDao.buscarPorId(it) }
                if (id != null && existente == null) {
                    return@withTransaction Resultado.Fallo(
                        "La ficha ya no existe en este equipo. Sincronice e intente de nuevo.",
                    )
                }

                val ahora = maxOf(
                    System.currentTimeMillis(),
                    (Fechas.desdeIso(existente?.actualizadoEn) ?: 0L) + 1L,
                )
                val iso = Fechas.isoDesde(ahora)
                val esAlta = existente == null
                var entidad = datos.copy(
                    id = existente?.id ?: 0L,
                    creadoEn = existente?.creadoEn ?: iso,
                    actualizadoEn = iso,
                    activo = if (esAlta) 1 else datos.activo,
                )

                val localId: Long
                val filaUuid: String
                if (esAlta) {
                    localId = empleadoDao.insertar(entidad)
                    if (localId <= 0L) {
                        return@withTransaction Resultado.Fallo(
                            "Ya existe un empleado con la cédula ${entidad.cedula}.",
                        )
                    }
                    filaUuid = UUID.randomUUID().toString()
                    identidadDao.vincular(
                        IdentidadEntity(tabla = TABLA, uuid = filaUuid, idLocal = localId),
                    )
                    entidad = entidad.copy(id = localId)
                } else {
                    localId = entidad.id
                    empleadoDao.actualizar(entidad)
                    filaUuid = identidadDao.uuidDe(TABLA, localId) ?: run {
                        // Una fila llegada de un nodo antiguo podría no tener
                        // identidad global; se le asigna una ahora para que su
                        // edición pueda viajar.
                        val nueva = UUID.randomUUID().toString()
                        identidadDao.vincular(
                            IdentidadEntity(tabla = TABLA, uuid = nueva, idLocal = localId),
                        )
                        nueva
                    }
                }

                val base = Espejo.payload(TABLA, entidad, existente, esAlta)
                    ?: return@withTransaction Resultado.Exito(localId)
                val payload = Espejo.conForaneasComoUuid(TABLA, base) { tabla, idLocal ->
                    identidadDao.uuidDe(tabla, idLocal)
                }
                val opId = UUID.randomUUID().toString()
                operacionDao.encolar(
                    OperacionPendienteEntity(
                        opId = opId,
                        tabla = TABLA,
                        filaUuid = filaUuid,
                        operacion = "upsert",
                        payload = payload.toString(),
                        creadoEn = ahora,
                        dispositivo = equipo,
                        usuario = sesion.usuario,
                        estado = ESTADO_PENDIENTE,
                        motivo = null,
                    ),
                )
                aplicador.registrarLocal(
                    tabla = TABLA,
                    filaUuid = filaUuid,
                    opId = opId,
                    campos = payload,
                    momentoIso = iso,
                    dispositivo = equipo,
                )
                Resultado.Exito(localId)
            }
        } catch (error: CancellationException) {
            throw error
        } catch (error: Exception) {
            Resultado.Fallo(
                "No se pudo guardar la ficha: ${error.message ?: "error inesperado"}.",
                error,
            )
        }
    }

    /**
     * Baja lógica: la ficha queda con ``activo = 0`` y viaja como ``delete``.
     *
     * Igual que en el escritorio, la fila no se borra: conserva su historia y
     * puede reactivarse editándola de nuevo.
     */
    suspend fun desactivar(id: Long): Resultado<Unit> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        if (!sesion.puede(Permiso.ELIMINAR)) {
            return Resultado.Fallo("El rol «${sesion.rol.etiqueta}» no permite dar de baja fichas.")
        }
        val equipo = configuracionRepositorio.cargar().equipo.ifBlank { "movil" }

        return try {
            baseDatos.withTransaction {
                val existente = empleadoDao.buscarPorId(id)
                    ?: return@withTransaction Resultado.Fallo(
                        "La ficha ya no existe en este equipo.",
                    )
                if (existente.activo == 0) return@withTransaction Resultado.Exito(Unit)

                val ahora = maxOf(
                    System.currentTimeMillis(),
                    (Fechas.desdeIso(existente.actualizadoEn) ?: 0L) + 1L,
                )
                val iso = Fechas.isoDesde(ahora)
                empleadoDao.actualizar(existente.copy(activo = 0, actualizadoEn = iso))
                val filaUuid = identidadDao.uuidDe(TABLA, id) ?: run {
                    val nueva = UUID.randomUUID().toString()
                    identidadDao.vincular(
                        IdentidadEntity(tabla = TABLA, uuid = nueva, idLocal = id),
                    )
                    nueva
                }
                val opId = UUID.randomUUID().toString()
                // El borrado se identifica por la fila global; la cédula viaja
                // además como clave natural para que un nodo que aún no conoce
                // el UUID pueda reconocer la ficha.
                val payload = JsonObject(
                    mapOf("cedula" to JsonPrimitive(existente.cedula)),
                )
                operacionDao.encolar(
                    OperacionPendienteEntity(
                        opId = opId,
                        tabla = TABLA,
                        filaUuid = filaUuid,
                        operacion = "delete",
                        payload = payload.toString(),
                        creadoEn = ahora,
                        dispositivo = equipo,
                        usuario = sesion.usuario,
                        estado = ESTADO_PENDIENTE,
                        motivo = null,
                    ),
                )
                aplicador.registrarLocal(
                    tabla = TABLA,
                    filaUuid = filaUuid,
                    opId = opId,
                    campos = payload,
                    momentoIso = iso,
                    dispositivo = equipo,
                    borrado = true,
                )
                Resultado.Exito(Unit)
            }
        } catch (error: CancellationException) {
            throw error
        } catch (error: Exception) {
            Resultado.Fallo(
                "No se pudo dar de baja la ficha: ${error.message ?: "error inesperado"}.",
                error,
            )
        }
    }

    /** Reglas del modelo del escritorio, comprobadas también en el teléfono */
    private fun validar(datos: EmpleadoEntity): String? {
        if (datos.nombres.isBlank()) return "Los nombres son obligatorios."
        if (datos.nombres.length > 100) return "Los nombres no pueden superar 100 caracteres."
        if (datos.apellidos.isBlank()) return "Los apellidos son obligatorios."
        if (datos.apellidos.length > 100) return "Los apellidos no pueden superar 100 caracteres."
        if (datos.cedula.isBlank()) return "La cédula es obligatoria."
        if (datos.cedula.length > 20) return "La cédula no puede superar 20 caracteres."
        if (datos.tipoEmpleado !in TIPOS_EMPLEADO) {
            return "El tipo de empleado debe ser docente, administrativo o mantenimiento."
        }
        if (datos.cargo.isBlank()) return "El cargo es obligatorio."
        if (datos.departamento.isBlank()) return "El departamento es obligatorio."
        if (datos.fechaContratacion.isBlank()) return "La fecha de contratación es obligatoria."
        if (Fechas.desdeIso("${datos.fechaContratacion}T00:00:00") == null) {
            return "La fecha de contratación debe tener el formato AAAA-MM-DD."
        }
        datos.fechaTerminacion?.takeIf { it.isNotBlank() }?.let { fecha ->
            if (Fechas.desdeIso("${fecha}T00:00:00") == null) {
                return "La fecha de terminación debe tener el formato AAAA-MM-DD."
            }
        }
        if (datos.salarioBase < 0) return "El salario no puede ser negativo."
        if ((datos.peso ?: 0.0) < 0) return "El peso no puede ser negativo."
        if ((datos.altura ?: 0.0) < 0) return "La altura no puede ser negativa."
        if (datos.email != null && datos.email!!.isNotBlank() && !datos.email!!.contains("@")) {
            return "El correo no parece válido."
        }
        return null
    }

    private companion object {
        const val TABLA = "empleados"
        const val ESTADO_PENDIENTE = "PENDIENTE"
        val TIPOS_EMPLEADO = setOf("docente", "administrativo", "mantenimiento")
    }
}
