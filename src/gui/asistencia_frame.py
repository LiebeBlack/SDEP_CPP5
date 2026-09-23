"""
Módulo de Asistencia

Interfaz del control de asistencia: registro de jornadas con cálculo
automático de horas trabajadas, tardanzas y horas extra, marcado de
ausencias y justificación desde incidencias aprobadas, además de los
totales del período que alimentan la nómina.
"""

import logging
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

import customtkinter as ctk

from src.gui.frames import _habilitar_orden_columnas, _seleccionar_fila_click
from src.gui.theme import COLORES
from src.models import Asistencia, Empleado, TipoAsistencia
from src.utils.helpers import format_date, parse_date

logger = logging.getLogger(__name__)

TIPOS_ASISTENCIA = [tipo.value for tipo in TipoAsistencia]
ETIQUETAS_TIPO = {
    "presente": "Presente",
    "tardanza": "Tardanza",
    "ausente": "Ausente",
    "permiso": "Permiso",
    "vacaciones": "Vacaciones",
    "reposo": "Reposo",
    "feriado": "Feriado",
}


class AsistenciaFrame(ctk.CTkFrame):
    """Frame del módulo de asistencia"""

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self.servicio = self._crear_servicio()
        self._empleados: dict[int, Empleado] = {}
        self.registros: list[Asistencia] = []
        self._create_widgets()
        self._cargar_empleados()
        self._load_data()

    # ------------------------------------------------------------------
    # Servicios
    # ------------------------------------------------------------------
    def _crear_servicio(self):
        """Crea el servicio de asistencia con la sesión activa"""
        try:
            from src.services import AsistenciaService

            return AsistenciaService(self.session)
        except (ImportError, AttributeError) as e:
            logger.error("No se pudo inicializar el servicio de asistencia: %s", e)
            return None

    def _permite(self, accion: str) -> bool:
        """Consulta los permisos del usuario en sesión"""
        try:
            return bool(self.main_window.tiene_permiso(accion))
        except (AttributeError, TypeError):
            return True

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Crea la barra de filtros, la tabla y el resumen"""
        titulo = ctk.CTkLabel(
            self,
            text="Control de Asistencia",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORES["texto"],
        )
        titulo.pack(pady=(14, 6), padx=20, anchor="w")

        self._crear_barra_filtros()
        self._crear_tabla()
        self._crear_resumen()

    def _crear_barra_filtros(self) -> None:
        """Barra superior con rango de fechas, filtros y acciones"""
        barra = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        barra.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(barra, text="Desde:", text_color=COLORES["texto"]).pack(
            side="left", padx=(12, 4), pady=10
        )
        hoy = date.today()
        self.desde_entry = ctk.CTkEntry(barra, width=100)
        self.desde_entry.pack(side="left", pady=10)
        self.desde_entry.insert(0, (hoy - timedelta(days=30)).strftime("%d/%m/%Y"))

        ctk.CTkLabel(barra, text="Hasta:", text_color=COLORES["texto"]).pack(
            side="left", padx=(10, 4), pady=10
        )
        self.hasta_entry = ctk.CTkEntry(barra, width=100)
        self.hasta_entry.pack(side="left", pady=10)
        self.hasta_entry.insert(0, hoy.strftime("%d/%m/%Y"))

        ctk.CTkLabel(barra, text="Empleado:", text_color=COLORES["texto"]).pack(
            side="left", padx=(10, 4), pady=10
        )
        self.empleado_combo = ctk.CTkComboBox(barra, width=200, values=["Todos"])
        self.empleado_combo.pack(side="left", pady=10)
        self.empleado_combo.set("Todos")

        ctk.CTkButton(
            barra,
            text="🔍 Buscar",
            width=90,
            command=self._load_data,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            barra,
            text="📄 Reporte PDF",
            width=120,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._exportar_pdf,
        ).pack(side="right", padx=(4, 12))

        ctk.CTkButton(
            barra,
            text="📊 Exportar",
            width=100,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._exportar,
        ).pack(side="right", padx=4)

        if self._permite("update"):
            ctk.CTkButton(
                barra,
                text="✅ Aplicar incidencias",
                width=150,
                fg_color=COLORES["campo"],
                hover_color=COLORES["panel_hover"],
                command=self._aplicar_incidencias,
            ).pack(side="right", padx=4)

        if self._permite("create"):
            ctk.CTkButton(
                barra,
                text="➕ Registrar jornada",
                width=150,
                command=self._nueva_jornada,
            ).pack(side="right", padx=4)

    def _crear_tabla(self) -> None:
        """Tabla de registros de asistencia"""
        contenedor = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        contenedor.pack(fill="both", expand=True, padx=20, pady=8)

        columnas = (
            "empleado",
            "fecha",
            "tipo",
            "entrada",
            "salida",
            "horas",
            "tardanza",
            "extra",
            "observaciones",
        )
        self.tree = ttk.Treeview(contenedor, columns=columnas, show="headings", height=16)
        encabezados = {
            "empleado": ("Empleado", 220),
            "fecha": ("Fecha", 100),
            "tipo": ("Tipo", 100),
            "entrada": ("Entrada", 80),
            "salida": ("Salida", 80),
            "horas": ("Horas", 70),
            "tardanza": ("Tardanza", 80),
            "extra": ("H. extra", 80),
            "observaciones": ("Observaciones", 240),
        }
        for clave, (texto, ancho) in encabezados.items():
            self.tree.heading(clave, text=texto)
            self.tree.column(clave, width=ancho, anchor="w" if clave == "empleado" else "center")

        _habilitar_orden_columnas(self.tree)
        # El clic y el clic derecho dejan siempre seleccionada la fila bajo
        # el cursor: sin esto, en algunas plataformas el doble clic abre el
        # registro anterior en lugar del que el usuario señaló.
        self.tree.bind("<ButtonRelease-1>", lambda evento: _seleccionar_fila_click(self.tree, evento))
        self.tree.bind("<Button-3>", lambda evento: _seleccionar_fila_click(self.tree, evento))

        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        self.tree.bind("<Double-1>", lambda _evento: self._editar_registro())

    def _crear_resumen(self) -> None:
        """Resumen de totales del período consultado"""
        resumen = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        resumen.pack(fill="x", padx=20, pady=(0, 16))

        self.resumen_label = ctk.CTkLabel(
            resumen,
            text="Sin datos del período",
            font=ctk.CTkFont(size=12),
            text_color=COLORES["texto_suave"],
            anchor="w",
        )
        self.resumen_label.pack(fill="x", padx=14, pady=10)

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------
    def _cargar_empleados(self) -> None:
        """Carga los empleados activos en el selector"""
        try:
            from src.repositories import EmpleadoRepository

            empleados = EmpleadoRepository(self.session).get_activos()
            self._empleados = {int(empleado.id): empleado for empleado in empleados}
            valores = ["Todos"] + [
                f"{empleado.cedula} - {empleado.nombre_completo}" for empleado in empleados
            ]
            self.empleado_combo.configure(values=valores)
            self.empleado_combo.set("Todos")
        except (AttributeError, TypeError, ValueError):
            logger.warning("No se pudieron cargar los empleados del selector", exc_info=True)

    def _rango_fechas(self) -> tuple[date, date] | None:
        """Lee el rango de fechas de la barra de filtros"""
        desde = parse_date(self.desde_entry.get().strip())
        hasta = parse_date(self.hasta_entry.get().strip())
        if desde is None or hasta is None:
            messagebox.showwarning("Fechas", "Indique un rango de fechas válido (dd/mm/aaaa)")
            return None
        if hasta < desde:
            messagebox.showwarning("Fechas", "La fecha final no puede ser anterior a la inicial")
            return None
        return desde, hasta

    def _empleado_seleccionado(self) -> int | None:
        """Identificador del empleado elegido en el selector (None = todos)"""
        seleccion = self.empleado_combo.get().strip()
        if not seleccion or seleccion == "Todos":
            return None
        cedula = seleccion.split(" - ", 1)[0].strip()
        for identificador, empleado in self._empleados.items():
            if str(getattr(empleado, "cedula", "")).strip() == cedula:
                return identificador
        return None

    def _load_data(self) -> None:
        """Carga los registros del período y actualiza la tabla y el resumen"""
        if self.servicio is None:
            messagebox.showerror("Asistencia", "El servicio de asistencia no está disponible")
            return
        rango = self._rango_fechas()
        if rango is None:
            return
        desde, hasta = rango

        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            empleado_id = self._empleado_seleccionado()
            if empleado_id is not None:
                self.registros = self.servicio.listar_por_empleado(empleado_id, desde, hasta)
            else:
                self.registros = self.servicio.listar_por_periodo(desde, hasta)
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error consultando la asistencia del período: %s", e)
            messagebox.showerror("Asistencia", f"No se pudo consultar la asistencia:\n{e}")
            return

        for registro in self.registros:
            empleado = self._empleados.get(int(registro.empleado_id))
            nombre = empleado.nombre_completo if empleado else f"Empleado {registro.empleado_id}"
            self.tree.insert(
                "",
                "end",
                iid=str(registro.id),
                values=(
                    nombre,
                    format_date(registro.fecha),
                    ETIQUETAS_TIPO.get(registro.tipo_valor, registro.tipo_valor),
                    registro.hora_entrada.strftime("%H:%M") if registro.hora_entrada else "-",
                    registro.hora_salida.strftime("%H:%M") if registro.hora_salida else "-",
                    f"{float(registro.horas_trabajadas or 0):.2f}",
                    str(int(registro.minutos_tardanza or 0)),
                    f"{float(registro.total_horas_extra or 0):.2f}",
                    (registro.observaciones or "")[:60],
                ),
            )

        self._actualizar_resumen(desde, hasta, self._empleado_seleccionado())

    def _actualizar_resumen(self, desde: date, hasta: date, empleado_id: int | None) -> None:
        """Muestra los totales del período consultado"""
        total_horas = sum(float(registro.horas_trabajadas or 0) for registro in self.registros)
        total_extra = sum(float(registro.total_horas_extra or 0) for registro in self.registros)
        faltas = sum(1 for registro in self.registros if registro.es_falta)
        tardanzas = sum(int(registro.minutos_tardanza or 0) for registro in self.registros)

        detalle = ""
        if empleado_id is not None:
            try:
                resumen = self.servicio.resumen_periodo(empleado_id, desde, hasta)
                detalle = (
                    f" | Días trabajados: {resumen.get('dias_trabajados', 0)}"
                    f" | Horario semanal: {resumen.get('horas_semanales_horario', 0)} h"
                )
            except (AttributeError, ValueError, TypeError):
                logger.debug("No se pudo obtener el resumen del empleado", exc_info=True)

        self.resumen_label.configure(
            text=(
                f"Registros: {len(self.registros)} | Horas trabajadas: {total_horas:.2f} | "
                f"Horas extra: {total_extra:.2f} | Faltas sin justificar: {faltas} | "
                f"Tardanzas: {tardanzas} min{detalle}"
            )
        )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def _nueva_jornada(self) -> None:
        """Abre el diálogo de registro de jornada"""
        dialogo = JornadaDialog(self, self.main_window, self._empleados, self.servicio)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_data()

    def _editar_registro(self) -> None:
        """Edita el registro seleccionado"""
        registro_id = self._seleccion_id()
        if registro_id is None:
            return
        registro = next(
            (item for item in self.registros if int(item.id) == registro_id), None
        )
        if registro is None:
            return
        dialogo = JornadaDialog(
            self, self.main_window, self._empleados, self.servicio, registro=registro
        )
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_data()

    def _seleccion_id(self) -> int | None:
        """Identificador del registro seleccionado en la tabla"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Asistencia", "Seleccione un registro de la tabla")
            return None
        try:
            return int(seleccion[0])
        except (TypeError, ValueError):
            return None

    def _aplicar_incidencias(self) -> None:
        """Marca la asistencia de los días cubiertos por incidencias aprobadas"""
        if self.servicio is None:
            return
        rango = self._rango_fechas()
        if rango is None:
            return
        desde, hasta = rango
        empleado_id = self._empleado_seleccionado()
        marcados = 0
        try:
            if empleado_id is not None:
                marcados = self.servicio.aplicar_incidencias_aprobadas(empleado_id, desde, hasta)
            else:
                for identificador in self._empleados:
                    marcados += self.servicio.aplicar_incidencias_aprobadas(
                        identificador, desde, hasta
                    )
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("No se pudieron aplicar las incidencias: %s", e)
            messagebox.showerror("Asistencia", f"No se pudieron aplicar las incidencias:\n{e}")
            return
        messagebox.showinfo(
            "Asistencia",
            f"Días marcados desde incidencias aprobadas: {marcados}",
        )
        self._load_data()

    # ------------------------------------------------------------------
    # Exportación
    # ------------------------------------------------------------------
    def _filas_exportables(self) -> list[dict]:
        """Convierte los registros en filas planas para exportar"""
        filas = []
        for registro in self.registros:
            empleado = self._empleados.get(int(registro.empleado_id))
            filas.append(
                {
                    "Empleado": empleado.nombre_completo if empleado else registro.empleado_id,
                    "Cédula": getattr(empleado, "cedula", ""),
                    "Fecha": format_date(registro.fecha),
                    "Tipo": ETIQUETAS_TIPO.get(registro.tipo_valor, registro.tipo_valor),
                    "Entrada": registro.hora_entrada.strftime("%H:%M")
                    if registro.hora_entrada
                    else "",
                    "Salida": registro.hora_salida.strftime("%H:%M")
                    if registro.hora_salida
                    else "",
                    "Horas trabajadas": float(registro.horas_trabajadas or 0),
                    "Minutos tardanza": int(registro.minutos_tardanza or 0),
                    "Horas extra diurnas": float(registro.horas_extra_diurnas or 0),
                    "Horas extra nocturnas": float(registro.horas_extra_nocturnas or 0),
                    "Horas extra feriadas": float(registro.horas_extra_feriadas or 0),
                    "Justificada": "Sí" if registro.justificada else "No",
                    "Observaciones": registro.observaciones or "",
                }
            )
        return filas

    def _exportar(self) -> None:
        """Exporta el listado de asistencia a Excel o CSV"""
        if not self.registros:
            messagebox.showinfo("Asistencia", "No hay registros para exportar")
            return
        try:
            from pathlib import Path

            from src.config import settings
            from src.utils.exporter import exportar_archivo
            from src.utils.helpers import ensure_directory_exists, get_timestamp

            carpeta = Path(settings.exports_path)
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"asistencia_{get_timestamp()}.xlsx"
            exportar_archivo(self._filas_exportables(), str(destino), hoja="Asistencia")
            messagebox.showinfo("Asistencia", f"Exportado en:\n{destino}")
        except (OSError, ValueError, ImportError) as e:
            logger.warning("No se pudo exportar la asistencia", exc_info=True)
            messagebox.showerror("Asistencia", f"No se pudo exportar:\n{e}")

    def _exportar_pdf(self) -> None:
        """Genera el reporte PDF de asistencia del período"""
        if not self.registros:
            messagebox.showinfo("Asistencia", "No hay registros para el reporte")
            return
        rango = self._rango_fechas()
        if rango is None:
            return
        desde, hasta = rango
        try:
            from pathlib import Path

            from src.config import settings
            from src.utils.helpers import (
                abrir_con_aplicacion_predeterminada,
                ensure_directory_exists,
                get_timestamp,
            )
            from src.utils.pdf_generator import pdf_generator

            filas = self._filas_exportables()
            resumen = None
            empleado_id = self._empleado_seleccionado()
            if empleado_id is not None:
                resumen = self.servicio.resumen_periodo(empleado_id, desde, hasta)

            carpeta = Path(settings.exports_path) / "asistencia"
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"reporte_asistencia_{get_timestamp()}.pdf"
            pdf_generator.generate_reporte_asistencia(
                filas, str(destino), desde=desde, hasta=hasta, resumen=resumen
            )
            abrir_con_aplicacion_predeterminada(destino)
            messagebox.showinfo("Asistencia", f"Reporte generado:\n{destino}")
        except (OSError, ValueError, ImportError) as e:
            logger.warning("No se pudo generar el reporte de asistencia", exc_info=True)
            messagebox.showerror("Asistencia", f"No se pudo generar el reporte:\n{e}")


