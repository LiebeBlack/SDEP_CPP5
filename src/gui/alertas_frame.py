"""
Módulo de Alertas

Vista completa de las alertas accionables del sistema. Reutiliza el mismo
generador que el panel del Dashboard, pero muestra todas las alertas
vigentes con su categoría y cantidad, y permite exportarlas.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

from src.gui.alertas_panel import COLORES_SEVERIDAD, ETIQUETAS_SEVERIDAD
from src.gui.frames import _habilitar_orden_columnas, _seleccionar_fila_click
from src.gui.theme import COLORES

logger = logging.getLogger(__name__)

CATEGORIAS = [
    "Todas",
    "Documentos",
    "Contratos",
    "Incidencias",
    "Asistencia",
    "Préstamos",
    "Nómina",
    "Respaldo",
    "Credenciales",
]


class AlertasFrame(ctk.CTkFrame):
    """Frame del módulo de alertas del sistema"""

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self.servicio = self._crear_servicio()
        self.alertas: list[dict] = []
        self._create_widgets()
        self._load_data()

    def _crear_servicio(self):
        """Crea el servicio de alertas con la sesión activa"""
        try:
            from src.services import AlertaService

            return AlertaService(self.session)
        except (ImportError, AttributeError) as e:
            logger.error("No se pudo inicializar el servicio de alertas: %s", e)
            return None

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Crea el encabezado, los filtros, la tabla y el resumen"""
        ctk.CTkLabel(
            self,
            text="Alertas del Sistema",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORES["texto"],
        ).pack(pady=(14, 6), padx=20, anchor="w")

        barra = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        barra.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(barra, text="Categoría:", text_color=COLORES["texto"]).pack(
            side="left", padx=(12, 4), pady=10
        )
        self.categoria_combo = ctk.CTkComboBox(
            barra, width=160, values=CATEGORIAS, command=lambda _v: self._render()
        )
        self.categoria_combo.pack(side="left", pady=10)
        self.categoria_combo.set("Todas")

        ctk.CTkButton(barra, text="🔄 Actualizar", width=120, command=self._load_data).pack(
            side="left", padx=8
        )

        ctk.CTkButton(
            barra,
            text="📄 Reporte PDF",
            width=120,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._exportar_pdf,
        ).pack(side="right", padx=(4, 12))

        ctk.CTkButton(
            barra,
            text="↗ Ir al módulo",
            width=130,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._ir_al_modulo,
        ).pack(side="right", padx=4)

        contenedor = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        contenedor.pack(fill="both", expand=True, padx=20, pady=8)

        columnas = ("severidad", "categoria", "titulo", "cantidad", "descripcion", "accion")
        self.tree = ttk.Treeview(contenedor, columns=columnas, show="headings", height=15)
        encabezados = {
            "severidad": ("Severidad", 110),
            "categoria": ("Categoría", 120),
            "titulo": ("Alerta", 260),
            "cantidad": ("Casos", 70),
            "descripcion": ("Descripción", 380),
            "accion": ("Acción", 130),
        }
        for clave, (texto, ancho) in encabezados.items():
            self.tree.heading(clave, text=texto)
            self.tree.column(
                clave,
                width=ancho,
                anchor="center" if clave in ("severidad", "cantidad", "accion") else "w",
            )

        _habilitar_orden_columnas(self.tree)
        self.tree.bind(
            "<ButtonRelease-1>", lambda evento: _seleccionar_fila_click(self.tree, evento)
        )
        self.tree.bind("<Double-1>", lambda _evento: self._ir_al_modulo())

        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        resumen = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        resumen.pack(fill="x", padx=20, pady=(0, 16))
        self.resumen_label = ctk.CTkLabel(
            resumen,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORES["texto_suave"],
            anchor="w",
            justify="left",
        )
        self.resumen_label.pack(fill="x", padx=14, pady=10)

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------
    def _load_data(self) -> None:
        """Recalcula las alertas y redibuja la tabla"""
        if self.servicio is None:
            messagebox.showerror("Alertas", "El servicio de alertas no está disponible")
            return
        usuario = getattr(self.main_window, "current_user", None)
        try:
            alertas = self.servicio.generar_alertas(usuario)
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("No se pudieron generar las alertas: %s", e)
            messagebox.showerror("Alertas", f"No se pudieron generar las alertas:\n{e}")
            return

        self.alertas = [alerta.to_dict() for alerta in alertas]
        self._render()

    def _render(self) -> None:
        """Aplica el filtro de categoría y pinta la tabla y el resumen"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        categoria = self.categoria_combo.get().strip()
        visibles = self.alertas
        if categoria and categoria != "Todas":
            clave = categoria.lower()
            visibles = [
                alerta
                for alerta in self.alertas
                if str(alerta.get("categoria", "")).lower().startswith(clave[:7])
            ]

        for alerta in visibles:
            severidad = str(alerta.get("severidad", "info"))
            self.tree.insert(
                "",
                "end",
                iid=str(alerta.get("clave", "")),
                values=(
                    ETIQUETAS_SEVERIDAD.get(severidad, severidad),
                    str(alerta.get("categoria", "")).capitalize(),
                    alerta.get("titulo", ""),
                    int(alerta.get("cantidad") or 0),
                    alerta.get("descripcion", ""),
                    str(alerta.get("modulo") or "-"),
                ),
                tags=(severidad,),
            )

        for severidad, color in COLORES_SEVERIDAD.items():
            try:
                self.tree.tag_configure(severidad, foreground=color)
            except tk.TclError:
                logger.debug("No se pudo aplicar el color de severidad", exc_info=True)

        criticas = sum(
            1 for alerta in visibles if str(alerta.get("severidad")) == "critica"
        )
        advertencias = sum(
            1 for alerta in visibles if str(alerta.get("severidad")) == "advertencia"
        )
        total_casos = sum(int(alerta.get("cantidad") or 0) for alerta in visibles)
        self.resumen_label.configure(
            text=(
                f"Alertas mostradas: {len(visibles)} · Críticas: {criticas} · "
                f"Advertencias: {advertencias} · Casos pendientes: {total_casos}"
            )
        )

    def _alerta_seleccionada(self) -> dict | None:
        """Alerta seleccionada en la tabla"""
        seleccion = self.tree.selection()
        if not seleccion:
            return None
        clave = seleccion[0]
        return next(
            (alerta for alerta in self.alertas if str(alerta.get("clave")) == clave), None
        )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def _ir_al_modulo(self) -> None:
        """Navega al módulo donde se resuelve la alerta seleccionada"""
        alerta = self._alerta_seleccionada()
        if alerta is None:
            messagebox.showinfo("Alertas", "Seleccione una alerta de la lista")
            return
        modulo = alerta.get("modulo")
        if not modulo:
            messagebox.showinfo(
                "Alertas",
                "Esta alerta se resuelve directamente desde Configuración o el respaldo.",
            )
            return
        try:
            self.main_window._show_frame(str(modulo))
        except (AttributeError, tk.TclError):
            logger.debug("No se pudo navegar al módulo %s", modulo, exc_info=True)

    def exportar_pdf(self) -> None:
        """Exporta las alertas visibles a un PDF y ofrece abrirlo"""
        if not self.alertas:
            messagebox.showinfo("Alertas", "No hay alertas para exportar")
            return
        try:
            from pathlib import Path

            from src.config import settings
            from src.utils.helpers import (
                abrir_con_aplicacion_predeterminada,
                ensure_directory_exists,
                get_timestamp,
            )
            from src.utils.pdf_generator import pdf_generator

            carpeta = Path(settings.exports_path) / "alertas"
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"alertas_{get_timestamp()}.pdf"
            pdf_generator.generate_reporte_alertas(self.alertas, str(destino))
            abrir_con_aplicacion_predeterminada(destino)
            messagebox.showinfo("Alertas", f"Reporte generado:\n{destino}")
        except (OSError, ValueError, ImportError) as e:
            logger.warning("No se pudo exportar el reporte de alertas", exc_info=True)
            messagebox.showerror("Alertas", f"No se pudo generar el reporte:\n{e}")

    def _exportar_pdf(self) -> None:
        """Alias de exportar_pdf para el atajo F5/Ctrl+S del marco"""
        self.exportar_pdf()
