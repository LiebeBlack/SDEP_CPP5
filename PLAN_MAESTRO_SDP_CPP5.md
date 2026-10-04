# Plan maestro SDEP_CPP5 — Completar, corregir, refinar y afinar

**Proyecto:** Sistema de Gestión de Personal y Nómina para Instituciones Educativas
**Versión declarada:** 3.0.1 (fuente única: el archivo `VERSION`)
**Fecha de la auditoría:** 2026-10-04
**Alcance:** correcciones y adiciones. **Sin refactor estructural**: no se reorganiza `src/gui/frames.py`, ni los patrones de logging, ni los `try/except` anidados existentes.
**Método:** auditoría estática por lectura directa del código. Ninguna cifra de este documento procede de un documento previo; las que no se pudieron medir están marcadas como **no medidas**.

Este documento tiene dos partes. La **Parte 1** es el informe de auditoría: qué está mal hoy, con referencia `archivo:línea`. La **Parte 2** son las siete fases de ejecución, cada una con criterio de aceptación y comandos de verificación.

---

# PARTE 1 — INFORME DE AUDITORÍA

## 0. Resumen ejecutivo

El núcleo del sistema está sano, y conviene decirlo con precisión porque condiciona todo lo demás. La arquitectura en capas es real y se respeta en todo el árbol. La aritmética de nómina usa `Decimal` con `ROUND_HALF_UP` de principio a fin, incluido el redondeo bancario comercial en `src/nomina/tipos.py:63`. Las migraciones de esquema son idempotentes y verificadas por `tests/test_migraciones.py`. El motor de sincronización tiene un modelo de conflictos sobrio, con reglas nombradas y campos sensibles declarados. El CI prueba, compila para Windows y Linux y publica releases firmadas.

Los problemas **no están en el núcleo**. Están exactamente en dos sitios:

1. **En lo que quedó a medio construir.** Un subdominio académico completo —2.530 líneas de modelos, repositorios y servicios, con autorización por token, cierre de periodos, boletines y actas— que **ningún usuario puede alcanzar**. No hay interfaz, no hay pruebas, no se sincroniza y no aparece en la documentación. La capa de datos está terminada; la de presentación no existe.
2. **En lo que quedó viejo.** Documentación que afirma cifras y comportamientos que el código ya no tiene, más residuos de una sesión de depuración versionados como si fueran código.

Ninguno se resuelve con un parche local. El primero decide el valor de las 2.530 líneas existentes; el segundo decide si el sistema puede seguir documentándose sin información falsa.

## 1. Magnitud del código

| Métrica | Valor |
|---|---|
| Archivos Python en `src/` | 75 |
| Líneas en `src/` | 26.759 |
| Funciones y métodos | 1.934 |
| Archivos de prueba (`tests/test_*.py`) | 27 |
| Pruebas automatizadas | **no medida** (ver Fase 0) |
| Cobertura | **no medida** (ver Fase 0) |
| Subdominio académico completo | ~2.530 |

## 2. Hallazgo A — Subdominio académico huérfano (CRÍTICO)

### 2.1 Qué existe y está bien construido

Seis modelos, todos exportados en `src/models/__init__.py`, por lo que `Base.metadata.create_all` los crea en cada arranque sin tocar nada más:

| Modelo | Tabla | Clave natural para sincronización |
|---|---|---|
| `src/models/estudiante.py:43` | `estudiantes` | `cedula` (única, indexada — `estudiante.py:48-49`) |
| `src/models/grado.py:40` | `grados` | `(periodo_id, nombre, seccion)` — único compuesto en `grado.py:43` |
| `src/models/matricula.py:35` | `matriculas` | estudiante + grado |
| `src/models/nota_final.py:36` | `notas_finales` | `(estudiante_id, grado_id, materia)` |
| `src/models/periodo_academico.py:37` | `periodos_academicos` | año / nombre del periodo |
| `src/models/token_sesion.py:42` | `tokens_sesion` | **no replicar** (ver Fase 5) |

Tres servicios completos sobre ellos:

