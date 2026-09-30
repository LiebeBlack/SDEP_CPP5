"""
Nodo central de sincronización

Es un servicio HTTP pequeño (biblioteca estándar) que se ejecuta en un equipo de
la intranet y guarda el estado autoritativo: aplica las operaciones que reciben
los puestos con **el mismo motor de mezcla** que usan ellos, les asigna un ``seq``
global (que es el orden definitivo entre equipos) y responde las novedades que
cada puesto aún no tiene.

No hay dependencias nuevas: el servidor HTTP y el cliente TLS son de la
biblioteca estándar, y la persistencia reutiliza SQLAlchemy y los modelos del
sistema, de modo que las tablas del nodo central son exactamente las mismas.

Puesta en marcha
----------------
    py -3 -m sync_agent servidor --db sync_central.db --host 0.0.0.0 --port 8765
    py -3 -m sync_agent servidor --db sync_central.db --crear-dispositivo "Direccion"

El token se muestra una sola vez: en la base queda solo su hash.
"""

from __future__ import annotations

import json
import logging
import secrets
import threading
from dataclasses import dataclass, field
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from sync_agent import registro
from sync_agent.aplicador import AplicadorRemoto, momento_de_operacion
from sync_agent.comun import ahora_utc, dumps, hash_bytes, loads
from sync_agent.esquema import (
    BaseSync,
    BitacoraSync,
    ConflictoSync,
    DispositivoSync,
    OpServidor,
)

logger = logging.getLogger(__name__)

VERSION_PROTOCOLO = "1"
MAX_OPS_POR_LOTE = 500
MAX_BYTES_PETICION = 3 * 1024 * 1024
MAX_BYTES_BLOB = 64 * 1024 * 1024
PETICIONES_POR_MINUTO = 120
DIAS_RETENCION_OPS = 180


@dataclass
class ServidorConfig:
    """Parámetros de funcionamiento del nodo central"""

    url_db: str = "sqlite:///sync_central.db"
    dir_blobs: Path = field(default_factory=lambda: Path("sync_blobs"))
    host: str = "0.0.0.0"
    puerto: int = 8765
    max_ops_por_lote: int = MAX_OPS_POR_LOTE
    max_bytes_peticion: int = MAX_BYTES_PETICION
    max_bytes_blob: int = MAX_BYTES_BLOB
    peticiones_por_minuto: int = PETICIONES_POR_MINUTO
    certificado: str | None = None
    clave: str | None = None


class ErrorPeticion(Exception):
    """Petición inválida: se responde con el código indicado"""

    def __init__(self, mensaje: str, codigo: int = 400):
        super().__init__(mensaje)
        self.codigo = codigo


