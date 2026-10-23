"""
GUI Theme
Configuración visual global: paletas de apariencia (oscura/clara),
alta resolución (DPI) y estilos consistentes para widgets ttk
(Treeview, Combobox, menús desplegables).

El módulo también centraliza las funciones de apariencia que antes vivían
duplicadas en main_window/login_window.
"""

import logging
import sys

logger = logging.getLogger(__name__)

try:
    import customtkinter as ctk

    _CTK_DISPONIBLE = True
except Exception:  # pragma: no cover
    _CTK_DISPONIBLE = False

_DPI_CONFIGURADO = False
_DPI_INTENTADO = False

# Paleta oscura (tema por defecto) - profundidad, no plana
PALETA_OSCURA = {
    "fondo": "#0f172a",  # azul muy oscuro (slate-900)
    "panel": "#1e293b",  # slate-800 (tarjetas, paneles)
    "panel_hover": "#334155",  # slate-700 (hover)
    "campo": "#334155",  # slate-700 (campos de entrada)
    "campo_fondo": "#1e293b",  # slate-800 (fondo de campos)
    "texto": "#f8fafc",  # slate-50 (texto principal)
    "texto_suave": "#94a3b8",  # slate-400 (texto secundario)
    "acento": "#3b82f6",  # blue-500 (acento Windows 11)
    "acento_hover": "#60a5fa",  # blue-400 (acento hover)
    "borde": "#475569",  # slate-600 (bordes sutiles)
    "sombra": "#000000",  # sombra (simulada con capas)
    "exito": "#10b981",  # emerald-500
    "advertencia": "#f59e0b",  # amber-500
    "error": "#ef4444",  # red-500
}

# Paleta clara (tema alternativo) - estilo Windows 11 claro
PALETA_CLARA = {
    "fondo": "#f8fafc",  # slate-50
    "panel": "#ffffff",  # blanco puro (tarjetas elevadas)
    "panel_hover": "#f1f5f9",  # slate-100 (hover)
    "campo": "#ffffff",  # blanco (campos de entrada)
    "campo_fondo": "#ffffff",  # blanco (fondo de campos)
    "texto": "#0f172a",  # slate-900 (texto principal)
    "texto_suave": "#64748b",  # slate-500 (texto secundario)
    "acento": "#2563eb",  # blue-600 (acento Windows 11)
    "acento_hover": "#3b82f6",  # blue-500 (acento hover)
    "borde": "#cbd5e1",  # slate-200 (bordes sutiles)
    "sombra": "#000000",  # sombra (simulada con capas)
    "exito": "#059669",  # emerald-600
    "advertencia": "#d97706",  # amber-600
    "error": "#dc2626",  # red-600
}

# Paleta activa (se muta en caliente al cambiar de tema, de modo que los
# widgets creados después del cambio toman los colores nuevos)
COLORES = dict(PALETA_OSCURA)

# Radio de esquinas redondeadas (estilo Windows 11: 8-12px)
RADIO_PEQUEÑO = 6
RADIO_MEDIO = 10
RADIO_GRANDE = 14

# Grosor de borde sutil (no plano, con definición)
BORDE_GRUESO = 1

# Familia de fuente segura para CustomTkinter (se resuelve en el primer
# setup_ui_raiz; antes de eso se usa "Arial" como fallback).
FUENTE_SEGURA: str = "Arial"


def aplicar_modo_apariencia(modo: str = "Light") -> None:
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
    # Un valor inválido o corrupto cae al tema claro (el de la pantalla
    # de inicio por defecto) en lugar de romper la configuración visual.
    modo = modo if modo in ("Dark", "Light", "System") else "Light"
    ctk.set_appearance_mode(modo)
    # Con "System" el modo real lo decide el sistema operativo: se pregunta a
    # CustomTkinter después de aplicarlo en lugar de asumir oscuro. Antes, un
    # equipo con Windows en modo claro y la preferencia "System" recibía la
    # paleta oscura mientras los controles nativos se pintaban claros, y la
    # interfaz quedaba con mitades de dos temas.
    modo_efectivo = ctk.get_appearance_mode()
    if modo_efectivo == "Light":
        paleta = PALETA_CLARA
    else:
        paleta = PALETA_OSCURA
    COLORES.clear()
    COLORES.update(paleta)
    try:
        import tkinter as tk

        raiz = getattr(tk, "_default_root", None)
        if raiz is not None:
            configure_ttk_styles(raiz)
    except Exception:
        logger.debug("ajuste visual ignorado", exc_info=True)


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
    global _DPI_CONFIGURADO, _DPI_INTENTADO
    if _DPI_INTENTADO or sys.platform != "win32":
        return _DPI_CONFIGURADO
    _DPI_INTENTADO = True
    try:
        import ctypes

        # Per-Monitor v2 (Windows 10 1703+)
        try:
            if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
                _DPI_CONFIGURADO = True
                return True
        except (AttributeError, OSError, ctypes.ArgumentError):
            logger.debug("Per-Monitor v2 no disponible; probando el siguiente nivel")
        # Per-Monitor (Windows 8.1+)
        try:
            if ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0:
                _DPI_CONFIGURADO = True
                return True
        except (AttributeError, OSError, ctypes.ArgumentError):
            logger.debug("Per-Monitor no disponible; probando el siguiente nivel")
        # System DPI (Windows Vista+)
        _DPI_CONFIGURADO = bool(ctypes.windll.user32.SetProcessDPIAware())
        return _DPI_CONFIGURADO
    except (AttributeError, OSError, ImportError) as error:
        logger.debug("No se pudo configurar DPI awareness: %s", error, exc_info=True)
        return False


