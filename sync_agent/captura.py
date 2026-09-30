"""
Captura de cambios (enganche al ORM)

El agente no pide a los servicios que avisen de sus cambios: escucha la
confirmación de la sesión de SQLAlchemy. Así la captura es **imposible de
olvidar** (ningún CRUD nuevo queda fuera) y, sobre todo, es **atómica**: las
filas de ``sync_journal``, ``sync_campos`` y ``sync_versiones`` se añaden a la
misma sesión y se confirman en la misma transacción que el dato, de modo que un
corte de energía no puede dejar una edición sin su operación de sincronización.

Se escribe en dos tiempos porque los identificadores locales solo existen
después del volcado: ``before_flush`` lee el historial de atributos y anota qué
cambió; ``after_flush_postexec`` ya tiene las claves primarias y escribe el
journal con el payload definitivo.
"""

from __future__ import annotations

import logging
import weakref
from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import and_, event, inspect as sa_inspect
from sqlalchemy.orm import Session

from sync_agent import identidad, registro
from sync_agent.comun import ahora_utc, dumps, nuevo_uuid, serializar_valor
from sync_agent.esquema import (
    DIRECCION_SALIDA,
    PENDIENTE,
    CampoRemoto,
    JournalOp,
    VersionFila,
)

logger = logging.getLogger(__name__)

_CLAVE_PENDIENTES = "_sync_pendientes"
_CLAVE_SILENCIO = "_sync_silencioso"
_CLAVE_USUARIO = "_sync_usuario"

_instalado = False
_engines: "weakref.WeakSet" = weakref.WeakSet()
_dispositivo: str | None = None


# ----------------------------------------------------------------------
# Instalación y utilidades de contexto
# ----------------------------------------------------------------------
def instalar(session_factory=None, engine=None) -> None:
    """
    Instala la captura de cambios (idempotente)

    Args:
        session_factory: Fábrica de sesiones del sistema (informativo)
        engine: Motor sobre cuyos cambios se captura. Sin motor, se captura
            cualquier sesión (útil en las pruebas)
    """
    global _instalado
    if engine is not None:
        _engines.add(engine)
    if _instalado:
        return
    event.listen(Session, "before_flush", _antes_de_confirmar)
    event.listen(Session, "after_flush_postexec", _despues_de_confirmar)
    _instalado = True
    logger.info("Captura de cambios de sincronización instalada")


def desinstalar() -> None:
    """Retira la captura (pruebas y reinicializaciones)"""
    global _instalado
    if not _instalado:
        return
    event.remove(Session, "before_flush", _antes_de_confirmar)
    event.remove(Session, "after_flush_postexec", _despues_de_confirmar)
    _instalado = False


def establecer_dispositivo(uuid_dispositivo: str | None) -> None:
    """Fija el identificador del equipo que firma las operaciones"""
    global _dispositivo
    _dispositivo = uuid_dispositivo


def dispositivo_actual() -> str:
    """Identificador del equipo que firma las operaciones (se resuelve al usarse)"""
    global _dispositivo
    if _dispositivo:
        return _dispositivo
    try:
        from sync_agent.config import config_sync

        _dispositivo = config_sync.dispositivo_id
    except Exception:  # pragma: no cover - configuración no disponible
        logger.debug("Sin configuración de sincronización; se usa un equipo anónimo")
        _dispositivo = "desconocido"
    return _dispositivo


@contextmanager
def cambios_silenciosos(session: Session) -> Iterator[None]:
    """
    Silencia la captura mientras dure el bloque

    Se usa al aplicar operaciones que llegan de la red y al generar las
    operaciones base: si esos cambios se capturaran, el equipo devolvería al
    resto de la red lo que acaba de recibir (efecto eco).
    """
    info = session.info
    info[_CLAVE_SILENCIO] = int(info.get(_CLAVE_SILENCIO) or 0) + 1
    try:
        yield
    finally:
        restante = int(info.get(_CLAVE_SILENCIO) or 1) - 1
        if restante > 0:
            info[_CLAVE_SILENCIO] = restante
        else:
            info.pop(_CLAVE_SILENCIO, None)


def establecer_usuario(session: Session, usuario: str | None) -> None:
    """Anota qué usuario firma los cambios de esta sesión (para la auditoría)"""
    if usuario:
        session.info[_CLAVE_USUARIO] = usuario
    else:
        session.info.pop(_CLAVE_USUARIO, None)


def captura_activa(session: Session) -> bool:
    """Indica si los cambios de la sesión deben registrarse"""
    if session.info.get(_CLAVE_SILENCIO):
        return False
    if not _engines:
        return True
    try:
        bind = session.get_bind()
    except Exception:  # pragma: no cover - sesión sin motor único
        return False
    return getattr(bind, "engine", bind) in _engines


