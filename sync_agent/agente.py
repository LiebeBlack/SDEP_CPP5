"""
Agente de sincronización en segundo plano

Un único hilo demonio ejecuta el ciclo completo (subir, bajar, aplicar y mover
archivos) y espera con ``Event.wait``, que es una espera interrumpible: no hay
sondeos con ``sleep`` ni consumo de CPU mientras no toca trabajar.

Tres reglas que garantizan que la aplicación del usuario no se vea afectada:

1. **Sesión propia por tramo**: el agente nunca usa la sesión de la interfaz
   (una sesión de SQLAlchemy no es segura entre hilos).
2. **Ninguna conexión abierta durante la red**: se lee el lote, se cierra la
   sesión, se habla con el servidor y se abre una sesión nueva para confirmar.
3. **La interfaz nunca se toca desde el hilo**: el agente publica un estado
   inmutable y, si se le da un notificador, lo invoca para que la ventana
   genere su propio evento en el hilo principal.
"""

from __future__ import annotations

import logging
import random
import threading
from datetime import timedelta
from typing import Any, Callable

from sqlalchemy.exc import SQLAlchemyError

from sync_agent import identidad, registro
from sync_agent.aplicador import MOTIVO_ERROR, AplicadorRemoto
from sync_agent.captura import cambios_silenciosos, establecer_dispositivo
from sync_agent.cliente import ClienteSync, ErrorAutenticacion, ErrorSincronizacion
from sync_agent.comun import ahora_utc, dumps, hash_bytes, loads, nuevo_uuid
from sync_agent.config import ConfigSync, cargar
from sync_agent.esquema import (
    BLOB_POR_BAJAR,
    BLOB_POR_SUBIR,
    BLOB_SUBIDO,
    CONFIRMADA,
    DIFERIDA,
    DIRECCION_ENTRADA,
    DIRECCION_SALIDA,
    ENVIANDO,
    PENDIENTE,
    RECHAZADA,
    BlobSync,
    CampoRemoto,
    ConflictoSync,
    CursorSync,
    EstadoSync,
    JournalOp,
)

logger = logging.getLogger(__name__)

# Estados que publica el agente para la interfaz
ESTADO_DETENIDO = "detenido"
ESTADO_INACTIVO = "inactivo"
ESTADO_SIN_CONEXION = "sin_conexion"
ESTADO_SINCRONIZANDO = "sincronizando"
ESTADO_SINCRONIZADO = "sincronizado"
ESTADO_ERROR_TOKEN = "error_token"

MAX_INTENTOS_DIFERIDA = 10
MAX_LOTES_POR_CICLO = 20
DIAS_RETENCION_JOURNAL = 7
ESPERA_MAXIMA = 300


