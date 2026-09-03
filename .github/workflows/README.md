# 🚀 GitHub Actions Workflow

Flujo de CI/CD del Sistema de Gestión de Personal: pruebas, compilación del
ejecutable, instalador de Windows (Inno Setup) y publicación de releases.

## 📁 Workflow

| Workflow | Propósito | Trigger |
|----------|-----------|---------|
| [build.yml](build.yml) | Pruebas + ejecutable + instalador + release | Push a main/develop, etiquetas `v*`, manual |

## 🎯 Uso Simple

### 1. Compilación automática (sin release)
```bash
# Cualquier push a main/develop compila y sube el instalador como artefacto
git push origin main
```

### 2. Release final con instalador
```bash
# Crea el release en GitHub con el instalador Setup.exe y el ZIP portable
git tag v1.0.3
git push origin v1.0.3
```

### 3. Compilación manual
Desde la pestaña Actions → "Compilar e Instalar (Windows)" → Run workflow.

## ✅ Qué hace cada job

### tests (ubuntu)
- Ejecuta la suite pytest (58 pruebas) con cobertura.
- Sube el reporte de cobertura como artefacto.

### build (windows)
1. Instala dependencias y PyInstaller.
2. Lee la versión desde `VERSION` (fuente única).
3. Compila el ejecutable con `spec/app.spec` (onedir, icono, versión).
4. Autoverifica el ejecutable empaquetado con `--selftest`.
5. Compila el instalador con Inno Setup (`installer/setup.iss`).
6. Sube `Setup.exe` + ZIP portable como artefactos.
7. Si el push es una etiqueta `v*`, publica un Release en GitHub.

## 📝 Notas

- **Versionado**: la versión se lee de `VERSION` (actualmente 1.0.3).
- **Instalador**: instala en `Program Files` y guarda los datos del usuario
  en `%LOCALAPPDATA%\SistemaGestionPersonal`.
- **Datos del usuario**: se conservan al desinstalar (no se borran).