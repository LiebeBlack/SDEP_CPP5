"""
Pruebas de la política de credenciales y de los respaldos programados

Cubren lo que exige una instalación real en un colegio: bloqueo tras
varios intentos fallidos, caducidad de la contraseña, prohibición de
repetir las últimas claves y respaldo automático según el intervalo
configurado (con verificación de integridad del archivo).
"""

from datetime import datetime, timedelta

import pytest

from src.services.auth_service import (
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    AuthService,
)
from src.utils.backup_scheduler import BackupScheduler


@pytest.fixture()
def auth(session):
    return AuthService(session)


@pytest.fixture()
def admin(session, auth):
    return auth.usuario_por_username(DEFAULT_ADMIN_USERNAME)


# ----------------------------------------------------------------------
# Contraseñas
# ----------------------------------------------------------------------
def test_bloqueo_tras_intentos_fallidos(session, auth, admin):
    max_intentos = auth.max_intentos_fallidos()
    for _ in range(max_intentos):
        with pytest.raises(ValueError):
            auth.autenticar(DEFAULT_ADMIN_USERNAME, "clave_incorrecta")

    session.refresh(admin)
    assert admin.intentos_fallidos >= max_intentos
    assert admin.bloqueado_hasta is not None
    # Aun con la contraseña correcta, la cuenta está bloqueada
    with pytest.raises(ValueError, match="bloquead|intento"):
        auth.autenticar(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)


