import os, sys, tempfile
_TMP = tempfile.mkdtemp(prefix="sgp_smoke2_")
os.environ["SGP_BASE_DIR"] = _TMP
os.environ["DATABASE_PATH"] = "smoke2.db"
os.environ["DEBUG"] = "False"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import db_config
from src.models import Usuario
db_config.init_db()
session = db_config.get_session()
admin = session.query(Usuario).filter(Usuario.username == "admin").first()

from src.gui.theme import aplicar_modo_apariencia
from src.services.configuracion_service import ConfiguracionService
# Persistir el tema claro como lo haría el botón de la interfaz
ConfiguracionService(session).establecer_valor("apariencia_modo", "Light")
aplicar_modo_apariencia("Light")

from src.gui.main_window import MainWindow
app = MainWindow(current_user=admin)
app.update()
from PIL import ImageGrab

def shot(name):
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(f"tools/{name}.png")

app._show_frame("configuracion")
shot("light_config")
app._show_frame("nomina")
shot("light_nomina")
app._on_ayuda()
app.update()
# Capturar incluyendo el diálogo
x, y = app.winfo_rootx(), app.winfo_rooty()
w, h = app.winfo_width(), app.winfo_height()
ImageGrab.grab(bbox=(x, y, x + w, y + h + 400)).save("tools/light_ayuda.png")
print("captures done")
app._cleanup()
app.destroy()
db_config.close_session(session)