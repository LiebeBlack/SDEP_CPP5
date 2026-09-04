"""Pruebas del módulo de tema visual (theme.py)

Estas pruebas verifican la integridad de las paletas de color y la lógica
de cambio de apariencia sin requerir una ventana gráfica. Las funciones
que necesitan un widget Tk se prueban con objetos simulados (mocks).
"""

import re

import pytest

from src.gui import theme

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def test_paletas_tienen_mismas_claves():
    assert set(theme.PALETA_OSCURA.keys()) == set(theme.PALETA_CLARA.keys())


def test_paletas_colores_hex_validos():
    # Los valores pueden ser colores hex (#rrggbb) o nombres de color Tk ("white")
    for paleta in (theme.PALETA_OSCURA, theme.PALETA_CLARA):
        for clave, valor in paleta.items():
            assert _HEX_COLOR.match(valor) or valor in {"white", "black"}, \
                f"{clave} no es un color válido: {valor!r}"


def test_paletas_difieren_entre_si():
    assert theme.PALETA_OSCURA != theme.PALETA_CLARA


def test_colores_inicia_con_paleta_oscura():
    assert theme.COLORES == theme.PALETA_OSCURA


def test_aplicar_modo_light_actualiza_colores():
    theme.aplicar_modo_apariencia("Light")
    try:
        assert theme.COLORES == theme.PALETA_CLARA
    finally:
        # Restaurar el estado global para no afectar a otras pruebas
        theme.aplicar_modo_apariencia("Dark")


def test_aplicar_modo_dark_restaura_paleta():
    theme.aplicar_modo_apariencia("Light")
    theme.aplicar_modo_apariencia("Dark")
    assert theme.COLORES == theme.PALETA_OSCURA


def test_aplicar_modo_invalido_usa_oscuro():
    theme.aplicar_modo_apariencia("Raro")
    assert theme.COLORES == theme.PALETA_OSCURA


def test_centrar_ventana_mock():
    class VentanaMock:
        def __init__(self):
            self.geometria = None

        def update_idletasks(self):
            pass

        def winfo_screenwidth(self):
            return 1920

        def winfo_screenheight(self):
            return 1080

        def geometry(self, geo):
            self.geometria = geo

    ventana = VentanaMock()
    theme.centrar_ventana(ventana, 800, 600)
    # x = (1920-800)//2 = 560 ; y = (1080-600)//2 = 240
    assert ventana.geometria == "800x600+560+240"


def test_centrar_ventana_falla_usa_geometria_basica():
    class VentanaRota:
        def update_idletasks(self):
            raise RuntimeError("sin display")

        def geometry(self, geo):
            self.geometria = geo

    ventana = VentanaRota()
    theme.centrar_ventana(ventana, 400, 300)
    assert ventana.geometria == "400x300"


def test_cancelar_after_pendientes_mock():
    class TclMock:
        def call(self, *args):
            assert args == ("after", "info")
            return ["after#1", "after#2"]

    class RootMock:
        def __init__(self):
            self.tk = TclMock()
            self.cancelados = []

        def after_cancel(self, id_tarea):
            self.cancelados.append(id_tarea)

    root = RootMock()
    theme.cancelar_after_pendientes(root)
    assert root.cancelados == ["after#1", "after#2"]


def test_silenciar_errores_fondo_mock():
    class RootMock:
        def tk(self, *args):
            assert args == ("proc", "bgerror", "msg", "")

    theme.silenciar_errores_fondo(RootMock())


def test_enable_dpi_awareness_no_rompe():
    # Debe retornar bool sin excepción en cualquier plataforma
    resultado = theme.enable_windows_dpi_awareness()
    assert isinstance(resultado, bool)


def test_setup_ui_raiz_sin_display_no_rompe():
    """setup_ui_raiz debe fallar silenciosamente si no hay ventana raíz"""
    theme.setup_ui_raiz(None)