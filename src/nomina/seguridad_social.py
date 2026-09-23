"""
Cálculo de los aportes de seguridad social

Separa lo que aporta el empleado (descuento sobre su salario) de lo
que aporta el patrono (costo adicional que no se descuenta) y aplica
los techos de cotización cuando la configuración los define.
"""

from dataclasses import dataclass
from decimal import Decimal

from .tipos import CERO, Dinero, redondear


@dataclass(frozen=True, slots=True)
class AportesSeguridadSocial:
    """Aportes de un período, separando empleado y patrono"""

    seguro_empleado: Dinero = CERO
    pension_empleado: Dinero = CERO
    seguro_patronal: Dinero = CERO
    pension_patronal: Dinero = CERO
    base_seguro: Dinero = CERO
    base_pension: Dinero = CERO

    @property
    def total_empleado(self) -> Dinero:
        """Aporte total descontado al empleado"""
        return redondear(self.seguro_empleado + self.pension_empleado)

    @property
    def total_patronal(self) -> Dinero:
        """Aporte total a cargo del patrono"""
        return redondear(self.seguro_patronal + self.pension_patronal)

    @property
    def costo_total(self) -> Dinero:
        """Costo total de seguridad social del período"""
        return redondear(self.total_empleado + self.total_patronal)


def base_afectada(salario: Dinero, techo: Dinero) -> Dinero:
    """
    Base sobre la que se calcula el aporte

    Un techo en cero (o negativo) significa "sin techo": se cotiza
    sobre el salario completo. Con techo, la base se recorta al límite,
    que es como funcionan los topes de cotización.
    """
    if techo is None or techo <= CERO:
        return max(CERO, salario)
    return max(CERO, min(salario, techo))


def calcular_aporte(salario: Dinero, porcentaje: Dinero, techo: Dinero = CERO) -> Dinero:
    """Aporte resultante de aplicar un porcentaje sobre la base afectada"""
    if porcentaje <= CERO:
        return CERO
    return redondear(base_afectada(salario, techo) * porcentaje / Decimal(100))


def calcular_seguridad_social(
    salario: Dinero,
    porcentaje_seguro: Dinero,
    porcentaje_pension: Dinero,
    techo_seguro: Dinero = CERO,
    techo_pension: Dinero = CERO,
    porcentaje_seguro_patronal: Dinero = CERO,
    porcentaje_pension_patronal: Dinero = CERO,
) -> AportesSeguridadSocial:
    """
    Cálculo completo de seguridad social de un período

    Los porcentajes llegan como números (4.5 = 4.5%) tal como se cargan
    en la configuración, de modo que el usuario los vea igual que los
    escribe en pantalla.
    """
    return AportesSeguridadSocial(
        seguro_empleado=calcular_aporte(salario, porcentaje_seguro, techo_seguro),
        pension_empleado=calcular_aporte(salario, porcentaje_pension, techo_pension),
        seguro_patronal=calcular_aporte(
            salario, porcentaje_seguro_patronal, techo_seguro
        ),
        pension_patronal=calcular_aporte(
            salario, porcentaje_pension_patronal, techo_pension
        ),
        base_seguro=base_afectada(salario, techo_seguro),
        base_pension=base_afectada(salario, techo_pension),
    )
