package ve.edu.sdep.movil.dominio.modelo

/**
 * Política de edición por columna: qué puede tocar cada rol dentro de una ficha
 * que ya puede escribir.
 *
 * Complementa a [PoliticaRoles], que decide qué módulo abre y qué acción
 * ejecuta cada rol. Esta capa decide el detalle: qué columnas son de la
 * incumbencia de cada perfil, de modo que el teléfono admite **leer, crear,
 * editar y gestionar** con acceso controlado según lo que se edita, el permiso
 * y el usuario. El nodo central vuelve a validar todo: esta es la primera
 * barrera, no la única.
 *
 * Correspondencia con los perfiles de la institución:
 *
 * * **Director** → [Rol.ADMIN]: toda la ficha, incluidos sueldo y banco.
 * * **Administrativo** → [Rol.MANAGER]: ídem; administra el personal.
 * * **Profesor / trabajador** → [Rol.USER]: completa su propia ficha y gestiona
 *   sus documentos e incidencias, pero no las condiciones de gestión de
 *   personal (sueldo, banco, cargo, tipo de contratación), que fija la
 *   administración.
 * * **Solo lectura** → [Rol.VIEWER]: no escribe en ninguna columna.
 *
 * Es *fail-closed* para el trabajador: una columna que no figure en
 * [FICHA_PROPIA] ni en [GESTION_PROPIA] no la edita. La propiedad de la fila
 * (que solo toque las suyas) la fuerza además `TablaRepositorio` con la cédula
 * de la sesión, y las columnas de solo lectura del formulario
 * (`profesor_uuid`) las vuelve a filtrar `EsquemaTabla.esEditable`.
 */
object PoliticaEdicion {

    /**
     * Campos de la ficha personal que el propio trabajador completa.
     *
     * Son datos de su identidad, contacto y salud: los conoce él y no dependen
     * de una decisión administrativa.
     */
    private val FICHA_PROPIA = setOf(
        "nombres",
        "apellidos",
        "fecha_nacimiento",
        "genero",
        "estado_civil",
        "nacionalidad",
        "telefono",
        "celular",
        "email",
        "direccion",
        "ciudad",
        "estado",
        "codigo_postal",
        "peso",
        "altura",
        "tipo_sangre",
        "carnet_discapacidad",
        "enfermedades_preexistentes",
        "alergias_medicamentosas",
        "alergias_alimentarias",
        "hijos",
        "observaciones",
        "contacto_emergencia_nombre",
        "contacto_emergencia_telefono",
        "contacto_emergencia_relacion",
    )

    /**
     * Campos de sus documentos e incidencias: el trabajador los registra,
     * siempre sobre su propia cédula (la fila la ata `TablaRepositorio`).
     */
    private val GESTION_PROPIA = setOf(
        "tipo_documento",
        "titulo",
        "descripcion",
        "numero_documento",
        "fecha_emision",
        "fecha_vencimiento",
        "nombre_archivo",
        "tipo_incidencia",
        "fecha_inicio",
        "fecha_fin",
        "fecha_solicitud",
        "motivo",
        "dias_solicitados",
    )

    /**
     * Indica si el rol puede escribir la columna en un formulario.
     *
     * La validación de obligación y tipo se limita también a este ámbito: una
     * columna de gestión que el formulario no muestra no puede bloquear el
     * guardado de una ficha propia; la administración la completa después.
     */
    fun editable(columna: String, rol: Rol): Boolean = when (rol) {
        Rol.ADMIN, Rol.MANAGER -> true
        Rol.USER -> columna in FICHA_PROPIA || columna in GESTION_PROPIA
        Rol.VIEWER -> false
    }
}
