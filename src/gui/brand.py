"""
Identidad visual del producto (marca SDEP)

Un único lugar define el nombre, el lema y el isotipo. Antes cada ventana
repetía cadenas con grafías distintas ("Sistema de Gestión de Personal",
"SGP" en el icono, "SDEP" en el instalador y en la app Android), de modo que
la marca cambiaba según dónde se mirara.

El isotipo se dibuja con un Canvas de Tk: no depende de archivos externos,
toma los colores de la paleta activa (así que se recolorea al cambiar entre
tema claro y oscuro) y funciona igual en el `.exe`, en el APK y en un equipo
sin el paquete de imágenes.
"""

import logging
import os
import tkinter as tk

import customtkinter as ctk

from src.gui.theme import COLORES, familia_fuente_tk
from src.utils.helpers import get_resource_path

logger = logging.getLogger(__name__)

# --- Identidad ------------------------------------------------------------
NOMBRE_CORTO = "SDEP"
NOMBRE_PRODUCTO = "SDEP Escritorio"
NOMBRE_COMPLETO = "Sistema de Gestión de Personal"
LEMA = "Personal, nómina y calificaciones para instituciones educativas"

# Icono de la aplicación. Se empaqueta como dato de PyInstaller, de ahí que
# la ruta se resuelva con get_resource_path (desarrollo y .exe).
_RUTA_ICONO = "assets/app.ico"


def ruta_icono() -> str:
    """Ruta del icono de la aplicación, o cadena vacía si no se puede resolver."""
    try:
        return get_resource_path(_RUTA_ICONO)
    except Exception:
        logger.debug("No se pudo resolver la ruta del icono", exc_info=True)
        return ""


def aplicar_icono(ventana) -> bool:
    """
    Aplica el icono de la aplicación a una ventana Tk.

    En Windows se usa ``iconbitmap(default=...)``: Tk guarda ese icono como
    predeterminado de la aplicación, así que también lo heredan los
    ``CTkToplevel`` que se abren después (diálogos de alta, edición, reportes).
    En otros sistemas el .ico no es válido y el intento se descarta sin
    interrumpir el arranque.
    """
    ruta = ruta_icono()
    if not ruta or not os.path.exists(ruta):
        logger.debug("Icono de la aplicación no encontrado: %s", ruta)
        return False
    for argumento in ({"default": ruta}, {}):
        try:
            ventana.iconbitmap(**argumento)
            return True
        except tk.TclError:
            continue
        except Exception:
            logger.debug("No se pudo aplicar el icono de la aplicación", exc_info=True)
            return False
    logger.debug("El sistema no admite el icono .ico de la aplicación")
    return False


def aplicar_identidad_ventana(ventana, titulo: str | None = None) -> None:
    """Aplica icono y título con la marca a una ventana (diálogos incluidos)."""
    aplicar_icono(ventana)
    if titulo:
        ventana.title(f"{titulo} · {NOMBRE_CORTO}")


def _oscurecer(color: str, factor: float = 0.75) -> str:
    """Mezcla un color ``#rrggbb`` con negro (factor entre 0 y 1)."""
    try:
        valor = color.lstrip("#")
        if len(valor) != 6:
            return color
        rojo, verde, azul = (int(valor[i : i + 2], 16) for i in (0, 2, 4))
        return "#{:02x}{:02x}{:02x}".format(
            int(rojo * factor), int(verde * factor), int(azul * factor)
        )
    except (TypeError, ValueError):
        return color


def _cuadrado_redondeado(lienzo, x0, y0, x1, y1, radio: int, relleno: str) -> None:
    """
    Dibuja un cuadrado redondeado relleno sin depender de Pillow.

    Se compone de dos rectángulos cruzas y cuatro arcos en «pieslice»; es el
    mismo truco que usa el resto de la interfaz para las esquinas de 8-12 px.
    """
    radio = int(max(0, min(radio, (x1 - x0) / 2, (y1 - y0) / 2)))
    if radio <= 0:
        lienzo.create_rectangle(x0, y0, x1, y1, fill=relleno, outline=relleno)
        return
    lienzo.create_rectangle(x0 + radio, y0, x1 - radio, y1, fill=relleno, outline=relleno)
    lienzo.create_rectangle(x0, y0 + radio, x1, y1 - radio, fill=relleno, outline=relleno)
    for arco in (
        (x0, y0, x0 + 2 * radio, y0 + 2 * radio, 90),
        (x1 - 2 * radio, y0, x1, y0 + 2 * radio, 0),
        (x1 - 2 * radio, y1 - 2 * radio, x1, y1, 270),
        (x0, y1 - 2 * radio, x0 + 2 * radio, y1, 180),
    ):
        lienzo.create_arc(
            *arco[:4],
            start=arco[4],
            extent=90,
            fill=relleno,
            outline=relleno,
            style="pieslice",
        )