- **`src/services/academico_service.py`** — 30 métodos. CRUD de estudiantes, búsqueda, estadísticas, alta y estado de periodos, cierre y reapertura de periodo, grados y secciones, asignación de profesor, matrícula y retiro.
- **`src/services/nota_service.py`** — 28 métodos. Registro y actualización de notas, carga por lotes, escala y nota aprobatoria desde configuración, consolidado de periodo, promedio, datos de boletín y datos de acta.
- **`src/services/token_sesion_service.py`** — 9 métodos. `emitir` (línea 56, genera con `secrets.token_urlsafe`), `validar`, `revocar`, `revocar_usuario`, `limpiar_expirados`, `puede_escribir`, `tokens_vigentes`.

### 2.2 Qué lo respalda desde la infraestructura

- **Configuración ya sembrada:** `nota_minima` (0), `nota_maxima` (20) y `nota_aprobatoria` (10) en `src/config/database.py:479-500`, categoría `academico`. `NotaService.escala()` y `nota_aprobatoria()` las leen; no hay que inventar parámetros.
- **Protección a nivel de base de datos ya instalada:** tres triggers SQLite en `src/config/database.py:553-600` abortan con `RAISE(ABORT, ...)` cualquier `INSERT`, `UPDATE` o `DELETE` sobre `notas_finales` cuyo grado pertenezca a un periodo cerrado. Se recrean en cada arranque con `CREATE TRIGGER IF NOT EXISTS` y viajan dentro del archivo SQLite, de modo que siguen activos tras restaurar un respaldo.
- **Autorización por token ya resuelta:** `_exigir_token`, `_autorizar` y `_autorizar_sesion` en `nota_service.py:455-488`, con alcance por grado vía `TokenSesionService.puede_escribir`.

### 2.3 Qué falta

- **Interfaz gráfica: ausente por completo.** `grep -rl "Estudiante\|Grado\|Matricula\|NotaFinal\|PeriodoAcademico" src/gui` no devuelve **ningún** archivo. `MODULOS` (`main_window.py:40`), `TITULOS_VENTANA` (`:50`) y `FRAME_CLASSES` (`:60`) no los mencionan.
- **Pruebas: ausentes por completo.** Ningún archivo de `tests/` importa `academico_service`, `nota_service` ni `token_sesion_service`.
- **Sincronización: ausente.** `ENTIDADES` en `sync_agent/registro.py:68-105` replica seis tablas —`empleados`, `documentos`, `incidencias`, `contratos`, `pagos`, `configuraciones`— y ninguna es académica.
- **Documentación: ausente.** Ningún `.md` de la raíz ni de `TESIS/` nombra estudiantes, grados, matrículas ni notas, pese a que el proyecto es para instituciones educativas.

### 2.4 Por qué importa

Es el único hallazgo con capacidad de cambiar el valor del proyecto. Las 2.530 líneas no son un pasivo: son la mitad funcional de un sistema de gestión institucional, escritas con el mismo rigor que el resto —validación defensiva, auditoría en cada operación, autorización por token, protección a nivel de motor—. Pero código inalcanzable desde la interfaz no es producto: es deuda con documentación de código.

La contraste es incómoda: la base de datos de **todos** los usuarios tiene la configuración de calificaciones sembrada y los triggers activos, sobre tablas que nadie llena jamás. El sistema paga el coste de la protección y nunca cobra el beneficio de la función.

## 3. Hallazgo B — Documentación que contradice al código

| Ubicación | Afirma | Realidad verificada |
|---|---|---|
| `README.md:116` | «25 archivos» de prueba | 27 (`tests/test_*.py`) |
| `NOTAS_DESARROLLO.md:803` | Versión 3.0.0 | `VERSION` = 3.0.1 |
| `GUIA_USUARIO.md:645` | Versión 3.0.0 | 3.0.1 |
| `NOTAS_DESARROLLO.md:694` | Atajos `Ctrl+1..6` | 7 módulos en `MODULOS` |
| `NOTAS_DESARROLLO.md:727` | 295 pruebas, 57 % de cobertura | No reproducible; Fase 0 debe medir |
| `.env.example:15` | `APP_VERSION=1.0.4` | 3.0.1 |

El caso de `.env.example` es el más peligroso de los seis. `Settings.__init__` da prioridad a la variable de entorno (`self.app_version = os.getenv("APP_VERSION") or ...`), así que quien copie el archivo tal cual fija la versión y el rótulo `v1.0.4` aparece en la cabecera de la aplicación con un código 3.0.1.

## 4. Hallazgo C — Residuos de desarrollo versionados

