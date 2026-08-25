"""
Enums
Enumeraciones para los modelos de datos

Este módulo define todas las enumeraciones utilizadas en el sistema
para mantener la consistencia y tipado de los datos.
"""

from enum import Enum


class BaseEnum(str, Enum):
    """Clase base para enums con métodos auxiliares"""
    @classmethod
    def values(cls):
        """Retorna una lista con todos los valores del enum"""
        return [item.value for item in cls]
    
    @classmethod
    def has_value(cls, val):
        """Verifica si un valor existe en el enum"""
        return val in cls.values()


class TipoEmpleado(BaseEnum):
    """
    Tipos de empleados en el sistema
    
    Define las categorías principales de empleados en la institución educativa.
    """
    DOCENTE = "docente"
    ADMINISTRATIVO = "administrativo"
    MANTENIMIENTO = "mantenimiento"


class Genero(BaseEnum):
    """
    Género del empleado
    
    Opciones disponibles para clasificar el género de los empleados.
    """
    MASCULINO = "masculino"
    FEMENINO = "femenino"
    OTRO = "otro"


class EstadoCivil(BaseEnum):
    """
    Estado civil del empleado
    
    Estados civiles reconocidos en el sistema.
    """
    SOLTERO = "soltero"
    CASADO = "casado"
    DIVORCIADO = "divorciado"
    VIUDO = "viudo"
    UNION_LIBRE = "union_libre"


class TipoDocumento(BaseEnum):
    """
    Tipos de documentos gestionados en el sistema
    
    Clasificación de los diferentes tipos de documentos que pueden
    ser cargados para los empleados.
    """
    CEDULA = "cedula"
    TITULO = "titulo"
    REPOSO = "reposo"
    CERTIFICADO = "certificado"
    EXPEDIENTE = "expediente"
    OTRO = "otro"


class TipoIncidencia(BaseEnum):
    """
    Tipos de incidencias que pueden registrarse
    
    Clasificación de las diferentes razones de ausencia o permiso
    que pueden ser registradas en el sistema.
    """
    REPOSO_MEDICO = "reposo_medico"
    AUSENCIA = "ausencia"
    PERMISO = "permiso"
    VACACIONES = "vacaciones"
    LICENCIA = "licencia"


class EstadoIncidencia(BaseEnum):
    """
    Estados por los que puede pasar una incidencia
    
    Flujo de estados en el ciclo de vida de una incidencia desde
    su solicitud hasta su completación.
    """
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    COMPLETADO = "completado"


class TipoPago(BaseEnum):
    """
    Tipos de pagos que se pueden procesar
    
    Clasificación de los diferentes conceptos de pago que se manejan
    en el sistema de nómina.
    """
    SALARIO_BASE = "salario_base"
    BONIFICACION = "bonificacion"
    DESCUENTO = "descuento"
    HORAS_EXTRA = "horas_extra"
    COMISION = "comision"


class MetodoPago(BaseEnum):
    """
    Métodos de pago disponibles
    
    Formas en las que se pueden realizar los pagos a los empleados.
    """
    TRANSFERENCIA = "transferencia"
    EFECTIVO = "efectivo"
    CHEQUE = "cheque"
    DEPOSITO = "deposito"