package ve.edu.sdep.movil.dominio

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import ve.edu.sdep.movil.dominio.modelo.Permiso
import ve.edu.sdep.movil.dominio.modelo.PoliticaRoles
import ve.edu.sdep.movil.dominio.modelo.Rol

class PoliticaRolesTest {

    @Test
    fun `el administrador puede todo`() {
        Permiso.values().forEach { permiso ->
            assertTrue(
                "El administrador debería poder $permiso",
                PoliticaRoles.puede(Rol.ADMIN, permiso),
            )
        }
    }

    @Test
    fun `el editor registra y edita pero no borra ni administra`() {
        assertTrue(PoliticaRoles.puede(Rol.EDITOR, Permiso.CONSULTAR))
        assertTrue(PoliticaRoles.puede(Rol.EDITOR, Permiso.CREAR))
        assertTrue(PoliticaRoles.puede(Rol.EDITOR, Permiso.EDITAR))
        assertFalse(PoliticaRoles.puede(Rol.EDITOR, Permiso.ELIMINAR))
        assertFalse(PoliticaRoles.puede(Rol.EDITOR, Permiso.ADMINISTRAR_USUARIOS))
        assertFalse(PoliticaRoles.puede(Rol.EDITOR, Permiso.CONFIGURAR_SINCRONIZACION))
    }

    @Test
    fun `el lector solo consulta`() {
        assertTrue(PoliticaRoles.puede(Rol.VIEWER, Permiso.CONSULTAR))
        assertFalse(PoliticaRoles.puede(Rol.VIEWER, Permiso.CREAR))
        assertFalse(PoliticaRoles.puede(Rol.VIEWER, Permiso.EDITAR))
        assertFalse(PoliticaRoles.puede(Rol.VIEWER, Permiso.ELIMINAR))
        assertFalse(PoliticaRoles.puedeEditar(Rol.VIEWER))
    }

    @Test
    fun `un rol desconocido se degrada a consulta`() {
        assertFalse(PoliticaRoles.puede(Rol.desde("SUPERUSUARIO"), Permiso.CREAR))
        assertFalse(PoliticaRoles.puede(Rol.desde(null), Permiso.ELIMINAR))
    }
}
