"""
Registro Movil Model
Modelo de los registros capturados desde la aplicación Android

La aplicación móvil no es un sistema aparte: se conecta al nodo central de
sincronización como un puesto más y escribe en esta tabla. Cada registro lleva
su identificador global (``uuid_movil``), que es la clave natural con la que
los demás equipos reconocen la misma fila, y las marcas de tiempo con las que
el motor de mezcla decide qué escritura es la vigente.

El borrado es lógico (``activo``), igual que en ``empleados``, porque perder un
registro recién editado es peor que conservarlo desactivado.
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseModel


def _ahora() -> datetime:
    """Fecha/hora UTC actual sin zona horaria (formato de la base)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RegistroMovil(Base, BaseModel):
    """Registro de campo creado, editado o cerrado desde la aplicación móvil"""

    __tablename__ = "registros_moviles"

    # Identidad global: el servidor la exige para poder unificar la fila si el
    # mismo registro llega desde dos dispositivos distintos.
    uuid_movil: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)

    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    contenido: Mapped[str | None] = mapped_column(Text, nullable=True)
    categoria: Mapped[str] = mapped_column(
        String(60), nullable=False, default="general", index=True
    )
    valor: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Marcas de tiempo declaradas por el dispositivo que capturó el dato. Se
    # guardan como columnas propias (no se confunden con la auditoría del
    # modelo) porque el motor de mezcla las compara entre equipos.
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=_ahora, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=_ahora, nullable=False)

    dispositivo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    usuario: Mapped[str | None] = mapped_column(String(120), nullable=True)
    activo: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)

    def to_dict(self) -> dict[str, Any]:
        """Representación serializable, con las fechas en ISO 8601"""
        datos = super().to_dict()
        for campo in ("creado_en", "actualizado_en"):
            valor = datos.get(campo)
            datos[campo] = valor.isoformat() if isinstance(valor, datetime) else valor
        return datos

    def __repr__(self) -> str:
        return f"<RegistroMovil(id={self.id}, uuid={self.uuid_movil[:8]}, titulo={self.titulo!r})>"
