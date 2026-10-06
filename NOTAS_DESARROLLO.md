# Notas de Desarrollo - Sistema de Gestión de Personal

## Estado del Proyecto

El proyecto se encuentra en un estado estable y funcional con todas las funcionalidades principales implementadas y documentadas.

### Versión vigente: 3.0.1

Esta versión hace alcanzable el **subdominio académico** que existía en la capa de
datos sin interfaz, y cierra la auditoría estática de la versión 3.0.0.

**Módulo académico en el producto**

- Dos módulos nuevos en la barra lateral: **Estudiantes** (`Ctrl+8`), con el legajo y
  la estructura escolar (grados, secciones y matrículas), y **Calificaciones**
  (`Ctrl+9`), con las notas finales y los periodos académicos. Se resolvieron como dos
  módulos con pestañas para no superar el tope de nueve atajos directos; `Ctrl+1..7`
  conserva exactamente su significado anterior.
- La escritura de notas se autoriza con un **token de sesión académico** (en memoria,
  hash en la base): escribe la administración en cualquier grado y el docente asignado
  solo en el suyo; el rol de solo lectura nunca escribe.
- **Cerrar un periodo** bloquea sus notas en el servicio y en los disparadores de
  SQLite (incluso por SQL directo); reabrirlo exige rol administrador y queda auditado.
- Consolidado del periodo, boletín por estudiante y acta final del grado, además de la
  exportación de notas y del legajo a Excel.

**Datos académicos en la sincronización**

- Las tablas `estudiantes`, `periodos_academicos`, `grados`, `matriculas` y
  `notas_finales` se replican entre puestos; `tokens_sesion` queda fuera a propósito
  por ser una credencial local.
- `calificacion` es campo sensible: todo choque entre equipos se registra para su
  revisión, y una nota creada en dos puestos se unifica por su clave compuesta
  (estudiante, grado y materia) en lugar de duplicarse.

**Correcciones de esta versión**

- Módulo fantasma `reportes` fuera del mapa de permisos, con prueba de coherencia
  entre menú, marcos y mapa (`tests/test_permisos_modulos.py`).
- `log_message` usa `logging` (nivel por nombre, mensaje diferido) y su prueba verifica
  el registro con `caplog` en lugar de stdout.
- `.env.example` declara `APP_VERSION=3.0.1` y `README.md` cuenta los 32 archivos de prueba de la suite.
- Liquidaciones con referencia `LIQ-<contrato>` fija; el recálculo de un pago respeta
  días trabajados y prorrateo; el salario base vacío de un empleado falla con mensaje
  claro y una cédula vacía no borra la existente.
- Un valor idéntico con marca más reciente refresca la marca (convergencia del agente);
  nómina y finiquito cuentan el mismo criterio de incidencias; `completar` solo
  completa incidencias aprobadas.
- `.gitignore` excluye `*.db.gz`, `backups/` y `hang_stack.txt` (los archivos siguen
  en disco; retirarlos del índice de Git es una decisión del responsable).

> **Verificación ejecutada (2026-10-06, Windows + CPython 3.15.0rc3):** las
> correcciones se aplicaron primero por lectura estática y después se ejecutaron.
> La suite completa quedó en **551 pruebas sobre 32 archivos, todas exitosas**
> (0 fallos, 0 errores) y la cobertura medida es **56 % total** (servicios 76 %,
> motor de nómina 89 %). `flake8`, `black --check`, `isort --check-only`,
> `mypy` (98 archivos) y `tools/verify_docs.py` pasan sin hallazgos, y el arranque
> real (`python src/main.py --selftest`) devuelve código 0, tanto sobre una base
> nueva como sobre una base con el esquema anterior de matrículas (la migración
> reconstruye la tabla y deja solo la matrícula activa como única). Los defectos
> que esa primera ejecución destapó —reseteo de la base de prueba bloqueado por los
> disparadores de inmutabilidad, selector de periodo del módulo de notas, rematrícula
> tras retirar y resolución de la ruta del respaldo en su prueba— quedaron corregidos
> y cubiertos por pruebas. Las cifras de la sección 1.0.4 siguen marcadas como
> históricas.

## Características Implementadas

### ✅ Módulos Completos

1. **Gestión de Empleados**
   - CRUD completo de empleados
   - Búsqueda y filtrado avanzado
   - Gestión de fotos de perfil
   - Estadísticas y reportes
   - Validación de datos

2. **Gestión Documental**
   - Carga y almacenamiento de documentos
   - Control de vencimientos
   - Clasificación por tipo
   - Gestión por empleado
   - Validación de archivos

3. **Gestión de Incidencias**
   - Registro de permisos y ausencias
   - Flujo de aprobación/rechazo
   - Cálculo automático de días
   - Documentos de soporte
   - Control de incidencias vigentes

4. **Sistema de Nómina**
   - Generación automática de nóminas
   - Cálculo de deducciones
   - Integración con incidencias
   - Control de pagos pendientes
   - Generación de recibos PDF

5. **Configuración del Sistema**
   - Configuración por categorías
   - Parámetros de nómina
   - Datos institucionales
   - Validación de valores

6. **Contratos Laborales**
   - Alta, renovación y terminación con finiquito
   - Unicidad del contrato vigente y numeración automática
   - Control de contratos por vencer y vencidos

7. **Panel Analítico**
   - Indicadores clave y gráficos propios (barras, dona, línea)
   - Reportes PDF de contratos, vencimientos y movimiento anual

