"""
Pruebas del nodo central de sincronización

El nodo central es el **único escritor** de la base compartida: los puestos
envían sus operaciones y descargan las ajenas, nunca escriben directamente.
Aquí se verifica la lógica sin abrir puertos (``NucleoCentral``) y también el
transporte HTTP real sobre ``127.0.0.1`` con el puerto que asigne el sistema.
"""

import threading

import pytest

from sync_agent.comun import dumps, hash_bytes, nuevo_uuid
from sync_agent.servidor import (
    ErrorPeticion,
    NucleoCentral,
    ServidorConfig,
    ServidorSync,
)


@pytest.fixture()
def central(tmp_path):
    """Nodo central aislado en un directorio temporal"""
    config = ServidorConfig(
        url_db=f"sqlite:///{(tmp_path / 'central.db').as_posix()}",
        dir_blobs=tmp_path / "blobs",
        host="127.0.0.1",
        puerto=0,
        peticiones_por_minuto=120,
    )
    nucleo = NucleoCentral(config)
    yield nucleo
    nucleo.cerrar()


def _emparejar(nucleo, nombre="Secretaría"):
    """Da de alta un puesto y devuelve (identificador, token, dispositivo ORM)"""
    dispositivo_id, token = nucleo.crear_dispositivo(nombre)
    return dispositivo_id, token, nucleo.autenticar(dispositivo_id, token)


def _payload_empleado(**cambios):
    """
    Payload completo de un alta, tal como lo produce la captura real

    En un alta, la captura del ORM envía **todas** las columnas no nulas: una
    operación tiene que bastar por sí sola para recrear la fila en otro puesto.
    """
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


def _operacion(tabla="empleados", fila_uuid=None, payload=None, creado_en=None, **cambios):
    """Operación del protocolo lista para enviar"""
    operacion = {
        "op_id": nuevo_uuid(),
        "tabla": tabla,
        "fila_uuid": fila_uuid or nuevo_uuid(),
        "operacion": "upsert",
        "payload": payload if payload is not None else _payload_empleado(),
        "base_op_id": None,
        "dispositivo": "",
        "usuario": "prueba",
        "creado_en": creado_en or "2026-01-01T12:00:00",
    }
    operacion.update(cambios)
    return operacion


# ----------------------------------------------------------------------
# Servicio y credenciales
# ----------------------------------------------------------------------
def test_ping_responde_la_hora_y_las_tablas(central):
    datos = central.ping()
    assert datos["version_protocolo"]
    assert datos["hora"]
    assert "empleados" in datos["tablas"]


def test_equipo_sin_alta_no_puede_autenticarse(central):
    with pytest.raises(ErrorPeticion) as error:
        central.autenticar(nuevo_uuid(), "token-inventado")
    assert error.value.codigo == 401


def test_faltan_las_credenciales(central):
    with pytest.raises(ErrorPeticion) as error:
        central.autenticar(None, None)
    assert error.value.codigo == 401


def test_el_token_incorrecto_se_rechaza(central):
    dispositivo_id, _token, _ = _emparejar(central)
    with pytest.raises(ErrorPeticion) as error:
        central.autenticar(dispositivo_id, "otro-token")
    assert error.value.codigo == 401


def test_el_token_solo_se_entrega_una_vez(central):
    dispositivo_id, token, _ = _emparejar(central, "Rectoría")
    assert token
    listado = central.listar_dispositivos()
    registrado = next(fila for fila in listado if fila["dispositivo_id"] == dispositivo_id)
    assert registrado["nombre"] == "Rectoría"
    assert registrado["activo"] is True
    assert "token" not in registrado
    assert "token_hash" not in registrado


def test_un_equipo_revocado_pierde_el_acceso(central):
    dispositivo_id, token, _ = _emparejar(central)
    assert central.revocar_dispositivo(dispositivo_id) is True
    with pytest.raises(ErrorPeticion) as error:
        central.autenticar(dispositivo_id, token)
    assert error.value.codigo == 401


def test_revocar_un_equipo_inexistente_no_finge_exito(central):
    assert central.revocar_dispositivo(nuevo_uuid()) is False


