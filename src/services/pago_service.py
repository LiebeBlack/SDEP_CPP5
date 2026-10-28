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

from src.models import MetodoPago, Pago, TipoPago
from src.nomina import (
    DeduccionesManuales,
    EntradaNomina,
    HorasExtra,
    ParametrosNomina,
    ResultadoNomina,
    calcular_nomina,
    cargar_parametros_desde,
    redondear,
    validar_parametros,
)
from src.nomina.tipos import a_decimal
from src.repositories import (
    ConfiguracionRepository,
    EmpleadoRepository,
    PagoRepository,
)
from src.utils.helpers import parse_date_estricto, parse_float_estricto, parse_int_estricto

logger = logging.getLogger(__name__)


def _mismo_importe(actual: object, nuevo: object) -> bool:
    """
    Compara dos importes monetarios con la precisión de la nómina

    La base de datos devuelve ``Decimal`` y los formularios envían ``float``;
    comparar los tipos crudos hacía que un pago pareciera modificado al
    abrirlo y guardarlo sin tocar los importes, recalculándolo con los
    parámetros vigentes (y alterando un pago ya emitido).
    """
    try:
        return redondear(a_decimal(actual)) == redondear(a_decimal(nuevo))
    except (TypeError, ValueError, ArithmeticError):
        return actual == nuevo


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
        errores = self.validar_datos_pago(datos)
        if errores:
            raise ValueError("; ".join(errores))
        datos = self._normalizar_importes(datos)
        periodo_inicio, periodo_fin, fecha_pago = self._normalizar_fechas_pago(datos)
        empleado_id_validado = parse_int_estricto(datos.get("empleado_id"), "ID de empleado")
        if empleado_id_validado is None or empleado_id_validado <= 0:
            raise ValueError("El ID de empleado debe ser un número entero positivo")
        empleado = self.empleado_repository.get_by_id(empleado_id_validado)
        if empleado is None:
            raise ValueError("Empleado no encontrado")
        tipo_pago = getattr(datos.get("tipo_pago"), "value", datos.get("tipo_pago"))
        if tipo_pago not in TipoPago.values():
            raise ValueError("El tipo de pago no es válido")
        metodo_pago = getattr(
            datos.get("metodo_pago", MetodoPago.TRANSFERENCIA.value),
            "value",
            datos.get("metodo_pago", MetodoPago.TRANSFERENCIA.value),
        )
        if metodo_pago not in MetodoPago.values():
            raise ValueError("El método de pago no es válido")
        datos["empleado_id"] = empleado_id_validado
        datos["tipo_pago"] = tipo_pago
        datos["metodo_pago"] = metodo_pago
        if "pagado" in datos:
            estado_pagado = datos["pagado"]
            if isinstance(estado_pagado, bool):
                datos["pagado"] = int(estado_pagado)
            elif str(estado_pagado).strip() in {"0", "1"}:
                datos["pagado"] = int(str(estado_pagado).strip())
            else:
                raise ValueError("El estado pagado debe ser verdadero o falso")

        salario_base = round(float(datos["salario_base"]), 2)
        dias_trabajados, dias_periodo, prorrateado = self._prorrateo_de_datos(datos)
        if dias_periodo <= 0:
            raise ValueError("Los días del período deben ser mayores que cero")
        if not 0 <= dias_trabajados <= dias_periodo:
            raise ValueError("Los días trabajados deben estar entre 0 y los días del período")
        horas_extra_desglosadas = self._horas_extra(datos)
        resultado = self.calcular_con_motor(
            salario_base=salario_base,
            datos=datos,
            horas_extra=horas_extra_desglosadas,
        )
        # Salario efectivo del período: si el cálculo pidió prorratear, el
        # motor ya lo redujo a los días trabajados y es ese valor el que se
        # guarda (el mismo que usan las deducciones y el recálculo al editar).
        salario_periodo = round(float(resultado.salario_base), 2)

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
        bonificaciones = float(resultado.bonificaciones)
        aguinaldo = float(resultado.aguinaldo)
        bono_vacacional = float(resultado.bono_vacacional)

        total_deducciones = round(
            deduccion_seguro + deduccion_pension + deduccion_impuesto + otras_deducciones,
            2,
        )

        monto_bruto = round(
            salario_periodo + bonificaciones + monto_horas_extra + aguinaldo + bono_vacacional, 2
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
            salario_base=salario_periodo,
            dias_laborados=dias_trabajados,
            dias_periodo=dias_periodo,
            prorrateado=prorrateado,
            deduccion_seguro=deduccion_seguro,
            deduccion_pension=deduccion_pension,
            deduccion_impuesto=deduccion_impuesto,
            otras_deducciones=otras_deducciones,
            modalidad_calculo=resultado.modalidad,
            base_gravable=float(resultado.base_gravable),
            horas_extra_diurnas=float(resultado.horas_extra.diurnas),
            horas_extra_nocturnas=float(resultado.horas_extra.nocturnas),
            horas_extra_feriadas=float(resultado.horas_extra.feriadas),
            aguinaldo=aguinaldo,
            bono_vacacional=bono_vacacional,
            aporte_seguro_patronal=float(resultado.aporte_seguro_patronal),
            aporte_pension_patronal=float(resultado.aporte_pension_patronal),
            isr_tramo=resultado.isr_tramo,
            descripcion=datos.get("descripcion"),
            referencia_pago=ref_pago,
            observaciones=datos.get("observaciones"),
            pagado=int(datos.get("pagado", 0)),
        )

        return self.pago_repository.create(pago)

    # ------------------------------------------------------------------
    # Motor de nómina
    # ------------------------------------------------------------------
    def parametros_nomina(self) -> ParametrosNomina:
        """Parámetros de cálculo vigentes según la configuración del sistema"""
        try:
            return cargar_parametros_desde(self.config_repository.get_valor)
        except (SQLAlchemyError, ValueError, TypeError):
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
                dias_trabajados=self._entero_o_defecto(datos.get("dias_trabajados"), 30),
                dias_periodo=self._entero_o_defecto(datos.get("dias_periodo"), 30),
                prorratear=self._normalizar_bandera(datos.get("prorratear", False), "Prorratear"),
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
        # Un solo cálculo: las deducciones ya vienen en el resultado. Antes se
        # recalculaba la nómina entera una segunda vez para obtener los mismos
        # tres importes.
        return {
            "modalidad": resultado.modalidad,
            "deduccion_seguro": round(float(resultado.deduccion_seguro), 2),
            "deduccion_pension": round(float(resultado.deduccion_pension), 2),
            "deduccion_impuesto": round(float(resultado.deduccion_impuesto), 2),
            "total_deducciones": float(resultado.total_deducciones),
            "monto_neto": float(resultado.monto_neto),
            "base_gravable": float(resultado.base_gravable),
            "isr_tramo": resultado.isr_tramo,
        }

    @staticmethod
    def _entero_o_defecto(valor: object, por_defecto: int) -> int:
        """Convierte a entero conservando el cero y usa defecto solo en vacío."""
        if valor is None or str(valor).strip() == "":
            return por_defecto
        resultado = parse_int_estricto(valor, "Valor entero")
        if resultado is None:
            return por_defecto
        return resultado

    @staticmethod
    def _prorrateo_de_datos(datos: dict) -> tuple[int, int, bool]:
        """
        Días y bandera de prorrateo con los que se calcula un pago

        Devuelve los mismos valores que ``calcular_con_motor`` entrega al
        motor (30/30 días sin prorratear cuando no se indican), para poder
        guardarlos en el propio pago y reconstruir después un recálculo
        idéntico al editar.
        """
        return (
            PagoService._entero_o_defecto(datos.get("dias_trabajados"), 30),
            PagoService._entero_o_defecto(datos.get("dias_periodo"), 30),
            PagoService._normalizar_bandera(datos.get("prorratear", False), "Prorratear"),
        )

    @staticmethod
    def _normalizar_bandera(valor: object, etiqueta: str) -> bool:
        """Interpreta banderas de formulario/API sin que "0" cuente como True."""
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, int) and valor in (0, 1):
            return bool(valor)
        texto = str(valor).strip().lower()
        if texto in {"1", "true", "yes", "si", "sí"}:
            return True
        if texto in {"0", "false", "no", ""}:
            return False
        raise ValueError(f"{etiqueta} debe ser verdadero o falso")

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
    def _normalizar_fechas_pago(datos: dict) -> tuple[date | None, date | None, date]:
        """Resuelve periodo de inicio/fin y fecha de pago (hoy por defecto)"""
        periodo_inicio = datos["periodo_inicio"]
        if periodo_inicio is not None:
            periodo_inicio = parse_date_estricto(periodo_inicio, "Periodo de inicio")

        periodo_fin = datos["periodo_fin"]
        if periodo_fin is not None:
            periodo_fin = parse_date_estricto(periodo_fin, "Periodo de fin")

        fecha_pago = datos.get("fecha_pago")
        if fecha_pago is not None:
            fecha_pago = parse_date_estricto(fecha_pago, "Fecha de pago") or date.today()
        elif not fecha_pago:
            fecha_pago = date.today()

        return periodo_inicio, periodo_fin, fecha_pago

    @staticmethod
    def _referencia_por_defecto(empleado_id: int, periodo_inicio: date | None) -> str:
        """Referencia REC-<empleado>-<yyyymmdd> cuando no se proporciona una"""
        fecha = periodo_inicio.strftime("%Y%m%d") if periodo_inicio else "00"
        return f"REC-{empleado_id}-{fecha}"

    def actualizar_pago(self, pago_id: int, datos: dict) -> Pago:
        """Actualiza un pago existente"""
        pago = self.pago_repository.get_by_id(pago_id)
        if not pago:
            raise ValueError("Pago no encontrado")

        datos = dict(datos)
        if "empleado_id" in datos:
            empleado_id_solicitado = parse_int_estricto(datos["empleado_id"], "ID de empleado")
            if empleado_id_solicitado != pago.empleado_id:
                raise ValueError("No se puede reasignar un pago a otro empleado")
            datos.pop("empleado_id")

        errores_importes = self._errores_importes(datos)
        if errores_importes:
            raise ValueError("; ".join(errores_importes))
        datos = self._normalizar_importes(datos)

        # Normalizar fechas si vienen en datos y validar el rango final aunque
        # el formulario haya enviado solo uno de los extremos.
        for f_campo in ("periodo_inicio", "periodo_fin", "fecha_pago"):
            if f_campo in datos:
                fecha = parse_date_estricto(datos[f_campo], f_campo.replace("_", " "))
                if fecha is None:
                    raise ValueError(f"{f_campo.replace('_', ' ').capitalize()} es requerida")
                datos[f_campo] = fecha
        periodo_inicio_final = datos.get("periodo_inicio", pago.periodo_inicio)
        periodo_fin_final = datos.get("periodo_fin", pago.periodo_fin)
        if periodo_inicio_final is None or periodo_fin_final is None:
            raise ValueError("Las fechas de inicio y fin del período son requeridas")
        if periodo_fin_final < periodo_inicio_final:
            raise ValueError("La fecha fin debe ser igual o posterior a la fecha inicio")

        for campo_dia in ("dias_trabajados", "dias_periodo"):
            if campo_dia in datos:
                datos[campo_dia] = parse_int_estricto(
                    datos[campo_dia], campo_dia.replace("_", " ")
                )
                if datos[campo_dia] is None:
                    raise ValueError(f"{campo_dia.replace('_', ' ').capitalize()} es requerido")

        if "prorratear" in datos:
            datos["prorratear"] = self._normalizar_bandera(datos["prorratear"], "Prorratear")

        if "salario_base" in datos:
            salario_base = datos["salario_base"]
            if salario_base is None or salario_base <= 0:
                raise ValueError("El salario base debe ser un número finito mayor a 0")

        if "dias_trabajados" in datos or "dias_periodo" in datos:
            valor_dias = datos.get("dias_trabajados", pago.dias_laborados)
            valor_periodo = datos.get("dias_periodo", pago.dias_periodo)
            dias_trabajados_final = self._entero_o_defecto(valor_dias, 30)
            dias_periodo_final = self._entero_o_defecto(valor_periodo, 30)
            if dias_periodo_final <= 0:
                raise ValueError("Los días del período deben ser mayores que cero")
            if not 0 <= dias_trabajados_final <= dias_periodo_final:
                raise ValueError("Los días trabajados deben estar entre 0 y los días del período")

        campos_calculo = {
            "salario_base",
            "dias_trabajados",
            "dias_periodo",
            "prorratear",
            "bonificaciones",
            "horas_extra",
            "horas_extra_diurnas",
            "horas_extra_nocturnas",
            "horas_extra_feriadas",
            "descuentos",
            "deduccion_seguro",
            "deduccion_pension",
            "deduccion_impuesto",
            "otras_deducciones",
            "aguinaldo",
            "bono_vacacional",
        }
        # Recalcular solo si cambió realmente algún concepto que participa en
        # el cálculo. El formulario reenvía todos los importes al guardar
        # (aunque solo se marque el pago como realizado); compararlos con los
        # valores persistidos evita reescribir un pago histórico con los
        # parámetros de nómina del día.
        recalcular = any(
            campo in datos
            and (not hasattr(pago, campo) or not _mismo_importe(getattr(pago, campo), datos[campo]))
            for campo in campos_calculo - {"prorratear"}
        )
        prorratear_actual = bool(pago.prorrateado)
        if "prorratear" in datos:
            prorratear_solicitado = self._normalizar_bandera(datos["prorratear"], "Prorratear")
            datos["prorratear"] = prorratear_solicitado
            if prorratear_solicitado != prorratear_actual:
                recalcular = True

        if recalcular:
            campos_componentes = (
                "salario_base",
                "bonificaciones",
                "horas_extra",
                "horas_extra_diurnas",
                "horas_extra_nocturnas",
                "horas_extra_feriadas",
                "descuentos",
                "otras_deducciones",
                "aguinaldo",
                "bono_vacacional",
            )
            componentes = {
                campo: datos.get(campo, getattr(pago, campo) or 0) for campo in campos_componentes
            }
            horas_extra_desglosadas = self._horas_extra(componentes)
            datos_calculo = {
                campo: componentes[campo]
                for campo in (
                    "bonificaciones",
                    "descuentos",
                    "otras_deducciones",
                    "aguinaldo",
                    "bono_vacacional",
                )
            }
            es_liquidacion = pago.tipo_pago == TipoPago.LIQUIDACION.value
            # Solo una deducción enviada explícitamente se considera manual.
            # Si se edita el salario sin tocar las deducciones, el motor las
            # vuelve a calcular con los parámetros vigentes.
            for campo in ("deduccion_seguro", "deduccion_pension", "deduccion_impuesto"):
                if campo in datos or es_liquidacion:
                    datos_calculo[campo] = datos.get(campo, getattr(pago, campo) or 0)
            # El prorrateo forma parte del cálculo y se decide en dos ramas:
            # - si el formulario envía los días, el salario que llega se
            #   interpreta como el del período completo y el motor vuelve a
            #   prorratearlo con esos días;
            # - si no los envía, se conservan los días guardados en el pago y
            #   se recalcula sobre el salario del período ya guardado, sin
            #   prorratear otra vez (prorratear dos veces descontaría los
            #   días en cada edición y el neto bajaría solo).
            dias_laborados: int | None
            dias_periodo: int | None
            prorrateado: bool | None
            campos_prorrateo = {"dias_trabajados", "dias_periodo", "prorratear"}
            if campos_prorrateo & datos.keys():
                valor_dias = datos.get("dias_trabajados", pago.dias_laborados)
                valor_periodo = datos.get("dias_periodo", pago.dias_periodo)
                dias_laborados = self._entero_o_defecto(valor_dias, 30)
                dias_periodo = self._entero_o_defecto(valor_periodo, 30)
                prorrateado = (
                    self._normalizar_bandera(datos["prorratear"], "Prorratear")
                    if "prorratear" in datos
                    else bool(pago.prorrateado)
                )
                datos_calculo.update(
                    {
                        "dias_trabajados": dias_laborados,
                        "dias_periodo": dias_periodo,
                        "prorratear": prorrateado,
                    }
                )
            else:
                dias_laborados = pago.dias_laborados
                dias_periodo = pago.dias_periodo
                prorrateado = pago.prorrateado
                # Si el usuario cambia el salario de un pago prorrateado sin
                # reenviar los días, el importe del formulario es el salario
                # del período completo: hay que volver a prorratearlo con los
                # días guardados. Sin esto el pago quedaba marcado como
                # prorrateado pero pagaba el mes completo (y una segunda
                # edición lo prorratearía otra vez).
                if prorrateado and dias_periodo and "salario_base" in datos:
                    datos_calculo.update(
                        {
                            "dias_trabajados": 30 if dias_laborados is None else dias_laborados,
                            "dias_periodo": dias_periodo,
                            "prorratear": True,
                        }
                    )

            resultado = self.calcular_con_motor(
                salario_base=round(float(componentes["salario_base"] or 0), 2),
                datos=datos_calculo,
                horas_extra=horas_extra_desglosadas,
            )
            monto_horas_extra = (
                float(resultado.monto_horas_extra)
                if horas_extra_desglosadas.hay_horas
                else round(float(componentes["horas_extra"] or 0), 2)
            )
            monto_bruto = round(
                float(resultado.salario_base)
                + float(resultado.bonificaciones)
                + monto_horas_extra
                + float(resultado.aguinaldo)
                + float(resultado.bono_vacacional),
                2,
            )
            total_deducciones = round(
                float(resultado.deduccion_seguro)
                + float(resultado.deduccion_pension)
                + float(resultado.deduccion_impuesto)
                + float(resultado.otras_deducciones),
                2,
            )
            monto_neto = round(
                max(0.0, monto_bruto - total_deducciones - float(resultado.descuentos)), 2
            )
            datos["monto_bruto"] = monto_bruto
            datos["monto_neto"] = monto_neto
            datos.update(
                {
                    "salario_base": float(resultado.salario_base),
                    "horas_extra": monto_horas_extra,
                    "horas_extra_diurnas": float(resultado.horas_extra.diurnas),
                    "horas_extra_nocturnas": float(resultado.horas_extra.nocturnas),
                    "horas_extra_feriadas": float(resultado.horas_extra.feriadas),
                    "deduccion_seguro": float(resultado.deduccion_seguro),
                    "deduccion_pension": float(resultado.deduccion_pension),
                    "deduccion_impuesto": float(resultado.deduccion_impuesto),
                    "otras_deducciones": float(resultado.otras_deducciones),
                    "modalidad_calculo": resultado.modalidad,
                    "base_gravable": float(resultado.base_gravable),
                    "aguinaldo": float(resultado.aguinaldo),
                    "bono_vacacional": float(resultado.bono_vacacional),
                    "aporte_seguro_patronal": (
                        float(pago.aporte_seguro_patronal or 0)
                        if es_liquidacion
                        else float(resultado.aporte_seguro_patronal)
                    ),
                    "aporte_pension_patronal": (
                        float(pago.aporte_pension_patronal or 0)
                        if es_liquidacion
                        else float(resultado.aporte_pension_patronal)
                    ),
                    "isr_tramo": pago.isr_tramo if es_liquidacion else resultado.isr_tramo,
                    "dias_laborados": dias_laborados,
                    "dias_periodo": dias_periodo,
                    "prorrateado": prorrateado,
                }
            )
            if es_liquidacion:
                datos["modalidad_calculo"] = pago.modalidad_calculo
                datos["base_gravable"] = float(pago.base_gravable or 0)

        if "tipo_pago" in datos:
            tipo_pago = getattr(datos["tipo_pago"], "value", datos["tipo_pago"])
            if tipo_pago not in TipoPago.values():
                raise ValueError("El tipo de pago no es válido")
            datos["tipo_pago"] = tipo_pago
        if "metodo_pago" in datos:
            metodo_pago = getattr(datos["metodo_pago"], "value", datos["metodo_pago"])
            if metodo_pago not in MetodoPago.values():
                raise ValueError("El método de pago no es válido")
            datos["metodo_pago"] = metodo_pago
        if "pagado" in datos:
            estado_pagado = datos["pagado"]
            if isinstance(estado_pagado, bool):
                datos["pagado"] = int(estado_pagado)
            elif str(estado_pagado).strip() in {"0", "1"}:
                datos["pagado"] = int(str(estado_pagado).strip())
            else:
                raise ValueError("El estado pagado debe ser verdadero o falso")

        # Actualizar campos
        # `dias_trabajados` es una propiedad de solo lectura derivada del
        # período; para persistir el dato de prorrateo se guarda en
        # `dias_laborados`, nunca se intenta asignar a la propiedad.
        if "dias_trabajados" in datos:
            datos.pop("dias_trabajados")
        for campo, valor in datos.items():
            if hasattr(pago, campo) and campo not in {"empleado_id", "prorratear"}:
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
    ) -> Pago:
        """
        Genera automáticamente la nómina de un empleado para un periodo

        Args:
            empleado_id: Empleado a liquidar
            periodo_inicio: Inicio del período
            periodo_fin: Fin del período
        """
        if isinstance(periodo_inicio, str):
            periodo_inicio = parse_date_estricto(periodo_inicio, "Periodo de inicio")
        if isinstance(periodo_fin, str):
            periodo_fin = parse_date_estricto(periodo_fin, "Periodo de fin")

        if not periodo_inicio or not periodo_fin:
            raise ValueError("Fechas de período inválidas o requeridas")
        if periodo_fin < periodo_inicio:
            raise ValueError("La fecha fin debe ser igual o posterior a la fecha inicio")

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

        dias_calendario = (periodo_fin - periodo_inicio).days + 1
        # Un período que cubre un mes completo se liquida sobre el mes
        # comercial de 30 días, no sobre los días del calendario: febrero
        # (28/29 días) pagaba un salario proporcionalmente menor sin que el
        # empleado hubiera faltado. Los períodos parciales conservan sus días
        # reales.
        dias_base = 30 if dias_calendario >= 28 else dias_calendario
        dias_trabajados = max(0, dias_base - dias_incidencias)

        # Días efectivos sobre el mes comercial de 30 días: el prorrateo lo
        # aplica el motor y el pago guarda con qué días se calculó, de modo
        # que una edición posterior no devuelva el salario completo.
        dias_efectivos = min(dias_trabajados, 30)

        # Las horas extra del período se capturan por tipo en el formulario
        # de pago; la generación automática solo calcula el salario base.
        datos_pago = {
            "empleado_id": empleado_id,
            "tipo_pago": TipoPago.SALARIO_BASE.value,
            "periodo_inicio": periodo_inicio,
            "periodo_fin": periodo_fin,
            "salario_base": float(empleado.salario_base),
            "dias_trabajados": dias_efectivos,
            "dias_periodo": 30,
            "prorratear": True,
            "descripcion": (
                f"Nómina {periodo_inicio.strftime('%Y-%m-%d')} a "
                f"{periodo_fin.strftime('%Y-%m-%d')}"
            ),
        }

        return self.crear_pago(datos_pago)

    def generar_nominas_periodo(self, periodo_inicio: date, periodo_fin: date) -> list[Pago]:
        """Genera nóminas para todos los empleados activos en un periodo"""
        if isinstance(periodo_inicio, str):
            periodo_inicio = parse_date_estricto(periodo_inicio, "Periodo de inicio")
        if isinstance(periodo_fin, str):
            periodo_fin = parse_date_estricto(periodo_fin, "Periodo de fin")

        if not periodo_inicio or not periodo_fin:
            raise ValueError("Fechas de período inválidas o requeridas")
        if periodo_fin < periodo_inicio:
            raise ValueError("La fecha fin debe ser igual o posterior a la fecha inicio")

        empleados_activos = self.empleado_repository.get_activos()
        pagos_generados = []

        for empleado in empleados_activos:
            try:
                pago = self.generar_nominas_empleado(empleado.id, periodo_inicio, periodo_fin)
                pagos_generados.append(pago)
            except Exception as e:
                # Se continúa con el resto del personal (por ejemplo si el
                # empleado ya tiene nómina en el período), pero el motivo
                # queda registrado para poder diagnosticarlo.
                logger.warning(
                    "No se generó la nómina del empleado %s: %s",
                    empleado.id,
                    e,
                    exc_info=True,
                )
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

    @staticmethod
    def _errores_importes(datos: dict) -> list[str]:
        """Rechaza importes no numéricos y no finitos en todos los flujos."""
        campos_importe = (
            "salario_base",
            "bonificaciones",
            "horas_extra",
            "horas_extra_diurnas",
            "horas_extra_nocturnas",
            "horas_extra_feriadas",
            "descuentos",
            "deduccion_seguro",
            "deduccion_pension",
            "deduccion_impuesto",
            "otras_deducciones",
            "aguinaldo",
            "bono_vacacional",
            "monto_bruto",
            "monto_neto",
            "base_gravable",
            "aporte_seguro_patronal",
            "aporte_pension_patronal",
        )
        errores: list[str] = []
        for campo in campos_importe:
            valor = datos.get(campo)
            if campo not in datos or valor is None or str(valor).strip() == "":
                continue
            try:
                importe = parse_float_estricto(valor, campo.replace("_", " "))
                if importe is not None and importe < 0:
                    errores.append(f"{campo.replace('_', ' ').capitalize()} no puede ser negativo")
            except ValueError as error:
                errores.append(str(error))
        return errores

    @staticmethod
    def _normalizar_importes(datos: dict) -> dict:
        """Convierte todos los importes válidos al mismo float de dominio."""
        campos_importe = (
            "salario_base",
            "bonificaciones",
            "horas_extra",
            "horas_extra_diurnas",
            "horas_extra_nocturnas",
            "horas_extra_feriadas",
            "descuentos",
            "deduccion_seguro",
            "deduccion_pension",
            "deduccion_impuesto",
            "otras_deducciones",
            "aguinaldo",
            "bono_vacacional",
            "monto_bruto",
            "monto_neto",
            "base_gravable",
            "aporte_seguro_patronal",
            "aporte_pension_patronal",
        )
        normalizados = dict(datos)
        for campo in campos_importe:
            if campo not in normalizados:
                continue
            valor = normalizados[campo]
            if valor is None or str(valor).strip() == "":
                continue
            normalizados[campo] = parse_float_estricto(valor, campo.replace("_", " "))
        return normalizados

    def validar_datos_pago(self, datos: dict) -> list[str]:
        """Valida los datos de un pago"""
        errores = self._errores_importes(datos)

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
        fechas: dict[str, date | None] = {}
        for campo in ("periodo_inicio", "periodo_fin"):
            valor = datos.get(campo)
            try:
                fecha = parse_date_estricto(valor, campo.replace("_", " "))
            except ValueError as error:
                errores.append(str(error))
                fecha = None
            fechas[campo] = fecha
        if fechas["periodo_inicio"] and fechas["periodo_fin"]:
            if fechas["periodo_fin"] < fechas["periodo_inicio"]:
                errores.append("La fecha fin debe ser posterior a la fecha inicio")
        for campo in ("periodo_inicio", "periodo_fin"):
            if campo in datos and fechas[campo] is None:
                errores.append(f"El campo {campo.replace('_', ' ')} es requerido")

        try:
            empleado_id = parse_int_estricto(datos.get("empleado_id"), "ID de empleado")
            if empleado_id is not None and empleado_id <= 0:
                errores.append("El ID de empleado debe ser positivo")
        except ValueError as error:
            errores.append(str(error))

        tipo_pago = datos.get("tipo_pago")
        if hasattr(tipo_pago, "value"):
            tipo_pago = tipo_pago.value
        if tipo_pago and tipo_pago not in TipoPago.values():
            errores.append("El tipo de pago no es válido")

        metodo_pago = datos.get("metodo_pago")
        if hasattr(metodo_pago, "value"):
            metodo_pago = metodo_pago.value
        if metodo_pago and metodo_pago not in MetodoPago.values():
            errores.append("El método de pago no es válido")

        if "salario_base" in datos:
            try:
                salario = parse_float_estricto(datos["salario_base"], "Salario base")
                if salario is not None and salario <= 0:
                    errores.append("El salario base debe ser un número finito mayor a 0")
            except ValueError as error:
                errores.append(str(error))

        if "fecha_pago" in datos:
            try:
                fecha_pago = parse_date_estricto(datos.get("fecha_pago"), "Fecha de pago")
                if fecha_pago is None:
                    errores.append("La fecha de pago es requerida")
            except ValueError as error:
                errores.append(str(error))

        # Días del prorrateo: solo se validan cuando el pago se prorratea,
        # para no rechazar los pagos que no usan días (la mayoría).
        if datos.get("prorratear") or "dias_trabajados" in datos or "dias_periodo" in datos:
            try:
                dias_trabajados = parse_int_estricto(
                    datos.get("dias_trabajados", 30), "Días trabajados"
                )
                dias_periodo = parse_int_estricto(datos.get("dias_periodo", 30), "Días del período")
            except ValueError as error:
                errores.append(str(error))
            else:
                if dias_periodo is None or dias_periodo <= 0:
                    errores.append("Los días del período deben ser mayores que cero")
                elif dias_trabajados is None or not 0 <= dias_trabajados <= dias_periodo:
                    errores.append("Los días trabajados deben estar entre 0 y los días del período")

        return errores