8. **Módulo Académico** (incorporado en 3.0.1)
   - Estudiantes: legajo con cédula única, nivel, representante y contactos
   - Grados, secciones, docente responsable y matrícula por año escolar
   - Notas finales con autorización por token, consolidado, boletín y acta
   - Periodos académicos con cierre que bloquea las notas y reapertura auditada

### ✅ Infraestructura

- **Base de Datos**: SQLite con SQLAlchemy ORM
- **Interfaz Gráfica**: CustomTkinter con tema oscuro/claro configurable
- **Arquitectura**: Separación en capas (Models, Repositories, Services, GUI)
- **Utilidades**: Helpers, validadores, generadores de PDF
- **Documentación**: Completa en español

## Correcciones Realizadas

### Errores de Código Corregidos

1. **Uso de datetime.now().date()**
   - Cambiado a `date.today()` para consistencia
   - Agregado import de `date` en documento.py

2. **Conversión de Tipos Numéricos**
   - Corregidas conversiones de Decimal a float
   - Agregado casting explícito en operaciones financieras

3. **División por Cero**
   - Implementada división segura en helpers
   - Agregados checks en cálculos de nómina
   - Validación de denominadores

4. **Type Hints**
   - Agregados imports de `Any` y `Union`
   - Mejoradas anotaciones de tipo
   - Corregida configuración de mypy

5. **Importaciones Circulares**
   - Implementada carga diferida de frames
   - Reorganizados imports en main_window

6. **Permisos en atajos de teclado**: Ctrl+N y Ctrl+S ahora verifican el
   permiso del rol antes de crear/guardar registros (cierre del bypass de
   permisos por atajos).
7. **Restauración de respaldos**: se cierra la sesión de forma segura al
   restaurar, sin doble confirmación ni estado roto.
8. **Longitud de contraseña**: los diálogos usan la constante
   `LONGITUD_MINIMA_PASSWORD` (6) en lugar de textos fijos incoherentes.
9. **Empaquetado**: se añadió `openpyxl` a las dependencias y se corrigió
   `packages` en `pyproject.toml` para que `pip install .` funcione.
10. **Estado de respaldos**: `get_backup_status` ahora lee
    `backup_enabled` de la configuración en lugar de devolver siempre True.
11. **Cédula numérica**: el servicio valida que la cédula sea numérica.
12. **Limpieza**: eliminado código muerto y unificada la carga de la lista
    de empleados.

## Estructura de Archivos

```
SDEP_CPP5/
├── src/                          # Código fuente
│   ├── config/                   # Configuración
│   │   ├── database.py          # Configuración de BD
│   │   └── settings.py          # Configuración general
│   ├── gui/                     # Interfaz gráfica
│   │   ├── main_window.py      # Ventana principal
│   │   ├── frames.py           # Frames de módulos históricos
│   │   ├── contratos_frame.py  # Módulo de contratos
│   │   ├── estudiantes_frame.py # Legajo, grados y matrículas
│   │   ├── notas_frame.py      # Calificaciones y periodos académicos
│   │   ├── widgets/            # Gráficos y KPIs propios (Canvas)
│   │   ├── login_window.py     # Inicio de sesión
│   │   └── theme.py            # Tema claro/oscuro
│   ├── models/                  # Modelos de datos
│   │   ├── base.py             # Modelo base
│   │   ├── enums.py            # Enumeraciones
│   │   ├── empleado.py        # Modelo empleado
│   │   ├── documento.py       # Modelo documento
│   │   ├── incidencia.py      # Modelo incidencia
│   │   ├── pago.py           # Modelo pago
│   │   ├── contrato.py        # Contrato laboral
│   │   ├── configuracion.py   # Modelo configuración
│   │   ├── estudiante.py      # Estudiante del legajo académico
│   │   ├── grado.py           # Grado y sección del periodo
│   │   ├── matricula.py       # Matrícula por estudiante y grado
│   │   ├── nota_final.py      # Calificación por materia
│   │   ├── periodo_academico.py # Año escolar abierto o cerrado
│   │   ├── token_sesion.py     # Token académico (solo el hash)
│   │   └── usuario.py        # Modelo usuario
│   ├── nomina/                  # Motor de cálculo puro
│   │   ├── tipos.py            # Datos de entrada y resultado
│   │   ├── parametros.py       # Carga y validación de parámetros
│   │   ├── isr.py             # Impuesto por tramos progresivos
│   │   ├── seguridad_social.py # Aportes con techos
│   │   ├── horas_extra.py      # Recargos por tipo de jornada
│   │   ├── prestaciones.py     # Aguinaldo, vacaciones, prestaciones
│   │   ├── finiquito.py        # Liquidación completa
│   │   └── motor.py            # Orquestador del cálculo
│   ├── repositories/            # Acceso a datos
│   │   ├── base_repository.py # Repositorio base
│   │   ├── empleado_repository.py
│   │   ├── documento_repository.py
│   │   ├── incidencia_repository.py
│   │   ├── pago_repository.py
│   │   ├── contrato_repository.py
│   │   ├── configuracion_repository.py
│   │   └── usuario_repository.py
│   ├── services/                # Lógica de negocio
│   │   ├── empleado_service.py
│   │   ├── documento_service.py
│   │   ├── incidencia_service.py
│   │   ├── pago_service.py
│   │   ├── contrato_service.py
│   │   ├── configuracion_service.py
│   │   ├── academico_service.py # Legajo, grados, matrículas y periodos
│   │   ├── nota_service.py      # Notas, consolidado, boletín y acta
│   │   ├── token_sesion_service.py # Autorización de escritura de notas
│   │   └── auth_service.py
│   ├── utils/                   # Utilidades
│   │   ├── helpers.py          # Funciones auxiliares
│   │   ├── validators.py      # Validadores
│   │   ├── document_manager.py # Gestión documentos
│   │   ├── pdf_generator.py    # Generación PDF
│   │   ├── security.py        # Hash de contraseñas y permisos
│   │   ├── audit_logger.py    # Registro de auditoría
│   │   ├── backup_manager.py  # Copias de seguridad
│   │   ├── backup_scheduler.py # Respaldos automáticos programados
│   │   └── exporter.py        # Exportación Excel/CSV
│   └── main.py                 # Punto de entrada
├── sync_agent/                  # Agente de sincronización (paquete independiente)
│   ├── comun.py                # UUID, hash y serialización con etiquetas de tipo
│   ├── registro.py             # Qué se replica de cada tabla
│   ├── merge.py                # Motor de mezcla por campo (funciones puras)
│   ├── esquema.py              # Journal, identidad global, marcas y binarios
│   ├── identidad.py            # Identidad global (UUID) ↔ ids locales
│   ├── captura.py              # Enganche al ORM: journal en la misma transacción
│   ├── aplicador.py            # Aplica lo que llega de la red (cliente y servidor)
│   ├── cliente.py              # Cliente HTTP del protocolo
│   ├── agente.py               # Hilo de fondo: ciclo, reintentos y estado
│   ├── servidor.py             # Nodo central (servicio HTTP de la biblioteca estándar)
│   ├── config.py               # Configuración por equipo
│   ├── __main__.py             # Interfaz de línea de comandos
│   └── README.md               # Manual de operación
├── tests/                       # Pruebas automatizadas: 32 archivos · 551 casos (medido)
├── requirements.txt             # Dependencias
├── requirements-dev.txt         # Dependencias desarrollo
├── pyproject.toml             # Configuración proyecto
├── build.py                   # Script construcción
├── updater/                   # Actualizador automático (cada 2 días)
│   ├── auto_updater.py        # Lógica principal
│   ├── updater_gui.py         # Ventana de estado (tkinter)
│   ├── tray_icon.py           # Bandeja del sistema (ctypes)
│   └── updater.spec           # Spec de PyInstaller
├── README.md                  # Documentación general
├── DOCUMENTACION_TECNICA.md   # Documentación técnica
├── GUIA_USUARIO.md            # Guía de usuario
└── NOTAS_DESARROLLO.md        # Este archivo
```

