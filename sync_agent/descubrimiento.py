"""
Difusión del nodo central en la red local

El teléfono no recibe ninguna dirección escrita a mano: pregunta por difusión
UDP y el nodo central contesta con el puerto donde escucha. La respuesta no
lleva el token ni ningún dato de la institución; solo la identidad del servicio
y el puerto, que el teléfono vuelve a confirmar con ``GET /api/v1/ping`` antes
de emparejarse.

El sondeo HTTP de la subred sigue existiendo como respaldo (algunos puntos de
acceso bloquean la difusión), pero este canal es el que hace que la conexión
sea inmediata y funcione aunque el servidor esté en otro segmento del mismo
dominio de difusión.

Autor: SDEP-CPP5
"""

from __future__ import annotations

import json
import logging
import socket
import threading

logger = logging.getLogger(__name__)

# Puerto fijo de descubrimiento (el HTTP es 8765; este no se mueve para que el
# teléfono no dependa de la configuración del servidor).
PUERTO_DESCUBRIMIENTO = 8766

# Firma mínima de la petición. Sin ella, cualquier datagrama perdido en el
# puerto haría que el servicio contestara a un escáner cualquiera.
FIRMA_PETICION = b"SDEP/1 DESCUBRIR"

# Identidad que el teléfono comprueba antes de confiar en la respuesta
IDENTIDAD_NODO = "nodo-central-sincronizacion"


class DifusorDescubrimiento:
    """
    Responde a las peticiones de descubrimiento mientras el nodo esté activo

    Se ejecuta en un hilo propio y nunca interrumpe el arranque: si el puerto de
    difusión está ocupado (otra instancia del servidor, un cortafuegos que no
    deja abrirlo), el servicio HTTP sigue funcionando y el teléfono puede
    encontrar el nodo por el sondeo de la subred.
    """

    def __init__(
        self,
        puerto_http: int,
        puerto: int = PUERTO_DESCUBRIMIENTO,
        nombre: str | None = None,
    ):
        self.puerto_http = int(puerto_http)
        self.puerto = int(puerto)
        self.nombre = (nombre or "").strip()
        self._socket: socket.socket | None = None
        self._hilo: threading.Thread | None = None
        self._detener = threading.Event()

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def iniciar(self) -> bool:
        """Abre el puerto y lanza el hilo; False si no se pudo difundir"""
        if self.puerto <= 0 or self.puerto_http <= 0:
            return False
        if self._hilo is not None and self._hilo.is_alive():
            return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # En POSIX, SO_REUSEADDR permite reabrir tras un cierre rápido. En
            # Windows haría que dos procesos compartieran el puerto y las
            # respuestas se repartieran al azar: allí se deja desactivado.
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self.puerto))
            sock.settimeout(0.5)
            self._socket = sock
        except OSError as error:
            logger.info(
                "No se pudo abrir la difusión UDP en el puerto %s (%s); "
                "el teléfono aún puede encontrar el nodo por la subred",
                self.puerto,
                error,
            )
            return False

        self._detener.clear()
        self._hilo = threading.Thread(
            target=self._servir,
            name="descubrimiento-sync-udp",
            daemon=True,
        )
        self._hilo.start()
        logger.info("Difusión del nodo central activa en UDP %s", self.puerto)
        return True

    def detener(self, timeout: float = 2.0) -> None:
        """Cierra el socket y espera al hilo (idempotente)"""
        self._detener.set()
        sock = self._socket
        self._socket = None
        if sock is not None:
            try:
                sock.close()
            except OSError:
                logger.debug("Cierre defensivo del socket de difusión", exc_info=True)
        hilo = self._hilo
        self._hilo = None
        if hilo is not None and hilo.is_alive():
            hilo.join(timeout=max(0.1, timeout))

    @property
    def activo(self) -> bool:
        return self._hilo is not None and self._hilo.is_alive()

    # ------------------------------------------------------------------
    # Servicio
    # ------------------------------------------------------------------
    def _respuesta(self) -> bytes:
        """Cuerpo de la respuesta: identidad, protocolo y puerto HTTP"""
        return json.dumps(
            {
                "servidor": IDENTIDAD_NODO,
                "version_protocolo": "2",
                "puerto": self.puerto_http,
                "nombre": self.nombre,
            },
            ensure_ascii=False,
        ).encode("utf-8")

    def _servir(self) -> None:
        sock = self._socket
        respuesta = self._respuesta()
        while not self._detener.is_set() and sock is not None:
            try:
                datos, origen = sock.recvfrom(512)
            except socket.timeout:
                continue
            except OSError:
                break
            if not datos.startswith(FIRMA_PETICION):
                continue
            try:
                sock.sendto(respuesta, origen)
            except OSError:
                logger.debug("Respuesta de difusión no entregada", exc_info=True)
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass


def iniciar_difusion(
    puerto_http: int,
    puerto: int = PUERTO_DESCUBRIMIENTO,
    nombre: str | None = None,
) -> DifusorDescubrimiento:
    """Crea e inicia el difusor (aunque no logre abrir el puerto)"""
    difusor = DifusorDescubrimiento(puerto_http=puerto_http, puerto=puerto, nombre=nombre)
    difusor.iniciar()
    return difusor
