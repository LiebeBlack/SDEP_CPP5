"""
Módulo de Notas

Registro de calificaciones finales y control de los periodos académicos.
Es la puerta de entrada a la parte más sensible del subdominio académico:

- Las notas solo se escriben con un token de sesión válido y autorizado
  (administración, o el docente asignado al grado). El token se emite al
  abrir el módulo con la cuenta autenticada y vive solo en memoria.
- Un periodo cerrado bloquea toda escritura de notas, tanto en el servicio
  como en los disparadores de SQLite; reabrirlo exige rol administrador.

La pestaña de periodos vive aquí y no en un módulo aparte para no superar
el tope de nueve atajos directos (``Ctrl+1..9``) de la ventana principal.
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from src.gui.frames import InfoDialog, _habilitar_orden_columnas, _seleccionar_fila_click
from src.gui.theme import COLORES, habilitar_scroll_rueda
from src.models import Grado, Matricula, NotaFinal, PeriodoAcademico
from src.utils.helpers import format_date, parse_date

if TYPE_CHECKING:
    from src.services import NotaService

logger = logging.getLogger(__name__)

TODOS = "Todos"
COLOR_ERROR = "#e74c3c"


def _verificar_permiso(main_window, permiso: str, accion: str) -> bool:
    """Verifica el permiso operativo antes de ejecutar una acción."""
    if main_window is not None and main_window.tiene_permiso(permiso):
        return True
    messagebox.showwarning("Acceso denegado", f"Su rol no tiene permiso para {accion}")
    return False


class NotasFrame(ctk.CTkFrame):
    """Frame del módulo de calificaciones y periodos académicos"""

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self.servicio: NotaService | None = self._crear_servicio()
        self.tokens = None
        self.token: str | None = None
        self._periodos: list[PeriodoAcademico] = []
        self._grados: list[Grado] = []
        self._notas: list[NotaFinal] = []
        self._matriculas: list[Matricula] = []
        self._escala = (0.0, 20.0)
        self._nota_aprobatoria = 10.0
        self._create_widgets()
        self._emitir_token()
        self._cargar_datos_base()

    def _crear_servicio(self) -> NotaService | None:
        """Crea el servicio de notas con la sesión activa"""
        try:
            from src.services import NotaService

            return NotaService(self.session)
        except (ImportError, AttributeError) as e:
            logger.error("No se pudo inicializar el servicio de notas: %s", e)
            return None

    def _emitir_token(self) -> None:
        """Emite el token académico de la sesión (solo en memoria)"""
        usuario = getattr(self.main_window, "current_user", None)
        if usuario is None:
            logger.warning("Módulo de notas sin sesión autenticada: no se emite token")
            return
        try:
            from src.services import TokenSesionService

            self.tokens = TokenSesionService(self.session)
            self.token, _registro = self.tokens.emitir(usuario)
        except (ImportError, ValueError, AttributeError) as e:
            self.tokens = None
            self.token = None
            logger.error("No se pudo emitir el token académico: %s", e)

    def _puede_escribir(self, grado: Grado | None) -> bool:
        """¿El token vigente autoriza a escribir notas en el grado?"""
        if self.token is None or self.tokens is None:
            return False
        try:
            sesion = self.tokens.validar(self.token)
        except (AttributeError, ValueError, TypeError):
            logger.debug("Token académico no validable", exc_info=True)
            return False
        if sesion is None:
            return False
        return self.tokens.puede_escribir(sesion, grado)

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Crea las pestañas de notas y de periodos"""
        ctk.CTkLabel(
            self,
            text="Calificaciones y Periodos Académicos",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORES["texto"],
        ).pack(pady=(14, 6), padx=20, anchor="w")

        self.tabview = ctk.CTkTabview(self, fg_color=COLORES["panel"])
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        tab_notas = self.tabview.add("Notas")
        tab_periodos = self.tabview.add("Periodos")

        self._crear_tab_notas(tab_notas)
        self._crear_tab_periodos(tab_periodos)

    def _crear_tab_notas(self, parent) -> None:
        """Barra de contexto, acciones y tabla de notas"""
        barra = ctk.CTkFrame(parent, fg_color="transparent")
        barra.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(barra, text="Periodo:", text_color=COLORES["texto"]).grid(
            row=0, column=0, padx=(4, 4), pady=6, sticky="w"
        )
        self.periodo_combo = ctk.CTkComboBox(
            barra, width=170, values=[TODOS], command=lambda _v: self._on_periodo_cambio()
        )
        self.periodo_combo.grid(row=0, column=1, padx=(0, 10), pady=6, sticky="w")
        self.periodo_combo.set(TODOS)

        ctk.CTkLabel(barra, text="Grado:", text_color=COLORES["texto"]).grid(
            row=0, column=2, padx=(4, 4), pady=6, sticky="w"
        )
        self.grado_combo = ctk.CTkComboBox(
            barra, width=190, values=["-"], command=lambda _v: self._on_grado_cambio()
        )
        self.grado_combo.grid(row=0, column=3, padx=(0, 10), pady=6, sticky="w")

        self.search_entry = ctk.CTkEntry(
            barra, width=200, placeholder_text="Filtrar por estudiante o materia"
        )
        self.search_entry.grid(row=0, column=4, padx=(4, 8), pady=6, sticky="w")
        self.search_entry.bind("<Return>", lambda _e: self._load_notas())

        ctk.CTkButton(barra, text="🔍 Filtrar", width=88, command=self._load_notas).grid(
            row=0, column=5, padx=4, pady=6, sticky="w"
        )

        self.escala_label = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORES["texto_suave"],
            anchor="w",
        )
        self.escala_label.pack(fill="x", padx=12, pady=(0, 2))

        acciones = ctk.CTkFrame(parent, fg_color="transparent")
        acciones.pack(fill="x", padx=8, pady=(0, 4))
        for columna in range(7):
            acciones.grid_columnconfigure(columna, weight=1, uniform="acciones_notas")

        botones = (
            ("➕ Registrar nota", self._on_nueva_nota),
            ("✏️ Editar", self._editar_nota),
            ("🗑 Eliminar", self._eliminar_nota),
            ("📋 Consolidado", self._ver_consolidado),
            ("📄 Boletín", self._ver_boletin),
            ("📑 Acta", self._ver_acta),
            ("📊 Exportar", self._exportar),
        )
        for indice, (texto, comando) in enumerate(botones):
            ctk.CTkButton(
                acciones,
                text=texto,
                height=34,
                fg_color=COLORES["campo"] if indice else COLORES["acento"],
                hover_color=COLORES["panel_hover"],
                command=comando,
            ).grid(row=0, column=indice, padx=4, pady=2, sticky="ew")

        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=8, pady=4)

        columnas = ("estudiante", "cedula", "materia", "calificacion", "estado", "registrado_por")
        self.tree = ttk.Treeview(contenedor, columns=columnas, show="headings", height=12)
        habilitar_scroll_rueda(self.tree)
        encabezados = {
            "estudiante": ("Estudiante", 230),
            "cedula": ("Cédula", 95),
            "materia": ("Materia", 180),
            "calificacion": ("Calificación", 100),
            "estado": ("Estado", 95),
            "registrado_por": ("Registrada por", 120),
        }
        for clave, (texto, ancho) in encabezados.items():
            self.tree.heading(clave, text=texto)
            self.tree.column(
                clave,
                width=ancho,
                minwidth=60,
                anchor="w" if clave in ("estudiante", "materia") else "center",
                stretch=False,
            )
        _habilitar_orden_columnas(self.tree)
        self.tree.bind(
            "<ButtonRelease-1>", lambda evento: _seleccionar_fila_click(self.tree, evento)
        )
        self.tree.bind("<Double-1>", lambda _evento: self._editar_nota())

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_horizontal = ttk.Scrollbar(
            contenedor, orient="horizontal", command=self.tree.xview
        )
        scrollbar_horizontal.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_horizontal.set)

    def _crear_tab_periodos(self, parent) -> None:
        """Tabla de periodos con cierre y reapertura"""
        barra = ctk.CTkFrame(parent, fg_color="transparent")
        barra.pack(fill="x", padx=8, pady=(8, 4))
        for columna in range(4):
            barra.grid_columnconfigure(columna, weight=1, uniform="acciones_periodos")

        botones = (
            ("➕ Nuevo periodo", self._on_new_periodo),
            ("✏️ Editar", self._editar_periodo),
            ("🔒 Cerrar periodo", self._cerrar_periodo),
            ("🔓 Reabrir periodo", self._reabrir_periodo),
        )
        for indice, (texto, comando) in enumerate(botones):
            ctk.CTkButton(
                barra,
                text=texto,
                height=34,
                fg_color=COLORES["campo"] if indice else COLORES["acento"],
                hover_color=COLORES["panel_hover"],
                command=comando,
            ).grid(row=0, column=indice, padx=4, pady=2, sticky="ew")

        ctk.CTkLabel(
            parent,
            text=(
                "Cerrar un periodo bloquea sus notas de forma permanente (servicio y base de "
                "datos). Solo un administrador puede reabrirlo, y la operación queda auditada."
            ),
            font=ctk.CTkFont(size=11),
            text_color=COLORES["texto_suave"],
            anchor="w",
            justify="left",
            wraplength=900,
        ).pack(fill="x", padx=12, pady=(0, 4))

        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=8, pady=4)

        columnas = ("nombre", "inicio", "fin", "estado", "cerrado_por", "observaciones")
        self.periodos_tree = ttk.Treeview(
            contenedor, columns=columnas, show="headings", height=12
        )
        habilitar_scroll_rueda(self.periodos_tree)
        encabezados = {
            "nombre": ("Periodo", 130),
            "inicio": ("Inicio", 100),
            "fin": ("Fin", 100),
            "estado": ("Estado", 100),
            "cerrado_por": ("Cerrado por", 130),
            "observaciones": ("Observaciones", 300),
        }
        for clave, (texto, ancho) in encabezados.items():
            self.periodos_tree.heading(clave, text=texto)
            self.periodos_tree.column(
                clave,
                width=ancho,
                minwidth=60,
                anchor="w" if clave == "observaciones" else "center",
                stretch=False,
            )
        _habilitar_orden_columnas(self.periodos_tree)
        self.periodos_tree.bind(
            "<ButtonRelease-1>",
            lambda evento: _seleccionar_fila_click(self.periodos_tree, evento),
        )
        self.periodos_tree.bind("<Double-1>", lambda _evento: self._editar_periodo())

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.periodos_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.periodos_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_horizontal = ttk.Scrollbar(
            contenedor, orient="horizontal", command=self.periodos_tree.xview
        )
        scrollbar_horizontal.grid(row=1, column=0, sticky="ew")
        self.periodos_tree.configure(
            yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_horizontal.set
        )

    # ------------------------------------------------------------------
    # Datos de notas
    # ------------------------------------------------------------------
    def _cargar_datos_base(self) -> None:
        """Carga periodos, escala y notas del primer grado disponible"""
        if self.servicio is None:
            messagebox.showerror("Notas", "El servicio de notas no está disponible")
            return
        try:
            self._periodos = self.servicio.periodos.get_ordenados()
        except (AttributeError, ValueError, TypeError):
            logger.warning("No se pudieron cargar los periodos", exc_info=True)
            self._periodos = []
        valores = [TODOS] + [periodo.nombre for periodo in self._periodos]
        self.periodo_combo.configure(values=valores)
        if self.periodo_combo.get() not in valores:
            self.periodo_combo.set(self._periodo_en_curso() or TODOS)

        try:
            minima, maxima = self.servicio.escala()
            self._escala = (minima, maxima)
            self._nota_aprobatoria = self.servicio.nota_aprobatoria()
        except (AttributeError, ValueError, TypeError):
            logger.warning("No se pudo leer la escala de calificaciones", exc_info=True)

        self._on_periodo_cambio()
        self._load_periodos()

    def _periodo_en_curso(self) -> str | None:
        """Nombre del periodo abierto más reciente, si existe"""
        for periodo in self._periodos:
            if not periodo.esta_cerrado:
                return periodo.nombre
        return self._periodos[0].nombre if self._periodos else None

    def _periodo_seleccionado(self) -> PeriodoAcademico | None:
        """Periodo elegido en el selector de notas"""
        nombre = self.periodo_combo.get().strip()
        if not nombre or nombre == TODOS:
            return None
        return next((p for p in self._periodos if p.nombre == nombre), None)

    def _on_periodo_cambio(self) -> None:
        """Recarga los grados del periodo y sus notas"""
        periodo = self._periodo_seleccionado()
        self._grados = []
        if self.servicio is not None and periodo is not None:
            try:
                self._grados = self.servicio.grados.get_by_periodo(int(periodo.id))
            except (AttributeError, ValueError, TypeError):
                logger.warning("No se pudieron cargar los grados del periodo", exc_info=True)
                self._grados = []
        valores = [grado.nombre_completo for grado in self._grados] or ["-"]
        self.grado_combo.configure(values=valores)
        if self.grado_combo.get() not in valores:
            self.grado_combo.set(valores[0])
        self._on_grado_cambio()

    def _on_grado_cambio(self) -> None:
        """Recarga las notas del grado elegido"""
        self._matriculas = []
        grado = self._grado_seleccionado()
        if self.servicio is not None and grado is not None:
            try:
                self._matriculas = self.servicio.matriculas.get_by_grado(int(grado.id))
            except (AttributeError, ValueError, TypeError):
                logger.warning("No se pudieron cargar los matriculados", exc_info=True)
                self._matriculas = []
        self._load_notas()

    def _grado_seleccionado(self) -> Grado | None:
        """Grado elegido en el selector de notas"""
        nombre = self.grado_combo.get().strip()
        if not nombre or nombre == "-":
            return None
        return next((g for g in self._grados if g.nombre_completo == nombre), None)

    def _load_data(self) -> None:
        """Recarga completa del módulo (periodos, grados y notas)"""
        self._cargar_datos_base()

    def _load_notas(self) -> None:
        """Carga las notas del grado según el filtro de texto"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._notas = []

        grado = self._grado_seleccionado()
        periodo = self._periodo_seleccionado()
        estado_periodo = "sin periodo"
        if periodo is not None:
            estado_periodo = "cerrado" if periodo.esta_cerrado else "abierto"
        minima, maxima = self._escala
        self.escala_label.configure(
            text=(
                f"Escala: {minima:g} a {maxima:g} · Aprobatoria: {self._nota_aprobatoria:g} · "
                f"Periodo: {estado_periodo} · Grado: "
                f"{grado.nombre_completo if grado else 'sin seleccionar'}"
            )
        )

        if self.servicio is None or grado is None:
            return
        try:
            notas = self.servicio.listar_notas_de_grado(int(grado.id))
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error consultando notas: %s", e)
            messagebox.showerror("Notas", f"No se pudieron consultar las notas:\n{e}")
            return

        termino = self.search_entry.get().strip().lower()
        if termino:
            notas = [
                nota
                for nota in notas
                if termino in (nota.materia or "").lower()
                or termino in self._nombre_estudiante(nota).lower()
            ]
        self._notas = list(notas)
        for nota in self._notas:
            aprobada = float(nota.calificacion) >= self._nota_aprobatoria
            self.tree.insert(
                "",
                "end",
                iid=str(nota.id),
                values=(
                    self._nombre_estudiante(nota),
                    self._cedula_estudiante(nota),
                    nota.materia,
                    f"{float(nota.calificacion):g}",
                    "Aprobada" if aprobada else "Reprobada",
                    nota.registrado_por or "-",
                ),
                tags=("aprobada" if aprobada else "reprobada",),
            )
        try:
            self.tree.tag_configure("reprobada", foreground=COLOR_ERROR)
        except tk.TclError:
            logger.debug("No se pudo colorear la fila reprobada", exc_info=True)

    def _nombre_estudiante(self, nota: NotaFinal) -> str:
        """Nombre del estudiante de una nota (sin recargar la relación)"""
        return nota.estudiante.nombre_completo if nota.estudiante is not None else "-"

    def _cedula_estudiante(self, nota: NotaFinal) -> str:
        """Cédula del estudiante de una nota"""
        if nota.estudiante is None:
            return "-"
        return nota.estudiante.cedula or "-"

    def _nota_seleccionada(self) -> NotaFinal | None:
        """Nota seleccionada en la tabla"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Notas", "Seleccione una nota de la tabla")
            return None
        try:
            nota_id = int(seleccion[0])
        except (TypeError, ValueError):
            return None
        return next((n for n in self._notas if int(n.id) == nota_id), None)

    # ------------------------------------------------------------------
    # Acciones sobre notas
    # ------------------------------------------------------------------
    def _on_nueva_nota(self) -> None:
        """Abre el diálogo de registro de nota"""
        if self.servicio is None:
            return
        grado = self._grado_seleccionado()
        if grado is None:
            messagebox.showinfo("Notas", "Seleccione un periodo y un grado")
            return
        if not self._puede_escribir(grado):
            self._avisar_sin_autorizacion()
            return
        if not self._matriculas:
            messagebox.showinfo(
                "Notas",
                "El grado no tiene estudiantes matriculados; matricúlelos en el módulo "
                "de Estudiantes.",
            )
            return
        dialogo = NotaDialog(self, self.servicio, self.token, grado, self._matriculas)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._on_grado_cambio()

    def _editar_nota(self) -> None:
        """Corrige la calificación de la nota seleccionada"""
        if self.servicio is None:
            return
        nota = self._nota_seleccionada()
        if nota is None:
            return
        grado = next((g for g in self._grados if int(g.id) == int(nota.grado_id)), None)
        if grado is None or not self._puede_escribir(grado):
            self._avisar_sin_autorizacion()
            return
        dialogo = NotaDialog(
            self, self.servicio, self.token, grado, self._matriculas, nota=nota
        )
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._on_grado_cambio()

    def _eliminar_nota(self) -> None:
        """Elimina la nota seleccionada (con autorización y periodo abierto)"""
        if self.servicio is None:
            return
        nota = self._nota_seleccionada()
        if nota is None:
            return
        grado = next((g for g in self._grados if int(g.id) == int(nota.grado_id)), None)
        if grado is None or not self._puede_escribir(grado):
            self._avisar_sin_autorizacion()
            return
        if not messagebox.askyesno(
            "Notas",
            f"¿Eliminar la nota de {self._nombre_estudiante(nota)} en {nota.materia}?\n"
            "La eliminación queda registrada en la auditoría.",
        ):
            return
        try:
            self.servicio.eliminar(int(nota.id), self.token)
        except (ValueError, TypeError, AttributeError) as e:
            messagebox.showerror("Notas", f"No se pudo eliminar la nota:\n{e}")
            return
        self._on_grado_cambio()

    def _avisar_sin_autorizacion(self) -> None:
        """Explica por qué la sesión actual no puede escribir notas"""
        if self.token is None:
            mensaje = (
                "No hay un token académico vigente para esta sesión.\n"
                "Vuelva a iniciar sesión o reabra el módulo."
            )
        else:
            mensaje = (
                "Solo la administración (administrador o gestor) o el profesor\n"
                "asignado al grado pueden registrar o modificar sus notas."
            )
        messagebox.showwarning("Notas", mensaje)

    # ------------------------------------------------------------------
    # Reportes de notas
    # ------------------------------------------------------------------
    def _ver_consolidado(self) -> None:
        """Muestra las notas consolidadas del periodo"""
        if self.servicio is None:
            return
        periodo = self._periodo_seleccionado()
        if periodo is None:
            messagebox.showinfo("Consolidado", "Seleccione un periodo")
            return
        try:
            filas = self.servicio.consolidado_periodo(int(periodo.id))
        except (AttributeError, ValueError, TypeError) as e:
            messagebox.showerror("Consolidado", f"No se pudo generar el consolidado:\n{e}")
            return
        if not filas:
            messagebox.showinfo("Consolidado", "El periodo no tiene notas registradas")
            return
        ConsolidadoDialog(self, periodo, filas)

    def _ver_boletin(self) -> None:
        """Abre el boletín de un estudiante del grado seleccionado"""
        if self.servicio is None:
            return
        periodo = self._periodo_seleccionado()
        if periodo is None or not self._matriculas:
            messagebox.showinfo("Boletín", "Seleccione un periodo y un grado con estudiantes")
            return
        BoletinDialog(self, self.servicio, periodo, self._matriculas)

    def _ver_acta(self) -> None:
        """Abre el acta final del grado seleccionado"""
        if self.servicio is None:
            return
        grado = self._grado_seleccionado()
        if grado is None:
            messagebox.showinfo("Acta", "Seleccione un periodo y un grado")
            return
        try:
            datos = self.servicio.datos_acta(int(grado.id))
        except (AttributeError, ValueError, TypeError) as e:
            messagebox.showerror("Acta", f"No se pudo generar el acta:\n{e}")
            return
        if not datos.get("filas"):
            messagebox.showinfo("Acta", "El grado no tiene estudiantes matriculados")
            return
        ActaDialog(self, datos)

    def _exportar(self) -> None:
        """Exporta las notas mostradas a Excel"""
        if not _verificar_permiso(self.main_window, "report", "exportar notas"):
            return
        if not self._notas:
            messagebox.showinfo("Notas", "No hay notas para exportar")
            return
        filas = [
            {
                "Estudiante": self._nombre_estudiante(nota),
                "Cedula": self._cedula_estudiante(nota),
                "Materia": nota.materia,
                "Calificacion": float(nota.calificacion),
                "Estado": (
                    "Aprobada"
                    if float(nota.calificacion) >= self._nota_aprobatoria
                    else "Reprobada"
                ),
                "Registrada_por": nota.registrado_por or "",
            }
            for nota in self._notas
        ]
        try:
            from pathlib import Path

            from src.config import settings
            from src.utils.exporter import exportar_archivo
            from src.utils.helpers import ensure_directory_exists, get_timestamp

            carpeta = Path(settings.exports_path)
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"notas_{get_timestamp()}.xlsx"
            exportar_archivo(filas, str(destino), hoja="Notas")
            messagebox.showinfo("Notas", f"Exportado en:\n{destino}")
        except (OSError, ValueError, ImportError) as e:
            logger.warning("No se pudo exportar las notas", exc_info=True)
            messagebox.showerror("Notas", f"No se pudo exportar:\n{e}")

    # ------------------------------------------------------------------
    # Periodos académicos
    # ------------------------------------------------------------------
    def _load_periodos(self) -> None:
        """Carga la tabla de periodos"""
        for item in self.periodos_tree.get_children():
            self.periodos_tree.delete(item)
        for periodo in self._periodos:
            self.periodos_tree.insert(
                "",
                "end",
                iid=str(periodo.id),
                values=(
                    periodo.nombre,
                    format_date(periodo.fecha_inicio) if periodo.fecha_inicio else "-",
                    format_date(periodo.fecha_fin) if periodo.fecha_fin else "-",
                    "Cerrado" if periodo.esta_cerrado else "Abierto",
                    periodo.cerrado_por or "-",
                    periodo.observaciones or "",
                ),
            )

    def _periodo_seleccionado_tabla(self) -> PeriodoAcademico | None:
        """Periodo seleccionado en la pestaña de periodos"""
        seleccion = self.periodos_tree.selection()
        if not seleccion:
            messagebox.showinfo("Periodos", "Seleccione un periodo de la tabla")
            return None
        try:
            periodo_id = int(seleccion[0])
        except (TypeError, ValueError):
            return None
        return next((p for p in self._periodos if int(p.id) == periodo_id), None)

    def _on_new_periodo(self) -> None:
        """Abre el diálogo de alta de periodo"""
        if not _verificar_permiso(self.main_window, "create", "crear periodos"):
            return
        dialogo = PeriodoDialog(self, self.servicio)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._cargar_datos_base()

    def _editar_periodo(self) -> None:
        """Edita nombre, fechas u observaciones del periodo seleccionado"""
        if not _verificar_permiso(self.main_window, "update", "editar periodos"):
            return
        periodo = self._periodo_seleccionado_tabla()
        if periodo is None:
            return
        dialogo = PeriodoDialog(self, self.servicio, periodo)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._cargar_datos_base()

    def _cerrar_periodo(self) -> None:
        """Cierra el periodo seleccionado con el token académico"""
        periodo = self._periodo_seleccionado_tabla()
        if periodo is None:
            return
        if not self._requiere_administrador("cerrar periodos académicos"):
            return
        if periodo.esta_cerrado:
            messagebox.showinfo("Periodos", f"El periodo {periodo.nombre} ya está cerrado")
            return
        if not messagebox.askyesno(
            "Periodos",
            f"¿Cerrar el periodo {periodo.nombre}?\n"
            "Sus notas quedarán bloqueadas de forma permanente hasta que\n"
            "un administrador reabra el periodo.",
        ):
            return
        self._ejecutar_cambio_estado(periodo, cerrar=True)

    def _reabrir_periodo(self) -> None:
        """Reabre el periodo seleccionado (solo administrador)"""
        periodo = self._periodo_seleccionado_tabla()
        if periodo is None:
            return
        if not self._requiere_administrador("reabrir periodos académicos"):
            return
        if not periodo.esta_cerrado:
            messagebox.showinfo("Periodos", f"El periodo {periodo.nombre} ya está abierto")
            return
        if not messagebox.askyesno(
            "Periodos",
            f"¿Reabrir el periodo {periodo.nombre}?\n"
            "La reapertura habilita otra vez la edición de notas y queda auditada.",
        ):
            return
        self._ejecutar_cambio_estado(periodo, cerrar=False)

    def _requiere_administrador(self, accion: str) -> bool:
        """Cierre y reapertura exigen rol administrador y token vigente"""
        if self.main_window is None or not self.main_window.tiene_permiso("config"):
            messagebox.showwarning(
                "Acceso denegado",
                f"Solo un administrador puede {accion}",
            )
            return False
        if self.token is None:
            messagebox.showwarning(
                "Periodos",
                "No hay un token académico vigente; vuelva a iniciar sesión.",
            )
            return False
        return True

    def _ejecutar_cambio_estado(self, periodo: PeriodoAcademico, cerrar: bool) -> None:
        """Cierra o reabre el periodo y refresca la vista"""
        if self.servicio is None:
            return
        try:
            from src.services import AcademicoService

            academico = AcademicoService(self.session)
            if cerrar:
                academico.cerrar_periodo(int(periodo.id), self.token)
            else:
                academico.reabrir_periodo(int(periodo.id), self.token)
        except (ValueError, TypeError, AttributeError, ImportError) as e:
            logger.error("No se pudo cambiar el estado del periodo: %s", e)
            messagebox.showerror("Periodos", f"No se pudo completar la operación:\n{e}")
            return
        self._cargar_datos_base()


