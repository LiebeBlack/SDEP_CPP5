"""
Utilidades comunes del agente de sincronización

Reúne lo que comparten el cliente y el nodo central: tiempos UTC naive
(igual que los modelos), identificadores globales, hashing de binarios y la
codificación JSON de los valores que viajan por el protocolo.

El protocolo nunca transporta tipos de Python: cada valor se convierte a una
forma canónica y comparable (números y textos tal cual, fechas y decimales con
etiqueta de tipo, binarios como su hash). Así dos equipos distintos producen
exactamente la misma representación para el mismo dato, condición necesaria
para que la mezcla sea determinista.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid as _uuid
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum as EnumPython
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Enum as EnumSQL, Float, Integer, LargeBinary, Numeric

logger = logging.getLogger(__name__)

# Claves reservadas dentro de un valor serializado
ETIQUETA_TIPO = "__t__"
ETIQUETA_BLOB = "__blob__"

TIPO_DECIMAL = "decimal"
TIPO_FECHA = "date"
TIPO_DATETIME = "datetime"
TIPO_TEXTO = "str"


# ----------------------------------------------------------------------
# Tiempo e identidad
# ----------------------------------------------------------------------
def ahora_utc() -> datetime:
    """Fecha/hora UTC actual naive, coherente con las columnas de los modelos"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def nuevo_uuid() -> str:
    """Identificador global de una operación o de una fila replicada"""
    return str(_uuid.uuid4())


def hash_bytes(contenido: bytes) -> str:
    """Hash SHA-256 con el que se identifica el contenido de un binario"""
    return hashlib.sha256(contenido).hexdigest()


# ----------------------------------------------------------------------
# Codificación JSON
# ----------------------------------------------------------------------
def dumps(datos: Any) -> str:
    """Serializa a JSON canónico (claves ordenadas, sin espacios inútiles)"""
    return json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def loads(texto: str | bytes | None) -> Any:
    """Deserializa un JSON del protocolo; devuelve None si no es válido"""
    if not texto:
        return None
    try:
        return json.loads(texto)
    except (TypeError, ValueError):
        logger.warning("Payload de sincronización ilegible", exc_info=True)
        return None


def serializar_valor(valor: Any) -> Any:
    """
    Convierte un valor de modelo a su forma transportable

    Args:
        valor: Valor leído de la base de datos

    Returns:
        Número, texto, nulo o diccionario con etiqueta de tipo
    """
    if valor is None or isinstance(valor, (bool, int, str)):
        return valor
    if isinstance(valor, float):
        return valor
    if isinstance(valor, Decimal):
        return {ETIQUETA_TIPO: TIPO_DECIMAL, "v": str(valor)}
    if isinstance(valor, datetime):
        return {ETIQUETA_TIPO: TIPO_DATETIME, "v": valor.isoformat()}
    if isinstance(valor, date):
        return {ETIQUETA_TIPO: TIPO_FECHA, "v": valor.isoformat()}
    if isinstance(valor, (bytes, bytearray, memoryview)):
        datos = bytes(valor)
        return {ETIQUETA_BLOB: hash_bytes(datos), "tamano": len(datos)}
    if isinstance(valor, EnumPython):
        return valor.value
    return {ETIQUETA_TIPO: TIPO_TEXTO, "v": str(valor)}


def deserializar_valor(columna: Any, crudo: Any) -> Any:
    """
    Convierte un valor del protocolo al tipo que espera la columna destino

    El binario se resuelve aparte (el contenido llega por el endpoint de
    blobs), por eso su marca se traduce a None: quien aplica decide si el
    contenido ya está disponible localmente.

    Args:
        columna: Columna SQLAlchemy destino
        crudo: Valor tal como llegó en el payload

    Returns:
        Valor coercido al tipo de la columna
    """
    if crudo is None:
        return None

    if isinstance(crudo, dict):
        if ETIQUETA_BLOB in crudo:
            return None
        etiqueta = crudo.get(ETIQUETA_TIPO)
        valor = crudo.get("v")
        if etiqueta == TIPO_DECIMAL:
            return _a_decimal(valor)
        if etiqueta == TIPO_DATETIME:
            return _a_datetime(valor)
        if etiqueta == TIPO_FECHA:
            return _a_fecha(valor)
        return valor

    try:
        tipo = columna.type
    except AttributeError:  # pragma: no cover - columna sintética
        return crudo

    if isinstance(tipo, EnumSQL):
        # Las columnas enumeradas guardan el texto del miembro; SQLAlchemy lo
        # valida al enlazar, así que se entrega tal cual.
        return str(crudo)
    if isinstance(tipo, Float):
        return _a_float(crudo)
    if isinstance(tipo, Numeric):
        return _a_decimal(crudo)
    if isinstance(tipo, Integer):
        return _a_entero(crudo)
    if isinstance(tipo, Boolean):
        return _a_booleano(crudo)
    if isinstance(tipo, DateTime):
        return _a_datetime(crudo)
    if isinstance(tipo, Date):
        return _a_fecha(crudo)
    return crudo


def es_columna_blob(columna: Any) -> bool:
    """Indica si la columna almacena contenido binario"""
    try:
        return isinstance(columna.type, LargeBinary)
    except AttributeError:  # pragma: no cover - columna sintética
        return False


def es_marca_blob(valor: Any) -> bool:
    """Indica si un valor del protocolo representa un binario"""
    return isinstance(valor, dict) and ETIQUETA_BLOB in valor


def hash_de_marca(valor: Any) -> str | None:
    """Hash declarado por una marca de binario, o None si no lo es"""
    if es_marca_blob(valor):
        return str(valor.get(ETIQUETA_BLOB))
    return None


def tamano_de_marca(valor: Any) -> int:
    """Tamaño declarado por una marca de binario (0 si no aplica)"""
    if not es_marca_blob(valor):
        return 0
    try:
        return int(valor.get("tamano") or 0)
    except (TypeError, ValueError):
        return 0


def descripcion_valor(valor: Any, limite: int = 200) -> str:
    """Texto corto y legible de un valor, para conflictos y registros"""
    if valor is None:
        return "«vacío»"
    texto = valor if isinstance(valor, str) else dumps(valor)
    return texto if len(texto) <= limite else f"{texto[:limite]}…"


def _a_decimal(valor: Any) -> Decimal | None:
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _a_float(valor: Any) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _a_entero(valor: Any) -> int | None:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _a_booleano(valor: Any) -> bool | None:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return bool(valor)
    if isinstance(valor, str):
        return valor.strip().lower() in ("true", "1", "yes", "on", "si", "sí", "verdadero")
    return None


def _a_fecha(valor: Any) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _a_datetime(valor: Any) -> datetime | None:
    if isinstance(valor, datetime):
        return valor
    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day)
    try:
        return datetime.fromisoformat(str(valor))
    except ValueError:
        return None
