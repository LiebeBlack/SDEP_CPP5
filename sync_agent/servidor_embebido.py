"""
Servidor central embebido en la aplicación de escritorio

El nodo de sincronización vivía en un script aparte (`iniciar_servidor.py`) que
había que ejecutar a mano. Este módulo lo integra en el arranque del sistema:

* levanta el servicio HTTP en segundo plano sobre el puerto 8765;
* crea la base central y el almacén de binarios dentro de la carpeta de datos
  del usuario (nunca junto a un ejecutable de solo lectura);
* siembra las cuentas iniciales para que el teléfono pueda entrar con usuario y
  contraseña;
* configura este mismo equipo como puesto cliente del nodo local, de modo que
  los datos que llegan del teléfono se repliquen a la base del escritorio.

La preferencia se guarda en ``config.json`` (``sync_servidor_auto``). En el
primer inicio la interfaz pregunta si este equipo será el servidor; después el
servidor se abre solo con el sistema.
"""

from __future__ import annotations

import errno
import logging
import socket
import threading
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sync_agent.servidor import ServidorConfig, ServidorSync

logger = logging.getLogger(__name__)

CLAVE_SERVIDOR_AUTO = "sync_servidor_auto"
PUERTO_PREDETERMINADO = 8765
NOMBRE_BASE_CENTRAL = "sync_central.db"
DIRECTORIO_BLOBS = "sync_blobs"

ESTADO_DETENIDO = "detenido"
ESTADO_INICIANDO = "iniciando"
ESTADO_ACTIVO = "activo"
ESTADO_OCUPADO = "ocupado"
ESTADO_ERROR = "error"

# Mismas cuentas que documenta README.md y que crea `iniciar_servidor.py`.
# Se crean solo si faltan: una instalación existente conserva sus claves.
USUARIOS_INICIALES = (
    ("admin", "Admin1234", "admin", "Administrador del Sistema"),
    ("manager", "Gestor1234", "manager", "Gestor Principal"),
    ("user", "Usuario1234", "user", "Usuario Estándar"),
    ("viewer", "Lector1234", "viewer", "Lector de Solo Lectura"),
)

# Códigos de "dirección en uso" en Windows (WSAEADDRINUSE) y POSIX.
_CODIGOS_PUERTO_OCUPADO = {errno.EADDRINUSE, 10048}

_CANDADO_MODULO = threading.Lock()
_SERVIDOR: "ServidorEmbebido | None" = None


def _a_bool(valor: Any, por_defecto: bool = False) -> bool:
    """Interpreta un valor de configuración como booleano"""
    if valor is None:
        return por_defecto
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in ("true", "1", "yes", "on", "si", "sí", "verdadero")


def preferencia_servidor() -> bool | None:
    """
    Preferencia guardada para este equipo

    Returns:
        True/False si ya se respondió, None si todavía no se preguntó.
    """
    from src.config import settings

    valor = settings.get_config_value(CLAVE_SERVIDOR_AUTO, None)
    if valor is None:
        return None
    return _a_bool(valor)


