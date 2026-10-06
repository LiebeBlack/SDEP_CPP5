# Correcciones ejecutadas — SDEP_CPP5

**Fecha:** 2026-10-04
**Origen:** `OBSERVACIONES_CORRECCIONES.md` (inventario) y `PLAN_MAESTRO_SDP_CPP5.md` (fases).
**Método:** edición estática, sin ejecución. **No hay Python en la máquina** (el alias de Microsoft Store intercepta `python`; `py` no existe), así que **ninguna corrección fue verificada ejecutando la suite**. Cada edición sí se releyó después de aplicarla para comprobar coherencia sintáctica, y las pruebas existentes se revisaron antes de tocar su comportamiento.

> **Actualización (2026-10-06):** la verificación pendiente ya se ejecutó con CPython 3.15.0rc3 en Windows. El resultado, los defectos que destapó y lo que sigue abierto constan en **«Verificación ejecutada»**, al final de este documento.

> Regla de esta tabla: una fila vale como «aplicado» solo si el código quedó editado en disco; la columna «verificación» dice exactamente qué falta.

## Correcciones aplicadas

| # | Hallazgo | Archivo(s) | Cambio | Verificación pendiente |
|---|---|---|---|---|
| 1 | D.1 | `src/utils/security.py` | Quitado `"reportes"` de `MODULE_ACCESS`. Ya no hay módulo fantasma. | Suite / `test_permisos_modulos.py` |
| 2 | F.1 | `src/utils/helpers.py` | `log_message()` usa `logging` (nivel resuelto por nombre, mensaje diferido). Se conserva la firma. | Suite |
| 3 | F.2 | `tests/test_helpers.py` | El test de `log_message` pasó de `capsys` a `caplog` (sin este cambio la suite quedaba roja). | pytest |
| 4 | B.5 | `.env.example` | `APP_VERSION=3.0.1`. Además se quitaron **dos líneas basura `[TEMPLATE]`** que encabezaban el archivo (artefacto, sin referencias en el repositorio). | Revisión manual |
| 5 | B.1 | `README.md` | «25 archivos» → «27 archivos» de prueba. | Revisión manual |
| 6 | C.4 | `.gitignore` | Añadidos `*.db.gz`, `backups/` y `hang_stack.txt`. | Revisión manual |
| 7 | I.1 | `src/services/contrato_service.py` | La referencia de la liquidación es **siempre** `LIQ-<número>`; ya no depende de `registrado_por`. `_auditar()` acepta `usuario`, y `terminar_contrato` le pasa `registrado_por` para que quede auditado. | `test_contratos.py` (dos pruebas) |
| 8 | I.2 (parcial) | `src/services/pago_service.py` | `actualizar_pago` incorpora `dias_trabajados`, `dias_periodo` y `prorratear` al recálculo cuando el formulario los envía, y editar esos campos dispara recálculo. **Queda abierto** que `Pago` no persiste los días: un pago prorrateado por API y editado después sigue sin poder reconstruirlos (requiere columna/migración). | Suite |
| 9 | I.3 | `src/services/empleado_service.py` | `salario_base` vacío o no numérico en la edición falla con mensaje claro (antes se asignaba `None` y terminaba en «Error de integridad»); una cédula vacía se descarta en lugar de asignarse; los numéricos opcionales inválidos ya no pueden guardar texto. | `test_empleados.py` (dos pruebas) |
| 10 | I.4 | `sync_agent/merge.py`, `sync_agent/aplicador.py` | Un valor idéntico con marca más reciente **refresca la marca** (sin reescribir el valor) y el aplicador persiste ese refresco. Cierra la divergencia con operaciones fuera de orden. | `test_sync_merge.py` (dos pruebas) |
| 11 | I.5 | `src/services/incidencia_service.py`, `src/repositories/incidencia_repository.py` | Nómina y finiquito cuentan el mismo criterio (APROBADO + COMPLETADO). Para que COMPLETADO siempre signifique «aprobada y ocurrida», `completar()` solo completa desde APROBADO (antes completaba cualquier estado). **Cambio de comportamiento deliberado**: la GUI puede recibir `False` al completar una incidencia no aprobada. | Suite |
| 12 | I.6 | `src/repositories/contrato_repository.py` | `get_estadisticas` cuenta los vigentes con `COUNT` en SQL en lugar de hidratar filas. | Suite |
| 13 | I.7 | `src/services/pago_service.py` | `previsualizar_deducciones` calcula la nómina **una vez**; se eliminaron `_resolver_deducciones` y los tres `_calcular_deduccion_*` (sin llamadores). | Suite |
| 14 | I.8 | `src/repositories/configuracion_repository.py` | `set_valor` registra la excepción (`logger.exception`) antes de devolver `False`. | Suite |
| 15 | B.3 (parcial) | `tests/test_permisos_modulos.py` | Archivo nuevo: coherencia MODULOS ↔ FRAME_CLASSES ↔ MODULE_ACCESS, más un tope de nueve atajos documentado. | pytest |

