"""
Incidencia Service
Servicio de lógica de negocio para incidencias

Este servicio gestiona el ciclo de vida completo de incidencias,
incluyendo registro, aprobación, rechazo y control de vigencia.
"""

import logging
import os
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import TypeGuard, cast

from sqlalchemy.orm import Session

from src.config import settings
from src.models import EstadoIncidencia, Incidencia, TipoIncidencia
from src.repositories import EmpleadoRepository, IncidenciaRepository
from src.security.contexto import actual
from src.utils.helpers import parse_date_estricto, ruta_dentro_de
from src.utils.security import PermissionChecker

logger = logging.getLogger(__name__)


class IncidenciaService:
    """
    Servicio de gestión de incidencias

    Administra el flujo completo de incidencias desde su registro
    hasta su aprobación o rechazo, incluyendo cálculo automático
    de días y gestión de documentos de soporte.
    """

    def __init__(self, session: Session):
        """
        Inicializa el servicio de incidencias

        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self.session = session
        self.repository = IncidenciaRepository(session)
        self.empleado_repository = EmpleadoRepository(session)

    @staticmethod
    def _ruta_gestionada(ruta: str | None) -> TypeGuard[str]:
        """
        Indica si una ruta pertenece al almacén documental

        La ruta del soporte vive en la base de datos, así que se valida
        antes de leer o borrar el archivo: un registro manipulado no debe
        permitir operaciones sobre rutas ajenas al sistema.

        Se declara ``TypeGuard`` porque la columna puede ser nula: quien
        pregunte queda con una ruta no nula y puede usarla sin repetir la
        comprobación.
        """
        if not ruta:
            return False
        return ruta_dentro_de(settings.documents_path, ruta)

    def crear_incidencia(self, datos: dict, archivo_soporte: bytes | None = None) -> Incidencia:
        """Crea una nueva incidencia"""
        errores = self.validar_datos_incidencia(datos)
        if errores:
            raise ValueError("; ".join(errores))
        datos = dict(datos)
        datos["tipo_incidencia"] = self._normalizar_tipo(datos.get("tipo_incidencia"))
        estado = datos.get("estado", EstadoIncidencia.PENDIENTE)
        try:
            estado = EstadoIncidencia.coerce(estado).value
        except (TypeError, ValueError) as error:
            raise ValueError(f"Estado de incidencia inválido: {error}") from None
        if estado != EstadoIncidencia.PENDIENTE.value:
            raise ValueError("Una incidencia nueva debe iniciar en estado pendiente")
        if any(
            datos.get(campo) is not None
            for campo in (
                "dias_aprobados",
                "fecha_aprobacion",
                "aprobado_por",
                "comentarios_aprobacion",
            )
        ):
            raise ValueError("Los datos de aprobación solo se asignan al aprobar o rechazar")
        empleado_id = int(datos["empleado_id"])
        if self.empleado_repository.get_by_id(empleado_id) is None:
            raise ValueError("Empleado no encontrado")
        afecta_nominas = self._normalizar_afecta_nominas(datos.get("afecta_nominas", 1))
        fecha_inicio = parse_date_estricto(datos.get("fecha_inicio"), "Fecha de inicio")
        fecha_fin = parse_date_estricto(datos.get("fecha_fin"), "Fecha de fin")
        fecha_sol = parse_date_estricto(datos.get("fecha_solicitud"), "Fecha de solicitud")
        fecha_sol = fecha_sol or date.today()
        if fecha_inicio is None or fecha_fin is None:
            raise ValueError("Las fechas de inicio y fin son requeridas")

        # Calcular días solicitados
        dias_solicitados = max(1, (fecha_fin - fecha_inicio).days + 1)
        datos["dias_solicitados"] = dias_solicitados

        # Procesar archivo de soporte
        if archivo_soporte is not None:
            if not isinstance(archivo_soporte, (bytes, bytearray, memoryview)):
                raise ValueError("El soporte debe ser un archivo binario")
            archivo_soporte = bytes(archivo_soporte)
            nombre_soporte = str(datos.get("documento_soporte_nombre") or "soporte.pdf")
            self._validar_archivo_soporte(nombre_soporte, archivo_soporte)
            extension = self._obtener_extension(nombre_soporte)
            nombre_unico = f"soporte_{uuid.uuid4().hex}{extension}"
            ruta_completa = settings.get_document_path(nombre_unico)

            try:
                with open(ruta_completa, "wb") as f:
                    f.write(archivo_soporte)
            except OSError as e:
                logger.error("No se pudo guardar el archivo de soporte", exc_info=True)
                raise OSError(f"No se pudo guardar el archivo de soporte: {e}") from e

            datos["documento_soporte_nombre"] = nombre_unico
            datos["documento_soporte_ruta"] = ruta_completa
            datos["documento_soporte_binario"] = archivo_soporte

        try:
            tipo_inc = datos["tipo_incidencia"]
            if hasattr(tipo_inc, "value"):
                tipo_inc = tipo_inc.value

            incidencia = Incidencia(
                empleado_id=empleado_id,
                tipo_incidencia=tipo_inc,
                estado=estado,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                fecha_solicitud=fecha_sol,
                motivo=str(datos["motivo"]).strip(),
                descripcion=datos.get("descripcion"),
                dias_solicitados=dias_solicitados,
                documento_soporte_nombre=datos.get("documento_soporte_nombre"),
                documento_soporte_ruta=datos.get("documento_soporte_ruta"),
                documento_soporte_binario=datos.get("documento_soporte_binario"),
                afecta_nominas=afecta_nominas,
                observaciones=datos.get("observaciones"),
            )
            return self.repository.create(incidencia)
        except Exception:
            if archivo_soporte is not None and os.path.exists(ruta_completa):
                try:
                    os.remove(ruta_completa)
                except OSError:
                    logger.warning(
                        "No se pudo limpiar el archivo tras fallar la creación de la incidencia: %s",
                        ruta_completa,
                        exc_info=True,
                    )
            raise

    def actualizar_incidencia(
        self, incidencia_id: int, datos: dict, archivo_soporte: bytes | None = None
    ) -> Incidencia:
        """Actualiza una incidencia existente"""
        incidencia = self.repository.get_by_id(incidencia_id)
        if not incidencia:
            raise ValueError("Incidencia no encontrada")

        datos = dict(datos)
        ruta_anterior = incidencia.documento_soporte_ruta
        ruta_nueva = None

        # Los datos de aprobación se modifican exclusivamente por los métodos
        # aprobar/rechazar. La ficha puede reenviar empleado_id y estado, pero
        # solo se aceptan si coinciden con el registro actual.
        for campo_protegido in (
            "dias_aprobados",
            "fecha_aprobacion",
            "aprobado_por",
            "comentarios_aprobacion",
            "dias_solicitados",
            "documento_soporte_ruta",
            "documento_soporte_binario",
        ):
            if campo_protegido in datos:
                raise ValueError(
                    f"El campo {campo_protegido} solo se modifica mediante su flujo autorizado"
                )
        if "empleado_id" in datos:
            try:
                empleado_id_solicitado = int(datos.pop("empleado_id"))
            except (TypeError, ValueError, OverflowError):
                raise ValueError("El empleado de la incidencia no puede modificarse") from None
            if empleado_id_solicitado != incidencia.empleado_id:
                raise ValueError("El empleado de la incidencia no puede modificarse")

        estado_actual = getattr(incidencia.estado, "value", incidencia.estado)

        if estado_actual in (EstadoIncidencia.APROBADO.value, EstadoIncidencia.COMPLETADO.value):
            if archivo_soporte is not None:
                raise ValueError("No se puede sustituir el soporte de una incidencia ya aprobada")
            if "documento_soporte_nombre" in datos:
                nombre_actual = incidencia.documento_soporte_nombre
                if datos["documento_soporte_nombre"] != nombre_actual:
                    raise ValueError("No se puede cambiar el soporte de una incidencia ya aprobada")

        # Normalizar fechas si vienen; un valor inválido nunca se convierte
        # silenciosamente en fecha ausente.
        for campo, etiqueta in (
            ("fecha_inicio", "Fecha de inicio"),
            ("fecha_fin", "Fecha de fin"),
            ("fecha_solicitud", "Fecha de solicitud"),
        ):
            if campo in datos:
                datos[campo] = parse_date_estricto(datos[campo], etiqueta)

        # Si se actualizan las fechas, recalcular días
        if "fecha_inicio" in datos or "fecha_fin" in datos:
            fecha_inicio = datos.get("fecha_inicio", incidencia.fecha_inicio)
            fecha_fin = datos.get("fecha_fin", incidencia.fecha_fin)
            if not fecha_inicio or not fecha_fin:
                raise ValueError("Las fechas de inicio y fin son requeridas")
            if fecha_fin < fecha_inicio:
                raise ValueError("La fecha fin no puede ser anterior a la fecha de inicio")
            if estado_actual not in (
                EstadoIncidencia.APROBADO.value,
                EstadoIncidencia.COMPLETADO.value,
            ):
                datos["dias_solicitados"] = (fecha_fin - fecha_inicio).days + 1

        if estado_actual in (
            EstadoIncidencia.APROBADO.value,
            EstadoIncidencia.COMPLETADO.value,
        ) and ("fecha_inicio" in datos or "fecha_fin" in datos):
            fecha_inicio_final = datos.get("fecha_inicio", incidencia.fecha_inicio)
            fecha_fin_final = datos.get("fecha_fin", incidencia.fecha_fin)
            if (
                fecha_inicio_final != incidencia.fecha_inicio
                or fecha_fin_final != incidencia.fecha_fin
            ):
                raise ValueError(
                    "No se pueden cambiar fechas ni impacto de nómina de una incidencia "
                    "aprobada o completada"
                )

        if "estado" in datos:
            estado_solicitado = getattr(datos["estado"], "value", datos["estado"])
            estado_existente = getattr(incidencia.estado, "value", incidencia.estado)
            if estado_solicitado != estado_existente:
                raise ValueError(
                    "El estado solo se modifica mediante aprobar o rechazar la incidencia"
                )
            datos.pop("estado")
        for campo_protegido in (
            "dias_aprobados",
            "fecha_aprobacion",
            "aprobado_por",
            "comentarios_aprobacion",
        ):
            datos.pop(campo_protegido, None)
        if "tipo_incidencia" in datos:
            datos["tipo_incidencia"] = self._normalizar_tipo(datos["tipo_incidencia"])
        if "afecta_nominas" in datos:
            datos["afecta_nominas"] = self._normalizar_afecta_nominas(datos["afecta_nominas"])

        estado_actual = getattr(incidencia.estado, "value", incidencia.estado)
        if estado_actual in (EstadoIncidencia.APROBADO.value, EstadoIncidencia.COMPLETADO.value):
            fecha_inicio_cambiada = (
                "fecha_inicio" in datos and datos["fecha_inicio"] != incidencia.fecha_inicio
            )
            fecha_fin_cambiada = "fecha_fin" in datos and datos["fecha_fin"] != incidencia.fecha_fin
            nomina_cambiada = (
                "afecta_nominas" in datos and datos["afecta_nominas"] != incidencia.afecta_nominas
            )
            tipo_actual = self._normalizar_tipo(incidencia.tipo_incidencia)
            tipo_cambiado = "tipo_incidencia" in datos and datos["tipo_incidencia"] != tipo_actual
            if fecha_inicio_cambiada or fecha_fin_cambiada or nomina_cambiada or tipo_cambiado:
                raise ValueError(
                    "No se pueden cambiar fechas, tipo ni impacto financiero de una "
                    "incidencia aprobada o completada"
                )

        datos_validacion = {
            "empleado_id": incidencia.empleado_id,
            "tipo_incidencia": datos.get("tipo_incidencia", incidencia.tipo_incidencia),
            "fecha_inicio": datos.get("fecha_inicio", incidencia.fecha_inicio),
            "fecha_fin": datos.get("fecha_fin", incidencia.fecha_fin),
            "motivo": datos.get("motivo", incidencia.motivo),
            "afecta_nominas": datos.get("afecta_nominas", incidencia.afecta_nominas),
        }
        errores = self.validar_datos_incidencia(datos_validacion)
        if errores:
            raise ValueError("; ".join(errores))

        # Guardar el reemplazo antes de modificar la ruta registrada.
        if archivo_soporte is not None:
            if not isinstance(archivo_soporte, (bytes, bytearray, memoryview)):
                raise ValueError("El soporte debe ser un archivo binario")
            archivo_soporte = bytes(archivo_soporte)
            nombre_soporte = str(
                datos.get("documento_soporte_nombre")
                or incidencia.documento_soporte_nombre
                or "soporte.pdf"
            )
            self._validar_archivo_soporte(nombre_soporte, archivo_soporte)
            extension = self._obtener_extension(nombre_soporte)
            nombre_unico = f"soporte_{uuid.uuid4().hex}{extension}"
            ruta_nueva = settings.get_document_path(nombre_unico)

            try:
                with open(ruta_nueva, "wb") as f:
                    f.write(archivo_soporte)
            except OSError as e:
                logger.error("No se pudo guardar el nuevo archivo de soporte", exc_info=True)
                raise OSError(f"No se pudo guardar el nuevo archivo de soporte: {e}") from e

            datos["documento_soporte_nombre"] = nombre_unico
            datos["documento_soporte_ruta"] = ruta_nueva
            datos["documento_soporte_binario"] = archivo_soporte

        try:
            # Actualizar campos
            for campo, valor in datos.items():
                if hasattr(incidencia, campo) and campo not in [
                    "empleado_id",
                    "fecha_aprobacion",
                    "aprobado_por",
                ]:
                    setattr(incidencia, campo, valor)

            actualizado = self.repository.update(incidencia)
        except Exception:
            if ruta_nueva and os.path.exists(ruta_nueva):
                try:
                    os.remove(ruta_nueva)
                except OSError:
                    logger.warning(
                        "No se pudo limpiar el archivo nuevo tras fallar la actualización: %s",
                        ruta_nueva,
                        exc_info=True,
                    )
            raise

        if ruta_nueva and self._ruta_gestionada(ruta_anterior) and os.path.exists(ruta_anterior):
            try:
                os.remove(ruta_anterior)
            except OSError:
                logger.warning(
                    "La incidencia se actualizó, pero no se pudo eliminar el archivo anterior %s",
                    ruta_anterior,
                    exc_info=True,
                )
        return actualizado

    def eliminar_incidencia(self, incidencia_id: int) -> bool:
        """Elimina una incidencia"""
        incidencia = self.repository.get_by_id(incidencia_id)
        if incidencia:
            eliminada = self.repository.delete(incidencia_id)
            if not eliminada:
                return False

            # Borrar el archivo solo después de confirmar la eliminación.
            if self._ruta_gestionada(incidencia.documento_soporte_ruta) and os.path.exists(
                incidencia.documento_soporte_ruta
            ):
                try:
                    os.remove(incidencia.documento_soporte_ruta)
                except OSError:
                    logger.warning(
                        "La incidencia se eliminó, pero no se pudo borrar el archivo de soporte %s",
                        incidencia.documento_soporte_ruta,
                        exc_info=True,
                    )
            return True
        return False

    def obtener_incidencia(self, incidencia_id: int) -> Incidencia | None:
        """Obtiene una incidencia por ID"""
        return self.repository.get_by_id(incidencia_id)

    def listar_incidencias_empleado(self, empleado_id: int) -> list[Incidencia]:
        """Lista incidencias de un empleado"""
        return self.repository.get_by_empleado(empleado_id)

    def listar_todas(self) -> list[Incidencia]:
        """Lista todas las incidencias registradas"""
        return self.repository.get_all(limit=None)

    def listar_por_tipo(self, tipo: str) -> list[Incidencia]:
        """Lista incidencias por tipo"""
        return self.repository.get_by_tipo(tipo)

    def listar_por_estado(self, estado: str) -> list[Incidencia]:
        """Lista incidencias por estado"""
        return self.repository.get_by_estado(estado)

    def listar_pendientes(self) -> list[Incidencia]:
        """Lista incidencias pendientes de aprobación"""
        return self.repository.get_pendientes()

    def listar_vigentes(self) -> list[Incidencia]:
        """Lista incidencias vigentes actualmente"""
        return self.repository.get_vigentes()

    def listar_por_periodo(self, fecha_inicio: date, fecha_fin: date) -> list[Incidencia]:
        """Lista incidencias en un periodo"""
        return self.repository.get_by_periodo(fecha_inicio, fecha_fin)

    @staticmethod
    def _exigir_permiso_aprobacion() -> None:
        """Restringe aprobar/rechazar/completar a quien tenga sesión con permiso.

        Con sesión activa exige el permiso global de gestión: el WORKER solo
        crea y edita sus propias solicitudes, nunca las aprueba. Sin contexto
        (hilos de sistema y pruebas) no hay sesión de usuario que restringir.
        """
        contexto = actual()
        if contexto is not None and not PermissionChecker.has_permission(contexto.rol, "update"):
            raise PermissionError(
                "Se requiere permiso de gestión para aprobar o completar incidencias"
            )

    def aprobar_incidencia(
        self,
        incidencia_id: int,
        aprobado_por: str,
        comentarios: str | None = None,
        dias_aprobados: int | None = None,
    ) -> bool:
        """Aprueba una incidencia con días validados dentro de su duración."""
        self._exigir_permiso_aprobacion()
        incidencia = self.repository.get_by_id(incidencia_id)
        if incidencia is None:
            raise ValueError("Incidencia no encontrada")
        if incidencia.estado != EstadoIncidencia.PENDIENTE.value:
            raise ValueError("Solo se pueden aprobar incidencias pendientes")
        aprobado_por = str(aprobado_por or "").strip()
        if not aprobado_por:
            raise ValueError("Debe indicar quién aprueba la incidencia")
        if len(aprobado_por) > 100:
            raise ValueError("El nombre del aprobador no puede superar 100 caracteres")
        comentarios = self._normalizar_comentarios_aprobacion(comentarios)
        if dias_aprobados is not None:
            from src.utils.helpers import parse_int_estricto

            try:
                dias_aprobados = parse_int_estricto(dias_aprobados, "Días aprobados")
            except ValueError as error:
                raise ValueError(str(error)) from None
            if dias_aprobados is None:
                raise ValueError("Los días aprobados deben ser un número entero")
            if not 1 <= dias_aprobados <= incidencia.dias_solicitados:
                raise ValueError(
                    f"Los días aprobados deben estar entre 1 y {incidencia.dias_solicitados}"
                )
        actualizado = self.repository.aprobar(
            incidencia_id, aprobado_por, comentarios, dias_aprobados
        )
        if not actualizado:
            raise ValueError(
                "No se pudo aprobar: la incidencia cambió de estado o no pudo guardarse"
            )
        return True

    def rechazar_incidencia(
        self, incidencia_id: int, rechazado_por: str, comentarios: str | None = None
    ) -> bool:
        """Rechaza una incidencia pendiente."""
        self._exigir_permiso_aprobacion()
        incidencia = self.repository.get_by_id(incidencia_id)
        if incidencia is None:
            raise ValueError("Incidencia no encontrada")
        if incidencia.estado != EstadoIncidencia.PENDIENTE.value:
            raise ValueError("Solo se pueden rechazar incidencias pendientes")
        rechazado_por = str(rechazado_por or "").strip()
        if not rechazado_por:
            raise ValueError("Debe indicar quién rechaza la incidencia")
        if len(rechazado_por) > 100:
            raise ValueError("El nombre de quien rechaza no puede superar 100 caracteres")
        comentarios = self._normalizar_comentarios_aprobacion(comentarios)
        actualizado = self.repository.rechazar(incidencia_id, rechazado_por, comentarios)
        if not actualizado:
            raise ValueError(
                "No se pudo rechazar: la incidencia cambió de estado o no pudo guardarse"
            )
        return True

    def completar_incidencia(self, incidencia_id: int) -> bool:
        """Marca como completada una incidencia previamente aprobada."""
        self._exigir_permiso_aprobacion()
        incidencia = self.repository.get_by_id(incidencia_id)
        if incidencia is None:
            raise ValueError("Incidencia no encontrada")
        if incidencia.estado != EstadoIncidencia.APROBADO.value:
            raise ValueError("Solo se pueden completar incidencias aprobadas")
        if not self.repository.completar(incidencia_id):
            raise ValueError(
                "No se pudo completar: la incidencia cambió de estado o no pudo guardarse"
            )
        return True

    def obtener_soporte(self, incidencia_id: int) -> bytes | None:
        """Obtiene el archivo de soporte de una incidencia"""
        incidencia = self.repository.get_by_id(incidencia_id)
        if incidencia:
            if incidencia.documento_soporte_binario:
                return cast(bytes, incidencia.documento_soporte_binario)
            elif self._ruta_gestionada(incidencia.documento_soporte_ruta) and os.path.exists(
                incidencia.documento_soporte_ruta
            ):
                with open(incidencia.documento_soporte_ruta, "rb") as f:
                    return f.read()
        return None

    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas de incidencias"""
        return {
            "total": self.repository.count(),
            "pendientes": len(self.repository.get_pendientes()),
            "vigentes": len(self.repository.get_vigentes()),
            "por_tipo": self.repository.get_estadisticas_por_tipo(),
            "por_estado": self.repository.get_estadisticas_por_estado(),
        }

    def calcular_dias_incidencias_periodo(
        self, empleado_id: int, fecha_inicio: date, fecha_fin: date
    ) -> int:
        """Calcula los días de incidencias que afectan nómina de un empleado en un periodo"""
        inicio = parse_date_estricto(fecha_inicio, "Periodo de inicio")
        fin = parse_date_estricto(fecha_fin, "Periodo de fin")
        if inicio is None or fin is None:
            return 0
        if fin < inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")

        incidencias = self.repository.get_by_empleado_periodo(empleado_id, inicio, fin)
        rangos: list[tuple[date, date]] = []
        for incidencia in incidencias:
            # Cuentan aprobadas y completadas. Fusionar rangos evita descontar
            # dos veces los mismos días cuando hay incidencias superpuestas.
            estado = getattr(incidencia.estado, "value", incidencia.estado)
            if (
                estado not in (EstadoIncidencia.APROBADO.value, EstadoIncidencia.COMPLETADO.value)
                or getattr(incidencia, "afecta_nominas", 1) != 1
            ):
                continue

            inc_ini = parse_date_estricto(incidencia.fecha_inicio, "Fecha de inicio de incidencia")
            inc_fin = parse_date_estricto(incidencia.fecha_fin, "Fecha de fin de incidencia")
            if inc_ini is None or inc_fin is None:
                raise ValueError("Una incidencia aprobada no tiene un rango de fechas válido")
            dias_autorizados = incidencia.dias_aprobados
            if dias_autorizados is None:
                # Compatibilidad con registros aprobados antes de persistir
                # los días autorizados: en esos casos se usa la duración pedida.
                dias_autorizados = incidencia.dias_solicitados
            try:
                dias_autorizados = int(dias_autorizados)
            except (TypeError, ValueError, OverflowError):
                raise ValueError(
                    "Una incidencia aprobada tiene una cantidad de días autorizados inválida"
                ) from None
            duracion_solicitada = (inc_fin - inc_ini).days + 1
            dias_autorizados = min(max(0, dias_autorizados), duracion_solicitada)
            if dias_autorizados == 0:
                continue

            # Se autorizan los primeros N días desde la fecha solicitada.
            # El rango autorizado se recorta antes de intersectarlo con el
            # período para que nómina no descuente días no aprobados.
            fin_autorizado = min(inc_fin, inc_ini + timedelta(days=dias_autorizados - 1))
            rango_ini = max(inc_ini, inicio)
            rango_fin = min(fin_autorizado, fin)
            if rango_fin >= rango_ini:
                rangos.append((rango_ini, rango_fin))

        if not rangos:
            return 0

        rangos.sort(key=lambda rango: rango[0])
        dias_totales = 0
        inicio_actual, fin_actual = rangos[0]
        for siguiente_inicio, siguiente_fin in rangos[1:]:
            if siguiente_inicio <= fin_actual + timedelta(days=1):
                fin_actual = max(fin_actual, siguiente_fin)
                continue
            dias_totales += (fin_actual - inicio_actual).days + 1
            inicio_actual, fin_actual = siguiente_inicio, siguiente_fin
        dias_totales += (fin_actual - inicio_actual).days + 1
        return dias_totales

    @staticmethod
    def _normalizar_comentarios_aprobacion(comentarios: str | None) -> str | None:
        """Normaliza comentarios de aprobación y evita entradas desmesuradas."""
        if comentarios is None:
            return None
        texto = str(comentarios).strip()
        if len(texto) > 2000:
            raise ValueError("Los comentarios de aprobación no pueden superar 2000 caracteres")
        return texto or None

    @staticmethod
    def _normalizar_tipo(valor: object) -> str:
        """Convierte el tipo de incidencia a un valor permitido del dominio."""
        try:
            return TipoIncidencia.coerce(valor).value
        except (TypeError, ValueError):
            raise ValueError("El tipo de incidencia no es válido") from None

    @staticmethod
    def _normalizar_afecta_nominas(valor: object) -> int:
        """Normaliza la bandera de impacto en nómina a 0 o 1."""
        if isinstance(valor, bool):
            return int(valor)
        try:
            texto = str(valor).strip()
            if texto not in {"0", "1"}:
                raise ValueError
            normalizado = int(texto)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("La opción afecta nómina debe ser 0 o 1") from None
        if normalizado not in (0, 1):
            raise ValueError("La opción afecta nómina debe ser 0 o 1")
        return normalizado

    @staticmethod
    def _validar_archivo_soporte(nombre_archivo: str, contenido: bytes) -> None:
        """Valida tipo, nombre y tamaño del soporte antes de escribirlo."""
        from src.utils.security import SecurityValidator

        extensiones = (
            SecurityValidator.ALLOWED_IMAGE_EXTENSIONS
            | SecurityValidator.ALLOWED_DOCUMENT_EXTENSIONS
        )
        nombre = Path(nombre_archivo).name
        extension = Path(nombre).suffix.lower()
        if extension not in extensiones or not SecurityValidator.validate_filename(nombre):
            raise ValueError("Nombre o extensión de soporte no permitidos")
        if not SecurityValidator.validate_file_size(len(contenido)):
            raise ValueError("El soporte debe tener contenido y no superar 50 MB")

    def _obtener_extension(self, nombre_archivo: str) -> str:
        """Obtiene la extensión de un archivo"""
        if "." in nombre_archivo:
            return nombre_archivo[nombre_archivo.rfind(".") :].lower()
        return ""

    def validar_datos_incidencia(self, datos: dict) -> list[str]:
        """Valida los datos de una incidencia"""

        errores = []

        # Validaciones requeridas
        campos_requeridos = [
            "empleado_id",
            "tipo_incidencia",
            "fecha_inicio",
            "fecha_fin",
            "motivo",
        ]
        for campo in campos_requeridos:
            valor = datos.get(campo)
            falta_valor = valor is None or (isinstance(valor, str) and not valor.strip())
            if campo not in datos or falta_valor:
                errores.append(f"El campo {campo} es requerido")

        tipo = datos.get("tipo_incidencia")
        if tipo:
            try:
                self._normalizar_tipo(tipo)
            except ValueError as error:
                errores.append(str(error))

        motivo = datos.get("motivo")
        if motivo is not None and len(str(motivo).strip()) > 2000:
            errores.append("El motivo no puede superar 2000 caracteres")

        # Validaciones específicas
        fechas: dict[str, date | None] = {}
        for campo, etiqueta in (
            ("fecha_inicio", "Fecha de inicio"),
            ("fecha_fin", "Fecha de fin"),
        ):
            try:
                fechas[campo] = parse_date_estricto(datos.get(campo), etiqueta)
            except ValueError as error:
                errores.append(str(error))
                fechas[campo] = None
        f_ini = fechas["fecha_inicio"]
        f_fin = fechas["fecha_fin"]
        if f_ini and f_fin and f_fin < f_ini:
            errores.append("La fecha fin no puede ser anterior a la fecha inicio")

        if "empleado_id" in datos:
            from src.utils.helpers import parse_int_estricto

            try:
                empleado_id = parse_int_estricto(datos["empleado_id"], "ID de empleado")
                if empleado_id is None or empleado_id <= 0:
                    errores.append("El ID de empleado debe ser positivo")
            except ValueError as error:
                errores.append(str(error))

        if "afecta_nominas" in datos:
            try:
                self._normalizar_afecta_nominas(datos["afecta_nominas"])
            except ValueError as error:
                errores.append(str(error))

        return errores
