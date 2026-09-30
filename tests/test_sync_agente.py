"""
Pruebas del agente de sincronización (hilo de fondo)

La garantía que más importa aquí es la de **modo offline**: si no hay red, el
usuario sigue trabajando igual, el ciclo falla sin romper nada y las
operaciones quedan pendientes con su marca de tiempo para el próximo intento.
"""

import socket
import threading

from sync_agent.agente import (
    ESPERA_MAXIMA,
    ESTADO_DETENIDO,
    ESTADO_ERROR_TOKEN,
    ESTADO_INACTIVO,
    ESTADO_SIN_CONEXION,
    AgenteSincronizacion,
)
from sync_agent.esquema import PENDIENTE, JournalOp
from sync_agent.servidor import NucleoCentral, ServidorConfig, ServidorSync


def _puerto_libre() -> int:
    """Puerto que nadie está escuchando (para simular la caída de la red)"""
    with socket.socket() as sonda:
        sonda.bind(("127.0.0.1", 0))
        return sonda.getsockname()[1]


def _config(entorno, url, token, dispositivo, intervalo=5):
    from sync_agent.captura import establecer_dispositivo
    from sync_agent.config import cargar, guardar

    guardar(
        habilitado=True,
        url_servidor=url,
        token=token,
        dispositivo_id=dispositivo,
        intervalo_segundos=intervalo,
    )
    config = cargar()
    establecer_dispositivo(config.dispositivo_id)
    return config


def _operaciones(entorno):
    sesion = entorno.new_session()
    try:
        return sesion.query(JournalOp).order_by(JournalOp.id).all()
    finally:
        entorno.close_session(sesion)


def _crear_empleado(entorno, cedula="12345678"):
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


class ServicioEnMarcha:
    """Nodo central HTTP efímero para las pruebas del agente"""

    def __init__(self, tmp_path):
        self.config = ServidorConfig(
            url_db=f"sqlite:///{(tmp_path / 'central.db').as_posix()}",
            dir_blobs=tmp_path / "blobs",
            host="127.0.0.1",
            puerto=0,
        )
        self.servidor = ServidorSync(self.config)
        self.puerto = self.servidor.server_address[1]
        self.url = f"http://127.0.0.1:{self.puerto}"
        self._hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)

    @property
    def nucleo(self) -> NucleoCentral:
        return self.servidor.nucleo

    def __enter__(self):
        self._hilo.start()
        return self

    def __exit__(self, *_excepcion):
        self.servidor.shutdown()
        self.servidor.server_close()
        self._hilo.join(timeout=5)
        self.servidor.nucleo.cerrar()


# ----------------------------------------------------------------------
# Arranque y parada
# ----------------------------------------------------------------------
def test_no_arranca_sin_configuracion(entorno_sync):
    agente = AgenteSincronizacion()
    assert agente.iniciar() is False
    assert agente.activo() is False
    assert agente.estado()["estado"] == ESTADO_INACTIVO


def test_arranca_y_se_detiene_limpiamente(entorno_sync, tmp_path):
    with ServicioEnMarcha(tmp_path) as servicio:
        dispositivo, token = servicio.nucleo.crear_dispositivo("Puesto A")
        config = _config(entorno_sync, servicio.url, token, dispositivo)

        agente = AgenteSincronizacion(config)
        assert agente.iniciar() is True
        assert agente.activo() is True
        agente.detener(timeout=10)
        assert agente.activo() is False
        assert agente.estado()["estado"] == ESTADO_DETENIDO


def test_sincronizar_ahora_requiere_agente_en_marcha(entorno_sync):
    agente = AgenteSincronizacion()
    assert agente.sincronizar_ahora() is False


# ----------------------------------------------------------------------
# Resiliencia: sin red, el trabajo del usuario no se pierde
# ----------------------------------------------------------------------
def test_sin_servidor_el_ciclo_falla_sin_romper_nada(entorno_sync):
    _crear_empleado(entorno_sync)
    url = f"http://127.0.0.1:{_puerto_libre()}"
    config = _config(entorno_sync, url, "token-cualquiera", "dispositivo-de-prueba")

    agente = AgenteSincronizacion(config)
    resultado = agente.ciclo()

    assert resultado["correcto"] is False
    assert agente.estado()["estado"] == ESTADO_SIN_CONEXION
    assert agente.estado()["ultimo_error"]
    # Lo escrito durante el corte sigue esperando su turno
    operaciones = _operaciones(entorno_sync)
    assert len(operaciones) == 1
    assert operaciones[0].estado == PENDIENTE


def test_la_espera_tras_fallo_crece_y_tiene_tope():
    """Espera 30, 60, 120, 240 y luego se queda en el tope de cinco minutos

    El azar añade hasta un 10 % a cada espera (para que los puestos del colegio
    no golpeen el servidor a la vez cuando vuelve la red), así que se comprueba
    el rango de cada intento y no un valor exacto.
    """
    bases = [30, 60, 120, 240, ESPERA_MAXIMA, ESPERA_MAXIMA, ESPERA_MAXIMA]
    for intento, base in enumerate(bases, start=1):
        espera = AgenteSincronizacion._esperar_tras_fallo(intento)
        assert base <= espera <= base * 1.1, f"intento {intento}: {espera} s"


def test_un_token_rechazado_detiene_el_agente(entorno_sync, tmp_path):
    with ServicioEnMarcha(tmp_path) as servicio:
        dispositivo, _token = servicio.nucleo.crear_dispositivo("Puesto A")
        config = _config(entorno_sync, servicio.url, "token-incorrecto", dispositivo)

        agente = AgenteSincronizacion(config)
        resultado = agente.ciclo()

    assert resultado["correcto"] is False
    assert resultado.get("detener") is True
    assert agente.estado()["estado"] == ESTADO_ERROR_TOKEN
    assert agente.estado()["habilitado"] is False


def test_un_ciclo_no_puede_solaparse(entorno_sync):
    """Dos ciclos simultáneos duplicarían el envío: el candado lo impide"""
    url = f"http://127.0.0.1:{_puerto_libre()}"
    config = _config(entorno_sync, url, "token", "dispositivo")
    agente = AgenteSincronizacion(config)

    agente._en_ciclo.acquire()
    try:
        resultado = agente.ciclo()
    finally:
        agente._en_ciclo.release()
    assert resultado == {"correcto": True, "mensaje": "ciclo ya en curso"}
