"""
Módulo de Contratos

Interfaz de administración del ciclo de vida contractual: alta de
contratos, renovación encadenada, terminación con generación del
finiquito y control de los contratos próximos a vencer.
"""

from __future__ import annotations

import logging
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from src.gui.frames import _habilitar_orden_columnas, _seleccionar_fila_click
from src.gui.theme import COLORES
from src.models import Contrato, Empleado, EstadoContrato, TipoContrato
from src.utils.helpers import format_currency, format_date, parse_date

if TYPE_CHECKING:
    from src.services import ContratoService

logger = logging.getLogger(__name__)

FILTROS_ESTADO = ["Todos", "Vigentes", "Por vencer", "Vencidos", "Terminados"]
ETIQUETAS_ESTADO = {
    "vigente": "Vigente",
    "renovado": "Renovado",
    "vencido": "Vencido",
    "terminado": "Terminado",
}


class ContratosFrame(ctk.CTkFrame):
    """Frame del módulo de contratos laborales"""

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self.servicio: ContratoService | None = self._crear_servicio()
        self._empleados: dict[int, Empleado] = {}
        self.contratos: list[Contrato] = []
        self._create_widgets()
        self._cargar_empleados()
        self._load_data()

    def _crear_servicio(self) -> ContratoService | None:
        """Crea el servicio de contratos con la sesión activa"""
        try:
            from src.services import ContratoService

            return ContratoService(self.session)
        except (ImportError, AttributeError) as e:
            logger.error("No se pudo inicializar el servicio de contratos: %s", e)
            return None

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Crea la barra de acciones, la tabla y el resumen"""
        ctk.CTkLabel(
            self,
            text="Contratos Laborales",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORES["texto"],
        ).pack(pady=(14, 6), padx=20, anchor="w")

        self._crear_barra_acciones()
        self._crear_tabla()
        self._crear_resumen()

    def _crear_barra_acciones(self) -> None:
        """Barra de filtros y acciones sobre contratos"""
        barra = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        barra.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(barra, text="Estado:", text_color=COLORES["texto"]).pack(
            side="left", padx=(12, 4), pady=10
        )
        self.estado_combo = ctk.CTkComboBox(
            barra, width=140, values=FILTROS_ESTADO, command=lambda _v: self._load_data()
        )
        self.estado_combo.pack(side="left", pady=10)
        self.estado_combo.set("Vigentes")

        ctk.CTkLabel(barra, text="Empleado:", text_color=COLORES["texto"]).pack(
            side="left", padx=(12, 4), pady=10
        )
        self.empleado_combo = ctk.CTkComboBox(barra, width=220, values=["Todos"])
        self.empleado_combo.pack(side="left", pady=10)
        self.empleado_combo.set("Todos")

        ctk.CTkButton(barra, text="🔍 Buscar", width=90, command=self._load_data).pack(
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
            text="📊 Exportar",
            width=100,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._exportar,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            barra,
            text="🛑 Terminar",
            width=110,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._terminar_contrato,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            barra,
            text="🔄 Renovar",
            width=110,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._renovar_contrato,
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            barra, text="➕ Nuevo contrato", width=150, command=self._nuevo_contrato
        ).pack(side="right", padx=4)

    def _crear_tabla(self) -> None:
        """Tabla de contratos"""
        contenedor = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        contenedor.pack(fill="both", expand=True, padx=20, pady=8)

        columnas = (
            "numero",
            "empleado",
            "tipo",
            "cargo",
            "inicio",
            "fin",
            "dias",
            "salario",
            "estado",
        )
        self.tree = ttk.Treeview(contenedor, columns=columnas, show="headings", height=15)
        encabezados = {
            "numero": ("Número", 130),
            "empleado": ("Empleado", 220),
            "tipo": ("Tipo", 100),
            "cargo": ("Cargo", 150),
            "inicio": ("Inicio", 95),
            "fin": ("Fin", 95),
            "dias": ("Días", 60),
            "salario": ("Salario", 110),
            "estado": ("Estado", 100),
        }
        for clave, (texto, ancho) in encabezados.items():
            self.tree.heading(clave, text=texto)
            self.tree.column(clave, width=ancho, anchor="w" if clave in ("empleado", "cargo") else "center")

        _habilitar_orden_columnas(self.tree)
        self.tree.bind("<ButtonRelease-1>", lambda evento: _seleccionar_fila_click(self.tree, evento))
        self.tree.bind("<Double-1>", lambda _evento: self._ver_detalle())

        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

    def _crear_resumen(self) -> None:
        """Resumen de contratos y alertas de vencimiento"""
        resumen = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        resumen.pack(fill="x", padx=20, pady=(0, 16))
        self.resumen_label = ctk.CTkLabel(
            resumen,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORES["texto_suave"],
            anchor="w",
        )
        self.resumen_label.pack(fill="x", padx=14, pady=10)

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------
    def _cargar_empleados(self) -> None:
        """Carga los empleados activos en el selector"""
        try:
            from src.repositories import EmpleadoRepository

            empleados = EmpleadoRepository(self.session).get_activos()
            self._empleados = {int(empleado.id): empleado for empleado in empleados}
            valores = ["Todos"] + [
                f"{empleado.cedula} - {empleado.nombre_completo}" for empleado in empleados
            ]
            self.empleado_combo.configure(values=valores)
            self.empleado_combo.set("Todos")
        except (AttributeError, TypeError, ValueError):
            logger.warning("No se pudieron cargar los empleados del selector", exc_info=True)

    def _empleado_seleccionado(self) -> int | None:
        """Identificador del empleado elegido (None = todos)"""
        seleccion = self.empleado_combo.get().strip()
        if not seleccion or seleccion == "Todos":
            return None
        cedula = seleccion.split(" - ", 1)[0].strip()
        for identificador, empleado in self._empleados.items():
            if str(getattr(empleado, "cedula", "")).strip() == cedula:
                return identificador
        return None

    def _load_data(self) -> None:
        """Carga los contratos según el filtro seleccionado"""
        if self.servicio is None:
            messagebox.showerror("Contratos", "El servicio de contratos no está disponible")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        filtro = self.estado_combo.get().strip()
        empleado_id = self._empleado_seleccionado()
        try:
            if empleado_id is not None:
                contratos = self.servicio.listar_por_empleado(empleado_id)
                if filtro == "Vigentes":
                    contratos = [c for c in contratos if c.esta_vigente]
                elif filtro == "Por vencer":
                    contratos = [c for c in contratos if c.por_vencer()]
                elif filtro == "Vencidos":
                    contratos = [c for c in contratos if c.estado_valor == "vencido"]
                elif filtro == "Terminados":
                    contratos = [c for c in contratos if c.estado_valor == "terminado"]
            elif filtro == "Por vencer":
                contratos = self.servicio.listar_por_vencer()
            elif filtro == "Vencidos":
                contratos = self.servicio.listar_vencidos()
            elif filtro == "Terminados":
                contratos = self.servicio.listar_por_estado(EstadoContrato.TERMINADO.value)
            elif filtro == "Vigentes":
                contratos = [
                    contrato
                    for contrato in self.servicio.listar_contratos()
                    if contrato.esta_vigente
                ]
            else:
                contratos = self.servicio.listar_contratos()
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error consultando contratos: %s", e)
            messagebox.showerror("Contratos", f"No se pudieron consultar los contratos:\n{e}")
            return

        self.contratos = contratos
        for contrato in contratos:
            empleado = self._empleados.get(int(contrato.empleado_id))
            nombre = empleado.nombre_completo if empleado else f"Empleado {contrato.empleado_id}"
            dias = contrato.dias_para_vencer
            self.tree.insert(
                "",
                "end",
                iid=str(contrato.id),
                values=(
                    contrato.numero,
                    nombre,
                    str(contrato.tipo_valor).capitalize(),
                    contrato.cargo,
                    format_date(contrato.fecha_inicio),
                    format_date(contrato.fecha_fin) if contrato.fecha_fin else "Indefinido",
                    "-" if dias is None else dias,
                    format_currency(float(contrato.salario_pactado or 0)),
                    ETIQUETAS_ESTADO.get(contrato.estado_valor, contrato.estado_valor),
                ),
            )

        self._actualizar_resumen()

    def _actualizar_resumen(self) -> None:
        """Muestra los totales y los contratos por vencer"""
        vigentes = [contrato for contrato in self.contratos if contrato.esta_vigente]
        monto = sum(float(contrato.salario_pactado or 0) for contrato in vigentes)
        por_vencer = [contrato for contrato in self.contratos if contrato.por_vencer()]
        self.resumen_label.configure(
            text=(
                f"Contratos mostrados: {len(self.contratos)} | Vigentes: {len(vigentes)} | "
                f"Monto mensual comprometido: {format_currency(monto)} | "
                f"Por vencer: {len(por_vencer)}"
            )
        )

    def _contrato_seleccionado(self):
        """Contrato seleccionado en la tabla"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Contratos", "Seleccione un contrato de la tabla")
            return None
        try:
            contrato_id = int(seleccion[0])
        except (TypeError, ValueError):
            return None
        return next(
            (contrato for contrato in self.contratos if int(contrato.id) == contrato_id), None
        )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def _nuevo_contrato(self) -> None:
        """Abre el diálogo de alta de contrato"""
        dialogo = ContratoDialog(self, self.main_window, self._empleados, self.servicio)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_data()

    def _renovar_contrato(self) -> None:
        """Renueva el contrato seleccionado"""
        contrato = self._contrato_seleccionado()
        if contrato is None or self.servicio is None:
            return
        dialogo = RenovacionDialog(self, self.servicio, contrato)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_data()

    def _terminar_contrato(self) -> None:
        """Termina el contrato seleccionado y genera su finiquito"""
        contrato = self._contrato_seleccionado()
        if contrato is None or self.servicio is None:
            return
        dialogo = TerminacionDialog(self, self.servicio, contrato, self._empleados)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_data()

    def _ver_detalle(self) -> None:
        """Muestra el detalle del contrato seleccionado"""
        contrato = self._contrato_seleccionado()
        if contrato is None:
            return
        empleado = self._empleados.get(int(contrato.empleado_id))
        lineas = [
            f"Número: {contrato.numero}",
            f"Empleado: {empleado.nombre_completo if empleado else contrato.empleado_id}",
            f"Tipo: {str(contrato.tipo_valor).capitalize()}",
            f"Estado: {ETIQUETAS_ESTADO.get(contrato.estado_valor, contrato.estado_valor)}",
            f"Cargo: {contrato.cargo}",
            f"Departamento: {contrato.departamento or '-'}",
            f"Salario pactado: {format_currency(float(contrato.salario_pactado or 0))}",
            f"Jornada: {contrato.horas_semanales} h/semana",
            f"Inicio: {format_date(contrato.fecha_inicio)}",
            f"Fin: {format_date(contrato.fecha_fin) if contrato.fecha_fin else 'Indefinido'}",
            f"Días de vigencia: {contrato.dias_vigencia}",
            f"Renovación automática: {'Sí' if contrato.renovacion_automatica else 'No'}",
            f"Liquidación registrada: {format_currency(float(contrato.liquidacion_monto or 0))}",
        ]
        if contrato.motivo_terminacion:
            lineas.append(f"Motivo de terminación: {contrato.motivo_terminacion}")
        if contrato.clausulas:
            lineas.append(f"Cláusulas: {contrato.clausulas}")
        messagebox.showinfo(f"Contrato {contrato.numero}", "\n".join(lineas))

    # ------------------------------------------------------------------
    # Exportación
    # ------------------------------------------------------------------
    def _filas_exportables(self) -> list[dict]:
        """Convierte los contratos en filas planas para exportar"""
        filas = []
        for contrato in self.contratos:
            empleado = self._empleados.get(int(contrato.empleado_id))
            filas.append(
                {
                    "Numero": contrato.numero,
                    "Empleado": empleado.nombre_completo if empleado else contrato.empleado_id,
                    "Cedula": getattr(empleado, "cedula", ""),
                    "Tipo": str(contrato.tipo_valor).capitalize(),
                    "Cargo": contrato.cargo,
                    "Departamento": contrato.departamento or "",
                    "Inicio": format_date(contrato.fecha_inicio),
                    "Fin": format_date(contrato.fecha_fin) if contrato.fecha_fin else "Indefinido",
                    "Dias_vigencia": contrato.dias_vigencia,
                    "Salario_pactado": float(contrato.salario_pactado or 0),
                    "Horas_semanales": int(contrato.horas_semanales or 0),
                    "Estado": ETIQUETAS_ESTADO.get(contrato.estado_valor, contrato.estado_valor),
                    "Liquidacion": float(contrato.liquidacion_monto or 0),
                }
            )
        return filas

    def _exportar(self) -> None:
        """Exporta el listado de contratos"""
        if not self.contratos:
            messagebox.showinfo("Contratos", "No hay contratos para exportar")
            return
        try:
            from pathlib import Path

            from src.config import settings
            from src.utils.exporter import exportar_archivo
            from src.utils.helpers import ensure_directory_exists, get_timestamp

            carpeta = Path(settings.exports_path)
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"contratos_{get_timestamp()}.xlsx"
            exportar_archivo(self._filas_exportables(), str(destino), hoja="Contratos")
            messagebox.showinfo("Contratos", f"Exportado en:\n{destino}")
        except (OSError, ValueError, ImportError) as e:
            logger.warning("No se pudo exportar los contratos", exc_info=True)
            messagebox.showerror("Contratos", f"No se pudo exportar:\n{e}")

    def _exportar_pdf(self) -> None:
        """Genera el reporte PDF de contratos mostrados"""
        if not self.contratos:
            messagebox.showinfo("Contratos", "No hay contratos para el reporte")
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

            carpeta = Path(settings.exports_path) / "contratos"
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"reporte_contratos_{get_timestamp()}.pdf"
            pdf_generator.generate_reporte_contratos(
                self._filas_exportables(), str(destino), titulo=self.estado_combo.get()
            )
            abrir_con_aplicacion_predeterminada(destino)
            messagebox.showinfo("Contratos", f"Reporte generado:\n{destino}")
        except (OSError, ValueError, ImportError) as e:
            logger.warning("No se pudo generar el reporte de contratos", exc_info=True)
            messagebox.showerror("Contratos", f"No se pudo generar el reporte:\n{e}")


