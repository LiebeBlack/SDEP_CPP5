"""
Pago Service
Servicio de lógica de negocio para pagos y nómina

Este servicio maneja el procesamiento de nóminas, cálculo de deducciones,
generación de pagos y emisión de recibos, integrándose con incidencias
para el cálculo de días trabajados.
"""

import logging
from datetime import date

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Pago, Prestamo, TipoPago, MetodoPago
from src.nomina import (
    DeduccionesManuales,
    EntradaNomina,
    HorasExtra,
    ParametrosNomina,
    ResultadoNomina,
    calcular_nomina,
    cargar_parametros_desde,
    validar_parametros,
)
from src.nomina.tipos import CERO, a_decimal, redondear
from src.repositories import (
    AsistenciaRepository,
    ConfiguracionRepository,
    EmpleadoRepository,
    PagoRepository,
    PrestamoRepository,
)
from src.utils.helpers import parse_date

logger = logging.getLogger(__name__)


class PagoService:
    """
    Servicio de gestión de pagos y nómina

    Procesa nóminas automáticas, calcula deducciones según configuración,
    genera recibos de pago y mantiene el control de pagos pendientes
    y realizados.
    """

    def __init__(self, session: Session):
        """
        Inicializa el servicio de pagos

        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self.session = session
        self.pago_repository = PagoRepository(session)
        self.empleado_repository = EmpleadoRepository(session)
        self.config_repository = ConfiguracionRepository(session)
        self.prestamo_repository = PrestamoRepository(session)
        self.asistencia_repository = AsistenciaRepository(session)

    def crear_pago(self, datos: dict) -> Pago:
        """
        Crea un nuevo pago calculando deducciones y montos netos

        El cálculo lo realiza el motor de nómina (src/nomina). En la
        modalidad porcentual se reproduce exactamente el cálculo
        histórico del sistema; en la modalidad por tramos se aplican los
        techos de cotización, los aportes patronales y la tabla
        progresiva de ISR. Las deducciones capturadas explícitamente para
        un pago concreto siempre tienen prioridad sobre el cálculo.
        """
        periodo_inicio, periodo_fin, fecha_pago = self._normalizar_fechas_pago(datos)

        salario_base = round(float(datos["salario_base"]), 2)
        horas_extra_desglosadas = self._horas_extra(datos)
        resultado = self.calcular_con_motor(
            salario_base=salario_base,
            datos=datos,
            horas_extra=horas_extra_desglosadas,
        )

        # El monto de horas extra capturado a mano manda cuando no se
        # clasificaron horas por tipo (comportamiento histórico).
        monto_horas_extra = (
            float(resultado.monto_horas_extra)
            if horas_extra_desglosadas.hay_horas
            else round(float(datos.get("horas_extra", 0) or 0), 2)
        )

        deduccion_seguro = float(resultado.deduccion_seguro)
        deduccion_pension = float(resultado.deduccion_pension)
        deduccion_impuesto = float(resultado.deduccion_impuesto)
        otras_deducciones = float(resultado.otras_deducciones)
        descuentos = float(resultado.descuentos)
        deduccion_prestamo = float(resultado.deduccion_prestamo)
        bonificaciones = float(resultado.bonificaciones)
        aguinaldo = float(resultado.aguinaldo)
        bono_vacacional = float(resultado.bono_vacacional)

        total_deducciones = round(
            deduccion_seguro
            + deduccion_pension
            + deduccion_impuesto
            + otras_deducciones
            + deduccion_prestamo,
            2,
        )

        monto_bruto = round(
            salario_base + bonificaciones + monto_horas_extra + aguinaldo + bono_vacacional, 2
        )
        monto_neto = round(max(0.0, monto_bruto - total_deducciones - descuentos), 2)

        tipo_p = datos["tipo_pago"]
        if hasattr(tipo_p, "value"):
            tipo_p = tipo_p.value

        metodo_p = datos.get("metodo_pago", MetodoPago.TRANSFERENCIA.value)
        if hasattr(metodo_p, "value"):
            metodo_p = metodo_p.value

        empleado_id = int(datos["empleado_id"])
        ref_pago = datos.get("referencia_pago") or self._referencia_por_defecto(
            empleado_id, periodo_inicio
        )

        pago = Pago(
            empleado_id=empleado_id,
            tipo_pago=tipo_p,
            metodo_pago=metodo_p,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            fecha_pago=fecha_pago,
            monto_bruto=monto_bruto,
            monto_neto=monto_neto,
            descuentos=descuentos,
            bonificaciones=bonificaciones,
            horas_extra=monto_horas_extra,
            salario_base=salario_base,
            deduccion_seguro=deduccion_seguro,
            deduccion_pension=deduccion_pension,
            deduccion_impuesto=deduccion_impuesto,
            otras_deducciones=otras_deducciones,
            modalidad_calculo=resultado.modalidad,
            base_gravable=float(resultado.base_gravable),
            horas_extra_diurnas=float(resultado.horas_extra.diurnas),
            horas_extra_nocturnas=float(resultado.horas_extra.nocturnas),
            horas_extra_feriadas=float(resultado.horas_extra.feriadas),
            deduccion_prestamo=deduccion_prestamo,
            aguinaldo=aguinaldo,
            bono_vacacional=bono_vacacional,
            aporte_seguro_patronal=float(resultado.aporte_seguro_patronal),
            aporte_pension_patronal=float(resultado.aporte_pension_patronal),
            isr_tramo=resultado.isr_tramo,
            prestamo_id=self._prestamo_id(datos),
            descripcion=datos.get("descripcion"),
            referencia_pago=ref_pago,
            observaciones=datos.get("observaciones"),
            pagado=int(datos.get("pagado", 0)),
        )

        creado = self.pago_repository.create(pago)
        if creado.prestamo_id and deduccion_prestamo > 0:
            self._registrar_descuento_prestamo(creado)
        return creado

    # ------------------------------------------------------------------
    # Motor de nómina
    # ------------------------------------------------------------------
    def parametros_nomina(self) -> ParametrosNomina:
        """Parámetros de cálculo vigentes según la configuración del sistema"""
        try:
            return cargar_parametros_desde(self.config_repository.get_valor)
        except (ValueError, TypeError):
            logger.warning(
                "No se pudieron leer los parámetros de nómina; se usan los valores por defecto",
                exc_info=True,
            )
            return cargar_parametros_desde(lambda clave, por_defecto: por_defecto)

    def validar_parametros_nomina(self) -> list[str]:
        """Revisa la coherencia de los parámetros de nómina configurados"""
        return validar_parametros(self.parametros_nomina())

    def calcular_con_motor(
        self,
        salario_base: float,
        datos: dict | None = None,
        horas_extra: HorasExtra | None = None,
    ) -> ResultadoNomina:
        """
        Calcula un pago con el motor de nómina sin persistirlo

        Útil para la vista previa de la interfaz y para generar recibos
        sin crear registros.
        """
        datos = datos or {}
        return calcular_nomina(
            EntradaNomina(
                salario_base=a_decimal(salario_base),
                horas_extra=horas_extra or HorasExtra(),
                bonificaciones=a_decimal(datos.get("bonificaciones")),
                otras_deducciones=a_decimal(datos.get("otras_deducciones")),
                descuentos=a_decimal(datos.get("descuentos")),
                aguinaldo=a_decimal(datos.get("aguinaldo")),
                bono_vacacional=a_decimal(datos.get("bono_vacacional")),
                cuota_prestamo=a_decimal(
                    datos.get("deduccion_prestamo") or datos.get("cuota_prestamo")
                ),
                dias_trabajados=int(datos.get("dias_trabajados") or 30),
                dias_periodo=int(datos.get("dias_periodo") or 30),
                prorratear=bool(datos.get("prorratear")),
                deducciones_manuales=self._deducciones_manuales(datos),
            ),
            self.parametros_nomina(),
        )

    def previsualizar_deducciones(self, salario_base: float) -> dict:
        """
        Deducciones que corresponderían a un salario con los parámetros vigentes

        Permite mostrar en pantalla, antes de guardar, cuánto se
        descontaría; es el mismo cálculo que aplica crear_pago.
        """
        resultado = self.calcular_con_motor(salario_base)
        seguro, pension, impuesto = self._resolver_deducciones({}, salario_base)
        return {
            "modalidad": resultado.modalidad,
            "deduccion_seguro": seguro,
            "deduccion_pension": pension,
            "deduccion_impuesto": impuesto,
            "total_deducciones": float(resultado.total_deducciones),
            "monto_neto": float(resultado.monto_neto),
            "base_gravable": float(resultado.base_gravable),
            "isr_tramo": resultado.isr_tramo,
        }

    @staticmethod
    def _horas_extra(datos: dict) -> HorasExtra:
        """Desglose de horas extra clasificadas, si el usuario las capturó así"""
        diurnas = a_decimal(datos.get("horas_extra_diurnas"))
        nocturnas = a_decimal(datos.get("horas_extra_nocturnas"))
        feriadas = a_decimal(datos.get("horas_extra_feriadas"))
        if diurnas <= 0 and nocturnas <= 0 and feriadas <= 0:
            return HorasExtra()
        return HorasExtra(diurnas=diurnas, nocturnas=nocturnas, feriadas=feriadas)

    @staticmethod
    def _deducciones_manuales(datos: dict) -> DeduccionesManuales | None:
        """Deducciones capturadas a mano que deben prevalecer sobre el cálculo"""
        seguro = datos.get("deduccion_seguro")
        pension = datos.get("deduccion_pension")
        impuesto = datos.get("deduccion_impuesto")
        if seguro is None and pension is None and impuesto is None:
            return None
        return DeduccionesManuales(
            seguro=a_decimal(seguro) if seguro is not None else None,
            pension=a_decimal(pension) if pension is not None else None,
            impuesto=a_decimal(impuesto) if impuesto is not None else None,
        )

    @staticmethod
    def _prestamo_id(datos: dict) -> int | None:
        """Identificador de préstamo asociado al pago, si se indicó"""
        valor = datos.get("prestamo_id")
        if valor in (None, ""):
            return None
        try:
            return int(valor)
        except (TypeError, ValueError):
            return None

    def _registrar_descuento_prestamo(self, pago: Pago) -> bool:
        """Aplica al préstamo la cuota descontada en un pago"""
        from src.services.prestamo_service import PrestamoService

        prestamo_id = pago.prestamo_id
        if prestamo_id is None:
            return False
        servicio = PrestamoService(self.session)
        return servicio.registrar_descuento(
            int(prestamo_id), float(pago.deduccion_prestamo or 0), pago.fecha_pago
        )

    def aplicar_cuota_prestamo(self, pago: Pago, prestamo_id: int | None = None) -> bool:
        """
        Descuenta en un pago la cuota del préstamo activo del empleado

        Busca la cuota pendiente (o el préstamo indicado), la recorta al
        tope configurado sobre el neto y actualiza tanto el pago como el
        saldo del préstamo. Devuelve False si no había nada que descontar.
        """
        from src.services.prestamo_service import PrestamoService

        if pago is None or not pago.empleado_id:
            return False
        servicio = PrestamoService(self.session)
        prestamo: Prestamo | None
        cuota: object = 0
        if prestamo_id is not None:
            prestamo = servicio.obtener_prestamo(int(prestamo_id))
            if prestamo is not None:
                cuota = prestamo.monto_cuota
        else:
            prestamo, cuota = servicio.descuento_para_pago(
                pago.empleado_id, float(pago.monto_neto or 0)
            )
        descuento = redondear(a_decimal(cuota))
        if prestamo is None or descuento <= 0:
            return False

        # Las columnas monetarias son Numeric: se escriben en Decimal para
        # no perder precisión al pasar por float.
        neto = redondear(
            max(
                CERO,
                a_decimal(pago.monto_bruto)
                - a_decimal(pago.total_deducciones)
                - a_decimal(pago.descuentos),
            )
        )
        pago.prestamo_id = prestamo.id
        pago.deduccion_prestamo = descuento
        pago.monto_neto = neto
        self.pago_repository.update(pago)
        servicio.registrar_descuento(prestamo.id, float(descuento), pago.fecha_pago)
        return True

    @staticmethod
    def _normalizar_fechas_pago(datos: dict) -> tuple[date | None, date | None, date]:
        """Resuelve periodo de inicio/fin y fecha de pago (hoy por defecto)"""
        periodo_inicio = datos["periodo_inicio"]
        if isinstance(periodo_inicio, str):
            periodo_inicio = parse_date(periodo_inicio)

        periodo_fin = datos["periodo_fin"]
        if isinstance(periodo_fin, str):
            periodo_fin = parse_date(periodo_fin)

        fecha_pago = datos.get("fecha_pago")
        if isinstance(fecha_pago, str):
            fecha_pago = parse_date(fecha_pago) or date.today()
        elif not fecha_pago:
            fecha_pago = date.today()

        return periodo_inicio, periodo_fin, fecha_pago

    def _resolver_deducciones(self, datos: dict, salario_base: float) -> tuple[float, float, float]:
        """
        Deducciones del pago: las capturadas a mano o las calculadas

        Delega en el motor de nómina, que ya distingue entre el cálculo
        porcentual histórico y el cálculo por tramos, y respeta las
        deducciones explícitas si vienen en los datos.
        """
        resultado = self.calcular_con_motor(salario_base, datos)
        return (
            round(float(resultado.deduccion_seguro), 2),
            round(float(resultado.deduccion_pension), 2),
            round(float(resultado.deduccion_impuesto), 2),
        )

    @staticmethod
    def _referencia_por_defecto(empleado_id: int, periodo_inicio: date | None) -> str:
        """Referencia REC-<empleado>-<yyyymmdd> cuando no se proporciona una"""
        fecha = periodo_inicio.strftime("%Y%m%d") if periodo_inicio else "00"
        return f"REC-{empleado_id}-{fecha}"

    def actualizar_pago(self, pago_id: int, datos: dict) -> Pago:
        """Actualiza un pago existente"""
        from src.utils.helpers import parse_date

        pago = self.pago_repository.get_by_id(pago_id)
        if not pago:
            raise ValueError("Pago no encontrado")

        # Normalizar fechas si vienen en datos
        for f_campo in ["periodo_inicio", "periodo_fin", "fecha_pago"]:
            if f_campo in datos and isinstance(datos[f_campo], str):
                datos[f_campo] = parse_date(datos[f_campo])

        # Recalcular montos si se modifican los componentes
        recalcular = any(
            campo in datos
            for campo in [
                "salario_base",
                "bonificaciones",
                "horas_extra",
                "descuentos",
                "deduccion_seguro",
                "deduccion_pension",
                "deduccion_impuesto",
                "otras_deducciones",
            ]
        )

        if recalcular:
            salario_base = round(float(datos.get("salario_base", pago.salario_base) or 0), 2)
            bonificaciones = round(float(datos.get("bonificaciones", pago.bonificaciones) or 0), 2)
            horas_extra = round(float(datos.get("horas_extra", pago.horas_extra) or 0), 2)
            descuentos = round(float(datos.get("descuentos", pago.descuentos) or 0), 2)

            deduccion_seguro = round(
                float(datos.get("deduccion_seguro", pago.deduccion_seguro) or 0), 2
            )
            deduccion_pension = round(
                float(datos.get("deduccion_pension", pago.deduccion_pension) or 0), 2
            )
            deduccion_impuesto = round(
                float(datos.get("deduccion_impuesto", pago.deduccion_impuesto) or 0), 2
            )
            otras_deducciones = round(
                float(datos.get("otras_deducciones", pago.otras_deducciones) or 0), 2
            )

            total_deducciones = round(
                deduccion_seguro + deduccion_pension + deduccion_impuesto + otras_deducciones, 2
            )
            monto_bruto = round(salario_base + bonificaciones + horas_extra, 2)
            monto_neto = round(max(0.0, monto_bruto - total_deducciones - descuentos), 2)

            datos["monto_bruto"] = monto_bruto
            datos["monto_neto"] = monto_neto

        if "tipo_pago" in datos and hasattr(datos["tipo_pago"], "value"):
            datos["tipo_pago"] = datos["tipo_pago"].value
        if "metodo_pago" in datos and hasattr(datos["metodo_pago"], "value"):
            datos["metodo_pago"] = datos["metodo_pago"].value

        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(pago, campo) and campo not in ["empleado_id"]:
                setattr(pago, campo, valor)

        return self.pago_repository.update(pago)

    def eliminar_pago(self, pago_id: int) -> bool:
        """Elimina un pago"""
        return self.pago_repository.delete(pago_id)

    def obtener_pago(self, pago_id: int) -> Pago | None:
        """Obtiene un pago por ID"""
        return self.pago_repository.get_by_id(pago_id)

    def listar_pagos_empleado(self, empleado_id: int) -> list[Pago]:
        """Lista pagos de un empleado"""
        return self.pago_repository.get_by_empleado(empleado_id)

    def listar_por_periodo(self, fecha_inicio: date, fecha_fin: date) -> list[Pago]:
        """Lista pagos en un periodo"""
        return self.pago_repository.get_by_periodo(fecha_inicio, fecha_fin)

    def listar_pendientes(self) -> list[Pago]:
        """Lista pagos pendientes"""
        return self.pago_repository.get_pendientes()

    def listar_pendientes_empleado(self, empleado_id: int) -> list[Pago]:
        """Lista pagos pendientes de un empleado"""
        return self.pago_repository.get_pendientes_by_empleado(empleado_id)

    def listar_pagos(self) -> list[Pago]:
        """Lista todos los pagos"""
        return self.pago_repository.get_all()

    def listar_pagados(self) -> list[Pago]:
        """Lista pagos realizados"""
        return self.pago_repository.get_pagados()

    def marcar_pagado(self, pago_id: int) -> bool:
        """Marca un pago como realizado"""
        return self.pago_repository.marcar_pagado(pago_id)

    def marcar_pendiente(self, pago_id: int) -> bool:
        """Marca un pago como pendiente"""
        return self.pago_repository.marcar_pendiente(pago_id)

    def generar_nominas_empleado(
        self,
        empleado_id: int,
        periodo_inicio: date,
        periodo_fin: date,
        incluir_asistencia: bool = True,
        aplicar_prestamo: bool = True,
    ) -> Pago:
        """
        Genera automáticamente la nómina de un empleado para un periodo

        Args:
            empleado_id: Empleado a liquidar
            periodo_inicio: Inicio del período
            periodo_fin: Fin del período
            incluir_asistencia: Suma las horas extra registradas en asistencia
            aplicar_prestamo: Descuenta automáticamente la cuota del préstamo activo
        """
        from src.utils.helpers import parse_date

        if isinstance(periodo_inicio, str):
            periodo_inicio = parse_date(periodo_inicio)
        if isinstance(periodo_fin, str):
            periodo_fin = parse_date(periodo_fin)

        if not periodo_inicio or not periodo_fin:
            raise ValueError("Fechas de período inválidas o requeridas")

        empleado = self.empleado_repository.get_by_id(empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")

        # Verificar si ya existe nómina para este periodo
        pagos_existentes = self.pago_repository.get_by_empleado_periodo(
            empleado_id, periodo_inicio, periodo_fin
        )
        if pagos_existentes:
            raise ValueError("Ya existe una nómina para este periodo")

        # Calcular días trabajados (considerando incidencias)
        from src.services.incidencia_service import IncidenciaService

        incidencia_service = IncidenciaService(self.session)
        dias_incidencias = incidencia_service.calcular_dias_incidencias_periodo(
            empleado_id, periodo_inicio, periodo_fin
        )

        dias_periodo = (periodo_fin - periodo_inicio).days + 1
        dias_trabajados = max(0, dias_periodo - dias_incidencias)

        # Calcular salario proporcional (asumiendo mes comercial de 30 días)
        salario_diario = float(empleado.salario_base) / 30.0
        salario_base_periodo = round(salario_diario * min(dias_trabajados, 30), 2)

        # Horas extra clasificadas que registró el módulo de asistencia
        horas_extra = (
            self._horas_extra_periodo(empleado_id, periodo_inicio, periodo_fin)
            if incluir_asistencia
            else HorasExtra()
        )

        datos_pago = {
            "empleado_id": empleado_id,
            "tipo_pago": TipoPago.SALARIO_BASE.value,
            "periodo_inicio": periodo_inicio,
            "periodo_fin": periodo_fin,
            "salario_base": salario_base_periodo,
            "horas_extra_diurnas": float(horas_extra.diurnas),
            "horas_extra_nocturnas": float(horas_extra.nocturnas),
            "horas_extra_feriadas": float(horas_extra.feriadas),
            "descripcion": f"Nómina {periodo_inicio.strftime('%Y-%m-%d')} a {periodo_fin.strftime('%Y-%m-%d')}",
        }

        pago = self.crear_pago(datos_pago)
        if aplicar_prestamo:
            self.aplicar_cuota_prestamo(pago)
        return pago

    def _horas_extra_periodo(
        self, empleado_id: int, periodo_inicio: date, periodo_fin: date
    ) -> HorasExtra:
        """
        Horas extra clasificadas de un período según el módulo de asistencia

        Si el módulo no está disponible, la nómina se genera igual sin
        horas extra en lugar de fallar.
        """
        try:
            from src.services.asistencia_service import AsistenciaService

            return AsistenciaService(self.session).horas_extra_periodo(
                empleado_id, periodo_inicio, periodo_fin
            )
        except (SQLAlchemyError, ValueError, TypeError):
            logger.warning(
                "No se pudieron obtener las horas extra del empleado %s: se continúa sin ellas",
                empleado_id,
                exc_info=True,
            )
            return HorasExtra()

    def generar_nominas_periodo(self, periodo_inicio: date, periodo_fin: date) -> list[Pago]:
        """Genera nóminas para todos los empleados activos en un periodo"""
        from src.utils.helpers import parse_date

        if isinstance(periodo_inicio, str):
            periodo_inicio = parse_date(periodo_inicio)
        if isinstance(periodo_fin, str):
            periodo_fin = parse_date(periodo_fin)

        if not periodo_inicio or not periodo_fin:
            return []

        empleados_activos = self.empleado_repository.get_activos()
        pagos_generados = []

        for empleado in empleados_activos:
            try:
                pago = self.generar_nominas_empleado(empleado.id, periodo_inicio, periodo_fin)
                pagos_generados.append(pago)
            except Exception:
                # Continuar con el siguiente empleado si falla o ya existe
                continue

        return pagos_generados

    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas de pagos"""
        return {
            "total": self.pago_repository.count(),
            "pagados": len(self.pago_repository.get_pagados()),
            "pendientes": len(self.pago_repository.get_pendientes()),
            "por_tipo": self.pago_repository.get_estadisticas_por_tipo(),
            "por_metodo": self.pago_repository.get_estadisticas_por_metodo(),
        }

    def obtener_resumen_periodo(self, fecha_inicio: date, fecha_fin: date) -> dict:
        """Obtiene un resumen de pagos en un periodo"""
        pagos = self.pago_repository.get_by_periodo(fecha_inicio, fecha_fin)

        total_bruto = round(sum(float(p.monto_bruto or 0) for p in pagos), 2)
        total_neto = round(sum(float(p.monto_neto or 0) for p in pagos), 2)
        total_deducciones = round(sum(float(p.total_deducciones or 0) for p in pagos), 2)
        total_bonificaciones = round(sum(float(p.bonificaciones or 0) for p in pagos), 2)

        return {
            "cantidad_pagos": len(pagos),
            "total_bruto": total_bruto,
            "total_neto": total_neto,
            "total_deducciones": total_deducciones,
            "total_bonificaciones": total_bonificaciones,
            "promedio_neto": round(total_neto / len(pagos), 2) if pagos else 0.0,
        }

    def _calcular_deduccion_seguro(self, salario_base: float) -> float:
        """Deducción por seguro social con la configuración vigente"""
        return float(self.calcular_con_motor(salario_base).deduccion_seguro)

    def _calcular_deduccion_pension(self, salario_base: float) -> float:
        """Deducción por pensión con la configuración vigente"""
        return float(self.calcular_con_motor(salario_base).deduccion_pension)

    def _calcular_deduccion_impuesto(self, salario_base: float) -> float:
        """Retención de impuesto con la configuración vigente"""
        return float(self.calcular_con_motor(salario_base).deduccion_impuesto)

    def validar_datos_pago(self, datos: dict) -> list[str]:
        """Valida los datos de un pago"""
        from src.utils.helpers import parse_date

        errores = []

        # Validaciones requeridas
        campos_requeridos = [
            "empleado_id",
            "tipo_pago",
            "periodo_inicio",
            "periodo_fin",
            "salario_base",
        ]
        for campo in campos_requeridos:
            if campo not in datos or datos[campo] is None or str(datos[campo]).strip() == "":
                errores.append(f"El campo {campo} es requerido")

        # Validaciones específicas
        if "periodo_inicio" in datos and "periodo_fin" in datos:
            p_ini = (
                datos["periodo_inicio"]
                if isinstance(datos["periodo_inicio"], date)
                else parse_date(str(datos["periodo_inicio"]))
            )
            p_fin = (
                datos["periodo_fin"]
                if isinstance(datos["periodo_fin"], date)
                else parse_date(str(datos["periodo_fin"]))
            )
            if p_ini and p_fin and p_fin < p_ini:
                errores.append("La fecha fin debe ser posterior a la fecha inicio")

        if "salario_base" in datos:
            try:
                salario = float(datos["salario_base"])
                if salario <= 0:
                    errores.append("El salario base debe ser mayor a 0")
            except (ValueError, TypeError):
                errores.append("El salario base debe ser un número válido")

        return errores
