# CAPÍTULO IV: RESULTADOS

## 4.1 INTRODUCCIÓN

El presente capítulo expone los resultados obtenidos durante el desarrollo del Sistema de Gestión de Personal y Nómina para instituciones educativas y durante las pruebas técnicas aplicadas sobre el repositorio del proyecto. Se describe, en primer lugar, el sistema efectivamente construido —su arquitectura, sus módulos y sus características técnicas—; en segundo lugar, se presentan los hallazgos de la suite de pruebas automatizadas, de integración y de seguridad; y, finalmente, se define la estructura de registro de los resultados de usabilidad, de la implementación piloto y de la validación de hipótesis, cuya evidencia empírica se incorporará una vez concluida la aplicación del sistema en las instituciones participantes.

Conviene precisar, antes de continuar, el estatuto de la evidencia que se presenta. Los apartados 4.2 y 4.3 reportan resultados verificables de forma directa sobre el repositorio: la arquitectura está implementada en `src/`, los módulos son ejecutables, el esquema de base de datos se declara en los modelos y el número de funciones de prueba se cuenta sobre los archivos de `tests/`. Los apartados 4.4 a 4.7, en cambio, corresponden a la validación empírica con usuarios y, por consiguiente, su contenido se ofrece como estructura metodológica preparada para recibir las mediciones reales; los campos aún no medidos se señalan con el marcador `[por completar]`, conforme a la convención adoptada en todo el documento. Esta distinción evita atribuir al sistema resultados que todavía no han sido medidos y preserva la trazabilidad entre lo observado y lo afirmado.

## 4.2 DESCRIPCIÓN DEL SISTEMA DESARROLLADO

### 4.2.1 Arquitectura General

El sistema se materializó en una arquitectura de capas con separación estricta de responsabilidades. La organización del código en `src/` responde a cinco capas y a un dominio de cálculo independiente, decisión que permitió aislar la complejidad del cálculo de nómina del resto de la aplicación. La Tabla 4.1 resume la distribución del código fuente por capa, medida sobre la versión 2.82 del repositorio.

**Tabla 4.1. Distribución del código fuente por capa (versión 2.82)**

| Capa | Archivos | Líneas de código | Responsabilidad principal |
|------|----------|------------------|---------------------------|
| `src/models` | 13 | 1 832 | Entidades del dominio y enumeraciones (SQLAlchemy ORM) |
| `src/repositories` | 12 | 2 204 | Acceso a datos y consultas reutilizables |
| `src/services` | 11 | 4 609 | Reglas de negocio y orquestación de flujos |
| `src/utils` | 12 | 5 642 | Seguridad, auditoría, respaldos, PDF y utilidades |
| `src/config` | 4 | 1 169 | Configuración, rutas y sesión de base de datos |
| `src/gui` | 10 | 9 873 | Interfaz gráfica (CustomTkinter) |
| `src/nomina` | 10 | 1 723 | Motor de cálculo de nómina y prestaciones |
| `src/main.py` | 1 | 474 | Punto de entrada de la aplicación |
| **Total** | **73** | **27 534** | |

*Fuente: medición directa con `wc -l` sobre `src/` en la versión 2.82. El conteo de archivos incluye los módulos `__init__.py`.*

La cifra anterior evidencia una decisión de diseño pertinente para el contexto de aplicación: la capa gráfica concentra el 36 % del código y la lógica de negocio —servicios, modelos, repositorios y motor de nómina— el 38 %, de modo que las reglas críticas del dominio no dependen de los componentes visuales y pueden probarse de manera aislada.

#### 4.2.1.1 Capa de Presentación

La interfaz se construyó con CustomTkinter y se organiza en diez módulos accesibles desde la barra lateral o mediante atajos de teclado. El sistema de navegación comprende los módulos de Panel de control, Empleados, Documentos, Incidencias, Asistencia, Contratos, Préstamos, Nómina, Alertas y Configuración, asociados a las combinaciones `Ctrl+1` a `Ctrl+0`, respectivamente. La Tabla 4.2 detalla los componentes principales de esta capa.

**Tabla 4.2. Componentes de la capa de presentación**

| Componente | Archivo | Función |
|-----------|---------|---------|
| `LoginWindow` | `login_window.py` | Autenticación de usuarios |
| `MainWindow` | `main_window.py` | Ventana principal, navegación y atajos de teclado |
| `DashboardFrame` | `frames.py` | Panel de control con indicadores y tarjetas navegables |
| `EmpleadosFrame` | `frames.py` | Registro, edición, búsqueda y filtrado de empleados |
| `DocumentosFrame` | `frames.py` | Gestión documental y control de vencimientos |
| `IncidenciasFrame` | `frames.py` | Solicitudes, aprobación e impacto en nómina |
| `AsistenciaFrame` | `asistencia_frame.py` | Registro diario de jornada y cálculo de horas |
| `ContratosFrame` | `contratos_frame.py` | Vigencia y renovación de contratos laborales |
| `PrestamosFrame` | `prestamos_frame.py` | Anticipos y préstamos con amortización |
| `NominaFrame` | `frames.py` | Generación de nómina, recibos y planillas |
| `AlertasFrame` y `PanelAlertas` | `alertas_frame.py`, `alertas_panel.py` | Notificaciones de vencimientos y eventos |
| `ConfiguracionFrame` | `frames.py` | Parámetros institucionales, apariencia y respaldos |
| `theme.py` y `widgets/graficos.py` | `theme.py`, `widgets/graficos.py` | Paletas claro/oscuro y gráficos del panel |

*Fuente: inspección de `src/gui/` en la versión 2.82.*

La interfaz incorpora validación de formularios con retroalimentación visual inmediata, tablas con búsqueda y filtrado, menús contextuales por clic derecho, apariencia clara y oscura persistida en la configuración institucional, y un conjunto de atajos generales que comprende `Ctrl+N` para crear registros, `Ctrl+F` para enfocar el buscador, `Ctrl+S` para guardar cambios en configuración, `F5` para refrescar y `Esc` para cerrar diálogos o limpiar la selección.

#### 4.2.1.2 Capa de Servicios

Los servicios encapsulan las reglas de negocio y constituyen el único punto de entrada desde la interfaz hacia los datos. Se implementaron diez servicios: autenticación y control de acceso, empleados, documentos, incidencias, asistencia, contratos, préstamos, nómina, alertas y configuración. Cada uno valida las reglas del dominio, coordina los repositorios que le corresponden, ejecuta los cálculos y deja constancia de las operaciones sensibles en el registro de auditoría. Esta capa concentra 4 609 líneas y es, junto con el motor de nómina, el núcleo funcional del sistema.

