"""
Usuario Model
Modelo de datos para usuarios del sistema (autenticación y roles)
"""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime
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
