"""
Usuario Repository
Repositorio para operaciones de datos de usuarios
"""

from typing import cast

from sqlalchemy.orm import Session

from src.models import Usuario

from .base_repository import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    """Repositorio de usuarios"""

    def __init__(self, session: Session):
        super().__init__(Usuario, session)

    def get_by_username(self, username: str) -> Usuario | None:
        """Obtiene un usuario por nombre de usuario"""
        return cast(Usuario | None, self.session.query(Usuario).filter(Usuario.username == username).first())

    def get_activos(self) -> list[Usuario]:
        """Obtiene usuarios activos"""
        return cast(list[Usuario], self.session.query(Usuario).filter(Usuario.activo == 1).all())

    def count_activos(self) -> int:
        """Cuenta usuarios activos"""
        return cast(int, self.session.query(Usuario).filter(Usuario.activo == 1).count())