#### 4.2.1.3 Capa de Repositorios

La capa de acceso a datos aplica el patrón Repository sobre un repositorio base genérico, del cual heredan los diez repositorios concretos. Gracias a esta abstracción, las consultas frecuentes —búsqueda por cédula, por periodo o por estado— se escriben una sola vez, se reutilizan desde cualquier servicio y pueden probarse con independencia de la interfaz. Los repositorios gestionan además las transacciones y las relaciones entre entidades, de modo que ninguna otra capa manipula la sesión de base de datos directamente.

#### 4.2.1.4 Capa de Modelos

Los modelos se declararon con el ORM SQLAlchemy y representan las entidades del dominio junto con sus enumeraciones de apoyo. El esquema consta de diez tablas: `empleados`, `documentos`, `incidencias`, `asistencias`, `contratos`, `prestamos`, `pagos`, `horarios`, `configuraciones` y `usuarios`. Las relaciones principales responden a la naturaleza del negocio: un empleado concentra documentos, incidencias, registros de asistencia, contratos y pagos; los préstamos se amortizan contra la nómina; y los registros de asistencia se calculan contra el horario asignado.

#### 4.2.1.5 Dominio de Cálculo de Nómina

El cálculo de nómina se aisló en el paquete `src/nomina`, que no depende de la interfaz ni del acceso a datos y opera exclusivamente con tipos monetarios propios. Este dominio comprende el motor de cálculo, los parámetros de configuración, el cálculo del impuesto sobre la renta, las horas extra con recargos según tipo de jornada, las prestaciones laborales, las deducciones de seguridad social, la amortización de préstamos y el cálculo de finiquito. La separación permite que cada regla de cálculo se pruebe de forma exhaustiva: el módulo `tests/test_nomina_motor.py` reúne treinta y cuatro funciones de prueba dedicadas a verificar proporcionalidad, deducciones, topes y redondeos.

#### 4.2.1.6 Servicios Transversales

Los módulos transversales refuerzan la seguridad, la trazabilidad y la sostenibilidad de la información. `security.py` valida y sanitiza entradas, verifica permisos y gestiona contraseñas con PBKDF2-HMAC-SHA256, doscientas mil iteraciones y sal aleatorio de dieciséis bytes, con comparación en tiempo constante. `audit_logger.py` registra las acciones críticas, entre ellas los inicios de sesión y las operaciones sobre empleados, documentos, incidencias y nómina. `backup_manager.py` y `backup_scheduler.py` administran respaldos y restauración con políticas de retención, mientras que `pdf_generator.py` produce catorce tipos de documentos oficiales, entre los que figuran constancias de trabajo y de ingresos, recibos de pago, fichas de empleado, planillas de nómina, liquidaciones y reportes de incidencias, vencimientos, asistencia, contratos y préstamos. `document_manager.py` gobierna el almacenamiento de archivos y fotografías, `exporter.py` genera exportaciones en formatos abiertos y `jornada.py`, junto con `validators.py` y `helpers.py`, completa las utilidades de cálculo y validación.

### 4.2.2 Funcionalidades Implementadas

#### 4.2.2.1 Módulo de Empleados

El módulo permite registrar, consultar, actualizar y desactivar empleados mediante un formulario organizado en pestañas temáticas —datos personales, físicos, de contacto y laborales—. La cédula se valida como identificador único y el sistema admite la carga de fotografía del empleado, la categorización por tipo, cargo y departamento, la búsqueda por nombre, apellido o documento y el filtrado por tipo y departamento. La desactivación impide que el empleado aparezca en nóminas posteriores sin suprimir su historial, decisión que preserva la integridad de los registros históricos. El módulo ofrece además estadísticas de dotación por tipo, distribución por departamento, indicadores de antigüedad y generación de ficha individual en PDF. La Tabla 4.3 recoge los tiempos de referencia del proceso, cuya medición definitiva corresponde a la implementación piloto.

**Tabla 4.3. Registro de empleado: contraste proceso manual y sistema**

| Indicador | Proceso manual | Sistema | Observación |
|-----------|----------------|---------|-------------|
| Tiempo de registro | [por completar] | [por completar] | Medición cronometrada en el piloto |
| Validación de cédula duplicada | Manual, sujeta a omisión | Automática | Verificada por pruebas automatizadas |
| Recuperación de la ficha del empleado | Búsqueda en archivo físico | Consulta inmediata | Medición cronometrada en el piloto |
| Constancia en PDF | Elaboración manual | Generación automática | Verificada por pruebas de reportes |

*Fuente: funcionalidad implementada en el módulo de empleados; los tiempos se incorporarán con las mediciones del piloto.*

#### 4.2.2.2 Módulo de Gestión Documental

La gestión documental admite la carga de archivos en formato PDF e imagen, clasificados por tipo de documento, con registro de fecha de emisión y de vencimiento y almacenamiento organizado por empleado. El control de vencimientos constituye la aportación más valorada de este módulo, pues identifica de manera automática los documentos vencidos y aquellos próximos a vencer, y alimenta las alertas del sistema. Se incorporaron asimismo la vista previa y descarga del archivo original, la exportación del expediente documental y la validación de nombre, extensión, tamaño y tipo de archivo antes del almacenamiento. La pérdida de documentos, riesgo señalado en el planteamiento del problema, queda así reducida a los términos que la Tabla 4.4 resume.

**Tabla 4.4. Gestión documental: contraste proceso manual y sistema**

| Indicador | Proceso manual | Sistema | Observación |
|-----------|----------------|---------|-------------|
| Tiempo de incorporación de un documento | [por completar] | [por completar] | Medición cronometrada en el piloto |
| Detección de vencimientos | Revisión periódica manual | Alerta automática | Verificada por pruebas del gestor documental |
| Recuperación del documento | Búsqueda en archivo físico | Consulta inmediata | Medición cronometrada en el piloto |
| Integridad del archivo almacenado | Sujeta a deterioro | Copia digital verificada | Verificada por pruebas de respaldo |

*Fuente: funcionalidad implementada en el módulo documental; los tiempos se incorporarán con las mediciones del piloto.*

#### 4.2.2.3 Módulo de Incidencias