class NucleoCentral:
    """
    Lógica del nodo central, independiente del transporte HTTP

    Mantenerla separada permite usarla directamente desde las pruebas (sin
    abrir un puerto) y desde el propio asistente de consola, y deja al
    manejador HTTP solo la tarea de traducir peticiones y respuestas.
    """

    def __init__(self, config: ServidorConfig):
        self.config = config
        self.engine = self._crear_motor()
        self._preparar_esquema()
        # expire_on_commit=False es deliberado: las sesiones del servicio son
        # de vida corta y algunas devuelven una fila (el dispositivo que se
        # acaba de autenticar) que se usa DESPUÉS de que la sesión se cierre.
        # Con el valor por defecto, el commit caduca las columnas y leerlas
        # fuera de la sesión lanza DetachedInstanceError, de modo que toda
        # petición autenticada terminaba en un error 500.
        self.SessionFactory = sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=self.engine
        )
        self.config.dir_blobs.mkdir(parents=True, exist_ok=True)
        self._candado = threading.Lock()
        self._peticiones: dict[str, list] = {}
        logger.info("Nodo central listo en %s", self.config.url_db)

    # ------------------------------------------------------------------
    # Infraestructura
    # ------------------------------------------------------------------
    def _preparar_esquema(self) -> None:
        """
        Crea el esquema del nodo central: las tablas del agente **y las del dominio**

        El nodo central no es un simple buzón de operaciones: es el único
        escritor de la base compartida y el árbitro de la mezcla. Para poder
        resolver cada fila (por identidad global o por clave natural) y detectar
        los conflictos, necesita las mismas tablas de dominio que un puesto; sin
        ellas toda operación se rechazaba con `error_al_aplicar`.
        """
        from src.models import Base

        Base.metadata.create_all(bind=self.engine, checkfirst=True)
        BaseSync.metadata.create_all(bind=self.engine, checkfirst=True)
        logger.info(
            "Esquema del nodo central listo: %s tablas de dominio y %s del agente",
            len(Base.metadata.tables),
            len(BaseSync.metadata.tables),
        )

    def _crear_motor(self):
        from sync_agent.esquema import motor_desde_url

        motor = motor_desde_url(self.config.url_db, echo=False)
        if self.config.url_db.startswith("sqlite"):
            from sqlalchemy import event

            @event.listens_for(motor, "connect")
            def _pragmas(conexion, _registro):  # pragma: no cover - depende del motor
                cursor = conexion.cursor()
                try:
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA busy_timeout=30000")
                    cursor.execute("PRAGMA foreign_keys=ON")
                finally:
                    cursor.close()

        return motor

    def _sesion(self):
        return self.SessionFactory()

    def cerrar(self) -> None:
        """Libera el pool de conexiones"""
        try:
            self.engine.dispose()
        except Exception:  # pragma: no cover - cierre defensivo
            logger.debug("No se pudo liberar el motor del nodo central", exc_info=True)

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------
    def autenticar(self, dispositivo_id: str | None, token: str | None) -> DispositivoSync:
        """
        Verifica el dispositivo y su token

        Raises:
            ErrorPeticion: 401 si el dispositivo no existe o el token no coincide
        """
        if not dispositivo_id or not token:
            raise ErrorPeticion("Faltan las credenciales del equipo", 401)

        from src.utils.security import SecurityValidator

        sesion = self._sesion()
        try:
            dispositivo: DispositivoSync | None = (
                sesion.query(DispositivoSync)
                .filter(DispositivoSync.dispositivo_id == dispositivo_id)
                .first()
            )
            if dispositivo is None or not dispositivo.activo:
                raise ErrorPeticion("Equipo no autorizado", 401)
            if not SecurityValidator.verify_password(token, dispositivo.token_hash):
                self._bitacora(sesion, dispositivo_id, "auth_fallida", "token incorrecto", False)
                sesion.commit()
                raise ErrorPeticion("Token incorrecto", 401)
            dispositivo.ultima_conexion = ahora_utc()
            sesion.commit()
            return dispositivo
        except SQLAlchemyError:
            sesion.rollback()
            raise ErrorPeticion("Error interno al autenticar", 500) from None
        finally:
            sesion.close()

    def limitar_tasa(self, dispositivo_id: str) -> None:
        """Frena a un dispositivo que abuse del servicio (límite por minuto)"""
        if self.config.peticiones_por_minuto <= 0:
            return
        ahora = ahora_utc()
        with self._candado:
            marcas = [m for m in self._peticiones.get(dispositivo_id, []) if ahora - m < timedelta(minutes=1)]
            if len(marcas) >= self.config.peticiones_por_minuto:
                raise ErrorPeticion("Demasiadas peticiones; intente más tarde", 429)
            marcas.append(ahora)
            self._peticiones[dispositivo_id] = marcas

    # ------------------------------------------------------------------
    # Operaciones del protocolo
    # ------------------------------------------------------------------
    def ping(self) -> dict:
        """Estado básico del servicio (incluye la hora para medir desfases)"""
        return {
            "servidor": "nodo-central-sincronizacion",
            "version_protocolo": VERSION_PROTOCOLO,
            "hora": ahora_utc().isoformat(),
            "tablas": registro.tablas_sincronizadas(),
        }

    def push(self, dispositivo: DispositivoSync, cuerpo: dict) -> dict:
        """
        Aplica un lote de operaciones y las registra en el log del servidor

        La respuesta incluye en ``aplicadas`` **todo** identificador que el
        servidor tiene por aplicado (nuevo o ya conocido): eso hace que el
        reenvío de un lote sea seguro e idempotente para el cliente.
        """
        operaciones = cuerpo.get("ops") or []
        if not isinstance(operaciones, list):
            raise ErrorPeticion("El lote de operaciones no es una lista")
        if len(operaciones) > self.config.max_ops_por_lote:
            raise ErrorPeticion(
                f"El lote supera el máximo de {self.config.max_ops_por_lote} operaciones", 413
            )

        aplicadas: list[str] = []
        rechazadas: list[dict] = []
        conflictos: list[dict] = []
        sesion = self._sesion()
        try:
            aplicador = AplicadorRemoto(
                sesion,
                dispositivo_local=dispositivo.dispositivo_id,
                max_bytes_binario=self.config.max_bytes_blob,
            )
            for operacion in operaciones:
                if not isinstance(operacion, dict):
                    continue
                op_id = str(operacion.get("op_id") or "")
                if not op_id:
                    continue
                resultado = aplicador.aplicar(operacion)
                if resultado.diferida:
                    # En el servidor no hay padres "por llegar": la operación
                    # se rechaza con motivo para que el puesto la corrija.
                    rechazadas.append({"op_id": op_id, "motivo": resultado.motivo})
                    continue
                if not resultado.aplicada and resultado.motivo not in (
                    "duplicada",
                    "superada_por_una_escritura_mas_reciente",
                    "fila_borrada_en_el_nodo_central",
                ):
                    rechazadas.append({"op_id": op_id, "motivo": resultado.motivo})
                    continue

                if resultado.aplicada:
                    sesion.add(
                        OpServidor(
                            op_id=op_id,
                            tabla=resultado.tabla,
                            fila_uuid=resultado.fila_uuid,
                            operacion=str(operacion.get("operacion") or "upsert"),
                            payload=operacion.get("payload") or "{}",
                            base_op_id=operacion.get("base_op_id"),
                            dispositivo=dispositivo.dispositivo_id,
                            usuario=operacion.get("usuario"),
                            creado_en=momento_de_operacion(operacion),
                        )
                    )
                aplicadas.append(op_id)
                conflictos.extend(self._conflictos_json(resultado.conflictos))
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
            logger.error("No se pudo aplicar el lote recibido", exc_info=True)
            raise ErrorPeticion("Error interno al aplicar el lote", 500) from None
        finally:
            sesion.close()

        return {
            "aplicadas": aplicadas,
            "rechazadas": rechazadas,
            "conflictos": conflictos,
            "cursor": self.cursor_actual(),
        }

    def pull(self, dispositivo: DispositivoSync, cursor: int, limite: int) -> dict:
        """Devuelve las operaciones posteriores al cursor, sin las propias"""
        limite = max(1, min(int(limite or 200), self.config.max_ops_por_lote))
        sesion = self._sesion()
        try:
            filas = (
                sesion.query(OpServidor)
                .filter(
                    OpServidor.seq > int(cursor or 0),
                    OpServidor.dispositivo != dispositivo.dispositivo_id,
                )
                .order_by(OpServidor.seq)
                .limit(limite)
                .all()
            )
            operaciones = [
                {
                    "seq": fila.seq,
                    "op_id": fila.op_id,
                    "tabla": fila.tabla,
                    "fila_uuid": fila.fila_uuid,
                    "operacion": fila.operacion,
                    "payload": fila.payload,
                    "base_op_id": fila.base_op_id,
                    "dispositivo": fila.dispositivo,
                    "usuario": fila.usuario,
                    "creado_en": fila.creado_en.isoformat(),
                }
                for fila in filas
            ]
            maximo = int(sesion.query(func.max(OpServidor.seq)).scalar() or 0)
            ultimo = filas[-1].seq if filas else int(cursor or 0)
            return {
                "ops": operaciones,
                "cursor": ultimo,
                "hay_mas": bool(operaciones) and ultimo < maximo,
                "maximo": maximo,
            }
        except SQLAlchemyError:
            logger.error("No se pudo leer el log de operaciones", exc_info=True)
            raise ErrorPeticion("Error interno al leer novedades", 500) from None
        finally:
            sesion.close()

    def cursor_actual(self) -> int:
        """Último ``seq`` asignado por el nodo central"""
        sesion = self._sesion()
        try:
            return int(sesion.query(func.max(OpServidor.seq)).scalar() or 0)
        finally:
            sesion.close()

    # ------------------------------------------------------------------
    # Binarios
    # ------------------------------------------------------------------
    def guardar_blob(self, dispositivo: DispositivoSync, hash_archivo: str, contenido: bytes) -> dict:
        """Almacena un archivo verificado por su hash (queda deduplicado)"""
        if len(contenido) > self.config.max_bytes_blob:
            raise ErrorPeticion("El archivo supera el tamaño máximo admitido", 413)
        if hash_bytes(contenido) != hash_archivo:
            raise ErrorPeticion("El contenido no coincide con su hash", 422)

        destino = self._ruta_blob(hash_archivo)
        if not destino.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            temporal = destino.with_suffix(".parcial")
            temporal.write_bytes(contenido)
            temporal.replace(destino)
        return {"hash": hash_archivo, "tamano": len(contenido)}

    def leer_blob(self, hash_archivo: str) -> bytes | None:
        """Devuelve el contenido almacenado de un archivo, si existe"""
        ruta = self._ruta_blob(hash_archivo)
        if not ruta.exists():
            return None
        return ruta.read_bytes()

    def _ruta_blob(self, hash_archivo: str) -> Path:
        """Ruta del archivo dentro del almacén (subcarpeta por prefijo del hash)"""
        limpio = "".join(c for c in hash_archivo if c.isalnum())
        if len(limpio) != 64:
            raise ErrorPeticion("Identificador de archivo no válido")
        return self.config.dir_blobs / limpio[:2] / limpio

    # ------------------------------------------------------------------
    # Administración
    # ------------------------------------------------------------------
    def crear_dispositivo(self, nombre: str) -> tuple[str, str]:
        """
        Da de alta un puesto y devuelve su identificador y su token en claro

        El token no se puede recuperar después: en la base solo queda su hash.
        """
        from src.utils.security import SecurityValidator

        from sync_agent.comun import nuevo_uuid

        dispositivo_id = nuevo_uuid()
        token = secrets.token_urlsafe(32)
        sesion = self._sesion()
        try:
            sesion.add(
                DispositivoSync(
                    dispositivo_id=dispositivo_id,
                    nombre=nombre.strip() or "Puesto sin nombre",
                    token_hash=SecurityValidator.hash_password(token),
                    activo=1,
                )
            )
            self._bitacora(sesion, dispositivo_id, "dispositivo_creado", nombre, True)
            sesion.commit()
        finally:
            sesion.close()
        return dispositivo_id, token

    def listar_dispositivos(self) -> list[dict]:
        """Puestos registrados en el nodo central"""
        sesion = self._sesion()
        try:
            return [
                {
                    "dispositivo_id": fila.dispositivo_id,
                    "nombre": fila.nombre,
                    "activo": bool(fila.activo),
                    "creado_en": fila.creado_en.isoformat() if fila.creado_en else None,
                    "ultima_conexion": fila.ultima_conexion.isoformat()
                    if fila.ultima_conexion
                    else None,
                }
                for fila in sesion.query(DispositivoSync).order_by(DispositivoSync.nombre).all()
            ]
        finally:
            sesion.close()

    def revocar_dispositivo(self, dispositivo_id: str) -> bool:
        """Retira el permiso de un equipo perdido o dado de baja"""
        sesion = self._sesion()
        try:
            fila = (
                sesion.query(DispositivoSync)
                .filter(DispositivoSync.dispositivo_id == dispositivo_id)
                .first()
            )
            if fila is None:
                return False
            fila.activo = 0
            self._bitacora(sesion, dispositivo_id, "dispositivo_revocado", fila.nombre, True)
            sesion.commit()
            return True
        finally:
            sesion.close()

    def conflictos(self, solo_pendientes: bool = True, limite: int = 200) -> list[dict]:
        """Conflictos registrados en el nodo central"""
        sesion = self._sesion()
        try:
            consulta = sesion.query(ConflictoSync)
            if solo_pendientes:
                consulta = consulta.filter(ConflictoSync.resuelto == 0)
            filas = consulta.order_by(ConflictoSync.detectado_en.desc()).limit(limite).all()
            return [
                {
                    "tabla": fila.tabla,
                    "fila_uuid": fila.fila_uuid,
                    "campo": fila.campo,
                    "valor_local": loads(fila.valor_local),
                    "valor_remoto": loads(fila.valor_remoto),
                    "ganador": fila.ganador,
                    "regla": fila.regla,
                    "detectado_en": fila.detectado_en.isoformat() if fila.detectado_en else None,
                }
                for fila in filas
            ]
        finally:
            sesion.close()

    def purgar_historial(self, dias: int = DIAS_RETENCION_OPS) -> int:
        """Retira del log las operaciones antiguas que ya nadie necesita"""
        sesion = self._sesion()
        try:
            limite = ahora_utc() - timedelta(days=max(1, dias))
            borradas = (
                sesion.query(OpServidor).filter(OpServidor.recibido_en < limite).delete(
                    synchronize_session=False
                )
            )
            sesion.commit()
            logger.info("Historial del nodo central purgado: %s operaciones", borradas)
            return int(borradas or 0)
        finally:
            sesion.close()

    def estado(self) -> dict:
        """Resumen del nodo central para diagnóstico"""
        sesion = self._sesion()
        try:
            return {
                "operaciones": int(sesion.query(OpServidor).count()),
                "dispositivos": int(sesion.query(DispositivoSync).count()),
                "activos": int(
                    sesion.query(DispositivoSync).filter(DispositivoSync.activo == 1).count()
                ),
                "conflictos_pendientes": int(
                    sesion.query(ConflictoSync).filter(ConflictoSync.resuelto == 0).count()
                ),
                "archivos": len(list(self.config.dir_blobs.rglob("*")))
                if self.config.dir_blobs.exists()
                else 0,
            }
        finally:
            sesion.close()

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    @staticmethod
    def _conflictos_json(conflictos) -> list[dict]:
        """Convierte los conflictos del motor a la forma del protocolo"""
        return [
            {
                "tabla": c.tabla,
                "fila_uuid": c.fila_uuid,
                "campo": c.campo,
                "valor_local": c.valor_local,
                "valor_remoto": c.valor_remoto,
                "ganador": c.ganador,
                "regla": c.regla,
                "op_local_id": c.op_local_id,
                "op_remoto_id": c.op_remoto_id,
            }
            for c in conflictos
        ]

    @staticmethod
    def _bitacora(sesion, dispositivo: str | None, evento: str, detalle: str, correcto: bool) -> None:
        """Añade una entrada a la bitácora del nodo central"""
        sesion.add(
            BitacoraSync(
                dispositivo=dispositivo,
                evento=evento,
                detalle=detalle[:2000] if detalle else None,
                correcto=correcto,
            )
        )


