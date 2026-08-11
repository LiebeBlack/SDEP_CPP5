"""
Documento Repository
Repositorio para operaciones de datos de documentos
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models import Documento, TipoDocumento
from .base_repository import BaseRepository


class DocumentoRepository(BaseRepository[Documento]):
    """Repositorio de documentos"""
    
    def __init__(self, session: Session):
        super().__init__(Documento, session)
    
    def get_by_empleado(self, empleado_id: int) -> List[Documento]:
        """Obtiene documentos de un empleado"""
        return self.session.query(Documento).filter(
            Documento.empleado_id == empleado_id
        ).all()
    
    def get_by_tipo(self, tipo: str) -> List[Documento]:
        """Obtiene documentos por tipo"""
        return self.session.query(Documento).filter(
            Documento.tipo_documento == tipo
        ).all()
    
    def get_by_empleado_y_tipo(self, empleado_id: int, tipo: str) -> List[Documento]:
        """Obtiene documentos de un empleado por tipo"""
        return self.session.query(Documento).filter(
            and_(
                Documento.empleado_id == empleado_id,
                Documento.tipo_documento == tipo
            )
        ).all()
    
    def get_activos(self) -> List[Documento]:
        """Obtiene solo documentos activos"""
        return self.session.query(Documento).filter(Documento.activo == 1).all()
    
    def get_activos_by_empleado(self, empleado_id: int) -> List[Documento]:
        """Obtiene documentos activos de un empleado"""
        return self.session.query(Documento).filter(
            and_(
                Documento.empleado_id == empleado_id,
                Documento.activo == 1
            )
        ).all()
    
    def get_vencidos(self) -> List[Documento]:
        """Obtiene documentos vencidos"""
        from datetime import datetime
        return self.session.query(Documento).filter(
            and_(
                Documento.fecha_vencimiento.isnot(None),
                Documento.fecha_vencimiento < datetime.now().date()
            )
        ).all()
    
    def get_por_vencer(self, dias: int = 30) -> List[Documento]:
        """Obtiene documentos por vencer en X días"""
        from datetime import datetime, timedelta
        fecha_limite = datetime.now().date() + timedelta(days=dias)
        return self.session.query(Documento).filter(
            and_(
                Documento.fecha_vencimiento.isnot(None),
                Documento.fecha_vencimiento <= fecha_limite,
                Documento.fecha_vencimiento >= datetime.now().date()
            )
        ).all()
    
    def desactivar(self, id: int) -> bool:
        """Desactiva un documento"""
        documento = self.get_by_id(id)
        if documento:
            documento.activo = 0
            self.session.commit()
            return True
        return False
    
    def activar(self, id: int) -> bool:
        """Activa un documento"""
        documento = self.get_by_id(id)
        if documento:
            documento.activo = 1
            self.session.commit()
            return True
        return False
    
    def get_estadisticas_por_tipo(self) -> dict:
        """Obtiene estadísticas de documentos por tipo"""
        stats = {}
        documentos = self.get_activos()
        for doc in documentos:
            tipo = doc.tipo_documento
            stats[tipo] = stats.get(tipo, 0) + 1
        return stats