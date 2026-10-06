"""
Document Manager
Módulo de gestión documental
"""

import logging
import mimetypes
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from src.config import settings
from src.utils.helpers import (
    EXTENSIONES_ABRIBLES,
    ensure_directory_exists,
    escribir_archivo_seguro,
    format_file_size,
    generate_unique_filename,
    get_file_extension,
    is_valid_image_file,
    is_valid_pdf_file,
    leer_archivo_seguro,
    ruta_dentro_de,
)

logger = logging.getLogger(__name__)


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

    def save_document(
        self, file_content: bytes, original_filename: str, category: str = "general"
    ) -> tuple[str, str]:
        """
        Guarda un documento en el sistema de archivos

        Args:
            file_content: Contenido binario del archivo
            original_filename: Nombre original del archivo
            category: Categoría para organizar documentos

        Returns:
            tuple[ruta_completa, nombre_unico]
        """
        # Crear directorio de categoría si no existe. La categoría es un
        # único segmento de directorio: se valida para que no pueda salir
        # del almacén documental con separadores o '..'.
        if not category or Path(category).name != category or category in (".", ".."):
            raise ValueError(f"Categoría de documento no válida: {category!r}")
        category_dir = os.path.join(self.documents_dir, category)
        ensure_directory_exists(category_dir)

        # Generar nombre único
        unique_filename = generate_unique_filename(original_filename)
        file_path = os.path.join(category_dir, unique_filename)

        # Guardar archivo (con reintentos ante bloqueos transitorios)
        if not escribir_archivo_seguro(file_path, file_content):
            raise OSError(f"No se pudo escribir el documento: {file_path}")

        return file_path, unique_filename

    def save_photo(
        self, file_content: bytes, original_filename: str, employee_id: int
    ) -> tuple[str, str]:
        """
        Guarda una foto de perfil de empleado

        Args:
            file_content: Contenido binario de la imagen
            original_filename: Nombre original del archivo
            employee_id: ID del empleado

        Returns:
            tuple[ruta_completa, nombre_unico]
        """
        # Crear directorio de empleado si no existe. El identificador debe
        # ser numérico: un valor con separadores escribiría fuera del
        # directorio de fotografías.
        try:
            employee_dir_name = str(int(employee_id))
        except (TypeError, ValueError) as e:
            raise ValueError(f"Identificador de empleado no válido: {employee_id!r}") from e
        employee_dir = os.path.join(self.photos_dir, employee_dir_name)
        ensure_directory_exists(employee_dir)

        # Generar nombre único
        unique_filename = generate_unique_filename(original_filename)
        file_path = os.path.join(employee_dir, unique_filename)

        # Guardar archivo (con reintentos ante bloqueos transitorios)
        if not escribir_archivo_seguro(file_path, file_content):
            raise OSError(f"No se pudo escribir la foto: {file_path}")

        return file_path, unique_filename

    def ruta_gestionada(self, file_path: str) -> bool:
        """
        Indica si una ruta pertenece a alguno de los directorios gestionados

        Es la contención que separa las rutas que el sistema puede leer,
        borrar o abrir de las que solo existen en la base de datos por un
        error o una manipulación.

        Args:
            file_path: Ruta a comprobar

        Returns:
            bool: True si la ruta está dentro de documentos, fotos o exportaciones
        """
        if not file_path:
            return False
        return any(
            ruta_dentro_de(base, file_path)
            for base in (self.documents_dir, self.photos_dir, self.exports_dir)
        )

    def ruta_abrible(self, file_path: str) -> bool:
        """
        Indica si una ruta puede entregarse a la aplicación predeterminada

        Además de estar dentro de un directorio gestionado (o del directorio
        temporal del sistema, usado para los documentos servidos desde la
        base de datos), el archivo debe existir y tener una extensión
        permitida: así un registro manipulado no puede provocar la ejecución
        de un binario o un script.

        Args:
            file_path: Ruta a comprobar

        Returns:
            bool: True si es seguro abrirla
        """
        if not file_path or not os.path.isfile(file_path):
            return False

        import tempfile

        ubicaciones = (self.documents_dir, self.photos_dir, self.exports_dir, tempfile.gettempdir())
        if not any(ruta_dentro_de(base, file_path) for base in ubicaciones):
            logger.warning("Intento de abrir una ruta fuera de las permitidas: %s", file_path)
            return False

        return get_file_extension(file_path) in EXTENSIONES_ABRIBLES

    def get_document(self, file_path: str) -> bytes | None:
        """
        Obtiene el contenido de un documento

        Args:
            file_path: Ruta del archivo

        Returns:
            Contenido binario del archivo o None si no existe o está fuera
            de los directorios gestionados
        """
        if not self.ruta_gestionada(file_path):
            logger.warning("Lectura rechazada fuera del almacén documental: %s", file_path)
            return None
        if os.path.exists(file_path):
            return leer_archivo_seguro(file_path)
        return None

    def delete_document(self, file_path: str) -> bool:
        """
        Elimina un documento del sistema de archivos

        Args:
            file_path: Ruta del archivo

        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        if not self.ruta_gestionada(file_path):
            logger.warning("Borrado rechazado fuera del almacén documental: %s", file_path)
            return False
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                # Eliminar directorio si está vacío
                parent_dir = os.path.dirname(file_path)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                return True
            return False
        except OSError:
            # Un fallo silencioso dejaría el archivo en disco y al registro
            # apuntando a él; se registra para poder diagnosticarlo.
            logger.warning("No se pudo eliminar el documento %s", file_path, exc_info=True)
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
        if not self.ruta_gestionada(source_path):
            # El origen sí debe estar dentro del almacén: permitir copiar desde
            # fuera introduciría en el gestor documental cualquier archivo del
            # sistema (o el contenido de un dispositivo) sin control. El destino
            # no se restringe porque solo lo fija el código que llama -igual que
            # en `export_file`- y su propósito declarado es copiar "a otra
            # ubicación".
            logger.warning(
                "Copia rechazada: el origen no está en el almacén (%s)",
                source_path,
            )
            return False
        try:
            ensure_directory_exists(os.path.dirname(destination_path))
            shutil.copy2(source_path, destination_path)
            return True
        except OSError:
            logger.warning(
                "No se pudo copiar %s a %s", source_path, destination_path, exc_info=True
            )
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
        if not self.ruta_gestionada(source_path):
            # Igual que en `copy_document`: se protege el origen, no el destino.
            logger.warning(
                "Movimiento rechazado: el origen no está en el almacén (%s)",
                source_path,
            )
            return False
        try:
            ensure_directory_exists(os.path.dirname(destination_path))
            shutil.move(source_path, destination_path)
            return True
        except OSError:
            logger.warning("No se pudo mover %s a %s", source_path, destination_path, exc_info=True)
            return False

    def get_file_info(self, file_path: str) -> dict | None:
        """
        Obtiene información de un archivo

        Args:
            file_path: Ruta del archivo

        Returns:
            Diccionario con información del archivo, o None si no existe o
            está fuera de los directorios gestionados
        """
        if not self.ruta_gestionada(file_path):
            return None
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
            "is_pdf": is_valid_pdf_file(file_path),
        }

    def list_documents(self, category: str | None = None) -> list[dict]:
        """
        Lista documentos en una categoría

        Args:
            category: Categoría a listar (None para todas)

        Returns:
            Lista de diccionarios con información de archivos
        """
        documents: list[dict[str, Any]] = []

        if category:
            if Path(category).name != category or category in (".", ".."):
                return documents
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

    def list_employee_photos(self, employee_id: int) -> list[dict]:
        """
        Lista fotos de un empleado

        Args:
            employee_id: ID del empleado

        Returns:
            Lista de diccionarios con información de archivos
        """
        photos: list[dict[str, Any]] = []
        try:
            employee_dir = os.path.join(self.photos_dir, str(int(employee_id)))
        except (TypeError, ValueError):
            return photos

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

    def validate_file(
        self, file_content: bytes, filename: str, max_size_mb: int = 50
    ) -> tuple[bool, str]:
        """
        Valida un archivo antes de guardarlo

        Args:
            file_content: Contenido binario del archivo
            filename: Nombre del archivo
            max_size_mb: Tamaño máximo en MB

        Returns:
            tuple[es_valido, mensaje_error]
        """
        # Validar tamaño
        size_mb = len(file_content) / (1024 * 1024)
        if size_mb > max_size_mb:
            return False, f"El archivo excede el tamaño máximo de {max_size_mb}MB"

        # Validar tipo de archivo
        extension = get_file_extension(filename)
        valid_extensions = [
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
        ]

        if extension not in valid_extensions:
            return (
                False,
                f"Tipo de archivo no permitido. Extensiones válidas: {', '.join(valid_extensions)}",
            )

        return True, ""

    def export_file(
        self, file_content: bytes, filename: str, export_category: str = "exports"
    ) -> tuple[str, str]:
        """
        Exporta un archivo al directorio de exports

        Args:
            file_content: Contenido binario del archivo
            filename: Nombre del archivo
            export_category: Subcategoría de exportación

        Returns:
            tuple[ruta_completa, nombre_unico]
        """
        if (
            not export_category
            or Path(export_category).name != export_category
            or export_category in (".", "..")
        ):
            # '..' satisface Path('..').name == '..' y escaparía del
            # directorio de exportaciones: se rechaza de forma explícita.
            raise ValueError(f"Categoría de exportación no válida: {export_category!r}")
        category_dir = os.path.join(self.exports_dir, export_category)
        ensure_directory_exists(category_dir)

        unique_filename = generate_unique_filename(filename)
        file_path = os.path.join(category_dir, unique_filename)

        if not escribir_archivo_seguro(file_path, file_content):
            raise OSError(f"No se pudo exportar el archivo: {file_path}")

        return file_path, unique_filename

    def cleanup_old_files(self, days: int = 30, incluir_almacen_documental: bool = False) -> int:
        """
        Limpia archivos antiguos de las carpetas de trabajo

        Por omisión solo barre las exportaciones y los temporales de la
        aplicación: los documentos y las fotografías son datos del usuario a
        los que apunta la base de datos, y borrarlos por fecha de
        modificación dejaría registros activos sin archivo. El almacén
        documental solo se limpia si el llamador lo pide expresamente.

        Args:
            days: Días de antigüedad para eliminar archivos
            incluir_almacen_documental: barre también documentos y fotografías

        Returns:
            Cantidad de archivos eliminados
        """
        directorios = [self.exports_dir, settings.temp_dir]
        if incluir_almacen_documental:
            directorios.extend([self.documents_dir, self.photos_dir])
        return self._purgar_antiguos(directorios, days)

    def limpiar_temporales(self, days: int = 1) -> int:
        """
        Purga los temporales que dejó una ejecución anterior

        ReportLab, las previsualizaciones y las pruebas de escritura viven en
        ``tmp/`` dentro de la carpeta de datos. Nada de ahí debe sobrevivir a
        un arranque, así que se eliminan los archivos con más de un día: el
        margen evita borrar los de otra instancia abierta en paralelo.

        Args:
            days: Días de antigüedad a partir de los cuales se elimina

        Returns:
            Cantidad de archivos eliminados
        """
        return self._purgar_antiguos([settings.temp_dir], days)

    @staticmethod
    def _purgar_antiguos(directorios: list[str], days: int) -> int:
        """Elimina de las carpetas indicadas los archivos con más de `days` días"""
        eliminados = 0
        limite = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for directory in directorios:
            if not os.path.isdir(directory):
                continue
            for root, _dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getmtime(file_path) >= limite:
                            continue
                        os.remove(file_path)
                        eliminados += 1
                    except OSError:
                        # Archivo en uso por un visor u otro proceso: se deja
                        # para la próxima pasada en lugar de abortar la limpieza.
                        logger.debug("No se pudo limpiar %s", file_path, exc_info=True)

        return eliminados

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
            "photos_count": count_files(self.photos_dir),
        }


# Instancia global del gestor de documentos
document_manager = DocumentManager()