class ContratoDialog(ctk.CTkToplevel):
    """Diálogo de alta de contrato laboral"""

    def __init__(
        self,
        parent,
        main_window,
        empleados: dict[int, Empleado],
        servicio: ContratoService | None,
    ):
        super().__init__(parent)
        self.main_window = main_window
        self.empleados = empleados
        self.servicio = servicio
        self.guardado = False

        self.title("Nuevo contrato")
        self.geometry("560x620")
        self.resizable(False, False)
        self.transient(parent)

        self._create_widgets()
        self._actualizar_resumen()
        self._centrar()

    def _centrar(self) -> None:
        """Prepara el diálogo modal"""
        try:
            self.update_idletasks()
            self.grab_set()
        except tk.TclError:
            logger.debug("Diálogo de contrato sin grab establecido", exc_info=True)

    def _create_widgets(self) -> None:
        """Crea los campos del formulario"""
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)

        fila = 0

        def etiqueta(texto: str, fila_actual: int) -> None:
            ctk.CTkLabel(contenedor, text=texto, text_color=COLORES["texto"]).grid(
                row=fila_actual, column=0, sticky="w", pady=6
            )

        etiqueta("Empleado:", fila)
        valores = [
            f"{empleado.cedula} - {empleado.nombre_completo}"
            for empleado in self.empleados.values()
        ]
        self.empleado_combo = ctk.CTkComboBox(contenedor, width=320, values=valores or ["-"])
        self.empleado_combo.grid(row=fila, column=1, sticky="w", pady=6)
        if valores:
            self.empleado_combo.set(valores[0])
        self.empleado_combo.configure(command=lambda _v: self._actualizar_resumen())
        fila += 1

        etiqueta("Tipo de contrato:", fila)
        self.tipo_combo = ctk.CTkComboBox(
            contenedor, width=200, values=[tipo.value for tipo in TipoContrato]
        )
        self.tipo_combo.grid(row=fila, column=1, sticky="w", pady=6)
        self.tipo_combo.set(TipoContrato.INDEFINIDO.value)
        self.tipo_combo.configure(command=lambda _v: self._actualizar_resumen())
        fila += 1

        etiqueta("Cargo:", fila)
        self.cargo_entry = ctk.CTkEntry(contenedor, width=250)
        self.cargo_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Departamento:", fila)
        self.departamento_entry = ctk.CTkEntry(contenedor, width=250)
        self.departamento_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Salario pactado:", fila)
        self.salario_entry = ctk.CTkEntry(contenedor, width=150)
        self.salario_entry.grid(row=fila, column=1, sticky="w", pady=6)
        self.salario_entry.bind("<FocusOut>", lambda _e: self._actualizar_resumen())
        fila += 1

        etiqueta("Horas semanales:", fila)
        self.horas_entry = ctk.CTkEntry(contenedor, width=90)
        self.horas_entry.grid(row=fila, column=1, sticky="w", pady=6)
        self.horas_entry.insert(0, "40")
        fila += 1

        etiqueta("Fecha de inicio:", fila)
        self.inicio_entry = ctk.CTkEntry(contenedor, width=140)
        self.inicio_entry.grid(row=fila, column=1, sticky="w", pady=6)
        self.inicio_entry.insert(0, date.today().strftime("%d/%m/%Y"))
        fila += 1

        etiqueta("Fecha de fin:", fila)
        self.fin_entry = ctk.CTkEntry(contenedor, width=140, placeholder_text="dd/mm/aaaa")
        self.fin_entry.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        self.renovacion_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            contenedor, text="Renovación automática", variable=self.renovacion_var
        ).grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        etiqueta("Cláusulas:", fila)
        self.clausulas_text = ctk.CTkTextbox(contenedor, width=320, height=70)
        self.clausulas_text.grid(row=fila, column=1, sticky="w", pady=6)
        fila += 1

        self.resumen_label = ctk.CTkLabel(
            contenedor,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORES["texto_suave"],
            justify="left",
            anchor="w",
        )
        self.resumen_label.grid(row=fila, column=0, columnspan=2, sticky="w", pady=(10, 0))

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

    def _empleado_seleccionado(self):
        """Empleado elegido en el formulario"""
        seleccion = self.empleado_combo.get().strip()
        cedula = seleccion.split(" - ", 1)[0].strip() if seleccion else ""
        for empleado in self.empleados.values():
            if str(getattr(empleado, "cedula", "")).strip() == cedula:
                return empleado
        return None

    def _actualizar_resumen(self) -> None:
        """Muestra el número de contrato calculado y las fechas efectivas"""
        empleado = self._empleado_seleccionado()
        if empleado is None or self.servicio is None:
            self.resumen_label.configure(text="")
            return
        try:
            numero = self.servicio.generar_numero(int(empleado.id))
        except (AttributeError, ValueError, TypeError):
            numero = "(se calculará al guardar)"
        requiere_fin = (
            self.tipo_combo.get().strip() != TipoContrato.INDEFINIDO.value
        )
        self.resumen_label.configure(
            text=(
                f"Número de contrato: {numero} · "
                f"{'Requiere fecha de fin' if requiere_fin else 'Contrato indefinido'}"
            )
        )

    def _guardar(self) -> None:
        """Valida y crea el contrato"""
        if self.servicio is None:
            messagebox.showerror("Contratos", "El servicio de contratos no está disponible")
            return
        empleado = self._empleado_seleccionado()
        if empleado is None:
            messagebox.showwarning("Contratos", "Seleccione un empleado")
            return

        salario_texto = self.salario_entry.get().strip().replace(",", ".")
        try:
            salario = float(salario_texto)
        except (TypeError, ValueError):
            messagebox.showwarning("Contratos", "Indique un salario pactado válido")
            return

        datos = {
            "empleado_id": int(empleado.id),
            "tipo": self.tipo_combo.get().strip(),
            "cargo": self.cargo_entry.get().strip() or getattr(empleado, "cargo", ""),
            "departamento": self.departamento_entry.get().strip()
            or getattr(empleado, "departamento", None),
            "salario_pactado": salario,
            "horas_semanales": self.horas_entry.get().strip() or 40,
            "fecha_inicio": parse_date(self.inicio_entry.get().strip()) or date.today(),
            "fecha_fin": parse_date(self.fin_entry.get().strip()),
            "renovacion_automatica": bool(self.renovacion_var.get()),
            "clausulas": self.clausulas_text.get("1.0", "end").strip() or None,
            "aprobado_por": getattr(
                getattr(self.main_window, "current_user", None), "username", None
            ),
        }

        errores = self.servicio.validar_datos_contrato(datos)
        if errores:
            messagebox.showwarning("Contratos", "\n".join(errores))
            return

        try:
            self.servicio.crear_contrato(datos)
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("No se pudo crear el contrato: %s", e)
            messagebox.showerror("Contratos", f"No se pudo crear el contrato:\n{e}")
            return

        self.guardado = True
        self.destroy()