# ----------------------------------------------------------------------
# Enganches de la sesión
# ----------------------------------------------------------------------
def _antes_de_confirmar(session: Session, _contexto, _instancias) -> None:
    """Anota qué cambió, antes de que el volcado borre el historial"""
    if not captura_activa(session):
        return

    pendientes: list[dict[str, Any]] = []

    for obj in session.new:
        anotacion = _anotar(session, obj, "upsert", insertando=True)
        if anotacion:
            pendientes.append(anotacion)

    for obj in session.dirty:
        if obj in session.new or obj in session.deleted:
            continue
        if not session.is_modified(obj, include_collections=False):
            continue
        anotacion = _anotar(session, obj, "upsert", insertando=False)
        if anotacion:
            pendientes.append(anotacion)

    for obj in session.deleted:
        anotacion = _anotar(session, obj, "delete", insertando=False)
        if anotacion:
            pendientes.append(anotacion)

    if pendientes:
        session.info.setdefault(_CLAVE_PENDIENTES, []).extend(pendientes)


def _anotar(session: Session, obj: Any, operacion: str, insertando: bool) -> dict[str, Any] | None:
    """Prepara la anotación de un objeto para el paso posterior al volcado"""
    tabla = getattr(obj, "__tablename__", None)
    if not registro.es_sincronizable(tabla):
        return None

    if tabla == "configuraciones" and registro.configuracion_es_local(
        getattr(obj, "clave", None)
    ):
        # Las preferencias del equipo no viajan: tema visual, respaldos, agente...
        return None

    if operacion == "delete":
        return {"obj": obj, "tabla": tabla, "operacion": operacion, "cambios": {}}

    transportables = set(registro.columnas_transportables(tabla))
    cambios: dict[str, Any] = {}
    if insertando:
        for nombre in transportables:
            valor = getattr(obj, nombre, None)
            if valor is not None:
                cambios[nombre] = valor
    else:
        estado = sa_inspect(obj)
        for atributo in estado.mapper.column_attrs:
            nombre = atributo.key
            if nombre not in transportables:
                continue
            if not estado.attrs[nombre].history.has_changes():
                continue
            cambios[nombre] = getattr(obj, nombre, None)

    if not cambios:
        return None
    return {"obj": obj, "tabla": tabla, "operacion": operacion, "cambios": cambios}


def _despues_de_confirmar(session: Session, _contexto) -> None:
    """Escribe el journal y el estado de mezcla con las claves ya asignadas"""
    pendientes = session.info.pop(_CLAVE_PENDIENTES, None)
    if not pendientes:
        return

    dispositivo = dispositivo_actual()
    usuario = session.info.get(_CLAVE_USUARIO)
    momento = ahora_utc()
    uuid_por_fila: dict[tuple[str, int], str] = {}

    # 1. Identidad global de todas las filas tocadas (los hijos necesitan el
    #    UUID de su padre, aunque el padre se haya creado en esta misma vuelta)
    for anotacion in pendientes:
        obj = anotacion["obj"]
        id_local = getattr(obj, "id", None)
        if id_local is None:
            anotacion["uuid"] = None
            continue
        clave = registro.columna_clave_natural(anotacion["tabla"])
        valor_clave = getattr(obj, clave, None) if clave else None
        uuid = identidad.asegurar_uuid(session, anotacion["tabla"], id_local, valor_clave)
        anotacion["uuid"] = uuid
        if uuid:
            uuid_por_fila[(anotacion["tabla"], id_local)] = uuid

    # 2. Journal + estado de mezcla por campo
    for anotacion in pendientes:
        uuid = anotacion.get("uuid")
        if not uuid:
            logger.warning(
                "Se omite la sincronización de %s: no se pudo determinar su identidad",
                anotacion["tabla"],
            )
            continue

        operacion = anotacion["operacion"]
        op_id = nuevo_uuid()
        payload = _payload(session, anotacion, uuid_por_fila)
        borrado = operacion == "delete"

        session.add(
            JournalOp(
                op_id=op_id,
                tabla=anotacion["tabla"],
                fila_uuid=uuid,
                operacion=operacion,
                payload=dumps(payload),
                base_op_id=None,
                dispositivo=dispositivo,
                usuario=usuario,
                creado_en=momento,
                estado=PENDIENTE,
                direccion=DIRECCION_SALIDA,
            )
        )
        _actualizar_estado(
            session,
            tabla=anotacion["tabla"],
            fila_uuid=uuid,
            cambios=payload,
            op_id=op_id,
            dispositivo=dispositivo,
            momento=momento,
            borrado=borrado,
        )


def _payload(
    session: Session, anotacion: dict[str, Any], uuid_por_fila: dict[tuple[str, int], str]
) -> dict[str, Any]:
    """Payload serializado con las claves foráneas ya expresadas como UUID"""
    tabla = anotacion["tabla"]
    cambios = anotacion["cambios"]
    if not cambios:
        return {}

    payload: dict[str, Any] = {
        columna: serializar_valor(valor) for columna, valor in cambios.items()
    }

    foraneas = registro.claves_foraneas(tabla)
    for columna, tabla_padre in foraneas.items():
        if columna not in payload:
            continue
        valor = cambios[columna]
        if valor is None:
            continue
        uuid_padre = uuid_por_fila.get((tabla_padre, valor))
        if uuid_padre is None:
            uuid_padre = identidad.uuid_de_padre(session, tabla_padre, valor)
        if uuid_padre is None:
            logger.warning(
                "Se omite %s.%s: no se pudo identificar el registro %s#%s",
                tabla,
                columna,
                tabla_padre,
                valor,
            )
            payload.pop(columna, None)
            continue
        payload[columna] = uuid_padre
    return payload


