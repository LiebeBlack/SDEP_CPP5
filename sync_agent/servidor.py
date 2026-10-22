"""
Nodo central de sincronización

Es un servicio HTTP pequeño (biblioteca estándar) que se ejecuta en un equipo de
la intranet y guarda el estado autoritativo. Desde el protocolo de ciclos, cada
lote que llega se valida y queda en un **staging**: el servidor lo ordena por la
marca de tiempo corregida de cada evento, reconstruye la historia de las filas
afectadas y publica el resultado como un ``epoch`` indivisible (ver
``consolidacion.py``). Nada se aplica al estado operativo hasta que el ciclo
completo está validado; si falla, se revierte entero y los eventos se conservan
para el siguiente intento.

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
import sys
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

from sync_agent import consolidacion, registro
from sync_agent.api_acciones import ApiAcciones, ErrorApi
from sync_agent.aplicador import AplicadorRemoto, FilaPendiente, momento_de_operacion
from sync_agent.comun import ahora_utc, dumps, hash_bytes, loads, nuevo_uuid
from sync_agent.descubrimiento import PUERTO_DESCUBRIMIENTO, DifusorDescubrimiento
from sync_agent.esquema import (
    EVENTO_CONSOLIDADO,
    EVENTO_EN_STAGING,
    LOTE_CONSOLIDADO,
    LOTE_RECHAZADO,
    LOTE_RECIBIDO,
    AckEpoch,
    BaseSync,
    BitacoraSync,
    ConflictoSync,
    DispositivoSync,
    EpochFila,
    EpochSync,
    EventoSync,
    LoteEntrada,
    OpServidor,
    RelojPuesto,
)
from sync_agent.sesiones import ErrorSesion, SesionValida

logger = logging.getLogger(__name__)

VERSION_PROTOCOLO = "2"
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
    # Puerto UDP donde el nodo se anuncia al teléfono. 0 lo desactiva (pruebas
    # con puerto HTTP efímero o instalaciones donde la difusión no se permite).
    puerto_descubrimiento: int = PUERTO_DESCUBRIMIENTO
    nombre_equipo: str = ""
    # Une automáticamente cualquier teléfono de la red al nodo central, sin
    # código previo (decisión del propietario del sistema). Se puede apagar
    # desde la configuración del escritorio si en el futuro se quiere exigir
    # un emparejamiento supervisado; mientras tanto, la única protecciones son
    # el límite de peticiones y el hecho de que el login de usuario sigue
    # exigiendo una cuenta válida de la base institucional.
    emparejamiento_abierto: bool = True
    # Cuando está activo, los lotes pasan por el staging y se publican como
    # ciclos (reconstrucción histórica). Desactivarlo recupera el motor
    # anterior, que aplicaba cada operación al recibirla: solo para volver
    # atrás en una instalación concreta, nunca para operar a diario.
    consolidacion_activa: bool = True


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
        # Capa del protocolo 2: autenticación de usuario, acciones de negocio
        # y generación de documentos. Comparte el motor y el almacén de blobs.
        self.api = ApiAcciones(self)
        # Un solo consolidador a la vez: ordenar, reconstruir y publicar el
        # ciclo tiene que ser una secuencia única aunque lleguen varios lotes
        # al mismo tiempo.
        self._consolidacion = threading.Lock()
        # El ``ping`` es la única ruta sin autenticar y la llama cada teléfono
        # de la red: publica el ciclo desde memoria en lugar de consultar la
        # base en cada latido.
        self._epoch_cache = 0
        self.importar_legado()
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
            marcas = [
                m
                for m in self._peticiones.get(dispositivo_id, [])
                if ahora - m < timedelta(minutes=1)
            ]
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
            "epoch_actual": self._epoch_cache,
            "ciclos": True,
            "tablas": registro.tablas_sincronizadas(),
            # Capacidades del protocolo 2: el móvil decide qué pantallas
            # ofrecer según lo que el nodo central anuncia.
            "acciones": [
                "auth",
                "consultas",
                "admin",
                "nomina",
                "incidencias",
                "contratos",
                "academicos",
                "archivos",
            ],
        }

    def push(self, dispositivo: DispositivoSync, cuerpo: dict) -> dict:
        """
        Recibe un lote y lo consolida como un ciclo indivisible

        El lote no se aplica al estado operativo: se valida, se guarda en el
        staging (``sync_eventos``) y solo después se reconstruye la historia de
        las filas afectadas y se publica un ``epoch``. Si la consolidación no
        puede cerrarse, no se aplica nada y los eventos quedan en el log para
        el siguiente intento.
        """
        if not self.config.consolidacion_activa:
            return self.aplicar_lote_heredado(dispositivo, cuerpo)

        operaciones = cuerpo.get("ops") or []
        if not isinstance(operaciones, list):
            raise ErrorPeticion("El lote de operaciones no es una lista")
        if len(operaciones) > self.config.max_ops_por_lote:
            raise ErrorPeticion(
                f"El lote supera el máximo de {self.config.max_ops_por_lote} operaciones", 413
            )

        lote_id = str(cuerpo.get("lote_id") or "").strip() or nuevo_uuid()
        desfase_ms = consolidacion.acotar_desfase(cuerpo.get("desfase_ms"))
        sesion = self._sesion()
        try:
            existente = sesion.get(LoteEntrada, lote_id)
            if existente is not None:
                # Reenvío del mismo paquete: se responde lo que ya se decidió.
                return self._resumen_lote(sesion, existente)
            eventos, rechazadas, duplicadas = self._preparar_eventos(
                sesion, dispositivo, operaciones, lote_id, desfase_ms
            )
            self._registrar_reloj(sesion, dispositivo.dispositivo_id, desfase_ms)
            if eventos:
                sesion.add(
                    LoteEntrada(
                        lote_id=lote_id,
                        dispositivo=dispositivo.dispositivo_id,
                        n_ops=len(eventos),
                        hash=consolidacion.hash_lote(eventos),
                        desfase_ms=desfase_ms,
                        estado=LOTE_RECIBIDO,
                    )
                )
                for evento in eventos:
                    sesion.add(EventoSync(**evento))
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
            logger.error("No se pudo guardar el lote en el staging", exc_info=True)
            raise ErrorPeticion("Error interno al recibir el lote", 500) from None
        finally:
            sesion.close()

        if not eventos:
            # Todo el lote era un reenvío: se consolida lo que haya pendiente y
            # se confirman las operaciones que ya estaban en el log.
            resultado = self.consolidar()
            al_dia = resultado.get("estado") in (
                LOTE_CONSOLIDADO,
                consolidacion.ESTADO_SIN_NOVEDADES,
            )
            return {
                "lote_id": lote_id,
                "estado": resultado.get("estado"),
                "epoch": resultado.get("epoch") or self.epoch_actual(),
                "aplicadas": list(duplicadas) if al_dia else [],
                "rechazadas": rechazadas + list(resultado.get("rechazadas") or []),
                "conflictos": [],
                "cursor": self.cursor_actual(),
            }

        # Se consolidan todos los eventos pendientes, no solo los de este lote:
        # si un ciclo anterior no pudo cerrarse, sus eventos se reintentan aquí
        # en lugar de quedarse esperando un reenvío que ya no va a llegar.
        resultado = self.consolidar()
        resultado["lote_id"] = lote_id
        resultado["rechazadas"] = rechazadas + list(resultado.get("rechazadas") or [])
        if resultado.get("estado") == LOTE_CONSOLIDADO:
            # Las operaciones que ya estaban en el log (reenvío) también se
            # confirman: si no, el puesto las reintentaría para siempre.
            resultado["aplicadas"] = list(resultado.get("aplicadas") or []) + list(duplicadas)
        else:
            # No se aplicó nada: no se confirman los identificadores para que
            # el puesto conserve sus operaciones y las reintente.
            resultado["aplicadas"] = []
        return resultado

    def _preparar_eventos(
        self,
        sesion,
        dispositivo: DispositivoSync,
        operaciones: list,
        lote_id: str,
        desfase_ms: int,
    ) -> tuple[list[dict], list[dict], list[str]]:
        """
        Convierte el lote del protocolo en eventos del log, sin aplicarlos

        Cada operación se valida y se normaliza aquí: sello crudo, sello
        corregido por el desfase medido y lote al que pertenece. Las inválidas
        se devuelven aparte y no entran al staging; las que ya estaban en el log
        (reenvío del mismo puesto) se devuelven como duplicadas para poder
        confirmarlas sin volver a escribirlas.
        """
        eventos: list[dict] = []
        rechazadas: list[dict] = []
        duplicadas: list[str] = []
        identificadores = [
            str(operacion.get("op_id") or "")
            for operacion in operaciones
            if isinstance(operacion, dict)
        ]
        vistos = (
            {
                op_id
                for (op_id,) in sesion.query(EventoSync.op_id)
                .filter(EventoSync.op_id.in_(identificadores))
                .all()
            }
            if identificadores
            else set()
        )
        roles_cache: dict[str, str | None] = {}
        recibido = ahora_utc()
        for operacion in operaciones:
            if not isinstance(operacion, dict):
                continue
            op_id = str(operacion.get("op_id") or "")
            if not op_id:
                continue
            if op_id in vistos:
                # Reenvío de una operación ya recibida: es idempotente.
                duplicadas.append(op_id)
                continue
            tabla = str(operacion.get("tabla") or "")
            if not registro.es_sincronizable(tabla):
                rechazadas.append({"op_id": op_id, "motivo": "tabla_no_sincronizable"})
                continue
            fila_uuid = str(operacion.get("fila_uuid") or "")
            if not fila_uuid:
                rechazadas.append({"op_id": op_id, "motivo": "sin_identidad_global"})
                continue
            momento = consolidacion.momento_de_texto(operacion.get("creado_en"))
            if momento is None:
                rechazadas.append({"op_id": op_id, "motivo": "sello_de_tiempo_invalido"})
                continue
            payload = operacion.get("payload")
            if isinstance(payload, dict):
                payload = dumps(payload)
            if not isinstance(payload, str) or not payload:
                payload = "{}"
            if len(payload.encode("utf-8")) > self.config.max_bytes_peticion:
                rechazadas.append({"op_id": op_id, "motivo": "payload_demasiado_grande"})
                continue
            motivo_permiso = self._autorizar_escritura(sesion, operacion, roles_cache)
            if motivo_permiso:
                rechazadas.append({"op_id": op_id, "motivo": motivo_permiso})
                logger.info("Operación %s rechazada por permisos (%s)", op_id[:8], motivo_permiso)
                continue
            eventos.append(
                {
                    "op_id": op_id,
                    "lote_id": lote_id,
                    "tabla": tabla,
                    "fila_uuid": fila_uuid,
                    "operacion": str(operacion.get("operacion") or "upsert"),
                    "payload": payload,
                    "base_op_id": operacion.get("base_op_id"),
                    "dispositivo": dispositivo.dispositivo_id,
                    "usuario": operacion.get("usuario"),
                    "ocurrido_en": momento,
                    "ocurrido_corregido": consolidacion.corregir_momento(momento, desfase_ms),
                    "desfase_ms": desfase_ms,
                    "recibido_en": recibido,
                    "estado": EVENTO_EN_STAGING,
                }
            )
        return eventos, rechazadas, duplicadas

    def consolidar(self, lotes: list[str] | None = None) -> dict:
        """
        Reproduce el staging y publica un ciclo indivisible

        Se ordenan todos los eventos pendientes por su marca corregida, se
        reconstruye la historia completa de cada fila afectada y el resultado se
        escribe en una sola transacción. Si algo falla, se revierte todo: los
        eventos permanecen en el staging y el lote queda marcado con el motivo.
        """
        with self._consolidacion:
            return self._consolidar(lotes)

    def _consolidar(self, lotes: list[str] | None) -> dict:
        sesion = self._sesion()
        lotes_afectados: list[str] = []
        try:
            consulta = sesion.query(EventoSync).filter(EventoSync.estado == EVENTO_EN_STAGING)
            if lotes:
                consulta = consulta.filter(EventoSync.lote_id.in_(lotes))
            pendientes = consulta.all()
            if not pendientes:
                return {
                    "estado": consolidacion.ESTADO_SIN_NOVEDADES,
                    "epoch": self._epoch_actual(sesion),
                    "aplicadas": [],
                    "rechazadas": [],
                    "conflictos": [],
                    "cursor": self.cursor_actual(),
                }

            pendientes.sort(
                key=lambda fila: (
                    fila.ocurrido_corregido or fila.ocurrido_en,
                    fila.dispositivo or "",
                    fila.op_id,
                )
            )
            lotes_afectados = sorted({fila.lote_id for fila in pendientes})
            filas: list[dict] = []
            conflictos: list[dict] = []
            ids_pendientes = {fila.op_id for fila in pendientes}
            afectadas = sorted({(fila.tabla, fila.fila_uuid) for fila in pendientes})
            for tabla, fila_uuid in afectadas:
                historial = [
                    self._evento_wire(fila) for fila in self._historial(sesion, tabla, fila_uuid)
                ]
                publicada = consolidacion.fila_publicada(tabla, fila_uuid, historial)
                if publicada is not None:
                    filas.append(publicada)
                conflictos.extend(
                    consolidacion.conflictos_del_ciclo(tabla, fila_uuid, historial, ids_pendientes)
                )

            aplicador = AplicadorRemoto(
                sesion,
                dispositivo_local="nodo-central",
                max_bytes_binario=self.config.max_bytes_blob,
            )
            # Un hijo puede preceder a su padre en el reloj: el primer pase
            # difiere las filas huérfanas y el segundo, ya con los padres
            # escritos, las aplica. Si aún falta algo, no se consolida nada.
            pendientes_filas = aplicador.aplicar_ciclo(filas, diferir=True)
            if pendientes_filas:
                aplicador.aplicar_ciclo(pendientes_filas, diferir=False)

            epoch = self._epoch_actual(sesion) + 1
            # La secuencia se asigna antes de calcular el manifiesto: es parte
            # de lo que el cliente recalcula, y tiene que coincidir exacto.
            for secuencia, fila in enumerate(pendientes, start=1):
                fila.epoch = epoch
                fila.secuencia_global = secuencia
            eventos = [self._evento_wire(fila) for fila in pendientes]
            manifiesto = consolidacion.manifiesto_epoch(eventos, filas)
            for fila in pendientes:
                fila.estado = EVENTO_CONSOLIDADO
                fila.motivo = None
                sesion.add(
                    OpServidor(
                        op_id=fila.op_id,
                        tabla=fila.tabla,
                        fila_uuid=fila.fila_uuid,
                        operacion=fila.operacion,
                        payload=fila.payload,
                        base_op_id=fila.base_op_id,
                        dispositivo=fila.dispositivo,
                        usuario=fila.usuario,
                        creado_en=fila.ocurrido_corregido,
                        recibido_en=fila.recibido_en,
                    )
                )
            for lote_id in sorted({fila.lote_id for fila in pendientes}):
                lote = sesion.get(LoteEntrada, lote_id)
                if lote is not None:
                    lote.estado = LOTE_CONSOLIDADO
                    lote.epoch = epoch
                    lote.consolidado_en = ahora_utc()
                    lote.motivo = None
            sesion.add(
                EpochSync(
                    epoch=epoch,
                    manifiesto=manifiesto,
                    n_eventos=len(eventos),
                    n_filas=len(filas),
                )
            )
            for publicada in filas:
                sesion.add(
                    EpochFila(
                        epoch=epoch,
                        tabla=publicada["tabla"],
                        fila_uuid=publicada["fila_uuid"],
                        valores=dumps(publicada.get("valores") or {}),
                        borrado=1 if publicada.get("borrado") else 0,
                    )
                )
            for conflicto in conflictos:
                sesion.add(
                    ConflictoSync(
                        tabla=conflicto["tabla"],
                        fila_uuid=conflicto["fila_uuid"],
                        campo=conflicto["campo"],
                        valor_local=dumps(conflicto["valor_local"]),
                        valor_remoto=dumps(conflicto["valor_remoto"]),
                        ganador=conflicto["ganador"],
                        regla=conflicto["regla"],
                        op_local_id=conflicto["op_local_id"],
                        op_remoto_id=conflicto["op_remoto_id"],
                        resuelto=0,
                    )
                )
            sesion.commit()
            self._epoch_cache = epoch
            logger.info(
                "Ciclo %s consolidado: %s eventos, %s filas", epoch, len(eventos), len(filas)
            )
            return {
                "estado": LOTE_CONSOLIDADO,
                "epoch": epoch,
                "aplicadas": [fila.op_id for fila in pendientes],
                "rechazadas": [],
                "conflictos": conflictos,
                "cursor": self.cursor_actual(),
            }
        except (SQLAlchemyError, FilaPendiente) as error:
            sesion.rollback()
            logger.error("El ciclo no se pudo consolidar: %s", error, exc_info=True)
            self._rechazar_lotes(lotes_afectados or lotes, str(error))
            return {
                "estado": LOTE_RECHAZADO,
                "epoch": None,
                "aplicadas": [],
                "rechazadas": [{"op_id": "", "motivo": f"ciclo_no_consolidado: {error}"}],
                "conflictos": [],
                "cursor": self.cursor_actual(),
                "error": str(error),
            }
        finally:
            sesion.close()

    def _rechazar_lotes(self, lotes: list[str] | None, motivo: str) -> None:
        """Deja constancia del ciclo que no pudo cerrarse (los eventos se conservan)"""
        if not lotes:
            return
        sesion = self._sesion()
        try:
            for lote in sesion.query(LoteEntrada).filter(LoteEntrada.lote_id.in_(lotes)).all():
                lote.estado = LOTE_RECHAZADO
                lote.motivo = motivo[:2000]
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
            logger.warning("No se pudo marcar el lote rechazado", exc_info=True)
        finally:
            sesion.close()

    @staticmethod
    def _historial(sesion, tabla: str, fila_uuid: str) -> list[EventoSync]:
        """Historia completa de una fila, en orden cronológico"""
        filas = (
            sesion.query(EventoSync)
            .filter(EventoSync.tabla == tabla, EventoSync.fila_uuid == fila_uuid)
            .all()
        )
        filas.sort(
            key=lambda fila: (
                fila.ocurrido_corregido or fila.ocurrido_en,
                fila.dispositivo or "",
                fila.op_id,
            )
        )
        return cast(list[EventoSync], filas)

    @staticmethod
    def _evento_wire(fila: EventoSync) -> dict:
        """Forma de un evento en el protocolo y en el manifiesto"""
        return {
            "op_id": fila.op_id,
            "tabla": fila.tabla,
            "fila_uuid": fila.fila_uuid,
            "operacion": fila.operacion,
            "payload": fila.payload,
            "base_op_id": fila.base_op_id,
            "dispositivo": fila.dispositivo,
            "usuario": fila.usuario,
            "ocurrido_en": fila.ocurrido_en.isoformat(),
            "ocurrido_corregido": fila.ocurrido_corregido.isoformat(),
            "secuencia_global": int(fila.secuencia_global or 0),
        }

    @staticmethod
    def _epoch_actual(sesion) -> int:
        """Último ciclo publicado (0 si todavía no hay ninguno)"""
        return int(sesion.query(func.max(EpochSync.epoch)).scalar() or 0)

    def epoch_actual(self) -> int:
        """Último ciclo publicado, con sesión propia"""
        sesion = self._sesion()
        try:
            return self._epoch_actual(sesion)
        finally:
            sesion.close()

    def pull_epochs(self, dispositivo: DispositivoSync, desde: int, limite: int) -> dict:
        """
        Entrega los ciclos publicados posteriores a ``desde``

        Cada paquete es indivisible: el cliente lo aplica entero o no aplica
        nada, y el manifiesto le permite comprobar que llegó completo.
        """
        desde = max(0, int(desde or 0))
        limite = max(1, min(int(limite or 1), 20))
        sesion = self._sesion()
        try:
            actual = self._epoch_actual(sesion)
            filas = (
                sesion.query(EpochSync)
                .filter(EpochSync.epoch > desde, EpochSync.epoch > 0)
                .order_by(EpochSync.epoch)
                .limit(limite)
                .all()
            )
            paquetes = [self._paquete_epoch(sesion, fila) for fila in filas]
            ultimo = filas[-1].epoch if filas else desde
            return {
                "epochs": paquetes,
                "epoch_actual": actual,
                "cursor": ultimo,
                "hay_mas": bool(filas) and ultimo < actual,
            }
        except SQLAlchemyError:
            logger.error("No se pudieron leer los ciclos", exc_info=True)
            raise ErrorPeticion("Error interno al leer los ciclos", 500) from None
        finally:
            sesion.close()

    def _paquete_epoch(self, sesion, epoch: EpochSync) -> dict:
        """Ciclo completo listo para el cliente, con su manifiesto"""
        eventos = (
            sesion.query(EventoSync)
            .filter(EventoSync.epoch == epoch.epoch)
            .order_by(EventoSync.secuencia_global, EventoSync.id)
            .all()
        )
        filas = (
            sesion.query(EpochFila)
            .filter(EpochFila.epoch == epoch.epoch)
            .order_by(EpochFila.id)
            .all()
        )
        return {
            "epoch": epoch.epoch,
            "manifiesto": epoch.manifiesto,
            "publicado_en": epoch.publicado_en.isoformat(),
            "eventos": [self._evento_wire(fila) for fila in eventos],
            "filas": [
                {
                    "tabla": fila.tabla,
                    "fila_uuid": fila.fila_uuid,
                    "valores": loads(fila.valores) or {},
                    "borrado": bool(fila.borrado),
                }
                for fila in filas
            ],
        }

    def confirmar_epoch(self, dispositivo: DispositivoSync, epoch: int) -> dict:
        """Registra hasta qué ciclo tiene aplicado un puesto"""
        epoch = int(epoch or 0)
        sesion = self._sesion()
        try:
            existente = (
                sesion.query(AckEpoch)
                .filter(
                    AckEpoch.dispositivo == dispositivo.dispositivo_id,
                    AckEpoch.epoch == epoch,
                )
                .first()
            )
            if existente is None:
                sesion.add(AckEpoch(dispositivo=dispositivo.dispositivo_id, epoch=epoch))
            dispositivo.ultima_conexion = ahora_utc()
            sesion.commit()
            return {
                "epoch": epoch,
                "epoch_actual": self._epoch_actual(sesion),
                "atrasados": self._puestos_atrasados(sesion),
            }
        except SQLAlchemyError:
            sesion.rollback()
            logger.error("No se pudo confirmar el ciclo %s", epoch, exc_info=True)
            raise ErrorPeticion("Error interno al confirmar el ciclo", 500) from None
        finally:
            sesion.close()

    @staticmethod
    def _puestos_atrasados(sesion) -> list[dict]:
        """
        Puestos activos que aún no aplicaron el último ciclo publicado

        Es la lista que alimenta la ventana de consolidación: un puesto
        conectado que se atrasa se reintenta; uno apagado queda para el backfill
        del siguiente ciclo, conservando la posición de sus eventos.
        """
        actual = int(sesion.query(func.max(EpochSync.epoch)).scalar() or 0)
        atrasados: list[dict] = []
        for dispositivo in sesion.query(DispositivoSync).filter(DispositivoSync.activo == 1).all():
            ultimo = (
                sesion.query(func.max(AckEpoch.epoch))
                .filter(AckEpoch.dispositivo == dispositivo.dispositivo_id)
                .scalar()
            )
            if int(ultimo or 0) < actual:
                atrasados.append(
                    {
                        "dispositivo": dispositivo.dispositivo_id,
                        "nombre": dispositivo.nombre,
                        "epoch": int(ultimo or 0),
                        "ultima_conexion": (
                            dispositivo.ultima_conexion.isoformat()
                            if dispositivo.ultima_conexion
                            else None
                        ),
                    }
                )
        return atrasados

    @staticmethod
    def _registrar_reloj(sesion, dispositivo_id: str, desfase_ms: int, rtt_ms: int = 0) -> None:
        """Guarda el desfase medido del reloj del puesto"""
        fila = sesion.get(RelojPuesto, dispositivo_id)
        if fila is None:
            sesion.add(
                RelojPuesto(
                    dispositivo=dispositivo_id,
                    desfase_ms=desfase_ms,
                    rtt_ms=rtt_ms,
                    medido_en=ahora_utc(),
                )
            )
        else:
            fila.desfase_ms = desfase_ms
            fila.rtt_ms = rtt_ms
            fila.medido_en = ahora_utc()

    def _resumen_lote(self, sesion, lote: LoteEntrada) -> dict:
        """Respuesta idempotente para un lote ya recibido"""
        aplicadas = []
        if lote.estado == LOTE_CONSOLIDADO:
            aplicadas = [
                op_id
                for (op_id,) in sesion.query(EventoSync.op_id)
                .filter(EventoSync.lote_id == lote.lote_id)
                .all()
            ]
        return {
            "lote_id": lote.lote_id,
            "estado": lote.estado,
            "epoch": lote.epoch,
            "aplicadas": aplicadas,
            "rechazadas": [],
            "conflictos": [],
            "cursor": self.cursor_actual(),
        }

    def importar_legado(self) -> int:
        """
        Copia al log los ``sync_ops`` anteriores al protocolo de ciclos

        Son operaciones que el nodo ya aplicó con el motor anterior. Se
        convierten en eventos del ciclo 0, conservando su ``seq`` como orden, y
        las operaciones nuevas se publican como ciclos a partir del 1. Es
        idempotente: si ya hay ciclos, no hace nada.
        """
        self._epoch_cache = self.epoch_actual()
        sesion = self._sesion()
        try:
            if sesion.query(EpochSync).first() is not None:
                return 0
            existentes = {op_id for (op_id,) in sesion.query(EventoSync.op_id).all()}
            importados = 0
            for fila in sesion.query(OpServidor).order_by(OpServidor.seq).all():
                if fila.op_id in existentes:
                    continue
                sesion.add(
                    EventoSync(
                        op_id=fila.op_id,
                        lote_id="legado",
                        tabla=fila.tabla,
                        fila_uuid=fila.fila_uuid,
                        operacion=fila.operacion,
                        payload=fila.payload,
                        base_op_id=fila.base_op_id,
                        dispositivo=fila.dispositivo,
                        usuario=fila.usuario,
                        ocurrido_en=fila.creado_en,
                        ocurrido_corregido=fila.creado_en,
                        desfase_ms=0,
                        recibido_en=fila.recibido_en or fila.creado_en,
                        secuencia_global=fila.seq,
                        epoch=0,
                        estado=EVENTO_CONSOLIDADO,
                    )
                )
                importados += 1
            sesion.add(
                EpochSync(
                    epoch=0,
                    manifiesto=consolidacion.manifiesto_epoch([], []),
                    n_eventos=importados,
                    n_filas=0,
                )
            )
            sesion.commit()
            self._epoch_cache = self.epoch_actual()
            if importados:
                logger.info(
                    "Log de sincronización migrado: %s eventos del motor anterior", importados
                )
            return importados
        except SQLAlchemyError:
            sesion.rollback()
            logger.warning("No se pudo importar el log anterior", exc_info=True)
            return 0
        finally:
            sesion.close()

    def aplicar_lote_heredado(self, dispositivo: DispositivoSync, cuerpo: dict) -> dict:
        """
        Aplica un lote de operaciones con el motor anterior (sin staging)

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
            roles_cache: dict[str, str | None] = {}
            for operacion in operaciones:
                if not isinstance(operacion, dict):
                    continue
                op_id = str(operacion.get("op_id") or "")
                if not op_id:
                    continue
                # Autoridad final de permisos: una cuenta central sin permiso
                # de escritura no puede meter filas por la puerta de
                # sincronización, aunque el teléfono se la salte en la UI.
                motivo_permiso = self._autorizar_escritura(sesion, operacion, roles_cache)
                if motivo_permiso:
                    rechazadas.append({"op_id": op_id, "motivo": motivo_permiso})
                    logger.info(
                        "Operación %s rechazada por permisos (%s)",
                        op_id[:8],
                        motivo_permiso,
                    )
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

    def _autorizar_escritura(
        self, sesion, operacion: dict, roles_cache: dict[str, str | None]
    ) -> str | None:
        """
        Comprueba los permisos del rol de la cuenta que envía una operación

        Returns:
            Motivo de rechazo, o None si la operación está autorizada
        """
        tabla = str(operacion.get("tabla") or "")
        regla = TABLAS_PROTEGIDAS.get(tabla)
        if regla is None:
            return None
        username = str(operacion.get("usuario") or "").strip()
        if not username:
            # Puestos antiguos no envían usuario: la confianza sigue en el
            # token del dispositivo (y en la revocación administrativa).
            return None
        if username not in roles_cache:
            roles_cache[username] = self._rol_central(sesion, username)
        rol = roles_cache[username]
        if rol is None:
            # La cuenta no existe en la base central: pertenece a un puesto
            # que administra sus propias cuentas (usuarios no se replica).
            return None

        from src.utils.security import PermissionChecker

        modulo, permiso_escritura = regla
        tipo = str(operacion.get("operacion") or "upsert")
        permiso = "delete" if tipo == "delete" else permiso_escritura
        if not PermissionChecker.has_permission(rol, permiso):
            return f"permiso_insuficiente:{permiso}"
        if not PermissionChecker.can_access_module(rol, modulo):
            return f"modulo_no_autorizado:{modulo}"
        return None

    @staticmethod
    def _rol_central(sesion, username: str) -> str | None:
        """Rol de una cuenta en la base central (None si no existe)"""
        from src.models import Usuario

        usuario = sesion.query(Usuario).filter(Usuario.username == username).first()
        return usuario.rol_valor if usuario is not None else None

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
    # Protocolo 2: consultas, administración, acciones y archivos
    # ------------------------------------------------------------------
    def api_acciones(
        self,
        sesion_usuario,
        dispositivo: DispositivoSync,
        ruta: str,
        cuerpo: dict,
        parametros: dict,
        contenido: bytes | None = None,
    ) -> dict:
        """
        Despacha una petición del protocolo 2 a su acción

        Args:
            sesion_usuario: Sesión de usuario ya validada por el gestor
            dispositivo: Equipo autenticado (para el almacén de binarios)
            ruta: Ruta absoluta de la petición
            cuerpo: Cuerpo JSON ya decodificado ({} en GET)
            parametros: Parámetros de la cadena de consulta
            contenido: Cuerpo binario de ``/archivos/subir`` (crudo, sin
                JSON); lo entrega el manejador de la petición, que es quien
                tiene acceso al flujo de entrada

        Returns:
            dict JSON listo para responder
        """
        from sync_agent.api_acciones import ErrorApi

        api = self.api
        partes = [p for p in ruta.split("/") if p]
        # ['api', 'v1', seccion, ...]
        if len(partes) < 4 or partes[0] != "api" or partes[1] != "v1":
            raise ErrorApi("recurso no encontrado", 404)
        seccion, resto = partes[2], partes[3:]

        def entero(indice: int, nombre: str) -> int:
            try:
                return int(resto[indice])
            except (IndexError, ValueError):
                raise ErrorApi(f"Falta el identificador de {nombre}", 400) from None

        if seccion == "consultas":
            if resto == ["dashboard"]:
                return api.dashboard(sesion_usuario)
            if resto == ["auditoria"]:
                limite = int((parametros.get("limite") or ["100"])[0] or 100)
                return api.auditoria(sesion_usuario, limite)
            raise ErrorApi("recurso no encontrado", 404)

        if seccion == "admin":
            if resto == ["usuarios"]:
                if not cuerpo:
                    return api.listar_usuarios(sesion_usuario)
                return api.crear_usuario(sesion_usuario, cuerpo)
            if len(resto) == 2 and resto[0] == "usuarios":
                usuario_id = entero(1, "usuario")
                return api.actualizar_usuario(sesion_usuario, usuario_id, cuerpo)
            if len(resto) == 3 and resto[0] == "usuarios" and resto[2] == "desbloquear":
                usuario_id = entero(1, "usuario")
                return api.desbloquear_usuario(sesion_usuario, usuario_id)
            raise ErrorApi("recurso no encontrado", 404)

        if seccion == "acciones":
            return self._despachar_accion(api, sesion_usuario, resto, cuerpo)

        if seccion == "archivos":
            # /archivos/pdf/{tipo} · /archivos/excel/{tipo} · /archivos/subir
            if len(resto) == 2 and resto[0] in ("pdf", "excel"):
                return api.generar_archivo(sesion_usuario, resto[1], cuerpo, dispositivo)
            if resto == ["subir"]:
                nombre = (parametros.get("nombre") or ["archivo.bin"])[0]
                # El contenido viaja como cuerpo binario (no JSON) y llega
                # como parámetro: este núcleo no tiene acceso al flujo de
                # entrada de la petición (lo lee el manejador).
                return api.subir_archivo(sesion_usuario, nombre, contenido or b"", dispositivo)
            raise ErrorApi("recurso no encontrado", 404)

        raise ErrorApi("recurso no encontrado", 404)

    @staticmethod
    def _despachar_accion(
        api: ApiAcciones, sesion_usuario: SesionValida, resto: list[str], cuerpo: dict
    ) -> dict:
        """Despacha /api/v1/acciones/... según su segmento"""
        from sync_agent.api_acciones import ErrorApi

        def entero(indice: int, nombre: str) -> int:
            try:
                return int(resto[indice])
            except (IndexError, ValueError):
                raise ErrorApi(f"Falta el identificador de {nombre}", 400) from None

        if not resto:
            raise ErrorApi("recurso no encontrado", 404)

        grupo = resto[0]
        if grupo == "nomina":
            if resto[1:] == ["generar"]:
                return api.generar_nomina_periodo(sesion_usuario, cuerpo)
            if resto[1:] == ["resumen"]:
                return api.resumen_nomina(sesion_usuario, cuerpo)
            if len(resto) == 3 and resto[2] == "pagado":
                return api.marcar_pagado(sesion_usuario, entero(1, "pago"))

        elif grupo == "incidencias":
            if len(resto) == 3 and resto[2] == "aprobar":
                return api.aprobar_incidencia(sesion_usuario, entero(1, "incidencia"), cuerpo)
            if len(resto) == 3 and resto[2] == "rechazar":
                return api.rechazar_incidencia(sesion_usuario, entero(1, "incidencia"), cuerpo)

        elif grupo == "contratos":
            if len(resto) == 3 and resto[2] == "renovar":
                return api.renovar_contrato(sesion_usuario, entero(1, "contrato"), cuerpo)
            if len(resto) == 3 and resto[2] == "terminar":
                return api.terminar_contrato(sesion_usuario, entero(1, "contrato"), cuerpo)

        elif grupo == "academicos":
            return NucleoCentral._despachar_academico(api, sesion_usuario, resto[1:], cuerpo)

        raise ErrorApi("recurso no encontrado", 404)

    @staticmethod
    def _despachar_academico(
        api: ApiAcciones, sesion_usuario: SesionValida, resto: list[str], cuerpo: dict
    ) -> dict:
        """Despacha las rutas académicas: periodos, notas y tokens"""
        from sync_agent.api_acciones import ErrorApi

        def entero(indice: int, nombre: str) -> int:
            try:
                return int(resto[indice])
            except (IndexError, ValueError):
                raise ErrorApi(f"Falta el identificador de {nombre}", 400) from None

        if not resto:
            raise ErrorApi("recurso no encontrado", 404)

        if resto[0] == "periodo":
            if len(resto) == 3 and resto[2] == "cerrar":
                return api.cerrar_periodo(sesion_usuario, entero(1, "periodo"), cuerpo)
            if len(resto) == 3 and resto[2] == "reabrir":
                return api.reabrir_periodo(sesion_usuario, entero(1, "periodo"), cuerpo)

        if resto == ["notas", "lote"]:
            return api.cargar_notas_lote(sesion_usuario, cuerpo)
        if len(resto) == 3 and resto[0] == "notas" and resto[1] == "grado":
            return api.notas_de_grado(sesion_usuario, entero(2, "grado"))
        if resto == ["notas", "boletin"]:
            return api.boletin_estudiante(sesion_usuario, cuerpo)
        if resto == ["notas", "acta"]:
            return api.acta_grado(sesion_usuario, cuerpo)
        if resto == ["notas", "consolidado"]:
            return api.consolidado_periodo(sesion_usuario, cuerpo)
        if resto == ["token", "emitir"]:
            return api.emitir_token_academico(sesion_usuario)
        if resto == ["token", "revocar"]:
            return api.revocar_token_academico(sesion_usuario, cuerpo)

        raise ErrorApi("recurso no encontrado", 404)

    # ------------------------------------------------------------------
    # Binarios
    # ------------------------------------------------------------------
    def guardar_blob(
        self, dispositivo: DispositivoSync, hash_archivo: str, contenido: bytes
    ) -> dict:
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
    def emparejar(self, nombre: str | None, ip: str) -> dict:
        """
        Da de alta un puesto nuevo que se auto-descubrió en la red

        Es el camino sin supervisión: el teléfono que encontró el nodo pide sus
        credenciales de equipo sin que el administrador escriba nada. Solo se
        admite si ``emparejamiento_abierto`` está activo; se limita por IP para
        que nadie pueda crear cientos de equipos en bucle, y el alta queda
        registrada en la bitácora con la IP de origen.

        Args:
            nombre: Nombre visible del puesto (puede venir vacío)
            ip: Dirección del equipo que llama, para la bitácora y la tasa

        Returns:
            dict con ``dispositivo_id`` y ``token`` (el token solo se devuelve
            aquí; en la base queda únicamente su hash).

        Raises:
            ErrorPeticion: 403 si el emparejamiento está cerrado, 429 si la
                IP superó el límite de peticiones.
        """
        if not self.config.emparejamiento_abierto:
            raise ErrorPeticion(
                "El emparejamiento automático está desactivado en el nodo central",
                403,
            )
        # Tasa propia y más restrictiva que la general: el emparejamiento es
        # un evento raro, así que un bombardeo aquí es siempre sospechoso.
        self.limitar_tasa(f"emparejar:{ip}")
        dispositivo_id, token = self.crear_dispositivo((nombre or "").strip() or "Teléfono")
        logger.info("Puesto emparejado automáticamente desde la red (%s)", ip)
        return {"dispositivo_id": dispositivo_id, "token": token}

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
                    "ultima_conexion": (
                        fila.ultima_conexion.isoformat() if fila.ultima_conexion else None
                    ),
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
                sesion.query(OpServidor)
                .filter(OpServidor.recibido_en < limite)
                .delete(synchronize_session=False)
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
                "archivos": (
                    len(list(self.config.dir_blobs.rglob("*")))
                    if self.config.dir_blobs.exists()
                    else 0
                ),
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
    def _bitacora(
        sesion, dispositivo: str | None, evento: str, detalle: str, correcto: bool
    ) -> None:
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
RUTA_EPOCHS = "/api/v1/epochs"
RUTA_ACK = "/api/v1/ack"
RUTA_BLOB = "/api/v1/blob"