El módulo administra las incidencias que afectan la asistencia y, por extensión, el cálculo de la nómina: reposo médico, ausencia, permiso, vacaciones y licencia. Cada solicitud registra el empleado, el tipo, las fechas de inicio y fin, los días calculados de forma automática, el motivo y el documento de soporte cuando corresponde. El flujo de aprobación transita por los estados pendiente, aprobado, rechazado y completado, y conserva el nombre del aprobador y los comentarios de la decisión, con lo cual la trazabilidad de cada solicitud queda asegurada. El sistema identifica además las incidencias vigentes y su impacto en el periodo de nómina.

#### 4.2.2.4 Módulo de Asistencia

El control de asistencia registra la jornada diaria de cada empleado con siete tipos de marca —presente, tardanza, ausente, permiso, vacaciones, reposo y feriado— y calcula las horas efectivamente trabajadas contra el horario asignado. El módulo produce el reporte de asistencia por periodo y proporciona al motor de nómina la información necesaria para determinar los días y las horas que integran el cálculo.

#### 4.2.2.5 Módulo de Contratos

El módulo de contratos conserva la relación laboral de cada empleado —tipo de contrato, vigencia, remuneración y condiciones—, permite clasificar los contratos en indefinido, temporal, por obra y pasantía y advierte sobre las renovaciones y vencimientos próximos. Esta información alimenta el cálculo de finiquito y de prestaciones del dominio de nómina.

#### 4.2.2.6 Módulo de Préstamos y Anticipos

Los préstamos y anticipos se registran con su monto, número de cuotas y plan de amortización, y se descuentan automáticamente en el cálculo de la nómina del periodo correspondiente. El módulo conserva el saldo pendiente de cada empleado y genera el reporte de préstamos vigentes y liquidados.

#### 4.2.2.7 Módulo de Nómina

La nómina constituye el proceso de mayor criticidad financiera y, por ello, el de mayor densidad de reglas. El sistema calcula el salario proporcional a los días trabajados, integra las incidencias y los registros de asistencia, aplica las deducciones configurables —seguridad social, pensión e impuesto sobre la renta—, incorpora las horas extra con el recargo que corresponde a la jornada diurna, nocturna o mixta, descuenta las cuotas de préstamos y determina el salario neto. Sobre ese resultado genera los pagos individuales o masivos del periodo y produce los documentos asociados: recibo de pago individual, planilla consolidada, reporte de nómina y liquidación. La exactitud de los cálculos se verifica de manera sistemática en la suite automatizada.

**Tabla 4.5. Generación de nómina: contraste proceso manual y sistema**

| Indicador | Proceso manual | Sistema | Observación |
|-----------|----------------|---------|-------------|
| Tiempo de cálculo del periodo | [por completar] | [por completar] | Medición cronometrada en el piloto |
| Verificación de deducciones | Cálculo individual | Cálculo automático | Verificada por pruebas del motor de nómina |
| Emisión de recibos | Elaboración manual | Generación en PDF | Verificada por pruebas de reportes |
| Consistencia entre periodos | Sujeta a criterio del operador | Reglas configurables | Verificada por pruebas de pagos |

*Fuente: funcionalidad implementada en el módulo de nómina; los tiempos se incorporarán con las mediciones del piloto.*

#### 4.2.2.8 Módulo de Alertas

El módulo de alertas centraliza los avisos que el sistema genera de manera automática: vencimiento de documentos, proximidad de renovación de contratos, incidencias pendientes de resolución y saldos de préstamos. Las alertas se presentan en un panel específico y en el panel de control, lo que permite al personal administrativo anticipar gestiones en lugar de reaccionar ante contingencias consumadas.

#### 4.2.2.9 Módulo de Configuración

La configuración institucional comprende los datos de la institución —denominación, dirección, contacto e identificación—, los parámetros de nómina —porcentajes de deducción, salario mínimo de referencia y criterios de cálculo— y las políticas de recursos humanos —días de vacaciones, horas laborales semanales y reglas de incidencias—. El módulo administra además la apariencia clara u oscura, el cambio de contraseña del usuario autenticado, el visor de auditoría para el rol administrador y las operaciones de respaldo y restauración de la base de datos. La totalidad de los parámetros se modifica sin intervenir el código fuente, condición indispensable para que una misma distribución del sistema atienda a instituciones con políticas distintas.

### 4.2.3 Características Técnicas

#### 4.2.3.1 Base de Datos

El sistema utiliza SQLite como motor de persistencia y SQLAlchemy como capa de mapeo objeto-relacional. El esquema comprende diez tablas con integridad referencial mediante claves foráneas, índices sobre los campos de consulta frecuente —cédula, nombre y periodo— y un mecanismo de migración que permite evolucionar la estructura sin pérdida de datos. La elección de SQLite responde a las condiciones de operación previstas: instalación local, ausencia de servidor dedicado y volumen de información acotado. Las mediciones de rendimiento del apartado 4.3.3 determinarán si esa elección se sostiene en el rango superior de volumen previsto.

#### 4.2.3.2 Interfaz Gráfica

La interfaz mantiene un diseño consistente en los diez módulos, con temas claro y oscuro persistidos en la configuración, validación en tiempo real, retroalimentación visual de las acciones, navegación completa por teclado y diálogos auxiliares de ayuda y de información del sistema. Las tarjetas del panel de control son navegables y conducen al módulo correspondiente, lo que reduce la profundidad de navegación para las consultas habituales.

#### 4.2.3.3 Seguridad

Las medidas de seguridad implementadas abarcan la autenticación de usuarios, el control de acceso por rol con verificación de permisos por módulo y por operación, el almacenamiento de contraseñas con hash PBKDF2-HMAC-SHA256, el registro de auditoría de las acciones críticas, el respaldo y la restauración de la base de datos y la sanitización de entradas y archivos. La Tabla 4.6 detalla la matriz de acceso efectivamente implementada, verificada en `src/utils/security.py` y cubierta por pruebas automatizadas.

**Tabla 4.6. Matriz de acceso por rol y módulo**

| Módulo | Administrador | Gestor | Usuario | Solo lectura |
|--------|---------------|--------|---------|--------------|
| Empleados | Sí | Sí | Sí | Sí |
| Documentos | Sí | Sí | Sí | Sí |
| Incidencias | Sí | Sí | Sí | No |
| Asistencia | Sí | Sí | Sí | No |
| Contratos | Sí | Sí | No | No |
| Préstamos | Sí | Sí | No | No |
| Nómina | Sí | Sí | No | No |
| Alertas | Sí | Sí | No | No |
| Configuración | Sí | No | No | No |
| Reportes | Sí | Sí | No | Sí |

*Fuente: `PermissionChecker.can_access_module` en `src/utils/security.py`, versión 2.82.*

