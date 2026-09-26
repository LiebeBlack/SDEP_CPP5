# 🚀 GitHub Actions Workflows

Flujo de CI/CD del Sistema de Gestión de Personal: pruebas, compilación del
ejecutable (Windows y Linux), instalador de Windows (Inno Setup) y publicación
de releases firmadas.

## 📁 Workflows

| Workflow | Propósito | Disparadores |
|----------|-----------|--------------|
| [build.yml](build.yml) | Integración: pruebas, ejecutable Linux portable, ejecutable Windows, actualizador, instalador y artefactos. **No publica releases** | Push a main/develop, etiquetas `v*`, manual |
| [release.yml](release.yml) | Release firmada: compila, firma en dos pasadas (signtool SHA256 + timestamp) y publica la Release con el instalador firmado `SistemaGestionPersonal-Setup-<versión>.exe` como único adjunto | Push a `main`, etiquetas `v*`, manual |

Ninguna publicación la realiza `build.yml`: todas las releases las crea
`release.yml`, y siempre con los archivos firmados y auditados.

## 🎯 Uso simple

### 1. Release continua firmada por cada push (sin etiqueta)

```bash
# Cada push a main compila, firma y publica una Release continua
git push origin main
```

No hace falta crear etiquetas: `release.yml` genera la etiqueta interna
`continuous-v<versión>.<número de ejecución>` y publica la Release con el
instalador firmado. Los push a `develop` solo producen artefactos de
`build.yml`, sin Release.

### 2. Release versionada (opcional)

```bash
# Para una release con nombre y etiqueta versionados (ej: v2.82)
git tag v2.82
git push origin v2.82
```

### 3. Compilación manual

Desde la pestaña Actions → "Compilar e Instalar (Windows)" → Run workflow
(`build.yml`) o → "Release Firmada (Firma Masiva Profunda)" (`release.yml`).

## ✅ Qué hace cada job

### tests (ubuntu)

- Ejecuta la suite de pytest (453 funciones de prueba en 24 archivos) con
  cobertura.
- Sube el reporte de cobertura como artefacto.

### build-linux (debian 13)

1. Compila dentro de un contenedor **Debian 13** (glibc 2.41) e instala
   Python 3.15 con `uv`, de modo que el ejecutable funcione en Debian 13 y
   Ubuntu 24.04 LTS o superior.
2. Lee la versión desde `VERSION` (fuente única).
3. Compila el ejecutable con `spec/app.spec` (el mismo spec sirve para
   Windows y Linux; icono y metadatos de versión solo se aplican en Windows).
4. Autoverifica el ejecutable empaquetado con `--selftest` bajo `xvfb-run`.
5. Comprueba con `objdump` que la glibc máxima requerida por el paquete no
   supere 2.41.
6. Empaqueta `dist/SistemaGestionPersonal` en un `tar.gz` portable y lo sube
   como artefacto.

### build (windows)

1. Instala dependencias y PyInstaller.
2. Lee la versión desde `VERSION` (fuente única) y genera
   `src/config/build_info.py`; en releases continuas la versión visible añade
   el número de ejecución (`2.82.<run>`).
3. Compila el ejecutable con `spec/app.spec` (onedir, icono, metadatos).
4. Autoverifica el ejecutable empaquetado con `--selftest`.
5. Compila el actualizador `SDEP_CPP5_AutoUpdater.exe`.
6. Compila el instalador con Inno Setup (`installer/setup.iss`).
7. Crea el ZIP portable y sube como artefactos el instalador, el ZIP y el
   reporte de cobertura; el actualizador queda incluido dentro del instalador.

### build-sign-release (release.yml)

1. Compila el ejecutable y el actualizador, y genera el instalador.
2. Firma en dos pasadas: primero todo el contenido de `dist/` y `dist_updater/`
   (para que el instalador empaquete archivos ya firmados) y después el
   instalador final.
3. Audita que ningún archivo firmable quede sin firma o con otro certificado;
   si detecta alguno, la publicación se aborta.
4. Publica la Release con el instalador firmado como único adjunto.

## 📝 Notas

- **Firma de código (release.yml)**: requiere los secretos `PFX_BASE64` (PFX
  con la cadena de confianza completa, en Base64) y `PFX_PASSWORD`. El PFX se
  restaura en el runner, se valida y se elimina al finalizar; nunca viaja
  dentro del instalador.
- **Versionado**: la versión se lee de `VERSION` (actualmente 2.82). Con
  etiqueta `v*` la versión sale de la etiqueta (`v2.82` → `2.82`); con push a
  `main` se añade el número de ejecución.
- **Etiquetas de release continua**: `continuous-v<versión>.<run_number>`
  (únicas por compilación, no requieren gestión manual).
- **Adjunto de la Release**: únicamente el instalador firmado (el actualizador
  va incluido dentro del instalador).
- **Instalador**: instala en `Program Files` y guarda los datos del usuario
  en `%LOCALAPPDATA%\SistemaGestionPersonal`.
- **Datos del usuario**: se conservan al desinstalar (no se borran).