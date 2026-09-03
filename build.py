"""
Build Script
Script de construcción para empaquetar la aplicación
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Instala las dependencias del proyecto"""
    print("Instalando dependencias...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print("Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al instalar dependencias: {e}")
        return False

def build_exe():
    """Construye el ejecutable con PyInstaller"""
    print("Construyendo ejecutable...")
    try:
        # Always use direct PyInstaller command for reliability
        print("Usando comando directo de PyInstaller")
        pyinstaller_args = [
            sys.executable, "-m", "PyInstaller",
            "--name=SistemaGestionPersonal",
            "--onefile",
            "--windowed",
            "--add-data=src;src",
            "--hidden-import=customtkinter",
            "--hidden-import=PIL",
            "--hidden-import=reportlab",
            "--hidden-import=SQLAlchemy",
            "--hidden-import=python_dotenv",
            "--clean",
            "src/main.py"
        ]
        subprocess.run(pyinstaller_args, check=True)
        
        print("Ejecutable construido correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al construir ejecutable: {e}")
        return False

def create_installer():
    """Crea un instalador básico (opcional)"""
    print("Omitiendo creación de instalador (requiere NSIS o Inno Setup)")
    return True

def main():
    """Función principal"""
    print("=" * 50)
    print("PROCESO DE CONSTRUCCIÓN")
    print("=" * 50)
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Instalar dependencias
    if not install_dependencies():
        sys.exit(1)
    
    # Construir ejecutable
    if not build_exe():
        sys.exit(1)
    
    # Crear instalador (opcional)
    if not create_installer():
        sys.exit(1)
    
    print("=" * 50)
    print("CONSTRUCCIÓN COMPLETADA")
    print("=" * 50)
    print(f"Ejecutable ubicado en: {project_dir / 'dist' / 'SistemaGestionPersonal'}")

if __name__ == "__main__":
    main()