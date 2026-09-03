"""
Empleado Service
Servicio de lógica de negocio para empleados

Este servicio proporciona toda la lógica de negocio relacionada con la gestión
de empleados, incluyendo creación, actualización, eliminación, búsqueda y
estadísticas.
"""

from typing import List, Optional, Dict, Union, Any
from datetime import date
from sqlalchemy.orm import Session

from src.models import Empleado, TipoEmpleado
from src.repositories import EmpleadoRepository
from src.config import settings


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
    
    def crear_empleado(self, datos: Dict) -> Empleado:
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
        from src.utils.helpers import parse_date
        
        cedula = str(datos.get("cedula", "")).strip()
        if not cedula:
            raise ValueError("La cédula es requerida")
        
        # Validar que la cédula no exista
        if self.repository.get_by_cedula(cedula):
            raise ValueError("Ya existe un empleado con esta cédula")
        
        # Normalizar fechas
        fecha_nac = datos.get("fecha_nacimiento")
        if isinstance(fecha_nac, str):
            fecha_nac = parse_date(fecha_nac)
        
        fecha_cont = datos.get("fecha_contratacion")
        if isinstance(fecha_cont, str):
            fecha_cont = parse_date(fecha_cont) or date.today()
        elif not fecha_cont:
            fecha_cont = date.today()
        
        fecha_term = datos.get("fecha_terminacion")
        if isinstance(fecha_term, str):
            fecha_term = parse_date(fecha_term)
        
        # Normalizar números
        def to_float(val):
            try:
                return float(val) if val is not None and str(val).strip() != "" else None
            except (ValueError, TypeError):
                return None
        
        salario = to_float(datos.get("salario_base"))
        if salario is None:
            raise ValueError("El salario base es requerido y debe ser numérico")
        
        # Crear empleado
        empleado = Empleado(
            nombres=str(datos.get("nombres", "")).strip(),
            apellidos=str(datos.get("apellidos", "")).strip(),
            cedula=cedula,
            fecha_nacimiento=fecha_nac,
            genero=datos.get("genero"),
            estado_civil=datos.get("estado_civil"),
            nacionalidad=datos.get("nacionalidad"),
            peso=to_float(datos.get("peso")),
            altura=to_float(datos.get("altura")),
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
            fecha_contratacion=fecha_cont,
            fecha_terminacion=fecha_term,
            salario_base=salario,
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
            contacto_emergencia_relacion=datos.get("contacto_emergencia_relacion")
        )
        
        return self.repository.create(empleado)
    
    def actualizar_empleado(self, empleado_id: int, datos: Dict) -> Empleado:
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
                    datos[num_campo] = float(datos[num_campo]) if str(datos[num_campo]).strip() != "" else None
                except (ValueError, TypeError):
                    pass
        
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
    
    def obtener_empleado(self, empleado_id: int) -> Optional[Empleado]:
        """Obtiene un empleado por ID"""
        return self.repository.get_by_id(empleado_id)
    
    def obtener_empleado_por_cedula(self, cedula: str) -> Optional[Empleado]:
        """Obtiene un empleado por cédula"""
        return self.repository.get_by_cedula(cedula)
    
    def listar_empleados(self, skip: int = 0, limit: int = 100) -> List[Empleado]:
        """Lista todos los empleados"""
        return self.repository.get_all(skip, limit)
    
    def listar_empleados_activos(self) -> List[Empleado]:
        """Lista solo empleados activos"""
        return self.repository.get_activos()
    
    def listar_por_tipo(self, tipo: Union[str, TipoEmpleado]) -> List[Empleado]:
        """Lista empleados por tipo"""
        return self.repository.get_by_tipo(tipo)
    
    def listar_por_departamento(self, departamento: str) -> List[Empleado]:
        """Lista empleados por departamento"""
        return self.repository.get_by_departamento(departamento)
    
    def buscar_empleados(self, termino: str) -> List[Empleado]:
        """Busca empleados por nombre, apellido o cédula"""
        return self.repository.search_empleados(termino)
    
    def listar_filtrados(self, filtros: Dict) -> List[Empleado]:
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
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas generales de empleados
        
        Genera un resumen estadístico incluyendo total de empleados,
        empleados activos, distribución por tipo y por departamento.
        
        Returns:
            Dict: Diccionario con estadísticas de empleados
        """
        return {
            "total": self.repository.count(),
            "activos": len(self.repository.get_activos()),
            "por_tipo": self.repository.get_estadisticas_por_tipo(),
            "por_departamento": self.repository.get_estadisticas_por_departamento()
        }
    
    def validar_datos_empleado(self, datos: Dict) -> List[str]:
        """Valida los datos de un empleado"""
        errores = []
        
        # Validaciones requeridas
        campos_requeridos = ["nombres", "apellidos", "cedula", "tipo_empleado", "cargo", "departamento", "salario_base"]
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f"El campo {campo} es requerido")
        
        # Validaciones específicas
        if "cedula" in datos:
            if len(datos["cedula"]) < 5:
                errores.append("La cédula debe tener al menos 5 caracteres")
        
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