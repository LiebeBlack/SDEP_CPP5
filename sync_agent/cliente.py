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
from sync_agent.config import url_servidor_valida

logger = logging.getLogger(__name__)

RUTA_PING = "/api/v1/ping"
RUTA_PUSH = "/api/v1/push"
RUTA_PULL = "/api/v1/pull"
RUTA_EPOCHS = "/api/v1/epochs"
RUTA_ACK = "/api/v1/ack"
RUTA_BLOB = "/api/v1/blob"

USER_AGENT = "SDEP-SyncAgent/1.0"


class _SinRedireccion(urllib.request.HTTPRedirectHandler):
    """No reenvía cabeceras con credenciales a otro destino por un 3xx."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ErrorSincronizacion(Exception):
    """Error base del canal con el nodo central"""


class ErrorRed(ErrorSincronizacion):
    """Fallo transitorio: sin red, servidor apagado o respuesta 5xx"""


class ErrorAutenticacion(ErrorSincronizacion):
    """El token del equipo no es válido o fue revocado"""


class ErrorProtocolo(ErrorSincronizacion):
    """El servidor respondió algo que el agente no entiende"""


class ErrorNoSoportado(ErrorProtocolo):
    """El nodo central no publica ciclos: hay que usar el protocolo anterior"""


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
        if not url_servidor_valida(url_servidor):
            raise ValueError("La URL del servidor debe ser HTTP(S), absoluta y sin credenciales")
        if not token or not token.strip():
            raise ValueError("Falta el token del equipo")
        if not dispositivo or not dispositivo.strip():
            raise ValueError("Falta el identificador del equipo")
        self.base = url_servidor.strip().rstrip("/")
        self.token = token.strip()
        self.dispositivo = dispositivo
        self.timeout = timeout
        if verificar_ssl:
            self.contexto = ssl.create_default_context()
        else:
            logger.warning("Verificación TLS desactivada: solo para pruebas de intranet")
            self.contexto = ssl._create_unverified_context()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=self.contexto), _SinRedireccion()
        )
        # build_opener conserva su handler HTTPRedirectHandler por defecto si
        # recibe una subclase; retirarlo evita que esa instancia siga 302.
        self._opener.handlers = [
            handler
            for handler in self._opener.handlers
            if not isinstance(handler, urllib.request.HTTPRedirectHandler)
            or isinstance(handler, _SinRedireccion)
        ]

    # ------------------------------------------------------------------
    # Operaciones del protocolo
    # ------------------------------------------------------------------
    def ping(self) -> dict:
        """Comprueba el servicio y devuelve su estado y su hora"""
        return self._peticion("GET", RUTA_PING).datos

    def enviar_ops(
        self,
        operaciones: list[dict],
        lote_id: str | None = None,
        desfase_ms: int = 0,
    ) -> dict:
        """
        Envía un lote de operaciones locales

        Args:
            operaciones: Operaciones del protocolo
            lote_id: Identificador del paquete (idempotencia del staging)
            desfase_ms: Desfase medido del reloj de este equipo

        Returns:
            Resultado del servidor (aplicadas, rechazadas, epoch, cursor)
        """
        cuerpo: dict[str, Any] = {
            "dispositivo": self.dispositivo,
            "ops": operaciones,
            "desfase_ms": int(desfase_ms or 0),
        }
        if lote_id:
            cuerpo["lote_id"] = str(lote_id)
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

    def recibir_epochs(self, desde: int, limite: int = 1) -> dict:
        """
        Descarga los ciclos consolidados posteriores a ``desde``

        Raises:
            ErrorNoSoportado: si el nodo central es de una versión anterior
        """
        ruta = f"{RUTA_EPOCHS}?desde={int(desde)}&limite={int(limite)}"
        return self._peticion("GET", ruta).datos

    def confirmar_epoch(self, epoch: int) -> dict:
        """Confirma que este puesto aplicó el ciclo indicado"""
        return self._peticion("POST", RUTA_ACK, {"epoch": int(epoch)}).datos

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
        self,
        metodo: str,
        ruta: str,
        cuerpo: dict | None = None,
        datos_binarios: bytes | None = None,
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
            with self._opener.open(peticion, timeout=self.timeout) as resp:
                crudo = resp.read()
        except urllib.error.HTTPError as error:
            raise self._clasificar(error) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise ErrorRed("Sin conexión con el servidor central") from error

        if binario:
            return Respuesta({"binario": crudo})
        if not crudo:
            return Respuesta({})
        try:
            datos = json.loads(crudo.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as error:
            raise ErrorProtocolo(
                "Respuesta ilegible del servidor (se esperaba JSON UTF-8)"
            ) from error
        if not isinstance(datos, dict):
            raise ErrorProtocolo("Respuesta inválida del servidor (se esperaba un objeto JSON)")
        return Respuesta(datos)

    @staticmethod
    def _clasificar(error: urllib.error.HTTPError) -> ErrorSincronizacion:
        """Traduce un código HTTP en el error que corresponde al agente"""
        # No propagar el cuerpo: puede repetir datos de la petición y acabar
        # en el log persistente o en el estado visible del agente.
        if error.code == 401:
            return ErrorAutenticacion("El token del equipo no es válido o fue revocado")
        if error.code == 404:
            return ErrorNoSoportado(f"Recurso no encontrado ({error.code})")
        if error.code in (413, 422):
            return ErrorProtocolo(f"Lote rechazado por el servidor ({error.code})")
        if 300 <= error.code < 400:
            return ErrorProtocolo("El servidor redirigió la solicitud; revise la URL configurada")
        if error.code == 429:
            return ErrorRed(f"El servidor pidió esperar ({error.code})")
        return ErrorRed(f"El servidor respondió {error.code}")