# ----------------------------------------------------------------------
# Capa HTTP
# ----------------------------------------------------------------------
RUTA_PING = "/api/v1/ping"
RUTA_PUSH = "/api/v1/push"
RUTA_PULL = "/api/v1/pull"
RUTA_BLOB = "/api/v1/blob"


class ManejadorSync(BaseHTTPRequestHandler):
    """Traduce cada petición HTTP en una llamada al núcleo central"""

    server_version = "SDEP-SyncAgent/1.0"
    protocol_version = "HTTP/1.1"

    @property
    def nucleo(self) -> NucleoCentral:
        """Núcleo compartido por todos los hilos del servicio"""
        return cast(NucleoCentral, getattr(self.server, "nucleo"))

    def log_message(self, formato: str, *argumentos: Any) -> None:
        """Envía el registro del servidor a nuestro logger, no a stderr"""
        logger.debug("HTTP %s - %s", self.address_string(), formato % argumentos)

    def do_GET(self) -> None:  # noqa: N802 - nombre exigido por la biblioteca
        self._atender("GET")

    def do_POST(self) -> None:  # noqa: N802 - nombre exigido por la biblioteca
        self._atender("POST")

    # ------------------------------------------------------------------
    # Enrutado
    # ------------------------------------------------------------------
    def _atender(self, metodo: str) -> None:
        """Enruta la petición y traduce los errores a códigos HTTP"""
        ruta = urlparse(self.path)
        try:
            # El cuerpo se lee siempre, incluso si la petición va a ser
            # rechazada: si no se consumiera, la conexión persistente quedaría
            # desincronizada.
            self._cuerpo = self._leer_cuerpo() if metodo == "POST" else b""

            if ruta.path == RUTA_PING:
                self._responder_json(200, self.nucleo.ping())
                return

            dispositivo = self._autenticar()
            self.nucleo.limitar_tasa(dispositivo.dispositivo_id)

            if ruta.path == RUTA_PULL and metodo == "GET":
                parametros = parse_qs(ruta.query)
                cursor = int((parametros.get("cursor") or ["0"])[0] or 0)
                limite = int((parametros.get("limite") or ["200"])[0] or 200)
                self._responder_json(200, self.nucleo.pull(dispositivo, cursor, limite))
                return

            if ruta.path == RUTA_PUSH and metodo == "POST":
                self._responder_json(200, self.nucleo.push(dispositivo, self._leer_json()))
                return

            if ruta.path.startswith(RUTA_BLOB + "/"):
                self._atender_blob(metodo, dispositivo, ruta.path[len(RUTA_BLOB) + 1 :])
                return

            self._responder_json(404, {"error": "recurso no encontrado"})
        except ErrorPeticion as error:
            self._responder_json(error.codigo, {"error": str(error)})
        except (ValueError, TypeError) as error:
            self._responder_json(400, {"error": f"parámetros inválidos: {error}"})
        except Exception:
            logger.error("Fallo atendiendo %s %s", metodo, ruta.path, exc_info=True)
            self._responder_json(500, {"error": "error interno del nodo central"})

    def _atender_blob(self, metodo: str, dispositivo: DispositivoSync, hash_archivo: str) -> None:
        """Sube o entrega un archivo del almacén central"""
        if metodo == "POST":
            self._responder_json(
                200, self.nucleo.guardar_blob(dispositivo, hash_archivo, self._cuerpo)
            )
            return
        contenido = self.nucleo.leer_blob(hash_archivo)
        if contenido is None:
            self._responder_json(404, {"error": "archivo no disponible"})
            return
        self._responder_binario(200, contenido)

    def _autenticar(self) -> DispositivoSync:
        """Valida las credenciales del equipo que llama"""
        cabecera = self.headers.get("Authorization", "")
        token = cabecera[7:].strip() if cabecera.lower().startswith("bearer ") else ""
        return self.nucleo.autenticar(self.headers.get("X-Dispositivo"), token)

    # ------------------------------------------------------------------
    # Cuerpo y respuestas
    # ------------------------------------------------------------------
    def _leer_cuerpo(self) -> bytes:
        """Lee el cuerpo completo con un límite previo de tamaño"""
        try:
            longitud = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            raise ErrorPeticion("Cabecera Content-Length inválida") from None
        if longitud <= 0:
            return b""
        limite = max(
            self.nucleo.config.max_bytes_peticion, self.nucleo.config.max_bytes_blob
        )
        if longitud > limite:
            raise ErrorPeticion(f"El cuerpo supera el límite de {limite} bytes", 413)
        return self.rfile.read(longitud)

    def _leer_json(self) -> dict:
        """Interpreta el cuerpo como JSON del protocolo"""
        if not self._cuerpo:
            return {}
        if len(self._cuerpo) > self.nucleo.config.max_bytes_peticion:
            raise ErrorPeticion("El lote supera el tamaño máximo admitido", 413)
        try:
            datos = json.loads(self._cuerpo.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as error:
            raise ErrorPeticion(f"JSON inválido: {error}") from error
        if not isinstance(datos, dict):
            raise ErrorPeticion("Se esperaba un objeto JSON")
        return datos

    def _responder_json(self, codigo: int, datos: dict) -> None:
        """Responde en JSON con longitud explícita"""
        cuerpo = dumps(datos).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _responder_binario(self, codigo: int, contenido: bytes) -> None:
        """Responde con el contenido binario de un archivo"""
        self.send_response(codigo)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)


