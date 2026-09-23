# Notas de Desarrollo - Sistema de Gestión de Personal

## Estado del Proyecto

El proyecto se encuentra en un estado estable y funcional con todas las funcionalidades principales implementadas y documentadas.

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

6. **Control de Asistencia**
   - Registro de jornadas con cálculo de horas y tardanzas
   - Horarios por empleado y día de la semana
   - Horas extra clasificadas por recargo
   - Marcado automático desde incidencias aprobadas

7. **Contratos Laborales**
   - Alta, renovación y terminación con finiquito
   - Unicidad del contrato vigente y numeración automática
   - Control de contratos por vencer y vencidos

8. **Anticipos y Préstamos**
   - Solicitud, aprobación o rechazo y seguimiento del saldo
   - Tope de descuento sobre el salario y sobre el neto de la nómina
   - Plan de pagos y descuento automático en el pago

9. **Alertas del Sistema**
   - Alertas accionables por severidad con navegación al módulo
   - Vencimientos, pendientes, respaldos y credenciales

10. **Panel Analítico**
   - Indicadores clave y gráficos propios (barras, dona, línea)
   - Reportes PDF de asistencia, contratos, préstamos y alertas

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
│   │   ├── asistencia_frame.py # Módulo de asistencia
│   │   ├── contratos_frame.py  # Módulo de contratos
│   │   ├── prestamos_frame.py  # Módulo de préstamos
│   │   ├── alertas_frame.py    # Módulo de alertas
│   │   ├── alertas_panel.py    # Panel de alertas (Dashboard)
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
│   │   ├── horario.py         # Horario semanal
│   │   ├── asistencia.py      # Registro de jornada
│   │   ├── contrato.py        # Contrato laboral
│   │   ├── prestamo.py        # Anticipo o préstamo
│   │   ├── configuracion.py   # Modelo configuración
│   │   └── usuario.py        # Modelo usuario
│   ├── nomina/                  # Motor de cálculo puro
│   │   ├── tipos.py            # Datos de entrada y resultado
│   │   ├── parametros.py       # Carga y validación de parámetros
│   │   ├── isr.py             # Impuesto por tramos progresivos
│   │   ├── seguridad_social.py # Aportes con techos
│   │   ├── horas_extra.py      # Recargos por tipo de jornada
│   │   ├── prestaciones.py     # Aguinaldo, vacaciones, prestaciones
│   │   ├── prestamos.py        # Amortización de cuotas
│   │   ├── finiquito.py        # Liquidación completa
│   │   └── motor.py            # Orquestador del cálculo
│   ├── repositories/            # Acceso a datos
│   │   ├── base_repository.py # Repositorio base
│   │   ├── empleado_repository.py
│   │   ├── documento_repository.py
│   │   ├── incidencia_repository.py
│   │   ├── pago_repository.py
│   │   ├── horario_repository.py
│   │   ├── asistencia_repository.py
│   │   ├── contrato_repository.py
│   │   ├── prestamo_repository.py
│   │   ├── configuracion_repository.py
│   │   └── usuario_repository.py
│   ├── services/                # Lógica de negocio
│   │   ├── empleado_service.py
│   │   ├── documento_service.py
│   │   ├── incidencia_service.py
│   │   ├── pago_service.py
│   │   ├── asistencia_service.py
│   │   ├── contrato_service.py
│   │   ├── prestamo_service.py
│   │   ├── alerta_service.py
│   │   ├── configuracion_service.py
│   │   └── auth_service.py
│   ├── utils/                   # Utilidades
│   │   ├── helpers.py          # Funciones auxiliares
│   │   ├── validators.py      # Validadores
│   │   ├── jornada.py         # Cálculos de jornada laboral
│   │   ├── document_manager.py # Gestión documentos
│   │   ├── pdf_generator.py    # Generación PDF
│   │   ├── security.py        # Hash de contraseñas y permisos
│   │   ├── audit_logger.py    # Registro de auditoría
│   │   ├── backup_manager.py  # Copias de seguridad
│   │   ├── backup_scheduler.py # Respaldos automáticos programados
│   │   └── exporter.py        # Exportación Excel/CSV
│   └── main.py                 # Punto de entrada
├── tests/                       # Pruebas unitarias
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

## Novedades de la Versión 2.82

Esta versión **desarrolla** el sistema: añade los dominios que faltaban
(asistencia, contratos y préstamos), un motor de nómina real con tabla
progresiva de impuestos y prestaciones, alertas accionables, respaldos
programados y un panel analítico. Nada de lo anterior se retiró: los
contratos, columnas y cálculos de las versiones previas siguen
funcionando (las bases existentes se actualizan de forma aditiva).

### 1. Motor de nómina (`src/nomina/`)

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
- **Finiquito completo** con anticipos y otras deducciones
  (`src/nomina/finiquito.py`).
- **Préstamos**: cuota calculada hacia abajo, plan de amortización que
  cuadra exactamente con el monto y avance de saldo
  (`src/nomina/prestamos.py`).
- **Modalidades**: `porcentaje` reproduce exactamente el cálculo
  histórico y `tramos` activa el motor completo; el modo se elige con
  `modo_calculo_nomina` en Configuración.
- Las deducciones capturadas a mano por el usuario **mandan** sobre el
  cálculo automático, y el neto nunca puede ser negativo.

### 2. Asistencia y horarios