class MarcaSDEP(tk.Canvas):
    """Isotipo de la aplicación: monograma «S» sobre cuadrado redondeado."""

    def __init__(self, parent, tamano: int = 44, color_fondo: str | None = None, **kwargs):
        super().__init__(
            parent,
            width=tamano,
            height=tamano,
            highlightthickness=0,
            bd=0,
            bg=color_fondo or COLORES["panel"],
            **kwargs,
        )
        self._tamano = tamano
        self.dibujar()

    def dibujar(self) -> None:
        """Redibuja el isotipo con la paleta activa."""
        try:
            self.delete("all")
            tamano = self._tamano
            margen = max(2, tamano // 16)
            radio = max(6, tamano // 4)
            acento = COLORES["acento"]
            # Sombra inferior: da volumen sin depender de transparencias.
            _cuadrado_redondeado(
                self,
                margen,
                margen + max(1, tamano // 32),
                tamano - margen,
                tamano - margen + max(1, tamano // 32),
                radio,
                _oscurecer(acento, 0.55),
            )
            _cuadrado_redondeado(
                self, margen, margen, tamano - margen, tamano - margen, radio, acento
            )
            try:
                familia = familia_fuente_tk("TkDefaultFont", "Arial")
            except Exception:
                familia = "Arial"
            self.create_text(
                tamano / 2,
                tamano / 2,
                text="S",
                fill="white",
                font=(familia, max(8, int(tamano * 0.58)), "bold"),
            )
        except tk.TclError:
            # El lienzo ya no existe (ventana cerrándose): no hay nada que pintar.
            return

    def recolorear(self, color_fondo: str | None = None) -> None:
        """Actualiza el fondo del lienzo y vuelve a dibujar el isotipo."""
        if color_fondo:
            try:
                self.configure(bg=color_fondo)
            except tk.TclError:
                return
        self.dibujar()


class EncabezadoMarca(ctk.CTkFrame):
    """
    Isotipo + nombre del producto + descriptor, en fila o en columna.

    Sustituye los rótulos de texto sueltos del login y de la barra lateral:
    ambas ventanas comparten el mismo componente y, por tanto, la misma marca.
    """

    def __init__(
        self,
        parent,
        titulo: str = NOMBRE_PRODUCTO,
        subtitulo: str = NOMBRE_COMPLETO,
        orientacion: str = "horizontal",
        tamano_logo: int = 44,
        tamano_titulo: int = 16,
        wraplength: int = 0,
        color_fondo: str | None = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._color_fondo = color_fondo or COLORES["panel"]
        self._vertical = orientacion == "vertical"
        self._wraplength = wraplength

        alineacion = "center" if self._vertical else "w"
        justificacion = "center" if self._vertical else "left"

        self.logo = MarcaSDEP(self, tamano=tamano_logo, color_fondo=self._color_fondo)
        if self._vertical:
            self.logo.pack(pady=(0, 12))
        else:
            self.logo.pack(side="left", padx=(0, 12))

        textos = ctk.CTkFrame(self, fg_color="transparent")
        textos.pack(
            side="top" if self._vertical else "left",
            fill="x",
            expand=not self._vertical,
        )

        self.nombre_label = ctk.CTkLabel(
            textos,
            text=titulo,
            font=ctk.CTkFont(size=tamano_titulo, weight="bold"),
            text_color=COLORES["texto"],
            anchor=alineacion,
            justify=justificacion,
        )
        self.nombre_label.pack(fill="x")

        self.subtitulo_label = ctk.CTkLabel(
            textos,
            text=subtitulo,
            font=ctk.CTkFont(size=11),
            text_color=COLORES["texto_suave"],
            anchor=alineacion,
            justify=justificacion,
            wraplength=self._wraplength or 0,
        )
        self.subtitulo_label.pack(fill="x", pady=(2, 0))

    def recolorear(self, color_fondo: str | None = None) -> None:
        """Reaplica la paleta activa tras un cambio de tema."""
        if color_fondo:
            self._color_fondo = color_fondo
        self.logo.recolorear(self._color_fondo)
        for etiqueta, color in (
            (self.nombre_label, COLORES["texto"]),
            (self.subtitulo_label, COLORES["texto_suave"]),
        ):
            try:
                etiqueta.configure(text_color=color)
            except tk.TclError:
                return
