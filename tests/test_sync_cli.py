"""
Pruebas de la interfaz de línea de comandos del agente

`py -3 -m sync_agent` es la vía de operación sin interfaz gráfica: prepara el
equipo, consulta pendientes y conflictos, y administra los puestos del nodo
central. Estas pruebas la ejecutan de extremo a extremo (``main``), de modo que
la salida, los códigos de retorno (0 correcto / 1 error / 2 inactivo) y las
rutas de administración queden cubiertas como las usa un administrador.

Las únicas partes que no se ejercitan aquí son las que abren puertos (el arranque
del nodo central) y la espera hasta ``Ctrl+C``: se sustituyen por dobles.
"""

import json
import logging
import re

import pytest

from sync_agent.__main__ import (
    SALIDA_CORRECTA,
    SALIDA_ERROR,
    SALIDA_INACTIVO,
    main,
)
from sync_agent.comun import dumps, hash_bytes, nuevo_uuid
from sync_agent.esquema import ConflictoSync, SyncId


@pytest.fixture(autouse=True)
def _restaurar_logging():
    """
    Devuelve el registro a su estado previo tras cada prueba

    ``_configurar_logging`` sustituye los manejadores de la raíz; sin esta
    restauración, la herramienta dejaría la raíz apuntando a la salida capturada
    de la prueba y contaminaría a las siguientes.
    """
    raiz = logging.getLogger()
    manejadores = list(raiz.handlers)
    nivel = raiz.level
    yield
    for manejador in list(raiz.handlers):
        raiz.removeHandler(manejador)
    for manejador in manejadores:
        raiz.addHandler(manejador)
    raiz.setLevel(nivel)


def _crear_empleado(entorno, cedula="12345678"):
    """Empleado real creado por el servicio, como lo haría el usuario"""
    from src.services.empleado_service import EmpleadoService

    sesion = entorno.get_session()
    try:
        return EmpleadoService(sesion).crear_empleado(
            {
                "nombres": "Ana",
                "apellidos": "Gómez",
                "cedula": cedula,
                "tipo_empleado": "docente",
                "cargo": "Docente",
                "salario_base": 1200.0,
            }
        )
    finally:
        entorno.close_session(sesion)


def _crear_empleado_sin_agente(entorno, cedula="12345678"):
    """
    Empleado tal como queda en un puesto que **nunca** ejecutó el agente

    Con la captura instalada, el alta ya anota su identidad global; ese no es el
    caso de los datos heredados, que son los que ``init`` debe adoptar. Se borra
    la anotación para reproducir ese estado.
    """
    from sqlalchemy import text

    empleado = _crear_empleado(entorno, cedula)
    with entorno.engine.begin() as conn:
        conn.execute(text('DELETE FROM "sync_ids"'))
        conn.execute(text('DELETE FROM "sync_journal"'))
    return empleado


def _conflictos_tabla(entorno):
    """Número de conflictos locales guardados en la bandeja"""
    sesion = entorno.new_session()
    try:
        return sesion.query(ConflictoSync).count()
    finally:
        entorno.close_session(sesion)


def _filas_adoptadas(salida: str) -> int:
    """Lee cuántas filas adoptó `init` del resumen que imprime"""
    coincidencia = re.search(r"Filas adoptadas\.*\s+(\d+)", salida)
    assert coincidencia, salida
    return int(coincidencia.group(1))


def _identidades(entorno, tabla="empleados"):
    """Filas con identidad global anotadas para una tabla"""
    sesion = entorno.new_session()
    try:
        return sesion.query(SyncId).filter(SyncId.tabla == tabla).count()
    finally:
        entorno.close_session(sesion)


def _anotar_conflicto(entorno, campo="salario_base", revisado=False):
    """Coloca un conflicto en la bandeja local, como lo haría una mezcla"""
    sesion = entorno.new_session()
    try:
        sesion.add(
            ConflictoSync(
                tabla="empleados",
                fila_uuid=nuevo_uuid(),
                campo=campo,
                valor_local=dumps(1200.0),
                valor_remoto=dumps(1500.0),
                ganador="local",
                regla="escritura_mas_reciente",
                resuelto=1 if revisado else 0,
            )
        )
        sesion.commit()
    finally:
        entorno.close_session(sesion)


