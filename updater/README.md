# SDEP_CPP5 AutoUpdater (Actualizador automático)

Ejecutable de Windows que se encarga de **buscar actualizaciones** de
"Sistema de Gestión de Personal" en
[https://github.com/LiebeBlack/SDEP_CPP5/releases](https://github.com/LiebeBlack/SDEP_CPP5/releases),
**descargar e instalar** la última versión en silencio y **cerrarse solo**.

## Cómo funciona

1. **Al ejecutarlo por primera vez** (doble clic): pide una sola
   confirmación de UAC y se registra en el Programador de tareas de
   Windows para ejecutarse **cada 6 horas** (y también al iniciar sesión).
2. **En cada ejecución** consulta la última Release publicada en GitHub
   (API `releases/latest`).
3. Si la Release es más nueva que la última instalada registrada:
   - cierra la aplicación si está abierta (con aviso amable),
   - descarga `SistemaGestionPersonal-Setup-<versión>.exe` (con
     reintentos y verificación de tamaño),
   - lo instala en modo silencioso (`/VERYSILENT /SUPPRESSMSGBOXES`),
   - registra la versión instalada y termina.
4. Si ya está actualizado, no descarga nada y termina al instante.

El estado se guarda en `%LOCALAPPDATA%\SDEP_CPP5\auto_updater.json` y el
registro de actividad en `%LOCALAPPDATA%\SDEP_CPP5\updater.log`.

> En la primera ejecución, si la aplicación **no está instalada**, el
> actualizador instala la última versión disponible (comportamiento
> desactivable, ver variables de entorno).

## Cómo obtener el .exe

### Desde el CI (recomendado)

Cada Release publicada por el workflow `build.yml` incluye el adjunto
`SDEP_CPP5_AutoUpdater.exe` listo para usar.

### Compilar localmente (Windows)

```bash
python build.py --updater
```

Genera `dist_updater/SDEP_CPP5_AutoUpdater.exe` (PyInstaller onefile,
sin consola, ~10 MB, solo biblioteca estándar de Python).

## Instalación y uso

1. Copia `SDEP_CPP5_AutoUpdater.exe` a cualquier carpeta permanente
   (por ejemplo `C:\Program Files\Sistema de Gestión de Personal\`).
2. Ejecútalo una vez con doble clic y acepta el UAC: quedará
   programado cada 6 horas de forma automática.
3. A partir de ahí no hay que hacer nada: cada 6 horas revisa GitHub,
   descarga e instala las novedades y se cierra.

Para desprogramarlo:

```bat
schtasks /Delete /TN "SDEP_CPP5 AutoUpdater" /F
schtasks /Delete /TN "SDEP_CPP5 AutoUpdater (Logon)" /F
```

## Argumentos y variables de entorno

| Argumento       | Efecto                                                    |
|-----------------|-----------------------------------------------------------|
| *(sin args)*    | Registra las tareas (si falta) y ejecuta la actualización |
| `--check`       | Solo consulta GitHub e informa si hay novedades (sin instalar) |
| `--register`    | Registra las tareas del Programador y actualiza           |
| `--version`     | Muestra la versión del propio actualizador                |

| Variable de entorno              | Uso                                                        |
|----------------------------------|------------------------------------------------------------|
| `SDEP_UPDATE_API_URL`            | URL alternativa del JSON de Releases (pruebas)             |
| `SDEP_UPDATE_STATE_DIR`          | Carpeta del estado y del log (pruebas)                     |
| `SDEP_UPDATE_INSTALL_DIR`        | Ruta de instalación esperada de la app                     |
| `SDEP_UPDATE_INSTALL_IF_MISSING` | `"0"` para NO instalar si la app no está instalada         |

## Desarrollo y pruebas

La lógica (versiones, estado, selección del instalador, flujo de
actualización) está cubierta por `tests/test_auto_updater.py` y no
necesita red ni Windows:

```bash
python -m pytest tests/test_auto_updater.py -q --no-cov
```

El script usa solo la biblioteca estándar, por lo que el .exe no
depende del entorno virtual de la aplicación.