## Dependencias Principales

- **SQLAlchemy**: ORM para base de datos
- **CustomTkinter**: Interfaz gráfica moderna
- **ReportLab**: Generación de PDFs
- **Python-dotenv**: Gestión de variables de entorno
- **Pillow**: Procesamiento de imágenes
- **openpyxl**: Exportación a Excel (incluida la multihoja)

No se añadió ninguna dependencia para el panel analítico: los gráficos
se dibujan sobre `Canvas` de Tk (`src/gui/widgets/graficos.py`) y el motor
de nómina solo usa la biblioteca estándar (`decimal`, `datetime`).

## Configuración de Desarrollo

### Entorno Virtual

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### Instalación de Dependencias

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Para desarrollo
```

### Ejecución de la Aplicación

```bash
python src/main.py
```

### Construcción de Ejecutable

```bash
python build.py
```

## Pruebas

### Ejecutar Pruebas

```bash
pytest tests/
```

### Cobertura de Código

```bash
pytest tests/ --cov=src --cov-report=html
```

### Linting

```bash
black src/
isort src/
flake8 src/
pylint src/
```

## Buenas Prácticas Implementadas

1. **Separación de Responsabilidades**
   - Cada capa tiene una responsabilidad clara
   - Los servicios contienen la lógica de negocio
   - Los repositorios manejan solo acceso a datos

2. **Manejo de Errores**
   - Excepciones manejadas apropiadamente
   - Mensajes de error descriptivos
   - Rollback en operaciones de base de datos

3. **Validación de Datos**
   - Validaciones en servicios
   - Validadores especializados
   - Verificación de tipos y rangos

4. **Documentación**
   - Docstrings en todas las clases y métodos
   - Comentarios en código complejo
   - Documentación externa completa

5. **Tipo de Datos**
   - Type hints en todo el código
   - Enumeraciones para valores constantes
   - Modelos bien tipados

## Mejoras Futuras Sugeridas

### Funcionalidades

1. **Reportes Avanzados**
   - Reportes personalizados
   - Gráficos y estadísticas
   - Exportación a Excel

2. **Integraciones**
   - API REST para acceso externo
   - Integración con sistemas de asistencia
   - Conexión con sistemas bancarios

3. **Mejoras de UI**
   - Responsividad mejorada en pantallas pequeñas
   - Más temas y acentos de color

## Novedades de la Versión 2.81

### Migración a Python 3.15

- Requisito de intérprete: **Python 3.15** (`requires-python >=3.15` en
  `pyproject.toml`). Verificado con `3.15.0rc2` en Windows y con la rc
  más reciente en CI (`allow-prereleases: true` hasta la final del
  2026-10-01).
- Dependencias alineadas: SQLAlchemy 2.0.54 (serie 2.1 aún no publicada),
  customtkinter 6.0.0, reportlab 5.0.1, Pillow 12.3.0, openpyxl 3.1.5,
  PyInstaller 6.22 (primeras versiones con bootloaders de 3.15).
- Tipado modernizado en todo `src/`: unions PEP 604 (`X | None`) y
  contenedores nativos (`list[...]`, `dict[...]`, `tuple[...]`); el
  repositorio genérico usa sintaxis genérica PEP 695
  (`class BaseRepository[T]`).
- Retirados los `from __future__ import annotations` de `updater/`.
- Robustez: los `except Exception` silenciosos de servicios, repositorios,
  configuración y utilidades registran ahora `logger.warning(...,
  exc_info=True)`.
- `migrar_columnas` valida columna y tipo contra listas blancas antes de
  ejecutar la DDL de migración.
- El ejecutable Linux se compila ahora en **Debian 13** (glibc 2.41);
  deja de garantizarse Ubuntu 22.04 y Debian 12.
- Versión del sistema: **2.81** (`VERSION`, `pyproject.toml`, instalador,
  `APP_VERSION_DEFAULT`, `src/__init__.py`).

### Calidad y CI (cierre 2.81)

- Análisis estático limpio en todo el árbol: `mypy` sin errores en los
  52 archivos de `src/`, `updater/`, `tools/` y `build.py` (los módulos
  del actualizador quedaron tipados: DLLs de Windows como
  `ctypes.WinDLL | None` con guardas de invariante, callbacks
  `on_progress`/`on_download` con firma `Callable`, retornos `int`
  explícitos); `flake8` (F/E9/W6) sin hallazgos y cero `# type: ignore`.
