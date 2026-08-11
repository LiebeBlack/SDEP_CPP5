"""
Pago Service
Servicio de lógica de negocio para pagos y nómina
"""

from typing import List, Optional, Dict
from datetime import date, timedelta
from sqlalchemy.orm import Session
from decimal import Decimal
import os

from src.models import Pago, TipoPago, MetodoPago, Empleado
from src.repositories import PagoRepository, EmpleadoRepository, ConfiguracionRepository
from src.config import settings


class PagoService:
    """Servicio de gestión de pagos y nómina"""
    
    def __init__(self, session: Session):
        self.session = session
        self.pago_repository = PagoRepository(session)
        self.empleado_repository = EmpleadoRepository(session)
        self.config_repository = ConfiguracionRepository(session)
    
    def crear_pago(self, datos: Dict) -> Pago:
        """Crea un nuevo pago"""
        # Calcular deducciones automáticamente si no se proporcionan
        if "deduccion_seguro" not in datos or datos["deduccion_seguro"] is None:
            datos["deduccion_seguro"] = self._calcular_deduccion_seguro(datos["salario_base"])
        
        if "deduccion_pension" not in datos or datos["deduccion_pension"] is None:
            datos["deduccion_pension"] = self._calcular_deduccion_pension(datos["salario_base"])
        
        if "deduccion_impuesto" not in datos or datos["deduccion_impuesto"] is None:
            datos["deduccion_impuesto"] = self._calcular_deduccion_impuesto(datos["salario_base"])
        
        # Calcular montos
        descuentos = datos.get("descuentos", 0)
        bonificaciones = datos.get("bonificaciones", 0)
        horas_extra = datos.get("horas_extra", 0)
        
        total_deducciones = (
            datos["deduccion_seguro"] + 
            datos["deduccion_pension"] + 
            datos["deduccion_impuesto"] + 
            datos.get("otras_deducciones", 0)
        )
        
        monto_bruto = datos["salario_base"] + bonificaciones + horas_extra
        monto_neto = monto_bruto - total_deducciones - descuentos
        
        pago = Pago(
            empleado_id=datos["empleado_id"],
            tipo_pago=datos["tipo_pago"],
            metodo_pago=datos.get("metodo_pago", MetodoPago.TRANSFERENCIA.value),
            periodo_inicio=datos["periodo_inicio"],
            periodo_fin=datos["periodo_fin"],
            fecha_pago=datos.get("fecha_pago", date.today()),
            monto_bruto=monto_bruto,
            monto_neto=monto_neto,
            descuentos=descuentos,
            bonificaciones=bonificaciones,
            horas_extra=horas_extra,
            salario_base=datos["salario_base"],
            deduccion_seguro=datos["deduccion_seguro"],
            deduccion_pension=datos["deduccion_pension"],
            deduccion_impuesto=datos["deduccion_impuesto"],
            otras_deducciones=datos.get("otras_deducciones", 0),
            descripcion=datos.get("descripcion"),
            referencia_pago=datos.get("referencia_pago"),
            observaciones=datos.get("observaciones"),
            pagado=datos.get("pagado", 0)
        )
        
        return self.pago_repository.create(pago)
    
    def actualizar_pago(self, pago_id: int, datos: Dict) -> Pago:
        """Actualiza un pago existente"""
        pago = self.pago_repository.get_by_id(pago_id)
        if not pago:
            raise ValueError("Pago no encontrado")
        
        # Recalcular montos si se modifican los componentes
        recalcular = any(
            campo in datos 
            for campo in ["salario_base", "bonificaciones", "horas_extra", 
                        "descuentos", "deduccion_seguro", "deduccion_pension", 
                        "deduccion_impuesto", "otras_deducciones"]
        )
        
        if recalcular:
            salario_base = datos.get("salario_base", pago.salario_base)
            bonificaciones = datos.get("bonificaciones", pago.bonificaciones)
            horas_extra = datos.get("horas_extra", pago.horas_extra)
            descuentos = datos.get("descuentos", pago.descuentos)
            
            deduccion_seguro = datos.get("deduccion_seguro", pago.deduccion_seguro)
            deduccion_pension = datos.get("deduccion_pension", pago.deduccion_pension)
            deduccion_impuesto = datos.get("deduccion_impuesto", pago.deduccion_impuesto)
            otras_deducciones = datos.get("otras_deducciones", pago.otras_deducciones)
            
            total_deducciones = deduccion_seguro + deduccion_pension + deduccion_impuesto + otras_deducciones
            monto_bruto = salario_base + bonificaciones + horas_extra
            monto_neto = monto_bruto - total_deducciones - descuentos
            
            datos["monto_bruto"] = monto_bruto
            datos["monto_neto"] = monto_neto
        
        # Actualizar campos
        for campo, valor in datos.items():
            if hasattr(pago, campo) and campo not in ["empleado_id"]:
                setattr(pago, campo, valor)
        
        return self.pago_repository.update(pago)
    
    def eliminar_pago(self, pago_id: int) -> bool:
        """Elimina un pago"""
        return self.pago_repository.delete(pago_id)
    
    def obtener_pago(self, pago_id: int) -> Optional[Pago]:
        """Obtiene un pago por ID"""
        return self.pago_repository.get_by_id(pago_id)
    
    def listar_pagos_empleado(self, empleado_id: int) -> List[Pago]:
        """Lista pagos de un empleado"""
        return self.pago_repository.get_by_empleado(empleado_id)
    
    def listar_por_periodo(self, fecha_inicio: date, fecha_fin: date) -> List[Pago]:
        """Lista pagos en un periodo"""
        return self.pago_repository.get_by_periodo(fecha_inicio, fecha_fin)
    
    def listar_pendientes(self) -> List[Pago]:
        """Lista pagos pendientes"""
        return self.pago_repository.get_pendientes()
    
    def listar_pendientes_empleado(self, empleado_id: int) -> List[Pago]:
        """Lista pagos pendientes de un empleado"""
        return self.pago_repository.get_pendientes_by_empleado(empleado_id)
    
    def listar_pagos(self) -> List[Pago]:
        """Lista todos los pagos"""
        return self.pago_repository.get_all()
    
    def listar_pagados(self) -> List[Pago]:
        """Lista pagos realizados"""
        return self.pago_repository.get_pagados()
    
    def marcar_pagado(self, pago_id: int) -> bool:
        """Marca un pago como realizado"""
        return self.pago_repository.marcar_pagado(pago_id)
    
    def marcar_pendiente(self, pago_id: int) -> bool:
        """Marca un pago como pendiente"""
        return self.pago_repository.marcar_pendiente(pago_id)
    
    def generar_nominas_empleado(self, empleado_id: int, periodo_inicio: date, periodo_fin: date) -> Pago:
        """Genera automáticamente la nómina de un empleado para un periodo"""
        empleado = self.empleado_repository.get_by_id(empleado_id)
        if not empleado:
            raise ValueError("Empleado no encontrado")
        
        # Verificar si ya existe nómina para este periodo
        pagos_existentes = self.pago_repository.get_by_empleado_periodo(
            empleado_id, periodo_inicio, periodo_fin
        )
        if pagos_existentes:
            raise ValueError("Ya existe una nómina para este periodo")
        
        # Calcular días trabajados (considerando incidencias)
        from src.services.incidencia_service import IncidenciaService
        incidencia_service = IncidenciaService(self.session)
        dias_incidencias = incidencia_service.calcular_dias_incidencias_periodo(
            empleado_id, periodo_inicio, periodo_fin
        )
        
        dias_periodo = (periodo_fin - periodo_inicio).days + 1
        dias_trabajados = dias_periodo - dias_incidencias
        
        # Calcular salario proporcional
        salario_diario = empleado.salario_base / 30
        salario_base_periodo = salario_diario * dias_trabajados
        
        # Crear pago
        datos_pago = {
            "empleado_id": empleado_id,
            "tipo_pago": TipoPago.SALARIO_BASE.value,
            "periodo_inicio": periodo_inicio,
            "periodo_fin": periodo_fin,
            "salario_base": salario_base_periodo,
            "descripcion": f"Nómina {periodo_inicio.strftime('%Y-%m-%d')} a {periodo_fin.strftime('%Y-%m-%d')}"
        }
        
        return self.crear_pago(datos_pago)
    
    def generar_nominas_periodo(self, periodo_inicio: date, periodo_fin: date) -> List[Pago]:
        """Genera nóminas para todos los empleados activos en un periodo"""
        empleados_activos = self.empleado_repository.get_activos()
        pagos_generados = []
        
        for empleado in empleados_activos:
            try:
                pago = self.generar_nominas_empleado(empleado.id, periodo_inicio, periodo_fin)
                pagos_generados.append(pago)
            except Exception as e:
                # Continuar con el siguiente empleado si falla
                continue
        
        return pagos_generados
    
    def obtener_estadisticas(self) -> Dict:
        """Obtiene estadísticas de pagos"""
        return {
            "total": self.pago_repository.count(),
            "pagados": len(self.pago_repository.get_pagados()),
            "pendientes": len(self.pago_repository.get_pendientes()),
            "por_tipo": self.pago_repository.get_estadisticas_por_tipo(),
            "por_metodo": self.pago_repository.get_estadisticas_por_metodo()
        }
    
    def obtener_resumen_periodo(self, fecha_inicio: date, fecha_fin: date) -> Dict:
        """Obtiene un resumen de pagos en un periodo"""
        pagos = self.pago_repository.get_by_periodo(fecha_inicio, fecha_fin)
        
        total_bruto = sum(float(p.monto_bruto) for p in pagos)
        total_neto = sum(float(p.monto_neto) for p in pagos)
        total_deducciones = sum(float(p.descuentos) for p in pagos)
        total_bonificaciones = sum(float(p.bonificaciones) for p in pagos)
        
        return {
            "cantidad_pagos": len(pagos),
            "total_bruto": total_bruto,
            "total_neto": total_neto,
            "total_deducciones": total_deducciones,
            "total_bonificaciones": total_bonificaciones,
            "promedio_neto": total_neto / len(pagos) if pagos else 0
        }
    
    def _calcular_deduccion_seguro(self, salario_base: float) -> float:
        """Calcula la deducción de seguro social"""
        porcentaje = self.config_repository.get_valor("porcentaje_seguro", 4.5)
        return salario_base * (porcentaje / 100)
    
    def _calcular_deduccion_pension(self, salario_base: float) -> float:
        """Calcula la deducción de pensión"""
        porcentaje = self.config_repository.get_valor("porcentaje_pension", 5.0)
        return salario_base * (porcentaje / 100)
    
    def _calcular_deduccion_impuesto(self, salario_base: float) -> float:
        """Calcula la deducción de impuesto"""
        porcentaje = self.config_repository.get_valor("porcentaje_impuesto", 0.0)
        return salario_base * (porcentaje / 100)
    
    def validar_datos_pago(self, datos: Dict) -> List[str]:
        """Valida los datos de un pago"""
        errores = []
        
        # Validaciones requeridas
        campos_requeridos = ["empleado_id", "tipo_pago", "periodo_inicio", "periodo_fin", "salario_base"]
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f"El campo {campo} es requerido")
        
        # Validaciones específicas
        if "periodo_inicio" in datos and "periodo_fin" in datos:
            if datos["periodo_fin"] < datos["periodo_inicio"]:
                errores.append("La fecha fin debe ser posterior a la fecha inicio")
        
        if "salario_base" in datos:
            try:
                salario = float(datos["salario_base"])
                if salario <= 0:
                    errores.append("El salario base debe ser mayor a 0")
            except (ValueError, TypeError):
                errores.append("El salario base debe ser un número válido")
        
        return errores