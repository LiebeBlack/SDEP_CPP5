"""
Fixtures de pruebas

Antes de importar cualquier módulo de src se redirige la base de datos
a un archivo temporal, de modo que la suite nunca toca la base de datos
real del proyecto.
"""

import atexit
import os
import shutil
import tempfile

# --- Aislamiento: variables de entorno antes de importar src ---
_TMP_ROOT = tempfile.mkdtemp(prefix="sgp_tests_")
_DB_PATH = os.path.join(_TMP_ROOT, "test_personal.db")
_STORAGE_ROOT = os.path.join(_TMP_ROOT, "storage")

os.environ["DATABASE_PATH"] = _DB_PATH
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.replace(os.sep, '/')}"
os.environ["DOCUMENTS_PATH"] = "documents"
os.environ["PHOTOS_PATH"] = "photos"
os.environ["EXPORTS_PATH"] = "exports"
os.environ["DEBUG"] = "False"


def _cleanup():
    shutil.rmtree(_TMP_ROOT, ignore_errors=True)


atexit.register(_cleanup)

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def db_config():
    """Configuración de base de datos aislada (una vez por sesión)"""
    from src.config import db_config
    db_config.init_db()
    yield db_config
    db_config.engine.dispose()


@pytest.fixture()
def session(db_config):
    """Sesión de base de datos aislada por prueba"""
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
