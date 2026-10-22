"""
Pruebas de la difusión UDP del nodo central

El teléfono ya no recibe una dirección escrita a mano: pregunta por difusión y
el nodo responde con su identidad y el puerto HTTP. Estas pruebas comprueban
que la respuesta solo se entrega a la firma correcta, que incluye el puerto
real y que el servicio se puede detener sin dejar el socket abierto.
"""

import json
import socket

from sync_agent.descubrimiento import (
    FIRMA_PETICION,
    IDENTIDAD_NODO,
    DifusorDescubrimiento,
)
from sync_agent.servidor import ServidorConfig, ServidorSync


def _puerto_udp_libre() -> int:
    """Puerto UDP efímero que el sistema acaba de confirmar como libre"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sonda:
        sonda.bind(("127.0.0.1", 0))
        return int(sonda.getsockname()[1])


def test_responde_con_identidad_y_puerto_http():
    puerto = _puerto_udp_libre()
    difusor = DifusorDescubrimiento(puerto_http=8765, puerto=puerto, nombre="Equipo de secretaría")
    try:
        assert difusor.iniciar() is True
        assert difusor.activo is True

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cliente:
            cliente.settimeout(2.0)
            cliente.sendto(FIRMA_PETICION, ("127.0.0.1", puerto))
            datos, origen = cliente.recvfrom(2048)

        respuesta = json.loads(datos.decode("utf-8"))
        assert respuesta["servidor"] == IDENTIDAD_NODO
        assert respuesta["puerto"] == 8765
        assert respuesta["version_protocolo"] == "2"
        assert respuesta["nombre"] == "Equipo de secretaría"
        assert origen[0] == "127.0.0.1"
    finally:
        difusor.detener()

    assert difusor.activo is False


def test_el_servidor_http_difunde_su_puerto_real(tmp_path):
    """El anuncio lleva el puerto que el sistema asignó al HTTP"""
    puerto_difusion = _puerto_udp_libre()
    servidor = ServidorSync(
        ServidorConfig(
            url_db=f"sqlite:///{(tmp_path / 'central.db').as_posix()}",
            dir_blobs=tmp_path / "blobs",
            host="127.0.0.1",
            puerto=0,
            puerto_descubrimiento=puerto_difusion,
            nombre_equipo="Equipo de prueba",
        )
    )
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cliente:
            cliente.settimeout(2.0)
            cliente.sendto(FIRMA_PETICION, ("127.0.0.1", puerto_difusion))
            datos, _ = cliente.recvfrom(2048)
        respuesta = json.loads(datos.decode("utf-8"))
        assert respuesta["servidor"] == IDENTIDAD_NODO
        assert respuesta["puerto"] == servidor.server_address[1]
        assert respuesta["nombre"] == "Equipo de prueba"
    finally:
        servidor.cerrar()


def test_ignora_datagramas_ajenos():
    puerto = _puerto_udp_libre()
    difusor = DifusorDescubrimiento(puerto_http=8765, puerto=puerto)
    try:
        assert difusor.iniciar() is True
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cliente:
            cliente.settimeout(0.6)
            cliente.sendto(b"otra cosa", ("127.0.0.1", puerto))
            try:
                cliente.recvfrom(2048)
            except socket.timeout:
                pass
            else:  # pragma: no cover - solo falla si el filtro no funciona
                raise AssertionError("El difusor respondió a una firma desconocida")
    finally:
        difusor.detener()
