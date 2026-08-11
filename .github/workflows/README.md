# 🚀 GitHub Actions Workflows

Sistema simplificado de CI/CD para el Sistema de Gestión de Personal.

## 📁 Workflows

| Workflow | Propósito | Trigger |
|----------|-----------|---------|
| [ci.yml](ci.yml) | Tests básicos | Push a main/develop, PR |
| [build.yml](build.yml) | Construir ejecutable Windows | Push a main/develop, manual |
| [release.yml](release.yml) | Crear release con ejecutable | Push de tag (v*), manual |

## 🎯 Uso Simple

### 1. Desarrollo Normal
```bash
# Push a develop - ejecuta tests
git push origin develop

# Create PR - ejecuta tests
```

### 2. Crear Release
```bash
# Crear tag - ejecuta build y crea release
git tag v1.0.0
git push origin v1.0.0
```

### 3. Manual Trigger
```bash
# Trigger manual desde GitHub Actions UI
# o usando GitHub CLI
gh workflow run <workflow-name>
```

## ✅ Características

- **Simples**: Sin análisis complejos de código
- **Robustos**: Solo lo esencial para funcionar
- **Confiables**: Menos puntos de fallo
- **Rápidos**: Ejecución mínima

## 📝 Notas

- Los releases solo se crean cuando hay tags (v1.0.0, v1.0.1, etc.)
- Los builds se ejecutan en cada push a main/develop
- Los tests son opcionales - no fallan si no existen
- Sin notificaciones complejas, solo lo básico