Los permisos de operación se organizan de forma análoga: el administrador dispone de creación, lectura, actualización, eliminación, reportes, configuración, respaldo y restauración; el rol gestor de creación, lectura, actualización, eliminación y reportes; el rol usuario de lectura y actualización de registros propios; y el rol de solo lectura exclusivamente de consulta.

## 4.3 RESULTADOS DE PRUEBAS TÉCNICAS

### 4.3.1 Pruebas Automatizadas

La suite de pruebas evolucionó junto con el sistema. En la versión 2.79 el conjunto documentado comprendía 323 pruebas; la versión 2.82 —objeto de este informe— declara 453 funciones de prueba distribuidas en 24 archivos, con 5 371 líneas de código de prueba. La Tabla 4.7 presenta la distribución por archivo, medición verificable de manera directa sobre `tests/`.

**Tabla 4.7. Distribución de funciones de prueba por archivo (versión 2.82)**

| Archivo de prueba | Funciones | Área verificada |
|-------------------|-----------|-----------------|
| `test_helpers.py` | 66 | Formateo, fechas y utilidades auxiliares |
| `test_security.py` | 63 | Validación, sanitización y control de acceso |
| `test_validators.py` | 36 | Reglas de validación del dominio |
| `test_nomina_motor.py` | 34 | Motor de cálculo de nómina |
| `test_auto_updater.py` | 19 | Actualización automática del sistema |
| `test_asistencia.py` | 18 | Registro de jornada y cálculo de horas |
| `test_contratos.py` | 17 | Vigencia y renovación de contratos |
| `test_prestamos.py` | 17 | Amortización de anticipos y préstamos |
| `test_reportes.py` | 17 | Generación de documentos PDF |
| `test_auth.py` | 16 | Autenticación, roles y permisos |
| `test_empleados.py` | 16 | Gestión de empleados |
| `test_gui_smoke.py` | 16 | Humo de la interfaz gráfica |
| `test_credenciales.py` | 15 | Credenciales y política de contraseñas |
| `test_document_manager.py` | 15 | Almacenamiento de documentos |
| `test_alertas.py` | 13 | Generación de alertas |
| `test_jornada.py` | 13 | Cálculo de jornada laboral |
| `test_theme.py` | 13 | Paletas de apariencia |
| `test_backups.py` | 9 | Respaldo y restauración |
| `test_configuracion.py` | 9 | Parámetros configurables |
| `test_incidencias.py` | 8 | Incidencias y aprobaciones |
| `test_pagos.py` | 8 | Pagos y deducciones |
| `test_documentos.py` | 7 | Gestión documental |
| `test_migraciones.py` | 4 | Evolución del esquema |
| `test_settings_version.py` | 4 | Versión y parámetros de compilación |
| **Total** | **453** | |

*Fuente: conteo de funciones `test_` sobre `tests/`, versión 2.82. La suite se ejecuta con `pytest` y la configuración de cobertura está declarada en `pyproject.toml`.*

La distinción entre ambas mediciones merece precisión metodológica. Los porcentajes de cobertura que se exponen en la Tabla 4.8 corresponden a la medición ejecutada sobre la versión 1.0.4 del sistema; se conservan como referencia histórica y como evidencia de que la estrategia de pruebas alcanzó niveles altos en la lógica de negocio. Dado que el código creció de manera sustancial desde entonces, esos porcentajes no pueden atribuirse a la versión vigente: la cobertura de la versión 2.82 debe re-medirse con `pytest --cov=src` y sustituir los valores de la tabla antes de la presentación definitiva. La misma exigencia se aplica al estado de ejecución de la suite, cuya verificación corresponde al flujo de integración continua del repositorio y cuyo informe debe adjuntarse como evidencia.

**Tabla 4.8. Cobertura de referencia medida en la versión 1.0.4**

| Módulo | Líneas de código | Líneas cubiertas | Cobertura |
|--------|------------------|------------------|-----------|
| `models` | 393 | 363 | 92 % |
| `repositories` | 678 | 326 | 48 % |
| `services` | 815 | 608 | 75 % |
| `utils` | 1 442 | 1 167 | 81 % |
| `config` | 265 | 154 | 58 % |
| `gui` | 3 025 | 330 | 11 % |
| `main.py` | 220 | 0 | 0 % |
| **Total** | **6 841** | **2 951** | **43 %** |

*Fuente: medición con `pytest --cov=src` sobre la versión 1.0.4; la cobertura de la lógica de negocio —modelos, repositorios, servicios, utilidades y configuración, excluida la capa gráfica y el punto de entrada— alcanzó el 73 %.*

La lectura de estos datos admite dos conclusiones. La primera es que la cobertura es alta donde residen las reglas críticas del dominio —modelos, servicios y utilidades—, lo que resulta coherente con la estrategia de aislar el cálculo y las validaciones de la interfaz. La segunda es que la capa gráfica presenta cobertura baja, comportamiento esperable en aplicaciones de escritorio cuya automatización exige un entorno con pantalla; su verificación se apoya en las pruebas de humo de la interfaz y en los protocolos de usabilidad del apartado 4.4.

### 4.3.2 Pruebas de Integración

La suite verifica flujos completos sobre una base de datos aislada y sembrada para cada prueba, lo que permite comprobar la interacción entre capas sin interferencias entre casos. Los flujos cubiertos son los siguientes:

1. Cadena de personal: registro de un empleado, búsqueda, actualización y asociación de documentos, incidencias y pagos (`test_empleados.py`, `test_documentos.py`, `test_pagos.py`).
2. Cálculo de nómina: determinación de días y horas trabajadas con incidencias y asistencia, salario proporcional, deducciones, descuento de préstamos, salario neto y emisión de recibos (`test_nomina_motor.py`, `test_pagos.py`, `test_prestamos.py`).
3. Gestión de incidencias: solicitud, validación de fechas y días, aprobación y efecto en la nómina (`test_incidencias.py`).
4. Asistencia y jornada: registro diario, cruce con el horario asignado y cálculo de horas efectivas (`test_asistencia.py`, `test_jornada.py`).
5. Contratación: alta del contrato, vigencia, renovación y efecto en prestaciones y finiquito (`test_contratos.py`).
6. Autenticación y control de acceso: inicio de sesión, verificación de contraseñas, roles y permisos por módulo (`test_auth.py`, `test_security.py`).
7. Configuración y persistencia: siembra de parámetros iniciales, persistencia de la apariencia, migraciones de esquema y lectura de versión (`test_configuracion.py`, `test_migraciones.py`, `test_settings_version.py`).
8. Respaldo y restauración: ciclo completo de copia, verificación y restauración de la base de datos (`test_backups.py`).
9. Reportes: generación de los documentos PDF y de las exportaciones en formatos abiertos (`test_reportes.py`).
10. Alertas y actualización: generación de avisos y funcionamiento del actualizador automático (`test_alertas.py`, `test_auto_updater.py`).

