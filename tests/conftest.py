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
import logging
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

logger = logging.getLogger(__name__)


def _reset_database(db_config):
    """Limpia todas las tablas y vuelve a sembrar la configuración inicial

    El borrado va en orden inverso al de dependencias (hijos antes que
    padres): la conexión tiene activada la verificación de claves foráneas,
    así que borrar primero un empleado con documentos, pagos o contratos
    vivos fallaría como violación de integridad referencial.
    """
    from sqlalchemy import text

    from src.models import Base

    with db_config.engine.begin() as conn:
        # Los disparadores de inmutabilidad abortan el DELETE sobre
        # ``notas_finales`` cuando su grado pertenece a un periodo cerrado.
        # Como todos los DELETE van en una sola transacción, ese abort
        # revertía el reseteo completo y la base quedaba con las filas de la
        # prueba anterior: eso contaminaba en cascada a todas las pruebas
        # siguientes. Reabrir los periodos antes de vaciar desactiva la
        # condición de los disparadores y permite limpiar de verdad.
        tablas_existentes = {
            fila[0]
            for fila in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        }
        if "periodos_academicos" in tablas_existentes:
            conn.execute(text("UPDATE periodos_academicos SET estado = 'abierto'"))
        for tabla in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'DELETE FROM "{tabla.name}"'))
    db_config.init_db()

    # El agente de sincronización guarda identidad global por tabla e id local:
    # si esas tablas sobrevivieran al reinicio de los datos, un empleado nuevo
    # reutilizaría el id local de otro y heredaría su identidad global.
    try:
        from sync_agent.esquema import BaseSync

        tablas_sync = [tabla.name for tabla in reversed(BaseSync.metadata.sorted_tables)]
    except Exception:
        tablas_sync = []
    for nombre in tablas_sync:
        try:
            with db_config.engine.begin() as conn:
                conn.execute(text(f'DELETE FROM "{nombre}"'))
        except Exception:
            logger.debug("No se pudo limpiar la tabla %s del agente", nombre, exc_info=True)


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
def entorno_sync(db_config, monkeypatch):
    """
    Aisla el agente de sincronización dentro de una prueba

    La suite comparte un único archivo de base de datos y un único config.json,
    así que sin esta limpieza una prueba vería el journal, la identidad y los
    conflictos que dejaron las anteriores. Deja la base recién sembrada, las
    tablas del agente vacías, la captura de cambios instalada y la
    configuración del equipo en blanco (variables de entorno incluidas).
    """
    from sqlalchemy import text

    import sync_agent
    from src.config import settings
    from sync_agent import captura
    from sync_agent import config as config_sync
    from sync_agent import esquema

    _reset_database(db_config)
    db_config.preparar_sincronizacion()
    db_config.activar_captura_sincronizacion()

    with db_config.engine.begin() as conn:
        for tabla in reversed(esquema.BaseSync.metadata.sorted_tables):
            conn.execute(text(f'DELETE FROM "{tabla.name}"'))

    def _limpiar_configuracion_sync():
        """Deja la configuración del equipo como recién instalada"""
        for clave in (
            config_sync.CLAVE_HABILITADO,
            config_sync.CLAVE_URL,
            config_sync.CLAVE_TOKEN,
            config_sync.CLAVE_DISPOSITIVO,
            config_sync.CLAVE_EQUIPO,
            config_sync.CLAVE_INTERVALO,
            config_sync.CLAVE_BINARIO_MAX,
        ):
            try:
                settings.delete_config_value(clave)
            except OSError:
                pass
        for variable in (
            "SDP_SYNC_ACTIVADO",
            "SDP_SYNC_URL",
            "SDP_SYNC_TOKEN",
            "SDP_SYNC_INTERVALO",
            "SDP_SYNC_BINARIO_MAX",
            "SDP_SYNC_EQUIPO",
        ):
            monkeypatch.delenv(variable, raising=False)

    _limpiar_configuracion_sync()
    captura.establecer_dispositivo(None)
    sync_agent._agente = None

    yield db_config

    if sync_agent._agente is not None:
        try:
            sync_agent._agente.detener(timeout=5.0)
        except Exception:
            pass
        sync_agent._agente = None
    # Sin esta limpieza, una prueba posterior que construya la ventana
    # principal arrancaría el agente contra el servidor de esta prueba (ya
    # apagado) y ensuciaría su resultado.
    _limpiar_configuracion_sync()
    captura.establecer_dispositivo(None)


@pytest.fixture()
def storage(tmp_path, monkeypatch):
    """Redirige el almacenamiento de documentos/fotos a un directorio temporal"""
    from src.config import settings
    from src.utils.helpers import ensure_directory_exists

    # `temp_dir` también se redirige: el directorio base de las pruebas es
    # ancestro de `tmp_path`, y al limpiar temporales se recorría el almacén
    # entero del test. En producción esas carpetas son hermanas, no anidadas.
    for attr in ("documents_path", "photos_path", "exports_path", "temp_dir"):
        destino = str(tmp_path / attr)
        ensure_directory_exists(destino)
        monkeypatch.setattr(settings, attr, destino)
    return tmp_path
