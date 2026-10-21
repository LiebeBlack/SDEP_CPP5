"""
Pruebas del control de permisos del protocolo 2

La regla de oro: la interfaz móvil oculta lo que el rol no permite, pero la
**autoridad final es el servidor**. Aquí se comprueba que:

* cada endpoint exige sesión y aplica la misma matriz ``PermissionChecker``
  que usa la aplicación de escritorio (incluido el modo *fail-closed*);
* el ``push`` de una cuenta central sin permiso de escritura se rechaza, sin
  romper a los puestos antiguos que no envían usuario;
* el dashboard filtra los indicadores por el rol, como el panel del escritorio;
* los PDF/Excel se generan en el servidor y solo para quien puede verlos.
"""

import json
import threading
import urllib.error
import urllib.request

import pytest

from sync_agent.api_acciones import ErrorApi, exigir_permiso, serializar
from sync_agent.comun import dumps, nuevo_uuid
from sync_agent.sesiones import ErrorSesion, SesionValida
from sync_agent.servidor import (
    NucleoCentral,
    ServidorConfig,
    ServidorSync,
)

ROLES = ("admin", "manager", "user", "viewer")


# ----------------------------------------------------------------------
# Arreglos
# ----------------------------------------------------------------------
@pytest.fixture()
def central(tmp_path):
    """Nodo central con una cuenta por cada rol del escritorio"""
    config = ServidorConfig(
        url_db=f"sqlite:///{(tmp_path / 'central.db').as_posix()}",
        dir_blobs=tmp_path / "blobs",
        host="127.0.0.1",
        puerto=0,
    )
    nucleo = NucleoCentral(config)
    _crear_cuentas(nucleo)
    yield nucleo
    nucleo.cerrar()


def _crear_cuentas(nucleo):
    from src.services.auth_service import AuthService

    sesion = nucleo.SessionFactory()
    try:
        servicio = AuthService(sesion)
        for usuario, rol in (
            ("admin", "admin"),
            ("gestora", "manager"),
            ("docente", "user"),
            ("lector", "viewer"),
        ):
            if servicio.usuario_por_username(usuario) is None:
                servicio.crear_usuario(usuario, "Clave1234", rol, rol, debe_cambiar_password=False)
    finally:
        sesion.close()


def _sesion(rol: str) -> SesionValida:
    """Sesión sintética con el rol indicado (la validación se prueba aparte)"""
    return SesionValida(
        token_hash="x" * 64,
        username=f"usuario-{rol}",
        nombre_completo=None,
        rol=rol,
        dispositivo_id="equipo-test",
        expira_en=None,
    )


def _login(central, username, password="Clave1234"):
    return central.api.login({"username": username, "password": password}, "equipo-test")


def _payload_empleado(**cambios):
    datos = {
        "cedula": "12345678",
        "nombres": "Ana",
        "apellidos": "Gómez",
        "tipo_empleado": "docente",
        "cargo": "Docente",
        "departamento": "Docencia",
        "salario_base": 1200.0,
        "activo": 1,
    }
    datos.update(cambios)
    return dumps(datos)


def _operacion(tabla="empleados", payload=None, usuario=None):
    operacion = {
        "op_id": nuevo_uuid(),
        "tabla": tabla,
        "fila_uuid": nuevo_uuid(),
        "operacion": "upsert",
        "payload": payload if payload is not None else _payload_empleado(),
        "dispositivo": "equipo-test",
        "creado_en": "2026-01-01T12:00:00",
    }
    if usuario is not None:
        operacion["usuario"] = usuario
    return operacion


def _emparejar(central, nombre="Teléfono"):
    dispositivo_id, token = central.crear_dispositivo(nombre)
    return central.autenticar(dispositivo_id, token)