El informe de ejecución de la suite sobre la versión 2.82 deberá acompañarse como evidencia en el anexo correspondiente, con el número de pruebas ejecutadas, el resultado obtenido y la fecha de la ejecución.

### 4.3.3 Pruebas de Rendimiento

El protocolo de rendimiento se definió conforme a la metodología del Capítulo III y su aplicación corresponde a la implementación piloto, dado que las métricas carecen de sentido fuera de las condiciones reales de operación. La Tabla 4.9 establece los umbrales comprometidos y los campos que se completarán con las mediciones.

**Tabla 4.9. Protocolo de rendimiento y umbrales de aceptación**

| Métrica | Umbral | Resultado | Estado |
|---------|--------|-----------|--------|
| Tiempo de respuesta promedio en operaciones de consulta | Menor a 1 s | [por completar] | Pendiente de medición |
| Tiempo de respuesta máximo | Menor a 3 s | [por completar] | Pendiente de medición |
| Consumo de memoria en reposo | Menor a 150 MB | [por completar] | Pendiente de medición |
| Consumo de memoria bajo carga | Menor a 300 MB | [por completar] | Pendiente de medición |
| Tiempo de generación de nómina del periodo | Menor a 5 min | [por completar] | Pendiente de medición |
| Volumen de datos con el que se probó | Definido por el piloto | [por completar] | Pendiente de medición |
| Degradación observada al crecer el volumen | Sin degradación significativa | [por completar] | Pendiente de medición |

*Fuente: protocolo definido en el apartado 3.4.1.5; medición prevista durante el piloto.*

### 4.3.4 Pruebas de Seguridad

Los controles de seguridad implementados fueron verificados mediante pruebas automatizadas dedicadas, presentes en `test_security.py`, `test_auth.py` y `test_credenciales.py`. La revisión abarcó seis frentes. En materia de inyección de código, el riesgo se mitiga con consultas parametrizadas a través del ORM y con la sanitización complementaria de entradas; en una aplicación de escritorio no existe superficie de ataque web, si bien los campos se sanitizan antes de almacenarse. La autenticación se apoya en PBKDF2-HMAC-SHA256 con doscientas mil iteraciones, sal aleatorio y comparación en tiempo constante, y rechaza las credenciales inválidas sin revelar cuál de los dos datos falló. La autorización se resuelve con la matriz de roles y permisos expuesta en la Tabla 4.6. La auditoría registra los eventos de seguridad y las acciones críticas, y el tratamiento de archivos valida nombre, extensión, tamaño y tipo antes del almacenamiento. El respaldo y la restauración cierran el conjunto con políticas de retención configurables. El informe de cobertura específica del módulo de seguridad deberá actualizarse a la versión 2.82 conforme a la exigencia señalada en el apartado 4.3.1.

## 4.4 RESULTADOS DE PRUEBAS DE USABILIDAD

Los apartados que siguen describen la estructura de registro de las pruebas de usabilidad y se completarán con los datos obtenidos en las sesiones con usuarios, aplicando el protocolo del Anexo 3 y los procedimientos del Capítulo III.

### 4.4.1 Participantes

Las pruebas se aplicarán al conjunto de usuarios distribuido entre las instituciones piloto, procurando representar los cuatro perfiles definidos en el diseño muestral. La Tabla 4.10 organiza el registro.

**Tabla 4.10. Composición de los participantes en las pruebas de usabilidad**

| Perfil | Cantidad | Institución | Nivel de competencia tecnológica |
|--------|----------|-------------|----------------------------------|
| Directivos y coordinación | [por completar] | [por completar] | [por completar] |
| Personal de recursos humanos | [por completar] | [por completar] | [por completar] |
| Personal administrativo de apoyo | [por completar] | [por completar] | [por completar] |
| Personal docente (consulta) | [por completar] | [por completar] | [por completar] |

*Fuente: protocolo del Anexo 3; registro por completar con los participantes efectivos.*

### 4.4.2 Resultados por Tarea

Las tareas evaluadas corresponden a los procesos críticos del sistema: registro de un empleado, búsqueda de información, cálculo de la nómina del periodo, emisión de un recibo de pago, carga de un documento con vencimiento y registro y aprobación de una incidencia. Para cada tarea se registran el tiempo de ejecución, la tasa de éxito, el número de errores y la valoración subjetiva del participante, conforme a la Tabla 4.11.

**Tabla 4.11. Resultados por tarea de usabilidad**

| Tarea | Tiempo promedio | Tasa de éxito | Errores observados | Valoración (1-5) |
|-------|-----------------|---------------|--------------------|------------------|
| Registro de empleado | [por completar] | [por completar] | [por completar] | [por completar] |
| Búsqueda de empleado por cédula | [por completar] | [por completar] | [por completar] | [por completar] |
| Cálculo de nómina del periodo | [por completar] | [por completar] | [por completar] | [por completar] |
| Emisión de recibo de pago | [por completar] | [por completar] | [por completar] | [por completar] |
| Carga de documento con vencimiento | [por completar] | [por completar] | [por completar] | [por completar] |
| Registro y aprobación de incidencia | [por completar] | [por completar] | [por completar] | [por completar] |

*Fuente: protocolo del Anexo 3; registro por completar con las mediciones efectivas.*

Los problemas de usabilidad detectados en las sesiones se documentarán con la descripción del obstáculo, la frecuencia con que se presentó y la corrección introducida, de modo que la relación entre hallazgo e intervención quede explícita.

### 4.4.3 Resultados de Satisfacción

La satisfacción se medirá con el cuestionario del Anexo 2, complementado con la escala de usabilidad del sistema (SUS) cuando el número de participantes lo permita. La Tabla 4.12 organiza las dimensiones evaluadas y la Tabla 4.13 el contraste entre la percepción previa y posterior a la implementación.

**Tabla 4.12. Satisfacción por dimensión**

| Dimensión | Media | Desviación estándar | Interpretación |
|-----------|-------|---------------------|----------------|
| Facilidad de aprendizaje | [por completar] | [por completar] | [por completar] |
| Eficiencia de uso | [por completar] | [por completar] | [por completar] |
| Memorabilidad | [por completar] | [por completar] | [por completar] |
| Baja incidencia de errores | [por completar] | [por completar] | [por completar] |
| Satisfacción general | [por completar] | [por completar] | [por completar] |
| Puntuación SUS global | [por completar] | [por completar] | [por completar] |

