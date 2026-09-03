"""Pruebas del servicio de autenticación y gestión de usuarios"""

import pytest

from src.services.auth_service import (
    AuthService,
    ensure_default_admin,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
)
from src.utils.security import SecurityValidator


def test_hash_password_formato_pbkdf2():
    hash_valor = SecurityValidator.hash_password("secreto123")
    partes = hash_valor.split("$")
    assert partes[0] == "pbkdf2"
    assert len(partes) == 4
    assert SecurityValidator.verify_password("secreto123", hash_valor)
    assert not SecurityValidator.verify_password("otra", hash_valor)


def test_verify_password_legado_sha256():
    import hashlib
    import secrets
    salt = secrets.token_hex(16)
    viejo_hash = hashlib.sha256(("clave" + salt).encode()).hexdigest()
    assert SecurityValidator.verify_password("clave", f"{salt}${viejo_hash}")
    assert not SecurityValidator.verify_password("nope", f"{salt}${viejo_hash}")


def test_seed_admin_y_login(session):
    admin = ensure_default_admin(session)
    if admin is None:
        auth = AuthService(session)
        admin = auth.usuario_por_username(DEFAULT_ADMIN_USERNAME)
    assert admin is not None

    auth = AuthService(session)
    usuario = auth.autenticar(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
    assert usuario.id == admin.id
    assert usuario.rol_valor == "admin"
    assert usuario.debe_cambiar_password


def test_login_password_incorrecta(session):
    auth = AuthService(session)
    ensure_default_admin(session)
    with pytest.raises(ValueError):
        auth.autenticar(DEFAULT_ADMIN_USERNAME, "contraseña_equivocada")


def test_login_usuario_inexistente(session):
    auth = AuthService(session)
    with pytest.raises(ValueError):
        auth.autenticar("no_existe", "clave123")


def test_bloqueo_por_intentos_fallidos(session):
    auth = AuthService(session)
    ensure_default_admin(session)

    for _ in range(5):
        with pytest.raises(ValueError):
            auth.autenticar(DEFAULT_ADMIN_USERNAME, "clave_mala")

    with pytest.raises(ValueError) as exc:
        auth.autenticar(DEFAULT_ADMIN_USERNAME, "clave_mala")
    assert "bloqueada" in str(exc.value).lower()


def test_cambiar_password(session):
    auth = AuthService(session)
    ensure_default_admin(session)
    usuario = auth.autenticar(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)

    with pytest.raises(ValueError):
        auth.cambiar_password(usuario, "nueva123", actual_password="incorrecta")

    assert auth.cambiar_password(usuario, "nueva_segura", actual_password=DEFAULT_ADMIN_PASSWORD)
    assert not usuario.debe_cambiar_password
    auth.session.expire_all()
    auth.autenticar(DEFAULT_ADMIN_USERNAME, "nueva_segura")


def test_cambiar_password_corta(session):
    auth = AuthService(session)
    ensure_default_admin(session)
    usuario = auth.usuario_por_username(DEFAULT_ADMIN_USERNAME)
    with pytest.raises(ValueError):
        auth.cambiar_password(usuario, "123")


def test_crear_usuario_duplicado(session):
    auth = AuthService(session)
    ensure_default_admin(session)
    auth.crear_usuario("jperez", "clave123", "user", "Juan Pérez")
    with pytest.raises(ValueError):
        auth.crear_usuario("jperez", "clave123", "user")


def test_crear_usuario_rol_invalido(session):
    auth = AuthService(session)
    with pytest.raises(ValueError):
        auth.crear_usuario("inv", "clave123", "superadmin")


def test_no_se_puede_desactivar_la_propia_cuenta(session):
    auth = AuthService(session)
    admin = ensure_default_admin(session) or auth.usuario_por_username("admin")
    with pytest.raises(ValueError):
        auth.actualizar_usuario(admin.id, {"activo": 0}, usuario_actual=admin)


def test_no_se_puede_degradar_la_propia_cuenta(session):
    auth = AuthService(session)
    admin = ensure_default_admin(session) or auth.usuario_por_username("admin")
    with pytest.raises(ValueError):
        auth.actualizar_usuario(admin.id, {"rol": "user"}, usuario_actual=admin)


def test_actualizar_rol_y_reset_password(session):
    auth = AuthService(session)
    ensure_default_admin(session)
    creado = auth.crear_usuario("mrosa", "clave123", "user", "María Rosa")

    auth.actualizar_usuario(creado.id, {"rol": "manager", "password": "nuevaclave"})
    auth.session.expire_all()
    usuario = auth.usuario_por_id(creado.id)
    assert usuario.rol_valor == "manager"
    assert usuario.debe_cambiar_password == 1
