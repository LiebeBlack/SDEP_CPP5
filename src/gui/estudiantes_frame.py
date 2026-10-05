"""
Módulo de Estudiantes

Interfaz del legajo estudiantil y de la estructura escolar: estudiantes,
grados/secciones y matrículas. Los periodos académicos y las calificaciones
viven en el módulo de Notas; aquí se administra todo lo demás del subdominio
académico.

La interfaz no reimplementa reglas: cada validación (cédula duplicada, nivel
frente al grado, una sola matrícula activa por año) la resuelve el
``AcademicoService`` y su mensaje de error llega tal cual al usuario. El
módulo se organiza en pestañas para no superar el tope de nueve atajos
directos (`Ctrl+1..9`) que impone la ventana principal.
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from src.gui.frames import _habilitar_orden_columnas, _seleccionar_fila_click
from src.gui.theme import COLORES, habilitar_scroll_rueda
from src.models import Estudiante, Genero, Grado, NivelEducativo, PeriodoAcademico
from src.utils.helpers import format_date, parse_date

if TYPE_CHECKING:
    from src.services import AcademicoService

logger = logging.getLogger(__name__)

NIVELES = [NivelEducativo.INICIAL.value, NivelEducativo.SECUNDARIA.value]
GENEROS = [Genero.MASCULINO.value, Genero.FEMENINO.value]
ETIQUETAS_NIVEL = {"inicial": "Inicial", "secundaria": "Secundaria"}
ETIQUETAS_GENERO = {"": "Sin especificar"}
ETIQUETAS_GENERO.update({valor: valor.capitalize() for valor in GENEROS})

SIN_ASIGNAR = "Sin asignar"
TODOS = "Todos"
COLOR_ERROR = "#e74c3c"


def _verificar_permiso(main_window, permiso: str, accion: str) -> bool:
    """Verifica el permiso operativo antes de ejecutar una acción."""
    if main_window is not None and main_window.tiene_permiso(permiso):
        return True
    messagebox.showwarning("Acceso denegado", f"Su rol no tiene permiso para {accion}")
    return False


def _titulo_nivel(nivel: object) -> str:
    """Etiqueta legible del nivel educativo"""
    return ETIQUETAS_NIVEL.get(str(nivel), str(nivel))


class EstudiantesFrame(ctk.CTkFrame):
    """Frame del módulo de estudiantes, grados y matrículas"""

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self.servicio: AcademicoService | None = self._crear_servicio()
        self._estudiantes: list[Estudiante] = []
        self._periodos: list[PeriodoAcademico] = []
        self._grados: list[Grado] = []
        self._profesores: list[tuple[int, str]] = []
        self._create_widgets()
        self._cargar_combos()
        self._load_estudiantes()
        self._load_grados()

    def _crear_servicio(self) -> AcademicoService | None:
        """Crea el servicio académico con la sesión activa"""
        try:
            from src.services import AcademicoService

            return AcademicoService(self.session)
        except (ImportError, AttributeError) as e:
            logger.error("No se pudo inicializar el servicio académico: %s", e)
            return None

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Crea las pestañas de estudiantes y de grados/matrículas"""
        ctk.CTkLabel(
            self,
            text="Gestión de Estudiantes",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORES["texto"],
        ).pack(pady=(14, 6), padx=20, anchor="w")

        self.tabview = ctk.CTkTabview(self, fg_color=COLORES["panel"])
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        tab_estudiantes = self.tabview.add("Estudiantes")
        tab_grados = self.tabview.add("Grados y matrículas")

        self._crear_tab_estudiantes(tab_estudiantes)
        self._crear_tab_grados(tab_grados)

    def _crear_tab_estudiantes(self, parent) -> None:
        """Barra de búsqueda, tabla y resumen de estudiantes"""
        barra = ctk.CTkFrame(parent, fg_color="transparent")
        barra.pack(fill="x", padx=8, pady=(8, 4))

        self.search_entry = ctk.CTkEntry(
            barra, width=230, placeholder_text="Buscar por nombre o cédula"
        )
        self.search_entry.grid(row=0, column=0, padx=(4, 8), pady=6, sticky="w")
        self.search_entry.bind("<Return>", lambda _e: self._load_estudiantes())

        ctk.CTkLabel(barra, text="Nivel:", text_color=COLORES["texto"]).grid(
            row=0, column=1, padx=(4, 4), pady=6, sticky="w"
        )
        self.nivel_combo = ctk.CTkComboBox(
            barra, width=130, values=[TODOS] + NIVELES, command=lambda _v: self._load_estudiantes()
        )
        self.nivel_combo.grid(row=0, column=2, padx=(0, 8), pady=6, sticky="w")
        self.nivel_combo.set(TODOS)

        ctk.CTkLabel(barra, text="Estado:", text_color=COLORES["texto"]).grid(
            row=0, column=3, padx=(4, 4), pady=6, sticky="w"
        )
        self.estado_combo = ctk.CTkComboBox(
            barra,
            width=110,
            values=["Activos", TODOS],
            command=lambda _v: self._load_estudiantes(),
        )
        self.estado_combo.grid(row=0, column=4, padx=(0, 8), pady=6, sticky="w")
        self.estado_combo.set("Activos")

        ctk.CTkButton(barra, text="🔍 Buscar", width=88, command=self._load_estudiantes).grid(
            row=0, column=5, padx=4, pady=6, sticky="w"
        )

        acciones = ctk.CTkFrame(parent, fg_color="transparent")
        acciones.pack(fill="x", padx=8, pady=(0, 4))
        for columna in range(4):
            acciones.grid_columnconfigure(columna, weight=1, uniform="acciones_est")

        ctk.CTkButton(
            acciones,
            text="➕ Nuevo estudiante",
            height=34,
            command=self._on_new_estudiante,
        ).grid(row=0, column=0, padx=4, pady=2, sticky="ew")
        ctk.CTkButton(
            acciones,
            text="✏️ Editar",
            height=34,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._editar_estudiante,
        ).grid(row=0, column=1, padx=4, pady=2, sticky="ew")
        ctk.CTkButton(
            acciones,
            text="🔁 Activar / Retirar",
            height=34,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._toggle_activo,
        ).grid(row=0, column=2, padx=4, pady=2, sticky="ew")
        ctk.CTkButton(
            acciones,
            text="📊 Exportar",
            height=34,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._exportar,
        ).grid(row=0, column=3, padx=4, pady=2, sticky="ew")

        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=8, pady=4)

        columnas = ("cedula", "estudiante", "nivel", "edad", "representante", "telefono", "estado")
        self.tree = ttk.Treeview(contenedor, columns=columnas, show="headings", height=12)
        habilitar_scroll_rueda(self.tree)
        encabezados = {
            "cedula": ("Cédula", 100),
            "estudiante": ("Estudiante", 240),
            "nivel": ("Nivel", 95),
            "edad": ("Edad", 55),
            "representante": ("Representante", 200),
            "telefono": ("Teléfono", 110),
            "estado": ("Estado", 90),
        }
        for clave, (texto, ancho) in encabezados.items():
            self.tree.heading(clave, text=texto)
            self.tree.column(
                clave,
                width=ancho,
                minwidth=50,
                anchor="w" if clave in ("estudiante", "representante") else "center",
                stretch=False,
            )
        _habilitar_orden_columnas(self.tree)
        self.tree.bind(
            "<ButtonRelease-1>", lambda evento: _seleccionar_fila_click(self.tree, evento)
        )
        self.tree.bind("<Double-1>", lambda _evento: self._editar_estudiante())

        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        scrollbar_horizontal = ttk.Scrollbar(
            contenedor, orient="horizontal", command=self.tree.xview
        )
        scrollbar_horizontal.grid(row=1, column=0, sticky="ew")
        self.tree.configure(
            yscrollcommand=scrollbar.set, xscrollcommand=scrollbar_horizontal.set
        )

        self.stats_label = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORES["texto_suave"],
            anchor="w",
        )
        self.stats_label.pack(fill="x", padx=12, pady=(0, 6))

    def _crear_tab_grados(self, parent) -> None:
        """Grados del periodo seleccionado y sus estudiantes matriculados"""
        barra = ctk.CTkFrame(parent, fg_color="transparent")
        barra.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(barra, text="Periodo:", text_color=COLORES["texto"]).grid(
            row=0, column=0, padx=(4, 4), pady=6, sticky="w"
        )
        self.periodo_combo = ctk.CTkComboBox(
            barra, width=180, values=[TODOS], command=lambda _v: self._load_grados()
        )
        self.periodo_combo.grid(row=0, column=1, padx=(0, 12), pady=6, sticky="w")
        self.periodo_combo.set(TODOS)

        ctk.CTkButton(barra, text="➕ Nuevo grado", width=130, command=self._on_new_grado).grid(
            row=0, column=2, padx=4, pady=6, sticky="w"
        )
        ctk.CTkButton(
            barra,
            text="✏️ Editar grado",
            width=120,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._editar_grado,
        ).grid(row=0, column=3, padx=4, pady=6, sticky="w")
        ctk.CTkButton(
            barra,
            text="👩‍🏫 Asignar profesor",
            width=150,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._asignar_profesor,
        ).grid(row=0, column=4, padx=4, pady=6, sticky="w")

        paneles = ctk.CTkFrame(parent, fg_color="transparent")
        paneles.pack(fill="both", expand=True, padx=8, pady=4)
        paneles.grid_rowconfigure(0, weight=1)
        paneles.grid_columnconfigure(0, weight=3)
        paneles.grid_columnconfigure(1, weight=2)

        self._crear_tabla_grados(paneles)
        self._crear_tabla_matriculas(paneles)

    def _crear_tabla_grados(self, parent) -> None:
        """Tabla de grados/secciones del periodo seleccionado"""
        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        contenedor.grid_rowconfigure(0, weight=1)
        contenedor.grid_columnconfigure(0, weight=1)

        columnas = ("grado", "nivel", "periodo", "profesor", "matriculados")
        self.grados_tree = ttk.Treeview(contenedor, columns=columnas, show="headings", height=12)
        habilitar_scroll_rueda(self.grados_tree)
        encabezados = {
            "grado": ("Grado", 150),
            "nivel": ("Nivel", 95),
            "periodo": ("Periodo", 120),
            "profesor": ("Profesor asignado", 190),
            "matriculados": ("Matriculados", 95),
        }
        for clave, (texto, ancho) in encabezados.items():
            self.grados_tree.heading(clave, text=texto)
            self.grados_tree.column(
                clave,
                width=ancho,
                minwidth=60,
                anchor="w" if clave == "profesor" else "center",
                stretch=False,
            )
        _habilitar_orden_columnas(self.grados_tree)
        self.grados_tree.bind(
            "<ButtonRelease-1>",
            lambda evento: _seleccionar_fila_click(self.grados_tree, evento),
        )
        self.grados_tree.bind("<Double-1>", lambda _evento: self._editar_grado())
        self.grados_tree.bind("<<TreeviewSelect>>", lambda _evento: self._on_grado_select())

        self.grados_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.grados_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.grados_tree.configure(yscrollcommand=scrollbar.set)

    def _crear_tabla_matriculas(self, parent) -> None:
        """Estudiantes matriculados en el grado seleccionado"""
        contenedor = ctk.CTkFrame(parent, fg_color="transparent")
        contenedor.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        cabecera = ctk.CTkFrame(contenedor, fg_color="transparent")
        cabecera.pack(fill="x")
        self.matriculas_label = ctk.CTkLabel(
            cabecera,
            text="Estudiantes matriculados",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORES["texto"],
            anchor="w",
        )
        self.matriculas_label.pack(side="left", padx=4)
        ctk.CTkButton(
            contenedor,
            text="➕ Matricular estudiante",
            height=30,
            command=self._matricular,
        ).pack(fill="x", padx=4, pady=4)
        ctk.CTkButton(
            contenedor,
            text="🚪 Retirar del grado",
            height=30,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._retirar_matricula,
        ).pack(fill="x", padx=4, pady=(0, 4))

        tabla = ctk.CTkFrame(contenedor, fg_color="transparent")
        tabla.pack(fill="both", expand=True)
        tabla.grid_rowconfigure(0, weight=1)
        tabla.grid_columnconfigure(0, weight=1)

        columnas = ("estudiante", "cedula", "fecha")
        self.matriculas_tree = ttk.Treeview(tabla, columns=columnas, show="headings", height=10)
        habilitar_scroll_rueda(self.matriculas_tree)
        for clave, (texto, ancho) in {
            "estudiante": ("Estudiante", 200),
            "cedula": ("Cédula", 95),
            "fecha": ("Matriculado", 95),
        }.items():
            self.matriculas_tree.heading(clave, text=texto)
            self.matriculas_tree.column(
                clave,
                width=ancho,
                minwidth=60,
                anchor="w" if clave == "estudiante" else "center",
                stretch=False,
            )
        self.matriculas_tree.bind(
            "<ButtonRelease-1>",
            lambda evento: _seleccionar_fila_click(self.matriculas_tree, evento),
        )
        self.matriculas_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(tabla, orient="vertical", command=self.matriculas_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.matriculas_tree.configure(yscrollcommand=scrollbar.set)

    # ------------------------------------------------------------------
    # Datos de estudiantes
    # ------------------------------------------------------------------
    def _load_data(self) -> None:
        """Recarga completa (se usa al volver a la pestaña de estudiantes)"""
        self._cargar_combos()
        self._load_estudiantes()
        self._load_grados()

    def _load_estudiantes(self) -> None:
        """Carga los estudiantes según búsqueda, nivel y estado elegidos"""
        if self.servicio is None:
            messagebox.showerror(
                "Estudiantes", "El servicio académico no está disponible"
            )
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        termino = self.search_entry.get().strip()
        nivel = self.nivel_combo.get().strip()
        solo_activos = self.estado_combo.get().strip() != TODOS

        try:
            if termino:
                estudiantes = self.servicio.buscar_estudiantes(termino)
            elif nivel != TODOS:
                estudiantes = self.servicio.listar_estudiantes_por_nivel(nivel)
            elif solo_activos:
                estudiantes = self.servicio.listar_estudiantes_activos()
            else:
                estudiantes = self.servicio.listar_estudiantes()
            if solo_activos:
                estudiantes = [e for e in estudiantes if e.activo]
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error consultando estudiantes: %s", e)
            messagebox.showerror("Estudiantes", f"No se pudieron consultar los estudiantes:\n{e}")
            return

        self._estudiantes = list(estudiantes)
        for estudiante in self._estudiantes:
            self.tree.insert(
                "",
                "end",
                iid=str(estudiante.id),
                values=(
                    estudiante.cedula or "-",
                    estudiante.nombre_completo,
                    _titulo_nivel(estudiante.nivel_valor),
                    estudiante.edad if estudiante.edad is not None else "-",
                    estudiante.representante or "-",
                    estudiante.telefono or estudiante.telefono_representante or "-",
                    "Activo" if estudiante.activo else "Retirado",
                ),
            )

        self._actualizar_estadisticas()

    def _actualizar_estadisticas(self) -> None:
        """Resumen del módulo en el pie de la pestaña"""
        if self.servicio is None:
            return
        try:
            datos = self.servicio.estadisticas()
        except (AttributeError, ValueError, TypeError):
            logger.debug("No se pudieron calcular las estadísticas académicas", exc_info=True)
            self.stats_label.configure(text="")
            return
        por_nivel = datos.get("por_nivel") or {}
        detalle_niveles = " · ".join(
            f"{_titulo_nivel(clave)}: {valor}" for clave, valor in por_nivel.items()
        )
        texto = (
            f"Estudiantes: {datos.get('estudiantes', 0)} · "
            f"Activos: {datos.get('estudiantes_activos', 0)}"
        )
        if detalle_niveles:
            texto += f" · {detalle_niveles}"
        texto += (
            f" · Periodos: {datos.get('periodos', 0)}"
            f" · Grados: {datos.get('grados', 0)}"
            f" · Matrículas activas: {datos.get('matriculas_activas', 0)}"
        )
        self.stats_label.configure(text=texto)

    def _estudiante_seleccionado(self) -> Estudiante | None:
        """Estudiante seleccionado en la tabla"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Estudiantes", "Seleccione un estudiante de la tabla")
            return None
        try:
            estudiante_id = int(seleccion[0])
        except (TypeError, ValueError):
            return None
        return next(
            (e for e in self._estudiantes if int(e.id) == estudiante_id), None
        )

    def _on_new_estudiante(self) -> None:
        """Abre el diálogo de alta de estudiante"""
        if not _verificar_permiso(self.main_window, "create", "registrar estudiantes"):
            return
        dialogo = EstudianteDialog(self, self.main_window, self.servicio)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_estudiantes()

    def _editar_estudiante(self) -> None:
        """Abre el diálogo de edición del estudiante seleccionado"""
        if not _verificar_permiso(self.main_window, "update", "editar estudiantes"):
            return
        estudiante = self._estudiante_seleccionado()
        if estudiante is None:
            return
        dialogo = EstudianteDialog(self, self.main_window, self.servicio, estudiante)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_estudiantes()

    def _toggle_activo(self) -> None:
        """Retira (baja lógica) o reactiva al estudiante seleccionado"""
        if not _verificar_permiso(self.main_window, "update", "activar o retirar estudiantes"):
            return
        estudiante = self._estudiante_seleccionado()
        if estudiante is None or self.servicio is None:
            return
        if estudiante.activo:
            mensaje = (
                f"¿Retirar a {estudiante.nombre_completo}?\n"
                "No se borran sus datos ni su historial de matrículas."
            )
        else:
            mensaje = f"¿Reactivar a {estudiante.nombre_completo}?"
        if not messagebox.askyesno("Estudiantes", mensaje):
            return
        try:
            if estudiante.activo:
                self.servicio.desactivar_estudiante(int(estudiante.id))
            else:
                self.servicio.activar_estudiante(int(estudiante.id))
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("No se pudo cambiar el estado del estudiante: %s", e)
            messagebox.showerror("Estudiantes", f"No se pudo actualizar:\n{e}")
            return
        self._load_estudiantes()

    def _exportar(self) -> None:
        """Exporta el listado de estudiantes mostrado"""
        if not _verificar_permiso(self.main_window, "report", "exportar estudiantes"):
            return
        if not self._estudiantes:
            messagebox.showinfo("Estudiantes", "No hay estudiantes para exportar")
            return
        filas: list[dict[str, Any]] = [
            {
                "Cedula": estudiante.cedula or "",
                "Estudiante": estudiante.nombre_completo,
                "Nivel": _titulo_nivel(estudiante.nivel_valor),
                "Edad": estudiante.edad if estudiante.edad is not None else "",
                "Representante": estudiante.representante or "",
                "Telefono": estudiante.telefono or "",
                "Email": estudiante.email or "",
                "Estado": "Activo" if estudiante.activo else "Retirado",
            }
            for estudiante in self._estudiantes
        ]
        try:
            from pathlib import Path

            from src.config import settings
            from src.utils.exporter import exportar_archivo
            from src.utils.helpers import ensure_directory_exists, get_timestamp

            carpeta = Path(settings.exports_path)
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"estudiantes_{get_timestamp()}.xlsx"
            exportar_archivo(filas, str(destino), hoja="Estudiantes")
            messagebox.showinfo("Estudiantes", f"Exportado en:\n{destino}")
        except (OSError, ValueError, ImportError) as e:
            logger.warning("No se pudo exportar los estudiantes", exc_info=True)
            messagebox.showerror("Estudiantes", f"No se pudo exportar:\n{e}")

    # ------------------------------------------------------------------
    # Datos de grados y matrículas
    # ------------------------------------------------------------------
    def _cargar_combos(self) -> None:
        """Rellena los selectores de periodos y la lista de docentes"""
        if self.servicio is None:
            return
        try:
            self._periodos = self.servicio.listar_periodos()
        except (AttributeError, ValueError, TypeError):
            logger.warning("No se pudieron cargar los periodos", exc_info=True)
            self._periodos = []
        valores = [TODOS] + [periodo.nombre for periodo in self._periodos]
        self.periodo_combo.configure(values=valores)
        if self.periodo_combo.get() not in valores:
            self.periodo_combo.set(TODOS)

        try:
            from src.repositories import UsuarioRepository

            usuarios = UsuarioRepository(self.session).get_activos()
            self._profesores = [
                (
                    int(usuario.id),
                    f"{usuario.nombre_completo or usuario.username} ({usuario.rol_valor})",
                )
                for usuario in usuarios
            ]
        except (AttributeError, TypeError, ValueError):
            logger.warning("No se pudieron cargar los docentes", exc_info=True)
            self._profesores = []

    def _periodo_seleccionado_id(self) -> int | None:
        """Periodo elegido en el filtro (None = todos)"""
        nombre = self.periodo_combo.get().strip()
        if not nombre or nombre == TODOS:
            return None
        for periodo in self._periodos:
            if periodo.nombre == nombre:
                return int(periodo.id)
        return None

    def _load_grados(self) -> None:
        """Carga los grados del periodo elegido"""
        for item in self.grados_tree.get_children():
            self.grados_tree.delete(item)
        self._limpiar_matriculas()

        if self.servicio is None:
            return
        try:
            grados = self.servicio.listar_grados(self._periodo_seleccionado_id())
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error consultando grados: %s", e)
            messagebox.showerror("Grados", f"No se pudieron consultar los grados:\n{e}")
            return

        self._grados = list(grados)
        for grado in self._grados:
            profesor = "-"
            if grado.profesor is not None:
                profesor = grado.profesor.nombre_completo or grado.profesor.username
            try:
                matriculados = self.servicio.matriculas.count_activas(int(grado.id))
            except (AttributeError, ValueError, TypeError):
                matriculados = 0
            self.grados_tree.insert(
                "",
                "end",
                iid=str(grado.id),
                values=(
                    grado.nombre_completo,
                    _titulo_nivel(grado.nivel_valor),
                    grado.periodo.nombre if grado.periodo else "-",
                    profesor,
                    matriculados,
                ),
            )

    def _grado_seleccionado(self, avisar: bool = True) -> Grado | None:
        """Grado seleccionado en la tabla (avisar=False para usos opcionales)"""
        seleccion = self.grados_tree.selection()
        if not seleccion:
            if avisar:
                messagebox.showinfo("Grados", "Seleccione un grado de la tabla")
            return None
        try:
            grado_id = int(seleccion[0])
        except (TypeError, ValueError):
            return None
        return next((g for g in self._grados if int(g.id) == grado_id), None)

    def _on_grado_select(self) -> None:
        """Carga los matriculados del grado recién seleccionado"""
        seleccion = self.grados_tree.selection()
        if not seleccion:
            self._limpiar_matriculas()
            return
        try:
            grado_id = int(seleccion[0])
        except (TypeError, ValueError):
            return
        self._load_matriculas(grado_id)

    def _load_matriculas(self, grado_id: int) -> None:
        """Carga los estudiantes matriculados en un grado"""
        self._limpiar_matriculas()
        if self.servicio is None:
            return
        try:
            matriculas = self.servicio.listar_matriculas_de_grado(grado_id)
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error consultando matrículas: %s", e)
            return
        grado = next((g for g in self._grados if int(g.id) == grado_id), None)
        if grado is not None:
            self.matriculas_label.configure(text=f"Matriculados en {grado.nombre_completo}")
        for matricula in matriculas:
            estudiante = matricula.estudiante
            self.matriculas_tree.insert(
                "",
                "end",
                iid=str(matricula.id),
                values=(
                    estudiante.nombre_completo if estudiante else "-",
                    (estudiante.cedula or "-") if estudiante else "-",
                    format_date(matricula.fecha_matricula) if matricula.fecha_matricula else "-",
                ),
            )

    def _limpiar_matriculas(self) -> None:
        """Vacía la tabla de matriculados"""
        for item in self.matriculas_tree.get_children():
            self.matriculas_tree.delete(item)
        self.matriculas_label.configure(text="Estudiantes matriculados")

    def _on_new_grado(self) -> None:
        """Abre el diálogo de alta de grado"""
        if not _verificar_permiso(self.main_window, "create", "crear grados"):
            return
        if not self._periodos:
            messagebox.showinfo(
                "Grados",
                "Cree primero un periodo académico en el módulo de Notas.",
            )
            return
        dialogo = GradoDialog(self, self.servicio, self._periodos, self._profesores)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._cargar_combos()
            self._load_grados()

    def _editar_grado(self) -> None:
        """Abre el diálogo de edición del grado seleccionado"""
        if not _verificar_permiso(self.main_window, "update", "editar grados"):
            return
        grado = self._grado_seleccionado()
        if grado is None:
            return
        dialogo = GradoDialog(self, self.servicio, self._periodos, self._profesores, grado)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_grados()

    def _asignar_profesor(self) -> None:
        """Asigna (o quita) el docente responsable del grado seleccionado"""
        if not _verificar_permiso(self.main_window, "update", "asignar profesores"):
            return
        grado = self._grado_seleccionado()
        if grado is None or self.servicio is None:
            return
        dialogo = ProfesorDialog(self, grado, self._profesores)
        self.wait_window(dialogo)
        if not getattr(dialogo, "guardado", False):
            return
        try:
            self.servicio.asignar_profesor(int(grado.id), getattr(dialogo, "profesor_id", None))
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("No se pudo asignar el profesor: %s", e)
            messagebox.showerror("Grados", f"No se pudo asignar el profesor:\n{e}")
            return
        self._load_grados()

    def _matricular(self) -> None:
        """Matricula a un estudiante en un grado"""
        if not _verificar_permiso(self.main_window, "create", "matricular estudiantes"):
            return
        if self.servicio is None:
            return
        try:
            estudiantes = self.servicio.listar_estudiantes_activos()
        except (AttributeError, ValueError, TypeError) as e:
            messagebox.showerror("Matrícula", f"No se pudieron cargar los estudiantes:\n{e}")
            return
        if not estudiantes:
            messagebox.showinfo("Matrícula", "No hay estudiantes activos para matricular")
            return
        if not self._grados:
            messagebox.showinfo("Matrícula", "No hay grados creados para el filtro elegido")
            return
        grado_actual = self._grado_seleccionado(avisar=False)
        dialogo = MatriculaDialog(self, self.servicio, estudiantes, self._grados, grado_actual)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_grados()
            if grado_actual is not None:
                self._load_matriculas(int(grado_actual.id))

    def _retirar_matricula(self) -> None:
        """Retira del grado la matrícula seleccionada (queda en el historial)"""
        if not _verificar_permiso(self.main_window, "delete", "retirar matrículas"):
            return
        seleccion = self.matriculas_tree.selection()
        if not seleccion:
            messagebox.showinfo("Matrícula", "Seleccione un estudiante matriculado")
            return
        if self.servicio is None:
            return
        try:
            matricula_id = int(seleccion[0])
        except (TypeError, ValueError):
            return
        nombre = self.matriculas_tree.item(seleccion[0], "values")[0]
        if not messagebox.askyesno(
            "Matrícula",
            f"¿Retirar a {nombre} del grado?\nLa matrícula queda en el historial.",
        ):
            return
        try:
            self.servicio.retirar_matricula(matricula_id)
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("No se pudo retirar la matrícula: %s", e)
            messagebox.showerror("Matrícula", f"No se pudo retirar:\n{e}")
            return
        grado = self._grado_seleccionado(avisar=False)
        grado_id = int(grado.id) if grado is not None else None
        self._load_grados()
        if grado_id is not None:
            self._load_matriculas(grado_id)


class _DialogoBase(ctk.CTkToplevel):
    """Base común de los diálogos del módulo: modal, centrado y con estado"""

    def __init__(self, parent, titulo: str, geometria: str):
        super().__init__(parent)
        self.guardado = False
        self.title(titulo)
        self.geometry(geometria)
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.bind("<Escape>", lambda _e: self.destroy())

    def _preparar_modal(self) -> None:
        """Centra el diálogo y captura el foco"""
        try:
            self.update_idletasks()
            self.grab_set()
        except tk.TclError:
            logger.debug("Diálogo sin grab establecido", exc_info=True)

    def _agregar_botones(self, guardar_texto: str = "Guardar") -> None:
        """Botones Guardar/Cancelar al pie del diálogo"""
        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(botones, text=guardar_texto, width=120, command=self._guardar).pack(
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

    def _guardar(self) -> None:  # pragma: no cover - las subclases lo implementan
        raise NotImplementedError


class EstudianteDialog(_DialogoBase):
    """Alta y edición de un estudiante"""

    def __init__(
        self,
        parent,
        main_window,
        servicio: AcademicoService | None,
        estudiante: Estudiante | None = None,
    ):
        super().__init__(
            parent, "Editar estudiante" if estudiante else "Nuevo estudiante", "620x660"
        )
        self.main_window = main_window
        self.servicio = servicio
        self.estudiante = estudiante
        self._create_widgets()
        self._preparar_modal()

    def _create_widgets(self) -> None:
        """Formulario del legajo estudiantil"""
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)
        fila = 0

        def etiqueta(texto: str) -> None:
            nonlocal fila
            ctk.CTkLabel(contenedor, text=texto, text_color=COLORES["texto"]).grid(
                row=fila, column=0, sticky="w", pady=6
            )

        etiqueta("Cédula:")
        self.cedula_entry = ctk.CTkEntry(contenedor, width=220)
        self.cedula_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Nombres:")
        self.nombres_entry = ctk.CTkEntry(contenedor, width=300)
        self.nombres_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Apellidos:")
        self.apellidos_entry = ctk.CTkEntry(contenedor, width=300)
        self.apellidos_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Fecha de nacimiento:")
        self.nacimiento_entry = ctk.CTkEntry(
            contenedor, width=150, placeholder_text="dd/mm/aaaa"
        )
        self.nacimiento_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Género:")
        self.genero_combo = ctk.CTkComboBox(
            contenedor, width=180, values=list(ETIQUETAS_GENERO.values())
        )
        self.genero_combo.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Nivel:")
        self.nivel_combo = ctk.CTkComboBox(
            contenedor, width=180, values=[_titulo_nivel(n) for n in NIVELES]
        )
        self.nivel_combo.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Representante:")
        self.representante_entry = ctk.CTkEntry(contenedor, width=300)
        self.representante_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Teléfono:")
        self.telefono_entry = ctk.CTkEntry(contenedor, width=180)
        self.telefono_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Teléfono del representante:")
        self.telefono_rep_entry = ctk.CTkEntry(contenedor, width=180)
        self.telefono_rep_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Email:")
        self.email_entry = ctk.CTkEntry(contenedor, width=260)
        self.email_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Dirección:")
        self.direccion_entry = ctk.CTkEntry(contenedor, width=300)
        self.direccion_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Observaciones:")
        self.observaciones_text = ctk.CTkTextbox(contenedor, width=320, height=60)
        self.observaciones_text.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        self.error_label = ctk.CTkLabel(
            contenedor,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_ERROR,
            anchor="w",
            justify="left",
            wraplength=560,
        )
        self.error_label.grid(row=fila, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self._cargar_estudiante()
        self._agregar_botones()

    def _cargar_estudiante(self) -> None:
        """Vuelca los datos del estudiante editado en el formulario"""
        if self.estudiante is None:
            self.genero_combo.set(ETIQUETAS_GENERO[""])
            self.nivel_combo.set(_titulo_nivel(NivelEducativo.INICIAL.value))
            return
        self.cedula_entry.insert(0, self.estudiante.cedula or "")
        self.nombres_entry.insert(0, self.estudiante.nombres or "")
        self.apellidos_entry.insert(0, self.estudiante.apellidos or "")
        if self.estudiante.fecha_nacimiento:
            self.nacimiento_entry.insert(0, format_date(self.estudiante.fecha_nacimiento))
        genero = self.estudiante.genero
        genero_valor = getattr(genero, "value", genero) or ""
        self.genero_combo.set(ETIQUETAS_GENERO.get(str(genero_valor), ETIQUETAS_GENERO[""]))
        self.nivel_combo.set(_titulo_nivel(self.estudiante.nivel_valor))
        self.representante_entry.insert(0, self.estudiante.representante or "")
        self.telefono_entry.insert(0, self.estudiante.telefono or "")
        self.telefono_rep_entry.insert(0, self.estudiante.telefono_representante or "")
        self.email_entry.insert(0, self.estudiante.email or "")
        self.direccion_entry.insert(0, self.estudiante.direccion or "")
        self.observaciones_text.insert("1.0", self.estudiante.observaciones or "")

    def _genero_valor(self) -> str | None:
        """Valor de género elegido (None si no se especifica)"""
        etiqueta = self.genero_combo.get().strip()
        for valor, texto in ETIQUETAS_GENERO.items():
            if texto == etiqueta:
                return valor or None
        return None

    def _guardar(self) -> None:
        """Valida el formulario y crea o actualiza el estudiante"""
        permiso = "update" if self.estudiante else "create"
        accion = "editar estudiantes" if self.estudiante else "registrar estudiantes"
        if not _verificar_permiso(self.main_window, permiso, accion):
            return
        if self.servicio is None:
            messagebox.showerror("Estudiantes", "El servicio académico no está disponible")
            return

        datos: dict[str, Any] = {
            "nombres": self.nombres_entry.get().strip(),
            "apellidos": self.apellidos_entry.get().strip(),
            "cedula": self.cedula_entry.get().strip(),
            "fecha_nacimiento": parse_date(self.nacimiento_entry.get().strip()),
            "genero": self._genero_valor(),
            "nivel": self.nivel_combo.get().strip().lower(),
            "representante": self.representante_entry.get().strip(),
            "telefono": self.telefono_entry.get().strip(),
            "telefono_representante": self.telefono_rep_entry.get().strip(),
            "email": self.email_entry.get().strip(),
            "direccion": self.direccion_entry.get().strip(),
            "observaciones": self.observaciones_text.get("1.0", "end").strip(),
        }
        try:
            if self.estudiante is None:
                self.servicio.crear_estudiante(datos)
            else:
                self.servicio.actualizar_estudiante(int(self.estudiante.id), datos)
        except (ValueError, TypeError, AttributeError) as e:
            self.error_label.configure(text=str(e))
            return
        self.guardado = True
        self.destroy()


class GradoDialog(_DialogoBase):
    """Alta y edición de un grado o sección"""

    def __init__(
        self,
        parent,
        servicio: AcademicoService | None,
        periodos: list[PeriodoAcademico],
        profesores: list[tuple[int, str]],
        grado: Grado | None = None,
    ):
        super().__init__(parent, "Editar grado" if grado else "Nuevo grado", "480x440")
        self.servicio = servicio
        self.periodos = periodos
        self.profesores = profesores
        self.grado = grado
        self._create_widgets()
        self._preparar_modal()

    def _create_widgets(self) -> None:
        """Formulario del grado"""
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)
        fila = 0

        def etiqueta(texto: str) -> None:
            nonlocal fila
            ctk.CTkLabel(contenedor, text=texto, text_color=COLORES["texto"]).grid(
                row=fila, column=0, sticky="w", pady=6
            )

        etiqueta("Periodo:")
        self.periodo_combo = ctk.CTkComboBox(
            contenedor, width=220, values=[p.nombre for p in self.periodos] or ["-"]
        )
        self.periodo_combo.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Nivel:")
        self.nivel_combo = ctk.CTkComboBox(
            contenedor, width=180, values=[_titulo_nivel(n) for n in NIVELES]
        )
        self.nivel_combo.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Nombre del grado:")
        self.nombre_entry = ctk.CTkEntry(
            contenedor, width=220, placeholder_text="Ej. 1er Año"
        )
        self.nombre_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Sección:")
        self.seccion_entry = ctk.CTkEntry(contenedor, width=80)
        self.seccion_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Profesor asignado:")
        self.profesor_combo = ctk.CTkComboBox(
            contenedor,
            width=300,
            values=[SIN_ASIGNAR] + [texto for _id, texto in self.profesores],
        )
        self.profesor_combo.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Observaciones:")
        self.observaciones_text = ctk.CTkTextbox(contenedor, width=300, height=60)
        self.observaciones_text.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        self.error_label = ctk.CTkLabel(
            contenedor,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORES["texto_suave"],
            anchor="w",
            justify="left",
            wraplength=420,
        )
        self.error_label.grid(row=fila, column=0, columnspan=2, sticky="w", pady=(8, 0))

        if self.grado is not None:
            periodo = self.grado.periodo
            self.periodo_combo.set(periodo.nombre if periodo else "-")
            self.periodo_combo.configure(state="disabled")
            self.nivel_combo.set(_titulo_nivel(self.grado.nivel_valor))
            self.nombre_entry.insert(0, self.grado.nombre or "")
            self.seccion_entry.insert(0, self.grado.seccion or "A")
            if self.grado.profesor is not None:
                for _id, texto in self.profesores:
                    if _id == int(self.grado.profesor_id or 0):
                        self.profesor_combo.set(texto)
                        break
            else:
                self.profesor_combo.set(SIN_ASIGNAR)
            self.observaciones_text.insert("1.0", self.grado.observaciones or "")
        else:
            self.seccion_entry.insert(0, "A")
            self.profesor_combo.set(SIN_ASIGNAR)
            self.nivel_combo.set(_titulo_nivel(NivelEducativo.SECUNDARIA.value))
            if self.periodos:
                self.periodo_combo.set(self.periodos[0].nombre)
        self._agregar_botones()

    def _periodo_id(self) -> int | None:
        """Identificador del periodo elegido"""
        nombre = self.periodo_combo.get().strip()
        for periodo in self.periodos:
            if periodo.nombre == nombre:
                return int(periodo.id)
        return None

    def _profesor_id(self) -> int | None:
        """Identificador del profesor elegido (None = sin asignar)"""
        texto = self.profesor_combo.get().strip()
        if not texto or texto == SIN_ASIGNAR:
            return None
        for profesor_id, etiqueta in self.profesores:
            if etiqueta == texto:
                return profesor_id
        return None

    def _guardar(self) -> None:
        """Crea o actualiza el grado con las reglas del servicio"""
        if self.servicio is None:
            messagebox.showerror("Grados", "El servicio académico no está disponible")
            return
        datos: dict[str, Any] = {
            "nivel": self.nivel_combo.get().strip().lower(),
            "nombre": self.nombre_entry.get().strip(),
            "seccion": self.seccion_entry.get().strip() or "A",
            "profesor_id": self._profesor_id(),
            "observaciones": self.observaciones_text.get("1.0", "end").strip(),
        }
        try:
            if self.grado is None:
                datos["periodo_id"] = self._periodo_id()
                self.servicio.crear_grado(datos)
            else:
                self.servicio.actualizar_grado(int(self.grado.id), datos)
        except (ValueError, TypeError, AttributeError) as e:
            self.error_label.configure(text=str(e))
            return
        self.guardado = True
        self.destroy()


class ProfesorDialog(_DialogoBase):
    """Asignación del docente responsable de un grado"""

    def __init__(self, parent, grado: Grado, profesores: list[tuple[int, str]]):
        super().__init__(parent, f"Profesor de {grado.nombre_completo}", "460x220")
        self.grado = grado
        self.profesores = profesores
        self.profesor_id: int | None = None

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(
            contenedor,
            text=(
                "El docente asignado es el único profesor autorizado a registrar\n"
                "y modificar las notas de este grado."
            ),
            text_color=COLORES["texto_suave"],
            justify="left",
        ).pack(anchor="w", pady=(0, 10))
        self.profesor_combo = ctk.CTkComboBox(
            contenedor,
            width=380,
            values=[SIN_ASIGNAR] + [texto for _id, texto in self.profesores],
        )
        self.profesor_combo.pack(anchor="w")
        if grado.profesor_id is not None:
            for profesor_id, texto in self.profesores:
                if profesor_id == int(grado.profesor_id):
                    self.profesor_combo.set(texto)
                    break
        else:
            self.profesor_combo.set(SIN_ASIGNAR)
        self._agregar_botones()
        self._preparar_modal()

    def _guardar(self) -> None:
        """Fija el profesor elegido (None lo desasigna)"""
        texto = self.profesor_combo.get().strip()
        self.profesor_id = None
        if texto and texto != SIN_ASIGNAR:
            for profesor_id, etiqueta in self.profesores:
                if etiqueta == texto:
                    self.profesor_id = profesor_id
                    break
        self.guardado = True
        self.destroy()


class MatriculaDialog(_DialogoBase):
    """Matrícula de un estudiante en un grado"""

    def __init__(
        self,
        parent,
        servicio: AcademicoService | None,
        estudiantes: list[Estudiante],
        grados: list[Grado],
        grado_actual: Grado | None = None,
    ):
        super().__init__(parent, "Matricular estudiante", "560x260")
        self.servicio = servicio
        self.estudiantes = estudiantes
        self.grados = grados
        self._create_widgets(grado_actual)
        self._preparar_modal()

    def _create_widgets(self, grado_actual: Grado | None) -> None:
        """Selectores de estudiante y grado"""
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(contenedor, text="Estudiante:", text_color=COLORES["texto"]).grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.estudiante_combo = ctk.CTkComboBox(
            contenedor,
            width=380,
            values=[
                f"{estudiante.cedula or 's/c'} - {estudiante.nombre_completo}"
                for estudiante in self.estudiantes
            ],
        )
        self.estudiante_combo.grid(row=0, column=1, sticky="w", pady=6)

        ctk.CTkLabel(contenedor, text="Grado:", text_color=COLORES["texto"]).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.grado_combo = ctk.CTkComboBox(
            contenedor, width=380, values=[self._etiqueta_grado(g) for g in self.grados]
        )
        self.grado_combo.grid(row=1, column=1, sticky="w", pady=6)
        if grado_actual is not None:
            self.grado_combo.set(self._etiqueta_grado(grado_actual))

        self.error_label = ctk.CTkLabel(
            contenedor,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORES["texto_suave"],
            anchor="w",
            justify="left",
            wraplength=500,
        )
        self.error_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self._agregar_botones()

    @staticmethod
    def _etiqueta_grado(grado: Grado) -> str:
        """Etiqueta única de un grado en el selector"""
        periodo = grado.periodo.nombre if grado.periodo else "-"
        return f"{periodo} · {grado.nombre_completo}"

    def _ids_seleccionados(self) -> tuple[int | None, int | None]:
        """Identificadores de estudiante y grado elegidos"""
        etiqueta_estudiante = self.estudiante_combo.get().strip()
        etiqueta_grado = self.grado_combo.get().strip()
        estudiante_id = None
        grado_id = None
        for estudiante in self.estudiantes:
            if (
                f"{estudiante.cedula or 's/c'} - {estudiante.nombre_completo}"
                == etiqueta_estudiante
            ):
                estudiante_id = int(estudiante.id)
                break
        for grado in self.grados:
            if self._etiqueta_grado(grado) == etiqueta_grado:
                grado_id = int(grado.id)
                break
        return estudiante_id, grado_id

    def _guardar(self) -> None:
        """Ejecuta la matrícula con las reglas del servicio"""
        if self.servicio is None:
            messagebox.showerror("Matrícula", "El servicio académico no está disponible")
            return
        estudiante_id, grado_id = self._ids_seleccionados()
        if estudiante_id is None or grado_id is None:
            self.error_label.configure(text="Seleccione un estudiante y un grado")
            return
        try:
            self.servicio.matricular(estudiante_id, grado_id)
        except (ValueError, TypeError, AttributeError) as e:
            self.error_label.configure(text=str(e))
            return
        self.guardado = True
        self.destroy()