# ----------------------------------------------------------------------
# Matriz de permisos (espejo puro de PermissionChecker)
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "rol,permiso,modulo,esperado",
    [
        # admin: todo
        ("admin", "create", "nomina", True),
        ("admin", "config", "configuracion", True),
        ("admin", "delete", "empleados", True),
        ("admin", "report", "contratos", True),
        # manager: crea, edita, borra y reporta; sin configuración
        ("manager", "create", "nomina", True),
        ("manager", "update", "contratos", True),
        ("manager", "report", "incidencias", True),
        ("manager", "config", "configuracion", False),
        # user: solo lectura y update_own; sin nómina ni contratos
        ("user", "read", "notas", True),
        ("user", "read", "empleados", True),
        ("user", "create", "empleados", False),
        ("user", "read", "nomina", False),
        ("user", "read", "contratos", False),
        # viewer: solo lectura
        ("viewer", "read", "documentos", True),
        ("viewer", "create", "documentos", False),
        ("viewer", "delete", "incidencias", False),
        ("viewer", "read", "configuracion", False),
    ],
)
def test_matriz_de_permisos_igual_al_escritorio(rol, permiso, modulo, esperado):
    """Cada combinación se evalúa con PermissionChecker, sin reimplementar nada"""
    if esperado:
        exigir_permiso(_sesion(rol), permiso, modulo)  # no debe lanzar
    else:
        with pytest.raises(ErrorApi) as error:
            exigir_permiso(_sesion(rol), permiso, modulo)
        assert error.value.codigo == 403


def test_modulo_desconocido_queda_denegado_para_todos(rol="viewer"):
    """Fail-closed: un módulo no declarado en MODULE_ACCESS no se abre jamás"""
    for personaje in ROLES:
        with pytest.raises(ErrorApi) as error:
            exigir_permiso(_sesion(personaje), "read", "modulo_inexistente")
        assert error.value.codigo == 403


# ----------------------------------------------------------------------
# Endpoints de sesión y dashboard
# ----------------------------------------------------------------------
def test_dashboard_filtra_indicadores_por_rol(central):
    # Cada bloque exige acceso al módulo según MODULE_ACCESS del escritorio:
    # admin y manager ven todo; user no ve contratos ni nómina; viewer solo
    # empleados, documentos y el subdominio académico.
    esperado_por_rol = {
        "admin": {"empleados", "documentos", "incidencias", "contratos", "nomina", "academico"},
        "manager": {"empleados", "documentos", "incidencias", "contratos", "nomina", "academico"},
        "user": {"empleados", "documentos", "incidencias", "academico"},
        "viewer": {"empleados", "documentos", "academico"},
    }
    for rol, esperados in esperado_por_rol.items():
        sesion = _sesion(rol)
        panel = central.api.dashboard(sesion)
        assert set(panel["indicadores"]) == esperados, f"rol {rol}"
        assert panel["rol"] == rol


def test_administracion_de_usuarios_exige_rol_admin(central):
    sesion_admin = _login(central, "admin")
    sesion_gestora = _login(central, "gestora")

    listado = central.api.listar_usuarios(central.api.validar(sesion_admin["sesion_token"]))
    assert {u["username"] for u in listado["usuarios"]} >= {"admin", "lector"}
    # Nunca se filtra el hash de la contraseña por la API
    assert all("password_hash" not in u for u in listado["usuarios"])

    with pytest.raises(ErrorApi) as error:
        central.api.listar_usuarios(central.api.validar(sesion_gestora["sesion_token"]))
    assert error.value.codigo == 403


def test_auditoria_solo_admin(central):
    sesion = _login(central, "admin")
    with pytest.raises(ErrorApi):
        central.api.auditoria(central.api.validar(_login(central, "lector")["sesion_token"]))
    panel = central.api.auditoria(central.api.validar(sesion["sesion_token"]), limite=10)
    assert "eventos" in panel


def test_acciones_exigen_sesion_valida(central):
    """Sin cabecera X-Sesion (o con un token inventado) nada se ejecuta"""
    with pytest.raises(ErrorSesion):
        central.api.validar(None)
    with pytest.raises(ErrorSesion):
        central.api.validar("token-inventado")


def test_generar_nomina_rechaza_a_solo_lectura(central):
    """La denegación ocurre ANTES de invocar el motor de nómina"""
    sesion = central.api.validar(_login(central, "lector")["sesion_token"])
    with pytest.raises(ErrorApi) as error:
        central.api.generar_nomina_periodo(
            sesion, {"periodo_inicio": "2026-01-01", "periodo_fin": "2026-01-31"}
        )
    assert error.value.codigo == 403


def test_aprobar_incidencia_rechaza_a_roles_sin_modulo(central):
    sesion_docente = central.api.validar(_login(central, "docente")["sesion_token"])
    # El rol user ni accede al módulo incidencias
    with pytest.raises(ErrorApi) as error:
        central.api.aprobar_incidencia(sesion_docente, 1, {})
    assert error.value.codigo == 403

    sesion_lector = central.api.validar(_login(central, "lector")["sesion_token"])
    # El rol viewer accede al módulo (solo lectura) pero no tiene permiso update
    with pytest.raises(ErrorApi) as error:
        central.api.aprobar_incidencia(sesion_lector, 1, {})
    assert error.value.codigo == 403


