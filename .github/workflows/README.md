# 🚀 GitHub Actions Workflows

Flujo de CI/CD del Sistema de Gestión de Personal: pruebas, compilación del
ejecutable (Windows y Linux), instalador de Windows (Inno Setup), APK de
Android y publicación de releases firmadas.

## 📁 Workflows

| Workflow | Propósito | Disparadores |
|----------|-----------|--------------|
| [build.yml](build.yml) | Integración: pruebas, ejecutable Linux portable, ejecutable Windows, actualizador, instalador, APK de Android sin firmar y artefactos. **No publica releases** | Push a main/develop, manual |
| [build_release.yml](build_release.yml) | APK Android firmado: restaura el almacén de firmas, compila `:app:assembleRelease`, verifica la firma con `apksigner` y publica el APK (y su firma v4 `.idsig`) como artefactos | Push a `main`, manual |
| [release.yml](release.yml) | Release firmada: compila, firma en dos pasadas (signtool SHA256 + timestamp) y publica la Release con el instalador firmado `SistemaGestionPersonal-Setup-<versión>.exe` como único adjunto | Push a `main`, etiquetas `v*`, manual |

Ninguna publicación la realiza `build.yml`: todas las releases las crea
`release.yml`, y siempre con los archivos firmados y auditados. `build.yml`
tampoco corre en etiquetas `v*`: esa es la única forma de que no compita con
la release firmada.

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
# Para una release con nombre y etiqueta versionados (ej: v3.0.1)
git tag v3.0.1
git push origin v3.0.1
```

### 3. Compilación manual

Desde la pestaña Actions → "Compilar e Instalar (Windows)" → Run workflow
(`build.yml`), → "Release Firmada (Firma Masiva Profunda)" (`release.yml`) o
→ "Android APK Firmado (Release)" (`build_release.yml`).

## ✅ Qué hace cada job

### tests (ubuntu)

- Ejecuta la suite de pytest (621 funciones de prueba en 38 archivos
  `test_*.py`, más `conftest.py`) con cobertura.
- Sube el reporte de cobertura como artefacto.

### build-linux (debian 13)

1. Compila dentro de un contenedor **Debian 13** (glibc 2.41) e instala
   Python 3.15.2 con `uv`, de modo que el ejecutable funcione en Debian 13 y
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
   el número de ejecución (`3.0.1.<run>`).
3. Compila el ejecutable con `spec/app.spec` (onedir, icono, metadatos).
4. Autoverifica el ejecutable empaquetado con `--selftest`.
5. Compila el actualizador `SDEP_CPP5_AutoUpdater.exe`.
6. Compila el instalador con Inno Setup (`installer/setup.iss`).
7. Crea el ZIP portable y sube como artefactos el instalador, el ZIP y el
   reporte de cobertura; el actualizador queda incluido dentro del instalador.

### build-android (build.yml)

1. Configura JDK 17 y el wrapper de Gradle.
2. Ejecuta las pruebas unitarias de Kotlin y compila el APK de depuración y el
   de release **sin firmar** (`:app:testDebugUnitTest :app:assembleDebug
   :app:assembleRelease`), que es lo que basta para validar R8 en cada push.
3. Sube ambos APK como artefactos; la firma de distribución la produce
   `build_release.yml`.

### build-android-signed (build_release.yml)

1. Lee `VERSION` y configura JDK 17.
2. Valida los cuatro secretos del almacén de firmas y lo restaura en
   `release.keystore` **antes** de compilar; sin el archivo,
   `signingConfigs/release` no existe y Gradle generaría un APK sin firmar.
3. Compila `:app:assembleRelease` con la firma de release.
4. Verifica el APK con `apksigner --verbose --print-certs` (v1/v2/v3/v4) y
   falla si el archivo firmado no existe.
5. Publica el APK y, cuando Gradle la genera, la firma v4 `.idsig` como
   artefactos independientes.
6. Borra el almacén del runner al terminar, incluso si la ejecución falla.

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
- **Firma del APK (build_release.yml)**: requiere los secretos
  `KEYSTORE_BASE64` (almacén `.keystore`/`.jks` en Base64),
  `KEYSTORE_PASSWORD`, `KEY_ALIAS` y `KEY_PASSWORD`. El almacén se restaura
  solo en el runner y se borra al terminar.
- **Versionado**: la versión se lee de `VERSION` (actualmente 3.0.1). Con
  etiqueta `v*` la versión sale de la etiqueta (`v3.0.1` → `3.0.1`); con push a
  `main` se añade el número de ejecución.
- **Etiquetas de release continua**: `continuous-v<versión>.<run_number>`
  (únicas por compilación, no requieren gestión manual).
- **Adjunto de la Release**: únicamente el instalador firmado (el actualizador
  va incluido dentro del instalador).
- **Instalador**: instala en `Program Files` y guarda los datos del usuario
  en `%LOCALAPPDATA%\SistemaGestionPersonal`.
- **Datos del usuario**: se conservan al desinstalar (no se borran).