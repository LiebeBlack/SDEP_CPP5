package ve.edu.sdep.movil.dominio.modelo

/**
 * Rol de la cuenta dentro de la aplicación.
 *
 * Los tres roles existen en la app y no dependen del usuario del escritorio:
 * el teléfono es un equipo más de la intranet y administra sus propias cuentas,
 * igual que cada puesto. El rol solo limita lo que la interfaz ofrece; la
 * validación definitiva de los datos la hace el nodo central al aplicar las
 * operaciones.
 */
enum class Rol(val etiqueta: String, val descripcion: String) {
    ADMIN(
        etiqueta = "Administrador",
        descripcion = "Registra, edita, elimina, administra cuentas y configura la sincronización",
    ),
    EDITOR(
        etiqueta = "Editor",
        descripcion = "Registra y edita registros; no elimina ni administra cuentas",
    ),
    VIEWER(
        etiqueta = "Consulta",
        descripcion = "Solo lectura: consulta los registros sincronizados",
    ),
    ;

    companion object {
        /** Convierte el texto almacenado en la base a un rol válido */
        fun desde(valor: String?): Rol =
            values().firstOrNull { it.name.equals(valor, ignoreCase = true) } ?: VIEWER
    }
}

/** Acciones que la interfaz debe permitir o bloquear */
enum class Permiso {
    CONSULTAR,
    CREAR,
    EDITAR,
    ELIMINAR,
    ADMINISTRAR_USUARIOS,
    CONFIGURAR_SINCRONIZACION,
}

/**
 * Política de permisos, en un solo lugar.
 *
 * La usan tanto los ViewModel (para rechazar una acción aunque la pantalla se
 * equivoque) como las pantallas (para ocultar lo que no corresponde).
 */
object PoliticaRoles {

    fun puede(rol: Rol, permiso: Permiso): Boolean = when (rol) {
        Rol.ADMIN -> true
        Rol.EDITOR -> permiso == Permiso.CONSULTAR ||
            permiso == Permiso.CREAR ||
            permiso == Permiso.EDITAR
        Rol.VIEWER -> permiso == Permiso.CONSULTAR
    }

    /** Atajo usado por la pantalla de edición */
    fun puedeEditar(rol: Rol): Boolean = puede(rol, Permiso.EDITAR)
}
