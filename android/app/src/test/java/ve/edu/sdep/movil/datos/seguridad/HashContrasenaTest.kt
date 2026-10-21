package ve.edu.sdep.movil.datos.seguridad

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * La contraseña no se guarda: se guarda su derivación. Estas pruebas fijan las
 * propiedades de las que depende la seguridad del ingreso.
 */
class HashContrasenaTest {

    private val hash = HashContrasena()

    @Test
    fun `la contrasena correcta se verifica`() {
        val almacenado = hash.crear("ClaveSegura123".toCharArray())
        assertTrue(hash.verificar("ClaveSegura123".toCharArray(), almacenado))
    }

    @Test
    fun `una contrasena distinta no se verifica`() {
        val almacenado = hash.crear("ClaveSegura123".toCharArray())
        assertFalse(hash.verificar("ClaveSegura124".toCharArray(), almacenado))
        assertFalse(hash.verificar("clavesegura123".toCharArray(), almacenado))
    }

    @Test
    fun `la misma contrasena produce derivaciones distintas`() {
        val primera = hash.crear("ClaveSegura123".toCharArray())
        val segunda = hash.crear("ClaveSegura123".toCharArray())
        assertNotEquals(primera, segunda)
        assertTrue(hash.verificar("ClaveSegura123".toCharArray(), primera))
        assertTrue(hash.verificar("ClaveSegura123".toCharArray(), segunda))
    }

    @Test
    fun `el formato declara algoritmo e iteraciones`() {
        val almacenado = hash.crear("ClaveSegura123".toCharArray(), iteraciones = 1000)
        val partes = almacenado.split('$')
        assertEquals(4, partes.size)
        assertEquals("pbkdf2_sha256", partes[0])
        assertEquals("1000", partes[1])
        assertTrue(partes[2].isNotEmpty())
        assertTrue(partes[3].isNotEmpty())
    }

    @Test
    fun `un registro malformado se rechaza sin lanzar`() {
        assertFalse(hash.verificar("ClaveSegura123".toCharArray(), ""))
        assertFalse(hash.verificar("ClaveSegura123".toCharArray(), "texto"))
        assertFalse(hash.verificar("ClaveSegura123".toCharArray(), "pbkdf2_sha256\$0\$a\$b"))
        assertFalse(hash.verificar("ClaveSegura123".toCharArray(), "pbkdf2_sha256\$1000\$!!!\$???"))
        assertFalse(hash.verificar("ClaveSegura123".toCharArray(), "otro\$1000\$a\$b"))
    }

    @Test
    fun `el hash rapido es estable y distinto por token`() {
        val uno = hash.hashRapido("token-a")
        val dos = hash.hashRapido("token-a")
        val otro = hash.hashRapido("token-b")
        assertEquals(uno, dos)
        assertNotEquals(uno, otro)
        assertEquals(43, uno.length) // 32 bytes en Base64 sin relleno
    }
}