# Rutas del protocolo 2 (acciones y consultas de la aplicación móvil)
RUTA_AUTH = "/api/v1/auth"
RUTA_CONSULTAS = "/api/v1/consultas"
RUTA_ADMIN = "/api/v1/admin"
RUTA_ACCIONES = "/api/v1/acciones"
RUTA_ARCHIVOS = "/api/v1/archivos"

# Escritura protegida por permisos: tabla -> (módulo, permiso de escritura)
# Un ``push`` de una cuenta que exista en la base central se autoriza aquí con
# la misma matriz que usa la interfaz de escritorio. Las operaciones sin
# usuario declarado (puestos antiguos) o de cuentas locales de otro puesto no
# se tocan: ``usuarios`` no se replica, así que solo se exige permiso cuando la
# cuenta es conocida en el nodo central. ``registros_moviles`` y
# ``notas_finales`` quedan fuera: la primera es captura de campo autenticada y
# las segundas las autoriza el token académico, no el mapa de módulos.
TABLAS_PROTEGIDAS: dict[str, tuple[str, str]] = {
    "empleados": ("empleados", "update"),
    "documentos": ("documentos", "update"),
    "incidencias": ("incidencias", "update"),
    "contratos": ("contratos", "update"),
    "pagos": ("nomina", "update"),
    "configuraciones": ("configuracion", "config"),
    "estudiantes": ("estudiantes", "update"),
    "periodos_academicos": ("notas", "update"),
    "grados": ("estudiantes", "update"),
    "matriculas": ("estudiantes", "update"),
}


