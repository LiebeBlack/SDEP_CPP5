# ⚡ Quick Start Guide - CI/CD con Instalador de Windows

Guía rápida del flujo CI/CD: pruebas, ejecutable e instalador automáticos.

## 🚀 Configuración en 2 minutos

### 1. Configurar Branch Protection (Recomendado)

Ve a `Settings > Branches`:

**Main Branch:**
- ✅ Require pull request reviews
- ✅ Require status checks: "Pruebas (pytest)"
- ✅ Require branches to be up to date

## 📋 Workflow

### Build & Release (`build.yml`)
- **Trigger**: Push a main/develop, etiquetas `v*`, manual
- **Función**: Pruebas (pytest) + ejecutable Windows + instalador (Inno Setup)
- **Output**: `Setup.exe` + ZIP portable (artefactos, y Release en etiquetas `v*`)
- **Duración**: ~5-7 minutos

## 🎯 Flujo de Trabajo

### Compilación automática (sin release)
```bash
# Cualquier push a main/develop compila y sube el instalador como artefacto
git push origin main
```

**Resultado:**
- ✅ Pruebas automatizadas (58 pruebas)
- ✅ Ejecutable Windows (onedir, icono, versión)
- ✅ Instalador `Setup.exe` subido como artefacto
- ✅ ZIP portable subido como artefacto

### Release final con instalador
```bash
# Crea el release en GitHub con el instalador Setup.exe y el ZIP portable
git tag v1.0.3
git push origin v1.0.3
```

**Resultado:**
- ✅ Release en GitHub con el instalador adjunto
- ✅ Instalador con instalación en `Program Files`
- ✅ Datos del usuario en `%LOCALAPPDATA%\SistemaGestionPersonal`

## 🔧 Solución de Problemas

### Build falla
1. Verifica que `src/main.py` exista
2. Verifica que las dependencias estén en `requirements.txt`
3. Prueba PyInstaller localmente: `python build.py --exe`

### Instalador falla
1. Verifica que el ejecutable se generó en `dist\SistemaGestionPersonal`
2. Revisa que `installer/setup.iss` apunte a la carpeta correcta
3. Verifica que `LICENSE` y `assets\app.ico` existan

### Release no se publica
1. Asegúrate de usar una etiqueta `v*` (ej: `v1.0.3`)
2. Verifica que el GITHUB_TOKEN tenga permisos de `contents: write`
3. Revisa los logs del workflow

## 📚 Documentación Adicional

- [.github/workflows/README.md](.github/workflows/README.md) - Documentación de workflows

---

**¡Listo!** El sistema CI/CD está configurado para compilar el software e
instalador final de Windows automáticamente.