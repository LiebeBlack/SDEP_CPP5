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
from .asistencia_repository import AsistenciaRepository
from .horario_repository import HorarioRepository
from .contrato_repository import ContratoRepository
from .prestamo_repository import PrestamoRepository

__all__ = [
    "BaseRepository",
    "EmpleadoRepository",
    "DocumentoRepository",
    "IncidenciaRepository",
    "PagoRepository",
    "ConfiguracionRepository",
    "UsuarioRepository",
    "AsistenciaRepository",
    "HorarioRepository",
    "ContratoRepository",
    "PrestamoRepository",
]
