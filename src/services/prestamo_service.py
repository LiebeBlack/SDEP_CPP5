"""
Prestamo Service
Servicio de lógica de negocio para anticipos y préstamos

Administra la solicitud, aprobación y amortización del dinero entregado
al empleado, y resuelve la cuota que corresponde descontar en cada
período de nómina respetando el tope configurado.
"""

import logging
from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import EstadoPrestamo, Prestamo, TipoPrestamo
from src.nomina import (
    ParametrosNomina,
    aplicar_descuento,
    calcular_descuento,
    calcular_monto_cuota,
    cargar_parametros_desde,
    monto_maximo_otorgable,
    plan_de_pagos,
    validar_solicitud,
)
from src.nomina.tipos import CERO, a_decimal, redondear
from src.repositories import ConfiguracionRepository, EmpleadoRepository, PrestamoRepository
from src.utils.audit_logger import AuditEventType, get_audit_logger
from src.utils.helpers import parse_date

logger = logging.getLogger(__name__)

MAX_CUOTAS_DEFECTO = 24


class PrestamoService:
    """Servicio de anticipos y préstamos al empleado"""

    def __init__(self, session: Session):
        self.session = session
        self.repository = PrestamoRepository(session)
        self.empleado_repository = EmpleadoRepository(session)
        self.config_repository = ConfiguracionRepository(session)

    # ------------------------------------------------------------------
    # Parámetros
    # ------------------------------------------------------------------
    def parametros(self) -> ParametrosNomina:
        """Parámetros de nómina vigentes (tope de descuento, cuotas máximas)"""
        return cargar_parametros_desde(self.config_repository.get_valor)

    def max_cuotas(self) -> int:
        """Cantidad máxima de cuotas permitidas"""
        try:
            return int(self.config_repository.get_valor("max_cuotas_prestamo", MAX_CUOTAS_DEFECTO))
        except (SQLAlchemyError, TypeError, ValueError):
            return MAX_CUOTAS_DEFECTO

    # ------------------------------------------------------------------
    # Solicitud y aprobación
    # ------------------------------------------------------------------
    def solicitar(self, datos: dict) -> Prestamo:
        """
        Registra la solicitud de un anticipo o préstamo

        Args:
            datos: empleado_id, monto, numero_cuotas, tipo, motivo y,
                opcionalmente, fecha_solicitud.

        Raises:
            ValueError: Si los datos no son válidos o el empleado no existe
        """
        errores = self.validar_datos_prestamo(datos)
        if errores:
            raise ValueError("; ".join(errores))

        empleado_id = int(datos["empleado_id"])
        empleado = self.empleado_repository.get_by_id(empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")

        monto = redondear(a_decimal(datos["monto"]))
        numero_cuotas = int(datos.get("numero_cuotas") or 1)
        tipo_valor = getattr(datos.get("tipo"), "value", datos.get("tipo")) or TipoPrestamo.PRESTAMO.value
        if tipo_valor == TipoPrestamo.ANTICIPO.value:
            numero_cuotas = 1

        cuota = redondear(monto / numero_cuotas) if numero_cuotas else monto
        fecha_solicitud = datos.get("fecha_solicitud") or date.today()
        if isinstance(fecha_solicitud, str):
            fecha_solicitud = parse_date(fecha_solicitud) or date.today()

        prestamo = Prestamo(
            empleado_id=empleado_id,
            tipo=tipo_valor,
            estado=EstadoPrestamo.SOLICITADO.value,
            monto=monto,
            numero_cuotas=numero_cuotas,
            monto_cuota=calcular_monto_cuota(monto, numero_cuotas) or cuota,
            cuotas_pagadas=0,
            saldo=monto,
            fecha_solicitud=fecha_solicitud,
            motivo=datos.get("motivo"),
            observaciones=datos.get("observaciones"),
        )
        creado = self.repository.create(prestamo)
        self._auditar(creado, "solicitar_prestamo", AuditEventType.DATA_CREATE)
        return creado

    def aprobar(
        self, prestamo_id: int, aprobado_por: str, fecha: date | None = None
    ) -> Prestamo:
        """
        Aprueba una solicitud y la deja lista para descontarse

        Un anticipo de una sola cuota queda activo de inmediato; los
        préstamos de varias cuotas también, porque la amortización se
        controla por cuotas y saldo.
        """
        prestamo = self.repository.get_by_id(prestamo_id)
        if not prestamo:
            raise ValueError("Préstamo no encontrado")
        if prestamo.estado_valor not in (
            EstadoPrestamo.SOLICITADO.value,
            EstadoPrestamo.CANCELADO.value,
        ):
            raise ValueError("El préstamo ya fue aprobado o pagado")

        prestamo.estado = EstadoPrestamo.ACTIVO
        prestamo.fecha_aprobacion = fecha or date.today()
        prestamo.aprobado_por = aprobado_por
        if prestamo.fecha_primer_descuento is None:
            prestamo.fecha_primer_descuento = prestamo.fecha_aprobacion
        if a_decimal(prestamo.saldo) <= CERO:
            prestamo.saldo = prestamo.monto

        actualizado = self.repository.update(prestamo)
        self._auditar(actualizado, "aprobar_prestamo", AuditEventType.DATA_UPDATE)
        return actualizado

    def rechazar(self, prestamo_id: int, motivo: str | None = None) -> Prestamo:
        """Rechaza una solicitud pendiente"""
        return self._cambiar_estado_solicitud(
            prestamo_id, EstadoPrestamo.CANCELADO, motivo, "rechazar_prestamo"
        )

    def cancelar(self, prestamo_id: int, motivo: str | None = None) -> Prestamo:
        """Cancela un préstamo activo (por ejemplo, si se paga por otra vía)"""
        prestamo = self.repository.get_by_id(prestamo_id)
        if not prestamo:
            raise ValueError("Préstamo no encontrado")
        prestamo.estado = EstadoPrestamo.CANCELADO
        if motivo is not None:
            prestamo.observaciones = motivo
        actualizado = self.repository.update(prestamo)
        self._auditar(actualizado, "cancelar_prestamo", AuditEventType.DATA_UPDATE)
        return actualizado

    def _cambiar_estado_solicitud(
        self, prestamo_id: int, estado: EstadoPrestamo, motivo: str | None, operacion: str
    ) -> Prestamo:
        """Cambia el estado de una solicitud registrando el motivo"""
        prestamo = self.repository.get_by_id(prestamo_id)
        if not prestamo:
            raise ValueError("Préstamo no encontrado")
        prestamo.estado = estado
        if motivo is not None:
            prestamo.observaciones = motivo
        actualizado = self.repository.update(prestamo)
        self._auditar(actualizado, operacion, AuditEventType.DATA_UPDATE)
        return actualizado

    def actualizar_prestamo(self, prestamo_id: int, datos: dict) -> Prestamo:
        """Actualiza los datos editables de un préstamo"""
        prestamo = self.repository.get_by_id(prestamo_id)
        if not prestamo:
            raise ValueError("Préstamo no encontrado")

        for campo in ("motivo", "observaciones", "aprobado_por", "tipo", "estado"):
            if campo in datos and datos[campo] is not None:
                valor = getattr(datos[campo], "value", datos[campo])
                setattr(prestamo, campo, valor)

        for campo in ("fecha_aprobacion", "fecha_primer_descuento"):
            if campo in datos and datos[campo] is not None:
                valor = datos[campo]
                if isinstance(valor, str):
                    valor = parse_date(valor)
                setattr(prestamo, campo, valor)

        if "monto" in datos and datos["monto"] is not None:
            prestamo.monto = redondear(a_decimal(datos["monto"]))
            prestamo.saldo = prestamo.monto
        if "numero_cuotas" in datos and datos["numero_cuotas"]:
            prestamo.numero_cuotas = int(datos["numero_cuotas"])
            prestamo.monto_cuota = calcular_monto_cuota(
                a_decimal(prestamo.monto), int(prestamo.numero_cuotas)
            )

        actualizado = self.repository.update(prestamo)
        self._auditar(actualizado, "actualizar_prestamo", AuditEventType.DATA_UPDATE)
        return actualizado

    # ------------------------------------------------------------------
    # Amortización
    # ------------------------------------------------------------------
    def cuota_pendiente(self, empleado_id: int) -> tuple[Prestamo, object] | None:
        """
        Préstamo y cuota que corresponde descontar al empleado

        Returns:
            tuple | None: (préstamo, monto de la cuota) o None si no hay
            nada que descontar.
        """
        prestamo = self.repository.get_siguiente_a_descontar(empleado_id)
        if prestamo is None:
            return None
        pendiente = calcular_descuento_teorico(prestamo)
        if pendiente <= CERO:
            return None
        return prestamo, pendiente

    def descuento_para_pago(
        self, empleado_id: int, neto_estimado: float
    ) -> tuple[Prestamo | None, object]:
        """
        Descuento aplicable en la próxima nómina

        Aplica el tope porcentual configurado sobre el neto estimado para
        no dejar al empleado sin remuneración disponible.
        """
        prestamo = self.repository.get_siguiente_a_descontar(empleado_id)
        if prestamo is None:
            return None, CERO
        parametros = self.parametros()
        monto = calcular_descuento(
            saldo=a_decimal(prestamo.saldo),
            monto_cuota=a_decimal(prestamo.monto_cuota),
            neto_disponible=a_decimal(neto_estimado),
            max_porcentaje=parametros.max_porcentaje_cuota_prestamo,
        )
        return prestamo, monto

    def registrar_descuento(
        self, prestamo_id: int, monto: float, fecha: date | None = None
    ) -> bool:
        """Persiste un descuento aplicado al préstamo"""
        return self.repository.registrar_descuento(prestamo_id, monto, fecha)

    def plan_de_pagos(self, prestamo_id: int) -> list[dict]:
        """Plan de amortización completo de un préstamo"""
        prestamo = self.repository.get_by_id(prestamo_id)
        if not prestamo:
            raise ValueError("Préstamo no encontrado")
        return plan_de_pagos(
            a_decimal(prestamo.monto),
            int(prestamo.numero_cuotas or 1),
            prestamo.fecha_primer_descuento or prestamo.fecha_solicitud,
        )

    def saldo_total(self, empleado_id: int) -> float:
        """Saldo pendiente total de un empleado"""
        return self.repository.get_saldo_total(empleado_id)

    def monto_maximo(self, empleado_id: int, numero_cuotas: int | None = None) -> float:
        """Monto máximo que puede otorgarse a un empleado sin exceder el tope"""
        empleado = self.empleado_repository.get_by_id(empleado_id)
        if not empleado:
            return 0.0
        parametros = self.parametros()
        cuotas = int(numero_cuotas or self.max_cuotas())
        maximo = monto_maximo_otorgable(
            a_decimal(empleado.salario_base),
            cuotas,
            parametros.max_porcentaje_cuota_prestamo,
        )
        return float(maximo)

    def sincronizar_estados(self) -> int:
        """
        Ajusta el estado de los préstamos según su saldo

        Un préstamo con saldo cero queda pagado; uno aprobado con saldo
        pasa a activo, que es el estado que ve la interfaz.
        """
        cambios = 0
        for prestamo in self.repository.get_all(skip=0, limit=None):
            estado = prestamo.estado_valor
            if estado in (EstadoPrestamo.CANCELADO.value, EstadoPrestamo.SOLICITADO.value):
                continue
            esperado = aplicar_descuento(
                saldo=a_decimal(prestamo.saldo),
                cuotas_pagadas=int(prestamo.cuotas_pagadas or 0),
                numero_cuotas=int(prestamo.numero_cuotas or 1),
                descuento=CERO,
                fecha=prestamo.fecha_ultimo_descuento,
            )["estado"]
            if estado != esperado:
                prestamo.estado = EstadoPrestamo.coerce(esperado)
                self.repository.update(prestamo)
                cambios += 1
        return cambios

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def obtener_prestamo(self, prestamo_id: int) -> Prestamo | None:
        return self.repository.get_by_id(prestamo_id)

    def listar_prestamos(self) -> list[Prestamo]:
        return self.repository.get_all(skip=0, limit=None)

    def listar_por_empleado(self, empleado_id: int) -> list[Prestamo]:
        return self.repository.get_by_empleado(empleado_id)

    def listar_activos(self, empleado_id: int | None = None) -> list[Prestamo]:
        return self.repository.get_activos(empleado_id)

    def listar_pendientes_aprobacion(self) -> list[Prestamo]:
        return self.repository.get_pendientes_aprobacion()

    def listar_por_estado(self, estado: str) -> list[Prestamo]:
        return self.repository.get_by_estado(estado)

    def obtener_estadisticas(self) -> dict:
        return self.repository.get_estadisticas()

    # ------------------------------------------------------------------
    # Validación
    # ------------------------------------------------------------------
    def validar_datos_prestamo(self, datos: dict) -> list[str]:
        """
        Valida una solicitud de anticipo o préstamo

        Comprueba los datos básicos y, cuando hay salario, que la cuota no
        supere el tope de descuento configurado.
        """
        errores: list[str] = []

        if not datos.get("empleado_id"):
            errores.append("El empleado es requerido")

        monto = a_decimal(datos.get("monto"))
        numero_cuotas = int(datos.get("numero_cuotas") or 1)
        max_cuotas = self.max_cuotas()
        parametros = self.parametros()

        salario = CERO
        empleado_id = datos.get("empleado_id")
        if empleado_id:
            try:
                empleado = self.empleado_repository.get_by_id(int(empleado_id))
                if empleado is None:
                    errores.append("Empleado no encontrado")
                else:
                    salario = a_decimal(empleado.salario_base)
            except (TypeError, ValueError):
                errores.append("Empleado inválido")

        errores.extend(
            validar_solicitud(
                monto=monto,
                numero_cuotas=numero_cuotas,
                max_cuotas=max_cuotas,
                salario_mensual=salario,
                max_porcentaje=parametros.max_porcentaje_cuota_prestamo,
            )
        )

        saldo_actual = self.repository.get_saldo_total(int(empleado_id)) if empleado_id else 0.0
        if saldo_actual > 0 and salario > 0:
            tope = float(
                redondear(salario * parametros.max_porcentaje_cuota_prestamo / 100)
            )
            if saldo_actual + (float(calcular_monto_cuota(monto, numero_cuotas)) if numero_cuotas else 0) > tope * max(1, numero_cuotas):
                errores.append(
                    "El empleado ya tiene descuentos por préstamo que, sumados a la nueva "
                    "cuota, superan el tope permitido sobre su salario"
                )

        return errores

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _auditar(self, prestamo: Prestamo, operacion: str, event_type: AuditEventType) -> None:
        """Registra la operación del préstamo en la auditoría"""
        try:
            audit = get_audit_logger()
            if not audit:
                return
            audit.log_event(
                event_type=event_type,
                entity_type="prestamo",
                entity_id=prestamo.id,
                user=prestamo.aprobado_por or "system",
                details={
                    "operacion": operacion,
                    "empleado_id": prestamo.empleado_id,
                    "tipo": prestamo.tipo_valor,
                    "estado": prestamo.estado_valor,
                    "monto": float(prestamo.monto or 0),
                    "saldo": float(prestamo.saldo or 0),
                },
                success=True,
            )
        except (SQLAlchemyError, ValueError, TypeError):
            logger.debug("No se pudo auditar la operación de préstamo", exc_info=True)


def calcular_descuento_teorico(prestamo: Prestamo):
    """
    Cuota teórica de un préstamo según su saldo actual

    Se expone como función de módulo para poder reutilizarla sin montar
    todo el servicio.
    """
    from src.nomina import cuota_a_descontar

    return cuota_a_descontar(a_decimal(prestamo.saldo), a_decimal(prestamo.monto_cuota))
