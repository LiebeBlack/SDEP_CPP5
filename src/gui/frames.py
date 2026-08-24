"""
GUI Frames
Frames específicos para cada módulo de la aplicación
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import tkinter as tk
import os
from typing import Optional, List
from datetime import date, datetime

from src.models import Empleado, TipoEmpleado, TipoDocumento, TipoIncidencia, EstadoIncidencia, TipoPago, MetodoPago
from src.utils.helpers import format_date, format_currency, calculate_age
from src.utils.pdf_generator import PDFGenerator


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
        
        actions = [
            ("Nuevo Empleado", lambda: self.main_window._show_frame("empleados")),
            ("Nuevo Documento", lambda: self.main_window._show_frame("documentos")),
            ("Nueva Incidencia", lambda: self.main_window._show_frame("incidencias")),
            ("Generar Nómina", lambda: self.main_window._show_frame("nomina")),
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
        
        # Botones de acción
        btn_frame = ctk.CTkFrame(search_frame)
        btn_frame.pack(side="right", padx=5)
        
        new_btn = ctk.CTkButton(btn_frame, text="Nuevo Empleado", command=self._on_new_empleado)
        new_btn.pack(side="left", padx=5)
        
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
        
        self.tree.column("cedula", width=120)
        self.tree.column("nombre", width=200)
        self.tree.column("cargo", width=150)
        self.tree.column("departamento", width=150)
        self.tree.column("tipo", width=100)
        self.tree.column("salario", width=100)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)
        
        # Eventos
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-1>", self._on_single_click)
        
        # Menú contextual
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Ver Detalles", command=self._on_view_details)
        self.context_menu.add_command(label="Editar", command=self._on_edit)
        self.context_menu.add_command(label="Documentos", command=self._on_documents)
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
                    self.tree.insert("", "end", values=(
                        emp.cedula,
                        emp.nombre_completo,
                        emp.cargo,
                        emp.departamento,
                        emp.tipo_empleado,
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
            self.tree.insert("", "end", values=(
                emp.cedula,
                emp.nombre_completo,
                emp.cargo,
                emp.departamento,
                emp.tipo_empleado,
                format_currency(emp.salario_base)
            ), tags=(str(emp.id),))
    
    def _on_double_click(self, event):
        """Maneja doble clic en un empleado"""
        self._on_view_details()
    
    def _on_single_click(self, event):
        """Maneja clic simple en un empleado"""
        self._on_view_details()
    
    def _show_context_menu(self, event):
        """Muestra el menú contextual"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _get_selected_empleado(self) -> Optional[Empleado]:
        """Obtiene el empleado seleccionado"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            empleado_id = int(item["tags"][0])
            return self.main_window.empleado_service.obtener_empleado(empleado_id)
        return None
    
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
            self.main_window._show_frame("documentos")
            # Aquí se podría pasar el ID del empleado al frame de documentos
    
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
        
        # Hacer que la ventana esté siempre al frente
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
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
        self.apellidos_label = self._create_detail_field(form_frame, "Apellidos:", 0, 1)
        self.cedula_label = self._create_detail_field(form_frame, "Cédula:", 1, 0)
        self.fecha_nacimiento_label = self._create_detail_field(form_frame, "Fecha Nacimiento:", 1, 1)
        
        self.genero_label = self._create_detail_field(form_frame, "Género:", 2, 0)
        self.estado_civil_label = self._create_detail_field(form_frame, "Estado Civil:", 2, 1)
        
        self.peso_label = self._create_detail_field(form_frame, "Peso (kg):", 3, 0)
        self.altura_label = self._create_detail_field(form_frame, "Altura (m):", 3, 1)
        self.tipo_sangre_label = self._create_detail_field(form_frame, "Tipo Sangre:", 4, 0)
        self.nacionalidad_label = self._create_detail_field(form_frame, "Nacionalidad:", 4, 1)
    
    def _create_laboral_details_tab(self, parent):
        """Crea la pestaña de datos laborales (solo lectura)"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tipo_empleado_label = self._create_detail_field(form_frame, "Tipo Empleado:", 0, 0)
        self.cargo_label = self._create_detail_field(form_frame, "Cargo:", 0, 1)
        self.departamento_label = self._create_detail_field(form_frame, "Departamento:", 1, 0)
        self.fecha_contratacion_label = self._create_detail_field(form_frame, "Fecha Contratación:", 1, 1)
        
        self.salario_base_label = self._create_detail_field(form_frame, "Salario Base:", 2, 0)
        self.nivel_educativo_label = self._create_detail_field(form_frame, "Nivel Educativo:", 2, 1)
        self.especialidad_label = self._create_detail_field(form_frame, "Especialidad:", 3, 0)
        self.titulo_obtenido_label = self._create_detail_field(form_frame, "Título Obtenido:", 3, 1)
        
        # Información adicional
        self.activo_label = self._create_detail_field(form_frame, "Estado:", 4, 0)
        self.antiguedad_label = self._create_detail_field(form_frame, "Antigüedad:", 4, 1)
    
    def _create_contacto_details_tab(self, parent):
        """Crea la pestaña de contacto (solo lectura)"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.telefono_label = self._create_detail_field(form_frame, "Teléfono:", 0, 0)
        self.celular_label = self._create_detail_field(form_frame, "Celular:", 0, 1)
        self.email_label = self._create_detail_field(form_frame, "Email:", 1, 0)
        self.direccion_label = self._create_detail_field(form_frame, "Dirección:", 1, 1)
        
        self.ciudad_label = self._create_detail_field(form_frame, "Ciudad:", 2, 0)
        self.estado_label = self._create_detail_field(form_frame, "Estado:", 2, 1)
        self.codigo_postal_label = self._create_detail_field(form_frame, "Código Postal:", 3, 0)
        
        # Contacto de emergencia
        emergency_frame = ctk.CTkFrame(form_frame, fg_color="#3c3c3c")
        emergency_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        emergency_label = ctk.CTkLabel(emergency_frame, text="Contacto de Emergencia", 
                                     font=ctk.CTkFont(weight="bold"), text_color="white")
        emergency_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        self.contacto_emergencia_nombre_label = self._create_detail_field(emergency_frame, "Nombre:", 1, 0)
        self.contacto_emergencia_telefono_label = self._create_detail_field(emergency_frame, "Teléfono:", 1, 1)
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
        
        # Hacer que la ventana esté siempre al frente
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        self._create_widgets()
        
        if empleado:
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
        self.apellidos_entry = self._create_form_field(form_frame, "Apellidos:", 0, 1)
        self.cedula_entry = self._create_form_field(form_frame, "Cédula:", 1, 0)
        self.fecha_nacimiento_entry = self._create_form_field(form_frame, "Fecha Nacimiento:", 1, 1)
        
        self.genero_combo = self._create_combo_field(form_frame, "Género:", 2, 0, 
                                                      ["masculino", "femenino", "otro"])
        self.estado_civil_combo = self._create_combo_field(form_frame, "Estado Civil:", 2, 1,
                                                           ["soltero", "casado", "divorciado", "viudo", "union_libre"])
        
        self.peso_entry = self._create_form_field(form_frame, "Peso (kg):", 3, 0)
        self.altura_entry = self._create_form_field(form_frame, "Altura (m):", 3, 1)
        self.tipo_sangre_entry = self._create_form_field(form_frame, "Tipo Sangre:", 4, 0)
        self.nacionalidad_entry = self._create_form_field(form_frame, "Nacionalidad:", 4, 1)
    
    def _create_laboral_tab(self, parent):
        """Crea la pestaña de datos laborales"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tipo_empleado_combo = self._create_combo_field(form_frame, "Tipo Empleado:", 0, 0,
                                                            ["docente", "administrativo", "mantenimiento"])
        self.cargo_entry = self._create_form_field(form_frame, "Cargo:", 0, 1)
        self.departamento_entry = self._create_form_field(form_frame, "Departamento:", 1, 0)
        self.fecha_contratacion_entry = self._create_form_field(form_frame, "Fecha Contratación:", 1, 1)
        
        self.salario_base_entry = self._create_form_field(form_frame, "Salario Base:", 2, 0)
        self.nivel_educativo_entry = self._create_form_field(form_frame, "Nivel Educativo:", 2, 1)
        self.especialidad_entry = self._create_form_field(form_frame, "Especialidad:", 3, 0)
        self.titulo_obtenido_entry = self._create_form_field(form_frame, "Título Obtenido:", 3, 1)
    
    def _create_contacto_tab(self, parent):
        """Crea la pestaña de contacto"""
        form_frame = ctk.CTkFrame(parent, fg_color="#2b2b2b")
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.telefono_entry = self._create_form_field(form_frame, "Teléfono:", 0, 0)
        self.celular_entry = self._create_form_field(form_frame, "Celular:", 0, 1)
        self.email_entry = self._create_form_field(form_frame, "Email:", 1, 0)
        self.direccion_entry = self._create_form_field(form_frame, "Dirección:", 1, 1)
        
        self.ciudad_entry = self._create_form_field(form_frame, "Ciudad:", 2, 0)
        self.estado_entry = self._create_form_field(form_frame, "Estado:", 2, 1)
        self.codigo_postal_entry = self._create_form_field(form_frame, "Código Postal:", 3, 0)
        
        # Contacto de emergencia
        emergency_frame = ctk.CTkFrame(form_frame, fg_color="#3c3c3c")
        emergency_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        emergency_label = ctk.CTkLabel(emergency_frame, text="Contacto de Emergencia", 
                                     font=ctk.CTkFont(weight="bold"))
        emergency_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        self.contacto_emergencia_nombre_entry = self._create_form_field(emergency_frame, "Nombre:", 1, 0)
        self.contacto_emergencia_telefono_entry = self._create_form_field(emergency_frame, "Teléfono:", 1, 1)
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
        from src.utils.helpers import parse_date
        return parse_date(date_str)
    
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
                messagebox.showinfo("Éxito", "Empleado actualizado correctamente")
            else:
                # Verificar que la cédula no exista antes de crear
                if datos.get("cedula"):
                    existing = self.main_window.empleado_service.obtener_empleado_por_cedula(datos["cedula"])
                    if existing:
                        messagebox.showerror("Error", "Ya existe un empleado con esta cédula")
                        return
                
                self.main_window.empleado_service.crear_empleado(datos)
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
        
        self.tree.column("tipo", width=150)
        self.tree.column("titulo", width=250)
        self.tree.column("fecha", width=120)
        self.tree.column("estado", width=100)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)
        
        # Menú contextual
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Ver Documento", command=self._on_view_documento)
        self.context_menu.add_command(label="Descargar", command=self._on_download_documento)
        self.context_menu.add_command(label="Eliminar", command=self._on_delete_documento)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        # Cargar empleados
        self._load_empleados()
    
    def _load_empleados(self):
        """Carga la lista de empleados en el combo"""
        empleados = self.main_window.empleado_service.listar_empleados_activos()
        self.empleado_combo['values'] = [f"{emp.nombre_completo} ({emp.cedula})" for emp in empleados]
        self.empleado_data = {f"{emp.nombre_completo} ({emp.cedula})": emp.id for emp in empleados}
    
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
            self.tree.insert("", "end", values=("", "", "", ""))
            return
        
        try:
            documentos = self.main_window.documento_service.listar_documentos_empleado(self.current_empleado_id)
            
            if not documentos:
                self.tree.insert("", "end", values=("", "No hay documentos", "", ""))
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
        """Obtiene el documento seleccionado"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            doc_id = int(item["tags"][0])
            return self.main_window.documento_service.obtener_documento(doc_id)
        return None
    
    def _on_new_documento(self):
        """Maneja la creación de nuevo documento"""
        if not self.current_empleado_id:
            messagebox.showwarning("Advertencia", "Seleccione un empleado primero")
            return
        
        dialog = DocumentoDialog(self, self.main_window, self.current_empleado_id)
        self.wait_window(dialog)
        if dialog.result:
            self._load_documentos()
    
    def _on_view_documento(self):
        """Muestra el documento seleccionado"""
        documento = self._get_selected_documento()
        if documento:
            contenido = self.main_window.documento_service.obtener_archivo(documento.id)
            if contenido:
                # Aquí se podría abrir el documento con el visor correspondiente
                messagebox.showinfo("Documento", f"Documento: {documento.titulo}\nTamaño: {len(contenido)} bytes")
            else:
                messagebox.showerror("Error", "No se pudo cargar el documento")
    
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
    
    def __init__(self, parent, main_window, empleado_id: int):
        super().__init__(parent)
        self.main_window = main_window
        self.empleado_id = empleado_id
        self.result = False
        self.file_content = None
        
        self.title("Nuevo Documento")
        self.geometry("600x400")
        
        # Hacer que la ventana esté siempre al frente
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        self._create_widgets()
    
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
        """Guarda el documento"""
        try:
            if not self.file_content:
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
            
            # Validar campos requeridos
            if not datos["titulo"]:
                messagebox.showerror("Error", "El título es requerido")
                return
            
            errores = self.main_window.documento_service.validar_datos_documento(datos)
            if errores:
                messagebox.showerror("Errores de Validación", "\n".join(errores))
                return
            
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
        
        self.tree.column("tipo", width=120)
        self.tree.column("fechas", width=150)
        self.tree.column("dias", width=60)
        self.tree.column("estado", width=100)
        self.tree.column("motivo", width=200)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)
        
        # Menú contextual
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Ver Detalles", command=self._on_view_incidencia)
        self.context_menu.add_command(label="Aprobar", command=self._on_approve_incidencia)
        self.context_menu.add_command(label="Rechazar", command=self._on_reject_incidencia)
        self.context_menu.add_command(label="Eliminar", command=self._on_delete_incidencia)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _load_data(self):
        """Carga los datos iniciales"""
        self._load_empleados()
        self._load_incidencias()
    
    def _load_empleados(self):
        """Carga la lista de empleados en el combo"""
        empleados = self.main_window.empleado_service.listar_empleados_activos()
        self.empleado_combo['values'] = [f"{emp.nombre_completo} ({emp.cedula})" for emp in empleados]
        self.empleado_data = {f"{emp.nombre_completo} ({emp.cedula})": emp.id for emp in empleados}
    
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
            self.tree.insert("", "end", values=("", "", "", "", ""))
            return
        
        try:
            incidencias = self.main_window.incidencia_service.listar_incidencias_empleado(self.current_empleado_id)
            
            if not incidencias:
                self.tree.insert("", "end", values=("", "No hay incidencias", "", "", ""))
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
        """Obtiene la incidencia seleccionada"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            incidencia_id = int(item["tags"][0])
            return self.main_window.incidencia_service.obtener_incidencia(incidencia_id)
        return None
    
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
        details = f"""
Tipo: {incidencia.tipo_incidencia}
Estado: {incidencia.estado}
Fecha Solicitud: {format_date(incidencia.fecha_solicitud)}
Periodo: {format_date(incidencia.fecha_inicio)} - {format_date(incidencia.fecha_fin)}
Días Solicitados: {incidencia.dias_solicitados}
Días Aprobados: {incidencia.dias_aprobados or 'N/A'}
Motivo: {incidencia.motivo}
Descripción: {incidencia.descripcion or 'N/A'}
Aprobado Por: {incidencia.aprobado_por or 'N/A'}
Comentarios: {incidencia.comentarios_aprobacion or 'N/A'}
"""
        messagebox.showinfo("Detalles de Incidencia", details)


