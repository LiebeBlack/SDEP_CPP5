"""
GUI Theme
Configuración visual global: alta resolución (DPI) y estilos oscuros
consistentes para widgets ttk (Treeview, Combobox, menús desplegables).

El módulo también centraliza las funciones de apariencia que antes vivían
duplicadas en main_window/login_window.
"""

import sys

try:
    import customtkinter as ctk
    _CTK_DISPONIBLE = True
except Exception:  # pragma: no cover
    _CTK_DISPONIBLE = False

_DPI_CONFIGURADO = False

COLORES = {
    "fondo": "#1a1a1a",
    "panel": "#2b2b2b",
    "campo": "#3c3c3c",
    "texto": "white",
    "texto_suave": "#cccccc",
    "acento": "#1f538d",
    "borde": "#555555",
}


def enable_windows_dpi_awareness() -> bool:
    """
    Activa la conciencia de DPI por monitor ANTES de crear cualquier
    ventana Tk.

    Sin esto, Windows escala en modo bitmap las ventanas Tk cuando el
    usuario tiene el escalado del sistema por encima del 100 %: la
    interfaz se ve borrosa, las proporciones del login se deforman y
    los textos pierden nitidez.

    Se ejecuta una sola vez por proceso; en sistemas que no son Windows
    no hace nada.
    """
    global _DPI_CONFIGURADO
    if _DPI_CONFIGURADO or sys.platform != "win32":
        return _DPI_CONFIGURADO
    _DPI_CONFIGURADO = True
    try:
        import ctypes

        # Per-Monitor v2 (Windows 10 1703+)
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
            return True
        except (AttributeError, OSError):
            pass
        # Per-Monitor (Windows 8.1+)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            return True
        except (AttributeError, OSError):
            pass
        # System DPI (Windows Vista+)
        ctypes.windll.user32.SetProcessDPIAware()
        return True
    except Exception:
        return False


def configure_ttk_styles(root=None) -> None:
    """
    Aplica el tema oscuro a Treeview y Combobox (ttk).

    Requiere que exista una ventana raíz Tk (se crea una por defecto si
    no se pasa una). Idempotente: se puede llamar al crear cada ventana.
    """
    try:
        from tkinter import ttk

        if root is None:
            root = ttk._default_root
        if root is None:
            import tkinter as tk
            root = tk._default_root
        if root is None:  # pragma: no cover
            return

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # --- Treeview (tablas) ---
        style.configure(
            "Treeview",
            background=COLORES["panel"],
            foreground="white",
            fieldbackground=COLORES["panel"],
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#3c3c3c",
            foreground="white",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", COLORES["acento"])],
            foreground=[("selected", "white")],
        )
        style.map("Treeview.Heading", background=[("active", "#4c4c4c")])

        # --- Scrollbar vertical ---
        style.configure(
            "Vertical.TScrollbar",
            background="#3c3c3c",
            troughcolor=COLORES["panel"],
            bordercolor=COLORES["panel"],
            arrowcolor="white",
        )

        # --- Combobox (selectores) ---
        style.configure(
            "TCombobox",
            fieldbackground=COLORES["campo"],
            background=COLORES["campo"],
            foreground="white",
            arrowcolor="#cccccc",
            bordercolor="#555555",
            lightcolor=COLORES["campo"],
            darkcolor=COLORES["campo"],
            selectbackground=COLORES["campo"],
            selectforeground="white",
            padding=4,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORES["campo"]),
                             ("focus", COLORES["campo"])],
            foreground=[("readonly", "white")],
            selectbackground=[("readonly", COLORES["campo"])],
            selectforeground=[("readonly", "white")],
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORES["campo"],
            foreground="white",
            insertcolor="white",
            bordercolor="#555555",
            lightcolor=COLORES["campo"],
            darkcolor=COLORES["campo"],
        )

        # Lista desplegable del Combobox (es un Listbox interno de Tk)
        for clave, valor in (
            ("*TCombobox*Listbox.background", COLORES["campo"]),
            ("*TCombobox*Listbox.foreground", "white"),
            ("*TCombobox*Listbox.selectBackground", COLORES["acento"]),
            ("*TCombobox*Listbox.selectForeground", "white"),
            ("*TCombobox*Listbox.borderWidth", "1"),
            ("*TCombobox*Listbox.font", "Segoe UI 10"),
        ):
            try:
                root.option_add(clave, valor)
            except Exception:
                continue
    except Exception:
        # Nunca impedir que la ventana se muestre por un problema de estilo
        pass


def aplicar_escalado_customtkinter(root=None) -> None:
    """
    Ajusta el escalado de CustomTkinter para que coincida con el factor
    DPI del sistema, evitando controles desproporcionados en pantallas
    de alta densidad.
    """
    if not _CTK_DISPONIBLE:
        return
    try:
        if root is None:
            import tkinter as tk
            root = tk._default_root
        if root is None:  # pragma: no cover
            return
        # tk devuelve puntos por pulgada; 72 pt = 100 % de escala
        factor = float(root.tk.call("tk", "scaling")) / 72.0
        if 0.5 <= factor <= 3.0:
            ctk.set_widget_scaling(max(0.8, min(1.25, factor)))
            ctk.set_window_scaling(max(0.8, min(1.25, factor)))
    except Exception:
        pass


def centrar_ventana(ventana, ancho: int, alto: int) -> None:
    """Centra una ventana en la pantalla (respetando la resolución real)"""
    try:
        ventana.update_idletasks()
        pantalla_ancho = ventana.winfo_screenwidth()
        pantalla_alto = ventana.winfo_screenheight()
        x = max(0, (pantalla_ancho - ancho) // 2)
        y = max(0, (pantalla_alto - alto) // 2)
        ventana.geometry(f"{ancho}x{alto}+{x}+{y}")
    except Exception:
        ventana.geometry(f"{ancho}x{alto}")


def setup_ui_raiz(root) -> None:
    """
    Aplicación completa de apariencia al crear una ventana raíz:
    estilos ttk, listbox de combos y escalado de CustomTkinter.
    """
    enable_windows_dpi_awareness()
    configure_ttk_styles(root)
    aplicar_escalado_customtkinter(root)
