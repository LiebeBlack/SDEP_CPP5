"""
Token Sesion Model
Modelo de datos de los tokens de sesión

Un token de sesión autoriza operaciones sensibles (por ahora, registrar
o modificar notas) durante un tiempo limitado y con un alcance concreto.
En la base de datos solo se guarda el hash SHA-256 del token: quien lea
la tabla no puede reutilizarlo. El token en claro se entrega una única
vez, al emitirlo.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel

if TYPE_CHECKING:
    from .usuario import Usuario


def _utcnow() -> datetime:
    """Fecha/hora UTC actual sin zona horaria (la base guarda naive)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TokenSesion(Base, BaseModel):
    """
    Modelo de token de sesión

    Atributos:
        usuario_id: Cuenta que solicitó el token
        token_hash: Hash SHA-256 del token (nunca el token en claro)
        rol: Rol de la cuenta al emitirlo (evita releerlo en cada uso)
        alcance: Ámbito autorizado (por ahora "academico")
        expira_en: Momento en que el token deja de ser válido
        revocado_en: Momento de revocación explícita (None = vigente)
    """

    __tablename__ = "tokens_sesion"

    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    alcance: Mapped[str] = mapped_column(
        String(30), nullable=False, default="academico", index=True
    )
    expira_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revocado_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relaciones
    usuario: Mapped["Usuario"] = relationship("Usuario")

    def vigente(self, momento: datetime | None = None) -> bool:
        """
        Indica si el token sigue siendo utilizable

        Args:
            momento: Instante de referencia (por defecto, ahora en UTC)
        """
        if self.revocado_en is not None:
            return False
        return self.expira_en > (momento or _utcnow())

    @property
    def username(self) -> str | None:
        """Nombre de usuario que solicitó el token"""
        return self.usuario.username if self.usuario is not None else None

    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario (sin exponer el hash completo)"""
        data = super().to_dict()
        data.pop("token_hash", None)
        data["usuario"] = self.username
        return data