def test_periodo_reabrir_solo_config(central):
    """Reabrir periodos exige 'config' → solo administrador"""
    for usuario in ("gestora", "docente", "lector"):
        sesion = central.api.validar(_login(central, usuario)["sesion_token"])
        with pytest.raises(ErrorApi) as error:
            central.api.reabrir_periodo(sesion, 1, {})
        assert error.value.codigo == 403


# ----------------------------------------------------------------------
# Push protegido por permisos (autoridad final del servidor)
# ----------------------------------------------------------------------
def test_push_rechaza_a_cuentas_centrales_sin_permiso(central):
    """Un viewer central no puede meter empleados por la puerta de sincronización"""
    dispositivo = _emparejar(central)
    operacion = _operacion(usuario="lector")

    respuesta = central.push(dispositivo, {"ops": [operacion]})

    assert respuesta["aplicadas"] == []
    assert respuesta["rechazadas"][0]["op_id"] == operacion["op_id"]
    assert "permiso" in respuesta["rechazadas"][0]["motivo"]


def test_push_rechaza_al_manager_en_nomina(central):
    dispositivo = _emparejar(central)
    operacion = _operacion(
        tabla="pagos",
        payload=dumps(
            {
                "empleado_id": 1,
                "tipo_pago": "salario_base",
                "periodo_inicio": "2026-01-01",
                "periodo_fin": "2026-01-31",
                "monto_bruto": 100.0,
                "monto_neto": 90.0,
                "salario_base": 100.0,
            }
        ),
        usuario="gestora",
    )

    # manager sí tiene update en nómina: la operación pasa el control de permisos
    # (puede fallar después por otros motivos de datos, nunca por permisos)
    respuesta = central.push(dispositivo, {"ops": [operacion]})
    motivos = [r["motivo"] for r in respuesta["rechazadas"]]
    assert not any(m.startswith("permiso") or m.startswith("modulo") for m in motivos)

    # viewer no
    negada = _operacion(
        tabla="pagos",
        payload=dumps(
            {
                "empleado_id": 2,
                "tipo_pago": "salario_base",
                "periodo_inicio": "2026-01-01",
                "periodo_fin": "2026-01-31",
                "monto_bruto": 100.0,
                "monto_neto": 90.0,
                "salario_base": 100.0,
            }
        ),
        usuario="lector",
    )
    respuesta = central.push(dispositivo, {"ops": [negada]})
    assert respuesta["rechazadas"][0]["motivo"].startswith("permiso")


def test_push_sin_usuario_sigue_funcionando(central):
    """Retrocompatibilidad: los puestos escritorio no envían usuario"""
    dispositivo = _emparejar(central)
    operacion = _operacion()  # sin clave "usuario"

    respuesta = central.push(dispositivo, {"ops": [operacion]})

    assert respuesta["aplicadas"] == [operacion["op_id"]]


def test_push_de_cuenta_local_de_otro_puesto_no_se_bloquea(central):
    """'usuarios' no se replica: una cuenta local desconocida aquí no se juzga"""
    dispositivo = _emparejar(central)
    operacion = _operacion(usuario="cuenta-local-otro-puesto")

    respuesta = central.push(dispositivo, {"ops": [operacion]})

    assert respuesta["aplicadas"] == [operacion["op_id"]]


def test_push_del_admin_siempre_pasa(central):
    dispositivo = _emparejar(central)
    operacion = _operacion(usuario="admin")

    respuesta = central.push(dispositivo, {"ops": [operacion]})

    assert respuesta["aplicadas"] == [operacion["op_id"]]


def test_registros_moviles_no_exige_mapa_de_modulos(central):
    """La captura de campo del móvil autentica por dispositivo y sesión propia"""
    dispositivo = _emparejar(central)
    operacion = _operacion(
        tabla="registros_moviles",
        payload=dumps(
            {
                "uuid_movil": nuevo_uuid(),
                "titulo": "Visita 4to B",
                "categoria": "general",
                "creado_en": "2026-01-01T12:00:00",
                "actualizado_en": "2026-01-01T12:00:00",
                "activo": 1,
            }
        ),
        usuario="docente",
    )

    respuesta = central.push(dispositivo, {"ops": [operacion]})

    assert respuesta["aplicadas"] == [operacion["op_id"]]