*Fuente: cuestionario del Anexo 2 y escala SUS; registro por completar con los datos efectivos.*

**Tabla 4.13. Contraste de percepción antes y después de la implementación**

| Aspecto evaluado | Antes | Después | Diferencia | Significancia |
|------------------|-------|---------|------------|---------------|
| Satisfacción general con la gestión de personal | [por completar] | [por completar] | [por completar] | [por completar] |
| Percepción de eficiencia administrativa | [por completar] | [por completar] | [por completar] | [por completar] |
| Facilidad de acceso a la información | [por completar] | [por completar] | [por completar] | [por completar] |
| Utilidad percibida de los reportes | [por completar] | [por completar] | [por completar] | [por completar] |

*Fuente: instrumento del Anexo 2 aplicado en dos momentos; registro por completar con los datos efectivos.*

El tratamiento estadístico de estos datos seguirá el procedimiento definido en el apartado 3.6.1.2 —prueba t para muestras relacionadas, prueba de rangos con signo de Wilcoxon cuando no se verifique la normalidad, chi-cuadrado para distribuciones de respuesta y análisis de varianza para la comparación entre perfiles de usuario—, con un nivel de significancia de 0,05. Los resultados se registrarán en este apartado una vez concluida la recolección.

## 4.5 RESULTADOS DE IMPLEMENTACIÓN PILOTO

La implementación piloto constituye el componente empírico del estudio y se ejecutará conforme a los procedimientos del apartado 3.5 y a los instrumentos de los anexos 1, 2, 3, 8 y 9. Los apartados siguientes organizan su registro.

### 4.5.1 Instituciones Participantes

**Tabla 4.14. Caracterización de las instituciones piloto**

| Institución | Nivel educativo | Número de empleados | Ámbito | Fecha de inicio |
|-------------|-----------------|---------------------|--------|-----------------|
| Institución 1 | [por completar] | [por completar] | [por completar] | [por completar] |
| Institución 2 | [por completar] | [por completar] | [por completar] | [por completar] |
| Institución 3 | [por completar] | [por completar] | [por completar] | [por completar] |

*Fuente: criterios de selección del apartado 3.3.2.1; registro por completar con las instituciones efectivamente participantes, cuyo número se ajustará al rango de tres a cinco previsto en el diseño muestral.*

### 4.5.2 Métricas de Impacto Cuantitativo

#### 4.5.2.1 Tiempos de Procesamiento

El efecto del sistema sobre los tiempos administrativos se medirá comparando el tiempo empleado en cada proceso antes y después de la implementación, con observación directa y cronometraje. La Tabla 4.15 recoge el registro previsto.

**Tabla 4.15. Tiempos de procesamiento antes y después de la implementación**

| Proceso | Antes (min) | Después (min) | Reducción (min) | Reducción (%) |
|---------|-------------|---------------|-----------------|---------------|
| Registro de empleado | [por completar] | [por completar] | [por completar] | [por completar] |
| Búsqueda de información de personal | [por completar] | [por completar] | [por completar] | [por completar] |
| Cálculo de la nómina del periodo | [por completar] | [por completar] | [por completar] | [por completar] |
| Emisión de recibos de pago | [por completar] | [por completar] | [por completar] | [por completar] |
| Control de documentos y vencimientos | [por completar] | [por completar] | [por completar] | [por completar] |
| Registro y aprobación de incidencias | [por completar] | [por completar] | [por completar] | [por completar] |

*Fuente: observación directa y cronometraje conforme al apartado 3.4.1.2; registro por completar con las mediciones efectivas.*

La prueba t para muestras relacionadas permitirá contrastar si la reducción observada es estadísticamente significativa; se reportarán el estadístico, los grados de libertad y el valor de probabilidad asociado.

#### 4.5.2.2 Tasas de Error

El segundo indicador cuantitativo es la tasa de error de los procesos administrativos, obtenida del registro de correcciones, reclamos y reprocesos antes y después de la implementación, según se organiza en la Tabla 4.16.

**Tabla 4.16. Tasas de error antes y después de la implementación**

| Proceso | Antes (%) | Después (%) | Reducción (puntos) |
|---------|-----------|-------------|--------------------|
| Cálculo de nómina y deducciones | [por completar] | [por completar] | [por completar] |
| Registro y actualización de datos de personal | [por completar] | [por completar] | [por completar] |
| Control documental y vencimientos | [por completar] | [por completar] | [por completar] |
| Seguimiento de incidencias y ausencias | [por completar] | [por completar] | [por completar] |

*Fuente: registro institucional de correcciones y reprocesos; registro por completar con las mediciones efectivas.*

Del contraste anterior se derivarán, cuando la información disponible lo permita, la estimación del costo evitado por errores no incurridos, la variación en el número de reclamos laborales y el grado de cumplimiento de las obligaciones de reporte ante las instancias correspondientes.

#### 4.5.2.3 Satisfacción del Personal

El tercer indicador atiende a la percepción del personal sobre la gestión de sus propios asuntos administrativos, dimensión que el planteamiento del problema identificó como afectada por los errores y las demoras del proceso manual. La Tabla 4.17 organiza su registro.

**Tabla 4.17. Indicadores de satisfacción del personal**

| Indicador | Antes | Después | Variación |
|-----------|-------|---------|-----------|
| Satisfacción con la oportunidad de los pagos | [por completar] | [por completar] | [por completar] |
| Percepción de exactitud en la liquidación | [por completar] | [por completar] | [por completar] |
| Satisfacción con la información recibida | [por completar] | [por completar] | [por completar] |
| Satisfacción laboral general | [por completar] | [por completar] | [por completar] |

*Fuente: cuestionario del Anexo 2; registro por completar con los datos efectivos.*

### 4.5.3 Resultados Cualitativos

Los hallazgos cualitativos se obtendrán de las entrevistas, la observación directa y el análisis de contenido de los comentarios recogidos durante el piloto, conforme al procedimiento del apartado 3.6.2. Su registro comprenderá tres bloques: las opiniones de los usuarios sobre el sistema, las modificaciones observadas en los patrones de trabajo y las lecciones aprendidas durante la implementación. Cada bloque se documentará con la evidencia que lo sustenta —citas textuales anonimizadas, notas de campo y registros de sesión— para permitir la triangulación con los datos cuantitativos.

## 4.6 ANÁLISIS COMPARATIVO

### 4.6.1 Comparación con Soluciones Comerciales

