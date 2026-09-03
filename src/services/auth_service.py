"""
Auth Service
Servicio de autenticación y gestión de usuarios

Maneja el inicio y cierre de sesión, la verificación de credenciales
(PBKDF2), el bloqueo por intentos fallidos y la administración de
cuentas con roles. Registra en auditoría cada operación.
"""

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.models import Usuario, RolUsuario
from src.repositories import UsuarioRepository
from src.utils.security import SecurityValidator
from src.utils.audit_logger import AuditEventType, get_audit_logger

MAX_INTENTOS_FALLIDOS = 5
LONGITUD_MINIMA_PASSWORD = 6

# Credenciales del usuario administrador creado en el primer arranque
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


class AuthService:
    """
    Servicio de autenticación

    Encapsula la lógica de seguridad de acceso: verificación de
    credenciales, control de intentos fallidos, bloqueo de cuentas
    y administración de usuarios.
    """

    def __init__(self, session: Session):
        self.session = session
        self.repository = UsuarioRepository(session)

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------
    def autenticar(self, username: str, password: str) -> Usuario:
        """
        Autentica un usuario con nombre de usuario y contraseña

        Raises:
            ValueError: Si las credenciales son inválidas o la cuenta
                está inactiva o bloqueada
        """
        username = (username or "").strip()
        usuario = self.repository.get_by_username(username)

        if not usuario:
            self._audit_fallido(username, "usuario inexistente")
            raise ValueError("Usuario o contraseña incorrectos")

        if usuario.bloqueado:
            self._audit_fallido(username, "cuenta bloqueada")
            raise ValueError("La cuenta está bloqueada. Contacte al administrador.")

        if not usuario.activo:
            self._audit_fallido(username, "cuenta inactiva")
            raise ValueError("La cuenta está desactivada. Contacte al administrador.")

        if not SecurityValidator.verify_password(password, usuario.password_hash):
            usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
            if usuario.intentos_fallidos >= MAX_INTENTOS_FALLIDOS:
                usuario.bloqueado = 1
                self.session.commit()
                self._audit_fallido(
                    username, "cuenta bloqueada por intentos fallidos"
                )
                raise ValueError(
                    "Demasiados intentos fallidos. La cuenta ha sido bloqueada."
                )
            self.session.commit()
            restantes = MAX_INTENTOS_FALLIDOS - usuario.intentos_fallidos
            self._audit_fallido(username, "contraseña incorrecta")
            raise ValueError(
                f"Usuario o contraseña incorrectos. "
                f"Intentos restantes: {restantes}"
            )

        # Éxito: resetear contadores y registrar acceso
        usuario.intentos_fallidos = 0
        usuario.ultimo_login = self._now()
        self.session.commit()
        self._audit_exitoso(AuditEventType.USER_LOGIN, username)
        return usuario

    def cerrar_sesion(self, username: str) -> None:
        """Registra el cierre de sesión de un usuario"""
        self._audit_exitoso(AuditEventType.USER_LOGOUT, username)

    # ------------------------------------------------------------------
    # Cambio de contraseña
    # ------------------------------------------------------------------
    def cambiar_password(
        self, usuario: Usuario, nueva_password: str, actual_password: Optional[str] = None
    ) -> bool:
        """
        Cambia la contraseña de un usuario

        Si se entrega actual_password se valida contra la contraseña
        vigente antes de cambiarla.

        Raises:
            ValueError: Si la contraseña actual es incorrecta o la
                nueva no cumple los requisitos
        """
        if actual_password is not None:
            if not SecurityValidator.verify_password(
                actual_password, usuario.password_hash
            ):
                raise ValueError("La contraseña actual es incorrecta")

        if len(nueva_password or "") < LONGITUD_MINIMA_PASSWORD:
            raise ValueError(
                f"La nueva contraseña debe tener al menos "
                f"{LONGITUD_MINIMA_PASSWORD} caracteres"
            )

        usuario.password_hash = SecurityValidator.hash_password(nueva_password)
        usuario.debe_cambiar_password = 0
        self.session.commit()
        self._audit_exitoso(
            AuditEventType.DATA_UPDATE, usuario.username,
            entity_id=usuario.id,
            details={"operacion": "cambio_password"},
        )
        return True

    # ------------------------------------------------------------------
    # Administración de usuarios (admin)
    # ------------------------------------------------------------------
    def crear_usuario(
        self, username: str, password: str, rol: str,
        nombre_completo: str = "", debe_cambiar_password: bool = True,
    ) -> Usuario:
        """Crea un nuevo usuario de sistema"""
        username = (username or "").strip()
        if not username:
            raise ValueError("El nombre de usuario es requerido")

        if self.repository.get_by_username(username):
            raise ValueError("Ya existe un usuario con ese nombre")

        if len(password or "") < LONGITUD_MINIMA_PASSWORD:
            raise ValueError(
                f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres"
            )

        if rol not in RolUsuario.values():
            raise ValueError(f"Rol inválido. Roles válidos: {', '.join(RolUsuario.values())}")

        usuario = Usuario(
            username=username,
            password_hash=SecurityValidator.hash_password(password),
            nombre_completo=(nombre_completo or "").strip() or None,
            rol=rol,
            activo=1,
            debe_cambiar_password=1 if debe_cambiar_password else 0,
        )
        creado = self.repository.create(usuario)
        self._audit_exitoso(
            AuditEventType.DATA_CREATE, creado.username,
            entity_id=creado.id,
            details={"rol": rol},
        )
        return creado

    def actualizar_usuario(
        self, usuario_id: int, datos: Dict, usuario_actual: Optional[Usuario] = None
    ) -> Usuario:
        """
        Actualiza datos de un usuario (rol, nombre, estado)

        Impide desactivar o degradar a la propia cuenta administradora
        para evitar quedarse sin acceso.
        """
        usuario = self.repository.get_by_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")

        if "username" in datos and datos["username"]:
            nuevo_username = str(datos["username"]).strip()
            if nuevo_username != usuario.username:
                if self.repository.get_by_username(nuevo_username):
                    raise ValueError("Ya existe un usuario con ese nombre")
                usuario.username = nuevo_username

        if "rol" in datos and datos["rol"]:
            if datos["rol"] not in RolUsuario.values():
                raise ValueError("Rol inválido")
            if (
                usuario_actual is not None
                and usuario_actual.id == usuario.id
                and datos["rol"] != RolUsuario.ADMIN.value
            ):
                raise ValueError("No puede degradar su propia cuenta de administrador")
            usuario.rol = datos["rol"]

        if "nombre_completo" in datos:
            usuario.nombre_completo = str(datos["nombre_completo"] or "").strip() or None

        if "activo" in datos and datos["activo"] is not None:
            if usuario_actual is not None and usuario_actual.id == usuario.id:
                raise ValueError("No puede desactivar su propia cuenta")
            usuario.activo = 1 if int(datos["activo"]) else 0

        if "password" in datos and datos["password"]:
            usuario.password_hash = SecurityValidator.hash_password(
                str(datos["password"])
            )
            usuario.debe_cambiar_password = 1

        self.session.commit()
        self._audit_exitoso(
            AuditEventType.DATA_UPDATE, usuario.username,
            entity_id=usuario.id,
            details={"operacion": "actualizar_usuario"},
        )
        return usuario

    def listar_usuarios(self) -> List[Usuario]:
        """Lista todos los usuarios del sistema"""
        return self.repository.get_all()

    def listar_roles(self) -> List[str]:
        """Lista los roles disponibles"""
        return RolUsuario.values()

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def usuario_por_id(self, usuario_id: int) -> Optional[Usuario]:
        return self.repository.get_by_id(usuario_id)

    def usuario_por_username(self, username: str) -> Optional[Usuario]:
        return self.repository.get_by_username(username)

    def _now(self):
        from datetime import datetime
        return datetime.utcnow()

    def _audit_exitoso(self, event_type, username, entity_id=None, details=None):
        try:
            audit = get_audit_logger()
            if audit:
                audit.log_event(
                    event_type=event_type,
                    entity_type="usuario",
                    entity_id=entity_id,
                    user=username or "system",
                    details=details or {},
                    success=True,
                )
        except Exception:
            pass

    def _audit_fallido(self, username, motivo):
        try:
            audit = get_audit_logger()
            if audit:
                audit.log_event(
                    event_type=AuditEventType.SECURITY_AUTH_FAILURE,
                    entity_type="usuario",
                    user=username or "system",
                    details={"motivo": motivo},
                    success=False,
                )
        except Exception:
            pass


def ensure_default_admin(session: Session) -> Usuario:
    """
    Crea el usuario administrador por defecto si no existe ningún usuario

    Se invoca en el arranque del sistema la primera vez. La contraseña
    por defecto se documenta en la guía de usuario y se solicita su
    cambio en el primer inicio de sesión.
    """
    service = AuthService(session)
    if service.repository.count_activos() == 0 and service.repository.count() == 0:
        return service.crear_usuario(
            username=DEFAULT_ADMIN_USERNAME,
            password=DEFAULT_ADMIN_PASSWORD,
            rol=RolUsuario.ADMIN.value,
            nombre_completo="Administrador del Sistema",
            debe_cambiar_password=True,
        )
    return None