# ----------------------------------------------------------------------
# Diálogos
# ----------------------------------------------------------------------
class _DialogoBase(ctk.CTkToplevel):
    """Base común de los diálogos del módulo: modal, centrado y con estado"""

    def __init__(self, parent, titulo: str, geometria: str):
        super().__init__(parent)
        self.guardado = False
        self.title(titulo)
        self.geometry(geometria)
        self.resizable(False, False)
        self.transient(parent)
        self.bind("<Escape>", lambda _e: self.destroy())

    def _preparar_modal(self) -> None:
        """Centra el diálogo y captura el foco"""
        try:
            self.update_idletasks()
            self.grab_set()
        except tk.TclError:
            logger.debug("Diálogo sin grab establecido", exc_info=True)


class NotaDialog(_DialogoBase):
    """Registro y corrección de una nota final"""

    def __init__(
        self,
        parent,
        servicio: NotaService | None,
        token: str | None,
        grado: Grado,
        matriculas: list[Matricula],
        nota: NotaFinal | None = None,
    ):
        super().__init__(parent, "Corregir nota" if nota else "Registrar nota", "520x420")
        self.servicio = servicio
        self.token = token
        self.grado = grado
        self.matriculas = matriculas
        self.nota = nota
        self._create_widgets()
        self._preparar_modal()

    def _create_widgets(self) -> None:
        """Formulario de la nota"""
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)
        fila = 0

        def etiqueta(texto: str) -> None:
            nonlocal fila
            ctk.CTkLabel(contenedor, text=texto, text_color=COLORES["texto"]).grid(
                row=fila, column=0, sticky="w", pady=6
            )

        etiqueta("Grado:")
        ctk.CTkLabel(
            contenedor,
            text=self.grado.nombre_completo,
            text_color=COLORES["texto_suave"],
        ).grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        if self.nota is None:
            etiqueta("Estudiante:")
            self.estudiante_combo = ctk.CTkComboBox(
                contenedor,
                width=340,
                values=[
                    f"{m.estudiante.cedula or 's/c'} - {m.estudiante.nombre_completo}"
                    for m in self.matriculas
                    if m.estudiante is not None
                ],
            )
            self.estudiante_combo.grid(row=fila, column=1, sticky="w", pady=6)
            fila += 1

            etiqueta("Materia:")
            self.materia_entry = ctk.CTkEntry(
                contenedor, width=260, placeholder_text="Ej. Matemática"
            )
            self.materia_entry.grid(row=fila, column=1, sticky="w", pady=6)
            fila += 1
        else:
            etiqueta("Estudiante:")
            ctk.CTkLabel(
                contenedor,
                text=(
                    self.nota.estudiante.nombre_completo
                    if self.nota.estudiante is not None
                    else "-"
                ),
                text_color=COLORES["texto_suave"],
            ).grid(row=fila, column=1, sticky="w", pady=6)
            fila += 1
            etiqueta("Materia:")
            ctk.CTkLabel(
                contenedor, text=self.nota.materia, text_color=COLORES["texto_suave"]
            ).grid(row=fila, column=1, sticky="w", pady=6)
            fila += 1

        etiqueta("Calificación:")
        self.calificacion_entry = ctk.CTkEntry(contenedor, width=110)
        self.calificacion_entry.grid(row=fila, column=1, sticky="w", pady=6)
        if self.nota is not None:
            self.calificacion_entry.insert(0, f"{float(self.nota.calificacion):g}")
        fila += 1

        etiqueta("Observaciones:")
        self.observaciones_text = ctk.CTkTextbox(contenedor, width=320, height=60)
        self.observaciones_text.grid(row=fila, column=1, sticky="w", pady=6)
        if self.nota is not None and self.nota.observaciones:
            self.observaciones_text.insert("1.0", self.nota.observaciones)
        fila += 1

        self.error_label = ctk.CTkLabel(
            contenedor,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_ERROR,
            anchor="w",
            justify="left",
            wraplength=460,
        )
        self.error_label.grid(row=fila, column=0, columnspan=2, sticky="w", pady=(8, 0))

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(botones, text="Guardar", width=120, command=self._guardar).pack(
            side="right", padx=4
        )
        ctk.CTkButton(
            botones,
            text="Cancelar",
            width=110,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self.destroy,
        ).pack(side="right", padx=4)

    def _estudiante_id(self) -> int | None:
        """Identificador del estudiante elegido"""
        etiqueta = self.estudiante_combo.get().strip()
        for matricula in self.matriculas:
            if matricula.estudiante is None:
                continue
            if (
                f"{matricula.estudiante.cedula or 's/c'} - {matricula.estudiante.nombre_completo}"
                == etiqueta
            ):
                return int(matricula.estudiante_id)
        return None

    def _guardar(self) -> None:
        """Registra o corrige la nota con las reglas del servicio"""
        if self.servicio is None:
            messagebox.showerror("Notas", "El servicio de notas no está disponible")
            return
        calificacion = self.calificacion_entry.get().strip().replace(",", ".")
        observaciones = self.observaciones_text.get("1.0", "end").strip() or None
        try:
            if self.nota is None:
                estudiante_id = self._estudiante_id()
                self.servicio.registrar(
                    {
                        "grado_id": int(self.grado.id),
                        "estudiante_id": estudiante_id,
                        "materia": self.materia_entry.get().strip(),
                        "calificacion": calificacion,
                        "observaciones": observaciones,
                    },
                    self.token,
                )
            else:
                self.servicio.actualizar(
                    int(self.nota.id), calificacion, self.token, observaciones
                )
        except (ValueError, TypeError, AttributeError) as e:
            self.error_label.configure(text=str(e))
            return
        self.guardado = True
        self.destroy()


