package ve.edu.sdep.movil.datos.repositorio

import kotlinx.coroutines.CancellationException
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
 * Es una consulta de mejor esfuerzo: sin red o sin sesión devuelve un mapa
 * vacío y las fichas muestran el campo como sin resolver. Nada de la
 * sincronización depende de ella.
 */
@Singleton
class DocentesRepositorio @Inject constructor(
    private val apiFactory: ApiSyncFactory,
    private val configuracionRepositorio: ConfiguracionRepositorio,
    private val sesionRepositorio: SesionRepositorio,
) {

    /** Mapa UUID del docente → nombre para mostrar; vacío si no se pudo */
    suspend fun directorio(): Map<String, String> {
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
}
