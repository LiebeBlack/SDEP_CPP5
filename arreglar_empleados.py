"""
Script para arreglar empleados existentes y activarlos
"""
import sys
import io
from pathlib import Path

# Configurar UTF-8 para Windows
if sys.stdout is not None and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr is not None and hasattr(sys.stderr, 'buffer') and sys.stderr.buffer is not None:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Asegurar que el directorio raíz esté en sys.path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("=" * 70)
print("ARREGLAR EMPLEADOS EXISTENTES")
print("=" * 70)

# Inicializar base de datos
from src.config import db_config
session = db_config.get_session()

print("\n--- REVISAR EMPLEADOS EXISTENTES ---")
from src.models import Empleado
from src.repositories import EmpleadoRepository

emp_repo = EmpleadoRepository(session)
todos_empleados = emp_repo.get_all()

print(f"Total empleados en base de datos: {len(todos_empleados)}")

for emp in todos_empleados:
    print(f"ID: {emp.id}, Nombre: {emp.nombre_completo}, Cédula: {emp.cedula}, Activo: {emp.activo}")
    
    # Activar empleados inactivos
    if emp.activo != 1:
        print(f"  -> Activando empleado {emp.nombre_completo}")
        emp.activo = 1
        session.commit()
        print(f"  -> Empleado activado")

print("\n--- VERIFICAR EMPLEADOS ACTIVOS ---")
activos = emp_repo.get_activos()
print(f"Empleados activos: {len(activos)}")
for emp in activos:
    print(f"  - {emp.nombre_completo} ({emp.cedula})")

# Cerrar sesión
session.close()
print("\n[OK] Proceso completado")