# ----------------------------------------------------------------------
# Serialización
# ----------------------------------------------------------------------
def test_serializar_no_escapa_modelos_ni_decimales():
    from datetime import date
    from decimal import Decimal

    datos = serializar(
        {
            "monto": Decimal("12.50"),
            "fecha": date(2026, 3, 1),
            "binario": b"no viaja",
            "lista": [Decimal("1.00"), None, "texto"],
        }
    )
    assert datos == {
        "monto": 12.5,
        "fecha": "2026-03-01",
        "binario": None,
        "lista": [1.0, None, "texto"],
    }
    # Debe poder serializarse a JSON sin fallbacks
    json.dumps(datos)


# ----------------------------------------------------------------------
# Transporte HTTP: login + consultas con sesión
# ----------------------------------------------------------------------
class ServicioEnMarcha:
    """Servicio HTTP del nodo central escuchando en un puerto libre"""

    def __init__(self, config: ServidorConfig):
        self.servidor = ServidorSync(config)
        self.puerto = self.servidor.server_address[1]
        self._hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)

    def __enter__(self):
        self._hilo.start()
        return self

    def __exit__(self, *_excepcion):
        self.servidor.shutdown()
        self.servidor.server_close()
        self._hilo.join(timeout=5)
        self.servidor.nucleo.cerrar()


@pytest.fixture()
def servicio(tmp_path, db_config):
    """Nodo central hablado por HTTP con la base del escritorio inicializada"""
    # ``db_config`` (sesión) crea las tablas de la base de prueba: los
    # generadores de PDF leen la configuración institucional de ahí.
    config = ServidorConfig(
        url_db=f"sqlite:///{(tmp_path / 'central.db').as_posix()}",
        dir_blobs=tmp_path / "blobs",
        host="127.0.0.1",
        puerto=0,
    )
    with ServicioEnMarcha(config) as en_marcha:
        _crear_cuentas(en_marcha.servidor.nucleo)
        yield en_marcha


def _pedir(base, ruta, metodo="GET", cuerpo=None, sesion=None, equipo=None, token=None):
    """Petición HTTP cruda; devuelve (código, dict o bytes)"""
    data = None
    cabeceras = {"Accept": "application/json"}
    if cuerpo is not None:
        data = json.dumps(cuerpo).encode("utf-8")
        cabeceras["Content-Type"] = "application/json"
    if sesion:
        cabeceras["X-Sesion"] = sesion
    if equipo:
        cabeceras["X-Dispositivo"] = equipo
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    peticion = urllib.request.Request(base + ruta, data=data, headers=cabeceras, method=metodo)
    try:
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            crudo = respuesta.read()
            codigo = respuesta.status
    except urllib.error.HTTPError as error:
        crudo = error.read()
        codigo = error.code
    try:
        return codigo, json.loads(crudo.decode("utf-8"))
    except ValueError:
        return codigo, crudo


def test_login_por_http_devuelve_sesion(servicio):
    base = f"http://127.0.0.1:{servicio.puerto}"
    equipo_id, token_equipo = servicio.servidor.nucleo.crear_dispositivo("Teléfono")

    codigo, datos = _pedir(
        base,
        "/api/v1/auth/login",
        "POST",
        {"username": "admin", "password": "Clave1234"},
        equipo="tel",
    )
    assert codigo == 200
    assert datos["rol"] == "admin"
    token = datos["sesion_token"]

    codigo, info = _pedir(base, "/api/v1/auth/sesion", sesion=token)
    assert codigo == 200
    assert info["username"] == "admin"

    # Las consultas exigen doble credencial: equipo emparejado + sesión
    codigo, panel = _pedir(
        base, "/api/v1/consultas/dashboard", sesion=token, equipo=equipo_id, token=token_equipo
    )
    assert codigo == 200
    assert panel["indicadores"]

    codigo, error = _pedir(base, "/api/v1/auth/logout", "POST", sesion=token)
    assert codigo == 200

    codigo, _ = _pedir(
        base, "/api/v1/consultas/dashboard", sesion=token, equipo=equipo_id, token=token_equipo
    )
    assert codigo == 401


def test_login_por_http_contrasena_mala(servicio):
    base = f"http://127.0.0.1:{servicio.puerto}"
    codigo, datos = _pedir(
        base, "/api/v1/auth/login", "POST", {"username": "admin", "password": "mala"}, equipo="tel"
    )
    assert codigo == 401
    assert "error" in datos


