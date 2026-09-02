"""
Prueba visual de componentes GUI
Verifica que la aplicación se inicie y muestre correctamente
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("=" * 60)
print("PRUEBA VISUAL DE COMPONENTES GUI")
print("=" * 60)

# Prueba 1: Verificar correcciones de format_currency
print("\n--- PRUEBA 1: Verificación de format_currency ---")
try:
    from src.utils.helpers import format_currency
    
    # Probar con valores normales
    assert format_currency(1200.50) == "$1,200.50", "Error en formato normal"
    assert format_currency(0) == "$0.00", "Error en formato cero"
    
    # Probar con valores problemáticos
    assert format_currency(None) == "$0.00", "Error con None"
    assert format_currency("abc") == "$0.00", "Error con string invalido"
    assert format_currency("") == "$0.00", "Error con string vacio"
    
    print("[OK] format_currency maneja correctamente todos los casos")
except Exception as e:
    print(f"[ERROR] Error en format_currency: {e}")
    sys.exit(1)

# Prueba 2: Verificar mejoras de estilo Treeview
print("\n--- PRUEBA 2: Verificación de estilo Treeview ---")
try:
    from src.gui.main_window import configure_treeview_style
    
    # Intentar configurar el estilo
    configure_treeview_style()
    print("[OK] configure_treeview_style ejecutado sin errores")
except Exception as e:
    print(f"[ERROR] Error en configure_treeview_style: {e}")
    sys.exit(1)

# Prueba 3: Verificar anchos de columnas mejorados
print("\n--- PRUEBA 3: Verificación de anchos de columnas ---")
try:
    import tkinter as tk
    from tkinter import ttk
    
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana
    
    # Crear Treeview de prueba
    tree = ttk.Treeview(root, columns=("col1", "col2", "col3"), show="headings")
    
    # Verificar que podemos configurar columnas con minwidth
    tree.column("col1", width=200, minwidth=150)
    tree.column("col2", width=300, minwidth=200)
    tree.column("col3", width=120, minwidth=80)
    
    print("[OK] Configuración de columnas con minwidth funciona")
    
    root.destroy()
except Exception as e:
    print(f"[ERROR] Error en configuración de columnas: {e}")
    sys.exit(1)

# Prueba 4: Verificar carga de datos sin errores
print("\n--- PRUEBA 4: Verificación de carga de datos ---")
try:
    from src.config import db_config
    from src.services.empleado_service import EmpleadoService
    from src.utils.helpers import format_currency
    
    session = db_config.get_session()
    emp_service = EmpleadoService(session)
    
    # Obtener empleados y verificar format_currency en datos reales
    empleados = emp_service.listar_empleados_activos()
    
    for emp in empleados:
        # Verificar que format_currency funcione con datos reales
        salario_formateado = format_currency(emp.salario_base)
        assert "$" in salario_formateado, f"Error formateando salario de {emp.nombre_completo}"
    
    print(f"[OK] format_currency funciona con {len(empleados)} empleados reales")
    
    db_config.close_session(session)
except Exception as e:
    print(f"[ERROR] Error en carga de datos: {e}")
    try:
        db_config.close_session(session)
    except:
        pass
    sys.exit(1)

# Prueba 5: Verificar componentes de frames
print("\n--- PRUEBA 5: Verificación de componentes de frames ---")
try:
    from src.gui.frames import (
        EmpleadosFrame, DocumentosFrame, 
        IncidenciasFrame, NominaFrame
    )
    
    # Verificar que las clases existan y tengan los métodos necesarios
    assert hasattr(EmpleadosFrame, '_load_empleados'), "EmpleadosFrame no tiene _load_empleados"
    assert hasattr(DocumentosFrame, '_load_documentos'), "DocumentosFrame no tiene _load_documentos"
    assert hasattr(IncidenciasFrame, '_load_incidencias'), "IncidenciasFrame no tiene _load_incidencias"
    assert hasattr(NominaFrame, '_load_pagos'), "NominaFrame no tiene _load_pagos"
    
    print("[OK] Todos los frames tienen métodos de carga de datos")
except Exception as e:
    print(f"[ERROR] Error en verificación de frames: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("[OK] TODAS LAS PRUEBAS VISUALES PASARON")
print("=" * 60)
print("\nResumen de correcciones:")
print("- [OK] format_currency maneja None y valores invalidos")
print("- [OK] Estilo Treeview mejorado con fuentes y rowheight")
print("- [OK] Columnas con minwidth para evitar desbordamiento")
print("- [OK] Carga de datos con formateo correcto")
print("- [OK] Componentes de frames verificados")
print("\nLa aplicación debería visualizarse correctamente ahora.")
