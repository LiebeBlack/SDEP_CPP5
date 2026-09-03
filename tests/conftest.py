"""
Fixtures de pruebas

Antes de importar cualquier módulo de src se redirige TODO el almacenamiento
(base de datos, documentos, fotos, exportaciones, backups, logs) a un
directorio temporal mediante SGP_BASE_DIR. Así la suite nunca toca la base
de datos ni los directorios reales del proyecto.

Cada prueba comienza con una base de datos recién sembrada (tablas +
configuración inicial + usuario admin), de modo que los servicios que
asumen unicidad de cédula o conteos exactos se ejecutan aislados.
"""

import atexit
import os
import shutil
import tempfile

# --- Aislamiento: variables de entorno antes de importar src ---
_TMP_ROOT = tempfile.mkdtemp(prefix="sgp_tests_")
os.environ["SGP_BASE_DIR"] = _TMP_ROOT
os.environ["DATABASE_PATH"] = "test_personal.db"
os.environ["DEBUG"] = "False"


def _cleanup():
    shutil.rmtree(_TMP_ROOT, ignore_errors=True)


atexit.register(_cleanup)

import pytest  # noqa: E402


def _reset_database(db_config):
    """Limpia todas las tablas y vuelve a sembrar la configuración inicial"""
    from sqlalchemy import text

    from src.models import Base

    with db_config.engine.begin() as conn:
        for tabla in Base.metadata.sorted_tables:
            conn.execute(text(f'DELETE FROM "{tabla.name}"'))
    db_config.init_db()


@pytest.fixture(scope="session")
def db_config():
    """Configuración de base de datos aislada (una vez por sesión)"""
    from src.config import db_config
    db_config.init_db()
    yield db_config
    db_config.engine.dispose()


@pytest.fixture()
def session(db_config):
    """Sesión de base de datos limpia y sembrada para cada prueba"""
    _reset_database(db_config)
    sesion = db_config.get_session()
    yield sesion
    db_config.close_session(sesion)


@pytest.fixture()
def storage(tmp_path, monkeypatch):
    """Redirige el almacenamiento de documentos/fotos a un directorio temporal"""
    from src.config import settings
    from src.utils.helpers import ensure_directory_exists

    for attr in ("documents_path", "photos_path", "exports_path"):
        destino = str(tmp_path / attr)
        ensure_directory_exists(destino)
        monkeypatch.setattr(settings, attr, destino)
    return tmp_path
