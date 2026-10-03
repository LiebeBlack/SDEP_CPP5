"""Pruebas del empaquetador y de las comprobaciones del instalador."""

from pathlib import Path

import build


def test_leer_version_falla_si_el_archivo_esta_vacio(tmp_path, monkeypatch):
    (tmp_path / "VERSION").write_text(" \n", encoding="utf-8")
    monkeypatch.setattr(build, "RAIZ", tmp_path)

    try:
        build.leer_version()
    except ValueError as error:
        assert str(tmp_path / "VERSION") in str(error)
    else:
        raise AssertionError("Una versión vacía no debe producir un build")


def test_build_installer_exige_el_actualizador(tmp_path, monkeypatch):
    app_exe = tmp_path / "dist" / "SistemaGestionPersonal" / "SistemaGestionPersonal.exe"
    app_exe.parent.mkdir(parents=True)
    app_exe.write_bytes(b"app")
    monkeypatch.setattr(build, "RAIZ", tmp_path)
    monkeypatch.setattr(build, "localizar_iscc", lambda: Path("ISCC.exe"))
    monkeypatch.setattr(build, "leer_version", lambda: "3.0.1")

    assert build.build_installer() is False


def test_build_installer_falla_si_inno_no_crea_el_paquete(tmp_path, monkeypatch):
    app_exe = tmp_path / "dist" / "SistemaGestionPersonal" / "SistemaGestionPersonal.exe"
    updater_exe = tmp_path / "dist_updater" / "SDEP_CPP5_AutoUpdater.exe"
    app_exe.parent.mkdir(parents=True)
    updater_exe.parent.mkdir(parents=True)
    app_exe.write_bytes(b"app")
    updater_exe.write_bytes(b"updater")
    monkeypatch.setattr(build, "RAIZ", tmp_path)
    monkeypatch.setattr(build, "localizar_iscc", lambda: Path("ISCC.exe"))
    monkeypatch.setattr(build, "leer_version", lambda: "3.0.1")
    monkeypatch.setattr(build.subprocess, "run", lambda *args, **kwargs: None)

    assert build.build_installer() is False


def test_build_installer_confirma_paquete_generado(tmp_path, monkeypatch):
    app_exe = tmp_path / "dist" / "SistemaGestionPersonal" / "SistemaGestionPersonal.exe"
    updater_exe = tmp_path / "dist_updater" / "SDEP_CPP5_AutoUpdater.exe"
    app_exe.parent.mkdir(parents=True)
    updater_exe.parent.mkdir(parents=True)
    app_exe.write_bytes(b"app")
    updater_exe.write_bytes(b"updater")
    monkeypatch.setattr(build, "RAIZ", tmp_path)
    monkeypatch.setattr(build, "localizar_iscc", lambda: Path("ISCC.exe"))
    monkeypatch.setattr(build, "leer_version", lambda: "3.0.1")

    def crear_instalador(comando, **kwargs):
        directorio_salida = Path(next(arg[2:] for arg in comando if arg.startswith("/O")))
        directorio_salida.mkdir(parents=True, exist_ok=True)
        (directorio_salida / "SistemaGestionPersonal-Setup-3.0.1.exe").write_bytes(b"setup")

    monkeypatch.setattr(build.subprocess, "run", crear_instalador)

    assert build.build_installer() is True
    assert (
        tmp_path / "dist_installer" / "SistemaGestionPersonal-Setup-3.0.1.exe"
    ).is_file()


def test_instalador_exige_admin_y_cierra_procesos_bloqueantes():
    setup = (build.RAIZ / "installer" / "setup.iss").read_text(encoding="utf-8")

    assert "PrivilegesRequired=admin" in setup
    assert "CloseApplications=force" in setup
    assert "RestartApplications=no" in setup
