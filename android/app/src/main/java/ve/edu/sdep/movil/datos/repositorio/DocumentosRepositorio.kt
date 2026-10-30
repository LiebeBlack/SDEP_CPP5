package ve.edu.sdep.movil.datos.repositorio

import androidx.room.withTransaction
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import ve.edu.sdep.movil.datos.local.AplicadorEspejo
import ve.edu.sdep.movil.datos.local.BaseDatosSdep
import ve.edu.sdep.movil.datos.local.Espejo
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.documentos.DatosConstancia
import ve.edu.sdep.movil.datos.documentos.PLANTILLA_INSTITUCIONAL
import ve.edu.sdep.movil.datos.documentos.PdfConstanciaLocal
import ve.edu.sdep.movil.datos.documentos.antiguedadLegible
import ve.edu.sdep.movil.datos.documentos.edadEnAnios
import ve.edu.sdep.movil.datos.documentos.fechaLarga
import ve.edu.sdep.movil.datos.documentos.mesLargo
import ve.edu.sdep.movil.datos.documentos.montoEnLetras
import ve.edu.sdep.movil.datos.local.dao.ConfiguracionDao
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
    private val configuracionDao: ConfiguracionDao,
    private val documentoDao: DocumentoDao,
    private val identidadDao: IdentidadDao,
    private val operacionDao: OperacionDao,
    private val blobDao: ve.edu.sdep.movil.datos.local.dao.BlobPendienteDao,
    private val aplicador: AplicadorEspejo,
    private val apiFactory: ApiSyncFactory,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
) {
    data class PdfListo(
        val nombre: String,
        val contenido: ByteArray,
        val archivado: Boolean = false,
        /** Compuesto en este equipo: no viajó al nodo ni espera turno de red. */
        val local: Boolean = false,
    )

    // Última constancia compuesta en el teléfono: repetir la misma plantilla
    // para la misma ficha devuelve los mismos bytes sin volver a maquetar.
    // Clave y PDF van juntos en una sola referencia volátil: leerlos por
    // separado permitía devolver un PDF con la clave de otra ficha si dos
    // pantallas pedían constancias a la vez.
    @Volatile
    private var cacheLocal: Pair<String, PdfListo>? = null

    suspend fun empleadosVisibles(): List<ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity> {
        val sesion = sesionRepositorio.actual ?: return emptyList()
        if (!sesion.puedeAbrir(Modulo.EMPLEADOS)) return emptyList()
        if (sesion.esTrabajador) {
            val cedula = sesion.cedulaNormalizada
            if (cedula.isBlank()) return emptyList()
            return empleadoDao.buscarActivoPorCedulaNormalizada(cedula)?.let(::listOf).orEmpty()
        }
        return empleadoDao.listarActivos()
    }

    suspend fun empleadoVisiblePorCedula(cedula: String): ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity? {
        val sesion = sesionRepositorio.actual ?: return null
        if (!sesion.esTrabajador || !sesion.puedeAbrir(Modulo.EMPLEADOS)) return null
        val cedulaNormalizada = normalizarCedula(cedula)
        if (cedulaNormalizada.isBlank() || cedulaNormalizada != sesion.cedulaNormalizada) return null
        return empleadoDao.buscarActivoPorCedulaNormalizada(cedulaNormalizada)
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
        val bytes = withContext(Dispatchers.IO) {
            leerPdfLimitado(api.descargar(archivo.hash)).also { verificarPdf(it, archivo.hash) }
        }
        val nombreSeguro = nombrePdfSeguro(archivo.nombre, nombre)
        archivar(
            sesion, empleado.id, nombreSeguro,
            titulo.filterNot { it.isISOControl() }.trim().take(200).ifBlank { "Constancia de trabajo" },
            archivo.hash, bytes,
        )
        PdfListo(nombreSeguro, bytes, archivado = true)
    }

    /**
     * Constancia compuesta en el teléfono, sin red.
     *
     * Es la vía rápida: no hay dos viajes al nodo ni proceso en el escritorio,
     * y funciona sin conexión. El documento archivado con folio sigue siendo
     * [constancia], que sí requiere el nodo central.
     */
    suspend fun constanciaLocal(
        empleadoId: Long,
        plantilla: String,
        personalizada: Boolean,
        titulo: String = "Constancia de trabajo",
    ): Resultado<PdfListo> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        return try {
            val empleado = empleadoPropio(sesion, empleadoId)
            exigirGenerarConstancia(sesion)
            val cuerpo = if (personalizada) plantilla else PLANTILLA_INSTITUCIONAL
            require(cuerpo.toByteArray(Charsets.UTF_8).size <= MAX_PLANTILLA) {
                "La plantilla Markdown supera 64 KB."
            }
            val tituloSeguro = titulo.filterNot { it.isISOControl() }.trim().take(120)
                .ifBlank { "Constancia de trabajo" }
            val clave = listOf(empleado.id, empleado.actualizadoEn, tituloSeguro, cuerpo.hashCode())
                .joinToString("|")
            val cache = cacheLocal
            if (cache != null && cache.first == clave) return Resultado.Exito(cache.second)

            val institucion = institucion()
            val datos = DatosConstancia(
                institucion = institucion,
                titulo = tituloSeguro,
                valores = valoresConstancia(empleado, institucion),
            )
            val bytes = withContext(Dispatchers.Default) {
                PdfConstanciaLocal.generar(cuerpo, datos)
            }
            require(bytes.size in 5..MAX_PDF) { "El PDF generado está vacío o supera 8 MB." }
            require(bytes.copyOfRange(0, 5).decodeToString().startsWith("%PDF-")) {
                "El PDF generado no es válido."
            }
            val sufijo = (empleado.cedula.ifBlank { empleado.id.toString() })
                .filter { it.isLetterOrDigit() || it in "-_" }
                .take(80)
                .ifBlank { empleado.id.toString() }
            val listo = PdfListo("constancia_$sufijo.pdf", bytes, archivado = false, local = true)
            cacheLocal = clave to listo
            Resultado.Exito(listo)
        } catch (cancelacion: CancellationException) {
            throw cancelacion
        } catch (error: Exception) {
            Resultado.Fallo(error.message ?: "No se pudo componer la constancia.", error)
        }
    }

    /**
     * Valores ya resueltos para la ficha seleccionada: exactamente lo que se
     * escribirá en el documento. La pantalla los muestra antes de generar para
     * que nadie firme una constancia con un dato vacío por sorpresa.
     */
    suspend fun datosConstancia(empleadoId: Long): Map<String, String> {
        val empleado = empleadoDao.buscarPorId(empleadoId) ?: return emptyMap()
        return valoresConstancia(empleado, institucion())
    }

    /**
     * Nombre institucional del encabezado. La clave real de la configuración
     * es `nombre_institucion` (la misma que siembra el nodo y edita el
     * escritorio); `institucion_nombre` se conserva solo como respaldo de
     * espejos antiguos. Antes se leía únicamente la segunda, que nunca existe:
     * toda constancia del teléfono salía como «INSTITUCIÓN EDUCATIVA».
     */
    private suspend fun institucion(): String {
        for (clave in CLAVES_INSTITUCION) {
            val valor = configuracionDao.valor(clave)?.trim()
            if (!valor.isNullOrEmpty()) return valor
        }
        return "INSTITUCIÓN EDUCATIVA"
    }

    private fun valoresConstancia(
        empleado: ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity,
        institucion: String,
    ): Map<String, String> {
        val tipoEmpleado = empleado.tipoEmpleado.ifBlank { "Empleado" }
        val salario = runCatching {
            String.format(java.util.Locale.US, "${'$'}%,.2f", empleado.salarioBase)
        }.getOrDefault("$" + empleado.salarioBase)
        // Fecha y edad se calculan una sola vez: son datos derivados que la
        // plantilla puede pedir en palabras o en números.
        val hoy = LocalDate.now()
        val edad = edadEnAnios(empleado.fechaNacimiento)
        return mapOf(
            "nombre" to empleado.nombreCompleto,
            "nombre_completo" to empleado.nombreCompleto,
            "nombres" to empleado.nombres,
            "apellidos" to empleado.apellidos,
            "cedula" to empleado.cedula,
            "cargo" to empleado.cargo,
            "departamento" to empleado.departamento,
            "tipo_empleado" to tipoEmpleado.uppercase(),
            "salario" to salario,
            "salario_letras" to montoEnLetras(empleado.salarioBase),
            "fecha_contratacion" to fechaCorta(empleado.fechaContratacion),
            "fecha_emision" to fechaCorta(hoy.toString()),
            "fecha_emision_larga" to fechaLarga(hoy),
            "dia_emision" to hoy.dayOfMonth.toString(),
            "mes_emision" to mesLargo(hoy.monthValue),
            "anio_emision" to hoy.year.toString(),
            "institucion" to institucion,
            "antiguedad" to antiguedadLegible(empleado.fechaContratacion),
            "tipo_contratacion" to empleado.tipoContratacion.orEmpty().replace("_", " "),
            "telefono" to empleado.telefono.orEmpty(),
            "celular" to empleado.celular.orEmpty(),
            "correo" to empleado.email.orEmpty(),
            "direccion" to empleado.direccion.orEmpty(),
            "ciudad" to empleado.ciudad.orEmpty(),
            "estado" to empleado.estado.orEmpty(),
            "nacionalidad" to empleado.nacionalidad.orEmpty(),
            "genero" to empleado.genero.orEmpty().replace("_", " "),
            "estado_civil" to empleado.estadoCivil.orEmpty().replace("_", " "),
            "fecha_nacimiento" to fechaCorta(empleado.fechaNacimiento.orEmpty()),
            "edad" to (edad?.let { "$it años" } ?: ""),
            "nivel_educativo" to empleado.nivelEducativo.orEmpty(),
            "especialidad" to empleado.especialidad.orEmpty(),
            "titulo_obtenido" to empleado.tituloObtenido.orEmpty(),
        )
    }

    private fun fechaCorta(valor: String): String {
        val limpio = valor.trim()
        if (limpio.length < 10) return limpio
        val anio = limpio.substring(0, 4)
        val mes = limpio.substring(5, 7)
        val dia = limpio.substring(8, 10)
        return if (anio.all(Char::isDigit) && mes.all(Char::isDigit) && dia.all(Char::isDigit)) {
            "$dia/$mes/$anio"
        } else limpio
    }

    suspend fun fichaPdf(empleadoId: Long): Resultado<PdfListo> = conectado { sesion, api ->
        val empleado = empleadoPropio(sesion, empleadoId)
        exigirReporte(sesion, Modulo.EMPLEADOS)
        val archivo = api.generarPdf(
            "ficha_empleado",
            buildJsonObject { put("cedula", empleado.cedula) },
        )
        val bytes = withContext(Dispatchers.IO) {
            leerPdfLimitado(api.descargar(archivo.hash)).also { verificarPdf(it, archivo.hash) }
        }
        PdfListo(nombrePdfSeguro(archivo.nombre, "ficha_${empleado.cedula}.pdf"), bytes)
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
            val desdeTexto = periodoInicio ?: error("Indique la fecha inicial del período.")
            val hastaTexto = periodoFin ?: error("Indique la fecha final del período.")
            val desde = runCatching { LocalDate.parse(desdeTexto) }
                .getOrElse { error("La fecha inicial debe usar AAAA-MM-DD.") }
            val hasta = runCatching { LocalDate.parse(hastaTexto) }
                .getOrElse { error("La fecha final debe usar AAAA-MM-DD.") }
            require(desde.toString() == desdeTexto && hasta.toString() == hastaTexto) {
                "Las fechas deben tener el formato AAAA-MM-DD."
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
        val bytes = withContext(Dispatchers.IO) {
            leerPdfLimitado(api.descargar(archivo.hash)).also { verificarPdf(it, archivo.hash) }
        }
        PdfListo(nombrePdfSeguro(archivo.nombre, "$tipo.pdf"), bytes)
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
        val originalSeguro = nombreOriginal.substringAfterLast('/').substringAfterLast('\\')
        require(originalSeguro.endsWith(".pdf", ignoreCase = true)) {
            "Seleccione un archivo PDF con nombre válido."
        }
        val baseNombre = originalSeguro.substringBeforeLast('.')
            .filter { it.isLetterOrDigit() || it in "._- " }
            .trim()
            .take(100)
            .ifBlank { "documento" }
        val nombre = "$baseNombre.pdf"
        require(identidadDao.uuidDe("empleados", empleado.id) != null) {
            "La ficha debe sincronizarse antes de subir documentos."
        }
        val nombreParaServidor = if (sesion.esTrabajador) {
            val prefijoCedula = sesion.cedulaNormalizada
            require(prefijoCedula.isNotBlank() && prefijoCedula.all { it.isLetterOrDigit() || it in "-_" }) {
                "La cédula de la sesión no tiene un formato válido."
            }
            val nombreLimpio = baseNombre.filter { it.isLetterOrDigit() || it in "._- " }
            val maximoBase = 160 - prefijoCedula.length - 1 - "documento_".length - 4
            require(maximoBase >= 1) {
                "La cédula asociada no permite crear un nombre de archivo válido."
            }
            "${prefijoCedula}_documento_${nombreLimpio.take(maximoBase).ifBlank { "adjunto" }}.pdf"
        } else nombre
        val archivo = api.subirArchivo(
            nombreParaServidor,
            contenido.toRequestBody("application/pdf".toMediaType()),
        )
        withContext(Dispatchers.Default) { verificarPdf(contenido, archivo.hash) }
        val nombreSeguro = nombrePdfSeguro(archivo.nombre, nombre)
        archivar(
            sesion, empleado.id, nombreSeguro,
            titulo.filterNot { it.isISOControl() }.trim().take(200)
                .ifBlank { nombre.substringBeforeLast('.') },
            archivo.hash, contenido,
        )
        PdfListo(nombreSeguro, contenido, archivado = true)
    }

    private suspend fun empleadoPropio(sesion: Sesion, id: Long): ve.edu.sdep.movil.datos.local.entidad.EmpleadoEntity {
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
        val puedeGuardarPropio = sesion.esTrabajador &&
            empleadoDao.buscarPorId(empleadoId)?.cedula?.let {
                normalizarCedula(it) == sesion.cedulaNormalizada
            } == true && sesion.puede(Permiso.CREAR) &&
            sesion.puedeAbrir(Modulo.DOCUMENTOS)
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

    private fun nombrePdfSeguro(nombre: String?, alternativo: String): String {
        fun normalizar(valor: String): String? {
            val base = valor.substringAfterLast('/').substringAfterLast('\\')
            if (!base.endsWith(".pdf", ignoreCase = true)) return null
            val nombreLimpio = base.filter { it.isLetterOrDigit() || it in "._- " }.take(120)
            return nombreLimpio.takeIf { it.endsWith(".pdf", ignoreCase = true) }
        }
        return nombre?.let(::normalizar) ?: normalizar(alternativo) ?: "documento.pdf"
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

        /** Claves de configuración con el nombre de la institución, en orden. */
        val CLAVES_INSTITUCION = listOf("nombre_institucion", "institucion_nombre")
    }
}