# ----------------------------------------------------------------------
# Intercambio de operaciones
# ----------------------------------------------------------------------
def test_push_registra_y_pull_entrega_a_los_demas(central):
    id_a, token_a, dispositivo_a = _emparejar(central, "Puesto A")
    id_b, token_b, dispositivo_b = _emparejar(central, "Puesto B")

    operacion = _operacion(payload=_payload_empleado(cargo="Director"))
    resultado = central.push(dispositivo_a, {"ops": [operacion]})
    assert resultado["aplicadas"] == [operacion["op_id"]]
    assert resultado["cursor"] >= 1

    # El propio puesto no recibe de vuelta lo que envió
    propio = central.pull(dispositivo_a, 0, 100)
    assert propio["ops"] == []

    ajeno = central.pull(dispositivo_b, 0, 100)
    assert [op["op_id"] for op in ajeno["ops"]] == [operacion["op_id"]]
    assert ajeno["ops"][0]["fila_uuid"] == operacion["fila_uuid"]
    assert id_a != id_b


def test_reenviar_el_mismo_lote_es_idempotente(central):
    _, _, dispositivo = _emparejar(central, "Puesto A")
    operacion = _operacion()

    primero = central.push(dispositivo, {"ops": [operacion]})
    segundo = central.push(dispositivo, {"ops": [operacion]})

    assert primero["aplicadas"] == segundo["aplicadas"] == [operacion["op_id"]]
    # El log autoritativo no guarda la operación dos veces
    assert central.cursor_actual() == primero["cursor"] == segundo["cursor"]


def test_lote_demasiado_grande_se_rechaza(central):
    _, _, dispositivo = _emparejar(central)
    central.config.max_ops_por_lote = 1
    with pytest.raises(ErrorPeticion) as error:
        central.push(dispositivo, {"ops": [_operacion(), _operacion()]})
    assert error.value.codigo == 413


def test_el_lote_debe_ser_una_lista(central):
    _, _, dispositivo = _emparejar(central)
    with pytest.raises(ErrorPeticion):
        central.push(dispositivo, {"ops": "no soy una lista"})


def test_el_limite_de_peticiones_frena_el_abuso(central):
    _, _, dispositivo = _emparejar(central)
    central.config.peticiones_por_minuto = 3
    for _ in range(3):
        central.limitar_tasa(dispositivo.dispositivo_id)
    with pytest.raises(ErrorPeticion) as error:
        central.limitar_tasa(dispositivo.dispositivo_id)
    assert error.value.codigo == 429


def test_las_colisiones_quedan_en_la_bandeja_del_servidor(central):
    _, _, dispositivo_a = _emparejar(central, "Puesto A")
    _, _, dispositivo_b = _emparejar(central, "Puesto B")
    fila_uuid = nuevo_uuid()

    reciente = _operacion(
        fila_uuid=fila_uuid,
        payload=_payload_empleado(cargo="Director"),
        creado_en="2026-01-01T12:00:00",
        dispositivo=dispositivo_a.dispositivo_id,
    )
    antigua = _operacion(
        fila_uuid=fila_uuid,
        payload=dumps({"cargo": "Secretaria"}),
        creado_en="2026-01-01T11:00:00",
        dispositivo=dispositivo_b.dispositivo_id,
    )
    central.push(dispositivo_a, {"ops": [reciente]})
    central.push(dispositivo_b, {"ops": [antigua]})

    conflictos = central.conflictos()
    assert any(conflicto["campo"] == "cargo" for conflicto in conflictos)
    assert any(conflicto["ganador"] == "local" for conflicto in conflictos)


def test_el_estado_del_nodo_resume_su_actividad(central):
    _, _, dispositivo = _emparejar(central)
    central.push(dispositivo, {"ops": [_operacion()]})
    estado = central.estado()
    assert estado["operaciones"] >= 1
    assert estado["dispositivos"] == 1
    assert estado["activos"] == 1


