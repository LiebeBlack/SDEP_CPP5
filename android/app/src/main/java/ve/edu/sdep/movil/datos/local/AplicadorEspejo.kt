package ve.edu.sdep.movil.datos.local

import androidx.room.withTransaction
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import ve.edu.sdep.movil.datos.local.dao.*
import ve.edu.sdep.movil.datos.local.entidad.*
import ve.edu.sdep.movil.datos.remoto.OperacionDto
import java.security.MessageDigest
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Aplica operaciones que llegan del nodo central sobre el espejo local.
 *
 * Es el espejo exacto de `sync_agent/aplicador.py` y `sync_agent/merge.py`
 * del escritorio: misma regla de mezcla, mismos desempates y misma bandeja de
 * conflictos, de modo que todos los equipos convergen sin importar el orden
 * en que lleguen las operaciones.
 *
 * Garantías que ofrece cada aplicación:
 *
 * * **Exactamente una vez** ([OpAplicadaEntity]): reintentar el pull no
 *   duplica ni reaplica nada.
 * * **Nada se pisa por llegar tarde**: cada campo se decide por separado
 *   comparando la última escritura conocida con la que llega, mediante un
 *   orden total ((actualizado_en, dispositivo, op_id)); el valor perdedor
 *   queda registrado en la bandeja de conflictos.
 * * **Sin operaciones a medias**: si falta el registro padre de una clave
 *   foránea, la operación se difiere entera en [OperacionEntradaEntity] y se
 *   reintenta en cada ciclo, en lugar de crear una fila coja.
 * * **Sin ecos**: la fila se escribe con los campos planificados por el motor;
 *   lo que el usuario editó localmente queda protegido por sus propias marcas.
 */
