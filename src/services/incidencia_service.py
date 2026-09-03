"""
Incidencia Service
Servicio de lógica de negocio para incidencias

Este servicio gestiona el ciclo de vida completo de incidencias,
incluyendo registro, aprobación, rechazo y control de vigencia.
"""

from typing import List, Optional, Dict, Any
from datetime import date, timedelta
from sqlalchemy.orm import Session
import uuid
import os

from src.models import Incidencia, TipoIncidencia, EstadoIncidencia
from src.repositories import IncidenciaRepository
from src.config import settings


class IncidenciaService:
    """
    Servicio de gestión de incidencias
    
    Administra el flujo completo de incidencias desde su registro
    hasta su aprobación o rechazo, incluyendo cálculo automático
    de días y gestión de documentos de soporte.
    """
    
    def __init__(self, session: Session):
        """
        Inicializa el servicio de incidencias
        
        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self.session = session
        self.repository = IncidenciaRepository(session)
    
    def crear_incidencia(self, datos: Dict, archivo_soporte: bytes = None) -> Incidencia:
        """Crea una nueva incidencia"""
        from src.utils.helpers import parse_date
        
        # Normalizar fechas
        fecha_inicio = datos["fecha_inicio"]
        if isinstance(fecha_inicio, str):
            fecha_inicio = parse_date(fecha_inicio)
        
        fecha_fin = datos["fecha_fin"]
        if isinstance(fecha_fin, str):
            fecha_fin = parse_date(fecha_fin)
        
        fecha_sol = datos.get("fecha_solicitud")
        if isinstance(fecha_sol, str):
            fecha_sol = parse_date(fecha_sol) or date.today()
        elif not fecha_sol:
            fecha_sol = date.today()
        
        if not fecha_inicio or not fecha_fin:
            raise ValueError("Las fechas de inicio y fin son requeridas")
        
        # Calcular días solicitados
        dias_solicitados = max(1, (fecha_fin - fecha_inicio).days + 1)
        datos["dias_solicitados"] = dias_solicitados
        
        # Procesar archivo de soporte
        if archivo_soporte:
            extension = self._obtener_extension(datos.get("documento_soporte_nombre", "soporte.pdf"))
            nombre_unico = f"soporte_{uuid.uuid4().hex}{extension}"
            ruta_completa = settings.get_document_path(nombre_unico)
            
            try:
                with open(ruta_completa, 'wb') as f:
                    f.write(archivo_soporte)
            except Exception:
                pass
            
            datos["documento_soporte_nombre"] = nombre_unico
            datos["documento_soporte_ruta"] = ruta_completa
            datos["documento_soporte_binario"] = archivo_soporte
        
        tipo_inc = datos["tipo_incidencia"]
        if hasattr(tipo_inc, 'value'):
            tipo_inc = tipo_inc.value
        
        estado = datos.get("estado", EstadoIncidencia.PENDIENTE.value)
        if hasattr(estado, 'value'):
            estado = estado.value
        
        incidencia = Incidencia(
            empleado_id=int(datos["empleado_id"]),
            tipo_incidencia=tipo_inc,
            estado=estado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_solicitud=fecha_sol,
            motivo=str(datos["motivo"]).strip(),
            descripcion=datos.get("descripcion"),
            dias_solicitados=dias_solicitados,
            documento_soporte_nombre=datos.get("documento_soporte_nombre"),
            documento_soporte_ruta=datos.get("documento_soporte_ruta"),
            documento_soporte_binario=datos.get("documento_soporte_binario"),
            afecta_nominas=int(datos.get("afecta_nominas", 1)),
            observaciones=datos.get("observaciones")
        )
        
        return self.repository.create(incidencia)
    
    def actualizar_incidencia(self, incidencia_id: int, datos: Dict, archivo_soporte: bytes = None) -> Incidencia:
        """Actualiza una incidencia existente"""
        from src.utils.helpers import parse_date
        
        incidencia = self.repository.get_by_id(incidencia_id)
        if not incidencia:
            raise ValueError("Incidencia no encontrada")
        
        # Normalizar fechas si vienen
        if "fecha_inicio" in datos and isinstance(datos["fecha_inicio"], str):
            datos["fecha_inicio"] = parse_date(datos["fecha_inicio"])
        if "fecha_fin" in datos and isinstance(datos["fecha_fin"], str):
            datos["fecha_fin"] = parse_date(datos["fecha_fin"])
        
        # Si se actualizan las fechas, recalcular días
        if "fecha_inicio" in datos or "fecha_fin" in datos:
            fecha_inicio = datos.get("fecha_inicio", incidencia.fecha_inicio)
            fecha_fin = datos.get("fecha_fin", incidencia.fecha_fin)
            if fecha_inicio and fecha_fin:
                datos["dias_solicitados"] = max(1, (fecha_fin - fecha_inicio).days + 1)
        
        # Procesar nuevo archivo de soporte
        if archivo_soporte:
            # Eliminar archivo anterior
            if incidencia.documento_soporte_ruta and os.path.exists(incidencia.documento_soporte_ruta):
                try:
                    os.remove(incidencia.documento_soporte_ruta)
                except Exception:
                    pass
            
            extension = self._obtener_extension(datos.get("documento_soporte_nombre", "soporte.pdf"))
            nombre_unico = f"soporte_{uuid.uuid4().hex}{extension}"
            ruta_completa = settings.get_document_path(nombre_unico)
            
            try:
                with open(ruta_completa, 'wb') as f:
                    f.write(archivo_soporte)
            except Exception:
                pass
            
            datos["documento_soporte_nombre"] = nombre_unico
            datos["documento_soporte_ruta"] = ruta_completa
            datos["documento_soporte_binario"] = archivo_soporte
        
        if "tipo_incidencia" in datos and hasattr(datos["tipo_incidencia"], 'value'):
            datos["tipo_incidencia"] = datos["tipo_incidencia"].value
        if "estado" in datos and hasattr(datos["estado"], 'value'):
            datos["estado"] = datos["estado"].value
        
        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(incidencia, campo) and campo not in ["empleado_id", "fecha_aprobacion", "aprobado_por"]:
                setattr(incidencia, campo, valor)
        
        return self.repository.update(incidencia)
    
    def eliminar_incidencia(self, incidencia_id: int) -> bool:
        """Elimina una incidencia"""
        incidencia = self.repository.get_by_id(incidencia_id)
        if incidencia:
            # Eliminar archivo de soporte
            if incidencia.documento_soporte_ruta and os.path.exists(incidencia.documento_soporte_ruta):
                try:
                    os.remove(incidencia.documento_soporte_ruta)
                except Exception:
                    pass
            return self.repository.delete(incidencia_id)
        return False
    
    def obtener_incidencia(self, incidencia_id: int) -> Optional[Incidencia]:
        """Obtiene una incidencia por ID"""
        return self.repository.get_by_id(incidencia_id)
    
    def listar_incidencias_empleado(self, empleado_id: int) -> List[Incidencia]:
        """Lista incidencias de un empleado"""
        return self.repository.get_by_empleado(empleado_id)
    
    def listar_todas(self) -> List[Incidencia]:
        """Lista todas las incidencias registradas"""
        return self.repository.get_all(limit=None)
    
    def listar_por_tipo(self, tipo: str) -> List[Incidencia]:
        """Lista incidencias por tipo"""
        return self.repository.get_by_tipo(tipo)
    
    def listar_por_estado(self, estado: str) -> List[Incidencia]:
        """Lista incidencias por estado"""
        return self.repository.get_by_estado(estado)
    
    def listar_pendientes(self) -> List[Incidencia]:
        """Lista incidencias pendientes de aprobación"""
        return self.repository.get_pendientes()
    
    def listar_vigentes(self) -> List[Incidencia]:
        """Lista incidencias vigentes actualmente"""
        return self.repository.get_vigentes()
    
    def listar_por_periodo(self, fecha_inicio: date, fecha_fin: date) -> List[Incidencia]:
        """Lista incidencias en un periodo"""
        return self.repository.get_by_periodo(fecha_inicio, fecha_fin)
    
    def aprobar_incidencia(self, incidencia_id: int, aprobado_por: str, comentarios: str = None, dias_aprobados: int = None) -> bool:
        """Aprueba una incidencia"""
        return self.repository.aprobar(incidencia_id, aprobado_por, comentarios, dias_aprobados)
    
    def rechazar_incidencia(self, incidencia_id: int, rechazado_por: str, comentarios: str = None) -> bool:
        """Rechaza una incidencia"""
        return self.repository.rechazar(incidencia_id, rechazado_por, comentarios)
    
    def completar_incidencia(self, incidencia_id: int) -> bool:
        """Marca una incidencia como completada"""
        return self.repository.completar(incidencia_id)
    
    def obtener_soporte(self, incidencia_id: int) -> Optional[bytes]:
        """Obtiene el archivo de soporte de una incidencia"""
        incidencia = self.repository.get_by_id(incidencia_id)
        if incidencia:
            if incidencia.documento_soporte_binario:
                return incidencia.documento_soporte_binario
            elif incidencia.documento_soporte_ruta and os.path.exists(incidencia.documento_soporte_ruta):
                with open(incidencia.documento_soporte_ruta, 'rb') as f:
                    return f.read()
        return None
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de incidencias"""
        return {
            "total": self.repository.count(),
            "pendientes": len(self.repository.get_pendientes()),
            "vigentes": len(self.repository.get_vigentes()),
            "por_tipo": self.repository.get_estadisticas_por_tipo(),
            "por_estado": self.repository.get_estadisticas_por_estado()
        }
    
    def calcular_dias_incidencias_periodo(self, empleado_id: int, fecha_inicio: date, fecha_fin: date) -> int:
        """Calcula los días de incidencias que afectan nómina de un empleado en un periodo"""
        from src.utils.helpers import parse_date
        if isinstance(fecha_inicio, str):
            fecha_inicio = parse_date(fecha_inicio)
        if isinstance(fecha_fin, str):
            fecha_fin = parse_date(fecha_fin)
            
        if not fecha_inicio or not fecha_fin:
            return 0
            
        incidencias = self.repository.get_by_empleado_periodo(empleado_id, fecha_inicio, fecha_fin)
        dias_totales = 0
        for incidencia in incidencias:
            # Solo contar incidencias aprobadas que afectan nómina
            if incidencia.estado == EstadoIncidencia.APROBADO.value and getattr(incidencia, 'afecta_nominas', 1) == 1:
                inc_ini = incidencia.fecha_inicio if isinstance(incidencia.fecha_inicio, date) else parse_date(str(incidencia.fecha_inicio))
                inc_fin = incidencia.fecha_fin if isinstance(incidencia.fecha_fin, date) else parse_date(str(incidencia.fecha_fin))
                
                if inc_ini and inc_fin:
                    # Delimitar al rango de la consulta
                    rango_ini = max(inc_ini, fecha_inicio)
                    rango_fin = min(inc_fin, fecha_fin)
                    if rango_fin >= rango_ini:
                        dias_inc = (rango_fin - rango_ini).days + 1
                        dias_totales += dias_inc
                else:
                    dias_totales += incidencia.dias_aprobados or incidencia.dias_solicitados or 0
        return dias_totales
    
    def _obtener_extension(self, nombre_archivo: str) -> str:
        """Obtiene la extensión de un archivo"""
        if "." in nombre_archivo:
            return nombre_archivo[nombre_archivo.rfind("."):]
        return ""
    
    def validar_datos_incidencia(self, datos: Dict) -> List[str]:
        """Valida los datos de una incidencia"""
        from src.utils.helpers import parse_date
        errores = []
        
        # Validaciones requeridas
        campos_requeridos = ["empleado_id", "tipo_incidencia", "fecha_inicio", "fecha_fin", "motivo"]
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f"El campo {campo} es requerido")
        
        # Validaciones específicas
        if "fecha_inicio" in datos and "fecha_fin" in datos:
            f_ini = parse_date(datos["fecha_inicio"]) if isinstance(datos["fecha_inicio"], str) else datos["fecha_inicio"]
            f_fin = parse_date(datos["fecha_fin"]) if isinstance(datos["fecha_fin"], str) else datos["fecha_fin"]
            
            if f_ini and f_fin:
                if f_fin < f_ini:
                    errores.append("La fecha fin debe ser posterior a la fecha inicio")
            elif not f_ini or not f_fin:
                errores.append("Formato de fecha inválido")
        
        if "empleado_id" in datos:
            try:
                empleado_id = int(datos["empleado_id"])
                if empleado_id <= 0:
                    errores.append("El ID de empleado debe ser positivo")
            except (ValueError, TypeError):
                errores.append("El ID de empleado debe ser un número válido")
        
        return errores