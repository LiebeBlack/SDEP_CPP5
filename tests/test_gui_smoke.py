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
import time

ctk = pytest.importorskip("customtkinter")


def _tk_disponible() -> bool:
    """
    ¿Hay un display disponible para crear ventanas Tk?

    En Windows siempre hay pantalla y se devuelve True sin crear ninguna
    ventana (evita que parpadee brevemente una ventana 'tk' al recoger
    las pruebas). En Linux/macOS solo se comprueba de verdad si hay una
    variable de display configurada, y la ventana de prueba se crea y
    destruye al instante.
    """
    import os
    import sys

    if sys.platform == "win32":
        return True
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    try:
        import tkinter as tk

        raiz = tk.Tk()
        raiz.withdraw()
        raiz.destroy()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _tk_disponible(), reason="No hay display disponible para pruebas GUI"
)


MODULOS = [
    "dashboard",
    "empleados",
    "documentos",
    "incidencias",
    "contratos",
    "nomina",
    "configuracion",
    "estudiantes",
    "notas",
]


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
    win.update()  # procesa el mapeo del frame inicial antes de asumir
    yield win
    try:
        win.destroy()
    except Exception:
        pass


def _toplevels(win):
    """Todos los CTkToplevel del árbol de widgets (los diálogos pueden
    colgar de cualquier frame, no solo de la raíz)"""
    encontrados = []

    def _walk(w):
        for child in w.winfo_children():
            if isinstance(child, ctk.CTkToplevel):
                encontrados.append(child)
            _walk(child)

    _walk(win)
    return encontrados


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
            "empleados",
            "activos",
            "documentos",
            "incidencias",
            "pagos",
        }
        # Los indicadores analíticos y los gráficos también se construyen
        assert set(main_window.current_frame.indicadores) == {
            "nomina_mes",
            "por_vencer",
            "dotacion",
        }
        for grafico in (
            main_window.current_frame.grafico_departamentos,
            main_window.current_frame.grafico_contratos,
            main_window.current_frame.grafico_egresos,
        ):
            assert grafico.winfo_exists()
        assert main_window.current_frame.winfo_ismapped()

    def test_permisos_admin(self, main_window):
        for modulo in MODULOS:
            assert main_window.puede_ver_modulo(modulo), modulo
        for permiso in ("create", "update", "delete"):
            assert main_window.tiene_permiso(permiso), permiso
        assert main_window.rol_label() == "Administrador"

    def test_navegacion_todos_los_modulos(self, main_window):
        from src.gui.contratos_frame import ContratosFrame
        from src.gui.estudiantes_frame import EstudiantesFrame
        from src.gui.frames import (
            DashboardFrame,
            EmpleadosFrame,
            DocumentosFrame,
            IncidenciasFrame,
            NominaFrame,
            ConfiguracionFrame,
        )
        from src.gui.notas_frame import NotasFrame

        esperados = {
            "dashboard": DashboardFrame,
            "empleados": EmpleadosFrame,
            "documentos": DocumentosFrame,
            "incidencias": IncidenciasFrame,
            "contratos": ContratosFrame,
            "nomina": NominaFrame,
            "configuracion": ConfiguracionFrame,
            "estudiantes": EstudiantesFrame,
            "notas": NotasFrame,
        }
        for nombre, clase in esperados.items():
            main_window._show_frame(nombre)
            main_window.update()
            assert isinstance(main_window.current_frame, clase), nombre
            assert main_window.current_frame.winfo_exists(), nombre

    def test_arboles_de_datos_por_modulo(self, main_window):
        """Cada marco de tabla expone su Treeview y lo construye sin errores"""
        casos = {
            "empleados": "tree",
            "documentos": "tree",
            "incidencias": "tree",
            "contratos": "tree",
            "nomina": "tree",
            "configuracion": "audit_tree",
            "estudiantes": "tree",
            "notas": "tree",
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
        """Los diálogos de Ayuda y Acerca se crean y se cierran limpiamente
        (se espera el cierre real: CTkToplevel destruye con after(50))."""
        main_window._on_ayuda()
        main_window.update()
        dialogs = _toplevels(main_window)
        assert len(dialogs) == 1
        assert "Ayuda" in dialogs[0].title()
        dialogs[0].destroy()
        main_window.update()
        time.sleep(0.1)

        main_window._on_acerca_de()
        main_window.update()
        dialogs = _toplevels(main_window)
        assert len(dialogs) == 1
        assert "Acerca" in dialogs[0].title()
        dialogs[0].destroy()
        main_window.update()
        time.sleep(0.1)

    def test_mostrar_modulo_invalido(self, main_window, monkeypatch):
        """Un módulo no declarado en el mapa de permisos se deniega (fail-closed)

        Regresión: antes `can_access_module` devolvía True para cualquier
        módulo desconocido, así que un módulo nuevo de la interfaz que no se
        registrara en el mapa de permisos quedaba accesible a todos los roles.
        """
        from src.gui import main_window as modulo_ventana

        avisos: list[str] = []
        monkeypatch.setattr(
            modulo_ventana.messagebox,
            "showwarning",
            lambda titulo, mensaje: avisos.append(mensaje),
        )
        anterior = main_window.current_frame
        main_window._show_frame("modulo_inexistente")
        main_window.update()
        assert main_window.current_frame is anterior
        assert avisos and "permisos" in avisos[0]

    def test_seleccion_fila_click(self, main_window):
        """El clic/doble clic selecciona la fila bajo el cursor (fallback de selección)"""
        from types import SimpleNamespace
        from src.gui.frames import _seleccionar_fila_click, _id_fila_seleccionada

        main_window._show_frame("empleados")
        arbol = main_window.current_frame.tree
        arbol.insert(
            "",
            "end",
            iid="fila_test",
            values=("123", "Ana", "Docente", "General", "Docente", "500"),
            tags=("999",),
        )
        arbol.identify_row = lambda y: "fila_test" if y > 0 else ""
        # Fila bajo el cursor: queda seleccionada
        assert _seleccionar_fila_click(arbol, SimpleNamespace(y=5)) is True
        assert arbol.selection() == ("fila_test",)
        assert _id_fila_seleccionada(arbol) == 999
        # Sin fila bajo el cursor: la selección no cambia
        arbol.selection_remove("fila_test")
        assert _seleccionar_fila_click(arbol, SimpleNamespace(y=0)) is False
        assert not arbol.selection()

    def test_manual_auditoria_abre_dialogo(self, main_window):
        """El botón Manual de la sección de auditoría abre la guía"""
        main_window._show_frame("configuracion")
        frame = main_window.current_frame
        frame._on_manual_auditoria()
        main_window.update()
        dialogs = _toplevels(main_window)
        assert len(dialogs) == 1
        assert "Manual de Auditoría" in dialogs[0].title()
        dialogs[0].destroy()


class TestModuloAcademico:
    """Los módulos académicos construyen y muestran los datos sembrados"""

    @pytest.fixture()
    def datos_academicos(self, session):
        """Un año escolar con un grado, un estudiante matriculado y una nota"""
        from src.services import AcademicoService, NotaService

        academico = AcademicoService(session)
        periodo = academico.crear_periodo(
            {
                "nombre": "2025-2026",
                "fecha_inicio": "01/09/2025",
                "fecha_fin": "30/06/2026",
            }
        )
        grado = academico.crear_grado(
            {
                "periodo_id": int(periodo.id),
                "nivel": "secundaria",
                "nombre": "1er Año",
                "seccion": "A",
            }
        )
        estudiante = academico.crear_estudiante(
            {
                "nombres": "Ana",
                "apellidos": "Pérez",
                "cedula": "12345678",
                "nivel": "secundaria",
            }
        )
        academico.matricular(int(estudiante.id), int(grado.id))
        return {
            "academico": academico,
            "notas": NotaService(session),
            "periodo": periodo,
            "grado": grado,
            "estudiante": estudiante,
        }

    def test_estudiantes_frame_muestra_legajo_y_matriculas(
        self, datos_academicos, main_window
    ):
        main_window._show_frame("estudiantes")
        main_window.update()
        frame = main_window.current_frame

        filas = frame.tree.get_children()
        assert len(filas) == 1
        valores = frame.tree.item(filas[0], "values")
        assert valores[0] == "12345678"
        assert "Ana" in valores[1]
        assert valores[2] == "Secundaria"

        grados = frame.grados_tree.get_children()
        assert len(grados) == 1
        assert frame.grados_tree.item(grados[0], "values")[0] == "1er Año A"
        frame._load_matriculas(int(grados[0]))
        assert len(frame.matriculas_tree.get_children()) == 1

    def test_notas_frame_registra_y_muestra_calificaciones(
        self, datos_academicos, main_window
    ):
        main_window._show_frame("notas")
        main_window.update()
        frame = main_window.current_frame

        # El token académico se emite al abrir el módulo con la sesión activa
        assert frame.token
        grado = frame._grado_seleccionado()
        assert grado is not None
        assert frame._puede_escribir(grado)  # la administración escribe siempre
        # La escala se lee de la configuración sembrada (0 a 20, aprobatoria 10)
        assert frame._escala == (0.0, 20.0)
        assert frame._nota_aprobatoria == 10.0

        datos = datos_academicos
        datos["notas"].registrar(
            {
                "grado_id": int(grado.id),
                "estudiante_id": int(datos["estudiante"].id),
                "materia": "Matemática",
                "calificacion": 15,
            },
            frame.token,
        )
        frame._on_grado_cambio()
        notas = frame.tree.get_children()
        assert len(notas) == 1
        valores = frame.tree.item(notas[0], "values")
        assert valores[2] == "Matemática"
        assert valores[3] == "15"
        assert valores[4] == "Aprobada"

    def test_notas_frame_lista_periodos(self, datos_academicos, main_window):
        main_window._show_frame("notas")
        main_window.update()
        frame = main_window.current_frame

        periodos = frame.periodos_tree.get_children()
        assert len(periodos) == 1
        valores = frame.periodos_tree.item(periodos[0], "values")
        assert valores[0] == "2025-2026"
        assert valores[3] == "Abierto"


class TestTemaYCombobox:
    """Regresiones de tema visual y selectores"""

    def test_combobox_popdown_funciona_con_tema(self):
        """El tema no debe romper el desplegable de los combobox

        Regresión: la opción *TCombobox*Listbox.font con una familia de
        nombre compuesto ("Segoe UI") hacía fallar la creación del
        desplegable con 'expected integer but got UI'.
        """
        import tkinter as tk
        from tkinter import ttk
        from src.gui.theme import configure_ttk_styles

        root = tk.Tk()
        root.withdraw()
        try:
            configure_ttk_styles(root)
            combo = ttk.Combobox(root, values=["a", "b"], state="readonly")
            combo.pack()
            combo.set("a")
            root.update()
            # Crear el popdown igual que Tk al primer clic: no debe fallar
            pop = root.tk.call("ttk::combobox::PopdownWindow", combo._w)
            assert root.tk.call("winfo", "exists", pop) == 1
            combo.destroy()
        finally:
            root.destroy()

    def test_orden_por_encabezado(self, main_window):
        """El clic en un encabezado ordena la lista (ascendente/descendente)"""
        from src.gui.frames import _ordenar_por_columna, _habilitar_orden_columnas

        main_window._show_frame("empleados")
        arbol = main_window.current_frame.tree
        arbol.insert("", "end", iid="f2", values=("2", "Beta", "", "", "", ""), tags=("2",))
        arbol.insert("", "end", iid="f1", values=("1", "Alfa", "", "", "", ""), tags=("1",))
        _habilitar_orden_columnas(arbol)
        # Orden ascendente por cédula
        _ordenar_por_columna(arbol, "cedula")
        assert arbol.get_children("") == ("f1", "f2")
        assert "▲" in arbol.heading("cedula", "text")
        # Segundo clic: descendente
        _ordenar_por_columna(arbol, "cedula")
        assert arbol.get_children("") == ("f2", "f1")
        assert "▼" in arbol.heading("cedula", "text")


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

    def test_dialogo_cambio_password_valida(self, session, admin_usuario, monkeypatch):
        """Contraseñas que no coinciden no guardan nada"""
        from src.gui import login_window
        from src.services.auth_service import AuthService

        avisos: list[tuple[str, str]] = []
        monkeypatch.setattr(
            login_window.messagebox,
            "showerror",
            lambda titulo, mensaje: avisos.append((titulo, mensaje)),
        )

        auth = AuthService(session)
        padre = ctk.CTkToplevel()
        try:
            dlg = login_window.CambiarPasswordDialog(padre, auth, admin_usuario)
            dlg.update()
            dlg.new_pass.insert(0, "NuevaClave123")
            dlg.confirm_pass.insert(0, "OtraClave456")
            dlg._on_save()
            assert dlg.cambiado is False
            assert dlg.winfo_exists()  # sigue abierto
            assert len(avisos) == 1
            assert "no coinciden" in avisos[0][1]
        finally:
            padre.destroy()