- Los mensajes de error por `print()` en producción pasaron a `logger`
  (helpers, settings, main_window); los handlers `pass` restantes son
  best-effort auditado (callbacks de GUI, drenaje de cola, limpieza de
  locks).
- `pdf_generator`: `generate_reporte_nomina` y `generate_recibo_pago`
  se dividieron en helpers pequeños con tipado completo (salida
  idéntica; 17 pruebas de reportes en verde).
- Corrección de un bug de validación: los datos no numéricos en
  `dias_solicitados` pasaban la validación en silencio; ahora producen
  un error de validación claro.
- Corrección de diseño en permisos: `can_access_module` niega solo
  módulos conocidos; los desconocidos muestran el marco "Módulo en
  desarrollo" (antes quedaban bloqueados y la rama era inalcanzable).
- Estabilidad de pruebas GUI: los diálogos modales de `_show_frame` y
  el diálogo de cambio de contraseña verifican la ventana con guardas
  `TclError`; los tests de Ayuda/Acerca esperan el cierre real del
  `CTkToplevel` (elimina el flakiness por orden de ejecución).
- CI: el contenedor `debian:13` instala `binutils`, requerido por
  PyInstaller (`objdump`); corrige el fallo "On Linux, objdump is
  required" del build Linux.
- Auditoría funcional: `log_data_operation` acepta ahora el parámetro
  `success` (los eventos CRUD se descartaban por `TypeError` antes de
  registrarse) y la serialización JSON de eventos usa `default=str`
  (los `details` con fechas `datetime` revientan `json.dumps`; todos
  los eventos de auditoría de repositorios se estaban perdiendo).
- Empaquetado Linux: el spec añade explícitamente las librerías
  Tcl/Tk del intérprete standalone de Python 3.15 (`libtcl9tk9.0.so`,
  `libtk9.0.so`), que viven fuera del árbol de PyInstaller; corrige el
  fallo del selftest "libtcl9tk9.0.so: cannot open shared object file".

## Novedades de la Versión 3.0.0

Esta versión **redefine el alcance** del sistema: retira por completo los
módulos de **Asistencia**, **Préstamos** y **Alertas**, y conserva la
restante funcionalidad —empleados, documentos, incidencias, contratos,
nómina y configuración— junto con el motor de cálculo, los respaldos
programados y el panel analítico. El cambio es **incompatible** con el
esquema anterior: las tablas, columnas y parámetros de configuración de
los módulos retirados se purgan al arrancar, con respaldo automático
previo.

### 1. Retiro de Asistencia, Préstamos y Alertas

- Se eliminan los modelos `Horario`, `Asistencia` y `Prestamo`, con sus
  repositorios, servicios y pantallas, el paquete
  `src/nomina/prestamos.py` y las utilidades `src/utils/jornada.py`.
- La tabla `pagos` pierde `deduccion_prestamo` y `prestamo_id`. Como
  SQLite no admite `DROP COLUMN` sobre una columna que participa en una
  clave foránea, la tabla se reconstruye copiando las columnas vigentes y
  rehaciendo sus índices (`purgar_esquema_obsoleto`, en
  `src/config/database.py`).
- Las tablas `asistencias`, `horarios` y `prestamos` se eliminan, igual
  que los parámetros de configuración que solo consumían esos módulos: se
  borran de la base y del espejo `config.json` para que `obtener_valor`
  no los devuelva como si siguieran vigentes.
- La purga es idempotente (no toca nada si no queda nada por retirar) y
  va precedida de un respaldo `pre_purga_esquema`.
- La navegación queda en **siete módulos**, el panel de control pierde su
  panel de alertas y el indicador de dotación sustituye a los de
  ausentismo y préstamos.

### 2. Motor de nómina (`src/nomina/`)

Paquete de cálculo puro —no accede a la base de datos ni a la interfaz—
con importes en `Decimal` y redondeo comercial (`ROUND_HALF_UP`):

- **Seguridad social** con techos de cotización por concepto y aportes
  patronales separados (`src/nomina/seguridad_social.py`).