class IncidenciaDialog(ctk.CTkToplevel):
    """Diálogo para crear/editar incidencia"""
    
    def __init__(self, parent, main_window, empleado_id: int):
        super().__init__(parent)
        self.main_window = main_window
        self.empleado_id = empleado_id
        self.result = False
        self.file_content = None
        
        self.title("Nueva Incidencia")
        self.geometry("600x500")
        
        # Hacer que la ventana esté siempre al frente
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        self._create_widgets()
    
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
        
        # Hacer que la ventana esté siempre al frente
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
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
        
        self.tree.column("empleado", width=200)
        self.tree.column("periodo", width=150)
        self.tree.column("tipo", width=120)
        self.tree.column("bruto", width=100)
        self.tree.column("neto", width=100)
        self.tree.column("estado", width=80)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.tree.yview)
        
        # Menú contextual
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Ver Detalles", command=self._on_view_pago)
        self.context_menu.add_command(label="Generar Recibo", command=self._on_generate_recibo)
        self.context_menu.add_command(label="Marcar Pagado", command=self._on_mark_paid)
        self.context_menu.add_command(label="Eliminar", command=self._on_delete_pago)
        
        self.tree.bind("<Button-3>", self._show_context_menu)
    
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
                self.tree.insert("", "end", values=("", "No hay pagos", "", "", "", ""))
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
        """Obtiene el pago seleccionado"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            pago_id = int(item["tags"][0])
            return self.main_window.pago_service.obtener_pago(pago_id)
        return None
    
    def _on_view_pago(self):
        """Muestra detalles del pago seleccionado"""
        pago = self._get_selected_pago()
        if pago:
            empleado = self.main_window.empleado_service.obtener_empleado(pago.empleado_id)
            nombre_empleado = empleado.nombre_completo if empleado else "Desconocido"
            
            details = f"""
