"""
Empleado Service
Servicio de lógica de negocio para empleados

Este servicio proporciona toda la lógica de negocio relacionada con la gestión
de empleados, incluyendo creación, actualización, eliminación, búsqueda y
estadísticas.
"""

from datetime import date
from typing import Any

import logging
from sqlalchemy.orm import Session

from src.models import Empleado, TipoEmpleado
from src.repositories import EmpleadoRepository
from src.utils.helpers import parse_date

logger = logging.getLogger(__name__)


def _a_float_o_none(valor: Any) -> float | None:
    """Convierte a float; vacíos y no numéricos devuelven None"""
    if valor is None or str(valor).strip() == "":
        return None
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def _fecha_normalizada(valor: object) -> date | None:
    """Acepta date o cadena y devuelve date; None si no representa fecha"""
    if valor is None:
        return None
    if isinstance(valor, str):
        return parse_date(valor)
    if isinstance(valor, date):
        return valor
    return None


def _fecha_o_hoy(valor: object) -> date:
    """Acepta date o cadena; cadenas no parseables y vacíos caen a hoy"""
    if isinstance(valor, str):
        return parse_date(valor) or date.today()
    if isinstance(valor, date):
        return valor
    return date.today()


class EmpleadoService:
    """
    Servicio de gestión de empleados

    Este servicio maneja todas las operaciones relacionadas con empleados,
    actuando como intermediario entre la interfaz de usuario y el repositorio
    de datos. Implementa validaciones de negocio y reglas de negocio.
    """

    def __init__(self, session: Session):
        """
        Inicializa el servicio de empleados

        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self.session = session
        self.repository = EmpleadoRepository(session)

    def crear_empleado(self, datos: dict) -> Empleado:
        """
        Crea un nuevo empleado con validaciones

        Este método valida que la cédula no exista en el sistema y crea
        un nuevo registro de empleado con todos los datos proporcionados.

        Args:
            datos: Diccionario con los datos del empleado

        Returns:
            Empleado: Objeto empleado creado

        Raises:
            ValueError: Si la cédula ya existe o faltan datos requeridos
        """
        cedula = str(datos.get("cedula", "")).strip()
        if not cedula:
            raise ValueError("La cédula es requerida")

        # Validar que la cédula no exista
        if self.repository.get_by_cedula(cedula):
            raise ValueError("Ya existe un empleado con esta cédula")

        salario = _a_float_o_none(datos.get("salario_base"))
        if salario is None:
            raise ValueError("El salario base es requerido y debe ser numérico")

        empleado = self._construir_empleado(
            datos,
            cedula=cedula,
            salario_base=salario,
            fecha_nacimiento=_fecha_normalizada(datos.get("fecha_nacimiento")),
            fecha_contratacion=_fecha_o_hoy(datos.get("fecha_contratacion")),
            fecha_terminacion=_fecha_normalizada(datos.get("fecha_terminacion")),
        )
        return self.repository.create(empleado)

    @staticmethod
    def _construir_empleado(
        datos: dict,
        cedula: str,
        salario_base: float,
        fecha_nacimiento: date | None,
        fecha_contratacion: date,
        fecha_terminacion: date | None,
    ) -> Empleado:
        """Construye la entidad Empleado a partir del formulario validado"""
        return Empleado(
            nombres=str(datos.get("nombres", "")).strip(),
            apellidos=str(datos.get("apellidos", "")).strip(),
            cedula=cedula,
            fecha_nacimiento=fecha_nacimiento,
            genero=datos.get("genero"),
            estado_civil=datos.get("estado_civil"),
            nacionalidad=datos.get("nacionalidad"),
            peso=_a_float_o_none(datos.get("peso")),
            altura=_a_float_o_none(datos.get("altura")),
            tipo_sangre=datos.get("tipo_sangre"),
            telefono=datos.get("telefono"),
            celular=datos.get("celular"),
            email=datos.get("email"),
            direccion=datos.get("direccion"),
            ciudad=datos.get("ciudad"),
            estado=datos.get("estado"),
            codigo_postal=datos.get("codigo_postal"),
            tipo_empleado=datos["tipo_empleado"],
            cargo=str(datos.get("cargo", "")).strip(),
            departamento=str(datos.get("departamento", "")).strip(),
            fecha_contratacion=fecha_contratacion,
            fecha_terminacion=fecha_terminacion,
            salario_base=salario_base,
            nivel_educativo=datos.get("nivel_educativo"),
            especialidad=datos.get("especialidad"),
            titulo_obtenido=datos.get("titulo_obtenido"),
            titulo_secundaria=datos.get("titulo_secundaria") or None,
            institucion_bancaria=datos.get("institucion_bancaria") or None,
            numero_cuenta=datos.get("numero_cuenta") or None,
            tipo_cuenta=datos.get("tipo_cuenta") or None,
            carnet_discapacidad=datos.get("carnet_discapacidad") or None,
            enfermedades_preexistentes=datos.get("enfermedades_preexistentes") or None,
            alergias_medicamentosas=datos.get("alergias_medicamentosas") or None,
            alergias_alimentarias=datos.get("alergias_alimentarias") or None,
            tipo_contratacion=datos.get("tipo_contratacion") or None,
            hijos=datos.get("hijos") or None,
            observaciones=datos.get("observaciones"),
            contacto_emergencia_nombre=datos.get("contacto_emergencia_nombre"),
            contacto_emergencia_telefono=datos.get("contacto_emergencia_telefono"),
            contacto_emergencia_relacion=datos.get("contacto_emergencia_relacion"),
        )

    def actualizar_empleado(self, empleado_id: int, datos: dict) -> Empleado:
        """
        Actualiza un empleado existente

        Actualiza la información de un empleado existente, validando que
        no exista conflicto con la cédula si esta se modifica.

        Args:
            empleado_id: ID del empleado a actualizar
            datos: Diccionario con los datos a actualizar

        Returns:
            Empleado: Objeto empleado actualizado

        Raises:
            ValueError: Si el empleado no existe o hay conflicto de cédula
        """
        from src.utils.helpers import parse_date

        empleado = self.repository.get_by_id(empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")

        # Si se actualiza la cédula, verificar que no exista
        if "cedula" in datos and datos["cedula"]:
            nueva_cedula = str(datos["cedula"]).strip()
            if nueva_cedula != empleado.cedula:
                if self.repository.get_by_cedula(nueva_cedula):
                    raise ValueError("Ya existe un empleado con esta cédula")
                datos["cedula"] = nueva_cedula

        # Normalizar fechas si vienen en datos
        for f_campo in ["fecha_nacimiento", "fecha_contratacion", "fecha_terminacion"]:
            if f_campo in datos and isinstance(datos[f_campo], str):
                datos[f_campo] = parse_date(datos[f_campo])

        # Normalizar floats si vienen en datos
        for num_campo in ["salario_base", "peso", "altura"]:
            if num_campo in datos and datos[num_campo] is not None:
                try:
                    datos[num_campo] = (
                        float(datos[num_campo]) if str(datos[num_campo]).strip() != "" else None
                    )
                except (ValueError, TypeError):
                    logger.debug("Campo numérico inválido: %s", num_campo, exc_info=True)

        # Actualizar campos
        for campo, valor in datos.items():
            if campo == "id":
                continue
            if hasattr(empleado, campo):
                setattr(empleado, campo, valor)

        return self.repository.update(empleado)

    def eliminar_empleado(self, empleado_id: int) -> bool:
        """
        Elimina un empleado (desactivación lógica)

        En lugar de eliminar físicamente el registro, este método
        marca el empleado como inactivo, manteniendo el historial.

        Args:
            empleado_id: ID del empleado a desactivar

        Returns:
            bool: True si se desactivó correctamente, False en caso contrario
        """
        return self.repository.desactivar(empleado_id)

    def obtener_empleado(self, empleado_id: int) -> Empleado | None:
        """Obtiene un empleado por ID"""
        return self.repository.get_by_id(empleado_id)

    def obtener_empleado_por_cedula(self, cedula: str) -> Empleado | None:
        """Obtiene un empleado por cédula"""
        return self.repository.get_by_cedula(cedula)

    def listar_empleados(self, skip: int = 0, limit: int = 100) -> list[Empleado]:
        """Lista todos los empleados"""
        return self.repository.get_all(skip, limit)

    def listar_empleados_activos(self) -> list[Empleado]:
        """Lista solo empleados activos"""
        return self.repository.get_activos()

    def listar_por_tipo(self, tipo: str | TipoEmpleado) -> list[Empleado]:
        """Lista empleados por tipo"""
        return self.repository.get_by_tipo(tipo)

    def listar_por_departamento(self, departamento: str) -> list[Empleado]:
        """Lista empleados por departamento"""
        return self.repository.get_by_departamento(departamento)

    def buscar_empleados(self, termino: str) -> list[Empleado]:
        """Busca empleados por nombre, apellido o cédula"""
        return self.repository.search_empleados(termino)

    def listar_filtrados(self, filtros: dict) -> list[Empleado]:
        """Lista empleados con filtros múltiples"""
        return self.repository.get_filtrados(filtros)

    def actualizar_foto(self, empleado_id: int, ruta_foto: str) -> bool:
        """Actualiza la foto de perfil de un empleado"""
        empleado = self.repository.get_by_id(empleado_id)
        if empleado:
            empleado.foto_ruta = ruta_foto
            self.repository.update(empleado)
            return True
        return False

    def obtener_estadisticas(self) -> dict:
        """
        Obtiene estadísticas generales de empleados

        Genera un resumen estadístico incluyendo total de empleados,
        empleados activos, distribución por tipo y por departamento.

        Returns:
            dict: Diccionario con estadísticas de empleados
        """
        return {
            "total": self.repository.count(),
            "activos": len(self.repository.get_activos()),
            "por_tipo": self.repository.get_estadisticas_por_tipo(),
            "por_departamento": self.repository.get_estadisticas_por_departamento(),
        }

    def validar_datos_empleado(self, datos: dict) -> list[str]:
        """Valida los datos de un empleado"""
        errores = []

        # Validaciones requeridas
        campos_requeridos = [
            "nombres",
            "apellidos",
            "cedula",
            "tipo_empleado",
            "cargo",
            "departamento",
            "salario_base",
        ]
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f"El campo {campo} es requerido")

        # Validaciones específicas
        if "cedula" in datos:
            if len(datos["cedula"]) < 5:
                errores.append("La cédula debe tener al menos 5 caracteres")
            # Coherente con los validadores (src/utils/validators.py): la
            # cédula debe ser numérica (se ignoran guiones y espacios).
            ced_limpia = str(datos["cedula"]).replace("-", "").replace(" ", "")
            if not ced_limpia.isdigit():
                errores.append("La cédula debe contener solo números")

        if "salario_base" in datos:
            try:
                salario = float(datos["salario_base"])
                if salario <= 0:
                    errores.append("El salario base debe ser mayor a 0")
            except (ValueError, TypeError):
                errores.append("El salario base debe ser un número válido")

        if "email" in datos and datos["email"]:
            if "@" not in datos["email"]:
                errores.append("El email no es válido")

        return errores
