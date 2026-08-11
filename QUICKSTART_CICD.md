# ⚡ Quick Start Guide - CI/CD Simplificado

Guía rápida para el sistema CI/CD simplificado del proyecto.

## 🚀 Configuración en 2 minutos

### 1. Configurar GitHub Secrets (Opcional)

Ve a `Settings > Secrets and variables > Actions`:

**Solo si quieres notificaciones:**
- `SLACK_WEBHOOK_URL` - Slack webhook (opcional)
- `SMTP_SERVER` - Servidor SMTP (opcional)
- `SMTP_USERNAME` - Usuario SMTP (opcional)
- `SMTP_PASSWORD` - Contraseña SMTP (opcional)

### 2. Configurar Branch Protection (Recomendado)

Ve a `Settings > Branches`:

**Main Branch:**
- ✅ Require pull request reviews
- ✅ Require status checks: "CI"
- ✅ Require branches to be up to date

## 📋 Workflows Simplificados

### CI Workflow (`ci.yml`)
- **Trigger**: Push a main/develop, Pull Requests
- **Función**: Ejecuta tests básicos (si existen)
- **Duración**: ~2-3 minutos

### Build Workflow (`build.yml`)
- **Trigger**: Push a main/develop, Manual
- **Función**: Construye ejecutable Windows
- **Output**: Archivo ZIP con ejecutable
- **Duración**: ~5-7 minutos

### Release Workflow (`release.yml`)
- **Trigger**: Push de tag (v*), Manual
- **Función**: Crea release con ejecutable
- **Output**: GitHub Release con ZIP
- **Duración**: ~5-7 minutos

## 🎯 Flujo de Trabajo

### Desarrollo Normal
```bash
# 1. Trabajar en feature branch
git checkout -b feature/nueva-funcionalidad

# 2. Push y crear PR
git push origin feature/nueva-funcionalidad
# Crear PR en GitHub → CI se ejecuta automáticamente

# 3. Después de aprobación, merge a develop
git checkout develop
git merge feature/nueva-funcionalidad
git push origin develop → CI se ejecuta
```

### Crear Release
```bash
# 1. Merge develop a main
git checkout main
git merge develop
git push origin main → Build se ejecuta

# 2. Crear tag de versión
git tag v1.0.0
git push origin v1.0.0 → Release se crea automáticamente
```

## 🔧 Solución de Problemas

### Workflow falla
1. Revisa los logs en GitHub Actions
2. Verifica que las dependencias estén correctas
3. Si no hay tests, el workflow continuará normalmente

### No se crea release
1. Verifica que el tag tenga formato `v*` (ej: v1.0.0)
2. Verifica que el tag se haya pusheado: `git push origin v1.0.0`

### Build falla
1. Verifica que `src/main.py` exista
2. Verifica que las dependencias estén en `requirements.txt`
3. Prueba PyInstaller localmente

## 📚 Documentación Adicional

- [README.md](README.md) - Documentación del proyecto
- [.github/workflows/README.md](.github/workflows/README.md) - Documentación de workflows

---

**¡Listo!** El sistema CI/CD simplificado está configurado y listo para usar.