Empleado: {nombre_empleado}
Periodo: {format_date(pago.periodo_inicio)} - {format_date(pago.periodo_fin)}
Tipo: {pago.tipo_pago}
Método: {pago.metodo_pago}

Salario Base: {format_currency(float(pago.salario_base))}
Bonificaciones: {format_currency(float(pago.bonificaciones))}
Horas Extra: {format_currency(float(pago.horas_extra))}
Total Bruto: {format_currency(float(pago.monto_bruto))}

Deducciones:
- Seguro Social: {format_currency(float(pago.deduccion_seguro))}
- Pensión: {format_currency(float(pago.deduccion_pension))}
- Impuesto: {format_currency(float(pago.deduccion_impuesto))}
- Otras: {format_currency(float(pago.otras_deducciones))}
- Descuentos: {format_currency(float(pago.descuentos))}

Total Neto: {format_currency(float(pago.monto_neto))}
Estado: {'Pagado' if pago.pagado else 'Pendiente'}
"""
            messagebox.showinfo("Detalles del Pago", details)
    
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
                        "salario_base": float(pago.salario_base),
                        "bonificaciones": float(pago.bonificaciones),
                        "horas_extra": float(pago.horas_extra),
                        "monto_bruto": float(pago.monto_bruto),
                        "deduccion_seguro": float(pago.deduccion_seguro),
                        "deduccion_pension": float(pago.deduccion_pension),
                        "deduccion_impuesto": float(pago.deduccion_impuesto),
                        "otras_deducciones": float(pago.otras_deducciones),
                        "descuentos": float(pago.descuentos),
                        "monto_neto": float(pago.monto_neto)
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
        from src.utils.helpers import parse_date
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
        
        # Botón de guardar
        save_btn = ctk.CTkButton(self, text="Guardar Cambios", command=self._on_save)
        save_btn.pack(pady=10)
    
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
            # Configuración general
            general_config = self.main_window.config_service.obtener_configuracion_general()
            self.nombre_institucion_entry.delete(0, tk.END)
            self.nombre_institucion_entry.insert(0, general_config.get("nombre_institucion", ""))
            self.ruc_entry.delete(0, tk.END)
            self.ruc_entry.insert(0, general_config.get("ruc", ""))
            self.direccion_entry.delete(0, tk.END)
            self.direccion_entry.insert(0, general_config.get("direccion", ""))
            self.telefono_entry.delete(0, tk.END)
            self.telefono_entry.insert(0, general_config.get("telefono", ""))
            self.email_entry.delete(0, tk.END)
            self.email_entry.insert(0, general_config.get("email", ""))
            
            # Configuración de nómina
            nomina_config = self.main_window.config_service.obtener_configuracion_nomina()
            self.porcentaje_seguro_entry.delete(0, tk.END)
            self.porcentaje_seguro_entry.insert(0, str(nomina_config.get("porcentaje_seguro", "")))
            self.porcentaje_pension_entry.delete(0, tk.END)
            self.porcentaje_pension_entry.insert(0, str(nomina_config.get("porcentaje_pension", "")))
            self.porcentaje_impuesto_entry.delete(0, tk.END)
            self.porcentaje_impuesto_entry.insert(0, str(nomina_config.get("porcentaje_impuesto", "")))
            self.salario_minimo_entry.delete(0, tk.END)
            self.salario_minimo_entry.insert(0, str(nomina_config.get("salario_minimo", "")))
            
            # Configuración de RRHH
            rrhh_config = self.main_window.config_service.obtener_configuracion_recursos_humanos()
            self.dias_vacaciones_entry.delete(0, tk.END)
            self.dias_vacaciones_entry.insert(0, str(rrhh_config.get("dias_vacaciones_anual", "")))
            self.horas_laborales_entry.delete(0, tk.END)
            self.horas_laborales_entry.insert(0, str(rrhh_config.get("horas_laborales_semana", "")))
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar configuración: {str(e)}")
    
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