def obtener_ip_local() -> str:
    """Dirección IP de la red local (la que debe escribir el teléfono)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            # No envía paquetes: solo fuerza al sistema a elegir la interfaz
            # de salida, que es la misma que usa la red WiFi de la institución.
            conexion.connect(("8.8.8.8", 80))
            return str(conexion.getsockname()[0])
    except OSError:
        pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"


def _puerto_ocupado(puerto: int) -> bool:
    """Comprueba si ya hay un servicio escuchando en el puerto local"""
    if puerto <= 0:
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sonda:
            sonda.settimeout(0.4)
            return sonda.connect_ex(("127.0.0.1", puerto)) == 0
    except OSError:
        return False


def _estado_inicial() -> dict[str, Any]:
    """Estado de un servidor que todavía no se ha iniciado"""
    return {
        "estado": ESTADO_DETENIDO,
        "puerto": 0,
        "url_local": "",
        "url_red": "",
        "error": None,
        "cliente_configurado": False,
        "usuarios_creados": False,
    }


class ServidorEmbebido:
    """
    Nodo central y su hilo de servicio

    ``iniciar()`` devuelve de inmediato salvo que se pida ``esperar=True``, que
    se usa en el arranque para que el agente de sincronización ya encuentre la
    configuración del puesto escrita. ``detener()`` es idempotente y seguro
    incluso si el servidor aún se está preparando.
    """

    def __init__(
        self,
        directorio: str | Path | None = None,
        puerto: int = PUERTO_PREDETERMINADO,
        host: str = "0.0.0.0",
    ):
        if directorio is None:
            from src.config import settings

            directorio = settings.base_dir
        self.directorio = Path(directorio)
        self.puerto = int(puerto)
        self.host = host
        self.ip_local = obtener_ip_local()
        self._candado = threading.Lock()
        self._listo = threading.Event()
        self._detener = threading.Event()
        self._hilo: threading.Thread | None = None
        self._servidor: ServidorSync | None = None
        self._estado = _estado_inicial()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def iniciar(self, esperar: bool = False, timeout: float = 30.0) -> dict[str, Any]:
        """
        Arranca el nodo central (una sola vez)

        Args:
            esperar: bloquea hasta que el servicio esté escuchando (o falle)
            timeout: segundos máximos de espera cuando ``esperar`` es True

        Returns:
            Copia del estado vigente.
        """
        with self._candado:
            hilo_vivo = self._hilo is not None and self._hilo.is_alive()
            if not hilo_vivo:
                self._detener.clear()
                self._listo.clear()
                self._estado = dict(_estado_inicial(), estado=ESTADO_INICIANDO)
                self._directorio_listo()
                self._hilo = threading.Thread(
                    target=self._arrancar,
                    name="servidor-sync-embebido",
                    daemon=True,
                )
                self._hilo.start()

        if esperar:
            self._listo.wait(max(0.1, float(timeout)))
        return self.estado()

    def detener(self, timeout: float = 8.0) -> None:
        """Pide el cierre del servicio y espera al hilo (idempotente)"""
        self._detener.set()
        with self._candado:
            servidor = self._servidor
            hilo = self._hilo
        if servidor is not None:
            try:
                servidor.detener()
            except Exception:
                logger.debug("No se pudo pedir el cierre del nodo central", exc_info=True)
        if hilo is not None and hilo.is_alive():
            hilo.join(timeout=timeout)
        with self._candado:
            if self._hilo is hilo and (hilo is None or not hilo.is_alive()):
                self._hilo = None
            if self._servidor is servidor:
                self._servidor = None
            if self._estado.get("estado") != ESTADO_OCUPADO:
                self._estado = _estado_inicial()

    def estado(self) -> dict[str, Any]:
        """Copia thread-safe del estado para la interfaz y la bandeja"""
        with self._candado:
            return dict(self._estado)

    # ------------------------------------------------------------------
    # Arranque
    # ------------------------------------------------------------------
    def _directorio_listo(self) -> None:
        try:
            self.directorio.mkdir(parents=True, exist_ok=True)
        except OSError:
            logger.warning("No se pudo crear la carpeta del nodo central", exc_info=True)

    def _marcar(self, estado: str, **datos: Any) -> None:
        with self._candado:
            self._estado = dict(_estado_inicial(), estado=estado, **datos)

    def _arrancar(self) -> None:
        """Prepara la base, el servicio y la configuración del puesto"""
        servidor: ServidorSync | None = None
        nucleo = None

        if _puerto_ocupado(self.puerto):
            self._marcar(
                ESTADO_OCUPADO,
                puerto=self.puerto,
                error=(
                    f"El puerto {self.puerto} ya está en uso. "
                    "Puede que el servidor ya esté abierto en este equipo."
                ),
            )
            self._listo.set()
            return

        try:
            config = ServidorConfig(
                url_db=f"sqlite:///{(self.directorio / NOMBRE_BASE_CENTRAL).as_posix()}",
                dir_blobs=self.directorio / DIRECTORIO_BLOBS,
                host=self.host,
                puerto=self.puerto,
            )
            servidor = ServidorSync(config)
            nucleo = servidor.nucleo
        except OSError as error:
            codigo = getattr(error, "errno", None)
            estado = ESTADO_OCUPADO if codigo in _CODIGOS_PUERTO_OCUPADO else ESTADO_ERROR
            self._marcar(estado, puerto=self.puerto, error=str(error) or repr(error))
            self._listo.set()
            return
        except Exception as error:
            self._marcar(ESTADO_ERROR, puerto=self.puerto, error=str(error) or repr(error))
            logger.error("No se pudo crear el nodo central embebido", exc_info=True)
            self._listo.set()
            return

        puerto_real = int(servidor.server_address[1])
        url_local = f"http://127.0.0.1:{puerto_real}"
        url_red = f"http://{self.ip_local}:{puerto_real}"
        usuarios_creados = self._crear_usuarios(nucleo)
        cliente_configurado = False
        try:
            cliente_configurado = self._configurar_cliente(nucleo, url_local)
        except Exception:
            logger.warning("No se pudo auto-configurar este equipo como cliente", exc_info=True)

        with self._candado:
            if self._detener.is_set():
                # Se pidió detener mientras se preparaba la base: no se abre
                # el bucle de servicio y se libera lo construido.
                self._servidor = None
                self._estado = _estado_inicial()
            else:
                self._servidor = servidor
                self._estado = {
                    "estado": ESTADO_ACTIVO,
                    "puerto": puerto_real,
                    "url_local": url_local,
                    "url_red": url_red,
                    "error": None,
                    "cliente_configurado": cliente_configurado,
                    "usuarios_creados": usuarios_creados,
                }
        self._listo.set()

        if self._detener.is_set():
            try:
                servidor.cerrar()
            except Exception:
                logger.debug("Cierre defensivo del nodo central", exc_info=True)
            return

        logger.info(
            "Servidor central embebido escuchando en %s (base: %s)",
            url_red,
            config.url_db,
        )
        try:
            servidor.serve_forever(poll_interval=0.5)
        except Exception:
            logger.error("El servidor central embebido se detuvo por un error", exc_info=True)
            self._marcar(
                ESTADO_ERROR, puerto=puerto_real, error="El servidor se detuvo por un error"
            )
        finally:
            try:
                servidor.cerrar()
            finally:
                with self._candado:
                    if self._servidor is servidor:
                        self._servidor = None
                    self._hilo = None
                    if self._estado.get("estado") == ESTADO_ACTIVO:
                        self._estado = _estado_inicial()

    # ------------------------------------------------------------------
    # Auto-configuración
    # ------------------------------------------------------------------
    @staticmethod
    def _crear_usuarios(nucleo) -> bool:
        """
        Prepara las cuentas del nodo central

        Primero copia las cuentas del sistema de escritorio con su mismo hash,
        de modo que el teléfono use el mismo usuario y contraseña que la
        computadora. Después crea las cuentas iniciales que falten (una base ya
        usada conserva sus contraseñas).
        """
        from src.services.auth_service import AuthService

        sesion = nucleo.SessionFactory()
        try:
            servicio = AuthService(sesion)
            copiadas = ServidorEmbebido._copiar_usuarios_locales(sesion, servicio)
            for username, password, rol, nombre_completo in USUARIOS_INICIALES:
                if servicio.usuario_por_username(username) is None:
                    servicio.crear_usuario(
                        username,
                        password,
                        rol,
                        nombre_completo,
                        debe_cambiar_password=False,
                    )
                    logger.info("Cuenta inicial creada en el nodo central: %s", username)
            sesion.commit()
            if copiadas:
                logger.info("Cuentas del escritorio copiadas al nodo central: %s", copiadas)
            return True
        except Exception:
            sesion.rollback()
            logger.warning("No se pudieron crear las cuentas iniciales", exc_info=True)
            return False
        finally:
            sesion.close()

    @staticmethod
    def _copiar_usuarios_locales(sesion, servicio: Any) -> int:
        """
        Copia al nodo central las cuentas locales que todavía no existan

        Se copia el hash PBKDF2, nunca la contraseña en claro. La política de
        bloqueo y caducidad central empieza limpia; el rol, el estado y la
        obligación de cambiar la clave se conservan.
        """
        from src.config import db_config
        from src.models import Usuario

        copiadas = 0
        local = db_config.get_session()
        try:
            for origen in local.query(Usuario).all():
                if servicio.usuario_por_username(origen.username) is not None:
                    continue
                sesion.add(
                    Usuario(
                        username=origen.username,
                        password_hash=origen.password_hash,
                        nombre_completo=origen.nombre_completo,
                        rol=origen.rol,
                        activo=origen.activo,
                        debe_cambiar_password=origen.debe_cambiar_password,
                        fecha_cambio_password=origen.fecha_cambio_password,
                        password_historial=origen.password_historial,
                    )
                )
                copiadas += 1
            # El SessionFactory del nodo central usa autoflush=False: sin este
            # flush, las cuentas recién añadidas no las vería la consulta que
            # decide si hay que crear las cuentas iniciales.
            sesion.flush()
        except Exception:
            logger.warning("No se pudieron copiar las cuentas del escritorio", exc_info=True)
        finally:
            db_config.close_session(local)
        return copiadas

    @staticmethod
    def _configurar_cliente(nucleo, url_local: str) -> bool:
        """
        Deja este equipo como puesto cliente del nodo local

        Si el equipo venía sincronizando con otro servidor, el destino se
        reemplaza por el nodo local: es la única forma de que los datos del
        teléfono y los del escritorio compartan la misma base. Para seguir
        como cliente de otro servidor, este equipo no debe ser el nodo central.
        """
        from sync_agent import config as config_sync

        actual = config_sync.cargar()
        url_actual = (actual.url_servidor or "").strip()
        # Cualquier destino loopback es este mismo nodo, aunque el puerto haya
        # cambiado entre arranques (en producción es fijo, pero así el token
        # del puesto se reutiliza en lugar de duplicar dispositivos).
        es_este_nodo = urlparse(url_actual).hostname in ("127.0.0.1", "localhost", "::1")

        token_valido = False
        if es_este_nodo and actual.dispositivo_id and actual.token:
            try:
                nucleo.autenticar(actual.dispositivo_id, actual.token)
                token_valido = True
            except Exception:
                # El token puede pertenecer a una base central recreada.
                token_valido = False

        if token_valido:
            config_sync.guardar(url_servidor=url_local, habilitado=True)
            logger.info("Puesto configurado contra el nodo central local")
            return True

        nombre = actual.nombre_equipo or socket.gethostname()
        dispositivo_id, token = nucleo.crear_dispositivo(nombre)
        config_sync.guardar(
            url_servidor=url_local,
            token=token,
            dispositivo_id=dispositivo_id,
            habilitado=True,
            nombre_equipo=nombre,
        )
        logger.info("Puesto dado de alta en el nodo central y sincronización habilitada")
        return True


# ----------------------------------------------------------------------
# Instancia única del proceso
# ----------------------------------------------------------------------
def servidor_embebido_actual() -> ServidorEmbebido | None:
    """Servidor creado en este proceso, o None si nunca se arrancó"""
    return _SERVIDOR


def iniciar_servidor_embebido(
    esperar: bool = False,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Arranca (una sola vez) el nodo central de este proceso"""
    global _SERVIDOR
    with _CANDADO_MODULO:
        if _SERVIDOR is None:
            _SERVIDOR = ServidorEmbebido()
    return _SERVIDOR.iniciar(esperar=esperar, timeout=timeout)


def detener_servidor_embebido(timeout: float = 8.0) -> None:
    """Detiene el nodo central si estaba en marcha"""
    if _SERVIDOR is not None:
        _SERVIDOR.detener(timeout=timeout)


def estado_servidor_embebido() -> dict[str, Any]:
    """Estado del nodo central para la interfaz y la bandeja"""
    if _SERVIDOR is None:
        return _estado_inicial()
    return _SERVIDOR.estado()