## Tanda 2 — Fase 3 (GUI académica) y Fase 5 (sincronización)

| # | Fase | Archivo(s) | Cambio | Verificación pendiente |
|---|---|---|---|---|
| 16 | 3 | `src/gui/estudiantes_frame.py` (nuevo) | Módulo de **Estudiantes**: legajo (alta/edición/retiro/búsqueda/estadísticas/exportación) y pestaña de **Grados y matrículas** (grados, asignación de profesor, matrícula y retiro). Se implementa en un solo módulo porque el tope de `Ctrl+1..9` no permite tres frames nuevos. | `test_gui_smoke.py` (`TestModuloAcademico`) |
| 17 | 3 | `src/gui/notas_frame.py` (nuevo) | Módulo de **Calificaciones**: registro/edición/eliminación de notas con token académico, filtros, consolidado, boletín, acta y exportación; pestaña de **Periodos** (alta, edición, cierre y reapertura restringida a administrador). | `test_gui_smoke.py` |
| 18 | 3 | `src/gui/main_window.py` | `MODULOS`, `TITULOS_VENTANA` y `FRAME_CLASSES` con `estudiantes` (Ctrl+8) y `notas` (Ctrl+9); `METODOS_REFRESCAR/NUEVO` para F5 y Ctrl+N; guía rápida actualizada a `Ctrl+1..9`. Los módulos nuevos se añaden al final: `Ctrl+1..7` conserva su significado. | `test_permisos_modulos.py` (9 ≤ 9) |
| 19 | 3 | `src/utils/security.py` | `MODULE_ACCESS` con `estudiantes` (admin/manager/user/viewer) y `notas` (admin/manager/user). La escritura de notas la autoriza el **token** del servicio, no este mapa (un docente del rol `user` no tiene permiso `create`). | `test_permisos_modulos.py` |
| 20 | 3 | `tests/test_gui_smoke.py` | Navegación y tablas de los dos módulos nuevos, más `TestModuloAcademico`: el legajo lista al estudiante matriculado, las notas registran y muestran la calificación, los periodos se listan y la escala sale de la configuración (0–20, aprobatoria 10). | pytest |
| 21 | 5 | `sync_agent/registro.py` | `ENTIDADES` incorpora `estudiantes`, `periodos_academicos`, `grados`, `matriculas` y `notas_finales`; `tokens_sesion` queda **fuera** (credencial local) y se documenta en el propio registro. Nuevo campo `clave_natural_compuesta`: `(periodo_id, nombre, seccion)` para grados y `(estudiante_id, grado_id, materia)` para notas. | `tests/test_sync_academico.py` |
| 22 | 5 | `sync_agent/aplicador.py` | `_buscar_por_clave_compuesta`: unifica la fila local cuando el payload ya trae las claves foráneas traducidas a ids locales. Sin esto, una nota creada en dos puestos chocaba contra `uq_nota_estudiante_grado_materia` y no se aplicaba nunca. | `test_sync_integracion.py` (nota ajena) |
| 23 | 5 | `sync_agent/merge.py` | `notas_finales` entra en `CAMPOS_SENSIBLES` (`calificacion`): todo choque queda auditado aunque la regla general lo resuelva. | `test_sync_academico.py` |
| 24 | 5 | `tests/test_sync_academico.py`, `tests/test_sync_integracion.py` (nuevo/ampliado) | Registro de las cinco tablas (claves foráneas, baja lógica de matrículas, clave compuesta sobre columnas reales), más tres pruebas de integración contra el nodo central: la estructura académica viaja con las claves foráneas como UUID, un token de sesión no sale del equipo y una nota ajena se unifica por su clave compuesta sin duplicarse. | pytest |