- **ISR por tramos progresivos** (`src/nomina/isr.py`): cuota fija más
  tasa sobre el excedente, base gravable = ingresos menos aportes
  exentos, ajuste anual y tasa efectiva.
- **Horas extra con recargo** por tipo de jornada (diurna 25%, nocturna
  50%, feriada 100%) y valor hora derivado del salario y la jornada
  (`src/nomina/horas_extra.py`).
- **Prestaciones** proporcionales por meses y días de servicio:
  aguinaldo, bono vacacional, vacaciones no disfrutadas, prestaciones por
  antigüedad, indemnización y preaviso (`src/nomina/prestaciones.py`).
- **Finiquito completo** con prestaciones, indemnización, preaviso y
  otras deducciones (`src/nomina/finiquito.py`).
- **Modalidades**: `porcentaje` reproduce exactamente el cálculo
  histórico y `tramos` activa el motor completo; el modo se elige con
  `modo_calculo_nomina` en Configuración.
- Las deducciones capturadas a mano por el usuario **mandan** sobre el
  cálculo automático, y el neto nunca puede ser negativo.

### 3. Contratos

- Modelo `Contrato` con ciclo de vida completo (vigente, renovado,
  vencido, terminado), unicidad del contrato vigente por empleado y
  numeración generada automáticamente.
- **Renovación encadenada**: el nuevo contrato arranca el día siguiente
  al vencimiento y queda enlazado al anterior (`contrato_anterior_id`).
- **Terminación con finiquito**: calcula la liquidación y la registra como
  pago de tipo `liquidacion` (sin aportes de seguridad social), de modo
  que la nómina refleje el egreso.
- Sincronización automática de estados (vencidos y renovables) y
  detección de contratos por vencer, expuesta en el panel de control.

### 4. Respaldos programados y política de credenciales

- `src/utils/backup_scheduler.py`: respaldo automático según
  `backup_interval_hours` (con interruptor `backup_enabled`), verificación
  de integridad del archivo generado y estado consultable.
- Credenciales: bloqueo temporal tras varios intentos fallidos,
  caducidad de la contraseña, prohibición de repetir las últimas claves y
  de reutilizar la vigente, desbloqueo administrativo e historial.

### 5. Panel analítico y reportes

- `src/gui/widgets/graficos.py`: gráficos de barras, dona y línea más
  tarjetas de indicador dibujados sobre `Canvas` (sin dependencias nuevas).
- El Dashboard incorpora KPI reales (nómina del mes, contratos por vencer
  y dotación activa) y tres gráficos, dentro de un contenedor desplazable.
- Reportes PDF vigentes: constancias de trabajo, de estudios y de
  ingresos, recibo de pago, ficha de empleado, planilla de nómina,
  liquidación y reportes de empleados, incidencias, vencimientos,
  contratos y movimiento anual; exportación multihoja para Excel.

### 6. Interfaz

- **Siete módulos** en la barra lateral —Panel de control, Empleados,
  Documentos, Incidencias, Contratos, Nómina y Configuración—, navegables
  con `Ctrl+1`…`Ctrl+7`.
- `frames.py` se conserva como módulo histórico y los dominios con
  pantalla propia viven en módulos por responsabilidad
  (`contratos_frame.py`), junto con los diálogos de contratación.
- La lista de módulos, los títulos de ventana y los mapas de refresco se
  derivan de una sola estructura, de modo que teclas y módulos no pueden
  desincronizarse.
- Los servicios solo se instancian cuando el módulo se abre y toda
  operación que puede fallar muestra un mensaje entendible en lugar de
  dejar la ventana muda.

### 7. Calidad

- `mypy` sin errores en los ochenta archivos verificados —`src/`,
  `sync_agent/`, `updater/`, `tools/` y `build.py`— y cero `# type: ignore`;
  `flake8` (F/E9/W6) sin hallazgos con la configuración declarada en
  `.flake8`.
- Los enums del dominio (`BaseEnum.coerce`) normalizan cualquier valor
  recibido como texto a su miembro correspondiente: las columnas tipadas
  de SQLAlchemy dejan de recibir cadenas sueltas.
- **476 funciones de prueba** en 26 archivos: las 388 de la versión anterior
  más las 87 que verifican el agente de sincronización (mezcla, captura,
  ciclo, nodo central, integración entre dos puestos e interfaz de consola).

### 8. Correcciones de esta versión

- El diálogo de terminación de contrato mostraba un campo `anticipos` que
  ya no existe en el resultado del finiquito; ahora presenta las otras
  deducciones.
- `actualizar_contrato` escribía texto plano en columnas tipadas por enum;
  ahora normaliza el valor.
- Cambiar la contraseña por la misma vigente estaba permitido.
- `generar_nominas_periodo` descartaba los errores de un empleado con un
  `except Exception: continue` silencioso; ahora los registra con
  `logger.warning(..., exc_info=True)` y continúa con el resto.

### 9. Interfaz: concurrencia y ciclo de vida

- El respaldo automático ya no se ejecuta en el hilo de la interfaz: la
  copia de la base de datos (gzip + checksum + rotación) corre en un hilo
  de fondo y el resultado regresa mediante eventos virtuales procesados
  por el hilo principal, que muestra el aviso correspondiente.
- Un fallo del respaldo automático se registra como error y se notifica
  en pantalla; antes quedaba silenciado en el registro de depuración.
- Al salir, la aplicación cancela la verificación programada y espera de
  forma acotada (30 s) a que termine un respaldo en curso, para no cerrar
  con una copia de la base de datos a medias.
