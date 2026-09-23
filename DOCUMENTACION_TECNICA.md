# Documentación Técnica del Sistema

## Descripción General

El Sistema de Gestión de Personal y Nómina es una aplicación desarrollada en Python que permite administrar eficientemente los recursos humanos de instituciones educativas. El sistema cuenta con una interfaz gráfica moderna y una arquitectura modular que facilita su mantenimiento y expansión.

## Arquitectura del Sistema

### Patrones de Diseño Implementados

1. **Repository Pattern**: Separación entre lógica de negocio y acceso a datos
2. **Service Layer**: Lógica de negocio encapsulada en servicios
3. **ORM (Object-Relational Mapping)**: Uso de SQLAlchemy para mapeo de base de datos
4. **Dependency Injection**: Inyección de dependencias para mayor flexibilidad

### Estructura de Capas

```
┌─────────────────────────────────────┐
│         Interfaz Gráfica (GUI)      │
│    CustomTkinter + Tkinter Widgets  │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│           Capa de Servicios         │
│        Lógica de Negocio             │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         Capa de Repositorios        │
│         Acceso a Datos               │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│          Capa de Modelos            │
│         SQLAlchemy ORM               │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│        Base de Datos SQLite         │
└─────────────────────────────────────┘
```

## Modelos de Datos

### Modelo Base

Todos los modelos heredan de `BaseModel` que proporciona:
- `id`: Identificador único autoincremental
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización
- `to_dict()`: Método para convertir a diccionario

### Modelo Empleado

Representa la información completa de un empleado incluyendo:
- **Datos Personales**: Nombres, apellidos, cédula, fecha de nacimiento, género, estado civil
- **Datos Físicos**: Peso, altura, tipo de sangre, foto de perfil
- **Datos de Contacto**: Teléfono, celular, email, dirección, ciudad
- **Datos Laborales**: Tipo de empleado, cargo, departamento, fecha de contratación, salario
- **Datos Académicos**: Nivel educativo, especialidad, título obtenido
- **Contacto de Emergencia**: Nombre, teléfono y relación

### Modelo Documento

Gestiona la documentación digitalizada de empleados:
- **Información del Documento**: Tipo, título, descripción, número de documento
- **Fechas**: Emisión y vencimiento
- **Archivo**: Nombre, ruta, tamaño, tipo MIME, contenido binario
- **Estado**: Activo/inactivo, observaciones

### Modelo Incidencia

Controla permisos, reposos y ausencias:
- **Información de Incidencia**: Tipo, estado, fechas, motivo
- **Días**: Solicitados y aprobados
- **Documento de Soporte**: Archivo digital como respaldo
- **Aprobación**: Quién aprobó, fecha, comentarios
- **Impacto en Nómina**: Indica si afecta el cálculo de salarios

### Modelo Pago

Registra los pagos y nóminas:
- **Información del Pago**: Tipo, método de pago, periodo
- **Montos**: Bruto, neto, descuentos, bonificaciones, horas extra
- **Desglose**: Salario base, deducciones (seguro, pensión, impuesto)
- **Estado**: Pagado/pendiente, fecha de registro

### Modelo Horario

Define la jornada semanal de un empleado:
- Día de la semana, hora de inicio y fin, descanso y tolerancia
- Tipo de jornada (diurna, nocturna o mixta), que determina el recargo de
  las horas extra
- Cálculo de minutos y horas de la jornada

### Modelo Asistencia

Registro diario de la jornada:
- Fecha, horas de entrada y salida, horas trabajadas y minutos de tardanza
- Horas extra clasificadas (diurnas, nocturnas y feriadas)
- Tipo (presente, tardanza, ausente, permiso, vacaciones, reposo, feriado),
  marca de justificada y vínculo con la incidencia que la respalda
- Propiedades `es_falta`, `tiene_tardanza` y `total_horas_extra`

### Modelo Contrato

Contrato laboral con su ciclo de vida:
- Número, tipo (indefinido, temporal, por obra o pasantía), cargo,
  departamento, salario pactado y horas semanales
- Fechas de inicio, fin y terminación, estado, renovación automática y
  enlace al contrato anterior
