"""Ícono de bandeja del sistema (Windows) para el actualizador automático.

Implementado únicamente con ctypes y la biblioteca estándar:

  * crea una ventana oculta (message-only) que recibe los mensajes del
    ícono del área de notificación (la bandeja, abajo a la derecha),
  * muestra un menú contextual con clic derecho
    (Buscar actualizaciones ahora / Mostrar ventana / Salir),
  * entrega los comandos del menú a la aplicación mediante una cola
    thread-safe.

En plataformas que no sean Windows la clase es un no-op: el resto de la
aplicación puede llamarla sin preocuparse de la plataforma.
"""

from __future__ import annotations

import ctypes
import queue
import sys
import threading
from ctypes import wintypes as wt
from pathlib import Path

# ---------------------------------------------------------------------------
# Constantes de Windows
# ---------------------------------------------------------------------------
WM_APP = 0x8000
WM_TRAYICON = WM_APP + 13
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B
WM_DESTROY = 0x0002
WM_CLOSE = 0x0010

NIM_ADD = 0
NIM_MODIFY = 1
NIM_DELETE = 2
NIF_MESSAGE = 0x0001
NIF_ICON = 0x0002
NIF_TIP = 0x0004

HWND_MESSAGE = -3

IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010
IDI_APPLICATION = 32512

MF_STRING = 0x0000
MF_SEPARATOR = 0x0800
TPM_RETURNCMD = 0x0100
TPM_RIGHTBUTTON = 0x0002

CLASS_NAME = "SDEP_CPP5_AutoUpdater_Tray"


# ---------------------------------------------------------------------------
# Estructuras y funciones nativas (solo Windows)
# ---------------------------------------------------------------------------
class NOTIFYICONDATAW(ctypes.Structure):
    """Estructura NOTIFYICONDATAW (Windows 7 en adelante)."""

    _fields_ = [
        ("cbSize", wt.DWORD),
        ("hWnd", wt.HWND),
        ("uID", wt.UINT),
        ("uFlags", wt.UINT),
        ("uCallbackMessage", wt.UINT),
        ("hIcon", wt.HANDLE),
        ("szTip", ctypes.c_wchar * 128),
        ("dwState", wt.DWORD),
        ("dwStateMask", wt.DWORD),
        ("szInfo", ctypes.c_wchar * 256),
        ("uVersion", wt.UINT),
        ("szInfoTitle", ctypes.c_wchar * 64),
        ("dwInfoFlags", wt.DWORD),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", wt.HANDLE),
    ]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wt.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wt.HINSTANCE),
        ("hIcon", wt.HANDLE),
        ("hCursor", wt.HANDLE),
        ("hbrBackground", wt.HANDLE),
        ("lpszMenuName", ctypes.c_wchar_p),
        ("lpszClassName", ctypes.c_wchar_p),
    ]


WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)

_user32 = None
_shell32 = None
_kernel32 = None


