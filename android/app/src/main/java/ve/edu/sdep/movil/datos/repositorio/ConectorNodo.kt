package ve.edu.sdep.movil.datos.repositorio

import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import ve.edu.sdep.movil.datos.remoto.Descubrimiento
import ve.edu.sdep.movil.dominio.modelo.ConfiguracionSync
import ve.edu.sdep.movil.dominio.modelo.Resultado
import ve.edu.sdep.movil.sincronizacion.ProgramadorSync

/**
 * Vinculación automática del teléfono con el nodo central.
 *
 * Es el único punto que conoce el flujo «buscar → emparejar → guardar →
 * programar sincronización». Tanto el login como los ajustes y la
 * sincronización lo usan, de modo que el comportamiento es el mismo en
 * cualquier camino y no queda ningún formulario de configuración.
 *
 * La renovación es silenciosa: si el nodo cambió de IP o se recreó su base y
 * el token dejó de valer, se vuelve a emparejar sin pedir nada al usuario.
 * Entre intentos fallidos hay una espera corta para no encender la radio y
 * recorrer la red en cada reintento automático.
 */
@Singleton
class ConectorNodo @Inject constructor(
    private val descubrimiento: Descubrimiento,
    private val configuracion: ConfiguracionRepositorio,
    private val programador: ProgramadorSync,
) {

    private val candado = Mutex()
    private var ultimoIntento = 0L

    /**
     * Devuelve una vinculación utilizable.
     *
     * Si ya hay una guardada, se devuelve sin tocar la red. Si no, se busca el
     * escritorio y se guarda. Con ``forzar`` se ignora la espera entre
     * reintentos (lo usa el botón «Volver a buscar» y el login).
     */
    suspend fun asegurarConexion(forzar: Boolean = false): Resultado<ConfiguracionSync> =
        candado.withLock {
            val actual = configuracion.cargar()
            if (actual.completa) return@withLock Resultado.Exito(actual)

            if (!forzar && System.currentTimeMillis() - ultimoIntento < ESPERA_ENTRE_BUSQUEDAS_MS) {
                return@withLock Resultado.Fallo(mensajeSinNodo())
            }
            ultimoIntento = System.currentTimeMillis()
            buscarYGuardar(actual.url.takeIf { it.isNotBlank() })
        }

    /**
     * Renueva una vinculación existente porque el token fue rechazado o la
     * dirección cambió. Si la dirección guardada ya no responde, se hace el
     * descubrimiento completo por difusión y subred.
     */
    suspend fun revincular(): Resultado<ConfiguracionSync> = candado.withLock {
        ultimoIntento = System.currentTimeMillis()
        val actual = configuracion.cargar()
        buscarYGuardar(actual.url.takeIf { it.isNotBlank() })
    }

    /** Comprueba que la dirección guardada siga siendo el nodo central */
    suspend fun verificarUrlActual(): Boolean {
        val actual = configuracion.cargar()
        if (!actual.completa) return false
        return withContext(Dispatchers.IO) { descubrimiento.verificar(actual.url) }
    }

    private suspend fun buscarYGuardar(urlPreferida: String?): Resultado<ConfiguracionSync> {
        val vinculo = withContext(Dispatchers.IO) { descubrimiento.descubrir(urlPreferida) }
            ?: return Resultado.Fallo(mensajeSinNodo(), reintentable = true)

        val guardado = configuracion.guardar(
            url = vinculo.url,
            equipo = vinculo.equipo,
            token = vinculo.token,
            activa = true,
            periodoMinutos = configuracion.periodoMinutos,
        )
        if (!guardado) {
            return Resultado.Fallo(
                "Se encontró el sistema de escritorio pero no se pudo guardar la " +
                    "vinculación de forma segura. Revise el almacenamiento del teléfono.",
            )
        }

        val config = configuracion.cargar()
        try {
            programador.programar(configuracion.periodoMinutos)
        } catch (_: Throwable) {
            // WorkManager puede no estar disponible en un arranque muy temprano
            // o con la app recién instalada; la sincronización manual sigue.
        }
        return Resultado.Exito(config)
    }

    private fun mensajeSinNodo(): String =
        "No se encontró el sistema de escritorio en esta red. Compruebe que la " +
            "aplicación de escritorio esté abierta y que el teléfono esté en la misma Wi-Fi."

    private companion object {
        const val ESPERA_ENTRE_BUSQUEDAS_MS = 20_000L
    }
}
