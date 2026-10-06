"""
Pruebas de la captura de cambios del agente de sincronización

Lo que se verifica aquí es el corazón del modo offline: la aplicación sigue
escribiendo en su SQLite local y, **en la misma transacción**, un enganche del
ORM deja constancia de cada cambio replicable. Si la operación del usuario se
deshace, la operación tampoco se anuncia al resto de la red; y si el cambio
llega desde la red, no se reenvía (efecto eco).
"""

from datetime import date

from src.models import Configuracion, Documento, Empleado
from src.services.empleado_service import EmpleadoService
from sync_agent.comun import hash_bytes, loads
from sync_agent.esquema import (
    DIRECCION_SALIDA,
    PENDIENTE,
    CampoRemoto,
    JournalOp,
    SyncId,
    VersionFila,
)


def _datos_empleado(cedula="12345678", **cambios):
    """Datos mínimos de un empleado válido para el servicio"""
    datos = {
        "nombres": "Ana",
        "apellidos": "Gómez",
        "cedula": cedula,
        "fecha_nacimiento": date(1990, 5, 12),
        "genero": "femenino",
        "estado_civil": "soltero",
        "tipo_empleado": "docente",
        "cargo": "Docente de Matemáticas",
        "departamento": "Matemáticas",
        "fecha_contratacion": date(2020, 1, 15),
        "salario_base": 1500.0,
        "email": "ana.gomez@example.com",
        "telefono": "555-0100",
    }
    datos.update(cambios)
    return datos


def _empleado_minimo(cedula="60000000", **cambios):
    """Empleado válido construido a mano (sin pasar por el servicio)

    Se usa para simular datos que ya existían antes del agente: el servicio
    impone reglas de negocio que aquí solo estorbarían. Los campos sin valor
    por defecto en la columna se declaran porque son `NOT NULL`.
    """
    datos = {
        "cedula": cedula,
        "nombres": "Marta",
        "apellidos": "Ruiz",
        "tipo_empleado": "docente",
        "cargo": "Docente",
        "departamento": "Docencia",
        "salario_base": 900.0,
    }
    datos.update(cambios)
    return Empleado(**datos)


def _operaciones(entorno):
    """Operaciones registradas en el journal local"""
    sesion = entorno.new_session()
    try:
        return sesion.query(JournalOp).order_by(JournalOp.id).all()
    finally:
        entorno.close_session(sesion)


def test_alta_de_empleado_queda_en_el_journal(entorno_sync):
    sesion = entorno_sync.get_session()
    try:
        EmpleadoService(sesion).crear_empleado(_datos_empleado())
    finally:
        entorno_sync.close_session(sesion)

    operaciones = _operaciones(entorno_sync)
    assert len(operaciones) == 1
    operacion = operaciones[0]
    assert operacion.tabla == "empleados"
    assert operacion.operacion == "upsert"
    assert operacion.estado == PENDIENTE
    assert operacion.direccion == DIRECCION_SALIDA
    assert operacion.dispositivo
    assert operacion.fila_uuid


def test_la_operacion_lleva_los_campos_modificados(entorno_sync):
    sesion = entorno_sync.get_session()
    try:
        EmpleadoService(sesion).crear_empleado(_datos_empleado())
    finally:
        entorno_sync.close_session(sesion)

    payload = loads(_operaciones(entorno_sync)[0].payload)
    assert payload["cedula"] == "12345678"
    assert payload["cargo"] == "Docente de Matemáticas"
    assert payload["salario_base"] == 1500.0


def test_la_fila_adquiere_identidad_global(entorno_sync):
    sesion = entorno_sync.get_session()
    try:
        empleado = EmpleadoService(sesion).crear_empleado(_datos_empleado())
        empleado_id = empleado.id
    finally:
        entorno_sync.close_session(sesion)

    comprobacion = entorno_sync.new_session()
    try:
        fila = (
            comprobacion.query(SyncId)
            .filter(SyncId.tabla == "empleados", SyncId.id_local == empleado_id)
            .one()
        )
        assert len(fila.uuid) == 36

        version = (
            comprobacion.query(VersionFila)
            .filter(VersionFila.tabla == "empleados", VersionFila.fila_uuid == fila.uuid)
            .one()
        )
        assert version.ultimo_op_id
        assert version.dispositivo

        marcas = (
            comprobacion.query(CampoRemoto)
            .filter(CampoRemoto.tabla == "empleados", CampoRemoto.fila_uuid == fila.uuid)
            .all()
        )
        assert {marca.campo for marca in marcas} >= {"cedula", "cargo", "salario_base"}
    finally:
        entorno_sync.close_session(comprobacion)