## Tanda 2 — Fase 6 (documentación y portal)

| # | Hallazgo | Archivo(s) | Cambio | Verificación pendiente |
|---|---|---|---|---|
| 25 | B.2 | `NOTAS_DESARROLLO.md` | Nueva sección «Versión vigente: 3.0.1» (módulo académico, sincronización y correcciones de la auditoría, con la advertencia de que no se ha ejecutado la suite); pie del documento a 3.0.1. Las cifras de la sección 1.0.4 quedan marcadas como **históricas** en lugar de borrarse. | Revisión manual |
| 26 | B.1, B.6 | `README.md` | 32 archivos de prueba (eran 25 en la auditoría, 27 al corregirlos y 28 con la prueba de permisos de la tanda 1; la tanda 2 sumó los cuatro académicos), tabla de atajos `Ctrl+1..9`, sección del módulo académico y tablas de base de datos ampliadas. | Revisión manual |
| 27 | B.3, B.2 | `GUIA_USUARIO.md` | Sección «Módulos Académicos» (estudiantes, grados y matrículas, notas, tokens, cierre y reapertura de periodo), tabla de atajos a `Ctrl+1..9` y versión del sistema a 3.0.1. | Revisión manual |
| 28 | B.1, B.2 | `DOCUMENTACION_TECNICA.md`, `ESTRUCTURA_PROYECTO_COMPLETO.md` | Atajos a `Ctrl+1..9`; sección técnica del módulo académico (modelo, token, disparadores, sincronización); árbol de `ESTRUCTURA` corregido: archivos que no existen (`setup.py`, `build.spec`, `pytest.ini`, `.pylintrc.json`, `.black`, `.isort.cfg`, `.vscode/`), subcarpetas de `tests/` inexistentes y `assets/` real; sección de herramientas separada entre las que se usan y las evaluadas. | Revisión manual |
| 29 | F.2 | `docs/content/`, `docs/docs_data.js` | Las copias del portal quedaron sincronizadas por copia directa y el catálogo embebido se **reconstruyó desde el blob de `HEAD`** con un script Perl que reproduce al generador oficial: mismo formato y orden de claves, `ensure_ascii=False`, contenido CRLF→LF y `readingTime` con la regla de redondeo de Python. Comprobado con Perl: 20/20 entradas decodifican, sin ids duplicados, cada `content` es idéntico a su `.md` y `git diff` del catálogo son **15 líneas** (los tres campos recalculados de las cinco entradas editadas). **El portal debe regenerarse con la herramienta oficial** cuando haya intérprete. | `tools/verify_docs.py` + `tools/generate_docs_bundle.py` |
| 30 | B.2, F.2 | `docs/index.html`, `NOTAS_DESARROLLO.md` | Datos duros del portal corregidos contra la versión vigente y la suite real: `v3.0.0`→`v3.0.1` y «388 pruebas en 20 archivos»→**550 funciones en 32 archivos** (recuento estático), más una tarjeta «Módulo Académico» en la parrilla de módulos. Árbol de `NOTAS_DESARROLLO.md` alineado con el repositorio (módulos, modelos y servicios académicos; 32 archivos de prueba). | Navegador sobre el portal servido en local + relectura |

### Decisiones de diseño tomadas en esta tanda

- **Dos módulos académicos, no cuatro.** El plan preveía `academico_frame`, `estudiantes_frame`, `grados_frame` y `notas_frame`; con siete módulos previos, tres frames nuevos superan el tope de nueve atajos directos y el cuarto módulo quedaría sin `Ctrl+N`. La interfaz se resolvió con dos módulos por pestañas que dejan **todos** los datos alcanzables dentro del tope, sin romper ningún atajo existente.
- **Claves naturales compuestas.** La identidad global no admite una clave de varias columnas cuando alguna es una clave foránea, porque los ids locales no significan lo mismo en dos equipos. Se implementó una clave compuesta que se evalúa **solo en el receptor**, con el payload ya traducido a ids locales, y se mantuvo la clave natural simple (cédula, nombre de periodo) para la adopción de identidad entre equipos.
- **Los tokens de sesión no viajan.** Son credenciales del equipo: replicar su vigencia y alcance no aporta nada y amplía la superficie de exposición.

