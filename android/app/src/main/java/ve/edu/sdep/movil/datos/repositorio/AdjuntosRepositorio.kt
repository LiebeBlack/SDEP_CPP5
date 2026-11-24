package ve.edu.sdep.movil.datos.repositorio

import androidx.room.withTransaction
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import ve.edu.sdep.movil.datos.local.AplicadorEspejo
import ve.edu.sdep.movil.datos.local.BaseDatosSdep
import ve.edu.sdep.movil.datos.local.Espejo
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.dao.BlobPendienteDao
import ve.edu.sdep.movil.datos.local.dao.DocumentoDao
import ve.edu.sdep.movil.datos.local.dao.EmpleadoDao
import ve.edu.sdep.movil.datos.local.dao.IdentidadDao
import ve.edu.sdep.movil.datos.local.dao.IncidenciaDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.entidad.BlobPendienteEntity
import ve.edu.sdep.movil.datos.local.entidad.IdentidadEntity
import ve.edu.sdep.movil.datos.local.entidad.OperacionPendienteEntity
import ve.edu.sdep.movil.datos.documentos.TipoAdjunto
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Resultado
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.dominio.modelo.normalizarCedula
import ve.edu.sdep.movil.sincronizacion.ProgramadorSync
import java.security.MessageDigest
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Adjuntos de documento e incidencia desde el teléfono.
 *
 * Completa el pendiente de paridad: hasta ahora el legajo podía archivar
 * PDF nuevos, pero un documento o una incidencia que ya existían no podían
 * recibir su archivo desde el móvil, ni podía abrirse el adjunto que el
 * escritorio ya había cargado. El camino es el mismo del resto del sistema:
 * los bytes viven en el espejo local, la edición anuncia su huella SHA-256
 * en el payload y el contenido viaja por el canal de binarios del nodo
 * central, con deduplicación y verificación de hash en ambos extremos.
 *
 * Los permisos se comprueban dos veces, como en el resto del proyecto: la
 * pantalla decide qué mostrar y esta capa vuelve a comprobar el módulo y el
 * permiso antes de escribir.
 */