class RenovacionDialog(ctk.CTkToplevel):
    """Diálogo de renovación de un contrato vigente"""

    def __init__(self, parent, servicio: ContratoService | None, contrato: Contrato):
        super().__init__(parent)
        self.servicio = servicio
        self.contrato = contrato
        self.guardado = False

        self.title(f"Renovar contrato {contrato.numero}")
        self.geometry("460x320")
        self.resizable(False, False)
        self.transient(parent)

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            contenedor,
            text=(
                f"Contrato actual: {contrato.numero}\n"
                f"Vence: {format_date(contrato.fecha_fin) if contrato.fecha_fin else 'sin fecha'}\n"
                f"Salario actual: {format_currency(float(contrato.salario_pactado or 0))}"
            ),
            text_color=COLORES["texto"],
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(contenedor, text="Nueva fecha de fin:", text_color=COLORES["texto"]).pack(
            anchor="w"
        )
        self.fin_entry = ctk.CTkEntry(contenedor, width=160)
        self.fin_entry.pack(anchor="w", pady=4)

        ctk.CTkLabel(contenedor, text="Nuevo salario (opcional):", text_color=COLORES["texto"]).pack(
            anchor="w", pady=(8, 0)
        )
        self.salario_entry = ctk.CTkEntry(contenedor, width=160)
        self.salario_entry.pack(anchor="w", pady=4)

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(botones, text="Renovar", width=120, command=self._guardar).pack(
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

        try:
            self.update_idletasks()
            self.grab_set()
        except tk.TclError:
            logger.debug("Diálogo de renovación sin grab", exc_info=True)

    def _guardar(self) -> None:
        """Ejecuta la renovación del contrato"""
        if self.servicio is None:
            messagebox.showerror("Contratos", "El servicio de contratos no está disponible")
            return
        fecha_fin = parse_date(self.fin_entry.get().strip())
        if fecha_fin is None:
            messagebox.showwarning("Contratos", "Indique la nueva fecha de fin (dd/mm/aaaa)")
            return
        salario_texto = self.salario_entry.get().strip().replace(",", ".")
        salario = None
        if salario_texto:
            try:
                salario = float(salario_texto)
            except (TypeError, ValueError):
                messagebox.showwarning("Contratos", "El nuevo salario no es un número válido")
                return
        try:
            self.servicio.renovar_contrato(
                int(self.contrato.id), nueva_fecha_fin=fecha_fin, nuevo_salario=salario
            )
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("No se pudo renovar el contrato: %s", e)
            messagebox.showerror("Contratos", f"No se pudo renovar el contrato:\n{e}")
            return
        self.guardado = True
        self.destroy()


class TerminacionDialog(ctk.CTkToplevel):
    """Diálogo de terminación de contrato con vista previa del finiquito"""

    def __init__(
        self,
        parent,
        servicio: ContratoService | None,
        contrato: Contrato,
        empleados: dict[int, Empleado],
    ):
        super().__init__(parent)
        self.servicio = servicio
        self.contrato = contrato
        self.empleados = empleados
        self.guardado = False

        self.title(f"Terminar contrato {contrato.numero}")
        self.geometry("540x520")
        self.resizable(False, False)
        self.transient(parent)

        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(contenedor, text="Motivo:", text_color=COLORES["texto"]).pack(anchor="w")
        self.motivo_entry = ctk.CTkEntry(contenedor, width=420)
        self.motivo_entry.pack(anchor="w", pady=4)
        self.motivo_entry.insert(0, "renuncia")

        ctk.CTkLabel(contenedor, text="Fecha de terminación:", text_color=COLORES["texto"]).pack(
            anchor="w", pady=(8, 0)
        )
        self.fecha_entry = ctk.CTkEntry(contenedor, width=160)
        self.fecha_entry.pack(anchor="w", pady=4)
        self.fecha_entry.insert(0, date.today().strftime("%d/%m/%Y"))

        self.generar_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            contenedor,
            text="Registrar el pago de la liquidación (no afecta seguridad social)",
            variable=self.generar_var,
        ).pack(anchor="w", pady=8)

        ctk.CTkButton(
            contenedor, text="Calcular finiquito", width=160, command=self._previsualizar
        ).pack(anchor="w", pady=6)

        self.previa_label = ctk.CTkLabel(
            contenedor,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORES["texto"],
            justify="left",
            anchor="w",
        )
        self.previa_label.pack(anchor="w", pady=8, fill="x")

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(botones, text="Terminar contrato", width=170, command=self._guardar).pack(
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

        try:
            self.update_idletasks()
            self.grab_set()
        except tk.TclError:
            logger.debug("Diálogo de terminación sin grab", exc_info=True)

    def _previsualizar(self) -> dict[str, Any] | None:
        """Calcula y muestra el finiquito antes de confirmar"""
        if self.servicio is None:
            self.previa_label.configure(text="El servicio de contratos no está disponible")
            return None
        fecha = parse_date(self.fecha_entry.get().strip()) or date.today()
        try:
            finiquito = self.servicio.calcular_liquidacion(
                int(self.contrato.empleado_id), self.motivo_entry.get().strip() or "egreso", fecha
            )
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("No se pudo calcular el finiquito: %s", e)
            self.previa_label.configure(text=f"No se pudo calcular el finiquito: {e}")
            return None

        self.previa_label.configure(
            text=(
                f"Antigüedad: {float(finiquito.anos_servicio):.2f} año(s)\n"
                f"Prestaciones: {format_currency(float(finiquito.prestaciones))} · "
                f"Indemnización: {format_currency(float(finiquito.indemnizacion))}\n"
                f"Preaviso: {format_currency(float(finiquito.preaviso))} · "
                f"Vacaciones: {format_currency(float(finiquito.vacaciones))}\n"
                f"Aguinaldo: {format_currency(float(finiquito.aguinaldo))} · "
                f"Bono vacacional: {format_currency(float(finiquito.bono_vacacional))}\n"
                f"Anticipos por descontar: -{format_currency(float(finiquito.anticipos))}\n"
                f"NETO A PAGAR: {format_currency(float(finiquito.neto))}"
            )
        )
        return finiquito.to_dict()

    def _guardar(self) -> None:
        """Termina el contrato generando la liquidación"""
        if self.servicio is None:
            messagebox.showerror("Contratos", "El servicio de contratos no está disponible")
            return
        fecha = parse_date(self.fecha_entry.get().strip()) or date.today()
        motivo = self.motivo_entry.get().strip() or "egreso"
        try:
            self.servicio.terminar_contrato(
                int(self.contrato.id),
                motivo=motivo,
                fecha_terminacion=fecha,
                generar_liquidacion=bool(self.generar_var.get()),
            )
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("No se pudo terminar el contrato: %s", e)
            messagebox.showerror("Contratos", f"No se pudo terminar el contrato:\n{e}")
            return
        self.guardado = True
        messagebox.showinfo(
            "Contratos", f"Contrato {self.contrato.numero} terminado y liquidación registrada."
        )
        self.destroy()
