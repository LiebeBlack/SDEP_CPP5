"""Pruebas del sistema de backups y auditoría"""

from datetime import date

import pytest

from src.services.empleado_service import EmpleadoService


def _crear_empleado(session, cedula, nombres="Marco"):
    servicio = EmpleadoService(session)
    return servicio.crear_empleado({
        "nombres": nombres,
        "apellidos": "Antunes",
        "cedula": cedula,
        "tipo_empleado": "docente",
        "cargo": "Docente de Lengua",
        "departamento": "Letras",
        "fecha_contratacion": date(2022, 2, 1),
        "salario_base": 1100.0,
    })


def test_ciclo_completo_backup_y_restauracion(session, db_config):
    from src.utils.backup_manager import get_backup_manager

    gestor = get_backup_manager()
    primero = _crear_empleado(session, "70010001")
    primero_id = primero.id

    info = gestor.create_backup("estado_inicial")
    assert info["version"] == 2
    assert info["compressed"]
    assert info["checksum"]

    segundo = _crear_empleado(session, "70010002")
    segundo_id = segundo.id
    assert EmpleadoService(session).obtener_empleado(segundo_id) is not None

    # Restaurar: el segundo empleado debe desaparecer
    assert gestor.restore_backup("estado_inicial")

    nueva_sesion = db_config.get_session()
    try:
        assert EmpleadoService(nueva_sesion).obtener_empleado(primero_id) is not None
        assert EmpleadoService(nueva_sesion).obtener_empleado(segundo_id) is None
    finally:
        db_config.close_session(nueva_sesion)


def test_integridad_listar_y_eliminar(session):
    from src.utils.backup_manager import get_backup_manager

    gestor = get_backup_manager()
    _crear_empleado(session, "70010003")
    gestor.create_backup("verificar_este")

    lista = gestor.list_backups()
    nombres = [b["name"] for b in lista]
    assert "verificar_este" in nombres

    resultado = gestor.verify_backup_integrity("verificar_este")
    assert resultado["exists"]
    assert resultado["checksum_valid"]
    assert resultado["integrity_ok"]

    assert gestor.delete_backup("verificar_este")
    with pytest.raises(ValueError):
        gestor.verify_backup_integrity("verificar_este")


def test_backup_corrupto_detectado(session):
    from src.utils.backup_manager import get_backup_manager
    from pathlib import Path

    gestor = get_backup_manager()
    _crear_empleado(session, "70010004")
    gestor.create_backup("corromper_este")

    ruta = Path(gestor.metadata["corromper_este"]["path"])
    with open(ruta, "rb") as f:
        contenido = bytearray(f.read())
    contenido[len(contenido) // 2] ^= 0xFF  # corromper un byte
    with open(ruta, "wb") as f:
        f.write(contenido)

    resultado = gestor.verify_backup_integrity("corromper_este")
    assert not resultado["checksum_valid"]
    assert not resultado["integrity_ok"]

    with pytest.raises(Exception) as exc:
        gestor.restore_backup("corromper_este")
    assert "checksum" in str(exc.value).lower()


def _gestor_con_metadatos(tmp_path, cantidad, max_backups=10):
    """BackupManager aislado con N backups ficticios (el 0 es el más antiguo)."""
    from src.utils.backup_manager import BackupManager

    gestor = BackupManager()
    gestor.backup_dir = tmp_path
    gestor.metadata_file = tmp_path / "backup_metadata.json"
    gestor.max_backups = max_backups
    metadatos = {}
    for i in range(cantidad):
        nombre = f"b{i}"
        ruta = tmp_path / f"{nombre}.db.gz"
        ruta.write_bytes(b"x")
        metadatos[nombre] = {
            "name": nombre,
            "filename": f"{nombre}.db.gz",
            "path": str(ruta),
            "timestamp": f"2026090{i + 1:02d}_000000",  # b0 = 2026-09-01 (más viejo)
            "size_bytes": 1,
            "checksum": "",
            "compressed": True,
            "version": 2,
        }
    gestor.metadata = metadatos
    return gestor


def test_rotacion_conserva_los_mas_recientes(tmp_path):
    """Al superar el límite se eliminan los MÁS ANTIGUOS, no los nuevos."""
    gestor = _gestor_con_metadatos(tmp_path, cantidad=6, max_backups=3)

    stats = gestor.rotate_backups()

    assert stats["deleted_count"] == 3
    assert stats["total_after"] == 3
    conservados = sorted(gestor.metadata.keys())
    # Se quedan los 3 más recientes (b3, b4, b5); se borran b0, b1, b2
    assert conservados == ["b3", "b4", "b5"]
    for eliminado in ("b0", "b1", "b2"):
        assert eliminado not in gestor.metadata
        assert not (gestor.backup_dir / f"{eliminado}.db.gz").exists()


def test_rotacion_no_borra_cuando_hay_pocos_backups(tmp_path):
    gestor = _gestor_con_metadatos(tmp_path, cantidad=2, max_backups=5)
    stats = gestor.rotate_backups()
    assert stats["deleted_count"] == 0
    assert len(gestor.metadata) == 2


def test_rotacion_elimina_por_antiguedad(tmp_path, monkeypatch):
    """Backups fuera de la retención se eliminan aunque no se supere el límite."""
    from datetime import datetime, timedelta

    gestor = _gestor_con_metadatos(tmp_path, cantidad=3, max_backups=10)
    # Simular que hace 45 días se eliminó todo menos el más nuevo
    gestor.backup_retention_days = 30
    monkeypatch.setattr(
        gestor,
        "metadata",
        {
            "viejo": {
                "name": "viejo", "filename": "viejo.db.gz",
                "path": str(tmp_path / "viejo.db.gz"),
                "timestamp": (datetime.now() - timedelta(days=45)).strftime("%Y%m%d_%H%M%S"),
                "size_bytes": 1, "checksum": "", "compressed": True, "version": 2,
            },
            "reciente": {
                "name": "reciente", "filename": "reciente.db.gz",
                "path": str(tmp_path / "reciente.db.gz"),
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "size_bytes": 1, "checksum": "", "compressed": True, "version": 2,
            },
        },
    )
    (tmp_path / "viejo.db.gz").write_bytes(b"x")
    (tmp_path / "reciente.db.gz").write_bytes(b"x")

    stats = gestor.rotate_backups()
    assert stats["deleted_count"] == 1
    assert "viejo" not in gestor.metadata
    assert "reciente" in gestor.metadata


def test_exportar_auditoria_genera_json(session, storage):
    from src.utils.audit_logger import AuditEventType, get_audit_logger

    auditor = get_audit_logger()
    auditor.log_event(
        event_type=AuditEventType.USER_LOGIN,
        entity_type="usuario",
        user="admin",
        details={"prueba": True},
    )

    ruta = auditor.export_audit_log("2000-01-01", "2100-01-01")
    assert ruta.endswith(".json")
    with open(ruta, "r", encoding="utf-8") as f:
        import json
        eventos = json.load(f)
    assert any(e["user"] == "admin" for e in eventos)