class AgenteSincronizacion:
    """Hilo de sincronización y su estado observable"""

    def __init__(
        self,
        config: ConfigSync | None = None,
        notificador: Callable[[dict], None] | None = None,
        intervalo_por_defecto: int = 30,
    ):
        """
        Args:
            config: Configuración vigente (se lee del archivo si no se pasa)
            notificador: Función invocada tras cada ciclo con el estado nuevo
            intervalo_por_defecto: Intervalo si la configuración no lo define
        """
        self.config = config or cargar()
        self.notificador = notificador
        self.intervalo_por_defecto = intervalo_por_defecto

        self._hilo: threading.Thread | None = None
        self._detener = threading.Event()
        self._despertar = threading.Event()
        self._candado = threading.Lock()
        self._en_ciclo = threading.Lock()
        self._estado_lock = threading.Lock()
        self._estado: dict[str, Any] = {
            "habilitado": self.config.activo,
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

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def iniciar(self) -> bool:
        """
        Arranca el hilo de sincronización

        Returns:
            True si el hilo quedó en marcha
        """
        with self._candado:
            if self._hilo is not None and self._hilo.is_alive():
                return True
            if not self.config.activo:
                problemas = self.config.problemas()
                logger.info(
                    "Sincronización inactiva: %s",
                    "; ".join(problemas) if problemas else "deshabilitada en la configuración",
                )
                self._publicar(estado=ESTADO_INACTIVO, ultimo_error=problemas[0] if problemas else None)
                return False

            establecer_dispositivo(self.config.dispositivo_id)
            self._detener.clear()
            self._despertar.clear()
            self._hilo = threading.Thread(
                target=self._bucle, name="sincronizacion", daemon=True
            )
            self._hilo.start()
            self._publicar(estado=ESTADO_SINCRONIZANDO)
            logger.info(
                "Sincronización iniciada cada %s s contra %s",
                self.config.intervalo_segundos,
                self.config.url_servidor,
            )
            return True

    def detener(self, timeout: float = 5.0) -> None:
        """Detiene el hilo y espera de forma acotada a que termine"""
        self._detener.set()
        self._despertar.set()
        hilo = self._hilo
        if hilo is not None and hilo.is_alive():
            hilo.join(timeout=timeout)
            if hilo.is_alive():  # pragma: no cover - salida lenta
                logger.warning("El hilo de sincronización no terminó en %s s", timeout)
        self._hilo = None
        self._publicar(estado=ESTADO_DETENIDO)

    def activo(self) -> bool:
        """Indica si el hilo está en marcha"""
        return self._hilo is not None and self._hilo.is_alive()

    def sincronizar_ahora(self) -> bool:
        """
        Pide un ciclo inmediato sin bloquear a quien llama

        Returns:
            True si hay un agente en marcha que atenderá la petición
        """
        if not self.activo():
            return False
        self._despertar.set()
        return True

    def estado(self) -> dict:
        """Copia del estado observable (segura para leer desde otro hilo)"""
        with self._estado_lock:
            return dict(self._estado)

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------
    def _bucle(self) -> None:
        """Bucle del hilo: un ciclo, una espera interrumpible"""
        fallos = 0
        while not self._detener.is_set():
            self._despertar.clear()
            resultado = self.ciclo()
            # La espera es fraccionaria tras un fallo (lleva azar); con el
            # servicio en pie es el intervalo configurado, sin decimales.
            espera: float
            if resultado.get("correcto"):
                fallos = 0
                espera = float(max(1, self.config.intervalo_segundos))
            elif resultado.get("detener"):
                break
            else:
                fallos += 1
                espera = self._esperar_tras_fallo(fallos)
            self._publicar(
                fallos_consecutivos=fallos,
                siguiente_intento_segundos=None if resultado.get("correcto") else int(espera),
            )
            if self._detener.is_set():
                break
            self._despertar.wait(espera)

    @staticmethod
    def _esperar_tras_fallo(fallos: int) -> float:
        """
        Espera creciente con algo de azar

        30 s, 60 s, 120 s... hasta un máximo de cinco minutos. El azar evita
        que todos los puestos del colegio golpeen el servidor a la vez cuando
        vuelve la red.
        """
        # La anotación es necesaria: el tipado de la biblioteca estándar declara
        # «int ** int» como Any, así que sin ella la espera dejaría de ser
        # numérica para el verificador.
        base: int = min(30 * (2 ** max(0, fallos - 1)), ESPERA_MAXIMA)
        return base + random.uniform(0, min(5.0, base * 0.1))

    # ------------------------------------------------------------------
    # Un ciclo completo
    # ------------------------------------------------------------------
    def ciclo(self) -> dict:
        """
        Ejecuta un ciclo de sincronización completo

        Returns:
            Resumen del ciclo (``correcto``, ``mensaje``, contadores)
        """
        if not self._en_ciclo.acquire(blocking=False):
            return {"correcto": True, "mensaje": "ciclo ya en curso"}

        inicio = ahora_utc()
        resumen: dict[str, Any] = {"correcto": False, "mensaje": ""}
        try:
            if not self.config.configurado:
                problemas = self.config.problemas()
                self._publicar(estado=ESTADO_INACTIVO, ultimo_error=problemas[0] if problemas else None)
                resumen["mensaje"] = "sincronización no configurada"
                return resumen

            self._publicar(estado=ESTADO_SINCRONIZANDO)
            cliente = ClienteSync(
                url_servidor=self.config.url_servidor,
                token=self.config.token,
                dispositivo=self.config.dispositivo_id,
                timeout=self.config.timeout_segundos,
            )
            resumen = self._ejecutar(cliente)
        except ErrorAutenticacion as error:
            logger.error("Sincronización detenida: %s", error)
            self._publicar(estado=ESTADO_ERROR_TOKEN, ultimo_error=str(error), habilitado=False)
            self._registrar_evento("auth_fallida", str(error), correcto=False)
            resumen = {"correcto": False, "detener": True, "mensaje": str(error)}
        except ErrorSincronizacion as error:
            logger.warning("Ciclo de sincronización sin éxito: %s", error)
            self._publicar(estado=ESTADO_SIN_CONEXION, ultimo_error=str(error))
            resumen = {"correcto": False, "mensaje": str(error)}
        except Exception as error:  # pragma: no cover - red de seguridad del hilo
            logger.error("Fallo inesperado en el ciclo de sincronización", exc_info=True)
            self._publicar(estado=ESTADO_SIN_CONEXION, ultimo_error=str(error))
            resumen = {"correcto": False, "mensaje": str(error)}
        finally:
            milisegundos = int((ahora_utc() - inicio).total_seconds() * 1000)
            self._publicar(ms_ultimo_ciclo=milisegundos)
            self._en_ciclo.release()
        return resumen

    def _ejecutar(self, cliente: ClienteSync) -> dict:
        """Sube, baja y mueve binarios dentro de un ciclo"""
        desfase = self._ping(cliente)
        subida = self._subir(cliente)
        bajada = self._bajar(cliente)
        diferidas = self._reintentar_diferidas()
        binarios = self._mover_binarios(cliente)
        self._compactar()

        pendientes = self._contar_pendientes()
        conflictos = self._contar_conflictos()
        self._publicar(
            estado=ESTADO_SINCRONIZADO if pendientes == 0 else ESTADO_SINCRONIZANDO,
            pendientes=pendientes,
            conflictos=conflictos,
            ultima_sincronizacion=ahora_utc().isoformat(timespec="seconds"),
            ultimo_error=None,
            desfase_reloj_segundos=desfase,
            ciclos=int(self._estado.get("ciclos") or 0) + 1,
            subidas=int(self._estado.get("subidas") or 0) + subida,
            bajadas=int(self._estado.get("bajadas") or 0) + bajada,
        )
        self._guardar_estado(
            ultima_sincronizacion=ahora_utc().isoformat(timespec="seconds"),
            desfase_reloj=str(desfase),
            pendientes=str(pendientes),
        )
        if conflictos:
            self._registrar_evento(
                "conflictos",
                f"{conflictos} conflicto(s) pendientes de revisión",
                correcto=False,
            )
        return {
            "correcto": True,
            "mensaje": f"subidas={subida} bajadas={bajada} diferidas={diferidas} binarios={binarios}",
            "subidas": subida,
            "bajadas": bajada,
        }

    # ------------------------------------------------------------------
    # Pasos del ciclo
    # ------------------------------------------------------------------
    def _ping(self, cliente: ClienteSync) -> int:
        """Comprueba el servicio y mide el desfase de reloj con el servidor"""
        datos = cliente.ping()
        desfase = 0
        try:
            hora_servidor = datos.get("hora")
            if hora_servidor:
                from datetime import datetime

                desfase = int((ahora_utc() - datetime.fromisoformat(hora_servidor)).total_seconds())
        except (TypeError, ValueError):
            desfase = 0
        if abs(desfase) > 120:
            logger.warning(
                "El reloj de este equipo difiere %s s del servidor central; "
                "ajústelo para que la mezcla por fecha sea exacta",
                desfase,
            )
        return desfase

    def _subir(self, cliente: ClienteSync) -> int:
        """Envía las operaciones pendientes en lotes acotados"""
        enviadas = 0
        restante = max(1, self.config.max_ops_por_ciclo)
        while restante > 0:
            lote = self._tomar_lote(min(100, restante))
            if not lote:
                break
            operaciones = [entrada["operacion"] for entrada in lote]
            identificadores = [entrada["op_id"] for entrada in lote]
            try:
                respuesta = cliente.enviar_ops(operaciones)
            except ErrorSincronizacion:
                self._devolver_a_pendiente(identificadores)
                raise
            self._confirmar_envio(identificadores, respuesta)
            enviadas += len(lote)
            restante -= len(lote)
        return enviadas

    def _tomar_lote(self, limite: int) -> list[dict]:
        """
        Toma operaciones del journal y las marca como en envío

        La marca y la lectura del lote se confirman antes de tocar la red: si
        el proceso muere durante el envío, las operaciones quedan en estado
        «enviando» y el siguiente arranque las devuelve a la cola (el journal es
        la fuente de verdad, nunca la memoria del proceso).
        """
        sesion = self._sesion()
        try:
            filas = (
                sesion.query(JournalOp)
                .filter(
                    JournalOp.estado.in_((PENDIENTE, ENVIANDO)),
                    JournalOp.direccion == DIRECCION_SALIDA,
                )
                .order_by(JournalOp.id)
                .limit(limite)
                .all()
            )
            lote = [
                {"op_id": fila.op_id, "operacion": self._a_operacion(fila)} for fila in filas
            ]
            for fila in filas:
                fila.estado = ENVIANDO
                fila.intentos = int(fila.intentos or 0) + 1
            if filas:
                sesion.commit()
            return lote
        except SQLAlchemyError:
            sesion.rollback()
            logger.warning("No se pudo preparar el lote de envío", exc_info=True)
            return []
        finally:
            self._cerrar(sesion)

    def _a_operacion(self, fila: JournalOp) -> dict:
        """Convierte una fila del journal en operación del protocolo"""
        return {
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

    def _confirmar_envio(self, op_ids: list[str], respuesta: dict) -> None:
        """Marca como confirmadas las operaciones aceptadas por el servidor"""
        if not op_ids:
            return
        aceptadas = self._op_ids_respuesta(respuesta)
        confirmadas: list[str] = []
        sesion = self._sesion()
        try:
            for fila in sesion.query(JournalOp).filter(JournalOp.op_id.in_(op_ids)).all():
                if not aceptadas or fila.op_id in aceptadas:
                    fila.estado = CONFIRMADA
                    fila.error = None
                    confirmadas.append(fila.op_id)
                else:
                    fila.estado = PENDIENTE
                    fila.error = "rechazada por el nodo central"
            for conflicto in respuesta.get("conflictos") or []:
                self._guardar_conflicto_servidor(sesion, conflicto)
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
            logger.warning("No se pudo confirmar el lote enviado", exc_info=True)
            return
        finally:
            self._cerrar(sesion)
        self._registrar_binarios_de(confirmadas)

    @staticmethod
    def _op_ids_respuesta(respuesta: dict) -> set[str]:
        """Identificadores de las operaciones que el servidor dio por aplicadas"""
        aplicadas = respuesta.get("aplicadas")
        if isinstance(aplicadas, list):
            return {str(op) for op in aplicadas}
        return set()

    def _devolver_a_pendiente(self, op_ids: list[str]) -> None:
        """Devuelve a la cola las operaciones marcadas como en envío"""
        if not op_ids:
            return
        sesion = self._sesion()
        try:
            for fila in (
                sesion.query(JournalOp)
                .filter(JournalOp.op_id.in_(op_ids), JournalOp.estado == ENVIANDO)
                .all()
            ):
                fila.estado = PENDIENTE
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
            logger.warning("No se pudo devolver el lote a la cola", exc_info=True)
        finally:
            self._cerrar(sesion)

    def _bajar(self, cliente: ClienteSync) -> int:
        """Descarga y aplica las novedades del nodo central por lotes"""
        aplicadas = 0
        for _ in range(MAX_LOTES_POR_CICLO):
            cursor = self._cursor()
            respuesta = cliente.recibir_ops(cursor, limite=200)
            operaciones = respuesta.get("ops") or []
            if not operaciones:
                break
            aplicadas += self._aplicar_lote(operaciones)
            nuevo_cursor = int(respuesta.get("cursor") or cursor)
            self._guardar_cursor(nuevo_cursor)
            if not respuesta.get("hay_mas"):
                break
        return aplicadas

    def _aplicar_lote(self, operaciones: list[dict]) -> int:
        """Aplica un lote de operaciones remotas (transacción propia)"""
        sesion = self._sesion()
        aplicadas = 0
        try:
            aplicador = AplicadorRemoto(
                sesion,
                dispositivo_local=self.config.dispositivo_id,
                max_bytes_binario=self.config.max_bytes_binario,
            )
            for operacion in operaciones:
                resultado = aplicador.aplicar(operacion)
                if resultado.aplicada:
                    aplicadas += 1
                elif resultado.diferida:
                    self._guardar_diferida(sesion, operacion, resultado.motivo)
                elif resultado.motivo == MOTIVO_ERROR:
                    self._guardar_rechazo(sesion, operacion, resultado.motivo)
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
            logger.error("No se pudo aplicar el lote descargado", exc_info=True)
            return 0
        finally:
            self._cerrar(sesion)
        return aplicadas

    def _guardar_diferida(self, sesion, operacion: dict, motivo: str | None) -> None:
        """Guarda una operación cuya dependencia aún no llegó, para reintentarla"""
        existente = (
            sesion.query(JournalOp).filter(JournalOp.op_id == str(operacion.get("op_id"))).first()
        )
        if existente is not None:
            existente.intentos = int(existente.intentos or 0) + 1
            existente.error = motivo
            if existente.intentos > MAX_INTENTOS_DIFERIDA:
                existente.estado = RECHAZADA
            return
        sesion.add(
            JournalOp(
                op_id=str(operacion.get("op_id")),
                tabla=str(operacion.get("tabla")),
                fila_uuid=str(operacion.get("fila_uuid")),
                operacion=str(operacion.get("operacion")),
                payload=operacion.get("payload") or "{}",
                base_op_id=operacion.get("base_op_id"),
                dispositivo=str(operacion.get("dispositivo") or ""),
                usuario=operacion.get("usuario"),
                creado_en=ahora_utc(),
                estado=DIFERIDA,
                direccion=DIRECCION_ENTRADA,
                intentos=1,
                error=motivo,
            )
        )

    def _guardar_rechazo(self, sesion, operacion: dict, motivo: str | None) -> None:
        """Registra una operación que no se pudo aplicar, para que no se pierda"""
        sesion.add(
            ConflictoSync(
                tabla=str(operacion.get("tabla") or ""),
                fila_uuid=str(operacion.get("fila_uuid") or ""),
                campo="__operacion__",
                valor_local=None,
                valor_remoto=dumps(operacion.get("payload")),
                ganador="local",
                regla=f"operacion_rechazada:{motivo or 'desconocido'}",
                op_remoto_id=operacion.get("op_id"),
                resuelto=0,
            )
        )
        logger.error(
            "Operación rechazada en %s/%s: %s",
            operacion.get("tabla"),
            str(operacion.get("fila_uuid"))[:8],
            motivo,
        )

    def _reintentar_diferidas(self) -> int:
        """Reintenta las operaciones que esperaban a su registro padre"""
        sesion = self._sesion()
        try:
            pendientes = (
                sesion.query(JournalOp)
                .filter(
                    JournalOp.estado == DIFERIDA,
                    JournalOp.direccion == DIRECCION_ENTRADA,
                )
                .order_by(JournalOp.id)
                .limit(50)
                .all()
            )
            if not pendientes:
                return 0
            operaciones = [self._a_operacion(fila) for fila in pendientes]
            for fila in pendientes:
                sesion.delete(fila)
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
            return 0
        finally:
            self._cerrar(sesion)

        aplicadas = self._aplicar_lote(operaciones)
        logger.info("Operaciones diferidas reintentadas: %s de %s", aplicadas, len(operaciones))
        return aplicadas

    # ------------------------------------------------------------------
    # Binarios
    # ------------------------------------------------------------------
    def _mover_binarios(self, cliente: ClienteSync) -> int:
        """Sube y baja los archivos binarios pendientes"""
        movidos = 0
        for pendiente in self._blobs(BLOB_POR_SUBIR, DIRECCION_SALIDA):
            if self._subir_blob(cliente, pendiente):
                movidos += 1
        for pendiente in self._blobs(BLOB_POR_BAJAR, DIRECCION_ENTRADA):
            if self._bajar_blob(cliente, pendiente):
                movidos += 1
        return movidos

    def _blobs(self, estado: str, direccion: str) -> list[dict]:
        """Lista los binarios en un estado concreto (transacción corta)"""
        sesion = self._sesion()
        try:
            filas = (
                sesion.query(BlobSync)
                .filter(BlobSync.estado == estado, BlobSync.direccion == direccion)
                .order_by(BlobSync.creado_en)
                .limit(20)
                .all()
            )
            return [
                {
                    "hash": fila.hash,
                    "tamano": fila.tamano,
                    "tabla": fila.tabla,
                    "fila_uuid": fila.fila_uuid,
                    "columna": fila.columna,
                    "intentos": fila.intentos,
                }
                for fila in filas
            ]
        finally:
            self._cerrar(sesion)

    def _contenido_de_fila(self, tabla: str, fila_uuid: str, columna: str) -> bytes | None:
        """Lee el contenido binario de una fila local"""
        descripcion = registro.ENTIDADES.get(tabla)
        if descripcion is None:
            return None
        sesion = self._sesion()
        try:
            id_local = identidad.id_local_de(sesion, tabla, fila_uuid)
            if id_local is None:
                return None
            fila = sesion.get(descripcion.clase, id_local)
            if fila is None:
                return None
            contenido = getattr(fila, columna, None)
            if contenido is None:
                return None
            return bytes(contenido)
        finally:
            self._cerrar(sesion)

    def _subir_blob(self, cliente: ClienteSync, pendiente: dict) -> bool:
        """Envía un archivo al nodo central y marca su estado"""
        contenido = self._contenido_de_fila(
            pendiente["tabla"], pendiente["fila_uuid"], pendiente["columna"]
        )
        if contenido is None:
            self._marcar_blob(pendiente["hash"], BLOB_SUBIDO)
            return False
        if hash_bytes(contenido) != pendiente["hash"]:
            logger.warning(
                "El contenido de %s/%s cambió antes de subirlo; se subirá en el próximo ciclo",
                pendiente["tabla"],
                pendiente["fila_uuid"][:8],
            )
            return False
        if pendiente["tamano"] > self.config.max_bytes_binario:
            self._marcar_blob(pendiente["hash"], BLOB_SUBIDO)
            logger.warning(
                "El archivo %s (%s bytes) supera el límite y no se transfiere",
                pendiente["hash"][:12],
                pendiente["tamano"],
            )
            return False
        cliente.subir_blob(pendiente["hash"], contenido)
        self._marcar_blob(pendiente["hash"], BLOB_SUBIDO)
        return True

    def _bajar_blob(self, cliente: ClienteSync, pendiente: dict) -> bool:
        """Descarga un archivo del nodo central y lo escribe en su fila"""
        contenido = cliente.bajar_blob(pendiente["hash"])
        if contenido is None:
            self._marcar_blob(pendiente["hash"], BLOB_POR_BAJAR, incrementar=True)
            return False
        if self._escribir_blob(pendiente, contenido):
            self._marcar_blob(pendiente["hash"], BLOB_SUBIDO)
            return True
        return False

    def _escribir_blob(self, pendiente: dict, contenido: bytes) -> bool:
        """Escribe el contenido descargado en la fila, si sigue siendo el vigente"""
        descripcion = registro.ENTIDADES.get(pendiente["tabla"])
        if descripcion is None:
            return False
        sesion = self._sesion()
        try:
            id_local = identidad.id_local_de(sesion, pendiente["tabla"], pendiente["fila_uuid"])
            if id_local is None:
                return False
            fila = sesion.get(descripcion.clase, id_local)
            if fila is None:
                return False

            marca = (
                sesion.query(CampoRemoto)
                .filter(
                    CampoRemoto.tabla == pendiente["tabla"],
                    CampoRemoto.fila_uuid == pendiente["fila_uuid"],
                    CampoRemoto.campo == pendiente["columna"],
                )
                .first()
            )
            if marca is not None:
                vigente = loads(marca.valor)
                if isinstance(vigente, dict) and vigente.get("__blob__") not in (None, pendiente["hash"]):
                    # La fila ya apunta a otro archivo: este llegó tarde
                    logger.info(
                        "Se descarta el archivo %s: la fila apunta a otro contenido",
                        pendiente["hash"][:12],
                    )
                    return True

            with cambios_silenciosos(sesion):
                setattr(fila, pendiente["columna"], contenido)
            sesion.commit()
            return True
        except SQLAlchemyError:
            sesion.rollback()
            logger.warning("No se pudo escribir el archivo descargado", exc_info=True)
            return False
        finally:
            self._cerrar(sesion)

    def _marcar_blob(self, hash_archivo: str, estado: str, incrementar: bool = False) -> None:
        """Actualiza el estado de un binario"""
        sesion = self._sesion()
        try:
            fila = sesion.get(BlobSync, hash_archivo)
            if fila is None:
                return
            fila.estado = estado
            if incrementar:
                fila.intentos = int(fila.intentos or 0) + 1
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
        finally:
            self._cerrar(sesion)

    def _registrar_binarios_de(self, op_ids: list[str]) -> None:
        """Registra para envío los binarios que aparecen en las operaciones confirmadas"""
        if not op_ids:
            return
        sesion = self._sesion()
        try:
            filas = (
                sesion.query(JournalOp)
                .filter(JournalOp.op_id.in_(op_ids))
                .order_by(JournalOp.id)
                .limit(200)
                .all()
            )
            for fila in filas:
                payload = loads(fila.payload) or {}
                for columna, valor in payload.items():
                    if not isinstance(valor, dict) or "__blob__" not in valor:
                        continue
                    hash_archivo = str(valor.get("__blob__"))
                    tamano = int(valor.get("tamano") or 0)
                    if sesion.get(BlobSync, hash_archivo) is not None:
                        continue
                    sesion.add(
                        BlobSync(
                            hash=hash_archivo,
                            tamano=tamano,
                            tabla=fila.tabla,
                            fila_uuid=fila.fila_uuid,
                            columna=columna,
                            direccion=DIRECCION_SALIDA,
                            estado=BLOB_POR_SUBIR,
                        )
                    )
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
        finally:
            self._cerrar(sesion)

    # ------------------------------------------------------------------
    # Mantenimiento y consultas
    # ------------------------------------------------------------------
    def _compactar(self) -> None:
        """Retira del journal las operaciones ya confirmadas hace tiempo"""
        sesion = self._sesion()
        try:
            limite = ahora_utc() - timedelta(days=DIAS_RETENCION_JOURNAL)
            borradas = (
                sesion.query(JournalOp)
                .filter(JournalOp.estado == CONFIRMADA, JournalOp.creado_en < limite)
                .delete(synchronize_session=False)
            )
            if borradas:
                logger.info("Journal compactado: %s operaciones confirmadas retiradas", borradas)
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
        finally:
            self._cerrar(sesion)

    def _contar_pendientes(self) -> int:
        """Operaciones locales pendientes de enviar"""
        sesion = self._sesion()
        try:
            return int(
                sesion.query(JournalOp)
                .filter(JournalOp.estado == PENDIENTE, JournalOp.direccion == DIRECCION_SALIDA)
                .count()
            )
        except SQLAlchemyError:
            return 0
        finally:
            self._cerrar(sesion)

    def _contar_conflictos(self) -> int:
        """Conflictos registrados y no revisados"""
        sesion = self._sesion()
        try:
            return int(sesion.query(ConflictoSync).filter(ConflictoSync.resuelto == 0).count())
        except SQLAlchemyError:
            return 0
        finally:
            self._cerrar(sesion)

    def _cursor(self) -> int:
        """Último ``seq`` global aplicado"""
        sesion = self._sesion()
        try:
            fila = sesion.get(CursorSync, 1)
            return int(fila.ultimo_seq) if fila else 0
        except SQLAlchemyError:
            return 0
        finally:
            self._cerrar(sesion)

    def _guardar_cursor(self, valor: int) -> None:
        """Guarda el avance de la descarga"""
        sesion = self._sesion()
        try:
            fila = sesion.get(CursorSync, 1)
            if fila is None:
                fila = CursorSync(id=1, ultimo_seq=valor)
                sesion.add(fila)
            else:
                fila.ultimo_seq = valor
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
        finally:
            self._cerrar(sesion)

    def _guardar_estado(self, **valores: str) -> None:
        """Persiste el estado operativo para consultas y diagnóstico"""
        sesion = self._sesion()
        try:
            for clave, valor in valores.items():
                fila = sesion.get(EstadoSync, clave)
                if fila is None:
                    sesion.add(EstadoSync(clave=clave, valor=valor))
                else:
                    fila.valor = valor
            sesion.commit()
        except SQLAlchemyError:
            sesion.rollback()
        finally:
            self._cerrar(sesion)

    def _guardar_conflicto_servidor(self, sesion, conflicto: dict) -> None:
        """Guarda un conflicto informado por el nodo central"""
        if not isinstance(conflicto, dict):
            return
        sesion.add(
            ConflictoSync(
                tabla=str(conflicto.get("tabla") or ""),
                fila_uuid=str(conflicto.get("fila_uuid") or ""),
                campo=str(conflicto.get("campo") or ""),
                valor_local=dumps(conflicto.get("valor_local")),
                valor_remoto=dumps(conflicto.get("valor_remoto")),
                ganador=str(conflicto.get("ganador") or "remoto"),
                regla=str(conflicto.get("regla") or "informado_por_el_servidor"),
                op_local_id=conflicto.get("op_local_id"),
                op_remoto_id=conflicto.get("op_remoto_id"),
                resuelto=0,
            )
        )

    # ------------------------------------------------------------------
    # Infraestructura
    # ------------------------------------------------------------------
    @staticmethod
    def _sesion():
        """Sesión independiente para el hilo del agente"""
        from src.config.database import db_config

        return db_config.new_session()

    @staticmethod
    def _cerrar(sesion) -> None:
        """Cierra una sesión sin arrastrar el registry scoped"""
        if sesion is None:
            return
        try:
            sesion.close()
        except Exception:  # pragma: no cover - cierre defensivo
            logger.debug("No se pudo cerrar la sesión del agente", exc_info=True)

    def _publicar(self, **cambios) -> None:
        """Actualiza el estado observable y avisa al notificador"""
        with self._estado_lock:
            self._estado.update(cambios)
            instantanea = dict(self._estado)
        if self.notificador is not None:
            try:
                self.notificador(instantanea)
            except Exception:  # pragma: no cover - el notificador es de la interfaz
                logger.debug("El notificador de la interfaz falló", exc_info=True)

    @staticmethod
    def _registrar_evento(evento: str, detalle: str, correcto: bool = True) -> None:
        """Deja constancia en el registro de auditoría del sistema"""
        try:
            from src.utils.audit_logger import AuditEventType, get_audit_logger

            audit = get_audit_logger()
            if audit:
                audit.log_event(
                    event_type=AuditEventType.SYNC_ACTIVITY,
                    entity_type="sincronizacion",
                    details={"evento": evento, "detalle": detalle},
                    success=correcto,
                )
        except Exception:  # pragma: no cover - la auditoría nunca debe romper el ciclo
            logger.debug("No se pudo registrar el evento de sincronización", exc_info=True)


def uuid_de_operacion() -> str:
    """Identificador nuevo de operación (para utilidades y pruebas)"""
    return nuevo_uuid()
