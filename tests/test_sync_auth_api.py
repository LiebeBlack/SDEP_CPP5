"""
Pruebas de autenticación del protocolo 2 (login contra la base institucional)

La aplicación móvil entra con las MISMAS cuentas que el escritorio: aquí se
comprueba que el login valida contra la tabla ``usuarios``, que el bloqueo por
intentos y la caducidad se comportan igual que en el escritorio, que el token
que recibe el cliente nunca queda en claro en la base, y que la sesión sirve o
no según su estado.
"""

import pytest

from sync_agent.servidor import NucleoCentral, ServidorConfig
from sync_agent.sesiones import ErrorSesion, GestorSesiones, hash_token


@pytest.fixture()
def central(tmp_path):
    """Nodo central aislado con un administrador de prueba"""
    config = ServidorConfig(
        url_db=f"sqlite:///{(tmp_path / 'central.db').as_posix()}",
        dir_blobs=tmp_path / "blobs",
        host="127.0.0.1",
        puerto=0,
    )
    nucleo = NucleoCentral(config)
    _crear_usuarios(nucleo)
    yield nucleo
    nucleo.cerrar()


def _crear_usuarios(nucleo):
    """Crea las cuentas con los roles del escritorio (contraseñas PBKDF2 reales)"""
    from src.services.auth_service import AuthService

    sesion = nucleo.SessionFactory()
    try:
        servicio = AuthService(sesion)
        if servicio.usuario_por_username("admin") is None:
            servicio.crear_usuario(
                "admin", "Clave1234", "admin", "Administrador", debe_cambiar_password=False
            )
        if servicio.usuario_por_username("gestora") is None:
            servicio.crear_usuario(
                "gestora", "Clave1234", "manager", "Gestora", debe_cambiar_password=False
            )
        if servicio.usuario_por_username("docente") is None:
            servicio.crear_usuario(
                "docente",
                "Clave1234",
                "user",
                "Docente",
                debe_cambiar_password=False,
                cedula="12345678",
            )
        if servicio.usuario_por_username("lector") is None:
            servicio.crear_usuario(
                "lector", "Clave1234", "viewer", "Lector", debe_cambiar_password=False
            )
    finally:
        sesion.close()


def _login(nucleo, username="admin", password="Clave1234", dispositivo="equipo-test"):
    return nucleo.api.login({"username": username, "password": password}, dispositivo)


# ----------------------------------------------------------------------
# Login
# ----------------------------------------------------------------------
def test_login_devuelve_sesion_con_rol_de_la_base(central):
    datos = _login(central)

    assert datos["username"] == "admin"
    assert datos["rol"] == "admin"
    assert datos["debe_cambiar_password"] is False
    assert len(datos["sesion_token"]) >= 40
    assert datos["expira_en"]


def test_login_rechaza_contraseña_incorrecta(central):
    with pytest.raises(ErrorSesion) as error:
        _login(central, password="otra-clave")
    assert error.value.codigo == 401
    assert "incorrectos" in str(error.value).lower()


def test_login_rechaza_usuario_inexistente(central):
    with pytest.raises(ErrorSesion):
        _login(central, username="nadie", password="Clave1234")


def test_login_rechaza_campos_vacios(central):
    from sync_agent.api_acciones import ErrorApi

    with pytest.raises(ErrorApi) as error:
        _login(central, username="", password="")
    assert error.value.codigo == 400


def test_login_solo_muestra_cambio_obligatorio_si_esta_marcado(central):
    from src.models import Usuario
    from src.services.auth_service import AuthService

    sesion = central.SessionFactory()
    try:
        AuthService(sesion).crear_usuario(
            "nuevo", "Clave1234", "user", "Nuevo", debe_cambiar_password=True, cedula="12345679"
        )
    finally:
        sesion.close()

    datos = _login(central, username="nuevo")
    assert datos["debe_cambiar_password"] is True


def test_bloqueo_por_intentos_idéntico_al_escritorio(central):
    """5 contraseñas fallidas bloquean la cuenta (máximo del AuthService)"""
    for _ in range(5):
        with pytest.raises(ErrorSesion):
            _login(central, password="mala")

    with pytest.raises(ErrorSesion) as error:
        _login(central)
    assert "bloqueada" in str(error.value).lower()


