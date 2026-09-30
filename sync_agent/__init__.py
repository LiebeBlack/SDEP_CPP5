"""
Agente de Sincronización de Datos para la intranet (SDEP-CPP5)

Paquete **independiente** (se ejecuta con ``py -3 -m sync_agent``) que replica de
forma bidireccional los datos del sistema entre los puestos de la intranet y un
nodo central, y que además se integra en el software principal para funcionar
en segundo plano sin que el usuario lo note.

Piezas principales:

* ``merge``: motor de mezcla puro, campo por campo, con desempate determinista.
* ``captura``: enganche al ORM que registra cada cambio en la misma transacción.
* ``aplicador``: aplica lo que llega de la red (lo comparten cliente y servidor).
* ``agente``: hilo de fondo con espera interrumpible, reintentos y estado.
* ``servidor``: nodo central (servicio HTTP de la biblioteca estándar).

La aplicación sigue escribiendo siempre en su SQLite local: si no hay red, el
usuario trabaja igual y los cambios quedan encolados con su marca de tiempo.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from sync_agent.agente import (
    ESTADO_DETENIDO,
    ESTADO_ERROR_TOKEN,
    ESTADO_INACTIVO,
    ESTADO_SIN_CONEXION,
    ESTADO_SINCRONIZADO,
    ESTADO_SINCRONIZANDO,
    AgenteSincronizacion,
)
from sync_agent.config import ConfigSync, cargar, guardar
from sync_agent.merge import Conflicto, Marca, Plan, VersionFila, decidir_campo, planificar_campos

__all__ = [
    "AgenteSincronizacion",
    "ConfigSync",
    "Conflicto",
    "Marca",
    "Plan",
    "VersionFila",
    "agente_actual",
    "cargar",
    "decidir_campo",
    "detener_agente",
    "estado_sincronizacion",
    "guardar",
    "iniciar_agente",
    "planificar_campos",
    "sincronizar_ahora",
    "ESTADO_DETENIDO",
    "ESTADO_ERROR_TOKEN",
    "ESTADO_INACTIVO",
    "ESTADO_SIN_CONEXION",
    "ESTADO_SINCRONIZADO",
    "ESTADO_SINCRONIZANDO",
]

logger = logging.getLogger(__name__)

_agente: AgenteSincronizacion | None = None


def iniciar_agente(
    config: ConfigSync | None = None,
    notificador: Callable[[dict], None] | None = None,
) -> AgenteSincronizacion:
    """
    Crea (si hace falta) y arranca el agente de sincronización

    Es idempotente: si el agente ya está funcionando se devuelve el mismo y solo
    se actualiza el notificador de la interfaz.

    Args:
        config: Configuración a usar (se lee del archivo si no se pasa)
        notificador: Función que la interfaz registra para recibir el estado

    Returns:
        La instancia del agente (en marcha o inactiva según la configuración)
    """
    global _agente
    if _agente is None:
        _agente = AgenteSincronizacion(config or cargar(), notificador=notificador)
    elif notificador is not None:
        _agente.notificador = notificador
    _agente.iniciar()
    return _agente


def agente_actual() -> AgenteSincronizacion | None:
    """Agente creado en este proceso, o None si nunca se arrancó"""
    return _agente


def detener_agente(timeout: float = 5.0) -> None:
    """Detiene el agente si estaba funcionando (se llama al cerrar la aplicación)"""
    if _agente is not None:
        _agente.detener(timeout=timeout)


def estado_sincronizacion() -> dict[str, Any]:
    """
    Estado de la sincronización para la interfaz

    Returns:
        Copia del estado del agente; si nunca se arrancó, un estado detenido con
        la configuración vigente (para poder mostrarla y activarla).
    """
    if _agente is not None:
        return _agente.estado()
    config = cargar()
    return {
        "habilitado": config.activo,
        "estado": ESTADO_DETENIDO,
        "pendientes": 0,
        "conflictos": 0,
        "ultima_sincronizacion": None,
        "ultimo_error": None,
        "desfase_reloj_segundos": None,
        "ms_ultimo_ciclo": None,
        "ciclos": 0,
        "subidas": 0,
        "bajadas": 0,
        "fallos_consecutivos": 0,
        "siguiente_intento_segundos": None,
    }


def sincronizar_ahora() -> bool:
    """
    Pide una sincronización inmediata sin bloquear la interfaz

    Si el agente está en marcha se despierta el hilo; si está inactivo (por
    configuración) se ejecuta un ciclo suelto en un hilo de un solo uso, para
    que el botón de la ventana siga siendo útil.

    Returns:
        True si la petición quedó atendida
    """
    import threading

    if _agente is None:
        return False
    if _agente.activo():
        return _agente.sincronizar_ahora()
    threading.Thread(target=_agente.ciclo, name="sync-manual", daemon=True).start()
    return True
