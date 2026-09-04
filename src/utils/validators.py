from typing import List, Dict, Any
from datetime import date
import re
from src.utils.helpers import parse_date


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
    def validate_type(value: Any, expected_type: Any, field_name: str) -> None:
        """Valida el tipo de un campo"""
        if not isinstance(value, expected_type):
            raise ValidationError(f"El campo '{field_name}' debe ser de tipo {expected_type}")
    
    @staticmethod
    def validate_length(value: str, min_length: int, max_length: int, field_name: str) -> None:
        """Valida la longitud de un string"""
        if len(str(value)) < min_length:
            raise ValidationError(f"El campo '{field_name}' debe tener al menos {min_length} caracteres")
        if len(str(value)) > max_length:
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
            campos_requeridos = ["nombres", "apellidos", "cedula", "tipo_empleado", "cargo", "departamento", "salario_base"]
            for campo in campos_requeridos:
                if campo not in datos or datos[campo] is None or str(datos[campo]).strip() == "":
                    errores.append(f"El campo '{campo}' es requerido")
            
            # Validaciones específicas
            if "cedula" in datos and datos["cedula"]:
                ced_clean = str(datos["cedula"]).replace("-", "").replace(" ", "").strip()
                if not ced_clean.isdigit():
                    errores.append("La cédula debe contener solo números")
                elif len(ced_clean) < 5 or len(ced_clean) > 20:
                    errores.append("La cédula debe tener entre 5 y 20 dígitos")
            
            if "salario_base" in datos and datos["salario_base"] is not None and str(datos["salario_base"]).strip() != "":
                try:
                    sal = float(datos["salario_base"])
                    if sal <= 0:
                        errores.append("El salario base debe ser mayor a 0")
                except (ValueError, TypeError):
                    errores.append("El salario base debe ser un número válido")
            
            if "email" in datos and datos["email"]:
                email_val = str(datos["email"]).strip()
                if email_val and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email_val):
                    errores.append("El formato del email no es válido")
            
            if "fecha_nacimiento" in datos and datos["fecha_nacimiento"]:
                fnac = datos["fecha_nacimiento"] if isinstance(datos["fecha_nacimiento"], date) else parse_date(str(datos["fecha_nacimiento"]))
                if fnac and fnac > date.today():
                    errores.append("La fecha de nacimiento no puede ser futura")
            
            if "fecha_contratacion" in datos and datos["fecha_contratacion"]:
                fcont = datos["fecha_contratacion"] if isinstance(datos["fecha_contratacion"], date) else parse_date(str(datos["fecha_contratacion"]))
                if fcont and fcont > date.today():
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
            campos_requeridos = ["empleado_id", "tipo_documento", "titulo"]
            for campo in campos_requeridos:
                if campo not in datos or datos[campo] is None or str(datos[campo]).strip() == "":
                    errores.append(f"El campo '{campo}' es requerido")
            
            if "empleado_id" in datos and datos["empleado_id"] is not None:
                try:
                    emp_id = int(datos["empleado_id"])
                    if emp_id <= 0:
                        errores.append("El ID de empleado debe ser positivo")
                except (ValueError, TypeError):
                    errores.append("El ID de empleado debe ser un número entero válido")
            
            if "tamano_bytes" in datos and datos["tamano_bytes"]:
                if int(datos["tamano_bytes"]) > 50 * 1024 * 1024:  # 50MB
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
            campos_requeridos = ["empleado_id", "tipo_incidencia", "fecha_inicio", "fecha_fin", "motivo"]
            for campo in campos_requeridos:
                if campo not in datos or datos[campo] is None or str(datos[campo]).strip() == "":
                    errores.append(f"El campo '{campo}' es requerido")
            
            if "empleado_id" in datos and datos["empleado_id"] is not None:
                try:
                    emp_id = int(datos["empleado_id"])
                    if emp_id <= 0:
                        errores.append("El ID de empleado debe ser positivo")
                except (ValueError, TypeError):
                    errores.append("El ID de empleado debe ser un número entero válido")
            
            # Validar fechas
            if "fecha_inicio" in datos and "fecha_fin" in datos:
                ini = datos["fecha_inicio"] if isinstance(datos["fecha_inicio"], date) else parse_date(str(datos["fecha_inicio"]))
                fin = datos["fecha_fin"] if isinstance(datos["fecha_fin"], date) else parse_date(str(datos["fecha_fin"]))
                
                if ini and fin:
                    if fin < ini:
                        errores.append("La fecha fin no puede ser anterior a la fecha inicio")
                elif not ini or not fin:
                    errores.append("Las fechas de inicio y fin deben tener un formato válido (DD/MM/YYYY o YYYY-MM-DD)")
            
            if "dias_solicitados" in datos and datos["dias_solicitados"] is not None:
                try:
                    dias = int(datos["dias_solicitados"])
                    if dias <= 0:
                        errores.append("Los días solicitados deben ser mayores a 0")
                    elif dias > 365:
                        errores.append("Los días solicitados no pueden exceder 365")
                except (ValueError, TypeError):
                    pass
            
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
            campos_requeridos = ["empleado_id", "tipo_pago", "periodo_inicio", "periodo_fin", "salario_base"]
            for campo in campos_requeridos:
                if campo not in datos or datos[campo] is None or str(datos[campo]).strip() == "":
                    errores.append(f"El campo '{campo}' es requerido")
            
            if "empleado_id" in datos and datos["empleado_id"] is not None:
                try:
                    emp_id = int(datos["empleado_id"])
                    if emp_id <= 0:
                        errores.append("El ID de empleado debe ser positivo")
                except (ValueError, TypeError):
                    errores.append("El ID de empleado debe ser un número entero válido")
            
            if "periodo_inicio" in datos and "periodo_fin" in datos:
                ini = datos["periodo_inicio"] if isinstance(datos["periodo_inicio"], date) else parse_date(str(datos["periodo_inicio"]))
                fin = datos["periodo_fin"] if isinstance(datos["periodo_fin"], date) else parse_date(str(datos["periodo_fin"]))
                if ini and fin and fin < ini:
                    errores.append("La fecha fin del periodo no puede ser anterior a la fecha inicio")
            
            if "salario_base" in datos and datos["salario_base"] is not None and str(datos["salario_base"]).strip() != "":
                try:
                    sal = float(datos["salario_base"])
                    if sal <= 0:
                        errores.append("El salario base debe ser mayor a 0")
                except (ValueError, TypeError):
                    errores.append("El salario base debe ser un número válido")
            
            if "monto_bruto" in datos and "monto_neto" in datos and datos["monto_bruto"] is not None and datos["monto_neto"] is not None:
                try:
                    bruto = float(datos["monto_bruto"])
                    neto = float(datos["monto_neto"])
                    if neto > bruto:
                        errores.append("El monto neto no puede ser mayor al monto bruto")
                except (ValueError, TypeError):
                    pass
            
        except Exception as e:
            errores.append(f"Error en validación: {str(e)}")
        
        return errores