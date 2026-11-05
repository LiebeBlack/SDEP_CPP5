"""
Gráficos del Dashboard

Widgets de barras, dona, línea y tarjeta de indicador dibujados
directamente sobre un Canvas de Tk. No se usa ninguna librería externa de
gráficos: así el ejecutable no crece, no se añaden dependencias nuevas y
el tema de la aplicación se respeta sin capas de compatibilidad.

Todos los widgets son de solo lectura y redibujan sobre el canvas cuando
cambian los datos o el tamaño de la ventana.
"""

import tkinter as tk

import customtkinter as ctk

from src.gui.theme import COLORES, familia_fuente_tk

# Paleta de series (se repite cíclicamente si hay más datos que colores)
PALETA = (
    "#3B82F6",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#06B6D4",
    "#EC4899",
    "#84CC16",
)


class GraficoBase(ctk.CTkFrame):
    """Base común de los gráficos: título, canvas y redibujado"""

    def __init__(self, parent, titulo: str, alto: int = 200, **kwargs):
        kwargs.setdefault("fg_color", COLORES["panel"])
        kwargs.setdefault("corner_radius", 14)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORES["borde"])
        super().__init__(parent, **kwargs)
        self.titulo = titulo
        self.alto = alto

        self.titulo_label = ctk.CTkLabel(
            self,
            text=titulo,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORES["texto"],
            anchor="w",
        )
        self.titulo_label.pack(fill="x", padx=12, pady=(10, 4))

        self.canvas = tk.Canvas(
            self,
            height=alto,
            highlightthickness=0,
            bg=COLORES["panel"],
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        self._redraw_timer: str | None = None
        self._last_size: tuple[int, int] = (0, 0)
        self.canvas.bind("<Configure>", lambda _evento: self._solicitar_redibujo())

    def _solicitar_redibujo(self) -> None:
        if not self.winfo_exists():
            return
        w = int(self.canvas.winfo_width())
        h = int(self.canvas.winfo_height())
        if (w, h) == self._last_size and w > 1 and h > 1:
            return
        if self._redraw_timer is not None:
            try:
                self.after_cancel(self._redraw_timer)
            except Exception:
                pass
            self._redraw_timer = None
        self._redraw_timer = self.after(40, self._ejecutar_redibujo)

    def _ejecutar_redibujo(self) -> None:
        self._redraw_timer = None
        if self.winfo_exists():
            self._last_size = (int(self.canvas.winfo_width()), int(self.canvas.winfo_height()))
            self.dibujar()

    def destroy(self) -> None:
        if self._redraw_timer is not None:
            try:
                self.after_cancel(self._redraw_timer)
            except Exception:
                pass
            self._redraw_timer = None
        super().destroy()

    def _fuente_canvas(
        self, tamano: int, negrita: bool = False
    ) -> tuple[str, int] | tuple[str, int, str]:
        """Resuelve la fuente desde el intérprete Tk de este gráfico."""
        familia = familia_fuente_tk("TkDefaultFont", "Arial", self.canvas)
        return (familia, tamano, "bold") if negrita else (familia, tamano)

    def color_serie(self, indice: int) -> str:
        """Color de la serie indicada (cicla sobre la paleta)"""
        return PALETA[indice % len(PALETA)]

    def ancho(self) -> int:
        """Ancho útil del canvas en píxeles"""
        w = int(self.canvas.winfo_width())
        return w if w > 1 else 320

    def alto_canvas(self) -> int:
        """Alto útil del canvas en píxeles"""
        h = int(self.canvas.winfo_height())
        return h if h > 1 else max(80, self.alto)

    def limpiar(self) -> None:
        """Borra el contenido y muestra el estado vacío si corresponde"""
        self.canvas.delete("all")

    def mostrar_vacio(self, mensaje: str = "Sin datos para mostrar") -> None:
        """Dibuja el mensaje de estado vacío centrado"""
        self.limpiar()
        self.canvas.create_text(
            self.ancho() / 2,
            self.alto_canvas() / 2,
            text=mensaje,
            fill=COLORES["texto_suave"],
            font=self._fuente_canvas(11),
        )

    def dibujar(self) -> None:
        """Redibuja el gráfico (implementado por cada widget)"""
        try:
            self.canvas.configure(bg=COLORES["panel"])
            self.titulo_label.configure(text_color=COLORES["texto"])
        except Exception:
            pass


class GraficoBarras(GraficoBase):
    """
    Gráfico de barras verticales

    Cada barra lleva su etiqueta debajo y su valor encima, de modo que el
    gráfico sea legible sin necesidad de leyenda.
    """

    def __init__(self, parent, titulo: str, alto: int = 200, **kwargs):
        super().__init__(parent, titulo, alto, **kwargs)
        self.datos: list[tuple[str, float]] = []

    def establecer_datos(self, datos: list[tuple[str, float]]) -> None:
        """Carga los pares (etiqueta, valor) a representar"""
        self.datos = [(str(etiqueta), float(valor or 0)) for etiqueta, valor in datos]
        self.dibujar()

    def dibujar(self) -> None:
        super().dibujar()
        if not self.datos:
            self.mostrar_vacio()
            return

        # Sin este borrado, cada redibujado (cambio de datos o de tamaño)
        # dejaba encima las barras y etiquetas anteriores: al reducirse el
        # número de datos seguían visibles las barras que ya no existían.
        self.limpiar()
        ancho = max(120, self.ancho())
        alto = max(80, self.alto_canvas())
        margen_sup, margen_inf, margen_lat = 22, 34, 28
        base_y = max(margen_sup + 20, alto - margen_inf)
        maximo = max((abs(valor) for _, valor in self.datos), default=0) or 1

        disponibles = max(1, len(self.datos))
        ancho_util = max(40.0, float(ancho - margen_lat * 2))
        ancho_barra = max(8.0, (ancho_util / disponibles) * 0.6)
        paso = ancho_util / disponibles

        # Línea base
        self.canvas.create_line(
            margen_lat, base_y, ancho - margen_lat, base_y, fill=COLORES["texto_suave"]
        )

        for indice, (etiqueta, valor) in enumerate(self.datos):
            centro_x = margen_lat + paso * indice + paso / 2
            alto_barra = (base_y - margen_sup) * (abs(valor) / maximo)
            x0 = centro_x - ancho_barra / 2
            y0 = base_y - alto_barra
            self.canvas.create_rectangle(
                x0,
                y0,
                x0 + ancho_barra,
                base_y,
                fill=self.color_serie(indice),
                outline="",
            )
            self.canvas.create_text(
                centro_x,
                y0 - 9,
                text=self._formato_valor(valor),
                fill=COLORES["texto"],
                font=self._fuente_canvas(9, negrita=True),
            )
            recorte = etiqueta if len(etiqueta) <= 12 else etiqueta[:11] + "…"
            self.canvas.create_text(
                centro_x,
                base_y + 14,
                text=recorte,
                fill=COLORES["texto_suave"],
                font=self._fuente_canvas(9),
            )

    @staticmethod
    def _formato_valor(valor: float) -> str:
        """Valor abreviado para la etiqueta de la barra"""
        if abs(valor) >= 1_000_000:
            return f"{valor / 1_000_000:.1f}M"
        if abs(valor) >= 1_000:
            return f"{valor / 1_000:.1f}k"
        return f"{valor:.0f}" if float(valor).is_integer() else f"{valor:.2f}"


class GraficoDona(GraficoBase):
    """Gráfico de dona con leyenda lateral y porcentajes"""

    def __init__(self, parent, titulo: str, alto: int = 200, **kwargs):
        super().__init__(parent, titulo, alto, **kwargs)
        self.datos: list[tuple[str, float]] = []

    def establecer_datos(self, datos: list[tuple[str, float]]) -> None:
        """Carga los pares (etiqueta, valor) a representar"""
        self.datos = [
            (str(etiqueta), float(valor or 0)) for etiqueta, valor in datos if float(valor or 0) > 0
        ]
        self.dibujar()

    def dibujar(self) -> None:
        super().dibujar()
        if not self.datos:
            self.mostrar_vacio()
            return

        self.limpiar()
        ancho = self.ancho()
        alto = self.alto_canvas()
        total = sum(valor for _, valor in self.datos) or 1

        # La leyenda se reserva primero: antes el diámetro se calculaba solo
        # con el ancho y, en ventanas estrechas, la leyenda se salía por el
        # borde derecho y los textos aparecían recortados.
        leyenda_visible = ancho >= 260
        ancho_leyenda = min(240.0, max(120.0, ancho * 0.42)) if leyenda_visible else 0.0
        espacio_dona = ancho - ancho_leyenda - 32
        diametro = max(24.0, min(alto - 20, espacio_dona))
        radio = diametro / 2
        centro_x = 16 + radio
        centro_y = alto / 2
        grosor = max(4.0, min(radio * 0.42, radio * 0.9))

        inicio = 90.0
        for indice, (_etiqueta, valor) in enumerate(self.datos):
            extension = -360.0 * (valor / total)
            if abs(extension) >= 359.5:
                # El 100 % en un solo dato se dibuja como circunferencia
                # completa: un arco de 360° depende del redondeo de Tk y podía
                # quedar sin pintar, dejando la dona vacía.
                self.canvas.create_oval(
                    centro_x - radio,
                    centro_y - radio,
                    centro_x + radio,
                    centro_y + radio,
                    outline=self.color_serie(indice),
                    width=grosor,
                )
            else:
                self.canvas.create_arc(
                    centro_x - radio,
                    centro_y - radio,
                    centro_x + radio,
                    centro_y + radio,
                    start=inicio,
                    extent=extension,
                    style="arc",
                    outline=self.color_serie(indice),
                    width=grosor,
                )
            inicio += extension

        # Centro de la dona con el total
        self.canvas.create_text(
            centro_x,
            centro_y - 6,
            text=f"{total:,.0f}".replace(",", "."),
            fill=COLORES["texto"],
            font=self._fuente_canvas(14, negrita=True),
        )
        self.canvas.create_text(
            centro_x,
            centro_y + 12,
            text="total",
            fill=COLORES["texto_suave"],
            font=self._fuente_canvas(9),
        )

        # Leyenda: una fila cada 18 px como máximo y textos recortados al
        # ancho libre, para que no se salga por el borde derecho ni por abajo.
        if not leyenda_visible:
            return
        max_items = max(1, min(8, int((alto - 24) // 18)))
        datos_leyenda = self.datos[:max_items]
        truncado = len(self.datos) > max_items
        total_items = len(datos_leyenda) + (1 if truncado else 0)
        leyenda_x = centro_x + radio + 24
        leyenda_y = centro_y - (total_items * 18) / 2 + 8
        ancho_texto = max(40.0, ancho - (leyenda_x + 16) - 10)
        con_porcentaje = ancho_texto >= 80
        max_caracteres = max(6, int(ancho_texto / 6.2) - (4 if con_porcentaje else 0))
        for indice, (etiqueta, valor) in enumerate(datos_leyenda):
            y = leyenda_y + indice * 18
            self.canvas.create_rectangle(
                leyenda_x, y - 5, leyenda_x + 10, y + 5, fill=self.color_serie(indice), outline=""
            )
            if len(etiqueta) <= max_caracteres:
                texto = etiqueta
            else:
                texto = etiqueta[: max_caracteres - 1] + "…"
            sufijo = f"  {valor / total * 100:.0f}%" if con_porcentaje else ""
            self.canvas.create_text(
                leyenda_x + 16,
                y,
                text=f"{texto}{sufijo}",
                anchor="w",
                fill=COLORES["texto"],
                font=self._fuente_canvas(9),
            )
        if truncado:
            restantes = len(self.datos) - max_items
            y = leyenda_y + len(datos_leyenda) * 18
            self.canvas.create_text(
                leyenda_x + 16,
                y,
                text=f"...+{restantes} más",
                anchor="w",
                fill=COLORES["texto_suave"],
                font=self._fuente_canvas(9),
            )


class GraficoLinea(GraficoBase):
    """Gráfico de línea para series temporales (evolución mensual)"""

    def __init__(self, parent, titulo: str, alto: int = 200, **kwargs):
        super().__init__(parent, titulo, alto, **kwargs)
        self.puntos: list[tuple[str, float]] = []
        self.series: dict[str, list[tuple[str, float]]] = {}

    def establecer_datos(self, datos: list[tuple[str, float]]) -> None:
        """Carga una serie única de pares (etiqueta, valor)"""
        self.puntos = [(str(etiqueta), float(valor or 0)) for etiqueta, valor in datos]
        self.series = {}
        self.dibujar()

    def establecer_series(self, series: dict[str, list[tuple[str, float]]]) -> None:
        """Carga varias series comparables"""
        self.series = {
            str(nombre): [(str(etiqueta), float(valor or 0)) for etiqueta, valor in datos]
            for nombre, datos in series.items()
        }
        self.puntos = []
        self.dibujar()

    def dibujar(self) -> None:
        super().dibujar()
        series = self.series or {"Serie": self.puntos}
        series = {nombre: datos for nombre, datos in series.items() if datos}
        if not series:
            self.mostrar_vacio()
            return

        self.limpiar()
        ancho = max(120, self.ancho())
        alto = max(80, self.alto_canvas())
        margen_sup, margen_inf, margen_lat = 20, 32, 36
        base_y = max(margen_sup + 20, alto - margen_inf)
        # Escala por el mayor valor absoluto y acota el trazo al área del
        # gráfico: con valores negativos el máximo podía ser negativo (la
        # escala se invertía) o la línea caía sobre las etiquetas del eje.
        maximo = (
            max((abs(valor) for datos in series.values() for _, valor in datos), default=0) or 1
        )
        # El paso se calcula con la serie más larga: antes solo se miraba la
        # primera y una serie con más puntos desbordaba el borde derecho.
        max_puntos = max((len(datos) for datos in series.values()), default=1)
        etiquetas = [etiqueta for etiqueta, _ in next(iter(series.values()))]
        pasos = max(1, max_puntos - 1)
        ancho_util = max(40.0, float(ancho - margen_lat - 16))

        # Rejilla horizontal de referencia (cuatro niveles)
        for nivel in range(5):
            y = base_y - (base_y - margen_sup) * nivel / 4
            self.canvas.create_line(
                margen_lat, y, ancho - 16, y, fill=COLORES["panel_hover"], dash=(2, 4)
            )
            self.canvas.create_text(
                margen_lat - 6,
                y,
                text=GraficoBarras._formato_valor(maximo * nivel / 4),
                anchor="e",
                fill=COLORES["texto_suave"],
                font=self._fuente_canvas(8),
            )

        for indice_serie, (_nombre, datos) in enumerate(series.items()):
            coordenadas: list[float] = []
            for indice, (_etiqueta, valor) in enumerate(datos):
                x = margen_lat + ancho_util * (indice / pasos if pasos else 0)
                proporcion = (base_y - margen_sup) * (valor / maximo)
                y = min(base_y, max(margen_sup, base_y - proporcion))
                coordenadas.extend((x, y))
            if len(coordenadas) >= 4:
                self.canvas.create_line(
                    *coordenadas,
                    fill=self.color_serie(indice_serie),
                    width=2,
                    smooth=True,
                )
            for indice in range(0, len(coordenadas), 2):
                x, y = coordenadas[indice], coordenadas[indice + 1]
                self.canvas.create_oval(
                    x - 3,
                    y - 3,
                    x + 3,
                    y + 3,
                    fill=self.color_serie(indice_serie),
                    outline=COLORES["panel"],
                )

        # Etiquetas del eje horizontal (se saltan valores si hay muchos)
        salto = max(1, len(etiquetas) // 6)
        for indice, etiqueta in enumerate(etiquetas):
            if indice % salto:
                continue
            x = margen_lat + ancho_util * (indice / pasos if pasos else 0)
            self.canvas.create_text(
                x,
                base_y + 14,
                text=etiqueta,
                fill=COLORES["texto_suave"],
                font=self._fuente_canvas(8),
            )


class TarjetaIndicador(ctk.CTkFrame):
    """
    Tarjeta de indicador (KPI)

    Muestra un valor grande con su título, un icono y una variación
    opcional respecto al período anterior. Puede ser clicable para
    navegar al módulo relacionado.
    """

    def __init__(
        self,
        parent,
        titulo: str,
        icono: str = "",
        valor: str = "0",
        variacion: float | None = None,
        detalle: str | None = None,
        comando=None,
        **kwargs,
    ):
        kwargs.setdefault("fg_color", COLORES["campo"])
        kwargs.setdefault("corner_radius", 14)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORES["borde"])
        super().__init__(parent, **kwargs)
        self.comando = comando

        if icono:
            ctk.CTkLabel(self, text=icono, font=ctk.CTkFont(size=22)).pack(
                pady=(10, 0), padx=12, anchor="w"
            )

        self.valor_label = ctk.CTkLabel(
            self,
            text=valor,
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORES["texto"],
            anchor="w",
        )
        self.valor_label.pack(padx=12, anchor="w")

        ctk.CTkLabel(
            self,
            text=titulo,
            font=ctk.CTkFont(size=11),
            text_color=COLORES["texto_suave"],
            anchor="w",
        ).pack(padx=12, anchor="w")

        self.detalle_label = ctk.CTkLabel(
            self,
            text=detalle or "",
            font=ctk.CTkFont(size=10),
            text_color=COLORES["texto_suave"],
            anchor="w",
        )
        self.detalle_label.pack(padx=12, pady=(2, 10), anchor="w")

        self.variacion_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=COLORES["texto_suave"],
            anchor="w",
        )
        self.variacion_label.pack(padx=12, pady=(0, 10), anchor="w")
        if variacion is not None:
            self.establecer_variacion(variacion)

        if comando is not None:
            # Todos los hijos (icono y título incluidos) responden al clic:
            # antes solo el marco y los textos inferiores navegaban, así que
            # pulsar el icono o el título de la tarjeta no hacía nada.
            for widget in (self, *self.winfo_children()):
                widget.bind("<Button-1>", lambda _evento: self.comando())
                try:
                    widget.configure(cursor="hand2")
                except Exception:
                    pass

    def establecer_valor(self, valor: str, detalle: str | None = None) -> None:
        """Actualiza el valor mostrado y su detalle"""
        self.valor_label.configure(text=valor)
        if detalle is not None:
            self.detalle_label.configure(text=detalle)

    def establecer_variacion(self, variacion: float) -> None:
        """Muestra la variación porcentual respecto al período anterior"""
        if variacion > 0:
            texto, color = f"▲ {variacion:.1f}%", COLORES["error"]
        elif variacion < 0:
            texto, color = f"▼ {abs(variacion):.1f}%", COLORES["exito"]
        else:
            texto, color = "sin cambios", COLORES["texto_suave"]
        self.variacion_label.configure(text=texto, text_color=color)
