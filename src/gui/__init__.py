"""
GUI Module
Componentes de interfaz gráfica de usuario
"""

from .contratos_frame import ContratosFrame
from .estudiantes_frame import EstudiantesFrame
from .frames import (
    ConfiguracionFrame,
    DashboardFrame,
    DocumentosFrame,
    EmpleadosFrame,
    IncidenciasFrame,
    NominaFrame,
)
from .main_window import MainWindow
from .notas_frame import NotasFrame

__all__ = [
    "MainWindow",
    "DashboardFrame",
    "EmpleadosFrame",
    "DocumentosFrame",
    "IncidenciasFrame",
    "NominaFrame",
    "ConfiguracionFrame",
    "ContratosFrame",
    "EstudiantesFrame",
    "NotasFrame",
]