> **Limitación vigente:** nada de esta tanda se pudo ejecutar. La unificación por clave compuesta reasigna la identidad local de la fila (mismo comportamiento que la clave natural simple) y, si dos puestos crean la misma nota antes de sincronizar, el nodo central conserva ambas filas hasta que cada puesto unifique la suya; queda anotado para revisión con la suite en marcha.

## Correcciones añadidas a las pruebas (regresión)

- `tests/test_contratos.py`: la liquidación existente ahora verifica `referencia_pago == LIQ-<número>`; prueba nueva del flujo **sin** `registrado_por` (el caso real de la GUI).
- `tests/test_empleados.py`: salario vacío falla y no anula; cédula vacía no se asigna.
- `tests/test_sync_merge.py`: la marca se refresca con valor idéntico más reciente, y el caso de convergencia con valor idéntico adelantado (antes divergía).

## No ejecutado (requiere decisión o entorno)

| Asunto | Motivo |
|---|---|
| Fase 1 — `git rm --cached hang_stack.txt` y `git rm -r --cached backups` | Es una operación de índice Git; el historial no se reescribe y la decisión es del responsable. No se ejecutó ningún comando git. |
| Fase 3–5 — GUI académica, pruebas y sincronización de tablas académicas | **Ejecutada** en la tanda 2 (dos módulos con pestañas, tres archivos de pruebas y las cinco tablas sincronizadas). Su verificación con la suite sigue pendiente por falta de intérprete. |
| Fase 6 — cifras medidas de pruebas y cobertura (`NOTAS_DESARROLLO.md` y documentación derivada) | Depende de medir la suite (Fase 0), imposible sin intérprete. Las desviaciones del Hallazgo B y la documentación del módulo académico sí quedaron corregidas; el portal se regeneró por script y falta el paso oficial (`python tools/generate_docs_bundle.py`). |
| I.2 completo (persistir días/prorrateo en `pagos`) | Requiere migración de esquema y columnas de sincronización; no se hace sin poder ejecutar las migraciones. |
| I.9 (auditar lecturas en `get_by_id`) | Es política de auditoría, no un defecto; se deja como decisión. |

## Verificación recomendada (cuando haya Python)

```bash
python -m pytest tests/test_permisos_modulos.py tests/test_helpers.py tests/test_contratos.py tests/test_empleados.py tests/test_sync_merge.py -q
python -m pytest tests/test_gui_smoke.py tests/test_academico.py tests/test_notas.py tests/test_tokens_sesion.py tests/test_sync_academico.py tests/test_sync_integracion.py -q
python -m pytest tests/ -q
python -m flake8 src sync_agent tests
python tools/verify_docs.py
```

**Advertencia honesta:** hasta que esos comandos no se ejecuten, las correcciones son estáticamente razonadas, no verificadas. Cualquier fallo que aparezca debe reportarse como regresión de esta tanda, no maquillarse.

---

# Verificación ejecutada

**Fecha:** 2026-10-06
**Entorno:** Windows, CPython 3.15.0rc3, SQLAlchemy 2.1.3, customtkinter 6.0.0,
reportlab 5.0.1, Pillow 12.3.0, openpyxl 3.1.5, pytest 9.1.1.
**Instalación del intérprete:** `uv python install 3.15` (sin tocar el sistema);
las dependencias se instalaron en un entorno virtual local del repositorio.

## Resultado de la suite

| Comprobación | Resultado |
|---|---|
| `pytest tests/` | **551 pruebas, 32 archivos: 551 exitosas, 0 fallos, 0 errores** (200 s) |
| Cobertura total (`--cov=src`) | **56 %** (13.464 sentencias, 5.908 sin cubrir) |
| Cobertura de `src/services` | **76 %** |
| Cobertura de `src/nomina` | **89 %** |
| `flake8 src sync_agent updater tools build.py` | sin hallazgos |
| `black --check` (131 archivos) | sin cambios pendientes |
| `isort --check-only` | sin cambios pendientes |
| `mypy src sync_agent updater tools build.py` | **sin errores en 98 archivos** |
| `tools/verify_docs.py` | todos los chequeos pasan |
| `tools/generate_docs_bundle.py` | regenera `docs/` de forma idempotente |
| `python src/main.py --selftest` | código de salida **0** (base nueva y base con esquema anterior de matrículas) |