- **`hang_stack.txt`** — traza de un cuelgue de 15 s en `messagebox.showwarning` dentro de `_show_frame`, invocado desde `tests/test_gui_smoke.py:212`. El defecto **ya está corregido**: el test ahora hace `monkeypatch` de `showwarning` en `tests/test_gui_smoke.py:249`. El archivo sigue en el repositorio, añadido en el commit `4d51772` («4.7»), como documentación de un bug que ya no existe. Un `messagebox` modal que bloquea es exactamente lo que hace colgar una suite en CI, y el rastro de ese cuelgue no aporta nada que el test no documente ya.
- **`backups/`** — cuatro bases de datos comprimidas reales (`auto_shutdown.db.gz`, `initial_setup.db.gz`, `test_security.db.gz` y una más) más `backup_metadata.json`, que contiene **rutas absolutas del equipo del desarrollador** (`C:\Users\L\Documents\GitHub\SDEP_CPP5\backups\...`) y checksums de su base personal. `.gitignore` excluye `*.db` pero **no** `*.db.gz`, por lo que pasaron el filtro. Un respaldo puede contener datos personales de empleados: es material que no debería viajar en el historial de Git, porque el historial es permanente aunque el archivo se borre hoy.

## 5. Hallazgo D — Módulo fantasma en el mapa de permisos

`src/utils/security.py:406` declara, dentro de `MODULE_ACCESS` (líneas 399-407):

```python
"reportes": ("admin", "manager", "viewer"),
```

No existe ningún `reportes` en `MODULOS` ni en `FRAME_CLASSES`. El mapa es la fuente de verdad del control de acceso y `modulos_conocidos()` (línea 412) lo expone como módulo válido, de modo que el sistema cree proteger un módulo inexistente. «Reportes» sí aparece en el código, pero solo como el permiso de acción `"report"` que usan los generadores de PDF dentro de cada frame (`frames.py:910`, `:938`, `:2028`, `:2639`) — es una capacidad, no un módulo. Esa ambigüedad es precisamente lo que hace probable que alguien lo reintroduzca.

El caso inverso ya está bien resuelto y conviene preservarlo: `can_access_module` es *fail-closed* (línea 449) y `main_window.py:274-279` avisa en el arranque si un módulo del menú no tiene permiso declarado. Ese mecanismo funciona; lo que falta es limpiar el entry sobrante y blindar la coherencia con un test.

## 6. Hallazgo E — Cobertura de pruebas ausente

| Componente | Archivos de prueba que lo mencionan |
|---|---|
| `AcademicoService` | 0 |
| `NotaService` | 0 |
| `TokenSesionService` | 0 |
| `src/gui/widgets/graficos.py` | 0 |

Lo que queda sin verificar es lo más delicado del sistema: un motor que calcula notas de corte y un trigger que aborta operaciones para proteger datos inmutables. `TokenSesionService.emitir` genera credenciales con `secrets.token_urlsafe` y nadie prueba que un token expirado deje de validar.

## 7. Hallazgo F — Higiene menor

- **`src/utils/helpers.py:598`** — `log_message()` escribe con `print()` en vez de `logging`. Es el único `print()` en `src/`; los de `sync_agent/__main__.py` y `updater/` son legítimos por ser interfaces de línea de comandos. **Advertencia verificada:** el test `tests/test_helpers.py:228-231` captura stdout con `capsys` y afirma `"[WARNING]" in captured.out`. Migrar a `logging` **rompe ese test**, porque `logging` no escribe a stdout por defecto. La corrección exige actualizar el test para usar `caplog` además de cambiar la función; no basta con el cambio en `helpers.py`.
- **`docs/content/`** es una copia de los `.md` de la raíz y se desincroniza sola: `docs/content/README.md` mide 16.560 bytes contra 16.562 del original. Se regenera con `tools/generate_docs_bundle.py`.

---

# PARTE 2 — PLAN DE EJECUCIÓN

## Fase 0 — Línea base verificable

**Objetivo:** ninguna cifra de este plan se acepta por herencia. Se mide.

```bash
python -m pytest tests/ -q 2>&1 | tail -5
python -m pytest tests/ -q --cov=src --cov-report=term 2>&1 | tail -30
```

Registrar en este documento el número real de pruebas y el porcentaje real de cobertura, y reemplazar las cifras heredadas de `NOTAS_DESARROLLO.md:727`.

**Criterio de aceptación:** las cifras registradas provienen de una ejecución real, con su comando y su salida, no de un documento previo.

