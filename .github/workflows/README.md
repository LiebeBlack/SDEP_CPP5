# 🚀 GitHub Actions Workflow

Flujo de CI/CD del Sistema de Gestión de Personal: pruebas, compilación del
ejecutable, instalador de Windows (Inno Setup) y publicación de releases.

## 📁 Workflow

| Workflow | Propósito | Trigger |
|----------|-----------|---------|
| [build.yml](build.yml) | Pruebas + ejecutable + instalador + release | Push a main/develop, etiquetas `v*`, manual |

## 🎯 Uso Simple

### 1. Release automática por cada push (sin etiqueta)

```bash
# Cada push a main compila y publica automáticamente un Release en GitHub
git push origin main
```

No se necesita crear ninguna etiqueta: el workflow genera una etiqueta
interna única (`continuous-v<versión>.<número de run>`) y publica el
Release con el instalador `Setup.exe` y el ZIP portable.

### 2. Release versionada (opcional)

```bash
# Para una release con nombre y etiqueta versionados (ej: v1.0.3)
git tag v1.0.3
git push origin v1.0.3
```

### 3. Compilación manual

Desde la pestaña Actions → "Compilar e Instalar (Windows)" → Run workflow.

## ✅ Qué hace cada job

### tests (ubuntu)
- Ejecuta la suite pytest (79 pruebas) con cobertura.
- Sube el reporte de cobertura como artefacto.

### build (windows)
1. Instala dependencias y PyInstaller.
2. Lee la versión desde `VERSION` (fuente única).
3. Compila el ejecutable con `spec/app.spec` (onedir, icono, versión).
4. Autoverifica el ejecutable empaquetado con `--selftest`.
5. Compila el instalador con Inno Setup (`installer/setup.iss`).
6. Sube `Setup.exe` + ZIP portable como artefactos.
7. Publica un Release en GitHub en cada push a `main` (release continua)
   o cuando el push es una etiqueta `v*` (release versionada).
   Los pushes a `develop` solo generan artefactos, sin Release.

## 📝 Notas

- **Versionado**: la versión se lee de `VERSION` (actualmente 1.0.3).
- **Etiquetas de release continua**: `v1.0.3-ci.<run_number>` (únicas por
  compilación, no requieren gestión manual).
- **Instalador**: instala en `Program Files` y guarda los datos del usuario
  en `%LOCALAPPDATA%\SistemaGestionPersonal`.
- **Datos del usuario**: se conservan al desinstalar (no se borran).