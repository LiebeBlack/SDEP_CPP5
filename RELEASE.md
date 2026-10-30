# Procedimiento de release estable

Todo release parte de una única regla: **no se etiqueta un commit que no haya
pasado la puerta de calidad y la suite completa**. El resto son pasos mecánicos.

## 1. Puerta de calidad (obligatoria)

```bash
python tools/verificar_release.py --tests
```

Debe terminar con `RESULTADO: listo para etiquetar`. Comprueba:

| Comprobación | Qué verifica |
| --- | --- |
| Versión coherente | `VERSION`, `pyproject.toml`, `src/config/settings.py`, `src/__init__.py` e `installer/setup.iss` declaran la misma versión |
| Recurso del actualizador | `updater/updater.spec` deriva la versión de `VERSION` (no de un archivo fijo) |
| Sintaxis Python | todo `src/`, `sync_agent/`, `updater/`, `tools/` y los scripts de raíz compilan |
| Documentación | `tools/verify_docs.py` confirma que `docs/` corresponde a los `.md` de las fuentes |
| Credenciales rastreadas | ni `.env`, ni claves privadas, ni claves SSH en el índice de Git |
| Datos rastreados | avisa de bases y respaldos `.db`/`.db.gz` versionados |
| Árbol de trabajo | avisa si hay cambios sin confirmar (la etiqueta debe apuntar al commit ya probado) |
| Suite de pruebas | `pytest -q` completa |

Los **avisos** no bloquean, pero se revisan antes de etiquetar. Las **fallas**
impiden el release.

## 2. Subir la versión

La versión se cambia en un solo lugar y se propaga:

1. `VERSION` (fuente principal).
2. `pyproject.toml` → `version`.
3. `src/config/settings.py` → `APP_VERSION_DEFAULT`.
4. `src/__init__.py` → `__version__`.
5. `installer/setup.iss` → `#define MyAppVersion`.

Después, `python tools/verificar_release.py` debe quedar en `[OK] Versión
coherente`. El ejecutable y el actualizador toman la versión de `VERSION` al
compilarse (`spec/app.spec`, `updater/updater.spec`), así que no hay copias
manuales que actualizar.

La aplicación Android no lleva copia manual: `android/app/build.gradle.kts`
lee `VERSION` y deriva de ahí `versionName` y `versionCode` (3.0.1 → 30001).
La puerta falla si alguien vuelve a escribir un `versionName` literal o un
`versionCode` fijo.

## 3. Compilar localmente (opcional, para humo)

```bash
python build.py            # ejecutable + actualizador + instalador
python build.py --exe      # solo el ejecutable
```

Genera `src/config/build_info.py` con versión, commit y fecha. **No** se edita a
mano: lo escribe `build.py` (o el CI con `BUILD_VERSION`/`BUILD_COMMIT`).

## 4. Etiquetar y publicar

El flujo automatizado está en [QUICKSTART_CICD.md](QUICKSTART_CICD.md):

- `build.yml` — pruebas + ejecutables Windows/Linux en cada push (no publica).
- `release.yml` — compila, firma, empaqueta y publica el APK Android, el
  ejecutable, el actualizador y el instalador firmado.

Para una release versionada:

```bash
git tag 3.0.2
git push origin 3.0.2
```

La etiqueta **no** lleva prefijo `v` a propósito (así la nombra el workflow).
El tag debe apuntar a un commit que ya pasó la puerta de calidad.

## 5. Verificación posterior (en el equipo destino)

La instalación real se valida con [CHECKLIST_PRODUCCION.md](CHECKLIST_PRODUCCION.md):
firma Authenticode del instalador, reglas de firewall, tarea del actualizador y
primer arranque. Ese checklist registra las evidencias que se conservan en el
acta.

## Qué se corrigió en la preparación de releases

- `updater/updater.spec` incrustaba un `version_info.txt` fijo que quedó en
  **2.79.0**: el actualizador distribuido mostraba una versión distinta a la del
  producto. Ahora el recurso de versión se construye desde `VERSION`, igual que
  el ejecutable principal, y el archivo obsoleto se retiró.
- El login por HTTP fallaba de forma intermitente **solo** con la suite
  completa. No era la base de datos: el volcado de hilos mostró al hilo de la
  petición ejecutando el `__del__` de una fuente Tk (basura que dejaban las
  pruebas de GUI) dentro de SQLAlchemy. Ese destructor llama a Tcl, que no es
  seguro entre hilos, así que el hilo de la petición se quedaba bloqueado y la
  petición nunca respondía. Las pruebas de GUI recolectan ahora la basura en el
  hilo principal, que es el único que puede tocar Tcl: la suite pasó de ~4:03 a
  ~3:35 y dos corridas completas consecutivas quedaron en 642 pruebas.

  > **Regla para el código de interfaz:** un objeto Tk (ventanas, fuentes,
  > imágenes) debe destruirse en el hilo que lo creó. Los hilos de fondo —el
  > servidor de sincronización, los respaldos— nunca deben liberarlos.
