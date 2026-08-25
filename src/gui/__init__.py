"""
GUI Module
Componentes de interfaz gráfica de usuario
"""

from .main_window import MainWindow
from .frames import (
    DashboardFrame,
    EmpleadosFrame,
    DocumentosFrame,
    IncidenciasFrame,
    NominaFrame,
    ConfiguracionFrame
)

__all__ = [
    "MainWindow",
    "DashboardFrame",
    "EmpleadosFrame",
    "DocumentosFrame",
    "IncidenciasFrame",
    "NominaFrame",
    "ConfiguracionFrame"
]