"""Pruebas del servicio de empleados"""

from datetime import date, timedelta

import pytest

from src.services.empleado_service import EmpleadoService
from src.models import TipoEmpleado


def _datos_empleado(cedula="12345678", **cambios):
    datos = {
        "nombres": "Ana",
        "apellidos": "Gómez",
        "cedula": cedula,
        "fecha_nacimiento": date(1990, 5, 12),
        "genero": "femenino",
        "estado_civil": "soltero",
        "tipo_empleado": TipoEmpleado.DOCENTE.value,
        "cargo": "Docente de Matemáticas",
        "departamento": "Matemáticas",
        "fecha_contratacion": date(2020, 1, 15),
        "salario_base": 1500.0,
        "email": "ana.gomez@example.com",
        "telefono": "555-0100",
    }
    datos.update(cambios)
    return datos


def test_crear_empleado(session):
    servicio = EmpleadoService(session)
    empleado = servicio.crear_empleado(_datos_empleado())
    assert empleado.id is not None
    assert empleado.nombre_completo == "Ana Gómez"
    assert servicio.obtener_empleado(empleado.id) is not None


def test_cedula_duplicada_rechazada(session):
    servicio = EmpleadoService(session)
    servicio.crear_empleado(_datos_empleado())
    with pytest.raises(ValueError):
        servicio.crear_empleado(_datos_empleado())


def test_salario_requerido(session):
    servicio = EmpleadoService(session)
    datos = _datos_empleado(cedula="87654321")
    datos["salario_base"] = ""
    with pytest.raises(ValueError):
        servicio.crear_empleado(datos)


def test_actualizar_empleado(session):
    servicio = EmpleadoService(session)
    empleado = servicio.crear_empleado(_datos_empleado())
    actualizado = servicio.actualizar_empleado(empleado.id, {"cargo": "Director Académico"})
    assert actualizado.cargo == "Director Académico"


def test_cedula_en_uso_al_actualizar(session):
    servicio = EmpleadoService(session)
    servicio.crear_empleado(_datos_empleado())
    otro = servicio.crear_empleado(_datos_empleado(cedula="99999999"))
    with pytest.raises(ValueError):
        servicio.actualizar_empleado(otro.id, {"cedula": "12345678"})


def test_eliminacion_logica(session):
    servicio = EmpleadoService(session)
    empleado = servicio.crear_empleado(_datos_empleado())
    assert servicio.eliminar_empleado(empleado.id)
    session.expire_all()
    empleado = servicio.obtener_empleado(empleado.id)
    assert empleado.activo == 0
    assert empleado.id not in [e.id for e in servicio.listar_empleados_activos()]


def test_busqueda_por_nombre_y_cedula(session):
    servicio = EmpleadoService(session)
    servicio.crear_empleado(_datos_empleado())
    assert len(servicio.buscar_empleados("Ana")) >= 1
    assert len(servicio.buscar_empleados("12345678")) >= 1
    assert len(servicio.buscar_empleados("Inexistente")) == 0


def test_estadisticas(session):
    servicio = EmpleadoService(session)
    servicio.crear_empleado(_datos_empleado())
    servicio.crear_empleado(_datos_empleado(
        cedula="11111111",
        tipo_empleado=TipoEmpleado.ADMINISTRATIVO.value,
        nombres="Luis",
        apellidos="Pérez",
    ))
    stats = servicio.obtener_estadisticas()
    assert stats["total"] == 2
    assert stats["activos"] == 2
    assert stats["por_tipo"]["docente"] == 1
    assert stats["por_tipo"]["administrativo"] == 1


def test_edad_y_antiguedad():
    servicio = None  # solo propiedades del modelo
    from src.models import Empleado
    emp = Empleado(
        nombres="X", apellidos="Y", cedula="0001",
        fecha_nacimiento=date(1980, 1, 1),
        tipo_empleado=TipoEmpleado.DOCENTE.value,
        cargo="Docente", departamento="Ciencias",
        salario_base=100.0,
        fecha_contratacion=date.today() - timedelta(days=365 * 5),
    )
    assert emp.edad == date.today().year - 1980  # cumpleaños en enero ya transcurrido
    assert emp.antiguedad_anos == 5


def test_actualizar_foto(session, storage):
    servicio = EmpleadoService(session)
    empleado = servicio.crear_empleado(_datos_empleado())
    ruta = str(storage / "foto.jpg")
    with open(ruta, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
    assert servicio.actualizar_foto(empleado.id, ruta)
    session.expire_all()
    assert servicio.obtener_empleado(empleado.id).foto_ruta == ruta
