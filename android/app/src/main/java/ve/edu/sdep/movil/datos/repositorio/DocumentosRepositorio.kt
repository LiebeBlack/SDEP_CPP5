package ve.edu.sdep.movil.datos.repositorio

import androidx.room.withTransaction
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import ve.edu.sdep.movil.datos.local.AplicadorEspejo
import ve.edu.sdep.movil.datos.local.BaseDatosSdep
import ve.edu.sdep.movil.datos.local.Espejo
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.dao.DocumentoDao
import ve.edu.sdep.movil.datos.local.dao.EmpleadoDao
import ve.edu.sdep.movil.datos.local.dao.IdentidadDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.entidad.BlobPendienteEntity
import ve.edu.sdep.movil.datos.local.entidad.DocumentoEntity
import ve.edu.sdep.movil.datos.local.entidad.IdentidadEntity
import ve.edu.sdep.movil.datos.local.entidad.OperacionPendienteEntity
import ve.edu.sdep.movil.datos.remoto.ApiAcciones
import ve.edu.sdep.movil.datos.remoto.ApiSyncFactory
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Resultado
import ve.edu.sdep.movil.dominio.modelo.Sesion
import ve.edu.sdep.movil.dominio.modelo.normalizarCedula
import java.security.MessageDigest
import java.time.LocalDate
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/** Herramientas PDF del legajo de personal. */
@Singleton
class DocumentosRepositorio @Inject constructor(
    private val baseDatos: BaseDatosSdep,
    private val empleadoDao: EmpleadoDao,
    private val documentoDao: DocumentoDao,
    private val identidadDao: IdentidadDao,
    private val operacionDao: OperacionDao,
    private val blobDao: ve.edu.sdep.movil.datos.local.dao.BlobPendienteDao,
    private val aplicador: AplicadorEspejo,
    private val apiFactory: ApiSyncFactory,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
) {
    data class PdfListo(val nombre: String, val contenido: ByteArray, val archivado: Boolean = false)

    suspend fun empleadosVisibles(): List<ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity> {
        val sesion = sesionRepositorio.actual ?: return emptyList()
        if (!sesion.puedeAbrir(Modulo.EMPLEADOS)) return emptyList()
        val filas = empleadoDao.listarTodos().filter { it.activo == 1 &&
            (!sesion.esTrabajador || normalizarCedula(it.cedula) == sesion.cedulaNormalizada)
        }
        return if (sesion.esTrabajador) filas.take(1) else filas
    }

    suspend fun empleadoVisiblePorCedula(cedula: String): ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity? {
        val sesion = sesionRepositorio.actual ?: return null
        if (!sesion.esTrabajador || !sesion.puedeAbrir(Modulo.EMPLEADOS)) return null
        return empleadoDao.listarTodos().firstOrNull {
            it.activo == 1 && normalizarCedula(it.cedula) == sesion.cedulaNormalizada &&
                normalizarCedula(it.cedula) == normalizarCedula(cedula)
        }
    }

    suspend fun constancia(
        empleadoId: Long,
        plantilla: String,
        personalizada: Boolean,
        titulo: String = "Constancia de trabajo",
    ): Resultado<PdfListo> = conectado { sesion, api ->
        val empleado = empleadoPropio(sesion, empleadoId)
        exigirGenerarConstancia(sesion)

        require(empleado.activo == 1) {
            "Solo se pueden emitir constancias para personal activo."
        }
        if (personalizada && plantilla.toByteArray(Charsets.UTF_8).size > MAX_PLANTILLA) {
            error("La plantilla Markdown supera 64 KB.")
        }
        val sufijoSeguro = (empleado.cedula.ifBlank { empleado.id.toString() })
            .filter { it.isLetterOrDigit() || it in "-_" }
            .take(80)
            .ifBlank { empleado.id.toString() }
        val nombre = "constancia_$sufijoSeguro.pdf"
        val archivo = api.generarPdf(
            if (personalizada) "constancia_plantilla" else "constancia_trabajo",
            buildJsonObject {
                put("cedula", empleado.cedula)
                put("nombre_completo", empleado.nombreCompleto)
                if (personalizada) {
                    put("plantilla_markdown", plantilla)
                    put("titulo_documento", titulo.filterNot { it.isISOControl() }.trim().take(120).uppercase().ifBlank { "CONSTANCIA DE TRABAJO" })
                }
            },
        )
        val bytes = leerPdfLimitado(api.descargar(archivo.hash))
        verificarPdf(bytes, archivo.hash)
        val nombreSeguro = archivo.nombre?.substringAfterLast('/')?.substringAfterLast('\\')
            ?.filter { it.isLetterOrDigit() || it in "._- " }
            ?.take(120)
            ?.takeIf { it.endsWith(".pdf", ignoreCase = true) }
            ?: nombre
        archivar(sesion, empleado.id, nombreSeguro, titulo.filterNot { it.isISOControl() }.trim().take(200).ifBlank { "Constancia de trabajo" }, archivo.hash, bytes)
        PdfListo(nombreSeguro, bytes, archivado = true)
    }

    suspend fun fichaPdf(empleadoId: Long): Resultado<PdfListo> = conectado { sesion, api ->
        val empleado = empleadoPropio(sesion, empleadoId)
        exigirReporte(sesion, Modulo.EMPLEADOS)
        val archivo = api.generarPdf(
            "ficha_empleado",
            buildJsonObject { put("cedula", empleado.cedula) },
        )
        val bytes = leerPdfLimitado(api.descargar(archivo.hash))
        verificarPdf(bytes, archivo.hash)
        PdfListo(archivo.nombre ?: "ficha_${empleado.cedula}.pdf", bytes)
    }

    suspend fun reporte(
        tipo: String,
        periodoInicio: String? = null,
        periodoFin: String? = null,
    ): Resultado<PdfListo> = conectado { sesion, api ->
        val modulo = when (tipo) {
            "reporte_empleados" -> Modulo.EMPLEADOS
            "reporte_vencimientos" -> Modulo.DOCUMENTOS
            "reporte_incidencias" -> Modulo.INCIDENCIAS
            "reporte_contratos" -> Modulo.CONTRATOS
            "planilla_nomina" -> Modulo.NOMINA
            else -> error("Reporte no disponible.")
        }
        exigirReporte(sesion, modulo)
        if (tipo == "planilla_nomina") {
            val desde = runCatching {
                LocalDate.parse(periodoInicio ?: error("Indique la fecha inicial del período."))
            }.getOrElse {
                error("La fecha inicial debe usar AAAA-MM-DD.")
            }
            val hasta = runCatching {
                LocalDate.parse(periodoFin ?: error("Indique la fecha final del período."))
            }.getOrElse {
                error("La fecha final debe usar AAAA-MM-DD.")
            }
            require(!hasta.isBefore(desde)) { "La fecha final no puede ser anterior a la inicial." }
        }
        val archivo = api.generarPdf(
            tipo,
            buildJsonObject {
                if (tipo == "planilla_nomina") {
                    put("periodo_inicio", periodoInicio ?: error("Indique la fecha inicial del período."))
                    put("periodo_fin", periodoFin ?: error("Indique la fecha final del período."))
                }
            },
        )
        val bytes = leerPdfLimitado(api.descargar(archivo.hash))
        verificarPdf(bytes, archivo.hash)
        PdfListo(archivo.nombre ?: "$tipo.pdf", bytes)
    }

    suspend fun subirPdf(
        empleadoId: Long,
        nombreOriginal: String,
        titulo: String,
        contenido: ByteArray,
    ): Resultado<PdfListo> = conectado { sesion, api ->
        val empleado = empleadoPropio(sesion, empleadoId)
        if (!sesion.puedeAbrir(Modulo.DOCUMENTOS)) {
            error("Su rol no tiene permiso para guardar documentos del legajo.")
        }
        exigirCrear(sesion)
        if (contenido.size !in 5..MAX_PDF) error("El PDF está vacío o supera 8 MB.")
        if (!contenido.copyOfRange(0, 5).decodeToString().startsWith("%PDF-")) {
            error("El archivo seleccionado no es un PDF válido.")
        }
        val nombre = nombreOriginal.substringAfterLast('/').substringAfterLast('\\')
            .takeIf { it.endsWith(".pdf", ignoreCase = true) }
            ?.filter { it.isLetterOrDigit() || it in "._- " }
            ?.take(120)
            ?.takeIf { it.endsWith(".pdf", ignoreCase = true) }
            ?: error("Seleccione un archivo PDF con nombre válido.")
        require(identidadDao.uuidDe("empleados", empleado.id) != null) {
            "La ficha debe sincronizarse antes de subir documentos."
        }
        val nombreParaServidor = if (sesion.esTrabajador) {
            val prefijoCedula = sesion.cedulaNormalizada
            require(prefijoCedula.isNotBlank() && prefijoCedula.all { it.isLetterOrDigit() || it in "-_" }) {
                "La cédula de la sesión no tiene un formato válido."
            }
            "${prefijoCedula}_${nombre.filter { it.isLetterOrDigit() || it in "._- " }.take(110)}"
        } else nombre
        val archivo = api.subirArchivo(
            nombreParaServidor,
            contenido.toRequestBody("application/pdf".toMediaType()),
        )
        verificarPdf(contenido, archivo.hash)
        archivar(
            sesion, empleado.id, nombre,
            titulo.filterNot { it.isISOControl() }.trim().take(200)
                .ifBlank { nombre.substringBeforeLast('.') },
            archivo.hash, contenido,
        )
        PdfListo(archivo.nombre ?: nombre, contenido, archivado = true)
    }

    private suspend fun empleadoPropio(
        sesion: Sesion,
        id: Long,
    ): ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity {
        val empleado = empleadoDao.buscarPorId(id) ?: error("Empleado no encontrado; sincronice la ficha.")
        require(empleado.activo == 1) { "La ficha no pertenece a personal activo." }
        if (!sesion.puedeAbrir(Modulo.EMPLEADOS)) {
            error("Su rol no tiene permiso para acceder a fichas de empleados.")
        }
        if (sesion.esTrabajador && normalizarCedula(empleado.cedula) != sesion.cedulaNormalizada) {
            error("Solo puede generar o adjuntar documentos a su propia ficha.")
        }
        return empleado
    }

    private suspend fun archivar(
        sesion: Sesion,
        empleadoId: Long,
        nombre: String,
        titulo: String,
        hash: String,
        bytes: ByteArray,
    ) {
        val empleadoUuid = identidadDao.uuidDe("empleados", empleadoId)
            ?: error("La ficha debe sincronizarse antes de archivar documentos.")
        val puedeGuardarPropio =                sesion.esTrabajador && empleadoDao.buscarPorId(empleadoId)?.cedula?.let { normalizarCedula(it) == sesion.cedulaNormalizada } == true &&
                sesion.puede(Permiso.CREAR) && sesion.puedeAbrir(Modulo.DOCUMENTOS)
        val puedeGuardarGestion = !sesion.esTrabajador && sesion.puedeAbrir(Modulo.DOCUMENTOS) &&
            (sesion.puede(Permiso.CREAR) || sesion.puede(Permiso.REPORTAR))
        require(puedeGuardarPropio || puedeGuardarGestion) {
            "Su rol no puede guardar archivos en el legajo."
        }
        val config = configuracionRepositorio.cargar()
        val equipo = config.equipo.ifBlank { "movil" }
        baseDatos.withTransaction {
            val ahora = System.currentTimeMillis()
            val iso = Fechas.isoDesde(ahora)
            val fila = DocumentoEntity(
                empleadoId = empleadoId,
                tipoDocumento = "certificado",
                titulo = titulo,
                descripcion = "Archivo PDF del legajo.",
                fechaEmision = LocalDate.now().toString(),
                nombreArchivo = nombre.take(255),
                tamanoBytes = bytes.size,
                tipoMime = "application/pdf",
                contenidoHash = hash,
                contenidoBinario = bytes,
                creadoEn = iso,
                actualizadoEn = iso,
            )
            val id = documentoDao.insertar(fila)
            check(id > 0) { "No se pudo guardar el documento." }
            val uuid = UUID.randomUUID().toString()
            identidadDao.vincular(IdentidadEntity("documentos", uuid, id))
            val campos = Espejo.payload("documentos", fila.copy(id = id), null, completa = true)
                ?: error("No se pudo preparar la sincronización del documento.")
            val payload = Espejo.conForaneasComoUuid("documentos", campos) { tabla, idLocal ->
                if (tabla == "empleados" && idLocal == empleadoId) empleadoUuid
                else identidadDao.uuidDe(tabla, idLocal)
            }
            val opId = UUID.randomUUID().toString()
            operacionDao.encolar(
                OperacionPendienteEntity(
                    opId = opId, tabla = "documentos", filaUuid = uuid,
                    operacion = "upsert", payload = payload.toString(), creadoEn = ahora,
                    dispositivo = equipo, usuario = sesion.usuario,
                    estado = "PENDIENTE", motivo = null,
                ),
            )
            aplicador.registrarLocal("documentos", uuid, opId, payload, iso, equipo)
            blobDao.guardar(
                BlobPendienteEntity(
                    hash = hash, tamano = bytes.size, tabla = "documentos",
                    filaUuid = uuid, columna = "contenido_binario", direccion = "salida",
                    estado = "por_subir", creadoEn = ahora, actualizadoEn = ahora,
                ),
            )
        }
    }

    private suspend fun <T> conectado(
        accion: suspend (Sesion, ApiAcciones) -> T,
    ): Resultado<T> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        if (sesion.offline || sesion.token.isBlank()) {
            return Resultado.Fallo("Conéctese al nodo central para generar o subir PDFs.")
        }
        return try {
            val config = configuracionRepositorio.cargar()
            if (!config.completa) return Resultado.Fallo("No hay conexión con el nodo central.")
            Resultado.Exito(accion(sesion, apiFactory.acciones(config, sesion.token)))
        } catch (cancelacion: CancellationException) {
            throw cancelacion
        } catch (error: Exception) {
            val mensaje = if (error is retrofit2.HttpException && error.code() in 401..403) {
                "El nodo central denegó la acción por permisos o sesión."
            } else error.message ?: "No se pudo completar la operación."
            Resultado.Fallo(mensaje, error)
        }
    }

    private fun exigirGenerarConstancia(sesion: Sesion) {
        val puedeGenerarPropia = sesion.esTrabajador &&
            sesion.puedeAbrir(Modulo.DOCUMENTOS) && sesion.puede(Permiso.CREAR)
        if (!puedeGenerarPropia &&
            (!sesion.puedeAbrir(Modulo.EMPLEADOS) || !sesion.puede(Permiso.REPORTAR))
        ) {
            error("Su rol no tiene permiso para generar constancias.")
        }
    }

    private fun exigirReporte(sesion: Sesion, modulo: Modulo) {
        if (!sesion.puedeAbrir(modulo) || !sesion.puede(Permiso.REPORTAR)) {
            error("Su rol no tiene permiso para generar este reporte.")
        }
    }

    private fun exigirCrear(sesion: Sesion) {
        if (!sesion.puedeAbrir(Modulo.DOCUMENTOS) || !sesion.puede(Permiso.CREAR)) {
            error("Su rol no tiene permiso para adjuntar PDFs.")
        }
    }

    private fun leerPdfLimitado(cuerpo: okhttp3.ResponseBody): ByteArray = cuerpo.use { respuesta ->
        val longitud = respuesta.contentLength()
        require(longitud in 5L..MAX_PDF.toLong()) {
            "El PDF está vacío, supera 8 MB o no informa su tamaño."
        }
        val bytes = ByteArray(longitud.toInt())
        val entrada = respuesta.byteStream()
        var posicion = 0
        while (posicion < bytes.size) {
            val leidos = entrada.read(bytes, posicion, minOf(32 * 1024, bytes.size - posicion))
            if (leidos < 0) break
            if (leidos == 0) {
                val siguiente = entrada.read()
                if (siguiente < 0) break
                bytes[posicion++] = siguiente.toByte()
            } else {
                posicion += leidos
            }
        }
        require(posicion == bytes.size && entrada.read() == -1) {
            "El PDF recibido está incompleto o excede el tamaño informado."
        }
        bytes
    }

    private fun verificarPdf(bytes: ByteArray, hashEsperado: String) {
        require(bytes.size in 5..MAX_PDF) { "El PDF está vacío o supera 8 MB." }
        val hash = MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it) }
        require(hash == hashEsperado) { "La huella del PDF no coincide." }
        require(bytes.copyOfRange(0, 5).decodeToString().startsWith("%PDF-")) {
            "El archivo recibido no es PDF válido."
        }
    }

    private companion object {
        const val MAX_PDF = 8 * 1024 * 1024
        const val MAX_PLANTILLA = 65_536
    }
}
