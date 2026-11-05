# Auditoría y correcciones — SDEP_CPP5

Documento de cambios aplicados tras la revisión línea por línea del proyecto
completo (backend Python, agente/nodo de sincronización, app Android Kotlin,
updater, GUI, utilidades y configuración).

> **Nota de seguridad urgente:** el `sync_token` que estaba en `config.json`
> quedó expuesto en texto plano y debe considerarse **comprometido**. Se eliminó
> del archivo, pero en cualquier despliegue real debe **revocarse y
> regenerarse** manualmente en el nodo central y en los equipos que lo usaban.

---

## 1. Seguridad y configuración

### `config.json`
- **Eliminado el token de sincronización real** (`sync_token`) que estaba
  versionado en texto plano junto al ID de dispositivo y nombre de equipo.
  El token debe rotarse en el servidor; este archivo ya no contiene secretos.

### `iniciar_servidor.py`
- Detección de IP local ya no depende únicamente de conectividad UDP a
  `8.8.8.8` (fallaba en redes sin salida a Internet).
- Configuración por defecto más segura: enlace local por defecto, emparejamiento
  automático desactivado por defecto y cambio de contraseña obligatorio en las
  cuentas iniciales.

### `updater/auto_updater.py`
- **Path traversal corregido:** el nombre del asset descargado desde GitHub
  Releases se sanitiza y se valida que la ruta final quede dentro de
  `updates/` antes de escribir. Antes un nombre `..\..\...` podía escribir
  fuera del directorio de actualizaciones.

### `sync_agent/servidor.py`
- Límites de tamaño de cuerpo HTTP aplicados **antes** de procesar el contenido
  (mitiga DoS pre-autenticación; antes el cuerpo se leía completo con un límite
  efectivo de ~64 MB).
- Limpieza del diccionario del rate limiter para que no crezca sin límite.
- Validación estricta del payload y de los nombres de operación.
- Normalización de eventos: operaciones inválidas se **rechazan** en lugar de
  tratarse silenciosamente como `upsert`.

### `sync_agent/aplicador.py`
- Validación de operaciones antes de aplicar; las operaciones malformadas o no
  soportadas se rechazan en vez de aplicarse como `upsert`.

> **Pendiente conocido:** los defaults de `ServidorConfig`
> (`host="0.0.0.0"`, `emparejamiento_abierto=True`) siguen siendo permisivos en
> la clase; el endurecimiento efectivo se hace desde `iniciar_servidor.py` y la
> configuración. Se recomienda cambiarlos a `127.0.0.1`/`False` en una próxima
> iteración junto con la revisión de los puntos de sync listados en §5.

---

## 2 Backend — datos, nómina y respaldos

### `src/services/pago_service.py`
- **Doble prorrateo corregido:** la comparación usaba `dias_trabajados`
  (calendario) contra lo que enviaba el formulario (`dias_laborados`), por lo
  que `recalcular` se disparaba siempre y un salario ya prorrateado volvía a
  prorratearse (doble descuento de días).
- **Overlap de pagos corregido:** la verificación de períodos solapados ahora
  filtra por tipo de pago; antes cualquier pago que tocara el período
  (incluidos `LIQUIDACION`/`BONO`) bloqueaba la generación de la nómina.
- **Períodos > 1 mes:** se generaban un solo pago de un mes (`dias_base=30`
  forzado). Ahora se cubren los meses restantes.
- `actualizar_pago`: el `setattr` masivo sin lista blanca se sustituyó por una
  lista de campos editables permitidos.

### `src/services/documento_service.py`
- `actualizar_documento`: lista blanca de campos editables; ya no se pueden
  sobrescribir `id`, binario ni campos internos por mass-assignment.

### `src/utils/backup_manager.py`
- **Restauración destructiva corregida:** al restaurar un respaldo no
  comprimido, `temp_restore_path` apuntaba al propio backup y el `finally`
  hacía `unlink()` sobre él → se borraba el respaldo (incluidos los
  `pre_restore_*`). Ahora el temporal solo se crea para archivos realmente
  extraídos y el original nunca se elimina. Se mantiene la validación de
  integridad SQLite, la copia por etapas y el reemplazo atómico.

### `src/utils/backup_scheduler.py`
- Las comprobaciones previas (`debe_ejecutar`, `esta_habilitado`) se ejecutan
  dentro de `try/except`: el scheduler cumple su contrato de "nunca lanza".

### `src/utils/audit_logger.py`
- Exportación de auditoría: el nombre de archivo se reduce a `Path(...).name`
  y la salida queda confinada en `exports/` (antes un `../` en el nombre podía
  escribir fuera del directorio configurado).

