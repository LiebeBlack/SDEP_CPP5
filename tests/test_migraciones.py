"""
Pruebas de migración de esquema (columnas nuevas y purga de lo obsoleto)

Cubre los dos caminos que se ejecutan en cada arranque sobre una base ya
existente: `migrar_columnas` agrega columnas nuevas y
`purgar_esquema_obsoleto` retira las tablas y columnas de los módulos
que se dieron de baja (asistencia, horarios y préstamos).
"""

import pytest
from sqlalchemy import create_engine, text

from src.config.database import (
    COLUMNAS_OBSOLETAS_PAGOS,
    INDICE_MATRICULAS_ACTIVAS,
    MIGRACIONES_EMPLEADOS,
    TABLAS_OBSOLETAS,
    migrar_columnas,
    migrar_matriculas_unicidad_activa,
    purgar_esquema_obsoleto,
)


@pytest.fixture(autouse=True)
def _base_de_datos_de_la_suite(db_config):
    """
    Garantiza que el archivo de la base de la suite exista.

    Las migraciones crean un respaldo previo y el gestor de respaldos copia
    ``settings.database_path``; sin una base ya inicializada el respaldo falla
    y la migración se cancela. Depender de que otra prueba la haya creado hacía
    que este archivo fallara al ejecutarse solo.
    """
    return db_config


@pytest.fixture()
def engine_viejo(tmp_path):
    """Engine SQLite con la tabla empleados SIN las columnas nuevas"""
    engine = create_engine(f"sqlite:///{tmp_path / 'vieja.db'}")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE empleados ("
                "id INTEGER PRIMARY KEY, nombres VARCHAR(100), cedula VARCHAR(20) UNIQUE, "
                "salario_base FLOAT)"
            )
        )
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
        conn.execute(
            text(
                "INSERT INTO empleados (nombres, cedula, salario_base) "
                "VALUES ('Ana Gómez', '12345678', 1500.0)"
            )
        )
    migrar_columnas(engine_viejo)

    with engine_viejo.connect() as conn:
        fila = conn.execute(text("SELECT nombres, cedula, salario_base FROM empleados")).fetchone()
    assert fila == ("Ana Gómez", "12345678", 1500.0)


def test_migracion_permite_insertar_con_columnas_nuevas(engine_viejo):
    migrar_columnas(engine_viejo)
    with engine_viejo.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO empleados (nombres, cedula, salario_base, institucion_bancaria, "
                "numero_cuenta, tipo_cuenta, carnet_discapacidad, tipo_contratacion, "
                "titulo_secundaria, hijos) VALUES "
                "('Luis Pérez', '87654321', 1200.0, 'Banco Nacional', '999', 'ahorro', "
                "'DISC-9', 'fijo', 'Bachiller', 'María (10 años)')"
            )
        )
    with engine_viejo.connect() as conn:
        fila = conn.execute(
            text(
                "SELECT institucion_bancaria, numero_cuenta, tipo_cuenta, carnet_discapacidad, "
                "tipo_contratacion, titulo_secundaria, hijos FROM empleados"
            )
        ).fetchone()
    assert fila == (
        "Banco Nacional",
        "999",
        "ahorro",
        "DISC-9",
        "fijo",
        "Bachiller",
        "María (10 años)",
    )