def familia_fuente_tk(nombre: str = "TkDefaultFont", fallback: str = "Arial", root=None) -> str:
    """
    Resuelve la familia real de una fuente nombrada de Tk

    Si la fuente no existe o Tk aún no tiene raíz, devuelve el fallback
    del sistema operativo en lugar de lanzar un error de renderizado.
    """
    try:
        import tkinter.font as tkfont

        fuente = tkfont.nametofont(nombre, root) if root is not None else tkfont.nametofont(nombre)
        familia = fuente.actual("family")
        return familia or fallback
    except Exception:
        return fallback


def configurar_fuentes_seguras() -> str:
    """
    Devuelve una familia de fuente segura para CustomTkinter.

    Resuelve la fuente del sistema en lugar de usar nombres compuestos
    (como "Segoe UI") que en Tk 8.6 pueden disparar
    "expected integer but got UI" al renderizar desplegables o entradas.
    Con esta fuente se garantiza que el texto se muestre en cualquier
    equipo sin errores de fuente de CustomTkinter.
    """
    global FUENTE_SEGURA
    try:
        import tkinter as tk

        raiz = getattr(tk, "_default_root", None)
        if raiz is None:
            raiz = tk.Tk()
            raiz.withdraw()
        try:
            fuente = familia_fuente_tk("TkDefaultFont", "Arial", raiz)
            FUENTE_SEGURA = fuente
        finally:
            try:
                raiz.destroy()
            except Exception:
                pass
        return FUENTE_SEGURA
    except Exception:
        FUENTE_SEGURA = "Arial"
        return "Arial"


def habilitar_scroll_rueda(widget) -> None:
    """Activa el desplazamiento con rueda/trackpad en un widget con yview."""
    acumulado = {"vertical": 0, "horizontal": 0}

    def desplazar(evento, eje: str) -> str:
        try:
            if not getattr(widget, "winfo_exists", lambda: True)():
                return "break"
            delta = getattr(evento, "delta", 0)
            if delta:
                if sys.platform == "darwin":
                    pasos = 1 if delta > 0 else -1
                else:
                    if (acumulado[eje] > 0 and delta < 0) or (acumulado[eje] < 0 and delta > 0):
                        acumulado[eje] = 0
                    acumulado[eje] += delta
                    pasos = int(acumulado[eje] / 40)
                    if pasos != 0:
                        acumulado[eje] -= pasos * 40
                if pasos != 0:
                    vista = getattr(widget, "xview" if eje == "horizontal" else "yview", None)
                    if vista is not None:
                        vista("scroll", -pasos, "units")
            else:
                numero = getattr(evento, "num", None)
                if numero not in (4, 5):
                    return "break"
                pasos = -1 if numero == 4 else 1
                vista = getattr(widget, "xview" if eje == "horizontal" else "yview", None)
                if vista is not None:
                    vista("scroll", pasos, "units")
        except Exception:
            logger.debug("Desplazamiento local ignorado", exc_info=True)
        return "break"

    try:
        widget.bind("<MouseWheel>", lambda evento: desplazar(evento, "vertical"), add="+")
        widget.bind(
            "<Shift-MouseWheel>",
            lambda evento: desplazar(evento, "horizontal"),
            add="+",
        )
        widget.bind("<Button-4>", lambda evento: desplazar(evento, "vertical"), add="+")
        widget.bind("<Button-5>", lambda evento: desplazar(evento, "vertical"), add="+")
        widget.bind(
            "<Shift-Button-4>",
            lambda evento: desplazar(evento, "horizontal"),
            add="+",
        )
        widget.bind(
            "<Shift-Button-5>",
            lambda evento: desplazar(evento, "horizontal"),
            add="+",
        )
    except Exception:
        logger.debug("No se pudo habilitar scroll en el widget", exc_info=True)


