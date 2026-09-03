"""
GUI Frames
Frames específicos para cada módulo de la aplicación
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import os
import sys
import webbrowser
from typing import Optional, List
from datetime import date, datetime

from src.models import Empleado, TipoEmpleado, TipoDocumento, TipoIncidencia, EstadoIncidencia, TipoPago, MetodoPago
from src.utils.helpers import (
    format_date, format_currency, parse_date, mantener_ventana_al_frente
)
from src.utils.pdf_generator import PDFGenerator


def _id_fila_seleccionada(tree) -> Optional[int]:
    """ID numérico de la fila seleccionada en un Treeview o None"""
    seleccion = tree.selection()
    if not seleccion:
        return None
    tags = tree.item(seleccion[0], "tags") or ()
    if not tags:
        return None
    try:
        return int(tags[0])
    except (TypeError, ValueError, IndexError):
        return None


class DashboardFrame(ctk.CTkFrame):
    """Frame del Dashboard"""
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self._create_widgets()
        self._load_data()
    
    def _create_widgets(self):
        """Crea los widgets del dashboard"""
        # Título
        title = ctk.CTkLabel(
            self,
            text="Panel de Control",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        title.pack(pady=20)
        
        # Contenedor de tarjetas
        cards_container = ctk.CTkFrame(self, fg_color="#2b2b2b")
        cards_container.pack(fill="x", padx=20, pady=10)
        
        # Tarjetas de estadísticas
        self.stats_cards = {}
        
        cards = [
            ("Total Empleados", "empleados", "👥"),
            ("Empleados Activos", "activos", "✅"),
            ("Documentos", "documentos", "📁"),
            ("Incidencias Pendientes", "incidencias", "📅"),
            ("Pagos Pendientes", "pagos", "💰"),
        ]
        
        for i, (title_text, key, icon) in enumerate(cards):
            card = self._create_stat_card(cards_container, title_text, icon, key)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            cards_container.grid_columnconfigure(i, weight=1)
        
        # Sección de acciones rápidas
        actions_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        actions_frame.pack(fill="x", padx=20, pady=20)
        
        actions_title = ctk.CTkLabel(
            actions_frame,
            text="Acciones Rápidas",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        actions_title.pack(pady=10)
        
        actions_container = ctk.CTkFrame(actions_frame)
        actions_container.pack(fill="x", padx=10, pady=10)
        
        # Crear funciones separadas para evitar problemas de lambda
        def go_to_empleados():
            self.main_window._show_frame("empleados")
        
        def go_to_documentos():
            self.main_window._show_frame("documentos")
        
        def go_to_incidencias():
            self.main_window._show_frame("incidencias")
        
        def go_to_nomina():
            self.main_window._show_frame("nomina")
        
        actions = [
            ("Nuevo Empleado", go_to_empleados),
            ("Nuevo Documento", go_to_documentos),
            ("Nueva Incidencia", go_to_incidencias),
            ("Generar Nómina", go_to_nomina),
        ]
        
        for i, (text, command) in enumerate(actions):
            btn = ctk.CTkButton(
                actions_container,
                text=text,
                height=50,
                command=command
            )
            btn.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            actions_container.grid_columnconfigure(i, weight=1)
    
    def _create_stat_card(self, parent, title: str, icon: str, key: str) -> ctk.CTkFrame:
        """Crea una tarjeta de estadística"""
        card = ctk.CTkFrame(parent, height=150, fg_color="#3c3c3c", corner_radius=8)
        card.pack_propagate(False)
        
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=ctk.CTkFont(size=40)
        )
        icon_label.pack(pady=(15, 5))
        
        value_label = ctk.CTkLabel(
            card,
            text="0",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        value_label.pack(pady=5)
        
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color="#cccccc"
        )
        title_label.pack(pady=(5, 15))
        
        self.stats_cards[key] = value_label
        return card
    
    def _load_data(self):
        """Carga los datos del dashboard"""
        try:
            # Estadísticas de empleados
            try:
                stats = self.main_window.empleado_service.obtener_estadisticas()
                self.stats_cards["empleados"].configure(text=str(stats.get("total", 0)))
                self.stats_cards["activos"].configure(text=str(stats.get("activos", 0)))
            except Exception as e:
                self.stats_cards["empleados"].configure(text="0")
                self.stats_cards["activos"].configure(text="0")
            
            # Estadísticas de documentos
            try:
                doc_stats = self.main_window.documento_service.obtener_estadisticas()
                self.stats_cards["documentos"].configure(text=str(doc_stats.get("total", 0)))
            except Exception as e:
                self.stats_cards["documentos"].configure(text="0")
            
            # Estadísticas de incidencias
            try:
                incidencia_stats = self.main_window.incidencia_service.obtener_estadisticas()
                self.stats_cards["incidencias"].configure(text=str(incidencia_stats.get("pendientes", 0)))
            except Exception as e:
                self.stats_cards["incidencias"].configure(text="0")
            
            # Estadísticas de pagos
            try:
                pago_stats = self.main_window.pago_service.obtener_estadisticas()
                self.stats_cards["pagos"].configure(text=str(pago_stats.get("pendientes", 0)))
            except Exception as e:
                self.stats_cards["pagos"].configure(text="0")
            
        except Exception as e:
            # Error general, establecer todos en 0
            for key in self.stats_cards:
                self.stats_cards[key].configure(text="0")


class EmpleadosFrame(ctk.CTkFrame):
    """Frame de Gestión de Empleados"""
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.current_empleado = None
        self._create_widgets()
        self._load_empleados()
    
    def _create_widgets(self):
        """Crea los widgets del frame de empleados"""
        # Panel de búsqueda y filtros
        search_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        search_frame.pack(fill="x", padx=10, pady=10)
        
        # Campo de búsqueda
        search_label = tk.Label(search_frame, text="Buscar:", bg="#2b2b2b", fg="white", font=("Arial", 10))
        search_label.pack(side="left", padx=5)
        
        self.search_entry = tk.Entry(search_frame, width=40, bg="#3c3c3c", fg="white", insertbackground="white")
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self._on_search)
        
        # Filtro por tipo
        tipo_label = tk.Label(search_frame, text="Tipo:", bg="#2b2b2b", fg="white", font=("Arial", 10))
        tipo_label.pack(side="left", padx=5)
        
        self.tipo_combo = ttk.Combobox(
            search_frame,
            values=["Todos", "docente", "administrativo", "mantenimiento"],
            width=18,
            state="readonly",
            font=("Arial", 9)
        )
        self.tipo_combo.pack(side="left", padx=5)
        self.tipo_combo.set("Todos")
        self.tipo_combo.bind("<<ComboboxSelected>>", self._on_filter)
        
        # Botones de acción (según permisos del rol)
        btn_frame = ctk.CTkFrame(search_frame)
        btn_frame.pack(side="right", padx=5)
        
        if self.main_window.tiene_permiso("create"):
            new_btn = ctk.CTkButton(btn_frame, text="Nuevo Empleado", command=self._on_new_empleado)
            new_btn.pack(side="left", padx=5)
        
        if self.main_window.tiene_permiso("report"):
            report_btn = ctk.CTkButton(btn_frame, text="Reporte PDF", command=self._on_reporte_empleados)
            report_btn.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(btn_frame, text="Actualizar", command=self._load_empleados)
        refresh_btn.pack(side="left", padx=5)
        
        # Tabla de empleados
        table_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Treeview
        self.tree = ttk.Treeview(
            table_frame,
            columns=("cedula", "nombre", "cargo", "departamento", "tipo", "salario"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        
        self.tree.heading("cedula", text="Cédula")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("cargo", text="Cargo")
        self.tree.heading("departamento", text="Departamento")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("salario", text="Salario")
        
        self.tree.column("cedula", width=130, minwidth=100)
        self.tree.column("nombre", width=250, minwidth=150)
        self.tree.column("cargo", width=180, minwidth=120)
        self.tree.column("departamento", width=180, minwidth=120)
        self.tree.column("tipo", width=120, minwidth=80)
        self.tree.column("salario", width=120, minwidth=100)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)
        
        # Doble clic para ver detalles (un clic solo selecciona)
        self.tree.bind("<Double-1>", self._on_double_click)
        
        # Menú contextual según permisos del rol
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Ver Detalles", command=self._on_view_details)
        if self.main_window.tiene_permiso("update"):
            self.context_menu.add_command(label="Editar", command=self._on_edit)
        self.context_menu.add_separator()
        if self.main_window.tiene_permiso("report"):
            self.context_menu.add_command(label="Constancia de Trabajo (PDF)", command=self._on_constancia_trabajo)
            self.context_menu.add_command(label="Constancia de Estudios (PDF)", command=self._on_constancia_estudios)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Ver Documentos", command=self._on_documents)
        self.context_menu.add_command(label="Ver Incidencias", command=self._on_incidencias)
        if self.main_window.tiene_permiso("delete"):
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Eliminar", command=self._on_delete)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _load_empleados(self):
        """Carga la lista de empleados"""
        try:
            # Limpiar tabla
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Cargar empleados
            empleados = self.main_window.empleado_service.listar_empleados_activos()
            
            for emp in empleados:
                try:
                    tipo_emp_val = emp.tipo_empleado.value if hasattr(emp.tipo_empleado, 'value') else str(emp.tipo_empleado or '')
                    self.tree.insert("", "end", values=(
                        emp.cedula,
                        emp.nombre_completo,
                        emp.cargo,
                        emp.departamento,
                        tipo_emp_val,
                        format_currency(emp.salario_base)
                    ), tags=(str(emp.id),))
                except Exception as e:
                    # Continuar con el siguiente empleado si hay error
                    continue
                
        except Exception as e:
            # Mostrar error pero no bloquear la UI
            self.tree.insert("", "end", values=("", "Error al cargar datos", "", "", "", ""))
    
    def _on_search(self, event=None):
        """Maneja el evento de búsqueda"""
        search_term = self.search_entry.get()
        if search_term:
            empleados = self.main_window.empleado_service.buscar_empleados(search_term)
        else:
            empleados = self.main_window.empleado_service.listar_empleados_activos()
        
        self._update_tree(empleados)
    
    def _on_filter(self, event=None):
        """Maneja el evento de filtrado"""
        tipo = self.tipo_combo.get()
        if tipo != "Todos":
            try:
                empleados = self.main_window.empleado_service.listar_por_tipo(tipo)
            except:
                empleados = self.main_window.empleado_service.listar_empleados_activos()
        else:
            empleados = self.main_window.empleado_service.listar_empleados_activos()
        
        self._update_tree(empleados)
    
    def _update_tree(self, empleados: List[Empleado]):
        """Actualiza el treeview con una lista de empleados"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for emp in empleados:
            tipo_emp_val = emp.tipo_empleado.value if hasattr(emp.tipo_empleado, 'value') else str(emp.tipo_empleado or '')
            self.tree.insert("", "end", values=(
                emp.cedula,
                emp.nombre_completo,
                emp.cargo,
                emp.departamento,
                tipo_emp_val,
                format_currency(emp.salario_base)
            ), tags=(str(emp.id),))
    
    def _on_double_click(self, event):
        """Maneja doble clic en un empleado"""
        self._on_view_details()
    
    def _show_context_menu(self, event):
        """Muestra el menú contextual"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _get_selected_empleado(self) -> Optional[Empleado]:
        """Obtiene el empleado seleccionado o None si la fila no tiene datos"""
        empleado_id = _id_fila_seleccionada(self.tree)
        if empleado_id is None:
            return None
        return self.main_window.empleado_service.obtener_empleado(empleado_id)
    
    def _on_new_empleado(self):
        """Maneja la creación de nuevo empleado"""
        self._show_empleado_dialog()
    
    def _on_view_details(self):
        """Muestra detalles del empleado seleccionado"""
        empleado = self._get_selected_empleado()
        if empleado:
            self._show_empleado_details_dialog(empleado)
    
    def _on_edit(self):
        """Edita el empleado seleccionado"""
        empleado = self._get_selected_empleado()
        if empleado:
            self._show_empleado_dialog(empleado, edit_mode=True)
    
    def _on_documents(self):
        """Muestra documentos del empleado seleccionado"""
        empleado = self._get_selected_empleado()
        if empleado:
            self.main_window.show_frame("documentos", select_empleado=empleado.id)
    
    def _on_incidencias(self):
        """Muestra incidencias del empleado seleccionado"""
        empleado = self._get_selected_empleado()
        if empleado:
            self.main_window.show_frame("incidencias", select_empleado=empleado.id)
    
    def _on_constancia_trabajo(self):
        """Genera constancia de trabajo en PDF para el empleado seleccionado"""
        empleado = self._get_selected_empleado()
        if not empleado:
            messagebox.showwarning("Advertencia", "Seleccione un empleado primero")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"constancia_trabajo_{empleado.cedula}.pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if file_path:
            try:
                pdf_gen = PDFGenerator()
                pdf_gen.generate_constancia_trabajo(empleado, file_path)
                messagebox.showinfo("Éxito", f"Constancia de trabajo generada exitosamente:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar constancia: {str(e)}")
    
    def _on_constancia_estudios(self):
        """Genera constancia de estudios en PDF para el empleado seleccionado"""
        empleado = self._get_selected_empleado()
        if not empleado:
            messagebox.showwarning("Advertencia", "Seleccione un empleado primero")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"constancia_estudios_{empleado.cedula}.pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if file_path:
            try:
                pdf_gen = PDFGenerator()
                pdf_gen.generate_constancia_estudios(empleado, file_path)
                messagebox.showinfo("Éxito", f"Constancia de estudios generada exitosamente:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar constancia: {str(e)}")
    
    def _on_reporte_empleados(self):
        """Genera un reporte general de empleados en PDF"""
        empleados = self.main_window.empleado_service.listar_empleados_activos()
        if not empleados:
            messagebox.showwarning("Advertencia", "No hay empleados registrados para generar el reporte")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"reporte_empleados_{date.today().strftime('%Y%m%d')}.pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if file_path:
            try:
                pdf_gen = PDFGenerator()
                pdf_gen.generate_reporte_empleados(empleados, file_path)
                messagebox.showinfo("Éxito", f"Reporte de empleados generado exitosamente:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al generar reporte: {str(e)}")
    
    def _on_delete(self):
        """Elimina el empleado seleccionado"""
        empleado = self._get_selected_empleado()
        if empleado:
            if messagebox.askyesno("Confirmar", f"¿Desea eliminar al empleado {empleado.nombre_completo}?"):
                try:
                    self.main_window.empleado_service.eliminar_empleado(empleado.id)
                    self._load_empleados()
                    messagebox.showinfo("Éxito", "Empleado eliminado correctamente")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al eliminar empleado: {str(e)}")
    
    def _show_empleado_dialog(self, empleado: Optional[Empleado] = None, edit_mode: bool = False):
        """Muestra el diálogo de empleado"""
        dialog = EmpleadoDialog(self, self.main_window, empleado, edit_mode)
        self.wait_window(dialog)
        if dialog.result:
            self._load_empleados()
    
    def _show_empleado_details_dialog(self, empleado: Empleado):
        """Muestra solo los detalles del empleado (solo lectura)"""
        dialog = EmpleadoDetailsDialog(self, self.main_window, empleado)
        self.wait_window(dialog)


class EmpleadoDetailsDialog(ctk.CTkToplevel):
    """Diálogo para ver detalles de empleado (solo lectura)"""
    
    def __init__(self, parent, main_window, empleado: Empleado):
        super().__init__(parent)
        self.main_window = main_window
        self.empleado = empleado
        
        self.title(f"Detalles: {empleado.nombre_completo}")
        self.geometry("700x500")
        
        mantener_ventana_al_frente(self)
        
        self._create_widgets()
        self._load_empleado_data()
    

    
    def _create_widgets(self):
        """Crea los widgets del diálogo de detalles"""
        # Notebook para pestañas
        notebook = ctk.CTkTabview(self, fg_color="#2b2b2b")
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pestaña de datos personales
        personal_tab = notebook.add("Datos Personales")
        self._create_personal_details_tab(personal_tab)
        
        # Pestaña de datos laborales
        laboral_tab = notebook.add("Datos Laborales")
        self._create_laboral_details_tab(laboral_tab)
        
        # Pestaña de contacto
        contacto_tab = notebook.add("Contacto")
        self._create_contacto_details_tab(contacto_tab)
        
        # Botón de cerrar
        btn_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        close_btn = ctk.CTkButton(btn_frame, text="Cerrar", command=self._on_close)
        close_btn.pack(side="right", padx=5)
        
        # Botón de editar
        edit_btn = ctk.CTkButton(btn_frame, text="Editar", command=self._on_edit)
        edit_btn.pack(side="right", padx=5)
    
    def _create_personal_details_tab(self, parent):
        """Crea la pestaña de datos personales (solo lectura)"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Campos de datos personales (solo lectura)
        self.nombres_label = self._create_detail_field(form_frame, "Nombres:", 0, 0)
        self.apellidos_label = self._create_detail_field(form_frame, "Apellidos:", 0, 2)
        self.cedula_label = self._create_detail_field(form_frame, "Cédula:", 1, 0)
        self.fecha_nacimiento_label = self._create_detail_field(form_frame, "Fecha Nacimiento:", 1, 2)
        
        self.genero_label = self._create_detail_field(form_frame, "Género:", 2, 0)
        self.estado_civil_label = self._create_detail_field(form_frame, "Estado Civil:", 2, 2)
        
        self.peso_label = self._create_detail_field(form_frame, "Peso (kg):", 3, 0)
        self.altura_label = self._create_detail_field(form_frame, "Altura (m):", 3, 2)
        self.tipo_sangre_label = self._create_detail_field(form_frame, "Tipo Sangre:", 4, 0)
        self.nacionalidad_label = self._create_detail_field(form_frame, "Nacionalidad:", 4, 2)
    
    def _create_laboral_details_tab(self, parent):
        """Crea la pestaña de datos laborales (solo lectura)"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tipo_empleado_label = self._create_detail_field(form_frame, "Tipo Empleado:", 0, 0)
        self.cargo_label = self._create_detail_field(form_frame, "Cargo:", 0, 2)
        self.departamento_label = self._create_detail_field(form_frame, "Departamento:", 1, 0)
        self.fecha_contratacion_label = self._create_detail_field(form_frame, "Fecha Contratación:", 1, 2)
        
        self.salario_base_label = self._create_detail_field(form_frame, "Salario Base:", 2, 0)
        self.nivel_educativo_label = self._create_detail_field(form_frame, "Nivel Educativo:", 2, 2)
        self.especialidad_label = self._create_detail_field(form_frame, "Especialidad:", 3, 0)
        self.titulo_obtenido_label = self._create_detail_field(form_frame, "Título Obtenido:", 3, 2)
        
        # Información adicional
        self.activo_label = self._create_detail_field(form_frame, "Estado:", 4, 0)
        self.antiguedad_label = self._create_detail_field(form_frame, "Antigüedad:", 4, 2)
    
    def _create_contacto_details_tab(self, parent):
        """Crea la pestaña de contacto (solo lectura)"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.telefono_label = self._create_detail_field(form_frame, "Teléfono:", 0, 0)
        self.celular_label = self._create_detail_field(form_frame, "Celular:", 0, 2)
        self.email_label = self._create_detail_field(form_frame, "Email:", 1, 0)
        self.direccion_label = self._create_detail_field(form_frame, "Dirección:", 1, 2)
        
        self.ciudad_label = self._create_detail_field(form_frame, "Ciudad:", 2, 0)
        self.estado_label = self._create_detail_field(form_frame, "Estado:", 2, 2)
        self.codigo_postal_label = self._create_detail_field(form_frame, "Código Postal:", 3, 0)
        
        # Contacto de emergencia
        emergency_frame = ctk.CTkFrame(form_frame, fg_color="#3c3c3c")
        emergency_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=10)
        
        emergency_label = ctk.CTkLabel(emergency_frame, text="Contacto de Emergencia", 
                                     font=ctk.CTkFont(weight="bold"), text_color="white")
        emergency_label.grid(row=0, column=0, columnspan=4, pady=5)
        
        self.contacto_emergencia_nombre_label = self._create_detail_field(emergency_frame, "Nombre:", 1, 0)
        self.contacto_emergencia_telefono_label = self._create_detail_field(emergency_frame, "Teléfono:", 1, 2)
        self.contacto_emergencia_relacion_label = self._create_detail_field(emergency_frame, "Relación:", 2, 0)
    
    def _create_detail_field(self, parent, label: str, row: int, col: int) -> ctk.CTkLabel:
        """Crea un campo de detalle (solo lectura)"""
        ctk.CTkLabel(parent, text=label, text_color="white").grid(row=row, column=col, padx=5, pady=5, sticky="e")
        value_label = ctk.CTkLabel(parent, text="-", text_color="#cccccc", anchor="w")
        value_label.grid(row=row, column=col+1, padx=5, pady=5, sticky="w")
        return value_label
    
    def _load_empleado_data(self):
        """Carga los datos del empleado en el formulario"""
        # Datos personales
        self.nombres_label.configure(text=self.empleado.nombres)
        self.apellidos_label.configure(text=self.empleado.apellidos)
        self.cedula_label.configure(text=self.empleado.cedula)
        if self.empleado.fecha_nacimiento:
            self.fecha_nacimiento_label.configure(text=format_date(self.empleado.fecha_nacimiento))
        
        self.genero_label.configure(text=self.empleado.genero or "-")
        self.estado_civil_label.configure(text=self.empleado.estado_civil or "-")
        
        self.peso_label.configure(text=str(self.empleado.peso) if self.empleado.peso else "-")
        self.altura_label.configure(text=str(self.empleado.altura) if self.empleado.altura else "-")
        self.tipo_sangre_label.configure(text=self.empleado.tipo_sangre or "-")
        self.nacionalidad_label.configure(text=self.empleado.nacionalidad or "-")
        
        # Datos laborales
        self.tipo_empleado_label.configure(text=self.empleado.tipo_empleado)
        self.cargo_label.configure(text=self.empleado.cargo)
        self.departamento_label.configure(text=self.empleado.departamento)
        if self.empleado.fecha_contratacion:
            self.fecha_contratacion_label.configure(text=format_date(self.empleado.fecha_contratacion))
        
        self.salario_base_label.configure(text=format_currency(self.empleado.salario_base))
        self.nivel_educativo_label.configure(text=self.empleado.nivel_educativo or "-")
        self.especialidad_label.configure(text=self.empleado.especialidad or "-")
        self.titulo_obtenido_label.configure(text=self.empleado.titulo_obtenido or "-")
        
        # Información adicional
        self.activo_label.configure(text="Activo" if self.empleado.activo else "Inactivo")
        self.antiguedad_label.configure(text=f"{self.empleado.antiguedad_anos} años" if self.empleado.antiguedad_anos else "-")
        
        # Contacto
        self.telefono_label.configure(text=self.empleado.telefono or "-")
        self.celular_label.configure(text=self.empleado.celular or "-")
        self.email_label.configure(text=self.empleado.email or "-")
        self.direccion_label.configure(text=self.empleado.direccion or "-")
        self.ciudad_label.configure(text=self.empleado.ciudad or "-")
        self.estado_label.configure(text=self.empleado.estado or "-")
        self.codigo_postal_label.configure(text=self.empleado.codigo_postal or "-")
        
        # Contacto de emergencia
        self.contacto_emergencia_nombre_label.configure(text=self.empleado.contacto_emergencia_nombre or "-")
        self.contacto_emergencia_telefono_label.configure(text=self.empleado.contacto_emergencia_telefono or "-")
        self.contacto_emergencia_relacion_label.configure(text=self.empleado.contacto_emergencia_relacion or "-")
    
    def _on_close(self):
        """Cierra el diálogo"""
        self.destroy()
    
    def _on_edit(self):
        """Abre el diálogo de edición"""
        self.destroy()
        # Llamar al método de edición del frame padre
        if hasattr(self.main_window, 'current_frame') and hasattr(self.main_window.current_frame, '_on_edit'):
            # Encontrar el empleado seleccionado y editar
            self.main_window.current_frame._on_edit()


