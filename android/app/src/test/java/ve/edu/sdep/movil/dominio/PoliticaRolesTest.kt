package ve.edu.sdep.movil.dominio

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import ve.edu.sdep.movil.dominio.modelo.Modulo
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.PoliticaRoles
import ve.edu.sdep.movil.dominio.modelo.Rol

/**
 * Matriz de permisos del móvil.
 *
 * Debe coincidir con `src/utils/security.py` del escritorio: el nodo central
 * vuelve a comprobar la misma matriz antes de aceptar una escritura, así que
 * una pantalla que se equivoque no puede elevar permisos.
 */
class PoliticaRolesTest {

    @Test
    fun `el administrador puede todo`() {
        Permiso.entries.forEach { permiso ->
            assertTrue(
                "El administrador debería poder $permiso",
                PoliticaRoles.tiene(Rol.ADMIN, permiso),
            )
        }
    }

    @Test
    fun `el gestor registra y edita pero no configura ni respalda`() {
        assertTrue(PoliticaRoles.tiene(Rol.MANAGER, Permiso.CONSULTAR))
        assertTrue(PoliticaRoles.tiene(Rol.MANAGER, Permiso.CREAR))
        assertTrue(PoliticaRoles.tiene(Rol.MANAGER, Permiso.EDITAR))
        assertTrue(PoliticaRoles.tiene(Rol.MANAGER, Permiso.ELIMINAR))
        assertTrue(PoliticaRoles.tiene(Rol.MANAGER, Permiso.REPORTAR))
        assertFalse(PoliticaRoles.tiene(Rol.MANAGER, Permiso.CONFIGURAR))
        assertFalse(PoliticaRoles.tiene(Rol.MANAGER, Permiso.RESPALDAR))
    }

    @Test
    fun `el usuario completa su propia ficha y el lector solo consulta`() {
        // CREAR y EDITAR del WORKER son «own»: TablaRepositorio fuerza la
        // cédula de la sesión y el nodo central aplica la misma frontera.
        assertTrue(PoliticaRoles.tiene(Rol.USER, Permiso.CONSULTAR))
        assertTrue(PoliticaRoles.tiene(Rol.USER, Permiso.CREAR))
        assertTrue(PoliticaRoles.tiene(Rol.USER, Permiso.EDITAR))
        assertFalse(PoliticaRoles.tiene(Rol.USER, Permiso.ELIMINAR))
        assertFalse(PoliticaRoles.tiene(Rol.USER, Permiso.CONFIGURAR))
        assertFalse(PoliticaRoles.tiene(Rol.USER, Permiso.RESPALDAR))
        assertTrue(PoliticaRoles.puedeEditar(Rol.USER))
        assertTrue(PoliticaRoles.puedeCrear(Rol.USER))

        assertTrue(PoliticaRoles.tiene(Rol.VIEWER, Permiso.CONSULTAR))
        assertFalse(PoliticaRoles.tiene(Rol.VIEWER, Permiso.CREAR))
        assertFalse(PoliticaRoles.tiene(Rol.VIEWER, Permiso.EDITAR))
        assertFalse(PoliticaRoles.tiene(Rol.VIEWER, Permiso.ELIMINAR))
        assertFalse(PoliticaRoles.tiene(Rol.VIEWER, Permiso.CONFIGURAR))
        assertFalse(PoliticaRoles.puedeEditar(Rol.VIEWER))
        assertFalse(PoliticaRoles.puedeCrear(Rol.VIEWER))
    }

    @Test
    fun `un rol desconocido se degrada a consulta`() {
        val desconocido = Rol.desde("SUPERUSUARIO")
        assertFalse(PoliticaRoles.tiene(desconocido, Permiso.CREAR))
        assertFalse(PoliticaRoles.tiene(Rol.desde(null), Permiso.ELIMINAR))
        assertTrue(PoliticaRoles.tiene(desconocido, Permiso.CONSULTAR))
    }

    @Test
    fun `los modulos respetan el acceso por rol`() {
        assertTrue(PoliticaRoles.puedeAbrir(Rol.VIEWER, Modulo.EMPLEADOS))
        assertFalse(PoliticaRoles.puedeAbrir(Rol.VIEWER, Modulo.CONFIGURACION))
        assertTrue(PoliticaRoles.puedeAbrir(Rol.ADMIN, Modulo.CONFIGURACION))
        // La captura de campo está abierta a cualquier rol autenticado.
        assertTrue(PoliticaRoles.puedeAbrir(Rol.ADMIN, Modulo.REGISTROS))
        assertTrue(PoliticaRoles.puedeAbrir(Rol.VIEWER, Modulo.REGISTROS))
    }
}
