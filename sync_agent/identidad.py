"""
Identidad global de las filas replicadas

Los identificadores locales (autoincrementales de cada SQLite) **no** sirven
para sincronizar: el empleado 5 de un puesto no es el empleado 5 de otro. Por
eso cada fila replicada recibe un UUID estable, que se guarda junto a su id
local en la tabla ``sync_ids``.

Dos agujeros que este módulo cubre de forma explícita:

* **Claves naturales** (``cedula``, ``numero``, ``clave``): si el mismo registro
  se creó por separado en dos equipos, se reconoce por su clave natural y se
  unifica bajo un único UUID en vez de duplicarlo.
* **Claves foráneas**: en el payload viaja el UUID del padre, nunca su número
  local; al aplicar en otro equipo se traduce al id que allí le corresponde.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from sync_agent import registro
from sync_agent.comun import nuevo_uuid
from sync_agent.esquema import SyncId

logger = logging.getLogger(__name__)


def uuid_de_fila(session, tabla: str, id_local: int | None) -> str | None:
    """UUID de una fila local, o None si todavía no tiene identidad global"""
    if id_local is None:
        return None
    try:
        uuid: str | None = (
            session.query(SyncId.uuid)
            .filter(SyncId.tabla == tabla, SyncId.id_local == id_local)
            .scalar()
        )
        return uuid
    except SQLAlchemyError:
        logger.warning("No se pudo consultar la identidad de %s#%s", tabla, id_local, exc_info=True)
        return None


def id_local_de(session, tabla: str, uuid: str | None) -> int | None:
    """Id local que corresponde a un UUID en este equipo"""
    if not uuid:
        return None
    try:
        id_local: int | None = (
            session.query(SyncId.id_local)
            .filter(SyncId.tabla == tabla, SyncId.uuid == uuid)
            .scalar()
        )
        return id_local
    except SQLAlchemyError:
        logger.warning("No se pudo traducir el UUID %s de %s", uuid, tabla, exc_info=True)
        return None


def registrar(session, tabla: str, uuid: str, id_local: int) -> SyncId:
    """Vincula un UUID con un id local (idempotente)"""
    existente: SyncId | None = (
        session.query(SyncId).filter(SyncId.tabla == tabla, SyncId.id_local == id_local).first()
    )
    if existente is not None:
        if existente.uuid != uuid:
            logger.info(
                "Se reasigna la identidad de %s#%s: %s → %s",
                tabla,
                id_local,
                existente.uuid,
                uuid,
            )
            existente.uuid = uuid
        return existente

    vinculo = SyncId(tabla=tabla, uuid=uuid, id_local=id_local)
    session.add(vinculo)
    return vinculo


def uuid_por_clave_natural(session, tabla: str, valor: Any) -> str | None:
    """UUID de la fila que ya tiene ese valor de clave natural (o None)"""
    columna = registro.columna_clave_natural(tabla)
    if not columna or valor is None:
        return None
    columna_orm = registro.columna(tabla, columna)
    clase = registro.ENTIDADES[tabla].clase
    try:
        uuid: str | None = (
            session.query(SyncId.uuid)
            .join(clase, clase.id == SyncId.id_local)
            .filter(SyncId.tabla == tabla, columna_orm == valor)
            .scalar()
        )
        return uuid
    except SQLAlchemyError:
        logger.warning("No se pudo buscar %s por %s=%s", tabla, columna, valor, exc_info=True)
        return None


def asegurar_uuid(
    session, tabla: str, id_local: int | None, clave_natural: Any = None
) -> str | None:
    """
    Devuelve el UUID de una fila y lo crea si aún no lo tiene

    Args:
        session: Sesión de base de datos
        tabla: Tabla de la fila
        id_local: Identificador local de la fila
        clave_natural: Valor de la clave natural, si la tabla tiene una

    Returns:
        UUID de la fila, o None si no se puede determinar (sin id local)
    """
    if id_local is None:
        return None

    uuid = uuid_de_fila(session, tabla, id_local)
    if uuid:
        return uuid

    if clave_natural is not None:
        # Reconocer el mismo registro creado en otro equipo evita duplicarlo
        uuid_existente = uuid_por_clave_natural(session, tabla, clave_natural)
        if uuid_existente:
            registrar(session, tabla, uuid_existente, id_local)
            return uuid_existente

    uuid = nuevo_uuid()
    registrar(session, tabla, uuid, id_local)
    return uuid


def uuid_de_padre(session, tabla_padre: str, id_local: int | None) -> str | None:
    """
    UUID del padre de una clave foránea, adoptando la fila si aún no lo tenía

    Permite sincronizar filas creadas antes de instalar el agente: la primera
    vez que un hijo las referencia, el padre recibe su identidad global.

    Args:
        session: Sesión de base de datos
        tabla_padre: Tabla referenciada
        id_local: Id local del padre

    Returns:
        UUID del padre o None si no existe
    """
    if id_local is None:
        return None

    uuid = uuid_de_fila(session, tabla_padre, id_local)
    if uuid:
        return uuid

    descripcion = registro.entidad(tabla_padre)
    if descripcion is None:
        return None

    try:
        padre = session.get(descripcion.clase, id_local)
    except SQLAlchemyError:
        padre = None
    if padre is None:
        logger.warning("Clave foránea huérfana: %s#%s no existe", tabla_padre, id_local)
        return None

    clave = registro.columna_clave_natural(tabla_padre)
    valor_clave = getattr(padre, clave, None) if clave else None
    return asegurar_uuid(session, tabla_padre, id_local, valor_clave)


def traducir_payload_a_uuid(session, tabla: str, cambios: dict[str, Any]) -> dict[str, Any]:
    """
    Convierte las claves foráneas de un payload local a UUID

    Un número local en el payload sería un dato incorrecto en el equipo
    receptor (allí ese número es otra persona), así que la columna se omite si
    el padre no se puede identificar: es preferible un dato incompleto a un
    dato equivocado.

    Args:
        session: Sesión de base de datos
        tabla: Tabla de origen
        cambios: Columnas cambiadas con sus valores locales

    Returns:
        Payload con las claves foráneas ya expresadas como UUID
    """
    foraneas = registro.claves_foraneas(tabla)
    if not foraneas:
        return cambios

    resultado = dict(cambios)
    for columna, tabla_padre in foraneas.items():
        if columna not in resultado:
            continue
        uuid = uuid_de_padre(session, tabla_padre, resultado[columna])
        if uuid is None:
            logger.warning(
                "Se omite %s.%s: no se pudo identificar el registro referenciado (%s)",
                tabla,
                columna,
                resultado[columna],
            )
            resultado.pop(columna, None)
            continue
        resultado[columna] = uuid
    return resultado


def traducir_payload_a_local(
    session, tabla: str, cambios: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """
    Convierte las claves foráneas de un payload remoto a ids locales

    Args:
        session: Sesión de base de datos
        tabla: Tabla destino
        cambios: Columnas del payload remoto (claves foráneas como UUID)

    Returns:
        Tupla (payload traducido, columnas que aún no se pueden resolver). Si
        la segunda lista no está vacía, quien aplica debe diferir la operación:
        el registro padre todavía no llegó a este equipo.
    """
    foraneas = registro.claves_foraneas(tabla)
    if not foraneas:
        return cambios, []

    resultado = dict(cambios)
    pendientes: list[str] = []
    for columna, tabla_padre in foraneas.items():
        if columna not in resultado:
            continue
        valor = resultado[columna]
        if valor is None:
            continue
        id_local = id_local_de(session, tabla_padre, str(valor))
        if id_local is None:
            pendientes.append(columna)
            continue
        resultado[columna] = id_local
    return resultado, pendientes


def limpiar(session) -> None:
    """Elimina las equivalencias de identidad (solo pruebas y reinicialización)"""
    session.query(SyncId).delete()