class EmpleadoDialog(ctk.CTkToplevel):
    """Diálogo para crear/editar empleado"""
    
    def __init__(self, parent, main_window, empleado: Optional[Empleado] = None, edit_mode: bool = False):
        super().__init__(parent)
        self.main_window = main_window
        self.empleado = empleado
        self.edit_mode = edit_mode
        self.result = False
        
        self.title("Nuevo Empleado" if not empleado else "Editar Empleado")
        self.geometry("800x600")
        
        mantener_ventana_al_frente(self)
        
        self._create_widgets()
        
        # En modo edición precargar los datos del empleado
        if self.empleado and self.edit_mode:
            self._load_empleado_data()
    

    
    def _create_widgets(self):
        """Crea los widgets del diálogo"""
        # Notebook para pestañas
        notebook = ctk.CTkTabview(self, fg_color="#2b2b2b")
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pestaña de datos personales
        personal_tab = notebook.add("Datos Personales")
        self._create_personal_tab(personal_tab)
        
        # Pestaña de datos laborales
        laboral_tab = notebook.add("Datos Laborales")
        self._create_laboral_tab(laboral_tab)
        
        # Pestaña de contacto
        contacto_tab = notebook.add("Contacto")
        self._create_contacto_tab(contacto_tab)
        
        # Botones
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        save_btn = ctk.CTkButton(btn_frame, text="Guardar", command=self._on_save)
        save_btn.pack(side="right", padx=5)
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancelar", command=self._on_cancel)
        cancel_btn.pack(side="right", padx=5)
    
    def _create_personal_tab(self, parent):
        """Crea la pestaña de datos personales"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Campos de datos personales
        self.nombres_entry = self._create_form_field(form_frame, "Nombres:", 0, 0)
        self.apellidos_entry = self._create_form_field(form_frame, "Apellidos:", 0, 2)
        self.cedula_entry = self._create_form_field(form_frame, "Cédula:", 1, 0)
        self.fecha_nacimiento_entry = self._create_form_field(form_frame, "Fecha Nacimiento:", 1, 2)
        
        self.genero_combo = self._create_combo_field(form_frame, "Género:", 2, 0, 
                                                      ["masculino", "femenino", "otro"])
        self.estado_civil_combo = self._create_combo_field(form_frame, "Estado Civil:", 2, 2,
                                                           ["soltero", "casado", "divorciado", "viudo", "union_libre"])
        
        self.peso_entry = self._create_form_field(form_frame, "Peso (kg):", 3, 0)
        self.altura_entry = self._create_form_field(form_frame, "Altura (m):", 3, 2)
        self.tipo_sangre_entry = self._create_form_field(form_frame, "Tipo Sangre:", 4, 0)
        self.nacionalidad_entry = self._create_form_field(form_frame, "Nacionalidad:", 4, 2)
        
        # Foto de perfil (opcional)
        ctk.CTkLabel(form_frame, text="Foto de Perfil:", text_color="white").grid(
            row=5, column=0, padx=5, pady=10, sticky="e")
        self.photo_label = ctk.CTkLabel(
            form_frame, text="Sin foto", text_color="#aaaaaa", anchor="w")
        self.photo_label.grid(row=5, column=1, padx=5, pady=10, sticky="w")
        photo_btn = ctk.CTkButton(
            form_frame, text="Seleccionar…", width=110,
            command=self._on_select_foto)
        photo_btn.grid(row=5, column=2, columnspan=2, padx=5, pady=10, sticky="w")
    
    def _create_laboral_tab(self, parent):
        """Crea la pestaña de datos laborales"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tipo_empleado_combo = self._create_combo_field(form_frame, "Tipo Empleado:", 0, 0,
                                                            ["docente", "administrativo", "mantenimiento"])
        self.cargo_entry = self._create_form_field(form_frame, "Cargo:", 0, 2)
        self.departamento_entry = self._create_form_field(form_frame, "Departamento:", 1, 0)
        self.fecha_contratacion_entry = self._create_form_field(form_frame, "Fecha Contratación:", 1, 2)
        
        self.salario_base_entry = self._create_form_field(form_frame, "Salario Base:", 2, 0)
        self.nivel_educativo_entry = self._create_form_field(form_frame, "Nivel Educativo:", 2, 2)
        self.especialidad_entry = self._create_form_field(form_frame, "Especialidad:", 3, 0)
        self.titulo_obtenido_entry = self._create_form_field(form_frame, "Título Obtenido:", 3, 2)
    
    def _create_contacto_tab(self, parent):
        """Crea la pestaña de contacto"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.telefono_entry = self._create_form_field(form_frame, "Teléfono:", 0, 0)
        self.celular_entry = self._create_form_field(form_frame, "Celular:", 0, 2)
        self.email_entry = self._create_form_field(form_frame, "Email:", 1, 0)
        self.direccion_entry = self._create_form_field(form_frame, "Dirección:", 1, 2)
        
        self.ciudad_entry = self._create_form_field(form_frame, "Ciudad:", 2, 0)
        self.estado_entry = self._create_form_field(form_frame, "Estado:", 2, 2)
        self.codigo_postal_entry = self._create_form_field(form_frame, "Código Postal:", 3, 0)
        
        # Contacto de emergencia
        emergency_frame = ctk.CTkFrame(form_frame, fg_color="#3c3c3c")
        emergency_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=10)
        
        emergency_label = ctk.CTkLabel(emergency_frame, text="Contacto de Emergencia", 
                                     font=ctk.CTkFont(weight="bold"))
        emergency_label.grid(row=0, column=0, columnspan=4, pady=5)
        
        self.contacto_emergencia_nombre_entry = self._create_form_field(emergency_frame, "Nombre:", 1, 0)
        self.contacto_emergencia_telefono_entry = self._create_form_field(emergency_frame, "Teléfono:", 1, 2)
        self.contacto_emergencia_relacion_entry = self._create_form_field(emergency_frame, "Relación:", 2, 0)
    
    def _create_form_field(self, parent, label: str, row: int, col: int) -> ctk.CTkEntry:
        """Crea un campo de formulario"""
        ctk.CTkLabel(parent, text=label, text_color="white").grid(row=row, column=col, padx=5, pady=5, sticky="e")
        entry = ctk.CTkEntry(parent, width=200, fg_color="#3c3c3c", text_color="white", placeholder_text=" ")
        entry.grid(row=row, column=col+1, padx=5, pady=5, sticky="w")
        return entry
    
    def _create_combo_field(self, parent, label: str, row: int, col: int, values: List[str]) -> ttk.Combobox:
        """Crea un campo de combo"""
        ctk.CTkLabel(parent, text=label, text_color="white").grid(row=row, column=col, padx=5, pady=5, sticky="e")
        combo = ttk.Combobox(parent, values=values, width=25, state="readonly", font=("Arial", 9))
        combo.grid(row=row, column=col+1, padx=5, pady=5, sticky="w")
        if values:
            combo.set(values[0])  # Establecer primer valor por defecto
        return combo
    
    def _load_empleado_data(self):
        """Carga los datos del empleado en el formulario"""
        if not self.empleado:
            return
        
        # Datos personales
        if self.empleado.foto_ruta:
            self.photo_label.configure(text=os.path.basename(self.empleado.foto_ruta))
        self.nombres_entry.delete(0, tk.END)
        self.nombres_entry.insert(0, self.empleado.nombres)
        self.apellidos_entry.delete(0, tk.END)
        self.apellidos_entry.insert(0, self.empleado.apellidos)
        self.cedula_entry.delete(0, tk.END)
        self.cedula_entry.insert(0, self.empleado.cedula)
        if self.empleado.fecha_nacimiento:
            self.fecha_nacimiento_entry.delete(0, tk.END)
            self.fecha_nacimiento_entry.insert(0, format_date(self.empleado.fecha_nacimiento))
        
        if self.empleado.genero:
            self.genero_combo.set(self.empleado.genero)
        if self.empleado.estado_civil:
            self.estado_civil_combo.set(self.empleado.estado_civil)
        
        if self.empleado.peso:
            self.peso_entry.delete(0, tk.END)
            self.peso_entry.insert(0, str(self.empleado.peso))
        if self.empleado.altura:
            self.altura_entry.delete(0, tk.END)
            self.altura_entry.insert(0, str(self.empleado.altura))
        if self.empleado.tipo_sangre:
            self.tipo_sangre_entry.delete(0, tk.END)
            self.tipo_sangre_entry.insert(0, self.empleado.tipo_sangre)
        if self.empleado.nacionalidad:
            self.nacionalidad_entry.delete(0, tk.END)
            self.nacionalidad_entry.insert(0, self.empleado.nacionalidad)
        
        # Datos laborales
        self.tipo_empleado_combo.set(self.empleado.tipo_empleado)
        self.cargo_entry.delete(0, tk.END)
        self.cargo_entry.insert(0, self.empleado.cargo)
        self.departamento_entry.delete(0, tk.END)
        self.departamento_entry.insert(0, self.empleado.departamento)
        if self.empleado.fecha_contratacion:
            self.fecha_contratacion_entry.delete(0, tk.END)
            self.fecha_contratacion_entry.insert(0, format_date(self.empleado.fecha_contratacion))
        
        self.salario_base_entry.delete(0, tk.END)
        self.salario_base_entry.insert(0, str(self.empleado.salario_base))
        if self.empleado.nivel_educativo:
            self.nivel_educativo_entry.delete(0, tk.END)
            self.nivel_educativo_entry.insert(0, self.empleado.nivel_educativo)
        if self.empleado.especialidad:
            self.especialidad_entry.delete(0, tk.END)
            self.especialidad_entry.insert(0, self.empleado.especialidad)
        if self.empleado.titulo_obtenido:
            self.titulo_obtenido_entry.delete(0, tk.END)
            self.titulo_obtenido_entry.insert(0, self.empleado.titulo_obtenido)
        
        # Contacto
        if self.empleado.telefono:
            self.telefono_entry.delete(0, tk.END)
            self.telefono_entry.insert(0, self.empleado.telefono)
        if self.empleado.celular:
            self.celular_entry.delete(0, tk.END)
            self.celular_entry.insert(0, self.empleado.celular)
        if self.empleado.email:
            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, self.empleado.email)
        if self.empleado.direccion:
            self.direccion_entry.delete(0, tk.END)
            self.direccion_entry.insert(0, self.empleado.direccion)
        if self.empleado.ciudad:
            self.ciudad_entry.delete(0, tk.END)
            self.ciudad_entry.insert(0, self.empleado.ciudad)
        if self.empleado.estado:
            self.estado_entry.delete(0, tk.END)
            self.estado_entry.insert(0, self.empleado.estado)
        if self.empleado.codigo_postal:
            self.codigo_postal_entry.delete(0, tk.END)
            self.codigo_postal_entry.insert(0, self.empleado.codigo_postal)
        
        # Contacto de emergencia
        if self.empleado.contacto_emergencia_nombre:
            self.contacto_emergencia_nombre_entry.delete(0, tk.END)
            self.contacto_emergencia_nombre_entry.insert(0, self.empleado.contacto_emergencia_nombre)
        if self.empleado.contacto_emergencia_telefono:
            self.contacto_emergencia_telefono_entry.delete(0, tk.END)
            self.contacto_emergencia_telefono_entry.insert(0, self.empleado.contacto_emergencia_telefono)
        if self.empleado.contacto_emergencia_relacion:
            self.contacto_emergencia_relacion_entry.delete(0, tk.END)
            self.contacto_emergencia_relacion_entry.insert(0, self.empleado.contacto_emergencia_relacion)
    
    def _get_form_data(self) -> dict:
        """Obtiene los datos del formulario"""
        return {
            "nombres": self.nombres_entry.get(),
            "apellidos": self.apellidos_entry.get(),
            "cedula": self.cedula_entry.get(),
            "fecha_nacimiento": self._parse_date(self.fecha_nacimiento_entry.get()),
            "genero": self.genero_combo.get(),
            "estado_civil": self.estado_civil_combo.get(),
            "peso": self._parse_float(self.peso_entry.get()),
            "altura": self._parse_float(self.altura_entry.get()),
            "tipo_sangre": self.tipo_sangre_entry.get(),
            "nacionalidad": self.nacionalidad_entry.get(),
            "tipo_empleado": self.tipo_empleado_combo.get(),
            "cargo": self.cargo_entry.get(),
            "departamento": self.departamento_entry.get(),
            "fecha_contratacion": self._parse_date(self.fecha_contratacion_entry.get()),
            "salario_base": self._parse_float(self.salario_base_entry.get()),
            "nivel_educativo": self.nivel_educativo_entry.get(),
            "especialidad": self.especialidad_entry.get(),
            "titulo_obtenido": self.titulo_obtenido_entry.get(),
            "telefono": self.telefono_entry.get(),
            "celular": self.celular_entry.get(),
            "email": self.email_entry.get(),
            "direccion": self.direccion_entry.get(),
            "ciudad": self.ciudad_entry.get(),
            "estado": self.estado_entry.get(),
            "codigo_postal": self.codigo_postal_entry.get(),
            "contacto_emergencia_nombre": self.contacto_emergencia_nombre_entry.get(),
            "contacto_emergencia_telefono": self.contacto_emergencia_telefono_entry.get(),
            "contacto_emergencia_relacion": self.contacto_emergencia_relacion_entry.get(),
        }
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parsea una fecha"""
        return parse_date(date_str)
    
    def _on_select_foto(self):
        """Selecciona una imagen para la foto de perfil"""
        ruta = filedialog.askopenfilename(
            title="Seleccionar foto de perfil",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if ruta:
            self.photo_path = ruta
            self.photo_label.configure(text=os.path.basename(ruta), text_color="#8ab4f8")
    
    def _guardar_foto(self, empleado_id: int):
        """Guarda la foto seleccionada y actualiza la ruta del empleado"""
        ruta = getattr(self, "photo_path", None)
        if not ruta or not os.path.exists(ruta):
            return
        try:
            from src.utils.document_manager import document_manager
            with open(ruta, "rb") as f:
                contenido = f.read()
            ruta_guardada, _ = document_manager.save_photo(
                contenido, os.path.basename(ruta), empleado_id)
            self.main_window.empleado_service.actualizar_foto(empleado_id, ruta_guardada)
        except Exception as e:
            messagebox.showwarning(
                "Advertencia", f"El empleado se guardó pero no se pudo almacenar la foto: {e}")
    
    def _parse_float(self, value: str) -> Optional[float]:
        """Parsea un float"""
        try:
            return float(value) if value else None
        except ValueError:
            return None
    
    def _on_save(self):
        """Maneja el guardado del empleado"""
        try:
            datos = self._get_form_data()
            
            # Validaciones básicas
            errores = self.main_window.empleado_service.validar_datos_empleado(datos)
            if errores:
                messagebox.showerror("Errores de Validación", "\n".join(errores))
                return
            
            if self.empleado and self.edit_mode:
                self.main_window.empleado_service.actualizar_empleado(self.empleado.id, datos)
                self._guardar_foto(self.empleado.id)
                messagebox.showinfo("Éxito", "Empleado actualizado correctamente")
            else:
                # Verificar que la cédula no exista antes de crear
                if datos.get("cedula"):
                    existing = self.main_window.empleado_service.obtener_empleado_por_cedula(datos["cedula"])
                    if existing:
                        messagebox.showerror("Error", "Ya existe un empleado con esta cédula")
                        return
                
                empleado = self.main_window.empleado_service.crear_empleado(datos)
                self._guardar_foto(empleado.id)
                messagebox.showinfo("Éxito", "Empleado creado correctamente")
            
            self.result = True
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar empleado: {str(e)}")
    
    def _on_cancel(self):
        """Maneja la cancelación"""
        self.destroy()


class DocumentosFrame(ctk.CTkFrame):
    """Frame de Gestión Documental"""
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.current_empleado_id = None
        self._create_widgets()
        self._load_documentos()
    
    def _create_widgets(self):
        """Crea los widgets del frame de documentos"""
        # Panel de selección de empleado
        selection_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        selection_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(selection_frame, text="Empleado:", text_color="white").pack(side="left", padx=5)
        
        self.empleado_combo = ttk.Combobox(selection_frame, width=40, state="readonly", font=("Arial", 9))
        self.empleado_combo.pack(side="left", padx=5)
        self.empleado_combo.bind("<<ComboboxSelected>>", self._on_empleado_selected)
        
        refresh_btn = ctk.CTkButton(selection_frame, text="Actualizar", command=self._load_empleados)
        refresh_btn.pack(side="left", padx=5)
        
        # Panel de acciones
        actions_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        actions_frame.pack(fill="x", padx=10, pady=5)
        
        if self.main_window.tiene_permiso("create"):
            new_doc_btn = ctk.CTkButton(actions_frame, text="Nuevo Documento", command=self._on_new_documento)
            new_doc_btn.pack(side="left", padx=5)
        
        # Tabla de documentos
        table_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ctk.CTkScrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=("tipo", "titulo", "fecha", "estado"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("titulo", text="Título")
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("estado", text="Estado")
        
        self.tree.column("tipo", width=180, minwidth=120)
        self.tree.column("titulo", width=300, minwidth=200)
        self.tree.column("fecha", width=130, minwidth=100)
        self.tree.column("estado", width=120, minwidth=80)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)
        
        # Menú contextual según permisos del rol
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Ver Documento", command=self._on_view_documento)
        self.context_menu.add_command(label="Descargar", command=self._on_download_documento)
        if self.main_window.tiene_permiso("update"):
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Editar", command=self._on_edit_documento)
        if self.main_window.tiene_permiso("delete"):
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Eliminar", command=self._on_delete_documento)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self._on_view_documento())
        
        # Cargar empleados
        self._load_empleados()
    
    def _load_empleados(self):
        """Carga la lista de empleados en el combo"""
        empleados = self.main_window.empleado_service.listar_empleados_activos()
        self.empleado_combo['values'] = [f"{emp.nombre_completo} ({emp.cedula})" for emp in empleados]
        self.empleado_data = {f"{emp.nombre_completo} ({emp.cedula})": emp.id for emp in empleados}
    
    def select_empleado(self, empleado_id: int):
        """Selecciona un empleado específico programáticamente"""
        self._load_empleados()
        for label, emp_id in self.empleado_data.items():
            if emp_id == empleado_id:
                self.empleado_combo.set(label)
                self.current_empleado_id = empleado_id
                self._load_documentos()
                break
    
    def _on_empleado_selected(self, event):
        """Maneja la selección de empleado"""
        selected = self.empleado_combo.get()
        if selected in self.empleado_data:
            self.current_empleado_id = self.empleado_data[selected]
            self._load_documentos()
    
    def _load_documentos(self):
        """Carga los documentos del empleado seleccionado"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.current_empleado_id:
            self.tree.insert("", "end", values=("Seleccione un empleado", "", "", ""))
            return
        
        try:
            documentos = self.main_window.documento_service.listar_documentos_empleado(self.current_empleado_id)
            
            if not documentos:
                self.tree.insert("", "end", values=("", "No hay documentos registrados", "", ""))
                return
            
            for doc in documentos:
                try:
                    estado = "Vigente" if doc.es_valido else "Vencido"
                except AttributeError:
                    estado = "N/A"
                fecha_str = format_date(doc.fecha_emision) if doc.fecha_emision else "N/A"
                
                self.tree.insert("", "end", values=(
                    doc.tipo_documento,
                    doc.titulo,
                    fecha_str,
                    estado
                ), tags=(str(doc.id),))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar documentos: {str(e)}")
    
    def _show_context_menu(self, event):
        """Muestra el menú contextual"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _get_selected_documento(self):
        """Obtiene el documento seleccionado o None si la fila no tiene datos"""
        documento_id = _id_fila_seleccionada(self.tree)
        if documento_id is None:
            return None
        return self.main_window.documento_service.obtener_documento(documento_id)
    
    def _on_edit_documento(self):
        """Edita el documento seleccionado"""
        documento = self._get_selected_documento()
        if documento:
            dialog = DocumentoDialog(self, self.main_window, documento.empleado_id, documento)
            self.wait_window(dialog)
            if dialog.result:
                self._load_documentos()
    
    def _on_new_documento(self):
        """Maneja la creación de nuevo documento"""
        if not self.current_empleado_id:
            messagebox.showwarning("Advertencia", "Seleccione un empleado primero")
            return
        
        dialog = DocumentoDialog(self, self.main_window, self.current_empleado_id)
        self.wait_window(dialog)
        if dialog.result:
            self._load_documentos()
    
    def _abrir_con_aplicacion(self, ruta: str):
        """Abre un archivo con la aplicación predeterminada del sistema"""
        try:
            if sys.platform == "win32":
                os.startfile(ruta)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", ruta])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", ruta])
        except Exception:
            webbrowser.open(f"file://{ruta.replace(os.sep, '/')}")
    
    def _on_view_documento(self):
        """Muestra el documento seleccionado en el visor del sistema"""
        import tempfile
        documento = self._get_selected_documento()
        if not documento:
            return
        
        # 1. Si existe el archivo en disco, abrirlo directamente
        if documento.ruta_archivo and os.path.exists(documento.ruta_archivo):
            self._abrir_con_aplicacion(documento.ruta_archivo)
            return
        
        # 2. Si hay contenido binario, guardar a un archivo temporal y abrirlo
        contenido = self.main_window.documento_service.obtener_archivo(documento.id)
        if contenido:
            try:
                ext = os.path.splitext(documento.nombre_archivo)[1] or ".pdf"
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(contenido)
                    nombre_temporal = tmp.name
                self._abrir_con_aplicacion(nombre_temporal)
            except Exception:
                messagebox.showinfo(
                    "Documento",
                    f"Documento: {documento.titulo}\nArchivo: {documento.nombre_archivo}"
                    f"\nTamaño: {len(contenido)} bytes",
                )
        else:
            messagebox.showerror("Error", "No se pudo recuperar el archivo del documento")
    
    def _on_download_documento(self):
        """Descarga el documento seleccionado"""
        documento = self._get_selected_documento()
        if documento:
            contenido = self.main_window.documento_service.obtener_archivo(documento.id)
            if contenido:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    initialfile=documento.nombre_archivo,
                    filetypes=[("Todos los archivos", "*.*")]
                )
                if file_path:
                    with open(file_path, 'wb') as f:
                        f.write(contenido)
                    messagebox.showinfo("Éxito", "Documento descargado correctamente")
    
    def _on_delete_documento(self):
        """Elimina el documento seleccionado"""
        documento = self._get_selected_documento()
        if documento:
            if messagebox.askyesno("Confirmar", f"¿Desea eliminar el documento {documento.titulo}?"):
                try:
                    self.main_window.documento_service.eliminar_documento(documento.id)
                    self._load_documentos()
                    messagebox.showinfo("Éxito", "Documento eliminado correctamente")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al eliminar documento: {str(e)}")


