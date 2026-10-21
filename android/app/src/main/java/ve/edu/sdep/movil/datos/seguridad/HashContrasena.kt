package ve.edu.sdep.movil.datos.seguridad

import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Derivación y verificación de contraseñas con PBKDF2-HMAC-SHA256.
 *
 * Una contraseña nunca se guarda, ni en claro ni con un hash simple. Se guarda
 * la sal aleatoria, el número de iteraciones y la clave derivada, en el formato
 * ``pbkdf2_sha256$<iteraciones>$<sal>$<hash>``. Verificar vuelve a derivar con
 * la misma sal y compara en tiempo constante, de modo que un atacante con
 * acceso a la base no puede probar candidatos midiendo cuánto tarda la
 * comparación.
 */
@Singleton
class HashContrasena @Inject constructor() {

    fun crear(contrasena: CharArray, iteraciones: Int = ITERACIONES): String {
        val sal = ByteArray(BYTES_SAL).also { SecureRandom().nextBytes(it) }
        val derivada = derivar(contrasena, sal, iteraciones)
        return "$PREFIJO$$iteraciones$${codificar(sal)}$${codificar(derivada)}"
    }

    fun verificar(contrasena: CharArray, almacenado: String): Boolean {
        // Formato del escritorio Python (SecurityValidator): pbkdf2$<iter>$<sal hex>$<hash hex>.
        // El teléfono no valida el login localmente (lo hace el nodo central),
        // pero sí recibe hashes de la base en algunas operaciones administrativas
        // y este formato debe poder comprobarse sin reimplementar nada.
        if (almacenado.startsWith("$PREFIJO_ESCRITORIO$")) {
            return verificarEscritorio(contrasena, almacenado)
        }
        val partes = almacenado.split('$')
        if (partes.size != 4 || partes[0] != PREFIJO) return false
        val iteraciones = partes[1].toIntOrNull() ?: return false
        // Un registro manipulado con 0 iteraciones haría fallar la derivación;
        // uno con millones convertiría el ingreso en una denegación de servicio.
        if (iteraciones < 1 || iteraciones > 2_000_000) return false
        val sal = decodificar(partes[2]) ?: return false
        val esperado = decodificar(partes[3]) ?: return false
        if (sal.isEmpty() || esperado.isEmpty()) return false
        val calculado = derivar(contrasena, sal, iteraciones)
        return MessageDigest.isEqual(esperado, calculado)
    }

    /**
     * Verificación del formato del escritorio: pbkdf2$<iteraciones>$<sal hex>$<hash hex>.
     *
     * El mismo algoritmo (PBKDF2-HMAC-SHA256) y el mismo comparador en tiempo
     * constante que usa `SecurityValidator.verify_password` de Python; aquí se
     * reproduce la parte de verificación con los mismos límites de iteraciones.
     */
    private fun verificarEscritorio(contrasena: CharArray, almacenado: String): Boolean {
        val partes = almacenado.split('$')
        if (partes.size != 4) return false
        val iteraciones = partes[1].toIntOrNull() ?: return false
        if (iteraciones < 1 || iteraciones > 2_000_000) return false
        val sal = decodificarHex(partes[2]) ?: return false
        val esperado = decodificarHex(partes[3]) ?: return false
        if (sal.isEmpty() || esperado.isEmpty()) return false
        val calculado = derivar(contrasena, sal, iteraciones)
        return MessageDigest.isEqual(esperado, calculado)
    }

    /** Hash de un token aleatorio (se usa para el desbloqueo biométrico) */
    fun hashRapido(valor: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
        return codificar(digest.digest(valor.toByteArray(Charsets.UTF_8)))
    }

    private fun derivar(contrasena: CharArray, sal: ByteArray, iteraciones: Int): ByteArray {
        val especificacion = PBEKeySpec(contrasena, sal, iteraciones, BYTES_CLAVE * 8)
        return try {
            val fabrica = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
            fabrica.generateSecret(especificacion).encoded
        } finally {
            especificacion.clearPassword()
        }
    }

    private fun codificar(datos: ByteArray): String =
        Base64.getEncoder().withoutPadding().encodeToString(datos)

    private fun decodificar(texto: String): ByteArray? = try {
        Base64.getDecoder().decode(texto)
    } catch (_: IllegalArgumentException) {
        null
    }

    private fun decodificarHex(texto: String): ByteArray? {
        if (texto.isEmpty() || texto.length % 2 != 0) return null
        if (!texto.all { it in '0'..'9' || it in 'a'..'f' || it in 'A'..'F' }) return null
        return ByteArray(texto.length / 2) { indice ->
            texto.substring(indice * 2, indice * 2 + 2).toInt(16).toByte()
        }
    }

    companion object {
        private const val PREFIJO = "pbkdf2_sha256"
        private const val PREFIJO_ESCRITORIO = "pbkdf2"

        /**
         * Coste de la derivación. 120 000 iteraciones tardan unas décimas de
         * segundo en un teléfono de gama media: suficiente para el ingreso
         * manual y costoso para una fuerza bruta fuera del dispositivo.
         */
        const val ITERACIONES = 120_000
        private const val BYTES_SAL = 16
        private const val BYTES_CLAVE = 32
    }
}
