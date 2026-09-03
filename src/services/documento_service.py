"""
Documento Service
Servicio de lógica de negocio para documentos

Este servicio gestiona toda la operativa relacionada con documentos
de empleados, incluyendo carga, almacenamiento, validación y control
de vencimientos.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
import os
import uuid

from src.models import Documento, TipoDocumento
from src.repositories import DocumentoRepository
from src.config import settings


class DocumentoService:
    """
    Servicio de gestión de documentos
    
    Maneja la carga, almacenamiento y gestión de documentos digitales
    de empleados, incluyendo control de vencimientos y validación
    de archivos.
    """
    
    def __init__(self, session: Session):
        """
        Inicializa el servicio de documentos
        
        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self.session = session
        self.repository = DocumentoRepository(session)
    
    def crear_documento(self, datos: Dict, archivo_binario: bytes = None) -> Documento:
        """Crea un nuevo documento"""
        from src.utils.helpers import parse_date
        
        # Normalizar fechas
        fecha_emision = datos.get("fecha_emision")
        if isinstance(fecha_emision, str):
            fecha_emision = parse_date(fecha_emision)
        
        fecha_vencimiento = datos.get("fecha_vencimiento")
        if isinstance(fecha_vencimiento, str):
            fecha_vencimiento = parse_date(fecha_vencimiento)
        
        tipo_doc = datos.get("tipo_documento")
        if hasattr(tipo_doc, 'value'):
            tipo_doc = tipo_doc.value
        
        nombre_archivo = datos.get("nombre_archivo", "documento.pdf")
        
        # Generar nombre único para el archivo
        if archivo_binario:
            extension = self._obtener_extension(nombre_archivo)
            nombre_unico = f"{uuid.uuid4().hex}{extension}"
            ruta_completa = settings.get_document_path(nombre_unico)
            
            # Guardar archivo en disco
            try:
                with open(ruta_completa, 'wb') as f:
                    f.write(archivo_binario)
            except Exception:
                pass
            
            datos["nombre_archivo"] = nombre_unico
            datos["ruta_archivo"] = ruta_completa
            datos["tamano_bytes"] = len(archivo_binario)
            datos["contenido_binario"] = archivo_binario
        else:
            datos["ruta_archivo"] = datos.get("ruta_archivo", "")
        
        documento = Documento(
            empleado_id=int(datos["empleado_id"]),
            tipo_documento=tipo_doc,
            titulo=str(datos["titulo"]).strip(),
            descripcion=datos.get("descripcion"),
            numero_documento=datos.get("numero_documento"),
            fecha_emision=fecha_emision,
            fecha_vencimiento=fecha_vencimiento,
            nombre_archivo=datos.get("nombre_archivo", nombre_archivo),
            ruta_archivo=datos.get("ruta_archivo", ""),
            tamano_bytes=datos.get("tamano_bytes"),
            tipo_mime=datos.get("tipo_mime"),
            contenido_binario=datos.get("contenido_binario"),
            observaciones=datos.get("observaciones")
        )
        
        return self.repository.create(documento)
    
    def actualizar_documento(self, documento_id: int, datos: Dict, archivo_binario: bytes = None) -> Documento:
        """Actualiza un documento existente"""
        from src.utils.helpers import parse_date
        
        documento = self.repository.get_by_id(documento_id)
        if not documento:
            raise ValueError("Documento no encontrado")
        
        # Si se proporciona un nuevo archivo
        if archivo_binario:
            # Eliminar archivo anterior
            if documento.ruta_archivo and os.path.exists(documento.ruta_archivo):
                try:
                    os.remove(documento.ruta_archivo)
                except Exception:
                    pass
            
            extension = self._obtener_extension(datos.get("nombre_archivo", documento.nombre_archivo))
            nombre_unico = f"{uuid.uuid4().hex}{extension}"
            ruta_completa = settings.get_document_path(nombre_unico)
            
            try:
                with open(ruta_completa, 'wb') as f:
                    f.write(archivo_binario)
            except Exception:
                pass
            
            datos["nombre_archivo"] = nombre_unico
            datos["ruta_archivo"] = ruta_completa
            datos["tamano_bytes"] = len(archivo_binario)
            datos["contenido_binario"] = archivo_binario
        
        # Normalizar fechas si vienen en datos
        for f_campo in ["fecha_emision", "fecha_vencimiento"]:
            if f_campo in datos and isinstance(datos[f_campo], str):
                datos[f_campo] = parse_date(datos[f_campo])
        
        if "tipo_documento" in datos and hasattr(datos["tipo_documento"], 'value'):
            datos["tipo_documento"] = datos["tipo_documento"].value
        
        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(documento, campo) and campo != "empleado_id":
                setattr(documento, campo, valor)
        
        return self.repository.update(documento)
    
    def eliminar_documento(self, documento_id: int) -> bool:
        """Elimina un documento (desactivación lógica)"""
        documento = self.repository.get_by_id(documento_id)
        if documento:
            # Eliminar archivo físico
            if documento.ruta_archivo and os.path.exists(documento.ruta_archivo):
                try:
                    os.remove(documento.ruta_archivo)
                except Exception:
                    pass  # Continuar aunque falle la eliminación del archivo
            return self.repository.desactivar(documento_id)
        return False
    
    def obtener_documento(self, documento_id: int) -> Optional[Documento]:
        """Obtiene un documento por ID"""
        return self.repository.get_by_id(documento_id)
    
    def listar_documentos_empleado(self, empleado_id: int) -> List[Documento]:
        """Lista documentos de un empleado"""
        return self.repository.get_by_empleado(empleado_id)
    
    def listar_por_tipo(self, tipo: str) -> List[Documento]:
        """Lista documentos por tipo"""
        return self.repository.get_by_tipo(tipo)
    
    def listar_todas(self) -> List[Documento]:
        """Lista todos los documentos registrados"""
        return self.repository.get_all(limit=None)
    
    def listar_documentos_empleado_tipo(self, empleado_id: int, tipo: str) -> List[Documento]:
        """Lista documentos de un empleado por tipo"""
        return self.repository.get_by_empleado_y_tipo(empleado_id, tipo)
    
    def listar_vencidos(self) -> List[Documento]:
        """Lista documentos vencidos"""
        return self.repository.get_vencidos()
    
    def listar_por_vencer(self, dias: int = 30) -> List[Documento]:
        """Lista documentos por vencer"""
        return self.repository.get_por_vencer(dias)
    
    def obtener_archivo(self, documento_id: int) -> Optional[bytes]:
        """Obtiene el contenido binario de un documento"""
        documento = self.repository.get_by_id(documento_id)
        if documento:
            if documento.contenido_binario:
                return documento.contenido_binario
            elif documento.ruta_archivo and os.path.exists(documento.ruta_archivo):
                with open(documento.ruta_archivo, 'rb') as f:
                    return f.read()
        return None
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de documentos"""
        return {
            "total": self.repository.count(),
            "activos": len(self.repository.get_activos()),
            "vencidos": len(self.repository.get_vencidos()),
            "por_vencer": len(self.repository.get_por_vencer(30)),
            "por_tipo": self.repository.get_estadisticas_por_tipo()
        }
    
    def _obtener_extension(self, nombre_archivo: str) -> str:
        """Obtiene la extensión de un archivo"""
        if "." in nombre_archivo:
            return nombre_archivo[nombre_archivo.rfind("."):]
        return ""
    
    def validar_datos_documento(self, datos: Dict) -> List[str]:
        """Valida los datos de un documento"""
        errores = []
        
        # Validaciones requeridas
        campos_requeridos = ["empleado_id", "tipo_documento", "titulo", "nombre_archivo"]
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f"El campo {campo} es requerido")
        
        # Validaciones específicas
        if "empleado_id" in datos:
            try:
                empleado_id = int(datos["empleado_id"])
                if empleado_id <= 0:
                    errores.append("El ID de empleado debe ser positivo")
            except (ValueError, TypeError):
                errores.append("El ID de empleado debe ser un número válido")
        
        return errores