def test_purgar_esquema_obsoleto_retira_modulos_dados_de_baja(tmp_path):
    """
    La purga elimina las tablas retiradas y reconstruye `pagos` sin las
    columnas del préstamo, conservando los datos de las columnas comunes y
    rehaciendo los índices del modelo.
    """
    from src.models import Base

    engine = create_engine(f"sqlite:///{tmp_path / 'anterior.db'}")
    Base.metadata.create_all(engine)

    # Reproduce el esquema de la versión anterior: las tablas de los módulos
    # retirados y las dos columnas del préstamo dentro de `pagos`.
    with engine.begin() as conn:
        for tabla in TABLAS_OBSOLETAS:
            conn.execute(text(f"CREATE TABLE {tabla} (id INTEGER PRIMARY KEY)"))
        conn.execute(text("ALTER TABLE pagos ADD COLUMN deduccion_prestamo NUMERIC(10, 2)"))
        conn.execute(
            text("ALTER TABLE pagos ADD COLUMN prestamo_id INTEGER REFERENCES prestamos(id)")
        )
        conn.execute(
            text(
                # Fila completa del esquema anterior: al ir por SQL directo
                # hay que dar valor a toda columna no anulable, incluidas las
                # que el ORM rellenaría con su valor por omisión.
                "INSERT INTO pagos (empleado_id, tipo_pago, metodo_pago, periodo_inicio, "
                "periodo_fin, fecha_pago, monto_bruto, monto_neto, descuentos, "
                "bonificaciones, horas_extra, salario_base, deduccion_seguro, "
                "deduccion_pension, deduccion_impuesto, otras_deducciones, "
                "modalidad_calculo, base_gravable, horas_extra_diurnas, "
                "horas_extra_nocturnas, horas_extra_feriadas, aguinaldo, "
                "bono_vacacional, aporte_seguro_patronal, aporte_pension_patronal, "
                "pagado, created_at, updated_at, deduccion_prestamo, prestamo_id) "
                "VALUES "
                "(1, 'nomina', 'transferencia', '2026-01-01', '2026-01-31', '2026-02-01', "
                "1500.00, 1350.00, 0.00, 0.00, 0.00, 1500.00, 0.00, 0.00, 0.00, 0.00, "
                "'porcentaje', 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0, "
                "'2026-02-01 09:00:00', '2026-02-01 09:00:00', 100.00, 1)"
            )
        )

    cambios = purgar_esquema_obsoleto(engine)
    assert cambios == len(COLUMNAS_OBSOLETAS_PAGOS) + len(TABLAS_OBSOLETAS)

    with engine.connect() as conn:
        columnas = {fila[1] for fila in conn.execute(text("PRAGMA table_info(pagos)"))}
        tablas = {
            fila[0]
            for fila in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
        indices = {
            fila[0]
            for fila in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='pagos'")
            )
        }
        fila = conn.execute(text("SELECT id, monto_neto, salario_base FROM pagos")).fetchone()

    for columna in COLUMNAS_OBSOLETAS_PAGOS:
        assert columna not in columnas
    for tabla in TABLAS_OBSOLETAS:
        assert tabla not in tablas
    # Los índices del modelo no se pierden al reconstruir la tabla
    assert "ix_pagos_empleado_id" in indices
    # El dato de la columna común sobrevive a la reconstrucción
    assert fila == (1, 1350.00, 1500.00)

    # Idempotente: una segunda pasada no encuentra nada que purgar
    assert purgar_esquema_obsoleto(engine) == 0
    engine.dispose()


def test_migracion_matriculas_admite_rematricula(tmp_path):
    """
    La migración cambia la unicidad global de ``matriculas`` por una parcial

    El esquema anterior impedía volver a matricular a un estudiante en el
    mismo grado aunque su matrícula estuviera retirada (``activa = 0``). La
    migración reconstruye la tabla con el índice parcial del modelo vigente
    (una sola matrícula ACTIVA por estudiante y grado), conserva el historial y
    es idempotente.
    """
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from src.models import Base, Estudiante, Grado, Matricula, NivelEducativo, PeriodoAcademico

    engine = create_engine(f"sqlite:///{tmp_path / 'matriculas.db'}")
    Base.metadata.create_all(engine)

    # Reproduce el esquema anterior: unicidad global sobre (estudiante, grado)
    # en lugar del índice parcial que crea el modelo vigente.
    with engine.begin() as conn:
        conn.execute(text(f'DROP INDEX IF EXISTS "{INDICE_MATRICULAS_ACTIVAS}"'))
        conn.execute(
            text(
                "CREATE UNIQUE INDEX uq_matriculas_estudiante_grado "
                "ON matriculas (estudiante_id, grado_id)"
            )
        )

    sesion = sessionmaker(bind=engine)()
    try:
        periodo = PeriodoAcademico(nombre="2025-2026")
        sesion.add(periodo)
        sesion.flush()
        grado = Grado(
            periodo_id=periodo.id,
            nivel=NivelEducativo.SECUNDARIA,
            nombre="1er Año",
            seccion="A",
        )
        estudiante = Estudiante(
            nombres="Ana",
            apellidos="Gómez",
            cedula="10000001",
            nivel=NivelEducativo.SECUNDARIA,
        )
        sesion.add_all([grado, estudiante])
        sesion.flush()
        retirada = Matricula(estudiante_id=estudiante.id, grado_id=grado.id, activa=1)
        sesion.add(retirada)
        sesion.commit()
        retirada.activa = 0  # se retira: queda en el historial
        sesion.commit()
        matricula_id = int(retirada.id)
        estudiante_id = int(estudiante.id)
        grado_id = int(grado.id)
    finally:
        sesion.close()

    assert migrar_matriculas_unicidad_activa(engine) == 1

    with engine.connect() as conn:
        indices = {
            fila[0]
            for fila in conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='matriculas'")
            )
        }
    assert INDICE_MATRICULAS_ACTIVAS in indices

    sesion = sessionmaker(bind=engine)()
    try:
        # La matrícula retirada sobrevive con su identificador
        historica = sesion.get(Matricula, matricula_id)
        assert historica is not None
        assert historica.activa == 0
        # Y ahora se puede volver a matricular al mismo estudiante y grado
        nueva = Matricula(estudiante_id=estudiante_id, grado_id=grado_id, activa=1)
        sesion.add(nueva)
        sesion.commit()
        assert nueva.id != matricula_id
    finally:
        sesion.close()

    # Idempotente: la segunda pasada no vuelve a tocar la base
    assert migrar_matriculas_unicidad_activa(engine) == 0
    engine.dispose()
