package ve.edu.sdep.movil.dominio.modelo

/**
 * Roles y permisos del sistema, espejo de `src/utils/security.py`.
 *
 * Los mismos cuatro roles que el escritorio: administrador, gestor, usuario y
 * solo lectura. La matriz tiene DOS capas, igual que allá:
 *
 * 1. [PoliticaRoles.MODULOS] — qué módulo abre cada rol. Es *fail-closed*: un
 *    módulo que no figure declarado queda denegado para TODOS los roles.
 * 2. [PoliticaRoles.permisos] — qué acción puede ejecutar cada rol
 *    (create, read, update, delete, report, config…).
 *
 * La usan las pantallas (para ocultar lo que no corresponde), los ViewModel y
 * repositorios (para rechazar la acción aunque la pantalla se equivoque) y,
 * con exactamente la misma matriz, el nodo central (autoridad final). El test
 * `PoliticaRolesTest` compara esta tabla con el fixture exportado del
 * escritorio para que ninguna pueda divergir.
 */

/** Roles de la cuenta, tal como los guarda la tabla `usuarios` */
enum class Rol(val valor: String, val etiqueta: String, val descripcion: String) {
    ADMIN(
        valor = "admin",
        etiqueta = "Administrador",
        descripcion = "Todo el sistema: configura, administra cuentas y ve la auditoría",
    ),
    MANAGER(
        valor = "manager",
        etiqueta = "Gestor",
        descripcion = "Crea, edita, borra y genera reportes; sin configuración del sistema",
    ),
    USER(
        valor = "user",
        etiqueta = "Usuario",
        descripcion = "Completa su propia ficha y registra sus documentos e incidencias; sin nómina ni contratos",
    ),
    VIEWER(
        valor = "viewer",
        etiqueta = "Solo lectura",
        descripcion = "Consulta los datos; no crea, edita ni elimina",
    ),
    ;

    companion object {
        /** Convierte el texto de la base en un rol; lo desconocido degrada a consulta */
        fun desde(valor: String?): Rol =
            entries.firstOrNull { it.valor == valor || it.name.equals(valor, ignoreCase = true) }
                ?: VIEWER
    }
}

/** Acciones operativas sobre un módulo */
enum class Permiso(val etiqueta: String) {
    CREAR("crear"),
    CONSULTAR("leer"),
    EDITAR("editar"),
    ELIMINAR("eliminar"),
    REPORTAR("reportes"),
    CONFIGURAR("configurar"),
    RESPALDAR("respaldos"),
}

/** Módulos del sistema con control de acceso (los mismos del escritorio) */
enum class Modulo(val etiqueta: String, val ruta: String) {
    DASHBOARD("Panel de control", "dashboard"),
    EMPLEADOS("Empleados", "empleados"),
    DOCUMENTOS("Documentos", "documentos"),
    INCIDENCIAS("Incidencias", "incidencias"),
    CONTRATOS("Contratos", "contratos"),
    NOMINA("Nómina", "nomina"),
    CONFIGURACION("Configuración", "configuracion"),
    ESTUDIANTES("Estudiantes", "estudiantes"),
    NOTAS("Calificaciones", "notas"),
    REGISTROS("Registros de campo", "registros"),
    ;

    companion object {
        fun desde(ruta: String?): Modulo? = entries.firstOrNull { it.ruta == ruta }
    }
}

object PoliticaRoles {

    /**
     * Acceso por módulo: idéntico a `PermissionChecker.MODULE_ACCESS`.
     *
     * `DASHBOARD` y `REGISTROS` no pasan por este mapa en el escritorio (el
     * panel es el marco de bienvenida y la captura de campo es el uso propio
     * del teléfono); se declaran aquí para que también sean *fail-closed*.
     */
    val MODULOS: Map<Modulo, Set<Rol>> = mapOf(
        Modulo.DASHBOARD to Rol.entries.toSet(),
        Modulo.EMPLEADOS to setOf(Rol.ADMIN, Rol.MANAGER, Rol.USER, Rol.VIEWER),
        Modulo.DOCUMENTOS to setOf(Rol.ADMIN, Rol.MANAGER, Rol.USER, Rol.VIEWER),
        Modulo.INCIDENCIAS to setOf(Rol.ADMIN, Rol.MANAGER, Rol.USER),
        Modulo.CONTRATOS to setOf(Rol.ADMIN, Rol.MANAGER),
        Modulo.NOMINA to setOf(Rol.ADMIN, Rol.MANAGER),
        Modulo.CONFIGURACION to setOf(Rol.ADMIN),
        // El legajo académico y las notas son institucionales, no la ficha
        // personal del trabajador. El rol USER (WORKER) no los abre: así no
        // existe una lista global de estudiantes detrás de una cuenta personal.
        Modulo.ESTUDIANTES to setOf(Rol.ADMIN, Rol.MANAGER, Rol.VIEWER),
        Modulo.NOTAS to setOf(Rol.ADMIN, Rol.MANAGER),
        // La captura de campo es el uso propio del teléfono: cualquier rol
        // autenticado puede levantar registros; el editor de notas lo autoriza
        // además el token académico en el servidor.
        Modulo.REGISTROS to Rol.entries.toSet(),
    )

    /** Permisos de acción por rol, idéntico a `has_permission` */
    private val PERMISOS: Map<Rol, Set<Permiso>> = mapOf(
        Rol.ADMIN to Permiso.entries.toSet(),
        Rol.MANAGER to setOf(
            Permiso.CREAR, Permiso.CONSULTAR, Permiso.EDITAR, Permiso.ELIMINAR, Permiso.REPORTAR,
        ),
        // El WORKER puede completar su ficha y sus propios documentos e
        // incidencias. ``TablaRepositorio`` fuerza la cédula de la sesión y la
        // comprueba en cada escritura; el servidor hace la misma comprobación
        // antes de consolidar. Nunca son permisos globales.
        Rol.USER to setOf(Permiso.CONSULTAR, Permiso.CREAR, Permiso.EDITAR),
        Rol.VIEWER to setOf(Permiso.CONSULTAR),
    )

    /** Indica si el rol tiene el permiso de acción */
    fun tiene(rol: Rol, permiso: Permiso): Boolean =
        PERMISOS[rol]?.contains(permiso) ?: false

    /**
     * Indica si el rol puede abrir el módulo.
     *
     * *Fail-closed*: un módulo no declarado en [MODULOS] se deniega para
     * todos los roles, también para el administrador.
     */
    fun puedeAbrir(rol: Rol, modulo: Modulo): Boolean =
        MODULOS[modulo]?.contains(rol) ?: false

    /** Atajo para las pantallas: permiso de escritura */
    fun puedeEditar(rol: Rol): Boolean = tiene(rol, Permiso.EDITAR)

    /** Atajo para las pantallas: alta de registros */
    fun puedeCrear(rol: Rol): Boolean = tiene(rol, Permiso.CREAR)

    /** Atajo para las pantallas: bajas */
    fun puedeEliminar(rol: Rol): Boolean = tiene(rol, Permiso.ELIMINAR)

    /** Atajo para las pantallas: reportes y exportaciones */
    fun puedeReportar(rol: Rol): Boolean = tiene(rol, Permiso.REPORTAR)
}
