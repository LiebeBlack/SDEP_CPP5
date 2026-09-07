"""Ventana de estado del actualizador automático + bandeja del sistema.

Muestra en una ventana de tkinter todo lo que el actualizador hace
(comprobar, descargar, instalar, resultado) y coloca un ícono en la
bandeja del sistema (solo Windows) mientras trabaja.

El trabajo pesado (consulta a GitHub, descarga, instalación) corre en un
hilo secundario; la ventana solo se toca desde el hilo principal de Tk
mediante una cola thread-safe.
"""

from __future__ import annotations

import queue
import threading
from datetime import datetime

import tkinter as tk
from tkinter import ttk

from updater.tray_icon import TrayIcon

AUTO_CLOSE_MS = 6000      # cierre automático en éxito ("ya actualizado"/"completada")
POLL_MS = 120             # frecuencia de lectura de la cola
COLOR_EXITO = "#1a7f37"
COLOR_ERROR = "#b3261e"
COLOR_DETALLE = "#5f6368"


def _hora() -> str:
    return datetime.now().strftime("%H:%M:%S")


class UpdaterGui:
    """Ventana de estado del actualizador.

    ``run()`` ejecuta la comprobación/actualización y devuelve el código
    de resultado (0 = sin cambios, 1 = error, 2 = actualización realizada).
    """

    def __init__(self, install: bool):
        from updater import auto_updater as auto

        self._auto = auto
        self._install = install
        self._result_code = 0
        self._finished = False
        self._closing = False
        self._busy = False
        self._queue: queue.Queue = queue.Queue()
        self._root = tk.Tk()
        self._tray = TrayIcon(self._queue, tooltip="Actualizador SDEP_CPP5")
        self._build_window()

    # ------------------------------------------------------------------ API
    def run(self) -> int:
        """Arranca el hilo de trabajo, muestra la ventana y espera a que
        termine (o a que el usuario la cierre). Devuelve el código final."""
        self._auto.on_progress = self._emit_status
        self._auto.on_download = self._emit_download
        self._start_worker()
        self._tray.start()
        self._root.after(POLL_MS, self._poll)
        try:
            self._root.mainloop()
        except tk.TclError:
            pass
        finally:
            self._auto.on_progress = None
            self._auto.on_download = None
            self._tray.close()
        return self._result_code

    # ------------------------------------------------------------- ventana
    def _build_window(self) -> None:
        root = self._root
        root.title("Actualizador — Sistema de Gestión de Personal")
        ruta_icono = self._icon_path()
        if ruta_icono:
            try:
                root.iconbitmap(default=ruta_icono)
            except tk.TclError:
                pass
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        ancho, alto = 500, 360
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{ancho}x{alto}+{(sw - ancho) // 2}+{(sh - alto) // 2}")

        marco = ttk.Frame(root, padding=14)
        marco.pack(fill="both", expand=True)

        ttk.Label(
            marco, text="Actualizador automático",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")

        self._status = tk.Label(
            marco, text="Iniciando…", font=("Segoe UI", 11), anchor="w",
            justify="left", wraplength=460,
        )
        self._status.pack(fill="x", pady=(10, 2))

        self._detail = tk.Label(
            marco, text="", font=("Segoe UI", 9), fg=COLOR_DETALLE,
            anchor="w", justify="left", wraplength=460,
        )
        self._detail.pack(fill="x")

        self._progress = ttk.Progressbar(marco, mode="indeterminate", length=470)
        self._progress.pack(fill="x", pady=(8, 4))
        self._progress.start(12)

        ttk.Label(marco, text="Registro de actividad:", font=("Segoe UI", 9)).pack(
            anchor="w", pady=(4, 2)
        )
        self._log = tk.Text(
            marco, height=8, width=60, state="disabled",
            font=("Consolas", 8), wrap="word",
        )
        self._log.pack(fill="both", expand=True)

        botones = ttk.Frame(marco)
        botones.pack(fill="x", pady=(10, 0))
        self._btn_check = ttk.Button(
            botones, text="Buscar ahora", command=self._check_now, state="disabled"
        )
        self._btn_check.pack(side="left")
        self._btn_close = ttk.Button(botones, text="Cerrar", command=self._on_close)
        self._btn_close.pack(side="right")

    def _icon_path(self):
        import sys
        from pathlib import Path

        base = getattr(sys, "_MEIPASS", None)
        if base:
            candidato = Path(base) / "assets" / "app.ico"
            if candidato.exists():
                return str(candidato)
        candidato = (
            Path(__file__).resolve().parent.parent / "assets" / "app.ico"
        )
        return str(candidato) if candidato.exists() else None

    # ---------------------------------------------------------- hilo trabajo
    def _start_worker(self) -> None:
        self._busy = True
        self._finished = False
        self._btn_check.config(state="disabled")
        self._set_status("Comprobando actualizaciones…")
        self._progress.start(12)
        hilo = threading.Thread(target=self._worker, name="updater-worker", daemon=True)
        hilo.start()

    def _worker(self) -> None:
        try:
            self._result_code = self._auto.run_check(install=self._install)
        except Exception as exc:  # red de seguridad: nunca colgar la ventana
            self._result_code = 1
            self._emit_status(f"Error inesperado: {exc}")
        self._queue.put_nowait(("finished", self._result_code))

    # ------------------------------------------------------------- cola Tk
    def _emit_status(self, message: str) -> None:
        try:
            self._queue.put_nowait(("status", message))
        except Exception:
            pass

    def _emit_download(self, done: int, total: int) -> None:
        try:
            self._queue.put_nowait(("download", done, total))
        except Exception:
            pass

    def _poll(self) -> None:
        try:
            while True:
                item = self._queue.get_nowait()
                self._handle(item)
        except queue.Empty:
            pass
        if not self._closing:
            self._root.after(POLL_MS, self._poll)

    def _handle(self, item) -> None:
        kind = item[0]
        if kind == "status":
            self._on_status(item[1])
        elif kind == "download":
            self._on_download(item[1], item[2])
        elif kind == "finished":
            self._on_finished(item[1])
        elif kind == "check_now":
            if self._finished and not self._busy:
                self._start_worker()
        elif kind == "show":
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()
        elif kind == "exit":
            self._on_close()

    def _on_status(self, message: str) -> None:
        self._append_log(message)
        self._set_status(message)
        tooltip = message
        if len(tooltip) > 120:
            tooltip = tooltip[:117] + "…"
        self._tray.update_tooltip(tooltip)

    def _on_download(self, done: int, total: int) -> None:
        if total and done <= total:
            self._progress.stop()
            self._progress.config(mode="determinate", maximum=total, value=done)
            pct = done * 100 // total
            self._set_status(
                f"Descargando… {done / (1024 * 1024):.1f} de "
                f"{total / (1024 * 1024):.1f} MB ({pct} %)"
            )
        else:
            self._set_status(f"Descargando… {done / (1024 * 1024):.1f} MB")

    def _on_finished(self, code: int) -> None:
        self._busy = False
        self._finished = True
        self._progress.stop()
        if code == 0:
            self._set_status("✓ Ya está actualizado: todo al día", COLOR_EXITO)
        elif code == 2:
            self._set_status("✓ Actualización completada", COLOR_EXITO)
        else:
            self._set_status("✗ Hubo un error (consulta el registro)", COLOR_ERROR)
        self._append_log(f"Resultado: {self._status.cget('text')}")
        self._tray.update_tooltip(f"Actualizador: {self._status.cget('text')}")
        self._btn_check.config(state="normal")
        if code != 1:
            # Cierre automático tras unos segundos (resultado normal)
            self._root.after(AUTO_CLOSE_MS, self._on_close)

    # --------------------------------------------------------------- helpers
    def _set_status(self, text: str, color: str | None = None) -> None:
        self._status.config(text=text, fg=color or "#202124")

    def _append_log(self, line: str) -> None:
        self._log.config(state="normal")
        self._log.insert("end", f"[{_hora()}] {line}\n")
        self._log.see("end")
        self._log.config(state="disabled")

    def _check_now(self) -> None:
        if self._busy or self._closing:
            return
        self._log.config(state="normal")
        self._log.insert("end", f"[{_hora()}] --- Comprobación manual ---\n")
        self._log.config(state="disabled")
        self._start_worker()

    def _on_close(self) -> None:
        if self._closing:
            return
        self._closing = True
        try:
            self._root.destroy()
        except tk.TclError:
            pass