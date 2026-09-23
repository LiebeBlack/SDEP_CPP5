"""
Contrato Model
Modelo de datos de los contratos laborales

Representa el vínculo contractual de cada empleado: tipo, vigencia,
salario pactado y estado dentro de su ciclo de vida (vigente, por
vencer, vencido, renovado o terminado).
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel
from .enums import EstadoContrato, TipoContrato, valores_sql

if TYPE_CHECKING:
    from .empleado import Empleado


DIAS_UMBRAL_VENCIMIENTO = 30
CERO = Decimal("0.00")


class Contrato(Base, BaseModel):
    """
    Modelo de contrato laboral

    Atributos:
        empleado_id: Empleado contratado
        numero: Número único de contrato
        tipo: Indefinido, temporal, por obra o pasantía
        estado: Estado dentro del ciclo de vida del contrato
        cargo: Cargo pactado
        departamento: Departamento o unidad donde presta servicio
        salario_pactado: Salario mensual acordado
        horas_semanales: Jornada semanal pactada en horas
        fecha_inicio: Inicio de la vigencia
        fecha_fin: Fin de la vigencia (None si es indefinido)
        renovacion_automatica: Indica si se renueva al vencer (1 = sí)
        contrato_anterior_id: Contrato que este renueva, si aplica
        archivo_ruta: Ruta del documento firmado
        clausulas: Condiciones particulares
        motivo_terminacion: Razón de la terminación anticipada
        fecha_terminacion: Fecha efectiva de terminación
        liquidacion_monto: Monto del finiquito ya generado
        aprobado_por: Usuario que aprobó el contrato
        observaciones: Notas adicionales
    """

    __tablename__ = "contratos"

    empleado_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("empleados.id"), nullable=False, index=True
    )
    numero: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    tipo: Mapped[TipoContrato] = mapped_column(
        SQLEnum(TipoContrato, values_callable=valores_sql),
        nullable=False,
        default=TipoContrato.INDEFINIDO.value,
    )
    estado: Mapped[EstadoContrato] = mapped_column(
        SQLEnum(EstadoContrato, values_callable=valores_sql),
        nullable=False,
        default=EstadoContrato.VIGENTE.value,
        index=True,
    )
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)
    departamento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salario_pactado: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    horas_semanales: Mapped[int] = mapped_column(Integer, nullable=False, default=40)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    renovacion_automatica: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    contrato_anterior_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("contratos.id"), nullable=True
    )
    archivo_ruta: Mapped[str | None] = mapped_column(String(255), nullable=True)
    clausulas: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo_terminacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_terminacion: Mapped[date | None] = mapped_column(Date, nullable=True)
    liquidacion_monto: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=CERO
    )
    aprobado_por: Mapped[str | None] = mapped_column(String(50), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    empleado: Mapped["Empleado"] = relationship("Empleado", back_populates="contratos")

    # ------------------------------------------------------------------
    # Consultas de vigencia
    # ------------------------------------------------------------------
    @property
    def tipo_valor(self) -> str:
        """Valor string del tipo de contrato"""
        return self.tipo.value if hasattr(self.tipo, "value") else str(self.tipo)

    @property
    def estado_valor(self) -> str:
        """Valor string del estado del contrato"""
        return self.estado.value if hasattr(self.estado, "value") else str(self.estado)

    @property
    def es_indefinido(self) -> bool:
        """Indica si el contrato no tiene fecha de fin"""
        return self.fecha_fin is None

    @property
    def dias_vigencia(self) -> int:
        """
        Días totales pactados

        Para contratos indefinidos devuelve los días transcurridos
        desde el inicio hasta hoy.
        """
        if self.fecha_inicio is None:
            return 0
        fin = self.fecha_fin or date.today()
        return max(0, (fin - self.fecha_inicio).days)

    @property
    def dias_para_vencer(self) -> int | None:
        """
        Días que faltan para el vencimiento

        Devuelve None si el contrato es indefinido o ya terminó, y un
        valor negativo cuando la fecha de fin ya pasó.
        """
        if self.fecha_fin is None or self.estado_valor == EstadoContrato.TERMINADO.value:
            return None
        return (self.fecha_fin - date.today()).days

    def por_vencer(self, dias: int = DIAS_UMBRAL_VENCIMIENTO) -> bool:
        """
        Indica si el contrato está vigente y vence dentro del umbral

        Args:
            dias: Días de anticipación con los que se avisa
        """
        restantes = self.dias_para_vencer
        if restantes is None:
            return False
        return 0 <= restantes <= max(0, int(dias))

    @property
    def esta_vigente(self) -> bool:
        """Indica si el contrato sigue vigente a la fecha de hoy"""
        if self.estado_valor == EstadoContrato.TERMINADO.value:
            return False
        if self.fecha_fin is None:
            return True
        return self.fecha_fin >= date.today()

    @property
    def salario_diario(self) -> Decimal:
        """Salario diario derivado del salario mensual pactado"""
        if not self.salario_pactado:
            return CERO
        return (Decimal(self.salario_pactado) / Decimal(30)).quantize(Decimal("0.01"))

    @property
    def salario_hora(self) -> Decimal:
        """Valor de la hora ordinaria derivado de la jornada semanal pactada"""
        if not self.salario_pactado:
            return CERO
        horas_mes = Decimal(self.horas_semanales or 40) * Decimal(4.33)
        if horas_mes <= 0:
            horas_mes = Decimal(40) * Decimal(4.33)
        return (Decimal(self.salario_pactado) / horas_mes).quantize(Decimal("0.01"))

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario con campos calculados"""
        data = super().to_dict()
        data["tipo"] = self.tipo_valor
        data["estado"] = self.estado_valor
        data["esta_vigente"] = self.esta_vigente
        data["dias_vigencia"] = self.dias_vigencia
        data["dias_para_vencer"] = self.dias_para_vencer
        data["por_vencer"] = self.por_vencer()
        data["salario_diario"] = float(self.salario_diario)
        data["salario_hora"] = float(self.salario_hora)
        return data