---

## 3. Backend — modelos y repositorios

### `src/repositories/busqueda.py` y `base_repository.py`
- **Búsqueda con tildes en mayúsculas corregida:** la normalización ahora
  pliega acentos antes de `lower()`, de modo que `PÉREZ`, `Ñ` y `É` mayúsculas
  sí coinciden con `perez`, `n`, `e`. Afectaba a empleados y estudiantes.

### `src/repositories/nota_final_repository.py`
- `insertar_lote` ya no usa `session.execute(insert(...))` directo (DML bulk
  que saltaba el hook `before_flush` de aislamiento por cédula): ahora valida
  contexto/propiedad antes de insertar.

### `src/models/empleado.py`
- `salario_base`: `Float` → `Numeric(12, 2)` con tipo `Decimal`. El flotante
  binario introducía errores de redondeo en nómina.
  > ⚠️ Requiere migración/compatibilidad en bases existentes (SQLite ya guarda
  > el valor; verificar que el esquema coincida al crear la base).

### `src/models/registro_movil.py`
- `actualizado_en` ahora se actualiza automáticamente (`onupdate`) al editar;
  antes la marca de mezcla LWW nunca cambiaba al modificar la fila.

### `src/models/documento.py`
- `es_valido`/fechas: la validación dejó de ser fail-open ante fechas
  corruptas; se añadió `logger` para registrar el motivo del rechazo.

### `src/models/contrato.py`
- Cálculo/tipado decimal del salario: manejo de horas cero o inválidas y
  consistencia con `Numeric`.

### `src/repositories/empleado_repository.py`
- Filtro `activo`: acepta bool/entero/texto (`"1"`, `"true"`, `"si"`...); antes
  un `int()` sobre texto lanzaba `ValueError` y el `except` devolvía `[]`
  (todos los empleados "desaparecían" del listado).
- `get_estadisticas_por_tipo` / `por_departamento`: `GROUP BY` en SQL en lugar
  de hidratar todos los empleados activos en memoria (N+1).
- Logs de error ya no incluyen la cédula en claro (PII).

### `src/repositories/contrato_repository.py`
- `contar_activos_por_empleado`: cuenta solo contratos `VIGENTE` (antes
  incluía `VENCIDO`/`RENOVADO`).
- `get_estadisticas`: `indefinidos` ahora cuenta solo indefinidos **vigentes**,
  consistente con la métrica `vigentes`.

### `src/repositories/configuracion_repository.py`
- `set_valor` ahora pasa por `update()` → la escritura queda auditada como el
  resto del sistema (antes hacía `commit()` propio sin rastro en auditoría).

### `src/security/aislamiento.py`
- `_cedula_sql`: quita también `/`, `,`, `_` además de `.` y espacio, para
  acercarse a `normalizar_cedula` de Python (se documenta el límite: SQLite no
  tiene clase de caracteres; una cédula con signo exótico podría no coincidir).
- Comparación de `RegistroMovil.usuario` sin distinguir mayúsculas ni espacios
  sobrantes (los datos llegan del móvil con el nombre escrito distinto).
- `instalar()` con doble comprobación bajo `threading.Lock`: varios hilos
  pueden llamarlo al arrancar servidor y servicios sin registrar listeners
  duplicados.

### `src/models/enums.py`, `usuario.py`, `configuracion.py`
- Verificados: `BaseEnum.coerce` ya está centralizado; `password_vigente` ya
  compara en UTC; `valor_typed` bool ya acepta `yes/on/si/verdadero`.

### GUI (`src/gui/`)
- `main_window.py::_esperar_respaldo_y_cerrar`: espera acotada (~2 min) antes
  de cerrar; antes una copia de seguridad colgada dejaba la app abierta para
  siempre.
- `main_window.py::_verificar_respaldo_periodico`: `strptime` de la marca de
  tiempo envuelto en `try/except`; una marca ilegible se trata como "vencida"
  en lugar de propagar la excepción.
- `notas_frame.py::_requiere_administrador`: verificado correcto — el permiso
  `"config"` es exclusivo de `admin` en `PermissionChecker` (manager no lo
  tiene), coherente con el mensaje "solo administrador".

---

## 4. Agente/nodo de sincronización (`sync_agent/`)

### `agente.py`
- `_confirmar_envio` reescrito: solo se confirman las operaciones presentes en
  `aplicadas` del servidor. Antes, una respuesta con `aplicadas` vacía marcaba
  **todo** como `CONFIRMADA` → pérdida silenciosa de operaciones. Las
  `rechazadas` del servidor ahora se consumen y marcan la operación en el
  journal en lugar de reintentarla eternamente.