- Liquidación registrada, motivo de terminación y cláusulas
- Propiedades `esta_vigente`, `por_vencer()`, `dias_para_vencer`,
  `dias_vigencia` y salario diario y por hora

### Modelo Prestamo

Anticipo o préstamo al empleado:
- Tipo, estado, monto, número de cuotas, monto de cuota, cuotas pagadas y
  saldo (fuente de verdad de la amortización)
- Fechas de solicitud, aprobación y descuentos, motivo y usuario aprobador
- Propiedades `esta_activo`, `se_puede_descontar`, `porcentaje_pagado` y
  `monto_pagado`

### Modelo Usuario

Gestiona el acceso al sistema (autenticación y roles):
- **Credenciales**: `username` único y `password_hash` (PBKDF2)
- **Identidad**: Nombre completo
- **Rol**: admin, manager, user o viewer (enum `RolUsuario`)
- **Estado**: Activo/inactivo, debe cambiar contraseña, último acceso,
  intentos fallidos y bloqueo

### Modelo Configuración

Almacena la configuración del sistema en pares clave/valor tipados
(`string`, `int`, `float`, `bool` vía `valor_typed`):
- **Configuración General**: Nombre de institución, dirección, contacto
- **Configuración de Nómina**: Porcentajes de deducciones, salario mínimo
- **Configuración de RRHH**: Días de vacaciones, horas laborales
- **Configuración de Seguridad**: Respaldos y auditoría
- **Preferencias de interfaz**: `apariencia_modo` (tema oscuro/claro)

## Servicios del Sistema

### EmpleadoService

Encargado de la gestión completa de empleados:
- Crear, actualizar y eliminar empleados
- Búsqueda y filtrado avanzado
- Gestión de fotos de perfil
- Estadísticas y reportes
- Validación de datos

### DocumentoService

Maneja la gestión documental:
- Carga y almacenamiento de documentos
- Control de vencimientos
- Gestión por tipo y empleado
- Validación de archivos
- Generación de estadísticas

### IncidenciaService

Administra permisos y ausencias:
- Registro de incidencias
- Flujo de aprobación/rechazo
- Cálculo automático de días
- Gestión de documentos de soporte
- Control de incidencias vigentes

### PagoService

Procesa nóminas y pagos:
- Generación automática de nóminas
- Delega el cálculo en el motor de nómina (`src/nomina`) y conserva el
  cálculo porcentual histórico cuando esa modalidad está activa
- Descuento de la cuota de préstamo respetando el tope sobre el neto
- Toma las horas extra del período desde el servicio de asistencia
- Gestión de pagos pendientes y pagos de liquidación
- Reportes por periodo e integración con incidencias

### AsistenciaService

Registra la jornada real del personal:
- Alta y edición de jornadas con horas trabajadas, tardanzas y horas
  extra clasificadas (diurnas, nocturnas, feriadas)
- Cálculo contra el horario del empleado o contra la jornada por defecto
- Ausencias justificadas automáticas desde las incidencias aprobadas
  (operación idempotente)
- Totales y resumen por período para la nómina y los reportes
- Empleados con exceso de horas extra semanales

### ContratoService

Administra el ciclo de vida contractual:
- Alta con validaciones y numeración automática; un solo contrato vigente
  por empleado
- Renovación encadenada (arranca el día siguiente al vencimiento y enlaza
  con el contrato anterior)
- Terminación con cálculo del finiquito y registro del pago de liquidación
- Sincronización de estados (vencidos y renovables) y listados por vencer
- Sincronización del cargo, departamento y salario pactados con el empleado

### PrestamoService

Controla anticipos y préstamos:
- Solicitud con validación del tope de descuento sobre el salario
- Aprobación, rechazo y cancelación con auditoría
- Cuota pendiente y descuento aplicable al neto del pago
- Amortización (saldo, cuotas pagadas y cierre automático)
- Plan de pagos y estadísticas de la cartera

### AlertaService

Genera las alertas accionables del sistema:
- Documentos, contratos (vencidos y por vencer), empleados sin contrato
- Incidencias pendientes antiguas, asistencia sin registrar y ausentismo
- Préstamos por aprobar, pagos pendientes antiguos y respaldos atrasados
- Credenciales caducadas y cuentas bloqueadas
- Orden por severidad y `resumen()` para la barra lateral y el panel

