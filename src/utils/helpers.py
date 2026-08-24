"""
Helpers
Funciones helper y utilidades generales

Este módulo proporciona funciones auxiliares utilizadas en todo
el sistema para formateo, validación y manipulación de datos.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, date
from typing import Optional


def get_resource_path(relative_path: str) -> str:
    """
    Obtiene la ruta absoluta a un recurso, funcionando tanto en desarrollo como en EXE
    """
    try:
        # PyInstaller crea una carpeta temporal en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def format_date(fecha: date, formato: str = "%d/%m/%Y") -> str:
    """
    Formatea una fecha a string
    
    Args:
        fecha: Objeto date a formatear
        formato: Formato de salida (default: DD/MM/YYYY)
        
    Returns:
        str: Fecha formateada o string vacío si fecha es None
    """
    if fecha:
        return fecha.strftime(formato)
    return ""


def parse_date(fecha_str: str, formato: str = "%d/%m/%Y") -> Optional[date]:
    """
    Parsea un string a fecha
    
    Args:
        fecha_str: String con la fecha
        formato: Formato de entrada (default: DD/MM/YYYY)
        
    Returns:
        date: Objeto date o None si hay error
    """
    try:
        return datetime.strptime(fecha_str, formato).date()
    except (ValueError, TypeError):
        return None


def format_currency(monto: float, simbolo: str = "$") -> str:
    """
    Formatea un monto como moneda
    
    Args:
        monto: Valor numérico a formatear
        simbolo: Símbolo de moneda (default: $)
        
    Returns:
        str: Monto formateado con separadores de miles y decimales
    """
    return f"{simbolo}{monto:,.2f}"


def parse_currency(monto_str: str) -> Optional[float]:
    """
    Parsea un string de moneda a float
    
    Args:
        monto_str: String con el monto formateado
        
    Returns:
        float: Valor numérico o None si hay error
    """
    try:
        # Eliminar símbolos de moneda y espacios
        cleaned = monto_str.replace("$", "").replace("€", "").replace("£", "").replace(",", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def format_phone_number(telefono: str) -> str:
    """
    Formatea un número de teléfono
    
    Args:
        telefono: Número de teléfono sin formatear
        
    Returns:
        str: Número formateado según su longitud
    """
    if not telefono:
        return ""
    
    # Eliminar caracteres no numéricos
    cleaned = "".join(c for c in telefono if c.isdigit())
    
    # Formatear según longitud
    if len(cleaned) == 10:
        return f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
    elif len(cleaned) == 7:
        return f"{cleaned[:3]}-{cleaned[3:]}"
    
    return telefono


def validate_cedula(cedula: str) -> bool:
    """
    Valida formato básico de cédula
    
    Args:
        cedula: Número de cédula a validar
        
    Returns:
        bool: True si el formato es válido
    """
    if not cedula:
        return False
    
    # Eliminar guiones y espacios
    cleaned = cedula.replace("-", "").replace(" ", "")
    
    # Verificar que sea numérico y tenga longitud razonable
    return cleaned.isdigit() and 5 <= len(cleaned) <= 20


def validate_email(email: str) -> bool:
    """
    Valida formato básico de email
    
    Args:
        email: Dirección de correo a validar
        
    Returns:
        bool: True si el formato es válido (o es vacío/opcional)
    """
    if not email:
        return True  # Email opcional
    
    # Validación básica
    return "@" in email and "." in email.split("@")[-1]


def calculate_age(fecha_nacimiento: date) -> int:
    """
    Calcula la edad a partir de fecha de nacimiento
    
    Args:
        fecha_nacimiento: Fecha de nacimiento
        
    Returns:
        int: Edad calculada o 0 si fecha es None
    """
    if not fecha_nacimiento:
        return 0
    
    today = date.today()
    return today.year - fecha_nacimiento.year - (
        (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )


def truncate_text(texto: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Trunca un texto a una longitud máxima
    
    Args:
        texto: Texto a truncar
        max_length: Longitud máxima permitida
        suffix: Sufijo a agregar cuando se trunca
        
    Returns:
        str: Texto truncado o original si no excede el máximo
    """
    if not texto or len(texto) <= max_length:
        return texto
    return texto[:max_length - len(suffix)] + suffix


def normalize_string(texto: str) -> str:
    """
    Normaliza un string (elimina espacios extra, mayúsculas, etc.)
    
    Args:
        texto: String a normalizar
        
    Returns:
        str: String normalizado en mayúsculas sin espacios extra
    """
    if not texto:
        return ""
    return " ".join(texto.strip().split()).upper()


def get_file_extension(filename: str) -> str:
    """
    Obtiene la extensión de un archivo
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        str: Extensión del archivo incluyendo el punto
    """
    if "." in filename:
        return filename[filename.rfind("."):].lower()
    return ""


def is_valid_image_file(filename: str) -> bool:
    """
    Verifica si un archivo es una imagen válida
    
    Args:
        filename: Nombre del archivo a verificar
        
    Returns:
        bool: True si es una imagen con extensión válida
    """
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    return get_file_extension(filename) in valid_extensions


def is_valid_pdf_file(filename: str) -> bool:
    """
    Verifica si un archivo es un PDF válido
    
    Args:
        filename: Nombre del archivo a verificar
        
    Returns:
        bool: True si el archivo tiene extensión .pdf
    """
    return get_file_extension(filename) == '.pdf'


def format_file_size(size_bytes: int) -> str:
    """
    Formatea tamaño de archivo en formato legible
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        str: Tamaño formateado en la unidad apropiada
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    División segura que retorna default si el denominador es 0
    
    Args:
        numerator: Numerador de la división
        denominator: Denominador de la división
        default: Valor a retornar si la división no es posible
        
    Returns:
        float: Resultado de la división o valor por defecto
    """
    try:
        if denominator == 0 or denominator is None:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def clean_string(texto: str) -> str:
    """
    Limpia un string de caracteres peligrosos
    
    Args:
        texto: String a limpiar
        
    Returns:
        str: String sin caracteres potencialmente peligrosos
    """
    if not texto:
        return ""
    
    # Eliminar caracteres que podrían ser peligrosos
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')']
    cleaned = texto
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, "")
    
    return cleaned.strip()


def generate_unique_filename(original_filename: str) -> str:
    """
    Genera un nombre de archivo único basado en el original
    
    Args:
        original_filename: Nombre original del archivo
        
    Returns:
        str: Nombre único con UUID manteniendo la extensión
    """
    import uuid
    extension = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}{extension}"


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Asegura que un directorio exista, lo crea si es necesario
    
    Args:
        directory_path: Ruta del directorio a verificar/crear
        
    Returns:
        bool: True si el directorio existe o se creó correctamente
    """
    try:
        Path(directory_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_timestamp() -> str:
    """
    Retorna un timestamp actual formateado
    
    Returns:
        str: Timestamp en formato YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def log_message(message: str, level: str = "INFO") -> None:
    """
    Función simple de logging
    
    Args:
        message: Mensaje a registrar
        level: Nivel de log (INFO, WARNING, ERROR, etc.)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")