## Defectos que solo aparecieron al ejecutar

Ninguno de estos se veía por lectura estática; todos están corregidos y con prueba.

| # | Síntoma | Causa | Corrección |
|---|---|---|---|
| 1 | **76 errores en cascada** en casi todos los archivos de prueba | `_reset_database` borraba todo en una transacción; los disparadores de inmutabilidad abortaban el `DELETE` de `notas_finales` de un periodo cerrado y **revertían el reseteo completo**, dejando filas de la prueba anterior | `tests/conftest.py`: reabrir los periodos antes de vaciar |
| 2 | `test_notas` caía tras cerrar un periodo | mismo que el anterior (se reproducía incluso con el archivo aislado) | mismo |
| 3 | El módulo de **Notas** abría sin grado seleccionado | el selector de periodo nacía en `"Todos"`, que es un valor válido, así que la comprobación `get() not in valores` nunca elegía el año en curso | `src/gui/notas_frame.py`: selección inicial vacía |
| 4 | Retirar y volver a matricular fallaba con violación de unicidad | restricción `UNIQUE (estudiante_id, grado_id)` global; una matrícula retirada (`activa = 0`) bloqueaba la nueva | índice **parcial** (`WHERE activa = 1`) + migración `migrar_matriculas_unicidad_activa`, con prueba en `test_migraciones.py` |
| 5 | `test_backup_corrupto_detectado` no encontraba el archivo | la prueba usaba la ruta cruda de los metadatos, que hoy es **relativa** al almacén (a propósito, para no exponer rutas del equipo) | `tests/test_backups.py`: componer la ruta con el directorio del gestor |
| 6 | El test de fechas invertidas no ejercitaba la regla | los datos del caso (`30/06/2026` → `01/09/2026`) **no estaban invertidos** | `tests/test_academico.py`: invertir el dato |
| 7 | `flake8`: 4 `F824` en los módulos académicos | `nonlocal fila` declarado sin asignación dentro de la función | `src/gui/estudiantes_frame.py`, `src/gui/notas_frame.py` |
| 8 | `mypy`: 6 errores | tres variables sin anotación en `pago_service`, un `Any` en `notas_frame`, `os.getuid` (solo POSIX) en `settings.py` y un `Path` inferido como `Any` en `backup_manager` | anotaciones, `bool(...)`, `getattr(os, "getuid", None)` y `path: Path` |
| 9 | `black`/`isort`: 69 archivos por formatear y 15 con importaciones desordenadas | nunca se habían ejecutado (hallazgo G.1) | `black` + `isort` sobre todo el árbol |
| 10 | **Error de importación** tras pasar `isort` | reordenó `src/config/__init__.py`, cuya dependencia de orden era implícita | `database.py` importa la **instancia** desde `src.config.settings` (sin depender del orden) |
| 11 | `test_migraciones.py` fallaba **al ejecutarse solo** | las migraciones crean un respaldo previo y el archivo de la base de la suite no existía | fixture autouse que inicializa la base |
| 12 | Fuga de conexiones: `QueuePool ... timeout` en pruebas GUI tardías | el fixture de ventana principal nunca cerraba la sesión propia de la ventana (el cierre real usa `_cleanup`) | `tests/test_gui_smoke.py`: llamar a `_cleanup()` al desmontar |

## Lo que sigue abierto (decisión del responsable)

| Asunto | Por qué no se hizo aquí |
|---|---|
| `hang_stack.txt` y `backups/` siguen **rastreados** en Git | Retirarlos del índice (`git rm --cached`) cambia el índice del repositorio y el historial no se reescribe; el `.gitignore` ya los excluye. Es una operación de Git que decide el responsable. |
| I.2 completo (persistir días y prorrateo en `pagos`) | Requiere columnas nuevas y migración de esquema. |
| I.9 (auditar lecturas en `get_by_id`) | Es política de auditoría, no un defecto. |
| I.5 (criterio único de vacaciones) | Decisión funcional: qué debe contar para nómina y para finiquito. |