### ConfiguracionService

Controla la configuración del sistema:
- Gestión de parámetros institucionales
- Configuración por categorías
- Validación de valores
- Recuperación de configuraciones

## Motor de Nómina (`src/nomina`)

Paquete de **cálculo puro**: no accede a la base de datos ni a la interfaz,
recibe datos ya cargados y devuelve un resultado verificable. Todas las
operaciones usan `Decimal` con redondeo comercial (`ROUND_HALF_UP`) a dos
decimales, de modo que un recibo nunca queda con centavos imposibles.

| Módulo | Responsabilidad |
| --- | --- |
| `tipos.py` | Datos de entrada/salida (`EntradaNomina`, `ResultadoNomina`, `HorasExtra`, `TramoISR`, `ParametrosNomina`, `EntradaFiniquito`, `ResultadoFiniquito`) y utilidades `a_decimal`/`redondear` |
| `parametros.py` | Carga de los parámetros desde la configuración, valores por defecto, construcción de la tabla de tramos y validación de coherencia |
| `seguridad_social.py` | Base afectada con techos, aportes del empleado y del patrono |
| `isr.py` | Tramo aplicable, impuesto del período, ajuste anual y tasa efectiva |
| `horas_extra.py` | Valor de la hora ordinaria y montos por tipo de recargo |
| `prestaciones.py` | Antigüedad, aguinaldo, bono vacacional, vacaciones, prestaciones, indemnización y preaviso |
| `prestamos.py` | Cuota, plan de amortización, descuento y validación de solicitudes |
| `finiquito.py` | Liquidación completa y días de vacaciones pendientes |
| `motor.py` | Orquestador: `calcular_nomina`, `lineas_recibo` y `resumen_costo_empleador` |

**Modalidades** (`ParametrosNomina.modo`):

- `porcentaje`: aplica los porcentajes configurados sobre el salario base y
  reproduce exactamente el cálculo histórico del sistema.
- `tramos`: cálculo completo con techos de cotización, tabla progresiva de
  ISR (cuota fija + tasa sobre el excedente), base gravable = ingresos menos
  aportes exentos, aportes patronales y recargos de horas extra.

Invariantes garantizadas: el neto nunca es negativo, el impuesto nunca
supera la base y un dato sucio en la configuración cae al valor por defecto
en lugar de romper el cálculo.

## Utilidades del Sistema

### Helpers

Funciones auxiliares comunes:
- Formateo de fechas y monedas
- Validación de datos
- Cálculo de edad
- Gestión de archivos
- Generación de nombres únicos

### Validators

Validadores especializados:
- Validación de datos de empleados
- Validación de documentos
- Validación de incidencias
- Validación de pagos
- Validación de configuraciones

### DocumentManager

Gestión de archivos físicos:
- Guardado y recuperación de documentos
- Gestión de fotos de perfil
- Control de espacios
- Validación de tipos de archivo

### Security

Validación y saneamiento de datos de entrada, verificación de permisos
por rol y cifrado de contraseñas:
- `SecurityValidator`: validación de patrones (email, teléfono, cédula,
  nombres de archivo), saneamiento de strings y archivos, control de
  tamaño y extensión, rango numérico
- `hash_password` / `verify_password`: PBKDF2-HMAC-SHA256 con salt
  aleatorio (200.000 iteraciones) y compatibilidad con hashes legados
- `PermissionChecker`: matriz de permisos por rol
  (create/read/update/delete/report/config/backup/restore) y de acceso
  a módulos
- `SecurityLogger`: registra eventos de seguridad en la auditoría

### AuditLogger

Registro persistente de eventos del sistema en archivos JSON:
- Eventos de sistema (inicio/cierre), autenticación, respaldos, cambios
  de datos y errores
- Consulta de eventos recientes y exportación a Excel/CSV desde la GUI
- Se activa/desactiva desde Configuración > Seguridad y Respaldo

### Jornada

`src/utils/jornada.py` reúne los cálculos puros de jornada laboral:
- Minutos y horas entre marcas de entrada y salida (incluidos los turnos
  que cruzan la medianoche) y descuento del descanso