@Singleton
class AplicadorEspejo @Inject constructor(
    private val baseDatos: BaseDatosSdep,
    private val identidadDao: IdentidadDao,
    private val entradaDao: OperacionEntradaDao,
    private val campoRemotoDao: CampoRemotoDao,
    private val versionFilaDao: VersionFilaDao,
    private val opAplicadaDao: OpAplicadaDao,
    private val conflictoDao: ConflictoDao,
    private val registroDao: RegistroDao,
    private val empleadoDao: EmpleadoDao,
    private val documentoDao: DocumentoDao,
    private val incidenciaDao: IncidenciaDao,
    private val contratoDao: ContratoDao,
    private val pagoDao: PagoDao,
    private val estudianteDao: EstudianteDao,
    private val periodoDao: PeriodoAcademicoDao,
    private val gradoDao: GradoDao,
    private val matriculaDao: MatriculaDao,
    private val notaDao: NotaFinalDao,
    private val configuracionDao: ConfiguracionDao,
    private val blobDao: BlobPendienteDao,
) {

    // ==================================================================
    // Entrada principal
    // ==================================================================

    /**
     * Aplica una operación remota.
     *
     * Cada operación corre en su propia transacción: si una falla (un dato que
     * no cabe, un padre que falta), se revierte SOLO esa operación y el resto
     * del lote sigue aplicándose.
     */
    suspend fun aplicar(op: OperacionRemota): ResultadoAplicacion {
        if (op.tabla !in Espejo.TABLAS) return ResultadoAplicacion.Ignorada(MOTIVO_TABLA_DESCONOCIDA)
        if (op.opId.isBlank()) return ResultadoAplicacion.Ignorada(MOTIVO_SIN_IDENTIDAD)
        if (opAplicadaDao.contiene(op.opId) > 0) return ResultadoAplicacion.Duplicada

        return try {
            baseDatos.withTransaction {
                val resultado = if (op.operacion == "delete") {
                    aplicarBorrado(op)
                } else {
                    aplicarUpsert(op)
                }
                if (resultado is ResultadoAplicacion.Aplicada) {
                    opAplicadaDao.marcar(
                        OpAplicadaEntity(op.opId, op.tabla, System.currentTimeMillis()),
                    )
                }
                resultado
            }
        } catch (error: Exception) {
            ResultadoAplicacion.Error("${MOTIVO_ERROR}:${error.message ?: "sin detalle"}")
        }
    }

    /**
     * Registra las marcas de una escritura propia.
     *
     * Se llama dentro de la MISMA transacción que guarda el cambio y encola la
     * operación de salida, igual que la captura del agente de escritorio: así
     * la próxima operación remota que toque esos campos sabe que esta edición
     * local es más reciente y la respeta.
     */
    suspend fun registrarLocal(
        tabla: String,
        filaUuid: String,
        opId: String,
        campos: JsonObject,
        momentoIso: String,
        dispositivo: String,
        borrado: Boolean = false,
    ) {
        for ((campo, valor) in campos) {
            campoRemotoDao.guardar(
                CampoRemotoEntity(
                    tabla = tabla,
                    filaUuid = filaUuid,
                    campo = campo,
                    valor = Espejo.canonica(valor),
                    opId = opId,
                    dispositivo = dispositivo,
                    actualizadoEn = momentoIso,
                ),
            )
        }
        val version = versionFilaDao.deFila(tabla, filaUuid) ?: VersionFilaEntity(
            tabla = tabla,
            filaUuid = filaUuid,
        )
        val actualizada = if (borrado) {
            version.copy(
                borrado = 1,
                borradoEn = momentoIso,
                borradoOpId = opId,
                borradoDispositivo = dispositivo,
            )
        } else {
            version.copy(
                ultimoOpId = opId,
                actualizadoEn = momentoIso,
                dispositivo = dispositivo,
                borrado = 0,
            )
        }
        versionFilaDao.guardar(actualizada)
    }

    /**
     * Reintenta las operaciones diferidas (faltaba el registro padre).
     *
     * @return Cuántas diferidas quedaron resueltas en esta pasada
     */
    suspend fun reintentarDiferidas(limite: Int = 100): Int {
        val pendientes = entradaDao.pendientes(limite)
        var resueltas = 0
        val agotadas = mutableListOf<String>()
        for (entrada in pendientes) {
            val op = OperacionRemota.desde(entrada)
            when (aplicar(op)) {
                is ResultadoAplicacion.Aplicada,
                is ResultadoAplicacion.Duplicada,
                is ResultadoAplicacion.Ignorada,
                -> {
                    entradaDao.eliminar(entrada.opId)
                    resueltas++
                }

                else -> {
                    entradaDao.marcarIntento(entrada.opId)
                    if (entrada.intentos + 1 > MAX_INTENTOS_DIFERIDA) agotadas += entrada.opId
                }
            }
        }
        if (agotadas.isNotEmpty()) entradaDao.purgar(agotadas)
        return resueltas
    }

    // ==================================================================
    // Borrado
    // ==================================================================

    private suspend fun aplicarBorrado(op: OperacionRemota): ResultadoAplicacion {
        val marca = Marca(valor = "true", opId = op.opId, dispositivo = op.dispositivo, actualizadoEn = op.creadoEn)
        val version = versionFilaDao.deFila(op.tabla, op.filaUuid)?.aVersion()
        val (decision, conflicto) = decidirBorradoSobreActualizacion(version, marca)
        registrarConflicto(op.tabla, op.filaUuid, conflicto)
        if (decision != Decision.BORRAR) {
            return if (decision == Decision.IGNORAR_BORRADO) {
                ResultadoAplicacion.Duplicada
            } else {
                ResultadoAplicacion.Ignorada(MOTIVO_SUPERADA)
            }
        }

        val idLocal = identidadDao.idLocalDe(op.tabla, op.filaUuid)
        val borradoLogico = Espejo.BORRADO_LOGICO[op.tabla]
        when (op.tabla) {
            "registros_moviles" -> {
                val fila = registroDao.buscarPorUuid(op.filaUuid)
                if (fila != null) {
                    registroDao.insertar(
                        fila.copy(
                            eliminado = true,
                            estado = "SINCRONIZADO",
                            ultimaSync = System.currentTimeMillis(),
                        ),
                    )
                }
            }

            else -> {
                if (idLocal != null && borradoLogico != null) {
                    desactivar(op.tabla, idLocal)
                } else if (idLocal != null) {
                    borrarFila(op.tabla, idLocal)
                }
            }
        }

        guardarVersion(op.tabla, op.filaUuid, marca, borrado = true)
        return ResultadoAplicacion.Aplicada
    }

    // ==================================================================
    // Alta y modificación
    // ==================================================================

    private suspend fun aplicarUpsert(op: OperacionRemota): ResultadoAplicacion {
        val payload = op.payload ?: jsonObjectVacio()

        // Marcas entrantes, con la forma canónica del protocolo
        var entrantes = payload.entries.associate { (campo, valor) ->
            campo to Marca(Espejo.canonica(valor), op.opId, op.dispositivo, op.creadoEn)
        }
        if (entrantes.isEmpty()) return ResultadoAplicacion.Duplicada

        // Las claves foráneas llegan como UUID y se traducen a ids locales
        val (traducido, pendientes) = traducirForaneas(op.tabla, payload)
        if (pendientes.isNotEmpty()) {
            diferir(op, MOTIVO_DIFERIDA + ":" + pendientes.sorted().joinToString(","))
            return ResultadoAplicacion.Diferida(MOTIVO_DIFERIDA)
        }
        entrantes = entrantes.mapValues { (campo, marca) ->
            val valor = traducido[campo] ?: return@mapValues marca
            marca.copy(valor = Espejo.canonica(valor))
        }

        // Resolver la fila: identidad global → clave natural → crear
        val resolucion = resolverFila(op.tabla, op.filaUuid, traducido)
        val filaBase: Any? = resolucion.fila
        if (resolucion.error != null) {
            return ResultadoAplicacion.Error(MOTIVO_ERROR + ":" + resolucion.error)
        }

        // Un borrado vigente solo se levanta con una escritura posterior
        var revivir = false
        val version = versionFilaDao.deFila(op.tabla, op.filaUuid)?.aVersion()
        if (version != null && version.borrado) {
            val (decision, conflicto) = decidirBorrado(version, marca = entrantes.values.firstOrNull()
                ?: Marca(null, op.opId, op.dispositivo, op.creadoEn))
            registrarConflicto(op.tabla, op.filaUuid, conflicto)
            when (decision) {
                Decision.MANTENER_BORRADO -> return ResultadoAplicacion.Ignorada(MOTIVO_BORRADA)
                Decision.REVIVIR -> revivir = true
                else -> Unit
            }
        }

        val actuales = campoRemotoDao.deFila(op.tabla, op.filaUuid).associate { fila ->
            fila.campo to Marca(fila.valor, fila.opId, fila.dispositivo, fila.actualizadoEn)
        }

        // Los binarios no viajan en el payload: se programa su descarga
        programarBlobs(op, traducido, filaBase)

        val plan = planificarCampos(op.tabla, op.filaUuid, entrantes, actuales)
        registrarConflictos(op.tabla, op.filaUuid, plan.conflictos)
        if (plan.aplicar.isEmpty() && !revivir && plan.marcas.isEmpty()) {
            return if (plan.conflictos.isNotEmpty()) {
                ResultadoAplicacion.Ignorada(MOTIVO_SUPERADA)
            } else {
                ResultadoAplicacion.Duplicada
            }
        }

        if (plan.aplicar.isNotEmpty() || filaBase == null) {
            val camposAplicar = JsonObject(
                plan.aplicar.keys.associateWith { campo -> traducido[campo] ?: JsonPrimitive("") },
            )
            val nuevaFila = Espejo.aplicar(op.tabla, filaBase, camposAplicar)
                ?: return ResultadoAplicacion.Error(MOTIVO_ERROR + ":tabla sin espejo")
            val creada = guardarFila(op.tabla, op.filaUuid, filaBase, nuevaFila)
            if (creada.error != null) {
                return ResultadoAplicacion.Error(MOTIVO_ERROR + ":" + creada.error)
            }
        }

        if (revivir) revivir(op.tabla, op.filaUuid)
        for ((campo, marca) in plan.marcas) {
            campoRemotoDao.guardar(
                CampoRemotoEntity(
                    tabla = op.tabla,
                    filaUuid = op.filaUuid,
                    campo = campo,
                    valor = marca.valor,
                    opId = marca.opId,
                    dispositivo = marca.dispositivo,
                    actualizadoEn = marca.actualizadoEn,
                ),
            )
        }
        guardarVersion(
            op.tabla,
            op.filaUuid,
            Marca(null, op.opId, op.dispositivo, op.creadoEn),
            borrado = false,
        )
        return ResultadoAplicacion.Aplicada
    }

    // ==================================================================
    // Traducción de claves foráneas (UUID → id local)
    // ==================================================================

    private suspend fun traducirForaneas(
        tabla: String,
        payload: JsonObject,
    ): Pair<JsonObject, List<String>> {
        val foraneas = Espejo.CLAVES_FORANEAS[tabla] ?: return payload to emptyList()
        val resultado = mutableMapOf<String, JsonElement>()
        val pendientes = mutableListOf<String>()
        for ((campo, valor) in payload) {
            val tablaPadre = foraneas[campo]
            if (tablaPadre == null) {
                resultado[campo] = valor
                continue
            }
            val contenido = (valor as? JsonPrimitive)?.contentOrNull
            if (contenido == null) {
                resultado[campo] = valor
                continue
            }
            if (contenido.all { it in '0'..'9' }) {
                // Un id local en el payload sería un eco de otro equipo: se
                // interpreta como identidad ya resuelta (clientes antiguos).
                resultado[campo] = valor
                continue
            }
            val idLocal = identidadDao.idLocalDe(tablaPadre, contenido)
            if (idLocal == null) {
                pendientes += campo
                continue
            }
            resultado[campo] = JsonPrimitive(idLocal)
        }
        return JsonObject(resultado) to pendientes
    }

    // ==================================================================
    // Resolución de la fila destino
    // ==================================================================

    private data class Resolucion(val fila: Any?, val error: String? = null)

    private suspend fun resolverFila(
        tabla: String,
        filaUuid: String,
        payload: JsonObject,
    ): Resolucion {
        if (tabla == "registros_moviles") {
            return Resolucion(registroDao.buscarPorUuid(filaUuid))
        }

        // 1. La identidad ya conocida
        val idLocal = identidadDao.idLocalDe(tabla, filaUuid)
        if (idLocal != null) {
            buscarPorId(tabla, idLocal)?.let { return Resolucion(it) }
        }

        // 2. Clave natural (el mismo registro creado en otro equipo)
        val clave = Espejo.CLAVE_NATURAL[tabla]
        if (clave != null) {
            val valor = Espejo.texto(payload, clave)
            if (!valor.isNullOrBlank()) {
                buscarPorClaveNatural(tabla, clave, valor)?.let { encontrada ->
                    identidadDao.vincular(IdentidadEntity(tabla, filaUuid, idDe(encontrada)))
                    return Resolucion(encontrada)
                }
            }
        }

        // 3. Clave natural compuesta (solo evaluable con los padres ya traducidos)
        val compuesta = Espejo.CLAVE_NATURAL_COMPUESTA[tabla]
        if (compuesta != null) {
            val valores = compuesta.map { columna ->
                when {
                    columna.endsWith("_id") -> Espejo.entero(payload, columna)?.toLong()
                    else -> Espejo.texto(payload, columna)
                }
            }
            if (valores.all { it != null }) {
                buscarPorClaveCompuesta(tabla, valores)?.let { encontrada ->
                    identidadDao.vincular(IdentidadEntity(tabla, filaUuid, idDe(encontrada)))
                    return Resolucion(encontrada)
                }
            }
        }

        // 4. Crear la fila y vincular su identidad
        val nueva = Espejo.aplicar(tabla, null, payload)
            ?: return Resolucion(null, "tabla sin espejo")
        val id = insertarNueva(tabla, nueva)
        return if (id == null || id <= 0L) {
            Resolucion(null, "rechazada por una restricción de la base local")
        } else {
            identidadDao.vincular(IdentidadEntity(tabla, filaUuid, id))
            Resolucion(nueva)
        }
    }

    private fun idDe(fila: Any): Long = when (fila) {
        is EmpleadoEntity -> fila.id
        is DocumentoEntity -> fila.id
        is IncidenciaEntity -> fila.id
        is ContratoEntity -> fila.id
        is PagoEntity -> fila.id
        is EstudianteEntity -> fila.id
        is PeriodoAcademicoEntity -> fila.id
        is GradoEntity -> fila.id
        is MatriculaEntity -> fila.id
        is NotaFinalEntity -> fila.id
        is ConfiguracionEntity -> fila.id
        else -> 0L
    }

    private suspend fun buscarPorId(tabla: String, id: Long): Any? = when (tabla) {
        "empleados" -> empleadoDao.buscarPorId(id)
        "documentos" -> documentoDao.buscarPorId(id)
        "incidencias" -> incidenciaDao.buscarPorId(id)
        "contratos" -> contratoDao.buscarPorId(id)
        "pagos" -> pagoDao.buscarPorId(id)
        "estudiantes" -> estudianteDao.buscarPorId(id)
        "periodos_academicos" -> periodoDao.buscarPorId(id)
        "grados" -> gradoDao.buscarPorId(id)
        "matriculas" -> matriculaDao.buscarPorId(id)
        "notas_finales" -> notaDao.buscarPorId(id)
        "configuraciones" -> configuracionDao.buscarPorId(id)
        else -> null
    }

    private suspend fun buscarPorClaveNatural(tabla: String, clave: String, valor: String): Any? =
        when (tabla to clave) {
            "empleados" to "cedula" -> empleadoDao.buscarPorCedula(valor)
            "contratos" to "numero" -> contratoDao.buscarPorNumero(valor)
            "estudiantes" to "cedula" -> estudianteDao.buscarPorCedula(valor)
            "periodos_academicos" to "nombre" -> periodoDao.buscarPorNombre(valor)
            "configuraciones" to "clave" -> configuracionDao.buscarPorClave(valor)
            else -> null
        }

    @Suppress("UNCHECKED_CAST")
    private suspend fun buscarPorClaveCompuesta(tabla: String, valores: List<Any?>): Any? =
        when (tabla) {
            "grados" -> gradoDao.buscarPorClave(
                valores[0] as Long,
                valores[1] as String,
                valores[2] as String,
            )

            "matriculas" -> matriculaDao.buscarPorPar(valores[0] as Long, valores[1] as Long)
            "notas_finales" -> notaDao.buscarPorClave(
                valores[0] as Long,
                valores[1] as Long,
                valores[2] as String,
            )

            else -> null
        }

    /** Guarda la fila resultante de la mezcla (creada o actualizada) */
    private data class Guardado(val error: String? = null)

    private suspend fun guardarFila(
        tabla: String,
        filaUuid: String,
        base: Any?,
        nueva: Any,
    ): Guardado {
        if (tabla == "registros_moviles") {
            val registro = nueva as RegistroEntity
            registroDao.insertar(
                registro.copy(estado = "SINCRONIZADO", ultimaSync = System.currentTimeMillis()),
            )
            return Guardado()
        }
        if (base == null) {
            val id = insertarNueva(tabla, nueva)
            return if (id == null || id <= 0L) {
                Guardado("rechazada por una restricción de la base local")
            } else {
                identidadDao.vincular(IdentidadEntity(tabla, filaUuid, id))
                Guardado()
            }
        }
        when (tabla) {
            "empleados" -> empleadoDao.actualizar(nueva as EmpleadoEntity)
            "documentos" -> documentoDao.actualizar(nueva as DocumentoEntity)
            "incidencias" -> incidenciaDao.actualizar(nueva as IncidenciaEntity)
            "contratos" -> contratoDao.actualizar(nueva as ContratoEntity)
            "pagos" -> pagoDao.actualizar(nueva as PagoEntity)
            "estudiantes" -> estudianteDao.actualizar(nueva as EstudianteEntity)
            "periodos_academicos" -> periodoDao.actualizar(nueva as PeriodoAcademicoEntity)
            "grados" -> gradoDao.actualizar(nueva as GradoEntity)
            "matriculas" -> matriculaDao.actualizar(nueva as MatriculaEntity)
            "notas_finales" -> notaDao.actualizar(nueva as NotaFinalEntity)
            "configuraciones" -> configuracionDao.actualizar(nueva as ConfiguracionEntity)
        }
        return Guardado()
    }

    private suspend fun insertarNueva(tabla: String, fila: Any): Long? = when (tabla) {
        "empleados" -> empleadoDao.insertar(fila as EmpleadoEntity)
        "documentos" -> documentoDao.insertar(fila as DocumentoEntity)
        "incidencias" -> incidenciaDao.insertar(fila as IncidenciaEntity)
        "contratos" -> contratoDao.insertar(fila as ContratoEntity)
        "pagos" -> pagoDao.insertar(fila as PagoEntity)
        "estudiantes" -> estudianteDao.insertar(fila as EstudianteEntity)
        "periodos_academicos" -> periodoDao.insertar(fila as PeriodoAcademicoEntity)
        "grados" -> gradoDao.insertar(fila as GradoEntity)
        "matriculas" -> matriculaDao.insertar(fila as MatriculaEntity)
        "notas_finales" -> notaDao.insertar(fila as NotaFinalEntity)
        "configuraciones" -> configuracionDao.insertar(fila as ConfiguracionEntity)
        else -> null
    }

    /** Aplica la semántica de borrado lógico de cada tabla (`activo`/`activa`) */
    private suspend fun desactivar(tabla: String, id: Long) {
        when (tabla) {
            "empleados" -> empleadoDao.buscarPorId(id)?.let {
                empleadoDao.actualizar(it.copy(activo = 0))
            }

            "documentos" -> documentoDao.buscarPorId(id)?.let {
                documentoDao.actualizar(it.copy(activo = 0))
            }

            "estudiantes" -> estudianteDao.buscarPorId(id)?.let {
                estudianteDao.actualizar(it.copy(activo = 0))
            }

            "matriculas" -> matriculaDao.buscarPorId(id)?.let {
                matriculaDao.actualizar(it.copy(activa = 0))
            }

            else -> borrarFila(tabla, id)
        }
    }

    private suspend fun borrarFila(tabla: String, id: Long) {
        when (tabla) {
            "empleados" -> empleadoDao.borrar(id)
            "documentos" -> documentoDao.borrar(id)
            "incidencias" -> incidenciaDao.borrar(id)
            "contratos" -> contratoDao.borrar(id)
            "pagos" -> pagoDao.borrar(id)
            "estudiantes" -> estudianteDao.borrar(id)
            "periodos_academicos" -> periodoDao.borrar(id)
            "grados" -> gradoDao.borrar(id)
            "matriculas" -> matriculaDao.borrar(id)
            "notas_finales" -> notaDao.borrar(id)
            "configuraciones" -> configuracionDao.borrar(id)
        }
    }

    private suspend fun revivir(tabla: String, filaUuid: String) {
        val idLocal = identidadDao.idLocalDe(tabla, filaUuid) ?: return
        when (tabla) {
            "empleados" -> empleadoDao.buscarPorId(idLocal)?.let {
                empleadoDao.actualizar(it.copy(activo = 1))
            }

            "documentos" -> documentoDao.buscarPorId(idLocal)?.let {
                documentoDao.actualizar(it.copy(activo = 1))
            }

            "estudiantes" -> estudianteDao.buscarPorId(idLocal)?.let {
                estudianteDao.actualizar(it.copy(activo = 1))
            }

            "matriculas" -> matriculaDao.buscarPorId(idLocal)?.let {
                matriculaDao.actualizar(it.copy(activa = 1))
            }

            "registros_moviles" -> registroDao.buscarPorUuid(filaUuid)?.let {
                registroDao.insertar(
                    it.copy(eliminado = false, estado = "SINCRONIZADO", ultimaSync = System.currentTimeMillis()),
                )
            }
        }
    }

    // ==================================================================
    // Binarios
    // ==================================================================

    /**
     * Programa la descarga de los binarios que el payload anuncia por hash.
     *
     * El contenido nunca viaja en el payload: aquí solo queda qué hash hace
     * falta bajar y para qué fila y columna sirve. Si la fila ya tiene ese
     * mismo contenido, no se programa nada.
     */
    private suspend fun programarBlobs(op: OperacionRemota, payload: JsonObject, fila: Any?) {
        val columnas = when (op.tabla) {
            "documentos" -> mapOf("contenido_binario" to (fila as? DocumentoEntity)?.contenidoHash)
            "incidencias" -> mapOf(
                "documento_soporte_binario" to (fila as? IncidenciaEntity)?.documentoSoporteHash,
            )

            else -> return
        }
        for ((columna, hashActual) in columnas) {
            val elemento = payload[columna] ?: continue
            if (elemento !is kotlinx.serialization.json.JsonObject || "__blob__" !in elemento) continue
            val hash = Espejo.hashBlob(payload, columna) ?: continue
            if (hash == hashActual) continue
            val tamano = Espejo.tamanoBlob(payload, columna) ?: 0
            val estado = if (tamano > MAX_BLOB_BYTES) ESTADO_BLOB_OMITIDO else ESTADO_BLOB_POR_BAJAR
            val ahora = System.currentTimeMillis()
            blobDao.guardar(
                BlobPendienteEntity(
                    hash = hash,
                    tamano = tamano,
                    tabla = op.tabla,
                    filaUuid = op.filaUuid,
                    columna = columna,
                    direccion = "entrada",
                    estado = estado,
                    intentos = 0,
                    creadoEn = ahora,
                    actualizadoEn = ahora,
                ),
            )
        }
    }

    /**
     * Guarda el contenido descargado de un binario en su fila.
     *
     * @return true si el contenido coincide con su hash y quedó guardado
     */
    suspend fun guardarContenidoDescargado(blob: BlobPendienteEntity, contenido: ByteArray): Boolean {
        if (hashSha256(contenido) != blob.hash) return false
        when (blob.tabla) {
            "documentos" -> {
                val idLocal = identidadDao.idLocalDe(blob.tabla, blob.filaUuid) ?: return false
                val documento = documentoDao.buscarPorId(idLocal) ?: return false
                documentoDao.actualizar(
                    documento.copy(contenidoBinario = contenido, tamanoBytes = contenido.size),
                )
            }

            "incidencias" -> {
                val idLocal = identidadDao.idLocalDe(blob.tabla, blob.filaUuid) ?: return false
                val incidencia = incidenciaDao.buscarPorId(idLocal) ?: return false
                incidenciaDao.actualizar(
                    incidencia.copy(
                        documentoSoporteBinario = contenido,
                        documentoSoporteHash = blob.hash,
                    ),
                )
            }

            else -> return false
        }
        blobDao.eliminar(blob.hash)
        return true
    }

    // ==================================================================
    // Motor de mezcla (funciones puras, espejo de merge.py)
    // ==================================================================

    /** Última escritura conocida de un campo */
    data class Marca(
        val valor: String?,
        val opId: String,
        val dispositivo: String,
        val actualizadoEn: String,
    ) {
        /** Orden total y determinista: (actualizado_en, dispositivo, op_id) */
        fun compararCon(otra: Marca): Int {
            val porMomento = actualizadoEn.compareTo(otra.actualizadoEn)
            if (porMomento != 0) return porMomento
            val porDispositivo = dispositivo.compareTo(otra.dispositivo)
            if (porDispositivo != 0) return porDispositivo
            return opId.compareTo(otra.opId)
        }

        fun esLaMismaOperacion(otra: Marca): Boolean = opId == otra.opId
    }

    private enum class Decision { APLICAR, IGNORAR_ANTIGUA, IGNORAR_IDENTICA, REPETIDA }

    private data class ConflictoInterno(
        val campo: String,
        val valorLocal: String?,
        val valorRemoto: String?,
        val ganador: String,
        val regla: String,
        val opLocalId: String?,
        val opRemotoId: String?,
    )

    private data class Plan(
        val aplicar: Map<String, Marca>,
        val marcas: Map<String, Marca>,
        val conflictos: List<ConflictoInterno>,
    ) {
        val sinCambios: Boolean get() = aplicar.isEmpty()
    }

    private fun decidirCampo(actual: Marca?, entrante: Marca): Decision = when {
        actual == null -> Decision.APLICAR
        entrante.esLaMismaOperacion(actual) -> Decision.REPETIDA
        entrante.valor == actual.valor -> Decision.IGNORAR_IDENTICA
        entrante.compararCon(actual) > 0 -> Decision.APLICAR
        else -> Decision.IGNORAR_ANTIGUA
    }

    private fun planificarCampos(
        tabla: String,
        filaUuid: String,
        entrantes: Map<String, Marca>,
        actuales: Map<String, Marca>,
    ): Plan {
        val aplicar = mutableMapOf<String, Marca>()
        val marcas = mutableMapOf<String, Marca>()
        val conflictos = mutableListOf<ConflictoInterno>()
        val sensibles = CAMPOS_SENSIBLES[tabla].orEmpty()

        for ((campo, entrante) in entrantes) {
            val actual = actuales[campo]
            when (decidirCampo(actual, entrante)) {
                Decision.REPETIDA -> Unit

                Decision.IGNORAR_IDENTICA -> {
                    // El valor no cambia, pero la marca debe avanzar si la
                    // escritura entrante es más reciente: conservar la marca
                    // vieja permitiría que una operación intermedia, al llegar
                    // fuera de orden, pisara un valor ya reemplazado.
                    if (actual != null && entrante.compararCon(actual) > 0) marcas[campo] = entrante
                }

                Decision.APLICAR -> {
                    aplicar[campo] = entrante
                    marcas[campo] = entrante
                    if (actual != null && actual.valor != entrante.valor && campo in sensibles) {
                        conflictos += ConflictoInterno(
                            campo = campo,
                            valorLocal = actual.valor,
                            valorRemoto = entrante.valor,
                            ganador = GANADOR_REMOTO,
                            regla = "$REGLA_CAMPO_SENSIBLE:${evaluarReloj(actual.actualizadoEn, entrante.actualizadoEn)}",
                            opLocalId = actual.opId,
                            opRemotoId = entrante.opId,
                        )
                    }
                }

                Decision.IGNORAR_ANTIGUA -> {
                    conflictos += ConflictoInterno(
                        campo = campo,
                        valorLocal = actual?.valor,
                        valorRemoto = entrante.valor,
                        ganador = GANADOR_LOCAL,
                        regla = if (actual != null) {
                            evaluarReloj(entrante.actualizadoEn, actual.actualizadoEn)
                        } else {
                            REGLA_MAS_RECIENTE
                        },
                        opLocalId = actual?.opId,
                        opRemotoId = entrante.opId,
                    )
                }
            }
        }
        return Plan(aplicar, marcas, conflictos)
    }

    // ------------------------------------------------------------------
    // Borrados y versiones
    // ------------------------------------------------------------------

    private enum class DecisionBorrado { BORRAR, MANTENER_BORRADO, REVIVIR, IGNORAR_BORRADO }

    private data class VersionFila(
        val ultimoOpId: String?,
        val actualizadoEn: String?,
        val dispositivo: String?,
        val borrado: Boolean,
        val borradoEn: String?,
        val borradoOpId: String?,
        val borradoDispositivo: String?,
    ) {
        fun marcaUltima(): Marca? {
            val opId = ultimoOpId ?: return null
            val momento = actualizadoEn ?: return null
            return Marca(null, opId, dispositivo.orEmpty(), momento)
        }

        fun marcaBorrado(): Marca? {
            if (!borrado) return null
            val momento = borradoEn ?: return null
            return Marca(null, borradoOpId.orEmpty(), borradoDispositivo.orEmpty(), momento)
        }
    }

    private fun VersionFilaEntity.aVersion() = VersionFila(
        ultimoOpId = ultimoOpId,
        actualizadoEn = actualizadoEn,
        dispositivo = dispositivo,
        borrado = borrado != 0,
        borradoEn = borradoEn,
        borradoOpId = borradoOpId,
        borradoDispositivo = borradoDispositivo,
    )

    /** Un borrado es una escritura más: gana el más reciente (merge.py) */
    private fun decidirBorrado(
        version: VersionFila?,
        marca: Marca,
    ): Pair<DecisionBorrado, ConflictoInterno?> {
        val borrado = version?.marcaBorrado() ?: return DecisionBorrado.BORRAR to null
        if (marca.esLaMismaOperacion(borrado)) return DecisionBorrado.IGNORAR_BORRADO to null
        return if (marca.compararCon(borrado) >= 0) {
            DecisionBorrado.REVIVIR to ConflictoInterno(
                campo = "__borrado__",
                valorLocal = "true",
                valorRemoto = null,
                ganador = GANADOR_REMOTO,
                regla = REGLA_REVIVE,
                opLocalId = borrado.opId,
                opRemotoId = marca.opId,
            )
        } else {
            DecisionBorrado.MANTENER_BORRADO to ConflictoInterno(
                campo = "__borrado__",
                valorLocal = "true",
                valorRemoto = null,
                ganador = GANADOR_LOCAL,
                regla = REGLA_ACTUALIZACION_TARDIA,
                opLocalId = borrado.opId,
                opRemotoId = marca.opId,
            )
        }
    }

    private fun decidirBorradoSobreActualizacion(
        version: VersionFila?,
        marca: Marca,
    ): Pair<DecisionBorrado, ConflictoInterno?> {
        val ultima = version?.marcaUltima() ?: return DecisionBorrado.BORRAR to null
        if (marca.esLaMismaOperacion(ultima)) return DecisionBorrado.IGNORAR_BORRADO to null
        if (marca.compararCon(ultima) >= 0) return DecisionBorrado.BORRAR to null
        return DecisionBorrado.MANTENER_BORRADO to ConflictoInterno(
            campo = "__borrado__",
            valorLocal = "false",
            valorRemoto = "true",
            ganador = GANADOR_LOCAL,
            regla = REGLA_BORRADO_ANTIGUO,
            opLocalId = ultima.opId,
            opRemotoId = marca.opId,
        )
    }

    private fun guardarVersion(
        tabla: String,
        filaUuid: String,
        marca: Marca,
        borrado: Boolean,
    ) {
        val version = versionFilaDao.deFila(tabla, filaUuid) ?: VersionFilaEntity(
            tabla = tabla,
            filaUuid = filaUuid,
        )
        val actualizada = if (borrado) {
            version.copy(
                borrado = 1,
                borradoEn = marca.actualizadoEn,
                borradoOpId = marca.opId,
                borradoDispositivo = marca.dispositivo,
            )
        } else {
            version.copy(
                ultimoOpId = marca.opId,
                actualizadoEn = marca.actualizadoEn,
                dispositivo = marca.dispositivo,
                borrado = 0,
            )
        }
        versionFilaDao.guardar(actualizada)
    }

    // ------------------------------------------------------------------
    // Conflictos y diferidas
    // ------------------------------------------------------------------

    private suspend fun registrarConflicto(
        tabla: String,
        filaUuid: String,
        conflicto: ConflictoInterno?,
    ) {
        if (conflicto == null) return
        registrarConflictos(tabla, filaUuid, listOf(conflicto))
    }

    private suspend fun registrarConflictos(
        tabla: String,
        filaUuid: String,
        conflictos: List<ConflictoInterno>,
    ) {
        for (conflicto in conflictos) {
            conflictoDao.insertar(
                ConflictoEntity(
                    tabla = tabla,
                    filaUuid = filaUuid,
                    titulo = "$tabla/${filaUuid.take(8)}",
                    campo = conflicto.campo,
                    valorLocal = conflicto.valorLocal.orEmpty(),
                    valorRemoto = conflicto.valorRemoto.orEmpty(),
                    ganador = conflicto.ganador,
                    regla = conflicto.regla,
                    momento = System.currentTimeMillis(),
                    revisado = false,
                ),
            )
        }
    }

    /** Guarda la operación para reintentarla cuando llegue su registro padre */
    private suspend fun diferir(op: OperacionRemota, motivo: String) {
        entradaDao.encolar(
            OperacionEntradaEntity(
                opId = op.opId,
                tabla = op.tabla,
                filaUuid = op.filaUuid,
                operacion = op.operacion,
                payload = op.payload?.toString() ?: "{}",
                creadoEn = Fechas.desdeIso(op.creadoEn) ?: System.currentTimeMillis(),
                creadoEnIso = op.creadoEn,
                motivo = motivo,
            ),
        )
    }

    // ==================================================================
    // Utilidades
    // ==================================================================

    /**
     * Clasifica la relación entre dos marcas de tiempo.
     *
     * Dentro de la ventana de 2 segundos se consideran simultáneas (los
     * relojes de dos equipos nunca están perfectamente sincronizados) y el
     * desempate es el dispositivo.
     */
    private fun evaluarReloj(inicial: String, final: String): String {
        val a = Fechas.desdeIso(inicial)
        val b = Fechas.desdeIso(final)
        if (a == null || b == null) return REGLA_MAS_RECIENTE
        return if (b - a <= EPSILON_RELOJ_MILLIS) REGLA_SIMULTANEA else REGLA_MAS_RECIENTE
    }

    private fun hashSha256(contenido: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(contenido).joinToString("") { "%02x".format(it) }

    // ==================================================================
    // Resultados y constantes
    // ==================================================================

    sealed interface ResultadoAplicacion {
        data class Aplicada(val conflictos: Int = 0) : ResultadoAplicacion
        data object Duplicada : ResultadoAplicacion
        data class Diferida(val motivo: String) : ResultadoAplicacion
        data class Ignorada(val motivo: String) : ResultadoAplicacion
        data class Error(val motivo: String) : ResultadoAplicacion
    }

    /** Operación del protocolo, ya deserializada */
    data class OperacionRemota(
        val opId: String,
        val tabla: String,
        val filaUuid: String,
        val operacion: String,
        val payload: JsonObject?,
        val dispositivo: String,
        val usuario: String?,
        val creadoEn: String,
    ) {
        companion object {
            fun desde(dto: OperacionDto): OperacionRemota = OperacionRemota(
                opId = dto.opId,
                tabla = dto.tabla,
                filaUuid = dto.filaUuid,
                operacion = dto.operacion,
                payload = textoAJsonObject(dto.payload),
                dispositivo = dto.dispositivo,
                usuario = dto.usuario,
                creadoEn = dto.creadoEn,
            )

            fun desde(entrada: OperacionEntradaEntity): OperacionRemota = OperacionRemota(
                opId = entrada.opId,
                tabla = entrada.tabla,
                filaUuid = entrada.filaUuid,
                operacion = entrada.operacion,
                payload = textoAJsonObject(entrada.payload),
                dispositivo = "",
                usuario = null,
                creadoEn = entrada.creadoEnIso.ifBlank {
                    Fechas.isoDesde(entrada.creadoEn)
                },
            )
        }
    }

    companion object {
        const val MOTIVO_TABLA_DESCONOCIDA = "tabla_no_sincronizable"
        const val MOTIVO_DUPLICADA = "duplicada"
        const val MOTIVO_DIFERIDA = "diferida_sin_padre"
        const val MOTIVO_SUPERADA = "superada_por_una_escritura_mas_reciente"
        const val MOTIVO_BORRADA = "fila_borrada_en_el_nodo_central"
        const val MOTIVO_ERROR = "error_al_aplicar"
        const val MOTIVO_SIN_IDENTIDAD = "operacion_sin_op_id"

        const val ESTADO_BLOB_POR_BAJAR = "por_bajar"
        const val ESTADO_BLOB_OMITIDO = "omitido"

        private const val GANADOR_LOCAL = "local"
        private const val GANADOR_REMOTO = "remoto"
        private const val REGLA_MAS_RECIENTE = "escritura_mas_reciente"
        private const val REGLA_SIMULTANEA = "escritura_simultanea_desempate_dispositivo"
        private const val REGLA_CAMPO_SENSIBLE = "campo_sensible_revisar"
        private const val REGLA_REVIVE = "actualizacion_posterior_al_borrado"
        private const val REGLA_ACTUALIZACION_TARDIA = "borrado_posterior_ignora_actualizacion"
        private const val REGLA_BORRADO_ANTIGUO = "borrado_antiguo_ignorado"

        private const val EPSILON_RELOJ_MILLIS = 2_000L
        private const val MAX_INTENTOS_DIFERIDA = 10

        /** Tamaño máximo de binario que se transfiere en un teléfono */
        const val MAX_BLOB_BYTES = 8 * 1024 * 1024

        /**
         * Campos cuyo choque se registra siempre, aunque la regla general lo
         * resuelva sola: son importes y condiciones económicas que conviene
         * poder auditar. Idéntica a `merge.CAMPOS_SENSIBLES` del escritorio.
         */
        val CAMPOS_SENSIBLES: Map<String, Set<String>> = mapOf(
            "empleados" to setOf("salario_base"),
            "pagos" to setOf(
                "monto_bruto", "monto_neto", "descuentos", "bonificaciones", "horas_extra",
                "salario_base", "deduccion_seguro", "deduccion_pension", "deduccion_impuesto",
                "otras_deducciones", "base_gravable", "aguinaldo", "bono_vacacional",
            ),
            "contratos" to setOf("salario_pactado", "liquidacion_monto"),
            "notas_finales" to setOf("calificacion"),
        )
    }
}
