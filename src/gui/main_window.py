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
from src.gui.theme import (
    setup_ui_raiz,
    enable_windows_dpi_awareness,
    aplicar_modo_apariencia,
    COLORES,
)
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
    """
    Configura el estilo oscuro de la UI (compatibilidad)

    Delega en src.gui.theme para que Treeview, Combobox y sus menús
    desplegables compartan el mismo tema.
    """
    from src.gui.theme import configure_ttk_styles
    configure_ttk_styles()


class MainWindow(ctk.CTk):
    """Ventana principal del sistema"""

    def __init__(self, current_user: Optional[Usuario] = None):
        enable_windows_dpi_awareness()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        super().__init__()
        setup_ui_raiz(self)

        self._exit_status = "exit"

        self.title(settings.app_name)
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.configure(fg_color=COLORES["fondo"])

        # Confirmar salida antes de cerrar
        self.protocol("WM_DELETE_WINDOW", self._on_exit)

        # Copiar el nombre de usuario MIENTRAS el objeto sigue ligado a la
        # sesión de login; cualquier cierre de sesión scoped posterior lo
        # dejaría detached (incluso para atributos de clave primaria).
        username_snapshot = None
        if current_user is not None:
            try:
                username_snapshot = current_user.username
            except Exception:
                username_snapshot = None

        self._init_database()

        # Sesión propia y no scoped para toda la ventana: las operaciones
        # internas que usan get_session/close_session (registry) no la
        # cierran ni invalidan sus objetos cargados.
        self.session = db_config.new_session()
        self.empleado_service = EmpleadoService(self.session)
        self.documento_service = DocumentoService(self.session)
        self.incidencia_service = IncidenciaService(self.session)
        self.pago_service = PagoService(self.session)
        self.config_service = ConfiguracionService(self.session)

        # Cargar el usuario autenticado en la sesión dedicada
        self.current_user = None
        if username_snapshot:
            self.current_user = self.session.query(Usuario).filter(
                Usuario.username == username_snapshot).first()

        # Estado de la interfaz
        self.current_frame = None
        self.current_frame_name = "dashboard"
        self.sidebar_buttons = {}

        # Aplicar el modo de apariencia guardado antes de crear la interfaz
        try:
            modo = self.config_service.obtener_valor("apariencia_modo", "Dark") or "Dark"
            aplicar_modo_apariencia(modo)
        except Exception:
            aplicar_modo_apariencia("Dark")

        self._create_ui()

        self.update()
        self._show_frame("dashboard")
        self._programar_respaldo_periodico()

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
        self._bind_atajos()

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=250, corner_radius=0, fg_color=COLORES["panel"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.sidebar,
            text="SISTEMA DE GESTIÓN\nDE PERSONAL",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORES["texto"],
        )
        self.title_label.pack(pady=(20, 25), padx=20)

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

        self.institution_label = ctk.CTkLabel(
            self.sidebar,
            text=str(institution_name),
            font=ctk.CTkFont(size=11),
            wraplength=230,
            text_color=COLORES["texto_suave"],
        )
        self.institution_label.pack(pady=5, padx=10)

        # Usuario y rol en sesión
        if self.current_user is not None:
            self.user_label = ctk.CTkLabel(
                self.sidebar,
                text=f"{self.current_user.username} · {self.rol_label()}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COLORES["texto_suave"],
            )
            self.user_label.pack(pady=(4, 0), padx=10)

        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{settings.app_version}",
            font=ctk.CTkFont(size=10),
            text_color=COLORES["texto_suave"],
        )
        self.version_label.pack(side="bottom", pady=10)

    def _create_main_area(self):
        self.main_container = ctk.CTkFrame(
            self, corner_radius=0, fg_color=COLORES["fondo"])
        self.main_container.pack(side="right", fill="both", expand=True)

        self.header = ctk.CTkFrame(
            self.main_container, height=60, fg_color=COLORES["panel"])
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)

        self.frame_title = ctk.CTkLabel(
            self.header,
            text="Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORES["texto"],
        )
        self.frame_title.pack(side="left", padx=20, pady=15)

        # Alternar modo de apariencia (oscuro/claro), preferencia persistente
        self.apariencia_btn = ctk.CTkButton(
            self.header,
            text="☀️ Claro" if ctk.get_appearance_mode() == "Dark" else "🌙 Oscuro",
            width=110,
            height=35,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._toggle_apariencia,
        )
        self.apariencia_btn.pack(side="right", padx=5, pady=12)

        # Ayuda (guía rápida de uso y atajos)
        ayuda_btn = ctk.CTkButton(
            self.header,
            text="Ayuda",
            width=90,
            height=35,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._on_ayuda,
        )
        ayuda_btn.pack(side="right", padx=5, pady=12)

        # Acerca de (información de la aplicación)
        about_btn = ctk.CTkButton(
            self.header,
            text="Acerca de",
            width=100,
            height=35,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._on_acerca_de,
        )
        about_btn.pack(side="right", padx=5, pady=12)

        # Cerrar sesión
        logout_btn = ctk.CTkButton(
            self.header,
            text="Cerrar Sesión",
            width=120,
            height=35,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
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

        self.content_frame = ctk.CTkFrame(
            self.main_container, fg_color=COLORES["fondo"])
        self.content_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

    def _create_status_bar(self):
        from datetime import datetime

        self.status_bar = ctk.CTkFrame(
            self.main_container, height=30, fg_color=COLORES["panel"])
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Sistema listo",
            font=ctk.CTkFont(size=10),
            anchor="w",
            text_color=COLORES["texto_suave"],
        )
        self.status_label.pack(side="left", padx=10, pady=5)

        self.datetime_label = ctk.CTkLabel(
            self.status_bar,
            text=datetime.now().strftime("%Y-%m-%d %H:%M"),
            font=ctk.CTkFont(size=10),
            text_color=COLORES["texto_suave"],
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
    # Atajos de teclado
    # ------------------------------------------------------------------
    # Método canónico de "actualizar" por tipo de frame
    METODOS_REFRESCAR = {
        "DashboardFrame": "_load_data",
        "EmpleadosFrame": "_load_empleados",
        "DocumentosFrame": "_load_documentos",
        "IncidenciasFrame": "_load_data",
        "NominaFrame": "_load_pagos",
        "ConfiguracionFrame": "_load_configuracion",
    }

    # Método canónico de "nuevo registro" por tipo de frame
    METODOS_NUEVO = {
        "EmpleadosFrame": "_on_new_empleado",
        "DocumentosFrame": "_on_new_documento",
        "IncidenciasFrame": "_on_new_incidencia",
        "NominaFrame": "_on_new_pago",
        "ConfiguracionFrame": "_on_new_usuario",
    }

    # Método canónico de "guardar" por tipo de frame
    METODOS_GUARDAR = {
        "ConfiguracionFrame": "_on_save",
    }

    def _bind_atajos(self):
        """
        Vincula los atajos de teclado documentados en la guía de usuario.

        Los eventos se enlazan en la ventana principal, por lo que también
        se reciben cuando el foco está en cualquier control hijo; los
        diálogos modales (que capturan el foco con grab) conservan sus
        propias acciones y su cierre con Esc.
        """
        self.bind("<F5>", lambda e: self._atajo_refrescar())
        self.bind("<Control-n>", lambda e: self._atajo_nuevo())
        self.bind("<Control-f>", lambda e: self._enfocar_busqueda())
        self.bind("<Control-s>", lambda e: self._atajo_guardar())
        self.bind("<Escape>", lambda e: self._atajo_escape())
        # Navegación directa a cada módulo con Ctrl+1..6
        for indice, (frame_name, _titulo, _icono) in enumerate(MODULOS):
            self.bind(
                f"<Control-{indice + 1}>",
                lambda e, fn=frame_name: self._show_frame(fn),
            )

    def _ejecutar_metodo_frame(self, *nombres: str) -> bool:
        """
        Ejecuta el primer método existente del frame actual.

        Returns:
            True si se encontró y ejecutó un método
        """
        frame = self.current_frame
        if frame is None:
            return False
        for nombre in nombres:
            metodo = getattr(frame, nombre, None)
            if callable(metodo):
                try:
                    metodo()
                except Exception as e:
                    self.status_label.configure(text=f"Error en atajo: {e}")
                return True
        return False

    def _atajo_refrescar(self):
        """F5: recarga los datos del módulo activo"""
        nombre_clase = type(self.current_frame).__name__ if self.current_frame else ""
        metodo = self.METODOS_REFRESCAR.get(nombre_clase)
        if metodo and self._ejecutar_metodo_frame(metodo):
            self.status_label.configure(text="Lista actualizada (F5)")

    def _atajo_nuevo(self):
        """Ctrl+N: abre el diálogo de nuevo registro del módulo activo"""
        nombre_clase = type(self.current_frame).__name__ if self.current_frame else ""
        metodo = self.METODOS_NUEVO.get(nombre_clase)
        if metodo:
            self._ejecutar_metodo_frame(metodo)
        elif self.current_frame is not None:
            self.status_label.configure(
                text="Ctrl+N no aplica en este módulo (use Ayuda para más detalles)")

    def _atajo_guardar(self):
        """Ctrl+S: guarda los cambios del módulo activo (si lo soporta)"""
        nombre_clase = type(self.current_frame).__name__ if self.current_frame else ""
        metodo = self.METODOS_GUARDAR.get(nombre_clase)
        if metodo:
            self._ejecutar_metodo_frame(metodo)
        elif self.current_frame is not None:
            self.status_label.configure(
                text="Ctrl+S solo aplica en el módulo de Configuración")

    def _enfocar_busqueda(self):
        """Ctrl+F: enfoca el campo de búsqueda o filtro del módulo activo"""
        frame = self.current_frame
        if frame is None:
            return
        entrada = getattr(frame, "search_entry", None)
        if entrada is not None and entrada.winfo_exists():
            entrada.focus_set()
            self.status_label.configure(text="Búsqueda (Ctrl+F)")
            return
        # Sin campo de búsqueda propio: enfocar el primer selector (combobox)
        for hijo in frame.winfo_children():
            if isinstance(hijo, ttk.Combobox):
                hijo.focus_set()
                self.status_label.configure(text="Filtro (Ctrl+F)")
                return

    def _atajo_escape(self):
        """Esc en la ventana principal: limpia la selección de la tabla activa"""
        frame = self.current_frame
        if frame is None:
            return
        for attr in ("tree", "backup_tree", "usuarios_tree", "audit_tree"):
            arbol = getattr(frame, attr, None)
            if arbol is None:
                continue
            try:
                if arbol.selection():
                    arbol.selection_remove(arbol.selection())
                    self.status_label.configure(text="Selección eliminada (Esc)")
                    return
            except Exception:
                pass
        self.status_label.configure(
            text="Esc cierra los cuadros de diálogo abiertos")

    def _on_ayuda(self):
        """Muestra la guía rápida de uso y atajos de teclado"""
        from src.gui.frames import InfoDialog
        texto = (
            "GUÍA RÁPIDA\n"
            "===========\n\n"
            "Módulos del sistema (barra lateral o Ctrl+1 a Ctrl+6):\n"
            "  Ctrl+1  Dashboard      Ctrl+2  Empleados\n"
            "  Ctrl+3  Documentos     Ctrl+4  Incidencias\n"
            "  Ctrl+5  Nómina         Ctrl+6  Configuración\n\n"
            "Atajos generales:\n"
            "  Ctrl+N   Nuevo registro en el módulo activo\n"
            "  Ctrl+F   Buscar / enfocar filtro\n"
            "  Ctrl+S   Guardar cambios (módulo de configuración)\n"
            "  F5       Actualizar la lista del módulo activo\n"
            "  Esc      Cerrar diálogos o limpiar la selección\n\n"
            "Consejos:\n"
            "- Doble clic sobre una fila abre sus detalles.\n"
            "- Clic derecho muestra las acciones disponibles.\n"
            "- Los reportes PDF y exportaciones se guardan donde usted elija.\n"
            "- La sección 'Seguridad y Respaldo' permite crear, verificar,\n"
            "  restaurar y eliminar copias de seguridad de la base de datos.\n"
        )
        InfoDialog(self, "Ayuda - Guía Rápida", texto)

    def _on_acerca_de(self):
        """Muestra la información de la aplicación"""
        from src.gui.frames import InfoDialog
        texto = (
            "ACERCA DE\n"
            "=========\n\n"
            f"Sistema: {settings.app_name}\n"
            f"Versión: v{settings.app_version}\n\n"
            "Sistema de gestión de personal y nómina para instituciones\n"
            "educativas. Desarrollado en Python con CustomTkinter y\n"
            "SQLAlchemy (SQLite).\n\n"
            "Roles del sistema:\n"
            "  - Administrador: acceso total (configuración, usuarios,\n"
            "    respaldos y auditoría).\n"
            "  - Gestor: gestiona empleados, documentos, incidencias y\n"
            "    nómina.\n"
            "  - Usuario: consulta y gestión básica de personal.\n"
            "  - Solo lectura: consulta de empleados y documentos.\n\n"
            "Los datos se almacenan localmente (sin conexión a internet).\n"
            "Las contraseñas se guardan con hash seguro (PBKDF2).\n"
        )
        InfoDialog(self, "Acerca de", texto)

    # ------------------------------------------------------------------
    # Modo de apariencia (oscuro / claro)
    # ------------------------------------------------------------------
    def _toggle_apariencia(self):
        """Alterna entre tema oscuro y claro y guarda la preferencia"""
        try:
            modo_actual = ctk.get_appearance_mode()
            nuevo = "Light" if modo_actual == "Dark" else "Dark"
            aplicar_modo_apariencia(nuevo)
            self.config_service.establecer_valor("apariencia_modo", nuevo)
            self._recolorear_chrome()
            # Recrear el frame activo para que tome la paleta nueva
            self._show_frame(self.current_frame_name or "dashboard")
            self.apariencia_btn.configure(
                text="☀️ Claro" if nuevo == "Dark" else "🌙 Oscuro")
            self.status_label.configure(
                text=f"Tema {nuevo.lower()} aplicado")
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo cambiar el tema: {str(e)}")

    def _recolorear_chrome(self):
        """Reaplica la paleta a la barra lateral, cabecera y barra de estado"""
        try:
            self.configure(fg_color=COLORES["fondo"])
            self.sidebar.configure(fg_color=COLORES["panel"])
            self.title_label.configure(text_color=COLORES["texto"])
            self.institution_label.configure(text_color=COLORES["texto_suave"])
            if getattr(self, "user_label", None) is not None:
                self.user_label.configure(text_color=COLORES["texto_suave"])
            self.version_label.configure(text_color=COLORES["texto_suave"])
            self.main_container.configure(fg_color=COLORES["fondo"])
            self.header.configure(fg_color=COLORES["panel"])
            self.frame_title.configure(text_color=COLORES["texto"])
            self.status_bar.configure(fg_color=COLORES["panel"])
            self.status_label.configure(text_color=COLORES["texto_suave"])
            self.datetime_label.configure(text_color=COLORES["texto_suave"])
            self.content_frame.configure(fg_color=COLORES["fondo"])
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

            self.current_frame_name = frame_name

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

    # ------------------------------------------------------------------
    # Respaldos automáticos
    # ------------------------------------------------------------------
    def _programar_respaldo_periodico(self):
        """Programa respaldos automáticos según el intervalo configurado"""
        try:
            intervalo_horas = self.config_service.obtener_valor(
                "backup_interval_hours", 24) or 24
            intervalo_horas = max(1, int(intervalo_horas))
            self._verificar_respaldo_periodico()
            # Reprogramar en 30 minutos para reaccionar a cambios de configuración
            self.after(30 * 60 * 1000, self._programar_respaldo_periodico)
        except Exception:
            pass

    def _verificar_respaldo_periodico(self):
        """Crea un respaldo automático si ha transcurrido el intervalo configurado"""
        try:
            habilitado = self.config_service.obtener_valor("backup_enabled", True)
            if not habilitado:
                return
            intervalo_horas = self.config_service.obtener_valor(
                "backup_interval_hours", 24) or 24
            intervalo_horas = max(1, int(intervalo_horas))

            from src.utils.backup_manager import get_backup_manager
            from src.utils.helpers import get_timestamp
            from datetime import datetime, timedelta

            gestor = get_backup_manager()
            respaldos = gestor.list_backups()
            ultimo = respaldos[0]["timestamp"] if respaldos else None

            vencido = True
            if ultimo and len(str(ultimo)) == 15:
                ultima_fecha = datetime.strptime(str(ultimo), "%Y%m%d_%H%M%S")
                vencido = datetime.now() - ultima_fecha > timedelta(hours=intervalo_horas)

            if vencido:
                gestor.create_backup(f"auto_{get_timestamp()}")
        except Exception:
            pass

    def run(self) -> str:
        """Ejecuta la ventana y devuelve 'logout' o 'exit' al cerrarse"""
        self.mainloop()
        return self._exit_status
