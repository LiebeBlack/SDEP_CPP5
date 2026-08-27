#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba simple para verificar la instalación
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
    print("[OK] tkinter importado")
    
    from sqlalchemy import create_engine
    print("[OK] SQLAlchemy importado")
    
    from dotenv import load_dotenv
    print("[OK] python-dotenv importado")
    
    # Probar importación de CustomTkinter
    try:
        import customtkinter as ctk
        print("[OK] CustomTkinter importado")
    except ImportError as e:
        print(f"[ERROR] Error importando CustomTkinter: {e}")
    
    # Probar importación de módulos del proyecto
    print("Importando módulos del proyecto...")
    from src.config import settings
    print(f"[OK] Settings: {settings.app_name}")
    
    from src.config import db_config
    print("[OK] Database config importado")
    
    # Probar inicialización de base de datos
    print("Inicializando base de datos...")
    db_config.init_db()
    print("[OK] Base de datos inicializada")
    
    # Probar importación de modelos
    from src.models import Base, Empleado
    print("[OK] Modelos importados")
    
    # Probar importación de servicios
    from src.services import EmpleadoService
    print("[OK] Servicios importados")
    
    print("\n[SUCCESS] Todas las pruebas exitosas!")
    print("El sistema parece estar correctamente configurado.")
    
except Exception as e:
    print(f"\n[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()