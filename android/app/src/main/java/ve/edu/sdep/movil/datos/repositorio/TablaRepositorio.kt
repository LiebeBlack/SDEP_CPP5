package ve.edu.sdep.movil.datos.repositorio

import androidx.room.withTransaction
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import ve.edu.sdep.movil.datos.local.AplicadorEspejo
import ve.edu.sdep.movil.datos.local.BaseDatosSdep
import ve.edu.sdep.movil.datos.local.Espejo
import ve.edu.sdep.movil.datos.local.EsquemaTabla
import ve.edu.sdep.movil.datos.local.Fechas
import ve.edu.sdep.movil.datos.local.OpcionTabla
import ve.edu.sdep.movil.datos.local.TipoCampo
import ve.edu.sdep.movil.datos.local.dao.IdentidadDao
import ve.edu.sdep.movil.datos.local.dao.OperacionDao
import ve.edu.sdep.movil.datos.local.entidad.IdentidadEntity
import ve.edu.sdep.movil.datos.local.entidad.OperacionPendienteEntity
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.Resultado
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Escritura genérica del espejo.
 *
 * El mismo motor sirve a las diez tablas administrables: lee el esquema real
 * de SQLite, valida con ese esquema, construye la entidad con [Espejo.aplicar]
 * y guarda con la mecánica del sincronizador (identidad global, operación en
 * la cola y marcas de mezcla) dentro de una sola transacción. No hay una copia
 * de las reglas por tabla: si el escritorio añade una columna, el teléfono la
 * escribe sin cambios de código.
 *
 * Los permisos se comprueban dos veces: el módulo con la matriz de roles y la
 * acción concreta (crear, editar, eliminar). La pantalla puede equivocarse;
 * esta capa no.
 */