class DocumentoDialog(ctk.CTkToplevel):
    """Diálogo para crear/editar documento"""
    
    def __init__(self, parent, main_window, empleado_id: int, documento=None):
        super().__init__(parent)
        self.main_window = main_window
        self.empleado_id = empleado_id
        self.documento = documento
        self.result = False
        self.file_content = None
        
        self.title("Editar Documento" if documento else "Nuevo Documento")
        self.geometry("600x400")
        
        mantener_ventana_al_frente(self)
        
        self._create_widgets()
        if documento:
            self._load_documento_data()
    
    def _load_documento_data(self):
        """Precarga los datos del documento en el formulario"""
        if not self.documento:
            return
        
        self.tipo_combo.set(self.documento.tipo_documento)
        self.titulo_entry.insert(0, self.documento.titulo)
        if self.documento.descripcion:
            self.descripcion_text.insert("1.0", self.documento.descripcion)
        if self.documento.fecha_emision:
            self.fecha_emision_entry.insert(0, format_date(self.documento.fecha_emision))
        if self.documento.fecha_vencimiento:
            self.fecha_vencimiento_entry.insert(0, format_date(self.documento.fecha_vencimiento))
        if self.documento.nombre_archivo:
            self.file_label.configure(text=self.documento.nombre_archivo)

    
    def _create_widgets(self):
        """Crea los widgets del diálogo"""
        form_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tipo de documento
        ctk.CTkLabel(form_frame, text="Tipo de Documento:", text_color="white").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.tipo_combo = ttk.Combobox(
            form_frame,
            values=["cedula", "titulo", "reposo", "certificado", "expediente", "otro"],
            width=25,
            state="readonly",
            font=("Arial", 9)
        )
        self.tipo_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.tipo_combo.set("cedula")  # Valor por defecto
        
        # Título
        ctk.CTkLabel(form_frame, text="Título:", text_color="white").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.titulo_entry = ctk.CTkEntry(form_frame, width=300, fg_color="#3c3c3c", text_color="white", placeholder_text="Ingrese título")
        self.titulo_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Descripción
        ctk.CTkLabel(form_frame, text="Descripción:", text_color="white").grid(row=2, column=0, padx=5, pady=5, sticky="ne")
        self.descripcion_text = ctk.CTkTextbox(form_frame, width=300, height=100, fg_color="#3c3c3c", text_color="white")
        self.descripcion_text.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Fechas
        ctk.CTkLabel(form_frame, text="Fecha Emisión:", text_color="white").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.fecha_emision_entry = ctk.CTkEntry(form_frame, width=150, fg_color="#3c3c3c", text_color="white", placeholder_text="DD/MM/YYYY")
        self.fecha_emision_entry.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Fecha Vencimiento:", text_color="white").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        self.fecha_vencimiento_entry = ctk.CTkEntry(form_frame, width=150, fg_color="#3c3c3c", text_color="white", placeholder_text="DD/MM/YYYY")
        self.fecha_vencimiento_entry.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # Archivo
        file_frame = ctk.CTkFrame(form_frame, fg_color="#3c3c3c")
        file_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        
        ctk.CTkLabel(file_frame, text="Archivo:").pack(side="left", padx=5)
        self.file_label = ctk.CTkLabel(file_frame, text="Ningún archivo seleccionado")
        self.file_label.pack(side="left", padx=5)
        
        select_file_btn = ctk.CTkButton(file_frame, text="Seleccionar", command=self._on_select_file)
        select_file_btn.pack(side="left", padx=5)
        
        # Botones
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        save_btn = ctk.CTkButton(btn_frame, text="Guardar", command=self._on_save)
        save_btn.pack(side="right", padx=5)
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancelar", command=self._on_cancel)
        cancel_btn.pack(side="right", padx=5)
    
    def _on_select_file(self):
        """Selecciona un archivo"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("PDF Files", "*.pdf"),
                ("Image Files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            with open(file_path, 'rb') as f:
                self.file_content = f.read()
            
            filename = os.path.basename(file_path)
            self.file_label.configure(text=filename)
    
    def _on_save(self):
        """Guarda (crea o actualiza) el documento"""
        try:
            # Al editar, el archivo solo es obligatorio si no había uno previo
            requiere_archivo = not (self.documento and self.documento.ruta_archivo)
            if requiere_archivo and not self.file_content:
                messagebox.showerror("Error", "Debe seleccionar un archivo")
                return
            
            datos = {
                "empleado_id": self.empleado_id,
                "tipo_documento": self.tipo_combo.get(),
                "titulo": self.titulo_entry.get(),
                "descripcion": self.descripcion_text.get("1.0", "end").strip(),
                "fecha_emision": self._parse_date(self.fecha_emision_entry.get()),
                "fecha_vencimiento": self._parse_date(self.fecha_vencimiento_entry.get()),
                "nombre_archivo": self.file_label.cget("text")
            }
            
            if not datos["titulo"]:
                messagebox.showerror("Error", "El título es requerido")
                return
            
            if self.documento is None and self.file_content:
                datos["nombre_archivo"] = self.file_label.cget("text")
            
            errores = self.main_window.documento_service.validar_datos_documento(datos)
            if errores:
                messagebox.showerror("Errores de Validación", "\n".join(errores))
                return
            
            if self.documento:
                self.main_window.documento_service.actualizar_documento(
                    self.documento.id, datos, self.file_content)
                messagebox.showinfo("Éxito", "Documento actualizado correctamente")
            else:
                self.main_window.documento_service.crear_documento(datos, self.file_content)
                messagebox.showinfo("Éxito", "Documento creado correctamente")
            
            self.result = True
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar documento: {str(e)}")
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parsea una fecha"""
        from src.utils.helpers import parse_date
        return parse_date(date_str)
    
    def _on_cancel(self):
        """Cancela la operación"""
        self.destroy()