@Singleton
class AdjuntosRepositorio @Inject constructor(
    private val baseDatos: BaseDatosSdep,
    private val documentoDao: DocumentoDao,
    private val incidenciaDao: IncidenciaDao,
    private val empleadoDao: EmpleadoDao,
    private val identidadDao: IdentidadDao,
    private val operacionDao: OperacionDao,
    private val blobDao: BlobPendienteDao,
    private val aplicador: AplicadorEspejo,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
    private val programador: ProgramadorSync,
) {

    /** Tope de adjunto seleccionado desde el móvil: 8 MB (el nodo admite más). */
    private val maxBytes = 8 * 1024 * 1024

    /** Estados de una tabla que admite adjuntos. */
    data class Adjunto(
        val tabla: String,
        val id: Long,
        val nombre: String?,
        val hash: String?,
        val mime: String?,
        /** El binario está en el espejo de este teléfono */
        val disponible: Boolean,
        val tamano: Int,
    )

    /** Estado del adjunto de una fila, leído solo del espejo local */
    suspend fun estado(tabla: String, id: Long): Resultado<Adjunto> = withContext(Dispatchers.IO) {
        val sesion = sesionRepositorio.actual
            ?: return@withContext Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        when (tabla) {
            "documentos" -> {
                if (!sesion.puedeAbrir(Modulo.DOCUMENTOS)) {
                    return@withContext Resultado.Fallo("Su rol no tiene acceso al legajo.")
                }
                val metadatos = documentoDao.metadatosAdjunto(id)
                    ?: return@withContext Resultado.Fallo(
                        "El documento ya no está en este teléfono. Sincronice para confirmarlo.",
                    )
                if (sesion.esTrabajador && !esDocumentoPropio(id, sesion)) {
                    return@withContext Resultado.Fallo("Su rol solo puede consultar su propio legajo.")
                }
                Resultado.Exito(
                    Adjunto(
                        tabla = tabla, id = id,
                        nombre = metadatos.nombre,
                        hash = metadatos.hash,
                        mime = metadatos.mime,
                        disponible = metadatos.disponible,
                        tamano = metadatos.tamano,
                    ),
                )
            }
            "incidencias" -> {
                if (!sesion.puedeAbrir(Modulo.INCIDENCIAS)) {
                    return@withContext Resultado.Fallo("Su rol no tiene acceso a las incidencias.")
                }
                val metadatos = incidenciaDao.metadatosSoporte(id)
                    ?: return@withContext Resultado.Fallo(
                        "La incidencia ya no está en este teléfono. Sincronice para confirmarla.",
                    )
                if (sesion.esTrabajador && !esIncidenciaPropia(id, sesion)) {
                    return@withContext Resultado.Fallo("Su rol solo puede consultar sus propias incidencias.")
                }
                Resultado.Exito(
                    Adjunto(
                        tabla = tabla, id = id,
                        nombre = metadatos.nombre,
                        hash = metadatos.hash,
                        mime = metadatos.mime,
                        disponible = metadatos.disponible,
                        tamano = metadatos.tamano,
                    ),
                )
            }
            else -> Resultado.Fallo("Esta ficha no admite archivos adjuntos.")
        }
    }

    /** Contenido local del adjunto; si falta, la guía es sincronizar, no reintentar */
    suspend fun contenido(tabla: String, id: Long): Resultado<Pair<Adjunto, ByteArray>> =
        withContext(Dispatchers.IO) {
            val sesion = sesionRepositorio.actual
                ?: return@withContext Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
            val adjunto = when (val base = estado(tabla, id)) {
                is Resultado.Exito -> base.valor
                is Resultado.Fallo -> return@withContext base
            }
            if (sesion.esTrabajador) {
                val propio = when (tabla) {
                    "documentos" -> esDocumentoPropio(id, sesion)
                    "incidencias" -> esIncidenciaPropia(id, sesion)
                    else -> false
                }
                if (!propio) {
                    return@withContext Resultado.Fallo(
                        "Su rol solo puede consultar sus propios registros y adjuntos.",
                    )
                }
            }
            val bytes = when (tabla) {
                "documentos" -> documentoDao.contenidoAdjunto(id)
                "incidencias" -> incidenciaDao.contenidoSoporte(id)
                else -> null
            } ?: return@withContext Resultado.Fallo(
                "El archivo todavía no llegó a este teléfono. " +
                    "Sincronice con el nodo central y vuelva a intentarlo.",
            )
            val hashDeclarado = adjunto.hash
            if (hashDeclarado.isNullOrBlank() || !hashDeclarado.equals(sha256(bytes), ignoreCase = true)) {
                return@withContext Resultado.Fallo(
                    "El archivo no supera la verificación de integridad SHA-256 y no se abrirá.",
                )
            }
            Resultado.Exito(adjunto to bytes)
        }

    /**
     * Adjunta (o reemplaza) el archivo de una fila existente.
     *
     * Guarda los bytes en el espejo, anuncia la huella en el payload de la
     * edición y encola el binario para el canal de subida, todo dentro de la
     * misma transacción que el dato: si la app se cierra a mitad, o queda todo
     * registrado o nada.
     */
    suspend fun adjuntar(
        tabla: String,
        id: Long,
        nombre: String,
        mime: String?,
        bytes: ByteArray,
    ): Resultado<Unit> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        val nombreLimpio = nombre.substringAfterLast('/').substringAfterLast('\\').trim()
        if (nombreLimpio.isBlank()) return Resultado.Fallo("Seleccione un archivo con nombre válido.")
        if (bytes.isEmpty()) return Resultado.Fallo("El archivo está vacío.")
        if (bytes.size > maxBytes) {
            return Resultado.Fallo(
                "El archivo supera el límite de 8 MB para la selección desde el teléfono.",
            )
        }
        val mimeVerificado = TipoAdjunto.verificar(nombreLimpio, mime, bytes)
            ?: return Resultado.Fallo(
                "Formato no admitido o firma incompatible. Seleccione un PDF, JPEG o PNG con extensión y tipo compatibles.",
            )
        val problema = permisoDeAdjunto(sesion, tabla, id)
        if (problema != null) return Resultado.Fallo(problema)

        val hash = withContext(Dispatchers.Default) { sha256(bytes) }
        val equipo = configuracionRepositorio.cargar().equipo.ifBlank { "movil" }

        return try {
            baseDatos.withTransaction {
                val ahora = System.currentTimeMillis()
                val iso = Fechas.isoDesde(ahora)
                when (tabla) {
                    "documentos" -> {
                        val doc = documentoDao.buscarPorId(id)
                            ?: error("El documento ya no está en este teléfono. Sincronice e intente de nuevo.")
                        if (sesion.esTrabajador && !esDocumentoPropio(id, sesion)) {
                            error("Su rol solo puede adjuntar a documentos de su propio legajo.")
                        }
                        val uuid = identidadDao.uuidDe("documentos", id)
                            ?: error("El documento debe sincronizarse antes de adjuntar archivos.")
                        val nueva = doc.copy(
                            nombreArchivo = nombreLimpio.take(255),
                            tipoMime = mimeVerificado,
                            tamanoBytes = bytes.size,
                            contenidoHash = hash,
                            contenidoBinario = bytes,
                            actualizadoEn = iso,
                        )
                        documentoDao.actualizar(nueva)
                        encolarEdicion(
                            sesion, equipo, tabla, uuid, nueva, doc,
                            ahora, iso, hash, bytes, "contenido_binario",
                        )
                    }
                    "incidencias" -> {
                        val inc = incidenciaDao.buscarPorId(id)
                            ?: error("La incidencia ya no está en este teléfono. Sincronice e intente de nuevo.")
                        if (sesion.esTrabajador && !esIncidenciaPropia(id, sesion)) {
                            error("Su rol solo puede adjuntar a sus propias incidencias.")
                        }
                        val uuid = identidadDao.uuidDe("incidencias", id)
                            ?: error("La incidencia debe sincronizarse antes de adjuntar archivos.")
                        val nueva = inc.copy(
                            documentoSoporteNombre = nombreLimpio.take(255),
                            documentoSoporteHash = hash,
                            documentoSoporteBinario = bytes,
                            actualizadoEn = iso,
                        )
                        incidenciaDao.actualizar(nueva)
                        encolarEdicion(
                            sesion, equipo, tabla, uuid, nueva, inc,
                            ahora, iso, hash, bytes, "documento_soporte_binario",
                        )
                    }
                    else -> error("Esta ficha no admite archivos adjuntos.")
                }
            }
            // El adjunto queda durable en Room antes de pedir el envío; si
            // todavía no hay red, WorkManager conserva el trabajo pendiente.
            runCatching { programador.sincronizarAhora() }
            Resultado.Exito(Unit)
        } catch (cancelacion: CancellationException) {
            throw cancelacion
        } catch (error: IllegalStateException) {
            Resultado.Fallo(error.message ?: "No se pudo adjuntar el archivo.", error)
        } catch (error: Exception) {
            Resultado.Fallo(
                "No se pudo adjuntar el archivo: ${error.message ?: "error inesperado"}.",
                error,
            )
        }
    }

    /** Regla de permisos por tabla; devuelve el mensaje si el rol no puede */
    private suspend fun permisoDeAdjunto(
        sesion: Sesion,
        tabla: String,
        id: Long,
    ): String? = when (tabla) {
        "documentos" -> when {
            !sesion.puedeAbrir(Modulo.DOCUMENTOS) ->
                "Su rol no tiene acceso al legajo."
            sesion.esTrabajador -> {
                if (!sesion.puede(Permiso.CREAR)) {
                    "Su rol no permite adjuntar archivos al legajo."
                } else {
                    // Un trabajador solo adjunta a documentos de su propio legajo,
                    // con la misma regla del archivado de constancias.
                    val doc = documentoDao.buscarPorId(id)
                    val cedula = doc?.let { empleadoDao.buscarPorId(it.empleadoId) }?.cedula
                    val propio = cedula != null && normalizarCedula(cedula) == sesion.cedulaNormalizada
                    if (!propio) "Su rol solo puede adjuntar a documentos de su propio legajo."
                    else null
                }
            }
            !sesion.puede(Permiso.EDITAR) -> "Su rol no permite adjuntar archivos al legajo."
            else -> null
        }
        "incidencias" -> when {
            !sesion.puedeAbrir(Modulo.INCIDENCIAS) ->
                "Su rol no tiene acceso a las incidencias."
            sesion.esTrabajador -> {
                if (!sesion.puede(Permiso.CREAR)) {
                    "Su rol no permite adjuntar soportes a incidencias."
                } else if (!esIncidenciaPropia(id, sesion)) {
                    "Su rol solo puede adjuntar a sus propias incidencias."
                } else null
            }
            !sesion.puede(Permiso.EDITAR) ->
                "Su rol no permite adjuntar soportes a incidencias."
            else -> null
        }
        else -> "Esta ficha no admite archivos adjuntos."
    }

    /** Edición en cola + registro de mezcla + binario en espera de subida */
    private suspend fun encolarEdicion(
        sesion: Sesion,
        equipo: String,
        tabla: String,
        filaUuid: String,
        nueva: Any?,
        anterior: Any?,
        ahora: Long,
        iso: String,
        hash: String,
        bytes: ByteArray,
        columnaBlob: String,
    ) {
        val crudo = Espejo.payload(tabla, nueva, anterior, completa = false)
            ?: error("No se pudo preparar la sincronización del adjunto.")
        val payload = Espejo.conForaneasComoUuid(tabla, crudo) { padre, idLocal ->
            identidadDao.uuidDe(padre, idLocal)
        }
        val opId = UUID.randomUUID().toString()
        operacionDao.encolar(
            OperacionPendienteEntity(
                opId = opId,
                tabla = tabla,
                filaUuid = filaUuid,
                operacion = "upsert",
                payload = payload.toString(),
                creadoEn = ahora,
                dispositivo = equipo,
                usuario = sesion.usuario,
                estado = "PENDIENTE",
                motivo = null,
            ),
        )
        aplicador.registrarLocal(
            tabla = tabla,
            filaUuid = filaUuid,
            opId = opId,
            campos = payload,
            momentoIso = iso,
            dispositivo = equipo,
        )
        blobDao.guardar(
            BlobPendienteEntity(
                hash = hash,
                tamano = bytes.size,
                tabla = tabla,
                filaUuid = filaUuid,
                columna = columnaBlob,
                direccion = "salida",
                estado = "por_subir",
                creadoEn = ahora,
                actualizadoEn = ahora,
            ),
        )
    }

    private suspend fun esDocumentoPropio(id: Long, sesion: Sesion): Boolean {
        val empleadoId = documentoDao.empleadoIdDe(id) ?: return false
        val cedula = empleadoDao.buscarPorId(empleadoId)?.cedula ?: return false
        return normalizarCedula(cedula) == sesion.cedulaNormalizada
    }

    private suspend fun esIncidenciaPropia(id: Long, sesion: Sesion): Boolean {
        val empleadoId = incidenciaDao.empleadoIdDe(id) ?: return false
        val cedula = empleadoDao.buscarPorId(empleadoId)?.cedula ?: return false
        return normalizarCedula(cedula) == sesion.cedulaNormalizada
    }

    private fun sha256(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it) }
}
