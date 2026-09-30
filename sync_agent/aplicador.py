"""
Aplicación de operaciones remotas

Este módulo es el único lugar donde una operación que llega de la red se
convierte en cambios sobre la base de datos, y lo usan **tanto el cliente como
el nodo central**: así la mezcla se comporta igual en ambos extremos y no hay
dos implementaciones que puedan divergir.

Garantías que ofrece cada aplicación:

* **Exactamente una vez** (``sync_ops_aplicadas``): reintentar el envío no
  duplica ni reaplica nada.
* **Nada se pisa por llegar tarde**: cada campo se decide con el motor de
  mezcla; el valor perdedor queda en ``sync_conflictos``.
* **Sin ecos**: los cambios se escriben con la captura silenciada, de modo que
  no vuelven a la red como si fueran propios.
* **Sin operaciones a medias**: si falta el registro padre de una clave
  foránea, la operación se difiere entera en lugar de crear una fila coja.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from sync_agent import identidad, merge, registro
from sync_agent.captura import cambios_silenciosos
from sync_agent.comun import (
    ahora_utc,
    descripcion_valor,
    deserializar_valor,
    dumps,
    es_marca_blob,
    hash_bytes,
    hash_de_marca,
    loads,
    tamano_de_marca,
)
from sync_agent.esquema import (
    BLOB_OMITIDO,
    BLOB_POR_BAJAR,
    BlobSync,
    CampoRemoto,
    ConflictoSync,
    OpAplicada,
    VersionFila,
)

logger = logging.getLogger(__name__)

MOTIVO_DUPLICADA = "duplicada"
MOTIVO_DIFERIDA = "diferida_sin_padre"
MOTIVO_TABLA_DESCONOCIDA = "tabla_no_sincronizable"
MOTIVO_SUPERADA = "superada_por_una_escritura_mas_reciente"
MOTIVO_BORRADA = "fila_borrada_en_el_nodo_central"
MOTIVO_ERROR = "error_al_aplicar"


@dataclass
class ResultadoAplicacion:
    """Resultado de aplicar una operación remota"""

    op_id: str = ""
    tabla: str = ""
    fila_uuid: str = ""
    aplicada: bool = False
    diferida: bool = False
    motivo: str | None = None
    conflictos: list[merge.Conflicto] = field(default_factory=list)

    @property
    def resumen(self) -> str:
        """Descripción corta del resultado, para registros y bitácora"""
        estado = "aplicada" if self.aplicada else ("diferida" if self.diferida else "ignorada")
        detalle = f" ({self.motivo})" if self.motivo else ""
        return f"{estado}: {self.tabla}/{self.fila_uuid[:8]}{detalle}"


class AplicadorRemoto:
    """Aplica operaciones del protocolo sobre la base de datos local"""

    def __init__(self, session, dispositivo_local: str, max_bytes_binario: int = 5 * 1024 * 1024):
        """
        Args:
            session: Sesión de base de datos (la confirma quien llama)
            dispositivo_local: Identificador de este equipo
            max_bytes_binario: Tamaño máximo de binario que se transfiere solo
        """
        self.session = session
        self.dispositivo_local = dispositivo_local
        self.max_bytes_binario = max_bytes_binario

    # ------------------------------------------------------------------
    # Entrada principal
    # ------------------------------------------------------------------
    def aplicar(self, operacion: dict) -> ResultadoAplicacion:
        """
        Aplica una operación remota

        Args:
            operacion: Operación del protocolo (dict ya deserializado)

        Returns:
            ResultadoAplicacion con el desenlace y los conflictos detectados
        """
        tabla = str(operacion.get("tabla") or "")
        op_id = str(operacion.get("op_id") or "")
        fila_uuid = str(operacion.get("fila_uuid") or "")
        resultado = ResultadoAplicacion(op_id=op_id, tabla=tabla, fila_uuid=fila_uuid)

        if not registro.es_sincronizable(tabla):
            resultado.motivo = MOTIVO_TABLA_DESCONOCIDA
            logger.warning("Operación rechazada: tabla no sincronizable %r", tabla)
            return resultado

        if self._ya_aplicada(op_id):
            resultado.motivo = MOTIVO_DUPLICADA
            return resultado

        payload = loads(operacion.get("payload")) if isinstance(operacion.get("payload"), str) else operacion.get("payload")
        if not isinstance(payload, dict):
            payload = {}

        try:
            # Un punto de guardado por operación: si una falla (un dato que no
            # cabe en la columna, un padre que falta), se revierte SOLO esa
            # operación y el resto del lote sigue aplicándose. Sin esto, la
            # primera operación mala dejaba la sesión en estado de "rollback
            # pendiente" y hundía el lote entero con un error 500, de modo que
            # una sola fila corrupta bloqueaba la sincronización de todos.
            with self.session.begin_nested():
                with cambios_silenciosos(self.session):
                    if str(operacion.get("operacion")) == "delete":
                        self._aplicar_borrado(operacion, tabla, fila_uuid, resultado)
                    else:
                        self._aplicar_upsert(operacion, tabla, fila_uuid, payload, resultado)
        except SQLAlchemyError:
            logger.error("No se pudo aplicar %s", op_id, exc_info=True)
            resultado.aplicada = False
            resultado.motivo = MOTIVO_ERROR
            return resultado

        if resultado.aplicada:
            self._marcar_aplicada(op_id, tabla)
        self._guardar_conflictos(tabla, fila_uuid, resultado.conflictos)
        return resultado

    # ------------------------------------------------------------------
    # Borrado
    # ------------------------------------------------------------------
    def _aplicar_borrado(
        self, operacion: dict, tabla: str, fila_uuid: str, resultado: ResultadoAplicacion
    ) -> None:
        """Aplica un borrado remoto respetando la semántica de cada tabla"""
        marca = _marca_de(operacion, valor=True)
        version = self._version(tabla, fila_uuid)
        decision, conflicto = merge.decidir_borrado_sobre_actualizacion(version, marca)

        if conflicto is not None:
            resultado.conflictos.append(conflicto)
        if decision != merge.BORRAR:
            if decision == merge.IGNORAR_BORRADO:
                resultado.motivo = MOTIVO_DUPLICADA
            else:
                resultado.motivo = MOTIVO_SUPERADA
            return

        descripcion = registro.ENTIDADES[tabla]
        id_local = identidad.id_local_de(self.session, tabla, fila_uuid)
        fila = self.session.get(descripcion.clase, id_local) if id_local else None

        if fila is not None:
            if descripcion.borrado_logico:
                # El sistema no borra estos registros: los desactiva
                setattr(fila, descripcion.columna_activo, 0)
            else:
                self.session.delete(fila)

        self._actualizar_version(tabla, fila_uuid, marca, borrado=True)
        resultado.aplicada = True

    # ------------------------------------------------------------------
    # Alta y modificación
    # ------------------------------------------------------------------
    def _aplicar_upsert(
        self,
        operacion: dict,
        tabla: str,
        fila_uuid: str,
        payload: dict,
        resultado: ResultadoAplicacion,
    ) -> None:
        """Aplica un alta o modificación remota campo por campo"""
        entrantes = self._marcas_de(operacion, tabla, payload)
        if not entrantes:
            resultado.motivo = MOTIVO_DUPLICADA
            return

        traducido, pendientes = identidad.traducir_payload_a_local(self.session, tabla, payload)
        if pendientes:
            resultado.diferida = True
            resultado.motivo = f"{MOTIVO_DIFERIDA}:{','.join(sorted(pendientes))}"
            return
        entrantes = self._recalcular_entrantes(operacion, tabla, traducido, entrantes)

        fila = self._resolver_fila(tabla, fila_uuid, traducido)
        if fila is None:
            resultado.motivo = MOTIVO_ERROR
            return

        version = self._version(tabla, fila_uuid)
        revivir = False
        if version is not None and version.borrado:
            decision, conflicto = merge.decidir_borrado(version, _marca_de(operacion, valor=None))
            if conflicto is not None:
                resultado.conflictos.append(conflicto)
            if decision == merge.MANTENER_BORRADO:
                resultado.motivo = MOTIVO_BORRADA
                return
            revivir = decision == merge.REVIVIR

        actuales = self._marcas_actuales(tabla, fila_uuid)
        aplicables = self._depurar_binarios(tabla, fila_uuid, fila, entrantes)
        plan = merge.planificar_campos(tabla, fila_uuid, aplicables, actuales)
        resultado.conflictos.extend(plan.conflictos)

        if plan.sin_cambios and not revivir:
            resultado.motivo = MOTIVO_SUPERADA if plan.conflictos else MOTIVO_DUPLICADA
            return

        for campo, marca in plan.marcas.items():
            columna = registro.columna(tabla, campo)
            if columna is None or es_marca_blob(marca.valor):
                # El contenido de un binario llega por el canal de archivos
                continue
            setattr(fila, campo, deserializar_valor(columna, marca.valor))

        if revivir:
            self._revivir(tabla, fila)
        self._registrar_campos(tabla, fila_uuid, plan.marcas)
        self._actualizar_version(tabla, fila_uuid, _marca_de(operacion, valor=None), borrado=False)
        resultado.aplicada = True

    # ------------------------------------------------------------------
    # Resolución de la fila destino
    # ------------------------------------------------------------------
    def _resolver_fila(self, tabla: str, fila_uuid: str, payload: dict):
        """
        Encuentra la fila local que corresponde a una identidad global

        El orden importa: primero la identidad ya conocida; después la clave
        natural (el mismo registro creado en otro equipo se reconoce por su
        cédula, número de contrato o nombre de parámetro) y solo si no existe
        se crea una fila nueva.
        """
        descripcion = registro.ENTIDADES[tabla]
        id_local = identidad.id_local_de(self.session, tabla, fila_uuid)
        if id_local is not None:
            fila = self.session.get(descripcion.clase, id_local)
            if fila is not None:
                return fila

        clave = registro.columna_clave_natural(tabla)
        valor_clave = payload.get(clave) if clave else None
        if clave is None:
            # La tabla no se reconoce por ningún dato: solo cabe crearla.
            pass
        elif valor_clave is None:
            logger.warning(
                "Operación sin clave natural para crear %s/%s; se omite", tabla, fila_uuid[:8]
            )
            return None
        else:
            columna_orm = registro.columna(tabla, clave)
            fila = self.session.query(descripcion.clase).filter(columna_orm == valor_clave).first()
            if fila is not None:
                logger.info(
                    "Se unifica %s por su clave natural %s=%s", tabla, clave, valor_clave
                )
                identidad.registrar(self.session, tabla, fila_uuid, fila.id)
                return fila

        return self._crear_fila(tabla, fila_uuid, payload)

    def _crear_fila(self, tabla: str, fila_uuid: str, payload: dict):
        """Crea la fila local y la vincula a la identidad global"""
        descripcion = registro.ENTIDADES[tabla]
        fila = descripcion.clase()
        for campo, crudo in payload.items():
            columna = registro.columna(tabla, campo)
            if columna is None or es_marca_blob(crudo):
                continue
            setattr(fila, campo, deserializar_valor(columna, crudo))
        self._completar_columnas_locales(tabla, fila_uuid, fila, payload)

        self.session.add(fila)
        try:
            self.session.flush()
        except SQLAlchemyError:
            logger.error(
                "No se pudo crear la fila %s/%s: %s",
                tabla,
                fila_uuid[:8],
                descripcion_valor(payload),
                exc_info=True,
            )
            # La excepción se propaga para que el punto de guardado de
            # ``aplicar`` revierta esta operación: aquí no se puede dejar la
            # sesión a medias sin envenenar el resto del lote.
            raise

        identidad.registrar(self.session, tabla, fila_uuid, fila.id)
        return fila

    @staticmethod
    def _completar_columnas_locales(tabla: str, fila_uuid: str, fila, payload: dict) -> None:
        """
        Rellena las columnas que son locales **pero obligatorias**

        Las rutas de archivo no viajan: ``C:\\...\\documents\\x.pdf`` de otro
        puesto no significa nada en este. Pero la columna no admite nulos, así
        que una fila recibida nunca podría crearse. Se le asigna una ruta dentro
        de la carpeta gestionada de ESTE equipo, junto al nombre del archivo que
        sí viaja, para que el documento quede localizable y la interfaz pueda
        abrirlo (el contenido llega después por el canal de binarios).
        """
        descripcion = registro.ENTIDADES.get(tabla)
        if descripcion is None or not descripcion.columnas_locales:
            return

        from pathlib import Path

        from src.config import settings
        from src.utils.helpers import nombre_archivo_seguro

        for campo in descripcion.columnas_locales:
            columna = registro.columna(tabla, campo)
            if columna is None or columna.nullable:
                continue
            if getattr(fila, campo, None):
                continue
            nombre = payload.get("nombre_archivo") or payload.get("numero") or f"{tabla}.dat"
            limpio = nombre_archivo_seguro(str(nombre)) or f"{tabla}.dat"
            carpeta = settings.photos_path if campo == "foto_ruta" else settings.documents_path
            setattr(fila, campo, str(Path(carpeta) / f"{tabla}_{fila_uuid[:8]}_{limpio}"))

    # ------------------------------------------------------------------
    # Binarios
    # ------------------------------------------------------------------
    def _depurar_binarios(
        self, tabla: str, fila_uuid: str, fila, entrantes: dict[str, merge.Marca]
    ) -> dict[str, merge.Marca]:
        """
        Separa los campos binarios del resto y programa su descarga

        El contenido nunca viaja dentro del payload: aquí solo se registra qué
        hash hace falta. Si el archivo ya está en la fila (mismo hash) o pesa
        más que el límite configurado, no se programa ninguna transferencia.
        """
        descripcion = registro.ENTIDADES[tabla]
        if not descripcion.columnas_blob:
            return entrantes

        aplicables: dict[str, merge.Marca] = {}
        for campo, marca in entrantes.items():
            if campo not in descripcion.columnas_blob:
                aplicables[campo] = marca
                continue
            if not es_marca_blob(marca.valor):
                aplicables[campo] = marca
                continue

            hash_remoto = hash_de_marca(marca.valor)
            tamano = tamano_de_marca(marca.valor)
            contenido_actual = getattr(fila, campo, None)
            if contenido_actual and hash_bytes_local(contenido_actual) == hash_remoto:
                aplicables[campo] = marca
                continue

            if tamano > self.max_bytes_binario:
                self._programar_blob(
                    tabla, fila_uuid, campo, hash_remoto, tamano, BLOB_OMITIDO
                )
                logger.warning(
                    "El archivo de %s/%s (%s bytes) supera el límite; queda pendiente",
                    tabla,
                    fila_uuid[:8],
                    tamano,
                )
            else:
                self._programar_blob(tabla, fila_uuid, campo, hash_remoto, tamano, BLOB_POR_BAJAR)
            aplicables[campo] = marca
        return aplicables

    def _programar_blob(
        self, tabla: str, fila_uuid: str, columna: str, hash_remoto: str | None, tamano: int, estado: str
    ) -> None:
        """Registra (o actualiza) un binario pendiente de transferencia"""
        if not hash_remoto:
            return
        blob = self.session.get(BlobSync, hash_remoto)
        if blob is None:
            self.session.add(
                BlobSync(
                    hash=hash_remoto,
                    tamano=tamano,
                    tabla=tabla,
                    fila_uuid=fila_uuid,
                    columna=columna,
                    direccion="entrada",
                    estado=estado,
                )
            )
            return
        if blob.estado == BLOB_OMITIDO and estado == BLOB_POR_BAJAR:
            blob.estado = estado
        blob.tamano = tamano

    # ------------------------------------------------------------------
    # Estado de mezcla
    # ------------------------------------------------------------------
    def _marcas_de(self, operacion: dict, tabla: str, payload: dict) -> dict[str, merge.Marca]:
        """Construye la marca entrante de cada campo del payload"""
        momento = _momento_de(operacion)
        op_id = str(operacion.get("op_id") or "")
        dispositivo = str(operacion.get("dispositivo") or "")
        return {
            campo: merge.Marca(
                valor=valor,
                op_id=op_id,
                dispositivo=dispositivo,
                actualizado_en=momento,
            )
            for campo, valor in payload.items()
        }

    def _recalcular_entrantes(
        self,
        operacion: dict,
        tabla: str,
        traducido: dict[str, Any],
        entrantes: dict[str, merge.Marca],
    ) -> dict[str, merge.Marca]:
        """Rehace las marcas con las claves foráneas ya traducidas a ids locales"""
        momento = _momento_de(operacion)
        op_id = str(operacion.get("op_id") or "")
        dispositivo = str(operacion.get("dispositivo") or "")
        resultado: dict[str, merge.Marca] = {}
        for campo, marca in entrantes.items():
            valor = traducido.get(campo, marca.valor)
            resultado[campo] = merge.Marca(
                valor=valor, op_id=op_id, dispositivo=dispositivo, actualizado_en=momento
            )
        return resultado

    def _marcas_actuales(self, tabla: str, fila_uuid: str) -> dict[str, merge.Marca]:
        """Última escritura conocida de cada campo de la fila"""
        filas = (
            self.session.query(CampoRemoto)
            .filter(CampoRemoto.tabla == tabla, CampoRemoto.fila_uuid == fila_uuid)
            .all()
        )
        return {
            fila.campo: merge.Marca(
                valor=loads(fila.valor),
                op_id=fila.op_id,
                dispositivo=fila.dispositivo,
                actualizado_en=fila.actualizado_en,
            )
            for fila in filas
        }

    def _registrar_campos(self, tabla: str, fila_uuid: str, marcas: dict[str, merge.Marca]) -> None:
        """Guarda la última escritura de cada campo aplicado"""
        if not marcas:
            return
        existentes = {
            fila.campo: fila
            for fila in self.session.query(CampoRemoto)
            .filter(CampoRemoto.tabla == tabla, CampoRemoto.fila_uuid == fila_uuid)
            .all()
        }
        for campo, marca in marcas.items():
            fila = existentes.get(campo)
            if fila is None:
                self.session.add(
                    CampoRemoto(
                        tabla=tabla,
                        fila_uuid=fila_uuid,
                        campo=campo,
                        valor=dumps(marca.valor),
                        op_id=marca.op_id,
                        dispositivo=marca.dispositivo,
                        actualizado_en=marca.actualizado_en,
                    )
                )
            else:
                fila.valor = dumps(marca.valor)
                fila.op_id = marca.op_id
                fila.dispositivo = marca.dispositivo
                fila.actualizado_en = marca.actualizado_en

    def _version(self, tabla: str, fila_uuid: str) -> merge.VersionFila | None:
        """Estado de mezcla de una fila, en la forma que espera el motor"""
        fila = (
            self.session.query(VersionFila)
            .filter(VersionFila.tabla == tabla, VersionFila.fila_uuid == fila_uuid)
            .first()
        )
        if fila is None:
            return None
        return merge.VersionFila(
            ultimo_op_id=fila.ultimo_op_id,
            actualizado_en=fila.actualizado_en,
            dispositivo=fila.dispositivo,
            borrado=bool(fila.borrado),
            borrado_en=fila.borrado_en,
            borrado_op_id=fila.borrado_op_id,
            borrado_dispositivo=fila.borrado_dispositivo,
        )

    def _actualizar_version(
        self, tabla: str, fila_uuid: str, marca: merge.Marca, borrado: bool
    ) -> None:
        """Actualiza la última operación (o el borrado) de la fila"""
        fila = (
            self.session.query(VersionFila)
            .filter(VersionFila.tabla == tabla, VersionFila.fila_uuid == fila_uuid)
            .first()
        )
        if fila is None:
            fila = VersionFila(tabla=tabla, fila_uuid=fila_uuid)
            self.session.add(fila)

        if borrado:
            fila.borrado = 1
            fila.borrado_en = marca.actualizado_en
            fila.borrado_op_id = marca.op_id
            fila.borrado_dispositivo = marca.dispositivo
        else:
            fila.ultimo_op_id = marca.op_id
            fila.actualizado_en = marca.actualizado_en
            fila.dispositivo = marca.dispositivo
            if fila.borrado:
                fila.borrado = 0

    def _revivir(self, tabla: str, fila) -> None:
        """Devuelve a la vida una fila borrada que recibió una edición posterior"""
        descripcion = registro.ENTIDADES[tabla]
        if descripcion.borrado_logico:
            setattr(fila, descripcion.columna_activo, 1)

    # ------------------------------------------------------------------
    # Idempotencia, conflictos y bitácora
    # ------------------------------------------------------------------
    def _ya_aplicada(self, op_id: str) -> bool:
        """Indica si la operación ya se aplicó en este equipo"""
        if not op_id:
            return False
        return self.session.get(OpAplicada, op_id) is not None

    def _marcar_aplicada(self, op_id: str, tabla: str) -> None:
        """Registra la operación como aplicada (idempotencia)"""
        if not op_id or self.session.get(OpAplicada, op_id) is not None:
            return
        self.session.add(OpAplicada(op_id=op_id, tabla=tabla))

    def _guardar_conflictos(
        self, tabla: str, fila_uuid: str, conflictos: list[merge.Conflicto]
    ) -> None:
        """Guarda en la bandeja los conflictos detectados al aplicar"""
        for conflicto in conflictos:
            self.session.add(
                ConflictoSync(
                    tabla=conflicto.tabla or tabla,
                    fila_uuid=conflicto.fila_uuid or fila_uuid,
                    campo=conflicto.campo,
                    valor_local=dumps(conflicto.valor_local),
                    valor_remoto=dumps(conflicto.valor_remoto),
                    ganador=conflicto.ganador,
                    regla=conflicto.regla,
                    op_local_id=conflicto.op_local_id,
                    op_remoto_id=conflicto.op_remoto_id,
                    resuelto=0,
                )
            )
            logger.info("Conflicto de sincronización: %s", conflicto.resumen)


def hash_bytes_local(contenido: Any) -> str:
    """Hash de un contenido binario almacenado en una columna"""
    if isinstance(contenido, memoryview):
        contenido = contenido.tobytes()
    return hash_bytes(bytes(contenido))


def momento_de_operacion(operacion: dict) -> datetime:
    """Sello de tiempo declarado por una operación (público para el servidor)"""
    return _momento_de(operacion)


def _marca_de(operacion: dict, valor: Any) -> merge.Marca:
    """Marca de la operación completa (para borrados y versiones de fila)"""
    return merge.Marca(
        valor=valor,
        op_id=str(operacion.get("op_id") or ""),
        dispositivo=str(operacion.get("dispositivo") or ""),
        actualizado_en=_momento_de(operacion),
    )


def _momento_de(operacion: dict) -> datetime:
    """Sello de tiempo de la operación, con respaldo si llegó ilegible"""
    crudo = operacion.get("creado_en")
    if isinstance(crudo, datetime):
        return crudo
    try:
        return datetime.fromisoformat(str(crudo))
    except (TypeError, ValueError):
        logger.warning("Operación sin sello de tiempo válido; se usa la hora local")
        return ahora_utc()