class ServidorSync(ThreadingHTTPServer):
    """Servicio HTTP multihilo del nodo central"""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, config: ServidorConfig, nucleo: NucleoCentral | None = None):
        self.nucleo = nucleo or NucleoCentral(config)
        super().__init__((config.host, config.puerto), ManejadorSync)
        self.config_servidor = config
        if config.certificado and config.clave:
            self._envolver_tls(config.certificado, config.clave)

    def _envolver_tls(self, certificado: str, clave: str) -> None:
        """Protege el canal con TLS cuando se entrega un certificado"""
        import ssl

        contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        contexto.load_cert_chain(certfile=certificado, keyfile=clave)
        self.socket = contexto.wrap_socket(self.socket, server_side=True)
        logger.info("Servicio protegido con TLS")
    def detener(self) -> None:
        """Pide el cierre del bucle de servicio sin bloquear a quien llama"""
        threading.Thread(target=self.shutdown, daemon=True).start()

    def cerrar(self) -> None:
        """Cierra el socket y libera el motor de base de datos"""
        try:
            self.server_close()
        finally:
            self.nucleo.cerrar()


def ejecutar_servidor(config: ServidorConfig) -> int:
    """
    Arranca el nodo central y atiende hasta que se interrumpa

    Args:
        config: Parámetros del servicio

    Returns:
        Código de salida del proceso
    """
    import signal

    servidor = ServidorSync(config)
    logger.info(
        "Nodo central escuchando en http%s://%s:%s (base: %s)",
        "s" if config.certificado else "",
        config.host,
        config.puerto,
        config.url_db,
    )

    def _parar(_senal, _marco):
        logger.info("Deteniendo el nodo central…")
        servidor.detener()

    for senal in (signal.SIGINT, getattr(signal, "SIGTERM", None)):
        if senal is None:
            continue
        try:
            signal.signal(senal, _parar)
        except (ValueError, OSError):  # pragma: no cover - sin señales disponibles
            logger.debug("No se pudo instalar el manejador de %s", senal)

    try:
        servidor.serve_forever(poll_interval=0.5)
    finally:
        servidor.cerrar()
    return 0
