"""
Pruebas del servicio académico

Cubren las reglas que sostienen el subdominio: unicidad de cédula (en el
servicio y en la base), coherencia de fechas y niveles, una sola matrícula
activa por año escolar y el cierre de periodo, que solo un administrador
puede ejecutar (y reabrir) con un token de sesión válido.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from src.models import Estudiante, NivelEducativo, RolUsuario, Usuario
from src.services import AcademicoService, TokenSesionService


@pytest.fixture()
def academico(session):
    """Servicio académico sobre la base de datos de prueba"""
    return AcademicoService(session)


@pytest.fixture()
def admin(session):
    """Cuenta administradora sembrada por la base de datos de prueba"""
    usuario = session.query(Usuario).filter(Usuario.username == "admin").first()
    assert usuario is not None
    return usuario


@pytest.fixture()
def token_admin(session, admin):
    """Token académico de la cuenta administradora"""
    token, _registro = TokenSesionService(session).emitir(admin)
    return token


@pytest.fixture()
def periodo(academico):
    """Año escolar abierto"""
    return academico.crear_periodo({"nombre": "2025-2026"})


@pytest.fixture()
def grado(academico, periodo):
    """Grado de secundaria dentro del periodo"""
    return academico.crear_grado(
        {
            "periodo_id": int(periodo.id),
            "nivel": "secundaria",
            "nombre": "1er Año",
            "seccion": "A",
        }
    )


@pytest.fixture()
def estudiante(academico):
    """Estudiante activo de secundaria"""
    return academico.crear_estudiante(
        {
            "nombres": "Ana",
            "apellidos": "Gómez",
            "cedula": "10000001",
            "nivel": "secundaria",
        }
    )


# ----------------------------------------------------------------------
# Estudiantes
# ----------------------------------------------------------------------
def test_crear_estudiante_normaliza_los_datos(academico):
    estudiante = academico.crear_estudiante(
        {
            "nombres": "  Ana ",
            "apellidos": "Gómez",
            "cedula": " 10000001 ",
            "nivel": "secundaria",
            "telefono": "   ",
        }
    )
    assert estudiante.nombre_completo == "Ana Gómez"
    assert estudiante.cedula == "10000001"
    assert estudiante.telefono is None
    assert estudiante.activo == 1


def test_estudiante_sin_nombres_falla(academico):
    with pytest.raises(ValueError, match="nombres y apellidos"):
        academico.crear_estudiante({"nombres": " ", "apellidos": "Gómez", "nivel": "secundaria"})


def test_nivel_invalido_falla(academico):
    with pytest.raises(ValueError, match="Nivel educativo"):
        academico.crear_estudiante(
            {"nombres": "Ana", "apellidos": "Gómez", "nivel": "universidad"}
        )


def test_cedula_duplicada_se_rechaza(academico, estudiante):
    with pytest.raises(ValueError, match="cédula"):
        academico.crear_estudiante(
            {
                "nombres": "Otro",
                "apellidos": "Estudiante",
                "cedula": "10000001",
                "nivel": "secundaria",
            }
        )


def test_la_base_rechaza_cedulas_duplicadas_por_su_restriccion(session, academico, estudiante):
    """El servicio avisa antes, pero la garantía real está en el esquema."""
    duplicado = Estudiante(
        nombres="Otra",
        apellidos="Persona",
        cedula="10000001",
        nivel=NivelEducativo.SECUNDARIA,
    )
    session.add(duplicado)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    assert session.query(Estudiante).count() == 1


def test_desactivar_y_activar_estudiante(academico, estudiante):
    assert academico.desactivar_estudiante(int(estudiante.id)) is True
    assert academico.obtener_estudiante(int(estudiante.id)).activo == 0
    assert academico.activar_estudiante(int(estudiante.id)) is True
    assert academico.obtener_estudiante(int(estudiante.id)).activo == 1


def test_buscar_estudiantes_por_termino(academico, estudiante):
    assert [e.id for e in academico.buscar_estudiantes("Gómez")] == [estudiante.id]
    assert [e.id for e in academico.buscar_estudiantes("10000001")] == [estudiante.id]
    assert academico.buscar_estudiantes("nadie") == []


def test_estadisticas_del_modulo(academico, grado, estudiante):
    academico.matricular(int(estudiante.id), int(grado.id))
    datos = academico.estadisticas()
    assert datos["estudiantes"] == 1
    assert datos["estudiantes_activos"] == 1
    assert datos["periodos"] == 1
    assert datos["grados"] == 1
    assert datos["matriculas_activas"] == 1
    assert datos["por_nivel"].get("secundaria") == 1


# ----------------------------------------------------------------------
# Periodos académicos
# ----------------------------------------------------------------------
def test_periodo_duplicado_y_fechas_invertidas(academico, periodo):
    with pytest.raises(ValueError, match="Ya existe un periodo"):
        academico.crear_periodo({"nombre": "2025-2026"})
    with pytest.raises(ValueError, match="anterior"):
        academico.crear_periodo(
            {
                "nombre": "2026-2027",
                "fecha_inicio": "30/06/2026",
                "fecha_fin": "01/09/2026",
            }
        )


def test_el_estado_no_se_cambia_por_actualizacion(academico, periodo):
    with pytest.raises(ValueError, match="cerrar/reabrir"):
        academico.actualizar_periodo(int(periodo.id), {"estado": "cerrado"})


def test_cerrar_periodo_exige_token_y_rol_administrador(session, academico, periodo, admin):
    servicio_tokens = TokenSesionService(session)
    docente = Usuario(
        username="docente_token",
        password_hash="x",
        rol=RolUsuario.USER.value,
        activo=1,
    )
    session.add(docente)
    session.commit()
    token_docente, _registro = servicio_tokens.emitir(docente)

    with pytest.raises(ValueError, match="Token de sesión"):
        academico.cerrar_periodo(int(periodo.id), None)
    with pytest.raises(ValueError, match="administrador"):
        academico.cerrar_periodo(int(periodo.id), token_docente)
    assert academico.obtener_periodo(int(periodo.id)).esta_cerrado is False

    token_admin, _registro = servicio_tokens.emitir(admin)
    cerrado = academico.cerrar_periodo(int(periodo.id), token_admin)
    assert cerrado.esta_cerrado is True
    assert cerrado.cerrado_por == "admin"
    assert cerrado.cerrado_en is not None

    with pytest.raises(ValueError, match="ya está cerrado"):
        academico.cerrar_periodo(int(periodo.id), token_admin)


def test_reabrir_periodo_lo_deja_abierto(academico, periodo, token_admin):
    academico.cerrar_periodo(int(periodo.id), token_admin)
    reabierto = academico.reabrir_periodo(int(periodo.id), token_admin)
    assert reabierto.esta_cerrado is False
    assert reabierto.cerrado_por is None
    assert reabierto.cerrado_en is None


def test_periodo_en_curso_es_el_ultimo_abierto(academico, periodo):
    assert academico.periodo_en_curso().id == periodo.id


# ----------------------------------------------------------------------
# Grados y matrículas
# ----------------------------------------------------------------------
def test_grado_duplicado_se_rechaza(academico, periodo, grado):
    with pytest.raises(ValueError, match="Ya existe"):
        academico.crear_grado(
            {
                "periodo_id": int(periodo.id),
                "nivel": "secundaria",
                "nombre": "1er Año",
                "seccion": "A",
            }
        )


def test_grado_sin_periodo_falla(academico):
    with pytest.raises(ValueError, match="periodo académico"):
        academico.crear_grado({"nivel": "secundaria", "nombre": "1er Año"})


def test_matricular_valida_nivel_y_unicidad(academico, grado, estudiante):
    matricula = academico.matricular(int(estudiante.id), int(grado.id))
    assert matricula.activa == 1

    with pytest.raises(ValueError, match="ya está matriculado"):
        academico.matricular(int(estudiante.id), int(grado.id))

    inicial = academico.crear_estudiante(
        {"nombres": "Luis", "apellidos": "Pérez", "nivel": "inicial"}
    )
    with pytest.raises(ValueError, match="nivel"):
        academico.matricular(int(inicial.id), int(grado.id))


def test_retirar_matricula_permite_volver_a_matricular(academico, grado, estudiante):
    matricula = academico.matricular(int(estudiante.id), int(grado.id))
    assert academico.retirar_matricula(int(matricula.id)) is True
    assert academico.listar_matriculas_de_grado(int(grado.id)) == []

    nueva = academico.matricular(int(estudiante.id), int(grado.id))
    assert nueva.id != matricula.id


def test_asignar_profesor_valida_el_usuario(session, academico, grado):
    docente = Usuario(
        username="profesor1",
        password_hash="x",
        rol=RolUsuario.USER.value,
        activo=1,
    )
    session.add(docente)
    session.commit()

    actualizado = academico.asignar_profesor(int(grado.id), int(docente.id))
    assert actualizado.profesor_id == docente.id
    assert actualizado.profesor.username == "profesor1"

    with pytest.raises(ValueError, match="no existe o está inactivo"):
        academico.asignar_profesor(int(grado.id), 999999)

    actualizado = academico.asignar_profesor(int(grado.id), None)
    assert actualizado.profesor_id is None
