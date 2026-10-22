"""
Contexto de sesión para el aislamiento por cédula

La aplicación de escritorio y el nodo central comparten el mismo proceso de
negocio, pero no el mismo hilo: cada petición HTTP del nodo central corre en su
propio hilo y el agente de sincronización también. Por eso el contexto se guarda
en un ``ContextVar``: un contexto establecido en la interfaz no se filtra al
servidor ni a los trabajos de fondo.

Solo el rol ``user`` (WORKER) se considera restringido. Un ``user`` sin cédula
no puede iniciar sesión: la regla se valida en ``AuthService``.
"""

from __future__ import annotations

import re
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class ContextoSesion:
    """Identidad mínima necesaria para decidir qué filas puede ver una sesión."""

    usuario_id: int
    username: str
    rol: str
    cedula: str | None = None

    @property
    def es_trabajador(self) -> bool:
        return self.rol == "user"


_ACTUAL: ContextVar[ContextoSesion | None] = ContextVar("sdep_contexto_sesion", default=None)
_PATRON_CEDULA = re.compile(r"[^0-9A-Za-z-]")


def normalizar_cedula(valor: object) -> str:
    """Normaliza una cédula para compararla entre pantallas y bases.

    Se aceptan formatos como ``V-12.345.678`` y ``v 12345678``; la comparación
    se hace sin puntos, espacios ni minúsculas. Las cédulas solo contienen
    dígitos y, en Venezuela, un prefijo de nacionalidad.
    """
    texto = str(valor or "").strip().upper()
    return _PATRON_CEDULA.sub("", texto)


def establecer(
    usuario_id: int,
    username: str,
    rol: str,
    cedula: str | None = None,
) -> ContextoSesion:
    """Activa el contexto de una sesión en el hilo actual."""
    contexto = ContextoSesion(
        usuario_id=int(usuario_id or 0),
        username=str(username or ""),
        rol=str(rol or ""),
        cedula=normalizar_cedula(cedula) or None,
    )
    _ACTUAL.set(contexto)
    return contexto


def limpiar() -> None:
    """Desactiva el contexto del hilo actual."""
    _ACTUAL.set(None)


def actual() -> ContextoSesion | None:
    """Contexto activo, o ``None`` cuando la consulta es interna/global."""
    return _ACTUAL.get()