class IncidenciasFrame(ctk.CTkFrame):
    """Frame de Incidencias y Permisos"""
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.current_empleado_id = None
        self._create_widgets()
        self._load_data()
    
    def _create_widgets(self):
        """Crea los widgets del frame de incidencias"""
        # Panel de selección de empleado
        selection_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        selection_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(selection_frame, text="Empleado:", text_color="white").pack(side="left", padx=5)
        
        self.empleado_combo = ttk.Combobox(selection_frame, width=40, state="readonly", font=("Arial", 9))
        self.empleado_combo.pack(side="left", padx=5)
        self.empleado_combo.bind("<<ComboboxSelected>>", self._on_empleado_selected)
        
        refresh_btn = ctk.CTkButton(selection_frame, text="Actualizar", command=self._load_empleados)
        refresh_btn.pack(side="left", padx=5)
        
        # Panel de acciones
        actions_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        actions_frame.pack(fill="x", padx=10, pady=5)
        
        if self.main_window.tiene_permiso("create"):
            new_incidencia_btn = ctk.CTkButton(actions_frame, text="Nueva Incidencia", command=self._on_new_incidencia)
            new_incidencia_btn.pack(side="left", padx=5)
        
        # Tabla de incidencias
        table_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ctk.CTkScrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=("tipo", "fechas", "dias", "estado", "motivo"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("fechas", text="Fechas")
        self.tree.heading("dias", text="Días")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("motivo", text="Motivo")
        
        self.tree.column("tipo", width=150, minwidth=100)
        self.tree.column("fechas", width=200, minwidth=150)
        self.tree.column("dias", width=80, minwidth=60)
        self.tree.column("estado", width=120, minwidth=80)
        self.tree.column("motivo", width=300, minwidth=200)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)
        
        # Menú contextual según permisos del rol
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Ver Detalles", command=self._on_view_incidencia)
        if self.main_window.tiene_permiso("update"):
            self.context_menu.add_command(label="Editar", command=self._on_edit_incidencia)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Aprobar", command=self._on_approve_incidencia)
            self.context_menu.add_command(label="Rechazar", command=self._on_reject_incidencia)
        if self.main_window.tiene_permiso("delete"):
            self.context_menu.add_command(label="Eliminar", command=self._on_delete_incidencia)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self._on_view_incidencia())
    
    def _load_data(self):
        """Carga los datos iniciales"""
        self._load_empleados()
        self._load_incidencias()
    
    def _load_empleados(self):
        """Carga la lista de empleados en el combo"""
        empleados = self.main_window.empleado_service.listar_empleados_activos()
        self.empleado_combo['values'] = [f"{emp.nombre_completo} ({emp.cedula})" for emp in empleados]
        self.empleado_data = {f"{emp.nombre_completo} ({emp.cedula})": emp.id for emp in empleados}
    
    def select_empleado(self, empleado_id: int):
        """Selecciona un empleado específico programáticamente"""
        self._load_empleados()
        for label, emp_id in self.empleado_data.items():
            if emp_id == empleado_id:
                self.empleado_combo.set(label)
                self.current_empleado_id = empleado_id
                self._load_incidencias()
                break
    
    def _on_empleado_selected(self, event):
        """Maneja la selección de empleado"""
        selected = self.empleado_combo.get()
        if selected in self.empleado_data:
            self.current_empleado_id = self.empleado_data[selected]
            self._load_incidencias()
    
    def _load_incidencias(self):
        """Carga las incidencias del empleado seleccionado"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.current_empleado_id:
            self.tree.insert("", "end", values=("Seleccione un empleado", "", "", "", ""))
            return
        
        try:
            incidencias = self.main_window.incidencia_service.listar_incidencias_empleado(self.current_empleado_id)
            
            if not incidencias:
                self.tree.insert("", "end", values=("", "No hay incidencias registradas", "", "", ""))
                return
            
            for incidencia in incidencias:
                fechas = f"{format_date(incidencia.fecha_inicio)} - {format_date(incidencia.fecha_fin)}"
                dias = str(incidencia.dias_solicitados)
                estado = incidencia.estado.capitalize()
                motivo = incidencia.motivo[:30] + "..." if len(incidencia.motivo) > 30 else incidencia.motivo
                
                self.tree.insert("", "end", values=(
                    incidencia.tipo_incidencia,
                    fechas,
                    dias,
                    estado,
                    motivo
                ), tags=(str(incidencia.id),))
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar incidencias: {str(e)}")
    
    def _show_context_menu(self, event):
        """Muestra el menú contextual"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _get_selected_incidencia(self):
        """Obtiene la incidencia seleccionada o None si la fila no tiene datos"""
        incidencia_id = _id_fila_seleccionada(self.tree)
        if incidencia_id is None:
            return None
        return self.main_window.incidencia_service.obtener_incidencia(incidencia_id)
    
    def _on_edit_incidencia(self):
        """Edita la incidencia seleccionada"""
        incidencia = self._get_selected_incidencia()
        if incidencia:
            if incidencia.estado != EstadoIncidencia.PENDIENTE.value:
                messagebox.showwarning(
                    "Advertencia",
                    "Solo las incidencias pendientes pueden editarse",
                )
                return
            dialog = IncidenciaDialog(
                self, self.main_window, incidencia.empleado_id, incidencia)
            self.wait_window(dialog)
            if dialog.result:
                self._load_incidencias()
    
    def _on_new_incidencia(self):
        """Maneja la creación de nueva incidencia"""
        if not self.current_empleado_id:
            messagebox.showwarning("Advertencia", "Seleccione un empleado primero")
            return
        
        dialog = IncidenciaDialog(self, self.main_window, self.current_empleado_id)
        self.wait_window(dialog)
        if dialog.result:
            self._load_incidencias()
    
    def _on_view_incidencia(self):
        """Muestra detalles de la incidencia seleccionada"""
        incidencia = self._get_selected_incidencia()
        if incidencia:
            self._show_incidencia_details(incidencia)
    
    def _on_approve_incidencia(self):
        """Aprueba la incidencia seleccionada"""
        incidencia = self._get_selected_incidencia()
        if incidencia:
            if incidencia.estado != EstadoIncidencia.PENDIENTE.value:
                messagebox.showwarning("Advertencia", "Solo se pueden aprobar incidencias pendientes")
                return
            
            dialog = ApprovalDialog(self, "Aprobar Incidencia", "Aprobar", incidencia)
            self.wait_window(dialog)
            if dialog.result:
                try:
                    self.main_window.incidencia_service.aprobar_incidencia(
                        incidencia.id,
                        dialog.approved_by,
                        dialog.comments,
                        dialog.dias_aprobados
                    )
                    self._load_incidencias()
                    messagebox.showinfo("Éxito", "Incidencia aprobada correctamente")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al aprobar incidencia: {str(e)}")
    
    def _on_reject_incidencia(self):
        """Rechaza la incidencia seleccionada"""
        incidencia = self._get_selected_incidencia()
        if incidencia:
            if incidencia.estado != EstadoIncidencia.PENDIENTE.value:
                messagebox.showwarning("Advertencia", "Solo se pueden rechazar incidencias pendientes")
                return
            
            dialog = ApprovalDialog(self, "Rechazar Incidencia", "Rechazar", incidencia)
            self.wait_window(dialog)
            if dialog.result:
                try:
                    self.main_window.incidencia_service.rechazar_incidencia(
                        incidencia.id,
                        dialog.approved_by,
                        dialog.comments
                    )
                    self._load_incidencias()
                    messagebox.showinfo("Éxito", "Incidencia rechazada correctamente")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al rechazar incidencia: {str(e)}")
    
    def _on_delete_incidencia(self):
        """Elimina la incidencia seleccionada"""
        incidencia = self._get_selected_incidencia()
        if incidencia:
            if messagebox.askyesno("Confirmar", f"¿Desea eliminar la incidencia?"):
                try:
                    self.main_window.incidencia_service.eliminar_incidencia(incidencia.id)
                    self._load_incidencias()
                    messagebox.showinfo("Éxito", "Incidencia eliminada correctamente")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al eliminar incidencia: {str(e)}")
    
    def _show_incidencia_details(self, incidencia):
        """Muestra los detalles de una incidencia"""
        detalle = f"""
Tipo: {incidencia.tipo_incidencia}
Estado: {incidencia.estado}
Empleado ID: {incidencia.empleado_id}
Fecha Solicitud: {format_date(incidencia.fecha_solicitud)}
Periodo: {format_date(incidencia.fecha_inicio)} - {format_date(incidencia.fecha_fin)}
Días Solicitados: {incidencia.dias_solicitados}
Días Aprobados: {incidencia.dias_aprobados or 'N/A'}
Afecta Nómina: {'Sí' if incidencia.afecta_nominas else 'No'}
Motivo: {incidencia.motivo}
Descripción: {incidencia.descripcion or 'N/A'}
Aprobado Por: {incidencia.aprobado_por or 'N/A'}
Fecha Aprobación: {format_date(incidencia.fecha_aprobacion) if incidencia.fecha_aprobacion else 'N/A'}
Comentarios: {incidencia.comentarios_aprobacion or 'N/A'}
Soporte: {incidencia.documento_soporte_nombre or 'N/A'}
"""
        InfoDialog(self, "Detalles de Incidencia", detalle)