- `_reintentar_diferidas`: ya no borra todo el journal antes de recrearlo (si
  el proceso moría en medio se perdía la operación remota); conserva las
  entradas, sus contadores de reintento y los metadatos (`dispositivo`,
  `usuario`, `creado_en`) para el desempate de conflictos.
- `_subir_blob`/`_bajar_blob`: estados de blob corregidos (`omitido`,
  `por_bajar`), reintentos acotados y no se marca `BLOB_SUBIDO` cuando el
  contenido es `None` o excede el tamaño.

### `aplicador.py`
- FKs a tablas no replicadas ya no se convierten en `NULL` local pisando un
  valor válido (`traducido.get(campo, marca.valor)` corregido).
- Operaciones inválidas se rechazan; nombres de operación validados contra
  lista blanca.

### `identidad.py`
- Unificación por clave natural: ahora fusiona `sync_campos`/`sync_versiones`
  y maneja tombstones de borrado físico (antes reasignaba el UUID sin fusionar
  metadatos → divergencia entre nodos e `IntegrityError` por `sync_ids`
  huérfanos al revivir filas borradas físicamente).

---

## 5. App Android (`android/app/src/main/java/ve/edu/sdep/movil/`)

### Datos / sincronización
- `SincronizacionRepositorio.prepararCambioDeUsuario`: antes solo comprobaba
  `identidadDao.contar()`, pero `registros`/`operaciones_pendientes` no crean
  `IdentidadEntity` → `clearAllTables()` borraba capturas offline sin enviar.
  Ahora se protege cualquier registro u operación pendiente (nuevos
  `contarPendientes()` en `RegistroDao` y `OperacionDao`) y el intento de envío
  previo se verifica con esos mismos contadores.
- Operaciones `RECHAZADA` del servidor ahora propagan su estado al
  `RegistroEntity` local (`marcarRechazadas`): antes quedaban `PENDIENTE` para
  siempre.
