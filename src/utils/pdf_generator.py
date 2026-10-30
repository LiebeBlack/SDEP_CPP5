"""
PDF Generator
Módulo de generación de documentos PDF
"""

import re
import threading
import unicodedata
from datetime import date, datetime
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models import Empleado
from src.utils.helpers import format_currency, format_date

# Expresiones del procesador de plantillas: se compilan una sola vez y no en
# cada línea de cada documento (antes se recompilaban por línea).
_PATRON_CAMPO = re.compile(r"\{\{?\s*([^}\s]{1,40})\s*\}?\}")
_PATRON_NEGRITA = re.compile(r"\*\*(.+?)\*\*")
_PATRON_CURSIVA = re.compile(r"\*(.+?)\*")

# Los estilos de ReportLab son inmutables una vez creados: se construyen una vez
# por proceso en lugar de repetir la hoja de estilos base en cada PDF.
_ESTILOS: Any = None
_CANDADO_ESTILOS = threading.Lock()


def _normalizar_clave(clave: str) -> str:
    """Forma canónica de un campo: sin acentos, sin mayúsculas y con guiones bajos.

    Así «{{Cédula}}», «{{cédula }}» y «{{Cedula}}» resuelven al mismo dato que
    «{{cedula}}», que es lo que escriben las plantillas y lo que inserta la app.
    """
    sin_acentos = unicodedata.normalize("NFD", str(clave).strip().lower())
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9_]+", "_", sin_acentos).strip("_")


def _resolver_campo(coincidencia: re.Match, valores: dict, normalizados: dict) -> str:
    """Valor de un marcador; si no existe se deja el texto original."""
    crudo = coincidencia.group(1)
    if crudo in valores:
        return str(valores[crudo])
    return str(normalizados.get(_normalizar_clave(crudo), coincidencia.group(0)))


# Campos que el procesador de plantillas sabe completar. Es la lista que la
# app móvil ofrece como chips y la que el escritorio usa para avisar de
# título y marcadores mal escritos.
CAMPOS_PLANTILLA: tuple[str, ...] = (
    "nombre",
    "nombre_completo",
    "nombres",
    "apellidos",
    "cedula",
    "cargo",
    "departamento",
    "tipo_empleado",
    "salario",
    "salario_letras",
    "fecha_contratacion",
    "fecha_emision",
    "fecha_emision_larga",
    "dia_emision",
    "mes_emision",
    "anio_emision",
    "institucion",
    "nivel_educativo",
    "especialidad",
    "titulo_obtenido",
    "antiguedad",
    "tipo_contratacion",
    "telefono",
    "celular",
    "correo",
    "direccion",
    "ciudad",
    "estado",
    "nacionalidad",
    "genero",
    "estado_civil",
    "fecha_nacimiento",
    "edad",
)


# --- Valores derivados -------------------------------------------------------
#
# Las constancias piden datos que no están guardados como tal (monto en letras,
# antigüedad, fecha en palabras). Se calculan aquí, una sola vez por documento,
# para que todas las plantillas —teléfono, escritorio y nodo— impriman lo mismo.

_MESES_LARGOS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)

_UNIDADES_TEXTO = (
    "",
    "UNO",
    "DOS",
    "TRES",
    "CUATRO",
    "CINCO",
    "SEIS",
    "SIETE",
    "OCHO",
    "NUEVE",
    "DIEZ",
    "ONCE",
    "DOCE",
    "TRECE",
    "CATORCE",
    "QUINCE",
    "DIECISÉIS",
    "DIECISIETE",
    "DIECIOCHO",
    "DIECINUEVE",
    "VEINTE",
)
_DECENAS_TEXTO = (
    "",
    "",
    "VEINTE",
    "TREINTA",
    "CUARENTA",
    "CINCUENTA",
    "SESENTA",
    "SETENTA",
    "OCHENTA",
    "NOVENTA",
)
_CENTENAS_TEXTO = (
    "",
    "CIENTO",
    "DOSCIENTOS",
    "TRESCIENTOS",
    "CUATROCIENTOS",
    "QUINIENTOS",
    "SEISCIENTOS",
    "SETECIENTOS",
    "OCHOCIENTOS",
    "NOVECIENTOS",
)
_VEINTI_TEXTO = (
    "VEINTIÚN",
    "VEINTIDÓS",
    "VEINTITRÉS",
    "VEINTICUATRO",
    "VEINTICINCO",
    "VEINTISÉIS",
    "VEINTISIETE",
    "VEINTIOCHO",
    "VEINTINUEVE",
)