class PeriodoDialog(_DialogoBase):
    """Alta y edición de un periodo académico"""

    def __init__(
        self,
        parent,
        servicio: NotaService | None,
        periodo: PeriodoAcademico | None = None,
    ):
        super().__init__(parent, "Editar periodo" if periodo else "Nuevo periodo", "480x360")
        self.servicio = servicio
        self.periodo = periodo
        self._create_widgets()
        self._preparar_modal()

    def _create_widgets(self) -> None:
        """Formulario del periodo"""
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)
        fila = 0

        def etiqueta(texto: str) -> None:
            nonlocal fila
            ctk.CTkLabel(contenedor, text=texto, text_color=COLORES["texto"]).grid(
                row=fila, column=0, sticky="w", pady=6
            )

        etiqueta("Nombre:")
        self.nombre_entry = ctk.CTkEntry(
            contenedor, width=220, placeholder_text="Ej. 2025-2026"
        )
        self.nombre_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Fecha de inicio:")
        self.inicio_entry = ctk.CTkEntry(contenedor, width=140, placeholder_text="dd/mm/aaaa")
        self.inicio_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Fecha de fin:")
        self.fin_entry = ctk.CTkEntry(contenedor, width=140, placeholder_text="dd/mm/aaaa")
        self.fin_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Observaciones:")
        self.observaciones_text = ctk.CTkTextbox(contenedor, width=300, height=60)
        self.observaciones_text.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        self.error_label = ctk.CTkLabel(
            contenedor,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_ERROR,
            anchor="w",
            justify="left",
            wraplength=420,
        )
        self.error_label.grid(row=fila, column=0, columnspan=2, sticky="w", pady=(8, 0))

        if self.periodo is not None:
            self.nombre_entry.insert(0, self.periodo.nombre)
            if self.periodo.fecha_inicio:
                self.inicio_entry.insert(0, format_date(self.periodo.fecha_inicio))
            if self.periodo.fecha_fin:
                self.fin_entry.insert(0, format_date(self.periodo.fecha_fin))
            self.observaciones_text.insert("1.0", self.periodo.observaciones or "")

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(botones, text="Guardar", width=120, command=self._guardar).pack(
            side="right", padx=4
        )
        ctk.CTkButton(
            botones,
            text="Cancelar",
            width=110,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self.destroy,
        ).pack(side="right", padx=4)

    def _guardar(self) -> None:
        """Crea o actualiza el periodo con las reglas del servicio académico"""
        if self.servicio is None:
            messagebox.showerror("Periodos", "El servicio académico no está disponible")
            return
        datos: dict[str, Any] = {
            "nombre": self.nombre_entry.get().strip(),
            "fecha_inicio": parse_date(self.inicio_entry.get().strip()),
            "fecha_fin": parse_date(self.fin_entry.get().strip()),
            "observaciones": self.observaciones_text.get("1.0", "end").strip(),
        }
        try:
            from src.services import AcademicoService

            academico = AcademicoService(self.servicio.session)
            if self.periodo is None:
                academico.crear_periodo(datos)
            else:
                academico.actualizar_periodo(int(self.periodo.id), datos)
        except (ValueError, TypeError, AttributeError, ImportError) as e:
            self.error_label.configure(text=str(e))
            return
        self.guardado = True
        self.destroy()