def test_purgar_historial_retira_lo_antiguo(central):
    _, _, dispositivo = _emparejar(central)
    central.push(dispositivo, {"ops": [_operacion()]})
    # Nada tiene más de un día: la purga no debe llevarse lo reciente
    assert central.purgar_historial(dias=365) == 0
    assert central.purgar_historial(dias=1) == 0
    assert central.cursor_actual() >= 1


# ----------------------------------------------------------------------
# Binarios
# ----------------------------------------------------------------------
def test_los_blobs_se_guardan_deduplicados(central):
    _, _, dispositivo = _emparejar(central)
    contenido = b"contenido binario de prueba"
    digest = hash_bytes(contenido)

    central.guardar_blob(dispositivo, digest, contenido)
    central.guardar_blob(dispositivo, digest, contenido)  # repetido: no falla
    assert central.leer_blob(digest) == contenido


def test_un_blob_con_hash_incorrecto_se_rechaza(central):
    _, _, dispositivo = _emparejar(central)
    with pytest.raises(ErrorPeticion) as error:
        central.guardar_blob(dispositivo, hash_bytes(b"otra cosa"), b"contenido")
    assert error.value.codigo == 422


def test_un_blob_demasiado_grande_se_rechaza(central):
    _, _, dispositivo = _emparejar(central)
    central.config.max_bytes_blob = 4
    contenido = b"12345"
    with pytest.raises(ErrorPeticion) as error:
        central.guardar_blob(dispositivo, hash_bytes(contenido), contenido)
    assert error.value.codigo == 413


def test_un_blob_desconocido_no_se_inventa(central):
    assert central.leer_blob(hash_bytes(b"nunca subido")) is None


# ----------------------------------------------------------------------
# Transporte HTTP real
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
def servicio(tmp_path):
    """Nodo central hablado por HTTP, como lo hará el agente"""
    config = ServidorConfig(
        url_db=f"sqlite:///{(tmp_path / 'central.db').as_posix()}",
        dir_blobs=tmp_path / "blobs",
        host="127.0.0.1",
        puerto=0,
    )
    with ServicioEnMarcha(config) as en_marcha:
        yield en_marcha


def test_ciclo_http_completo_entre_dos_puestos(servicio):
    from sync_agent.cliente import ClienteSync

    dispositivo_a, token_a = servicio.servidor.nucleo.crear_dispositivo("Puesto A")
    dispositivo_b, token_b = servicio.servidor.nucleo.crear_dispositivo("Puesto B")
    url = f"http://127.0.0.1:{servicio.puerto}"

    cliente_a = ClienteSync(url, token_a, dispositivo_a, timeout=5)
    cliente_b = ClienteSync(url, token_b, dispositivo_b, timeout=5)

    assert cliente_a.ping()["servidor"] == "nodo-central-sincronizacion"

    operacion = _operacion(payload=_payload_empleado(cargo="Director"))
    respuesta = cliente_a.enviar_ops([operacion])
    assert respuesta["aplicadas"] == [operacion["op_id"]]

    novedades = cliente_b.recibir_ops(0)
    assert novedades["ops"][0]["fila_uuid"] == operacion["fila_uuid"]

    contenido = b"documento escaneado"
    digest = hash_bytes(contenido)
    cliente_a.subir_blob(digest, contenido)
    assert cliente_b.bajar_blob(digest) == contenido


def test_un_token_invalido_se_detecta_por_http(servicio):
    from sync_agent.cliente import ClienteSync, ErrorAutenticacion

    dispositivo, _token = servicio.servidor.nucleo.crear_dispositivo("Puesto A")
    cliente = ClienteSync(f"http://127.0.0.1:{servicio.puerto}", "token-falso", dispositivo, timeout=5)
    with pytest.raises(ErrorAutenticacion):
        cliente.recibir_ops(0)


def test_una_ruta_desconocida_responde_404(servicio):
    from sync_agent.cliente import ClienteSync, ErrorProtocolo

    dispositivo, token = servicio.servidor.nucleo.crear_dispositivo("Puesto A")
    cliente = ClienteSync(f"http://127.0.0.1:{servicio.puerto}", token, dispositivo, timeout=5)
    with pytest.raises(ErrorProtocolo):
        cliente._peticion("GET", "/api/v1/inexistente")