class IncidenciaDialog(ctk.CTkToplevel):
    """Diálogo para crear/editar incidencia"""
    
    def __init__(self, parent, main_window, empleado_id: int, incidencia=None):
        super().__init__(parent)
        self.main_window = main_window
        self.empleado_id = empleado_id
        self.incidencia = incidencia
        self.result = False
        self.file_content = None
        
        self.title("Editar Incidencia" if incidencia else "Nueva Incidencia")
        self.geometry("600x500")
        
        mantener_ventana_al_frente(self)
        
        self._create_widgets()
        if incidencia:
            self._load_incidencia_data()
    
    def _load_incidencia_data(self):
        """Precarga los datos de la incidencia en el formulario"""
        if not self.incidencia:
            return
        self.tipo_combo.set(self.incidencia.tipo_incidencia)
        self.fecha_inicio_entry.insert(0, format_date(self.incidencia.fecha_inicio))
        self.fecha_fin_entry.insert(0, format_date(self.incidencia.fecha_fin))
        self.motivo_text.insert("1.0", self.incidencia.motivo)
        if self.incidencia.descripcion:
            self.descripcion_text.insert("1.0", self.incidencia.descripcion)
        if self.incidencia.documento_soporte_nombre:
            self.file_label.configure(text=self.incidencia.documento_soporte_nombre)

    
    def _create_widgets(self):
        """Crea los widgets del diálogo"""
        form_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tipo de incidencia
        ctk.CTkLabel(form_frame, text="Tipo de Incidencia:", text_color="white").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.tipo_combo = ttk.Combobox(
            form_frame,
            values=["reposo_medico", "ausencia", "permiso", "vacaciones", "licencia"],
            width=25,
            state="readonly",
            font=("Arial", 9)
        )
        self.tipo_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.tipo_combo.set("reposo_medico")  # Valor por defecto
        
        # Fechas
        ctk.CTkLabel(form_frame, text="Fecha Inicio:", text_color="white").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.fecha_inicio_entry = ctk.CTkEntry(form_frame, width=150, fg_color="#3c3c3c", text_color="white", placeholder_text="DD/MM/YYYY")
        self.fecha_inicio_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(form_frame, text="Fecha Fin:", text_color="white").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.fecha_fin_entry = ctk.CTkEntry(form_frame, width=150, fg_color="#3c3c3c", text_color="white", placeholder_text="DD/MM/YYYY")
        self.fecha_fin_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Motivo
        ctk.CTkLabel(form_frame, text="Motivo:", text_color="white").grid(row=3, column=0, padx=5, pady=5, sticky="ne")
        self.motivo_text = ctk.CTkTextbox(form_frame, width=300, height=80, fg_color="#3c3c3c", text_color="white")
        self.motivo_text.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Descripción
        ctk.CTkLabel(form_frame, text="Descripción:", text_color="white").grid(row=4, column=0, padx=5, pady=5, sticky="ne")
        self.descripcion_text = ctk.CTkTextbox(form_frame, width=300, height=60, fg_color="#3c3c3c", text_color="white")
        self.descripcion_text.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # Archivo de soporte
        file_frame = ctk.CTkFrame(form_frame, fg_color="#3c3c3c")
        file_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        
        ctk.CTkLabel(file_frame, text="Documento de Soporte:").pack(side="left", padx=5)
        self.file_label = ctk.CTkLabel(file_frame, text="Ningún archivo seleccionado")
        self.file_label.pack(side="left", padx=5)
        
        select_file_btn = ctk.CTkButton(file_frame, text="Seleccionar", command=self._on_select_file)
        select_file_btn.pack(side="left", padx=5)
        
        # Botones
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        save_btn = ctk.CTkButton(btn_frame, text="Guardar", command=self._on_save)
        save_btn.pack(side="right", padx=5)
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancelar", command=self._on_cancel)
        cancel_btn.pack(side="right", padx=5)
    
    def _on_select_file(self):
        """Selecciona un archivo"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("PDF Files", "*.pdf"),
                ("Image Files", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            with open(file_path, 'rb') as f:
                self.file_content = f.read()
            
            filename = os.path.basename(file_path)
            self.file_label.configure(text=filename)
    
    def _on_save(self):
        """Guarda la incidencia"""
        try:
            datos = {
                "empleado_id": self.empleado_id,
                "tipo_incidencia": self.tipo_combo.get(),
                "fecha_inicio": self._parse_date(self.fecha_inicio_entry.get()),
                "fecha_fin": self._parse_date(self.fecha_fin_entry.get()),
                "motivo": self.motivo_text.get("1.0", "end").strip(),
                "descripcion": self.descripcion_text.get("1.0", "end").strip(),
                "documento_soporte_nombre": self.file_label.cget("text") if self.file_content else None
            }
            
            # Validar campos requeridos
            if not datos["motivo"]:
                messagebox.showerror("Error", "El motivo es requerido")
                return
            
            if not datos["fecha_inicio"] or not datos["fecha_fin"]:
                messagebox.showerror("Error", "Las fechas son requeridas")
                return
            
            errores = self.main_window.incidencia_service.validar_datos_incidencia(datos)
            if errores:
                messagebox.showerror("Errores de Validación", "\n".join(errores))
                return
            
            if self.incidencia:
                self.main_window.incidencia_service.actualizar_incidencia(
                    self.incidencia.id, datos, self.file_content)
                messagebox.showinfo("Éxito", "Incidencia actualizada correctamente")
            else:
                self.main_window.incidencia_service.crear_incidencia(datos, self.file_content)
                messagebox.showinfo("Éxito", "Incidencia creada correctamente")
            
            self.result = True
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar incidencia: {str(e)}")
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parsea una fecha"""
        from src.utils.helpers import parse_date
        return parse_date(date_str)
    
    def _on_cancel(self):
        """Cancela la operación"""
        self.destroy()