# ----------------------------------------------------------------------
# estado
# ----------------------------------------------------------------------
def test_el_estado_informa_de_lo_que_falta_por_configurar(entorno_sync, capsys):
    codigo = main(["estado"])

    salida = capsys.readouterr().out
    assert codigo == SALIDA_CORRECTA
    assert "Pendientes por enviar" in salida
    assert "Falta la dirección del servidor central" in salida
    assert "Defínalos" not in salida  # ese aviso es de `init`, no de `estado`


def test_el_estado_en_json_se_puede_consumir_por_otro_programa(entorno_sync, capsys):
    _crear_empleado(entorno_sync)

    codigo = main(["estado", "--json"])

    assert codigo == SALIDA_CORRECTA
    datos = json.loads(capsys.readouterr().out)
    assert datos["configurado"] is False
    assert datos["pendientes_por_enviar"] >= 1
    assert datos["conflictos_sin_revisar"] == 0
    assert datos["ultimo_seq_aplicado"] == 0


# ----------------------------------------------------------------------
# init
# ----------------------------------------------------------------------
def test_init_da_identidad_global_a_los_datos_previos(entorno_sync, capsys):
    """Los datos cargados antes del agente deben recibir identidad global"""
    _crear_empleado_sin_agente(entorno_sync)

    codigo = main(["init"])

    salida = capsys.readouterr().out
    assert codigo == SALIDA_CORRECTA
    assert "Equipo preparado para la sincronización" in salida
    assert _filas_adoptadas(salida) >= 1
    assert _identidades(entorno_sync) == 1


def test_init_es_idempotente_y_no_duplica_identidades(entorno_sync, capsys):
    _crear_empleado_sin_agente(entorno_sync)
    main(["init"])
    capsys.readouterr()

    assert main(["init"]) == SALIDA_CORRECTA

    assert "Filas adoptadas" in capsys.readouterr().out
    assert _identidades(entorno_sync) == 1


def test_init_sin_adoptar_deja_los_datos_previos_fuera_del_agente(entorno_sync, capsys):
    _crear_empleado_sin_agente(entorno_sync)

    codigo = main(["init", "--sin-adoptar"])

    salida = capsys.readouterr().out
    assert codigo == SALIDA_CORRECTA
    assert _filas_adoptadas(salida) == 0
    assert _identidades(entorno_sync) == 0

    # Y al ejecutarlo de nuevo, sin la bandera, el dato heredado sí se adopta
    assert main(["init"]) == SALIDA_CORRECTA
    assert _filas_adoptadas(capsys.readouterr().out) >= 1
    assert _identidades(entorno_sync) == 1


def test_init_informa_si_la_adopcion_falla(entorno_sync, capsys, monkeypatch):
    """Un fallo de adopción no puede terminar con el equipo a medio preparar"""
    import sync_agent.captura as captura

    def _revienta(_sesion):
        raise RuntimeError("no se pudo leer la tabla")

    monkeypatch.setattr(captura, "adoptar_existentes", _revienta)

    codigo = main(["init"])

    assert codigo == SALIDA_ERROR
    assert _identidades(entorno_sync) == 0


# ----------------------------------------------------------------------
# agente
# ----------------------------------------------------------------------
def test_agente_sin_configuracion_explica_por_que_no_arranca(entorno_sync, capsys):
    codigo = main(["agente"])

    salida = capsys.readouterr().out
    assert codigo == SALIDA_INACTIVO
    assert "El agente no puede arrancar todavía" in salida
    assert "Falta la dirección del servidor central" in salida


def test_agente_una_vez_avisa_del_fallo_y_devuelve_error(entorno_sync, capsys):
    """Un ciclo sin servidor configurado no puede devolver éxito"""
    codigo = main(["agente", "--una-vez"])

    salida = capsys.readouterr().out
    assert codigo == SALIDA_ERROR
    assert re.search(r"Correcto\.*\s+False", salida)


