"""
Auth Service
Servicio de autenticación y gestión de usuarios

Maneja el inicio y cierre de sesión, la verificación de credenciales
(PBKDF2), el bloqueo por intentos fallidos y la administración de
cuentas con roles. Registra en auditoría cada operación.
"""

from datetime import timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models import Usuario, RolUsuario
from src.repositories import UsuarioRepository
from src.utils.security import SecurityValidator
from src.utils.audit_logger import AuditEventType, get_audit_logger
import logging

logger = logging.getLogger(__name__)

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
            # El bloqueo puede ser permanente (lo levanta un administrador)
            # o temporal, en cuyo caso se libera solo al cumplirse el plazo.
            if self._bloqueo_temporal_cumplido(usuario):
                logger.info("Bloqueo temporal cumplido para %s: cuenta liberada", username)
            else:
                self._audit_fallido(username, "cuenta bloqueada")
                raise ValueError("La cuenta está bloqueada. Contacte al administrador.")

        if not usuario.activo:
            self._audit_fallido(username, "cuenta inactiva")
            raise ValueError("La cuenta está desactivada. Contacte al administrador.")

        max_intentos = self.max_intentos_fallidos()
        if not SecurityValidator.verify_password(password, usuario.password_hash):
            usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
            if usuario.intentos_fallidos >= max_intentos:
                usuario.bloqueado = 1
                usuario.bloqueado_hasta = self._now() + timedelta(
                    minutes=self.bloqueo_minutos()
                )
                self.session.commit()
                self._audit_fallido(username, "cuenta bloqueada por intentos fallidos")
                raise ValueError("Demasiados intentos fallidos. La cuenta ha sido bloqueada.")
            self.session.commit()
            restantes = max_intentos - usuario.intentos_fallidos
            self._audit_fallido(username, "contraseña incorrecta")
            raise ValueError(
                f"Usuario o contraseña incorrectos. " f"Intentos restantes: {restantes}"
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
        self, usuario: Usuario, nueva_password: str, actual_password: str | None = None
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
            if not SecurityValidator.verify_password(actual_password, usuario.password_hash):
                raise ValueError("La contraseña actual es incorrecta")

        minimo = self.longitud_minima_password()
        if len(nueva_password or "") < minimo:
            raise ValueError(
                f"La nueva contraseña debe tener al menos {minimo} caracteres"
            )

        # Rotar por obligación no tiene sentido si se repite la vigente, así
        # que se compara también contra la contraseña actual.
        if SecurityValidator.verify_password(nueva_password, usuario.password_hash):
            raise ValueError("La nueva contraseña no puede ser igual a la actual")

        historial = self.historial_password()
        if historial > 0 and self._password_repetida(usuario, nueva_password, historial):
            raise ValueError(
                f"No puede reutilizar ninguna de sus últimas {historial} contraseñas"
            )

        hash_anterior = usuario.password_hash
        usuario.password_hash = SecurityValidator.hash_password(nueva_password)
        usuario.recordar_password(hash_anterior, historial)
        usuario.fecha_cambio_password = self._now()
        usuario.debe_cambiar_password = 0
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        self.session.commit()
        self._audit_exitoso(
            AuditEventType.DATA_UPDATE,
            usuario.username,
            entity_id=usuario.id,
            details={"operacion": "cambio_password"},
        )
        return True

    # ------------------------------------------------------------------
    # Administración de usuarios (admin)
    # ------------------------------------------------------------------
    def crear_usuario(
        self,
        username: str,
        password: str,
        rol: str,
        nombre_completo: str = "",
        debe_cambiar_password: bool = True,
    ) -> Usuario:
        """Crea un nuevo usuario de sistema"""
        username = (username or "").strip()
        if not username:
            raise ValueError("El nombre de usuario es requerido")

        if self.repository.get_by_username(username):
            raise ValueError("Ya existe un usuario con ese nombre")

        minimo = self.longitud_minima_password()
        if len(password or "") < minimo:
            raise ValueError(f"La contraseña debe tener al menos {minimo} caracteres")

        if rol not in RolUsuario.values():
            raise ValueError(f"Rol inválido. Roles válidos: {', '.join(RolUsuario.values())}")

        usuario = Usuario(
            username=username,
            password_hash=SecurityValidator.hash_password(password),
            nombre_completo=(nombre_completo or "").strip() or None,
            rol=rol,
            activo=1,
            debe_cambiar_password=1 if debe_cambiar_password else 0,
            fecha_cambio_password=self._now(),
        )
        creado = self.repository.create(usuario)
        self._audit_exitoso(
            AuditEventType.DATA_CREATE,
            creado.username,
            entity_id=creado.id,
            details={"rol": rol},
        )
        return creado

    def actualizar_usuario(
        self, usuario_id: int, datos: dict, usuario_actual: Usuario | None = None
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
            usuario.password_hash = SecurityValidator.hash_password(str(datos["password"]))
            usuario.debe_cambiar_password = 1

        self.session.commit()
        self._audit_exitoso(
            AuditEventType.DATA_UPDATE,
            usuario.username,
            entity_id=usuario.id,
            details={"operacion": "actualizar_usuario"},
        )
        return usuario

    def listar_usuarios(self) -> list[Usuario]:
        """Lista todos los usuarios del sistema"""
        return self.repository.get_all()

    def listar_roles(self) -> list[str]:
        """Lista los roles disponibles"""
        return [rol.value for rol in RolUsuario]

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Política de credenciales
    # ------------------------------------------------------------------
    def _config(self, clave: str, por_defecto):
        """Lee un parámetro de configuración de seguridad sin romperse"""
        try:
            from src.repositories import ConfiguracionRepository

            valor = ConfiguracionRepository(self.session).get_valor(clave, por_defecto)
            return por_defecto if valor is None else valor
        except (SQLAlchemyError, ValueError, TypeError):
            logger.debug("No se pudo leer la configuración %s", clave, exc_info=True)
            return por_defecto

    def _config_int(self, clave: str, por_defecto: int) -> int:
        """Lee un parámetro entero de seguridad"""
        try:
            return int(self._config(clave, por_defecto))
        except (TypeError, ValueError):
            return por_defecto

    def max_intentos_fallidos(self) -> int:
        """Intentos fallidos permitidos antes de bloquear la cuenta"""
        return max(1, self._config_int("max_intentos_fallidos", MAX_INTENTOS_FALLIDOS))

    def bloqueo_minutos(self) -> int:
        """Minutos que dura el bloqueo temporal por intentos fallidos"""
        return max(1, self._config_int("bloqueo_minutos", 15))

    def longitud_minima_password(self) -> int:
        """Longitud mínima exigida a una contraseña"""
        return max(1, self._config_int("password_min_longitud", LONGITUD_MINIMA_PASSWORD))

    def historial_password(self) -> int:
        """Contraseñas anteriores que no se pueden repetir"""
        return max(0, self._config_int("password_historial", 3))

    def dias_caducidad_password(self) -> int:
        """Días de vigencia de una contraseña (0 = sin caducidad)"""
        return max(0, self._config_int("password_dias_caducidad", 90))

    def _bloqueo_temporal_cumplido(self, usuario: Usuario) -> bool:
        """
        Libera la cuenta si su bloqueo temporal ya venció

        Un bloqueo sin fecha de expiración es definitivo y solo lo levanta
        un administrador.
        """
        if usuario.bloqueado_hasta is None:
            return False
        if self._now() < usuario.bloqueado_hasta:
            return False
        usuario.bloqueado = 0
        usuario.bloqueado_hasta = None
        usuario.intentos_fallidos = 0
        self.session.commit()
        return True

    def _password_repetida(self, usuario: Usuario, nueva_password: str, historial: int) -> bool:
        """Indica si la nueva contraseña ya fue usada recientemente"""
        if historial <= 0:
            return False
        for hash_anterior in usuario.historial_hashes[:historial]:
            if SecurityValidator.verify_password(nueva_password, hash_anterior):
                return True
        return False

    def password_caducada(self, usuario: Usuario) -> bool:
        """Indica si la contraseña del usuario superó su vigencia"""
        return not usuario.password_vigente(self.dias_caducidad_password())

    def marcar_cambio_obligatorio_si_caducada(self, usuario: Usuario) -> bool:
        """
        Marca la cuenta para cambio obligatorio cuando la contraseña expiró

        Returns:
            bool: True si la cuenta quedó marcada para cambiar contraseña.
        """
        if usuario.debe_cambiar_password or not self.password_caducada(usuario):
            return False
        usuario.debe_cambiar_password = 1
        self.session.commit()
        self._audit_exitoso(
            AuditEventType.SECURITY_PERMISSION_DENIED,
            usuario.username,
            entity_id=usuario.id,
            details={"motivo": "contraseña caducada"},
        )
        return True

    def desbloquear_usuario(self, usuario_id: int) -> Usuario:
        """Levanta el bloqueo de una cuenta (acción de administrador)"""
        usuario = self.repository.get_by_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado")
        usuario.bloqueado = 0
        usuario.bloqueado_hasta = None
        usuario.intentos_fallidos = 0
        self.session.commit()
        self._audit_exitoso(
            AuditEventType.DATA_UPDATE,
            usuario.username,
            entity_id=usuario.id,
            details={"operacion": "desbloquear_usuario"},
        )
        return usuario

    def usuario_por_id(self, usuario_id: int) -> Usuario | None:
        return self.repository.get_by_id(usuario_id)

    def usuario_por_username(self, username: str) -> Usuario | None:
        return self.repository.get_by_username(username)

    def _now(self):
        from src.utils.helpers import utcnow

        return utcnow()

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
            logger.warning(
                "%s: operación auxiliar falló (se continúa)", "_audit_exitoso", exc_info=True
            )

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
            logger.warning(
                "%s: operación auxiliar falló (se continúa)", "_audit_fallido", exc_info=True
            )


def ensure_default_admin(session: Session) -> Usuario | None:
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