La comparación con los sistemas comerciales disponibles en el mercado se realizó sobre atributos cualitativos y rangos de costo referenciales, dado que las cotizaciones específicas dependen de cada proveedor y de la escala de la institución. La Tabla 4.18 sintetiza el contraste; los valores monetarios son estimaciones de mercado que deberán ajustarse con cotizaciones reales si la institución desea utilizarlos como base de decisión.

**Tabla 4.18. Contraste con soluciones comerciales de gestión de personal**

| Atributo | Sistema desarrollado | Soluciones comerciales | Valoración |
|----------|----------------------|------------------------|------------|
| Costo de adquisición | Sin costo de licencia | Del orden de miles a decenas de miles de dólares | Ventaja para el sistema desarrollado |
| Costo anual de sostenimiento | Sin licenciamiento; mantenimiento interno | Suscripción o soporte anual | Ventaja para el sistema desarrollado |
| Cobertura funcional básica | Empleados, documentos, incidencias, asistencia, contratos, préstamos, nómina y reportes | Equivalente, con mayor profundidad en algunos módulos | Paridad funcional en lo esencial |
| Analítica avanzada y planeación de talento | No incorporada | Disponible en las suites de mayor rango | Ventaja para las soluciones comerciales |
| Personalización institucional | Alta, mediante parámetros sin modificar código | Limitada por la configuración ofrecida por el proveedor | Ventaja para el sistema desarrollado |
| Soporte técnico | Comunitario y auto-soporte documentado | Mesa de ayuda contratada | Ventaja para las soluciones comerciales |
| Curva de aprendizaje | Moderada, con guía de usuario y capacitación | Variable según la suite | Ventaja para el sistema desarrollado |
| Dependencia tecnológica | Código abierto, sin licencias propietarias | Licenciamiento y formatos del proveedor | Ventaja para el sistema desarrollado |

*Fuente: análisis comparativo elaborado a partir de la funcionalidad implementada y de rangos de mercado referenciales; los valores monetarios requieren cotización específica.*

La conclusión que se desprende del cuadro es acotada y conviene enunciarla con precisión: el sistema desarrollado resulta competitivo en cobertura funcional básica, costo total de propiedad y capacidad de personalización, mientras que las soluciones comerciales conservan ventaja en analítica avanzada y soporte contratado. Para una institución con recursos limitados, ese intercambio favorece al sistema desarrollado; para una institución con requerimientos analíticos complejos, la decisión exige una evaluación adicional.

### 4.6.2 Comparación con el Proceso Manual

El contraste con el proceso manual se aborda en dos planos. El primero es cualitativo y ya resulta observable: la información deja de depender del archivo físico, los cálculos dejan de depender de la destreza del operador, la trazabilidad queda registrada de forma automática y la información se encuentra disponible de manera inmediata. El segundo plano es cuantitativo y se completará con las mediciones del piloto, según se recoge en la Tabla 4.19.

**Tabla 4.19. Contraste con el proceso manual**

| Aspecto | Proceso manual | Sistema desarrollado | Evidencia |
|---------|----------------|----------------------|-----------|
| Tiempo de procesamiento | Alto y variable según carga | Bajo y previsible | [por completar] |
| Tasa de errores en cálculos | Dependiente del operador | Reglas automatizadas verificadas | Pruebas del motor de nómina |
| Acceso a la información | Sujeto a búsqueda física | Consulta inmediata y filtrada | Pruebas de integración |
| Trazabilidad de las decisiones | Registro informal | Auditoría automática | Pruebas de seguridad |
| Control de vencimientos | Revisión periódica manual | Alerta automática | Pruebas de alertas y documentos |
| Continuidad ante ausencias del operador | Dependiente de la persona | Documentación y registro institucional | Guía de usuario y auditoría |
| Escalabilidad del proceso | Limitada por el tiempo disponible | Determinada por el volumen y la configuración | [por completar] |

*Fuente: contraste cualitativo y estructural; los campos pendientes se completarán con las mediciones del piloto.*

## 4.7 ESTRUCTURA DE VALIDACIÓN DE HIPÓTESIS

La validación de las hipótesis se realizará con la evidencia recopilada durante el piloto, aplicando los procedimientos estadísticos definidos en el apartado 3.6.1.2 y el análisis cualitativo del apartado 3.6.2. Los apartados siguientes presentan cada hipótesis con sus indicadores, de modo que la decisión de aceptación o rechazo quede vinculada a un criterio explícito.

### 4.7.1 Hipótesis General

La hipótesis general sostiene que la implementación del sistema mejorará de manera significativa la eficiencia administrativa, con una reducción de los tiempos de procesamiento de al menos el 50 % y una disminución de los errores administrativos de al menos el 80 %. La Tabla 4.20 establece los indicadores y los umbrales de decisión.

**Tabla 4.20. Indicadores de la hipótesis general**

| Indicador | Umbral de aceptación | Resultado | Decisión |
|-----------|----------------------|-----------|----------|
| Reducción promedio de tiempos de procesamiento | Mayor o igual al 50 % | [por completar] | [por completar] |
| Reducción promedio de la tasa de error | Mayor o igual al 80 % | [por completar] | [por completar] |
| Significancia estadística del cambio | Valor de probabilidad menor a 0,05 | [por completar] | [por completar] |

*Fuente: umbrales definidos en el anteproyecto y en el apartado 3.6.1.2; resultados por completar con la evidencia del piloto.*

### 4.7.2 Hipótesis Específicas

**H1. Arquitectura modular y mantenibilidad.** La hipótesis sostiene que la arquitectura modular facilita el mantenimiento y la expansión del sistema. Los indicadores son el tiempo requerido para incorporar una funcionalidad nueva y la comprensión del código por parte de un desarrollador ajeno al proyecto. La evidencia disponible a favor de esta hipótesis es la propia evolución del sistema: entre la versión 2.79 y la 2.82 se incorporaron cuatro módulos funcionales —asistencia, contratos, préstamos y alertas—, el motor de nómina y 130 funciones de prueba, sin refactorizaciones estructurales de las capas preexistentes. Los indicadores de percepción de terceros se registrarán durante el piloto.

**H2. Usabilidad de la interfaz gráfica.** La hipótesis sostiene que la interfaz gráfica mejora la usabilidad respecto de las alternativas de línea de comandos. Los indicadores son el tiempo de aprendizaje, la tasa de éxito en las tareas y la valoración de la interfaz, y se medirán con el protocolo del Anexo 3 conforme al apartado 4.4.2.