**Nota:** si la auditoría revela un fallo heredado, se reporta como hallazgo de Fase 0 y se decide antes de continuar. No se maquilla ni se salta. Sin Python disponible en la máquina de auditoría, esta fase es la primera que debe ejecutarse en un entorno con intérprete.

## Fase 1 — Higiene del repositorio

**Objetivo:** que el repositorio contenga solo código y documentación.

```bash
git rm --cached hang_stack.txt
git rm -r --cached backups
```

Añadir a `.gitignore`:

```
backups/
*.db.gz
hang_stack.txt
```

**Criterio de aceptación:** `git ls-files backups hang_stack.txt` devuelve vacío; la suite sigue verde. Los archivos permanecen en disco para el desarrollador (`--cached` no borra del disco).

**Decisión que corresponde al responsable del proyecto:** sacar los archivos del índice no los borra del historial. Si las bases comprimidas contienen datos personales reales, la medida completa exige además reescribir el historial —`git filter-repo`— o publicar un nuevo clon. Eso es destructivo y **no** se ejecuta sin autorización expresa. Esta fase solo usa `git rm --cached`.

## Fase 2 — Correcciones de código

**Objetivo:** cuatro cambios acotados, sin tocar estructura.

1. **Eliminar el módulo fantasma.** Quitar `"reportes"` de `MODULE_ACCESS` en `src/utils/security.py:406`.

2. **Migrar `log_message()` a `logging`, con su test.** Conservar la firma pública `(message, level="INFO") -> None`. Como `tests/test_helpers.py:228-231` captura stdout con `capsys`, **el test debe cambiarse a `caplog`** y afirmar sobre el registro, no sobre `captured.out`. El cambio en `helpers.py` y el cambio en el test son un solo trabajo: hacer solo el primero deja la suite roja.

3. **Test de coherencia del mapa de permisos.** Archivo nuevo `tests/test_permisos_modulos.py` que falle si se cumple cualquiera de estas:
   - un módulo de `MODULOS` no está en `FRAME_CLASSES`;
   - un módulo de `MODULOS` no está en `MODULE_ACCESS` y tampoco en `MODULOS_SIN_CONTROL_DE_ACCESO`;
   - `modulos_conocidos()` no coincide exactamente con el conjunto de módulos de `MODULOS` menos los exentos.

   Este test convierte el Hallazgo D en un defecto que no puede reaparecer. La tercera condición es la que detecta exactamente el caso de `"reportes"`.

4. **`.env.example`** a la versión real y `README.md:116` a 27 archivos. Se hace aquí porque es corrección de configuración y de dato verificable, no de redacción.

**Criterio de aceptación:** el test de coherencia pasa; `tests/test_helpers.py` pasa con `caplog`; `flake8` limpio; ningún otro test cambia de resultado.

## Fase 3 — Módulo académico: interfaz gráfica

**Objetivo:** hacer alcanzable desde el producto lo que ya existe en la capa de datos.

Archivos **nuevos**, siguiendo el patrón de `src/gui/contratos_frame.py`:

| Archivo | Contenido |
|---|---|
| `src/gui/academico_frame.py` | `PeriodosFrame`: alta de periodo, estado, cierre con token, reapertura restringida a admin |
| `src/gui/estudiantes_frame.py` | CRUD, búsqueda, filtros por nivel, estadísticas |
| `src/gui/grados_frame.py` | Grados y secciones, asignación de profesor, matrícula y retiro |
| `src/gui/notas_frame.py` | Registro por grado, carga por lotes, consolidado, boletín, acta |

**Cableado** en `src/gui/main_window.py`:
- `MODULOS` (línea 40), `TITULOS_VENTANA` (línea 50), `FRAME_CLASSES` (línea 60)
- `PermissionChecker.MODULE_ACCESS` en `src/utils/security.py:399-407` (el mapa completo, al que hay que añadir las entradas nuevas junto a las existentes)
- `METODOS_REFRESCAR` (línea 610), `METODOS_NUEVO` (línea 621) y `METODOS_GUARDAR` (línea 631) para que F5, Ctrl+N y Ctrl+S funcionen en los módulos nuevos

