"""
Usuario Model
Modelo de datos para usuarios del sistema (autenticación y roles)
"""

import json
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseModel
from .enums import RolUsuario


def _enum_values(enum_cls):
    return [e.value if hasattr(e, "value") else str(e) for e in enum_cls]


class Usuario(Base, BaseModel):
    """
    Modelo de usuario del sistema

    Almacena las credenciales (hash PBKDF2), el rol y el estado de
    cada cuenta con la que se accede a la aplicación.
    """

    __tablename__ = "usuarios"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_completo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    rol: Mapped[RolUsuario] = mapped_column(
        SQLEnum(RolUsuario, values_callable=_enum_values),
        nullable=False,
        default=RolUsuario.USER.value,
    )
    activo: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    debe_cambiar_password: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bloqueado: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fecha_cambio_password: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    password_historial: Mapped[str | None] = mapped_column(Text, nullable=True)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    @property
    def historial_hashes(self) -> list[str]:
        """
        Hashes de las contraseñas anteriores de la cuenta

        Se guardan como texto JSON; una entrada ilegible se ignora en
        lugar de impedir el cambio de contraseña.
        """
        if not self.password_historial:
            return []
        try:
            datos = json.loads(self.password_historial)
        except (ValueError, TypeError):
            return []
        if not isinstance(datos, list):
            return []
        return [str(item) for item in datos]

    def recordar_password(self, hash_anterior: str, limite: int) -> None:
        """
        Agrega un hash al historial conservando solo los últimos N

        Args:
            hash_anterior: Hash de la contraseña que se está reemplazando
            limite: Cuántos hashes anteriores se conservan (0 = ninguno)
        """
        if limite <= 0:
            self.password_historial = None
            return
        historial = [hash_anterior] + self.historial_hashes
        self.password_historial = json.dumps(historial[:limite])

    def password_vigente(self, dias_caducidad: int, referencia: datetime | None = None) -> bool:
        """
        Indica si la contraseña sigue vigente

        Sin caducidad configurada (0 o negativo) la contraseña no expira.
        Si nunca se registró un cambio, se usa la fecha de creación de la
        cuenta y, si tampoco existe, se considera vigente.
        """
        if dias_caducidad <= 0:
            return True
        desde = self.fecha_cambio_password or self.created_at
        if desde is None:
            return True
        momento = referencia or datetime.now()
        return (momento - desde).days <= dias_caducidad

    @property
    def rol_valor(self) -> str:
        """Valor string del rol del usuario"""
        return self.rol.value if hasattr(self.rol, "value") else str(self.rol)

    @property
    def es_admin(self) -> bool:
        return self.rol_valor == RolUsuario.ADMIN.value

    def to_dict(self):
        data = super().to_dict()
        data["rol"] = self.rol_valor
        data.pop("password_hash", None)
        return data
