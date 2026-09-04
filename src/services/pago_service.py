"""
Pago Service
Servicio de lógica de negocio para pagos y nómina

Este servicio maneja el procesamiento de nóminas, cálculo de deducciones,
generación de pagos y emisión de recibos, integrándose con incidencias
para el cálculo de días trabajados.
"""

from typing import List, Optional, Dict
from datetime import date
from sqlalchemy.orm import Session

from src.models import Pago, TipoPago, MetodoPago
from src.repositories import PagoRepository, EmpleadoRepository, ConfiguracionRepository


class PagoService:
    """
    Servicio de gestión de pagos y nómina
    
    Procesa nóminas automáticas, calcula deducciones según configuración,
    genera recibos de pago y mantiene el control de pagos pendientes
    y realizados.
    """
    
    def __init__(self, session: Session):
        """
        Inicializa el servicio de pagos
        
        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self.session = session
        self.pago_repository = PagoRepository(session)
        self.empleado_repository = EmpleadoRepository(session)
        self.config_repository = ConfiguracionRepository(session)
    
    def crear_pago(self, datos: Dict) -> Pago:
        """Crea un nuevo pago"""
        from src.utils.helpers import parse_date
        
        # Normalizar fechas
        periodo_inicio = datos["periodo_inicio"]
        if isinstance(periodo_inicio, str):
            periodo_inicio = parse_date(periodo_inicio)
        
        periodo_fin = datos["periodo_fin"]
        if isinstance(periodo_fin, str):
            periodo_fin = parse_date(periodo_fin)
        
        fecha_pago = datos.get("fecha_pago")
        if isinstance(fecha_pago, str):
            fecha_pago = parse_date(fecha_pago) or date.today()
        elif not fecha_pago:
            fecha_pago = date.today()
        
        salario_base = round(float(datos["salario_base"]), 2)
        
        # Calcular deducciones automáticamente si no se proporcionan
        if "deduccion_seguro" not in datos or datos["deduccion_seguro"] is None:
            deduccion_seguro = self._calcular_deduccion_seguro(salario_base)
        else:
            deduccion_seguro = round(float(datos["deduccion_seguro"]), 2)
        
        if "deduccion_pension" not in datos or datos["deduccion_pension"] is None:
            deduccion_pension = self._calcular_deduccion_pension(salario_base)
        else:
            deduccion_pension = round(float(datos["deduccion_pension"]), 2)
        
        if "deduccion_impuesto" not in datos or datos["deduccion_impuesto"] is None:
            deduccion_impuesto = self._calcular_deduccion_impuesto(salario_base)
        else:
            deduccion_impuesto = round(float(datos["deduccion_impuesto"]), 2)
        
        # Calcular montos
        descuentos = round(float(datos.get("descuentos", 0) or 0), 2)
        bonificaciones = round(float(datos.get("bonificaciones", 0) or 0), 2)
        horas_extra = round(float(datos.get("horas_extra", 0) or 0), 2)
        otras_deducciones = round(float(datos.get("otras_deducciones", 0) or 0), 2)
        
        total_deducciones = round(deduccion_seguro + deduccion_pension + deduccion_impuesto + otras_deducciones, 2)
        
        monto_bruto = round(salario_base + bonificaciones + horas_extra, 2)
        monto_neto = round(max(0.0, monto_bruto - total_deducciones - descuentos), 2)
        
        tipo_p = datos["tipo_pago"]
        if hasattr(tipo_p, 'value'):
            tipo_p = tipo_p.value
        
        metodo_p = datos.get("metodo_pago", MetodoPago.TRANSFERENCIA.value)
        if hasattr(metodo_p, 'value'):
            metodo_p = metodo_p.value
        
        empleado_id = int(datos["empleado_id"])
        ref_pago = datos.get("referencia_pago") or f"REC-{empleado_id}-{periodo_inicio.strftime('%Y%m%d') if periodo_inicio else '00'}"
        
        pago = Pago(
            empleado_id=empleado_id,
            tipo_pago=tipo_p,
            metodo_pago=metodo_p,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            fecha_pago=fecha_pago,
            monto_bruto=monto_bruto,
            monto_neto=monto_neto,
            descuentos=descuentos,
            bonificaciones=bonificaciones,
            horas_extra=horas_extra,
            salario_base=salario_base,
            deduccion_seguro=deduccion_seguro,
            deduccion_pension=deduccion_pension,
            deduccion_impuesto=deduccion_impuesto,
            otras_deducciones=otras_deducciones,
            descripcion=datos.get("descripcion"),
            referencia_pago=ref_pago,
            observaciones=datos.get("observaciones"),
            pagado=int(datos.get("pagado", 0))
        )
        
        return self.pago_repository.create(pago)
    
    def actualizar_pago(self, pago_id: int, datos: Dict) -> Pago:
        """Actualiza un pago existente"""
        from src.utils.helpers import parse_date
        
        pago = self.pago_repository.get_by_id(pago_id)
        if not pago:
            raise ValueError("Pago no encontrado")
        
        # Normalizar fechas si vienen en datos
        for f_campo in ["periodo_inicio", "periodo_fin", "fecha_pago"]:
            if f_campo in datos and isinstance(datos[f_campo], str):
                datos[f_campo] = parse_date(datos[f_campo])
        
        # Recalcular montos si se modifican los componentes
        recalcular = any(
            campo in datos 
            for campo in ["salario_base", "bonificaciones", "horas_extra", 
                        "descuentos", "deduccion_seguro", "deduccion_pension", 
                        "deduccion_impuesto", "otras_deducciones"]
        )
        
        if recalcular:
            salario_base = round(float(datos.get("salario_base", pago.salario_base) or 0), 2)
            bonificaciones = round(float(datos.get("bonificaciones", pago.bonificaciones) or 0), 2)
            horas_extra = round(float(datos.get("horas_extra", pago.horas_extra) or 0), 2)
            descuentos = round(float(datos.get("descuentos", pago.descuentos) or 0), 2)
            
            deduccion_seguro = round(float(datos.get("deduccion_seguro", pago.deduccion_seguro) or 0), 2)
            deduccion_pension = round(float(datos.get("deduccion_pension", pago.deduccion_pension) or 0), 2)
            deduccion_impuesto = round(float(datos.get("deduccion_impuesto", pago.deduccion_impuesto) or 0), 2)
            otras_deducciones = round(float(datos.get("otras_deducciones", pago.otras_deducciones) or 0), 2)
            
            total_deducciones = round(deduccion_seguro + deduccion_pension + deduccion_impuesto + otras_deducciones, 2)
            monto_bruto = round(salario_base + bonificaciones + horas_extra, 2)
            monto_neto = round(max(0.0, monto_bruto - total_deducciones - descuentos), 2)
            
            datos["monto_bruto"] = monto_bruto
            datos["monto_neto"] = monto_neto
        
        if "tipo_pago" in datos and hasattr(datos["tipo_pago"], 'value'):
            datos["tipo_pago"] = datos["tipo_pago"].value
        if "metodo_pago" in datos and hasattr(datos["metodo_pago"], 'value'):
            datos["metodo_pago"] = datos["metodo_pago"].value
        
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
        from src.utils.helpers import parse_date
        if isinstance(periodo_inicio, str):
            periodo_inicio = parse_date(periodo_inicio)
        if isinstance(periodo_fin, str):
            periodo_fin = parse_date(periodo_fin)
            
        if not periodo_inicio or not periodo_fin:
            raise ValueError("Fechas de período inválidas o requeridas")
            
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
        dias_trabajados = max(0, dias_periodo - dias_incidencias)
        
        # Calcular salario proporcional (asumiendo mes comercial de 30 días)
        salario_diario = float(empleado.salario_base) / 30.0
        salario_base_periodo = round(salario_diario * min(dias_trabajados, 30), 2)
        
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
        from src.utils.helpers import parse_date
        if isinstance(periodo_inicio, str):
            periodo_inicio = parse_date(periodo_inicio)
        if isinstance(periodo_fin, str):
            periodo_fin = parse_date(periodo_fin)
            
        if not periodo_inicio or not periodo_fin:
            return []
            
        empleados_activos = self.empleado_repository.get_activos()
        pagos_generados = []
        
        for empleado in empleados_activos:
            try:
                pago = self.generar_nominas_empleado(empleado.id, periodo_inicio, periodo_fin)
                pagos_generados.append(pago)
            except Exception:
                # Continuar con el siguiente empleado si falla o ya existe
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
        
        total_bruto = round(sum(float(p.monto_bruto or 0) for p in pagos), 2)
        total_neto = round(sum(float(p.monto_neto or 0) for p in pagos), 2)
        total_deducciones = round(sum(float(p.total_deducciones or 0) for p in pagos), 2)
        total_bonificaciones = round(sum(float(p.bonificaciones or 0) for p in pagos), 2)
        
        return {
            "cantidad_pagos": len(pagos),
            "total_bruto": total_bruto,
            "total_neto": total_neto,
            "total_deducciones": total_deducciones,
            "total_bonificaciones": total_bonificaciones,
            "promedio_neto": round(total_neto / len(pagos), 2) if pagos else 0.0
        }
    
    def _calcular_deduccion_seguro(self, salario_base: float) -> float:
        """Calcula la deducción de seguro social"""
        porcentaje = self.config_repository.get_valor("porcentaje_seguro", 4.5)
        try:
            return round(float(salario_base) * (float(porcentaje) / 100.0), 2)
        except (ValueError, TypeError):
            return 0.0
    
    def _calcular_deduccion_pension(self, salario_base: float) -> float:
        """Calcula la deducción de pensión"""
        porcentaje = self.config_repository.get_valor("porcentaje_pension", 5.0)
        try:
            return round(float(salario_base) * (float(porcentaje) / 100.0), 2)
        except (ValueError, TypeError):
            return 0.0
    
    def _calcular_deduccion_impuesto(self, salario_base: float) -> float:
        """Calcula la deducción de impuesto"""
        porcentaje = self.config_repository.get_valor("porcentaje_impuesto", 0.0)
        try:
            return round(float(salario_base) * (float(porcentaje) / 100.0), 2)
        except (ValueError, TypeError):
            return 0.0
    
    def validar_datos_pago(self, datos: Dict) -> List[str]:
        """Valida los datos de un pago"""
        from src.utils.helpers import parse_date
        errores = []
        
        # Validaciones requeridas
        campos_requeridos = ["empleado_id", "tipo_pago", "periodo_inicio", "periodo_fin", "salario_base"]
        for campo in campos_requeridos:
            if campo not in datos or datos[campo] is None or str(datos[campo]).strip() == "":
                errores.append(f"El campo {campo} es requerido")
        
        # Validaciones específicas
        if "periodo_inicio" in datos and "periodo_fin" in datos:
            p_ini = datos["periodo_inicio"] if isinstance(datos["periodo_inicio"], date) else parse_date(str(datos["periodo_inicio"]))
            p_fin = datos["periodo_fin"] if isinstance(datos["periodo_fin"], date) else parse_date(str(datos["periodo_fin"]))
            if p_ini and p_fin and p_fin < p_ini:
                errores.append("La fecha fin debe ser posterior a la fecha inicio")
        
        if "salario_base" in datos:
            try:
                salario = float(datos["salario_base"])
                if salario <= 0:
                    errores.append("El salario base debe ser mayor a 0")
            except (ValueError, TypeError):
                errores.append("El salario base debe ser un número válido")
        
        return errores