class ApprovalDialog(ctk.CTkToplevel):
    """Diálogo para aprobación/rechazo"""
    
    def __init__(self, parent, title: str, action: str, incidencia):
        super().__init__(parent)
        self.result = False
        self.approved_by = ""
        self.comments = ""
        self.dias_aprobados = None
        
        self.title(title)
        self.geometry("400x300")
        
        mantener_ventana_al_frente(self)
        
        self._create_widgets(title, action, incidencia)
    

    
    def _create_widgets(self, title: str, action: str, incidencia):
        """Crea los widgets del diálogo"""
        form_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Información de la incidencia
        info_text = f"Incidencia: {incidencia.tipo_incidencia}\nDías solicitados: {incidencia.dias_solicitados}"
        ctk.CTkLabel(form_frame, text=info_text, font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        # Aprobado por
        ctk.CTkLabel(form_frame, text=f"{action} por:", text_color="white").pack(anchor="w", padx=5)
        self.approved_by_entry = ctk.CTkEntry(form_frame, width=300, fg_color="#3c3c3c", text_color="white", placeholder_text="Nombre del aprobador")
        self.approved_by_entry.pack(padx=5, pady=5)
        if hasattr(self, 'approved_by') and self.approved_by:
            self.approved_by_entry.insert(0, self.approved_by)
        
        # Días aprobados (solo para aprobación)
        if action == "Aprobar":
            ctk.CTkLabel(form_frame, text="Días a aprobar:", text_color="white").pack(anchor="w", padx=5)
            self.dias_entry = ctk.CTkEntry(form_frame, width=100, fg_color="#3c3c3c", text_color="white")
            self.dias_entry.insert(0, str(incidencia.dias_solicitados))
            self.dias_entry.pack(padx=5, pady=5)
        
        # Comentarios
        ctk.CTkLabel(form_frame, text="Comentarios:", text_color="white").pack(anchor="w", padx=5)
        self.comments_text = ctk.CTkTextbox(form_frame, width=300, height=80, fg_color="#3c3c3c", text_color="white")
        self.comments_text.pack(padx=5, pady=5)
        
        # Botones
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        save_btn = ctk.CTkButton(btn_frame, text=action, command=self._on_save)
        save_btn.pack(side="right", padx=5)
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancelar", command=self._on_cancel)
        cancel_btn.pack(side="right", padx=5)
    
    def _on_save(self):
        """Guarda la acción"""
        self.approved_by = self.approved_by_entry.get().strip()
        self.comments = self.comments_text.get("1.0", "end").strip()
        
        if hasattr(self, 'dias_entry'):
            try:
                dias_str = self.dias_entry.get().strip()
                if not dias_str:
                    messagebox.showerror("Error", "Debe ingresar los días a aprobar")
                    return
                self.dias_aprobados = int(dias_str)
                if self.dias_aprobados <= 0:
                    messagebox.showerror("Error", "Los días deben ser mayores a 0")
                    return
            except ValueError:
                messagebox.showerror("Error", "Los días deben ser un número entero")
                return
        
        if not self.approved_by:
            messagebox.showerror("Error", "Debe ingresar quien aprueba/rechaza")
            return
        
        self.result = True
        self.destroy()
    
    def _on_cancel(self):
        """Cancela la operación"""
        self.destroy()


class NominaFrame(ctk.CTkFrame):
    """Frame de Nómina y Pagos"""
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self._create_widgets()
        self._load_pagos()
    
    def _create_widgets(self):
        """Crea los widgets del frame de nómina"""
        # Panel de generación de nómina
        generation_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        generation_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(generation_frame, text="Generar Nómina:", font=ctk.CTkFont(weight="bold"), text_color="white").pack(side="left", padx=5)
        
        ctk.CTkLabel(generation_frame, text="Desde:", text_color="white").pack(side="left", padx=5)
        self.fecha_inicio_entry = ctk.CTkEntry(generation_frame, width=120, placeholder_text="DD/MM/YYYY", fg_color="#3c3c3c", text_color="white")
        self.fecha_inicio_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(generation_frame, text="Hasta:", text_color="white").pack(side="left", padx=5)
        self.fecha_fin_entry = ctk.CTkEntry(generation_frame, width=120, placeholder_text="DD/MM/YYYY", fg_color="#3c3c3c", text_color="white")
        self.fecha_fin_entry.pack(side="left", padx=5)
        
        generate_btn = ctk.CTkButton(generation_frame, text="Generar", command=self._on_generate_nomina)
        generate_btn.pack(side="left", padx=5)
        
        # Panel de filtros
        filter_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Estado:", text_color="white").pack(side="left", padx=5)
        self.estado_combo = ttk.Combobox(filter_frame, values=["Todos", "Pendientes", "Pagados"], width=18, state="readonly", font=("Arial", 9))
        self.estado_combo.pack(side="left", padx=5)
        self.estado_combo.set("Todos")
        self.estado_combo.bind("<<ComboboxSelected>>", self._on_filter)
        
        if self.main_window.tiene_permiso("create"):
            nuevo_pago_btn = ctk.CTkButton(
                filter_frame, text="Nuevo Pago", command=self._on_new_pago)
            nuevo_pago_btn.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(filter_frame, text="Actualizar", command=self._load_pagos)
        refresh_btn.pack(side="right", padx=5)
        
        # Tabla de pagos
        table_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ctk.CTkScrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(
            table_frame,
            columns=("empleado", "periodo", "tipo", "bruto", "neto", "estado"),
            show="headings",
            yscrollcommand=scrollbar.set
        )
        
        self.tree.heading("empleado", text="Empleado")
        self.tree.heading("periodo", text="Periodo")
        self.tree.heading("tipo", text="Tipo")
        self.tree.heading("bruto", text="Bruto")
        self.tree.heading("neto", text="Neto")
        self.tree.heading("estado", text="Estado")
        
        self.tree.column("empleado", width=250, minwidth=180)
        self.tree.column("periodo", width=200, minwidth=150)
        self.tree.column("tipo", width=150, minwidth=100)
        self.tree.column("bruto", width=120, minwidth=100)
        self.tree.column("neto", width=120, minwidth=100)
        self.tree.column("estado", width=100, minwidth=80)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)
        
        # Menú contextual según permisos del rol
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Ver Detalles", command=self._on_view_pago)
        if self.main_window.tiene_permiso("report"):
            self.context_menu.add_command(label="Generar Recibo", command=self._on_generate_recibo)
        if self.main_window.tiene_permiso("update"):
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Marcar Pagado", command=self._on_mark_paid)
            self.context_menu.add_command(label="Marcar Pendiente", command=self._on_mark_unpaid)
            self.context_menu.add_command(label="Editar", command=self._on_edit_pago)
        if self.main_window.tiene_permiso("delete"):
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Eliminar", command=self._on_delete_pago)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self._on_view_pago())
    
    def _load_pagos(self):
        """Carga la lista de pagos"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            estado = self.estado_combo.get()
            
            if estado == "Pendientes":
                pagos = self.main_window.pago_service.listar_pendientes()
            elif estado == "Pagados":
                pagos = self.main_window.pago_service.listar_pagados()
            else:
                pagos = self.main_window.pago_service.listar_pagos()
            
            if not pagos:
                self.tree.insert("", "end", values=("", "No hay pagos registrados", "", "", "", ""))
                return
            
            for pago in pagos:
                try:
                    empleado = self.main_window.empleado_service.obtener_empleado(pago.empleado_id)
                    nombre_empleado = empleado.nombre_completo if empleado else "Desconocido"
                    
                    periodo = f"{format_date(pago.periodo_inicio)} - {format_date(pago.periodo_fin)}"
                    estado_pago = "Pagado" if pago.pagado else "Pendiente"
                    
                    self.tree.insert("", "end", values=(
                        nombre_empleado,
                        periodo,
                        pago.tipo_pago,
                        format_currency(float(pago.monto_bruto)),
                        format_currency(float(pago.monto_neto)),
                        estado_pago
                    ), tags=(str(pago.id),))
                except Exception as e:
                    continue
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar pagos: {str(e)}")
    
    def _on_filter(self, event):
        """Maneja el filtrado de pagos"""
        self._load_pagos()
    
    def _on_generate_nomina(self):
        """Genera nómina para un periodo"""
        fecha_inicio_str = self.fecha_inicio_entry.get()
        fecha_fin_str = self.fecha_fin_entry.get()
        
        if not fecha_inicio_str or not fecha_fin_str:
            messagebox.showwarning("Advertencia", "Debe ingresar las fechas del periodo")
            return
        
        try:
            fecha_inicio = self._parse_date(fecha_inicio_str)
            fecha_fin = self._parse_date(fecha_fin_str)
            
            if not fecha_inicio or not fecha_fin:
                messagebox.showerror("Error", "Formato de fecha inválido. Use DD/MM/YYYY")
                return
            
            if messagebox.askyesno("Confirmar", 
                                  f"¿Desea generar nómina para el periodo {format_date(fecha_inicio)} - {format_date(fecha_fin)}?"):
                pagos = self.main_window.pago_service.generar_nominas_periodo(fecha_inicio, fecha_fin)
                messagebox.showinfo("Éxito", f"Se generaron {len(pagos)} pagos")
                self._load_pagos()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar nómina: {str(e)}")
    
    def _show_context_menu(self, event):
        """Muestra el menú contextual"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _get_selected_pago(self):
        """Obtiene el pago seleccionado o None si la fila no tiene datos"""
        pago_id = _id_fila_seleccionada(self.tree)
        if pago_id is None:
            return None
        return self.main_window.pago_service.obtener_pago(pago_id)
    
    def _on_new_pago(self):
        """Abre el diálogo para registrar un pago manual"""
        dialog = PagoDialog(self, self.main_window)
        self.wait_window(dialog)
        if dialog.result:
            self._load_pagos()
    
    def _on_edit_pago(self):
        """Edita el pago seleccionado"""
        pago = self._get_selected_pago()
        if pago:
            dialog = PagoDialog(self, self.main_window, pago)
            self.wait_window(dialog)
            if dialog.result:
                self._load_pagos()
    
    def _on_view_pago(self):
        """Muestra detalles del pago seleccionado"""
        pago = self._get_selected_pago()
        if pago:
            empleado = self.main_window.empleado_service.obtener_empleado(pago.empleado_id)
            nombre_empleado = empleado.nombre_completo if empleado else "Desconocido"
            
            salario_base = float(pago.salario_base or 0)
            bonif = float(pago.bonificaciones or 0)
            hextra = float(pago.horas_extra or 0)
            bruto = float(pago.monto_bruto or 0)
            
            d_seg = float(pago.deduccion_seguro or 0)
            d_pen = float(pago.deduccion_pension or 0)
            d_imp = float(pago.deduccion_impuesto or 0)
            d_otr = float(pago.otras_deducciones or 0)
            desc = float(pago.descuentos or 0)
            neto = float(pago.monto_neto or 0)
            
            details = f"""
Empleado: {nombre_empleado}
Periodo: {format_date(pago.periodo_inicio)} - {format_date(pago.periodo_fin)}
Tipo: {pago.tipo_pago}
Método: {pago.metodo_pago}
Referencia: {pago.referencia_pago or 'N/A'}

Salario Base: {format_currency(salario_base)}
Bonificaciones: {format_currency(bonif)}
Horas Extra: {format_currency(hextra)}
Total Bruto: {format_currency(bruto)}

Deducciones:
- Seguro Social: {format_currency(d_seg)}
- Pensión: {format_currency(d_pen)}
- Impuesto: {format_currency(d_imp)}
- Otras: {format_currency(d_otr)}
- Descuentos: {format_currency(desc)}

Total Neto: {format_currency(neto)}
Estado: {'Pagado' if pago.pagado else 'Pendiente'}
"""
            InfoDialog(self, "Detalles del Pago", details)
    
    def _on_generate_recibo(self):
        """Genera recibo de pago"""
        pago = self._get_selected_pago()
        if pago:
            empleado = self.main_window.empleado_service.obtener_empleado(pago.empleado_id)
            if empleado:
                try:
                    pago_data = {
                        "nombre_empleado": empleado.nombre_completo,
                        "cedula": empleado.cedula,
                        "periodo_inicio": pago.periodo_inicio,
                        "periodo_fin": pago.periodo_fin,
                        "referencia_pago": pago.referencia_pago,
                        "salario_base": float(pago.salario_base or 0),
                        "bonificaciones": float(pago.bonificaciones or 0),
                        "horas_extra": float(pago.horas_extra or 0),
                        "monto_bruto": float(pago.monto_bruto or 0),
                        "deduccion_seguro": float(pago.deduccion_seguro or 0),
                        "deduccion_pension": float(pago.deduccion_pension or 0),
                        "deduccion_impuesto": float(pago.deduccion_impuesto or 0),
                        "otras_deducciones": float(pago.otras_deducciones or 0),
                        "descuentos": float(pago.descuentos or 0),
                        "monto_neto": float(pago.monto_neto or 0)
                    }
                    
                    file_path = filedialog.asksaveasfilename(
                        defaultextension=".pdf",
                        initialfile=f"recibo_{empleado.cedula}_{pago.id}.pdf",
                        filetypes=[("PDF Files", "*.pdf")]
                    )
                    
                    if file_path:
                        pdf_gen = PDFGenerator()
                        pdf_gen.generate_recibo_pago(pago_data, file_path)
                        messagebox.showinfo("Éxito", "Recibo generado correctamente")
                        
                except Exception as e:
                    messagebox.showerror("Error", f"Error al generar recibo: {str(e)}")
    
    def _on_mark_paid(self):
        """Marca el pago como realizado"""
        pago = self._get_selected_pago()
        if pago:
            if pago.pagado:
                messagebox.showinfo("Información", "Este pago ya está marcado como pagado")
                return
            
            if messagebox.askyesno("Confirmar", "¿Desea marcar este pago como pagado?"):
                try:
                    self.main_window.pago_service.marcar_pagado(pago.id)
                    self._load_pagos()
                    messagebox.showinfo("Éxito", "Pago marcado como pagado")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al marcar pago: {str(e)}")
    
    def _on_mark_unpaid(self):
        """Marca el pago como pendiente"""
        pago = self._get_selected_pago()
        if pago:
            if not pago.pagado:
                messagebox.showinfo("Información", "Este pago ya está pendiente")
                return
            
            if messagebox.askyesno("Confirmar", "¿Desea marcar este pago como pendiente?"):
                try:
                    self.main_window.pago_service.marcar_pendiente(pago.id)
                    self._load_pagos()
                    messagebox.showinfo("Éxito", "Pago marcado como pendiente")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al marcar pago: {str(e)}")
    
    def _on_delete_pago(self):
        """Elimina el pago seleccionado"""
        pago = self._get_selected_pago()
        if pago:
            if messagebox.askyesno("Confirmar", "¿Desea eliminar este pago?"):
                try:
                    self.main_window.pago_service.eliminar_pago(pago.id)
                    self._load_pagos()
                    messagebox.showinfo("Éxito", "Pago eliminado correctamente")
                except Exception as e:
                    messagebox.showerror("Error", f"Error al eliminar pago: {str(e)}")
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parsea una fecha"""
        return parse_date(date_str)


class ConfiguracionFrame(ctk.CTkFrame):
    """Frame de Configuración"""
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self._create_widgets()
        self._load_configuracion()
    
    def _create_widgets(self):
        """Crea los widgets del frame de configuración"""
        # Notebook para categorías
        self.notebook = ctk.CTkTabview(self, fg_color="#2b2b2b")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pestaña de configuración general
        general_tab = self.notebook.add("General")
        self._create_general_tab(general_tab)
        
        # Pestaña de configuración de nómina
        nomina_tab = self.notebook.add("Nómina")
        self._create_nomina_tab(nomina_tab)
        
        # Pestaña de configuración de recursos humanos
        rrhh_tab = self.notebook.add("Recursos Humanos")
        self._create_rrhh_tab(rrhh_tab)
        
        # Pestaña de seguridad y respaldos (admin)
        seguridad_tab = self.notebook.add("Seguridad y Respaldo")
        self._create_seguridad_tab(seguridad_tab)
        
        # Pestaña de usuarios (admin)
        usuarios_tab = self.notebook.add("Usuarios")
        self._create_usuarios_tab(usuarios_tab)
        
        # Botones generales
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        save_btn = ctk.CTkButton(btn_frame, text="Guardar Cambios", command=self._on_save)
        save_btn.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(
            btn_frame, text="Actualizar", command=self._load_configuracion)
        refresh_btn.pack(side="left", padx=5)
    
    def _create_seguridad_tab(self, parent):
        """Crea la pestaña de seguridad y respaldos"""
        # Opciones de respaldo automático y auditoría
        options = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        options.pack(fill="x", padx=10, pady=(10, 5))
        
        self.backup_enabled_var = tk.BooleanVar(value=True)
        backup_chk = ctk.CTkCheckBox(
            options, text="Respaldo automático al cerrar",
            variable=self.backup_enabled_var)
        backup_chk.grid(row=0, column=0, padx=10, pady=8, sticky="w")
        
        self.audit_enabled_var = tk.BooleanVar(value=True)
        audit_chk = ctk.CTkCheckBox(
            options, text="Auditoría de eventos",
            variable=self.audit_enabled_var)
        audit_chk.grid(row=0, column=1, padx=10, pady=8, sticky="w")
        
        ctk.CTkLabel(options, text="Intervalo (horas):", text_color="white").grid(
            row=1, column=0, padx=(10, 5), pady=6, sticky="e")
        self.backup_interval_entry = ctk.CTkEntry(
            options, width=80, fg_color="#3c3c3c", text_color="white")
        self.backup_interval_entry.grid(row=1, column=1, padx=5, pady=6, sticky="w")
        
        save_seg_btn = ctk.CTkButton(
            options, text="Guardar Seguridad", command=self._on_save_seguridad)
        save_seg_btn.grid(row=1, column=3, padx=15, pady=6, sticky="e")
        
        options.grid_columnconfigure(3, weight=1)
        
        # Información del directorio de respaldos
        info = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        info.pack(fill="x", padx=10, pady=5)
        self.backup_status_label = ctk.CTkLabel(
            info, text="Cargando estado de respaldos…", text_color="#cccccc",
            anchor="w", justify="left")
        self.backup_status_label.pack(fill="x", padx=10, pady=8)
        
        # Tabla de respaldos
        table_frame = ctk.CTkFrame(parent, fg_color="#1a1a1a")
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ctk.CTkScrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.backup_tree = ttk.Treeview(
            table_frame, columns=("nombre", "fecha", "tamano", "tipo"),
            show="headings", yscrollcommand=scrollbar.set)
        self.backup_tree.heading("nombre", text="Nombre")
        self.backup_tree.heading("fecha", text="Fecha")
        self.backup_tree.heading("tamano", text="Tamaño")
        self.backup_tree.heading("tipo", text="Tipo")
        self.backup_tree.column("nombre", width=220, minwidth=150)
        self.backup_tree.column("fecha", width=140, minwidth=100)
        self.backup_tree.column("tamano", width=100, minwidth=70)
        self.backup_tree.column("tipo", width=90, minwidth=70)
        self.backup_tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.backup_tree.yview)
        
        # Acciones sobre respaldos
        actions = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        actions.pack(fill="x", padx=10, pady=(5, 10))
        
        create_btn = ctk.CTkButton(actions, text="Crear Respaldo", command=self._on_create_backup)
        create_btn.pack(side="left", padx=5, pady=6)
        verify_btn = ctk.CTkButton(actions, text="Verificar", command=self._on_verify_backup)
        verify_btn.pack(side="left", padx=5, pady=6)
        restore_btn = ctk.CTkButton(actions, text="Restaurar", command=self._on_restore_backup)
        restore_btn.pack(side="left", padx=5, pady=6)
        delete_btn = ctk.CTkButton(actions, text="Eliminar", command=self._on_delete_backup)
        delete_btn.pack(side="left", padx=5, pady=6)
    
    def _create_usuarios_tab(self, parent):
        """Crea la pestaña de administración de usuarios"""
        table_frame = ctk.CTkFrame(parent, fg_color="#1a1a1a")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ctk.CTkScrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.usuarios_tree = ttk.Treeview(
            table_frame, columns=("usuario", "rol", "nombre", "estado"),
            show="headings", yscrollcommand=scrollbar.set)
        self.usuarios_tree.heading("usuario", text="Usuario")
        self.usuarios_tree.heading("rol", text="Rol")
        self.usuarios_tree.heading("nombre", text="Nombre")
        self.usuarios_tree.heading("estado", text="Estado")
        self.usuarios_tree.column("usuario", width=150, minwidth=100)
        self.usuarios_tree.column("rol", width=130, minwidth=90)
        self.usuarios_tree.column("nombre", width=220, minwidth=150)
        self.usuarios_tree.column("estado", width=100, minwidth=70)
        self.usuarios_tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.usuarios_tree.yview)
        
        actions = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        actions.pack(fill="x", padx=10, pady=(0, 10))
        
        nuevo_btn = ctk.CTkButton(actions, text="Nuevo Usuario", command=self._on_new_usuario)
        nuevo_btn.pack(side="left", padx=5, pady=6)
        editar_btn = ctk.CTkButton(actions, text="Editar", command=self._on_edit_usuario)
        editar_btn.pack(side="left", padx=5, pady=6)
        toggle_btn = ctk.CTkButton(
            actions, text="Activar / Desactivar", command=self._on_toggle_usuario)
        toggle_btn.pack(side="left", padx=5, pady=6)
        
        self.usuarios_tree.bind("<Double-1>", lambda e: self._on_edit_usuario())
    
    def _create_general_tab(self, parent):
        """Crea la pestaña de configuración general"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.nombre_institucion_entry = self._create_form_field(form_frame, "Nombre Institución:", 0)
        self.ruc_entry = self._create_form_field(form_frame, "RUC:", 1)
        self.direccion_entry = self._create_form_field(form_frame, "Dirección:", 2)
        self.telefono_entry = self._create_form_field(form_frame, "Teléfono:", 3)
        self.email_entry = self._create_form_field(form_frame, "Email:", 4)
    
    def _create_nomina_tab(self, parent):
        """Crea la pestaña de configuración de nómina"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.porcentaje_seguro_entry = self._create_form_field(form_frame, "Porcentaje Seguro Social (%):", 0)
        self.porcentaje_pension_entry = self._create_form_field(form_frame, "Porcentaje Pensión (%):", 1)
        self.porcentaje_impuesto_entry = self._create_form_field(form_frame, "Porcentaje Impuesto (%):", 2)
        self.salario_minimo_entry = self._create_form_field(form_frame, "Salario Mínimo:", 3)
    
    def _create_rrhh_tab(self, parent):
        """Crea la pestaña de configuración de recursos humanos"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.dias_vacaciones_entry = self._create_form_field(form_frame, "Días Vacaciones Anual:", 0)
        self.horas_laborales_entry = self._create_form_field(form_frame, "Horas Laborales Semana:", 1)
    
    def _create_form_field(self, parent, label: str, row: int) -> ctk.CTkEntry:
        """Crea un campo de formulario"""
        ctk.CTkLabel(parent, text=label, text_color="white").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        entry = ctk.CTkEntry(parent, width=300, fg_color="#3c3c3c", text_color="white")
        entry.grid(row=row, column=1, padx=5, pady=5, sticky="w")
        return entry
    
    def _load_configuracion(self):
        """Carga la configuración actual"""
        try:
            def safe_str(val):
                return "" if val is None else str(val)
            
            # Configuración general
            general_config = self.main_window.config_service.obtener_configuracion_general()
            self.nombre_institucion_entry.delete(0, tk.END)
            self.nombre_institucion_entry.insert(0, safe_str(general_config.get("nombre_institucion", "")))
            self.ruc_entry.delete(0, tk.END)
            self.ruc_entry.insert(0, safe_str(general_config.get("ruc", "")))
            self.direccion_entry.delete(0, tk.END)
            self.direccion_entry.insert(0, safe_str(general_config.get("direccion", "")))
            self.telefono_entry.delete(0, tk.END)
            self.telefono_entry.insert(0, safe_str(general_config.get("telefono", "")))
            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, safe_str(general_config.get("email", "")))
            
            # Configuración de nómina
            nomina_config = self.main_window.config_service.obtener_configuracion_nomina()
            self.porcentaje_seguro_entry.delete(0, tk.END)
            self.porcentaje_seguro_entry.insert(0, safe_str(nomina_config.get("porcentaje_seguro", "")))
            self.porcentaje_pension_entry.delete(0, tk.END)
            self.porcentaje_pension_entry.insert(0, safe_str(nomina_config.get("porcentaje_pension", "")))
            self.porcentaje_impuesto_entry.delete(0, tk.END)
            self.porcentaje_impuesto_entry.insert(0, safe_str(nomina_config.get("porcentaje_impuesto", "")))
            self.salario_minimo_entry.delete(0, tk.END)
            self.salario_minimo_entry.insert(0, safe_str(nomina_config.get("salario_minimo", "")))
            
            # Configuración de RRHH
            rrhh_config = self.main_window.config_service.obtener_configuracion_recursos_humanos()
            self.dias_vacaciones_entry.delete(0, tk.END)
            self.dias_vacaciones_entry.insert(0, safe_str(rrhh_config.get("dias_vacaciones_anual", "")))
            self.horas_laborales_entry.delete(0, tk.END)
            self.horas_laborales_entry.insert(0, safe_str(rrhh_config.get("horas_laborales_semana", "")))
            
            # Datos de la pestaña de seguridad y usuarios
            self._cargar_seguridad_y_usuarios()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar configuración: {str(e)}")
    
    def _cargar_seguridad_y_usuarios(self):
        """Carga valores de seguridad, respaldos y usuarios"""
        try:
            config_seguridad = self.main_window.config_service.obtener_categoria_dict("seguridad")
            self.backup_enabled_var.set(bool(config_seguridad.get("backup_enabled", True)))
            self.audit_enabled_var.set(bool(config_seguridad.get("audit_enabled", True)))
            self.backup_interval_entry.delete(0, tk.END)
            self.backup_interval_entry.insert(
                0, str(config_seguridad.get("backup_interval_hours", 24)))
        except Exception:
            pass
        self._refresh_backups()
        self._load_usuarios()
    
    def _on_save(self):
        """Guarda la configuración"""
        try:
            # Configuración general
            self.main_window.config_service.establecer_valor("nombre_institucion", self.nombre_institucion_entry.get())
            self.main_window.config_service.establecer_valor("ruc", self.ruc_entry.get())
            self.main_window.config_service.establecer_valor("direccion", self.direccion_entry.get())
            self.main_window.config_service.establecer_valor("telefono", self.telefono_entry.get())
            self.main_window.config_service.establecer_valor("email", self.email_entry.get())
            
            # Configuración de nómina
            self.main_window.config_service.establecer_valor("porcentaje_seguro", self._parse_float(self.porcentaje_seguro_entry.get()))
            self.main_window.config_service.establecer_valor("porcentaje_pension", self._parse_float(self.porcentaje_pension_entry.get()))
            self.main_window.config_service.establecer_valor("porcentaje_impuesto", self._parse_float(self.porcentaje_impuesto_entry.get()))
            self.main_window.config_service.establecer_valor("salario_minimo", self._parse_float(self.salario_minimo_entry.get()))
            
            # Configuración de RRHH
            self.main_window.config_service.establecer_valor("dias_vacaciones_anual", self._parse_int(self.dias_vacaciones_entry.get()))
            self.main_window.config_service.establecer_valor("horas_laborales_semana", self._parse_int(self.horas_laborales_entry.get()))
            
            messagebox.showinfo("Éxito", "Configuración guardada correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar configuración: {str(e)}")
    
    def _parse_float(self, value: str) -> Optional[float]:
        """Parsea un float"""
        try:
            return float(value) if value else None
        except ValueError:
            return None
    
    def _parse_int(self, value: str) -> Optional[int]:
        """Parsea un int"""
        try:
            return int(value) if value else None
        except ValueError:
            return None
    
    # ------------------------------------------------------------------
    # Seguridad y respaldos
    # ------------------------------------------------------------------
    def _on_save_seguridad(self):
        """Guarda la configuración de seguridad y auditoría"""
        try:
            self.main_window.config_service.establecer_valor(
                "backup_enabled", bool(self.backup_enabled_var.get()))
            self.main_window.config_service.establecer_valor(
                "audit_enabled", bool(self.audit_enabled_var.get()))
            intervalo = self._parse_int(self.backup_interval_entry.get()) or 24
            self.main_window.config_service.establecer_valor(
                "backup_interval_hours", max(1, min(intervalo, 720)))
            self._load_configuracion()
            self._refresh_backups()
            messagebox.showinfo("Éxito", "Configuración de seguridad guardada")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar configuración: {str(e)}")
    
    def _backup_seleccionado(self) -> Optional[str]:
        """Nombre del respaldo seleccionado en la tabla"""
        seleccion = self.backup_tree.selection()
        if not seleccion:
            return None
        tags = self.backup_tree.item(seleccion[0], "tags") or ()
        return tags[0] if tags else None
    
    def _refresh_backups(self):
        """Actualiza la lista de respaldos disponibles"""
        from src.utils.backup_manager import get_backup_manager
        from src.utils.helpers import format_file_size
        
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        try:
            backups = get_backup_manager().list_backups()
            respaldo_texto = "Sí" if self.backup_enabled_var.get() else "No"
            self.backup_status_label.configure(
                text=f"Respaldo al cerrar: {respaldo_texto}  ·  "
                     f"Total: {len(backups)} respaldo(s)")
            for b in backups:
                fecha = str(b.get("timestamp", ""))
                if len(fecha) == 15:
                    fecha = f"{fecha[6:8]}/{fecha[4:6]}/{fecha[:4]} {fecha[9:11]}:{fecha[11:13]}"
                self.backup_tree.insert("", "end", values=(
                    b.get("name", ""),
                    fecha,
                    format_file_size(b.get("size_bytes", 0)),
                    "comprimido" if b.get("compressed") else "directo",
                ), tags=(b.get("name", ""),))
        except Exception as e:
            self.backup_status_label.configure(text=f"Error al listar respaldos: {e}")
    
    def _on_create_backup(self):
        """Crea un respaldo manual de la base de datos"""
        try:
            from src.utils.backup_manager import get_backup_manager
            from src.utils.helpers import get_timestamp
            info = get_backup_manager().create_backup(f"manual_{get_timestamp()}")
            self._refresh_backups()
            messagebox.showinfo("Éxito", f"Respaldo creado: {info.get('name')}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear el respaldo: {str(e)}")
    
    def _on_verify_backup(self):
        """Verifica la integridad del respaldo seleccionado"""
        nombre = self._backup_seleccionado()
        if not nombre:
            messagebox.showwarning("Advertencia", "Seleccione un respaldo")
            return
        try:
            from src.utils.backup_manager import get_backup_manager
            resultado = get_backup_manager().verify_backup_integrity(nombre)
            mensaje = (
                f"Respaldo: {nombre}\n\n"
                f"Archivo presente: {'Sí' if resultado['exists'] else 'No'}\n"
                f"Tamaño correcto: {'Sí' if resultado['size_correct'] else 'No'}\n"
                f"Checksum válido: {'Sí' if resultado['checksum_valid'] else 'No'}\n"
                f"Integridad: {'OK' if resultado['integrity_ok'] else 'CORRUPTA'}"
            )
            if resultado["integrity_ok"]:
                messagebox.showinfo("Verificación de Respaldo", mensaje)
            else:
                messagebox.showwarning("Verificación de Respaldo", mensaje)
        except Exception as e:
            messagebox.showerror("Error", f"Error al verificar el respaldo: {str(e)}")
    
    def _on_restore_backup(self):
        """Restaura el respaldo seleccionado"""
        nombre = self._backup_seleccionado()
        if not nombre:
            messagebox.showwarning("Advertencia", "Seleccione un respaldo")
            return
        
        if not messagebox.askyesno(
            "Confirmar restauración",
            f"Se reemplazará la base de datos actual por el respaldo '{nombre}'.\n"
            "¿Desea continuar?",
        ):
            return
        try:
            from src.config import db_config
            db_config.restore_backup(nombre)
            messagebox.showinfo(
                "Restauración exitosa",
                "Base de datos restaurada. La aplicación se reiniciará.",
            )
            self.main_window._on_logout()
        except Exception as e:
            messagebox.showerror("Error", f"Error al restaurar el respaldo: {str(e)}")
    
    def _on_delete_backup(self):
        """Elimina el respaldo seleccionado"""
        nombre = self._backup_seleccionado()
        if not nombre:
            messagebox.showwarning("Advertencia", "Seleccione un respaldo")
            return
        if messagebox.askyesno(
            "Confirmar", f"¿Eliminar el respaldo '{nombre}'?"):
            try:
                from src.utils.backup_manager import get_backup_manager
                if get_backup_manager().delete_backup(nombre):
                    self._refresh_backups()
                    messagebox.showinfo("Éxito", "Respaldo eliminado")
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el respaldo")
            except Exception as e:
                messagebox.showerror("Error", f"Error al eliminar el respaldo: {str(e)}")
    
    # ------------------------------------------------------------------
    # Administración de usuarios
    # ------------------------------------------------------------------
    def _load_usuarios(self):
        """Carga los usuarios del sistema"""
        from src.config import db_config
        from src.services.auth_service import AuthService
        
        for item in self.usuarios_tree.get_children():
            self.usuarios_tree.delete(item)
        
        session = db_config.get_session()
        try:
            usuarios = AuthService(session).listar_usuarios()
            for u in usuarios:
                self.usuarios_tree.insert("", "end", values=(
                    u.username,
                    u.rol_valor,
                    u.nombre_completo or "",
                    "Activo" if u.activo else "Inactivo",
                ), tags=(str(u.id),))
        finally:
            db_config.close_session(session)
    
    def _usuario_seleccionado(self) -> Optional[int]:
        """ID del usuario seleccionado"""
        seleccion = self.usuarios_tree.selection()
        if not seleccion:
            return None
        tags = self.usuarios_tree.item(seleccion[0], "tags") or ()
        if not tags:
            return None
        try:
            return int(tags[0])
        except (TypeError, ValueError):
            return None
    
    def _on_new_usuario(self):
        """Crea un nuevo usuario de sistema"""
        dialog = UsuarioDialog(self, self.main_window)
        self.wait_window(dialog)
        if dialog.result:
            self._load_usuarios()
    
    def _on_edit_usuario(self):
        """Edita el usuario seleccionado"""
        usuario_id = self._usuario_seleccionado()
        if usuario_id is None:
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        dialog = UsuarioDialog(self, self.main_window, usuario_id)
        self.wait_window(dialog)
        if dialog.result:
            self._load_usuarios()
    
    def _on_toggle_usuario(self):
        """Activa o desactiva el usuario seleccionado"""
        from src.config import db_config
        from src.services.auth_service import AuthService
        
        usuario_id = self._usuario_seleccionado()
        if usuario_id is None:
            messagebox.showwarning("Advertencia", "Seleccione un usuario")
            return
        
        session = db_config.get_session()
        try:
            auth = AuthService(session)
            usuario = auth.usuario_por_id(usuario_id)
            if not usuario:
                messagebox.showerror("Error", "Usuario no encontrado")
                return
            accion = "desactivar" if usuario.activo else "activar"
            if not messagebox.askyesno(
                "Confirmar", f"¿Desea {accion} al usuario '{usuario.username}'?"):
                return
            auth.actualizar_usuario(
                usuario_id,
                {"activo": 0 if usuario.activo else 1},
                usuario_actual=self.main_window.current_user,
            )
            self._load_usuarios()
            messagebox.showinfo("Éxito", f"Usuario {accion}do correctamente")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        finally:
            db_config.close_session(session)


