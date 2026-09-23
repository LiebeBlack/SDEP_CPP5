"""
Módulo de Anticipos y Préstamos

Administra las solicitudes de anticipo y préstamo del personal: alta con
validación del tope de descuento sobre el salario, aprobación o rechazo,
seguimiento del saldo por cuotas, plan de pagos y exportación.
"""

import logging
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import customtkinter as ctk

from src.gui.frames import _habilitar_orden_columnas, _seleccionar_fila_click
from src.gui.theme import COLORES
from src.models import Empleado, EstadoPrestamo, Prestamo, TipoPrestamo
from src.utils.helpers import format_currency, format_date, parse_date

logger = logging.getLogger(__name__)

FILTROS = ["Todos", "Pendientes", "Activos", "Pagados", "Rechazados o cancelados"]
ETIQUETAS_ESTADO = {
    "solicitado": "Solicitado",
    "aprobado": "Aprobado",
    "activo": "Activo",
    "pagado": "Pagado",
    "cancelado": "Rechazado o cancelado",
}


class PrestamosFrame(ctk.CTkFrame):
    """Frame del módulo de anticipos y préstamos"""

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window
        self.session = main_window.session
        self.servicio = self._crear_servicio()
        self._empleados: dict[int, Empleado] = {}
        self.prestamos: list[Prestamo] = []
        self._create_widgets()
        self._cargar_empleados()
        self._load_data()

    def _crear_servicio(self):
        """Crea el servicio de préstamos con la sesión activa"""
        try:
            from src.services import PrestamoService

            return PrestamoService(self.session)
        except (ImportError, AttributeError) as e:
            logger.error("No se pudo inicializar el servicio de préstamos: %s", e)
            return None

    # ------------------------------------------------------------------
    # Interfaz
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Crea la barra de acciones, la tabla y el resumen"""
        ctk.CTkLabel(
            self,
            text="Anticipos y Préstamos",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORES["texto"],
        ).pack(pady=(14, 6), padx=20, anchor="w")

        self._crear_barra_acciones()
        self._crear_tabla()
        self._crear_resumen()

    def _crear_barra_acciones(self) -> None:
        """Filtros y acciones sobre préstamos"""
        barra = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        barra.pack(fill="x", padx=20, pady=8)

        ctk.CTkLabel(barra, text="Estado:", text_color=COLORES["texto"]).pack(
            side="left", padx=(12, 4), pady=10
        )
        self.estado_combo = ctk.CTkComboBox(
            barra, width=140, values=FILTROS, command=lambda _v: self._load_data()
        )
        self.estado_combo.pack(side="left", pady=10)
        self.estado_combo.set("Pendientes")

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
            text="📋 Plan de pagos",
            width=130,
            fg_color=COLORES["campo"],
            hover_color=COLORES["panel_hover"],
            command=self._ver_plan,
        ).pack(side="right", padx=4)

        if self.main_window.tiene_permiso("update"):
            ctk.CTkButton(
                barra,
                text="❌ Rechazar",
                width=110,
                fg_color=COLORES["campo"],
                hover_color=COLORES["panel_hover"],
                command=self._rechazar,
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                barra,
                text="✅ Aprobar",
                width=110,
                fg_color=COLORES["campo"],
                hover_color=COLORES["panel_hover"],
                command=self._aprobar,
            ).pack(side="right", padx=4)

        if self.main_window.tiene_permiso("create"):
            ctk.CTkButton(
                barra, text="➕ Nueva solicitud", width=150, command=self._nueva_solicitud
            ).pack(side="right", padx=4)

    def _crear_tabla(self) -> None:
        """Tabla de préstamos"""
        contenedor = ctk.CTkFrame(self, fg_color=COLORES["panel"], corner_radius=8)
        contenedor.pack(fill="both", expand=True, padx=20, pady=8)

        columnas = (
            "empleado",
            "tipo",
            "monto",
            "cuota",
            "pagadas",
            "saldo",
            "avance",
            "solicitud",
            "estado",
        )
        self.tree = ttk.Treeview(contenedor, columns=columnas, show="headings", height=15)
        encabezados = {
            "empleado": ("Empleado", 220),
            "tipo": ("Tipo", 100),
            "monto": ("Monto", 110),
            "cuota": ("Cuota", 100),
            "pagadas": ("Pagadas", 80),
            "saldo": ("Saldo", 110),
            "avance": ("Avance", 80),
            "solicitud": ("Solicitud", 100),
            "estado": ("Estado", 110),
        }
        for clave, (texto, ancho) in encabezados.items():
            self.tree.heading(clave, text=texto)
            self.tree.column(
                clave, width=ancho, anchor="w" if clave == "empleado" else "center"
            )

        _habilitar_orden_columnas(self.tree)
        self.tree.bind(
            "<ButtonRelease-1>", lambda evento: _seleccionar_fila_click(self.tree, evento)
        )
        self.tree.bind("<Double-1>", lambda _evento: self._ver_plan())

        scrollbar = ttk.Scrollbar(contenedor, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

    def _crear_resumen(self) -> None:
        """Resumen de cartera de préstamos"""
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
        """Carga los préstamos según el filtro seleccionado"""
        if self.servicio is None:
            messagebox.showerror("Préstamos", "El servicio de préstamos no está disponible")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        filtro = self.estado_combo.get().strip()
        empleado_id = self._empleado_seleccionado()
        try:
            if self.servicio.sincronizar_estados():
                logger.debug("Estados de préstamos sincronizados")
            if empleado_id is not None:
                prestamos = self.servicio.listar_por_empleado(empleado_id)
                prestamos = self._aplicar_filtro(prestamos, filtro)
            elif filtro == "Pendientes":
                prestamos = self.servicio.listar_pendientes_aprobacion()
            elif filtro == "Activos":
                prestamos = self.servicio.listar_activos()
            elif filtro == "Pagados":
                prestamos = self.servicio.listar_por_estado(EstadoPrestamo.PAGADO.value)
            elif filtro == "Rechazados o cancelados":
                prestamos = self.servicio.listar_por_estado(EstadoPrestamo.CANCELADO.value)
            else:
                prestamos = self.servicio.listar_prestamos()
        except (AttributeError, ValueError, TypeError) as e:
            logger.error("Error consultando préstamos: %s", e)
            messagebox.showerror("Préstamos", f"No se pudieron consultar los préstamos:\n{e}")
            return

        self.prestamos = prestamos
        for prestamo in prestamos:
            empleado = self._empleados.get(int(prestamo.empleado_id))
            nombre = empleado.nombre_completo if empleado else f"Empleado {prestamo.empleado_id}"
            self.tree.insert(
                "",
                "end",
                iid=str(prestamo.id),
                values=(
                    nombre,
                    "Anticipo" if prestamo.tipo_valor == TipoPrestamo.ANTICIPO.value else "Préstamo",
                    format_currency(float(prestamo.monto or 0)),
                    format_currency(float(prestamo.monto_cuota or 0)),
                    f"{int(prestamo.cuotas_pagadas or 0)}/{int(prestamo.numero_cuotas or 0)}",
                    format_currency(float(prestamo.saldo or 0)),
                    f"{float(prestamo.porcentaje_pagado or 0):.0f}%",
                    format_date(prestamo.fecha_solicitud),
                    ETIQUETAS_ESTADO.get(prestamo.estado_valor, prestamo.estado_valor),
                ),
            )

        self._actualizar_resumen()

    def _aplicar_filtro(self, prestamos: list, filtro: str) -> list:
        """Filtra una lista de préstamos por estado"""
        mapa = {
            "Pendientes": {EstadoPrestamo.SOLICITADO.value},
            "Activos": {EstadoPrestamo.APROBADO.value, EstadoPrestamo.ACTIVO.value},
            "Pagados": {EstadoPrestamo.PAGADO.value},
            "Rechazados o cancelados": {EstadoPrestamo.CANCELADO.value},
        }
        estados = mapa.get(filtro)
        if estados is None:
            return prestamos
        return [prestamo for prestamo in prestamos if prestamo.estado_valor in estados]

    def _actualizar_resumen(self) -> None:
        """Muestra los totales de la cartera mostrada"""
        activos = [prestamo for prestamo in self.prestamos if prestamo.esta_activo]
        pendientes = [
            prestamo
            for prestamo in self.prestamos
            if prestamo.estado_valor == EstadoPrestamo.SOLICITADO.value
        ]
        saldo = sum(float(prestamo.saldo or 0) for prestamo in activos)
        otorgado = sum(float(prestamo.monto or 0) for prestamo in self.prestamos)
        self.resumen_label.configure(
            text=(
                f"Registros: {len(self.prestamos)} | Activos: {len(activos)} | "
                f"Pendientes de aprobación: {len(pendientes)} | "
                f"Otorgado: {format_currency(otorgado)} | Saldo por cobrar: {format_currency(saldo)}"
            )
        )

    def _prestamo_seleccionado(self):
        """Préstamo seleccionado en la tabla"""
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Préstamos", "Seleccione un préstamo de la tabla")
            return None
        try:
            prestamo_id = int(seleccion[0])
        except (TypeError, ValueError):
            return None
        return next(
            (prestamo for prestamo in self.prestamos if int(prestamo.id) == prestamo_id), None
        )

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------
    def _nueva_solicitud(self) -> None:
        """Abre el diálogo de nueva solicitud"""
        dialogo = SolicitudDialog(self, self.main_window, self._empleados, self.servicio)
        self.wait_window(dialogo)
        if getattr(dialogo, "guardado", False):
            self._load_data()

    def _aprobar(self) -> None:
        """Aprueba la solicitud seleccionada"""
        prestamo = self._prestamo_seleccionado()
        if prestamo is None or self.servicio is None:
            return
        usuario = getattr(getattr(self.main_window, "current_user", None), "username", None)
        if not messagebox.askyesno(
            "Préstamos",
            f"¿Aprobar el {prestamo.tipo_valor} de "
            f"{format_currency(float(prestamo.monto or 0))}?",
        ):
            return
        try:
            self.servicio.aprobar(int(prestamo.id), aprobado_por=usuario or "sistema")
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("No se pudo aprobar el préstamo: %s", e)
            messagebox.showerror("Préstamos", f"No se pudo aprobar la solicitud:\n{e}")
            return
        messagebox.showinfo("Préstamos", "Solicitud aprobada. Se descontará en la nómina.")
        self._load_data()

    def _rechazar(self) -> None:
        """Rechaza la solicitud seleccionada"""
        prestamo = self._prestamo_seleccionado()
        if prestamo is None or self.servicio is None:
            return
        motivo = ctk.CTkInputDialog(
            text="Motivo del rechazo:", title="Rechazar solicitud"
        ).get_input()
        if motivo is None:
            return
        try:
            self.servicio.rechazar(int(prestamo.id), motivo=motivo.strip() or None)
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("No se pudo rechazar el préstamo: %s", e)
            messagebox.showerror("Préstamos", f"No se pudo rechazar la solicitud:\n{e}")
            return
        self._load_data()

    def _ver_plan(self) -> None:
        """Muestra el plan de pagos del préstamo seleccionado"""
        prestamo = self._prestamo_seleccionado()
        if prestamo is None or self.servicio is None:
            return
        try:
            plan = self.servicio.plan_de_pagos(int(prestamo.id))
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("No se pudo calcular el plan de pagos: %s", e)
            messagebox.showerror("Préstamos", f"No se pudo calcular el plan de pagos:\n{e}")
            return

        lineas = [
            f"{prestamo.tipo_valor.capitalize()} de "
            f"{format_currency(float(prestamo.monto or 0))}",
            f"Estado: {ETIQUETAS_ESTADO.get(prestamo.estado_valor, prestamo.estado_valor)}",
            f"Cuotas: {int(prestamo.cuotas_pagadas or 0)}/{int(prestamo.numero_cuotas or 0)}",
            f"Saldo: {format_currency(float(prestamo.saldo or 0))}",
            "",
            "Cuota  |  Monto  |  Saldo al pagar",
        ]
        for cuota in plan:
            lineas.append(
                f"{int(cuota.get('numero', 0)):>5}  |  "
                f"{format_currency(float(cuota.get('monto', 0)))}  |  "
                f"{format_currency(float(cuota.get('saldo', 0)))}"
            )
        messagebox.showinfo(f"Plan de pagos #{prestamo.id}", "\n".join(lineas))

    # ------------------------------------------------------------------
    # Exportación
    # ------------------------------------------------------------------
    def _filas_exportables(self) -> list[dict]:
        """Convierte los préstamos en filas planas para exportar"""
        filas = []
        for prestamo in self.prestamos:
            empleado = self._empleados.get(int(prestamo.empleado_id))
            filas.append(
                {
                    "Empleado": empleado.nombre_completo
                    if empleado
                    else prestamo.empleado_id,
                    "Cedula": getattr(empleado, "cedula", ""),
                    "Tipo": "Anticipo"
                    if prestamo.tipo_valor == TipoPrestamo.ANTICIPO.value
                    else "Préstamo",
                    "Estado": ETIQUETAS_ESTADO.get(prestamo.estado_valor, prestamo.estado_valor),
                    "Monto": float(prestamo.monto or 0),
                    "Cuotas": int(prestamo.numero_cuotas or 0),
                    "Cuotas_pagadas": int(prestamo.cuotas_pagadas or 0),
                    "Monto_cuota": float(prestamo.monto_cuota or 0),
                    "Saldo": float(prestamo.saldo or 0),
                    "Avance": round(float(prestamo.porcentaje_pagado or 0), 2),
                    "Solicitud": format_date(prestamo.fecha_solicitud),
                    "Aprobacion": format_date(prestamo.fecha_aprobacion)
                    if prestamo.fecha_aprobacion
                    else "",
                    "Motivo": prestamo.motivo or "",
                }
            )
        return filas

    def _exportar(self) -> None:
        """Exporta el listado de préstamos"""
        if not self.prestamos:
            messagebox.showinfo("Préstamos", "No hay préstamos para exportar")
            return
        try:
            from pathlib import Path

            from src.config import settings
            from src.utils.exporter import exportar_archivo
            from src.utils.helpers import ensure_directory_exists, get_timestamp

            carpeta = Path(settings.exports_path)
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"prestamos_{get_timestamp()}.xlsx"
            exportar_archivo(self._filas_exportables(), str(destino), hoja="Prestamos")
            messagebox.showinfo("Préstamos", f"Exportado en:\n{destino}")
        except (OSError, ValueError, ImportError) as e:
            logger.warning("No se pudo exportar los préstamos", exc_info=True)
            messagebox.showerror("Préstamos", f"No se pudo exportar:\n{e}")

    def _exportar_pdf(self) -> None:
        """Genera el reporte PDF de préstamos mostrados"""
        if not self.prestamos:
            messagebox.showinfo("Préstamos", "No hay préstamos para el reporte")
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

            carpeta = Path(settings.exports_path) / "prestamos"
            ensure_directory_exists(str(carpeta))
            destino = carpeta / f"reporte_prestamos_{get_timestamp()}.pdf"
            pdf_generator.generate_reporte_prestamos(
                self._filas_exportables(), str(destino), titulo=self.estado_combo.get()
            )
            abrir_con_aplicacion_predeterminada(destino)
            messagebox.showinfo("Préstamos", f"Reporte generado:\n{destino}")
        except (OSError, ValueError, ImportError) as e:
            logger.warning("No se pudo generar el reporte de préstamos", exc_info=True)
            messagebox.showerror("Préstamos", f"No se pudo generar el reporte:\n{e}")


class SolicitudDialog(ctk.CTkToplevel):
    """Diálogo de solicitud de anticipo o préstamo"""

    def __init__(
        self, parent, main_window, empleados: dict[int, Empleado], servicio
    ):
        super().__init__(parent)
        self.main_window = main_window
        self.empleados = empleados
        self.servicio = servicio
        self.guardado = False

        self.title("Nueva solicitud de anticipo o préstamo")
        self.geometry("520x520")
        self.resizable(False, False)
        self.transient(parent)

        self._create_widgets()
        self._actualizar_topes()
        self._centrar()

    def _centrar(self) -> None:
        """Prepara el diálogo modal"""
        try:
            self.update_idletasks()
            self.grab_set()
        except tk.TclError:
            logger.debug("Diálogo de solicitud sin grab establecido", exc_info=True)

    def _create_widgets(self) -> None:
        """Crea los campos del formulario"""
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=16)

        valores = [
            f"{empleado.cedula} - {empleado.nombre_completo}"
            for empleado in self.empleados.values()
        ]

        ctk.CTkLabel(contenedor, text="Empleado:", text_color=COLORES["texto"]).grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.empleado_combo = ctk.CTkComboBox(contenedor, width=300, values=valores or ["-"])
        self.empleado_combo.grid(row=0, column=1, sticky="w", pady=6)
        if valores:
            self.empleado_combo.set(valores[0])
        self.empleado_combo.configure(command=lambda _v: self._actualizar_topes())

        ctk.CTkLabel(contenedor, text="Tipo:", text_color=COLORES["texto"]).grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.tipo_combo = ctk.CTkComboBox(
            contenedor, width=180, values=[tipo.value for tipo in TipoPrestamo]
        )
        self.tipo_combo.grid(row=1, column=1, sticky="w", pady=6)
        self.tipo_combo.set(TipoPrestamo.PRESTAMO.value)
        self.tipo_combo.configure(command=lambda _v: self._actualizar_topes())

        ctk.CTkLabel(contenedor, text="Monto:", text_color=COLORES["texto"]).grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.monto_entry = ctk.CTkEntry(contenedor, width=140)
        self.monto_entry.grid(row=2, column=1, sticky="w", pady=6)
        self.monto_entry.bind("<FocusOut>", lambda _e: self._actualizar_topes())

        ctk.CTkLabel(contenedor, text="Número de cuotas:", text_color=COLORES["texto"]).grid(
            row=3, column=0, sticky="w", pady=6
        )
        self.cuotas_entry = ctk.CTkEntry(contenedor, width=90)
        self.cuotas_entry.grid(row=3, column=1, sticky="w", pady=6)
        self.cuotas_entry.insert(0, "1")
        self.cuotas_entry.bind("<FocusOut>", lambda _e: self._actualizar_topes())

        ctk.CTkLabel(contenedor, text="Fecha de solicitud:", text_color=COLORES["texto"]).grid(
            row=4, column=0, sticky="w", pady=6
        )
        self.fecha_entry = ctk.CTkEntry(contenedor, width=140)
        self.fecha_entry.grid(row=4, column=1, sticky="w", pady=6)
        self.fecha_entry.insert(0, date.today().strftime("%d/%m/%Y"))

        ctk.CTkLabel(contenedor, text="Motivo:", text_color=COLORES["texto"]).grid(
            row=5, column=0, sticky="nw", pady=6
        )
        self.motivo_text = ctk.CTkTextbox(contenedor, width=300, height=70)
        self.motivo_text.grid(row=5, column=1, sticky="w", pady=6)

        self.topes_label = ctk.CTkLabel(
            contenedor,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=COLORES["texto_suave"],
            justify="left",
            anchor="w",
        )
        self.topes_label.grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 0))

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(botones, text="Solicitar", width=120, command=self._guardar).pack(
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

    def _empleado_id(self) -> int | None:
        """Identificador del empleado elegido"""
        seleccion = self.empleado_combo.get().strip()
        if not seleccion:
            return None
        cedula = seleccion.split(" - ", 1)[0].strip()
        for identificador, empleado in self.empleados.items():
            if str(getattr(empleado, "cedula", "")).strip() == cedula:
                return identificador
        return None

    def _monto_capturado(self) -> float:
        """Monto escrito en el formulario (0 si no es válido)"""
        try:
            return float(self.monto_entry.get().strip().replace(",", ".") or 0)
        except (TypeError, ValueError):
            return 0.0

    def _cuotas_capturadas(self) -> int:
        """Número de cuotas escrito en el formulario (1 si no es válido)"""
        try:
            return max(1, int(self.cuotas_entry.get().strip() or 1))
        except (TypeError, ValueError):
            return 1

    def _actualizar_topes(self) -> None:
        """Muestra el monto máximo y la cuota estimada según el salario"""
        if self.servicio is None:
            return
        empleado_id = self._empleado_id()
        if empleado_id is None:
            self.topes_label.configure(text="")
            return

        tipo = self.tipo_combo.get().strip()
        cuotas = 1 if tipo == TipoPrestamo.ANTICIPO.value else self._cuotas_capturadas()
        try:
            maximo = self.servicio.monto_maximo(empleado_id, cuotas)
            saldo = self.servicio.saldo_total(empleado_id)
        except (ValueError, TypeError, AttributeError):
            logger.debug("No se pudieron calcular los topes del préstamo", exc_info=True)
            return

        monto = self._monto_capturado()
        cuota = monto / cuotas if cuotas else 0.0
        self.topes_label.configure(
            text=(
                f"Monto máximo por tope salarial: {format_currency(maximo)} · "
                f"Saldo vigente: {format_currency(saldo)}\n"
                f"Cuota estimada: {format_currency(cuota)} x {cuotas}"
            )
        )

    def _guardar(self) -> None:
        """Valida y registra la solicitud"""
        if self.servicio is None:
            messagebox.showerror("Préstamos", "El servicio de préstamos no está disponible")
            return
        empleado_id = self._empleado_id()
        if empleado_id is None:
            messagebox.showwarning("Préstamos", "Seleccione un empleado")
            return

        monto = self._monto_capturado()
        if monto <= 0:
            messagebox.showwarning("Préstamos", "Indique un monto válido")
            return

        tipo = self.tipo_combo.get().strip()
        cuotas = 1 if tipo == TipoPrestamo.ANTICIPO.value else self._cuotas_capturadas()
        datos = {
            "empleado_id": empleado_id,
            "tipo": tipo,
            "monto": monto,
            "numero_cuotas": cuotas,
            "fecha_solicitud": parse_date(self.fecha_entry.get().strip()) or date.today(),
            "motivo": self.motivo_text.get("1.0", "end").strip() or None,
        }

        errores = self.servicio.validar_datos_prestamo(datos)
        if errores:
            messagebox.showwarning("Préstamos", "\n".join(errores))
            return

        try:
            self.servicio.solicitar(datos)
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("No se pudo registrar la solicitud: %s", e)
            messagebox.showerror("Préstamos", f"No se pudo registrar la solicitud:\n{e}")
            return

        self.guardado = True
        messagebox.showinfo(
            "Préstamos", "Solicitud registrada. Queda pendiente de aprobación."
        )
        self.destroy()
