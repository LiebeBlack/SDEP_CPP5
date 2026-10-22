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

# Estados de un lote recibido en el staging del nodo central
LOTE_RECIBIDO = "recibido"
LOTE_CONSOLIDADO = "consolidado"
LOTE_RECHAZADO = "rechazado"

# Estados de un evento del log inmutable
EVENTO_EN_STAGING = "staging"
EVENTO_CONSOLIDADO = "consolidado"


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


class LoteEntrada(BaseSync):
    """
    Paquete recibido de un puesto: la unidad de validación del staging

    El lote se registra completo antes de consolidar. Si la consolidación no
    puede cerrarse, el lote queda marcado con su motivo y **sus eventos siguen
    en el log**: nada se aplica a medias y nada se pierde.
    """

    __tablename__ = "sync_lotes"

    lote_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dispositivo: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    n_ops: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    desfase_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=LOTE_RECIBIDO, index=True
    )
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)
    consolidado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    epoch: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)


class EventoSync(BaseSync):
    """
    Log inmutable: cada acción de cada máquina, con su sello crudo y corregido

    Es la fuente de verdad del nodo central. ``ocurrido_en`` es lo que declaró
    el puesto y ``ocurrido_corregido`` lo que resulta de restarle el desfase
    medido de su reloj; el replay ordena por el segundo y conserva el primero
    para poder auditar qué reloj estaba mal.

    ``secuencia_global`` solo se asigna al consolidar: es el orden definitivo
    del replay dentro del ciclo, y es lo que publica el ``epoch``.
    """

    __tablename__ = "sync_eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    op_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    lote_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fila_uuid: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operacion: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    base_op_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dispositivo: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    usuario: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ocurrido_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    ocurrido_corregido: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    desfase_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recibido_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)
    secuencia_global: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    epoch: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EVENTO_EN_STAGING, index=True
    )
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_sync_eventos_estado_momento", "estado", "ocurrido_corregido"),
    )


class EpochSync(BaseSync):
    """Ciclo consolidado: la unidad atómica que reciben los puestos"""

    __tablename__ = "sync_epochs"

    epoch: Mapped[int] = mapped_column(Integer, primary_key=True)
    manifiesto: Mapped[str] = mapped_column(String(64), nullable=False)
    n_eventos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_filas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    publicado_en: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=ahora_utc
    )


class EpochFila(BaseSync):
    """Estado consolidado de cada fila afectada por un ciclo"""

    __tablename__ = "sync_epoch_filas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    epoch: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tabla: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    fila_uuid: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    valores: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    borrado: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("epoch", "tabla", "fila_uuid", name="uq_sync_epoch_filas_clave"),
    )


class AckEpoch(BaseSync):
    """Confirmación de un puesto: hasta qué ciclo tiene aplicado"""

    __tablename__ = "sync_acks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dispositivo: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    epoch: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    confirmado_en: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=ahora_utc
    )

    __table_args__ = (
        UniqueConstraint("dispositivo", "epoch", name="uq_sync_acks_clave"),
    )


class RelojPuesto(BaseSync):
    """Desfase de reloj medido de cada puesto (para corregir sus sellos)"""

    __tablename__ = "sync_relojes"

    dispositivo: Mapped[str] = mapped_column(String(36), primary_key=True)
    desfase_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rtt_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    medido_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)


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


class SesionApi(BaseSync):
    """
    Sesiones de usuario del protocolo 2

    El cliente móvil entra con usuario y contraseña de la tabla ``usuarios``
    y recibe un token aleatorio. Aquí solo queda su hash (SHA-256): nunca el
    token en claro, y tampoco la contraseña, que sigue viviendo como derivación
    PBKDF2 en la cuenta.
    """

    __tablename__ = "sync_sesiones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    nombre_completo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    dispositivo_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=ahora_utc)
    expira_en: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    expira_absoluta: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    debe_cambiar_password: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revocada: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


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
