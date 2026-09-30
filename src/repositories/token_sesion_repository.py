"""
Token Sesion Repository
Repositorio para operaciones de datos de los tokens de sesión
"""

import logging
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import TokenSesion
from src.utils.helpers import utcnow
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class TokenSesionRepository(BaseRepository[TokenSesion]):
    """Repositorio de tokens de sesión con manejo robusto de errores"""

    def __init__(self, session: Session):
        super().__init__(TokenSesion, session)

    def get_by_hash(self, token_hash: str) -> TokenSesion | None:
        """Obtiene un token por el hash de su valor (nunca por el valor)"""
        try:
            return (
                self.session.query(TokenSesion)
                .filter(TokenSesion.token_hash == token_hash)
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al buscar un token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al buscar un token: {e}")
            return None

    def get_vigentes(
        self, usuario_id: int | None = None, alcance: str | None = None
    ) -> list[TokenSesion]:
        """Lista los tokens vigentes (no revocados y sin expirar)"""
        try:
            query = self.session.query(TokenSesion).filter(
                TokenSesion.revocado_en.is_(None),
                TokenSesion.expira_en > utcnow(),
            )
            if usuario_id is not None:
                query = query.filter(TokenSesion.usuario_id == usuario_id)
            if alcance:
                query = query.filter(TokenSesion.alcance == alcance)
            return query.order_by(TokenSesion.expira_en.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error de base de datos al listar tokens vigentes: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar tokens vigentes: {e}")
            return []

    def revocar_usuario(self, usuario_id: int, alcance: str | None = None) -> int:
        """
        Revoca todos los tokens vigentes de una cuenta

        Se usa al cerrar sesión o al desactivar un usuario: a partir de ese
        momento ninguno de sus tokens sirve para escribir notas.
        """
        try:
            query = self.session.query(TokenSesion).filter(
                TokenSesion.usuario_id == usuario_id,
                TokenSesion.revocado_en.is_(None),
            )
            if alcance:
                query = query.filter(TokenSesion.alcance == alcance)
            cantidad = query.update({"revocado_en": utcnow()}, synchronize_session=False)
            self.session.commit()
            logger.info("Tokens revocados del usuario %s: %s", usuario_id, cantidad)
            return int(cantidad or 0)
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al revocar los tokens: {e}")
            return 0
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al revocar los tokens: {e}")
            return 0

    def eliminar_expirados(self, momento: datetime | None = None) -> int:
        """Elimina los tokens expirados o revocados (limpieza periódica)"""
        try:
            referencia = momento or utcnow()
            cantidad = (
                self.session.query(TokenSesion)
                .filter(
                    or_(
                        TokenSesion.expira_en <= referencia,
                        TokenSesion.revocado_en.isnot(None),
                    )
                )
                .delete(synchronize_session=False)
            )
            self.session.commit()
            return int(cantidad or 0)
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error de base de datos al limpiar tokens: {e}")
            return 0
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inesperado al limpiar tokens: {e}")
            return 0