def _tiene_scroll_propio(widget, secuencia: str) -> bool:
    """
    ¿Ese widget (o su clase Tk) ya atiende esa rueda por su cuenta?

    Las clases estándar (Text, Listbox, ttk.Treeview) traen su propio binding
    de rueda. El binding global corre al final de la cadena de *bindtags*, así
    que sin esta comprobación el mismo giro desplazaría el widget dos veces.
    Ante cualquier duda se responde True: es preferible dejar el
    desplazamiento nativo a duplicarlo.
    """
    try:
        if widget.bind(secuencia):
            return True
        return bool(widget.bind_class(widget.winfo_class(), secuencia))
    except Exception:
        logger.debug("No se pudo comprobar el scroll nativo del widget", exc_info=True)
        return True


def habilitar_scroll_global(root) -> None:
    """
    Activa el desplazamiento universal con rueda de ratón y trackpad/touchpad
    para toda la interfaz (Treeviews, Canvas, CTkScrollableFrame, Text, Listbox).

    Detecta el widget bajo el cursor (o su contenedor desplazable más cercano)
    y aplica el desplazamiento vertical u horizontal sin requerir foco previo
    ni producir excepciones si el widget se destruye. Los widgets que ya traen
    su propio binding de rueda se dejan intactos para no desplazarlos dos
    veces.
    """
    if root is None:
        return
    acumulado = {"vertical": 0, "horizontal": 0}

    def _scroll_global(evento, eje: str = "vertical"):
        try:
            x_root = getattr(evento, "x_root", None)
            y_root = getattr(evento, "y_root", None)
            if x_root is None or y_root is None:
                return

            w = root.winfo_containing(x_root, y_root)
            if w is None:
                return

            delta = getattr(evento, "delta", 0)
            numero = getattr(evento, "num", None)
            if delta:
                secuencia = "<Shift-MouseWheel>" if eje == "horizontal" else "<MouseWheel>"
            elif numero in (4, 5):
                secuencia = (
                    f"<Shift-Button-{numero}>" if eje == "horizontal" else f"<Button-{numero}>"
                )
            else:
                return
            if _tiene_scroll_propio(w, secuencia):
                return

            target = None
            curr = w
            while curr is not None:
                if hasattr(curr, "_parent_canvas"):
                    target = curr._parent_canvas
                    break
                attr = "xview" if eje == "horizontal" else "yview"
                if hasattr(curr, attr) and callable(getattr(curr, attr)):
                    target = curr
                    break
                curr = getattr(curr, "master", None)

            if target is None:
                return

            if delta:
                if sys.platform == "darwin":
                    pasos = 1 if delta > 0 else -1
                else:
                    if (acumulado[eje] > 0 and delta < 0) or (acumulado[eje] < 0 and delta > 0):
                        acumulado[eje] = 0
                    acumulado[eje] += delta
                    pasos = int(acumulado[eje] / 40)
                    if pasos != 0:
                        acumulado[eje] -= pasos * 40
                if pasos != 0:
                    vista = getattr(target, "xview" if eje == "horizontal" else "yview", None)
                    if vista is not None:
                        vista("scroll", -pasos, "units")
            else:
                pasos = -1 if numero == 4 else 1
                vista = getattr(target, "xview" if eje == "horizontal" else "yview", None)
                if vista is not None:
                    vista("scroll", pasos, "units")
            return "break"
        except Exception:
            logger.debug("Desplazamiento global ignorado", exc_info=True)

    try:
        root.bind_all("<MouseWheel>", lambda e: _scroll_global(e, "vertical"), add="+")
        root.bind_all("<Shift-MouseWheel>", lambda e: _scroll_global(e, "horizontal"), add="+")
        root.bind_all("<Button-4>", lambda e: _scroll_global(e, "vertical"), add="+")
        root.bind_all("<Button-5>", lambda e: _scroll_global(e, "vertical"), add="+")
        root.bind_all("<Shift-Button-4>", lambda e: _scroll_global(e, "horizontal"), add="+")
        root.bind_all("<Shift-Button-5>", lambda e: _scroll_global(e, "horizontal"), add="+")
    except Exception:
        logger.debug("No se pudo registrar scroll global", exc_info=True)


