# SDEP_CPP5 AutoUpdater (Actualizador automático)

Ejecutable de Windows que se encarga de **buscar actualizaciones** de
"Sistema de Gestión de Personal" en
[https://github.com/LiebeBlack/SDEP_CPP5/releases](https://github.com/LiebeBlack/SDEP_CPP5/releases),
**descargar e instalar** la última versión en silencio y **cerrarse solo**.

## Cómo funciona

1. **El instalador (Setup.exe) ya lo incluye**: al instalar la aplicación
   queda copiado en la carpeta de instalación y se **programa solo** en el
   Programador de tareas de Windows para ejecutarse **cada 2 días a las
   09:00** con privilegios elevados (no hace falta hacer nada a mano).
2. **En cada ejecución** consulta la última Release publicada en GitHub
   (API `releases/latest`).
3. Si la Release es más nueva que la última instalada registrada:
   - cierra la aplicación si está abierta (con aviso amable),
   - descarga `SistemaGestionPersonal-Setup-<versión>.exe` (con
     reintentos y verificación de tamaño),
   - lo instala en modo silencioso (`/VERYSILENT /SUPPRESSMSGBOXES`),
   - registra la versión instalada y termina.
4. Si ya está actualizado, no descarga nada y termina al instante.

### Ventana de estado y bandeja del sistema

Mientras trabaja, el actualizador muestra **una ventana que cuenta todo lo
que hace** (comprobando, actualización disponible, descarga con porcentaje
y MB, instalación, "ya está actualizado" / "actualización completada",
errores) y coloca un **ícono en la bandeja del sistema** (la barra
inferior derecha de Windows). El ícono muestra el estado en su texto
flotante y tiene menú con clic derecho:

- **Buscar actualizaciones ahora**
- **Mostrar ventana**
- **Salir**

La ventana se cierra sola a los pocos segundos cuando todo salió bien; si
hubo un error queda abierta para que puedas leerlo.

El estado se guarda en `%LOCALAPPDATA%\SDEP_CPP5\auto_updater.json` y el
registro de actividad en `%LOCALAPPDATA%\SDEP_CPP5\updater.log`.

> En la primera ejecución, si la aplicación **no está instalada**, el
> actualizador instala la última versión disponible (comportamiento
> desactivable, ver variables de entorno).

## Cómo obtener el .exe

### Desde el CI (recomendado)

Cada Release publicada por el workflow `build.yml` incluye el adjunto
`SDEP_CPP5_AutoUpdater.exe` listo para usar (y las Releases firmadas por
`release.yml` lo firman también).

### Compilar localmente (Windows)

```bash
python build.py --updater
```

Genera `dist_updater/SDEP_CPP5_AutoUpdater.exe` (PyInstaller onefile,
sin consola, con tkinter para la ventana de estado y la bandeja).

## Instalación y uso

**Normal (recomendado):** instala la aplicación con `Setup.exe`. El
actualizador queda instalado y programado cada 2 días automáticamente.
Al desinstalar la aplicación, la tarea programada también se elimina.

**Manual:** copia `SDEP_CPP5_AutoUpdater.exe` a cualquier carpeta
permanente (por ejemplo `C:\Program Files\Sistema de Gestión de
Personal\`), ejecútalo una vez con doble clic y acepta el UAC: quedará
programado cada 2 días de forma automática.

Para desprogramarlo a mano:

```bat
schtasks /Delete /TN "SDEP_CPP5 AutoUpdater" /F
```

## Argumentos y variables de entorno

| Argumento         | Efecto                                                         |
|-------------------|----------------------------------------------------------------|
| *(sin args)*      | Registra la tarea (si falta) y actualiza **con ventana y bandeja** |
| `--check`         | Solo consulta GitHub e informa si hay novedades (sin instalar, en texto) |
| `--check --gui`   | Igual que `--check` pero con la ventana de estado              |
| `--register`      | Registra la tarea del Programador y actualiza                  |
| `--register-only` | SOLO registra la tarea (lo usa el instalador, sin ventana)     |
| `--unregister`    | Elimina las tareas programadas (lo usa el desinstalador)       |
| `--no-gui`        | Fuerza modo texto (sin ventana ni bandeja)                     |
| `--version`       | Muestra la versión del propio actualizador                     |

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

El script usa la biblioteca estándar (más tkinter solo para la ventana de
estado), por lo que el .exe no depende del entorno virtual de la
aplicación.