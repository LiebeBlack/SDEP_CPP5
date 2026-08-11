"""
Empleado Service
Servicio de lógica de negocio para empleados
"""

from typing import List, Optional, Dict
from datetime import date
from sqlalchemy.orm import Session

from src.models import Empleado, TipoEmpleado
from src.repositories import EmpleadoRepository
from src.config import settings


class EmpleadoService:
    """Servicio de gestión de empleados"""
    
    def __init__(self, session: Session):
        self.session = session
        self.repository = EmpleadoRepository(session)
    
    def crear_empleado(self, datos: Dict) -> Empleado:
        """Crea un nuevo empleado con validaciones"""
        # Validar que la cédula no exista
        if self.repository.get_by_cedula(datos.get("cedula")):
            raise ValueError("Ya existe un empleado con esta cédula")
        
        # Crear empleado
        empleado = Empleado(
            nombres=datos["nombres"],
            apellidos=datos["apellidos"],
            cedula=datos["cedula"],
            fecha_nacimiento=datos.get("fecha_nacimiento"),
            genero=datos.get("genero"),
            estado_civil=datos.get("estado_civil"),
            nacionalidad=datos.get("nacionalidad"),
            peso=datos.get("peso"),
            altura=datos.get("altura"),
            tipo_sangre=datos.get("tipo_sangre"),
            telefono=datos.get("telefono"),
            celular=datos.get("celular"),
            email=datos.get("email"),
            direccion=datos.get("direccion"),
            ciudad=datos.get("ciudad"),
            estado=datos.get("estado"),
            codigo_postal=datos.get("codigo_postal"),
            tipo_empleado=datos["tipo_empleado"],
            cargo=datos["cargo"],
            departamento=datos["departamento"],
            fecha_contratacion=datos.get("fecha_contratacion", date.today()),
            salario_base=datos["salario_base"],
            nivel_educativo=datos.get("nivel_educativo"),
            especialidad=datos.get("especialidad"),
            titulo_obtenido=datos.get("titulo_obtenido"),
            observaciones=datos.get("observaciones"),
            contacto_emergencia_nombre=datos.get("contacto_emergencia_nombre"),
            contacto_emergencia_telefono=datos.get("contacto_emergencia_telefono"),
            contacto_emergencia_relacion=datos.get("contacto_emergencia_relacion")
        )
        
        return self.repository.create(empleado)
    
    def actualizar_empleado(self, empleado_id: int, datos: Dict) -> Empleado:
        """Actualiza un empleado existente"""
        empleado = self.repository.get_by_id(empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")
        
        # Si se actualiza la cédula, verificar que no exista
        if "cedula" in datos and datos["cedula"] != empleado.cedula:
            if self.repository.get_by_cedula(datos["cedula"]):
                raise ValueError("Ya existe un empleado con esta cédula")
        
        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(empleado, campo):
                setattr(empleado, campo, valor)
        
        return self.repository.update(empleado)
    
    def eliminar_empleado(self, empleado_id: int) -> bool:
        """Elimina un empleado (desactivación lógica)"""
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
    
    def listar_por_tipo(self, tipo: TipoEmpleado) -> List[Empleado]:
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
        """Obtiene estadísticas generales de empleados"""
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