def _hasta_999(numero: int) -> str:
    """Número entre 1 y 999 escrito en palabras."""
    if numero <= 0:
        return ""
    if numero == 100:
        return "CIEN"
    centenas, resto = divmod(numero, 100)
    partes = [_CENTENAS_TEXTO[centenas]] if centenas else []
    if 0 < resto <= 20:
        partes.append(_UNIDADES_TEXTO[resto])
    elif 20 < resto < 30:
        partes.append(_VEINTI_TEXTO[resto - 21])
    else:
        decenas, unidades = divmod(resto, 10)
        if decenas:
            partes.append(_DECENAS_TEXTO[decenas])
        if unidades:
            partes.append("Y " + _UNIDADES_TEXTO[unidades])
    return " ".join(parte for parte in partes if parte)


def _entero_en_letras(numero: int) -> str:
    """Número entero no negativo escrito en palabras (hasta 999 999 999)."""
    if numero == 0:
        return "CERO"
    millones, resto = divmod(int(numero), 1_000_000)
    miles, unidades = divmod(resto, 1_000)
    partes = []
    if millones:
        partes.append("UN MILLÓN" if millones == 1 else f"{_hasta_999(millones)} MILLONES")
    if miles:
        partes.append("MIL" if miles == 1 else f"{_hasta_999(miles)} MIL")
    if unidades:
        partes.append(_hasta_999(unidades))
    texto = " ".join(partes)
    return texto[:-1] if texto.endswith("UNO") else texto


def monto_en_letras(monto: Any, moneda: str = "BOLÍVARES") -> str:
    """Monto con su expresión en palabras: «MIL OCHOCIENTOS CON 00/100».

    La parte entera se escribe en letras y los céntimos como fracción de 100,
    que es la forma habitual en las constancias de ingresos venezolanas.
    """
    # Sin dato se devuelve vacío: imprimir «CERO BOLÍVARES» haría creer que el
    # salario es cero, que no es lo mismo que no tenerlo registrado.
    if monto is None or (isinstance(monto, str) and not monto.strip()):
        return ""
    try:
        valor = round(float(monto), 2)
    except (TypeError, ValueError):
        return ""
    if valor < 0:
        return ""
    entero = int(valor)
    centimos = int(round((valor - entero) * 100))
    if centimos == 100:
        entero += 1
        centimos = 0
    if entero > 999_999_999:
        return ""
    return f"{_entero_en_letras(entero)} {moneda} CON {centimos:02d}/100"


def _fecha_larga(valor: Any) -> str:
    """«30 de octubre de 2026» a partir de una fecha o de un texto ISO."""
    if isinstance(valor, datetime):
        fecha = valor.date()
    elif isinstance(valor, date):
        fecha = valor
    else:
        texto = str(valor or "").strip()
        if len(texto) < 10:
            return texto
        try:
            fecha = date.fromisoformat(texto[:10])
        except ValueError:
            return texto
    return f"{fecha.day} de {_MESES_LARGOS[fecha.month - 1]} de {fecha.year}"


def _antiguedad_legible(desde: Any, hasta: Any = None) -> str:
    """Antigüedad en años y meses: «7 años y 4 meses»."""
    if not isinstance(desde, date):
        return ""
    referencia = hasta if isinstance(hasta, date) else date.today()
    if referencia < desde:
        return ""
    meses = (referencia.year - desde.year) * 12 + (referencia.month - desde.month)
    if referencia.day < desde.day:
        meses -= 1
    anios, resto = divmod(max(meses, 0), 12)
    partes = []
    if anios:
        partes.append(f"{anios} {'año' if anios == 1 else 'años'}")
    if resto:
        partes.append(f"{resto} {'mes' if resto == 1 else 'meses'}")
    return " y ".join(partes) or "menos de un mes"


