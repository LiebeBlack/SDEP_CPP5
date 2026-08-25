"""
PDF Generator
Módulo de generación de documentos PDF
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus import PageBreak, KeepTogether
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import date
from typing import Optional, Dict, List
import os

from src.config import settings
from src.models import Empleado
from src.utils.helpers import format_date, format_currency


class PDFGenerator:
    """Generador de documentos PDF"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.page_size = letter
        
    def _setup_custom_styles(self):
        """Configura estilos personalizados"""
        # Estilo para título
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para subtítulo
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para cuerpo de texto
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Estilo para etiquetas
        self.styles.add(ParagraphStyle(
            name='CustomLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            textColor=colors.darkgray
        ))
        
        # Estilo para datos
        self.styles.add(ParagraphStyle(
            name='CustomData',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        # Estilo para pie de página
        self.styles.add(ParagraphStyle(
            name='CustomFooter',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.gray,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
    
    def _get_configuracion(self) -> Dict:
        """Obtiene configuración de la institución"""
        from src.services import ConfiguracionService
        from src.config import db_config
        
        session = db_config.get_session()
        try:
            config_service = ConfiguracionService(session)
            return config_service.obtener_configuracion_general()
        finally:
            db_config.close_session(session)
    
    def generate_constancia_trabajo(self, empleado: Empleado, output_path: str) -> str:
        """
        Genera una constancia de trabajo
        
        Args:
            empleado: Objeto Empleado
            output_path: Ruta donde se guardará el PDF
            
        Returns:
            Ruta del PDF generado
        """
        config = self._get_configuracion()
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Encabezado institucional
        story.append(Paragraph(
            config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
            self.styles['CustomTitle']
        ))
        
        if config.get("direccion"):
            story.append(Paragraph(
                config["direccion"],
                self.styles['CustomFooter']
            ))
        
        if config.get("telefono"):
            story.append(Paragraph(
                f"Teléfono: {config['telefono']}",
                self.styles['CustomFooter']
            ))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Título del documento
        story.append(Paragraph(
            "CONSTANCIA DE TRABAJO",
            self.styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Fecha
        fecha_actual = format_date(date.today())
        story.append(Paragraph(
            f"Fecha: {fecha_actual}",
            self.styles['CustomData']
        ))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Cuerpo de la constancia
        cuerpo = f"""
        Por medio de la presente, la {config.get('nombre_institucion', 'Institución')} 
        certifica que el(la) Sr(a). <b>{empleado.nombre_completo}</b>, 
        portador(a) de la cédula de identidad N° <b>{empleado.cedula}</b>, 
        labora en esta institución desde el día <b>{format_date(empleado.fecha_contratacion)}</b>.
        """
        
        story.append(Paragraph(cuerpo, self.styles['CustomBody']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Datos del cargo
        tipo_str = empleado.tipo_empleado.value.upper() if hasattr(empleado.tipo_empleado, 'value') else str(empleado.tipo_empleado).upper()
        datos_cargo = f"""
        Actualmente desempeña el cargo de <b>{empleado.cargo}</b> en el departamento de 
        <b>{empleado.departamento}</b>, con una categoría de <b>{tipo_str}</b>.
        """
        
        story.append(Paragraph(datos_cargo, self.styles['CustomBody']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Condiciones laborales
        condiciones = f"""
        Devengando un salario mensual de <b>{format_currency(empleado.salario_base)}</b>.
        """
        
        story.append(Paragraph(condiciones, self.styles['CustomBody']))
        
        story.append(Spacer(1, 0.4*inch))
        
        # Cierre
        cierre = """
        Esta constancia se expide a solicitud del interesado para los fines que considere conveniente.
        """
        
        story.append(Paragraph(cierre, self.styles['CustomBody']))
        
        story.append(Spacer(1, 1.5*inch))
        
        # Espacio para firma
        firma_table = Table([
            ["_________________________________", "_________________________________"],
            ["Firma Autorizada", "Sello"],
            ["", ""],
            [config.get("nombre_institucion", "Institución"), ""]
        ], colWidths=[3*inch, 2*inch])
        
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(firma_table)
        
        # Generar PDF
        doc.build(story)
        
        return output_path
    
    def generate_constancia_estudios(self, empleado: Empleado, output_path: str) -> str:
        """
        Genera una constancia de estudios
        
        Args:
            empleado: Objeto Empleado
            output_path: Ruta donde se guardará el PDF
            
        Returns:
            Ruta del PDF generado
        """
        config = self._get_configuracion()
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Encabezado
        story.append(Paragraph(
            config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
            self.styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Título
        story.append(Paragraph(
            "CONSTANCIA DE ESTUDIOS",
            self.styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Fecha
        story.append(Paragraph(
            f"Fecha: {format_date(date.today())}",
            self.styles['CustomData']
        ))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Cuerpo
        cuerpo = f"""
        Por medio de la presente se hace constar que <b>{empleado.nombre_completo}</b>, 
        portador(a) de la cédula de identidad N° <b>{empleado.cedula}</b>, 
        cuenta con el nivel educativo de <b>{empleado.nivel_educativo or 'No especificado'}</b>.
        """
        
        story.append(Paragraph(cuerpo, self.styles['CustomBody']))
        
        if empleado.especialidad:
            especialidad = f"""
            Con especialización en <b>{empleado.especialidad}</b>.
            """
            story.append(Paragraph(especialidad, self.styles['CustomBody']))
        
        if empleado.titulo_obtenido:
            titulo = f"""
            Obteniendo el título de <b>{empleado.titulo_obtenido}</b>.
            """
            story.append(Paragraph(titulo, self.styles['CustomBody']))
        
        story.append(Spacer(1, 1.5*inch))
        
        # Firma
        firma_table = Table([
            ["_________________________________"],
            ["Firma Autorizada"],
            [config.get("nombre_institucion", "Institución")]
        ], colWidths=[3*inch])
        
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(firma_table)
        
        doc.build(story)
        
        return output_path
    
    def generate_recibo_pago(self, pago_data: Dict, output_path: str) -> str:
        """
        Genera un recibo de pago
        
        Args:
            pago_data: Diccionario con datos del pago
            output_path: Ruta donde se guardará el PDF
            
        Returns:
            Ruta del PDF generado
        """
        config = self._get_configuracion()
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Encabezado
        story.append(Paragraph(
            config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
            self.styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Título
        story.append(Paragraph(
            "RECIBO DE PAGO",
            self.styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Información general
        info_table = Table([
            ["Fecha:", format_date(date.today())],
            ["Recibo N°:", pago_data.get("referencia_pago", "N/A")],
            ["Empleado:", pago_data.get("nombre_empleado", "N/A")],
            ["Cédula:", pago_data.get("cedula", "N/A")],
            ["Periodo:", f"{format_date(pago_data['periodo_inicio'])} a {format_date(pago_data['periodo_fin'])}"]
        ], colWidths=[1.5*inch, 4*inch])
        
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(info_table)
        
        story.append(Spacer(1, 0.3*inch))
        
        # Desglose de pagos
        story.append(Paragraph("DESGLOSE DE PAGOS", self.styles['CustomSubtitle']))
        
        total_deducc = round(
            float(pago_data.get('deduccion_seguro', 0) or 0) +
            float(pago_data.get('deduccion_pension', 0) or 0) +
            float(pago_data.get('deduccion_impuesto', 0) or 0) +
            float(pago_data.get('otras_deducciones', 0) or 0) +
            float(pago_data.get('descuentos', 0) or 0),
            2
        )
        
        desglose_table = Table([
            ["Concepto", "Monto"],
            ["Salario Base", format_currency(float(pago_data['salario_base']))],
            ["Bonificaciones", format_currency(float(pago_data.get('bonificaciones', 0) or 0))],
            ["Horas Extra", format_currency(float(pago_data.get('horas_extra', 0) or 0))],
            ["TOTAL INGRESOS", format_currency(float(pago_data['monto_bruto']))],
            ["", ""],
            ["Deducción Seguro Social", format_currency(float(pago_data.get('deduccion_seguro', 0) or 0))],
            ["Deducción Pensión", format_currency(float(pago_data.get('deduccion_pension', 0) or 0))],
            ["Deducción Impuesto", format_currency(float(pago_data.get('deduccion_impuesto', 0) or 0))],
            ["Otras Deducciones", format_currency(float(pago_data.get('otras_deducciones', 0) or 0))],
            ["Descuentos", format_currency(float(pago_data.get('descuentos', 0) or 0))],
            ["TOTAL DEDUCCIONES", format_currency(total_deducc)],
            ["", ""],
            ["NETO A PAGAR", format_currency(float(pago_data['monto_neto']))]
        ], colWidths=[3*inch, 2.5*inch])
        
        desglose_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LINEABOVE', (0, 4), (-1, 4), 1, colors.black),
            ('LINEBELOW', (0, 4), (-1, 4), 1, colors.black),
            ('FONTNAME', (0, 4), (1, 4), 'Helvetica-Bold'),
            ('LINEABOVE', (0, 11), (-1, 11), 1, colors.black),
            ('LINEBELOW', (0, 11), (-1, 11), 1, colors.black),
            ('FONTNAME', (0, 11), (1, 11), 'Helvetica-Bold'),
            ('LINEABOVE', (0, 13), (-1, 13), 1.5, colors.darkblue),
            ('LINEBELOW', (0, 13), (-1, 13), 1.5, colors.darkblue),
            ('FONTNAME', (0, 13), (1, 13), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 13), (1, 13), 11),
        ]))
        
        story.append(desglose_table)
        
        story.append(Spacer(1, 1.5*inch))
        
        # Firma
        firma_table = Table([
            ["_________________________________"],
            ["Firma Recibido"],
            ["", ""],
            ["Fecha: _________________"]
        ], colWidths=[3*inch])
        
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(firma_table)
        
        doc.build(story)
        
        return output_path
    
    def generate_reporte_empleados(self, empleados: List[Empleado], output_path: str) -> str:
        """
        Genera un reporte de empleados
        
        Args:
            empleados: Lista de objetos Empleado
            output_path: Ruta donde se guardará el PDF
            
        Returns:
            Ruta del PDF generado
        """
        config = self._get_configuracion()
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=18
        )
        
        story = []
        
        # Encabezado
        story.append(Paragraph(
            config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
            self.styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Título
        story.append(Paragraph(
            "REPORTE DE EMPLEADOS",
            self.styles['CustomTitle']
        ))
        
        story.append(Spacer(1, 0.1*inch))
        
        # Fecha
        story.append(Paragraph(
            f"Fecha: {format_date(date.today())} | Total: {len(empleados)} empleados",
            self.styles['CustomData']
        ))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Tabla de empleados
        data = [["Cédula", "Nombre", "Cargo", "Departamento", "Tipo", "Salario"]]
        
        for emp in empleados:
            tipo_display = emp.tipo_empleado.value.capitalize() if hasattr(emp.tipo_empleado, 'value') else str(emp.tipo_empleado).capitalize()
            data.append([
                str(emp.cedula),
                emp.nombre_completo,
                str(emp.cargo or ""),
                str(emp.departamento or ""),
                tipo_display,
                format_currency(emp.salario_base)
            ])
        
        tabla = Table(data, colWidths=[1*inch, 2*inch, 1.5*inch, 1.5*inch, 1*inch, 1*inch])
        
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(tabla)
        
        doc.build(story)
        
        return output_path


# Instancia global del generador de PDFs
pdf_generator = PDFGenerator()