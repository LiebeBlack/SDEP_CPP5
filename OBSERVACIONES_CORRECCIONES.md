# Observaciones de corrección — SDEP_CPP5

**Naturaleza de este documento:** catálogo de observaciones. Cada línea citada apunta al estado del código en la fecha de la auditoría. **Las correcciones ya ejecutadas están registradas en `CORRECCIONES_EJECUTADAS.md`** (sin verificación en ejecución: no hay Python en la máquina); lo que no figure allí sigue pendiente de decisión.

**Fecha:** 2026-10-04
**Método:** lectura estática. No hay Python en la máquina de auditoría, así que ningún check se ejecutó y ninguna cifra de cobertura se midió.
**Alcance declarado:** correcciones, no refactor estructural.

Documento hermano: `PLAN_MAESTRO_SDP_CPP5.md` (hoja de ruta por fases). Este documento es el **inventario preciso** de qué corregir y dónde; el plan es el orden en que hacerlo.

## Índice de secciones

| # | Sección | Observaciones |
|---|---|---|
| A | [Módulo académico inalcanzable](#a) | 5 |
| B | [Documentación que contradice al código](#b) | 7 |
| C | [Residuos versionados](#c) | 4 |
| D | [Mapa de permisos](#d) | 4 |
| E | [Cobertura de pruebas ausente](#e) | 4 |
| F | [Higiene de código](#f) | 4 |
| G | [Brecha de proceso en CI](#g) | 4 |
| H | [Motor de nómina, línea por línea](#h) | 4 |
| I | [Servicios, repositorios y sincronización](#i) | 9 |

**Prioridad sugerida por impacto, no por oportunidad de ejecución:**

| Orden | Sección | Razón |
|---|---|---|
| 1º | G | Explica por qué existen B y F, y el arreglo es un workflow |
| 2º | A | Único hallazgo que cambia el valor del proyecto |
| 3º | C | Datos personales en el historial de Git |
| 4º | B | Credibilidad de la documentación |
| 5º | I | Defectos de integración en servicios y sincronización |
| 6º | D, E, F, H | Mantenimiento y consistencia |

**Sobre H:** salió de leer el código de `src/nomina/` completo en lugar de usar `grep`. Contiene un hallazgo retirado (H.1) y tres observaciones menores, ninguna de ellas un defecto de cálculo. Se conserva el registro del descarte porque un informe de calidad que solo publica lo que encontró también miente: lo relevante es que el motor de nómina **fue revisado línea por línea y no tiene defectos de cálculo**, y eso solo es comprobable si queda constancia del camino seguido.

**Sobre I:** segunda pasada de lectura estricta, esta vez sobre `src/services/`, `src/repositories/` y `sync_agent/`. A diferencia de H, aquí sí hay defectos: dos afectan datos que se guardan (I.1 y I.2) y uno roza el invariante de convergencia de la sincronización (I.4). Ninguno es un error de cálculo del motor de nómina.

---

<a id="a"></a>
## A. Módulo académico inalcanzable

Observación de mayor alcance. Un subdominio de ~2.530 líneas existe en la capa de datos y lógica, y no es alcanzable desde ningún punto de entrada del producto.

### A.1 — Sin interfaz gráfica

**Observación:** ningún archivo de `src/gui/` referencia los modelos académicos. Verificado: cero coincidencias.

| Ubicación | Estado actual |
|---|---|
| `src/gui/main_window.py:40` | `MODULOS` — 7 entradas, ninguna académica |
| `src/gui/main_window.py:50` | `TITULOS_VENTANA` — 7 entradas, ninguna académica |
| `src/gui/main_window.py:60` | `FRAME_CLASSES` — 7 entradas, ninguna académica |
| `src/gui/main_window.py:610` | `METODOS_REFRESCAR` — sin entradas académicas |
| `src/gui/main_window.py:621` | `METODOS_NUEVO` — sin entradas académicas |
| `src/gui/main_window.py:631` | `METODOS_GUARDAR` — sin entradas académicas |

**Efecto:** `AcademicoService` (30 métodos), `NotaService` (28) y `TokenSesionService` (9) no tienen ningún camino de ejecución desde la interfaz.

### A.2 — La infraestructura ya está lista

**Observación:** la capa de datos no necesita trabajo previo; ya está sembrada y protegida.

| Ubicación | Qué hay |
|---|---|
| `src/config/database.py:479` | `nota_minima` = 0 |
| `src/config/database.py:490` | `nota_maxima` = 20 |
| `src/config/database.py:495` | `nota_aprobatoria` = 10 |
| `src/config/database.py:553-600` | 3 triggers `RAISE(ABORT)` sobre `notas_finales` |
| `src/services/nota_service.py:455-488` | `_exigir_token`, `_autorizar`, `_autorizar_sesion` |

**Efecto:** la configuración de calificaciones está sembrada en la base de datos de todos los usuarios y los triggers de inmutabilidad están activos, sobre tablas que no se llenan.

### A.3 — Sin pruebas

**Observación:** ningún archivo de `tests/` importa los tres servicios académicos. Cero coincidencias para cada uno.

### A.4 — Sin sincronización

**Observación:** `ENTIDADES` replica 6 tablas. Ninguna es académica.

| Tabla replicada | ¿Académica? |
|---|---|
| `empleados`, `documentos`, `incidencias` | No |
| `contratos`, `pagos`, `configuraciones` | No |

### A.5 — Sin documentación

**Observación:** ningún `.md` de la raíz ni de `TESIS/` nombra estudiantes, grados, matrículas ni notas, pese a que el proyecto es para instituciones educativas.

---

<a id="b"></a>
## B. Documentación que contradice al código

**Observación de conjunto:** 12 desviaciones verificadas una a una. Cada línea citada se leyó y su contenido coincide con lo descrito.

### B.1 — Número de archivos de prueba

| Ubicación | Dice | Realidad |
|---|---|---|
| `README.md:116` | «25 archivos» | 27 (`tests/test_*.py`) |

**Nota:** el conteo de 27 no incluye `conftest.py`, que no empieza por `test_`.

### B.2 — Versión declarada

| Ubicación | Dice | `VERSION` |
|---|---|---|
| `NOTAS_DESARROLLO.md:803` | 3.0.0 | 3.0.1 |
| `GUIA_USUARIO.md:645` | 3.0.0 | 3.0.1 |
| `NOTAS_DESARROLLO.md:369` | «Novedades de la Versión 3.0.0» | 3.0.1 |
| `QUICKSTART_CICD.md:57-59` | ejemplo `v3.0.0` | ejemplo, menor |
| `CONTRIBUTING.md:405` | ejemplo `v3.0.0` | ejemplo, menor |

### B.3 — Cifras de pruebas y cobertura

| Ubicación | Afirma | Realidad |
|---|---|---|
| `NOTAS_DESARROLLO.md:727` | 295 pruebas | **no medida** |
| `NOTAS_DESARROLLO.md:729` | 57 % total, >70 % en lógica de negocio | **no medida** |

**Efecto:** son las cifras más propagadas del proyecto y no son reproducibles. Requieren medición antes de publicarse.

### B.4 — Atajos de teclado

| Ubicación | Afirma | Realidad |
|---|---|---|
| `NOTAS_DESARROLLO.md:694` | `Ctrl+1..6` | 7 módulos → `Ctrl+1..7` |
| `GUIA_USUARIO.md:593` | `Ctrl+1 … Ctrl+7` | correcto |
| `DOCUMENTACION_TECNICA.md:353` | `Ctrl+1 … Ctrl+7` | correcto |
| `DOCUMENTACION_TECNICA.md:339` | `Ctrl+1..7` | correcto |
| `README.md:303` | `Ctrl+1 … Ctrl+7` | correcto |

**Observación:** solo `NOTAS_DESARROLLO.md:694` está mal, pero es la única que además contradice su propia tabla posterior (línea 461 dice `Ctrl+1..7`).

### B.5 — `.env.example` fija una versión obsoleta

**Observación:** la más peligrosa de la sección.

| Ubicación | Valor |
|---|---|
| `.env.example:15` | `APP_VERSION=1.0.4` |

**Efecto:** `Settings.__init__` prioriza la variable de entorno (`os.getenv("APP_VERSION") or ...`). Quien copie `.env.example` a `.env` fija la versión y la aplicación muestra `v1.0.4` con un código 3.0.1. Un `.env` no versionado seguiría funcionando, pero el rótulo de versión quedaría congelado.

### B.6 — `docs/content/` desincronizado

**Observación:** `docs/content/` es copia de los `.md` de la raíz y diverge.

| Archivo | Original | Copia | Δ |
|---|---|---|---|
| `README.md` | 16.562 B | 16.560 B | 2 B |

**Efecto:** el portal web sirve primero la copia local, así que muestra contenido obsoleto al abrirse sin conexión. Detalle en la sección G.

### B.7 — Referencias de versión en ejemplos

**Observación menor:** `README.md:156-157` usa `v3.0.1` como ejemplo de tag. Es correcto y no requiere cambio.

---

<a id="c"></a>
## C. Residuos versionados

### C.1 — `hang_stack.txt`

**Observación:** traza de pila de un cuelgue de 15 s. Commit `4d51772` («4.7»).

**Ubicaciones relacionadas:**

| Ubicación | Qué documenta |
|---|---|
| `hang_stack.txt` | La traza completa del cuelgue |
| `src/gui/main_window.py:641` | `_show_frame` — el frame donde se bloquea |
| `tests/test_gui_smoke.py:212` | El test que lo disparaba |
| `tests/test_gui_smoke.py:249` | El `monkeypatch` que hoy lo neutraliza |

**Efecto:** el defecto **ya está corregido**. El archivo documenta un bug inexistente: su único valor es histórico, y un `messagebox` modal bloqueante es precisamente lo que cuelga una suite en CI. La prueba de regresión vigente está en `test_gui_smoke.py:240-258`, donde `test_mostrar_modulo_invalido` verifica que el frame actual no cambia y que el aviso contiene «permisos».

### C.2 — `backups/` con bases reales

**Observación:** cuatro bases comprimidas y su metadato están versionados.

| Archivo versionado | Contenido |
|---|---|
| `backups/auto_shutdown.db.gz` | Base real comprimida |
| `backups/initial_setup.db.gz` | Base real comprimida |
| `backups/test_security.db.gz` | Base real comprimida |
| `backups/backup_metadata.json` | Metadatos con rutas absolutas |

### C.3 — Rutas absolutas del desarrollador en metadatos

**Observación:** `backups/backup_metadata.json` contiene rutas del equipo de desarrollo y checksums de su base personal.

```json
"path": "C:\Users\L\Documents\GitHub\SDEP_CPP5\backups\initial_setup.db.gz"
```

**Efecto:** expone la estructura del disco del desarrollador. Un respaldo puede contener datos personales de empleados; el historial de Git es permanente aunque el archivo se borre hoy.

### C.4 — `.gitignore` deja pasar los respaldos

**Observación:** `.gitignore` excluye `*.db` pero **no** `*.db.gz`.

| Regla actual | ¿Cubre los respaldos? |
|---|---|
| `*.db` | No — los archivos son `.db.gz` |
| `*.sqlite`, `*.sqlite3` | No |

**Efecto:** los respaldos pasaron el filtro porque la extensión compuesta `.db.gz` no coincide con el patrón `*.db`.

---

<a id="d"></a>
## D. Mapa de permisos

### D.1 — Módulo fantasma «reportes»

**Observación:** `MODULE_ACCESS` declara un módulo que no existe.

| Ubicación | Contenido actual |
|---|---|
| `src/utils/security.py:399` | Inicio de `MODULE_ACCESS` |
| `src/utils/security.py:406` | `"reportes": ("admin", "manager", "viewer"),` |
| `src/utils/security.py:407` | Fin del diccionario |
| `src/utils/security.py:412` | `modulos_conocidos()` devuelve `frozenset(MODULE_ACCESS)` |

**Efecto:** `modulos_conocidos()` expone `reportes` como módulo válido del sistema. No existe en `MODULOS` ni en `FRAME_CLASSES`, así que el sistema declara proteger algo que no tiene.

### D.2 — «Reportes» sí existe, pero es otra cosa

**Observación:** la ambigüedad que puede Causear la reaparición del error. Estas son **capacidades**, no módulos:

| Ubicación | Qué es |
|---|---|
| `src/gui/frames.py:910` | permiso `"report"` — reportes de empleados |
| `src/gui/frames.py:938` | permiso `"report"` — ficha de empleado |
| `src/gui/frames.py:2028` | permiso `"report"` — reporte de vencimientos |
| `src/gui/frames.py:2639` | permiso `"report"` — reporte de incidencias |
| `src/gui/contratos_frame.py:466` | permiso `"report"` — reportes de contratos |
| `src/gui/main_window.py:780` | mención en el diálogo Ayuda |

**Lectura:** quien lea `security.py:406` y vea «reportes» repetido en varios frames puede concluir que falta un módulo `reportes` en `MODULOS`. El mapa mezcla dos conceptos: módulos navegables y permisos de acción.

### D.3 — El mecanismo inverso ya funciona

**Observación:** el riesgo de un módulo *declarado sin implementar* está cubierto.

| Ubicación | Qué hace |
|---|---|
| `src/utils/security.py:449` | `can_access_module` es *fail-closed*: módulo desconocido se deniega para todos |
| `src/gui/main_window.py:270-273` | Detecta módulos de `MODULOS` sin permiso declarado |
| `src/gui/main_window.py:274-279` | Registra un `warning` en el arranque |

**Efecto:** un módulo nuevo en `MODULOS` sin entrada en `MODULE_ACCESS` queda oculto para todos los roles y además avisa. Ese mecanismo es correcto y conviene preservar.

### D.4 — Permiso `update_own` declarado y nunca consumido

**Observación:** el rol `user` tiene un permiso que nada lee.

| Ubicación | Contenido |
|---|---|
| `src/utils/security.py:441` | `"user": ["read", "update_own"]` |

**Verificado:** `update_own` no aparece en ningún otro archivo de `src/`. El comentario de `security.py:439-440` ya lo explica: el rol Usuario no tiene vínculo de propiedad con una cuenta de empleado que validar. Está declarado de forma intencionada, pero no tiene consumidor; conviene que sea una decisión explícita y no un descuido.

---

<a id="e"></a>
## E. Cobertura de pruebas ausente

### E.1 — Tres servicios sin un solo test

**Observación:** verificado con grep sobre `tests/*.py`. Cero coincidencias para cada uno.

| Servicio | Métodos | Archivos de prueba que lo mencionan |
|---|---|---|
| `src/services/academico_service.py` | 30 | 0 |
| `src/services/nota_service.py` | 28 | 0 |
| `src/services/token_sesion_service.py` | 9 | 0 |

**Efecto:** lo sin verificar es lo más sensible del sistema. `TokenSesionService.emitir` (línea 56) genera credenciales con `secrets.token_urlsafe`, y nadie comprueba que un token expirado deje de validar ni que el hash no se invierta.

### E.2 — Los triggers de inmutabilidad no se prueban por SQL directo

**Observación:** `src/config/database.py:553-600` define tres triggers que abortan `INSERT`, `UPDATE` y `DELETE` sobre `notas_finales` en periodos cerrados.

**Efecto:** su propósito declarado es proteger «incluso por SQL directo (scripts de corrección, importaciones masivas, herramientas externas)». Ninguna prueba los ejercita por esa vía: probarlos solo a través del servicio dejaría sin verificar justamente el escenario que motiva su existencia.

### E.3 — Los gráficos del dashboard no tienen test

**Observación:** `src/gui/widgets/graficos.py` (437 líneas) dibuja barras, dona y línea sobre `Canvas`. Cero archivos de prueba lo mencionan.

**Efecto:** `test_gui_smoke.py` verifica que los tres widgets se construyen (`winfo_exists()`), pero no que dibujen datos correctos.

### E.4 — Cifras de cobertura no medidas

**Observación:** `NOTAS_DESARROLLO.md:727-729` publica 295 pruebas y 57 % de cobertura. No se reprodujeron.

**Efecto:** al no haber Python en la máquina de auditoría, no se midió nada. La cifra real puede ser mayor o menor; lo que consta es que la publicada no es verificable tal como está.

---

<a id="f"></a>
## F. Higiene de código

### F.1 — `log_message()` escribe a stdout

**Observación:** única llamada a `print()` en todo `src/`.

| Ubicación | Contenido |
|---|---|
| `src/utils/helpers.py:589` | `def log_message(message: str, level: str = "INFO") -> None:` |
| `src/utils/helpers.py:597` | `timestamp = datetime.now().strftime(...)` |
| `src/utils/helpers.py:598` | `print(f"[{timestamp}] [{level}] {message}")` |
| `src/utils/helpers.py:17` | `logger = logging.getLogger(__name__)` — ya existe en el módulo |

**Efecto:** el módulo ya tiene un `logger`; la función no lo usa. Los `print` de `sync_agent/__main__.py` y `updater/` sí son legítimos: son interfaces de línea de comandos.

### F.2 — Su test depende de stdout

**Observación:** la corrección de F.1 **rompe** esta prueba si se hace sola.

| Ubicación | Contenido |
|---|---|
| `tests/test_helpers.py:228` | `def test_log_message(self, capsys):` |
| `tests/test_helpers.py:229` | `helpers.log_message("mensaje de prueba", "WARNING")` |
| `tests/test_helpers.py:230` | `captured = capsys.readouterr()` |
| `tests/test_helpers.py:231` | `assert "[WARNING]" in captured.out` |

**Efecto:** `logging` no escribe a stdout por defecto, así que migrar F.1 sin migrar esta prueba a `caplog` deja la suite en rojo. Los dos cambios son un solo trabajo.

### F.3 — 165 llamadas de log con f-string

**Observación:** formato eagerness. `logger` evalúa los argumentos aunque el nivel esté desactivado.

| Ubicación | Ejemplo |
|---|---|
| `src/config/database.py:193` | `logger.info(f"Migración: columna {tabla}.{columna} agregada")` |
| `src/config/database.py:328` | `logger.info(f"Purga: tabla {tabla} eliminada")` |
| `src/config/database.py:652` | `logger.info(f"Base de datos configurada: {self.database_path}")` |
| `src/config/database.py:707` | `logger.error(f"Error creando engine de base de datos: {e}")` |
| `src/config/database.py:756` | `logger.warning(f"No se pudo preparar el esquema de sincronización: {e}")` |

**Total verificado:** 165 ocurrencias en `src/`.

**Lectura:** no es un defecto funcional y el proyecto ya usa el estilo diferido (`logger.warning("... %s", valor)`) en el código nuevo. Es inconsistencia de estilo, no de comportamiento.

### F.4 — Cuatro `except` que silencian

**Observación:** sin registro y sin re-lanzamiento. Verificado en contexto: los cuatro son tolerancias deliberadas, no rutas de error de negocio.

| Ubicación | Contexto verificado | Juicio |
|---|---|---|
| `updater/auto_updater.py:174` | `except OSError:` al escribir en el archivo de log | Razonable: si el log no se puede escribir, no hay a dónde reportar |
| `updater/auto_updater.py:181-182` | callback `on_progress(message)` invocado por la GUI que llama | Razonable: la GUI que llama no debe propagar |
| `updater/auto_updater.py:271-273` | callback `on_download(done, total)` en la descarga | Razonable: mismo caso |
| `updater/updater_gui.py:178-180` | `_emit_status`: `self._queue.put_nowait` | Razonable: Tk sin hilo principal; una cola llena no debe tumbar la app |
| `updater/updater_gui.py:184-186` | `_emit_download`: idéntico | Razonable: mismo caso |

**Lectura:** los cuatro están en el actualizador, fuera de `src/`, y los tres últimos son exactamente el patrón correcto para código que cruza hilos hacia Tk. **No se observa ningún defecto aquí**; queda registrado para que conste que se revisó y se descartó.

---

<a id="g"></a>
## G. Brecha de proceso en CI

Observación de proceso, no de código. Explica por qué los hallazgos B y F llegan a existir: **las herramientas que los detectarían existen, están escritas y no se ejecutan en ningún sitio.**

### G.1 — El CI ejecuta pytest y nada más

**Observación:** `build.yml` declara cinco herramientas de calidad y ninguna se invoca.

| Herramienta | ¿Declarada? | ¿Ejecutada por el CI? |
|---|---|---|
| pytest | Sí | **Sí** |
| flake8 | Sí (`requirements-dev.txt`, `.flake8`) | **No** |
| black | Sí (`pyproject.toml`) | **No** |
| isort | Sí (`pyproject.toml`) | **No** |
| mypy | Sí (`pyproject.toml`) | **No** |
| pylint | Sí (`requirements-dev.txt`) | **No** |

**Verificado:** cero coincidencias de `flake8`, `black`, `isort`, `mypy` o `pylint` en `.github/workflows/`.

**Ubicaciones:**

| Archivo | Contenido |
|---|---|
| `requirements-dev.txt` | Declara las seis herramientas |
| `.flake8` | Configura `select = F,E9,W6` |
| `pyproject.toml` | Configura `[tool.black]`, `[tool.isort]`, `[tool.mypy]` |
| `.github/workflows/build.yml:41-42` | Único check de calidad: `python -m pytest tests/ -q` |

**Efecto:** una configuración de linters escrita con cuidado y nunca aplicada. El código puede alejarse del estilo declarado sin que nada lo advierta.

### G.2 — Existe un verificador de documentación que nadie ejecuta

**Observación:** `tools/verify_docs.py` valida exactamente el hallazgo B.6.

| Ubicación | Qué valida |
|---|---|
| `tools/verify_docs.py:22-47` | `check_content_mirrors()` — compara cada `.md` de la raíz con su copia en `docs/content/` |
| `tools/verify_docs.py:43` | `raise RuntimeError` con la lista de copias desincronizadas |
| `tools/verify_docs.py:63-69` | Valida que `docs_data.js` tenga tantos documentos como el manifiesto |

**Efecto:** la herramienta detecta `docs/content/` desincronizado y falla con un mensaje accionable. **No hay ningún workflow que la invoque.** Por eso la desviación de B.6 sigue en el repositorio: existe el detector, falta la alarma.

### G.3 — La desincronización está presente

**Observación:** la desviación que G.2 podría detectar existe hoy.

| Original | Copia | Δ |
|---|---|---|
| `README.md` — 16.562 B | `docs/content/README.md` — 16.560 B | 2 B |

**Efecto:** el portal sirve primero la copia local (lo documenta el propio `verify_docs.py:24-27`), así que un usuario sin conexión lee contenido obsoleto. Regenerar con `python tools/generate_docs_bundle.py` lo resuelve, pero nada lo hace automáticamente.

### G.4 — Síntesis

**Observación de conjunto:** los hallazgos B, F.1 y F.3 no son descuidos aislados; son la clase de defecto que un pipeline de calidad ejecutando las herramientas ya escritas habría impedido. La observación accionable no es «configurar más linters» sino **«ejecutar en CI los checks que el proyecto ya declara»**: es trabajo de un workflow, no de configuración de herramientas.

---

<a id="h"></a>
## H. Motor de nómina — lectura línea por línea

Observaciones obtenidas leyendo el código completo de los ocho módulos de `src/nomina/`, no con grep.

**Advertencia de método:** la primera observación de esta sección parecía un bug de cálculo que afectaba dinero pagado. Se verificó y **resultó ser un falso positivo mío, causado por un error aritmético al trazar a mano**. El registro del descarte se conserva en H.1 para que conste, y para que quien lea este documento no reproduzca el mismo error. La lección operativa: sin intérprete disponible, una traza manual con división entera **no es evidencia suficiente** para acusar un defecto monetario. Hay que ejecutar la aritmética.

### H.1 — Falso positivo descartado: el cálculo de antigüedad es correcto (RETIRADO)

**Este hallazgo se formuló, se verificó y se descartó. Se documenta para que conste.**

**Lo que se afirmó:** que [prestaciones.py:35-37](src/nomina/prestaciones.py#L35-L37) calculaba la fecha del último aniversario mensual sobre el mes equivocado, y que en el caso de un año exacto eso situaba el aniversario en el futuro, perdiendo días de antigüedad.

**La traza que lo sostenía** (ingreso `2020-01-15`, egreso `2021-01-15`, meses = 12):

```
anio = 2020 + ((1-1) + 12) // 12 = 2020 + 0  = 2020     <- error aqui
mes  = ((1-1) + 12) % 12 + 1      = 11 + 1    = 12
```

**Por qué era falsa:** cometí dos errores aritméticos en la misma operación. `((1-1) + 12) // 12` es `12 // 12`, que vale **1**, no 0. Y `((1-1) + 12) % 12` es `12 % 12`, que vale **0**, no 11. Con las cifras correctas:

```
anio = 2020 + 1 = 2021
mes  = 0 + 1 = 1
aniversario = 2021-01-15   ->  igual al egreso, 0 días. Correcto.
```

La fórmula es correcta porque `(mes - 1 + meses) // 12` y `(mes - 1 + meses) % 12 + 1` **son el par coherente**: el índice base 0 reparte los meses entre año y mes, y el `+ 1` devuelve el mes calendario. No hay desfase.

**Verificación ejecutada:** se reprodujeron las líneas 29-42 con aritmética entera en shell sobre 12 casos, entre ellos los que un error de este tipo suele delatar.

| Ingreso → Egreso | Meses | Aniversario calculado | ¿Correcto? |
|---|---|---|---|
| 15/01/2020 → 15/01/2021 | 12 | 2021-01-15 | Sí |
| 31/12/2020 → 31/12/2021 | 12 | 2021-12-31 | Sí |
| 20/07/2019 → 20/07/2025 | 72 | 2025-07-20 | Sí |
| 29/02/2020 → 29/02/2024 | 48 | 2024-02-28 | Sí (bisiesto) |
| 31/01/2021 → 31/03/2022 | 14 | 2022-03-31 | Sí |
| 15/09/2020 → 14/08/2021 | 10 | 2021-07-15 | Sí |
| 31/03/2020 → 01/05/2020 | 1 | 2020-04-28 | Sí (ver abajo) |
| 31/01/2018 → 31/01/2026 | 96 | 2026-01-31 | Sí |

En **ningún** caso el aniversario cae después de la fecha de egreso, que es exactamente la condición que el hallazgo sostenía estar rota.

**El caso que sí merecía atención** es el 31/01/2020 → 01/05/2020: la fórmula produce `date(2020, 4, 31)`, que no existe. El `try/except ValueError` de [prestaciones.py:38-40](src/nomina/prestaciones.py#L38-L40) lo resuelve a `date(2020, 4, 28)`, y el resultado (1 mes + 3 días) es el correcto. Es decir: **el código tiene una defensa explícita para el caso de mes inexistente, y funciona.** Ese `try/except` es buena práctica, no un parche.

**Conclusión:** `meses_y_dias_entre()` es correcto. **No hay defecto de cálculo en el motor de nómina.** Se retira el hallazgo.

### H.2 — Doble llamada idéntica en el cálculo de vacaciones

**Observación:** `dias_vacaciones_pendientes()` invoca dos veces la misma función con los mismos argumentos y descarta media tupla cada vez.

| Línea | Código |
|---|---|
| `src/nomina/finiquito.py:161` | `_, dias = meses_y_dias_entre(fecha_ingreso, fecha_egreso)` |
| `src/nomina/finiquito.py:162` | `meses_servicio, _ = meses_y_dias_entre(fecha_ingreso, fecha_egreso)` |

**Efecto:** no es un defecto funcional —el resultado es idéntico—, pero el segundo cálculo es trabajo desperdiciado dentro de una función que corre al cerrar un contrato. El arreglo es una sola llamada desempaquetando ambos valores.

### H.3 — `_como_fecha` trunca a 10 caracteres sin avisar

**Observación:** el parser corta la cadena antes de validar el formato.

| Línea | Código |
|---|---|
| `src/nomina/finiquito.py:57` | `return datetime.strptime(texto[:10], formato).date()` |

**Lectura:** `texto[:10]` acepta `"2021-01-15 23:59:59"` (correcto) pero también trunca en silencio cualquier basura que comparta los diez primeros caracteres. Para los tres formatos que acepta —`%Y-%m-%d`, `%d/%m/%Y`, `%d-%m-%Y`— el corte es inofensivo porque esos formatos no llevan hora. Se registra porque es una asunción implícita: si mañana se añade un formato con hora, el truncado rompe. No es un defecto hoy.

### H.4 — Lo que está correcto en el motor

**Observación de conjunto:** tras leer los ocho módulos, estos puntos están bien resueltos y no requieren cambio:

| Módulo | Práctica correcta verificada |
|---|---|
| `src/nomina/tipos.py:63` | `redondear()` usa `ROUND_HALF_UP`, el criterio de recibo de pago |
| `src/nomina/tipos.py:36` | `a_decimal()` acepta formatos con coma o punto decimal y no lanza excepción |
| `src/nomina/isr.py:53` | `calcular_isr()` recorta el impuesto a la base para que la configuración inconsistente no produzca neto negativo |
| `src/nomina/seguridad_social.py:46` | `base_afectada()` trata techo cero como «sin techo», que es la convención de la configuración |
| `src/nomina/horas_extra.py:62` | `monto_por_recargo()` aplica `max(CERO, recargo)`, así un recargo negativo en configuración no resta dinero |
| `src/nomina/motor.py:139` | El neto se recorta a cero: nunca se genera un importe a cobrar |
| `src/nomina/parametros.py:141` | `validar_parametros()` detecta porcentajes fuera de 0-100 y tramos solapados |

**Excepto:** H.1 es el único defecto de cálculo encontrado, y está en `prestaciones.py`, no en el motor principal.

---

<a id="i"></a>
## I. Servicios, repositorios y sincronización — lectura línea por línea

Observaciones de la segunda pasada de lectura estricta (solo lectura, sin ejecutar código): `src/services/`, `src/repositories/` y `sync_agent/`. A diferencia de H, esta sección sí contiene defectos; ninguno de cálculo de nómina, pero dos con efecto sobre datos que se guardan.

### I.1 — La referencia «LIQ-» de una liquidación depende de un parámetro que la GUI no envía

**Observación (defecto real).**

| Ubicación | Contenido |
|---|---|
| `src/services/contrato_service.py:445-446` | `if registrado_por:` / `datos["referencia_pago"] = f"LIQ-{contrato.numero}"` |
| `src/services/contrato_service.py:274` | `registrado_por` en la firma, documentado como «Usuario que ejecuta la terminación» |
| `src/gui/contratos_frame.py:921-926` | La GUI llama `terminar_contrato(...)` sin `registrado_por` (ni `metodo_pago`) |
| `src/services/pago_service.py:118-120` | Si no llega `referencia_pago`, usa `_referencia_por_defecto` |
| `src/services/pago_service.py:284-287` | `_referencia_por_defecto()` devuelve `REC-<empleado>-<yyyymmdd>` |
| `tests/test_contratos.py:187-192` | El test sí pasa `registrado_por="admin"`, y no verifica `referencia_pago` |

**Efecto:** en el flujo real (botón «Terminar contrato» del módulo de contratos) la liquidación se guarda con referencia `REC-…`, no con la `LIQ-…` que el código reserva para ella. El parámetro `registrado_por` no se audita en ningún otro sitio: su único uso es habilitar el prefijo. El test que cubre la liquidación pasa el parámetro, por lo que el hueco no aparece en la suite.

**Lectura:** el defecto es la condicional. La intención evidente —docstring y nombre del parámetro— es que la referencia sea `LIQ-<número>` siempre y que el usuario quede auditado. La corrección tiene que decidir: (a) fijar la referencia sin condicional y auditar `registrado_por` como usuario del evento, o (b) eliminar el parámetro si no se va a usar. No ambas cosas a la vez.

### I.2 — Editar un pago prorrateado recalcula el salario completo

**Observación.** `crear_pago` respeta el prorrateo (toma `dias_trabajados`, `dias_periodo` y `prorratear` de los datos, y el motor los aplica), pero el recálculo de `actualizar_pago` arma un diccionario reducido que no los incluye.

| Ubicación | Contenido |
|---|---|
| `src/services/pago_service.py:337-346` | `datos_calculo` solo con bonificaciones, descuentos, otras deducciones, aguinaldo y bono vacacional |
| `src/services/pago_service.py:355-359` | `calcular_con_motor(..., datos=datos_calculo, ...)` |
| `src/nomina/motor.py:64-67` | El prorrateo solo ocurre si `entrada.prorratear` es verdadero |

**Efecto:** en un pago creado con prorrateo (p. ej. 15 días trabajados), editar cualquier campo del conjunto de cálculo (una bonificación, un descuento, el salario) recalcula con los valores por defecto de `EntradaNomina` (`dias_trabajados=30`, `dias_periodo=30`, `prorratear=False`) y el salario base vuelve al mes completo: el neto sube sin que nadie lo haya pedido. `actualizar_pago` nunca incorpora los días al recálculo, así que el formulario no puede evitarlo.

**Lectura:** corregir exige decidir de dónde salen los días al editar (persistirlos en `Pago`, recibirlos del formulario, o conservar el desglose existente). Es decisión de diseño, no un simple parche.

### I.3 — `actualizar_empleado` puede anular el salario y no protege la cédula vacía

| Ubicación | Contenido |
|---|---|
| `src/services/empleado_service.py:200-205` | `salario_base`, `peso` y `altura`: si llega cadena vacía, el valor se convierte en `None` |
| `src/services/empleado_service.py:210-214` | Bucle genérico `setattr`: aplica todo lo que venga en `datos` |
| `src/models/empleado.py:128` | `salario_base` es `nullable=False` |
| `src/services/empleado_service.py:186-193` | La validación de cédula solo actúa si `datos["cedula"]` es verdadero |
| `src/services/empleado_service.py:72-94` | `crear_empleado` no invoca `validar_datos_empleado` |

**Efecto:** un `""` en el campo salario del formulario de edición llega como `None` y se asigna; al no admitir nulos la columna, el `commit` falla y `base_repository` lo convierte en `ValueError("Error de integridad: la actualización viola restricciones")`, un mensaje que no explica cuál campo. Un caso análogo ocurre con la cédula vacía (queda `""`, no `NULL`, y el bucle genérico la asigna). Y como la validación «de formulario» vive en la GUI (`validar_datos_empleado`), cualquier llamada directa al servicio crea o actualiza sin pasar por ella.

**Lectura:** defensa en profundidad: decidir en el servicio si un vacío significa «no tocar» o «borrar», y validar los campos obligatorios también en `crear_empleado`.

### I.4 — `merge.decidir_campo` no refresca la marca cuando el valor llega idéntico

| Ubicación | Contenido |
|---|---|
| `sync_agent/merge.py:201-202` | `if entrante.valor == actual.valor: return DECISION_IGNORAR_IDENTICA` |
| `sync_agent/merge.py:238-241` | `planificar_campos` omite esa decisión: no devuelve valor ni marca |
| `sync_agent/aplicador.py` (`_aplicar_upsert` → `_registrar_campos`) | Solo persiste las marcas devueltas por el plan |
| `tests/test_sync_merge.py:98-100` | El atajo está congelado en una prueba |

**Efecto:** la marca local del campo se queda con la escritura vieja. Si después llega, fuera de orden, una escritura intermedia del mismo equipo, su clave supera a la marca vieja y **se aplica**, aunque el equipo remoto ya la había reemplazado por el valor idéntico. Resultado: divergencia entre equipos justo en el caso que el orden total busca evitar. Bajo impacto práctico (requiere reordenamiento de operaciones y valores repetidos), pero es una grieta real del invariante de convergencia.

**Lectura:** el arreglo consistente es que un valor idéntico más reciente actualice la marca sin escribir el valor (y que uno más antiguo se ignore). Corregirlo toca `tests/test_sync_merge.py`.

### I.5 — Vacaciones: dos criterios distintos para el mismo concepto

| Ubicación | Criterio |
|---|---|
| `src/services/contrato_service.py:376-395` | Cuenta APROBADO **y** COMPLETADO (días disfrutados del finiquito) |
| `src/services/incidencia_service.py:333-354` | Cuenta solo APROBADO (días que afectan nómina) |

**Efecto:** una incidencia de vacaciones que se marca COMPLETADA cuenta para las vacaciones disfrutadas del finiquito, pero deja de contar para el descuento de días de la nómina del periodo. Los dos números del sistema no cuadran entre sí para el mismo hecho.

**Lectura:** la observación es que hoy el sistema responde distinto a la misma pregunta según quién pregunte. Cuál de los dos criterios es el correcto es una decisión funcional, no técnica.

### I.6 — `ContratoRepository.get_estadisticas` carga filas para contarlas

| Ubicación | Contenido |
|---|---|
| `src/repositories/contrato_repository.py:182` | `vigentes = len(self.get_vigentes())` |
| `src/repositories/incidencia_repository.py` (`get_estadisticas_por_tipo`) | Documenta el mismo patrón ya corregido allí con `GROUP BY` |
| `src/repositories/pago_repository.py` (`get_estadisticas_por_tipo`, `get_estadisticas_por_metodo`) | También agregado en SQL |

**Efecto:** para un contador se hidratan todas las filas de contratos vigentes. Con el volumen de una institución es tolerable, pero el repositorio que ya documenta la corrección del mismo patrón en otra tabla mantiene aquí la versión ineficiente. Se corrige con un `count()` con los mismos filtros.

### I.7 — `previsualizar_deducciones` calcula la nómina dos veces; tres helpers harían una tercera

| Ubicación | Contenido |
|---|---|
| `src/services/pago_service.py:211-212` | `calcular_con_motor(salario_base)` y luego `_resolver_deducciones({}, salario_base)` |
| `src/services/pago_service.py:268-283` | `_resolver_deducciones` vuelve a llamar a `calcular_con_motor` |
| `src/services/pago_service.py:593-603` | `_calcular_deduccion_seguro`, `_calcular_deduccion_pension` y `_calcular_deduccion_impuesto`: cada una recalcularía toda la nómina |

**Efecto:** la vista previa hace dos cálculos completos donde basta uno. Los tres helpers privados no tienen ningún llamador en `src/` (la búsqueda no encuentra coincidencias fuera de su propia definición) y cada uno repetiría el cálculo completo. Es coste y código muerto, no un error de importes.

### I.8 — `ConfiguracionRepository.set_valor` falla en silencio

| Ubicación | Contenido |
|---|---|
| `src/repositories/configuracion_repository.py:34-45` | `try: … except Exception: self.session.rollback(); return False` |
| `src/repositories/configuracion_repository.py` | Declara un `logger` de módulo y no lo usa en ninguna rama |

**Efecto:** quien recibe `False` no puede distinguir «la clave no existe» de «la escritura falló», y la causa del fallo no queda en ningún log. Es el único repositorio auditado en esta pasada que captura sin registrar.

### I.9 — `get_by_id` audita cada lectura

| Ubicación | Contenido |
|---|---|
| `src/repositories/base_repository.py:79-100` | `get_by_id` llama `_log_data_operation("read", …)` tanto si encuentra como si no |
| `src/utils/audit_logger.py` | La auditoría escribe una línea JSON en archivos diarios, con `json.dumps`, chequeo de patrones y lista en memoria |

**Efecto:** cada lectura puntual agrega una entrada de auditoría de valor casi nulo (el `user` es `None` → «system») y el caso «no encontrado» se marca como fallo. En flujos que resuelven nombres fila a fila, eso es escritura de disco por fila. No es un defecto de datos: es ruido y coste.

**Cierre de la sección:** de las nueve observaciones, I.1 e I.2 son defectos con efecto sobre datos guardados (referencia de una liquidación y recálculo de un pago editado); I.4 es una grieta del invariante de convergencia de la sincronización; el resto son consistencia, rendimiento o diagnóstico.