**H3. Reducción de errores financieros.** La hipótesis sostiene que la automatización reduce los errores en el cálculo de la nómina. El indicador inmediato es la verificación automatizada de las reglas de cálculo; el indicador de impacto es la variación de la tasa de error y del costo evitado, que se registrará conforme al apartado 4.5.2.2.

**H4. Acceso a la información.** La hipótesis sostiene que la digitalización mejora el acceso a la información. El indicador inmediato es la disponibilidad de la información de personal, documentos y pagos desde el propio sistema, condición verificable en la funcionalidad implementada; el indicador de impacto es la variación del tiempo de búsqueda, que se registrará en el piloto. Cabe precisar que, al tratarse de una aplicación de escritorio, la disponibilidad se circunscribe a los equipos donde el sistema está instalado; el acceso remoto figura como línea de expansión en el Capítulo V.

**H5. Adopción mediante capacitación y documentación.** La hipótesis sostiene que la capacitación y la documentación facilitan la adopción. Los indicadores son la proporción de usuarios activos, la satisfacción con la capacitación y la utilidad percibida de la documentación, cuya medición corresponde al piloto.

## 4.8 ANÁLISIS DE FACTORES DE ÉXITO

### 4.8.1 Factores Técnicos

El primer factor técnico que explica el resultado obtenido es la selección de tecnologías maduras y de código abierto —Python, SQLAlchemy, CustomTkinter, ReportLab y OpenPyXL—, decisión que eliminó el costo de licenciamiento y garantizó documentación abundante. El segundo es la arquitectura de capas con patrones Repository y Service, que permitió probar cada componente de manera aislada y evitó que la interfaz concentrara reglas de negocio. El tercero es el desarrollo iterativo con verificación continua: la suite de pruebas creció con cada funcionalidad y funcionó como red de seguridad frente a las regresiones. El cuarto es el aislamiento del dominio de cálculo de nómina en un paquete independiente, lo que posibilitó una densidad de pruebas notablemente superior en el componente de mayor riesgo financiero.

### 4.8.2 Factores Organizacionales

En el plano organizacional, la literatura revisada en el Capítulo II ya anticipaba que el éxito de estos sistemas depende más de las condiciones institucionales que de la tecnología. Los factores que el proyecto procuró asegurar son el respaldo de la dirección, la participación de los usuarios en la definición de requerimientos y en la validación, la capacitación diferenciada por perfil y la comunicación clara de los alcances del sistema. La verificación empírica de su peso relativo corresponde al piloto.

### 4.8.3 Factores Contextuales

El contexto de aplicación reúne condiciones favorables y restricciones conocidas. Entre las primeras se cuentan la necesidad institucional explícita de ordenar la gestión de personal, la disponibilidad de equipos informáticos básicos y la disposición del personal a incorporar herramientas nuevas cuando percibe un beneficio concreto. Entre las restricciones figuran la conectividad limitada, la diversidad de competencias digitales y la ausencia de áreas de tecnología con dedicación exclusiva, condiciones que orientaron el diseño hacia una aplicación de escritorio, de instalación local, con guía de usuario y respaldos periódicos.

## 4.9 LIMITACIONES Y RETOS

### 4.9.1 Limitaciones Identificadas

Las limitaciones técnicas se concentran en la escalabilidad —el motor SQLite y la arquitectura de escritorio están concebidos para volúmenes del orden de miles de empleados, no de decenas de miles—, en la dependencia de infraestructura básica y en la ausencia de integración con otros sistemas institucionales. Las limitaciones funcionales comprenden la escasa flexibilidad de la analítica, la inexistencia de versión web o móvil y la falta de soporte multiinstitución en una misma instalación. Las limitaciones metodológicas, por su parte, derivan del tamaño de la muestra prevista —entre tres y cinco instituciones—, de la duración acotada del periodo de evaluación y de la especificidad del contexto regional, circunstancias que restringen la generalización de los hallazgos sin invalidarlos.

### 4.9.2 Retos Enfrentados

Durante el desarrollo, el reto principal fue sostener el equilibrio entre cobertura funcional y simplicidad de uso: cada módulo añadido incrementa el valor del sistema y, al mismo tiempo, la carga cognitiva que el usuario debe asumir, tensión que se resolvió agrupando funcionalidad afín y reservando los módulos sensibles a los roles con competencia para operarlos. El segundo reto fue preservar la coherencia entre la configuración institucional y las reglas de cálculo, resuelto mediante parámetros sin código. El tercero fue mantener la disciplina de documentación mientras el sistema evolucionaba, lo que obligó a tratar la documentación como entregable y no como actividad final. Durante la implementación, los retos previstos son la resistencia inicial al cambio, la heterogeneidad de competencias tecnológicas, el soporte sostenido durante la transición y la resolución de incidencias técnicas en el momento en que ocurran.

## 4.10 CONCLUSIONES DEL CAPÍTULO

Los resultados técnicos expuestos permiten sostener tres afirmaciones con respaldo verificable. En primer lugar, el sistema fue efectivamente construido: la versión 2.82 comprende 27 534 líneas de código distribuidas en nueve capas y componentes, diez módulos funcionales con acceso por rol, diez tablas con integridad referencial y un motor de nómina que concentra las reglas de mayor riesgo financiero. En segundo lugar, la calidad técnica descansa en una suite de 453 funciones de prueba organizadas en 24 archivos, con énfasis explícito en seguridad, validación del dominio y cálculo de nómina, y en un conjunto de servicios transversales que cubren auditoría, respaldos, generación documental y actualización del sistema. En tercer lugar, la cobertura de código medida en la versión 1.0.4 alcanzó niveles altos en la lógica de negocio, resultado que debe re-medirse sobre la versión vigente para que la afirmación conserve validez sobre el estado actual del software.

Los apartados de validación empírica definen con precisión qué se medirá, cómo se medirá y con qué umbral se decidirá, de manera que la evidencia pendiente no constituya una indeterminación metodológica, sino un registro preparado para recibirla. Las hipótesis planteadas se resolverán con esa evidencia: tres de ellas cuentan ya con indicadores estructurales verificados, mientras que su magnitud de impacto permanece condicionada al piloto. Las limitaciones identificadas —muestra acotada, periodo breve, contexto regional y dependencia de recursos propios— son consistentes con el alcance de un trabajo de grado y delimitan con honestidad el campo de validez de los resultados.

Con este balance, el siguiente capítulo presenta las conclusiones generales de la investigación, las recomendaciones para la implementación en instituciones educativas y las líneas de trabajo que el proyecto deja abiertas.
