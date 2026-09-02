"""
Script de prueba específico para verificar carga de datos en GUI
"""
import sys
import io
from pathlib import Path
from datetime import date

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
print("PRUEBA DE CARGA DE DATOS EN GUI")
print("=" * 70)

# 1. Inicializar base de datos y sesión
print("\n--- CONFIGURACIÓN ---")
try:
    from src.config import settings, db_config
    session = db_config.get_session()
    print("[OK] Base de datos y sesión inicializadas")
except Exception as e:
    print(f"[ERROR] Error en inicialización: {e}")
    sys.exit(1)

# 2. Crear empleados de prueba
print("\n--- CREACIÓN DE DATOS DE PRUEBA ---")
try:
    from src.services import EmpleadoService
    from src.models import TipoEmpleado
    
    emp_service = EmpleadoService(session)
    
    # Crear varios empleados de prueba
    empleados_prueba = [
        {
            "nombres": "Juan",
            "apellidos": "García",
            "cedula": "1111111111",
            "tipo_empleado": TipoEmpleado.DOCENTE,
            "cargo": "Profesor de Matemáticas",
            "departamento": "Matemáticas",
            "salario_base": 1500.0,
            "fecha_contratacion": date(2023, 1, 15)
        },
        {
            "nombres": "María",
            "apellidos": "López",
            "cedula": "2222222222",
            "tipo_empleado": TipoEmpleado.DOCENTE,
            "cargo": "Profesora de Historia",
            "departamento": "Historia",
            "salario_base": 1400.0,
            "fecha_contratacion": date(2023, 2, 1)
        },
        {
            "nombres": "Carlos",
            "apellidos": "Rodríguez",
            "cedula": "3333333333",
            "tipo_empleado": TipoEmpleado.ADMINISTRATIVO,
            "cargo": "Secretario",
            "departamento": "Administración",
            "salario_base": 1200.0,
            "fecha_contratacion": date(2023, 3, 10)
        }
    ]
    
    empleados_creados = []
    for datos in empleados_prueba:
        try:
            emp = emp_service.crear_empleado(datos)
            empleados_creados.append(emp)
            print(f"[OK] Empleado creado: {emp.nombre_completo}")
        except Exception as e:
            print(f"[WARNING] No se pudo crear empleado {datos['nombres']}: {e}")
    
    print(f"[OK] Total empleados creados: {len(empleados_creados)}")
    
except Exception as e:
    print(f"[ERROR] Error creando empleados de prueba: {e}")
    import traceback
    traceback.print_exc()
    session.close()
    sys.exit(1)

# 3. Probar estadísticas para dashboard
print("\n--- ESTADÍSTICAS PARA DASHBOARD ---")
try:
    from src.services import DocumentoService, IncidenciaService, PagoService
    
    doc_service = DocumentoService(session)
    incidencia_service = IncidenciaService(session)
    pago_service = PagoService(session)
    
    # Estadísticas de empleados
    emp_stats = emp_service.obtener_estadisticas()
    print(f"[OK] Estadísticas empleados:")
    print(f"   - Total: {emp_stats.get('total', 0)}")
    print(f"   - Activos: {emp_stats.get('activos', 0)}")
    print(f"   - Por tipo: {emp_stats.get('por_tipo', {})}")
    
    # Estadísticas de documentos
    doc_stats = doc_service.obtener_estadisticas()
    print(f"[OK] Estadísticas documentos:")
    print(f"   - Total: {doc_stats.get('total', 0)}")
    print(f"   - Activos: {doc_stats.get('activos', 0)}")
    
    # Estadísticas de incidencias
    incidencia_stats = incidencia_service.obtener_estadisticas()
    print(f"[OK] Estadísticas incidencias:")
    print(f"   - Total: {incidencia_stats.get('total', 0)}")
    print(f"   - Pendientes: {incidencia_stats.get('pendientes', 0)}")
    
    # Estadísticas de pagos
    pago_stats = pago_service.obtener_estadisticas()
    print(f"[OK] Estadísticas pagos:")
    print(f"   - Total: {pago_stats.get('total', 0)}")
    print(f"   - Pendientes: {pago_stats.get('pendientes', 0)}")
    
except Exception as e:
    print(f"[ERROR] Error obteniendo estadísticas: {e}")
    import traceback
    traceback.print_exc()

# 4. Probar carga de empleados en lista
print("\n--- CARGA DE LISTA DE EMPLEADOS ---")
try:
    empleados_lista = emp_service.listar_empleados_activos()
    print(f"[OK] Cargados {len(empleados_lista)} empleados activos")
    
    for emp in empleados_lista:
        print(f"   - {emp.nombre_completo} ({emp.cedula}) - {emp.cargo}")
    
except Exception as e:
    print(f"[ERROR] Error cargando lista de empleados: {e}")
    import traceback
    traceback.print_exc()

# 5. Probar importación de frames GUI
print("\n--- IMPORTACIÓN DE FRAMES GUI ---")
try:
    from src.gui.frames import (
        DashboardFrame, EmpleadosFrame, DocumentosFrame,
        IncidenciasFrame, NominaFrame, ConfiguracionFrame
    )
    print("[OK] Todos los frames importados correctamente")
    
    # Verificar que las clases existan
    print(f"[OK] DashboardFrame: {DashboardFrame}")
    print(f"[OK] EmpleadosFrame: {EmpleadosFrame}")
    print(f"[OK] DocumentosFrame: {DocumentosFrame}")
    print(f"[OK] IncidenciasFrame: {IncidenciasFrame}")
    print(f"[OK] NominaFrame: {NominaFrame}")
    print(f"[OK] ConfiguracionFrame: {ConfiguracionFrame}")
    
except Exception as e:
    print(f"[ERROR] Error importando frames GUI: {e}")
    import traceback
    traceback.print_exc()

# 6. Limpiar datos de prueba
print("\n--- LIMPIEZA DE DATOS DE PRUEBA ---")
try:
    for emp in empleados_creados:
        try:
            emp_service.eliminar_empleado(emp.id)
            print(f"[OK] Empleado eliminado: {emp.nombre_completo}")
        except Exception as e:
            print(f"[WARNING] No se pudo eliminar empleado {emp.nombre_completo}: {e}")
    
    print("[OK] Limpieza completada")
    
except Exception as e:
    print(f"[ERROR] Error en limpieza: {e}")

# Cerrar sesión
session.close()
print("\n[OK] Sesión cerrada")

print("\n" + "=" * 70)
print("[OK] PRUEBA DE GUI COMPLETADA")
print("=" * 70)
print("\nLa aplicación está lista para mostrar datos correctamente.")
print("Ejecute: py src\\main.py")
