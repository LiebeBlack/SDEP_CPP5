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
