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

### Integración y empaquetado (`build.yml`)
- **Disparadores**: push a `main` o `develop`, etiquetas `v*` y ejecución manual
- **Función**: pruebas con pytest + ejecutable Windows + actualizador automático + instalador (Inno Setup)
  + ejecutable Linux portable (PyInstaller dentro de Debian 13)
- **Salidas (artefactos del run)**: `Setup.exe` (incluye el actualizador automático) + ZIP portable (Windows) + `tar.gz` portable (Linux) + reporte de cobertura
- **Compatibilidad**: el ejecutable Linux se compila en Debian 13
  (glibc 2.41) y funciona en Debian 13 y Ubuntu 24.04 LTS o superior
  (autoverificado en CI con `--selftest` dentro de contenedores
  `debian:13-slim`, con comprobación de la glibc requerida)
- **No publica releases**: solo compila y verifica
- **Duración**: ~5-9 minutos (Windows y Linux compilan en paralelo)

### Release firmada (`release.yml`)
- **Disparadores**: push a `main`, etiquetas `v*` y ejecución manual
- **Función**: compila, firma en dos pasadas (todo el contenido de `dist/`
  y después el instalador final), audita que ningún archivo firmable quede
  sin firma y publica la Release
- **Adjunto publicado**: únicamente el instalador
  `SistemaGestionPersonal-Setup-<versión>.exe`
- **Secretos requeridos**: `PFX_BASE64` y `PFX_PASSWORD`

## 🎯 Flujo de Trabajo

### Release continua firmada por cada push (sin etiqueta)
```bash
# Cualquier push a main compila, firma y publica una Release continua
git push origin main
```

**Resultado:**
- ✅ Pruebas automatizadas (453 funciones de prueba)
- ✅ Ejecutable Windows (onedir, icono, versión)
- ✅ Instalador `Setup.exe` firmado y adjunto a la Release
- ✅ ZIP portable (Windows) y `tar.gz` (Linux) como artefactos del run
- ✅ Release con etiqueta interna `continuous-v<versión>.<número de ejecución>`

### Release versionada (opcional)
```bash
# Crea una release con nombre y etiqueta versionados (ej: v2.82)
git tag v2.82
git push origin v2.82
```

**Resultado:**
- ✅ Release en GitHub con el instalador firmado adjunto
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
1. Verifica que el push fue a `main` (o usa una etiqueta `v*`): las releases
   las publica `release.yml`, no `build.yml`
2. Verifica que el GITHUB_TOKEN tenga permisos de `contents: write`
3. Verifica que los secretos `PFX_BASE64` y `PFX_PASSWORD` existan y que el
   certificado sea válido: sin firma, la auditoría final aborta la publicación
4. Revisa los logs del workflow

## 📚 Documentación Adicional

- [.github/workflows/README.md](.github/workflows/README.md) - Documentación de workflows

---

**¡Listo!** El sistema CI/CD está configurado para compilar el software y el
instalador final de Windows, y para publicar una Release firmada por cada
cambio enviado a `main`.