class ConsolidadoDialog(ctk.CTkToplevel):
    """Vista de solo lectura de las notas consolidadas de un periodo"""

    def __init__(self, parent, periodo: PeriodoAcademico, filas: list[dict[str, Any]]):
        super().__init__(parent)
        self.title(f"Consolidado {periodo.nombre}")
        self.geometry("860x520")
        self.transient(parent)
        self.bind("<Escape>", lambda _e: self.destroy())

        ctk.CTkLabel(
            self,
            text=f"Consolidado del periodo {periodo.nombre} · {len(filas)} notas",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORES["texto"],
        ).pack(anchor="w", padx=16, pady=(14, 6))

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("grado", "estudiante", "cedula", "materia", "calificacion")
        arbol = ttk.Treeview(contenedor, columns=columnas, show="headings", height=18)
        habilitar_scroll_rueda(arbol)
        for clave, (texto, ancho) in {
            "grado": ("Grado", 140),
            "estudiante": ("Estudiante", 240),
            "cedula": ("Cédula", 95),
            "materia": ("Materia", 170),
            "calificacion": ("Calificación", 100),
        }.items():
            arbol.heading(clave, text=texto)
            arbol.column(
                clave,
                width=ancho,
                minwidth=60,
                anchor="w" if clave in ("estudiante", "materia") else "center",
                stretch=False,
            )
        arbol.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=arbol.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        arbol.configure(yscrollcommand=scrollbar.set)

        for fila in filas:
            arbol.insert(
                "",
                "end",
                values=(
                    fila.get("grado", ""),
                    fila.get("estudiante", ""),
                    fila.get("cedula") or "-",
                    fila.get("materia", ""),
                    f"{float(fila.get('calificacion', 0)):g}",
                ),
            )
        ctk.CTkButton(self, text="Cerrar", width=110, command=self.destroy).pack(
            anchor="e", padx=16, pady=(0, 14)
        )


