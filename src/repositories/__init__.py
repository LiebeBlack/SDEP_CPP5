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
from .contrato_repository import ContratoRepository
from .estudiante_repository import EstudianteRepository
from .periodo_academico_repository import PeriodoAcademicoRepository
from .grado_repository import GradoRepository
from .matricula_repository import MatriculaRepository
from .nota_final_repository import NotaFinalRepository
from .token_sesion_repository import TokenSesionRepository

__all__ = [
    "BaseRepository",
    "EmpleadoRepository",
    "DocumentoRepository",
    "IncidenciaRepository",
    "PagoRepository",
    "ConfiguracionRepository",
    "UsuarioRepository",
    "ContratoRepository",
    "EstudianteRepository",
    "PeriodoAcademicoRepository",
    "GradoRepository",
    "MatriculaRepository",
    "NotaFinalRepository",
    "TokenSesionRepository",
]
