"""
Pruebas del servicio de notas finales

Verifican las tres reglas del módulo: solo escriben la administración o el
docente asignado al grado (con token vigente), el cierre de periodo bloquea
toda escritura —incluido SQL directo, por los disparadores de SQLite— y el
guardado por lotes es atómico.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from src.models import NotaFinal, RolUsuario, Usuario
from src.services import AcademicoService, NotaService, TokenSesionService
from src.utils.helpers import utcnow


@pytest.fixture()
def academico(session):
    """Servicio académico sobre la base de datos de prueba"""
    return AcademicoService(session)


@pytest.fixture()
def notas(session):
    """Servicio de notas sobre la base de datos de prueba"""
    return NotaService(session)


@pytest.fixture()
def admin(session):
    """Cuenta administradora sembrada por la base de datos de prueba"""
    usuario = session.query(Usuario).filter(Usuario.username == "admin").first()
    assert usuario is not None
    return usuario


@pytest.fixture()
def token_admin(session, admin):
    """Token académico de la administración (escribe en cualquier grado)"""
    token, _registro = TokenSesionService(session).emitir(admin)
    return token


@pytest.fixture()
def estructura(academico):
    """Periodo abierto, grado, dos estudiantes matriculados y sus notas base"""
    periodo = academico.crear_periodo({"nombre": "2025-2026"})
    grado = academico.crear_grado(
        {
            "periodo_id": int(periodo.id),
            "nivel": "secundaria",
            "nombre": "1er Año",
            "seccion": "A",
        }
    )
    primero = academico.crear_estudiante(
        {"nombres": "Ana", "apellidos": "Gómez", "cedula": "20000001", "nivel": "secundaria"}
    )
    segundo = academico.crear_estudiante(
        {"nombres": "Luis", "apellidos": "Pérez", "cedula": "20000002", "nivel": "secundaria"}
    )
    academico.matricular(int(primero.id), int(grado.id))
    academico.matricular(int(segundo.id), int(grado.id))
    return {
        "periodo": periodo,
        "grado": grado,
        "estudiante": primero,
        "otro": segundo,
    }


def _datos(estructura, calificacion=15, materia="Matemática", estudiante=None):
    """Payload base de una nota"""
    return {
        "grado_id": int(estructura["grado"].id),
        "estudiante_id": int((estudiante or estructura["estudiante"]).id),
        "materia": materia,
        "calificacion": calificacion,
    }


# ----------------------------------------------------------------------
# Escala y validaciones
# ----------------------------------------------------------------------
def test_escala_y_aprobatoria_desde_la_configuracion(notas):
    assert notas.escala() == (0.0, 20.0)
    assert notas.nota_aprobatoria() == 10.0


def test_registrar_nota_normaliza_la_calificacion(notas, estructura, token_admin):
    nota = notas.registrar(_datos(estructura, "15,5"), token_admin)
    assert float(nota.calificacion) == 15.5
    assert nota.registrado_por == "admin"
    assert nota.materia == "Matemática"


def test_no_se_repite_la_misma_materia(notas, estructura, token_admin):
    notas.registrar(_datos(estructura), token_admin)
    with pytest.raises(ValueError, match="Ya existe una nota"):
        notas.registrar(_datos(estructura, calificacion=18), token_admin)


def test_calificacion_fuera_de_escala_o_invalida(notas, estructura, token_admin):
    with pytest.raises(ValueError, match="entre 0 y 20"):
        notas.registrar(_datos(estructura, calificacion=21), token_admin)
    with pytest.raises(ValueError, match="debe ser un número"):
        notas.registrar(_datos(estructura, calificacion="alto"), token_admin)
    with pytest.raises(ValueError, match="calificación es requerida"):
        notas.registrar(_datos(estructura, calificacion=""), token_admin)


def test_materia_requerida(notas, estructura, token_admin):
    with pytest.raises(ValueError, match="materia es requerida"):
        notas.registrar(_datos(estructura, materia="   "), token_admin)


def test_estudiante_no_matriculado_no_recibe_nota(academico, notas, estructura, token_admin):
    ajeno = academico.crear_estudiante(
        {"nombres": "Marta", "apellidos": "Ruiz", "cedula": "20000003", "nivel": "secundaria"}
    )
    with pytest.raises(ValueError, match="no está matriculado"):
        notas.registrar(_datos(estructura, estudiante=ajeno), token_admin)


# ----------------------------------------------------------------------
# Autorización por token
# ----------------------------------------------------------------------
def test_sin_token_no_se_escribe(notas, estructura):
    with pytest.raises(ValueError, match="token de sesión"):
        notas.registrar(_datos(estructura), None)


def test_el_docente_solo_escribe_en_su_grado(session, academico, notas, estructura, token_admin):
    docente = Usuario(
        username="profesor_notas",
        password_hash="x",
        rol=RolUsuario.USER.value,
        activo=1,
    )
    session.add(docente)
    session.commit()
    token_docente, _registro = TokenSesionService(session).emitir(docente)

    with pytest.raises(ValueError, match="profesor asignado"):
        notas.registrar(_datos(estructura), token_docente)

    academico.asignar_profesor(int(estructura["grado"].id), int(docente.id))
    nota = notas.registrar(_datos(estructura, materia="Historia"), token_docente)
    assert nota.registrado_por == "profesor_notas"


def test_un_rol_de_consulta_no_escribe_aunque_este_asignado(session, academico, notas, estructura):
    consulta = Usuario(
        username="consulta_notas",
        password_hash="x",
        rol=RolUsuario.VIEWER.value,
        activo=1,
    )
    session.add(consulta)
    session.commit()
    academico.asignar_profesor(int(estructura["grado"].id), int(consulta.id))
    token_consulta, _registro = TokenSesionService(session).emitir(consulta)

    with pytest.raises(ValueError, match="profesor asignado"):
        notas.registrar(_datos(estructura), token_consulta)


# ----------------------------------------------------------------------
# Bloqueo por cierre de periodo
# ----------------------------------------------------------------------
def test_el_servicio_bloquea_las_notas_de_un_periodo_cerrado(
    academico, notas, estructura, token_admin
):
    nota = notas.registrar(_datos(estructura), token_admin)
    academico.cerrar_periodo(int(estructura["periodo"].id), token_admin)

    with pytest.raises(ValueError, match="cerrado"):
        notas.registrar(_datos(estructura, materia="Biología"), token_admin)
    with pytest.raises(ValueError, match="cerrado"):
        notas.actualizar(int(nota.id), 18, token_admin)
    with pytest.raises(ValueError, match="cerrado"):
        notas.eliminar(int(nota.id), token_admin)


def test_los_disparadores_bloquean_las_notas_por_sql_directo(
    session, academico, notas, estructura, token_admin
):
    """
    El cierre protege el dato incluso fuera del servicio

    Los disparadores de SQLite existen precisamente para cubrir lo que el
    servicio no controla (scripts de corrección, importaciones masivas), así
    que se prueban por SQL directo y no a través de ``NotaService``.
    """
    nota = notas.registrar(_datos(estructura), token_admin)
    academico.cerrar_periodo(int(estructura["periodo"].id), token_admin)

    with pytest.raises(DatabaseError):
        session.execute(
            text('UPDATE "notas_finales" SET calificacion = 19 WHERE id = :id'),
            {"id": int(nota.id)},
        )
    session.rollback()

    with pytest.raises(DatabaseError):
        session.execute(
            text('DELETE FROM "notas_finales" WHERE id = :id'),
            {"id": int(nota.id)},
        )
    session.rollback()

    momento = utcnow()
    with pytest.raises(DatabaseError):
        session.execute(
            text(
                'INSERT INTO "notas_finales" '
                "(estudiante_id, grado_id, materia, calificacion, created_at, updated_at) "
                "VALUES (:estudiante, :grado, 'Física', 12, :momento, :momento)"
            ),
            {
                "estudiante": int(estructura["estudiante"].id),
                "grado": int(estructura["grado"].id),
                "momento": momento,
            },
        )
    session.rollback()

    # La nota original sigue intacta
    session.expire_all()
    actual = session.get(NotaFinal, int(nota.id))
    assert float(actual.calificacion) == 15.0


def test_un_periodo_reabierto_vuelve_a_permitir_escritura(
    session, academico, notas, estructura, token_admin
):
    academia = academico
    academia.cerrar_periodo(int(estructura["periodo"].id), token_admin)
    academia.reabrir_periodo(int(estructura["periodo"].id), token_admin)
    nota = notas.registrar(_datos(estructura), token_admin)
    assert session.get(NotaFinal, int(nota.id)) is not None


# ----------------------------------------------------------------------
# Guardado por lotes y reportes
# ----------------------------------------------------------------------
def test_guardar_lote_inserta_todas_las_filas(notas, estructura, token_admin):
    filas = [
        _datos(estructura, calificacion=14, materia="Matemática"),
        _datos(estructura, calificacion=16, materia="Historia"),
        _datos(estructura, calificacion=12, materia="Matemática", estudiante=estructura["otro"]),
    ]
    assert notas.guardar_lote(filas, token_admin) == 3
    assert len(notas.listar_notas_de_grado(int(estructura["grado"].id))) == 3


def test_el_lote_es_atomico_y_senala_la_fila_mala(notas, estructura, token_admin):
    filas = [
        _datos(estructura, calificacion=14, materia="Matemática"),
        _datos(estructura, calificacion=99, materia="Historia"),
    ]
    with pytest.raises(ValueError, match="Fila 2"):
        notas.guardar_lote(filas, token_admin)
    assert notas.listar_notas_de_grado(int(estructura["grado"].id)) == []

    with pytest.raises(ValueError, match="No hay notas"):
        notas.guardar_lote([], token_admin)


def test_un_lote_repetido_se_rechaza_completo(notas, estructura, token_admin):
    filas = [
        _datos(estructura, materia="Matemática"),
        _datos(estructura, materia="Matemática"),
    ]
    with pytest.raises(ValueError, match="repetidas"):
        notas.guardar_lote(filas, token_admin)


def test_consolidado_boletin_y_acta(notas, estructura, token_admin):
    notas.registrar(_datos(estructura, calificacion=15, materia="Matemática"), token_admin)
    notas.registrar(_datos(estructura, calificacion=17, materia="Historia"), token_admin)
    periodo_id = int(estructura["periodo"].id)
    grado_id = int(estructura["grado"].id)
    estudiante_id = int(estructura["estudiante"].id)

    consolidado = notas.consolidado_periodo(periodo_id)
    assert len(consolidado) == 2
    assert {"estudiante", "grado", "materia", "calificacion"} <= set(consolidado[0])

    assert notas.promedio(estudiante_id, grado_id) == 16.0

    boletin = notas.datos_boletin(estudiante_id, periodo_id)
    assert boletin["estudiante"]["nombre"] == "Ana Gómez"
    assert boletin["grado"]["nombre"] == "1er Año A"
    assert boletin["promedio"] == 16.0
    assert boletin["nota_aprobatoria"] == 10.0
    # Las notas del boletín salen ordenadas por materia
    assert [fila["materia"] for fila in boletin["notas"]] == ["Historia", "Matemática"]

    acta = notas.datos_acta(grado_id)
    assert acta["materias"] == ["Historia", "Matemática"]
    assert len(acta["filas"]) == 2  # también el estudiante sin notas
    primera = next(f for f in acta["filas"] if f["estudiante_id"] == estudiante_id)
    assert primera["notas"]["Matemática"] == 15.0
    assert primera["promedio"] == 16.0


def test_actualizar_y_eliminar_nota(notas, estructura, token_admin):
    nota = notas.registrar(_datos(estructura), token_admin)
    corregida = notas.actualizar(int(nota.id), 18, token_admin, "Revisión del docente")
    assert float(corregida.calificacion) == 18.0
    assert corregida.observaciones == "Revisión del docente"

    assert notas.eliminar(int(nota.id), token_admin) is True
    assert notas.obtener_nota(int(nota.id)) is None
