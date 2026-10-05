# Correcciones ejecutadas — SDEP_CPP5

**Fecha:** 2026-10-04
**Origen:** `OBSERVACIONES_CORRECCIONES.md` (inventario) y `PLAN_MAESTRO_SDP_CPP5.md` (fases).
**Método:** edición estática, sin ejecución. **No hay Python en la máquina** (el alias de Microsoft Store intercepta `python`; `py` no existe), así que **ninguna corrección fue verificada ejecutando la suite**. Cada edición sí se releyó después de aplicarla para comprobar coherencia sintáctica, y las pruebas existentes se revisaron antes de tocar su comportamiento.

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
| Fase 6 — documentación y portal (`NOTAS_DESARROLLO.md`, `GUIA_USUARIO.md`, `docs/content/`, cifras medidas) | Depende de medir la suite (Fase 0), imposible sin intérprete. |
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
