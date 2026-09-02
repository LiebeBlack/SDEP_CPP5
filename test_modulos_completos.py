"""
Script de prueba completo para verificar funcionalidad de todos los módulos
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
print("PRUEBA COMPLETA DE MODULOS")
print("=" * 70)

# 1. Probar configuracion y base de datos
print("\n--- PRUEBA 1: Configuracion y Base de Datos ---")
try:
    from src.config import settings, db_config
    print("[OK] Configuracion importada correctamente")
    print(f"   - Base de datos: {settings.database_path}")
    print(f"   - Directorio documentos: {settings.documents_path}")
    
    # Inicializar base de datos
    db_config.init_db()
    print("[OK] Base de datos inicializada correctamente")
    
    # Obtener sesión
    session = db_config.get_session()
    print("[OK] Sesion de base de datos obtenida")
    
except Exception as e:
    print(f"[ERROR] Error en configuracion/base de datos: {e}")
    sys.exit(1)

# 2. Probar modelos
print("\n--- PRUEBA 2: Modelos ---")
try:
    from src.models import (
        Empleado, Documento, Incidencia, Pago, Configuracion,
        TipoEmpleado, TipoDocumento, TipoIncidencia, EstadoIncidencia,
        TipoPago, MetodoPago
    )
    print("[OK] Todos los modelos importados correctamente")
    print(f"   - Modelos: Empleado, Documento, Incidencia, Pago, Configuracion")
    print(f"   - Enums: TipoEmpleado, TipoDocumento, TipoIncidencia, etc.")
except Exception as e:
    print(f"[ERROR] Error en modelos: {e}")
    sys.exit(1)

# 3. Probar repositorios
print("\n--- PRUEBA 3: Repositorios ---")
try:
    from src.repositories import (
        EmpleadoRepository, DocumentoRepository, IncidenciaRepository,
        PagoRepository, ConfiguracionRepository
    )
    print("[OK] Todos los repositorios importados correctamente")
    
    # Probar repositorio de empleados
    emp_repo = EmpleadoRepository(session)
    print("[OK] EmpleadoRepository instanciado correctamente")
    
    # Probar repositorio de configuración
    config_repo = ConfiguracionRepository(session)
    configs = config_repo.get_all()
    print(f"[OK] ConfiguracionRepository funcionando ({len(configs)} configuraciones)")
    
except Exception as e:
    print(f"[ERROR] Error en repositorios: {e}")
    session.close()
    sys.exit(1)

# 4. Probar servicios
print("\n--- PRUEBA 4: Servicios ---")
try:
    from src.services import (
        EmpleadoService, DocumentoService, IncidenciaService,
        PagoService, ConfiguracionService
    )
    print("[OK] Todos los servicios importados correctamente")
    
    # Probar servicio de empleados
    emp_service = EmpleadoService(session)
    stats = emp_service.obtener_estadisticas()
    print(f"[OK] EmpleadoService funcionando")
    print(f"   - Total empleados: {stats.get('total', 0)}")
    print(f"   - Empleados activos: {stats.get('activos', 0)}")
    
    # Probar servicio de configuración
    config_service = ConfiguracionService(session)
    config_general = config_service.obtener_configuracion_general()
    print(f"[OK] ConfiguracionService funcionando")
    print(f"   - Nombre institucion: {config_general.get('nombre_institucion', 'N/A')}")
    
except Exception as e:
    print(f"[ERROR] Error en servicios: {e}")
    import traceback
    traceback.print_exc()
    session.close()
    sys.exit(1)

# 5. Probar utilidades
print("\n--- PRUEBA 5: Utilidades ---")
try:
    from src.utils.helpers import format_date, format_currency, calculate_age
    from src.utils.validators import EmpleadoValidator, DocumentoValidator
    from src.utils.pdf_generator import PDFGenerator
    
    print("[OK] Utilidades importadas correctamente")
    
    # Probar formateo
    from datetime import date
    test_date = date(2024, 1, 15)
    formatted = format_date(test_date)
    print(f"[OK] Formateo de fecha funcionando: {formatted}")
    
    # Probar validacion
    test_datos = {
        "nombres": "Juan",
        "apellidos": "Perez",
        "cedula": "1234567890",
        "tipo_empleado": TipoEmpleado.DOCENTE,
        "cargo": "Profesor",
        "departamento": "Matematicas",
        "salario_base": 1000.0
    }
    errores = EmpleadoValidator.validate_datos_empleado(test_datos)
    if not errores:
        print("[OK] Validacion de empleado funcionando correctamente")
    else:
        print(f"[WARNING] Validacion encontro errores: {errores}")
    
except Exception as e:
    print(f"[ERROR] Error en utilidades: {e}")
    import traceback
    traceback.print_exc()
    session.close()
    sys.exit(1)

# 6. Probar GUI frames
print("\n--- PRUEBA 6: GUI Frames ---")
try:
    from src.gui.frames import (
        DashboardFrame, EmpleadosFrame, DocumentosFrame,
        IncidenciasFrame, NominaFrame, ConfiguracionFrame
    )
    print("[OK] Todos los frames de GUI importados correctamente")
    print("   - DashboardFrame, EmpleadosFrame, DocumentosFrame")
    print("   - IncidenciasFrame, NominaFrame, ConfiguracionFrame")
except Exception as e:
    print(f"[ERROR] Error en GUI frames: {e}")
    import traceback
    traceback.print_exc()
    session.close()
    sys.exit(1)

# 7. Probar creación de empleado (prueba funcional real)
print("\n--- PRUEBA 7: Creación de Empleado (Funcional) ---")
try:
    test_empleado_datos = {
        "nombres": "Carlos",
        "apellidos": "Rodriguez",
        "cedula": "4443332221",
        "tipo_empleado": TipoEmpleado.DOCENTE,
        "cargo": "Profesor de Prueba",
        "departamento": "Testing",
        "salario_base": 1200.0,
        "fecha_contratacion": date.today()
    }
    
    nuevo_empleado = emp_service.crear_empleado(test_empleado_datos)
    print(f"[OK] Empleado de prueba creado correctamente")
    print(f"   - ID: {nuevo_empleado.id}")
    print(f"   - Nombre: {nuevo_empleado.nombre_completo}")
    print(f"   - Cedula: {nuevo_empleado.cedula}")
    
    # Eliminar empleado de prueba
    emp_service.eliminar_empleado(nuevo_empleado.id)
    print("[OK] Empleado de prueba eliminado correctamente")
    
except Exception as e:
    print(f"[ERROR] Error en prueba funcional de empleado: {e}")
    import traceback
    traceback.print_exc()
    session.close()
    sys.exit(1)

# Cerrar sesion
session.close()
print("\n[OK] Sesion de base de datos cerrada")

print("\n" + "=" * 70)
print("[OK] TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
print("=" * 70)
print("\nEl sistema esta funcionando correctamente:")
print("- [OK] Configuracion y base de datos")
print("- [OK] Modelos de datos")
print("- [OK] Repositorios")
print("- [OK] Servicios de negocio")
print("- [OK] Utilidades y validaciones")
print("- [OK] Frames de GUI")
print("- [OK] Funcionalidad CRUD")