def test_una_operacion_deshacida_no_se_anuncia(entorno_sync):
    """Atomicidad: lo que no se confirma tampoco se anuncia a la red"""
    sesion = entorno_sync.get_session()
    try:
        EmpleadoService(sesion).crear_empleado(_datos_empleado(cedula="40000000"))
        sesion.add(_empleado_minimo(cedula="50000000", nombres="Luis", apellidos="Pérez"))
        sesion.flush()
        sesion.rollback()
    finally:
        entorno_sync.close_session(sesion)

    operaciones = _operaciones(entorno_sync)
    assert len(operaciones) == 1
    assert loads(operaciones[0].payload)["cedula"] == "40000000"


def test_el_binario_viaja_como_hash(entorno_sync):
    sesion = entorno_sync.get_session()
    try:
        empleado = EmpleadoService(sesion).crear_empleado(_datos_empleado())
        sesion.add(
            Documento(
                empleado_id=empleado.id,
                tipo_documento="titulo",
                titulo="Título de licenciatura",
                nombre_archivo="titulo.pdf",
                ruta_archivo="documents/titulo.pdf",
                contenido_binario=b"contenido de prueba",
            )
        )
        sesion.commit()
    finally:
        entorno_sync.close_session(sesion)

    documentos = [op for op in _operaciones(entorno_sync) if op.tabla == "documentos"]
    assert len(documentos) == 1
    payload = loads(documentos[0].payload)
    # El contenido no viaja en la operación: se identifica por su hash
    assert payload["contenido_binario"] == {
        "__blob__": hash_bytes(b"contenido de prueba"),
        "tamano": len(b"contenido de prueba"),
    }
    # La clave foránea viaja como identidad global, no como id local
    assert isinstance(payload["empleado_id"], str)
    assert len(payload["empleado_id"]) == 36


def test_los_cambios_silenciosos_no_se_anuncian(entorno_sync):
    """Lo que llega de la red se aplica sin devolverse al resto (anti-eco)"""
    from sync_agent.captura import cambios_silenciosos

    sesion = entorno_sync.get_session()
    try:
        with cambios_silenciosos(sesion):
            EmpleadoService(sesion).crear_empleado(_datos_empleado())
    finally:
        entorno_sync.close_session(sesion)

    assert _operaciones(entorno_sync) == []


def test_las_preferencias_del_equipo_no_se_replican(entorno_sync):
    """Tema visual, respaldos y ajustes del agente son decisiones de cada puesto"""
    sesion = entorno_sync.get_session()
    try:
        # Una preferencia institucional (viaja) y dos del puesto (no viajan).
        # `nombre_institucion` ya viene sembrada, así que se modifica.
        sesion.query(Configuracion).filter(
            Configuracion.clave == "nombre_institucion"
        ).one().valor = "Colegio Central"
        for clave, valor, tipo in (
            ("apariencia_modo", "Dark", "string"),
            ("sync_habilitado", "true", "bool"),
        ):
            sesion.add(Configuracion(clave=clave, valor=valor, tipo_dato=tipo, categoria="general"))
        sesion.commit()
    finally:
        entorno_sync.close_session(sesion)

    operaciones = _operaciones(entorno_sync)
    # Solo la preferencia institucional deja operación: las del equipo no se
    # anuncian a la red (y la operación lleva únicamente el campo modificado,
    # que es `valor`, no la clave).
    assert len(operaciones) == 1
    assert operaciones[0].tabla == "configuraciones"
    assert "valor" in loads(operaciones[0].payload)
    claves = {loads(op.payload).get("clave") for op in operaciones}
    assert "apariencia_modo" not in claves
    assert "sync_habilitado" not in claves


def test_adoptar_existentes_es_idempotente(entorno_sync):
    """Los datos cargados antes de instalar el agente también deben viajar"""
    from sync_agent.captura import adoptar_existentes, cambios_silenciosos

    sesion = entorno_sync.new_session()
    try:
        with cambios_silenciosos(sesion):
            # Sin captura: simula datos que ya existían antes del agente
            sesion.add(_empleado_minimo())
            sesion.commit()
    finally:
        entorno_sync.close_session(sesion)

    assert _operaciones(entorno_sync) == []

    sesion = entorno_sync.new_session()
    try:
        adoptadas = adoptar_existentes(sesion)
        sesion.commit()
    finally:
        entorno_sync.close_session(sesion)
    assert adoptadas >= 1
    assert any(loads(op.payload).get("cedula") == "60000000" for op in _operaciones(entorno_sync))

    sesion = entorno_sync.new_session()
    try:
        assert adoptar_existentes(sesion) == 0
    finally:
        entorno_sync.close_session(sesion)
