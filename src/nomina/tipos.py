"""
Tipos del motor de nómina
Estructuras de datos puras compartidas por todos los cálculos de nómina

Ninguna de estas clases toca la base de datos ni la interfaz: son datos
inmutables que entran y salen del motor, lo que hace que cada cálculo sea
predecible y verificable de forma aislada.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from src.models.enums import ModoCalculoNomina

# Todos los importes del sistema se manejan con dos decimales exactos.
CENTAVO = Decimal("0.01")
CERO = Decimal("0.00")

type Dinero = Decimal
type TramoDict = dict[str, Any]


def a_decimal(valor: Any, por_defecto: Decimal = CERO) -> Decimal:
    """
    Convierte cualquier valor numérico a Decimal de forma segura

    Acepta Decimal, int, float, str (con separadores de miles o coma
    decimal) y None. Ante un valor no convertible devuelve el valor por
    defecto en lugar de lanzar una excepción: un dato sucio en la
    configuración no debe impedir calcular la nómina.
    """
    if valor is None or valor == "":
        return por_defecto
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, bool):
        return Decimal(int(valor))
    if isinstance(valor, int):
        return Decimal(valor)
    if isinstance(valor, float):
        return Decimal(str(valor))
    try:
        texto = str(valor).strip().replace(" ", "")
        # Formato internacional "1,234.56" o local "1.234,56"
        if "," in texto and "." in texto:
            texto = (
                texto.replace(".", "").replace(",", ".")
                if texto.rfind(",") > texto.rfind(".")
                else texto.replace(",", "")
            )
        else:
            texto = texto.replace(",", ".")
        return Decimal(texto)
    except (ArithmeticError, ValueError):
        return por_defecto


def redondear(valor: Any) -> Decimal:
    """
    Redondea un importe a dos decimales con redondeo bancario comercial

    Se usa ROUND_HALF_UP (no el redondeo por defecto de Decimal, que es
    ROUND_HALF_EVEN) porque es el criterio que espera un recibo de pago:
    0.005 sube a 0.01.
    """
    from decimal import ROUND_HALF_UP

    return a_decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class TramoISR:
    """Un tramo de la tabla progresiva de impuesto sobre la renta"""

    limite_inferior: Dinero
    limite_superior: Dinero | None
    tasa: Dinero
    cuota_fija: Dinero

    @classmethod
    def desde_dict(cls, datos: TramoDict) -> "TramoISR":
        """Construye un tramo a partir de su representación en configuración"""
        return cls(
            limite_inferior=a_decimal(datos.get("limite_inferior")),
            limite_superior=(
                None
                if datos.get("limite_superior") in (None, "", "None")
                else a_decimal(datos.get("limite_superior"))
            ),
            tasa=a_decimal(datos.get("tasa")),
            cuota_fija=a_decimal(datos.get("cuota_fija")),
        )

    def aplica_a(self, base: Dinero) -> bool:
        """Indica si una base gravable cae dentro del tramo"""
        if base < self.limite_inferior:
            return False
        return self.limite_superior is None or base <= self.limite_superior

    def calcular(self, base: Dinero) -> Dinero:
        """
        Impuesto del tramo para una base gravable

        Aplica la cuota fija del tramo más la tasa sobre el excedente
        del límite inferior, que es el esquema de tabla progresiva.
        """
        excedente = max(CERO, base - self.limite_inferior)
        return redondear(self.cuota_fija + excedente * self.tasa / Decimal(100))

    def descripcion(self) -> str:
        """Texto legible del tramo, útil para el recibo de pago"""
        if self.limite_superior is None:
            rango = f"desde {self.limite_inferior:.2f}"
        else:
            rango = f"{self.limite_inferior:.2f} - {self.limite_superior:.2f}"
        return f"{rango} ({self.tasa:.2f}%)"


@dataclass(frozen=True, slots=True)
class ParametrosNomina:
    """
    Parámetros de cálculo vigentes

    Se construyen una vez por período de nómina y se reutilizan en cada
    empleado, de modo que todos los pagos de un mismo período se calculen
    con exactamente las mismas reglas.
    """

    modo: ModoCalculoNomina = ModoCalculoNomina.PORCENTAJE
    porcentaje_seguro: Dinero = Decimal("4.5")
    porcentaje_pension: Dinero = Decimal("5.0")
    porcentaje_impuesto: Dinero = CERO
    techo_seguro: Dinero = CERO
    techo_pension: Dinero = CERO
    porcentaje_seguro_patronal: Dinero = CERO
    porcentaje_pension_patronal: Dinero = CERO
    tramos_isr: tuple[TramoISR, ...] = ()
    horas_jornada_diaria: Dinero = Decimal(8)
    recargo_diurno: Dinero = Decimal("25.0")
    recargo_nocturno: Dinero = Decimal("50.0")
    recargo_feriado: Dinero = Decimal("100.0")
    dias_aguinaldo: Dinero = Decimal(15)
    dias_bono_vacacional: Dinero = Decimal(15)
    dias_prestaciones_por_ano: Dinero = Decimal(30)
    dias_preaviso: Dinero = Decimal(30)
    max_porcentaje_cuota_prestamo: Dinero = Decimal("30.0")
    salario_minimo: Dinero = CERO

    @property
    def usa_tramos(self) -> bool:
        """Indica si el cálculo por tramos está activo"""
        return self.modo == ModoCalculoNomina.TRAMOS

    @property
    def tramos_ordenados(self) -> tuple[TramoISR, ...]:
        """Tramos ordenados por límite inferior (defensa ante configuraciones desordenadas)"""
        return tuple(sorted(self.tramos_isr, key=lambda tramo: tramo.limite_inferior))


@dataclass(frozen=True, slots=True)
class HorasExtra:
    """Horas extra de un período, clasificadas por tipo de recargo"""

    diurnas: Dinero = CERO
    nocturnas: Dinero = CERO
    feriadas: Dinero = CERO

    @property
    def total(self) -> Dinero:
        """Total de horas extra del período"""
        return redondear(self.diurnas + self.nocturnas + self.feriadas)

    @property
    def hay_horas(self) -> bool:
        """Indica si el período registró horas extra"""
        return self.total > CERO


@dataclass(frozen=True, slots=True)
class DeduccionesManuales:
    """
    Deducciones capturadas a mano por el usuario

    Cuando la interfaz recibe un importe explícito para un concepto, ese
    valor manda sobre el cálculo automático: es el empleado quien conoce
    los casos particulares y no debe ser sobrescrito por el motor.
    """

    seguro: Dinero | None = None
    pension: Dinero | None = None
    impuesto: Dinero | None = None


@dataclass(frozen=True, slots=True)
class EntradaNomina:
    """
    Datos de entrada de un cálculo de nómina

    Reúne todo lo que el motor necesita para calcular el pago de un
    empleado en un período, sin depender de la base de datos.
    """

    salario_base: Dinero
    dias_trabajados: int = 30
    dias_periodo: int = 30
    prorratear: bool = False
    horas_extra: HorasExtra = field(default_factory=HorasExtra)
    bonificaciones: Dinero = CERO
    otras_deducciones: Dinero = CERO
    descuentos: Dinero = CERO
    aguinaldo: Dinero = CERO
    bono_vacacional: Dinero = CERO
    cuota_prestamo: Dinero = CERO
    deducciones_manuales: DeduccionesManuales | None = None


@dataclass(frozen=True, slots=True)
class ResultadoNomina:
    """Resultado completo de un cálculo de nómina, listo para persistir"""

    modalidad: str = ModoCalculoNomina.PORCENTAJE.value
    salario_base: Dinero = CERO
    monto_horas_extra: Dinero = CERO
    bonificaciones: Dinero = CERO
    aguinaldo: Dinero = CERO
    bono_vacacional: Dinero = CERO
    base_gravable: Dinero = CERO
    deduccion_seguro: Dinero = CERO
    deduccion_pension: Dinero = CERO
    deduccion_impuesto: Dinero = CERO
    otras_deducciones: Dinero = CERO
    descuentos: Dinero = CERO
    deduccion_prestamo: Dinero = CERO
    aporte_seguro_patronal: Dinero = CERO
    aporte_pension_patronal: Dinero = CERO
    isr_tramo: str | None = None
    horas_extra: HorasExtra = field(default_factory=HorasExtra)

    @property
    def total_ingresos(self) -> Dinero:
        """Suma de todos los conceptos a favor del empleado"""
        return redondear(
            self.salario_base
            + self.monto_horas_extra
            + self.bonificaciones
            + self.aguinaldo
            + self.bono_vacacional
        )

    @property
    def total_deducciones(self) -> Dinero:
        """Suma de todos los descuentos aplicados al empleado"""
        return redondear(
            self.deduccion_seguro
            + self.deduccion_pension
            + self.deduccion_impuesto
            + self.otras_deducciones
            + self.descuentos
            + self.deduccion_prestamo
        )

    @property
    def monto_bruto(self) -> Dinero:
        """Monto bruto del período (antes de deducciones)"""
        return self.total_ingresos

    @property
    def monto_neto(self) -> Dinero:
        """Monto neto a pagar al empleado"""
        return redondear(max(CERO, self.total_ingresos - self.total_deducciones))

    @property
    def total_aportes_patronales(self) -> Dinero:
        """Aportes a cargo del patrono (costo adicional, no descontado)"""
        return redondear(self.aporte_seguro_patronal + self.aporte_pension_patronal)

    def to_dict(self) -> dict[str, Any]:
        """Diccionario con los campos listos para volcar en el modelo Pago"""
        return {
            "modalidad_calculo": self.modalidad,
            "salario_base": float(redondear(self.salario_base)),
            "horas_extra": float(redondear(self.monto_horas_extra)),
            "horas_extra_diurnas": float(redondear(self.horas_extra.diurnas)),
            "horas_extra_nocturnas": float(redondear(self.horas_extra.nocturnas)),
            "horas_extra_feriadas": float(redondear(self.horas_extra.feriadas)),
            "bonificaciones": float(redondear(self.bonificaciones)),
            "aguinaldo": float(redondear(self.aguinaldo)),
            "bono_vacacional": float(redondear(self.bono_vacacional)),
            "base_gravable": float(redondear(self.base_gravable)),
            "deduccion_seguro": float(redondear(self.deduccion_seguro)),
            "deduccion_pension": float(redondear(self.deduccion_pension)),
            "deduccion_impuesto": float(redondear(self.deduccion_impuesto)),
            "otras_deducciones": float(redondear(self.otras_deducciones)),
            "descuentos": float(redondear(self.descuentos)),
            "deduccion_prestamo": float(redondear(self.deduccion_prestamo)),
            "aporte_seguro_patronal": float(redondear(self.aporte_seguro_patronal)),
            "aporte_pension_patronal": float(redondear(self.aporte_pension_patronal)),
            "isr_tramo": self.isr_tramo,
            "monto_bruto": float(self.monto_bruto),
            "monto_neto": float(self.monto_neto),
        }


@dataclass(frozen=True, slots=True)
class EntradaFiniquito:
    """Datos necesarios para liquidar a un empleado que cesa funciones"""

    salario_mensual: Dinero
    fecha_ingreso: Any
    fecha_egreso: Any
    dias_vacaciones_pendientes: Dinero = CERO
    dias_utilidades_pendientes: Dinero = CERO
    anticipos_pendientes: Dinero = CERO
    otras_deducciones: Dinero = CERO
    motivo: str | None = None


@dataclass(frozen=True, slots=True)
class ResultadoFiniquito:
    """Desglose completo de una liquidación o finiquito"""

    anos_servicio: Dinero = CERO
    meses_servicio: int = 0
    dias_servicio: int = 0
    prestaciones: Dinero = CERO
    indemnizacion: Dinero = CERO
    preaviso: Dinero = CERO
    vacaciones: Dinero = CERO
    bono_vacacional: Dinero = CERO
    aguinaldo: Dinero = CERO
    anticipos: Dinero = CERO
    otras_deducciones: Dinero = CERO
    motivo: str | None = None

    @property
    def total_asignaciones(self) -> Dinero:
        """Total de conceptos a favor del empleado"""
        return redondear(
            self.prestaciones
            + self.indemnizacion
            + self.preaviso
            + self.vacaciones
            + self.bono_vacacional
            + self.aguinaldo
        )

    @property
    def total_deducciones(self) -> Dinero:
        """Total de conceptos a descontar"""
        return redondear(self.anticipos + self.otras_deducciones)

    @property
    def neto(self) -> Dinero:
        """Monto neto de la liquidación"""
        return redondear(max(CERO, self.total_asignaciones - self.total_deducciones))

    def to_dict(self) -> dict[str, Any]:
        """Diccionario con el desglose del finiquito"""
        return {
            "anos_servicio": float(self.anos_servicio),
            "meses_servicio": self.meses_servicio,
            "dias_servicio": self.dias_servicio,
            "prestaciones": float(self.prestaciones),
            "indemnizacion": float(self.indemnizacion),
            "preaviso": float(self.preaviso),
            "vacaciones": float(self.vacaciones),
            "bono_vacacional": float(self.bono_vacacional),
            "aguinaldo": float(self.aguinaldo),
            "anticipos": float(self.anticipos),
            "otras_deducciones": float(self.otras_deducciones),
            "total_asignaciones": float(self.total_asignaciones),
            "total_deducciones": float(self.total_deducciones),
            "neto": float(self.neto),
            "motivo": self.motivo,
        }