def test_un_login_correcto_limpia_los_intentos(session, auth, admin):
    with pytest.raises(ValueError):
        auth.autenticar(DEFAULT_ADMIN_USERNAME, "clave_incorrecta")
    session.refresh(admin)
    assert admin.intentos_fallidos == 1

    auth.autenticar(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
    session.refresh(admin)
    assert admin.intentos_fallidos == 0


def test_desbloqueo_manual_de_la_cuenta(session, auth, admin):
    for _ in range(auth.max_intentos_fallidos()):
        with pytest.raises(ValueError):
            auth.autenticar(DEFAULT_ADMIN_USERNAME, "clave_incorrecta")

    desbloqueado = auth.desbloquear_usuario(admin.id)
    assert desbloqueado.intentos_fallidos == 0
    assert desbloqueado.bloqueado_hasta is None
    assert auth.autenticar(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)


def test_el_bloqueo_temporal_expira_solo(session, auth, admin):
    for _ in range(auth.max_intentos_fallidos()):
        with pytest.raises(ValueError):
            auth.autenticar(DEFAULT_ADMIN_USERNAME, "clave_incorrecta")

    session.refresh(admin)
    admin.bloqueado_hasta = datetime.now() - timedelta(minutes=1)
    session.commit()

    assert auth.autenticar(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)


def test_no_se_repite_una_password_del_historial(session, auth, admin):
    assert auth.cambiar_password(admin, "ClaveSegura1", actual_password=DEFAULT_ADMIN_PASSWORD)
    session.refresh(admin)
    # Ni la contraseña vigente ni la anterior pueden volver a usarse
    with pytest.raises(ValueError, match="igual a la actual"):
        auth.cambiar_password(admin, "ClaveSegura1", actual_password="ClaveSegura1")
    with pytest.raises(ValueError, match="reutilizar"):
        auth.cambiar_password(
            admin, DEFAULT_ADMIN_PASSWORD, actual_password="ClaveSegura1"
        )


def test_historial_limita_las_ultimas_claves(session, auth, admin):
    assert auth.historial_password() >= 1
    auth.cambiar_password(admin, "ClaveSegura1", actual_password=DEFAULT_ADMIN_PASSWORD)
    auth.cambiar_password(admin, "ClaveSegura2", actual_password="ClaveSegura1")
    session.refresh(admin)
    # La inmediatamente anterior sigue bloqueada para reutilizarse
    with pytest.raises(ValueError):
        auth.cambiar_password(admin, "ClaveSegura1", actual_password="ClaveSegura2")


def test_caducidad_de_la_password(session, auth, admin):
    assert auth.dias_caducidad_password() > 0
    assert not auth.password_caducada(admin)

    admin.fecha_cambio_password = datetime.now() - timedelta(
        days=auth.dias_caducidad_password() + 1
    )
    admin.debe_cambiar_password = 0
    session.commit()
    assert auth.password_caducada(admin)

    assert auth.marcar_cambio_obligatorio_si_caducada(admin)
    session.refresh(admin)
    assert admin.debe_cambiar_password == 1
    # Ya marcada no se vuelve a marcar
    assert not auth.marcar_cambio_obligatorio_si_caducada(admin)


def test_la_password_recien_cambiada_no_esta_caducada(session, auth, admin):
    assert auth.cambiar_password(admin, "ClaveSegura9", actual_password=DEFAULT_ADMIN_PASSWORD)
    session.refresh(admin)
    assert not auth.password_caducada(admin)
    assert admin.debe_cambiar_password == 0
    assert admin.fecha_cambio_password is not None


def test_crear_usuario_marca_cambio_obligatorio(session, auth):
    usuario = auth.crear_usuario(
        "nuevo_gestor",
        "ClaveInicial1",
        "manager",
        nombre_completo="Gestor de Prueba",
    )
    assert usuario.debe_cambiar_password == 1
    assert auth.autenticar("nuevo_gestor", "ClaveInicial1")
    # El usuario nuevo aparece en los listados de la pantalla de usuarios
    assert "nuevo_gestor" in [item.username for item in auth.listar_usuarios()]
    assert auth.listar_roles()


# ----------------------------------------------------------------------
# Respaldos programados
# ----------------------------------------------------------------------
def test_el_programador_lee_la_configuracion(session):
    programador = BackupScheduler.desde_sesion(session)
    assert programador.intervalo_horas() > 0
    assert isinstance(programador.esta_habilitado(), bool)
    estado = programador.estado()
    assert "habilitado" in estado
    assert "intervalo_horas" in estado
    assert "proxima_ejecucion" in estado


def test_sin_respaldos_previos_el_programador_debe_ejecutar(session):
    programador = BackupScheduler.desde_sesion(session)
    assert programador.debe_ejecutar()


def test_ejecutar_crea_un_respaldo_verificado(session):
    programador = BackupScheduler.desde_sesion(session)
    resultado = programador.ejecutar(forzar=True)
    assert set(resultado) == {"ejecutado", "motivo", "backup", "verificacion"}
    assert resultado["ejecutado"] is True
    respaldo = resultado["backup"]
    assert respaldo and respaldo.get("name")
    verificacion = resultado["verificacion"]
    assert verificacion is not None
    assert verificacion.get("exists") is True
    assert verificacion.get("checksum_valid") is True


def test_tras_un_respaldo_no_hace_falta_otro(session):
    programador = BackupScheduler.desde_sesion(session)
    resultado = programador.comprobar_y_ejecutar()
    assert "ejecutado" in resultado
    assert programador.ultima_ejecucion() is not None
    assert not programador.debe_ejecutar()
    assert programador.proxima_ejecucion() > datetime.now()


def test_programador_deshabilitado_no_se_activa(session):
    def obtener(clave, por_defecto):
        if clave == "backup_enabled":
            return False
        return por_defecto

    programador = BackupScheduler(obtener_valor=obtener)
    assert not programador.esta_habilitado()
    assert programador.proxima_ejecucion() is None
    assert programador.debe_ejecutar() is False

    # Forzar sí funciona incluso con los respaldos automáticos apagados
    resultado = programador.ejecutar(forzar=True)
    assert resultado["ejecutado"] is True


def test_el_callback_de_respaldo_recibe_el_resultado(session):
    programador = BackupScheduler.desde_sesion(session)
    recibidos: list[dict] = []
    resultado = programador.comprobar_y_ejecutar(callback=recibidos.append)
    if resultado["ejecutado"]:
        assert recibidos and recibidos[0]["ejecutado"] is True
