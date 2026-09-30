"""
Token Sesion Service
Servicio de tokens de sesión para operaciones sensibles

Emite, valida y revoca tokens de sesión con alcance limitado (por ahora
el módulo académico). En la base solo se guarda el hash SHA-256 del token:
si alguien lee la tabla no puede reutilizarlo. La autorización efectiva
para escribir notas se resuelve con el rol vigente del usuario y, en el
caso de los docentes, con el grado que tienen asignado.
"""

import hashlib
import logging
import secrets
from datetime import timedelta

from sqlalchemy.orm import Session

from src.models import Grado, RolUsuario, TokenSesion, Usuario
from src.repositories import TokenSesionRepository, UsuarioRepository
from src.utils.helpers import utcnow

logger = logging.getLogger(__name__)

# Alcance y duración por defecto de un token académico
ALCANCE_ACADEMICO = "academico"
DURACION_MINUTOS = 480  # una jornada laboral
LONGITUD_TOKEN = 32  # 32 bytes -> 43 caracteres url-safe

# Roles que pueden escribir notas en cualquier grado (administración)
ROLES_ESCRITURA_ACADEMICA = (RolUsuario.ADMIN.value, RolUsuario.MANAGER.value)


class TokenSesionService:
    """
    Servicio de tokens de sesión

    El token en claro se entrega una única vez (al emitirlo); el servicio
    solo persiste su hash. La validación comprueba que el token exista, no
    esté revocado, no haya expirado y que la cuenta siga activa.
    """

    def __init__(self, session: Session):
        self.session = session
        self.repository = TokenSesionRepository(session)
        self._usuarios = UsuarioRepository(session)

    # ------------------------------------------------------------------
    # Emisión, validación y revocación
    # ------------------------------------------------------------------
    @staticmethod
    def _hash(token: str) -> str:
        """Hash SHA-256 del token (lo único que se guarda)"""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def emitir(
        self,
        usuario: Usuario | None,
        alcance: str = ALCANCE_ACADEMICO,
        minutos: int = DURACION_MINUTOS,
    ) -> tuple[str, TokenSesion]:
        """
        Emite un token de sesión para una cuenta

        Args:
            usuario: Cuenta autenticada que solicita el token
            alcance: Ámbito autorizado (por defecto, académico)
            minutos: Vigencia del token en minutos

        Returns:
            tuple: (token en claro, registro TokenSesion)

        Raises:
            ValueError: Si no hay usuario, la cuenta está inactiva o los
                parámetros no son válidos
        """
        if usuario is None or not getattr(usuario, "id", None):
            raise ValueError("Se requiere un usuario autenticado para emitir el token")
        if not getattr(usuario, "activo", 0):
            raise ValueError("La cuenta está desactivada: no se pueden emitir tokens")
        if not alcance:
            raise ValueError("El alcance del token es requerido")

        token = secrets.token_urlsafe(LONGITUD_TOKEN)
        registro = TokenSesion(
            usuario_id=int(usuario.id),
            token_hash=self._hash(token),
            rol=usuario.rol_valor,
            alcance=alcance,
            expira_en=utcnow() + timedelta(minutes=max(1, int(minutos))),
        )
        creado = self.repository.create(registro)
        logger.info("Token de sesión emitido para %s (alcance %s)", usuario.username, alcance)
        return token, creado

    def validar(self, token: str | None, alcance: str | None = ALCANCE_ACADEMICO) -> TokenSesion | None:
        """
        Valida un token y devuelve su registro, o None si no sirve

        Se comprueba el hash (sin comparar el token en claro), la vigencia,
        el alcance y que la cuenta propietaria siga existiendo y activa.
        """
        if not token or not isinstance(token, str):
            return None
        registro = self.repository.get_by_hash(self._hash(token))
        if registro is None or not registro.vigente():
            return None
        if alcance and registro.alcance != alcance:
            return None
        usuario = self._usuarios.get_by_id(registro.usuario_id)
        if usuario is None or not usuario.activo:
            return None
        return registro

    def revocar(self, token: str | None) -> bool:
        """Revoca un token concreto (cierre de sesión o pérdida del equipo)"""
        if not token or not isinstance(token, str):
            return False
        registro = self.repository.get_by_hash(self._hash(token))
        if registro is None or registro.revocado_en is not None:
            return False
        registro.revocado_en = utcnow()
        self.session.commit()
        logger.info("Token de sesión revocado (usuario %s)", registro.username)
        return True

    def revocar_usuario(
        self, usuario_id: int, alcance: str | None = ALCANCE_ACADEMICO
    ) -> int:
        """Revoca todos los tokens vigentes de una cuenta (desactivación, robo)"""
        return self.repository.revocar_usuario(usuario_id, alcance)

    def limpiar_expirados(self) -> int:
        """Elimina los tokens expirados o revocados"""
        return self.repository.eliminar_expirados()

    # ------------------------------------------------------------------
    # Permisos académicos
    # ------------------------------------------------------------------
    def puede_escribir(self, sesion: TokenSesion, grado: Grado | None = None) -> bool:
        """
        Indica si el token puede registrar o modificar notas

        Administración (admin/gestor) escribe en cualquier grado; un docente
        solo en el grado que tiene asignado (grado.profesor_id) y siempre que
        su rol vigente lo permita (un usuario "solo lectura" no escribe, ni
        aunque aparezca asignado). Se consulta el rol actual, no el del
        momento de emitir el token, para que una degradación de rol surta
        efecto de inmediato.
        """
        usuario = sesion.usuario
        if usuario is None or not usuario.activo:
            return False
        rol = usuario.rol_valor
        if rol in ROLES_ESCRITURA_ACADEMICA:
            return True
        if grado is None or grado.profesor_id is None:
            return False
        return rol == RolUsuario.USER.value and int(sesion.usuario_id) == int(grado.profesor_id)

    def tokens_vigentes(self, usuario_id: int | None = None) -> list[TokenSesion]:
        """Lista los tokens vigentes (auditoría de sesiones activas)"""
        return self.repository.get_vigentes(usuario_id, ALCANCE_ACADEMICO)