class InfoDialog(ctk.CTkToplevel):
    """Ventana de solo lectura para mostrar información extensa"""
    
    def __init__(self, parent, title: str, text: str):
        super().__init__(parent)
        self.title(title)
        self.geometry("620x460")
        mantener_ventana_al_frente(self)
        if parent is not None:
            self.transient(parent)
        
        container = ctk.CTkFrame(self, fg_color="#2b2b2b")
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        textbox = ctk.CTkTextbox(
            container, fg_color="#1f1f1f", text_color="#e6e6e6",
            font=ctk.CTkFont(family="Consolas", size=12), wrap="word")
        textbox.pack(fill="both", expand=True, padx=8, pady=8)
        textbox.insert("1.0", text)
        textbox.configure(state="disabled")
        
        close_btn = ctk.CTkButton(container, text="Cerrar", width=120, command=self.destroy)
        close_btn.pack(pady=(0, 8))


class PagoDialog(ctk.CTkToplevel):
    """Diálogo para registrar o editar un pago manual"""
    
    TIPOS = [
        ("salario_base", "Salario Base"),
        ("bonificacion", "Bonificación"),
        ("horas_extra", "Horas Extra"),
        ("comision", "Comisión"),
        ("descuento", "Descuento"),
    ]
    METODOS = ["transferencia", "efectivo", "cheque", "deposito"]
    
    def __init__(self, parent, main_window, pago=None):
        super().__init__(parent)
        self.main_window = main_window
        self.pago = pago
        self.result = False
        
        self.title("Editar Pago" if pago else "Nuevo Pago")
        self.geometry("620x560")
        mantener_ventana_al_frente(self)
        if parent is not None:
            self.transient(parent)
        
        self._create_widgets()
        if pago:
            self._load_pago_data()
    
    def _create_widgets(self):
        form = ctk.CTkFrame(self, fg_color="#2b2b2b")
        form.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Empleado
        ctk.CTkLabel(form, text="Empleado:", text_color="white").grid(
            row=0, column=0, padx=8, pady=6, sticky="e")
        self.empleado_combo = ttk.Combobox(
            form, width=38, state="readonly", font=("Arial", 9))
        self.empleado_combo.grid(row=0, column=1, columnspan=3, padx=8, pady=6, sticky="w")
        self._load_empleados()
        
        # Tipo de pago
        ctk.CTkLabel(form, text="Tipo de Pago:", text_color="white").grid(
            row=1, column=0, padx=8, pady=6, sticky="e")
        self.tipo_combo = ttk.Combobox(
            form, width=30, state="readonly", font=("Arial", 9))
        self.tipo_combo['values'] = [etiqueta for _, etiqueta in self.TIPOS]
        self.tipo_combo.grid(row=1, column=1, padx=8, pady=6, sticky="w")
        self.tipo_combo.current(0)
        
        ctk.CTkLabel(form, text="Método:", text_color="white").grid(
            row=1, column=2, padx=8, pady=6, sticky="e")
        self.metodo_combo = ttk.Combobox(
            form, width=20, values=self.METODOS, state="readonly", font=("Arial", 9))
        self.metodo_combo.grid(row=1, column=3, padx=8, pady=6, sticky="w")
        self.metodo_combo.set("transferencia")
        
        # Periodo
        ctk.CTkLabel(form, text="Período desde:", text_color="white").grid(
            row=2, column=0, padx=8, pady=6, sticky="e")
        self.periodo_inicio_entry = ctk.CTkEntry(
            form, width=110, fg_color="#3c3c3c", text_color="white",
            placeholder_text="DD/MM/YYYY")
        self.periodo_inicio_entry.grid(row=2, column=1, padx=8, pady=6, sticky="w")
        
        ctk.CTkLabel(form, text="Período hasta:", text_color="white").grid(
            row=2, column=2, padx=8, pady=6, sticky="e")
        self.periodo_fin_entry = ctk.CTkEntry(
            form, width=110, fg_color="#3c3c3c", text_color="white",
            placeholder_text="DD/MM/YYYY")
        self.periodo_fin_entry.grid(row=2, column=3, padx=8, pady=6, sticky="w")
        
        # Montos
        monto_fila = 3
        ctk.CTkLabel(form, text="Salario Base:", text_color="white").grid(
            row=monto_fila, column=0, padx=8, pady=6, sticky="e")
        self.salario_entry = ctk.CTkEntry(
            form, width=140, fg_color="#3c3c3c", text_color="white")
        self.salario_entry.grid(row=monto_fila, column=1, padx=8, pady=6, sticky="w")
        
        ctk.CTkLabel(form, text="Bonificaciones:", text_color="white").grid(
            row=monto_fila, column=2, padx=8, pady=6, sticky="e")
        self.bonificaciones_entry = ctk.CTkEntry(
            form, width=140, fg_color="#3c3c3c", text_color="white")
        self.bonificaciones_entry.grid(
            row=monto_fila, column=3, padx=8, pady=6, sticky="w")
        
        ctk.CTkLabel(form, text="Horas Extra:", text_color="white").grid(
            row=4, column=0, padx=8, pady=6, sticky="e")
        self.horas_extra_entry = ctk.CTkEntry(
            form, width=140, fg_color="#3c3c3c", text_color="white")
        self.horas_extra_entry.grid(row=4, column=1, padx=8, pady=6, sticky="w")
        
        ctk.CTkLabel(form, text="Otras Deducciones:", text_color="white").grid(
            row=4, column=2, padx=8, pady=6, sticky="e")
        self.otras_deducciones_entry = ctk.CTkEntry(
            form, width=140, fg_color="#3c3c3c", text_color="white")
        self.otras_deducciones_entry.grid(
            row=4, column=3, padx=8, pady=6, sticky="w")
        
        ctk.CTkLabel(form, text="Descuentos:", text_color="white").grid(
            row=5, column=0, padx=8, pady=6, sticky="e")
        self.descuentos_entry = ctk.CTkEntry(
            form, width=140, fg_color="#3c3c3c", text_color="white")
        self.descuentos_entry.grid(row=5, column=1, padx=8, pady=6, sticky="w")
        
        self.pagado_var = tk.BooleanVar(value=False)
        pagado_chk = ctk.CTkCheckBox(
            form, text="Marcar como pagado", variable=self.pagado_var)
        pagado_chk.grid(row=5, column=3, padx=8, pady=6, sticky="w")
        
        ctk.CTkLabel(form, text="Observaciones:", text_color="white").grid(
            row=6, column=0, padx=8, pady=6, sticky="ne")
        self.observaciones_text = ctk.CTkTextbox(
            form, width=400, height=60, fg_color="#3c3c3c", text_color="white")
        self.observaciones_text.grid(
            row=6, column=1, columnspan=3, padx=8, pady=6, sticky="w")
        
        # Botones
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        save_btn = ctk.CTkButton(btn_frame, text="Guardar", command=self._on_save)
        save_btn.pack(side="right", padx=5)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy)
        cancel_btn.pack(side="right", padx=5)
    
    def _load_empleados(self):
        empleados = self.main_window.empleado_service.listar_empleados_activos()
        self.empleado_map = {
            f"{emp.nombre_completo} ({emp.cedula})": emp.id for emp in empleados}
        self.empleado_combo['values'] = list(self.empleado_map.keys())
        if self.pago:
            empleado = self.main_window.empleado_service.obtener_empleado(
                self.pago.empleado_id)
            if empleado:
                etiqueta = f"{empleado.nombre_completo} ({empleado.cedula})"
                if etiqueta in self.empleado_map:
                    self.empleado_combo.set(etiqueta)
                else:
                    self.empleado_combo['values'] = \
                        [etiqueta] + list(self.empleado_map.keys())
                    self.empleado_combo.set(etiqueta)
                self.empleado_combo.configure(state="readonly")
        elif self.empleado_map:
            self.empleado_combo.current(0)
    
    def _load_pago_data(self):
        """Precarga los datos del pago en el formulario"""
        if not self.pago:
            return
        tipo_actual = self.pago.tipo_pago
        for valor, etiqueta in self.TIPOS:
            if valor == tipo_actual:
                self.tipo_combo.set(etiqueta)
                break
        else:
            self.tipo_combo.set(tipo_actual)
        self.metodo_combo.set(self.pago.metodo_pago or "transferencia")
        self.periodo_inicio_entry.insert(
            0, format_date(self.pago.periodo_inicio))
        self.periodo_fin_entry.insert(0, format_date(self.pago.periodo_fin))
        self.salario_entry.insert(0, str(float(self.pago.salario_base or 0)))
        self.bonificaciones_entry.insert(
            0, str(float(self.pago.bonificaciones or 0)))
        self.horas_extra_entry.insert(
            0, str(float(self.pago.horas_extra or 0)))
        self.otras_deducciones_entry.insert(
            0, str(float(self.pago.otras_deducciones or 0)))
        self.descuentos_entry.insert(0, str(float(self.pago.descuentos or 0)))
        self.pagado_var.set(bool(self.pago.pagado))
        if self.pago.observaciones:
            self.observaciones_text.insert("1.0", self.pago.observaciones)
    
    def _on_save(self):
        """Guarda el pago (crea o actualiza)"""
        try:
            if not self.empleado_combo.get():
                messagebox.showerror("Error", "Seleccione un empleado")
                return
            
            if self.pago:
                empleado_id = self.pago.empleado_id
            else:
                empleado_id = self.empleado_map[self.empleado_combo.get()]
            
            tipo_etiqueta = self.tipo_combo.get()
            tipo_valor = tipo_etiqueta
            for valor, etiqueta in self.TIPOS:
                if etiqueta == tipo_etiqueta:
                    tipo_valor = valor
                    break
            
            datos = {
                "empleado_id": empleado_id,
                "tipo_pago": tipo_valor,
                "metodo_pago": self.metodo_combo.get(),
                "periodo_inicio": self.periodo_inicio_entry.get(),
                "periodo_fin": self.periodo_fin_entry.get(),
                "salario_base": self._parse_float(self.salario_entry.get()),
                "bonificaciones": self._parse_float(self.bonificaciones_entry.get()),
                "horas_extra": self._parse_float(self.horas_extra_entry.get()),
                "otras_deducciones": self._parse_float(self.otras_deducciones_entry.get()),
                "descuentos": self._parse_float(self.descuentos_entry.get()),
                "pagado": 1 if self.pagado_var.get() else 0,
                "observaciones": self.observaciones_text.get("1.0", "end").strip() or None,
            }
            
            errores = self.main_window.pago_service.validar_datos_pago(datos)
            if errores:
                messagebox.showerror("Errores de Validación", "\n".join(errores))
                return
            
            if self.pago:
                self.main_window.pago_service.actualizar_pago(self.pago.id, datos)
                messagebox.showinfo("Éxito", "Pago actualizado correctamente")
            else:
                self.main_window.pago_service.crear_pago(datos)
                messagebox.showinfo("Éxito", "Pago registrado correctamente")
            
            self.result = True
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Error de Validación", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar pago: {str(e)}")
    
    def _parse_float(self, value: str) -> Optional[float]:
        try:
            return float(value) if value else 0.0
        except ValueError:
            return 0.0


