"""
Main Window
Ventana principal de la aplicación (requiere sesión iniciada)
"""

from typing import Optional

import customtkinter as ctk
from tkinter import messagebox, ttk

from src.config import settings, db_config
from src.models import Usuario
from src.utils.security import PermissionChecker
from src.services.empleado_service import EmpleadoService
from src.services.documento_service import DocumentoService
from src.services.incidencia_service import IncidenciaService
from src.services.pago_service import PagoService
from src.services.configuracion_service import ConfiguracionService
from src.gui.frames import (
    DashboardFrame, EmpleadosFrame, DocumentosFrame,
    IncidenciasFrame, NominaFrame, ConfiguracionFrame,
)

# Módulos del sistema: (nombre interno, título, ícono)
MODULOS = [
    ("dashboard", "Dashboard", "📊"),
    ("empleados", "Empleados", "👥"),
    ("documentos", "Documentos", "📁"),
    ("incidencias", "Incidencias", "📅"),
    ("nomina", "Nómina", "💰"),
    ("configuracion", "Configuración", "⚙️"),
]

TITULOS_VENTANA = {
    "dashboard": "Dashboard",
    "empleados": "Gestión de Empleados",
    "documentos": "Gestión Documental",
    "incidencias": "Incidencias y Permisos",
    "nomina": "Nómina y Pagos",
    "configuracion": "Configuración",
}

FRAME_CLASSES = {
    "dashboard": DashboardFrame,
    "empleados": EmpleadosFrame,
    "documentos": DocumentosFrame,
    "incidencias": IncidenciasFrame,
    "nomina": NominaFrame,
    "configuracion": ConfiguracionFrame,
}

ROL_LABELS = {
    "admin": "Administrador",
    "manager": "Gestor",
    "user": "Usuario",
    "viewer": "Solo lectura",
}


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
        style.configure("Vertical.TScrollbar",
                        background="#3c3c3c",
                        troughcolor="#2b2b2b",
                        bordercolor="#2b2b2b",
                        arrowcolor="white")
    except Exception:
        pass