**Restricción dura — el tope de nueve.** La numeración de `Ctrl+1..9` se deriva de `enumerate(MODULOS, start=1)` en `main_window.py:652`, no de un mapa propio. Con 7 módulos actuales, agregar 3 lleva la lista a 10 y el décimo cae en el `break` de la línea 653, quedándose sin atajo directo. El plan, por tanto:
- prioriza **dos** módulos de interfaz nuevos (`estudiantes` y `notas`, los de mayor valor: el legajo del estudiante y el registro de calificaciones),
- declara `academico` (periodos y grados) como el tercero solo si la suite sigue verde,
- y en cualquier caso documenta explícitamente en la guía qué módulos tienen atajo directo y cuáles no.

No se rompe ningún atajo existente: `Ctrl+1..7` siguen significando exactamente lo mismo.

**Criterio de aceptación:**
- Test de humo de GUI que instancia y navega los módulos nuevos, siguiendo el patrón de `test_navegacion_todos_los_modulos` en `tests/test_gui_smoke.py:136`.
- Test explícito del límite de atajos: si `len(MODULOS) > 9`, el test falla y obliga a documentar qué módulo quedó fuera.
- El aviso de `main_window.py:274-279` no se dispara para ningún módulo nuevo.
- Los cuatro frames exponen los atributos que `main_window.py` espera: `tree`, `search_entry` o un combobox para Ctrl+F, y el método canónico de recarga.

## Fase 4 — Módulo académico: pruebas

Archivos nuevos: `tests/test_academico.py`, `tests/test_notas.py`, `tests/test_tokens_sesion.py`.

Cobertura obligatoria:

1. Unicidad de cédula de estudiante (rechazo de duplicado) — la restricción está en la base (`estudiante.py:48-49`, `unique=True`), el test debe probarla contra la base real, no contra un `if` del servicio.
2. Cierre de periodo bloqueando el registro de notas — **por dos vías**: la regla del servicio *y* el trigger SQLite. El trigger se prueba con SQL directo (`INSERT`/`UPDATE`/`DELETE` crudos), porque existe precisamente para cubrir lo que el servicio no controla; si solo se prueba la vía del servicio, no se verifica la garantía real.
3. Reapertura de periodo restringida a administrador.
4. `TokenSesionService`: emisión con alcance, validación, expiración, revocación, `puede_escribir` por grado.
5. Escala y nota aprobatoria leídas de la configuración (0–20, aprobatoria 10).
6. Consolidado de boletín y datos de acta.
7. `limpiar_expirados`.

**Criterio de aceptación:** los tres archivos pasan; la cobertura medida en Fase 4 supera la de Fase 0 y el número queda registrado en este documento.

## Fase 5 — Módulo académico: sincronización

**Objetivo:** que los datos académicos viajen entre puestos sin filtrar secretos ni permitir reescribir notas cerradas.

1. **Registrar** en `ENTIDADES` (`sync_agent/registro.py:68`) `estudiantes`, `periodos_academicos`, `grados`, `matriculas` y `notas_finales`, con las claves naturales de la tabla de la sección 2.1.
2. **`tokens_sesion`: local por equipo, nunca replicado.** Un token es una credencial: `emitir` genera con `secrets.token_urlsafe` y solo se guarda su hash. Replicar la fila **no** filtra el token en claro (eso es correcto), pero sí replica el alcance y la vigencia de sesiones que no tienen sentido fuera del equipo. Queda explícitamente **fuera** de `ENTIDADES`, junto al patrón de `COLUMNAS_LOCALES` (`registro.py:24`) para las columnas que no viajan.
3. **`notas_finales` en `CAMPOS_SENSIBLES`** (`sync_agent/merge.py:54`). Sin esta entrada, un choque resuelto por marca temporal podría reescribir una nota de un periodo ya cerrado, saltándose el trigger a propósito. Es el único punto de toda la Fase 5 con consecuencia sobre datos reales.
4. **Actualizar `tests/conftest.py::_reset_database`** para limpiar las tablas nuevas entre pruebas, junto al bloque que ya limpia las del agente.

**Criterio de aceptación:**
- Test de integración que sincronice un registro académico entre dos bases y verifique el resultado en ambas.
- Test que verifique que un `token_sesion` **nunca** sale del equipo emisor.
- Test que verifique que un choque en `notas_finales` queda registrado como conflicto sensible.

## Fase 6 — Documentación y portal

**Objetivo:** que ningún documento afirme algo que el código no haga.

