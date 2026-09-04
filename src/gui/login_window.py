"""
Login Window
Ventana de inicio de sesión del sistema
"""

import tkinter as tk
from typing import Optional

import customtkinter as ctk
from tkinter import messagebox

from src.config import db_config
from src.models import Usuario
from src.services.auth_service import (
    AuthService,
    DEFAULT_ADMIN_PASSWORD,
)
from src.utils.helpers import mantener_ventana_al_frente
from src.utils.security import SecurityValidator
from src.gui.theme import (
    enable_windows_dpi_awareness,
    setup_ui_raiz,
    centrar_ventana,
    cancelar_after_pendientes,
    aplicar_modo_apariencia,
    COLORES,
)


class CambiarPasswordDialog(ctk.CTkToplevel):
    """Diálogo para cambiar la contraseña (obligatorio en el primer acceso)"""

    def __init__(self, parent, auth_service: AuthService, usuario: Usuario):
        super().__init__(parent)
        self.auth_service = auth_service
        self.usuario = usuario
        self.cambiado = False

        self.title("Cambiar Contraseña")
        self.geometry("480x330")
        self.resizable(False, False)
        mantener_ventana_al_frente(self)
        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(parent)

        self._create_widgets()

    def _create_widgets(self):
        container = ctk.CTkFrame(self, fg_color=COLORES["panel"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            container,
            text="Debe cambiar la contraseña inicial\nantes de continuar",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORES["texto"],
            justify="center",
        ).pack(pady=(10, 20))

        ctk.CTkLabel(
            container,
            text="Usuario:",
            text_color=COLORES["texto"],
            anchor="w",
        ).pack(fill="x", padx=5)
        self.user_label = ctk.CTkLabel(
            container,
            text=self.usuario.username,
            text_color=COLORES["texto_suave"],
            anchor="w",
        )
        self.user_label.pack(fill="x", padx=5, pady=(0, 10))

        ctk.CTkLabel(
            container, text="Nueva contraseña:", text_color=COLORES["texto"], anchor="w"
        ).pack(fill="x", padx=5)
        self.new_pass = ctk.CTkEntry(
            container, show="*", fg_color=COLORES["campo"], text_color=COLORES["texto"])
        self.new_pass.pack(fill="x", padx=5, pady=(2, 8))

        ctk.CTkLabel(
            container, text="Confirmar contraseña:", text_color=COLORES["texto"], anchor="w"
        ).pack(fill="x", padx=5)
        self.confirm_pass = ctk.CTkEntry(
            container, show="*", fg_color=COLORES["campo"], text_color=COLORES["texto"])
        self.confirm_pass.pack(fill="x", padx=5, pady=(2, 12))

        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        save_btn = ctk.CTkButton(
            btn_frame, text="Guardar", command=self._on_save)
        save_btn.pack(side="right", padx=5)

        cancel_btn = ctk.CTkButton(
            btn_frame, text="Cancelar", fg_color="#8a3b3b",
            hover_color="#a04a4a", command=self._on_cancel)
        cancel_btn.pack(side="right", padx=5)

    def _on_save(self):
        nueva = self.new_pass.get()
        confirmacion = self.confirm_pass.get()
        if not nueva:
            messagebox.showerror("Error", "Debe ingresar la nueva contraseña")
            return
        if nueva != confirmacion:
            messagebox.showerror("Error", "Las contraseñas no coinciden")
            return
        try:
            self.auth_service.cambiar_password(self.usuario, nueva)
            self.cambiado = True
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _on_cancel(self):
        self.destroy()


class LoginWindow(ctk.CTk):
    """Ventana de inicio de sesión"""

    def __init__(self):
        enable_windows_dpi_awareness()
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        super().__init__()
        setup_ui_raiz(self)

        self.user: Optional[Usuario] = None
        self._session_activa = None

        # Respetar el modo de apariencia guardado por el usuario
        try:
            from src.services.configuracion_service import ConfiguracionService
            session = db_config.get_session()
            try:
                modo = ConfiguracionService(session).obtener_valor(
                    "apariencia_modo", "Dark") or "Dark"
            finally:
                db_config.close_session(session)
            aplicar_modo_apariencia(modo)
        except Exception:
            aplicar_modo_apariencia("Dark")

        self.title("Iniciar Sesión — Sistema de Gestión de Personal")
        self.resizable(False, False)
        self.configure(fg_color=COLORES["fondo"])
        centrar_ventana(self, 880, 480)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_ui()
        self._show_initial_hint()

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _create_ui(self):
        # Panel izquierdo: marca
        brand = ctk.CTkFrame(self, width=340, corner_radius=0, fg_color="#22334d")
        brand.pack(side="left", fill="y")
        brand.pack_propagate(False)

        ctk.CTkLabel(
            brand,
            text="SISTEMA DE GESTIÓN\nDE PERSONAL Y NÓMINA",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white",
            justify="center",
        ).pack(expand=True, padx=20)

        ctk.CTkLabel(
            brand,
            text="Instituciones Educativas",
            font=ctk.CTkFont(size=12),
            text_color="#aabbdd",
        ).pack(pady=(0, 30))

        # Panel derecho: formulario (colores de la paleta activa para que
        # las etiquetas sigan siendo legibles al cambiar a tema claro)
        form = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORES["fondo"])
        form.pack(side="right", fill="both", expand=True)

        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner,
            text="Iniciar Sesión",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORES["texto"],
        ).pack(pady=(0, 20))

        ctk.CTkLabel(
            inner, text="Usuario:", text_color=COLORES["texto"], anchor="w"
        ).pack(fill="x")
        self.username_entry = ctk.CTkEntry(
            inner, width=320, height=38, fg_color=COLORES["panel"],
            text_color=COLORES["texto"], placeholder_text="Nombre de usuario")
        self.username_entry.pack(pady=(4, 12))
        self.username_entry.bind("<Return>", lambda e: self._focus_password())

        ctk.CTkLabel(
            inner, text="Contraseña:", text_color=COLORES["texto"], anchor="w"
        ).pack(fill="x")
        self.password_entry = ctk.CTkEntry(
            inner, width=320, height=38, show="*", fg_color=COLORES["panel"],
            text_color=COLORES["texto"], placeholder_text="Contraseña")
        self.password_entry.pack(pady=(4, 16))
        self.password_entry.bind("<Return>", lambda e: self._on_login())

        login_btn = ctk.CTkButton(
            inner,
            text="Ingresar",
            width=320,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_login,
        )
        login_btn.pack(pady=(4, 10))

        self.hint_label = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#ccaa44",
            wraplength=320,
            justify="center",
        )
        self.hint_label.pack(pady=(6, 0))

        self.username_entry.focus_set()

    def _focus_password(self):
        self.password_entry.focus_set()

    def _show_initial_hint(self):
        """Muestra las credenciales iniciales solo mientras no se hayan cambiado"""
        try:
            session = db_config.get_session()
            try:
                auth = AuthService(session)
                admin = auth.usuario_por_username("admin")
                if admin is not None and admin.debe_cambiar_password:
                    if SecurityValidator.verify_password(
                        DEFAULT_ADMIN_PASSWORD, admin.password_hash
                    ):
                        self.hint_label.configure(
                            text="Primer acceso: usuario 'admin' · contraseña "
                            "'admin123'. Deberá cambiarla al ingresar."
                        )
            finally:
                db_config.close_session(session)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------
    def _on_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Debe ingresar usuario y contraseña")
            return

        session = db_config.get_session()
        try:
            auth = AuthService(session)
            usuario = auth.autenticar(username, password)
            if usuario is None:
                messagebox.showerror("Error", "No se pudo iniciar sesión")
                return

            # Primer acceso: obligar a cambiar la contraseña inicial
            if usuario.debe_cambiar_password:
                dialog = CambiarPasswordDialog(self, auth, usuario)
                self.wait_window(dialog)
                if not dialog.cambiado:
                    messagebox.showwarning(
                        "Acceso cancelado",
                        "Debe cambiar la contraseña inicial para continuar",
                    )
                    self.password_entry.delete(0, tk.END)
                    return

            self.user = usuario
            self._session_activa = session
            cancelar_after_pendientes(self)
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Error de Autenticación", str(e))
            self.password_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al iniciar sesión: {str(e)}")
        finally:
            # La sesión permanece abierta si el inicio de sesión fue exitoso:
            # el Usuario autenticado sigue ligado a ella y la ventana principal
            # (misma sesión scoped) la cerrará al salir o cerrar sesión.
            if self.user is None:
                db_config.close_session(session)

    def _on_close(self):
        self.user = None
        cancelar_after_pendientes(self)
        self.destroy()

    def run(self) -> Optional[Usuario]:
        """Muestra la ventana y devuelve el usuario autenticado o None"""
        self.mainloop()
        return self.user