class MainWindow(ctk.CTk):
    """Ventana principal del sistema"""

    def __init__(self, current_user: Optional[Usuario] = None):
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        super().__init__()
        configure_treeview_style()

        self.current_user = current_user
        self._exit_status = "exit"

        self.title(settings.app_name)
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.configure(fg_color="#1a1a1a")

        # Confirmar salida antes de cerrar
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

        self._init_database()

        # Servicios con una sesión dedicada a la ventana
        self.session = db_config.get_session()
        self.empleado_service = EmpleadoService(self.session)
        self.documento_service = DocumentoService(self.session)
        self.incidencia_service = IncidenciaService(self.session)
        self.pago_service = PagoService(self.session)
        self.config_service = ConfiguracionService(self.session)

        # Estado de la interfaz
        self.current_frame = None
        self.sidebar_buttons = {}

        self._create_ui()

        self.update()
        self._show_frame("dashboard")

    # ------------------------------------------------------------------
    # Permisos del usuario actual
    # ------------------------------------------------------------------
    def tiene_permiso(self, permiso: str) -> bool:
        """¿El usuario actual puede ejecutar una acción (create/update/...)?"""
        if self.current_user is None:
            return True
        return PermissionChecker.has_permission(self.current_user.rol_valor, permiso)

    def puede_ver_modulo(self, modulo: str) -> bool:
        """¿El usuario actual puede acceder a un módulo?"""
        if modulo == "dashboard":
            return True
        if self.current_user is None:
            return True
        return PermissionChecker.can_access_module(self.current_user.rol_valor, modulo)

    def rol_label(self) -> str:
        if self.current_user is None:
            return ""
        return ROL_LABELS.get(self.current_user.rol_valor, self.current_user.rol_valor)

    # ------------------------------------------------------------------
    # Base de datos
    # ------------------------------------------------------------------
    def _init_database(self):
        try:
            db_config.init_db()
        except Exception as e:
            messagebox.showerror(
                "Error de Base de Datos",
                f"No se pudo inicializar la base de datos: {str(e)}",
            )
            self.destroy()
            raise

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _create_ui(self):
        self._create_sidebar()
        self._create_main_area()
        self._create_status_bar()

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#2b2b2b")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        title_label = ctk.CTkLabel(
            self.sidebar,
            text="SISTEMA DE GESTIÓN\nDE PERSONAL",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white",
        )
        title_label.pack(pady=(20, 25), padx=20)

        # Solo los módulos permitidos para el rol del usuario
        for frame_name, titulo, icono in MODULOS:
            if not self.puede_ver_modulo(frame_name):
                continue

            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icono} {titulo}",
                font=ctk.CTkFont(size=14),
                height=46,
                anchor="w",
                command=lambda fn=frame_name: self._show_frame(fn),
            )
            btn.pack(pady=4, padx=10, fill="x")
            self.sidebar_buttons[frame_name] = btn

        separator = ctk.CTkFrame(self.sidebar, height=2)
        separator.pack(pady=15, padx=10, fill="x")

        # Información de la institución
        institution_name = "Institución Educativa"
        try:
            config = self.config_service.obtener_configuracion_general()
            institution_name = config.get("nombre_institucion") or institution_name
        except Exception:
            pass

        institution_label = ctk.CTkLabel(
            self.sidebar,
            text=str(institution_name),
            font=ctk.CTkFont(size=11),
            wraplength=230,
            text_color="#cccccc",
        )
        institution_label.pack(pady=5, padx=10)

        # Usuario y rol en sesión
        if self.current_user is not None:
            user_label = ctk.CTkLabel(
                self.sidebar,
                text=f"{self.current_user.username} · {self.rol_label()}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#8ab4f8",
            )
            user_label.pack(pady=(4, 0), padx=10)

        version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{settings.app_version}",
            font=ctk.CTkFont(size=10),
            text_color="#888888",
        )
        version_label.pack(side="bottom", pady=10)

    def _create_main_area(self):
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="#1a1a1a")
        self.main_container.pack(side="right", fill="both", expand=True)

        self.header = ctk.CTkFrame(self.main_container, height=60, fg_color="#2b2b2b")
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)

        self.frame_title = ctk.CTkLabel(
            self.header,
            text="Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        )
        self.frame_title.pack(side="left", padx=20, pady=15)

        # Cerrar sesión
        logout_btn = ctk.CTkButton(
            self.header,
            text="Cerrar Sesión",
            width=120,
            height=35,
            fg_color="#3c3c3c",
            hover_color="#4c4c4c",
            command=self._on_logout,
        )
        logout_btn.pack(side="right", padx=(5, 10), pady=12)

        # Salir de la aplicación
        exit_btn = ctk.CTkButton(
            self.header,
            text="Salir",
            width=80,
            height=35,
            command=self._on_exit,
        )
        exit_btn.pack(side="right", padx=5, pady=12)

        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="#1a1a1a")
        self.content_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

    def _create_status_bar(self):
        from datetime import datetime

        self.status_bar = ctk.CTkFrame(self.main_container, height=30, fg_color="#2b2b2b")
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Sistema listo",
            font=ctk.CTkFont(size=10),
            anchor="w",
            text_color="#cccccc",
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        self.datetime_label = ctk.CTkLabel(
            self.status_bar,
            text=datetime.now().strftime("%Y-%m-%d %H:%M"),
            font=ctk.CTkFont(size=10),
            text_color="#cccccc",
        )
        self.datetime_label.pack(side="right", padx=10, pady=5)
        self._update_clock()

    def _update_clock(self):
        try:
            from datetime import datetime
            if hasattr(self, 'datetime_label') and self.datetime_label.winfo_exists():
                self.datetime_label.configure(
                    text=datetime.now().strftime("%Y-%m-%d %H:%M"))
                self.after(30000, self._update_clock)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def show_frame(self, frame_name: str, **kwargs):
        """Muestra un frame y aplica parámetros de selección si el frame lo soporta"""
        self._show_frame(frame_name)
        if kwargs and self.current_frame is not None:
            for key, value in kwargs.items():
                metodo = getattr(self.current_frame, key, None)
                if callable(metodo):
                    try:
                        metodo(value)
                    except Exception as e:
                        print(f"Error aplicando parámetro '{key}' al frame: {e}")

    def _show_frame(self, frame_name: str):
        try:
            if not self.puede_ver_modulo(frame_name):
                messagebox.showwarning(
                    "Acceso denegado",
                    "Su rol no tiene permisos para acceder a este módulo",
                )
                return

            # Destruir el frame actual
            if self.current_frame is not None:
                try:
                    self.current_frame.destroy()
                except Exception:
                    pass

            self.frame_title.configure(
                text=TITULOS_VENTANA.get(frame_name, frame_name))

            frame_class = FRAME_CLASSES.get(frame_name)
            if frame_class is not None:
                self.current_frame = frame_class(self.content_frame, self)
                self.current_frame.pack(fill="both", expand=True)
            else:
                self.current_frame = ctk.CTkFrame(self.content_frame)
                self.current_frame.pack(fill="both", expand=True)
                ctk.CTkLabel(
                    self.current_frame,
                    text=f"Módulo {frame_name} en desarrollo",
                    font=ctk.CTkFont(size=16),
                ).pack(expand=True)

            self.status_label.configure(
                text=f"Mostrando: {TITULOS_VENTANA.get(frame_name, frame_name)}")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al cargar el módulo {frame_name}: {str(e)}")
            self.current_frame = ctk.CTkFrame(self.content_frame)
            self.current_frame.pack(fill="both", expand=True)
            ctk.CTkLabel(
                self.current_frame,
                text=f"Error al cargar: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="red",
            ).pack(expand=True)

    # ------------------------------------------------------------------
    # Sesión
    # ------------------------------------------------------------------
    def _on_logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Desea cerrar la sesión actual?"):
            self._cleanup()
            self._exit_status = "logout"
            self.destroy()

    def _on_exit(self):
        if messagebox.askyesno("Salir", "¿Desea salir de la aplicación?"):
            self._cleanup()
            self._exit_status = "exit"
            self.destroy()

    def _cleanup(self):
        try:
            if self.session is not None:
                db_config.close_session(self.session)
                self.session = None
        except Exception:
            pass

    def run(self) -> str:
        """Ejecuta la ventana y devuelve 'logout' o 'exit' al cerrarse"""
        self.mainloop()
        return self._exit_status
