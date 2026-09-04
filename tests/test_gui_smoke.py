"""
Pruebas de humo de la capa gráfica (GUI)

Instancian la ventana principal, la ventana de login y los marcos de cada
módulo con un Tk real y la base de datos aislada temporal de conftest.
Si el entorno no dispone de pantalla (por ejemplo CI sin X), el módulo
completo se omite con skip en lugar de fallar.

Estas pruebas ejercitan la construcción real de los widgets, la navegación
entre módulos, los atajos de teclado y el cambio de tema, por lo que
detectan errores de ejecución que los análisis estáticos no ven.
"""

import pytest

ctk = pytest.importorskip("customtkinter")


def _tk_disponible() -> bool:
    """¿Hay un display disponible para crear ventanas Tk?"""
    try:
        import tkinter as tk
        raiz = tk.Tk()
        raiz.withdraw()
        raiz.destroy()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _tk_disponible(), reason="No hay display disponible para pruebas GUI")


MODULOS = ["dashboard", "empleados", "documentos",
           "incidencias", "nomina", "configuracion"]


@pytest.fixture()
def admin_usuario(session):
    """Usuario administrador sembrado por la base de datos de pruebas"""
    from src.models import Usuario
    admin = session.query(Usuario).filter(Usuario.username == "admin").first()
    assert admin is not None
    return admin


@pytest.fixture()
def main_window(session, admin_usuario):
    """Ventana principal autenticada como administrador"""
    from src.gui.main_window import MainWindow
    win = MainWindow(current_user=admin_usuario)
    yield win
    try:
        win.destroy()
    except Exception:
        pass


def _toplevels(win):
    return [w for w in win.winfo_children() if isinstance(w, ctk.CTkToplevel)]


class TestMainWindow:
    """Ventana principal: construcción, navegación, atajos y tema"""

    def test_instanciacion_basica(self, main_window):
        from src.config import settings
        from src.gui.frames import DashboardFrame
        assert main_window.title() == settings.app_name
        assert main_window.version_label.cget("text") == f"v{settings.app_version}"
        assert set(main_window.sidebar_buttons) == set(MODULOS)
        assert isinstance(main_window.current_frame, DashboardFrame)
        assert set(main_window.current_frame.stats_cards) == {
            "empleados", "activos", "documentos", "incidencias", "pagos"}
        assert main_window.current_frame.winfo_ismapped()

    def test_permisos_admin(self, main_window):
        for modulo in MODULOS:
            assert main_window.puede_ver_modulo(modulo), modulo
        for permiso in ("create", "update", "delete"):
            assert main_window.tiene_permiso(permiso), permiso
        assert main_window.rol_label() == "Administrador"

    def test_navegacion_todos_los_modulos(self, main_window):
        from src.gui.frames import (
            DashboardFrame, EmpleadosFrame, DocumentosFrame,
            IncidenciasFrame, NominaFrame, ConfiguracionFrame,
        )
        esperados = {
            "dashboard": DashboardFrame,
            "empleados": EmpleadosFrame,
            "documentos": DocumentosFrame,
            "incidencias": IncidenciasFrame,
            "nomina": NominaFrame,
            "configuracion": ConfiguracionFrame,
        }
        for nombre, clase in esperados.items():
            main_window._show_frame(nombre)
            main_window.update()
            assert isinstance(main_window.current_frame, clase), nombre
            assert main_window.current_frame.winfo_ismapped(), nombre

    def test_arboles_de_datos_por_modulo(self, main_window):
        """Cada marco de tabla expone su Treeview y lo construye sin errores"""
        casos = {
            "empleados": "tree",
            "documentos": "tree",
            "incidencias": "tree",
            "nomina": "tree",
            "configuracion": "audit_tree",
        }
        for modulo, attr in casos.items():
            main_window._show_frame(modulo)
            arbol = getattr(main_window.current_frame, attr, None)
            assert arbol is not None, f"{modulo} sin atributo {attr}"
            assert arbol.winfo_exists()

    def test_toggle_apariencia_persiste(self, main_window):
        """El botón de tema alterna oscuro/claro y guarda la preferencia"""
        ctk.set_appearance_mode("Dark")
        main_window._toggle_apariencia()
        assert ctk.get_appearance_mode() == "Light"
        assert main_window.config_service.obtener_valor("apariencia_modo") == "Light"
        assert main_window.current_frame is not None  # el frame se recrea
        main_window._toggle_apariencia()
        assert ctk.get_appearance_mode() == "Dark"
        assert main_window.config_service.obtener_valor("apariencia_modo") == "Dark"

    def test_atajos_en_dashboard(self, main_window):
        main_window._atajo_refrescar()
        assert main_window.status_label.cget("text") == "Lista actualizada (F5)"
        main_window._atajo_nuevo()
        assert "Ctrl+N no aplica" in main_window.status_label.cget("text")
        main_window._atajo_guardar()
        assert "Ctrl+S solo aplica" in main_window.status_label.cget("text")
        main_window._atajo_escape()
        assert main_window.status_label.cget("text")  # sin excepción

    def test_atajos_en_empleados(self, main_window):
        main_window._show_frame("empleados")
        main_window._atajo_refrescar()
        assert "Lista actualizada" in main_window.status_label.cget("text")
        main_window._enfocar_busqueda()
        assert main_window.status_label.cget("text") == "Búsqueda (Ctrl+F)"
        # con una fila seleccionada, Esc limpia la selección
        arbol = main_window.current_frame.tree
        arbol.insert("", "end", iid="fila1", values=("1", "Prueba"))
        arbol.selection_set("fila1")
        main_window._atajo_escape()
        assert not arbol.selection()
        assert "Selección eliminada" in main_window.status_label.cget("text")

    def test_ayuda_y_acerca(self, main_window):
        main_window._on_ayuda()
        main_window.update()
        dialogs = _toplevels(main_window)
        assert len(dialogs) == 1
        assert "Ayuda" in dialogs[0].title()
        dialogs[0].destroy()

        main_window._on_acerca_de()
        main_window.update()
        dialogs = _toplevels(main_window)
        assert len(dialogs) == 1
        assert "Acerca" in dialogs[0].title()
        dialogs[0].destroy()

    def test_mostrar_modulo_invalido(self, main_window):
        """Un módulo desconocido cae en el marco de 'en desarrollo'"""
        main_window._show_frame("modulo_inexistente")
        assert main_window.current_frame is not None