class JornadaDialog(ctk.CTkToplevel):
    """Diálogo de registro o edición de una jornada"""

    def __init__(
        self,
        parent,
        main_window,
        empleados: dict[int, Empleado],
        servicio,
        registro: Asistencia | None = None,
    ):
        super().__init__(parent)
        self.main_window = main_window
        self.empleados = empleados
        self.servicio = servicio
        self.registro = registro
        self.guardado = False

        self.title("Registrar jornada" if registro is None else "Editar jornada")
        self.geometry("520x560")
        self.resizable(False, False)
        self.transient(parent)

        self._create_widgets()
        if registro is not None:
            self._cargar_registro()
        self._actualizar_vista_previa()
        self._centrar()

    def _centrar(self) -> None:
        """Centra el diálogo sobre la ventana principal"""
        try:
            self.update_idletasks()
            self.grab_set()
        except tk.TclError:
            logger.debug("Diálogo sin grab establecido", exc_info=True)

    def _create_widgets(self) -> None:
        """Crea los campos del formulario"""
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            contenedor, text="Empleado:", text_color=COLORES["texto"]
        ).grid(row=0, column=0, sticky="w", pady=6)
        valores = [
            f"{empleado.cedula} - {empleado.nombre_completo}"
            for empleado in self.empleados.values()
        ]
        self.empleado_combo = ctk.CTkComboBox(contenedor, width=300, values=valores or ["-"])
        self.empleado_combo.grid(row=0, column=1, sticky="w", pady=6)
        if valores:
            self.empleado_combo.set(valores[0])

        ctk.CTkLabel(contenedor, text="Fecha:", text_color=COLORES["texto"]).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.fecha_entry = ctk.CTkEntry(contenedor, width=140)
        self.fecha_entry.grid(row=1, column=1, sticky="w", pady=6)
        self.fecha_entry.insert(0, date.today().strftime("%d/%m/%Y"))

        ctk.CTkLabel(contenedor, text="Hora de entrada:", text_color=COLORES["texto"]).grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.entrada_entry = ctk.CTkEntry(contenedor, width=140, placeholder_text="07:00")
        self.entrada_entry.grid(row=2, column=1, sticky="w", pady=6)
        self.entrada_entry.bind("<FocusOut>", lambda _e: self._actualizar_vista_previa())

        ctk.CTkLabel(contenedor, text="Hora de salida:", text_color=COLORES["texto"]).grid(
            row=3, column=0, sticky="w", pady=6
        )
        self.salida_entry = ctk.CTkEntry(contenedor, width=140, placeholder_text="15:00")
        self.salida_entry.grid(row=3, column=1, sticky="w", pady=6)
        self.salida_entry.bind("<FocusOut>", lambda _e: self._actualizar_vista_previa())

        ctk.CTkLabel(contenedor, text="Tipo:", text_color=COLORES["texto"]).grid(
            row=4, column=0, sticky="w", pady=6
        )
        self.tipo_combo = ctk.CTkComboBox(
            contenedor,
            width=180,
            values=["Automático"] + list(TIPOS_ASISTENCIA),
        )
        self.tipo_combo.grid(row=4, column=1, sticky="w", pady=6)
        self.tipo_combo.set("Automático")

        self.justificada_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            contenedor, text="Ausencia justificada", variable=self.justificada_var
        ).grid(row=5, column=1, sticky="w", pady=6)

        ctk.CTkLabel(contenedor, text="Observaciones:", text_color=COLORES["texto"]).grid(
            row=6, column=0, sticky="nw", pady=6
        )
        self.observaciones_text = ctk.CTkTextbox(contenedor, width=300, height=80)
        self.observaciones_text.grid(row=6, column=1, sticky="w", pady=6)

        self.previa_label = ctk.CTkLabel(
            contenedor,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORES["texto_suave"],
            justify="left",
            anchor="w",
        )
        self.previa_label.grid(row=7, column=0, columnspan=2, sticky="w", pady=(10, 0))

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(botones, text="Guardar", width=120, command=self._guardar).pack(
            side="right", padx=4
        )
        ctk.CTkButton(
            botones,
            text="Cancelar",
            width=110,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self.destroy,
        ).pack(side="right", padx=4)

    # ------------------------------------------------------------------
    # Datos del formulario
    # ------------------------------------------------------------------
    def _cargar_registro(self) -> None:
        """Vuelca en el formulario el registro que se está editando"""
        registro = self.registro
        if registro is None:
            return
        for empleado in self.empleados.values():
            if int(empleado.id) == int(registro.empleado_id):
                self.empleado_combo.set(f"{empleado.cedula} - {empleado.nombre_completo}")
                break
        self.fecha_entry.delete(0, tk.END)
        self.fecha_entry.insert(0, format_date(registro.fecha))
        if registro.hora_entrada:
            self.entrada_entry.insert(0, registro.hora_entrada.strftime("%H:%M"))
        if registro.hora_salida:
            self.salida_entry.insert(0, registro.hora_salida.strftime("%H:%M"))
        self.tipo_combo.set(registro.tipo_valor)
        self.justificada_var.set(bool(registro.justificada))
        if registro.observaciones:
            self.observaciones_text.insert("1.0", registro.observaciones)

    def _empleado_id(self) -> int | None:
        """Identificador del empleado elegido"""
        seleccion = self.empleado_combo.get().strip()
        if not seleccion:
            return None
        cedula = seleccion.split(" - ", 1)[0].strip()
        for identificador, empleado in self.empleados.items():
            if str(getattr(empleado, "cedula", "")).strip() == cedula:
                return identificador
        return None

    def _actualizar_vista_previa(self) -> None:
        """Muestra el cálculo de horas y tardanza antes de guardar"""
        from src.utils.jornada import (
            calcular_horas_trabajadas,
            calcular_minutos_tardanza,
            parsear_hora,
        )

        entrada = parsear_hora(self.entrada_entry.get().strip())
        salida = parsear_hora(self.salida_entry.get().strip())
        horas = calcular_horas_trabajadas(entrada, salida)

        tardanza = 0
        if entrada is not None and self.servicio is not None:
            empleado_id = self._empleado_id()
            fecha = parse_date(self.fecha_entry.get().strip())
            if empleado_id is not None and fecha is not None:
                horario = self.servicio.horario_repository.get_dia(empleado_id, fecha.weekday())
                if horario is not None:
                    tardanza = calcular_minutos_tardanza(
                        entrada, horario.hora_inicio, int(horario.tolerancia_minutos or 0)
                    )

        self.previa_label.configure(
            text=(
                f"Vista previa: {horas:.2f} hora(s) trabajadas · "
                f"tardanza {tardanza} minuto(s)"
            )
        )

    def _guardar(self) -> None:
        """Valida y guarda el registro de asistencia"""
        if self.servicio is None:
            messagebox.showerror("Asistencia", "El servicio de asistencia no está disponible")
            return
        empleado_id = self._empleado_id()
        if empleado_id is None:
            messagebox.showwarning("Asistencia", "Seleccione un empleado")
            return
        fecha = parse_date(self.fecha_entry.get().strip())
        if fecha is None:
            messagebox.showwarning("Asistencia", "Indique una fecha válida (dd/mm/aaaa)")
            return

        tipo = self.tipo_combo.get().strip()
        datos = {
            "empleado_id": empleado_id,
            "fecha": fecha,
            "hora_entrada": self.entrada_entry.get().strip() or None,
            "hora_salida": self.salida_entry.get().strip() or None,
            "tipo": None if tipo in ("", "Automático") else tipo,
            "justificada": bool(self.justificada_var.get()),
            "observaciones": self.observaciones_text.get("1.0", "end").strip() or None,
            "registrado_por": getattr(
                getattr(self.main_window, "current_user", None), "username", None
            ),
        }

        errores = self.servicio.validar_datos_asistencia(datos)
        if errores:
            messagebox.showwarning("Asistencia", "\n".join(errores))
            return

        try:
            if self.registro is None:
                self.servicio.registrar_jornada(**datos)
            else:
                self.servicio.actualizar_asistencia(
                    int(self.registro.id), {k: v for k, v in datos.items() if k != "empleado_id"}
                )
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("No se pudo guardar la jornada: %s", e)
            messagebox.showerror("Asistencia", f"No se pudo guardar la jornada:\n{e}")
            return

        self.guardado = True
        self.destroy()
