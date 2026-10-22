"""
Consistencia de las cuentas entre el escritorio y el nodo central

La base institucional (``src.config.db_config``) es la que usa la aplicación de
escritorio y la única donde el administrador edita cuentas. El nodo central
guarda una **copia** para poder autenticar al teléfono. Esa copia se hacía una
sola vez, al configurar el servidor embebido: en cuanto alguien cambiaba su
contraseña en el escritorio con el sistema ya abierto (el caso normal, porque
la cuenta inicial obliga a cambiarla en el primer ingreso), el escritorio
aceptaba la clave nueva y el teléfono seguía respondiendo «usuario o contraseña
incorrectos». Lo mismo ocurría al revés: un cambio hecho desde el móvil dejaba
al escritorio con la contraseña anterior.

Este módulo mantiene las dos bases alineadas sin reimplementar la política de
credenciales: copia el hash PBKDF2 y el estado, nunca la contraseña en claro.

* ``refrescar_desde_escritorio`` se usa cuando el login central falla. Si la
  contraseña presentada **sí** es la de la base institucional (y la cuenta allí
  está activa y sin bloqueo), actualiza la copia central y permite reintentar
  una vez. Una contraseña incorrecta nunca refresca ni desbloquea nada.
* ``espejar_en_escritorio`` se usa cuando la contraseña cambia desde el móvil:
  el escritorio recibe el nuevo hash para que la cuenta siga siendo la misma en
  ambos lados.
* ``copiar_cuenta`` lo usa el arranque del nodo embebido para actualizar las
  cuentas que ya existían, no solo las que faltaban.

Solo se actúa sobre la instalación embebida (``<datos>/sync_central.db``). En
pruebas, en un servidor lanzado suelto o con una base central en otra ruta, las
funciones no tocan nada. Todos los fallos son *best-effort*: un espejo que no se
puede escribir nunca convierte un login válido en un error.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

NOMBRE_BASE_CENTRAL = "sync_central.db"


# ----------------------------------------------------------------------
# Utilidades de rutas y sesiones
# ----------------------------------------------------------------------
def _ruta_sqlite(url: str | None) -> Path | None:
    """Ruta de archivo de una URL SQLite (None si no es un archivo)"""
    if not url or not url.startswith("sqlite"):
        return None
    crudo = url.split("sqlite:///", 1)[-1] if "sqlite:///" in url else ""
    if not crudo or crudo == ":memory:" or crudo.startswith("file:"):
        return None
    try:
        return Path(crudo).expanduser().resolve()
    except OSError:
        return None


def es_instalacion_embebida(url_central: str | None) -> bool:
    """
    Indica si la base central es la del servidor embebido de este equipo

    Compara la ruta real con ``<carpeta de datos>/sync_central.db``. Es la
    garantía de que estas funciones solo actúan donde está la base
    institucional del escritorio; una base central de pruebas o de otro
    servidor nunca se mezcla con las cuentas locales.
    """
    ruta = _ruta_sqlite(url_central)
    if ruta is None:
        return False
    try:
        from src.config import settings

        esperada = (Path(settings.base_dir) / NOMBRE_BASE_CENTRAL).resolve()
    except Exception:  # pragma: no cover - entorno sin configuración cargada
        logger.debug("No se pudo resolver la ruta del nodo central embebido", exc_info=True)
        return False
    return ruta == esperada


def _abrir_central(url_central: str) -> tuple[Any, Session] | None:
    """Motor y sesión de la base central (None si no está disponible)"""
    ruta = _ruta_sqlite(url_central)
    if ruta is None or not ruta.exists():
        return None
    try:
        from sync_agent.esquema import motor_desde_url

        motor = motor_desde_url(url_central, echo=False)
        fabrica = sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=motor
        )
        return motor, fabrica()
    except SQLAlchemyError:
        logger.warning("No se pudo abrir la base central para el espejo de cuentas", exc_info=True)
        return None


def _usuario(sesion: Session, username: str):
    """Cuenta por nombre de usuario en la base de la sesión"""
    from src.models import Usuario

    return sesion.query(Usuario).filter(Usuario.username == username).first()


# ----------------------------------------------------------------------
# Copia de campos
# ----------------------------------------------------------------------
def _rol_valor(usuario) -> str:
    """Valor de texto del rol (acepta el enum o el texto ya convertido)"""
    return getattr(usuario, "rol_valor", str(usuario.rol))


def cuentas_difieren(destino, origen) -> bool:
    """Indica si dos filas de cuenta no representan las mismas credenciales"""
    return (
        (destino.password_hash or "") != (origen.password_hash or "")
        or _rol_valor(destino) != _rol_valor(origen)
        or bool(destino.activo) != bool(origen.activo)
        or bool(destino.debe_cambiar_password) != bool(origen.debe_cambiar_password)
        or (destino.nombre_completo or "") != (origen.nombre_completo or "")
    )


def copiar_cuenta(destino, origen, incluir_estado: bool = True) -> bool:
    """
    Vuelca una cuenta de origen sobre la fila de destino

    Args:
        destino: fila de ``usuarios`` que se actualiza
        origen: fila de ``usuarios`` con el estado vigente
        incluir_estado: copiar además rol y estado de activación. En el login
            se deja en False a propósito: solo se refrescan credenciales, de
            modo que una desactivación hecha en el nodo central siga valiendo.

    Returns:
        True si cambió algún campo (no confirma la transacción)
    """
    cambio_hash = (destino.password_hash or "") != (origen.password_hash or "")
    if incluir_estado:
        diferente = cuentas_difieren(destino, origen)
    else:
        # El rol y la activación no se tocan: una desactivación hecha en el
        # nodo central debe seguir valiendo aunque el escritorio aún la ignore.
        diferente = (
            cambio_hash
            or bool(destino.debe_cambiar_password) != bool(origen.debe_cambiar_password)
            or (destino.nombre_completo or "") != (origen.nombre_completo or "")
        )
    if not diferente:
        return False

    destino.password_hash = origen.password_hash
    destino.nombre_completo = origen.nombre_completo
    destino.password_historial = origen.password_historial
    destino.fecha_cambio_password = origen.fecha_cambio_password
    destino.debe_cambiar_password = origen.debe_cambiar_password
    if incluir_estado:
        destino.rol = _rol_valor(origen)
        destino.activo = int(origen.activo or 0)

    if cambio_hash:
        # Una contraseña nueva nace con los contadores limpios, igual que hace
        # ``AuthService.cambiar_password`` en la base donde se cambió.
        destino.intentos_fallidos = 0
        destino.bloqueado = 0
        destino.bloqueado_hasta = None
    return True


# ----------------------------------------------------------------------
# Escritorio -> nodo central
# ----------------------------------------------------------------------
def refrescar_desde_escritorio(url_central: str | None, username: str, password: str) -> bool:
    """
    Actualiza la copia central si la contraseña es la del escritorio

    Se llama solo tras un login fallido en el nodo central. La contraseña se
    verifica contra la base institucional con el mismo ``SecurityValidator``
    del escritorio; si no coincide, la cuenta local está inactiva o bloqueada,
    no se toca la base central y el error original se conserva.

    Args:
        url_central: URL SQLAlchemy del nodo central
        username: cuenta que intentó entrar
        password: contraseña presentada por el teléfono

    Returns:
        True si se actualizó la copia central y conviene reintentar el login.
    """
    if not es_instalacion_embebida(url_central):
        return False
    abierta = _abrir_central(str(url_central))
    if abierta is None:
        return False
    motor, central = abierta
    local = None
    try:
        from src.config import db_config
        from src.models import Usuario
        from src.utils.security import SecurityValidator

        local = db_config.get_session()
        origen = _usuario(local, username)
        if origen is None or not origen.activo or origen.bloqueado:
            return False
        if not SecurityValidator.verify_password(password or "", origen.password_hash):
            return False

        destino = _usuario(central, username)
        if destino is None:
            # Cuenta creada en el escritorio con el sistema ya abierto: el
            # nodo central no la conoce todavía. Se da de alta con la clave
            # que acaba de verificarse, sin esperar a reiniciar el servidor.
            central.add(
                Usuario(
                    username=origen.username,
                    password_hash=origen.password_hash,
                    nombre_completo=origen.nombre_completo,
                    rol=_rol_valor(origen),
                    activo=int(origen.activo or 0),
                    debe_cambiar_password=int(origen.debe_cambiar_password or 0),
                    fecha_cambio_password=origen.fecha_cambio_password,
                    password_historial=origen.password_historial,
                )
            )
            central.commit()
            logger.info("Cuenta %r creada en el nodo central desde el escritorio", username)
            return True
        if not copiar_cuenta(destino, origen, incluir_estado=False):
            return False
        central.commit()
        logger.info("Cuenta %r refrescada desde el escritorio en el nodo central", username)
        return True
    except (SQLAlchemyError, RuntimeError):
        central.rollback()
        logger.warning(
            "No se pudo refrescar la cuenta %r en el nodo central", username, exc_info=True
        )
        return False
    except Exception:  # pragma: no cover - el espejo nunca debe romper el login
        central.rollback()
        logger.warning("Espejo de cuentas inesperado en el login", exc_info=True)
        return False
    finally:
        central.close()
        try:
            motor.dispose()
        except Exception:
            logger.debug("No se pudo liberar el motor central del espejo", exc_info=True)
        if local is not None:
            try:
                from src.config import db_config

                db_config.close_session(local)
            except Exception:
                logger.debug("No se pudo cerrar la sesión local del espejo", exc_info=True)


# ----------------------------------------------------------------------
# Nodo central -> escritorio
# ----------------------------------------------------------------------
def espejar_en_escritorio(url_central: str | None, username: str) -> bool:
    """
    Lleva al escritorio las credenciales cambiadas desde el móvil

    El cambio de contraseña del protocolo 2 se aplica sobre la copia central.
    Sin este espejo, el escritorio seguiría esperando la contraseña anterior y
    la cuenta quedaría inservible en el equipo donde vive la base institucional.

    Returns:
        True si la cuenta del escritorio se actualizó.
    """
    if not es_instalacion_embebida(url_central):
        return False
    abierta = _abrir_central(str(url_central))
    if abierta is None:
        return False
    motor, central = abierta
    local = None
    try:
        from src.config import db_config

        origen = _usuario(central, username)
        if origen is None:
            return False
        local = db_config.get_session()
        destino = _usuario(local, username)
        if destino is None:
            logger.info(
                "La cuenta %r no existe en el escritorio; no se crea desde el móvil",
                username,
            )
            return False
        if not copiar_cuenta(destino, origen, incluir_estado=False):
            return False
        local.commit()
        logger.info("Contraseña de %r replicada del móvil al escritorio", username)
        return True
    except (SQLAlchemyError, RuntimeError):
        if local is not None:
            local.rollback()
        logger.warning("No se pudo replicar la cuenta %r al escritorio", username, exc_info=True)
        return False
    except Exception:  # pragma: no cover - el espejo nunca debe romper el cambio
        if local is not None:
            local.rollback()
        logger.warning("Espejo de cuentas inesperado al cambiar la contraseña", exc_info=True)
        return False
    finally:
        central.close()
        try:
            motor.dispose()
        except Exception:
            logger.debug("No se pudo liberar el motor central del espejo", exc_info=True)
        if local is not None:
            try:
                from src.config import db_config

                db_config.close_session(local)
            except Exception:
                logger.debug("No se pudo cerrar la sesión local del espejo", exc_info=True)