- El temporizador de seguridad del diálogo de cambio de contraseña se
  cancela cuando el diálogo termina por la vía normal; antes podía
  dispararse sobre una ventana ya destruida.
- Al cerrar sesión también se cancela la verificación programada de
  respaldo (no solo al salir): la ventana se destruye y la aplicación crea
  otra, de modo que una tarea viva apuntaba a una sesión ya cerrada.

### 10. Auditoría de seguridad y datos

- **Control de acceso a módulos fail-closed.** El mapa de permisos vive
  ahora en un único punto (`PermissionChecker.MODULE_ACCESS`) y un módulo
  que no figure en él se deniega para todos los roles. Antes, un módulo
  desconocido se concedía a cualquier rol: bastaba añadir un módulo a la
  interfaz y olvidarlo en el mapa para dejarlo accesible —incluida la
  creación y el borrado— al rol de solo lectura.
- **Sin sesión no hay permisos.** `tiene_permiso` y `puede_ver_modulo`
  deniegan todo cuando la ventana no tiene usuario cargado; antes devolvían
  `True` y la interfaz habilitaba crear, editar y eliminar en todos los
  módulos. La barra lateral avisa en el registro si un módulo del menú
  quedara fuera del mapa de permisos.
- **Contención de rutas (path traversal).** Los servicios documentales
  validan que la ruta a leer, borrar o abrir esté dentro de los directorios
  gestionados, el gestor documental restringe las rutas que entrega al
  lanzador del sistema a ubicaciones gestionadas o temporales con extensión
  permitida, y los nombres de archivo que se concatenan a un directorio se
  validan como nombre simple. Una fila manipulada ya no puede provocar la
  lectura, el borrado o la ejecución de un archivo arbitrario.
- **Integridad referencial efectiva.** Las conexiones de SQLite activan
  `PRAGMA foreign_keys=ON` (era la única forma de que el esquema declarado
  se cumpliera: sin él, documentos, pagos y contratos podían quedar
  apuntando a un empleado inexistente).
- **Fin del truncado silencioso.** `get_all` ya no recorta en 100 filas por
  omisión: la tabla de nómina y las estadísticas del dashboard solo veían
  los primeros cien registros. Las estadísticas de pagos e incidencias se
  agregan en SQL (`GROUP BY`) en lugar de cargar todas las filas para
  contarlas, y la lectura por identificador usa el mapa de identidad de la
  sesión, eliminando el patrón N+1 de los listados que resuelven el nombre
  del empleado fila por fila.
- **Sin temporales huérfanos.** La previsualización de documentos guardados
  en la base de datos creaba una copia temporal que nadie borraba; ahora se
  elimina al abrir el siguiente documento y al salir del módulo.
- **Escrituras y borrados diagnosticables.** El gestor documental registra
  los fallos de copia, movimiento y borrado (antes devolvía `False` en
  silencio) y rechaza la categoría de exportación `..`, que escapaba del
  directorio de exportaciones.
- **Ciclo de vida de las sesiones.** `close_session` solo libera el registry
  scoped cuando la sesión cerrada es la del hilo; cerrar una sesión
  independiente (`new_session`, como la de la ventana principal) invalidaba
  la sesión compartida que otro consumidor del mismo hilo estuviera usando.
- **Un único listado de extensiones abribles.** `EXTENSIONES_ABRIBLES` vive
  en `helpers.py` y lo consumen tanto el gestor documental como
  `abrir_con_aplicacion_predeterminada`, que ahora exige que la ruta sea un
  archivo real con extensión permitida antes de entregarla al sistema.
- **Limpieza de datos con criterio.** `cleanup_old_files` ya no borra
  documentos ni fotografías por fecha de modificación salvo petición
  explícita (dejaría registros activos sin archivo) y el arranque purga los
  temporales de la ejecución anterior (`limpiar_temporales`), que antes se
  acumulaban sin límite en `tmp/`.

### 11. Correcciones de la revisión final (consola y análisis estático)

- **La consola del agente no ensucia su propia salida.** El registro de
  `py -3 -m sync_agent` se escribía en stdout, de modo que `estado --json` y
  `conflictos --json` devolvían una línea de registro delante del JSON y
  ningún programa podía consumirlos. El registro va ahora a stderr, la salida
  estándar queda solo para el resultado del comando y la suite lo verifica en
  ambas salidas.
- **La interfaz de consola entra en las pruebas.** `sync_agent/__main__.py`
  (los seis subcomandos) no tenía ninguna prueba: se ejecuta ahora de extremo a
  extremo —la adopción de los datos previos en `init`, el estado y la bandeja
  de conflictos, el alta y la baja de puestos, la exportación de conflictos del
  nodo central y los códigos de retorno 0/1/2—, lo que de paso descubrió el
  defecto anterior.
- **Tipado estático del paquete de sincronización.** `mypy` no estaba
  instalado y el paquete nunca se había verificado: aparecieron veintiocho
  hallazgos (retenciones de `Any`, tablas consultadas a través de un `type` sin
  atributos, la espera creciente del agente anotada como entero). Quedan
  corregidos, junto con los de `incidencia_service` y `documento_service`, que
  declaran `_ruta_gestionada` como `TypeGuard`: la columna puede ser nula y
  quien pregunta queda con una ruta no nula.
- **`int ** int` no está tipado.** El tipado de la biblioteca estándar declara
  esa potencia como `Any`, así que la espera entre reintentos lleva anotación
  explícita para no perder el tipo numérico ante el verificador.
