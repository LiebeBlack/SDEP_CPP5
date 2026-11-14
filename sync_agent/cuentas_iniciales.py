"""Aprovisionamiento idempotente de las cuentas genéricas del nodo.

La única cuenta genérica creada automáticamente es ``admin``. Las cuentas
institucionales ``manager``, ``user`` y ``viewer`` que ya existan se conservan;
no se crean ni eliminan desde este aprovisionador. La cuenta ``user`` necesita
una cédula real para poder autenticarse: no se inventa identidad ni se permite
compartir datos de empleados bajo una cédula ficticia.
"""

from __future__ import annotations

import logging

from src.services.auth_service import (
    AuthService,
    CLAVES_INICIALES_ANTERIORES,
    CUENTAS_INICIALES,
)
from src.utils.security import SecurityValidator

logger = logging.getLogger(__name__)


def preparar_cuentas_iniciales(servicio: AuthService) -> tuple[list[str], list[str]]:
    """Crea solo el administrador inicial, preservando cuentas existentes.

    Es seguro repetir la operación: la cuenta existente conserva su contraseña,
    rol y estado; solo se fuerza rotación si aún usa la clave inicial conocida.
    Ningún trabajador recibe cédula ficticia. Los demás roles se crean desde la
    administración explícita de usuarios, no automáticamente.

    Args:
        servicio: Servicio de autenticación conectado a la base del nodo.

    Returns:
        Dos listas: administrador creado y cuenta inicial existente que quedó
        marcada para cambiar su contraseña.
    """
    creadas: list[str] = []
    requieren_cambio: list[str] = []

    for username, password, rol, nombre_completo in CUENTAS_INICIALES:
        usuario = servicio.usuario_por_username(username)
        if usuario is None:
            servicio.crear_usuario(
                username=username,
                password=password,
                rol=rol,
                nombre_completo=nombre_completo,
                debe_cambiar_password=True,
                cedula=None,
            )
            creadas.append(username)
            continue

        claves_conocidas = (password, *CLAVES_INICIALES_ANTERIORES.get(username, ()))
        if not usuario.debe_cambiar_password and any(
            SecurityValidator.verify_password(clave, usuario.password_hash)
            for clave in claves_conocidas
        ):
            usuario.debe_cambiar_password = 1
            usuario.fecha_cambio_password = None
            requieren_cambio.append(username)

    if requieren_cambio:
        servicio.session.commit()

    for username in creadas:
        logger.info(
            "Cuenta administradora inicial creada; requiere cambiar la contraseña: %s", username
        )
    for username in requieren_cambio:
        logger.warning("La cuenta admin conserva una clave inicial conocida; se exigirá rotarla")

    return creadas, requieren_cambio
