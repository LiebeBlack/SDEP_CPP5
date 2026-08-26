#!/usr/bin/env python
"""
Script de prueba simple para verificar la instalación
"""

print("Iniciando prueba...")

try:
    import sys
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    # Agregar directorio raíz al path
    from pathlib import Path
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))
    print(f"Project root: {project_root}")
    
    # Probar importación de módulos básicos
    print("Importando módulos básicos...")
    import tkinter
    print("✓ tkinter importado")
    
    from sqlalchemy import create_engine
    print("✓ SQLAlchemy importado")
    
    from dotenv import load_dotenv
    print("✓ python-dotenv importado")
    
    # Probar importación de CustomTkinter
    try:
        import customtkinter as ctk
        print("✓ CustomTkinter importado")
    except ImportError as e:
        print(f"✗ Error importando CustomTkinter: {e}")
    
    # Probar importación de módulos del proyecto
    print("Importando módulos del proyecto...")
    from src.config import settings
    print(f"✓ Settings: {settings.app_name}")
    
    from src.config import db_config
    print("✓ Database config importado")
    
    # Probar inicialización de base de datos
    print("Inicializando base de datos...")
    db_config.init_db()
    print("✓ Base de datos inicializada")
    
    # Probar importación de modelos
    from src.models import Base, Empleado
    print("✓ Modelos importados")
    
    # Probar importación de servicios
    from src.services import EmpleadoService
    print("✓ Servicios importados")
    
    print("\n✅ Todas las pruebas exitosas!")
    print("El sistema parece estar correctamente configurado.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()