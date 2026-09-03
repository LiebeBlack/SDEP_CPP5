"""
PDF Generator
Módulo de generación de documentos PDF
"""

from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.platypus import PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import date
from typing import Optional, Dict, List, Tuple
import os
from xml.sax.saxutils import escape

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
        
        # Estilo para etiquetas de ficha (campo)
        self.styles.add(ParagraphStyle(
            name='FichaLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.darkgray,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Estilo para valores de ficha (dato)
        self.styles.add(ParagraphStyle(
            name='FichaValor',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leading=11
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
        
        if empleado.titulo_secundaria:
            titulo_sec = f"""
            Con título de bachiller en <b>{empleado.titulo_secundaria}</b>.
            """
            story.append(Paragraph(titulo_sec, self.styles['CustomBody']))
        
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
    
    @staticmethod
    def _flotante(valor) -> float:
        """Convierte un valor a número con tolerancia a vacíos"""
        try:
            return round(float(valor or 0), 2)
        except (TypeError, ValueError):
            return 0.0
    
    def _valor_ficha(self, valor) -> str:
        """Texto legible de un valor de empleado para la ficha PDF"""
        if valor is None or valor == "":
            return ""
        if hasattr(valor, "value"):
            return str(valor.value)
        if isinstance(valor, date):
            return format_date(valor)
        if isinstance(valor, float):
            return format_currency(valor)
        return str(valor)
    
    @staticmethod
    def _escape_pdf(texto) -> str:
        """Escapa texto para Paragraph y conserva saltos de línea"""
        return escape(str(texto), {"\n": "<br/>"})
    
    def _agregar_seccion_ficha(self, story, titulo: str, pares: List[Tuple[str, str]]):
        """Agrega una sección tipo ficha si contiene al menos un dato"""
        pares = [(self._escape_pdf(label), self._escape_pdf(valor))
                 for label, valor in pares if valor]
        if not pares:
            return
        story.append(Paragraph(titulo, self.styles['CustomSubtitle']))
        filas = [[Paragraph(label, self.styles['FichaLabel']),
                  Paragraph(valor, self.styles['FichaValor'])]
                 for label, valor in pares]
        tabla = Table(filas, colWidths=[1.9*inch, 4.9*inch])
        tabla.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('LINEBELOW', (0, 0), (-1, -2), 0.25, colors.lightgrey),
        ]))
        story.append(KeepTogether([tabla, Spacer(1, 0.12*inch)]))
    
    def generate_ficha_empleado(self, empleado: Empleado, output_path: str) -> str:
        """
        Genera la ficha completa del empleado en PDF
        
        Incluye datos personales, de contacto, laborales, académicos,
        bancarios, de salud y familiares.
        
        Args:
            empleado: Objeto Empleado
            output_path: Ruta donde se guardará el PDF
            
        Returns:
            Ruta del PDF generado
        """
        config = self._get_configuracion()
        v = self._valor_ficha
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=30
        )
        
        story = []
        
        story.append(Paragraph(
            config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("FICHA DEL EMPLEADO", self.styles['CustomTitle']))
        story.append(Paragraph(
            f"Fecha de emisión: {format_date(date.today())}",
            self.styles['CustomData']
        ))
        story.append(Spacer(1, 0.15*inch))
        
        edad = empleado.edad
        antiguedad = empleado.antiguedad_anos
        
        # Datos personales
        self._agregar_seccion_ficha(story, "Datos Personales", [
            ("Nombre Completo", v(empleado.nombre_completo)),
            ("Cédula", v(empleado.cedula)),
            ("Fecha de Nacimiento", v(empleado.fecha_nacimiento)),
            ("Edad", f"{edad} años" if edad else ""),
            ("Género", v(empleado.genero)),
            ("Estado Civil", v(empleado.estado_civil)),
            ("Nacionalidad", v(empleado.nacionalidad)),
            ("Tipo de Sangre", v(empleado.tipo_sangre)),
        ])
        
        # Contacto
        self._agregar_seccion_ficha(story, "Contacto y Emergencia", [
            ("Teléfono", v(empleado.telefono)),
            ("Celular", v(empleado.celular)),
            ("Correo Electrónico", v(empleado.email)),
            ("Dirección", v(empleado.direccion)),
            ("Ciudad", v(empleado.ciudad)),
            ("Estado/Provincia", v(empleado.estado)),
            ("Código Postal", v(empleado.codigo_postal)),
            ("Contacto de Emergencia", v(empleado.contacto_emergencia_nombre)),
            ("Teléfono de Emergencia", v(empleado.contacto_emergencia_telefono)),
            ("Relación", v(empleado.contacto_emergencia_relacion)),
        ])
        
        # Laboral
        estado_laboral = "Activo" if empleado.activo else "Inactivo"
        self._agregar_seccion_ficha(story, "Datos Laborales", [
            ("Puesto de Trabajo", v(empleado.cargo)),
            ("Departamento", v(empleado.departamento)),
            ("Tipo de Empleado", v(empleado.tipo_empleado)),
            ("Tipo de Contratación", v(empleado.tipo_contratacion)),
            ("Fecha de Ingreso", v(empleado.fecha_contratacion)),
            ("Fecha de Terminación", v(empleado.fecha_terminacion)),
            ("Salario Mensual", v(empleado.salario_base)),
            ("Estado Laboral", estado_laboral),
            ("Antigüedad", f"{antiguedad} años" if antiguedad else ""),
        ])
        
        # Académico
        self._agregar_seccion_ficha(story, "Formación Académica", [
            ("Nivel Educativo", v(empleado.nivel_educativo)),
            ("Especialidad", v(empleado.especialidad)),
            ("Título de Secundaria", v(empleado.titulo_secundaria)),
            ("Título Universitario", v(empleado.titulo_obtenido)),
        ])
        
        # Salud y bancarios
        self._agregar_seccion_ficha(story, "Salud y Datos Bancarios", [
            ("Institución Bancaria", v(empleado.institucion_bancaria)),
            ("Número de Cuenta", v(empleado.numero_cuenta)),
            ("Tipo de Cuenta", v(empleado.tipo_cuenta)),
            ("Carnet de Discapacidad", v(empleado.carnet_discapacidad)),
            ("Enfermedades Preexistentes/Crónicas", v(empleado.enfermedades_preexistentes)),
            ("Alergias Medicamentosas", v(empleado.alergias_medicamentosas)),
            ("Alergias Alimentarias o Ambientales", v(empleado.alergias_alimentarias)),
        ])
        
        # Familia
        self._agregar_seccion_ficha(story, "Datos Familiares", [
            ("Hijos", v(empleado.hijos)),
        ])
        
        self._agregar_seccion_ficha(story, "Observaciones", [
            ("Notas", v(empleado.observaciones)),
        ])
        
        doc.build(story)
        return output_path
    
    def generate_reporte_nomina(self, pagos: List[Dict], output_path: str,
                                titulo_periodo: Optional[str] = None) -> str:
        """
        Genera una planilla resumen de nómina con totales
        
        Args:
            pagos: Lista de diccionarios con los datos de cada pago
                (claves esperadas: nombre_empleado, cedula, cargo, salario_base,
                bonificaciones, horas_extra, deduccion_seguro, deduccion_pension,
                deduccion_impuesto, otras_deducciones, descuentos, monto_neto)
            output_path: Ruta donde se guardará el PDF
            titulo_periodo: Texto descriptivo del periodo (opcional)
            
        Returns:
            Ruta del PDF generado
            
        Raises:
            ValueError: Si la lista de pagos está vacía
        """
        if not pagos:
            raise ValueError("No hay pagos para incluir en la planilla")
        
        config = self._get_configuracion()
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=36,
            leftMargin=36,
            topMargin=48,
            bottomMargin=30
        )
        
        story = []
        story.append(Paragraph(
            config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 0.15*inch))
        story.append(Paragraph("PLANILLA DE NÓMINA", self.styles['CustomTitle']))
        
        if not titulo_periodo:
            primero = pagos[0]
            inicio = primero.get("periodo_inicio")
            fin = primero.get("periodo_fin")
            if inicio and fin:
                titulo_periodo = f"Periodo: {format_date(inicio)} a {format_date(fin)}"
            else:
                titulo_periodo = f"Total de pagos: {len(pagos)}"
        story.append(Paragraph(titulo_periodo, self.styles['CustomData']))
        story.append(Spacer(1, 0.15*inch))
        
        # Totales acumuladores
        totales = {
            "salario": 0.0, "extras": 0.0, "isss": 0.0, "afp": 0.0,
            "isr": 0.0, "otras": 0.0, "descuentos": 0.0, "neto": 0.0,
        }
        
        encabezados = ["No.", "Empleado", "Cédula", "Cargo", "Salario Base",
                       "Extras", "ISSS", "AFP", "ISR", "Otras", "Descuentos",
                       "Neto a Pagar"]
        filas = [encabezados]
        
        for indice, pago in enumerate(pagos, start=1):
            extras = self._flotante(pago.get("bonificaciones")) + self._flotante(pago.get("horas_extra"))
            fila = [
                str(indice),
                str(pago.get("nombre_empleado", "")),
                str(pago.get("cedula", "")),
                str(pago.get("cargo", "")),
                format_currency(self._flotante(pago.get("salario_base"))),
                format_currency(extras),
                format_currency(self._flotante(pago.get("deduccion_seguro"))),
                format_currency(self._flotante(pago.get("deduccion_pension"))),
                format_currency(self._flotante(pago.get("deduccion_impuesto"))),
                format_currency(self._flotante(pago.get("otras_deducciones"))),
                format_currency(self._flotante(pago.get("descuentos"))),
                format_currency(self._flotante(pago.get("monto_neto"))),
            ]
            filas.append(fila)
            
            totales["salario"] += self._flotante(pago.get("salario_base"))
            totales["extras"] += extras
            totales["isss"] += self._flotante(pago.get("deduccion_seguro"))
            totales["afp"] += self._flotante(pago.get("deduccion_pension"))
            totales["isr"] += self._flotante(pago.get("deduccion_impuesto"))
            totales["otras"] += self._flotante(pago.get("otras_deducciones"))
            totales["descuentos"] += self._flotante(pago.get("descuentos"))
            totales["neto"] += self._flotante(pago.get("monto_neto"))
        
        fila_totales = ["TOTALES", "", "", "",
                        format_currency(totales["salario"]),
                        format_currency(totales["extras"]),
                        format_currency(totales["isss"]),
                        format_currency(totales["afp"]),
                        format_currency(totales["isr"]),
                        format_currency(totales["otras"]),
                        format_currency(totales["descuentos"]),
                        format_currency(totales["neto"])]
        filas.append(fila_totales)
        
        tabla = Table(filas, repeatRows=1,
                      colWidths=[0.4*inch, 1.9*inch, 1.0*inch, 1.5*inch,
                                 0.85*inch, 0.7*inch, 0.65*inch, 0.65*inch,
                                 0.65*inch, 0.65*inch, 0.8*inch, 0.85*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
            ('GRID', (0, 0), (-1, -2), 0.4, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.darkblue),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(tabla)
        story.append(Spacer(1, 0.15*inch))
        story.append(Paragraph(
            f"Total neto a pagar: <b>{format_currency(totales['neto'])}</b> | "
            f"Registros: {len(pagos)}",
            self.styles['CustomData']
        ))
        
        doc.build(story)
        return output_path


# Instancia global del generador de PDFs
pdf_generator = PDFGenerator()