def test_cuenta_inactiva_no_entra(central):
    from src.models import Usuario
    from src.services.auth_service import AuthService

    sesion = central.SessionFactory()
    try:
        AuthService(sesion).actualizar_usuario(
            AuthService(sesion).usuario_por_username("lector").id, {"activo": 0}
        )
    finally:
        sesion.close()

    with pytest.raises(ErrorSesion) as error:
        _login(central, username="lector")
    assert "desactivada" in str(error.value).lower()


# ----------------------------------------------------------------------
# Vida de la sesión
# ----------------------------------------------------------------------
def test_el_token_nunca_queda_en_claro_en_la_base(central):
    datos = _login(central)
    token = datos["sesion_token"]

    sesion = central.SessionFactory()
    try:
        from sync_agent.esquema import SesionApi

        filas = sesion.query(SesionApi).all()
        assert filas, "la sesión debió registrarse"
        assert all(fila.token_hash != token for fila in filas)
        # El hash guardado es SHA-256 (64 hex), no el token en claro
        assert all(len(fila.token_hash) == 64 for fila in filas)
        assert any(fila.token_hash == hash_token(token) for fila in filas)
        # Ni la contraseña ni el token en claro aparecen en ninguna fila
        textos = [str(valor) for fila in filas for valor in fila.__dict__.values()]
        assert not any("Clave1234" in texto for texto in textos)
        assert not any(token in texto for texto in textos)
    finally:
        sesion.close()


def test_validar_sesion_conoce_al_usuario_y_su_rol(central):
    datos = _login(central, username="gestora")

    valido = central.api.validar(datos["sesion_token"])

    assert valido.username == "gestora"
    assert valido.rol == "manager"
    assert valido.dispositivo_id == "equipo-test"


def test_sesion_expirada_se_rechaza(central):
    from datetime import timedelta

    datos = _login(central)
    gestor = GestorSesiones(central.SessionFactory)
    token_hash = hash_token(datos["sesion_token"])

    sesion = central.SessionFactory()
    try:
        from sync_agent.comun import ahora_utc
        from sync_agent.esquema import SesionApi

        fila = sesion.query(SesionApi).filter(SesionApi.token_hash == token_hash).first()
        fila.expira_en = ahora_utc() - timedelta(seconds=1)
        sesion.commit()
    finally:
        sesion.close()

    with pytest.raises(ErrorSesion) as error:
        gestor.validar(datos["sesion_token"])
    assert error.value.codigo == 401
    assert "expiró" in str(error.value).lower()


def test_logout_revoca_la_sesion(central):
    datos = _login(central)

    central.api.cerrar_sesion(datos["sesion_token"])

    with pytest.raises(ErrorSesion):
        central.api.validar(datos["sesion_token"])


def test_login_desde_otro_dispositivo_no_cierra_el_anterior(central):
    """Dos sesiones simultáneas (teléfono y tableta) son válidas por separado"""
    una = _login(central, dispositivo="telefono")
    otra = _login(central, dispositivo="tableta")

    assert central.api.validar(una["sesion_token"]).dispositivo_id == "telefono"
    assert central.api.validar(otra["sesion_token"]).dispositivo_id == "tableta"


def test_cambio_de_password_aplica_las_reglas_del_escritorio(central):
    datos = _login(central)

    # Contraseña demasiado corta: rechazo con el mensaje del AuthService
    with pytest.raises(ErrorSesion) as error:
        central.api.cambiar_password(datos["sesion_token"], {"nueva": "corta"})
    assert error.value.codigo == 400

    # Cambio válido con la contraseña actual
    central.api.cambiar_password(
        datos["sesion_token"], {"nueva": "NuevaClave9", "actual": "Clave1234"}
    )

    # La sesión sigue viva y la contraseña antigua ya no sirve
    central.api.validar(datos["sesion_token"])
    with pytest.raises(ErrorSesion):
        central.api.login({"username": "admin", "password": "Clave1234"}, "equipo")
    nueva = central.api.login({"username": "admin", "password": "NuevaClave9"}, "equipo")
    assert nueva["rol"] == "admin"


def test_no_se_puede_reutilizar_la_contraseña_vigente(central):
    datos = _login(central)
    with pytest.raises(ErrorSesion) as error:
        central.api.cambiar_password(
            datos["sesion_token"], {"nueva": "Clave1234", "actual": "Clave1234"}
        )
    assert "igual" in str(error.value).lower() or "actual" in str(error.value).lower()
