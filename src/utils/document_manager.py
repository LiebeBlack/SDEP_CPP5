"""
Document Manager
Módulo de gestión documental
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import datetime
import mimetypes

from src.config import settings
from src.utils.helpers import (
    get_file_extension, is_valid_image_file, is_valid_pdf_file,
    generate_unique_filename, ensure_directory_exists, format_file_size
)


class DocumentManager:
    """Gestor de documentos y archivos"""
    
    def __init__(self):
        self.documents_dir = settings.documents_path
        self.photos_dir = settings.photos_path
        self.exports_dir = settings.exports_path
        
        # Asegurar que los directorios existan
        ensure_directory_exists(self.documents_dir)
        ensure_directory_exists(self.photos_dir)
        ensure_directory_exists(self.exports_dir)
    
    def save_document(self, file_content: bytes, original_filename: str, 
                      category: str = "general") -> Tuple[str, str]:
        """
        Guarda un documento en el sistema de archivos
        
        Args:
            file_content: Contenido binario del archivo
            original_filename: Nombre original del archivo
            category: Categoría para organizar documentos
            
        Returns:
            Tuple[ruta_completa, nombre_unico]
        """
        # Crear directorio de categoría si no existe
        category_dir = os.path.join(self.documents_dir, category)
        ensure_directory_exists(category_dir)
        
        # Generar nombre único
        unique_filename = generate_unique_filename(original_filename)
        file_path = os.path.join(category_dir, unique_filename)
        
        # Guardar archivo
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path, unique_filename
    
    def save_photo(self, file_content: bytes, original_filename: str,
                  employee_id: int) -> Tuple[str, str]:
        """
        Guarda una foto de perfil de empleado
        
        Args:
            file_content: Contenido binario de la imagen
            original_filename: Nombre original del archivo
            employee_id: ID del empleado
            
        Returns:
            Tuple[ruta_completa, nombre_unico]
        """
        # Crear directorio de empleado si no existe
        employee_dir = os.path.join(self.photos_dir, str(employee_id))
        ensure_directory_exists(employee_dir)
        
        # Generar nombre único
        unique_filename = generate_unique_filename(original_filename)
        file_path = os.path.join(employee_dir, unique_filename)
        
        # Guardar archivo
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path, unique_filename
    
    def get_document(self, file_path: str) -> Optional[bytes]:
        """
        Obtiene el contenido de un documento
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Contenido binario del archivo o None si no existe
        """
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return f.read()
        return None
    
    def delete_document(self, file_path: str) -> bool:
        """
        Elimina un documento del sistema de archivos
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # Eliminar directorio si está vacío
                parent_dir = os.path.dirname(file_path)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                return True
            return False
        except Exception:
            return False
    
    def copy_document(self, source_path: str, destination_path: str) -> bool:
        """
        Copia un documento a otra ubicación
        
        Args:
            source_path: Ruta de origen
            destination_path: Ruta de destino
            
        Returns:
            True si se copió correctamente, False en caso contrario
        """
        try:
            ensure_directory_exists(os.path.dirname(destination_path))
            shutil.copy2(source_path, destination_path)
            return True
        except Exception:
            return False
    
    def move_document(self, source_path: str, destination_path: str) -> bool:
        """
        Mueve un documento a otra ubicación
        
        Args:
            source_path: Ruta de origen
            destination_path: Ruta de destino
            
        Returns:
            True si se movió correctamente, False en caso contrario
        """
        try:
            ensure_directory_exists(os.path.dirname(destination_path))
            shutil.move(source_path, destination_path)
            return True
        except Exception:
            return False
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        Obtiene información de un archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Diccionario con información del archivo o None si no existe
        """
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "extension": get_file_extension(file_path),
            "mime_type": mime_type,
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "is_image": is_valid_image_file(file_path),
            "is_pdf": is_valid_pdf_file(file_path)
        }
    
    def list_documents(self, category: str = None) -> List[dict]:
        """
        Lista documentos en una categoría
        
        Args:
            category: Categoría a listar (None para todas)
            
        Returns:
            Lista de diccionarios con información de archivos
        """
        documents = []
        
        if category:
            search_dir = os.path.join(self.documents_dir, category)
            if not os.path.exists(search_dir):
                return documents
        else:
            search_dir = self.documents_dir
        
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_info = self.get_file_info(file_path)
                if file_info:
                    documents.append(file_info)
        
        return documents
    
    def list_employee_photos(self, employee_id: int) -> List[dict]:
        """
        Lista fotos de un empleado
        
        Args:
            employee_id: ID del empleado
            
        Returns:
            Lista de diccionarios con información de archivos
        """
        photos = []
        employee_dir = os.path.join(self.photos_dir, str(employee_id))
        
        if not os.path.exists(employee_dir):
            return photos
        
        for file in os.listdir(employee_dir):
            file_path = os.path.join(employee_dir, file)
            file_info = self.get_file_info(file_path)
            if file_info and file_info["is_image"]:
                photos.append(file_info)
        
        return photos
    
    def get_document_url(self, file_path: str) -> str:
        """
        Genera una URL para acceder al documento
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            URL del documento
        """
        return f"file:///{file_path.replace(os.sep, '/')}"
    
    def validate_file(self, file_content: bytes, filename: str, 
                     max_size_mb: int = 50) -> Tuple[bool, str]:
        """
        Valida un archivo antes de guardarlo
        
        Args:
            file_content: Contenido binario del archivo
            filename: Nombre del archivo
            max_size_mb: Tamaño máximo en MB
            
        Returns:
            Tuple[es_valido, mensaje_error]
        """
        # Validar tamaño
        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"El archivo excede el tamaño máximo de {max_size_mb}MB"
        
        # Validar tipo de archivo
        extension = get_file_extension(filename)
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.doc', '.docx', '.xls', '.xlsx']
        
        if extension not in valid_extensions:
            return False, f"Tipo de archivo no permitido. Extensiones válidas: {', '.join(valid_extensions)}"
        
        return True, ""
    
    def export_file(self, file_content: bytes, filename: str, 
                    export_category: str = "exports") -> Tuple[str, str]:
        """
        Exporta un archivo al directorio de exports
        
        Args:
            file_content: Contenido binario del archivo
            filename: Nombre del archivo
            export_category: Subcategoría de exportación
            
        Returns:
            Tuple[ruta_completa, nombre_unico]
        """
        category_dir = os.path.join(self.exports_dir, export_category)
        ensure_directory_exists(category_dir)
        
        unique_filename = generate_unique_filename(filename)
        file_path = os.path.join(category_dir, unique_filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path, unique_filename
    
    def cleanup_old_files(self, days: int = 30) -> int:
        """
        Limpia archivos antiguos
        
        Args:
            days: Días de antigüedad para eliminar archivos
            
        Returns:
            Cantidad de archivos eliminados
        """
        count = 0
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for directory in [self.documents_dir, self.photos_dir, self.exports_dir]:
            if not os.path.exists(directory):
                continue
            
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            count += 1
                        except Exception:
                            pass
        
        return count
    
    def get_storage_stats(self) -> dict:
        """
        Obtiene estadísticas de almacenamiento
        
        Returns:
            Diccionario con estadísticas
        """
        def get_dir_size(directory):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        
        def count_files(directory):
            count = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                count += len(filenames)
            return count
        
        documents_size = get_dir_size(self.documents_dir)
        photos_size = get_dir_size(self.photos_dir)
        exports_size = get_dir_size(self.exports_dir)
        total_size = documents_size + photos_size + exports_size
        
        return {
            "documents_size": documents_size,
            "documents_size_formatted": format_file_size(documents_size),
            "photos_size": photos_size,
            "photos_size_formatted": format_file_size(photos_size),
            "exports_size": exports_size,
            "exports_size_formatted": format_file_size(exports_size),
            "total_size": total_size,
            "total_size_formatted": format_file_size(total_size),
            "documents_count": count_files(self.documents_dir),
            "photos_count": count_files(self.photos_dir)
        }


# Instancia global del gestor de documentos
document_manager = DocumentManager()