def test_endpoints_sin_sesion_responden_401(servicio):
    base = f"http://127.0.0.1:{servicio.puerto}"
    for ruta in (
        "/api/v1/consultas/dashboard",
        "/api/v1/admin/usuarios",
        "/api/v1/acciones/nomina/generar",
    ):
        codigo, _ = _pedir(base, ruta, "POST" if "acciones" in ruta else "GET", {})
        assert codigo == 401, ruta


def test_ping_anuncia_protocolo_2_y_v1_sigue_viva(servicio):
    base = f"http://127.0.0.1:{servicio.puerto}"

    codigo, ping = _pedir(base, "/api/v1/ping")
    assert codigo == 200
    assert ping["version_protocolo"] == "2"
    assert "auth" in ping["acciones"]
    # El contrato v1 que usan los puestos de escritorio no cambió
    assert "registros_moviles" in ping["tablas"]
    assert set(("empleados", "documentos", "pagos", "contratos")) <= set(ping["tablas"])

    # push v1 sin usuario y con token de equipo: se acepta igual que siempre
    equipo_id, token = servicio.servidor.nucleo.crear_dispositivo("Escritorio")
    codigo, respuesta = _pedir(
        base,
        "/api/v1/push",
        "POST",
        {"dispositivo": equipo_id, "ops": [_operacion()]},
        equipo=equipo_id,
        token=token,
    )
    assert codigo == 200
    assert respuesta["aplicadas"]


def test_admin_por_http_exige_rol(servicio):
    base = f"http://127.0.0.1:{servicio.puerto}"
    equipo_id, token_equipo = servicio.servidor.nucleo.crear_dispositivo("Teléfono")
    _, admin = _pedir(
        base, "/api/v1/auth/login", "POST", {"username": "admin", "password": "Clave1234"}
    )
    _, lector = _pedir(
        base, "/api/v1/auth/login", "POST", {"username": "lector", "password": "Clave1234"}
    )

    codigo, listado = _pedir(
        base,
        "/api/v1/admin/usuarios",
        sesion=admin["sesion_token"],
        equipo=equipo_id,
        token=token_equipo,
    )
    assert codigo == 200
    assert listado["usuarios"]

    codigo, _ = _pedir(
        base,
        "/api/v1/admin/usuarios",
        sesion=lector["sesion_token"],
        equipo=equipo_id,
        token=token_equipo,
    )
    assert codigo == 403


def test_archivo_generado_se_entrega_por_blob(servicio):
    """El PDF del escritorio se genera en el servidor y baja por el canal v1"""
    base = f"http://127.0.0.1:{servicio.puerto}"
    _, admin = _pedir(
        base, "/api/v1/auth/login", "POST", {"username": "admin", "password": "Clave1234"}
    )
    equipo_id, token = servicio.servidor.nucleo.crear_dispositivo("Teléfono")

    # Un empleado real para la constancia
    nucleo = servicio.servidor.nucleo
    sesion = nucleo.SessionFactory()
    try:
        from src.services.empleado_service import EmpleadoService

        empleado = EmpleadoService(sesion).crear_empleado(
            {
                "nombres": "Ana",
                "apellidos": "Gómez",
                "cedula": "87654321",
                "tipo_empleado": "docente",
                "cargo": "Docente",
                "departamento": "Docencia",
                "salario_base": 1200.0,
            }
        )
        empleado_id = empleado.id
    finally:
        sesion.close()

    codigo, archivo = _pedir(
        base,
        "/api/v1/archivos/pdf/constancia_trabajo",
        "POST",
        {"empleado_id": empleado_id},
        sesion=admin["sesion_token"],
        equipo=equipo_id,
        token=token,
    )
    assert codigo == 200, archivo
    assert len(archivo["hash"]) == 64
    assert archivo["descarga"].startswith("/api/v1/blob/")

    codigo, contenido = _pedir(base, archivo["descarga"], equipo=equipo_id, token=token)
    assert codigo == 200
    assert contenido.startswith(b"%PDF")

    # Un viewer no puede pedirlo
    _, lector = _pedir(
        base, "/api/v1/auth/login", "POST", {"username": "lector", "password": "Clave1234"}
    )
    codigo, _ = _pedir(
        base,
        "/api/v1/archivos/pdf/constancia_trabajo",
        "POST",
        {"empleado_id": empleado_id},
        sesion=lector["sesion_token"],
        equipo=equipo_id,
        token=token,
    )
    assert codigo == 403