class BoletinDialog(ctk.CTkToplevel):
    """Selección de estudiante y vista del boletín de un periodo"""

    def __init__(
        self,
        parent,
        servicio: NotaService,
        periodo: PeriodoAcademico,
        matriculas: list[Matricula],
    ):
        super().__init__(parent)
        self.servicio = servicio
        self.periodo = periodo
        self.matriculas = [m for m in matriculas if m.estudiante is not None]
        self.title(f"Boletín {periodo.nombre}")
        self.geometry("520x200")
        self.transient(parent)
        self.bind("<Escape>", lambda _e: self.destroy())

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(contenedor, text="Estudiante:", text_color=COLORES["texto"]).grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.estudiante_combo = ctk.CTkComboBox(
            contenedor,
            width=340,
            values=[
                f"{m.estudiante.cedula or 's/c'} - {m.estudiante.nombre_completo}"
                for m in self.matriculas
            ],
        )
        self.estudiante_combo.grid(row=0, column=1, sticky="w", pady=6)
        ctk.CTkButton(contenedor, text="Ver boletín", width=120, command=self._mostrar).grid(
            row=1, column=1, sticky="e", pady=(12, 0)
        )
        try:
            self.grab_set()
        except tk.TclError:
            logger.debug("Boletín sin grab establecido", exc_info=True)

    def _estudiante_id(self) -> int | None:
        """Identificador del estudiante elegido"""
        etiqueta = self.estudiante_combo.get().strip()
        for matricula in self.matriculas:
            if (
                f"{matricula.estudiante.cedula or 's/c'} - {matricula.estudiante.nombre_completo}"
                == etiqueta
            ):
                return int(matricula.estudiante_id)
        return None

    def _mostrar(self) -> None:
        """Genera y muestra el texto del boletín"""
        estudiante_id = self._estudiante_id()
        if estudiante_id is None:
            messagebox.showinfo("Boletín", "Seleccione un estudiante")
            return
        try:
            datos = self.servicio.datos_boletin(estudiante_id, int(self.periodo.id))
        except (ValueError, TypeError, AttributeError) as e:
            messagebox.showerror("Boletín", f"No se pudo generar el boletín:\n{e}")
            return

        lineas = [
            f"BOLETÍN DE CALIFICACIONES — {datos['periodo']['nombre']}",
            "=" * 52,
            f"Estudiante: {datos['estudiante']['nombre']}",
            f"Cédula: {datos['estudiante'].get('cedula') or 's/c'}",
            f"Nivel: {datos['estudiante'].get('nivel', '-')}",
        ]
        grado = datos.get("grado")
        if grado:
            lineas.append(f"Grado: {grado['nombre']}")
        lineas.append(f"Periodo: {datos['periodo']['nombre']} ({datos['periodo']['estado']})")
        lineas.append("-" * 52)
        if datos["notas"]:
            for nota in datos["notas"]:
                lineas.append(f"  {nota['materia']:<30} {nota['calificacion']:>6.2f}")
        else:
            lineas.append("  (sin notas registradas)")
        lineas.append("-" * 52)
        promedio = datos.get("promedio")
        lineas.append(f"Promedio: {promedio if promedio is not None else '-'}")
        lineas.append(
            f"Escala: {datos['nota_minima']:g} a {datos['nota_maxima']:g} · "
            f"Aprobatoria: {datos['nota_aprobatoria']:g}"
        )
        InfoDialog(self, f"Boletín — {datos['estudiante']['nombre']}", "\n".join(lineas))


