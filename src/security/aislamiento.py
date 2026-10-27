"""
Aislamiento de datos por cédula

Una sola política para el escritorio, el nodo central y cualquier consulta que
se ejecute con una sesión de usuario:

* El rol ``admin`` y ``manager`` conserva la visión global.
* El rol ``user`` es el **WORKER**: solo ve las filas de su propia cédula.
* ``viewer`` conserva la lectura global que ya tenía (es una cuenta de consulta
  institucional, no una cuenta personal de trabajador).

La política se aplica en dos capas de SQLAlchemy:

1. ``do_orm_execute`` añade ``with_loader_criteria`` a cada SELECT con la
   entidad afectada. Cubre listados, búsquedas y agregados, no solo la pantalla
   que se acordó filtrar.
2. ``before_flush`` rechaza altas, ediciones y bajas que salgan de la cédula
   (o del usuario, para los registros de campo y la propia cuenta).

El agente de sincronización y el nodo central crean sus sesiones en hilos sin
contexto, así que la replicación sigue siendo global. El nodo central establece
el contexto por petición antes de ejecutar una acción del móvil.
"""

from __future__ import annotations

import logging

from sqlalchemy import event, false, func, inspect as sa_inspect, select
from sqlalchemy.orm import Session, with_loader_criteria

from src.models import (
    Configuracion,
    Contrato,
    Documento,
    Empleado,
    Estudiante,
    Grado,
    Incidencia,
    Matricula,
    NotaFinal,
    Pago,
    PeriodoAcademico,
    RegistroMovil,
    TokenSesion,
    Usuario,
)
from src.security.contexto import ContextoSesion, actual, normalizar_cedula
from src.utils.security import PermissionChecker

logger = logging.getLogger(__name__)

_INSTALADO = False


class ErrorAislamiento(ValueError):
    """Operación rechazada porque pertenece a otra cédula."""


# ----------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------
def _cedula_sql(modelo):
    """Expresión SQL de la cédula sin puntos ni espacios, en mayúsculas."""
    return func.upper(func.replace(func.replace(modelo.cedula, ".", ""), " ", ""))


def _criterio(entidad, contexto: ContextoSesion):
    """Criterio de visibilidad para una entidad, o ``None`` si es global."""
    cedula = contexto.cedula
    if entidad is Empleado:
        return _cedula_sql(Empleado) == cedula
    if entidad in (Documento, Incidencia, Pago, Contrato):
        propios = select(Empleado.id).where(_cedula_sql(Empleado) == cedula)
        return entidad.empleado_id.in_(propios)
    if entidad is Grado:
        return Grado.profesor_id == contexto.usuario_id
    if entidad is NotaFinal:
        propios = select(Grado.id).where(Grado.profesor_id == contexto.usuario_id)
        return NotaFinal.grado_id.in_(propios)
    if entidad is Usuario:
        return Usuario.id == contexto.usuario_id
    if entidad is RegistroMovil:
        # Los registros de campo se identifican por la cuenta que los capturó;
        # no existe una cédula de empleado asociada a la fila.
        return RegistroMovil.usuario == contexto.username
    if entidad is Configuracion:
        # Parámetros institucionales sin datos personales: la lectura sigue
        # disponible para que la política de contraseñas se pueda consultar.
        return None
    if entidad in (Estudiante, PeriodoAcademico, Matricula, TokenSesion):
        # El WORKER no tiene un vínculo de propiedad con el dominio académico
        # en este modelo. Se deniega por defecto en vez de exponer el legado
        # completo a una cuenta personal.
        return false()
    # Cualquier modelo futuro queda cerrado hasta declarar aquí su propietario.
    return false()


def _entidades(statement) -> list:
    """Entidades ORM que participan en una sentencia."""
    vistas = []
    for descripcion in getattr(statement, "column_descriptions", []) or []:
        entidad = descripcion.get("entity")
        if entidad is not None and hasattr(entidad, "__table__") and entidad not in vistas:
            vistas.append(entidad)
    return vistas


def _filtrar_consulta(state) -> None:
    """Añade el filtro de cédula a cualquier SELECT ejecutado con contexto."""
    if not state.is_select:
        return
    if state.execution_options.get("saltar_aislamiento"):
        return
    contexto = actual()
    if contexto is None or not contexto.es_trabajador:
        return
    if not contexto.cedula:
        # Un WORKER sin cédula no debería existir (AuthService lo impide).
        # Si llega aquí por una fila antigua, no se le muestra nada.
        state.statement = state.statement.where(false())
        return

    sentencia = state.statement
    for entidad in _entidades(sentencia):
        criterio = _criterio(entidad, contexto)
        if criterio is None:
            continue
        sentencia = sentencia.options(with_loader_criteria(entidad, criterio, include_aliases=True))
    state.statement = sentencia


# ----------------------------------------------------------------------
# Comprobación directa de objetos
# ----------------------------------------------------------------------
def _empleado_id_de(obj, session: Session) -> int | None:
    """Id del empleado al que pertenece una fila hija, si ya se conoce."""
    empleado_id = getattr(obj, "empleado_id", None)
    if empleado_id:
        return int(empleado_id)
    empleado = getattr(obj, "empleado", None)
    if empleado is not None:
        return getattr(empleado, "id", None)
    return None


def _es_empleado_propio(obj, session: Session, contexto: ContextoSesion) -> bool:
    cedula = normalizar_cedula(getattr(obj, "cedula", None))
    if cedula and cedula == contexto.cedula:
        return True
    empleado_id = _empleado_id_de(obj, session)
    if empleado_id is None:
        return False
    empleado = session.get(Empleado, empleado_id)
    return bool(empleado is not None and normalizar_cedula(empleado.cedula) == contexto.cedula)