def _actualizar_estado(
    session: Session,
    tabla: str,
    fila_uuid: str,
    cambios: dict[str, Any],
    op_id: str,
    dispositivo: str,
    momento,
    borrado: bool,
) -> None:
    """Actualiza la última escritura de cada campo y la versión de la fila"""
    if cambios:
        existentes = {
            fila.campo: fila
            for fila in session.query(CampoRemoto)
            .filter(CampoRemoto.tabla == tabla, CampoRemoto.fila_uuid == fila_uuid)
            .all()
        }
        for campo, valor in cambios.items():
            serializado = dumps(valor)
            fila = existentes.get(campo)
            if fila is None:
                session.add(
                    CampoRemoto(
                        tabla=tabla,
                        fila_uuid=fila_uuid,
                        campo=campo,
                        valor=serializado,
                        op_id=op_id,
                        dispositivo=dispositivo,
                        actualizado_en=momento,
                    )
                )
            else:
                fila.valor = serializado
                fila.op_id = op_id
                fila.dispositivo = dispositivo
                fila.actualizado_en = momento

    version = (
        session.query(VersionFila)
        .filter(VersionFila.tabla == tabla, VersionFila.fila_uuid == fila_uuid)
        .first()
    )
    if version is None:
        version = VersionFila(tabla=tabla, fila_uuid=fila_uuid)
        session.add(version)

    if borrado:
        version.borrado = 1
        version.borrado_en = momento
        version.borrado_op_id = op_id
        version.borrado_dispositivo = dispositivo
    else:
        version.ultimo_op_id = op_id
        version.actualizado_en = momento
        version.dispositivo = dispositivo
    if version.borrado and not borrado:
        # Una edición posterior al borrado devuelve la fila a la vida
        version.borrado = 0


# ----------------------------------------------------------------------
# Adopción de los datos que ya existían
# ----------------------------------------------------------------------
def adoptar_existentes(session: Session, lote: int = 500) -> int:
    """
    Da identidad global y operación base a los datos previos al agente

    Se ejecuta una sola vez por equipo (es idempotente): sin ella, todo lo que
    ya estaba cargado antes de instalar el agente nunca llegaría al resto de la
    red, porque nadie lo ha modificado desde entonces.

    Args:
        session: Sesión de base de datos
        lote: Filas procesadas por vuelta

    Returns:
        Cantidad de filas adoptadas
    """
    from sync_agent.esquema import SyncId

    dispositivo = dispositivo_actual()
    total = 0

    for nombre in registro.tablas_sincronizadas():
        descripcion = registro.ENTIDADES[nombre]
        clase = descripcion.clase

        while True:
            filas: list[Any] = (
                session.query(clase)
                .outerjoin(
                    SyncId,
                    and_(SyncId.tabla == nombre, SyncId.id_local == clase.id),
                )
                .filter(SyncId.id.is_(None))
                .limit(lote)
                .all()
            )
            if not filas:
                break

            uuid_por_fila: dict[tuple[str, int], str] = {}
            for fila in filas:
                clave = registro.columna_clave_natural(nombre)
                valor_clave = getattr(fila, clave, None) if clave else None
                uuid = identidad.asegurar_uuid(session, nombre, fila.id, valor_clave)
                if uuid:
                    uuid_por_fila[(nombre, fila.id)] = uuid

            momento = ahora_utc()
            for fila in filas:
                uuid = uuid_por_fila.get((nombre, fila.id))
                if not uuid:
                    continue
                if nombre == "configuraciones" and registro.configuracion_es_local(fila.clave):
                    continue
                anotacion = {
                    "obj": fila,
                    "tabla": nombre,
                    "operacion": "upsert",
                    "cambios": {
                        columna: getattr(fila, columna, None)
                        for columna in registro.columnas_transportables(nombre)
                        if getattr(fila, columna, None) is not None
                    },
                }
                payload = _payload(session, anotacion, uuid_por_fila)
                if not payload:
                    continue
                op_id = nuevo_uuid()
                session.add(
                    JournalOp(
                        op_id=op_id,
                        tabla=nombre,
                        fila_uuid=uuid,
                        operacion="upsert",
                        payload=dumps(payload),
                        dispositivo=dispositivo,
                        usuario=None,
                        creado_en=momento,
                        estado=PENDIENTE,
                        direccion=DIRECCION_SALIDA,
                    )
                )
                _actualizar_estado(
                    session,
                    tabla=nombre,
                    fila_uuid=uuid,
                    cambios=payload,
                    op_id=op_id,
                    dispositivo=dispositivo,
                    momento=momento,
                    borrado=False,
                )
                total += 1

            session.commit()

    if total:
        logger.info("Datos adoptados para sincronización: %s filas", total)
    return total
