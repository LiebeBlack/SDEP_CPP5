"""
Configuración del agente de sincronización

La configuración vive en ``config.json`` (el mismo archivo de preferencias del
sistema) y admite sobrescritura por variables de entorno, de modo que un
despliegue pueda fijar el servidor y el token sin tocar la interfaz.

Decisión deliberada: el identificador del equipo (``dispositivo_id``) y el
token **no** se guardan en la tabla ``configuraciones``, porque esa tabla sí se
replica: cada puesto debe tener su propia identidad y su propio secreto.
"""

from __future__ import annotations

import logging
import os
import socket
from dataclasses import asdict, dataclass, replace
from urllib.parse import urlparse

from sync_agent.comun import nuevo_uuid

logger = logging.getLogger(__name__)

CLAVE_HABILITADO = "sync_habilitado"
CLAVE_URL = "sync_servidor_url"
CLAVE_INTERVALO = "sync_intervalo_segundos"
CLAVE_BINARIO_MAX = "sync_max_bytes_binario"
CLAVE_TOKEN = "sync_token"
CLAVE_DISPOSITIVO = "sync_dispositivo_id"
CLAVE_EQUIPO = "sync_nombre_equipo"

INTERVALO_MINIMO = 5
INTERVALO_MAXIMO = 3600


@dataclass
class ConfigSync:
    """Parámetros de funcionamiento del agente en este equipo"""

    habilitado: bool = False
    url_servidor: str = ""
    token: str = ""
    dispositivo_id: str = ""
    nombre_equipo: str = ""
    intervalo_segundos: int = 30
    timeout_segundos: int = 15
    max_ops_por_ciclo: int = 200
    max_bytes_por_ciclo: int = 2_000_000
    max_bytes_binario: int = 5 * 1024 * 1024

    # ------------------------------------------------------------------
    # Derivados
    # ------------------------------------------------------------------
    @property
    def configurado(self) -> bool:
        """Indica si hay servidor y token para intentar sincronizar"""
        return bool(self.url_servidor and self.token and self.dispositivo_id)

    @property
    def activo(self) -> bool:
        """Indica si el agente debe estar funcionando"""
        return bool(self.habilitado and self.configurado)

    def problemas(self) -> list[str]:
        """Lista de impedimentos para sincronizar (vacía si todo está bien)"""
        fallos: list[str] = []
        if not self.url_servidor:
            fallos.append("Falta la dirección del servidor central")
        elif not _url_valida(self.url_servidor):
            fallos.append(f"La dirección del servidor no es válida: {self.url_servidor}")
        if not self.token:
            fallos.append("Falta el token del equipo (lo entrega el servidor central)")
        if not self.dispositivo_id:
            fallos.append("Falta el identificador del equipo")
        if not (INTERVALO_MINIMO <= self.intervalo_segundos <= INTERVALO_MAXIMO):
            fallos.append(
                f"El intervalo debe estar entre {INTERVALO_MINIMO} y {INTERVALO_MAXIMO} segundos"
            )
        return fallos

    def a_dict(self) -> dict:
        """Representación en diccionario (sin el token, para mostrar en pantalla)"""
        datos = asdict(self)
        datos["token"] = "configurado" if self.token else ""
        return datos


def _url_valida(url: str) -> bool:
    """Comprueba que la dirección sea http(s) con host"""
    partes = urlparse(url)
    return partes.scheme in ("http", "https") and bool(partes.netloc)


def _a_bool(valor, por_defecto: bool = False) -> bool:
    if valor is None:
        return por_defecto
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in ("true", "1", "yes", "on", "si", "sí", "verdadero")


def _a_int(valor, por_defecto: int) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return por_defecto


