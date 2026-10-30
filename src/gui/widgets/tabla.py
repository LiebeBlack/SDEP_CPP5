"""
Estado visual de las tablas (ttk.Treeview).

Las tablas de la aplicación resolvían el "no hay datos" insertando una fila
falsa dentro del propio árbol: esa fila era seleccionable y rompía los manejadores
que esperan un identificador numérico en la primera columna. Aquí el aviso se
dibuja encima del árbol, sin tocar sus filas, y se acompaña de dos utilidades
poco costosas: la cebra de filas y el contador de resultados.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.gui.theme import COLORES, familia_fuente_tk

__all__ = ["EstadoTabla", "configurar_cebra", "etiqueta_fila", "resumen_conteo"]


def _familia() -> str:
    """Familia tipográfica del sistema, con reserva si Tk no responde."""
    try:
        return familia_fuente_tk("TkDefaultFont", "Arial")
    except Exception:  # pragma: no cover - depende del entorno gráfico
        return "Arial"


def configurar_cebra(arbol: ttk.Treeview) -> None:
    """Registra las dos etiquetas de fondo alterno.

    Se llama una sola vez, al construir la tabla. Los colores se derivan de la
    paleta activa para que el contraste se mantenga en tema claro y oscuro.
    """
    try:
        arbol.tag_configure("fila_par", background=COLORES["panel"])
        arbol.tag_configure("fila_impar", background=COLORES["fondo"])
    except tk.TclError:  # pragma: no cover - árbol ya destruido
        return


def etiqueta_fila(indice: int) -> tuple[str]:
    """Etiqueta de cebra para la fila ``indice`` (base cero)."""
    return ("fila_par",) if indice % 2 == 0 else ("fila_impar",)


def resumen_conteo(cantidad: int, singular: str, plural: str, filtro: str = "") -> str:
    """Texto del contador: «12 empleados» o «3 de 12 empleados (filtro)»."""
    if cantidad == 1:
        base = f"1 {singular}"
    else:
        base = f"{cantidad:,} {plural}".replace(",", ".")
    if filtro:
        return f"{base} · coincidencias con «{filtro}»"
    return base


class EstadoTabla:
    """Aviso superpuesto para una tabla sin filas.

    Se dibuja con ``place`` sobre el árbol, de modo que no altera el empaquetado
    ni el tamaño de la tabla, y desaparece en cuanto hay datos.
    """

    def __init__(self, arbol: ttk.Treeview) -> None:
        self._arbol = arbol
        self._contenedor = getattr(arbol, "master", None) or arbol
        self._etiqueta: tk.Label | None = None
        self._visible = False

    # ------------------------------------------------------------------
    def _crear(self) -> tk.Label:
        if self._etiqueta is None or not self._etiqueta.winfo_exists():
            self._etiqueta = tk.Label(
                self._contenedor,
                text="",
                bg=COLORES["panel"],
                fg=COLORES["texto"],
                font=(_familia(), 11),
                justify="center",
                wraplength=420,
                padx=18,
                pady=14,
                bd=0,
            )
        return self._etiqueta

    def mostrar(self, mensaje: str, detalle: str = "") -> None:
        """Muestra el aviso; si se indica ``detalle`` va en una segunda línea."""
        texto = mensaje if not detalle else f"{mensaje}\n{detalle}"
        etiqueta = self._crear()
        etiqueta.configure(text=texto)
        if not self._visible:
            etiqueta.place(in_=self._arbol, relx=0.5, rely=0.45, anchor="center")
            self._visible = True
        else:
            etiqueta.lift()

    def ocultar(self) -> None:
        """Quita el aviso cuando la tabla vuelve a tener filas."""
        if not self._visible:
            return
        if self._etiqueta is not None and self._etiqueta.winfo_exists():
            self._etiqueta.place_forget()
        self._visible = False

    def actualizar(self, cantidad: int, mensaje: str, detalle: str = "") -> None:
        """Azúcar sintáctico: oculta con filas y avisa cuando no hay ninguna."""
        if cantidad:
            self.ocultar()
        else:
            self.mostrar(mensaje, detalle)

    def destroy(self) -> None:
        if self._etiqueta is not None and self._etiqueta.winfo_exists():
            self._etiqueta.destroy()
        self._etiqueta = None
        self._visible = False