class ManejadorSync(BaseHTTPRequestHandler):
    """Traduce cada petición HTTP en una llamada al núcleo central"""

    server_version = "SDEP-SyncAgent/1.0"
    protocol_version = "HTTP/1.1"
    # Un cliente que abre la conexión y deja de enviar datos no puede retener
    # un hilo del servidor para siempre: el servicio es multihilo y cada
    # conexión colgada consume uno. Pasado este tiempo, ``socketserver`` cierra
    # la conexión y el teléfono reintenta.
    timeout = 30

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

    def do_PUT(self) -> None:  # noqa: N802 - nombre exigido por la biblioteca
        # La actualización de una cuenta (``PUT /api/v1/admin/usuarios/{id}``)
        # existe en el cliente móvil y en ``api_acciones``; sin este método, el
        # servidor respondía 501 ("Unsupported method") y la administración de
        # cuentas desde el teléfono nunca podía completarse.
        self._atender("PUT")

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
            self._cuerpo = self._leer_cuerpo() if metodo in ("POST", "PUT") else b""

            if ruta.path == RUTA_PING:
                self._responder_json(200, self.nucleo.ping())
                return

            # --- Protocolo 2: autenticación de usuario (sin token de equipo
            # todavía: el login es el único punto abierto y por eso lleva su
            # propio límite de peticiones) ---
            if ruta.path == f"{RUTA_AUTH}/login" and metodo == "POST":
                self.nucleo.limitar_tasa("login:" + (self.client_address[0] or "?"))
                datos = self.nucleo.api.login(self._leer_json(), self.headers.get("X-Dispositivo"))
                self._responder_json(200, datos)
                return

            # --- Auto-emparejamiento: un teléfono que se descubrió solo pide
            # sus credenciales de equipo. Abierto por decisión del propietario;
            # el toggle del nodo central lo puede cerrar. ---
            if ruta.path == f"{RUTA_AUTH}/emparejar" and metodo == "POST":
                datos = self.nucleo.emparejar(
                    self.headers.get("X-Nombre-Equipo"),
                    self.client_address[0] or "?",
                )
                self._responder_json(200, datos)
                return

            if ruta.path.startswith(f"{RUTA_AUTH}/"):
                accion = ruta.path[len(RUTA_AUTH) + 1 :]
                token = self._token_sesion()
                if accion == "sesion" and metodo == "GET":
                    self._responder_json(200, self.nucleo.api.info_sesion(token))
                elif accion == "logout" and metodo == "POST":
                    self._responder_json(200, self.nucleo.api.cerrar_sesion(token))
                elif accion == "cambiar-password" and metodo == "POST":
                    datos = self.nucleo.api.cambiar_password(token, self._leer_json())
                    self._responder_json(200, datos)
                else:
                    self._responder_json(404, {"error": "recurso no encontrado"})
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

            if ruta.path == RUTA_EPOCHS and metodo == "GET":
                parametros = parse_qs(ruta.query)
                desde = int((parametros.get("desde") or ["0"])[0] or 0)
                limite = int((parametros.get("limite") or ["1"])[0] or 1)
                self._responder_json(200, self.nucleo.pull_epochs(dispositivo, desde, limite))
                return

            if ruta.path == RUTA_ACK and metodo == "POST":
                cuerpo = self._leer_json()
                epoch = int(cuerpo.get("epoch") or 0)
                self._responder_json(200, self.nucleo.confirmar_epoch(dispositivo, epoch))
                return

            if ruta.path.startswith(RUTA_BLOB + "/"):
                self._atender_blob(metodo, dispositivo, ruta.path[len(RUTA_BLOB) + 1 :])
                return

            # --- Protocolo 2: consultas, administración, acciones y archivos ---
            if ruta.path.startswith(
                (RUTA_CONSULTAS + "/", RUTA_ADMIN + "/", RUTA_ACCIONES + "/", RUTA_ARCHIVOS + "/")
            ):
                sesion_usuario = self.nucleo.api.validar(self._token_sesion())
                # /archivos/subir trae bytes crudos, no JSON: su cuerpo se lee
                # como binario dentro de la acción.
                es_subida = ruta.path.startswith(RUTA_ARCHIVOS + "/subir")
                cuerpo = (
                    {}
                    if es_subida
                    else (self._leer_json() if metodo in ("POST", "PUT") else {})
                )
                datos = self.nucleo.api_acciones(
                    sesion_usuario,
                    dispositivo,
                    ruta.path,
                    cuerpo,
                    parse_qs(ruta.query),
                    contenido=self._cuerpo_archivo() if es_subida else None,
                )
                self._responder_json(200, datos)
                return

            self._responder_json(404, {"error": "recurso no encontrado"})
        except ErrorApi as error:
            self._responder_json(error.codigo, {"error": str(error)})
        except ErrorSesion as error:
            self._responder_json(error.codigo, {"error": str(error)})
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

    def _token_sesion(self) -> str:
        """Token de sesión de usuario (cabecera ``X-Sesion``)"""
        return (self.headers.get("X-Sesion") or "").strip()

    def _cuerpo_archivo(self) -> bytes:
        """Cuerpo crudo de la petición (para subidas binarias)"""
        return getattr(self, "_cuerpo", b"")

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
        limite = max(self.nucleo.config.max_bytes_peticion, self.nucleo.config.max_bytes_blob)
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
        self._responder_bytes(
            codigo, dumps(datos).encode("utf-8"), "application/json; charset=utf-8"
        )

    def _responder_binario(self, codigo: int, contenido: bytes) -> None:
        """Responde con el contenido binario de un archivo"""
        self._responder_bytes(codigo, contenido, "application/octet-stream")

    def _responder_bytes(self, codigo: int, cuerpo: bytes, tipo: str) -> None:
        """
        Escribe una respuesta completa

        Si el teléfono ya cerró la conexión (cambio de red, pantalla apagada),
        ``write`` lanza una excepción de conexión. Antes escapaba al manejador
        genérico y este intentaba responder **otra vez** sobre la misma
        conexión rota, ensuciando el registro con un segundo error. Aquí el
        corte se anota y se termina la petición.
        """
        try:
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
        except (
            BrokenPipeError,
            ConnectionResetError,
            ConnectionAbortedError,
            TimeoutError,
        ) as error:
            logger.info("El cliente %s cerró la conexión: %s", self.client_address[0], error)
            self.close_connection = True


