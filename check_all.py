"""Comprehensive project checker - syntax, imports, and basic runtime checks."""
import ast
import os
import sys
import importlib
import traceback

def check_syntax(filepath):
    """Check file for syntax errors."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return None
    except SyntaxError as e:
        return f"SYNTAX ERROR in {filepath}: line {e.lineno}: {e.msg}"

def check_imports(filepath):
    """Check file for import issues by parsing AST."""
    issues = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        importlib.import_module(alias.name)
                    except ImportError as e:
                        issues.append(f"  IMPORT ERROR line {node.lineno}: {alias.name} - {e}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        mod = importlib.import_module(node.module)
                        for alias in node.names:
                            if not hasattr(mod, alias.name):
                                # Try importing directly
                                try:
                                    importlib.import_module(f"{node.module}.{alias.name}")
                                except ImportError:
                                    issues.append(f"  IMPORT ERROR line {node.lineno}: cannot import '{alias.name}' from '{node.module}'")
                    except ImportError as e:
                        issues.append(f"  IMPORT ERROR line {node.lineno}: {node.module} - {e}")
    except Exception as e:
        issues.append(f"  PARSE ERROR: {e}")
    return issues

def try_import_module(module_path):
    """Try to import a module and report errors."""
    try:
        mod = importlib.import_module(module_path)
        return None
    except Exception as e:
        return f"RUNTIME IMPORT ERROR for {module_path}: {type(e).__name__}: {e}"

def main():
    print("=" * 70)
    print("COMPREHENSIVE PROJECT CHECK")
    print("=" * 70)
    
    # Add project root to path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 1. Syntax check all .py files
    print("\n--- SYNTAX CHECK ---")
    syntax_errors = 0
    for root, dirs, files in os.walk('src'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if f.endswith('.py'):
                filepath = os.path.join(root, f)
                err = check_syntax(filepath)
                if err:
                    print(err)
                    syntax_errors += 1
    print(f"Syntax errors found: {syntax_errors}")
    
    # 2. Try importing each module
    print("\n--- MODULE IMPORT CHECK ---")
    import_errors = 0
    modules_to_check = [
        'src',
        'src.config',
        'src.config.settings',
        'src.config.database',
        'src.models',
        'src.models.base',
        'src.models.enums',
        'src.models.empleado',
        'src.models.pago',
        'src.models.incidencia',
        'src.models.documento',
        'src.models.configuracion',
        'src.utils',
        'src.utils.helpers',
        'src.utils.validators',
        'src.utils.security',
        'src.utils.audit_logger',
        'src.utils.backup_manager',
        'src.utils.document_manager',
        'src.utils.pdf_generator',
        'src.repositories',
        'src.repositories.base_repository',
        'src.repositories.empleado_repository',
        'src.repositories.pago_repository',
        'src.repositories.incidencia_repository',
        'src.repositories.documento_repository',
        'src.repositories.configuracion_repository',
        'src.services',
        'src.services.empleado_service',
        'src.services.pago_service',
        'src.services.incidencia_service',
        'src.services.documento_service',
        'src.services.configuracion_service',
    ]
    
    for mod in modules_to_check:
        err = try_import_module(mod)
        if err:
            print(err)
            import_errors += 1
        else:
            print(f"  OK: {mod}")
    
    print(f"\nImport errors found: {import_errors}")
    
    # 3. Check cross-references
    print("\n--- CROSS-REFERENCE CHECK ---")
    try:
        from src.models import Empleado, Pago, Incidencia, Documento, Configuracion
        print("  OK: All model classes importable from src.models")
    except Exception as e:
        print(f"  ERROR: Cannot import models: {e}")
    
    try:
        from src.repositories import (EmpleadoRepository, PagoRepository, 
                                       IncidenciaRepository, DocumentoRepository,
                                       ConfiguracionRepository)
        print("  OK: All repository classes importable from src.repositories")
    except Exception as e:
        print(f"  ERROR: Cannot import repositories: {e}")
    
    try:
        from src.services import (EmpleadoService, PagoService, 
                                   IncidenciaService, DocumentoService,
                                   ConfiguracionService)
        print("  OK: All service classes importable from src.services")
    except Exception as e:
        print(f"  ERROR: Cannot import services: {e}")
    
    print("\n" + "=" * 70)
    print("CHECK COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    main()