- Minutos de tardanza sobre la hora prevista, aplicando la tolerancia
- Reconocimiento de feriados (desde lista o JSON) y de días de descanso
  configurables
- Clasificación de las horas extra por tipo de jornada y de los registros
  de asistencia (presente, tardanza o ausente)

### BackupScheduler

`src/utils/backup_scheduler.py` programa los respaldos automáticos:
- Intervalo en horas e interruptor de habilitación desde la configuración
- ``ultima_ejecucion``realmente usada (incluye los respaldos ya guardados,
  de modo que reiniciar la aplicación no respalde antes de tiempo)
- Verificación de integridad del archivo generado y estado consultable
- ``comprobar_y_ejecutar``con callback para avisar a la interfaz y
  ``programar``/``cancelar``sobre el bucle de eventos de Tk
- ``ejecutar(forzar=True)``para el botón "Respaldar ahora", y nunca lanza
  excepciones: un respaldo fallido no debe tumbar la aplicación

### BackupManager

Copias de seguridad de la base de datos:
- Creación manual y automática (al cerrar o por intervalo configurable
  en horas)
- Compresión opcional, metadatos en `backup_metadata.json`
- Verificación de integridad (archivo presente, tamaño y checksum)
- Restauración y eliminación desde la interfaz, con confirmación
- Restauración programática con cierre previo de la sesión (Windows)

### Exporter

Exportación de listados a archivos:
- **Excel (.xlsx)** mediante `openpyxl`
- **CSV** con BOM UTF-8 para compatibilidad con Excel
- Uso común desde todos los módulos (empleados, documentos,
  incidencias, pagos, auditoría)

## Interfaz Gráfica

### Componentes Principales

1. **LoginWindow**: Inicio de sesión con credenciales, aviso de primer
   acceso y obligación de cambiar la contraseña inicial
2. **MainWindow**: Ventana principal con barra lateral, cabecera, barra
   de estado, atajos de teclado y tema de apariencia
3. **DashboardFrame**: Panel de control con tarjetas estadísticas
   navegables y acciones rápidas
4. **EmpleadosFrame**: Gestión de empleados (CRUD, búsqueda, filtros,
   reportes PDF y exportación)
5. **DocumentosFrame**: Gestión documental con control de vencimientos
6. **IncidenciasFrame**: Control de permisos y ausencias con flujo de
   aprobación
7. **NominaFrame**: Procesamiento de nóminas, recibos y planillas PDF
8. **ConfiguracionFrame**: Configuración institucional, de nómina, RRHH,
   seguridad/respaldos, usuarios y auditoría
9. **AsistenciaFrame**: registro de jornadas, horarios, aplicación de
   incidencias aprobadas, totales del período y reporte PDF
10. **ContratosFrame**: alta, renovación, terminación con finiquito y
    control de vencimientos
11. **PrestamosFrame**: solicitudes, aprobación o rechazo, plan de pagos y
    cartera
12. **AlertasFrame** y **PanelAlertas**: alertas accionables por severidad
    con navegación al módulo y exportación PDF
13. **Widgets de gráficos** (`src/gui/widgets/graficos.py`): barras, dona,
    línea y tarjetas de indicador dibujadas sobre `Canvas`, sin
    dependencias externas de gráficos
14. **Diálogos (Toplevel)**: `EmpleadoDialog`, `EmpleadoDetailsDialog`,
    `DocumentoDialog`, `IncidenciaDialog`, `ApprovalDialog`, `PagoDialog`,
    `JornadaDialog`, `ContratoDialog`, `RenovacionDialog`,
    `TerminacionDialog`, `SolicitudDialog`, `UsuarioDialog`,
    `CambiarPasswordDialog`, `InfoDialog` (texto extenso para
    Ayuda/Acerca de). Todos se cierran con **Esc**

### Theme (Apariencia)

El módulo `src/gui/theme.py` centraliza la apariencia de la aplicación:

- Paletas **oscura** (`PALETA_OSCURA`) y **clara** (`PALETA_CLARA`) con
  claves semánticas (fondo, panel, campo, texto, acento, borde) en el
  diccionario global `COLORES`