- **Lectura de los comandos del sistema.** `reg`, `taskkill`, `tasklist` y
  `schtasks` escriben en la página de códigos OEM de Windows mientras que
  Python 3.15 decodifica en UTF-8: un acento en un mensaje localizado hacía
  fallar la lectura dentro del hilo de `subprocess` y la salida del comando se
  perdía. Los nueve usos del actualizador se leen ahora con `errors="replace"`.
- **`.flake8` existe de verdad:** la estructura documentada lo declaraba desde
  las primeras versiones, pero el archivo no estaba. Declara la verificación
  que ya se aplicaba (F/E9/W6 y línea de 100) para que `flake8 src/` sea
  reproducible.

### Sincronización de datos entre puestos (`sync_agent/`)

Los puestos del colegio dejaron de ser islas: ahora replican los datos
institucionales entre sí a través de un **nodo central** de la intranet, sin
dejar de escribir en su propio SQLite en ningún momento.

- **Paquete independiente.** `sync_agent/` se puede ejecutar solo
  (`py -3 -m sync_agent`) o funcionar embebido en la aplicación: la captura se
  engancha al ORM en el arranque y el agente vive en un hilo de fondo. Nada de
  esto es obligatorio; una instalación sin configurar sigue funcionando igual.
- **Modo offline real.** El usuario escribe siempre en local y los cambios
  quedan encolados con su marca de tiempo. Si no hay red, el ciclo falla sin
  romper nada y reintenta con espera creciente (30 s → 60 s → 120 s → 300 s,
  con algo de azar para no golpear todos a la vez cuando vuelve la conexión).
- **Captura en la misma transacción.** Un enganche a los eventos de `Session`
  anota qué cambió antes de que el ORM vuelva a la base, y la operación queda en
  el journal junto al dato. Una transacción deshecha no anuncia nada: el sistema
  nunca replica lo que no llegó a confirmarse.
- **Identidad global por UUID.** Cada fila tiene un UUID (`sync_ids`) y se une a
  su equivalente en otros puestos por su clave natural (`empleados.cedula`,
  `contratos.numero`, `configuraciones.clave`), de modo que el mismo registro
  creado en dos equipos es uno solo.
- **Mezcla por campo, no por fila.** Dos puestos que editan columnas distintas
  del mismo registro conservan **ambas** ediciones; solo cuando tocan la misma
  columna hay un ganador, elegido con un orden total y determinista
  (`momento`, `equipo`, `operación`) que hace converger a todos los nodos sin
  importar el orden de llegada. Los campos económicos (salarios y montos) dejan
  conflicto **aunque gane el valor remoto**, para poder auditarlos.
- **Nada se descarta en silencio.** El valor perdedor de cada choque queda en
  una bandeja de conflictos, visible en Configuración → Sincronización y por
  consola (`py -3 -m sync_agent conflictos`).
- **Borrados con criterio.** Un borrado posterior gana, pero una edición
  posterior a un borrado **revive** la fila: perder un dato recién editado es
  peor que resucitar un registro borrado por error.
- **Binarios por hash.** Documentos e incidencias viajan siempre como hash y
  tamaño; el contenido se transfiere solo si no supera el límite (5 MB por
  defecto) y queda deduplicado en el nodo central.
- **Usuarios y preferencias no viajan.** La tabla `usuarios` no se replica
  (cada puesto administra sus cuentas) y tampoco las preferencias locales
  (tema, respaldos, ajustes del propio agente).
- **Captura de lo que ya existía.** `adoptar_existentes()` da identidad global
  a los datos cargados antes de instalar el agente —idempotente y sin modificar
  nada—, que de otro modo nunca se anunciarían (nadie los ha modificado desde
  entonces).
- **Nodo central sin dependencias nuevas.** Servicio HTTP de la biblioteca
  estándar que escribe el SQLite central en WAL como único escritor, con `seq`
  global autoritativo, autenticación por token hasheado (PBKDF2), límite de
  peticiones por minuto y TLS opcional.
- **Interfaz integrada.** Indicador en la barra de estado, botón «Sincronizar
  ahora» y una pestaña de Sincronización (estado, contadores, prueba de
  conexión, bandeja de conflictos y adopción de datos previos).
- **Auditoría.** Los ciclos y sus incidencias se registran con el nuevo tipo de
  evento `SYNC_ACTIVITY`.

## Novedades de la Versión 2.79

### Actualización automática (cada 2 días)

- El actualizador (`updater/`) queda **incluido en el instalador** y se
  programa en el Programador de tareas de Windows para ejecutarse
  **cada 2 días a las 09:00** (antes: cada 6 horas + al iniciar sesión).
- Nueva **ventana de estado** (`updater/updater_gui.py`) que informa de
  cada etapa (comprobando, descargando con porcentaje, instalando,
  resultado) y se cierra sola al terminar.
- Nuevo **ícono en la bandeja del sistema** (`updater/tray_icon.py`,
  Windows) implementado solo con ctypes: menú contextual con buscar
  ahora, mostrar ventana y salir.
- El instalador lo registra al instalar (`--register-only`) y lo
  desprograma al desinstalar (`--unregister`); se elimina también la
  tarea antigua.
- Modo de ejecución con `--check` (texto) o con ventana (`--gui`); el
  UAC de registro no duplica ventanas.

### Distribución y CI/CD

- **Versión portable de Linux** generada automáticamente en GitHub Actions:
  el workflow `build.yml` compila la aplicación con PyInstaller dentro de
  un contenedor **Ubuntu 22.04** (glibc 2.35, el mismo `spec/app.spec` que
  Windows) y publica un `tar.gz` portable en los artefactos y Releases de
  cada push. Funciona en Ubuntu 22.04, Debian 12 y Debian 13 (verificado en
  CI con selftests en contenedores `ubuntu:22.04`, `debian:12` y `debian:13`).
