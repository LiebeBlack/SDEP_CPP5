"""
Cliente HTTP del protocolo de sincronización

Usa la biblioteca estándar (``urllib``), igual que el actualizador del
sistema: la aplicación se instala en equipos de colegio y no conviene sumar
dependencias por un canal que solo necesita hablar con un servicio de la
intranet.

Los errores se clasifican por su naturaleza, porque el agente reacciona
distinto ante cada uno: un corte de red se reintenta con espera creciente, un
token inválido se detiene y se avisa al usuario, y una respuesta malformada se
registra como incidente del servidor.
"""

from __future__ import annotations

import json
import logging
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from sync_agent.comun import dumps, hash_bytes

logger = logging.getLogger(__name__)

RUTA_PING = "/api/v1/ping"
RUTA_PUSH = "/api/v1/push"
RUTA_PULL = "/api/v1/pull"
RUTA_BLOB = "/api/v1/blob"

USER_AGENT = "SDEP-SyncAgent/1.0"


class ErrorSincronizacion(Exception):
    """Error base del canal con el nodo central"""


class ErrorRed(ErrorSincronizacion):
    """Fallo transitorio: sin red, servidor apagado o respuesta 5xx"""


class ErrorAutenticacion(ErrorSincronizacion):
    """El token del equipo no es válido o fue revocado"""


class ErrorProtocolo(ErrorSincronizacion):
    """El servidor respondió algo que el agente no entiende"""


@dataclass
class Respuesta:
    """Respuesta del nodo central ya decodificada"""

    datos: dict[str, Any]

    def __getitem__(self, clave: str) -> Any:
        return self.datos.get(clave)


class ClienteSync:
    """Cliente del nodo central de sincronización"""

    def __init__(
        self,
        url_servidor: str,
        token: str,
        dispositivo: str,
        timeout: int = 15,
        verificar_ssl: bool = True,
    ):
        """
        Args:
            url_servidor: Dirección base del servicio (http://host:8765)
            token: Token entregado por el administrador del nodo central
            dispositivo: Identificador del equipo
            timeout: Segundos de espera por petición
            verificar_ssl: Validar el certificado del servidor (no desactivar
                salvo en una intranet con certificado propio)
        """
        self.base = url_servidor.rstrip("/")
        self.token = token
        self.dispositivo = dispositivo
        self.timeout = timeout
        if verificar_ssl:
            self.contexto = ssl.create_default_context()
        else:
            logger.warning("Verificación TLS desactivada: solo para pruebas de intranet")
            self.contexto = ssl._create_unverified_context()

    # ------------------------------------------------------------------
    # Operaciones del protocolo
    # ------------------------------------------------------------------
    def ping(self) -> dict:
        """Comprueba el servicio y devuelve su estado y su hora"""
        return self._peticion("GET", RUTA_PING).datos

    def enviar_ops(self, operaciones: list[dict]) -> dict:
        """
        Envía un lote de operaciones locales

        Args:
            operaciones: Operaciones del protocolo

        Returns:
            Resultado del servidor (aplicadas, rechazadas, conflictos, cursor)
        """
        cuerpo = {"dispositivo": self.dispositivo, "ops": operaciones}
        return self._peticion("POST", RUTA_PUSH, cuerpo).datos

    def recibir_ops(self, cursor: int, limite: int = 200) -> dict:
        """
        Descarga las novedades posteriores al cursor

        Args:
            cursor: Último ``seq`` global aplicado
            limite: Máximo de operaciones por lote

        Returns:
            Operaciones y cursor actualizado
        """
        ruta = f"{RUTA_PULL}?cursor={int(cursor)}&limite={int(limite)}"
        return self._peticion("GET", ruta).datos

    def subir_blob(self, hash_archivo: str, contenido: bytes) -> None:
        """Envía un archivo binario identificado por su hash"""
        if hash_bytes(contenido) != hash_archivo:
            raise ErrorProtocolo("El contenido local no coincide con su hash declarado")
        self._peticion("POST", f"{RUTA_BLOB}/{hash_archivo}", datos_binarios=contenido)

    def bajar_blob(self, hash_archivo: str) -> bytes | None:
        """
        Descarga un archivo binario y comprueba su integridad

        Returns:
            Contenido verificado, o None si el servidor no lo tiene
        """
        try:
            respuesta = self._peticion("GET", f"{RUTA_BLOB}/{hash_archivo}", binario=True)
        except ErrorProtocolo:
            logger.warning("El nodo central no tiene el archivo %s", hash_archivo[:12])
            return None
        contenido = respuesta.datos.get("binario") or b""
        if hash_bytes(contenido) != hash_archivo:
            logger.error("El archivo %s llegó corrupto y se descarta", hash_archivo[:12])
            return None
        return contenido

    # ------------------------------------------------------------------
    # Transporte
    # ------------------------------------------------------------------
    def _peticion(
        self, metodo: str, ruta: str, cuerpo: dict | None = None, datos_binarios: bytes | None = None,
        binario: bool = False,
    ) -> Respuesta:
        """Ejecuta una petición y clasifica cualquier fallo"""
        url = f"{self.base}{ruta}"
        cabeceras = {
            "User-Agent": USER_AGENT,
            "Authorization": f"Bearer {self.token}",
            "X-Dispositivo": self.dispositivo,
            "Accept": "application/json",
        }
        datos = None
        if cuerpo is not None:
            datos = dumps(cuerpo).encode("utf-8")
            cabeceras["Content-Type"] = "application/json; charset=utf-8"
        elif datos_binarios is not None:
            datos = datos_binarios
            cabeceras["Content-Type"] = "application/octet-stream"

        peticion = urllib.request.Request(url, data=datos, headers=cabeceras, method=metodo)
        try:
            with urllib.request.urlopen(peticion, timeout=self.timeout, context=self.contexto) as resp:
                crudo = resp.read()
        except urllib.error.HTTPError as error:
            raise self._clasificar(error) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise ErrorRed(f"Sin conexión con {self.base}: {error}") from error

        if binario:
            return Respuesta({"binario": crudo})
        if not crudo:
            return Respuesta({})
        try:
            return Respuesta(json.loads(crudo.decode("utf-8")))
        except (UnicodeDecodeError, ValueError) as error:
            raise ErrorProtocolo(f"Respuesta ilegible del servidor: {error}") from error

    @staticmethod
    def _clasificar(error: urllib.error.HTTPError) -> ErrorSincronizacion:
        """Traduce un código HTTP en el error que corresponde al agente"""
        try:
            detalle = error.read().decode("utf-8", errors="replace")[:300]
        except Exception:  # pragma: no cover - cuerpo no legible
            detalle = ""
        if error.code == 401:
            return ErrorAutenticacion("El token del equipo no es válido o fue revocado")
        if error.code == 404:
            return ErrorProtocolo(f"Recurso no encontrado ({error.code}): {detalle}")
        if error.code in (413, 422):
            return ErrorProtocolo(f"Lote rechazado por el servidor ({error.code}): {detalle}")
        if error.code == 429:
            return ErrorRed(f"El servidor pidió esperar ({error.code}): {detalle}")
        return ErrorRed(f"El servidor respondió {error.code}: {detalle}")
