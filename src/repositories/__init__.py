"""
Repositories Module
Capa de acceso a datos
"""

from .base_repository import BaseRepository
from .empleado_repository import EmpleadoRepository
from .documento_repository import DocumentoRepository
from .incidencia_repository import IncidenciaRepository
from .pago_repository import PagoRepository
from .configuracion_repository import ConfiguracionRepository
from .usuario_repository import UsuarioRepository

__all__ = [
    "BaseRepository",
    "EmpleadoRepository",
    "DocumentoRepository",
    "IncidenciaRepository",
    "PagoRepository",
    "ConfiguracionRepository",
    "UsuarioRepository"
]