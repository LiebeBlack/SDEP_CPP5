# 🚀 GitHub Actions Workflows

Sistema simplificado de CI/CD para el Sistema de Gestión de Personal.

## 📁 Workflows

| Workflow | Propósito | Trigger |
|----------|-----------|---------|
| [build.yml](build.yml) | Construir ejecutable y crear pre-releases | Push a main/develop, manual |
| [release.yml](release.yml) | Crear releases oficiales con ejecutable | Push de tag (v*), manual |

## 🎯 Uso Simple

### 1. Desarrollo (Automatic Pre-releases)
```bash
# Push a develop - crea pre-release automáticamente
git push origin develop
# → Crea pre-release: dev-1, dev-2, dev-3...
# → Incluye ejecutable Windows
```

### 2. Release Oficial
```bash
# Crear tag de versión oficial
git tag v1.0.0
git push origin v1.0.0
# → Crea release oficial v1.0.0
# → Incluye ejecutable Windows
```

### 3. Manual Trigger
```bash
# Trigger manual desde GitHub Actions UI
gh workflow run <workflow-name>
```

## ✅ Características

- **Automático**: Cada push a develop crea pre-release
- **Pre-releases**: Todos los releases de develop son pre-releases
- **Ejecutables**: Cada release incluye el ejecutable Windows
- **Simples**: Sin tests automáticos que pueden fallar
- **Robustos**: Solo construcción y releases

## 📝 Notas

- **Develop branch**: Crea pre-releases automáticas (dev-1, dev-2, etc.)
- **Main branch**: Solo construye ejecutables (sin releases automáticos)
- **Releases oficiales**: Solo con tags (v1.0.0, v1.0.1, etc.)
- **Todos los releases incluyen**: Ejecutable Windows comprimido en ZIP