class TestLogin:
    """Ventana de inicio de sesión y diálogo de cambio de contraseña"""

    def test_login_window(self, session):
        from src.gui.login_window import LoginWindow
        win = LoginWindow()
        try:
            win.update()
            assert win.title() == "Iniciar Sesión — Sistema de Gestión de Personal"
            assert win.username_entry is not None
            assert win.password_entry is not None
            assert win.hint_label.cget("text") != ""
        finally:
            win.destroy()

    def test_dialogo_cambio_password(self, session, admin_usuario):
        from src.gui.login_window import CambiarPasswordDialog
        from src.services.auth_service import AuthService
        auth = AuthService(session)
        padre = ctk.CTkToplevel()
        try:
            dlg = CambiarPasswordDialog(padre, auth, admin_usuario)
            dlg.update()
            assert dlg.user_label.cget("text") == "admin"
            dlg.new_pass.insert(0, "NuevaClave123")
            dlg.confirm_pass.insert(0, "NuevaClave123")
            dlg._on_save()
            assert dlg.cambiado is True
            # la contraseña quedó realmente actualizada
            usuario = auth.autenticar(admin_usuario.username, "NuevaClave123")
            assert usuario is not None
            assert not usuario.debe_cambiar_password
        finally:
            padre.destroy()

    def test_dialogo_cambio_password_valida(self, session, admin_usuario):
        """Contraseñas que no coinciden no guardan nada"""
        from src.gui.login_window import CambiarPasswordDialog
        from src.services.auth_service import AuthService
        auth = AuthService(session)
        padre = ctk.CTkToplevel()
        try:
            dlg = CambiarPasswordDialog(padre, auth, admin_usuario)
            dlg.update()
            dlg.new_pass.insert(0, "NuevaClave123")
            dlg.confirm_pass.insert(0, "OtraClave456")
            dlg._on_save()
            assert dlg.cambiado is False
            assert dlg.winfo_exists()  # sigue abierto
        finally:
            padre.destroy()