- El spec de PyInstaller es ahora multiplataforma: el icono y el recurso
  de versión (`version_info.txt`) solo se aplican en Windows.
- La versión del sistema pasa a **2.79** (archivo `VERSION`, `pyproject.toml`,
  instalador Inno Setup y `APP_VERSION_DEFAULT`).

## Novedades de la Versión 1.0.4

### Interfaz y Usabilidad

- **Tema oscuro/claro configurable** con botón en la cabecera y
  preferencia persistente (`apariencia_modo` en la configuración);
  aplica también a la ventana de inicio de sesión.
- **Atajos de teclado** en la ventana principal: Ctrl+1..6 (módulos),
  Ctrl+N (nuevo registro), Ctrl+F (buscar), Ctrl+S (guardar), F5
  (actualizar) y Esc (cerrar diálogos / limpiar selección). *(En la versión
  vigente los atajos de módulo son Ctrl+1..9; ver «Versión vigente: 3.0.1».)*
- **Botones Ayuda y Acerca de** en la cabecera con guía rápida e
  información de la aplicación.
- **Tarjetas del Dashboard navegables**: un clic lleva al módulo
  correspondiente.
- Cierre de todos los diálogos con la tecla **Esc**.

### Documentación

- Corregidos errores de codificación (emoji dañados) en `README.md` y
  `ESTRUCTURA_PROYECTO_COMPLETO.md`.
- Corregida la estructura de listas de `GUIA_USUARIO.md` y actualizada
  a la versión vigente.
- Ampliada `DOCUMENTACION_TECNICA.md` (theme, atajos, Security,
  AuditLogger, BackupManager, Exporter, modelo Usuario).

### Técnicas

1. **Base de Datos**
   - SQLite como motor persistente (con directorio de datos configurable)
   - Migraciones ligeras e idempotentes de esquema (`migrar_columnas`),
     cubiertas por `tests/test_migraciones.py`
   - PostgreSQL/MySQL y migraciones con Alembic quedan como trabajo
     futuro para despliegues multi-usuario

2. **Performance**
   - Índices en las consultas frecuentes (búsqueda por cédula, nombre y periodo)
   - Caching de consultas y lazy loading quedan como mejoras pendientes
     para grandes volúmenes de datos

3. **Testing** *(cifras históricas de la versión 1.0.4; la medición vigente se
   realiza con cada ejecución de la suite)*
   - **295 pruebas automatizadas** (unitarias, de integración y de humo
     GUI), todas exitosas en su momento
   - Cobertura de código: **57% total**; en la lógica de negocio (modelos,
     repositorios, servicios y utilidades) la cobertura supera el 70%
   - **Pruebas de humo GUI** (`tests/test_gui_smoke.py`) instancian la
     ventana principal, el login y los marcos de cada módulo con Tk real;
     se omiten automáticamente en entornos sin pantalla

### Robustería (fallbacks y anti-fugas)

- **Manejador global de excepciones** (`sys.excepthook` y
  `threading.excepthook`): cualquier error no capturado se registra en el
  log y en la auditoría y se muestra al usuario con un mensaje amigable,
  en lugar de terminar en silencio.
- **Limpieza garantizada de sesión**: la sesión de la ventana principal se
  cierra siempre (`try/finally`), incluso si la construcción o la
  ejecución fallan; si la construcción falla a mitad de camino se libera
  la sesión scoped del hilo.
- **Selección de filas corregida**: el doble clic y el clic derecho ahora
  seleccionan la fila bajo el cursor (`_seleccionar_fila_click`) en todos
  los módulos, de modo que "Ver detalles", "Editar" y el menú contextual
  funcionan siempre.
- **Sección de auditoría ampliada**: botón **Manual** con la guía de uso
  y doble clic sobre un evento para ver su detalle completo (datos
  técnicos, IP, errores).

## Mantenimiento

### Tareas Regulares

1. **Copias de Seguridad**
   - Base de datos
   - Documentos digitales
   - Configuración

2. **Actualizaciones**
   - Dependencias
   - Seguridad
   - Funcionalidades

3. **Monitoreo**
   - Logs del sistema
   - Performance
   - Errores

## Solución de Problemas

### Problemas Comunes y Soluciones

1. **Error al iniciar**
   - Verificar Python 3.15+
   - Reinstalar dependencias
   - Verificar permisos

2. **Error de base de datos**
   - Restaurar el respaldo más reciente desde la configuración
   - Reiniciar aplicación
   - Verificar espacio en disco
   - Solo como último recurso (y tras respaldar), eliminar el archivo .db

3. **Problemas con GUI**
   - Verificar CustomTkinter instalado
   - Reinstalar dependencias GUI
   - Verificar compatibilidad de sistema

## Conclusión

El sistema se encuentra en un estado funcional y bien documentado. La arquitectura modular facilita el mantenimiento y la expansión futura. Todas las funcionalidades principales están implementadas y probadas.

Para más información, consulte:
- `README.md` - Visión general del proyecto
- `DOCUMENTACION_TECNICA.md` - Detalles técnicos
- `GUIA_USUARIO.md` - Manual para usuarios finales

---

**Versión**: 3.0.1  
**Estado**: Estable (a la espera de ejecutar la suite en un equipo con Python)  
**Última actualización**: 2026