- `aplicar_modo_apariencia(modo)`: cambia el modo de CustomTkinter,
  actualiza `COLORES` y reaplica los estilos ttk (tablas, combos, menús)
- Los frames leen los colores de `COLORES` al construirse; al alternar
  el tema, la ventana principal reconfigura su "chrome" y recrea el
  frame activo para que tome la paleta nueva
- La preferencia se guarda con la clave `apariencia_modo` ("Dark"/
  "Light") en la tabla de configuración y se aplica en el login y en
  la ventana principal
- `enable_windows_dpi_awareness()`: alta resolución en Windows
- `centrar_ventana`, `cancelar_after_pendientes`, `silenciar_errores_fondo`:
  utilidades de ventana y limpieza de temporizadores

### Características de la Interfaz

- Diseño moderno con tema oscuro por defecto y tema claro configurable
- Navegación por módulos con barra lateral, clic en tarjetas del
  Dashboard y atajos de teclado (Ctrl+1..6)
- Cabecera con acceso a Ayuda, Acerca de, tema de apariencia, cierre de
  sesión y salida
- Barra de estado inferior con reloj y mensajes contextuales
- Tablas con filtros y búsqueda
- Formularios de entrada validados
- Menús contextuales con clic derecho y doble clic para ver detalles
- Generación de reportes en tiempo real
- Adaptabilidad a diferentes tamaños de pantalla

### Atajos de Teclado

| Atajo | Acción |
| --- | --- |
| Ctrl+1 … Ctrl+6 | Navegar al módulo correspondiente |
| Ctrl+N | Nuevo registro en el módulo activo |
| Ctrl+F | Enfocar búsqueda/filtro |
| Ctrl+S | Guardar (Configuración) |
| F5 | Actualizar lista |
| Esc | Cerrar diálogo o limpiar selección |

Los atajos se enlazan en `MainWindow._bind_atajos()` y delegan en
métodos canónicos por tipo de frame (tablas `METODOS_REFRESCAR`,
`METODOS_NUEVO` y `METODOS_GUARDAR`), lo que permite ampliarlos sin
acoplar la ventana principal a cada módulo.

## Seguridad y Validación

### Medidas de Seguridad

- Almacenamiento local de datos (sin conexión a internet requerida; la
  actualización automática consulta GitHub de forma opcional)
- Validación de entradas de usuario
- Control de acceso por tipo de usuario y por módulo
- Contraseñas con hash **PBKDF2-HMAC-SHA256** (200.000 iteraciones,
  salt aleatorio de 16 bytes; formato `pbkdf2$iteraciones$salt$hash`),
  con compatibilidad de lectura para hashes SHA-256 legados
- Bloqueo de cuenta y contador de intentos fallidos de inicio de sesión
- Registro de auditoría persistente (archivos JSON) con eventos de
  sistema, autenticación, respaldos, cambios de datos y errores
- Verificación de integridad de respaldos (checksum)
- Copias de seguridad automáticas al cerrar y por intervalo configurable

### Validaciones Implementadas

- Validación de formatos de cédula
- Validación de correos electrónicos
- Validación de fechas (no futuras para nacimiento)
- Validación de rangos numéricos
- Validación de campos requeridos
- Validación de tipos de archivo

## Configuración

### Variables de Entorno

El sistema utiliza variables de entorno para configuración:
- `DATABASE_URL`: URL de conexión a base de datos
- `APP_NAME`: Nombre de la aplicación
- `DEBUG`: Modo de depuración
- `DOCUMENTS_PATH`: Ruta de documentos
- `PHOTOS_PATH`: Ruta de fotos
- `EXPORTS_PATH`: Ruta de exportaciones

### Configuración en Base de Datos

La configuración se almacena en la base de datos y puede modificarse desde la interfaz:
- Datos de la institución
- Parámetros de nómina
- Configuración de recursos humanos
- Preferencias del sistema

## Integración y Extensión

### Puntos de Extensión

El sistema está diseñado para facilitar la extensión:
- Agregar nuevos tipos de empleados
- Implementar nuevos tipos de documentos
- Crear nuevos reportes
- Integrar con otros sistemas
- Agregar nuevos métodos de pago

### API Potencial

