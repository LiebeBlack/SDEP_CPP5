"""
PDF Generator
Módulo de generación de documentos PDF
"""

from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from datetime import date
from xml.sax.saxutils import escape

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
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor=colors.darkblue,
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        # Estilo para subtítulo
        self.styles.add(
            ParagraphStyle(
                name="CustomSubtitle",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.darkblue,
                spaceAfter=12,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
            )
        )

        # Estilo para cuerpo de texto
        self.styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=self.styles["Normal"],
                fontSize=11,
                spaceAfter=10,
                alignment=TA_JUSTIFY,
                fontName="Helvetica",
            )
        )

        # Estilo para etiquetas
        self.styles.add(
            ParagraphStyle(
                name="CustomLabel",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=5,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                textColor=colors.darkgray,
            )
        )

        # Estilo para datos
        self.styles.add(
            ParagraphStyle(
                name="CustomData",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=8,
                alignment=TA_LEFT,
                fontName="Helvetica",
            )
        )

        # Estilo para etiquetas de ficha (campo)
        self.styles.add(
            ParagraphStyle(
                name="FichaLabel",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.darkgray,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
            )
        )

        # Estilo para valores de ficha (dato)
        self.styles.add(
            ParagraphStyle(
                name="FichaValor",
                parent=self.styles["Normal"],
                fontSize=9,
                alignment=TA_LEFT,
                fontName="Helvetica",
                leading=11,
            )
        )

        # Estilo para pie de página
        self.styles.add(
            ParagraphStyle(
                name="CustomFooter",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.gray,
                alignment=TA_CENTER,
                fontName="Helvetica",
            )
        )

    def _get_configuracion(self) -> dict:
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
            bottomMargin=18,
        )

        story = []

        # Encabezado institucional
        story.append(
            Paragraph(
                config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
                self.styles["CustomTitle"],
            )
        )

        if config.get("direccion"):
            story.append(Paragraph(config["direccion"], self.styles["CustomFooter"]))

        if config.get("telefono"):
            story.append(Paragraph(f"Teléfono: {config['telefono']}", self.styles["CustomFooter"]))

        story.append(Spacer(1, 0.5 * inch))

        # Título del documento
        story.append(Paragraph("CONSTANCIA DE TRABAJO", self.styles["CustomTitle"]))

        story.append(Spacer(1, 0.3 * inch))

        # Fecha
        fecha_actual = format_date(date.today())
        story.append(Paragraph(f"Fecha: {fecha_actual}", self.styles["CustomData"]))

        story.append(Spacer(1, 0.3 * inch))

        # Cuerpo de la constancia
        cuerpo = f"""
        Por medio de la presente, la {config.get('nombre_institucion', 'Institución')} 
        certifica que el(la) Sr(a). <b>{empleado.nombre_completo}</b>, 
        portador(a) de la cédula de identidad N° <b>{empleado.cedula}</b>, 
        labora en esta institución desde el día <b>{format_date(empleado.fecha_contratacion)}</b>.
        """

        story.append(Paragraph(cuerpo, self.styles["CustomBody"]))

        story.append(Spacer(1, 0.2 * inch))

        # Datos del cargo
        tipo_str = (
            empleado.tipo_empleado.value.upper()
            if hasattr(empleado.tipo_empleado, "value")
            else str(empleado.tipo_empleado).upper()
        )
        datos_cargo = f"""
        Actualmente desempeña el cargo de <b>{empleado.cargo}</b> en el departamento de 
        <b>{empleado.departamento}</b>, con una categoría de <b>{tipo_str}</b>.
        """

        story.append(Paragraph(datos_cargo, self.styles["CustomBody"]))

        story.append(Spacer(1, 0.2 * inch))

        # Condiciones laborales
        condiciones = f"""
        Devengando un salario mensual de <b>{format_currency(empleado.salario_base)}</b>.
        """

        story.append(Paragraph(condiciones, self.styles["CustomBody"]))

        story.append(Spacer(1, 0.4 * inch))

        # Cierre
        cierre = """
        Esta constancia se expide a solicitud del interesado para los fines que considere conveniente.
        """

        story.append(Paragraph(cierre, self.styles["CustomBody"]))

        story.append(Spacer(1, 1.5 * inch))

        # Espacio para firma
        firma_table = Table(
            [
                ["_________________________________", "_________________________________"],
                ["Firma Autorizada", "Sello"],
                ["", ""],
                [config.get("nombre_institucion", "Institución"), ""],
            ],
            colWidths=[3 * inch, 2 * inch],
        )

        firma_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                ]
            )
        )

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
            bottomMargin=18,
        )

        story = []

        # Encabezado
        story.append(
            Paragraph(
                config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
                self.styles["CustomTitle"],
            )
        )

        story.append(Spacer(1, 0.5 * inch))

        # Título
        story.append(Paragraph("CONSTANCIA DE ESTUDIOS", self.styles["CustomTitle"]))

        story.append(Spacer(1, 0.3 * inch))

        # Fecha
        story.append(Paragraph(f"Fecha: {format_date(date.today())}", self.styles["CustomData"]))

        story.append(Spacer(1, 0.3 * inch))

        # Cuerpo
        cuerpo = f"""
        Por medio de la presente se hace constar que <b>{empleado.nombre_completo}</b>, 
        portador(a) de la cédula de identidad N° <b>{empleado.cedula}</b>, 
        cuenta con el nivel educativo de <b>{empleado.nivel_educativo or 'No especificado'}</b>.
        """

        story.append(Paragraph(cuerpo, self.styles["CustomBody"]))

        if empleado.especialidad:
            especialidad = f"""
            Con especialización en <b>{empleado.especialidad}</b>.
            """
            story.append(Paragraph(especialidad, self.styles["CustomBody"]))

        if empleado.titulo_secundaria:
            titulo_sec = f"""
            Con título de bachiller en <b>{empleado.titulo_secundaria}</b>.
            """
            story.append(Paragraph(titulo_sec, self.styles["CustomBody"]))

        if empleado.titulo_obtenido:
            titulo = f"""
            Obteniendo el título de <b>{empleado.titulo_obtenido}</b>.
            """
            story.append(Paragraph(titulo, self.styles["CustomBody"]))

        story.append(Spacer(1, 1.5 * inch))

        # Firma
        firma_table = Table(
            [
                ["_________________________________"],
                ["Firma Autorizada"],
                [config.get("nombre_institucion", "Institución")],
            ],
            colWidths=[3 * inch],
        )

        firma_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        story.append(firma_table)

        doc.build(story)

        return output_path

    def generate_recibo_pago(self, pago_data: dict, output_path: str) -> str:
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
            bottomMargin=18,
        )

        story = [
            Paragraph(
                config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
                self.styles["CustomTitle"],
            ),
            Spacer(1, 0.3 * inch),
            Paragraph("RECIBO DE PAGO", self.styles["CustomTitle"]),
            Spacer(1, 0.3 * inch),
            self._tabla_info_recibo(pago_data),
            Spacer(1, 0.3 * inch),
            Paragraph("DESGLOSE DE PAGOS", self.styles["CustomSubtitle"]),
            self._tabla_desglose_recibo(pago_data),
            Spacer(1, 1.5 * inch),
            self._tabla_firma_recibo(),
        ]

        doc.build(story)

        return output_path

    def _tabla_info_recibo(self, pago_data: dict) -> Table:
        """Tabla de datos generales del recibo (fecha, empleado, periodo)"""
        info_table = Table(
            [
                ["Fecha:", format_date(date.today())],
                ["Recibo N°:", pago_data.get("referencia_pago", "N/A")],
                ["Empleado:", pago_data.get("nombre_empleado", "N/A")],
                ["Cédula:", pago_data.get("cedula", "N/A")],
                [
                    "Periodo:",
                    f"{format_date(pago_data['periodo_inicio'])} a {format_date(pago_data['periodo_fin'])}",
                ],
            ],
            colWidths=[1.5 * inch, 4 * inch],
        )
        info_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return info_table

    def _tabla_desglose_recibo(self, pago_data: dict) -> Table:
        """Tabla de ingresos y deducciones con totales resaltados"""
        total_deducc = round(
            float(pago_data.get("deduccion_seguro", 0) or 0)
            + float(pago_data.get("deduccion_pension", 0) or 0)
            + float(pago_data.get("deduccion_impuesto", 0) or 0)
            + float(pago_data.get("otras_deducciones", 0) or 0)
            + float(pago_data.get("descuentos", 0) or 0),
            2,
        )

        desglose_table = Table(
            [
                ["Concepto", "Monto"],
                ["Salario Base", format_currency(float(pago_data["salario_base"]))],
                ["Bonificaciones", format_currency(float(pago_data.get("bonificaciones", 0) or 0))],
                ["Horas Extra", format_currency(float(pago_data.get("horas_extra", 0) or 0))],
                ["TOTAL INGRESOS", format_currency(float(pago_data["monto_bruto"]))],
                ["", ""],
                [
                    "Deducción Seguro Social",
                    format_currency(float(pago_data.get("deduccion_seguro", 0) or 0)),
                ],
                [
                    "Deducción Pensión",
                    format_currency(float(pago_data.get("deduccion_pension", 0) or 0)),
                ],
                [
                    "Deducción Impuesto",
                    format_currency(float(pago_data.get("deduccion_impuesto", 0) or 0)),
                ],
                [
                    "Otras Deducciones",
                    format_currency(float(pago_data.get("otras_deducciones", 0) or 0)),
                ],
                ["Descuentos", format_currency(float(pago_data.get("descuentos", 0) or 0))],
                ["TOTAL DEDUCCIONES", format_currency(total_deducc)],
                ["", ""],
                ["NETO A PAGAR", format_currency(float(pago_data["monto_neto"]))],
            ],
            colWidths=[3 * inch, 2.5 * inch],
        )
        desglose_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEABOVE", (0, 4), (-1, 4), 1, colors.black),
                    ("LINEBELOW", (0, 4), (-1, 4), 1, colors.black),
                    ("FONTNAME", (0, 4), (1, 4), "Helvetica-Bold"),
                    ("LINEABOVE", (0, 11), (-1, 11), 1, colors.black),
                    ("LINEBELOW", (0, 11), (-1, 11), 1, colors.black),
                    ("FONTNAME", (0, 11), (1, 11), "Helvetica-Bold"),
                    ("LINEABOVE", (0, 13), (-1, 13), 1.5, colors.darkblue),
                    ("LINEBELOW", (0, 13), (-1, 13), 1.5, colors.darkblue),
                    ("FONTNAME", (0, 13), (1, 13), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 13), (1, 13), 11),
                ]
            )
        )
        return desglose_table

    def _tabla_firma_recibo(self) -> Table:
        """Bloque de firma y fecha al pie del recibo"""
        firma_table = Table(
            [
                ["_________________________________"],
                ["Firma Recibido"],
                ["", ""],
                ["Fecha: _________________"],
            ],
            colWidths=[3 * inch],
        )
        firma_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        return firma_table

    def generate_reporte_empleados(self, empleados: list[Empleado], output_path: str) -> str:
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
            output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=18
        )

        story = []

        # Encabezado
        story.append(
            Paragraph(
                config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
                self.styles["CustomTitle"],
            )
        )

        story.append(Spacer(1, 0.2 * inch))

        # Título
        story.append(Paragraph("REPORTE DE EMPLEADOS", self.styles["CustomTitle"]))

        story.append(Spacer(1, 0.1 * inch))

        # Fecha
        story.append(
            Paragraph(
                f"Fecha: {format_date(date.today())} | Total: {len(empleados)} empleados",
                self.styles["CustomData"],
            )
        )

        story.append(Spacer(1, 0.2 * inch))

        # Tabla de empleados
        data = [["Cédula", "Nombre", "Cargo", "Departamento", "Tipo", "Salario"]]

        for emp in empleados:
            tipo_display = (
                emp.tipo_empleado.value.capitalize()
                if hasattr(emp.tipo_empleado, "value")
                else str(emp.tipo_empleado).capitalize()
            )
            data.append(
                [
                    str(emp.cedula),
                    emp.nombre_completo,
                    str(emp.cargo or ""),
                    str(emp.departamento or ""),
                    tipo_display,
                    format_currency(emp.salario_base),
                ]
            )

        tabla = Table(
            data, colWidths=[1 * inch, 2 * inch, 1.5 * inch, 1.5 * inch, 1 * inch, 1 * inch]
        )

        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]
            )
        )

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

    def _agregar_seccion_ficha(self, story, titulo: str, pares: list[tuple[str, str]]):
        """Agrega una sección tipo ficha si contiene al menos un dato"""
        pares = [
            (self._escape_pdf(label), self._escape_pdf(valor)) for label, valor in pares if valor
        ]
        if not pares:
            return
        story.append(Paragraph(titulo, self.styles["CustomSubtitle"]))
        filas = [
            [
                Paragraph(label, self.styles["FichaLabel"]),
                Paragraph(valor, self.styles["FichaValor"]),
            ]
            for label, valor in pares
        ]
        tabla = Table(filas, colWidths=[1.9 * inch, 4.9 * inch])
        tabla.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.lightgrey),
                ]
            )
        )
        story.append(KeepTogether([tabla, Spacer(1, 0.12 * inch)]))

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
            output_path, pagesize=A4, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=30
        )

        story = []

        story.append(
            Paragraph(
                config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
                self.styles["CustomTitle"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("FICHA DEL EMPLEADO", self.styles["CustomTitle"]))
        story.append(
            Paragraph(f"Fecha de emisión: {format_date(date.today())}", self.styles["CustomData"])
        )
        story.append(Spacer(1, 0.15 * inch))

        edad = empleado.edad
        antiguedad = empleado.antiguedad_anos

        # Datos personales
        self._agregar_seccion_ficha(
            story,
            "Datos Personales",
            [
                ("Nombre Completo", v(empleado.nombre_completo)),
                ("Cédula", v(empleado.cedula)),
                ("Fecha de Nacimiento", v(empleado.fecha_nacimiento)),
                ("Edad", f"{edad} años" if edad else ""),
                ("Género", v(empleado.genero)),
                ("Estado Civil", v(empleado.estado_civil)),
                ("Nacionalidad", v(empleado.nacionalidad)),
                ("Tipo de Sangre", v(empleado.tipo_sangre)),
            ],
        )

        # Contacto
        self._agregar_seccion_ficha(
            story,
            "Contacto y Emergencia",
            [
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
            ],
        )

        # Laboral
        estado_laboral = "Activo" if empleado.activo else "Inactivo"
        self._agregar_seccion_ficha(
            story,
            "Datos Laborales",
            [
                ("Puesto de Trabajo", v(empleado.cargo)),
                ("Departamento", v(empleado.departamento)),
                ("Tipo de Empleado", v(empleado.tipo_empleado)),
                ("Tipo de Contratación", v(empleado.tipo_contratacion)),
                ("Fecha de Ingreso", v(empleado.fecha_contratacion)),
                ("Fecha de Terminación", v(empleado.fecha_terminacion)),
                ("Salario Mensual", v(empleado.salario_base)),
                ("Estado Laboral", estado_laboral),
                ("Antigüedad", f"{antiguedad} años" if antiguedad else ""),
            ],
        )

        # Académico
        self._agregar_seccion_ficha(
            story,
            "Formación Académica",
            [
                ("Nivel Educativo", v(empleado.nivel_educativo)),
                ("Especialidad", v(empleado.especialidad)),
                ("Título de Secundaria", v(empleado.titulo_secundaria)),
                ("Título Universitario", v(empleado.titulo_obtenido)),
            ],
        )

        # Salud y bancarios
        self._agregar_seccion_ficha(
            story,
            "Salud y Datos Bancarios",
            [
                ("Institución Bancaria", v(empleado.institucion_bancaria)),
                ("Número de Cuenta", v(empleado.numero_cuenta)),
                ("Tipo de Cuenta", v(empleado.tipo_cuenta)),
                ("Carnet de Discapacidad", v(empleado.carnet_discapacidad)),
                ("Enfermedades Preexistentes/Crónicas", v(empleado.enfermedades_preexistentes)),
                ("Alergias Medicamentosas", v(empleado.alergias_medicamentosas)),
                ("Alergias Alimentarias o Ambientales", v(empleado.alergias_alimentarias)),
            ],
        )

        # Familia
        self._agregar_seccion_ficha(
            story,
            "Datos Familiares",
            [
                ("Hijos", v(empleado.hijos)),
            ],
        )

        self._agregar_seccion_ficha(
            story,
            "Observaciones",
            [
                ("Notas", v(empleado.observaciones)),
            ],
        )

        doc.build(story)
        return output_path

    def generate_reporte_nomina(
        self, pagos: list[dict], output_path: str, titulo_periodo: str | None = None
    ) -> str:
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
            bottomMargin=30,
        )

        story = [
            Paragraph(
                config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
                self.styles["CustomTitle"],
            ),
            Spacer(1, 0.15 * inch),
            Paragraph("PLANILLA DE NÓMINA", self.styles["CustomTitle"]),
            Paragraph(
                self._titulo_periodo_nomina(pagos, titulo_periodo), self.styles["CustomData"]
            ),
            Spacer(1, 0.15 * inch),
        ]

        filas, totales = self._filas_y_totales_nomina(pagos)
        filas.append(self._fila_totales_nomina(totales))

        tabla = Table(filas, repeatRows=1, colWidths=self._anchos_planilla_nomina())
        tabla.setStyle(TableStyle(self._estilo_planilla_nomina()))

        story.append(tabla)
        story.append(Spacer(1, 0.15 * inch))
        story.append(
            Paragraph(
                f"Total neto a pagar: <b>{format_currency(totales['neto'])}</b> | "
                f"Registros: {len(pagos)}",
                self.styles["CustomData"],
            )
        )

        doc.build(story)
        return output_path

    def _titulo_periodo_nomina(self, pagos: list[dict], titulo_periodo: str | None) -> str:
        """Resuelve el subtítulo de la planilla a partir del primer pago"""
        if titulo_periodo:
            return titulo_periodo
        inicio = pagos[0].get("periodo_inicio")
        fin = pagos[0].get("periodo_fin")
        if inicio and fin:
            return f"Periodo: {format_date(inicio)} a {format_date(fin)}"
        return f"Total de pagos: {len(pagos)}"

    def _filas_y_totales_nomina(
        self, pagos: list[dict]
    ) -> tuple[list[list[str]], dict[str, float]]:
        """Construye las filas de la planilla y acumula los totales en una pasada"""
        totales = {
            "salario": 0.0,
            "extras": 0.0,
            "isss": 0.0,
            "afp": 0.0,
            "isr": 0.0,
            "otras": 0.0,
            "descuentos": 0.0,
            "neto": 0.0,
        }
        filas = [
            [
                "No.",
                "Empleado",
                "Cédula",
                "Cargo",
                "Salario Base",
                "Extras",
                "ISSS",
                "AFP",
                "ISR",
                "Otras",
                "Descuentos",
                "Neto a Pagar",
            ]
        ]

        for indice, pago in enumerate(pagos, start=1):
            extras = self._flotante(pago.get("bonificaciones")) + self._flotante(
                pago.get("horas_extra")
            )
            filas.append(
                [
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
            )

            totales["salario"] += self._flotante(pago.get("salario_base"))
            totales["extras"] += extras
            totales["isss"] += self._flotante(pago.get("deduccion_seguro"))
            totales["afp"] += self._flotante(pago.get("deduccion_pension"))
            totales["isr"] += self._flotante(pago.get("deduccion_impuesto"))
            totales["otras"] += self._flotante(pago.get("otras_deducciones"))
            totales["descuentos"] += self._flotante(pago.get("descuentos"))
            totales["neto"] += self._flotante(pago.get("monto_neto"))

        return filas, totales

    def _fila_totales_nomina(self, totales: dict[str, float]) -> list[str]:
        """Fila final TOTALES de la planilla"""
        return [
            "TOTALES",
            "",
            "",
            "",
            format_currency(totales["salario"]),
            format_currency(totales["extras"]),
            format_currency(totales["isss"]),
            format_currency(totales["afp"]),
            format_currency(totales["isr"]),
            format_currency(totales["otras"]),
            format_currency(totales["descuentos"]),
            format_currency(totales["neto"]),
        ]

    def _anchos_planilla_nomina(self) -> list[float]:
        """Anchos de columna de la planilla (en pulgadas)"""
        return [
            0.4 * inch,
            1.9 * inch,
            1.0 * inch,
            1.5 * inch,
            0.85 * inch,
            0.7 * inch,
            0.65 * inch,
            0.65 * inch,
            0.65 * inch,
            0.65 * inch,
            0.8 * inch,
            0.85 * inch,
        ]

    def _estilo_planilla_nomina(self) -> list[tuple]:
        """Comandos de estilo de la planilla de nómina"""
        return [
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7.5),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
            ("GRID", (0, 0), (-1, -2), 0.4, colors.black),
            ("BACKGROUND", (0, -1), (-1, -1), colors.beige),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.darkblue),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

    def generate_reporte_incidencias(
        self, filas: list[dict], output_path: str, titulo: str | None = None
    ) -> str:
        """
        Genera un reporte de incidencias y permisos

        Args:
            filas: Lista de diccionarios con los datos de cada incidencia
                (claves: nombre_empleado, tipo_incidencia, fecha_inicio,
                fecha_fin, dias_solicitados, estado, motivo)
            output_path: Ruta donde se guardará el PDF
            titulo: Título adicional (empleado o periodo, opcional)

        Returns:
            Ruta del PDF generado

        Raises:
            ValueError: Si la lista está vacía
        """
        if not filas:
            raise ValueError("No hay incidencias para incluir en el reporte")

        config = self._get_configuracion()

        doc = SimpleDocTemplate(
            output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=48, bottomMargin=30
        )

        story = []
        story.append(
            Paragraph(
                config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
                self.styles["CustomTitle"],
            )
        )
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("REPORTE DE INCIDENCIAS Y PERMISOS", self.styles["CustomTitle"]))
        if titulo:
            story.append(Paragraph(titulo, self.styles["CustomData"]))
        story.append(Spacer(1, 0.15 * inch))

        encabezados = ["No.", "Empleado", "Tipo", "Desde", "Hasta", "Días", "Estado", "Motivo"]
        tabla_datos = [encabezados]
        total_dias = 0.0

        for indice, fila in enumerate(filas, start=1):
            dias = self._flotante(fila.get("dias_solicitados"))
            total_dias += dias
            motivo = str(fila.get("motivo", "") or "")
            if len(motivo) > 40:
                motivo = motivo[:40] + "..."
            tabla_datos.append(
                [
                    str(indice),
                    str(fila.get("nombre_empleado", "")),
                    str(fila.get("tipo_incidencia", "")),
                    format_date(fila.get("fecha_inicio")),
                    format_date(fila.get("fecha_fin")),
                    str(int(dias)) if dias == int(dias) else f"{dias:g}",
                    str(fila.get("estado", "")).capitalize(),
                    motivo,
                ]
            )

        tabla = Table(
            tabla_datos,
            repeatRows=1,
            colWidths=[
                0.4 * inch,
                1.5 * inch,
                1.0 * inch,
                0.95 * inch,
                0.95 * inch,
                0.5 * inch,
                0.9 * inch,
                1.2 * inch,
            ],
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(tabla)
        story.append(Spacer(1, 0.15 * inch))
        story.append(
            Paragraph(
                f"Total de incidencias: <b>{len(filas)}</b> | Días solicitados: <b>{int(total_dias)}</b>",
                self.styles["CustomData"],
            )
        )

        doc.build(story)
        return output_path

    def generate_reporte_vencimientos(
        self, filas: list[dict], output_path: str, titulo: str | None = None
    ) -> str:
        """
        Genera un control de vencimientos de documentos

        Args:
            filas: Lista de diccionarios con los datos de cada documento
                (claves: nombre_empleado, tipo_documento, titulo,
                fecha_vencimiento, estado)
            output_path: Ruta donde se guardará el PDF
            titulo: Título adicional (opcional)

        Returns:
            Ruta del PDF generado

        Raises:
            ValueError: Si la lista está vacía
        """
        if not filas:
            raise ValueError("No hay documentos para incluir en el control")

        config = self._get_configuracion()

        doc = SimpleDocTemplate(
            output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=48, bottomMargin=30
        )

        story = []
        story.append(
            Paragraph(
                config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"),
                self.styles["CustomTitle"],
            )
        )
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("CONTROL DE VENCIMIENTOS DE DOCUMENTOS", self.styles["CustomTitle"]))
        if titulo:
            story.append(Paragraph(titulo, self.styles["CustomData"]))
        story.append(Spacer(1, 0.15 * inch))

        encabezados = ["No.", "Empleado", "Tipo", "Título", "Vence", "Estado"]
        tabla_datos = [encabezados]
        conteos = {"Vigente": 0, "Por vencer": 0, "Vencido": 0}

        for indice, fila in enumerate(filas, start=1):
            estado = str(fila.get("estado", "")).capitalize()
            conteos[estado] = conteos.get(estado, 0) + 1
            titulo_doc = str(fila.get("titulo", "") or "")
            if len(titulo_doc) > 45:
                titulo_doc = titulo_doc[:45] + "..."
            tabla_datos.append(
                [
                    str(indice),
                    str(fila.get("nombre_empleado", "")),
                    str(fila.get("tipo_documento", "")),
                    titulo_doc,
                    format_date(fila.get("fecha_vencimiento")),
                    estado,
                ]
            )

        tabla = Table(
            tabla_datos,
            repeatRows=1,
            colWidths=[0.4 * inch, 1.8 * inch, 1.1 * inch, 2.1 * inch, 0.95 * inch, 1.0 * inch],
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),
                    ("FONTSIZE", (0, 1), (-1, -1), 7.5),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(tabla)
        story.append(Spacer(1, 0.15 * inch))
        resumen = " | ".join(f"{nombre}: <b>{cantidad}</b>" for nombre, cantidad in conteos.items())
        story.append(
            Paragraph(
                f"Total de documentos: <b>{len(filas)}</b> | {resumen}", self.styles["CustomData"]
            )
        )

        doc.build(story)
        return output_path

    # ------------------------------------------------------------------
    # Reportes nuevos: ingresos, asistencia, contratos, préstamos y liquidación
    # ------------------------------------------------------------------
    def generate_constancia_ingresos(
        self,
        empleado: Empleado,
        output_path: str,
        ingresos: dict | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        finalidad: str | None = None,
    ) -> str:
        """
        Genera una constancia de ingresos

        Args:
            empleado: Empleado titular de la constancia
            output_path: Ruta donde se guardará el PDF
            ingresos: Totales del período (bruto, deducciones, neto, aportes)
            desde: Inicio del período certificado
            hasta: Fin del período certificado
            finalidad: Uso declarado de la constancia
        """
        ingresos = ingresos or {}
        config = self._get_configuracion()
        doc = SimpleDocTemplate(
            output_path, pagesize=A4, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
        )

        story = [
            Paragraph(
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
                self.styles["CustomTitle"],
            ),
            Spacer(1, 0.15 * inch),
            Paragraph("CONSTANCIA DE INGRESOS", self.styles["CustomTitle"]),
            Spacer(1, 0.25 * inch),
        ]

        periodo = self._texto_periodo(desde, hasta)
        if periodo:
            story.append(Paragraph(f"Período certificado: <b>{periodo}</b>", self.styles["CustomData"]))
            story.append(Spacer(1, 0.1 * inch))

        story.append(
            Paragraph(
                f"Quien suscribe hace constar que <b>{escape(empleado.nombre_completo)}</b>, "
                f"portador(a) de la cédula de identidad <b>{escape(str(empleado.cedula))}</b>, "
                f"presta servicios en esta institución desempeñando el cargo de "
                f"<b>{escape(str(empleado.cargo or ''))}</b> en el departamento de "
                f"<b>{escape(str(empleado.departamento or ''))}</b>, devengando los ingresos "
                "que se detallan a continuación.",
                self.styles["CustomBody"],
            )
        )
        story.append(Spacer(1, 0.2 * inch))

        conceptos = [
            ("Salario base del período", ingresos.get("total_bruto")),
            ("Deducciones aplicadas", ingresos.get("total_deducciones")),
            ("Bonificaciones y horas extra", ingresos.get("total_extra")),
            ("Aportes patronales", ingresos.get("total_aportes_patronales")),
            ("Neto pagado", ingresos.get("total_neto")),
        ]
        tabla_datos = [["Concepto", "Monto"]]
        for concepto, monto in conceptos:
            tabla_datos.append([concepto, format_currency(float(monto or 0))])

        tabla = Table(tabla_datos, colWidths=[4.0 * inch, 2.0 * inch])
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(tabla)
        story.append(Spacer(1, 0.2 * inch))

        if ingresos.get("total_pagos") is not None:
            story.append(
                Paragraph(
                    f"La constancia comprende <b>{int(ingresos.get('total_pagos') or 0)}</b> "
                    "pago(s) registrados en el sistema.",
                    self.styles["CustomBody"],
                )
            )
        if finalidad:
            story.append(
                Paragraph(
                    f"Constancia que se expide para: <b>{escape(finalidad)}</b>",
                    self.styles["CustomData"],
                )
            )

        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("_______________________________", self.styles["CustomFooter"]))
        story.append(Paragraph("Departamento de Recursos Humanos", self.styles["CustomFooter"]))
        story.append(
            Paragraph(f"Emitida el {format_date(date.today())}", self.styles["CustomFooter"])
        )

        doc.build(story)
        return output_path

    def generate_liquidacion(
        self,
        empleado: Empleado,
        desglose: dict,
        output_path: str,
        fecha_egreso: date | None = None,
        contrato: str | None = None,
    ) -> str:
        """
        Genera el recibo de liquidación (finiquito) de un empleado

        Args:
            empleado: Empleado que cesa funciones
            desglose: Resultado del finiquito (claves: prestaciones,
                indemnizacion, preaviso, vacaciones, bono_vacacional,
                aguinaldo, anticipos, otras_deducciones, neto...)
            output_path: Ruta donde se guardará el PDF
            fecha_egreso: Fecha efectiva del egreso
            contrato: Número del contrato terminado
        """
        config = self._get_configuracion()
        doc = SimpleDocTemplate(
            output_path, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=48, bottomMargin=42
        )

        story = [
            Paragraph(
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
                self.styles["CustomTitle"],
            ),
            Spacer(1, 0.15 * inch),
            Paragraph("RECIBO DE LIQUIDACIÓN LABORAL", self.styles["CustomTitle"]),
            Spacer(1, 0.2 * inch),
        ]

        datos_empleado = [
            ["Empleado", escape(empleado.nombre_completo)],
            ["Cédula", escape(str(empleado.cedula or ''))],
            ["Cargo", escape(str(empleado.cargo or ''))],
            ["Ingreso", format_date(empleado.fecha_contratacion)],
            ["Egreso", format_date(fecha_egreso or date.today())],
            ["Antigüedad", f"{float(desglose.get('anos_servicio') or 0):.2f} año(s)"],
        ]
        if contrato:
            datos_empleado.append(["Contrato", escape(str(contrato))])
        if desglose.get("motivo"):
            datos_empleado.append(["Motivo", escape(str(desglose.get("motivo")))])

        tabla_info = Table(datos_empleado, colWidths=[1.5 * inch, 5.0 * inch])
        tabla_info.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.darkgray),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(tabla_info)
        story.append(Spacer(1, 0.25 * inch))

        asignaciones = [
            ("Prestaciones acumuladas", desglose.get("prestaciones")),
            ("Indemnización", desglose.get("indemnizacion")),
            ("Preaviso", desglose.get("preaviso")),
            ("Vacaciones no disfrutadas", desglose.get("vacaciones")),
            ("Bono vacacional", desglose.get("bono_vacacional")),
            ("Aguinaldo", desglose.get("aguinaldo")),
        ]
        deducciones = [
            ("Anticipos y préstamos pendientes", desglose.get("anticipos")),
            ("Otras deducciones", desglose.get("otras_deducciones")),
        ]

        filas = [["Concepto", "Asignaciones", "Deducciones"]]
        for concepto, monto in asignaciones:
            filas.append([concepto, format_currency(float(monto or 0)), "-"])
        for concepto, monto in deducciones:
            filas.append([concepto, "-", format_currency(float(monto or 0))])
        filas.append(
            [
                "TOTALES",
                format_currency(float(desglose.get("total_asignaciones") or 0)),
                format_currency(float(desglose.get("total_deducciones") or 0)),
            ]
        )
        filas.append(["NETO A PAGAR", format_currency(float(desglose.get("neto") or 0)), ""])

        tabla = Table(filas, colWidths=[3.4 * inch, 1.6 * inch, 1.6 * inch])
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.whitesmoke]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(tabla)
        story.append(Spacer(1, 0.35 * inch))
        story.append(
            Paragraph(
                "El empleado declara recibir el monto neto indicado como pago total de "
                "sus prestaciones y demás conceptos derivados de la relación laboral.",
                self.styles["CustomBody"],
            )
        )
        story.append(Spacer(1, 0.5 * inch))
        firma = Table(
            [["_________________________", "_________________________"]],
            colWidths=[3.4 * inch, 3.2 * inch],
        )
        firma.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(firma)
        story.append(
            Paragraph(
                "Firma del empleado&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Por la institución",
                self.styles["CustomFooter"],
            )
        )

        doc.build(story)
        return output_path

    def generate_reporte_asistencia(
        self,
        filas: list[dict],
        output_path: str,
        desde: date | None = None,
        hasta: date | None = None,
        resumen: dict | None = None,
    ) -> str:
        """
        Genera un reporte de asistencia por período

        Args:
            filas: Registros con empleado, fecha, tipo, horas, tardanza y horas extra
            output_path: Ruta donde se guardará el PDF
            desde: Inicio del período
            hasta: Fin del período
            resumen: Totales del período (opcional)
        """
        if not filas:
            raise ValueError("No hay registros de asistencia para el reporte")

        config = self._get_configuracion()
        doc = SimpleDocTemplate(
            output_path, pagesize=landscape(A4), rightMargin=28, leftMargin=28, topMargin=40, bottomMargin=28
        )

        story = [
            Paragraph(
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
                self.styles["CustomTitle"],
            ),
            Spacer(1, 0.12 * inch),
            Paragraph("REPORTE DE ASISTENCIA", self.styles["CustomTitle"]),
        ]
        periodo = self._texto_periodo(desde, hasta)
        if periodo:
            story.append(Paragraph(f"Período: <b>{periodo}</b>", self.styles["CustomData"]))
        story.append(Spacer(1, 0.12 * inch))

        encabezados = [
            "No.",
            "Empleado",
            "Fecha",
            "Tipo",
            "Entrada",
            "Salida",
            "Horas",
            "Tardanza",
            "H. extra",
            "Observaciones",
        ]
        tabla_datos = [encabezados]
        total_horas = 0.0
        total_extra = 0.0
        for indice, fila in enumerate(filas, start=1):
            horas = float(fila.get("horas_trabajadas") or 0)
            extra = float(fila.get("horas_extra") or 0)
            total_horas += horas
            total_extra += extra
            observaciones = str(fila.get("observaciones") or "")
            if len(observaciones) > 40:
                observaciones = observaciones[:40] + "..."
            tabla_datos.append(
                [
                    str(indice),
                    str(fila.get("empleado", ""))[:30],
                    format_date(fila.get("fecha")),
                    str(fila.get("tipo", "")).capitalize(),
                    str(fila.get("hora_entrada") or "-"),
                    str(fila.get("hora_salida") or "-"),
                    f"{horas:.2f}",
                    str(fila.get("minutos_tardanza") or 0),
                    f"{extra:.2f}",
                    observaciones,
                ]
            )

        tabla = Table(
            tabla_datos,
            repeatRows=1,
            colWidths=[
                0.35 * inch,
                1.9 * inch,
                0.85 * inch,
                0.85 * inch,
                0.7 * inch,
                0.7 * inch,
                0.6 * inch,
                0.7 * inch,
                0.7 * inch,
                1.7 * inch,
            ],
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (6, 0), (8, -1), "RIGHT"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(tabla)
        story.append(Spacer(1, 0.1 * inch))

        partes = [
            f"Registros: <b>{len(filas)}</b>",
            f"Horas trabajadas: <b>{total_horas:.2f}</b>",
            f"Horas extra: <b>{total_extra:.2f}</b>",
        ]
        if resumen:
            partes.append(f"Faltas: <b>{int(resumen.get('faltas_injustificadas') or 0)}</b>")
            partes.append(
                f"Tardanzas: <b>{int(resumen.get('minutos_tardanza') or 0)} min</b>"
            )
        story.append(Paragraph(" | ".join(partes), self.styles["CustomData"]))

        doc.build(story)
        return output_path

    def generate_reporte_contratos(
        self,
        filas: list[dict],
        output_path: str,
        titulo: str | None = None,
    ) -> str:
        """
        Genera un reporte de contratos laborales

        Args:
            filas: Contratos con número, empleado, tipo, fechas, salario y estado
            output_path: Ruta donde se guardará el PDF
            titulo: Encabezado adicional (por ejemplo "Por vencer")
        """
        if not filas:
            raise ValueError("No hay contratos para incluir en el reporte")

        config = self._get_configuracion()
        doc = SimpleDocTemplate(
            output_path, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=28
        )

        story = [
            Paragraph(
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
                self.styles["CustomTitle"],
            ),
            Spacer(1, 0.12 * inch),
            Paragraph("REPORTE DE CONTRATOS LABORALES", self.styles["CustomTitle"]),
        ]
        if titulo:
            story.append(Paragraph(escape(titulo), self.styles["CustomData"]))
        story.append(Spacer(1, 0.12 * inch))

        encabezados = [
            "No.",
            "Número",
            "Empleado",
            "Tipo",
            "Cargo",
            "Inicio",
            "Fin",
            "Días",
            "Salario",
            "Estado",
        ]
        tabla_datos = [encabezados]
        total_salarios = 0.0
        for indice, fila in enumerate(filas, start=1):
            salario = float(fila.get("salario_pactado") or 0)
            total_salarios += salario
            dias = fila.get("dias_para_vencer")
            tabla_datos.append(
                [
                    str(indice),
                    str(fila.get("numero", "")),
                    str(fila.get("empleado", ""))[:28],
                    str(fila.get("tipo", "")).capitalize(),
                    str(fila.get("cargo", ""))[:22],
                    format_date(fila.get("fecha_inicio")),
                    format_date(fila.get("fecha_fin")) if fila.get("fecha_fin") else "Indefinido",
                    "-" if dias in (None, "") else str(dias),
                    format_currency(salario),
                    str(fila.get("estado", "")).capitalize(),
                ]
            )

        tabla = Table(
            tabla_datos,
            repeatRows=1,
            colWidths=[
                0.35 * inch,
                1.1 * inch,
                1.9 * inch,
                0.85 * inch,
                1.5 * inch,
                0.8 * inch,
                0.95 * inch,
                0.45 * inch,
                0.95 * inch,
                0.85 * inch,
            ],
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (7, 0), (8, -1), "RIGHT"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(tabla)
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                f"Total de contratos: <b>{len(filas)}</b> | "
                f"Monto mensual comprometido: <b>{format_currency(total_salarios)}</b>",
                self.styles["CustomData"],
            )
        )

        doc.build(story)
        return output_path

    def generate_reporte_prestamos(
        self,
        filas: list[dict],
        output_path: str,
        titulo: str | None = None,
    ) -> str:
        """
        Genera un reporte de anticipos y préstamos

        Args:
            filas: Préstamos con empleado, tipo, montos, cuotas, saldo y estado
            output_path: Ruta donde se guardará el PDF
            titulo: Encabezado adicional
        """
        if not filas:
            raise ValueError("No hay préstamos para incluir en el reporte")

        config = self._get_configuracion()
        doc = SimpleDocTemplate(
            output_path, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=28
        )

        story = [
            Paragraph(
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
                self.styles["CustomTitle"],
            ),
            Spacer(1, 0.12 * inch),
            Paragraph("REPORTE DE ANTICIPOS Y PRÉSTAMOS", self.styles["CustomTitle"]),
        ]
        if titulo:
            story.append(Paragraph(escape(titulo), self.styles["CustomData"]))
        story.append(Spacer(1, 0.12 * inch))

        encabezados = [
            "No.",
            "Empleado",
            "Tipo",
            "Monto",
            "Cuota",
            "Cuotas",
            "Pagadas",
            "Saldo",
            "Avance",
            "Estado",
        ]
        tabla_datos = [encabezados]
        total_otorgado = 0.0
        total_saldo = 0.0
        for indice, fila in enumerate(filas, start=1):
            monto = float(fila.get("monto") or 0)
            saldo = float(fila.get("saldo") or 0)
            total_otorgado += monto
            total_saldo += saldo
            tabla_datos.append(
                [
                    str(indice),
                    str(fila.get("empleado", ""))[:30],
                    str(fila.get("tipo", "")).capitalize(),
                    format_currency(monto),
                    format_currency(float(fila.get("monto_cuota") or 0)),
                    str(fila.get("numero_cuotas") or 0),
                    str(fila.get("cuotas_pagadas") or 0),
                    format_currency(saldo),
                    f"{float(fila.get('porcentaje_pagado') or 0):.0f}%",
                    str(fila.get("estado", "")).capitalize(),
                ]
            )

        tabla = Table(
            tabla_datos,
            repeatRows=1,
            colWidths=[
                0.35 * inch,
                2.1 * inch,
                0.9 * inch,
                0.95 * inch,
                0.95 * inch,
                0.6 * inch,
                0.65 * inch,
                0.95 * inch,
                0.6 * inch,
                0.95 * inch,
            ],
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 7.5),
                    ("FONTSIZE", (0, 1), (-1, -1), 7),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (3, 0), (7, -1), "RIGHT"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(tabla)
        story.append(Spacer(1, 0.1 * inch))
        story.append(
            Paragraph(
                f"Operaciones: <b>{len(filas)}</b> | Total otorgado: "
                f"<b>{format_currency(total_otorgado)}</b> | Saldo pendiente: "
                f"<b>{format_currency(total_saldo)}</b>",
                self.styles["CustomData"],
            )
        )

        doc.build(story)
        return output_path

    def generate_reporte_anual_empleado(
        self,
        empleado: Empleado,
        filas: list[dict],
        output_path: str,
        anio: int | None = None,
    ) -> str:
        """
        Genera el resumen anual de pagos de un empleado

        Args:
            empleado: Empleado del resumen
            filas: Pagos del año (período, tipo, bruto, deducciones, neto)
            output_path: Ruta donde se guardará el PDF
            anio: Año del resumen
        """
        if not filas:
            raise ValueError("No hay pagos registrados para el resumen anual")

        config = self._get_configuracion()
        doc = SimpleDocTemplate(
            output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=48, bottomMargin=30
        )

        story = [
            Paragraph(
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
                self.styles["CustomTitle"],
            ),
            Spacer(1, 0.12 * inch),
            Paragraph(
                f"RESUMEN ANUAL DE PAGOS {anio or date.today().year}", self.styles["CustomTitle"]
            ),
            Spacer(1, 0.12 * inch),
            Paragraph(
                f"Empleado: <b>{escape(empleado.nombre_completo)}</b> | "
                f"Cédula: <b>{escape(str(empleado.cedula or ''))}</b>",
                self.styles["CustomData"],
            ),
            Spacer(1, 0.12 * inch),
        ]

        encabezados = ["No.", "Período", "Tipo", "Bruto", "Deducciones", "Neto"]
        tabla_datos = [encabezados]
        total_bruto = 0.0
        total_deducciones = 0.0
        total_neto = 0.0
        for indice, fila in enumerate(filas, start=1):
            bruto = float(fila.get("monto_bruto") or 0)
            deducciones = float(fila.get("total_deducciones") or 0)
            neto = float(fila.get("monto_neto") or 0)
            total_bruto += bruto
            total_deducciones += deducciones
            total_neto += neto
            tabla_datos.append(
                [
                    str(indice),
                    f"{format_date(fila.get('periodo_inicio'))} - "
                    f"{format_date(fila.get('periodo_fin'))}",
                    str(fila.get("tipo_pago", "")).capitalize(),
                    format_currency(bruto),
                    format_currency(deducciones),
                    format_currency(neto),
                ]
            )
        tabla_datos.append(
            [
                "",
                "TOTALES",
                "",
                format_currency(total_bruto),
                format_currency(total_deducciones),
                format_currency(total_neto),
            ]
        )

        tabla = Table(
            tabla_datos,
            repeatRows=1,
            colWidths=[0.4 * inch, 2.0 * inch, 1.1 * inch, 1.0 * inch, 1.15 * inch, 1.0 * inch],
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(tabla)
        story.append(Spacer(1, 0.15 * inch))
        story.append(
            Paragraph(
                f"Pagos del año: <b>{len(filas)}</b> | Promedio neto: "
                f"<b>{format_currency(total_neto / len(filas))}</b>",
                self.styles["CustomData"],
            )
        )

        doc.build(story)
        return output_path

    def _texto_periodo(self, desde: date | None, hasta: date | None) -> str:
        """Texto legible del período de un reporte (cadena vacía si no se indicó)"""
        if desde and hasta:
            return f"{format_date(desde)} a {format_date(hasta)}"
        if desde:
            return f"desde {format_date(desde)}"
        if hasta:
            return f"hasta {format_date(hasta)}"
        return ""

    def generate_reporte_alertas(self, alertas: list[dict], output_path: str) -> str:
        """
        Genera el reporte de alertas vigentes del sistema

        Args:
            alertas: Alertas con titulo, severidad, cantidad y descripción
            output_path: Ruta donde se guardará el PDF
        """
        if not alertas:
            raise ValueError("No hay alertas vigentes para el reporte")

        config = self._get_configuracion()
        doc = SimpleDocTemplate(
            output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=48, bottomMargin=30
        )

        story = [
            Paragraph(
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
                self.styles["CustomTitle"],
            ),
            Spacer(1, 0.12 * inch),
            Paragraph("REPORTE DE ALERTAS DEL SISTEMA", self.styles["CustomTitle"]),
            Spacer(1, 0.12 * inch),
        ]

        for alerta in alertas:
            severidad = str(alerta.get("severidad", "")).capitalize()
            story.append(
                Paragraph(
                    f"<b>{escape(str(alerta.get('titulo', '')))}</b> "
                    f"({severidad}, {int(alerta.get('cantidad') or 0)} caso(s))",
                    self.styles["CustomSubtitle"],
                )
            )
            story.append(
                Paragraph(escape(str(alerta.get("descripcion", ""))), self.styles["CustomData"])
            )
            detalles = alerta.get("detalles") or []
            if detalles:
                lista = Table(
                    [["• " + escape(str(detalle))] for detalle in detalles],
                    colWidths=[6.5 * inch],
                )
                lista.setStyle(
                    TableStyle(
                        [
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("LEFTPADDING", (0, 0), (-1, -1), 12),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ]
                    )
                )
                story.append(lista)
            story.append(Spacer(1, 0.12 * inch))

        story.append(
            Paragraph(
                f"Total de alertas: <b>{len(alertas)}</b> | "
                f"Generado el {format_date(date.today())}",
                self.styles["CustomFooter"],
            )
        )

        doc.build(story)
        return output_path


# Instancia global del generador de PDFs
pdf_generator = PDFGenerator()
