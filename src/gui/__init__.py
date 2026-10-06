"""
GUI Module
Componentes de interfaz gráfica de usuario
"""

from .frames import (
    ConfiguracionFrame,
    DashboardFrame,
    DocumentosFrame,
    EmpleadosFrame,
    IncidenciasFrame,
    NominaFrame,
)
from .main_window import MainWindow

__all__ = [
    "MainWindow",
    "DashboardFrame",
    "EmpleadosFrame",
    "DocumentosFrame",
    "IncidenciasFrame",
    "NominaFrame",
    "ConfiguracionFrame",
]