def campos_desconocidos(plantilla: str) -> list[str]:
    """Marcadores que la plantilla usa y el generador no sabe completar.

    Sirve para avisar antes de emitir: sin esto, un `{{cargo_empleado}}`
    inventado termina impreso tal cual en el documento.
    """
    conocidas = {_normalizar_clave(clave) for clave in CAMPOS_PLANTILLA}
    desconocidos: list[str] = []
    for coincidencia in _PATRON_CAMPO.finditer(plantilla or ""):
        crudo = coincidencia.group(1)
        if _normalizar_clave(crudo) not in conocidas and crudo not in desconocidos:
            desconocidos.append(crudo)
    return desconocidos


def _dato(fila: dict, *claves: str, defecto: Any = "") -> Any:
    """Devuelve el primer valor presente de una fila (admite varios nombres)."""
    for clave in claves:
        if clave in fila and fila[clave] is not None:
            return fila[clave]
    return defecto


def _estilos_compartidos() -> Any:
    """Hoja de estilos única del proceso.

    ReportLab la trata como solo lectura (las ``ParagraphStyle`` no se mutan
    después de crearse), así que reconstruirla en cada documento era trabajo
    repetido en cada constancia pedida desde el teléfono.
    """
    global _ESTILOS
    if _ESTILOS is None:
        with _CANDADO_ESTILOS:
            if _ESTILOS is None:
                creador = PDFGenerator.__new__(PDFGenerator)
                creador.styles = getSampleStyleSheet()
                creador._setup_custom_styles()
                _ESTILOS = creador.styles
    return _ESTILOS


