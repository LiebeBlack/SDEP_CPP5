"""
Sincronización del subdominio académico

Verifica el registro de las cinco tablas académicas (estudiantes, periodos,
grados, matrículas y notas finales) y las dos decisiones que protegen datos
reales: una calificación es campo sensible (todo choque se audita) y los
tokens de sesión no viajan entre equipos porque son credenciales locales.
"""

from sync_agent import merge, registro

TABLAS_ACADEMICAS = {
    "estudiantes",
    "periodos_academicos",
    "grados",
    "matriculas",
    "notas_finales",
}


def test_las_tablas_academicas_estan_registradas():
    assert TABLAS_ACADEMICAS <= set(registro.tablas_sincronizadas())


def test_los_tokens_de_sesion_no_se_replican():
    """Un token es una credencial del equipo: replicarlo no tiene sentido."""
    assert not registro.es_sincronizable("tokens_sesion")
    assert "tokens_sesion" not in registro.tablas_sincronizadas()


def test_las_claves_foraneas_academicas_apuntan_a_sus_padres():
    """Las claves foráneas viajan como UUID, no como ids locales."""
    assert registro.claves_foraneas("grados")["periodo_id"] == "periodos_academicos"
    assert registro.claves_foraneas("matriculas") == {
        "estudiante_id": "estudiantes",
        "grado_id": "grados",
    }
    assert registro.claves_foraneas("notas_finales") == {
        "estudiante_id": "estudiantes",
        "grado_id": "grados",
    }


def test_las_calificaciones_son_campo_sensible():
    """Un choque de calificaciones queda registrado aunque la regla lo resuelva."""
    assert "calificacion" in merge.CAMPOS_SENSIBLES["notas_finales"]


def test_las_matriculas_se_retiran_con_baja_logica():
    """Retirar una matrícula la desactiva; no se borra su historial."""
    entidad = registro.ENTIDADES["matriculas"]
    assert entidad.borrado_logico is True
    assert entidad.columna_activo == "activa"


def test_la_clave_compuesta_solo_usa_columnas_de_la_tabla():
    """Las claves compuestas se evalúan con columnas reales del modelo."""
    for nombre in ("grados", "notas_finales"):
        entidad = registro.ENTIDADES[nombre]
        disponibles = set(registro.columnas(nombre))
        assert set(entidad.clave_natural_compuesta) <= disponibles, nombre
