# ⚡ Quick Start Guide - CI/CD con Pre-releases Automáticos

Guía rápida para el sistema CI/CD con pre-releases automáticos.

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
- ✅ Require status checks: "Build"
- ✅ Require branches to be up to date

## 📋 Workflows

### Build Workflow (`build.yml`)
- **Trigger**: Push a main/develop, Manual
- **Función**: Construye ejecutable Windows + Pre-releases automáticos (develop)
- **Output**: Archivo ZIP + Pre-release en GitHub
- **Duración**: ~5-7 minutos

### Release Workflow (`release.yml`)
- **Trigger**: Push a main, Manual
- **Función**: Crea release pre-release con ejecutable
- **Output**: GitHub Release (pre-release) con ZIP
- **Duración**: ~5-7 minutos

## 🎯 Flujo de Trabajo

### Desarrollo - Pre-releases Automáticas
```bash
# Push a develop - crea pre-release automáticamente
git push origin develop
```

**Resultado:**
- ✅ Pre-release: `dev-1`, `dev-2`, `dev-3`...
- ✅ Incluye ejecutable Windows
- ✅ Totalmente automático

### Main Branch - Releases Automáticos
```bash
# Push a main - crea release automáticamente
git push origin main
```

**Resultado:**
- ✅ Release: `1.0.0-1`, `1.0.0-2`, `1.0.0-3`...
- ✅ Incluye ejecutable Windows
- ✅ Todos son pre-releases

### Release Oficial (Manual)
```bash
# Manual trigger desde GitHub Actions UI
# Ingresar versión: ej: 1.0.0
```

**Resultado:**
- ✅ Release oficial con versión específica
- ✅ Incluye ejecutable Windows
- ✅ Control manual de versiones

## 🔧 Solución de Problemas

### No se crea pre-release
1. Verifica que el push sea a la rama `develop`
2. Revisa los logs en GitHub Actions
3. Verifica permisos del GITHUB_TOKEN

### Build falla
1. Verifica que `src/main.py` exista
2. Verifica que las dependencias estén en `requirements.txt`
3. Prueba PyInstaller localmente

### Release falla
1. Verifica que el GITHUB_TOKEN tenga permisos de `contents: write`
2. Revisa los logs del workflow
3. Verifica que el ZIP se haya creado correctamente

## 📚 Documentación Adicional

- [README.md](README.md) - Documentación del proyecto
- [.github/workflows/README.md](.github/workflows/README.md) - Documentación de workflows

---

**¡Listo!** El sistema CI/CD está configurado para crear pre-releases automáticas con ejecutables.
