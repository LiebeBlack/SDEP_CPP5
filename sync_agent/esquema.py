"""
Esquema del agente de sincronización

Las tablas ``sync_*`` viven en el **mismo archivo de base de datos** que el
sistema: es la única forma de que el dato y su operación de sincronización se
confirmen en la misma transacción. Si vivieran en otro archivo, un corte de luz
entre dos confirmaciones dejaría un cambio sin replicar (o al revés).

La metadata es independiente de la del sistema, así que las migraciones y las
pruebas del software principal no se ven afectadas: el agente crea y mantiene
sus propias tablas.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sync_agent.comun import ahora_utc

# Estados del journal
PENDIENTE = "pendiente"
ENVIANDO = "enviando"
CONFIRMADA = "confirmada"
RECHAZADA = "rechazada"
DIFERIDA = "diferida"

DIRECCION_SALIDA = "salida"
DIRECCION_ENTRADA = "entrada"

# Estados de un binario en tránsito
BLOB_POR_SUBIR = "por_subir"
BLOB_SUBIDO = "subido"
BLOB_POR_BAJAR = "por_bajar"
BLOB_DISPONIBLE = "disponible"
BLOB_OMITIDO = "omitido"


class BaseSync(DeclarativeBase):
    """Base declarativa exclusiva de las tablas del agente"""


class SyncId(BaseSync):
    """Equivalencia entre la identidad global (UUID) y el id local de cada puesto"""

    __tablename__ = "sync_ids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    uuid: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    id_local: Mapped[int] = mapped_column(Integer, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)

    __table_args__ = (
        UniqueConstraint("tabla", "uuid", name="uq_sync_ids_tabla_uuid"),
        UniqueConstraint("tabla", "id_local", name="uq_sync_ids_tabla_id_local"),
    )


class JournalOp(BaseSync):
    """
    Operación pendiente de enviar (dirección salida) o diferida de aplicar
    (dirección entrada)

    El ``id`` actúa como secuencia local: crece de forma monótona en este
    equipo, lo que permite ordenar sus propias operaciones cuando los sellos de
    tiempo coinciden. El orden autoritativo entre equipos lo asigna el nodo
    central con su ``seq`` global.
    """

    __tablename__ = "sync_journal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    op_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fila_uuid: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operacion: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    base_op_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dispositivo: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    usuario: Mapped[str | None] = mapped_column(String(50), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=PENDIENTE, index=True)
    direccion: Mapped[str] = mapped_column(
        String(10), nullable=False, default=DIRECCION_SALIDA, index=True
    )
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_sync_journal_estado_direccion", "estado", "direccion"),)


class CampoRemoto(BaseSync):
    """Última escritura conocida de cada campo de cada fila (base de la mezcla)"""

    __tablename__ = "sync_campos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fila_uuid: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    campo: Mapped[str] = mapped_column(String(80), nullable=False)
    valor: Mapped[str | None] = mapped_column(Text, nullable=True)
    op_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dispositivo: Mapped[str] = mapped_column(String(36), nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    __table_args__ = (UniqueConstraint("tabla", "fila_uuid", "campo", name="uq_sync_campos_clave"),)


class VersionFila(BaseSync):
    """Estado de una fila replicada: última operación y borrado vigente"""

    __tablename__ = "sync_versiones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fila_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    ultimo_op_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dispositivo: Mapped[str | None] = mapped_column(String(36), nullable=True)
    borrado: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    borrado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    borrado_op_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    borrado_dispositivo: Mapped[str | None] = mapped_column(String(36), nullable=True)

    __table_args__ = (UniqueConstraint("tabla", "fila_uuid", name="uq_sync_versiones_clave"),)


class OpAplicada(BaseSync):
    """Registro de operaciones ya aplicadas: garantiza aplicación exactamente una vez"""

    __tablename__ = "sync_ops_aplicadas"

    op_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    aplicado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)


class CursorSync(BaseSync):
    """Marca de agua de la última novedad descargada del nodo central"""

    __tablename__ = "sync_cursor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ultimo_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=ahora_utc, onupdate=ahora_utc
    )


class ConflictoSync(BaseSync):
    """Bandeja de conflictos: el valor perdedor nunca se descarta en silencio"""

    __tablename__ = "sync_conflictos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fila_uuid: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    campo: Mapped[str] = mapped_column(String(80), nullable=False)
    valor_local: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_remoto: Mapped[str | None] = mapped_column(Text, nullable=True)
    ganador: Mapped[str] = mapped_column(String(10), nullable=False)
    regla: Mapped[str] = mapped_column(String(80), nullable=False)
    op_local_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    op_remoto_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    detectado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)
    resuelto: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resolucion: Mapped[str | None] = mapped_column(Text, nullable=True)


class BlobSync(BaseSync):
    """Binario en tránsito: se identifica por hash y nunca se duplica"""

    __tablename__ = "sync_blobs"

    hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    tamano: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False)
    fila_uuid: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    columna: Mapped[str] = mapped_column(String(80), nullable=False)
    direccion: Mapped[str] = mapped_column(String(10), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default=BLOB_POR_SUBIR)
    intentos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=ahora_utc, onupdate=ahora_utc
    )


class EstadoSync(BaseSync):
    """Estado operativo del agente en este equipo (última sincronización, error...)"""

    __tablename__ = "sync_estado"

    clave: Mapped[str] = mapped_column(String(50), primary_key=True)
    valor: Mapped[str | None] = mapped_column(Text, nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=ahora_utc, onupdate=ahora_utc
    )


# ----------------------------------------------------------------------
# Tablas exclusivas del nodo central
# ----------------------------------------------------------------------
class DispositivoSync(BaseSync):
    """Puesto autorizado a sincronizar (el token se guarda hasheado)"""

    __tablename__ = "sync_dispositivos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dispositivo_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)
    ultima_conexion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    version_app: Mapped[str | None] = mapped_column(String(30), nullable=True)


class OpServidor(BaseSync):
    """Log autoritativo del nodo central: el ``seq`` es el orden global"""

    __tablename__ = "sync_ops"

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    op_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fila_uuid: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operacion: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    base_op_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dispositivo: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    usuario: Mapped[str | None] = mapped_column(String(50), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    recibido_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)


class BitacoraSync(BaseSync):
    """Auditoría del nodo central: cada ciclo aceptado o rechazado"""

    __tablename__ = "sync_bitacora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dispositivo: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    evento: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    correcto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)


def tablas() -> list:
    """Todas las tablas del agente (para respaldos, purgas y pruebas)"""
    return list(BaseSync.metadata.sorted_tables)


def asegurar_esquema(engine) -> None:
    """
    Crea las tablas del agente si no existen (idempotente)

    Args:
        engine: Motor SQLAlchemy del archivo de base de datos
    """
    BaseSync.metadata.create_all(bind=engine, checkfirst=True)


def preparar(engine, session_factory=None) -> None:
    """
    Deja el agente listo: tablas creadas y captura de cambios instalada

    Args:
        engine: Motor SQLAlchemy del archivo de base de datos
        session_factory: Fábrica de sesiones sobre la que capturar los cambios
    """
    asegurar_esquema(engine)
    if session_factory is not None:
        from sync_agent.captura import instalar

        instalar(session_factory, engine)


def motor_desde_url(url: str, echo: bool = False):
    """Crea un motor SQLite/SQLAlchemy con los parámetros del proyecto"""
    parametros = {}
    if url.startswith("sqlite"):
        parametros = {"connect_args": {"check_same_thread": False, "timeout": 30}}
    return create_engine(url, echo=echo, pool_pre_ping=True, **parametros)