def _win32_api() -> None:
    """Inicializa (una sola vez) las funciones nativas de Windows."""
    global _user32, _shell32, _kernel32
    if _user32 is not None or sys.platform != "win32":
        return
    _user32 = ctypes.windll.user32
    _shell32 = ctypes.windll.shell32  # Shell_NotifyIconW vive en shell32
    _kernel32 = ctypes.windll.kernel32

    _shell32.Shell_NotifyIconW.argtypes = [wt.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
    _shell32.Shell_NotifyIconW.restype = wt.BOOL

    _user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    _user32.RegisterClassW.restype = wt.ATOM

    _user32.CreateWindowExW.argtypes = [
        wt.DWORD, ctypes.c_wchar_p, ctypes.c_wchar_p, wt.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wt.HWND, wt.HMENU, wt.HINSTANCE, ctypes.c_void_p,
    ]
    _user32.CreateWindowExW.restype = wt.HWND

    _user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
    _user32.DefWindowProcW.restype = ctypes.c_ssize_t

    _user32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
    _user32.PostMessageW.restype = wt.BOOL

    _user32.GetMessageW.argtypes = [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT]
    _user32.GetMessageW.restype = wt.BOOL

    _user32.TranslateMessage.argtypes = [ctypes.POINTER(wt.MSG)]
    _user32.TranslateMessage.restype = wt.BOOL

    _user32.DispatchMessageW.argtypes = [ctypes.POINTER(wt.MSG)]
    _user32.DispatchMessageW.restype = ctypes.c_ssize_t

    _user32.PostQuitMessage.argtypes = [ctypes.c_int]

    _user32.DestroyWindow.argtypes = [wt.HWND]
    _user32.DestroyWindow.restype = wt.BOOL

    _user32.LoadImageW.argtypes = [
        wt.HINSTANCE, ctypes.c_wchar_p, wt.UINT, ctypes.c_int, ctypes.c_int, wt.UINT,
    ]
    _user32.LoadImageW.restype = wt.HANDLE

    _user32.LoadIconW.argtypes = [wt.HINSTANCE, ctypes.c_wchar_p]
    _user32.LoadIconW.restype = wt.HANDLE

    _user32.CreatePopupMenu.restype = wt.HMENU
    # UINT_PTR: puntero de tamaño nativo (ctypes.wintypes no lo define)
    _user32.AppendMenuW.argtypes = [wt.HMENU, wt.UINT, ctypes.c_size_t, ctypes.c_wchar_p]
    _user32.AppendMenuW.restype = wt.BOOL

    _user32.TrackPopupMenu.argtypes = [
        wt.HMENU, wt.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.HWND, ctypes.c_void_p,
    ]
    _user32.TrackPopupMenu.restype = ctypes.c_ulong

    _user32.DestroyMenu.argtypes = [wt.HMENU]
    _user32.DestroyMenu.restype = wt.BOOL

    _user32.GetCursorPos.argtypes = [ctypes.POINTER(wt.POINT)]
    _user32.GetCursorPos.restype = wt.BOOL

    _kernel32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    _kernel32.GetModuleHandleW.restype = wt.HMODULE


# Instancias activas por hwnd, para que WndProc sepa a qué TrayIcon pertenece
_INSTANCES: dict[int, "TrayIcon"] = {}


def _icon_path() -> Path | None:
    """Localiza assets/app.ico (datos del .exe compilado o el repo)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidato = Path(base) / "assets" / "app.ico"
        if candidato.exists():
            return candidato
    candidato = Path(__file__).resolve().parent.parent / "assets" / "app.ico"
    return candidato if candidato.exists() else None


class TrayIcon:
    """Ícono de bandeja con menú contextual (Windows). No-op en otros SO.

    Los comandos del menú se entregan como diccionarios {"action": ...}
    a la cola ``commands``: "check_now", "show" o "exit".
    """

    MENU_CHECK = 1001
    MENU_SHOW = 1002
    MENU_EXIT = 1003

    def __init__(self, commands: queue.Queue, tooltip: str = "Actualizador SDEP_CPP5"):
        self._commands = commands
        self._tooltip = tooltip
        self._hwnd: int | None = None
        self._hicon = None
        self._thread: threading.Thread | None = None
        self._stopping = threading.Event()
        self._wndproc_ref: WNDPROC | None = None

    # ------------------------------------------------------------------ API
    def start(self) -> None:
        """Arranca el hilo de la bandeja (una sola vez)."""
        if sys.platform != "win32" or self._thread is not None:
            return
        _win32_api()
        self._thread = threading.Thread(target=self._run, name="tray-icon", daemon=True)
        self._thread.start()

    def close(self) -> None:
        """Quita el ícono y detiene el hilo (idempotente)."""
        self._stopping.set()
        if sys.platform == "win32" and _user32 is not None and self._hwnd:
            _user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
        if self._thread is not None:
            self._thread.join(timeout=3)

    def update_tooltip(self, text: str) -> None:
        """Actualiza el texto flotante del ícono (máx. 127 caracteres)."""
        if sys.platform != "win32" or _shell32 is None or self._hwnd is None:
            return
        self._tooltip = text
        nid = self._make_nid(tip=text)
        _shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    # ------------------------------------------------------------- internals
    def _run(self) -> None:
        self._wndproc_ref = WNDPROC(self._wnd_proc)
        wc = WNDCLASSW()
        wc.lpfnWndProc = ctypes.cast(self._wndproc_ref, ctypes.c_void_p)
        wc.hInstance = _kernel32.GetModuleHandleW(None)
        wc.lpszClassName = CLASS_NAME
        _user32.RegisterClassW(ctypes.byref(wc))

        hwnd = _user32.CreateWindowExW(
            0, CLASS_NAME, "SDEP_CPP5", 0,
            0, 0, 0, 0, HWND_MESSAGE, None, wc.hInstance, None,
        )
        if not hwnd:
            return
        self._hwnd = hwnd
        _INSTANCES[hwnd] = self
        self._hicon = self._load_icon()
        _shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(self._make_nid(tip=self._tooltip)))

        try:
            msg = wt.MSG()
            while not self._stopping.is_set():
                result = _user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result <= 0:  # WM_QUIT o error
                    break
                _user32.TranslateMessage(ctypes.byref(msg))
                _user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            _shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._make_nid()))
            _INSTANCES.pop(hwnd, None)
            _user32.DestroyWindow(hwnd)
            self._hwnd = None

    def _wnd_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_TRAYICON:
            event = lparam & 0xFFFF
            if event in (WM_RBUTTONUP, WM_CONTEXTMENU):
                self._show_menu()
            elif event == WM_LBUTTONDBLCLK:
                self._put("show")
            return 0
        if msg == WM_DESTROY:
            _user32.PostQuitMessage(0)
            return 0
        return _user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _show_menu(self) -> None:
        menu = _user32.CreatePopupMenu()
        if not menu:
            return
        try:
            _user32.AppendMenuW(menu, MF_STRING, self.MENU_CHECK, "Buscar actualizaciones ahora")
            _user32.AppendMenuW(menu, MF_STRING, self.MENU_SHOW, "Mostrar ventana")
            _user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
            _user32.AppendMenuW(menu, MF_STRING, self.MENU_EXIT, "Salir")
            pt = wt.POINT()
            _user32.GetCursorPos(ctypes.byref(pt))
            cmd = _user32.TrackPopupMenu(
                menu, TPM_RETURNCMD | TPM_RIGHTBUTTON,
                pt.x, pt.y, 0, self._hwnd, None,
            )
        finally:
            _user32.DestroyMenu(menu)
        if cmd == self.MENU_CHECK:
            self._put("check_now")
        elif cmd == self.MENU_SHOW:
            self._put("show")
        elif cmd == self.MENU_EXIT:
            self._put("exit")

    def _put(self, action: str) -> None:
        try:
            self._commands.put_nowait({"action": action})
        except Exception:
            pass

    def _make_nid(self, tip: str | None = None) -> NOTIFYICONDATAW:
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = self._hicon
        nid.szTip = (tip or self._tooltip)[:127]
        return nid

    def _load_icon(self):
        ruta = _icon_path()
        if ruta:
            hicon = _user32.LoadImageW(
                None, str(ruta), IMAGE_ICON, 32, 32, LR_LOADFROMFILE
            )
            if hicon:
                return hicon
        # Respaldo: ícono genérico de aplicación de Windows
        return _user32.LoadIconW(
            None, ctypes.cast(ctypes.c_void_p(IDI_APPLICATION), ctypes.c_wchar_p)
        )