- `Espejo.canonica()`: nuevo `escaparCadena()` que escapa comillas, barra
  invertida y **todos** los caracteres de control igual que
  `json.dumps(ensure_ascii=False)` de Python. Antes solo escapaba `"` y `\`,
  así que las marcas canónicas de mezcla diferían entre Android y el nodo
  central.
- `Espejo.payload` (ediciones): envía solo columnas modificadas (`completa`
  solo en altas); verificado que `TablaRepositorio.guardar` ya calcula el
  diff entidad-a-entidad — no hay lost update por payload completo.
- `AplicadorEspejo.reintentarDiferidas`: las operaciones diferidas ahora
  conservan `dispositivo`/`usuario` originales (columnas nuevas en
  `operaciones_entrada`, migración Room **v3→v4** `MIGRATION_3_4` registrada
  en `ModuloBaseDatos`), de modo que el desempate de conflictos por
  simultaneidad usa el mismo origen que el protocolo. El contador de
  intentos (`intentos = intentos + 1` con `MAX_INTENTOS_DIFERIDA = 10`) ya era
  correcto y `purgar` coincide (`intentos > 10`).
- `DaosEspejo.pendientesDeEntrada`: `omitido` es terminal y ya no se
  reselecciona; se añade `intentos < maxIntentos`. Antes un blob `omitido` se
  reintentaba en cada ciclo indefinidamente.
- `SincronizacionRepositorio.descargarBlob`: se rechaza por `Content-Length`
  o `tamano` conocido todo blob > 64 MiB (`MAX_BYTES_BLOB`) **antes** de
  leer el cuerpo; antes `bytes()` cargaba el archivo completo en memoria
  (OOM ante un nodo comprometido).

### Autenticación / sesión
- `AutenticacionRepositorio.entrarConBiometria`: si el nodo no envía
  `expira_en`, la sesión ya **no es eterna**: se acota con
  `vida_relativa_horas` (nuevo campo en `SesionInfoDto`, default 12 h).
- `Sesion.vigente()` y `vigente()` privado del repositorio: `expiraEn <= 0`
  ya no se interpreta como "siempre vigente"; una sesión sin caducidad
  informada no es vigente.
- `HttpException` en login biométrico: solo 401/403 invalidan la credencial
  biométrica; 5xx/429 son transitorios (`reintentable = true`) y conservan la
  credencial.

### UI
- `UserProfileScreen`: añadido `LaunchedEffect(Unit) { cargarPerfil() }` —
  antes nadie invocaba la carga y "Mi perfil" siempre salía vacío.
- `EmpleadoViewModel.guardar`: nueva validación `errorDecimal()` — salario
  base obligatorio, finito y ≥ 0; peso/altura opcionales pero deben ser
  números > 0. Antes un texto inválido se convertía en `0.0`/`null` y se
  sincronizaba al escritorio.
- `HerramientasPdfViewModel.limpiarMensaje()` + `PantallaHerramientasPdf`:
  el snackbar se muestra una vez y se limpia el mensaje; antes un mensaje
  viejo reaparecía al re-entrar a la pantalla ("snackbar fantasma").
- `TablaRepositorio.opcionesForaneas`: la tabla padre se valida contra
  `Espejo.CLAVES_FORANEAS` antes de interpolarla en SQL — antes cualquier
  nombre con forma de tabla (incluidas las internas del espejo) era
  consultable.
- `Fechas.isoDesde`: formato fijo `yyyy-MM-dd'T'HH:mm:ss` + fracción de 6
  dígitos cuando hay nanosegundos (como `datetime.isoformat()` de Python).
  Antes `ISO_LOCAL_DATE_TIME` omitía segundos en punto, rompiendo la
  comparación lexicográfica de marcas de mezcla.

---

## 6. Pruebas

- `tests/test_pagos.py`: corregido el comentario que sugería que el motor
  debía prorratear un mes completo (el empleado está contratado desde 2019;
  febrero 2026 es mes completo → salario íntegro es lo correcto).
- `tests/test_registros_moviles.py`: docstring corregido (el reintento usa el
  mismo `uuid`, no "otro fila_uuid").
- `tests/test_security.py`: `TestSecurityLogger` ahora **verifica** que cada
  evento queda persistido en `audit_logger.recent_events` con su
  `event_type`, `details` y `success` correctos (antes solo comprobaba que no
  lanzara excepción).

---

## 7. Ítems conocidos pendientes (próxima iteración)

- `ServidorConfig`: cambiar defaults de clase a `host="127.0.0.1"` y
  `emparejamiento_abierto=False`; exposición LAN solo por configuración
  explícita. Revisar todos los puntos de construcción de la config.
- Cuota de disco en `POST /api/v1/blob/{hash}` del nodo central (hoy cualquier
  dispositivo autenticado puede llenar el disco).
- `token_sesion_repository` usa `query.update()` que bypassa el aislamiento
  ORM (revisar si aplica a WORKER).
- `_log_data_operation` audita `to_dict()` completo → datos bancarios/salud en
  claro en el log de auditoría; saneamiento selectivo pendiente.
- Migración explícita `Empleado.salario_base` Float→Numeric en bases existentes.
- Android: `cleartextTrafficPermitted` + confianza en CAs de usuario
  (`seguridad_red.xml`), `leerPdfLimitado` con respuestas chunked sin
  `Content-Length`, `codigoVersion`/parseo de versión, `Json` lenient,
  `Dispatchers.IO` para lectura sincrónica de `EncryptedSharedPreferences`,
  `puedeEditar` en registros existentes, orden de `LaunchedEffect` de
  navegación, colisión de hash en `blobs_pendientes` (PK `hash` con `REPLACE`).
- GUI: guards `None` en `contratos_frame`/`estudiantes_frame`/`frames.py`,
  `notas_frame` validación float, `theme.py`/`graficos` edge cases,
  try/except en descargas del updater.
- `ContratoRepository`/`empleado_repository.get_filtrados`: revisar el caso de
  filtro mal formado (hoy devuelve `[]` silenciosamente).

---

## 8. Correcciones tras el primer build de CI

El pipeline de GitHub Actions (`flake8` + `assembleRelease`) detectó tres
errores introducidos en la primera pasada; todos corregidos:

- `sync_agent/agente.py`: eliminado el import sin uso `MOTIVO_ERROR`
  (F401 de flake8).
- `SincronizacionRepositorio.kt::descargarBlob`: `return` dentro de una
  función con cuerpo de expresión → convertida a cuerpo de bloque.
- `TablaRepositorio.kt::opcionesForaneas`: `CLAVES_FORANEAS.values.flatten()`
  no compila porque los valores son `Map` (no `Iterable`) →
  `flatMap { it.values }` para obtener los nombres de tabla padre.

## 9. Verificación realizada

- `python -m compileall` sobre `src`, `sync_agent`, `tests`, `updater` e
  `iniciar_servidor.py`: **sin errores de sintaxis** tras todas las ediciones.
- Revisión manual de cada edición (no hay Git disponible en el entorno para
  diff automático).
- La app Android no pudo compilarse en este entorno (sin Gradle/Android SDK);
  los cambios Kotlin siguen las convenciones existentes (Room migrations,
  DAO suspend, Compose `LaunchedEffect`) y deben validarse con `./gradlew
  assembleDebug` en un equipo con el SDK.