def configure_ttk_styles(root=None) -> None:
    """
    Aplica la paleta activa a Treeview y Combobox (ttk), incluidos los
    Listbox internos de los desplegables.

    Requiere que exista una ventana raíz Tk (se crea una por defecto si
    no se pasa una). Idempotente: se puede llamar al crear cada ventana
    y al cambiar de tema.
    """
    try:
        from tkinter import ttk

        if root is None:
            root = getattr(ttk, "_default_root", None)
        if root is None:
            import tkinter as tk

            root = getattr(tk, "_default_root", None)
        if root is None:  # pragma: no cover
            return

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except Exception:
            logger.debug("ajuste visual ignorado", exc_info=True)

        # --- Treeview (tablas) ---
        # La familia de fuente se resuelve desde la fuente por defecto de
        # Tk en lugar de fijar "Segoe UI": en equipos donde esa familia no
        # está instalada, Tk la sustituye silenciosamente y el renderizado
        # se degrada; en Tk 8.6 un nombre compuesto ("Segoe UI") en ciertos
        # contextos de fuente dispara el error "expected integer but got UI"
        # al desplegar los combos. Con la familia resuelta se garantiza que
        # la fuente exista siempre en cualquier sistema.
        try:
            from tkinter import font as tkfont

            _fuente_familia = tkfont.nametofont("TkDefaultFont", root).actual("family")
            _fuente_tamano = tkfont.nametofont("TkDefaultFont", root).actual("size")
            _fuente_tabla = (_fuente_familia, _fuente_tamano)
            _fuente_encabezado = (_fuente_familia, _fuente_tamano, "bold")
        except Exception:
            _fuente_tabla = None
            _fuente_encabezado = None

        style.configure(
            "Treeview",
            background=COLORES["panel"],
            foreground=COLORES["texto"],
            fieldbackground=COLORES["panel"],
            rowheight=28,
            borderwidth=0,
        )
        if _fuente_tabla is not None:
            style.configure("Treeview", font=_fuente_tabla)

        style.configure(
            "Treeview.Heading",
            background=COLORES["campo"],
            foreground=COLORES["texto"],
            relief="flat",
            borderwidth=0,
        )
        if _fuente_encabezado is not None:
            style.configure("Treeview.Heading", font=_fuente_encabezado)
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
        style.configure(
            "Horizontal.TScrollbar",
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
            fieldbackground=[("readonly", COLORES["campo"]), ("focus", COLORES["campo"])],
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
        _recolorear_listboxes(root)
    except Exception:
        # Nunca impedir que la ventana se muestre por un problema de estilo
        logger.debug("No se pudieron registrar los estilos ttk", exc_info=True)


def _recolorear_listboxes(root) -> None:
    """Actualiza también las listas internas de desplegables ya creados."""
    opciones = (
        "-background",
        COLORES["campo"],
        "-foreground",
        COLORES["texto"],
        "-selectbackground",
        COLORES["acento"],
        "-selectforeground",
        "white",
        "-highlightbackground",
        COLORES["borde"],
        "-highlightcolor",
        COLORES["acento"],
    )
    pendientes = [root._w]
    while pendientes:
        padre = pendientes.pop()
        try:
            hijos = root.tk.splitlist(root.tk.call("winfo", "children", padre))
        except Exception:
            logger.debug("No se pudieron consultar los widgets hijos de %s", padre, exc_info=True)
            continue
        for hijo in hijos:
            try:
                if root.tk.call("winfo", "class", hijo) == "Listbox":
                    root.tk.call(hijo, "configure", *opciones)
                pendientes.append(hijo)
            except Exception:
                logger.debug("No se pudo actualizar el color del widget %s", hijo, exc_info=True)


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

            root = getattr(tk, "_default_root", None)
        if root is None:  # pragma: no cover
            return
        # tk devuelve puntos por pulgada; 72 pt = 100 % de escala
        scaling_raw = float(root.tk.call("tk", "scaling"))
        if scaling_raw <= 0:
            return
        factor = scaling_raw / 72.0
        if 0.5 <= factor <= 3.0:
            ctk.set_widget_scaling(max(0.8, min(1.25, factor)))
            ctk.set_window_scaling(max(0.8, min(1.25, factor)))
    except Exception:
        logger.debug("ajuste visual ignorado", exc_info=True)


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
        logger.debug("ajuste visual ignorado", exc_info=True)


def silenciar_errores_fondo(root) -> None:
    """
    Evita que los errores de fondo de Tcl (after internos) ensucien stderr

    Solo afecta a errores Tcl de segundo plano; los errores de los
    callbacks de Python se siguen manejando con report_callback_exception.
    """
    try:
        root.tk.call("proc", "bgerror", "msg", "")
    except Exception:
        logger.debug("ajuste visual ignorado", exc_info=True)


def configurar_report_callback_exception(root) -> None:
    """
    Muestra y registra los errores que ocurren dentro de callbacks Tk.

    Sin este manejador, una excepción dentro de un callback (botón, after,
    evento) solo se imprime en la consola y la ventana puede quedar en
    negro o congelada sin explicación. Con él, el error se registra en la
    auditoría, se imprime y se muestra al usuario, de modo que nunca hay
    un fallo silencioso.
    """
    try:

        def _manejador(tipo, valor, tb):
            try:
                from src.utils.audit_logger import get_audit_logger

                audit = get_audit_logger()
                if audit:
                    audit.log_error(valor, context={"operation": "callback_interfaz"})
            except Exception:
                logger.debug("ajuste visual ignorado", exc_info=True)
            try:
                import traceback

                traceback.print_exception(tipo, valor, tb)
            except Exception:
                logger.debug("ajuste visual ignorado", exc_info=True)
            try:
                from tkinter import messagebox

                messagebox.showerror(
                    "Error de interfaz",
                    f"Ocurrió un error en la interfaz:\n{valor}\n\n"
                    "El error quedó registrado en la auditoría del sistema.",
                )
            except Exception:
                logger.debug("ajuste visual ignorado", exc_info=True)

        root.report_callback_exception = _manejador
    except Exception:
        logger.debug("ajuste visual ignorado", exc_info=True)


def setup_ui_raiz(root) -> None:
    """
    Aplicación completa de apariencia al crear una ventana raíz:
    estilos ttk, listbox de combos, escalado de CustomTkinter,
    desplazamiento con rueda/touchpad para toda la interfaz,
    limpieza de errores de fondo de Tcl y manejador de errores de
    callbacks (nunca congelar en silencio).
    """
    enable_windows_dpi_awareness()
    configurar_fuentes_seguras()
    configure_ttk_styles(root)
    aplicar_escalado_customtkinter(root)
    habilitar_scroll_global(root)
    silenciar_errores_fondo(root)
    configurar_report_callback_exception(root)


def estilo_tarjeta_moderna() -> dict:
    """
    Devuelve los kwargs de estilo para una tarjeta moderna (Windows 11):

    - Esquinas redondeadas (RADIO_GRANDE)
    - Fondo de panel (elevado sobre el fondo principal)
    - Borde sutil (BORDE_GRUESO con COLORES["borde"])
    - Sin relieve plano: la elevación se sugiere con color y borde, no con sombra
      pesada (CustomTkinter no soporta sombras reales).
    """
    return {
        "corner_radius": RADIO_GRANDE,
        "fg_color": COLORES["panel"],
        "border_width": BORDE_GRUESO,
        "border_color": COLORES["borde"],
    }


def estilo_boton_moderno(variante: str = "primario") -> dict:
    """
    Devuelve los kwargs de estilo para un botón moderno (Windows 11):

    Variantes:
      - "primario": fondo acento, texto blanco, hover acento_hover
      - "secundario": fondo transparente, borde acento, texto acento
      - "fantasma": fondo transparente, sin borde, texto suave, hover panel_hover
    """
    base = {
        "corner_radius": RADIO_MEDIO,
        "height": 36,
        "border_width": 0,
    }
    if variante == "primario":
        base.update(
            fg_color=COLORES["acento"],
            hover_color=COLORES["acento_hover"],
            text_color="white",
            border_color=COLORES["acento"],
        )
    elif variante == "secundario":
        base.update(
            fg_color="transparent",
            hover_color=COLORES["panel_hover"],
            text_color=COLORES["texto"],
            border_color=COLORES["borde"],
            border_width=1,
        )
    else:  # fantasma
        base.update(
            fg_color="transparent",
            hover_color=COLORES["panel_hover"],
            text_color=COLORES["texto_suave"],
        )
    return base


def estilo_campo_moderno() -> dict:
    """
    Devuelve los kwargs de estilo para un campo de entrada moderno.
    """
    return {
        "corner_radius": RADIO_MEDIO,
        "fg_color": COLORES["campo_fondo"],
        "border_color": COLORES["borde"],
        "border_width": 1,
        "text_color": COLORES["texto"],
    }


def estilo_combo_moderno() -> dict:
    """
    Devuelve los kwargs de estilo para un combobox moderno.
    """
    return {
        "corner_radius": RADIO_MEDIO,
        "fg_color": COLORES["campo_fondo"],
        "border_color": COLORES["borde"],
        "border_width": 1,
        "text_color": COLORES["texto"],
        "button_color": COLORES["acento"],
        "button_hover_color": COLORES["acento_hover"],
    }
