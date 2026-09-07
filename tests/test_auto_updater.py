"""Pruebas del actualizador automático (updater/auto_updater.py).

Solo cubren la lógica pura (versiones, estado, consulta de Releases e
instalación simulada); nunca descargan archivos ni tocan el Programador
de tareas. La URL de la API se sustituye por un archivo local (file://).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from updater import auto_updater as updater  # noqa: E402

FIXTURE_RELEASE = {
    "tag_name": "continuous-v2.79.55",
    "name": "Release continua v2.79 (#55)",
    "assets": [
        {
            "name": "SistemaGestionPersonal-Linux-2.79.tar.gz",
            "browser_download_url": "https://example.invalid/linux.tar.gz",
            "size": 100,
        },
        {
            "name": "SistemaGestionPersonal-Setup-2.79.exe",
            "browser_download_url": "https://example.invalid/Setup.exe",
            "size": 200,
        },
        {
            "name": "SistemaGestionPersonal-Windows-2.79.zip",
            "browser_download_url": "https://example.invalid/windows.zip",
            "size": 300,
        },
    ],
}


@pytest.fixture()
def release_file(tmp_path):
    """Crea una Release JSON local y la usa como API 'latest'."""
    ruta = tmp_path / "release.json"
    ruta.write_text(json.dumps(FIXTURE_RELEASE), encoding="utf-8")
    updater.API_LATEST_URL = ruta.as_uri()
    updater.INSTALL_IF_MISSING = True
    return ruta


@pytest.fixture()
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SDEP_UPDATE_STATE_DIR", str(tmp_path / "estado"))
    return tmp_path / "estado"


# ---------------------------------------------------------------------------
# Versiones
# ---------------------------------------------------------------------------
def test_parse_version_variantes():
    assert updater.parse_version("continuous-v2.79.55") == (2, 79, 55)
    assert updater.parse_version("v2.79") == (2, 79, 0)
    assert updater.parse_version("2.79.50") == (2, 79, 50)
    assert updater.parse_version("Release v3.0.0") == (3, 0, 0)
    assert updater.parse_version("997a027") is None
    assert updater.parse_version("") is None
    assert updater.parse_version(None) is None


def test_is_newer():
    assert updater.is_newer((2, 79, 55), (2, 79, 50))
    assert updater.is_newer((2, 79, 55), (2, 79, 0))
    assert updater.is_newer((3, 0, 0), (2, 79, 55))
    assert not updater.is_newer((2, 79, 55), (2, 79, 55))
    assert not updater.is_newer((2, 79, 50), (2, 79, 55))
    assert not updater.is_newer((1, 9, 9), (2, 0, 0))


def test_version_to_str():
    assert updater.version_to_str((2, 79, 55)) == "2.79.55"


# ---------------------------------------------------------------------------
# Activos de la Release
# ---------------------------------------------------------------------------
def test_find_setup_asset():
    asset = updater.find_setup_asset(FIXTURE_RELEASE["assets"])
    assert asset is not None
    assert asset["name"] == "SistemaGestionPersonal-Setup-2.79.exe"


def test_find_setup_asset_sin_setup():
    activos = [{"name": "app.exe", "url": "x", "size": 1}]
    assert updater.find_setup_asset(activos)["name"] == "app.exe"
    assert updater.find_setup_asset([]) is None


# ---------------------------------------------------------------------------
# Estado
# ---------------------------------------------------------------------------
def test_estado_roundtrip(isolated_state):
    assert not updater.state_path().exists()
    updater.save_state({"last_tag": "continuous-v2.79.55", "ok": True})
    assert updater.state_path().exists()
    estado = updater.load_state()
    assert estado == {"last_tag": "continuous-v2.79.55", "ok": True}


def test_estado_vacio_si_no_existe(isolated_state):
    assert updater.load_state() == {}


def test_estado_ignora_json_invalido(isolated_state):
    updater.state_path().parent.mkdir(parents=True, exist_ok=True)
    updater.state_path().write_text("{no-json", encoding="utf-8")
    assert updater.load_state() == {}


# ---------------------------------------------------------------------------
# Consulta a la API de GitHub
# ---------------------------------------------------------------------------
def test_fetch_latest(release_file):
    release = updater.fetch_latest()
    assert release["tag"] == "continuous-v2.79.55"
    assert len(release["assets"]) == 3
    assert release["assets"][1]["url"].endswith("Setup.exe")


def test_fetch_latest_error(tmp_path, monkeypatch):
    updater.API_LATEST_URL = (tmp_path / "no_existe.json").as_uri()
    monkeypatch.setattr(updater.time, "sleep", lambda segundos: None)
    with pytest.raises(RuntimeError):
        updater.fetch_latest()


# ---------------------------------------------------------------------------
# Lógica de actualización (run_check)
# ---------------------------------------------------------------------------
def test_run_check_actualizado(release_file, isolated_state):
    updater.save_state({"last_tag": "continuous-v2.79.55"})
    assert updater.run_check(install=True) == 0
    assert updater.load_state()["last_tag"] == "continuous-v2.79.55"


def test_run_check_detecta_actualizacion(release_file, isolated_state):
    updater.save_state({"last_tag": "continuous-v2.79.50"})
    assert updater.run_check(install=False) == 2
    # --check no debe cambiar el estado registrado
    assert updater.load_state()["last_tag"] == "continuous-v2.79.50"


def test_run_check_primera_ejecucion(release_file, isolated_state):
    assert updater.run_check(install=False) == 2


def _falsa_descarga(url, dest, expected_size=0):
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"setup")
    return dest


def test_run_check_instala_y_registra(release_file, isolated_state, monkeypatch):
    monkeypatch.setattr(updater, "app_installed", lambda: True)
    monkeypatch.setattr(updater, "install_setup", lambda ruta: 0)
    monkeypatch.setattr(updater, "download", _falsa_descarga)
    assert updater.run_check(install=True) == 2
    estado = updater.load_state()
    assert estado["last_tag"] == "continuous-v2.79.55"
    assert estado.get("last_installed_utc")


def test_run_check_error_instalador(release_file, isolated_state, monkeypatch):
    monkeypatch.setattr(updater, "app_installed", lambda: True)
    monkeypatch.setattr(updater, "install_setup", lambda ruta: 5)
    monkeypatch.setattr(updater, "download", _falsa_descarga)
    assert updater.run_check(install=True) == 1
    assert "last_tag" not in updater.load_state()


def test_run_check_no_instala_si_falta_y_desactivado(release_file, isolated_state, monkeypatch):
    monkeypatch.setattr(updater, "app_installed", lambda: False)
    updater.INSTALL_IF_MISSING = False
    assert updater.run_check(install=True) == 0


def test_run_check_consulta_fallida(release_file, isolated_state, monkeypatch):
    updater.API_LATEST_URL = (Path(release_file).parent / "ausente.json").as_uri()
    monkeypatch.setattr(updater.time, "sleep", lambda segundos: None)
    assert updater.run_check(install=True) == 1
    assert updater.load_state().get("last_error")