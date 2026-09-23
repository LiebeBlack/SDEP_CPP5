"""
Panel de alertas

Muestra las alertas vigentes del sistema (vencimientos, pendientes,
respaldos atrasados, credenciales caducadas) con su severidad y un botón
que lleva directamente al módulo donde se resuelven.
"""

import logging
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from src.gui.theme import COLORES

logger = logging.getLogger(__name__)

# Colores por severidad de la alerta
COLORES_SEVERIDAD = {
    "critica": "#EF4444",
    "advertencia": "#F59E0B",
    "info": "#3B82F6",
}

ETIQUETAS_SEVERIDAD = {
    "critica": "Crítica",
    "advertencia": "Advertencia",
    "info": "Informativa",
}


class PanelAlertas(ctk.CTkFrame):
    """
    Panel de alertas accionables

    Args:
        parent: Contenedor padre
        main_window: Ventana principal (para navegar entre módulos)
        maximo: Cantidad máxima de alertas visibles a la vez
    """

    def __init__(self, parent, main_window, maximo: int = 5):
        super().__init__(parent, fg_color=COLORES["panel"], corner_radius=8)
        self.main_window = main_window
        self.maximo = maximo
        self.alertas: list[dict] = []
        self._crear_widgets()
        self.cargar()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def _crear_widgets(self) -> None:
        """Crea el encabezado, los contadores y el contenedor de alertas"""
        encabezado = ctk.CTkFrame(self, fg_color="transparent")
        encabezado.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            encabezado,
            text="Alertas del sistema",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORES["texto"],
        ).pack(side="left")

        self.contador_label = ctk.CTkLabel(
            encabezado,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORES["texto_suave"],
        )
        self.contador_label.pack(side="left", padx=10)

        ctk.CTkButton(
            encabezado,
            text="Exportar",
            width=80,
            height=26,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self.exportar_pdf,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            encabezado,
            text="Actualizar",
            width=90,
            height=26,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self.cargar,
        ).pack(side="right", padx=4)

        self.contenedor = ctk.CTkScrollableFrame(
            self, fg_color="transparent", height=210
        )
        self.contenedor.pack(fill="both", expand=True, padx=10, pady=(0, 12))

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------
    def cargar(self) -> list[dict]:
        """
        Recalcula las alertas y redibuja el panel

        Returns:
            list[dict]: Alertas vigentes (lista vacía si algo falla).
        """
        for widget in self.contenedor.winfo_children():
            widget.destroy()

        try:
            from src.services import AlertaService

            session = getattr(self.main_window, "session", None)
            if session is None:
                self._mostrar_mensaje("Sin sesión de datos activa")
                return []
            usuario = getattr(self.main_window, "current_user", None)
            resumen = AlertaService(session).resumen(usuario)
        except Exception:
            logger.warning("No se pudieron cargar las alertas", exc_info=True)
            self._mostrar_mensaje("No se pudieron cargar las alertas")
            return []

        self.alertas = [
            alerta.to_dict()
            for alerta in (resumen.get("alertas") or [])
        ][: self.maximo]
        self._actualizar_contador(resumen)

        if not self.alertas:
            self._mostrar_mensaje("Todo en orden: no hay alertas pendientes")
            return []

        for alerta in self.alertas:
            self._crear_tarjeta(alerta)
        return self.alertas

    def _actualizar_contador(self, resumen: dict) -> None:
        """Muestra el número de alertas por severidad en el encabezado"""
        criticas = int(resumen.get("criticas") or 0)
        advertencias = int(resumen.get("advertencias") or 0)
        informativas = int(resumen.get("informativas") or 0)
        self.contador_label.configure(
            text=f"{criticas} crítica(s) · {advertencias} advertencia(s) · {informativas} info"
        )

    def _mostrar_mensaje(self, mensaje: str) -> None:
        """Muestra un mensaje informativo en lugar de la lista"""
        ctk.CTkLabel(
            self.contenedor,
            text=mensaje,
            font=ctk.CTkFont(size=12),
            text_color=COLORES["texto_suave"],
        ).pack(pady=20)

    def _crear_tarjeta(self, alerta: dict) -> None:
        """Crea la tarjeta de una alerta con su acción"""
        severidad = str(alerta.get("severidad", "info"))
        color = COLORES_SEVERIDAD.get(severidad, COLORES["texto_suave"])

        tarjeta = ctk.CTkFrame(self.contenedor, fg_color=COLORES["campo"], corner_radius=6)
        tarjeta.pack(fill="x", pady=3, padx=2)

        barra = ctk.CTkFrame(tarjeta, width=4, fg_color=color, corner_radius=2)
        barra.pack(side="left", fill="y", padx=(6, 8), pady=6)

        textos = ctk.CTkFrame(tarjeta, fg_color="transparent")
        textos.pack(side="left", fill="both", expand=True, pady=6)

        ctk.CTkLabel(
            textos,
            text=str(alerta.get("titulo", "")),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORES["texto"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            textos,
            text=str(alerta.get("descripcion", "")),
            font=ctk.CTkFont(size=10),
            text_color=COLORES["texto_suave"],
            anchor="w",
            wraplength=420,
            justify="left",
        ).pack(fill="x")
        detalles = alerta.get("detalles") or []
        if detalles:
            ctk.CTkLabel(
                textos,
                text=" · ".join(str(detalle) for detalle in detalles[:3]),
                font=ctk.CTkFont(size=9),
                text_color=COLORES["texto_suave"],
                anchor="w",
                wraplength=420,
                justify="left",
            ).pack(fill="x")

        etiqueta = ETIQUETAS_SEVERIDAD.get(severidad, "Info")
        modulo = alerta.get("modulo")
        if modulo:
            ctk.CTkButton(
                tarjeta,
                text=f"{etiqueta} · Ir",
                width=96,
                height=26,
                fg_color=color,
                hover_color=COLORES["panel_hover"],
                command=lambda m=modulo: self._ir_a(m),
            ).pack(side="right", padx=8, pady=8)
        else:
            ctk.CTkLabel(
                tarjeta,
                text=etiqueta,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=color,
            ).pack(side="right", padx=10)

    def _ir_a(self, modulo: str) -> None:
        """Navega al módulo indicado por la alerta"""
        try:
            self.main_window._show_frame(modulo)
        except (AttributeError, tk.TclError):
            logger.debug("No se pudo navegar al módulo %s", modulo, exc_info=True)

    # ------------------------------------------------------------------
    # Exportación
    # ------------------------------------------------------------------
    def exportar_pdf(self) -> None:
        """Exporta las alertas vigentes a un PDF y ofrece abrirlo"""
        if not self.alertas:
            messagebox.showinfo("Alertas", "No hay alertas para exportar")
            return
        try:
            from pathlib import Path

            from src.config import settings
            from src.utils.helpers import ensure_directory_exists, get_timestamp
            from src.utils.pdf_generator import pdf_generator

            carpeta = Path(settings.exports_path) / "alertas"
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"alertas_{get_timestamp()}.pdf"
            pdf_generator.generate_reporte_alertas(self.alertas, str(destino))

            from src.utils.helpers import abrir_con_aplicacion_predeterminada

            if abrir_con_aplicacion_predeterminada(destino):
                messagebox.showinfo("Alertas", f"Reporte generado:\n{destino}")
            else:
                messagebox.showinfo(
                    "Alertas", f"Reporte generado en:\n{destino}\n\nÁbralo manualmente."
                )
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning("No se pudo exportar el reporte de alertas", exc_info=True)
            messagebox.showerror("Alertas", f"No se pudo generar el reporte:\n{e}")