# ----------------------------------------------------------------------
# conflictos
# ----------------------------------------------------------------------
def test_conflictos_sin_registros_lo_dice_sin_tabla_vacia(entorno_sync, capsys):
    codigo = main(["conflictos"])

    salida = capsys.readouterr().out
    assert codigo == SALIDA_CORRECTA
    assert "Conflictos sin revisar: 0" in salida
    assert "(sin registros)" in salida


def test_conflictos_muestra_los_valores_que_compitieron(entorno_sync, capsys):
    _anotar_conflicto(entorno_sync)

    codigo = main(["conflictos"])

    salida = capsys.readouterr().out
    assert codigo == SALIDA_CORRECTA
    assert "Conflictos sin revisar: 1" in salida
    assert "salario_base" in salida
    assert "escritura_mas_reciente" in salida
    assert "1200" in salida and "1500" in salida


def test_conflictos_oculta_los_ya_revisados_salvo_que_se_pidan(entorno_sync, capsys):
    _anotar_conflicto(entorno_sync, campo="cargo", revisado=True)
    _anotar_conflicto(entorno_sync, campo="salario_base", revisado=False)
    capsys.readouterr()

    assert main(["conflictos"]) == SALIDA_CORRECTA
    pendientes = capsys.readouterr().out
    assert "Conflictos sin revisar: 1" in pendientes
    assert "cargo" not in pendientes

    assert main(["conflictos", "--todos"]) == SALIDA_CORRECTA
    todos = capsys.readouterr().out
    assert "Conflictos registrados: 2" in todos
    assert "cargo" in todos


def test_conflictos_en_json_es_una_lista(entorno_sync, capsys):
    _anotar_conflicto(entorno_sync)

    assert main(["conflictos", "--json"]) == SALIDA_CORRECTA

    registros = json.loads(capsys.readouterr().out)
    assert len(registros) == 1
    assert registros[0]["tabla"] == "empleados"
    assert registros[0]["campo"] == "salario_base"
    assert registros[0]["valor_local"] == "1200.0"
    assert registros[0]["valor_remoto"] == "1500.0"


def test_conflictos_respeta_el_limite_de_filas(entorno_sync, capsys):
    for indice in range(3):
        _anotar_conflicto(entorno_sync, campo=f"campo_{indice}")
    capsys.readouterr()

    assert main(["conflictos", "--limite", "2", "--json"]) == SALIDA_CORRECTA

    assert len(json.loads(capsys.readouterr().out)) == 2


# ----------------------------------------------------------------------
# servidor y dispositivos (administración del nodo central)
# ----------------------------------------------------------------------
def _url_central(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'central.db').as_posix()}"


def test_los_puestos_se_dan_de_alta_y_de_baja_por_consola(tmp_path, capsys):
    url = _url_central(tmp_path)

    codigo = main(["servidor", "--db", url, "--crear-dispositivo", "Secretaría"])
    salida = capsys.readouterr().out
    assert codigo == SALIDA_CORRECTA
    assert "Puesto 'Secretaría' creado" in salida
    assert "no se puede recuperar después" in salida
    identificador = re.search(r"Identificador:\s+(\S+)", salida).group(1)
    token = re.search(r"Token:\s+(\S+)", salida).group(1)
    assert token and token != identificador

    assert main(["dispositivos", "--db", url, "--listar"]) == SALIDA_CORRECTA
    listado = capsys.readouterr().out
    assert "Puestos registrados: 1" in listado
    assert "Secretaría" in listado
    assert token not in listado  # el token no vuelve a salir nunca

    assert main(["dispositivos", "--db", url, "--revocar", identificador]) == SALIDA_CORRECTA
    assert "revocado" in capsys.readouterr().out

    assert main(["dispositivos", "--db", url, "--revocar", nuevo_uuid()]) == SALIDA_ERROR
    assert "No existe un puesto" in capsys.readouterr().out


