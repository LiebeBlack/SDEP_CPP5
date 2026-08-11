"""
Enums
Enumeraciones para los modelos de datos
"""

from enum import Enum


class TipoEmpleado(str, Enum):
    """Tipos de empleados"""
    DOCENTE = "docente"
    ADMINISTRATIVO = "administrativo"
    MANTENIMIENTO = "mantenimiento"


class Genero(str, Enum):
    """Género del empleado"""
    MASCULINO = "masculino"
    FEMENINO = "femenino"
    OTRO = "otro"


class EstadoCivil(str, Enum):
    """Estado civil"""
    SOLTERO = "soltero"
    CASADO = "casado"
    DIVORCIADO = "divorciado"
    VIUDO = "viudo"
    UNION_LIBRE = "union_libre"


class TipoDocumento(str, Enum):
    """Tipos de documentos"""
    CEDULA = "cedula"
    TITULO = "titulo"
    REPOSO = "reposo"
    CERTIFICADO = "certificado"
    EXPEDIENTE = "expediente"
    OTRO = "otro"


class TipoIncidencia(str, Enum):
    """Tipos de incidencias"""
    REPOSO_MEDICO = "reposo_medico"
    AUSENCIA = "ausencia"
    PERMISO = "permiso"
    VACACIONES = "vacaciones"
    LICENCIA = "licencia"


class EstadoIncidencia(str, Enum):
    """Estado de incidencias"""
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    COMPLETADO = "completado"


class TipoPago(str, Enum):
    """Tipos de pago"""
    SALARIO_BASE = "salario_base"
    BONIFICACION = "bonificacion"
    DESCUENTO = "descuento"
    HORAS_EXTRA = "horas_extra"
    COMISION = "comision"


class MetodoPago(str, Enum):
    """Métodos de pago"""
    TRANSFERENCIA = "transferencia"
    EFECTIVO = "efectivo"
    CHEQUE = "cheque"
    DEPOSITO = "deposito"