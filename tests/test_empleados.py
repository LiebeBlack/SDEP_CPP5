"""Pruebas del servicio de empleados"""

from datetime import date

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


def test_busqueda_insensible_a_mayusculas_y_tildes(session):
    servicio = EmpleadoService(session)
    servicio.crear_empleado(_datos_empleado(cedula="7770001", apellidos="Gómez"))
    # Sin tilde, en minúsculas: debe encontrar a "Gómez"
    assert len(servicio.buscar_empleados("gomez")) >= 1
    # Mayúsculas sin tilde
    assert len(servicio.buscar_empleados("GOMEZ")) >= 1
    # Nombre parcial sin tilde
    assert len(servicio.buscar_empleados("ana")) >= 1


def test_busqueda_solo_empleados_activos(session):
    servicio = EmpleadoService(session)
    emp = servicio.crear_empleado(_datos_empleado(cedula="7770002", nombres="Carlos"))
    servicio.eliminar_empleado(emp.id)
    session.expire_all()
    assert servicio.buscar_empleados("Carlos") == []


def test_busqueda_combinada_con_tipo(session):
    servicio = EmpleadoService(session)
    servicio.crear_empleado(_datos_empleado(cedula="7770003", nombres="Pedro"))
    servicio.crear_empleado(_datos_empleado(
        cedula="7770004", nombres="Pedro",
        tipo_empleado=TipoEmpleado.ADMINISTRATIVO.value,
        apellidos="Ruiz",
    ))
    # Solo docentes llamados Pedro
    docentes = servicio.listar_filtrados({"busqueda": "Pedro", "tipo": "docente", "activo": 1})
    assert len(docentes) == 1
    assert docentes[0].apellidos == "Gómez"
    # Todos los Pedro (dos tipos)
    todos = servicio.listar_filtrados({"busqueda": "Pedro", "activo": 1})
    assert len(todos) == 2


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
    from src.models import Empleado
    hoy = date.today()
    try:
        fecha_contrato = date(hoy.year - 5, hoy.month, hoy.day)
    except ValueError:  # 29 de febrero sin año bisiesto a 5 años
        fecha_contrato = date(hoy.year - 5, hoy.month, 28)
    emp = Empleado(
        nombres="X", apellidos="Y", cedula="0001",
        fecha_nacimiento=date(1980, 1, 1),
        tipo_empleado=TipoEmpleado.DOCENTE.value,
        cargo="Docente", departamento="Ciencias",
        salario_base=100.0,
        fecha_contratacion=fecha_contrato,
    )
    assert emp.edad == hoy.year - 1980  # cumpleaños en enero ya transcurrido
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


def test_campos_opcionales_adicionales(session):
    """Los campos opcionales (bancarios, salud, familia, académicos) se persisten"""
    servicio = EmpleadoService(session)
    datos = _datos_empleado(cedula="5550001", **{
        "institucion_bancaria": "Banco Nacional",
        "numero_cuenta": "123456789",
        "tipo_cuenta": "ahorro",
        "carnet_discapacidad": "DISC-001",
        "enfermedades_preexistentes": "Asma",
        "alergias_medicamentosas": "Penicilina",
        "alergias_alimentarias": "Maní",
        "tipo_contratacion": "indefinido",
        "titulo_secundaria": "Bachiller en Ciencias",
        "hijos": "María (10 años, C.I. 12345678)",
    })
    empleado = servicio.crear_empleado(datos)
    session.expire_all()
    emp = servicio.obtener_empleado(empleado.id)
    assert emp.institucion_bancaria == "Banco Nacional"
    assert emp.numero_cuenta == "123456789"
    assert emp.tipo_cuenta == "ahorro"
    assert emp.carnet_discapacidad == "DISC-001"
    assert emp.enfermedades_preexistentes == "Asma"
    assert emp.alergias_medicamentosas == "Penicilina"
    assert emp.alergias_alimentarias == "Maní"
    assert emp.tipo_contratacion == "indefinido"
    assert emp.titulo_secundaria == "Bachiller en Ciencias"
    assert "María" in emp.hijos


def test_campos_opcionales_vacios_son_none(session):
    """Los campos opcionales vacíos se guardan como NULL"""
    servicio = EmpleadoService(session)
    datos = _datos_empleado(cedula="5550002")
    datos.update({
        "institucion_bancaria": "",
        "numero_cuenta": "",
        "tipo_contratacion": "",
        "hijos": "",
    })
    empleado = servicio.crear_empleado(datos)
    session.expire_all()
    emp = servicio.obtener_empleado(empleado.id)
    assert emp.institucion_bancaria is None
    assert emp.numero_cuenta is None
    assert emp.tipo_contratacion is None
    assert emp.hijos is None


def test_actualizar_campos_opcionales(session):
    """La actualización persiste los campos opcionales nuevos"""
    servicio = EmpleadoService(session)
    empleado = servicio.crear_empleado(_datos_empleado(cedula="5550003"))
    servicio.actualizar_empleado(empleado.id, {
        "institucion_bancaria": "Banco del Pacífico",
        "tipo_contratacion": "fijo",
    })
    session.expire_all()
    emp = servicio.obtener_empleado(empleado.id)
    assert emp.institucion_bancaria == "Banco del Pacífico"
    assert emp.tipo_contratacion == "fijo"
    assert emp.numero_cuenta is None