class PDFGenerator:
    """Generador de documentos PDF"""

    def __init__(self):
        self.styles = _estilos_compartidos()
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
        from src.config import db_config
        from src.services import ConfiguracionService

        session = db_config.get_session()
        try:
            config_service = ConfiguracionService(session)
            return config_service.obtener_configuracion_general()
        finally:
            db_config.close_session(session)

    def generate_constancia_plantilla(
        self,
        empleado: Empleado,
        plantilla_markdown: str,
        output_path: str,
        titulo_documento: str = "CONSTANCIA DE TRABAJO",
        configuracion: dict | None = None,
    ) -> str:
        """Genera una constancia a partir de Markdown confiable y datos del empleado.

        ``configuracion`` evita abrir una segunda sesión de base de datos cuando
        quien llama ya tiene una abierta (el servidor móvil, por ejemplo).
        """
        if not isinstance(plantilla_markdown, str) or not plantilla_markdown.strip():
            raise ValueError("La plantilla Markdown está vacía")
        if len(plantilla_markdown.encode("utf-8")) > 65_536:
            raise ValueError("La plantilla Markdown no puede superar 64 KB")

        config = configuracion if configuracion is not None else self._get_configuracion()
        nombre_institucion = str(config.get("nombre_institucion") or "INSTITUCIÓN EDUCATIVA")
        titulo_documento = str(titulo_documento or "CONSTANCIA DE TRABAJO").strip()[:120]
        tipo_empleado = (
            empleado.tipo_empleado.value
            if hasattr(empleado.tipo_empleado, "value")
            else str(empleado.tipo_empleado or "")
        )

        def _texto(objeto: Any, atributo: str) -> str:
            """Campo de texto del empleado, ya sea enum, nulo o cadena."""
            valor = getattr(objeto, atributo, None)
            if valor is None:
                return ""
            return str(getattr(valor, "value", valor)).replace("_", " ").strip()

        hoy = date.today()
        fecha_nacimiento = getattr(empleado, "fecha_nacimiento", None)
        edad = getattr(empleado, "edad", None)
        valores = {
            "nombre": empleado.nombre_completo or "",
            "nombre_completo": empleado.nombre_completo or "",
            "nombres": getattr(empleado, "nombres", "") or "",
            "apellidos": getattr(empleado, "apellidos", "") or "",
            "cedula": empleado.cedula or "",
            "cargo": empleado.cargo or "",
            "departamento": empleado.departamento or "",
            "tipo_empleado": str(tipo_empleado).upper(),
            "fecha_contratacion": format_date(empleado.fecha_contratacion),
            "salario": format_currency(empleado.salario_base),
            "salario_letras": monto_en_letras(empleado.salario_base),
            "fecha_emision": format_date(hoy),
            "fecha_emision_larga": _fecha_larga(hoy),
            "dia_emision": str(hoy.day),
            "mes_emision": _MESES_LARGOS[hoy.month - 1],
            "anio_emision": str(hoy.year),
            "institucion": nombre_institucion,
            "nivel_educativo": getattr(empleado, "nivel_educativo", None) or "",
            "especialidad": getattr(empleado, "especialidad", None) or "",
            "titulo_obtenido": getattr(empleado, "titulo_obtenido", None) or "",
            "antiguedad": _antiguedad_legible(empleado.fecha_contratacion, hoy),
            "tipo_contratacion": _texto(empleado, "tipo_contratacion"),
            "telefono": _texto(empleado, "telefono"),
            "celular": _texto(empleado, "celular"),
            "correo": _texto(empleado, "email"),
            "direccion": _texto(empleado, "direccion"),
            "ciudad": _texto(empleado, "ciudad"),
            "estado": _texto(empleado, "estado"),
            "nacionalidad": _texto(empleado, "nacionalidad"),
            "genero": _texto(empleado, "genero"),
            "estado_civil": _texto(empleado, "estado_civil"),
            "fecha_nacimiento": format_date(fecha_nacimiento),
            "edad": f"{edad} años" if edad else "",
        }
        valores_normalizados = {_normalizar_clave(clave): valor for clave, valor in valores.items()}
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=54,
            bottomMargin=36,
        )
        story = [
            Paragraph(
                escape(nombre_institucion),
                self.styles["CustomTitle"],
            ),
            Paragraph(escape(str(titulo_documento)[:120]), self.styles["CustomSubtitle"]),
            Spacer(1, 0.2 * inch),
        ]

        lineas = plantilla_markdown.splitlines()
        if len(lineas) > 600:
            raise ValueError("La plantilla Markdown supera el máximo de 600 líneas")
        # El título ya va en la cabecera del documento: si la plantilla abre con
        # un encabezado igual (lo normal, porque su primer «#» es el título), se
        # omite para que no aparezca impreso dos veces.
        titulo_cabecera = _normalizar_clave(titulo_documento)
        primer_encabezado = True
        for linea in lineas:
            linea_limpia = linea.strip()
            if linea_limpia.startswith("### "):
                nivel_titulo = 3
                linea_limpia = linea_limpia[4:].strip()
            elif linea_limpia.startswith("## "):
                nivel_titulo = 2
                linea_limpia = linea_limpia[3:].strip()
            elif linea_limpia.startswith("# "):
                nivel_titulo = 1
                linea_limpia = linea_limpia[2:].strip()
            else:
                nivel_titulo = 0
            if nivel_titulo and primer_encabezado:
                primer_encabezado = False
                if _normalizar_clave(linea_limpia) == titulo_cabecera:
                    continue
            texto = escape(linea_limpia)
            texto = _PATRON_CAMPO.sub(
                lambda match: escape(_resolver_campo(match, valores, valores_normalizados)),
                texto,
            )
            if not texto:
                story.append(Spacer(1, 6))
            elif nivel_titulo:
                story.append(Paragraph(texto, self.styles[f"Heading{nivel_titulo}"]))
            else:
                texto = _PATRON_NEGRITA.sub(r"<b>\1</b>", texto)
                texto = _PATRON_CURSIVA.sub(r"<i>\1</i>", texto)
                if texto.startswith("- "):
                    texto = "&#8226; " + texto[2:]
                story.append(Paragraph(texto, self.styles["CustomBody"]))

        # Si la plantilla ya trae su bloque de firma, no se añade otro encima.
        if "firma" not in plantilla_markdown.lower():
            story.extend(
                [
                    Spacer(1, 0.5 * inch),
                    Table(
                        [
                            ["____________________________", ""],
                            ["Firma autorizada", "SELLO INSTITUCIONAL"],
                            [escape(nombre_institucion), "Fecha: ______________"],
                        ],
                        colWidths=[3 * inch, 3 * inch],
                        rowHeights=[0.28 * inch, 0.72 * inch, 0.28 * inch],
                        style=TableStyle(
                            [
                                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                                ("FONTSIZE", (0, 0), (-1, -1), 9),
                                ("BOX", (1, 1), (1, 1), 1, colors.darkblue),
                                ("TOPPADDING", (0, 0), (-1, -1), 5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                            ]
                        ),
                    ),
                ]
            )
        doc.build(story)
        return output_path

    def generate_constancia_trabajo(
        self,
        empleado: Empleado,
        output_path: str,
        configuracion: dict | None = None,
    ) -> str:
        """
        Genera una constancia de trabajo

        Args:
            empleado: Objeto Empleado
            output_path: Ruta donde se guardará el PDF
            configuracion: configuración ya cargada (opcional)

        Returns:
            Ruta del PDF generado
        """
        config = configuracion if configuracion is not None else self._get_configuracion()

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
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
                self.styles["CustomTitle"],
            )
        )

        if config.get("direccion"):
            story.append(Paragraph(escape(str(config["direccion"])), self.styles["CustomFooter"]))

        if config.get("telefono"):
            story.append(
                Paragraph(
                    f"Teléfono: {escape(str(config['telefono']))}", self.styles["CustomFooter"]
                )
            )

        story.append(Spacer(1, 0.5 * inch))

        # Título del documento
        story.append(Paragraph("CONSTANCIA DE TRABAJO", self.styles["CustomTitle"]))

        story.append(Spacer(1, 0.3 * inch))

        # Fecha
        fecha_actual = format_date(date.today())
        story.append(Paragraph(f"Fecha: {fecha_actual}", self.styles["CustomData"]))

        story.append(Spacer(1, 0.3 * inch))

        # Escapar texto externo antes de insertarlo en el marcado de ReportLab.
        nombre_institucion = escape(str(config.get("nombre_institucion", "Institución")))
        nombre_empleado = escape(str(empleado.nombre_completo or ""))
        cedula_empleado = escape(str(empleado.cedula or ""))
        cuerpo = f"""
        Por medio de la presente, la {nombre_institucion}
        certifica que el(la) Sr(a). <b>{nombre_empleado}</b>,
        portador(a) de la cédula de identidad N° <b>{cedula_empleado}</b>,
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
        Actualmente desempeña el cargo de <b>{escape(str(empleado.cargo or 'No especificado'))}</b> en el departamento de
        <b>{escape(str(empleado.departamento or 'No especificado'))}</b>, con una categoría de <b>{escape(tipo_str)}</b>.
        """

        story.append(Paragraph(datos_cargo, self.styles["CustomBody"]))

        story.append(Spacer(1, 0.2 * inch))

        # Condiciones laborales
        condiciones = f"""
        Devengando un salario mensual de <b>{escape(format_currency(empleado.salario_base))}</b>.
        """

        story.append(Paragraph(condiciones, self.styles["CustomBody"]))

        story.append(Spacer(1, 0.4 * inch))

        # Cierre
        cierre = """
        Esta constancia se expide a solicitud del interesado para los fines que
        considere conveniente.
        """

        story.append(Paragraph(cierre, self.styles["CustomBody"]))

        story.append(Spacer(1, 1.5 * inch))

        # Espacio para firma
        firma_table = Table(
            [
                ["_________________________________", "_________________________________"],
                ["Firma Autorizada", "Sello"],
                ["", ""],
                [nombre_institucion, ""],
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
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
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
        Por medio de la presente se hace constar que <b>{escape(str(empleado.nombre_completo or ''))}</b>, 
        portador(a) de la cédula de identidad N° <b>{escape(str(empleado.cedula or ''))}</b>, 
        cuenta con el nivel educativo de <b>{escape(str(empleado.nivel_educativo or 'No especificado'))}</b>.
        """

        story.append(Paragraph(cuerpo, self.styles["CustomBody"]))

        if empleado.especialidad:
            especialidad = f"""
            Con especialización en <b>{escape(str(empleado.especialidad))}</b>.
            """
            story.append(Paragraph(especialidad, self.styles["CustomBody"]))

        if empleado.titulo_secundaria:
            titulo_sec = f"""
            Con título de bachiller en <b>{escape(str(empleado.titulo_secundaria))}</b>.
            """
            story.append(Paragraph(titulo_sec, self.styles["CustomBody"]))

        if empleado.titulo_obtenido:
            titulo = f"""
            Obteniendo el título de <b>{escape(str(empleado.titulo_obtenido))}</b>.
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
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
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
                    f"{format_date(pago_data['periodo_inicio'])} a "
                    f"{format_date(pago_data['periodo_fin'])}",
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
                [
                    "Bonificaciones",
                    format_currency(float(pago_data.get("bonificaciones", 0) or 0)),
                ],
                ["Horas Extra", format_currency(float(pago_data.get("horas_extra", 0) or 0))],
                ["Aguinaldo", format_currency(float(pago_data.get("aguinaldo", 0) or 0))],
                [
                    "Bono Vacacional",
                    format_currency(float(pago_data.get("bono_vacacional", 0) or 0)),
                ],
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
                    ("LINEABOVE", (0, 6), (-1, 6), 1, colors.black),
                    ("LINEBELOW", (0, 6), (-1, 6), 1, colors.black),
                    ("FONTNAME", (0, 6), (1, 6), "Helvetica-Bold"),
                    ("LINEABOVE", (0, 13), (-1, 13), 1, colors.black),
                    ("LINEBELOW", (0, 13), (-1, 13), 1, colors.black),
                    ("FONTNAME", (0, 13), (1, 13), "Helvetica-Bold"),
                    ("LINEABOVE", (0, 15), (-1, 15), 1.5, colors.darkblue),
                    ("LINEBELOW", (0, 15), (-1, 15), 1.5, colors.darkblue),
                    ("FONTNAME", (0, 15), (1, 15), "Helvetica-Bold"),
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
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
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
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
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
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
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
            extras = sum(
                self._flotante(pago.get(campo))
                for campo in (
                    "bonificaciones",
                    "horas_extra",
                    "aguinaldo",
                    "bono_vacacional",
                )
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
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
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
                f"Total de incidencias: <b>{len(filas)}</b> | "
                f"Días solicitados: <b>{int(total_dias)}</b>",
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
                escape(str(config.get("nombre_institucion", "INSTITUCIÓN EDUCATIVA"))),
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
    # Reportes nuevos: ingresos, contratos y liquidación
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
            story.append(
                Paragraph(f"Período certificado: <b>{periodo}</b>", self.styles["CustomData"])
            )
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
                aguinaldo, otras_deducciones, neto...)
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
            ["Cédula", escape(str(empleado.cedula or ""))],
            ["Cargo", escape(str(empleado.cargo or ""))],
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
            output_path,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=40,
            bottomMargin=28,
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
            # Las filas llegan del listado de la interfaz (claves con
            # mayúscula: "Empleado", "Salario_pactado"...) o de un diccionario
            # normalizado. Se aceptan ambas formas para que el reporte no
            # salga con columnas vacías.
            salario = float(str(_dato(fila, "salario_pactado", "Salario_pactado", defecto=0) or 0))
            total_salarios += salario
            dias = _dato(fila, "dias_para_vencer", defecto=None)
            if dias in (None, ""):
                # Acepta la clave con tilde ("Días_vigencia", la que hoy usan
                # los listados de la interfaz) y la antigua sin ella.
                dias = _dato(fila, "Días_vigencia", "Dias_vigencia", defecto=None)
            fin = _dato(fila, "fecha_fin", "Fin", defecto=None)
            tabla_datos.append(
                [
                    str(indice),
                    str(_dato(fila, "numero", "Número", "Numero")),
                    str(_dato(fila, "empleado", "Empleado"))[:28],
                    str(_dato(fila, "tipo", "Tipo")).capitalize(),
                    str(_dato(fila, "cargo", "Cargo"))[:22],
                    format_date(str(_dato(fila, "fecha_inicio", "Inicio", defecto=None))),
                    format_date(str(fin)) if fin not in (None, "") else "Indefinido",
                    "-" if dias in (None, "") else str(dias),
                    format_currency(salario),
                    str(_dato(fila, "estado", "Estado")).capitalize(),
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


# Instancia global del generador de PDFs
pdf_generator = PDFGenerator()
