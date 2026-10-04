"""
Coherencia entre el menú de módulos y el mapa de permisos.

Convierte el hallazgo D en un defecto que la suite detecta: ningún módulo
puede faltar en FRAME_CLASSES, ningún módulo controlado puede faltar en
MODULE_ACCESS y el mapa no puede declarar módulos que no existen en el menú.
"""

from src.gui.main_window import (
    FRAME_CLASSES,
    MODULOS,
    MODULOS_SIN_CONTROL_DE_ACCESO,
)
from src.utils.security import PermissionChecker


def test_todo_modulo_tiene_frame():
    for nombre, _titulo, _icono in MODULOS:
        assert nombre in FRAME_CLASSES, f"El módulo {nombre!r} no tiene frame"


def test_todo_modulo_controlado_tiene_permiso():
    for nombre, _titulo, _icono in MODULOS:
        if nombre in MODULOS_SIN_CONTROL_DE_ACCESO:
            continue
        assert nombre in PermissionChecker.MODULE_ACCESS, (
            f"El módulo {nombre!r} no está declarado en MODULE_ACCESS "
            "(quedaría oculto para todos los roles)"
        )


def test_el_mapa_no_declara_modulos_inexistentes():
    """El caso «reportes»: un módulo protegido que no existe en el menú."""
    esperados = (
        frozenset(nombre for nombre, _titulo, _icono in MODULOS)
        - MODULOS_SIN_CONTROL_DE_ACCESO
    )
    assert PermissionChecker.modulos_conocidos() == esperados


def test_el_limite_de_atajos_esta_documentado():
    """
    Ctrl+1..9 se deriva del orden de MODULOS. Si se superan nueve módulos, el
    décimo queda sin atajo directo: el plan exige decidirlo y documentarlo
    antes de agregar más módulos a la interfaz.
    """
    assert len(MODULOS) <= 9, (
        "MODULOS supera los nueve atajos directos; hay que documentar qué "
        "módulo queda sin Ctrl+N o reorganizar los atajos"
    )
