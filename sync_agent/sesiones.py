"""
Sesiones de usuario del nodo central

La aplicación móvil (y cualquier cliente del protocolo 2) entra con **usuario y
contraseña de la tabla ``usuarios``** de la base institucional: exactamente las
mismas cuentas que usa la aplicación de escritorio, con el mismo bloqueo por
intentos, la misma caducidad y el mismo historial de contraseñas, porque quien
valida sigue siendo ``AuthService``.

El cliente recibe un **token aleatorio de 256 bits** que se guarda hasheado
(SHA-256): en la base no queda nada recuperable. La vida del token es
deslizante (cada petición válida la alarga) con un tope absoluto, de modo que
una sesión usada a diario sigue abierta pero un token olvidado caduca solo.

El teléfono no guarda contraseñas en ningún momento: con el token y el
desbloqueo biométrico basta para volver a entrar durante la ventana offline
configurada en la app.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.security.contexto import normalizar_cedula
from sync_agent import cuentas
from sync_agent.comun import ahora_utc
from sync_agent.esquema import SesionApi

logger = logging.getLogger(__name__)

# Vida deslizante: cada petición válida alarga la sesión hasta este máximo
VIDA_RELATIVA_HORAS = 12
# Tope absoluto: aunque se use a diario, la sesión se renueva tras esta vida
VIDA_ABSOLUTA_DIAS = 7
LONGITUD_TOKEN = 32


class ErrorSesion(Exception):
    """La sesión no sirve; ``codigo`` es el estado HTTP con el que responder"""

    def __init__(self, mensaje: str, codigo: int = 401):
        super().__init__(mensaje)
        self.codigo = codigo


@dataclass(frozen=True)
class SesionValida:
    """Datos de una sesión ya verificada, listos para la capa de acciones"""

    token_hash: str
    username: str
    nombre_completo: str | None
    rol: str
    dispositivo_id: str | None
    expira_en: datetime
    debe_cambiar_password: bool = False
    usuario_id: int = 0
    cedula: str | None = None


def hash_token(token: str) -> str:
    """SHA-256 del token: los tokens son aleatorios de 256 bits, no contraseñas"""
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def codigo_de_credencial(mensaje: str) -> int:
    """
    Código HTTP que corresponde a un rechazo de ``AuthService``

    El cliente móvil distingue la cuenta bloqueada (423) de la desactivada
    (403) y del par usuario/contraseña incorrectos (401). Antes todo salía
    como 401 y la app no podía explicar el motivo real al usuario.
    """
    texto = (mensaje or "").lower()
    if "bloqueada" in texto or "intentos fallidos" in texto:
        return 423
    if "desactivada" in texto:
        return 403
    return 401


class GestorSesiones:
    """
    Emisión, validación y cierre de sesiones de usuario

    Trabaja contra la misma base que el nodo central y delega la política de
    credenciales en ``AuthService``: la regla de acceso no se reimplementa aquí,
    se consulta a la única que existe.
    """

    def __init__(
        self,
        session_factory,
        vida_relativa_horas: int = VIDA_RELATIVA_HORAS,
        url_central: str | None = None,
    ):
        """
        Args:
            session_factory: Fábrica de sesiones SQLAlchemy de la base central
            vida_relativa_horas: Horas que vive (y se alarga) cada sesión
            url_central: URL de la base central; permite mantener sus cuentas
                alineadas con la base institucional del escritorio
        """
        self._fabrica = session_factory
        self.vida_relativa = max(1, int(vida_relativa_horas))
        self.url_central = url_central or ""

    # ------------------------------------------------------------------
    # Login y cierre
    # ------------------------------------------------------------------
    def iniciar(self, username: str, password: str, dispositivo_id: str | None = None) -> dict:
        """
        Valida las credenciales contra la tabla ``usuarios`` y emite un token

        Raises:
            ErrorSesion: 401 con el mensaje de ``AuthService`` (usuario o
                contraseña incorrectos, cuenta bloqueada o desactivada)
        """
        from src.services.auth_service import AuthService

        sesion = self._fabrica()
        try:
            servicio = AuthService(sesion)
            try:
                usuario = servicio.autenticar(username or "", password or "")
            except ValueError as error:
                # La copia central puede haberse quedado atrás: el caso típico
                # es la contraseña que el usuario cambió en el escritorio con
                # el sistema ya abierto. Si la contraseña presentada sí es la
                # de la base institucional, se refresca la copia y se
                # reintenta una sola vez. Una clave incorrecta no refresca
                # nada, así que el bloqueo por intentos sigue intacto.
                if not cuentas.refrescar_desde_escritorio(
                    self.url_central, username or "", password or ""
                ):
                    # El AuthService redacta los mensajes exactos que ya
                    # conoce el usuario del escritorio (cuenta bloqueada,
                    # inactiva, intentos restantes…): se conservan sin tocar.
                    raise ErrorSesion(str(error), codigo_de_credencial(str(error))) from None
                sesion.rollback()
                try:
                    usuario = AuthService(sesion).autenticar(username or "", password or "")
                except ValueError as repetido:
                    raise ErrorSesion(str(repetido), codigo_de_credencial(str(repetido))) from None
            minimo_password = servicio.longitud_minima_password()
            token = secrets.token_urlsafe(LONGITUD_TOKEN)
            ahora = ahora_utc()
            registro = SesionApi(
                token_hash=hash_token(token),
                username=usuario.username,
                nombre_completo=usuario.nombre_completo,
                rol=usuario.rol_valor,
                usuario_id=usuario.id,
                cedula=normalizar_cedula(usuario.cedula) or None,
                dispositivo_id=dispositivo_id,
                creada_en=ahora,
                expira_en=ahora + timedelta(hours=self.vida_relativa),
                expira_absoluta=ahora + timedelta(days=VIDA_ABSOLUTA_DIAS),
                debe_cambiar_password=int(usuario.debe_cambiar_password or 0),
                revocada=0,
            )
            sesion.add(registro)
            sesion.commit()
            return {
                "sesion_token": token,
                "username": usuario.username,
                "nombre_completo": usuario.nombre_completo,
                "rol": usuario.rol_valor,
                "usuario_id": usuario.id,
                "cedula": normalizar_cedula(usuario.cedula) or None,
                "debe_cambiar_password": bool(usuario.debe_cambiar_password),
                "expira_en": registro.expira_en.isoformat(),
                "vida_relativa_horas": self.vida_relativa,
                # La app valida el cambio de contraseña con la misma regla
                # del servidor, no con una copia inventada del cliente.
                "password_min_longitud": minimo_password,
            }
        except SQLAlchemyError:
            sesion.rollback()
            logger.error("No se pudo registrar la sesión de %r", username, exc_info=True)
            raise ErrorSesion("Error interno al iniciar sesión", 500) from None
        finally:
            sesion.close()

    def cerrar(self, token: str) -> bool:
        """Revoca la sesión del token; devuelve False si no existía"""
        sesion = self._fabrica()
        try:
            fila = self._buscar(sesion, token)
            if fila is None:
                return False
            fila.revocada = 1
            sesion.commit()
            return True
        except SQLAlchemyError:
            sesion.rollback()
            logger.error("No se pudo cerrar la sesión", exc_info=True)
            return False
        finally:
            sesion.close()

    def cerrar_todas_de(self, username: str) -> int:
        """Revoca todas las sesiones abiertas de una cuenta (admin o logout total)"""
        sesion = self._fabrica()
        try:
            filas = (
                sesion.query(SesionApi)
                .filter(SesionApi.username == username, SesionApi.revocada == 0)
                .all()
            )
            for fila in filas:
                fila.revocada = 1
            sesion.commit()
            return len(filas)
        except SQLAlchemyError:
            sesion.rollback()
            logger.error("No se pudieron revocar las sesiones de %r", username, exc_info=True)
            return 0
        finally:
            sesion.close()

    # ------------------------------------------------------------------
    # Validación
    # ------------------------------------------------------------------
    def validar(self, token: str | None, deslizar: bool = True) -> SesionValida:
        """
        Comprueba un token y devuelve la sesión que representa

        Args:
            token: Token en claro recibido en la cabecera Authorization
            deslizar: Si es True, alarga la vida de la sesión (el uso renovado)

        Raises:
            ErrorSesion: 401 si el token no existe, fue revocado o expiró
        """
        if not token or not token.strip():
            raise ErrorSesion("Falta el token de sesión", 401)

        sesion = self._fabrica()
        try:
            fila = self._buscar(sesion, token)
            if fila is None:
                raise ErrorSesion("La sesión no existe o ya fue cerrada", 401)
            if fila.revocada:
                raise ErrorSesion("La sesión fue revocada; vuelva a entrar", 401)

            ahora = ahora_utc()
            if fila.expira_en is None or ahora >= fila.expira_en:
                raise ErrorSesion("La sesión expiró; vuelva a entrar", 401)
            if fila.expira_absoluta is None or ahora >= fila.expira_absoluta:
                raise ErrorSesion("La sesión llegó a su vida máxima; vuelva a entrar", 401)

            if deslizar:
                renovada = ahora + timedelta(hours=self.vida_relativa)
                limite = fila.expira_absoluta
                fila.expira_en = min(renovada, limite)

            # La cuenta pudo desactivarse o cambiar de rol mientras la sesión
            # estaba abierta: el rol vigente es el de la base, no el del token.
            usuario = self._usuario(sesion, fila.username)
            if usuario is None or not usuario.activo:
                fila.revocada = 1
                sesion.commit()
                raise ErrorSesion("La cuenta está desactivada; consulte al administrador", 401)
            rol = usuario.rol_valor
            if rol == "user" and not normalizar_cedula(usuario.cedula):
                fila.revocada = 1
                sesion.commit()
                raise ErrorSesion(
                    "La cuenta no tiene cédula asignada; consulte al administrador", 403
                )
            if rol != fila.rol:
                fila.rol = rol
            cedula = normalizar_cedula(usuario.cedula) or None
            fila.usuario_id = usuario.id
            fila.cedula = cedula
            debe_cambiar = bool(usuario.debe_cambiar_password)
            if debe_cambiar != bool(fila.debe_cambiar_password):
                fila.debe_cambiar_password = int(debe_cambiar)

            sesion.commit()
            return SesionValida(
                token_hash=fila.token_hash,
                username=fila.username,
                nombre_completo=fila.nombre_completo or usuario.nombre_completo,
                rol=rol,
                dispositivo_id=fila.dispositivo_id,
                expira_en=fila.expira_en,
                debe_cambiar_password=debe_cambiar,
                usuario_id=usuario.id,
                cedula=cedula,
            )
        except SQLAlchemyError:
            sesion.rollback()
            logger.error("No se pudo validar la sesión", exc_info=True)
            raise ErrorSesion("Error interno al validar la sesión", 500) from None
        finally:
            sesion.close()

    # ------------------------------------------------------------------
    # Cambio de contraseña (misma política que el escritorio)
    # ------------------------------------------------------------------
    def cambiar_password(self, token: str, nueva: str, actual: str | None = None) -> None:
        """
        Cambia la contraseña de la cuenta de la sesión

        Raises:
            ErrorSesion: 400 si la política de credenciales rechaza el cambio
        """
        from src.services.auth_service import AuthService

        sesion_valida = self.validar(token, deslizar=False)
        sesion = self._fabrica()
        try:
            usuario = self._usuario(sesion, sesion_valida.username)
            if usuario is None:
                raise ErrorSesion("La cuenta ya no existe", 401)
            AuthService(sesion).cambiar_password(usuario, nueva, actual)

            # El cambio invalida las demás sesiones abiertas de la cuenta, pero
            # la que hizo el cambio sigue viva para no expulsar al usuario.
            vigente = self._buscar(sesion, token)
            consulta = sesion.query(SesionApi).filter(
                SesionApi.username == usuario.username, SesionApi.revocada == 0
            )
            if vigente is not None:
                consulta = consulta.filter(SesionApi.token_hash != vigente.token_hash)
            for fila in consulta.all():
                fila.revocada = 1
            if vigente is not None:
                vigente.debe_cambiar_password = 0
            sesion.commit()
            # El escritorio usa la misma cuenta: si el cambio se hizo desde el
            # móvil, allí debe valer la contraseña nueva de inmediato.
            cuentas.espejar_en_escritorio(self.url_central, usuario.username)
        except ValueError as error:
            sesion.rollback()
            raise ErrorSesion(str(error), 400) from None
        except SQLAlchemyError:
            sesion.rollback()
            logger.error("No se pudo cambiar la contraseña", exc_info=True)
            raise ErrorSesion("Error interno al cambiar la contraseña", 500) from None
        finally:
            sesion.close()

    # ------------------------------------------------------------------
    # Administración
    # ------------------------------------------------------------------
    def listar_activas(self, limite: int = 200) -> list[dict]:
        """Sesiones vigentes, para diagnóstico del administrador"""
        sesion = self._fabrica()
        try:
            ahora = ahora_utc()
            filas = (
                sesion.query(SesionApi)
                .filter(SesionApi.revocada == 0, SesionApi.expira_en > ahora)
                .order_by(SesionApi.creada_en.desc())
                .limit(limite)
                .all()
            )
            return [
                {
                    "username": fila.username,
                    "rol": fila.rol,
                    "dispositivo": fila.dispositivo_id,
                    "creada_en": fila.creada_en.isoformat() if fila.creada_en else None,
                    "expira_en": fila.expira_en.isoformat() if fila.expira_en else None,
                }
                for fila in filas
            ]
        finally:
            sesion.close()

    def purgar_expiradas(self, dias: int = 30) -> int:
        """Elimina sesiones caducadas antiguas para que la tabla no crezca sin fin"""
        sesion = self._fabrica()
        try:
            limite = ahora_utc() - timedelta(days=max(1, dias))
            borradas = (
                sesion.query(SesionApi)
                .filter(SesionApi.expira_absoluta < limite)
                .delete(synchronize_session=False)
            )
            sesion.commit()
            return int(borradas or 0)
        except SQLAlchemyError:
            sesion.rollback()
            return 0
        finally:
            sesion.close()

    # ------------------------------------------------------------------
    # Interno
    # ------------------------------------------------------------------
    @staticmethod
    def _buscar(sesion: Session, token: str) -> SesionApi | None:
        if not token or not token.strip():
            return None
        return (
            sesion.query(SesionApi)
            .filter(SesionApi.token_hash == hash_token(token.strip()))
            .first()
        )

    @staticmethod
    def _usuario(sesion: Session, username: str):
        from src.models import Usuario

        return sesion.query(Usuario).filter(Usuario.username == username).first()
