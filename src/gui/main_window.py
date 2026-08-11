"""
Main Window
Ventana principal de la aplicación
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from typing import Optional

# Configurar estilo para Treeview en modo oscuro
style = ttk.Style()
style.theme_use('clam')
style.configure("Treeview",
                background="#2b2b2b",
                foreground="white",
                fieldbackground="#2b2b2b",
                rowheight=25)
style.configure("Treeview.Heading",
                background="#3c3c3c",
                foreground="white",
                relief="flat")
style.map("Treeview",
          background=[('selected', '#1f538d')])

from src.config import settings, db_config
from src.services import EmpleadoService, DocumentoService, IncidenciaService, PagoService, ConfiguracionService


class MainWindow(ctk.CTk):
    """Ventana principal del sistema"""
    
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana
        self.title(settings.app_name)
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Configurar tema
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Inicializar base de datos
        self._init_database()
        
        # Inicializar servicios
        self.session = db_config.get_session()
        self.empleado_service = EmpleadoService(self.session)
        self.documento_service = DocumentoService(self.session)
        self.incidencia_service = IncidenciaService(self.session)
        self.pago_service = PagoService(self.session)
        self.config_service = ConfiguracionService(self.session)
        
        # Variables de UI
        self.current_frame = None
        self.sidebar_buttons = {}
        
        # Crear interfaz
        self._create_ui()
        
        # Cargar frame inicial
        self._show_frame("dashboard")
    
    def _init_database(self):
        """Inicializa la base de datos"""
        try:
            db_config.init_db()
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", 
                               f"No se pudo inicializar la base de datos: {str(e)}")
    
    def _create_ui(self):
        """Crea la interfaz de usuario"""
        # Crear sidebar
        self._create_sidebar()
        
        # Crear área principal
        self._create_main_area()
        
        # Crear barra de estado
        self._create_status_bar()
    
    def _create_sidebar(self):
        """Crea la barra lateral de navegación"""
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo/Título
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="SISTEMA DE GESTIÓN\nDE PERSONAL",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(20, 30), padx=20)
        
        # Botones de navegación
        buttons = [
            ("Dashboard", "dashboard", "📊"),
            ("Empleados", "empleados", "👥"),
            ("Documentos", "documentos", "📁"),
            ("Incidencias", "incidencias", "📅"),
            ("Nómina", "nomina", "💰"),
            ("Configuración", "configuracion", "⚙️"),
        ]
        
        for text, frame_name, icon in buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon} {text}",
                font=ctk.CTkFont(size=14),
                height=50,
                anchor="w",
                command=lambda f=frame_name: self._show_frame(f)
            )
            btn.pack(pady=5, padx=10, fill="x")
            self.sidebar_buttons[frame_name] = btn
        
        # Separador
        separator = ctk.CTkFrame(self.sidebar, height=2)
        separator.pack(pady=20, padx=10, fill="x")
        
        # Información de la institución
        config = self.config_service.obtener_configuracion_general()
        institution_name = config.get("nombre_institucion", "Institución Educativa")
        
        institution_label = ctk.CTkLabel(
            self.sidebar,
            text=institution_name,
            font=ctk.CTkFont(size=11),
            wraplength=230
        )
        institution_label.pack(pady=10, padx=10)
        
        # Versión
        version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{settings.app_version}",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        version_label.pack(side="bottom", pady=10)
    
    def _create_main_area(self):
        """Crea el área principal de contenido"""
        self.main_container = ctk.CTkFrame(self, corner_radius=0)
        self.main_container.pack(side="right", fill="both", expand=True)
        
        # Header
        self.header = ctk.CTkFrame(self.main_container, height=60)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)
        
        # Título del frame actual
        self.frame_title = ctk.CTkLabel(
            self.header,
            text="Dashboard",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.frame_title.pack(side="left", padx=20, pady=15)
        
        # Botón de salir
        exit_btn = ctk.CTkButton(
            self.header,
            text="Salir",
            width=80,
            height=35,
            command=self._on_exit
        )
        exit_btn.pack(side="right", padx=20, pady=12)
        
        # Contenedor de frames
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)
    
    def _create_status_bar(self):
        """Crea la barra de estado"""
        self.status_bar = ctk.CTkFrame(self.main_container, height=30)
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.pack_propagate(False)
        
        # Etiqueta de estado
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Sistema listo",
            font=ctk.CTkFont(size=10),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Fecha y hora
        from datetime import datetime
        datetime_label = ctk.CTkLabel(
            self.status_bar,
            text=datetime.now().strftime("%Y-%m-%d %H:%M"),
            font=ctk.CTkFont(size=10)
        )
        datetime_label.pack(side="right", padx=10, pady=5)
    
    def _show_frame(self, frame_name: str):
        """Muestra un frame específico"""
        # Eliminar frame actual si existe
        if self.current_frame:
            self.current_frame.destroy()
        
        # Actualizar título
        titles = {
            "dashboard": "Dashboard",
            "empleados": "Gestión de Empleados",
            "documentos": "Gestión Documental",
            "incidencias": "Incidencias y Permisos",
            "nomina": "Nómina y Pagos",
            "configuracion": "Configuración"
        }
        self.frame_title.configure(text=titles.get(frame_name, frame_name))
        
        # Crear nuevo frame
        frame_mapping = {
            "dashboard": frames.Dashboard,
            "empleados": frames.Empleados,
            "documentos": frames.Documentos,
            "incidencias": frames.Incidencias,
            "nomina": frames.Nomina,
            "configuracion": frames.Configuracion
        }
        
        frame_class = frame_mapping.get(frame_name)
        
        if frame_class:
            self.current_frame = frame_class(self.content_frame, self)
            self.current_frame.pack(fill="both", expand=True)
        else:
            # Frame por defecto si no existe
            self.current_frame = ctk.CTkFrame(self.content_frame)
            self.current_frame.pack(fill="both", expand=True)
            
            label = ctk.CTkLabel(
                self.current_frame,
                text=f"Módulo {frame_name} en desarrollo",
                font=ctk.CTkFont(size=16)
            )
            label.pack(expand=True)
        
        # Actualizar estado
        self.status_label.configure(text=f"Mostrando: {titles.get(frame_name, frame_name)}")
    
    def _on_exit(self):
        """Maneja el cierre de la aplicación"""
        if messagebox.askyesno("Salir", "¿Desea salir de la aplicación?"):
            self._cleanup()
            self.destroy()
    
    def _cleanup(self):
        """Limpia recursos antes de cerrar"""
        try:
            if self.session:
                db_config.close_session(self.session)
        except Exception:
            pass
    
    def run(self):
        """Ejecuta la aplicación"""
        self.mainloop()


# Import de frames
from src.gui.frames import (
    DashboardFrame, EmpleadosFrame, DocumentosFrame, 
    IncidenciasFrame, NominaFrame, ConfiguracionFrame
)

class frames:
    """Contenedor de frames de la aplicación"""
    Dashboard = DashboardFrame
    Empleados = EmpleadosFrame
    Documentos = DocumentosFrame
    Incidencias = IncidenciasFrame
    Nomina = NominaFrame
    Configuracion = ConfiguracionFrame