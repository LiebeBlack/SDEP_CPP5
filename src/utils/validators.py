"""
Validators
Funciones de validación de datos
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
import re


class ValidationError(Exception):
    """Excepción para errores de validación"""
    pass


class Validator:
    """Clase base para validadores"""
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """Valida que un campo sea requerido"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"El campo '{field_name}' es requerido")
    
    @staticmethod
    def validate_type(value: Any, expected_type: type, field_name: str) -> None:
        """Valida el tipo de un campo"""
        if not isinstance(value, expected_type):
            raise ValidationError(f"El campo '{field_name}' debe ser de tipo {expected_type.__name__}")
    
    @staticmethod
    def validate_length(value: str, min_length: int, max_length: int, field_name: str) -> None:
        """Valida la longitud de un string"""
        if len(value) < min_length:
            raise ValidationError(f"El campo '{field_name}' debe tener al menos {min_length} caracteres")
        if len(value) > max_length:
            raise ValidationError(f"El campo '{field_name}' no puede exceder {max_length} caracteres")
    
    @staticmethod
    def validate_range(value: float, min_value: float, max_value: float, field_name: str) -> None:
        """Valida el rango de un número"""
        if value < min_value or value > max_value:
            raise ValidationError(f"El campo '{field_name}' debe estar entre {min_value} y {max_value}")
    
    @staticmethod
    def validate_positive(value: float, field_name: str) -> None:
        """Valida que un número sea positivo"""
        if value <= 0:
            raise ValidationError(f"El campo '{field_name}' debe ser mayor a 0")


class EmpleadoValidator(Validator):
    """Validador específico para empleados"""
    
    @staticmethod
    def validate_datos_empleado(datos: Dict[str, Any]) -> List[str]:
        """Valida datos completos de empleado"""
        errores = []
        
        try:
            # Campos requeridos
            campos_requeridos = {
                "nombres": (str, 2, 100),
                "apellidos": (str, 2, 100),
                "cedula": (str, 5, 20),
                "tipo_empleado": (str, 1, 50),
                "cargo": (str, 2, 100),
                "departamento": (str, 2, 100),
                "salario_base": (float, 0, 1000000)
            }
            
            for campo, (tipo, min_len, max_len) in campos_requeridos.items():
                if campo not in datos or not datos[campo]:
                    errores.append(f"El campo '{campo}' es requerido")
                    continue
                
                try:
                    if tipo == str:
                        EmpleadoValidator.validate_type(datos[campo], str, campo)
                        EmpleadoValidator.validate_length(datos[campo], min_len, max_len, campo)
                    elif tipo == float:
                        EmpleadoValidator.validate_type(datos[campo], (int, float), campo)
                        EmpleadoValidator.validate_positive(float(datos[campo]), campo)
                except ValidationError as e:
                    errores.append(str(e))
            
            # Validaciones específicas
            if "cedula" in datos:
                if not datos["cedula"].replace("-", "").replace(" ", "").isdigit():
                    errores.append("La cédula debe contener solo números")
            
            if "email" in datos and datos["email"]:
                if not re.match(r'^[^@]+@[^@]+\.[^@]+$', datos["email"]):
                    errores.append("El formato del email no es válido")
            
            if "fecha_nacimiento" in datos and datos["fecha_nacimiento"]:
                if datos["fecha_nacimiento"] > date.today():
                    errores.append("La fecha de nacimiento no puede ser futura")
            
            if "fecha_contratacion" in datos and datos["fecha_contratacion"]:
                if datos["fecha_contratacion"] > date.today():
                    errores.append("La fecha de contratación no puede ser futura")
            
        except Exception as e:
            errores.append(f"Error en validación: {str(e)}")
        
        return errores


class DocumentoValidator(Validator):
    """Validador específico para documentos"""
    
    @staticmethod
    def validate_datos_documento(datos: Dict[str, Any]) -> List[str]:
        """Valida datos completos de documento"""
        errores = []
        
        try:
            # Campos requeridos
            campos_requeridos = {
                "empleado_id": (int, 1, 1000000),
                "tipo_documento": (str, 1, 50),
                "titulo": (str, 2, 200),
                "nombre_archivo": (str, 1, 255)
            }
            
            for campo, (tipo, min_len, max_len) in campos_requeridos.items():
                if campo not in datos or not datos[campo]:
                    errores.append(f"El campo '{campo}' es requerido")
                    continue
                
                try:
                    if tipo == str:
                        DocumentoValidator.validate_type(datos[campo], str, campo)
                        DocumentoValidator.validate_length(datos[campo], min_len, max_len, campo)
                    elif tipo == int:
                        DocumentoValidator.validate_type(datos[campo], int, campo)
                        DocumentoValidator.validate_positive(datos[campo], campo)
                except ValidationError as e:
                    errores.append(str(e))
            
            # Validaciones específicas
            if "fecha_vencimiento" in datos and datos["fecha_vencimiento"]:
                if datos["fecha_vencimiento"] < date.today():
                    errores.append("La fecha de vencimiento no puede ser pasada")
            
            if "tamano_bytes" in datos and datos["tamano_bytes"]:
                if datos["tamano_bytes"] > 50 * 1024 * 1024:  # 50MB
                    errores.append("El archivo no puede exceder 50MB")
            
        except Exception as e:
            errores.append(f"Error en validación: {str(e)}")
        
        return errores