1. Corregir las desviaciones de la tabla del Hallazgo B, con las cifras medidas en Fase 0 y Fase 4.
2. Documentar el módulo académico en `README.md`, `GUIA_USUARIO.md`, `DOCUMENTACION_TECNICA.md` y `ESTRUCTURA_PROYECTO_COMPLETO.md`: qué es, quién puede acceder, qué significa cerrar un periodo y qué queda bloqueado.
3. Actualizar las tablas de atajos de `GUIA_USUARIO.md:593` y `DOCUMENTACION_TECNICA.md:353` según los módulos finales, indicando sin ambigüedad qué números tienen atajo directo.
4. Regenerar el portal: `python tools/generate_docs_bundle.py`.

**Criterio de aceptación:** `python tools/verify_docs.py` pasa; ninguna cifra de la documentación contradice lo que el código hace.

## Fase 7 — Verificación de cierre

```bash
python -m pytest tests/ -q
python -m flake8 src sync_agent updater tools tests
python -m black --check src sync_agent updater tools tests
python -m isort --check-only src sync_agent updater tools tests
python -m mypy src
python build.py --exe
python tools/verify_docs.py
```

**Criterio de aceptación:** todo en verde, o la limitación documentada de forma explícita como limitación.

Reglas que no se negocian:
- Ningún check se omite.
- Ningún assert se debilita.
- Ningún `except` se amplía para tragarse un fallo.
- Ninguna supresión de tipo o de lint se añade para forzar el paso. Si una supresión es realmente necesaria, se explica por qué en este documento y se verifica el comportamiento que suprime.
- Los checks filtrados por `tail` conservan el código de salida del comando probado (`set -o pipefail`), porque un filtro que imprime verde no es un check verde.

---

## Riesgos declarados

| Riesgo | Impacto | Mitigación |
|---|---|---|
| La Fase 3 es el grueso del trabajo | Alto | Es la fase que decide el valor de las 2.530 líneas existentes; se entrega primero y en incrementos verificables |
| Pasar de 7 a 9+ módulos agota `Ctrl+1..9` | Medio | Tope explícito en Fase 3 y test que obliga a documentar qué módulo se queda sin atajo |
| Replicar `notas_finales` sin `CAMPOS_SENSIBLES` | **Alto** | Un merge por marca podría reescribir una nota de periodo cerrado; es el entry de `merge.py:54` |
| Réplica de `tokens_sesion` | **Alto** | Publica alcance y vigencia de sesiones locales fuera del equipo; queda fuera de `ENTIDADES` |
| `git rm --cached` no borra del historial | Medio | Las bases siguen en commits antiguos; reescribir el historial requiere autorización expresa |
| Migrar `log_message` sin tocar su test | Medio | `capsys` → `caplog` es parte del mismo cambio, o la suite queda roja |
| La auditoría fue estática y sin Python | Medio | Fase 0 mide por primera vez; cualquier fallo heredado se reporta antes de avanzar |

---

## Orden de ejecución y dependencias

```
Fase 0  (medir)
   ↓
Fase 1  (higiene) ── independiente
   ↓
Fase 2  (código + test de coherencia)
   ↓
Fase 3  (GUI académica) ── depende de Fase 2 para el mapa de permisos
   ↓
Fase 4  (tests académicos) ── puede empezar en paralelo con Fase 3
   ↓
Fase 5  (sincronización) ── depende de Fase 3 (las tablas ya deben tener uso real)
   ↓
Fase 6  (documentación) ── depende de Fases 3, 4 y 5 para documentar lo que existe
   ↓
Fase 7  (verificación de cierre)
```

Las Fases 0, 1 y 2 son de bajo riesgo y pueden ejecutarse de inmediato. La Fase 3 es la única que requiere decisión de producto sobre el alcance de la interfaz.

---

## Registro de auditoría

| Dato | Valor |
|---|---|
| Método | Lectura estática del código y de la documentación |
| Python disponible | No — Fase 0 pendiente |
| Checks ejecutados | Ninguno |
| Hallazgos confirmados | 6 (A a F) |
| Correcciones al plan previo | Conteo de archivos de prueba 28 → **27**; `log_message` **sí** rompe su test (el plan previo afirmaba lo contrario) |

---

*Documento generado como auditoría y hoja de ruta. Las cifras de cobertura y número de pruebas deben completarse con la medición real de la Fase 0 antes de considerarse cerrado.*
