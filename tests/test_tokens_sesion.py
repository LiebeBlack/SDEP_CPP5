"""
Pruebas del servicio de tokens de sesión

``emitir`` entrega el token en claro una única vez; la base solo guarda su
hash. La validación comprueba vigencia, alcance y que la cuenta siga activa, y
``puede_escribir`` resuelve la autorización académica con el rol **actual** del
usuario y el grado asignado.
"""

from datetime import timedelta

import pytest

from src.models import RolUsuario, Usuario
from src.services import AcademicoService, TokenSesionService
from src.utils.helpers import utcnow


@pytest.fixture()
def tokens(session):
    """Servicio de tokens sobre la base de datos de prueba"""
    return TokenSesionService(session)


@pytest.fixture()
def admin(session):
    """Cuenta administradora sembrada por la base de datos de prueba"""
    usuario = session.query(Usuario).filter(Usuario.username == "admin").first()
    assert usuario is not None
    return usuario


@pytest.fixture()
def grado(session):
    """Grado de secundaria para probar la autorización por grado"""
    academico = AcademicoService(session)
    periodo = academico.crear_periodo({"nombre": "2025-2026"})
    return academico.crear_grado(
        {
            "periodo_id": int(periodo.id),
            "nivel": "secundaria",
            "nombre": "1er Año",
            "seccion": "A",
        }
    )


def _crear_usuario(session, username: str, rol: str, activo: int = 1) -> Usuario:
    """Usuario mínimo para las pruebas de tokens"""
    usuario = Usuario(username=username, password_hash="x", rol=rol, activo=activo)
    session.add(usuario)
    session.commit()
    return usuario


# ----------------------------------------------------------------------
# Emisión y validación
# ----------------------------------------------------------------------
def test_emitir_solo_guarda_el_hash(tokens, admin):
    token, registro = tokens.emitir(admin)
    assert token
    assert registro.token_hash != token
    assert len(registro.token_hash) == 64
    assert registro.alcance == "academico"

    validado = tokens.validar(token)
    assert validado is not None
    assert validado.id == registro.id
    assert validado.username == "admin"


def test_validar_rechaza_tokens_desconocidos(tokens, admin):
    tokens.emitir(admin)
    assert tokens.validar(None) is None
    assert tokens.validar("") is None
    assert tokens.validar("token-inventado") is None


def test_emitir_exige_usuario_activo(tokens, session):
    with pytest.raises(ValueError, match="usuario autenticado"):
        tokens.emitir(None)
    with pytest.raises(ValueError, match="usuario autenticado"):
        tokens.emitir(Usuario(username="sin_id", password_hash="x", rol="user", activo=1))

    inactivo = _crear_usuario(session, "inactivo", RolUsuario.USER.value, activo=0)
    with pytest.raises(ValueError, match="desactivada"):
        tokens.emitir(inactivo)


def test_el_alcance_limita_la_validez(tokens, admin):
    token, registro = tokens.emitir(admin, alcance="otro")
    assert tokens.validar(token) is None
    validado = tokens.validar(token, "otro")
    assert validado is not None
    assert validado.id == registro.id


def test_un_token_expirado_no_valida(session, tokens, admin):
    token, registro = tokens.emitir(admin)
    registro.expira_en = utcnow() - timedelta(minutes=1)
    session.commit()
    assert tokens.validar(token) is None


# ----------------------------------------------------------------------
# Revocación y limpieza
# ----------------------------------------------------------------------
def test_revocar_invalida_el_token(tokens, admin):
    token, _registro = tokens.emitir(admin)
    assert tokens.revocar(token) is True
    assert tokens.validar(token) is None
    assert tokens.revocar(token) is False
    assert tokens.revocar(None) is False


def test_revocar_usuario_cierra_todas_sus_sesiones(tokens, admin):
    primero, _r1 = tokens.emitir(admin)
    segundo, _r2 = tokens.emitir(admin)
    assert tokens.revocar_usuario(int(admin.id)) == 2
    assert tokens.validar(primero) is None
    assert tokens.validar(segundo) is None
    assert tokens.tokens_vigentes(int(admin.id)) == []


def test_limpiar_expirados_deja_solo_los_vigentes(session, tokens, admin):
    expirado, registro_expirado = tokens.emitir(admin)
    registro_expirado.expira_en = utcnow() - timedelta(minutes=1)
    session.commit()

    revocado, _registro = tokens.emitir(admin)
    tokens.revocar(revocado)

    vigente, _registro = tokens.emitir(admin)

    assert tokens.limpiar_expirados() == 2
    assert tokens.validar(expirado) is None
    assert tokens.validar(revocado) is None
    assert tokens.validar(vigente) is not None


# ----------------------------------------------------------------------
# Autorización académica
# ----------------------------------------------------------------------
def test_puede_escribir_segun_rol_y_grado(session, tokens, grado):
    admin = session.query(Usuario).filter(Usuario.username == "admin").first()
    gestor = _crear_usuario(session, "gestor_t", RolUsuario.MANAGER.value)
    docente = _crear_usuario(session, "docente_t", RolUsuario.USER.value)
    otro_docente = _crear_usuario(session, "docente_ajeno", RolUsuario.USER.value)
    consulta = _crear_usuario(session, "consulta_t", RolUsuario.VIEWER.value)

    grado.profesor_id = int(docente.id)
    session.commit()

    def sesion_de(usuario):
        token, _registro = tokens.emitir(usuario)
        return tokens.validar(token)

    assert tokens.puede_escribir(sesion_de(admin), grado) is True
    assert tokens.puede_escribir(sesion_de(gestor), grado) is True
    assert tokens.puede_escribir(sesion_de(docente), grado) is True
    assert tokens.puede_escribir(sesion_de(otro_docente), grado) is False
    # Sin grado (escritura general) solo la administración pasa
    assert tokens.puede_escribir(sesion_de(admin)) is True
    assert tokens.puede_escribir(sesion_de(docente)) is False
    # Un rol de consulta no escribe ni estando asignado al grado
    grado.profesor_id = int(consulta.id)
    session.commit()
    assert tokens.puede_escribir(sesion_de(consulta), grado) is False


def test_una_degradacion_de_rol_surte_efecto_de_inmediato(session, tokens, grado):
    gestor = _crear_usuario(session, "gestor_degradado", RolUsuario.MANAGER.value)
    token, _registro = tokens.emitir(gestor)
    sesion_token = tokens.validar(token)
    assert tokens.puede_escribir(sesion_token, grado) is True

    gestor.rol = RolUsuario.VIEWER.value
    session.commit()
    assert tokens.puede_escribir(sesion_token, grado) is False


def test_una_cuenta_desactivada_no_escribe(session, tokens, grado):
    docente = _crear_usuario(session, "docente_baja", RolUsuario.USER.value)
    grado.profesor_id = int(docente.id)
    session.commit()
    token, _registro = tokens.emitir(docente)
    assert tokens.validar(token) is not None

    docente.activo = 0
    session.commit()
    assert tokens.validar(token) is None
