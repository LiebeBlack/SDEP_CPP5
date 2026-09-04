# ⚡ Quick Start Guide - CI/CD con Instalador de Windows

Guía rápida del flujo CI/CD: pruebas, ejecutable, instalador y release
automáticos.

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
- **Output**: `Setup.exe` + ZIP portable
  - Push a **main** → Release automática en GitHub (sin etiqueta)
  - Push a **develop** → solo artefactos
  - Etiqueta `v*` → Release versionada con el nombre de la etiqueta
- **Duración**: ~5-7 minutos

## 🎯 Flujo de Trabajo

### Release automática por cada push (sin etiqueta)
```bash
# Cualquier push a main compila, instala y publica un Release automáticamente
git push origin main
```

**Resultado:**
- ✅ Pruebas automatizadas (79 pruebas)
- ✅ Ejecutable Windows (onedir, icono, versión)
- ✅ Instalador `Setup.exe` subido como artefacto
- ✅ ZIP portable subido como artefacto
- ✅ Release en GitHub con instalador adjunto (etiqueta interna automática)

### Release versionada (opcional)
```bash
# Crea una release con nombre y etiqueta versionados (ej: v1.0.4)
git tag v1.0.4
git push origin v1.0.4
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
1. Verifica que el push fue a `main` (o usa una etiqueta `v*`)
2. Verifica que el GITHUB_TOKEN tenga permisos de `contents: write`
3. Revisa los logs del workflow

## 📚 Documentación Adicional

- [.github/workflows/README.md](.github/workflows/README.md) - Documentación de workflows

---

**¡Listo!** El sistema CI/CD está configurado para compilar el software e
instalador final de Windows y publicar un Release por cada cambio enviado.