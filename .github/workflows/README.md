# 🚀 GitHub Actions Workflows

Sistema de CI/CD corregido y mejorado para el Sistema de Gestión de Personal.

## 📁 Workflows

| Workflow | Propósito | Trigger | Ejecutable en Release |
|----------|-----------|---------|----------------------|
| [build.yml](build.yml) | Construir ejecutable + Pre-releases | Push a main/develop, manual | ✅ Sí (develop) |
| [release.yml](release.yml) | Crear releases oficiales | Push a main, manual | ✅ Sí |

## ✅ Correcciones Realizadas

### Build Workflow
- ✅ **Permisos correctos**: `contents: write` para crear releases
- ✅ **Validación de archivos**: Verifica que `src/main.py` existe
- ✅ **Hidden imports**: Agregados todos los imports necesarios
- ✅ **Validación de ejecutable**: Verifica que se creó correctamente
- ✅ **Validación de ZIP**: Verifica que el ZIP se creó correctamente
- ✅ **Logs detallados**: Muestra tamaños de archivos para debugging
- ✅ **Bandera --clean**: Limpia builds anteriores

### Release Workflow
- ✅ **Permisos correctos**: `contents: write` para crear releases
- ✅ **Validación de archivos**: Verifica que `src/main.py` existe
- ✅ **Hidden imports**: Agregados todos los imports necesarios
- ✅ **Validación de ejecutable**: Verifica que se creó correctamente
- ✅ **Validación de ZIP**: Verifica que el ZIP se creó correctamente
- ✅ **Logs detallados**: Muestra tamaños de archivos para debugging
- ✅ **Versionado automático**: Usa run_number para versiones automáticas

## 🎯 Uso Simple

### 1. Desarrollo - Pre-releases Automáticas
```bash
# Push a develop - crea pre-release automáticamente con ejecutable
git push origin develop
# → Pre-release: dev-1, dev-2, dev-3...
# → Incluye ejecutable Windows en ZIP
```

### 2. Main Branch - Releases Automáticos
```bash
# Push a main - crea release automáticamente con ejecutable
git push origin main
# → Release: 1.0.0-1, 1.0.0-2, 1.0.0-3...
# → Incluye ejecutable Windows en ZIP
```

### 3. Release Oficial (Manual)
```bash
# Manual trigger desde GitHub Actions UI
# Ingresar versión: ej: 1.0.0
# → Release oficial con versión específica
# → Incluye ejecutable Windows en ZIP
```

## ✅ Características Mejoradas

- **Ejecutables garantizados**: Validación en cada paso
- **Hidden imports completos**: customtkinter, PIL, reportlab, SQLAlchemy, pydantic, etc.
- **Debugging mejorado**: Logs detallados con tamaños de archivos
- **Pre-releases automáticos**: Cada push a develop crea release
- **Releases automáticos**: Cada push a main crea release
- **Permisos correctos**: `contents: write` para crear releases
- **Limpieza de builds**: Bandera `--clean` en PyInstaller

## 📝 Notas

- **Develop branch**: Crea pre-releases automáticas (dev-X) con ejecutable
- **Main branch**: Crea releases automáticos (1.0.0-X) con ejecutable
- **Todos los releases incluyen**: Ejecutable Windows comprimido en ZIP
- **Validación completa**: Cada paso verifica que el archivo se creó correctamente
- **Logs detallados**: Muestra tamaños de archivos para facilitar debugging