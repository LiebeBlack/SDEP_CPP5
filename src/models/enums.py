"""
Enums
Enumeraciones para los modelos de datos

Este módulo define todas las enumeraciones utilizadas en el sistema
para mantener la consistencia y tipado de los datos.
"""

from enum import Enum
from typing import Self


def valores_sql(enum_cls: type[Enum]) -> list[str]:
    """
    Valores de un enum listos para SQLEnum(values_callable=...)

    SQLAlchemy guarda el valor de cada miembro (no su nombre), que es
    justo lo que devuelve este helper evitando repetir la comprensión
    en cada modelo.
    """
    return [item.value if hasattr(item, "value") else str(item) for item in enum_cls]


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

    @classmethod
    def coerce(cls, valor: object) -> Self:
        """
        Normaliza un valor al miembro correspondiente del enum

        Las columnas de los modelos se declaran con el tipo del enum, así
        que al asignarles datos que llegan como texto (formularios,
        configuración o JSON) conviene convertir de una vez: acepta el
        propio miembro, su valor y su nombre.

        Raises:
            ValueError: Si el valor no pertenece al enum
        """
        if isinstance(valor, cls):
            return valor
        texto = str(valor)
        try:
            return cls(texto)
        except ValueError:
            pass
        try:
            return cls[texto.upper()]
        except KeyError:
            raise ValueError(
                f"{texto!r} no es un valor válido de {cls.__name__}"
            ) from None


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
    LIQUIDACION = "liquidacion"


class MetodoPago(BaseEnum):
    """
    Métodos de pago disponibles

    Formas en las que se pueden realizar los pagos a los empleados.
    """

    TRANSFERENCIA = "transferencia"
    EFECTIVO = "efectivo"
    CHEQUE = "cheque"
    DEPOSITO = "deposito"


class RolUsuario(BaseEnum):
    """
    Roles de usuario del sistema

    Determinan qué módulos y acciones puede realizar cada usuario
    en la aplicación.
    """

    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"


class TipoAsistencia(BaseEnum):
    """
    Tipos de registro de asistencia

    Clasifica cada registro diario de jornada, desde la presencia
    normal hasta las ausencias justificadas.
    """

    PRESENTE = "presente"
    TARDANZA = "tardanza"
    AUSENTE = "ausente"
    PERMISO = "permiso"
    VACACIONES = "vacaciones"
    REPOSO = "reposo"
    FERIADO = "feriado"


class TipoJornada(BaseEnum):
    """
    Tipos de jornada laboral

    Determina el recargo aplicable a las horas extra calculadas sobre
    el horario correspondiente.
    """

    DIURNA = "diurna"
    NOCTURNA = "nocturna"
    MIXTA = "mixta"


class TipoContrato(BaseEnum):
    """Tipos de contrato laboral"""

    INDEFINIDO = "indefinido"
    TEMPORAL = "temporal"
    OBRA = "obra"
    PASANTIA = "pasantia"


class EstadoContrato(BaseEnum):
    """Estados del ciclo de vida de un contrato"""

    VIGENTE = "vigente"
    RENOVADO = "renovado"
    VENCIDO = "vencido"
    TERMINADO = "terminado"


class TipoPrestamo(BaseEnum):
    """Tipos de descuento diferido al empleado"""

    ANTICIPO = "anticipo"
    PRESTAMO = "prestamo"


class EstadoPrestamo(BaseEnum):
    """Estados por los que pasa un anticipo o préstamo"""

    SOLICITADO = "solicitado"
    APROBADO = "aprobado"
    ACTIVO = "activo"
    PAGADO = "pagado"
    CANCELADO = "cancelado"


class ModoCalculoNomina(BaseEnum):
    """
    Modo de cálculo de las deducciones de nómina

    PORCENTAJE conserva el cálculo histórico (porcentajes planos de
    configuración) y TRAMOS activa el motor con tabla progresiva de
    ISR, techos de aportes y recargos de horas extra.
    """

    PORCENTAJE = "porcentaje"
    TRAMOS = "tramos"


class SeveridadAlerta(BaseEnum):
    """Severidad de las alertas mostradas al usuario"""

    INFO = "info"
    ADVERTENCIA = "advertencia"
    CRITICA = "critica"
