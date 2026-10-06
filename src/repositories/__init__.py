"""
Repositories Module
Capa de acceso a datos
"""

from .base_repository import BaseRepository
from .configuracion_repository import ConfiguracionRepository
from .contrato_repository import ContratoRepository
from .documento_repository import DocumentoRepository
from .empleado_repository import EmpleadoRepository
from .estudiante_repository import EstudianteRepository
from .grado_repository import GradoRepository
from .incidencia_repository import IncidenciaRepository
from .matricula_repository import MatriculaRepository
from .nota_final_repository import NotaFinalRepository
from .pago_repository import PagoRepository
from .periodo_academico_repository import PeriodoAcademicoRepository
from .token_sesion_repository import TokenSesionRepository
from .usuario_repository import UsuarioRepository

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