def puede_ver_objeto(obj, session: Session, contexto: ContextoSesion | None = None) -> bool:
    """Indica si la sesión puede ver un objeto ya cargado.

    ``Session.get`` no pasa siempre por ``with_loader_criteria``; esta
    comprobación cubre la lectura directa por id que usan los formularios.
    """
    contexto = contexto or actual()
    if contexto is None or not contexto.es_trabajador:
        return True
    if not contexto.cedula:
        return False
    if isinstance(obj, Empleado):
        return normalizar_cedula(obj.cedula) == contexto.cedula
    if isinstance(obj, (Documento, Incidencia, Pago, Contrato)):
        return _es_empleado_propio(obj, session, contexto)
    if isinstance(obj, Usuario):
        return getattr(obj, "id", None) == contexto.usuario_id
    if isinstance(obj, RegistroMovil):
        return (obj.usuario or "") == contexto.username
    if isinstance(obj, Grado):
        return getattr(obj, "profesor_id", None) == contexto.usuario_id
    if isinstance(obj, NotaFinal):
        grado = getattr(obj, "grado", None) or session.get(Grado, obj.grado_id)
        return bool(grado is not None and grado.profesor_id == contexto.usuario_id)
    return False


# ----------------------------------------------------------------------
# Comprobación de escrituras
# ----------------------------------------------------------------------
def _permite(contexto: ContextoSesion, permiso: str) -> bool:
    return PermissionChecker.has_permission(contexto.rol, permiso)


def _motivo_escritura(
    obj,
    session: Session,
    contexto: ContextoSesion,
    *,
    es_nueva: bool,
    es_baja: bool,
) -> str | None:
    """Motivo por el que una escritura no está permitida, o ``None``."""
    if not contexto.cedula:
        return "La cuenta no tiene cédula asignada; no puede modificar datos."

    if isinstance(obj, Empleado):
        if es_baja:
            return "Solo un administrador puede dar de baja una ficha."
        if not es_nueva:
            estado = sa_inspect(obj)
            campos_protegidos = {
                "cedula",
                "tipo_empleado",
                "cargo",
                "departamento",
                "fecha_contratacion",
                "fecha_terminacion",
                "salario_base",
                "activo",
            }
            if any(
                estado.attrs[campo].history.has_changes()
                for campo in campos_protegidos
            ):
                return "Solo un administrador puede modificar los datos laborales o de identidad."
        if not _es_empleado_propio(obj, session, contexto):
            return "No puede modificar la ficha de otra cédula."
        permiso = "create_own" if es_nueva else "update_own"
        if not _permite(contexto, permiso):
            return "Su rol no permite completar su propia ficha."
        return None

    if isinstance(obj, (Documento, Incidencia)):
        if es_baja:
            return "Solo un administrador puede eliminar registros."
        if not _es_empleado_propio(obj, session, contexto):
            return "No puede acceder a documentos o incidencias de otra cédula."
        permiso = "create_own" if es_nueva else "update_own"
        if not _permite(contexto, permiso):
            return "Su rol no permite modificar sus propios registros."
        return None

    if isinstance(obj, RegistroMovil):
        if (obj.usuario or "") != contexto.username:
            return "El registro de campo pertenece a otra cuenta."
        if es_baja:
            return "Los registros de campo se desactivan, no se borran."
        return None

    if isinstance(obj, Usuario):
        if es_nueva or getattr(obj, "id", None) != contexto.usuario_id:
            return "Solo puede modificar su propia cuenta."
        estado = sa_inspect(obj)
        campos_editables = {
            "password_hash",
            "password_historial",
            "fecha_cambio_password",
            "debe_cambiar_password",
            "intentos_fallidos",
            "bloqueado",
            "bloqueado_hasta",
            "ultimo_login",
        }
        campos_modificados = {
            atributo.key
            for atributo in estado.attrs
            if atributo.history.has_changes()
        }
        if campos_modificados - campos_editables:
            return "No puede modificar el rol, la cédula ni el estado de su cuenta."
        return None

    # Nómina, contratos, academia y configuración: el WORKER no escribe aquí.
    if isinstance(
        obj,
        (
            Pago,
            Contrato,
            Grado,
            NotaFinal,
            Estudiante,
            PeriodoAcademico,
            Matricula,
            Configuracion,
            TokenSesion,
        ),
    ):
        return "Su rol no tiene permiso para modificar este módulo."

    return "La tabla no tiene una regla de propiedad declarada."


def _verificar_escrituras(session: Session, _flush_context, _instances) -> None:
    """Aborta el flush si un WORKER intenta escribir fuera de su cédula."""
    contexto = actual()
    if contexto is None or not contexto.es_trabajador:
        return
    for obj in list(session.new):
        if not hasattr(obj, "__table__"):
            continue
        motivo = _motivo_escritura(obj, session, contexto, es_nueva=True, es_baja=False)
        if motivo:
            raise ErrorAislamiento(motivo)
    for obj in list(session.dirty):
        if not hasattr(obj, "__table__"):
            continue
        motivo = _motivo_escritura(obj, session, contexto, es_nueva=False, es_baja=False)
        if motivo:
            raise ErrorAislamiento(motivo)
    for obj in list(session.deleted):
        if not hasattr(obj, "__table__"):
            continue
        motivo = _motivo_escritura(obj, session, contexto, es_nueva=False, es_baja=True)
        if motivo:
            raise ErrorAislamiento(motivo)


def instalar() -> None:
    """Instala los dos oyentes una sola vez por proceso."""
    global _INSTALADO
    if _INSTALADO:
        return
    event.listen(Session, "do_orm_execute", _filtrar_consulta)
    event.listen(Session, "before_flush", _verificar_escrituras)
    _INSTALADO = True
    logger.debug("Aislamiento por cédula instalado en SQLAlchemy")