def test_el_listado_de_puestos_admite_json(tmp_path, capsys):
    url = _url_central(tmp_path)
    main(["dispositivos", "--db", url, "--crear", "Rectoría"])
    capsys.readouterr()

    assert main(["servidor", "--db", url, "--listar-dispositivos", "--json"]) == SALIDA_CORRECTA

    registrados = json.loads(capsys.readouterr().out)
    assert [puesto["nombre"] for puesto in registrados] == ["Rectoría"]
    assert registrados[0]["activo"] is True
    assert "token_hash" not in registrados[0]


def test_los_conflictos_del_nodo_se_exportan_a_un_archivo(tmp_path, capsys):
    """Dos puestos que editan el mismo campo dejan un conflicto exportable"""
    url = _url_central(tmp_path)
    payload = {
        "cedula": "12345678",
        "nombres": "Ana",
        "apellidos": "Gómez",
        "tipo_empleado": "docente",
        "departamento": "Docencia",
        "salario_base": 1200.0,
        "activo": 1,
    }
    from sync_agent.servidor import NucleoCentral, ServidorConfig

    nucleo = NucleoCentral(
        ServidorConfig(url_db=url, dir_blobs=tmp_path / "blobs", host="127.0.0.1", puerto=0)
    )
    try:
        puesto_a, _token_a = nucleo.crear_dispositivo("Puesto A")
        puesto_b, _token_b = nucleo.crear_dispositivo("Puesto B")
        dispositivo_a = nucleo.autenticar(puesto_a, _token_a)
        dispositivo_b = nucleo.autenticar(puesto_b, _token_b)
        fila_uuid = nuevo_uuid()
        nucleo.push(
            dispositivo_a,
            {
                "ops": [
                    {
                        "op_id": nuevo_uuid(),
                        "tabla": "empleados",
                        "fila_uuid": fila_uuid,
                        "operacion": "upsert",
                        "payload": dumps({**payload, "cargo": "Director"}),
                        "base_op_id": None,
                        "dispositivo": puesto_a,
                        "usuario": "prueba",
                        "creado_en": "2026-01-01T12:00:00",
                    }
                ]
            },
        )
        nucleo.push(
            dispositivo_b,
            {
                "ops": [
                    {
                        "op_id": nuevo_uuid(),
                        "tabla": "empleados",
                        "fila_uuid": fila_uuid,
                        "operacion": "upsert",
                        "payload": dumps({**payload, "cargo": "Secretaria"}),
                        "base_op_id": None,
                        "dispositivo": puesto_b,
                        "usuario": "prueba",
                        "creado_en": "2026-01-01T11:00:00",
                    }
                ]
            },
        )
    finally:
        nucleo.cerrar()

    destino = tmp_path / "conflictos.json"
    codigo = main(["servidor", "--db", url, "--exportar-conflictos", str(destino)])

    salida = capsys.readouterr().out
    assert codigo == SALIDA_CORRECTA
    assert "Conflictos exportados" in salida
    exportados = json.loads(destino.read_text(encoding="utf-8"))
    assert any(registro["campo"] == "cargo" for registro in exportados)


def test_la_purga_del_historial_se_puede_ejecutar_por_consola(tmp_path, capsys):
    url = _url_central(tmp_path)

    codigo = main(["servidor", "--db", url, "--purgar-historial", "365"])

    salida = capsys.readouterr().out
    assert codigo == SALIDA_CORRECTA
    assert "Operaciones retiradas del historial central: 0" in salida


def test_el_arranque_del_nodo_central_anuncia_donde_escucha(tmp_path, capsys, monkeypatch):
    """El arranque real queda fuera (bloquearía la suite): se sustituye el servicio"""
    import sync_agent.servidor as servidor

    visto = {}

    def _servicio_falso(config):
        visto["config"] = config
        return SALIDA_CORRECTA

    monkeypatch.setattr(servidor, "ejecutar_servidor", _servicio_falso)

    codigo = main(
        ["servidor", "--db", _url_central(tmp_path), "--host", "127.0.0.1", "--puerto", "8899"]
    )

    salida = capsys.readouterr().out
    assert codigo == SALIDA_CORRECTA
    assert "Nodo central escuchando en http://127.0.0.1:8899" in salida
    assert visto["config"].puerto == 8899
    assert visto["config"].host == "127.0.0.1"


