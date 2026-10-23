"""
Main Window
Ventana principal de la aplicación (requiere sesión iniciada)
"""

import logging
import queue
import sys
import threading
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
from typing import Any

import customtkinter as ctk

from src.config import db_config, settings
from src.gui.contratos_frame import ContratosFrame
from src.gui.estudiantes_frame import EstudiantesFrame
from src.gui.frames import (
    ConfiguracionFrame,
    DashboardFrame,
    DocumentosFrame,
    EmpleadosFrame,
    IncidenciasFrame,
    NominaFrame,
)
from src.gui.notas_frame import NotasFrame
from src.gui.theme import (
    BORDE_GRUESO,
    COLORES,
    RADIO_MEDIO,
    RADIO_GRANDE,
    aplicar_modo_apariencia,
    configurar_fuentes_seguras,
    estilo_boton_moderno,
    estilo_campo_moderno,
    estilo_combo_moderno,
    estilo_tarjeta_moderna,
    enable_windows_dpi_awareness,
    setup_ui_raiz,
)
from src.models import Usuario
from src.services.configuracion_service import ConfiguracionService
from src.services.documento_service import DocumentoService
from src.services.empleado_service import EmpleadoService
from src.services.incidencia_service import IncidenciaService
from src.services.pago_service import PagoService
from src.utils.security import PermissionChecker

logger = logging.getLogger(__name__)

# Módulos del sistema: (nombre interno, título, ícono)
MODULOS = [
    ("dashboard", "Panel de control", "📊"),
    ("empleados", "Empleados", "👥"),
    ("documentos", "Documentos", "📁"),
    ("incidencias", "Incidencias", "📅"),
    ("contratos", "Contratos", "📜"),
    ("nomina", "Nómina", "💰"),
    ("configuracion", "Configuración", "⚙️"),
    # Módulos académicos: se añaden al final para que Ctrl+1..7 conserve
    # exactamente el significado que tenía antes de existir este módulo.
    ("estudiantes", "Estudiantes", "🎓"),
    ("notas", "Calificaciones", "📝"),
]

TITULOS_VENTANA = {
    "dashboard": "Panel de control",
    "empleados": "Gestión de Empleados",
    "documentos": "Gestión Documental",
    "incidencias": "Incidencias y Permisos",
    "contratos": "Contratos Laborales",
    "nomina": "Nómina y Pagos",
    "configuracion": "Configuración",
    "estudiantes": "Gestión de Estudiantes",
    "notas": "Calificaciones y Periodos",
}

FRAME_CLASSES: dict[str, type[ctk.CTkFrame]] = {
    "dashboard": DashboardFrame,
    "empleados": EmpleadosFrame,
    "documentos": DocumentosFrame,
    "incidencias": IncidenciasFrame,
    "contratos": ContratosFrame,
    "nomina": NominaFrame,
    "configuracion": ConfiguracionFrame,
    "estudiantes": EstudiantesFrame,
    "notas": NotasFrame,
}

ROL_LABELS = {
    "admin": "Administrador",
    "manager": "Gestor",
    "user": "Usuario",
    "viewer": "Solo lectura",
}

