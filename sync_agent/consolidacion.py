"""
Reglas puras del ciclo de consolidación

El nodo central es el motor de reconstrucción histórica: guarda **cada** evento
de cada máquina en un log inmutable, los ordena por su marca de tiempo corregida
y reproduce la historia de cada fila afectada para obtener el estado final.

Este módulo no toca la base de datos: son funciones puras que comparten el
servidor (al consolidar), el agente (al verificar el ciclo antes de aplicarlo) y
las pruebas. Así el orden y el manifiesto se calculan exactamente igual en los
dos extremos, y un ciclo alterado o incompleto se detecta por su hash.

Reglas del modelo
-----------------
* **Nada se descarta**: cada operación es un evento del log, con su sello crudo
  y el corregido por el desfase medido del equipo emisor.
* **Orden total**: ``(ocurrido_corregido, dispositivo, op_id)``. El desempate
  solo entra cuando dos hechos comparten exactamente el mismo sello, y es
  determinista, de modo que todos los nodos reconstruyen la misma historia.
* **Replay por fila**: el estado de una fila es el resultado de reproducir su
  historia completa; una edición posterior a un borrado la revive.
* **Commit indivisible**: el resultado del replay se publica como un ciclo
  (``epoch``) con manifiesto; el cliente lo aplica entero o no aplica nada.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Iterable

# Desfase de reloj que se acepta corregir. Más allá de un día, el sello del
# puesto es un error de configuración, no un desfase medible en la intranet.
DESFASE_MAXIMO_MS = 24 * 60 * 60 * 1000

ESTADO_SIN_NOVEDADES = "sin_novedades"

OPERACION_BORRADO = "delete"


def acotar_desfase(valor: Any) -> int:
    """
    Normaliza el desfase reportado por un puesto (milisegundos)

    Un valor absurdo (reloj a años de distancia) se recorta en lugar de
    reordenar la historia completa del colegio.
    """
    try:
        desfase = int(valor or 0)
    except (TypeError, ValueError):
        return 0
    return max(-DESFASE_MAXIMO_MS, min(DESFASE_MAXIMO_MS, desfase))


def corregir_momento(momento: datetime, desfase_ms: int) -> datetime:
    """
    Sello del puesto traducido al reloj del nodo central

    ``desfase_ms`` es lo que adelanta el reloj del puesto respecto del servidor
    (medido en el handshake): restarlo deja el hecho en la línea de tiempo
    común, sin reescribir el sello original, que se conserva en el log.
    """
    return momento - timedelta(milliseconds=int(desfase_ms or 0))


def momento_de_texto(crudo: Any, respaldo: datetime | None = None) -> datetime | None:
    """Interpreta un sello ISO del protocolo (``respaldo`` si no se puede)"""
    if isinstance(crudo, datetime):
        return crudo
    if not crudo:
        return respaldo
    try:
        return datetime.fromisoformat(str(crudo))
    except (TypeError, ValueError):
        return respaldo


def clave_cronologica(evento: dict) -> tuple[datetime, str, str]:
    """
    Orden total y determinista de los hechos

    ``ocurrido_corregido`` manda; el dispositivo y el ``op_id`` solo desempatan
    dos hechos con exactamente el mismo sello.
    """
    momento = (
        momento_de_texto(evento.get("ocurrido_corregido"))
        or momento_de_texto(evento.get("ocurrido_en"))
        or datetime.min
    )
    return (momento, str(evento.get("dispositivo") or ""), str(evento.get("op_id") or ""))


def ordenar_eventos(eventos: Iterable[dict]) -> list[dict]:
    """Lista de eventos en el orden en que ocurrieron"""
    return sorted(eventos, key=clave_cronologica)


def payload_de(evento: dict) -> dict:
    """Payload del evento ya decodificado (dict vacío si viene ilegible)"""
    crudo = evento.get("payload")
    if isinstance(crudo, dict):
        return dict(crudo)
    if isinstance(crudo, str) and crudo:
        try:
            valor = json.loads(crudo)
        except ValueError:
            return {}
        return dict(valor) if isinstance(valor, dict) else {}
    return {}


def agrupar_por_fila(eventos: Iterable[dict]) -> dict[tuple[str, str], list[dict]]:
    """Agrupa los eventos por fila, conservando el orden recibido"""
    grupos: dict[tuple[str, str], list[dict]] = {}
    for evento in eventos:
        clave = (str(evento.get("tabla") or ""), str(evento.get("fila_uuid") or ""))
        grupos.setdefault(clave, []).append(evento)
    return grupos


def reconstruir(historial: Iterable[dict]) -> dict[str, Any] | None:
    """
    Estado final de una fila al reproducir su historia completa

    Cada evento solo aporta las columnas que tocó; un borrado se deshace si
    después hubo una edición (perder un dato reciente es peor que revivir un
    registro borrado por error). No se decide por «el último que llegó», sino
    por el orden cronológico de los hechos.

    Returns:
        ``{"valores": {...}, "borrado": bool}`` o None si no hay historia
    """
    valores: dict[str, Any] = {}
    borrado = False
    hubo_eventos = False
    for evento in ordenar_eventos(historial):
        hubo_eventos = True
        if str(evento.get("operacion") or "upsert") == OPERACION_BORRADO:
            borrado = True
            continue
        valores.update(payload_de(evento))
        borrado = False
    if not hubo_eventos:
        return None
    return {"valores": valores, "borrado": borrado}


def fila_publicada(tabla: str, fila_uuid: str, historial: Iterable[dict]) -> dict | None:
    """Estado consolidado de una fila, con su identidad global"""
    estado = reconstruir(historial)
    if estado is None:
        return None
    return {"tabla": tabla, "fila_uuid": fila_uuid, **estado}


def _canonico(datos: Any) -> str:
    """JSON estable: el mismo texto en el servidor y en cada puesto"""
    return json.dumps(
        datos,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def _evento_canonico(evento: dict) -> dict:
    """Forma canónica de un evento para el manifiesto del ciclo"""
    momento = momento_de_texto(evento.get("ocurrido_corregido")) or momento_de_texto(
        evento.get("ocurrido_en")
    )
    return {
        "op_id": str(evento.get("op_id") or ""),
        "tabla": str(evento.get("tabla") or ""),
        "fila_uuid": str(evento.get("fila_uuid") or ""),
        "operacion": str(evento.get("operacion") or "upsert"),
        "payload": _canonico(payload_de(evento)),
        "dispositivo": str(evento.get("dispositivo") or ""),
        "ocurrido_corregido": momento.isoformat() if momento else "",
        "secuencia_global": int(evento.get("secuencia_global") or 0),
    }


def _fila_canonica(fila: dict) -> dict:
    """Forma canónica de una fila consolidada para el manifiesto del ciclo"""
    return {
        "tabla": str(fila.get("tabla") or ""),
        "fila_uuid": str(fila.get("fila_uuid") or ""),
        "borrado": bool(fila.get("borrado")),
        "valores": _canonico(dict(fila.get("valores") or {})),
    }


def manifiesto_epoch(eventos: Iterable[dict], filas: Iterable[dict]) -> str:
    """
    Huella del ciclo completo

    El servidor la publica y cada cliente la recalcula con lo que recibió: si no
    coincide, el paquete llegó incompleto o alterado y no se aplica nada.
    """
    contenido = {
        "eventos": [_evento_canonico(evento) for evento in eventos],
        "filas": [_fila_canonica(fila) for fila in filas],
    }
    return hashlib.sha256(_canonico(contenido).encode("utf-8")).hexdigest()


def hash_lote(eventos: Iterable[dict]) -> str:
    """Huella del lote recibido (auditoría del staging)"""
    contenido = [_evento_canonico(evento) for evento in eventos]
    return hashlib.sha256(_canonico(contenido).encode("utf-8")).hexdigest()


def manifiesto_valido(paquete: dict) -> bool:
    """Indica si el ciclo recibido coincide con su manifiesto"""
    try:
        esperado = str(paquete.get("manifiesto") or "")
        if not esperado:
            return False
        calculado = manifiesto_epoch(paquete.get("eventos") or [], paquete.get("filas") or [])
        return calculado == esperado
    except (TypeError, ValueError):
        return False


def validar_paquete(paquete: dict) -> str | None:
    """
    Motivo por el que un ciclo no se puede aplicar

    Returns:
        None si el paquete es aplicable; el motivo del rechazo en caso contrario
    """
    if not isinstance(paquete, dict):
        return "ciclo ilegible"
    try:
        epoch = int(paquete.get("epoch") or 0)
    except (TypeError, ValueError):
        return "ciclo sin número"
    if epoch <= 0:
        return "ciclo sin número"
    if not isinstance(paquete.get("eventos"), list):
        return "ciclo sin eventos"
    if not isinstance(paquete.get("filas"), list):
        return "ciclo sin filas consolidadas"
    if not manifiesto_valido(paquete):
        return "el ciclo llegó incompleto o alterado"
    return None
