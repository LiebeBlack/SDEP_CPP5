"""
Main Window
Ventana principal de la aplicación
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from typing import Optional

# Configurar estilo para Treeview en modo oscuro
def configure_treeview_style():
    """Configura el estilo de Treeview para modo oscuro"""
    try:
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        fieldbackground="#2b2b2b",
                        rowheight=28,
                        borderwidth=0,
                        font=('Arial', 10))
        style.configure("Treeview.Heading",
                        background="#3c3c3c",
                        foreground="white",
                        relief="flat",
                        borderwidth=0,
                        font=('Arial', 10, 'bold'))
        style.map("Treeview",
                  background=[('selected', '#1f538d')],
                  foreground=[('selected', 'white')])
        style.map("Treeview.Heading",
                  background=[('active', '#4c4c4c')])
        # Configurar scrollbar
        style.configure("Vertical.TScrollbar",
                        background="#3c3c3c",
                        troughcolor="#2b2b2b",
                        bordercolor="#2b2b2b",
                        arrowcolor="white")
    except Exception:
        pass  # Continuar si falla la configuración de estilo

from src.config import settings, db_config
from src.services.empleado_service import EmpleadoService
from src.services.documento_service import DocumentoService
from src.services.incidencia_service import IncidenciaService
from src.services.pago_service import PagoService
from src.services.configuracion_service import ConfiguracionService


class MainWindow(ctk.CTk):
    """Ventana principal del sistema"""
    
    def __init__(self):
        # Configurar tema primero
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        super().__init__()
        
        # Configurar estilos después de inicializar la ventana
        configure_treeview_style()
        
        # Configuración de la ventana
        self.title(settings.app_name)
        self.geometry("1200x800")
        self.minsize(1000, 700)
        
        # Configurar colores de fondo
        self.configure(fg_color="#1a1a1a")
        
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
        
        # Cargar frame inicial después de actualizar la ventana
        self.update()
        self._show_frame("dashboard")
    
    def _init_database(self):
        """Inicializa la base de datos"""
        try:
            db_config.init_db()
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", 
                               f"No se pudo inicializar la base de datos: {str(e)}")
            self.destroy()
            raise
    
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
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#2b2b2b")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo/Título
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="SISTEMA DE GESTIÓN\nDE PERSONAL",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
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
            # Usar función wrapper para evitar problema de lambda en loop
            def make_command(fn):
                return lambda: self._show_frame(fn)
            
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon} {text}",
                font=ctk.CTkFont(size=14),
                height=50,
                anchor="w",
                command=make_command(frame_name)
            )
            btn.pack(pady=5, padx=10, fill="x")
            self.sidebar_buttons[frame_name] = btn
        
        # Separador
        separator = ctk.CTkFrame(self.sidebar, height=2)
        separator.pack(pady=20, padx=10, fill="x")
        
        # Información de la institución
        try:
            config = self.config_service.obtener_configuracion_general()
            institution_name = config.get("nombre_institucion") if config else None
        except Exception:
            institution_name = None
            
        if not institution_name:
            institution_name = "Institución Educativa"
        
        institution_label = ctk.CTkLabel(
            self.sidebar,
            text=str(institution_name),
            font=ctk.CTkFont(size=11),
            wraplength=230,
            text_color="#cccccc"
        )
        institution_label.pack(pady=10, padx=10)
        
        # Versión
        version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{settings.app_version}",
            font=ctk.CTkFont(size=10),
            text_color="#888888"
        )
        version_label.pack(side="bottom", pady=10)
    
    def _create_main_area(self):
        """Crea el área principal de contenido"""
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        self.main_container.pack(side="right", fill="both", expand=True)
        
        # Header
        self.header = ctk.CTkFrame(self.main_container, height=60, fg_color="#2b2b2b")
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)
        
        # Título del frame actual
        self.frame_title = ctk.CTkLabel(
            self.header,
            text="Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
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
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="#1a1a1a")
        self.content_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)
    
    def _create_status_bar(self):
        """Crea la barra de estado"""
        self.status_bar = ctk.CTkFrame(self.main_container, height=30, fg_color="#2b2b2b")
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.pack_propagate(False)
        
        # Etiqueta de estado
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Sistema listo",
            font=ctk.CTkFont(size=10),
            anchor="w",
            text_color="#cccccc"
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Fecha y hora
        from datetime import datetime
        self.datetime_label = ctk.CTkLabel(
            self.status_bar,
            text=datetime.now().strftime("%Y-%m-%d %H:%M"),
            font=ctk.CTkFont(size=10),
            text_color="#cccccc"
        )
        self.datetime_label.pack(side="right", padx=10, pady=5)
        self._update_clock()
    
    def _update_clock(self):
        """Actualiza el reloj de la barra de estado periódicamente"""
        try:
            from datetime import datetime
            if hasattr(self, 'datetime_label') and self.datetime_label.winfo_exists():
                self.datetime_label.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M"))
                self.after(30000, self._update_clock)
        except Exception:
            pass
    
    def show_frame(self, frame_name: str, **kwargs):
        """Muestra un frame específico y opcionalmente pasa parámetros"""
        self._show_frame(frame_name)
        if kwargs and self.current_frame:
            for k, v in kwargs.items():
                if hasattr(self.current_frame, k):
                    try:
                        getattr(self.current_frame, k)(v)
                    except Exception:
                        pass
    
    def _show_frame(self, frame_name: str):
        """Muestra un frame específico"""
        try:
            # Eliminar frame actual si existe
            if self.current_frame:
                try:
                    self.current_frame.destroy()
                except Exception:
                    pass
            
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
                "dashboard": frames.DashboardFrame,
                "empleados": frames.EmpleadosFrame,
                "documentos": frames.DocumentosFrame,
                "incidencias": frames.IncidenciasFrame,
                "nomina": frames.NominaFrame,
                "configuracion": frames.ConfiguracionFrame
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
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el módulo {frame_name}: {str(e)}")
            # Crear frame de error
            self.current_frame = ctk.CTkFrame(self.content_frame)
            self.current_frame.pack(fill="both", expand=True)
            
            error_label = ctk.CTkLabel(
                self.current_frame,
                text=f"Error al cargar: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="red"
            )
            error_label.pack(expand=True)
    
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


# Import de frames al final para evitar dependencias circulares
def _get_frames():
    """Retorna las clases de frames de forma diferida"""
    from src.gui.frames import (
        DashboardFrame, EmpleadosFrame, DocumentosFrame, 
        IncidenciasFrame, NominaFrame, ConfiguracionFrame
    )
    
    class FramesContainer:
        """Contenedor de frames de la aplicación"""
        Dashboard = DashboardFrame
        Empleados = EmpleadosFrame
        Documentos = DocumentosFrame
        Incidencias = IncidenciasFrame
        Nomina = NominaFrame
        Configuracion = ConfiguracionFrame
    
    return FramesContainer


# Instancia diferida de frames
frames = _get_frames()