# Módulos que no pasan por el mapa de permisos: el dashboard es el marco de
# bienvenida (sin datos ni acciones) y se muestra a cualquier sesión.
MODULOS_SIN_CONTROL_DE_ACCESO = frozenset({"dashboard"})


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

    def __init__(
        self,
        current_user: Usuario | str | None = None,
        preparar_servidor: bool = False,
    ):
        enable_windows_dpi_awareness()
        # Tema claro por defecto (coherente con el login). La preferencia
        # guardada del usuario se aplica más abajo, antes de crear la
        # interfaz, de modo que la ventana nunca parpadea en un tema ajeno.
        ctk.set_appearance_mode("Light")
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

        # Estado de respaldo automático: evita respaldos solapados y el cierre
        # de la aplicación a mitad de una copia de la base de datos.
        self._backup_en_curso = threading.Event()
        self._backup_timer: str | None = None
        # Identificador del reloj de la barra de estado: se cancela en
        # _cleanup para no dejar una tarea programada sobre una ventana que
        # ya se destruyó.
        self._clock_timer: str | None = None
        # Los hilos de fondo (respaldo, sincronización) no llaman nunca a
        # Tk: depositan el evento aquí y el hilo principal lo genera.
        self._eventos_hilo: queue.Queue[Any] = queue.Queue()
        self._eventos_poll_id: str | None = None

        # Bandeja del servidor central: los comandos del icono se encolan
        # desde su hilo y se ejecutan aquí, en el hilo de Tk.
        self._bandeja: Any = None
        self._bandeja_comandos: queue.Queue[tuple[str, ...]] = queue.Queue()
        self._bandeja_poll_id: str | None = None
        self._bandeja_estado_previo: str | None = None
        self._bandeja_menu_previo: list[Any] | None = None
        self._bandeja_reiniciar_sync = False
        # Vigilancia del nodo central: si el servicio se cae (error de disco,
        # cierre inesperado del hilo), se vuelve a levantar sin que el usuario
        # tenga que hacer nada. No reintenta cuando el usuario lo detuvo desde
        # la bandeja (allí la preferencia queda en False).
        self._servidor_timer: str | None = None
        self._servidor_reintentos = 0
        # Solo la ventana abierta por el arranque normal gestiona el nodo
        # central; las ventanas creadas sin esa responsabilidad (pruebas,
        # herramientas) no deben abrir puertos por su cuenta.
        self._vigilancia_servidor_activa = preparar_servidor

        # Resultados del respaldo automático: el hilo de respaldo encola el
        # evento y este hilo principal muestra el aviso al usuario.
        self.bind(
            "<<RespaldoAutomaticoCompletado>>",
            lambda _evento: self._on_respaldo_completado(),
        )
        self.bind(
            "<<RespaldoAutomaticoFallado>>",
            lambda _evento: self._on_respaldo_fallado(),
        )

        # Estado de sincronización: el agente avisa desde su propio hilo y el
        # aviso se encola como evento virtual, que el hilo principal procesa.
        self._sync_estado_pendiente: dict = {}
        self.bind(
            "<<EstadoSincronizacion>>",
            lambda _evento: self._pintar_estado_sincronizacion(),
        )

        # Identidad de la sesión: se acepta el nombre de usuario (texto) o
        # el objeto ya cargado. Con texto no hay dependencia de ninguna
        # sesión ajena; con objeto se copia el nombre antes de tocar la base
        # para no depender de que siga ligado a su sesión de origen.
        username_snapshot = None
        if isinstance(current_user, str):
            username_snapshot = current_user.strip() or None
        elif current_user is not None:
            try:
                username_snapshot = current_user.username
            except Exception:
                username_snapshot = None

        self._init_database()

        # Sesión propia y no scoped para toda la ventana: las operaciones
        # internas que usan get_session/close_session (registry) no la
        # cierran ni invalidan sus objetos cargados.
        self.current_user: Usuario | None = None
        self._inicializar_sesion(username_snapshot)

        # Estado de la interfaz
        self.current_frame: ctk.CTkFrame | None = None
        self.current_frame_name = "dashboard"
        self.sidebar_buttons: dict[str, ctk.CTkButton] = {}

        # Aplicar el modo de apariencia guardado antes de crear la interfaz
        try:
            modo = self.config_service.obtener_valor("apariencia_modo", "Light") or "Light"
            aplicar_modo_apariencia(modo)
        except Exception:
            aplicar_modo_apariencia("Light")

        self._create_ui()
        self._show_frame("dashboard")
        # Construir y medir la vista inicial antes del primer ciclo de eventos
        # evita pintar una ventana vacía y procesar callbacks durante el arranque.
        self.update_idletasks()
        if preparar_servidor:
            # Debe ejecutarse ANTES de vincular el agente: si el servidor queda
            # activo, el agente lee la configuración del puesto ya escrita.
            self._preparar_servidor_inicial()
        self._programar_vigilancia_servidor()
        self._programar_respaldo_periodico()
        self._vincular_sincronizacion()
        self._procesar_eventos_hilo()

    # ------------------------------------------------------------------
    # Permisos del usuario actual
    # ------------------------------------------------------------------
    def tiene_permiso(self, permiso: str) -> bool:
        """¿El usuario actual puede ejecutar una acción (create/update/...)?

        Sin sesión autenticada se deniega siempre (fail-closed): antes se
        devolvía True, de modo que una ventana construida sin usuario
        habilitaba crear, editar y eliminar en todos los módulos.
        """
        if self.current_user is None:
            logger.warning("Permiso %r denegado: no hay sesión activa", permiso)
            return False
        return PermissionChecker.has_permission(self.current_user.rol_valor, permiso)

    def puede_ver_modulo(self, modulo: str) -> bool:
        """¿El usuario actual puede acceder a un módulo?"""
        if self.current_user is None:
            # Sin sesión solo queda disponible el dashboard (marco de
            # bienvenida, sin datos ni acciones).
            return modulo == "dashboard"
        if modulo == "dashboard":
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

    def _inicializar_sesion(self, username: str | None = None) -> None:
        """(Re)crea la sesión de la ventana y sus servicios asociados."""
        session = db_config.new_session()
        try:
            current_user = (
                session.query(Usuario).filter(Usuario.username == username).first()
                if username
                else None
            )
            empleado_service = EmpleadoService(session)
            documento_service = DocumentoService(session)
            incidencia_service = IncidenciaService(session)
            pago_service = PagoService(session)
            config_service = ConfiguracionService(session)
        except Exception:
            db_config.close_session(session)
            raise

        self.session = session
        self.empleado_service = empleado_service
        self.documento_service = documento_service
        self.incidencia_service = incidencia_service
        self.pago_service = pago_service
        self.config_service = config_service
        self.current_user = current_user

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _create_ui(self):
        self._create_sidebar()
        self._create_main_area()
        self._create_status_bar()
        self._bind_atajos()

    def _create_sidebar(self):
        # Validación temprana del mapa de permisos: un módulo del menú que no
        # esté declarado en PermissionChecker.MODULE_ACCESS queda oculto para
        # todos los roles (fail-closed). Se avisa en el log para detectar la
        # desincronización al añadir un módulo nuevo.
        sin_declarar = [
            nombre
            for nombre, _titulo, _icono in MODULOS
            if nombre not in MODULOS_SIN_CONTROL_DE_ACCESO
            and nombre not in PermissionChecker.modulos_conocidos()
        ]
        if sin_declarar:
            logger.warning(
                "Módulos del menú sin permiso declarado (quedarán ocultos "
                "para todos los roles): %s",
                ", ".join(sin_declarar),
            )

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=COLORES["panel"])
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
                font=ctk.CTkFont(size=13),
                height=38,
                anchor="w",
                **estilo_boton_moderno("fantasma"),
                command=lambda fn=frame_name: self._show_frame(fn),
            )
            btn.pack(pady=2, padx=10, fill="x")
            self.sidebar_buttons[frame_name] = btn

        separator = ctk.CTkFrame(self.sidebar, height=2)
        separator.pack(pady=15, padx=10, fill="x")

        # Información de la institución
        institution_name = "Institución Educativa"
        try:
            config = self.config_service.obtener_configuracion_general()
            institution_name = config.get("nombre_institucion") or institution_name
        except Exception:
            logger.debug("operación de interfaz ignorada", exc_info=True)

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
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORES["fondo"])
        self.main_container.pack(side="right", fill="both", expand=True)

        self.header = ctk.CTkFrame(
            self.main_container,
            height=60,
            fg_color=COLORES["panel"],
            corner_radius=RADIO_MEDIO,
            border_width=BORDE_GRUESO,
            border_color=COLORES["borde"],
        )
        self.header.pack(side="top", fill="x", padx=10, pady=(10, 5))
        self.header.pack_propagate(False)

        self.frame_title = ctk.CTkLabel(
            self.header,
            text="Panel de control",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORES["texto"],
        )
        self.frame_title.pack(side="left", padx=20, pady=15)

        # Alternar modo de apariencia (oscuro/claro), preferencia persistente
        self.apariencia_btn = ctk.CTkButton(
            self.header,
            text="☀️ Claro" if ctk.get_appearance_mode() == "Dark" else "🌙 Oscuro",
            width=95,
            height=35,
            fg_color=COLORES["acento"],
            hover_color=COLORES["panel_hover"],
            text_color="white",
            command=self._toggle_apariencia,
        )
        self.apariencia_btn.pack(side="right", padx=3, pady=12)

        # Ayuda (guía rápida de uso y atajos)
        self.ayuda_btn = ctk.CTkButton(
            self.header,
            text="Ayuda",
            width=75,
            height=35,
            fg_color=COLORES["acento"],
            hover_color=COLORES["panel_hover"],
            text_color="white",
            command=self._on_ayuda,
        )
        self.ayuda_btn.pack(side="right", padx=3, pady=12)

        # Acerca de (información de la aplicación)
        self.about_btn = ctk.CTkButton(
            self.header,
            text="Acerca de",
            width=85,
            height=35,
            fg_color=COLORES["acento"],
            hover_color=COLORES["panel_hover"],
            text_color="white",
            command=self._on_acerca_de,
        )
        self.about_btn.pack(side="right", padx=3, pady=12)

        # Cerrar sesión
        self.logout_btn = ctk.CTkButton(
            self.header,
            text="Cerrar Sesión",
            width=105,
            height=35,
            fg_color=COLORES["acento"],
            hover_color=COLORES["panel_hover"],
            text_color="white",
            command=self._on_logout,
        )
        self.logout_btn.pack(side="right", padx=(3, 6), pady=12)

        # Salir de la aplicación
        self.exit_btn = ctk.CTkButton(
            self.header,
            text="Salir",
            width=65,
            height=35,
            fg_color=COLORES["acento"],
            hover_color=COLORES["panel_hover"],
            text_color="white",
            command=self._on_exit,
        )
        self.exit_btn.pack(side="right", padx=3, pady=12)

        self.content_frame = ctk.CTkFrame(
            self.main_container,
            **estilo_tarjeta_moderna(),
        )
        self.content_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

    def _create_status_bar(self):
        from datetime import datetime

        self.status_bar = ctk.CTkFrame(
            self.main_container,
            height=30,
            fg_color=COLORES["panel"],
            corner_radius=RADIO_MEDIO,
            border_width=BORDE_GRUESO,
            border_color=COLORES["borde"],
        )
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=(5, 10))
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

        # Indicador del agente de sincronización: dice de un vistazo si los
        # datos de este puesto ya están en la red o si hay algo esperando.
        self.sync_label = ctk.CTkLabel(
            self.status_bar,
            text="Sincronización: —",
            font=ctk.CTkFont(size=10),
            text_color=COLORES["texto_suave"],
        )
        self.sync_label.pack(side="right", padx=(10, 0), pady=5)

        self.sync_btn = ctk.CTkButton(
            self.status_bar,
            text="Sincronizar ahora",
            width=120,
            height=22,
            font=ctk.CTkFont(size=10),
            command=self._on_sincronizar_ahora,
        )
        if self.tiene_permiso("config"):
            self.sync_btn.pack(side="right", padx=(10, 10), pady=4)

        self._update_clock()

    # ------------------------------------------------------------------
    # Sincronización con la intranet
    # ------------------------------------------------------------------
    def _vincular_sincronizacion(self):
        """
        Conecta la barra de estado con el agente de sincronización

        Si el agente ya está en marcha (lo arranca main.py antes de abrir la
        ventana) solo se registra el notificador; si no, se intenta arrancar
        aquí, de modo que un cierre y una reapertura de sesión no dejen la
        sincronización apagada. Nada de esto es obligatorio: sin agente, la
        barra muestra el estado y el resto de la aplicación funciona igual.
        """
        try:
            from sync_agent import agente_actual, estado_sincronizacion, iniciar_agente
        except Exception:
            logger.debug("El agente de sincronización no está disponible", exc_info=True)
            self._pintar_estado_sincronizacion({"habilitado": False})
            return

        try:
            # Si el servidor se configuró al abrir esta sesión (primer inicio),
            # main.py todavía no activó la captura; se hace aquí antes de
            # arrancar el agente. Ambas operaciones son idempotentes.
            from sync_agent.config import cargar as cargar_sync

            if cargar_sync().activo:
                db_config.preparar_sincronizacion()
                db_config.activar_captura_sincronizacion()
            agente = agente_actual()
            if agente is None:
                agente = iniciar_agente(notificador=self._on_estado_sincronizacion)
            else:
                agente.notificador = self._on_estado_sincronizacion
            self._pintar_estado_sincronizacion(estado_sincronizacion())
        except Exception:
            logger.warning("No se pudo vincular la sincronización", exc_info=True)

    def _on_estado_sincronizacion(self, estado: dict) -> None:
        """Recibe el estado del agente (hilo de fondo) y lo encola al principal"""
        try:
            self._sync_estado_pendiente = dict(estado)
        except Exception:
            return
        self._notificar_hilo_principal("<<EstadoSincronizacion>>")

    def _pintar_estado_sincronizacion(self, estado: dict | None = None) -> None:
        """Actualiza el indicador de la barra de estado (hilo principal)"""
        if estado is None:
            estado = self._sync_estado_pendiente
        if not hasattr(self, "sync_label"):
            return
        try:
            if not self.sync_label.winfo_exists():
                return
        except tk.TclError:
            return

        etiquetas = {
            "detenido": ("detenida", "texto_suave"),
            "inactivo": ("inactiva", "texto_suave"),
            "sin_conexion": ("sin conexión", "error"),
            "sincronizando": ("sincronizando…", "acento"),
            "sincronizado": ("al día", "ok"),
            "error_token": ("token rechazado", "error"),
        }
        es_oscuro = ctk.get_appearance_mode() == "Dark"
        colores = {
            "texto_suave": COLORES["texto_suave"],
            "acento": COLORES["acento"],
            "ok": "#2ecc71" if es_oscuro else "#1e8449",
            "error": "#e74c3c" if es_oscuro else "#c0392b",
        }

        clave = str(estado.get("estado") or "detenido")
        texto, color = etiquetas.get(clave, (clave, "texto_suave"))
        pendientes = int(estado.get("pendientes") or 0)
        if pendientes:
            texto = f"{texto} · {pendientes} pendiente{'s' if pendientes != 1 else ''}"
        conflictos = int(estado.get("conflictos") or 0)
        if conflictos:
            texto = f"{texto} · {conflictos} conflicto{'s' if conflictos != 1 else ''}"

        try:
            self.sync_label.configure(text=f"Sincronización: {texto}", text_color=colores[color])
            habilitado = bool(estado.get("habilitado"))
            self.sync_btn.configure(state="normal" if habilitado else "disabled")
        except tk.TclError:
            logger.debug("Indicador de sincronización omitido: ventana cerrada")

    def _on_sincronizar_ahora(self):
        """Pide un ciclo inmediato de sincronización y lo informa en la barra"""
        if not self.tiene_permiso("config"):
            self._avisar_acceso_denegado()
            return
        try:
            from sync_agent import estado_sincronizacion, sincronizar_ahora
        except Exception:
            messagebox.showinfo(
                "Sincronización",
                "El agente de sincronización no está disponible en esta instalación.",
            )
            return
        try:
            if not sincronizar_ahora():
                messagebox.showinfo(
                    "Sincronización",
                    "La sincronización no está habilitada en este equipo.\n"
                    "Actívela en Configuración → Sincronización.",
                )
                return
            estado = estado_sincronizacion()
            self._sync_estado_pendiente = dict(estado)
            self._pintar_estado_sincronizacion(estado)
            self.status_label.configure(text="Sincronización solicitada…")
        except Exception as e:
            logger.warning("No se pudo solicitar la sincronización", exc_info=True)
            messagebox.showwarning("Sincronización", f"No se pudo sincronizar: {e}")

    def _update_clock(self):
        try:
            from datetime import datetime

            if hasattr(self, "datetime_label") and self.datetime_label.winfo_exists():
                self.datetime_label.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M"))
                self._clock_timer = self.after(30000, self._update_clock)
                # El reloj también refresca el indicador de sincronización:
                # si el agente está inactivo nadie más avisa de su estado.
                self.after(50, self._refrescar_indicador_sincronizacion)
        except Exception:
            logger.debug("operación de interfaz ignorada", exc_info=True)

    def _refrescar_indicador_sincronizacion(self) -> None:
        """Relee el estado del agente para el indicador de la barra de estado"""
        try:
            from sync_agent import estado_sincronizacion

            self._pintar_estado_sincronizacion(estado_sincronizacion())
        except Exception:
            logger.debug("operación de interfaz ignorada", exc_info=True)

    # ------------------------------------------------------------------
    # Servidor central y bandeja del sistema
    # ------------------------------------------------------------------
    def _preparar_servidor_inicial(self) -> None:
        """
        Arranca el nodo central que el teléfono necesita para conectarse

        En una instalación nueva el servidor se activa por sí solo: el teléfono
        no tiene ninguna pantalla de configuración y debe encontrar el sistema
        apenas se abra la aplicación. El usuario puede detenerlo desde el icono
        de la bandeja; esa decisión queda guardada en config.json y se respeta
        en los arranques siguientes.
        """
        try:
            from sync_agent.servidor_embebido import (
                CLAVE_SERVIDOR_AUTO,
                ESTADO_ACTIVO,
                iniciar_servidor_embebido,
                preferencia_servidor,
            )
        except Exception:
            logger.warning("El servidor central embebido no está disponible", exc_info=True)
            return

        try:
            preferencia = preferencia_servidor()
            if preferencia is None:
                # Primera vez: el nodo central es el comportamiento normal.
                # Se informa en la barra de estado y en la bandeja, sin pedir
                # al usuario que configure nada.
                preferencia = True
                settings.set_config_value(CLAVE_SERVIDOR_AUTO, True)
                logger.info("Nodo central activado por primera vez en este equipo")

            if preferencia:
                estado = iniciar_servidor_embebido(esperar=True)
                if estado.get("estado") == ESTADO_ACTIVO:
                    self.status_label.configure(
                        text=f"Servidor para el teléfono: {estado.get('url_red')}"
                    )
                else:
                    self.status_label.configure(
                        text=(
                            "Servidor para el teléfono no disponible: "
                            f"{estado.get('error') or estado.get('estado')}"
                        )
                    )
            else:
                self.status_label.configure(
                    text="Servidor para el teléfono detenido (se inicia desde la bandeja)"
                )
        except Exception:
            logger.warning("No se pudo preparar el servidor central", exc_info=True)

    # ------------------------------------------------------------------
    # Vigilancia del nodo central
    # ------------------------------------------------------------------
    def _programar_vigilancia_servidor(self) -> None:
        """Revisa el estado del nodo central cada 20 segundos"""
        if not self._vigilancia_servidor_activa:
            return
        if self._servidor_timer is not None:
            try:
                self.after_cancel(self._servidor_timer)
            except Exception:
                logger.debug("operación de interfaz ignorada", exc_info=True)
        self._servidor_timer = None
        try:
            if self.winfo_exists():
                self._servidor_timer = self.after(20_000, self._vigilar_servidor)
        except tk.TclError:
            logger.debug("La ventana se cerró al programar la vigilancia del servidor")

    def _vigilar_servidor(self) -> None:
        """Vuelve a levantar el servicio si se cayó y el usuario lo quiere activo"""
        self._servidor_timer = None
        try:
            from sync_agent.servidor_embebido import (
                ESTADO_ACTIVO,
                ESTADO_DETENIDO,
                ESTADO_ERROR,
                ESTADO_OCUPADO,
                estado_servidor_embebido,
                iniciar_servidor_embebido,
                preferencia_servidor,
            )

            estado = estado_servidor_embebido()
            clave = str(estado.get("estado") or ESTADO_DETENIDO)
            if clave == ESTADO_ACTIVO:
                self._servidor_reintentos = 0
            elif clave == ESTADO_OCUPADO:
                # Hay otro servicio en el puerto (probablemente otra instancia
                # de la aplicación): reiniciar solo repetiría el mismo error.
                self._servidor_reintentos = 0
            elif clave in (ESTADO_DETENIDO, ESTADO_ERROR):
                if preferencia_servidor() is True and self._servidor_reintentos < 5:
                    self._servidor_reintentos += 1
                    logger.warning(
                        "El nodo central está %s; reintentando arranque (%s/5)",
                        clave,
                        self._servidor_reintentos,
                    )
                    iniciar_servidor_embebido(esperar=False)
                    # La configuración del puesto y el agente se reenganchan
                    # cuando el servicio vuelva a estar activo.
                    self._bandeja_reiniciar_sync = True
        except Exception:
            logger.debug("Vigilancia del servidor omitida", exc_info=True)
        finally:
            self._programar_vigilancia_servidor()

    def iniciar_bandeja_servidor(self) -> None:
        """Muestra el estado del servidor en el área de notificación (Windows)"""
        if sys.platform != "win32" or self._bandeja is not None:
            return
        try:
            from sync_agent.servidor_embebido import estado_servidor_embebido
            from updater.tray_icon import TrayIcon
        except Exception:
            logger.warning("No se pudo cargar la bandeja del servidor", exc_info=True)
            return

        try:
            estado = estado_servidor_embebido()
            self._bandeja = TrayIcon(
                self._bandeja_comandos,
                tooltip=self._texto_bandeja(estado),
                menu=self._menu_bandeja(estado),
                class_name="SDEP_CPP5_Servidor_Tray",
            )
            self._bandeja.start()
            self._bandeja_menu_previo = self._menu_bandeja(estado)
            # El icono tarda unos instantes en tener ventana propia: la primera
            # notificación se deja para el primer sondeo, ya con el icono listo.
            self._bandeja_poll_id = self.after(1500, self._procesar_bandeja)
        except Exception:
            logger.warning("No se pudo mostrar la bandeja del servidor", exc_info=True)
            self._bandeja = None

    def _menu_bandeja(self, estado: dict) -> list[Any]:
        """Elementos del menú contextual según el estado del servidor"""
        activo = estado.get("estado") == "activo"
        elementos: list[Any] = [
            ("Abrir el sistema", "show"),
            ("Copiar URL para el teléfono", "copiar"),
            ("Mostrar datos de conexión", "datos"),
        ]
        if activo:
            elementos.append(("Detener servidor y desactivar autoarranque", "detener"))
        else:
            elementos.append(("Iniciar servidor en este equipo", "iniciar"))
        elementos.append(None)
        elementos.append(("Salir", "exit"))
        return elementos

    @staticmethod
    def _texto_bandeja(estado: dict) -> str:
        """Texto flotante del icono (el límite de Windows lo recorta el icono)"""
        clave = str(estado.get("estado") or "detenido")
        if clave == "activo":
            return f"SDEP · Servidor activo · {estado.get('url_red') or ''}"
        if clave == "iniciando":
            return "SDEP · Iniciando servidor…"
        if clave == "ocupado":
            return "SDEP · Servidor ya abierto en este equipo"
        if clave == "error":
            return "SDEP · Servidor con error"
        return "SDEP · Servidor detenido"

    def _actualizar_bandeja(self) -> None:
        """Refresca icono, menú y estado, y avisa de los cambios importantes"""
        if self._bandeja is None:
            return
        try:
            from sync_agent.servidor_embebido import estado_servidor_embebido

            estado = estado_servidor_embebido()
        except Exception:
            logger.debug("No se pudo leer el estado del servidor", exc_info=True)
            return

        clave = str(estado.get("estado") or "detenido")
        try:
            menu = self._menu_bandeja(estado)
            if menu != self._bandeja_menu_previo:
                self._bandeja.set_menu(menu)
                self._bandeja_menu_previo = menu
            self._bandeja.update_tooltip(self._texto_bandeja(estado))
        except Exception:
            logger.debug("No se pudo actualizar el icono del servidor", exc_info=True)

        if self._bandeja_reiniciar_sync and clave == "activo":
            self._bandeja_reiniciar_sync = False
            try:
                # Un arranque posterior del nodo no pasó por main.py: hay que
                # preparar el esquema y enganchar la captura antes de recrear
                # el agente, igual que en el arranque normal.
                from src.config import db_config
                from sync_agent import estado_sincronizacion, reiniciar_agente

                db_config.preparar_sincronizacion()
                db_config.activar_captura_sincronizacion()
                reiniciar_agente()
                self._sync_estado_pendiente = dict(estado_sincronizacion())
                self._pintar_estado_sincronizacion()
            except Exception:
                logger.warning("No se pudo reiniciar el agente", exc_info=True)

        if clave == self._bandeja_estado_previo:
            return
        if clave == "activo":
            self._notificar_bandeja(
                "Servidor activo",
                f"El teléfono puede conectarse en {estado.get('url_red')}",
            )
        elif clave in ("ocupado", "error"):
            self._notificar_bandeja(
                "Servidor no disponible",
                str(estado.get("error") or "Revisa el estado del servidor"),
            )
        elif clave == "detenido" and self._bandeja_estado_previo is not None:
            self._notificar_bandeja(
                "Servidor detenido",
                "El teléfono no podrá conectarse hasta que lo inicies de nuevo.",
            )
        self._bandeja_estado_previo = clave

    def _notificar_bandeja(self, titulo: str, mensaje: str) -> None:
        """Muestra un aviso del sistema desde el icono (si está disponible)"""
        if self._bandeja is None:
            return
        try:
            self._bandeja.notify(titulo, mensaje)
        except Exception:
            logger.debug("No se pudo mostrar el aviso del servidor", exc_info=True)

    def _procesar_bandeja(self) -> None:
        """Atiende los comandos del icono y refresca su estado (hilo de Tk)"""
        self._bandeja_poll_id = None
        if self._bandeja is None:
            return
        try:
            while True:
                comando = self._bandeja_comandos.get_nowait()
                self._ejecutar_comando_bandeja(comando[0] if comando else "")
        except queue.Empty:
            pass
        except Exception:
            logger.debug("Comando de bandeja inválido", exc_info=True)

        self._actualizar_bandeja()
        try:
            self._bandeja_poll_id = self.after(1000, self._procesar_bandeja)
        except tk.TclError:
            logger.debug("La ventana se cerró durante el sondeo de la bandeja")

    def _ejecutar_comando_bandeja(self, accion: str) -> None:
        """Despacha una acción elegida en el menú del icono"""
        if accion == "show":
            try:
                self.deiconify()
                self.state("normal")
                self.lift()
                self.focus_force()
            except tk.TclError:
                logger.debug("No se pudo traer la ventana al frente")
        elif accion == "copiar":
            self._copiar_url_servidor()
        elif accion == "datos":
            self._mostrar_datos_conexion()
        elif accion == "iniciar":
            self._iniciar_servidor_desde_bandeja()
        elif accion == "detener":
            self._detener_servidor_desde_bandeja()
        elif accion == "exit":
            self._on_exit()

    def _copiar_url_servidor(self) -> None:
        """Copia al portapapeles la dirección que debe escribir el teléfono"""
        try:
            from sync_agent.servidor_embebido import estado_servidor_embebido

            estado = estado_servidor_embebido()
            url = str(estado.get("url_red") or estado.get("url_local") or "")
            if not url:
                messagebox.showinfo(
                    "Servidor",
                    "El servidor no está activo en este equipo.\n"
                    "Inícialo desde el menú del icono de la bandeja.",
                )
                return
            self.clipboard_clear()
            self.clipboard_append(url)
            self.update_idletasks()
            self.status_label.configure(text=f"URL copiada: {url}")
        except Exception:
            logger.debug("No se pudo copiar la URL del servidor", exc_info=True)

    def _mostrar_datos_conexion(self) -> None:
        """Explica cómo conectar el teléfono al nodo central"""
        try:
            from sync_agent.servidor_embebido import estado_servidor_embebido

            estado = estado_servidor_embebido()
        except Exception:
            estado = {}
        url = str(estado.get("url_red") or estado.get("url_local") or "")
        if not url:
            messagebox.showinfo(
                "Datos de conexión",
                "El servidor no está activo en este equipo.\n\n"
                "Inícialo desde el menú del icono de la bandeja del sistema.",
            )
            return
        messagebox.showinfo(
            "Datos de conexión",
            "En el teléfono (SDEP Móvil):\n"
            "1. Conéctelo a la misma red Wi-Fi que este equipo.\n"
            "2. Abra la aplicación: encuentra este servidor sola, sin escribir "
            "dirección ni token.\n"
            "3. Ingrese con el mismo usuario y contraseña de esta computadora.\n\n"
            f"Dirección del nodo (solo para diagnóstico): {url}\n\n"
            "El nodo central copia las cuentas de este equipo que aún no existan "
            "allí; las demás conservan su clave y las faltantes usan las iniciales.",
        )

    def _iniciar_servidor_desde_bandeja(self) -> None:
        """Activa el arranque automático y levanta el nodo central ahora"""
        try:
            from sync_agent.servidor_embebido import (
                CLAVE_SERVIDOR_AUTO,
                iniciar_servidor_embebido,
            )

            settings.set_config_value(CLAVE_SERVIDOR_AUTO, True)
            self._bandeja_reiniciar_sync = True
            self._servidor_reintentos = 0
            iniciar_servidor_embebido(esperar=False)
            self.status_label.configure(text="Iniciando servidor para el teléfono…")
        except Exception:
            logger.warning("No se pudo iniciar el servidor desde la bandeja", exc_info=True)

    def _detener_servidor_desde_bandeja(self) -> None:
        """Desactiva el arranque automático y detiene el nodo central"""
        try:
            from sync_agent.servidor_embebido import (
                CLAVE_SERVIDOR_AUTO,
                detener_servidor_embebido,
            )

            settings.set_config_value(CLAVE_SERVIDOR_AUTO, False)
            detener_servidor_embebido()
            try:
                from urllib.parse import urlparse

                from sync_agent import config as config_sync
                from sync_agent import detener_agente

                detener_agente(timeout=3.0)
                # Si este puesto sincronizaba contra el nodo local, dejarlo
                # habilitado solo generaría un intento fallido cada 30 s con
                # el servidor apagado. Al volver a iniciarlo, el nodo escribe
                # la configuración y lo habilita de nuevo.
                actual = config_sync.cargar()
                if urlparse(actual.url_servidor or "").hostname in (
                    "127.0.0.1",
                    "localhost",
                    "::1",
                ):
                    config_sync.guardar(habilitado=False)
            except Exception:
                logger.debug("No se pudo detener el agente al cerrar el servidor", exc_info=True)
            self.status_label.configure(text="Servidor detenido")
            self.after(50, self._actualizar_bandeja)
        except Exception:
            logger.warning("No se pudo detener el servidor desde la bandeja", exc_info=True)

    # ------------------------------------------------------------------
    # Atajos de teclado
    # ------------------------------------------------------------------
    # Método canónico de "actualizar" por tipo de frame
    METODOS_REFRESCAR = {
        "DashboardFrame": "_load_data",
        "EmpleadosFrame": "_load_empleados",
        "DocumentosFrame": "_load_documentos",
        "IncidenciasFrame": "_load_data",
        "ContratosFrame": "_load_data",
        "NominaFrame": "_load_pagos",
        "ConfiguracionFrame": "_load_configuracion",
        "EstudiantesFrame": "_load_data",
        "NotasFrame": "_load_data",
    }

    # Método canónico de "nuevo registro" por tipo de frame
    METODOS_NUEVO = {
        "EmpleadosFrame": "_on_new_empleado",
        "DocumentosFrame": "_on_new_documento",
        "IncidenciasFrame": "_on_new_incidencia",
        "ContratosFrame": "_nuevo_contrato",
        "NominaFrame": "_on_new_pago",
        "ConfiguracionFrame": "_on_new_usuario",
        "EstudiantesFrame": "_on_new_estudiante",
        "NotasFrame": "_on_nueva_nota",
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
        # Navegación directa a cada módulo con Ctrl+1..N, en el mismo orden
        # que MODULOS. La numeración se deriva de la propia lista para que
        # las teclas y los módulos no puedan desincronizarse.
        for indice, (frame_name, _titulo, _icono) in enumerate(MODULOS, start=1):
            if indice > 9:
                logger.warning(
                    "MODULOS supera los nueve atajos directos; %s solo es "
                    "accesible desde la barra lateral",
                    frame_name,
                )
                break
            self.bind(
                f"<Control-Key-{indice}>",
                lambda e, fn=frame_name: self._show_frame(fn),
            )

    def _ejecutar_metodo_frame(self, *nombres: str) -> bool:
        """
        Ejecuta el primer método existente del frame actual.

        Returns:
            True si se encontró un método y terminó sin error
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
                    return False
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
        if not self.tiene_permiso("create"):
            self.status_label.configure(
                text="Su rol no tiene permiso para crear registros (Ctrl+N)"
            )
            return
        nombre_clase = type(self.current_frame).__name__ if self.current_frame else ""
        metodo = self.METODOS_NUEVO.get(nombre_clase)
        if metodo:
            self._ejecutar_metodo_frame(metodo)
        elif self.current_frame is not None:
            self.status_label.configure(
                text="Ctrl+N no aplica en este módulo (use Ayuda para más detalles)"
            )

    def _atajo_guardar(self):
        """Ctrl+S: guarda los cambios del módulo activo (si lo soporta)"""
        if not self.tiene_permiso("update"):
            self.status_label.configure(
                text="Su rol no tiene permiso para guardar cambios (Ctrl+S)"
            )
            return
        nombre_clase = type(self.current_frame).__name__ if self.current_frame else ""
        metodo = self.METODOS_GUARDAR.get(nombre_clase)
        if metodo:
            self._ejecutar_metodo_frame(metodo)
        elif self.current_frame is not None:
            self.status_label.configure(text="Ctrl+S solo aplica en el módulo de Configuración")

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
                    arbol.selection_remove(*arbol.selection())
                    self.status_label.configure(text="Selección eliminada (Esc)")
                    return
            except Exception:
                logger.debug("operación de interfaz ignorada", exc_info=True)
        self.status_label.configure(text="Esc cierra los cuadros de diálogo abiertos")

    def _on_ayuda(self):
        """Muestra la guía rápida de uso y atajos de teclado"""
        from src.gui.frames import InfoDialog

        texto = (
            "GUÍA RÁPIDA\n"
            "===========\n\n"
            "Módulos del sistema (barra lateral o Ctrl+1 a Ctrl+9):\n"
            "  Ctrl+1  Panel de control  Ctrl+2  Empleados\n"
            "  Ctrl+3  Documentos     Ctrl+4  Incidencias\n"
            "  Ctrl+5  Contratos      Ctrl+6  Nómina\n"
            "  Ctrl+7  Configuración  Ctrl+8  Estudiantes\n"
            "  Ctrl+9  Calificaciones\n\n"
            "Atajos generales:\n"
            "  Ctrl+N   Nuevo registro en el módulo activo\n"
            "  Ctrl+F   Buscar / enfocar filtro\n"
            "  Ctrl+S   Guardar cambios (módulo de configuración)\n"
            "  F5       Actualizar la lista del módulo activo\n"
            "  Esc      Cerrar diálogos o limpiar la selección\n\n"
            "Consejos:\n"
            "- Doble clic sobre una fila abre sus detalles.\n"
            "- Clic derecho muestra las acciones disponibles.\n"
            "- Use la rueda del ratón o el trackpad para desplazarse por las tablas;\n"
            "  mantenga Shift mientras desplaza para moverse horizontalmente.\n"
            "- Los reportes PDF y exportaciones se guardan donde usted elija.\n"
            "- La sección 'Seguridad y Respaldo' permite crear, verificar,\n"
            "  restaurar y eliminar copias de seguridad de la base de datos.\n"
        )
        InfoDialog(self, "Ayuda - Guía Rápida", texto)

    def _on_acerca_de(self):
        """Muestra la información de la aplicación"""
        from src.gui.frames import InfoDialog

        detalle_build = ""
        if getattr(settings, "build_commit", ""):
            detalle_build = f"Build: {settings.build_commit}"
            if getattr(settings, "build_date", ""):
                detalle_build += f" ({settings.build_date})"
        texto = (
            "ACERCA DE\n"
            "=========\n\n"
            f"Sistema: {settings.app_name}\n"
            f"Versión: v{settings.app_version}\n"
            + (f"{detalle_build}\n" if detalle_build else "")
            + "\n"
            "Sistema de gestión de personal y nómina para instituciones\n"
            "educativas. Desarrollado en Python con CustomTkinter y\n"
            "SQLAlchemy (SQLite).\n\n"
            "Roles del sistema:\n"
            "  - Administrador: acceso total (configuración, usuarios,\n"
            "    respaldos y auditoría).\n"
            "  - Gestor: gestiona empleados, documentos, incidencias y\n"
            "    nómina.\n"
            "  - Usuario: consulta empleados, documentos e incidencias; no modifica\n"
            "    registros hasta que exista una asociación segura con su empleado.\n"
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
            # Aplicar el tema recrea el frame activo (los widgets guardan la
            # paleta al construirse), así que se confirma antes cuando puede
            # haber un formulario a medio llenar. El dashboard no tiene
            # datos que perder y cambia sin preguntar.
            if (self.current_frame_name or "dashboard") != "dashboard" and not messagebox.askyesno(
                "Cambiar tema",
                "Para aplicar el tema se recargará la vista actual y se perderán\n"
                "los cambios que no haya guardado.\n\n¿Desea continuar?",
            ):
                return

            modo_actual = ctk.get_appearance_mode()
            nuevo = "Light" if modo_actual == "Dark" else "Dark"
            aplicar_modo_apariencia(nuevo)
            configurar_fuentes_seguras()
            puede_guardar_preferencia = self.tiene_permiso("config")
            if puede_guardar_preferencia:
                self.config_service.establecer_valor("apariencia_modo", nuevo)
            self._recolorear_chrome()
            # Recrear el frame activo para que tome la paleta nueva
            self._show_frame(self.current_frame_name or "dashboard")
            self.apariencia_btn.configure(text="☀️ Claro" if nuevo == "Dark" else "🌙 Oscuro")
            mensaje = f"Tema {nuevo.lower()} aplicado"
            if not puede_guardar_preferencia:
                mensaje += " (solo para esta sesión)"
            self.status_label.configure(text=mensaje)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cambiar el tema: {str(e)}")

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
            self.header.configure(
                fg_color=COLORES["panel"],
                border_color=COLORES["borde"],
            )
            self.frame_title.configure(text_color=COLORES["texto"])
            self.status_bar.configure(
                fg_color=COLORES["panel"],
                border_color=COLORES["borde"],
            )
            self.status_label.configure(text_color=COLORES["texto_suave"])
            self.datetime_label.configure(text_color=COLORES["texto_suave"])
            self.content_frame.configure(
                fg_color=COLORES["panel"],
                border_color=COLORES["borde"],
            )
            # Botones de la cabecera (se recrean con la paleta nueva)
            self.apariencia_btn.configure(
                fg_color=COLORES["acento"], hover_color=COLORES["acento_hover"],
                text_color="white",
            )
            self.ayuda_btn.configure(
                fg_color=COLORES["acento"], hover_color=COLORES["acento_hover"],
                text_color="white",
            )
            self.about_btn.configure(
                fg_color=COLORES["acento"], hover_color=COLORES["acento_hover"],
                text_color="white",
            )
            self.logout_btn.configure(
                fg_color=COLORES["acento"], hover_color=COLORES["acento_hover"],
                text_color="white",
            )
            self.exit_btn.configure(
                fg_color=COLORES["acento"], hover_color=COLORES["acento_hover"],
                text_color="white",
            )
            # Los botones de módulos también siguen la paleta activa.
            for boton in self.sidebar_buttons.values():
                boton.configure(
                    fg_color="transparent",
                    hover_color=COLORES["panel_hover"],
                    text_color=COLORES["texto"],
                )
        except Exception:
            logger.debug("operación de interfaz ignorada", exc_info=True)

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def show_frame(self, frame_name: str, **kwargs):
        """Muestra un frame y aplica parámetros de selección si el frame lo soporta"""
        if not self.puede_ver_modulo(frame_name):
            self._show_frame(frame_name)
            return
        self._show_frame(frame_name)
        if kwargs and self.current_frame is not None:
            for key, value in kwargs.items():
                metodo = getattr(self.current_frame, key, None)
                if callable(metodo):
                    try:
                        metodo(value)
                    except Exception as e:
                        logger.error("Error aplicando parámetro '%s' al frame: %s", key, e)

    def _show_frame(self, frame_name: str):
        try:
            if not self.puede_ver_modulo(frame_name):
                self._avisar_acceso_denegado()
                return

            self.current_frame_name = frame_name

            # Destruir el frame actual
            if self.current_frame is not None:
                try:
                    self.current_frame.destroy()
                except Exception:
                    logger.debug("operación de interfaz ignorada", exc_info=True)

            self.frame_title.configure(text=TITULOS_VENTANA.get(frame_name, frame_name))

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
                text=f"Mostrando: {TITULOS_VENTANA.get(frame_name, frame_name)}"
            )
        except Exception as e:
            self._avisar_error_modulo(frame_name, str(e))
            self.current_frame = ctk.CTkFrame(self.content_frame)
            self.current_frame.pack(fill="both", expand=True)
            ctk.CTkLabel(
                self.current_frame,
                text=f"Error al cargar: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="red",
            ).pack(expand=True)

    def _avisar_acceso_denegado(self) -> None:
        """Avisa al usuario que su rol no permite el módulo solicitado"""
        try:
            messagebox.showwarning(
                "Acceso denegado",
                "Su rol no tiene permisos para acceder a este módulo",
            )
        except tk.TclError:
            # Sin raíz operativa (cierre en curso, sesión no interactiva):
            # el aviso se registra y la aplicación sigue viva.
            logger.warning("Aviso de acceso denegado no mostrable", exc_info=True)

    def _avisar_error_modulo(self, frame_name: str, detalle: str) -> None:
        """Informa el fallo de carga de un módulo sin bloquear la interfaz"""
        try:
            messagebox.showerror("Error", f"Error al cargar el módulo {frame_name}: {detalle}")
        except tk.TclError:
            logger.error("Error al cargar el módulo %s: %s", frame_name, detalle, exc_info=True)

    # ------------------------------------------------------------------
    # Sesión
    # ------------------------------------------------------------------
    def _on_logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Desea cerrar la sesión actual?"):
            self._cleanup()
            self._exit_status = "logout"
            self.destroy()

    def _on_exit(self):
        if not messagebox.askyesno(
            "Salir",
            "¿Desea salir de la aplicación?\n\n"
            "El servidor para el teléfono también se detendrá.",
        ):
            return
        self._cancelar_respaldo_programado()
        if self._backup_en_curso.is_set():
            # No cerrar con una copia de la base de datos a medias: se espera
            # (de forma acotada) a que el respaldo en curso termine.
            try:
                messagebox.showinfo(
                    "Respaldo en curso",
                    "Se está creando una copia de seguridad.\n"
                    "La aplicación se cerrará al terminar.",
                )
            except tk.TclError:
                pass
        self._esperar_respaldo_y_cerrar()

    def _esperar_respaldo_y_cerrar(self):
        if self._backup_en_curso.is_set():
            if self.winfo_exists():
                self.after(500, self._esperar_respaldo_y_cerrar)
            return
        self._cleanup()
        self._exit_status = "exit"
        if self.winfo_exists():
            self.destroy()

    def _cleanup(self):
        # El respaldo periódico también se cancela aquí: _cleanup corre al
        # salir y al cerrar sesión, y tras un cierre de sesión la aplicación
        # crea otra ventana mientras esta deja de existir (una tarea
        # programada viva fallaría contra la sesión de base de datos ya
        # cerrada).
        self._cancelar_respaldo_programado()
        for atributo in (
            "_clock_timer",
            "_eventos_poll_id",
            "_bandeja_poll_id",
            "_servidor_timer",
        ):
            identificador = getattr(self, atributo, None)
            if identificador is not None:
                try:
                    self.after_cancel(identificador)
                except Exception:
                    logger.debug("operación de interfaz ignorada", exc_info=True)
                setattr(self, atributo, None)
        # El icono de la bandeja pertenece a esta ventana: se retira antes de
        # destruirla para no dejar un icono huérfano en el área de notificación.
        try:
            if self._bandeja is not None:
                self._bandeja.close()
                self._bandeja = None
        except Exception:
            logger.debug("No se pudo cerrar la bandeja del servidor", exc_info=True)
        # Revocar los tokens académicos de esta sesión ANTES de cerrar la
        # sesión de base de datos. Sin esto, un token de notas seguía siendo
        # válido hasta ocho horas después de cerrar sesión (o de salir de la
        # aplicación) y la tabla de tokens crecía sin control.
        try:
            if self.current_user is not None:
                from src.services import TokenSesionService

                # Sesión propia: revocar no debe confirmar ni descartar
                # cambios pendientes de la sesión de la ventana.
                sesion_tokens = db_config.new_session()
                try:
                    TokenSesionService(sesion_tokens).revocar_usuario(int(self.current_user.id))
                finally:
                    db_config.close_session(sesion_tokens)
        except Exception:
            logger.debug("No se pudieron revocar los tokens de la sesión", exc_info=True)
        try:
            if self.session is not None:
                db_config.close_session(self.session)
                self.session = None
        except Exception:
            logger.debug("operación de interfaz ignorada", exc_info=True)

    # ------------------------------------------------------------------
    # Respaldos automáticos
    # ------------------------------------------------------------------
    def _cancelar_respaldo_programado(self) -> None:
        """Cancela la próxima verificación de respaldo pendiente"""
        if self._backup_timer is not None:
            try:
                self.after_cancel(self._backup_timer)
            except Exception:
                logger.debug("operación de interfaz ignorada", exc_info=True)
            self._backup_timer = None

    def _programar_respaldo_periodico(self):
        """Verifica el respaldo automático y se reprograma cada 30 minutos"""
        try:
            if self.winfo_exists():
                self._backup_timer = self.after(30 * 60 * 1000, self._programar_respaldo_periodico)
        except tk.TclError:
            logger.debug("La ventana se cerró al programar el respaldo periódico")
        try:
            self._verificar_respaldo_periodico()
        except Exception:
            logger.debug("operación de interfaz ignorada", exc_info=True)

    def _verificar_respaldo_periodico(self):
        """Crea un respaldo automático si ha transcurrido el intervalo configurado"""
        try:
            if not self.config_service.obtener_valor("backup_enabled", True):
                return
            intervalo_horas = max(
                1,
                int(self.config_service.obtener_valor("backup_interval_hours", 24) or 24),
            )

            from src.utils.backup_manager import get_backup_manager
            from src.utils.helpers import get_timestamp

            gestor = get_backup_manager()
            respaldos = gestor.list_backups()
            ultimo = respaldos[0]["timestamp"] if respaldos else None

            vencido = True
            if ultimo and len(str(ultimo)) == 15:
                ultima_fecha = datetime.strptime(str(ultimo), "%Y%m%d_%H%M%S")
                vencido = datetime.now() - ultima_fecha > timedelta(hours=intervalo_horas)

            if vencido and not self._backup_en_curso.is_set():
                # La copia (gzip + checksum + rotación) se ejecuta fuera del
                # hilo de la interfaz para no congelar la ventana.
                self._backup_en_curso.set()
                threading.Thread(
                    target=self._ejecutar_respaldo_en_segundo_plano,
                    args=(gestor, f"auto_{get_timestamp()}"),
                    name="respaldo-automatico",
                    daemon=True,
                ).start()
        except Exception:
            logger.debug("operación de interfaz ignorada", exc_info=True)

    def _ejecutar_respaldo_en_segundo_plano(self, gestor, nombre):
        """Ejecuta el respaldo fuera del hilo de la interfaz"""
        try:
            gestor.create_backup(nombre)
        except Exception:
            # Un fallo del respaldo automático deja los datos sin protección:
            # se registra como error y se avisa en la interfaz.
            logger.error("El respaldo automático falló", exc_info=True)
            self._notificar_hilo_principal("<<RespaldoAutomaticoFallado>>")
        else:
            self._notificar_hilo_principal("<<RespaldoAutomaticoCompletado>>")
        finally:
            self._backup_en_curso.clear()

    def _notificar_hilo_principal(self, evento: str) -> None:
        """Encola un evento virtual para que lo procese el hilo principal

        El hilo de fondo NO llama a ``event_generate`` (Tk no es seguro
        entre hilos): solo deposita el nombre del evento en una cola. El
        hilo principal la vacía en ``_procesar_eventos_hilo`` y genera el
        evento, que es cuando los manejadores ``bind`` se ejecutan.
        """
        try:
            self._eventos_hilo.put(str(evento))
        except Exception:
            logger.debug("no se pudo encolar el evento %s", evento)

    def _procesar_eventos_hilo(self) -> None:
        """Genera en el hilo principal los eventos encolados por los hilos"""
        self._eventos_poll_id = None
        while True:
            try:
                evento = self._eventos_hilo.get_nowait()
            except queue.Empty:
                break
            try:
                self.event_generate(evento, when="tail")
            except Exception:
                logger.debug("Evento %s omitido: ventana cerrada", evento)
        try:
            if self.winfo_exists():
                self._eventos_poll_id = self.after(100, self._procesar_eventos_hilo)
        except tk.TclError:
            logger.debug("La ventana se cerró durante el procesamiento de eventos")

    def _mostrar_aviso_respaldo(self, titulo: str, mensaje: str) -> None:
        """Muestra el resultado del respaldo automático desde el hilo principal"""
        try:
            if self.winfo_exists():
                messagebox.showinfo(titulo, mensaje)
        except tk.TclError:
            logger.debug("aviso de respaldo omitido: ventana cerrada")

    def _on_respaldo_completado(self) -> None:
        self._mostrar_aviso_respaldo(
            "Respaldo automático",
            "Se creó una copia de seguridad de la base de datos.",
        )

    def _on_respaldo_fallado(self) -> None:
        self._mostrar_aviso_respaldo(
            "Respaldo automático",
            "No se pudo crear la copia de seguridad.\n" "Revise el registro para más detalles.",
        )

    def run(self) -> str:
        """Ejecuta la ventana y devuelve 'logout' o 'exit' al cerrarse"""
        self.mainloop()
        return self._exit_status