class ServidorSync(ThreadingHTTPServer):
    """Servicio HTTP multihilo del nodo central"""

    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address) -> None:
        """
        Registra el fallo de una petición en lugar de volcar una traza

        ``socketserver`` imprime la traza completa por consola cuando una
        petición escapa de su manejador, de modo que una desconexión normal de
        un cliente (o el fallo al responder a una conexión ya cerrada) parecía
        una avería del nodo. Se distingue el corte de conexión del fallo
        inesperado: el primero se anota sin traza y el segundo con ella.
        """
        error = sys.exc_info()[1]
        if isinstance(error, (ConnectionError, TimeoutError, OSError)):
            logger.info("Conexión con %s interrumpida: %s", client_address, error)
            return
        logger.error("Fallo atendiendo a %s", client_address, exc_info=True)

    def __init__(self, config: ServidorConfig, nucleo: NucleoCentral | None = None):
        self.nucleo = nucleo or NucleoCentral(config)
        super().__init__((config.host, config.puerto), ManejadorSync)
        self.config_servidor = config
        if config.certificado and config.clave:
            self._envolver_tls(config.certificado, config.clave)
        # La difusión se abre después del HTTP: el puerto real ya se conoce
        # (importante cuando el sistema elige uno efímero) y un fallo aquí
        # nunca impide atender a los puestos que ya conocen la dirección.
        self.difusor: DifusorDescubrimiento | None = None
        if config.puerto_descubrimiento:
            self.difusor = DifusorDescubrimiento(
                puerto_http=int(self.server_address[1]),
                puerto=config.puerto_descubrimiento,
                nombre=config.nombre_equipo,
            )
            self.difusor.iniciar()

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

    def server_close(self) -> None:
        """Cierra también la difusión al cerrar el socket HTTP"""
        difusor = getattr(self, "difusor", None)
        if difusor is not None:
            difusor.detener()
            self.difusor = None
        super().server_close()

    def cerrar(self) -> None:
        """Cierra el socket, la difusión y libera el motor de base de datos"""
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