def test_la_carpeta_de_binarios_por_omision_vive_junto_a_la_base(tmp_path):
    """Sin `--blobs`, los binarios quedan al lado de la base del nodo central"""
    from pathlib import Path

    from sync_agent.__main__ import _dir_blobs_por_defecto

    assert _dir_blobs_por_defecto("sqlite:////datos/central.db") == Path(
        "/datos/central_blobs"
    )
    # Una base que no sea SQLite cae en el nombre por omisión, junto al proceso
    assert _dir_blobs_por_defecto("postgresql://usuario@host/central") == Path(
        "sync_central_blobs"
    )


def test_la_consola_respeta_la_carpeta_de_binarios_indicada(tmp_path, capsys, monkeypatch):
    """`--blobs` debe llegar al nodo central tal como se escribió"""
    import sync_agent.servidor as servidor

    carpeta = tmp_path / "binarios"
    visto = {}

    def _servicio_falso(config):
        visto["config"] = config
        return SALIDA_CORRECTA

    monkeypatch.setattr(servidor, "ejecutar_servidor", _servicio_falso)

    codigo = main(
        [
            "servidor",
            "--db",
            _url_central(tmp_path),
            "--blobs",
            str(carpeta),
            "--host",
            "127.0.0.1",
            "--puerto",
            "8899",
        ]
    )

    assert codigo == SALIDA_CORRECTA
    assert visto["config"].dir_blobs == carpeta


def test_un_binario_del_nodo_se_deduplica_por_su_hash(tmp_path):
    """El nodo central comprueba el hash: el mismo contenido no se guarda dos veces"""
    from sync_agent.servidor import ErrorPeticion, NucleoCentral, ServidorConfig

    nucleo = NucleoCentral(
        ServidorConfig(
            url_db=_url_central(tmp_path), dir_blobs=tmp_path / "blobs", host="127.0.0.1", puerto=0
        )
    )
    try:
        puesto, token = nucleo.crear_dispositivo("Puesto A")
        dispositivo = nucleo.autenticar(puesto, token)
        contenido = "escaneo de cédula".encode("utf-8")
        nucleo.guardar_blob(dispositivo, hash_bytes(contenido), contenido)
        nucleo.guardar_blob(dispositivo, hash_bytes(contenido), contenido)
        assert nucleo.leer_blob(hash_bytes(contenido)) == contenido
        with pytest.raises(ErrorPeticion):
            nucleo.guardar_blob(dispositivo, hash_bytes(b"otro"), contenido)
    finally:
        nucleo.cerrar()


# ----------------------------------------------------------------------
# Comportamiento del punto de entrada
# ----------------------------------------------------------------------
def test_un_comando_que_falla_no_se_lleva_por_delante_la_consola(capsys, monkeypatch):
    import sync_agent.__main__ as cli

    def _revienta(_args):
        raise RuntimeError("la base está bloqueada")

    monkeypatch.setattr(cli, "cmd_estado", _revienta)

    codigo = main(["estado"])

    capturado = capsys.readouterr()
    assert codigo == SALIDA_ERROR
    assert "la base está bloqueada" in capturado.err
    assert "la base está bloqueada" not in capturado.out


def test_sin_subcomando_la_herramienta_lo_explica(capsys):
    with pytest.raises(SystemExit) as salida:
        main([])
    assert salida.value.code != 0
    assert "usage" in capsys.readouterr().err


def test_solo_se_ofrecen_los_subcomandos_documentados():
    from sync_agent.__main__ import _parser

    parser = _parser()
    acciones = [
        accion for accion in parser._actions if getattr(accion, "choices", None)
    ]
    subcomandos = sorted(acciones[0].choices)
    assert subcomandos == [
        "agente",
        "conflictos",
        "dispositivos",
        "estado",
        "init",
        "servidor",
    ]
