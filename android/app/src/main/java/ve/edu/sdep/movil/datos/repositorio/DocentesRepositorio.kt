package ve.edu.sdep.movil.datos.repositorio

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import ve.edu.sdep.movil.datos.remoto.ApiSyncFactory
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Directorio de docentes del nodo central.
 *
 * Las cuentas `usuarios` no se replican entre equipos, pero los grados
 * referencian a su profesor por el UUID global de la cuenta (`profesor_uuid`).
 * Este repositorio consulta `GET /api/v1/consultas/docentes` y devuelve el par
 * UUID → nombre con el que las pantallas resuelven el docente, sin replicar
 * cuentas ni credenciales en el teléfono.
 *
 * Tratamiento de datos de nivel empresarial:
 *
 * * **Caché con vigencia**: el directorio cambia poco (altas de cuentas), así
 *   que se consulta como mucho una vez cada [VIGENCIA_CACHE_MS] y no en cada
 *   entrada a una pantalla.
 * * **Stale-on-error**: si el nodo no responde, se sirve la última copia buena
 *   en vez de dejar las fichas sin nombre por un corte de Wi-Fi.
 * * **Mejor esfuerzo**: sin red, sin sesión o sin vinculación devuelve lo
 *   cacheado (o vacío). Nada de la sincronización depende de esta consulta.
 */
@Singleton
class DocentesRepositorio @Inject constructor(
    private val apiFactory: ApiSyncFactory,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
) {

    private val candado = Mutex()
    private var cache: Map<String, String> = emptyMap()
    private var cacheEn: Long = 0L

    /** Mapa UUID del docente → nombre para mostrar; vacío si nunca se pudo */
    suspend fun directorio(): Map<String, String> = candado.withLock {
        val ahora = System.currentTimeMillis()
        if (cache.isNotEmpty() && ahora - cacheEn < VIGENCIA_CACHE_MS) return@withLock cache

        val fresco = consultar()
        if (fresco.isNotEmpty()) {
            cache = fresco
            cacheEn = ahora
        }
        // Stale-on-error: una consulta fallida no borra la última copia buena.
        fresco.ifEmpty { cache }
    }

    private suspend fun consultar(): Map<String, String> {
        val sesion = sesionRepositorio.actual ?: return emptyMap()
        if (sesion.offline || sesion.token.isBlank()) return emptyMap()
        return try {
            val config = configuracionRepositorio.cargar()
            if (!config.completa) return emptyMap()
            apiFactory.acciones(config, sesion.token).docentes().docentes
                .asSequence()
                .filter { it.uuid.isNotBlank() }
                .associate { it.uuid to it.nombre }
        } catch (error: CancellationException) {
            throw error
        } catch (_: Exception) {
            emptyMap()
        }
    }

    private companion object {
        /** El directorio cambia poco: una consulta por ventana es suficiente */
        const val VIGENCIA_CACHE_MS = 10 * 60 * 1000L
    }
}