class UsuarioDialog(ctk.CTkToplevel):
    """Diálogo para crear o editar un usuario de sistema"""
    
    def __init__(self, parent, main_window, usuario_id: Optional[int] = None):
        super().__init__(parent)
        self.main_window = main_window
        self.usuario_id = usuario_id
        self.result = False
        
        self.title("Editar Usuario" if usuario_id else "Nuevo Usuario")
        self.geometry("480x430")
        mantener_ventana_al_frente(self)
        if parent is not None:
            self.transient(parent)
        
        self.usuario = None
        if usuario_id:
            from src.config import db_config
            from src.services.auth_service import AuthService
            session = db_config.get_session()
            try:
                self.usuario = AuthService(session).usuario_por_id(usuario_id)
            finally:
                db_config.close_session(session)
        
        self._create_widgets()
        if self.usuario:
            self._load_usuario_data()
    
    def _create_widgets(self):
        form = ctk.CTkFrame(self, fg_color="#2b2b2b")
        form.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(form, text="Usuario:", text_color="white").grid(
            row=0, column=0, padx=8, pady=6, sticky="e")
        self.username_entry = ctk.CTkEntry(
            form, width=260, fg_color="#3c3c3c", text_color="white")
        self.username_entry.grid(row=0, column=1, padx=8, pady=6, sticky="w")
        
        ctk.CTkLabel(form, text="Nombre Completo:", text_color="white").grid(
            row=1, column=0, padx=8, pady=6, sticky="e")
        self.nombre_entry = ctk.CTkEntry(
            form, width=260, fg_color="#3c3c3c", text_color="white")
        self.nombre_entry.grid(row=1, column=1, padx=8, pady=6, sticky="w")
        
        ctk.CTkLabel(form, text="Rol:", text_color="white").grid(
            row=2, column=0, padx=8, pady=6, sticky="e")
        self.rol_combo = ttk.Combobox(
            form, values=["admin", "manager", "user", "viewer"],
            width=20, state="readonly", font=("Arial", 9))
        self.rol_combo.grid(row=2, column=1, padx=8, pady=6, sticky="w")
        self.rol_combo.set("user")
        
        if self.usuario is None:
            ctk.CTkLabel(form, text="Contraseña:", text_color="white").grid(
                row=3, column=0, padx=8, pady=6, sticky="e")
            self.password_entry = ctk.CTkEntry(
                form, width=260, show="*", fg_color="#3c3c3c",
                text_color="white")
            self.password_entry.grid(row=3, column=1, padx=8, pady=6, sticky="w")
        else:
            ctk.CTkLabel(
                form, text="Nueva Contraseña (opcional):",
                text_color="white").grid(row=3, column=0, padx=8, pady=6, sticky="e")
            self.password_entry = ctk.CTkEntry(
                form, width=260, show="*", fg_color="#3c3c3c",
                text_color="white", placeholder_text="Dejar vacía para no cambiar")
            self.password_entry.grid(row=3, column=1, padx=8, pady=6, sticky="w")
        
        self.activo_var = tk.BooleanVar(value=True)
        activo_chk = ctk.CTkCheckBox(
            form, text="Cuenta activa", variable=self.activo_var)
        activo_chk.grid(row=4, column=1, padx=8, pady=6, sticky="w")
        
        hint = ctk.CTkLabel(
            form,
            text="Mínimo 6 caracteres para la contraseña.",
            text_color="#888888", font=ctk.CTkFont(size=11))
        hint.grid(row=5, column=1, padx=8, pady=2, sticky="w")
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        save_btn = ctk.CTkButton(btn_frame, text="Guardar", command=self._on_save)
        save_btn.pack(side="right", padx=5)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancelar", command=self.destroy)
        cancel_btn.pack(side="right", padx=5)
    
    def _load_usuario_data(self):
        self.username_entry.insert(0, self.usuario.username)
        if self.usuario.nombre_completo:
            self.nombre_entry.insert(0, self.usuario.nombre_completo)
        self.rol_combo.set(self.usuario.rol_valor)
        self.activo_var.set(bool(self.usuario.activo))
    
    def _on_save(self):
        from src.config import db_config
        from src.services.auth_service import AuthService
        
        try:
            session = db_config.get_session()
            try:
                auth = AuthService(session)
                if self.usuario:
                    datos = {
                        "username": self.username_entry.get(),
                        "nombre_completo": self.nombre_entry.get(),
                        "rol": self.rol_combo.get(),
                        "activo": 1 if self.activo_var.get() else 0,
                    }
                    nueva_pass = self.password_entry.get()
                    if nueva_pass:
                        datos["password"] = nueva_pass
                    auth.actualizar_usuario(
                        self.usuario.id, datos,
                        usuario_actual=self.main_window.current_user)
                    messagebox.showinfo("Éxito", "Usuario actualizado correctamente")
                else:
                    auth.crear_usuario(
                        username=self.username_entry.get(),
                        password=self.password_entry.get(),
                        rol=self.rol_combo.get(),
                        nombre_completo=self.nombre_entry.get(),
                        debe_cambiar_password=False,
                    )
                    messagebox.showinfo("Éxito", "Usuario creado correctamente")
                self.result = True
                self.destroy()
            finally:
                db_config.close_session(session)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar usuario: {str(e)}")