- Modelos `Horario` y `Asistencia` con horas trabajadas, tardanza y horas
  extra clasificadas por recargo.
- `src/utils/jornada.py`: cálculos puros de jornada (turnos que cruzan la
  medianoche, descanso, tolerancia, feriados y días de descanso
  configurables).
- En feriado o día de descanso laborado no hay jornada prevista que
  cumplir: todo lo trabajado se paga como hora feriada.
- Las **incidencias aprobadas** marcan la asistencia del período de forma
  idempotente (reaplicar el rango no reescribe días ya justificados).
- La nómina consume las horas extra del período desde la asistencia.

### 3. Contratos

- Modelo `Contrato` con ciclo de vida completo (vigente, renovado,
  vencido, terminado), unicidad del contrato vigente por empleado y
  numeración generada automáticamente.
- **Renovación encadenada**: el nuevo contrato arranca el día siguiente
  al vencimiento y queda enlazado al anterior (`contrato_anterior_id`).
- **Terminación con finiquito**: calcula la liquidación y la registra como
  pago de tipo `liquidacion` (sin aportes de seguridad social), de modo
  que la nómina refleje el egreso.
- Sincronización automática de estados (vencidos y renovables) y alertas
  de vencimiento.

### 4. Anticipos y préstamos

- Modelo `Prestamo` con flujo solicitud → aprobación/rechazo → descuento
  por cuotas → cierre.
- Tope de descuento configurable sobre el salario y, al aplicar la cuota
  en la nómina, sobre el neto disponible del empleado.
- Los anticipos son de una sola cuota por definición.

### 5. Alertas accionables

- `src/services/alerta_service.py` reúne documentos por vencer, contratos
  vencidos o por vencer, **empleados sin contrato vigente**, incidencias
  pendientes antiguas, asistencia sin registrar, ausentismo elevado,
  préstamos por aprobar, pagos pendientes antiguos, respaldos atrasados y
  credenciales caducadas.
- Cada alerta indica severidad, cantidad, detalle y el **módulo donde se
  resuelve**; el panel y el módulo de Alertas permiten ir directo.

### 6. Respaldos programados y política de credenciales

- `src/utils/backup_scheduler.py`: respaldo automático según
  `backup_interval_hours` (con interruptor `backup_enabled`), verificación
  de integridad del archivo generado y estado consultable.
- Credenciales: bloqueo temporal tras varios intentos fallidos,
  caducidad de la contraseña, prohibición de repetir las últimas claves y
  de reutilizar la vigente, desbloqueo administrativo e historial.

### 7. Panel analítico y reportes

- `src/gui/widgets/graficos.py`: gráficos de barras, dona y línea más
  tarjetas de indicador dibujados sobre `Canvas` (sin dependencias nuevas).
- El Dashboard incorpora KPI reales (nómina del mes, ausentismo, contratos
  por vencer, saldo por cobrar), tres gráficos y el panel de alertas,
  dentro de un contenedor desplazable.
- Nuevos reportes PDF: asistencia, contratos, préstamos y alertas, además
  de los existentes; exportación multihoja para Excel.

### 8. Interfaz

- Nuevos módulos en la barra lateral: **Asistencia**, **Contratos**,
  **Préstamos** y **Alertas** (10 módulos en total, navegables con
  `Ctrl+1`…`Ctrl+9` y `Ctrl+0`; `Ctrl+10` no es una secuencia válida de Tk),
  con los permisos por rol ampliados.
- `frames.py` se conserva como módulo histórico y los dominios nuevos
  viven en módulos propios por responsabilidad
  (`asistencia_frame.py`, `contratos_frame.py`, `prestamos_frame.py`,
  `alertas_frame.py`, `alertas_panel.py`).
- Los servicios solo se instancian cuando el módulo se abre y toda
  operación que puede fallar muestra un mensaje entendible en lugar de
  dejar la ventana muda.

### 9. Calidad

- `mypy` sin errores en 75 archivos de `src/` y cero `# type: ignore`;
  `flake8` (F/E9/W6) sin hallazgos.
- Los enums del dominio (`BaseEnum.coerce`) normalizan cualquier valor
  recibido como texto a su miembro correspondiente: las columnas tipadas
  de SQLAlchemy dejan de recibir cadenas sueltas.
- **455 pruebas** en verde (eran 326): suites nuevas para el motor de
  nómina, jornada, asistencia, contratos, préstamos, alertas y política de
  credenciales/respaldos.

### 10. Correcciones de esta versión

- Las horas trabajadas en feriado o día de descanso no generaban horas
  extra: se comparaban contra la jornada prevista de un día laboral.
- Aplicar incidencias aprobadas dos veces reescribía los días ya marcados.
- `actualizar_contrato` y `actualizar_asistencia` escribían texto plano en
  columnas tipadas por enum; ahora normalizan el valor.
- La alerta de empleados sin contrato vigente no existía pese a que el
  panel mostraba el indicador.
- Cambiar la contraseña por la misma vigente estaba permitido.

### 11. Interfaz: concurrencia y ciclo de vida

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
  (actualizar) y Esc (cerrar diálogos / limpiar selección).
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

3. **Testing**
   - **295 pruebas automatizadas** (unitarias, de integración y de humo
     GUI), todas exitosas
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

**Versión**: 2.82  
**Estado**: Estable  
**Última actualización**: 2026