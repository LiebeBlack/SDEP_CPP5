"""
GUI Theme
Configuración visual global: paletas de apariencia (oscura/clara),
alta resolución (DPI) y estilos consistentes para widgets ttk
(Treeview, Combobox, menús desplegables).

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

# Paleta oscura (tema por defecto)
PALETA_OSCURA = {
    "fondo": "#1a1a1a",
    "panel": "#2b2b2b",
    "panel_hover": "#3a3a3a",
    "campo": "#3c3c3c",
    "texto": "white",
    "texto_suave": "#cccccc",
    "acento": "#1f538d",
    "borde": "#555555",
}

# Paleta clara (tema alternativo)
PALETA_CLARA = {
    "fondo": "#f2f2f2",
    "panel": "#e2e2e2",
    "panel_hover": "#d4d4d4",
    "campo": "#ffffff",
    "texto": "#1a1a1a",
    "texto_suave": "#555555",
    "acento": "#2a6fdb",
    "borde": "#aaaaaa",
}

# Paleta activa (se muta en caliente al cambiar de tema, de modo que los
# widgets creados después del cambio toman los colores nuevos)
COLORES = dict(PALETA_OSCURA)


def aplicar_modo_apariencia(modo: str = "Dark") -> None:
    """
    Aplica un modo de apariencia ("Dark" o "Light") a toda la aplicación.

    Cambia el modo de CustomTkinter (los widgets con colores por defecto
    se actualizan solos), actualiza la paleta global y reaplica los
    estilos ttk (tablas, combos, menús).

    Los widgets creados con colores explícitos tomados de la paleta
    (COLORES) se recoloran al recrearse; las ventanas principales
    reconfiguran su "chrome" (barra lateral, cabecera, barra de estado)
    inmediatamente después de llamar a esta función.
    """
    if not _CTK_DISPONIBLE:
        return
    modo = modo if modo in ("Dark", "Light", "System") else "Dark"
    ctk.set_appearance_mode(modo)
    if modo == "Light":
        paleta = PALETA_CLARA
    else:
        # "Dark" y "System" usan la paleta oscura (la interfaz está
        # diseñada sobre esta; el tema claro es una alternativa explícita)
        paleta = PALETA_OSCURA
    COLORES.clear()
    COLORES.update(paleta)
    try:
        import tkinter as tk
        raiz = tk._default_root
        if raiz is not None:
            configure_ttk_styles(raiz)
    except Exception:
        pass


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
    Aplica la paleta activa a Treeview y Combobox (ttk).

    Requiere que exista una ventana raíz Tk (se crea una por defecto si
    no se pasa una). Idempotente: se puede llamar al crear cada ventana
    y al cambiar de tema.
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
            foreground=COLORES["texto"],
            fieldbackground=COLORES["panel"],
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=COLORES["campo"],
            foreground=COLORES["texto"],
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", COLORES["acento"])],
            foreground=[("selected", "white")],
        )
        style.map(
            "Treeview.Heading",
            background=[("active", COLORES["panel_hover"])],
        )

        # --- Scrollbar vertical ---
        style.configure(
            "Vertical.TScrollbar",
            background=COLORES["campo"],
            troughcolor=COLORES["panel"],
            bordercolor=COLORES["panel"],
            arrowcolor=COLORES["texto_suave"],
        )

        # --- Combobox (selectores) ---
        style.configure(
            "TCombobox",
            fieldbackground=COLORES["campo"],
            background=COLORES["campo"],
            foreground=COLORES["texto"],
            arrowcolor=COLORES["texto_suave"],
            bordercolor=COLORES["borde"],
            lightcolor=COLORES["campo"],
            darkcolor=COLORES["campo"],
            selectbackground=COLORES["campo"],
            selectforeground=COLORES["texto"],
            padding=4,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORES["campo"]),
                             ("focus", COLORES["campo"])],
            foreground=[("readonly", COLORES["texto"])],
            selectbackground=[("readonly", COLORES["campo"])],
            selectforeground=[("readonly", COLORES["texto"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORES["campo"],
            foreground=COLORES["texto"],
            insertcolor=COLORES["texto"],
            bordercolor=COLORES["borde"],
            lightcolor=COLORES["campo"],
            darkcolor=COLORES["campo"],
        )

        # Lista desplegable del Combobox (es un Listbox interno de Tk).
        # IMPORTANTE: NO se configura la opción de fuente de esa lista
        # (*TCombobox*Listbox.font): en Tk 8.6 la creación del desplegable
        # falla con "expected integer but got UI" cuando la familia tiene
        # un nombre compuesto como "Segoe UI", y el menú no llega a
        # desplegarse nunca. El listbox hereda la fuente por defecto del
        # tema, que es legible en ambos modos.
        for clave, valor in (
            ("*TCombobox*Listbox.background", COLORES["campo"]),
            ("*TCombobox*Listbox.foreground", COLORES["texto"]),
            ("*TCombobox*Listbox.selectBackground", COLORES["acento"]),
            ("*TCombobox*Listbox.selectForeground", "white"),
            ("*TCombobox*Listbox.borderWidth", "1"),
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


def cancelar_after_pendientes(root) -> None:
    """
    Cancela los temporizadores `after` pendientes de una ventana

    CustomTkinter programa tareas internas (comprobación de DPI,
    animaciones de botones, redibujos). Si la ventana se destruye antes
    de que esas tareas se ejecuten, Tk las ejecuta igualmente sobre
    widgets ya eliminados y escribe en stderr líneas como
    "invalid command name ...". Se cancelan antes de destruir.
    """
    try:
        for id_tarea in root.tk.call("after", "info"):
            try:
                root.after_cancel(id_tarea)
            except Exception:
                continue
    except Exception:
        pass


def silenciar_errores_fondo(root) -> None:
    """
    Evita que los errores de fondo de Tcl (after internos) ensucien stderr

    Solo afecta a errores Tcl de segundo plano; los errores de los
    callbacks de Python se siguen manejando con report_callback_exception.
    """
    try:
        root.tk.call("proc", "bgerror", "msg", "")
    except Exception:
        pass


def setup_ui_raiz(root) -> None:
    """
    Aplicación completa de apariencia al crear una ventana raíz:
    estilos ttk, listbox de combos, escalado de CustomTkinter y
    limpieza de errores de fondo de Tcl.
    """
    enable_windows_dpi_awareness()
    configure_ttk_styles(root)
    aplicar_escalado_customtkinter(root)
    silenciar_errores_fondo(root)