Se puede extender para incluir:
- API REST para integración externa
- Servicios web para acceso remoto
- Integración con sistemas de nómina externos
- Conexión con sistemas de asistencia
- Integración con sistemas de facturación

## Actualización Automática (AutoUpdater)

El proyecto incluye un componente independiente de **actualización
automática** (`updater/`), empaquetado como ejecutable propio
(`SDEP_CPP5_AutoUpdater.exe`, PyInstaller onefile, sin consola) e
integrado en el instalador de Windows.

### Arquitectura

- `updater/auto_updater.py` — Lógica principal (solo biblioteca
  estándar): consulta la última Release de GitHub, descarga el
  instalador `Setup.exe`, lo instala en silencio y administra la tarea
  programada.
- `updater/updater_gui.py` — Ventana de estado en tkinter que muestra el
  progreso (comprobando, descargando con porcentaje, instalando,
  resultado) mediante los ganchos `on_progress` / `on_download`.
- `updater/tray_icon.py` — Ícono de la **bandeja del sistema** (Windows)
  implementado con `ctypes` (`Shell_NotifyIconW`), ventana oculta
  message-only y menú contextual (buscar ahora / mostrar ventana /
  salir). Es un no-op en sistemas que no sean Windows.
- `updater/updater.spec` — Spec de PyInstaller (onefile, tkinter, ícono).

### Programación (cada 2 días)

El actualizador crea una tarea en el Programador de tareas de Windows
(`schtasks /SC DAILY /MO 2 /ST 09:00`): comprueba novedades **cada 2
días a las 09:00** con privilegios elevados. El instalador la registra
al instalar (`--register-only`) y la elimina al desinstalar
(`--unregister`); la tarea antigua "al iniciar sesión" se elimina
automáticamente.

### Flujo de actualización

1. Consulta `releases/latest` de GitHub (3 intentos con espera creciente).
2. Compara la versión de la Release con la última instalada registrada
   (`%LOCALAPPDATA%\SDEP_CPP5uto_updater.json`).
3. Si hay versión nueva: cierra la aplicación si está abierta, descarga
   el instalador con reintentos y verificación de tamaño, y lo ejecuta en
   silencio (`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART`).
4. Registra la versión instalada y termina.

### Modos de ejecución

| Argumento         | Efecto |
|-------------------|--------|
| *(sin argumentos)*| Registra la tarea (si falta) y actualiza con ventana + bandeja |
| `--check`         | Solo consulta e informa (modo texto) |
| `--check --gui`   | Consulta con ventana de estado |
| `--register`      | Registra las tareas y actualiza |
| `--register-only` | Solo registra la tarea (lo usa el instalador) |
| `--unregister`    | Elimina las tareas (lo usa el desinstalador) |
| `--no-gui`        | Fuerza modo texto |

Variables de entorno: `SDEP_UPDATE_API_URL`, `SDEP_UPDATE_STATE_DIR`,
`SDEP_UPDATE_INSTALL_DIR`, `SDEP_UPDATE_INSTALL_IF_MISSING` (ver
`updater/README.md`).

## Mantenimiento

### Tareas de Mantenimiento Rutinario

- Copias de seguridad de la base de datos
- Limpieza de documentos obsoletos
- Actualización de configuraciones
- Revisión de logs del sistema
- Optimización de base de datos

### Solución de Problemas Comunes

- **Error de conexión a base de datos**: Verificar permisos de archivo
- **Error al cargar documentos**: Verificar espacio en disco
- **Problemas con la interfaz**: Reinstalar dependencias
- **Error en cálculos**: Verificar configuración de nómina

## Rendimiento y Optimización

### Consideraciones de Rendimiento

- Uso de índices en base de datos
- Paginación de resultados
- Carga diferida de relaciones
- Optimización de consultas
- Gestión eficiente de memoria

### Escalabilidad

El sistema puede manejar:
- Hasta 1000 empleados sin degradación significativa
- Miles de documentos por empleado
- Historial ilimitado de pagos
- Múltiples usuarios concurrentes (si se implementa servidor)

## Conclusión

Este sistema proporciona una solución completa y robusta para la gestión de personal en instituciones educativas, con una arquitectura bien diseñada que facilita su mantenimiento y expansión futura.