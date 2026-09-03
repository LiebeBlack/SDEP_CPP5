"""Pruebas de migración de esquema (columnas nuevas en bases existentes)"""

import pytest
from sqlalchemy import create_engine, text

from src.config.database import MIGRACIONES_EMPLEADOS, migrar_columnas


@pytest.fixture()
def engine_viejo(tmp_path):
    """Engine SQLite con la tabla empleados SIN las columnas nuevas"""
    engine = create_engine(f"sqlite:///{tmp_path / 'vieja.db'}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE empleados ("
            "id INTEGER PRIMARY KEY, nombres VARCHAR(100), cedula VARCHAR(20) UNIQUE, "
            "salario_base FLOAT)"
        ))
    yield engine
    engine.dispose()


def test_migracion_agrega_columnas_faltantes(engine_viejo):
    agregadas = migrar_columnas(engine_viejo)
    assert agregadas == len(MIGRACIONES_EMPLEADOS)

    with engine_viejo.connect() as conn:
        columnas = {row[1] for row in conn.execute(text("PRAGMA table_info(empleados)"))}
    assert "institucion_bancaria" in columnas
    assert "numero_cuenta" in columnas
    assert "tipo_cuenta" in columnas
    assert "carnet_discapacidad" in columnas
    assert "enfermedades_preexistentes" in columnas
    assert "alergias_medicamentosas" in columnas
    assert "alergias_alimentarias" in columnas
    assert "tipo_contratacion" in columnas
    assert "titulo_secundaria" in columnas
    assert "hijos" in columnas


def test_migracion_es_idempotente(engine_viejo):
    migrar_columnas(engine_viejo)
    assert migrar_columnas(engine_viejo) == 0


def test_migracion_no_rompe_datos_existentes(engine_viejo):
    with engine_viejo.begin() as conn:
        conn.execute(text(
            "INSERT INTO empleados (nombres, cedula, salario_base) "
            "VALUES ('Ana Gómez', '12345678', 1500.0)"
        ))
    migrar_columnas(engine_viejo)

    with engine_viejo.connect() as conn:
        fila = conn.execute(text(
            "SELECT nombres, cedula, salario_base FROM empleados"
        )).fetchone()
    assert fila == ("Ana Gómez", "12345678", 1500.0)


def test_migracion_permite_insertar_con_columnas_nuevas(engine_viejo):
    migrar_columnas(engine_viejo)
    with engine_viejo.begin() as conn:
        conn.execute(text(
            "INSERT INTO empleados (nombres, cedula, salario_base, institucion_bancaria, "
            "numero_cuenta, tipo_cuenta, carnet_discapacidad, tipo_contratacion, "
            "titulo_secundaria, hijos) VALUES "
            "('Luis Pérez', '87654321', 1200.0, 'Banco Nacional', '999', 'ahorro', "
            "'DISC-9', 'fijo', 'Bachiller', 'María (10 años)')"
        ))
    with engine_viejo.connect() as conn:
        fila = conn.execute(text(
            "SELECT institucion_bancaria, numero_cuenta, tipo_cuenta, carnet_discapacidad, "
            "tipo_contratacion, titulo_secundaria, hijos FROM empleados"
        )).fetchone()
    assert fila == ("Banco Nacional", "999", "ahorro", "DISC-9", "fijo", "Bachiller", "María (10 años)")