class ActaDialog(ctk.CTkToplevel):
    """Vista de solo lectura del acta final de un grado"""

    def __init__(self, parent, datos: dict[str, Any]):
        super().__init__(parent)
        grado = datos.get("grado", {})
        self.title(f"Acta {grado.get('nombre', '')}".strip())
        self.geometry("900x540")
        self.transient(parent)
        self.bind("<Escape>", lambda _e: self.destroy())

        ctk.CTkLabel(
            self,
            text=(
                f"Acta final · {grado.get('nombre', '')} · "
                f"{datos.get('periodo', {}).get('nombre', '')}"
            ),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORES["texto"],
        ).pack(anchor="w", padx=16, pady=(14, 6))

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        materias = list(datos.get("materias") or [])
        columnas = ["estudiante", "cedula"] + [f"materia_{i}" for i in range(len(materias))]
        columnas.append("promedio")
        arbol = ttk.Treeview(contenedor, columns=columnas, show="headings", height=18)
        habilitar_scroll_rueda(arbol)

        def encabezado(clave: str, texto: str, ancho: int) -> None:
            arbol.heading(clave, text=texto)
            arbol.column(clave, width=ancho, minwidth=60, anchor="center", stretch=False)

        encabezado("estudiante", "Estudiante", 230)
        encabezado("cedula", "Cédula", 95)
        for indice, materia in enumerate(materias):
            encabezado(f"materia_{indice}", materia, 90)
        encabezado("promedio", "Promedio", 90)

        arbol.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=arbol.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_horizontal = ttk.Scrollbar(
            contenedor, orient="horizontal", command=arbol.xview
        )
        scrollbar_horizontal.grid(row=1, column=0, sticky="ew")
        arbol.configure(yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_horizontal.set)

        aprobatoria = float(datos.get("nota_aprobatoria", 0) or 0)
        for fila in datos.get("filas") or []:
            notas = fila.get("notas") or {}
            valores: list[Any] = [fila.get("estudiante", ""), fila.get("cedula") or "-"]
            reprobadas = False
            for materia in materias:
                calificacion = notas.get(materia)
                if calificacion is None:
                    valores.append("-")
                else:
                    valores.append(f"{float(calificacion):g}")
                    if float(calificacion) < aprobatoria:
                        reprobadas = True
            promedio = fila.get("promedio")
            valores.append(f"{float(promedio):g}" if promedio is not None else "-")
            arbol.insert(
                "",
                "end",
                values=tuple(valores),
                tags=("reprobadas" if reprobadas else "ok",),
            )
        try:
            arbol.tag_configure("reprobadas", foreground=COLOR_ERROR)
        except tk.TclError:
            logger.debug("No se pudo colorear el acta", exc_info=True)

        leyenda = (
            f"Profesor: {datos.get('profesor') or '-'} · "
            f"Escala: {datos.get('nota_minima', 0):g} a {datos.get('nota_maxima', 0):g} · "
            f"Aprobatoria: {aprobatoria:g}"
        )
        ctk.CTkLabel(
            self, text=leyenda, font=ctk.CTkFont(size=11), text_color=COLORES["texto_suave"]
        ).pack(anchor="w", padx=16, pady=(0, 4))
        ctk.CTkButton(self, text="Cerrar", width=110, command=self.destroy).pack(
            anchor="e", padx=16, pady=(0, 14)
        )