@Singleton
class TablaRepositorio @Inject constructor(
    private val baseDatos: BaseDatosSdep,
    private val identidadDao: IdentidadDao,
    private val operacionDao: OperacionDao,
    private val aplicador: AplicadorEspejo,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
) {

    /** Columnas editables de la tabla, leídas del esquema real */
    suspend fun columnas(tabla: String): List<ve.edu.sdep.movil.datos.local.ColumnaTabla> =
        withContext(Dispatchers.IO) { EsquemaTabla.columnas(baseDatos, tabla) }

    /** Fila completa por id local (incluye columnas de control) */
    suspend fun cargar(tabla: String, id: Long): Map<String, String?>? =
        withContext(Dispatchers.IO) { cargarDirecto(tabla, id) }

    /**
     * Lectura sin cambio de hilo.
     *
     * Se usa dentro de las transacciones de [guardar] y [eliminar]: la lectura
     * debe ver la misma conexión que la escritura.
     */
    private fun cargarDirecto(tabla: String, id: Long): Map<String, String?>? {
        if (!EsquemaTabla.esAdministrable(tabla)) return null
        val columnas = EsquemaTabla.columnas(baseDatos, tabla).map { it.nombre } +
            listOf("id", "updated_at")
        val sql = "SELECT ${columnas.joinToString(", ")} FROM $tabla WHERE id = ? LIMIT 1"
        return baseDatos.openHelper.readableDatabase.query(sql, arrayOf<Any>(id)).use { cursor ->
            if (!cursor.moveToFirst()) null else leerFila(cursor)
        }
    }

    /** Filas de la tabla, de la más reciente a la más antigua */
    suspend fun listar(tabla: String, limite: Int = 500): List<Map<String, String?>> =
        withContext(Dispatchers.IO) {
            if (!EsquemaTabla.esAdministrable(tabla)) return@withContext emptyList()
            val columnas = columnas(tabla).map { it.nombre } + listOf("id", "updated_at")
            val orden = if ("fecha_inicio" in columnas) "fecha_inicio DESC" else "id DESC"
            val sql = "SELECT ${columnas.joinToString(", ")} FROM $tabla ORDER BY $orden LIMIT $limite"
            baseDatos.openHelper.readableDatabase.query(sql).use { cursor ->
                val filas = mutableListOf<Map<String, String?>>()
                while (cursor.moveToNext()) filas += leerFila(cursor)
                filas
            }
        }

    /** Opciones de una tabla padre, para el selector de clave foránea */
    suspend fun opcionesForaneas(tabla: String): List<OpcionTabla> = withContext(Dispatchers.IO) {
        val etiqueta = when (tabla) {
            "empleados" -> "nombres || ' ' || apellidos || ' · ' || cedula"
            "estudiantes" -> "nombres || ' ' || apellidos || ' · ' || cedula"
            "grados" -> "nombre || ' · ' || seccion"
            "periodos_academicos" -> "nombre"
            "contratos" -> "numero"
            else -> "CAST(id AS TEXT)"
        }
        val sql = "SELECT id, $etiqueta AS etiqueta FROM $tabla ORDER BY etiqueta"
        val opciones = mutableListOf<OpcionTabla>()
        runCatching {
            baseDatos.openHelper.readableDatabase.query(sql).use { cursor ->
                while (cursor.moveToNext()) {
                    opciones += OpcionTabla(
                        id = cursor.getLong(0),
                        etiqueta = cursor.getString(1) ?: "Registro ${cursor.getLong(0)}",
                    )
                }
            }
        }
        opciones
    }

    /** Crea (``id`` nulo) o modifica una fila de cualquier tabla administrable */
    suspend fun guardar(
        tabla: String,
        id: Long?,
        valores: Map<String, String>,
    ): Resultado<Long> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        if (!EsquemaTabla.esAdministrable(tabla)) {
            return Resultado.Fallo("Esta tabla no se administra desde el teléfono.")
        }
        val modulo = EsquemaTabla.moduloDeTabla(tabla)
            ?: return Resultado.Fallo("El módulo no está disponible en el teléfono.")
        if (!sesion.puedeAbrir(modulo)) {
            return Resultado.Fallo("Su rol no tiene acceso a este módulo.")
        }
        val permiso = if (id == null) Permiso.CREAR else Permiso.EDITAR
        if (!sesion.puede(permiso)) {
            val accion = if (id == null) "crear" else "editar"
            return Resultado.Fallo("El rol «${sesion.rol.etiqueta}» no permite $accion registros.")
        }

        val esquema = columnas(tabla)
        if (esquema.isEmpty()) return Resultado.Fallo("La tabla no tiene columnas editables.")
        val datos = valores.filterKeys { clave -> esquema.any { it.nombre == clave } }
        val problema = withContext(Dispatchers.IO) { validar(tabla, esquema, datos) }
        if (problema != null) return Resultado.Fallo(problema)

        val equipo = configuracionRepositorio.cargar().equipo.ifBlank { "movil" }

        return try {
            baseDatos.withTransaction {
                val base = id?.let { aplicador.filaLocal(tabla, it) }
                if (id != null && base == null) {
                    return@withTransaction Resultado.Fallo(
                        "El registro ya no existe en este equipo. Sincronice e intente de nuevo.",
                    )
                }
                val anterior = id?.let { cargarDirecto(tabla, it) }
                val ahora = maxOf(
                    System.currentTimeMillis(),
                    (Fechas.desdeIso(anterior?.get("updated_at")) ?: 0L) + 1L,
                )
                val iso = Fechas.isoDesde(ahora)

                val campos = camposDe(esquema, datos).toMutableMap()
                campos["updated_at"] = JsonPrimitive(iso)
                if (base == null) campos["created_at"] = JsonPrimitive(iso)

                val nueva = Espejo.aplicar(tabla, base, JsonObject(campos))
                    ?: return@withTransaction Resultado.Fallo("La tabla no admite escritura.")
                val filaUuid = id?.let { identidadDao.uuidDe(tabla, it) } ?: run {
                    val nueva = UUID.randomUUID().toString()
                    // Una fila llegada de un nodo antiguo puede no tener
                    // identidad global: se le asigna antes de anunciar el cambio.
                    if (id != null) identidadDao.vincular(IdentidadEntity(tabla, nueva, id))
                    nueva
                }

                aplicador.guardarFilaLocal(tabla, filaUuid, base, nueva)?.let { motivo ->
                    return@withTransaction Resultado.Fallo(
                        "No se pudo guardar: $motivo.",
                    )
                }
                val localId = identidadDao.idLocalDe(tabla, filaUuid)
                    ?: return@withTransaction Resultado.Fallo(
                        "No se pudo identificar el registro guardado.",
                    )

                val crudo = Espejo.payload(tabla, nueva, base, base == null)
                    ?: return@withTransaction Resultado.Exito(localId)
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
                        estado = ESTADO_PENDIENTE,
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
                Resultado.Exito(localId)
            }
        } catch (error: CancellationException) {
            throw error
        } catch (error: Exception) {
            Resultado.Fallo(
                "No se pudo guardar el registro: ${error.message ?: "error inesperado"}.",
                error,
            )
        }
    }

    /** Baja de una fila, con la semántica de cada tabla */
    suspend fun eliminar(tabla: String, id: Long): Resultado<Unit> {
        val sesion = sesionRepositorio.actual
            ?: return Resultado.Fallo("La sesión se cerró. Vuelva a entrar.")
        if (!EsquemaTabla.esAdministrable(tabla)) {
            return Resultado.Fallo("Esta tabla no se administra desde el teléfono.")
        }
        val modulo = EsquemaTabla.moduloDeTabla(tabla)
            ?: return Resultado.Fallo("El módulo no está disponible en el teléfono.")
        if (!sesion.puedeAbrir(modulo) || !sesion.puede(Permiso.ELIMINAR)) {
            return Resultado.Fallo("El rol «${sesion.rol.etiqueta}» no permite eliminar registros.")
        }
        val equipo = configuracionRepositorio.cargar().equipo.ifBlank { "movil" }

        return try {
            baseDatos.withTransaction {
                if (aplicador.filaLocal(tabla, id) == null) {
                    return@withTransaction Resultado.Fallo("El registro ya no existe en este equipo.")
                }
                val fila = cargarDirecto(tabla, id)
                    ?: return@withTransaction Resultado.Fallo("El registro ya no existe en este equipo.")
                val filaUuid = identidadDao.uuidDe(tabla, id) ?: run {
                    val nueva = UUID.randomUUID().toString()
                    identidadDao.vincular(IdentidadEntity(tabla, nueva, id))
                    nueva
                }
                val ahora = maxOf(
                    System.currentTimeMillis(),
                    (Fechas.desdeIso(fila["updated_at"]) ?: 0L) + 1L,
                )
                val iso = Fechas.isoDesde(ahora)

                aplicador.eliminarLocal(tabla, id)

                val claves = mutableMapOf<String, JsonElement>()
                Espejo.CLAVE_NATURAL[tabla]?.let { columna ->
                    fila[columna]?.let { claves[columna] = JsonPrimitive(it) }
                }
                Espejo.CLAVE_NATURAL_COMPUESTA[tabla]?.forEach { columna ->
                    fila[columna]?.let { claves[columna] = JsonPrimitive(it) }
                }
                val payload = Espejo.conForaneasComoUuid(tabla, JsonObject(claves)) { padre, local ->
                    identidadDao.uuidDe(padre, local)
                }
                val opId = UUID.randomUUID().toString()
                operacionDao.encolar(
                    OperacionPendienteEntity(
                        opId = opId,
                        tabla = tabla,
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
                    tabla = tabla,
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
                "No se pudo eliminar el registro: ${error.message ?: "error inesperado"}.",
                error,
            )
        }
    }

    // ------------------------------------------------------------------
    // Utilidades
    // ------------------------------------------------------------------

    private fun leerFila(cursor: android.database.Cursor): Map<String, String?> {
        val fila = mutableMapOf<String, String?>()
        for (indice in 0 until cursor.columnCount) {
            fila[cursor.getColumnName(indice)] = cursor.getString(indice)
        }
        return fila
    }

    /** Convierte el texto del formulario al tipo JSON que espera el protocolo */
    private fun camposDe(
        columnas: List<ve.edu.sdep.movil.datos.local.ColumnaTabla>,
        datos: Map<String, String>,
    ): Map<String, JsonElement> {
        val campos = mutableMapOf<String, JsonElement>()
        for (columna in columnas) {
            val texto = datos[columna.nombre]?.trim().orEmpty()
            campos[columna.nombre] = when {
                texto.isEmpty() -> JsonNull
                columna.tipo == TipoCampo.ENTERO -> JsonPrimitive(texto.toInt())
                columna.tipo == TipoCampo.DECIMAL -> JsonPrimitive(texto.toDouble())
                columna.tipo == TipoCampo.BOOLEANO ->
                    JsonPrimitive(if (texto == "1" || texto.equals("true", true)) 1 else 0)
                else -> JsonPrimitive(texto)
            }
        }
        return campos
    }

    /** Comprueba obligatorios, números, fechas, listas cerradas y claves foráneas */
    private fun validar(
        tabla: String,
        columnas: List<ve.edu.sdep.movil.datos.local.ColumnaTabla>,
        datos: Map<String, String>,
    ): String? {
        for (columna in columnas) {
            val texto = datos[columna.nombre]?.trim().orEmpty()
            if (columna.requerido && texto.isEmpty()) {
                return "«${columna.etiqueta}» es obligatorio."
            }
            if (texto.isEmpty()) continue
            when (columna.tipo) {
                TipoCampo.ENTERO -> if (texto.toIntOrNull() == null) {
                    return "«${columna.etiqueta}» debe ser un número entero."
                }

                TipoCampo.DECIMAL -> if (texto.toDoubleOrNull() == null) {
                    return "«${columna.etiqueta}» debe ser un número."
                }

                TipoCampo.FECHA -> {
                    val conHora = if (texto.length <= 10) "${texto}T00:00:00" else texto
                    if (Fechas.desdeIso(conHora) == null) {
                        return "«${columna.etiqueta}» debe tener el formato AAAA-MM-DD."
                    }
                }

                TipoCampo.OPCION -> if (texto !in columna.opciones) {
                    return "«${columna.etiqueta}» debe ser uno de: ${columna.opciones.joinToString(", ")}."
                }

                TipoCampo.FORANEA -> {
                    val id = texto.toLongOrNull()
                        ?: return "«${columna.etiqueta}» debe ser un registro válido."
                    val padre = columna.tablaForanea ?: continue
                    val existe = runCatching {
                        baseDatos.openHelper.readableDatabase
                            .query("SELECT 1 FROM $padre WHERE id = ? LIMIT 1", arrayOf<Any>(id))
                            .use { it.moveToFirst() }
                    }.getOrDefault(false)
                    if (!existe) {
                        return "El registro elegido en «${columna.etiqueta}» ya no existe."
                    }
                }

                else -> Unit
            }
        }
        if ("email" in datos.keys) {
            val correo = datos["email"]?.trim().orEmpty()
            if (correo.isNotEmpty() && !correo.contains("@")) {
                return "El correo electrónico no parece válido."
            }
        }
        return null
    }

    private companion object {
        const val ESTADO_PENDIENTE = "PENDIENTE"
    }
}
