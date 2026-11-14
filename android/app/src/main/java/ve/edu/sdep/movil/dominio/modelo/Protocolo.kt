package ve.edu.sdep.movil.dominio.modelo

/**
 * Contrato del protocolo con el nodo central (lado del cliente).
 *
 * Un solo lugar para lo que esta aplicación habla y espera: la versión del
 * protocolo, las secciones que el nodo puede anunciar y la regla de
 * compatibilidad que usa la negociación automática antes de emparejar,
 * sincronizar o mostrar módulos.
 *
 * Espejo deliberado del lado servidor (`VERSION_PROTOCOLO`,
 * `CAPACIDADES_PROTOCOLO` en `sync_agent/servidor.py`). Ningún otro archivo
 * debería inventar versiones ni nombres de capacidad.
 */
object Protocolo {

    /** Versión del protocolo que esta aplicación habla */
    const val VERSION = "2"

    /**
     * Secciones de la API que el nodo puede anunciar en su `ping`.
     *
     * Una capacidad nueva del servidor no rompe a esta versión de la app: se
     * ignora hasta que la aplicación la conozca. Y una capacidad desconocida
     * nunca habilita un módulo: el filtrado es *fail-closed* hacia el futuro.
     */
    val CAPACIDADES = setOf(
        "auth",
        "consultas",
        "admin",
        "nomina",
        "incidencias",
        "contratos",
        "academicos",
        "archivos",
    )

    /**
     * ¿Puede esta aplicación hablar con el nodo que anuncia ese rango?
     *
     * El nodo publica `[min_version_protocolo, version_protocolo]`: las
     * versiones que todavía acepta. La aplicación entra en el rango si su
     * versión mayor está entre ambas. Un nodo antiguo que no anuncia rango se
     * acepta: su identidad ya se verificó y, si el intercambio real no
     * coincide, el deserializador lo reporta con un mensaje propio.
     */
    fun compatible(versionServidor: String, minVersionServidor: String = ""): Boolean {
        val hablada = numeroDe(VERSION) ?: return true
        val maxima = numeroDe(versionServidor) ?: return true
        val minima = numeroDe(minVersionServidor) ?: 1
        return hablada in minima..maxima
    }

    /** Número mayor de una versión («2», «2.1» → 2); null si no lo trae */
    private fun numeroDe(version: String): Int? =
        version.substringBefore('.').trim().toIntOrNull()
}