class IncidenciaValidator(Validator):
    """Validador específico para incidencias"""
    
    @staticmethod
    def validate_datos_incidencia(datos: Dict[str, Any]) -> List[str]:
        """Valida datos completos de incidencia"""
        errores = []
        
        try:
            # Campos requeridos
            campos_requeridos = {
                "empleado_id": (int, 1, 1000000),
                "tipo_incidencia": (str, 1, 50),
                "fecha_inicio": (date, 0, 0),
                "fecha_fin": (date, 0, 0),
                "motivo": (str, 5, 500)
            }
            
            for campo, (tipo, min_len, max_len) in campos_requeridos.items():
                if campo not in datos or not datos[campo]:
                    errores.append(f"El campo '{campo}' es requerido")
                    continue
                
                try:
                    if tipo == str:
                        IncidenciaValidator.validate_type(datos[campo], str, campo)
                        IncidenciaValidator.validate_length(datos[campo], min_len, max_len, campo)
                    elif tipo == int:
                        IncidenciaValidator.validate_type(datos[campo], int, campo)
                        IncidenciaValidator.validate_positive(datos[campo], campo)
                    elif tipo == date:
                        IncidenciaValidator.validate_type(datos[campo], date, campo)
                except ValidationError as e:
                    errores.append(str(e))
            
            # Validaciones específicas
            if "fecha_inicio" in datos and "fecha_fin" in datos:
                if datos["fecha_fin"] < datos["fecha_inicio"]:
                    errores.append("La fecha fin debe ser posterior a la fecha inicio")
                
                if datos["fecha_inicio"] < date.today():
                    errores.append("La fecha inicio no puede ser pasada")
            
            if "dias_solicitados" in datos and datos["dias_solicitados"]:
                if datos["dias_solicitados"] <= 0:
                    errores.append("Los días solicitados deben ser mayores a 0")
                if datos["dias_solicitados"] > 365:
                    errores.append("Los días solicitados no pueden exceder 365")
            
        except Exception as e:
            errores.append(f"Error en validación: {str(e)}")
        
        return errores


class PagoValidator(Validator):
    """Validador específico para pagos"""
    
    @staticmethod
    def validate_datos_pago(datos: Dict[str, Any]) -> List[str]:
        """Valida datos completos de pago"""
        errores = []
        
        try:
            # Campos requeridos
            campos_requeridos = {
                "empleado_id": (int, 1, 1000000),
                "tipo_pago": (str, 1, 50),
                "periodo_inicio": (date, 0, 0),
                "periodo_fin": (date, 0, 0),
                "salario_base": (float, 0, 1000000)
            }
            
            for campo, (tipo, min_len, max_len) in campos_requeridos.items():
                if campo not in datos or not datos[campo]:
                    errores.append(f"El campo '{campo}' es requerido")
                    continue
                
                try:
                    if tipo == str:
                        PagoValidator.validate_type(datos[campo], str, campo)
                        PagoValidator.validate_length(datos[campo], min_len, max_len, campo)
                    elif tipo == int:
                        PagoValidator.validate_type(datos[campo], int, campo)
                        PagoValidator.validate_positive(datos[campo], campo)
                    elif tipo == float:
                        PagoValidator.validate_type(datos[campo], (int, float), campo)
                        PagoValidator.validate_positive(float(datos[campo]), campo)
                    elif tipo == date:
                        PagoValidator.validate_type(datos[campo], date, campo)
                except ValidationError as e:
                    errores.append(str(e))
            
            # Validaciones específicas
            if "periodo_inicio" in datos and "periodo_fin" in datos:
                if datos["periodo_fin"] < datos["periodo_inicio"]:
                    errores.append("La fecha fin del periodo debe ser posterior a la fecha inicio")
            
            if "monto_bruto" in datos and "monto_neto" in datos:
                if datos["monto_neto"] > datos["monto_bruto"]:
                    errores.append("El monto neto no puede ser mayor al monto bruto")
            
        except Exception as e:
            errores.append(f"Error en validación: {str(e)}")
        
        return errores