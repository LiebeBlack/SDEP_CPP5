"""Pruebas de la resolución de versión de la aplicación.

Cadena de precedencia de settings.app_version:
    variable de entorno APP_VERSION > build_info incrustado (CI/build.py)
    > archivo VERSION (desarrollo) > constante APP_VERSION_DEFAULT.
"""

import sys
from pathlib import Path

from src.config.settings import Settings

RAIZ = Path(__file__).resolve().parents[1]

# El paquete src.config exporta 'settings' como instancia, así que el módulo
# solo es accesible de forma fiable a través de sys.modules.
settings_module = sys.modules["src.config.settings"]


class _BuildInfoFalso:
    """Simula el módulo generado src/config/build_info.py"""

    BUILD_VERSION = "2.79.55"
    BUILD_COMMIT = "abc1234"
    BUILD_DATE = "2026-09-07T00:00:00+00:00"


def test_version_desde_archivo_version_sin_build_info(monkeypatch):
    # En desarrollo, sin build_info.py, la versión sale de VERSION
    monkeypatch.setattr(settings_module, "_build_info", None)
    s = Settings()
    esperado = RAIZ.joinpath("VERSION").read_text(encoding="utf-8").strip()
    assert s.app_version == esperado
    assert s.build_commit == ""


def test_version_desde_build_info_incrustado(monkeypatch):
    monkeypatch.setattr(settings_module, "_build_info", _BuildInfoFalso())
    s = Settings()
    assert s.app_version == "2.79.55"
    assert s.build_commit == "abc1234"
    assert s.build_date == "2026-09-07T00:00:00+00:00"


def test_variable_entorno_gana_a_build_info(monkeypatch):
    monkeypatch.setattr(settings_module, "_build_info", _BuildInfoFalso())
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    s = Settings()
    assert s.app_version == "9.9.9"


def test_default_cuando_no_hay_nada(monkeypatch):
    monkeypatch.setattr(settings_module, "_build_info", None)
    # Simula un empaquetado sin VERSION ni build_info: la lectura de
    # VERSION falla y cae al valor por defecto.
    monkeypatch.setattr(settings_module, "_version_desarrollo", lambda: "")
    s = Settings()
    assert s.app_version == "2.79"