def cargar() -> ConfigSync:
    """
    Lee la configuración efectiva (config.json + variables de entorno)

    Returns:
        ConfigSync con los valores vigentes y la identidad del equipo ya
        asignada (se genera y persiste la primera vez).
    """
    from src.config import settings

    leer = settings.get_config_value
    config = ConfigSync(
        habilitado=_a_bool(leer(CLAVE_HABILITADO, False)),
        url_servidor=str(leer(CLAVE_URL, "") or "").strip(),
        token=str(leer(CLAVE_TOKEN, "") or "").strip(),
        dispositivo_id=str(leer(CLAVE_DISPOSITIVO, "") or "").strip(),
        nombre_equipo=str(leer(CLAVE_EQUIPO, "") or "").strip(),
        intervalo_segundos=_a_int(leer(CLAVE_INTERVALO, 30), 30),
        max_bytes_binario=_a_int(leer(CLAVE_BINARIO_MAX, 5 * 1024 * 1024), 5 * 1024 * 1024),
    )

    # Sobrescritura por entorno: útil para despliegues y para las pruebas
    if os.getenv("SDP_SYNC_ACTIVADO") is not None:
        config.habilitado = _a_bool(os.getenv("SDP_SYNC_ACTIVADO"), config.habilitado)
    if os.getenv("SDP_SYNC_URL"):
        config.url_servidor = os.environ["SDP_SYNC_URL"].strip()
    if os.getenv("SDP_SYNC_TOKEN"):
        config.token = os.environ["SDP_SYNC_TOKEN"].strip()
    if os.getenv("SDP_SYNC_INTERVALO"):
        config.intervalo_segundos = _a_int(os.environ["SDP_SYNC_INTERVALO"], config.intervalo_segundos)
    if os.getenv("SDP_SYNC_BINARIO_MAX"):
        config.max_bytes_binario = _a_int(
            os.environ["SDP_SYNC_BINARIO_MAX"], config.max_bytes_binario
        )
    if os.getenv("SDP_SYNC_EQUIPO"):
        config.nombre_equipo = os.environ["SDP_SYNC_EQUIPO"].strip()

    if not config.nombre_equipo:
        config.nombre_equipo = socket.gethostname()
    if not config.dispositivo_id:
        config.dispositivo_id = nuevo_uuid()
        try:
            settings.set_config_value(CLAVE_DISPOSITIVO, config.dispositivo_id)
            settings.set_config_value(CLAVE_EQUIPO, config.nombre_equipo)
        except OSError:
            logger.warning("No se pudo guardar la identidad del equipo", exc_info=True)

    return config


def guardar(**cambios) -> ConfigSync:
    """
    Persiste cambios de configuración y devuelve la configuración resultante

    Args:
        cambios: pares clave/valor aceptados por ConfigSync

    Returns:
        ConfigSync actualizada
    """
    from src.config import settings

    mapa = {
        "habilitado": CLAVE_HABILITADO,
        "url_servidor": CLAVE_URL,
        "token": CLAVE_TOKEN,
        "intervalo_segundos": CLAVE_INTERVALO,
        "max_bytes_binario": CLAVE_BINARIO_MAX,
        "nombre_equipo": CLAVE_EQUIPO,
        # El identificador lo entrega el nodo central al dar de alta el puesto;
        # permitirlo aquí evita tener que tocar config.json a mano.
        "dispositivo_id": CLAVE_DISPOSITIVO,
    }
    for nombre, valor in cambios.items():
        clave = mapa.get(nombre)
        if clave is None:
            raise ValueError(f"Parámetro de sincronización desconocido: {nombre}")
        settings.set_config_value(clave, valor)
    return cargar()


class _ConfigDinamica:
    """
    Acceso perezoso a la configuración

    El agente se importa en muchos puntos del arranque; resolver el archivo de
    preferencias solo cuando se necesita evita depender del orden de carga.
    """

    def __getattr__(self, nombre: str):
        if nombre.startswith("_"):
            raise AttributeError(nombre)
        return getattr(cargar(), nombre)

    def recargar(self) -> ConfigSync:
        """Fuerza una lectura nueva del archivo de preferencias"""
        return cargar()

    def clonar(self, **cambios) -> ConfigSync:
        """Copia la configuración vigente con los cambios indicados"""
        return replace(cargar(), **cambios)


config_sync = _ConfigDinamica()
