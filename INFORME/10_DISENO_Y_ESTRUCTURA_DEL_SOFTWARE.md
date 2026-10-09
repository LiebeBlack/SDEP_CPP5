# DISEÑO Y ESTRUCTURA DEL SOFTWARE CONSTRUIDO

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5, repositorio en versión vigente 3.0.1.
**Documento:** 10 del expediente del informe del estado de la investigación.

---

## 1. Introducción

Este documento describe el diseño y la estructuración del software efectivamente construido. A diferencia de un diseño previsto, describe lo que existe: la arquitectura implementada, las capas del sistema, el modelo de datos, los módulos funcionales, los componentes transversales y auxiliares, y las rutas de verificación. Cada afirmación es comprobable sobre el repositorio y se indica, cuando corresponde, la ubicación que permite comprobarla.

El documento se organiza en cuatro partes. La primera expone la arquitectura y su distribución real en el código. La segunda describe el modelo de datos, los módulos funcionales y el dominio de cálculo. La tercera examina los componentes trasversales y auxiliares: seguridad, auditoría, respaldos, generación documental, sincronización, actualización y empaquetado. La cuarta presenta la verificación, los puntos de extensión y las limitaciones.

---

## 2. Arquitectura del sistema

### 2.1 Organización por capas

El sistema se organiza en una arquitectura de capas que separa responsabilidades y establece una dirección única de dependencia: la presentación conoce a los servicios; los servicios conocen a los repositorios y al dominio de cálculo; los repositorios conocen a los modelos; y los servicios transversales son accesibles desde cualquiera de esas capas. Ninguna capa inferior conoce a una superior.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ CAPA DE PRESENTACIÓN · CustomTkinter                                   │
│ LoginWindow · MainWindow · nueve módulos · tema claro/oscuro ·         │
│ widgets de gráficos propios                                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE SERVICIOS · reglas de negocio y orquestación de flujos         │
│ auth · empleado · documento · incidencia · contrato · pago ·           │
│ configuración · académico · notas · token de sesión                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE REPOSITORIOS · patrón Repository sobre repositorio base        │
│ repositorio base genérico y repositorios concretos por entidad         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE MODELOS · SQLAlchemy ORM                                       │
│ trece entidades y enumeraciones del dominio                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ DOMINIO DE NÓMINA · cálculo aislado de la interfaz y del acceso a datos│
│ motor · parámetros · impuesto sobre la renta · horas extra ·           │
│ prestaciones · seguridad social · finiquito · tipos                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ SERVICIOS TRANSVERSALES · seguridad, trazabilidad y sostenibilidad     │
│ security · audit_logger · backup_manager · backup_scheduler ·          │
│ pdf_generator · document_manager · exporter · validators · helpers     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ BASE DE DATOS · SQLite con integridad referencial y migraciones        │
└────────────────────────────────────────────────────────────────────────┘
```

*Fuente: elaboración propia a partir de la implementación efectivamente desplegada en `src/`, versión 3.0.1.*

### 2.2 Distribución real del código por capa

La distribución del código confirma la arquitectura declarada. Sobre los 77 archivos Python de `src/`, que suman 29 475 líneas, la extensión de cada capa es la siguiente.

| Capa o componente | Archivos | Líneas | Proporción |
|-------------------|----------|--------|------------|
| Presentación (`gui/`) | 10 | 11 598 | 39,3 % |
| Servicios transversales (`utils/`) | 10 | 5 525 | 18,7 % |
| Servicios de negocio (`services/`) | 11 | 4 332 | 14,7 % |
| Repositorios (`repositories/`) | 16 | 2 383 | 8,1 % |
| Modelos (`models/`) | 16 | 1 887 | 6,4 % |
| Configuración (`config/`) | 3 | 1 706 | 5,8 % |
| Dominio de nómina (`nomina/`) | 9 | 1 502 | 5,1 % |
| Punto de entrada y paquete raíz | 2 | 542 | 1,8 % |
| **Total** | **77** | **29 475** | **100 %** |

La concentración de la mayor extensión en la capa de presentación es esperable en una aplicación de escritorio con nueve módulos, formularios y validaciones de entrada; no debe leerse como un defecto de diseño, sino como la consecuencia de que la interfaz es la superficie de contacto con usuarios de competencias heterogéneas. La capa de servicios transversales ocupa el segundo lugar, lo que refleja el peso de la seguridad, la auditoría, los respaldos y la generación documental en las decisiones de sostenibilidad del producto.

### 2.3 Principios de diseño observados

| Principio | Manifestación verificable |
|-----------|---------------------------|
| Separación de responsabilidades | Cada capa en su directorio; los servicios no construyen componentes de interfaz |
| Bajo acoplamiento | El dominio de nómina no importa la interfaz ni los repositorios |
| Alta cohesión | Cada servicio corresponde a un módulo funcional delimitado |
| Abstracción entre capas | Repositorio base genérico del que heredan los concretos |
| Inversión de dependencia | Los servicios reciben sus repositorios en lugar de instanciarlos internamente |
| Trazabilidad | Las operaciones sensibles pasan por el registrador de auditoría |

### 2.4 Patrones de diseño aplicados

Cuatro patrones estructuran la implementación. El patrón **Repository** se materializa en un repositorio base genérico que expone las operaciones comunes de consulta y persistencia, del que heredan los repositorios concretos que añaden las consultas propias de cada entidad. El patrón **Service Layer** concentra las reglas de negocio en servicios con un punto de entrada único por operación. El patrón **Modelo–Vista–Controlador**, adaptado a escritorio, separa los modelos de dominio, los servicios que aplican reglas y los componentes que presentan resultados. La **inyección de dependencias** permite que los servicios reciban sus colaboradores, condición que habilita tanto las pruebas automatizadas como la sustitución de componentes.

---

## 3. Modelo de datos

### 3.1 Esquema relacional

El esquema comprende trece tablas, con integridad referencial y un mecanismo de migración que adapta la estructura cuando una versión nueva lo requiere. Las tablas se agrupan en tres conjuntos: el núcleo de personal y nómina, el dominio académico y la gestión de sesiones.

| Conjunto | Tabla | Propósito |
|----------|-------|-----------|
| Núcleo | `empleados` | Información personal, laboral, bancaria y de contacto del personal |
| Núcleo | `documentos` | Documentos del empleado con tipo, fechas y archivo asociado |
| Núcleo | `incidencias` | Permisos, reposos y ausencias con su soporte y estado de aprobación |
| Núcleo | `contratos` | Relación laboral, tipo, vigencia y encadenamiento de renovaciones |
| Núcleo | `pagos` | Registro de nómina y pagos por periodo |
| Núcleo | `configuraciones` | Parámetros institucionales y del sistema |
| Núcleo | `usuarios` | Credenciales, rol y control de acceso |
| Académico | `estudiantes` | Legajo del estudiante, con cédula única |
| Académico | `grados` | Grados y secciones por año escolar, con docente responsable |
| Académico | `matriculas` | Asignación del estudiante a un grado y periodo |
| Académico | `notas_finales` | Calificaciones por materia y periodo |
| Académico | `periodos_academicos` | Año escolar, cierre y reapertura |
| Sesiones | `tokens_sesion` | Tokens de alcance académico, almacenados solo como resumen criptográfico |

### 3.2 Relaciones principales

Las relaciones del núcleo son de uno a muchos desde el empleado hacia sus documentos, incidencias, contratos y pagos. Las tablas de configuración y de usuarios son registros independientes que sostienen los parámetros del sistema y el control de acceso. En el dominio académico, la matrícula relaciona al estudiante con un grado y un periodo, y las notas finales se vinculan al estudiante, la materia y el periodo, con una única matrícula activa por estudiante y periodo como regla de integridad.

```text
empleados 1 ──── N documentos
empleados 1 ──── N incidencias
empleados 1 ──── N contratos
empleados 1 ──── N pagos
estudiantes 1 ── N matriculas N ── 1 grados
grados 1 ─────── N notas_finales
periodos_academicos 1 ── N matriculas
periodos_academicos 1 ── N notas_finales
configuraciones ─── parámetros del sistema
usuarios ───────── credenciales, rol y control de acceso
tokens_sesion ──── tokens de alcance académico
```

### 3.3 Integridad y migraciones

El esquema impone restricciones de integridad sobre los campos críticos: la cédula del empleado y la del estudiante son únicas, los campos identificativos son obligatorios y las relaciones mantienen la referencia a la entidad padre. El mecanismo de migración permite abrir una base creada por una versión anterior sin pérdida de información, capacidad verificada en la comprobación de arranque del producto, que se ejecuta tanto sobre una base nueva como sobre una base con el esquema anterior.

---

## 4. Módulos funcionales

### 4.1 Módulos de la interfaz

La interfaz presenta nueve módulos de navegación, accesibles con los atajos `Ctrl+1` a `Ctrl+9`.

| Orden | Módulo | Contenido funcional |
|-------|--------|---------------------|
| 1 | Panel de control | Indicadores de nómina del mes, contratos por vencer y dotación activa, con gráficos de barras, dona y línea dibujados sobre el lienzo del propio componente gráfico |
| 2 | Empleados | Registro, consulta, actualización, búsqueda, filtrado, fotografía y ficha individual en PDF |
| 3 | Documentos | Carga de archivos, control de vigencia, consulta y descarga |
| 4 | Incidencias | Registro con soporte, cómputo de días y flujo de aprobación o rechazo |
| 5 | Contratos | Alta, renovación encadenada, terminación con finiquito y control de vencimientos |
| 6 | Nómina | Cálculo del periodo, revisión de pagos, recibo individual y planilla consolidada |
| 7 | Configuración | Datos institucionales, parámetros, políticas, apariencia, seguridad, auditoría y respaldos |
| 8 | Estudiantes | Legajo, búsqueda por nombre o cédula y exportación |
| 9 | Calificaciones | Grados, matrículas, notas finales, consolidado y boletín, con cierre de periodo |

Los siete primeros módulos corresponden al núcleo de gestión de personal y nómina descrito en la versión 3.0.0 del corpus académico; los dos últimos corresponden a la extensión académica incorporada en el repositorio vigente. La ampliación se realizó sobre la misma estructura de capas, sin alterar los módulos preexistentes.

### 4.2 Capa de servicios de negocio

Los servicios implementan las reglas del dominio y constituyen el punto de entrada único de cada operación. Su número y su correspondencia con los módulos se resumen a continuación.

| Servicio | Responsabilidad |
|----------|-----------------|
| Autenticación | Verificación de credenciales, sesión y control de acceso |
| Empleados | Reglas de registro y actualización del personal, incluida la unicidad de la cédula |
| Documentos | Registro documental, control de vigencia y gestión de archivos |
| Incidencias | Registro, cómputo de días, flujo de aprobación y efecto en nómina |
| Contratos | Alta, renovación encadenada, unicidad del contrato vigente y terminación |
| Pagos | Cálculo de la nómina del periodo y registro de pagos |
| Configuración | Parámetros institucionales, políticas y datos del sistema |
| Académico | Legajo del estudiante, grados y matrículas |
| Notas | Calificaciones, consolidado del periodo y cierre del grado |
| Token de sesión | Autorización de alcance académico con vigencia diaria |

Un servicio típico valida la regla de negocio antes de delegar en el repositorio: al crear un empleado, comprueba que no exista otro con la misma cédula y, de existir, interrumpe la operación con un error explícito. Esa validación en la capa de servicios, y no en la interfaz, es la que garantiza que la regla se aplique con independencia del punto de entrada.

### 4.3 Capa de repositorios

El repositorio base implementa las operaciones comunes —crear, obtener, listar, actualizar y eliminar— de forma genérica, y los repositorios concretos heredan de él y añaden las consultas específicas de su entidad, como la búsqueda de un empleado por su cédula o la recuperación de los pagos de un periodo. Esta organización evita la duplicación de las operaciones comunes y concentra en un solo lugar la lógica de persistencia compartida.

---

## 5. Dominio de cálculo de nómina

### 5.1 Aislamiento del dominio

El dominio de nómina constituye una capa propia, aislada de la interfaz y del acceso a datos. El paquete comprende nueve archivos: el motor de cálculo, los parámetros, el impuesto sobre la renta, las horas extra, las prestaciones, la seguridad social, el finiquito y los tipos del dominio, además del inicializador del paquete. El aislamiento permite probar las reglas financieras sin levantar la aplicación, condición que se refleja en el nivel de cobertura alcanzado: 89 % en la medición del 6 de octubre de 2026.

### 5.2 Reglas implementadas

El motor de cálculo contempla las siguientes reglas. La determinación del impuesto sobre la renta admite dos modalidades: una porcentual, que responde a la práctica histórica de algunas instituciones, y otra por tramos progresivos con techos de cotización y aportes patronales. Las horas extraordinarias se calculan con recargo según la jornada en que se laboren —diurna, nocturna o feriada—. Las prestaciones comprenden el aguinaldo, el bono vacacional, las prestaciones por antigüedad, la indemnización y el preaviso, calculados de forma proporcional al tiempo servido. La seguridad social aplica las deducciones y los aportes conforme a los parámetros configurados.

Todos los parámetros cuantitativos —porcentajes, topes, tarifas y valores de referencia— residen en la configuración institucional y no en el código. Esa decisión, derivada del principio de adaptación al contexto, permite que una modificación normativa o una decisión interna se refleje sin alterar el software.

---

## 6. Servicios transversales

### 6.1 Seguridad y control de acceso

El módulo de seguridad implementa la derivación de contraseñas con PBKDF2-HMAC-SHA256, doscientas mil iteraciones y sal aleatoria de dieciséis bytes, con verificación en tiempo constante para evitar la filtración por análisis temporal. Sobre esa base, el control de acceso administra ocho entradas de módulo y cuatro roles —administrador, gestor, usuario y solo lectura—, y el panel de control queda exento del control por constituir un resumen de información de acceso general.

Dos decisiones merecen señalarse. La primera es la denegación explícita ante un módulo desconocido: si un módulo se registra en la interfaz y se omite en el mapa de permisos, el acceso se deniega en lugar de concederse, lo que evita que un olvido de configuración deje un módulo abierto a todos los roles. La segunda es que la autorización académica para la carga de calificaciones no depende solo del rol, sino de un token de alcance limitado vinculado al docente asignado al grado, con vigencia de una jornada y almacenado únicamente como resumen criptográfico.

El sistema incorpora además medidas de endurecimiento operativo: bloqueo de la cuenta tras intentos fallidos con desbloqueo administrativo, caducidad de contraseñas, historial de claves y cambio obligatorio.

### 6.2 Auditoría

El registrador de auditoría conserva las operaciones sensibles con indicación del usuario, la operación y el momento. Su producto es consultable por el administrador y exportable, lo que convierte la trazabilidad en un instrumento verificable y no en un registro inaccesible. La auditoría es, en términos prácticos, la respuesta del sistema a los principios de transparencia y rendición de cuentas que la Constitución impone a la Administración.

### 6.3 Respaldos

La política de respaldo comprende la creación de la copia con marca temporal única, la verificación de su integridad, el registro del evento y la eliminación de las copias que exceden la retención configurada. La restauración valida el archivo, respalda el estado actual antes de reemplazar y deja constancia del procedimiento. La programación automática de los respaldos evita que la continuidad del servicio dependa de que alguien recuerde ejecutarlos.

### 6.4 Generación documental

El generador de documentos produce doce tipos de documento en formato PDF: constancia de trabajo, constancia de estudios, constancia de ingresos, recibo de pago, ficha de empleado, planilla de nómina, liquidación, y reportes de empleados, de nómina, de incidencias, de vencimientos, de contratos y de movimiento anual del empleado. La generación es uniforme y automática, lo que sustituye una elaboración manual lenta y sujeta a variación por un resultado consistente.

### 6.5 Gestión de archivos y exportación

El gestor de documentos administra el almacenamiento de los archivos asociados a los empleados, con control de los formatos admitidos y del tamaño máximo. El exportador genera los listados en formatos abiertos —hoja de cálculo y texto delimitado compatible con las herramientas ofimáticas de uso común—, incluida la exportación de varias hojas. Los validadores reúnen las comprobaciones de formato sobre los datos de entrada, y las utilidades auxiliares concentran las funciones de apoyo compartidas por las distintas capas.

---

## 7. Componentes auxiliares del repositorio

### 7.1 Agente de sincronización entre puestos

El agente de sincronización es un paquete independiente de 13 archivos y 5 433 líneas que replica los datos institucionales entre los puestos de una red local a través de un nodo central. Se ejecuta por sí solo o embebido en la aplicación.

Sus garantías de diseño lo hacen apto para el contexto: la escritura es siempre local y las operaciones se encolan con su marca temporal, de modo que el sistema funcione sin red; la captura es transaccional, con un enlace a los eventos de la sesión de base de datos que registra la operación en la misma transacción que el dato; cada registro recibe un identificador único y se unifica por su clave natural, de modo que un registro creado en dos puestos es uno solo; la mezcla se resuelve por campo con un orden total y determinista que garantiza la convergencia con independencia del orden de llegada; el nodo central actúa como único escritor autoritativo, con servicio HTTP sobre base de datos en modo de registro anticipado, autenticación por token y límite de peticiones; y los archivos binarios viajan como resumen criptográfico y tamaño, con deduplicación en el nodo central.

La tabla de usuarios y las preferencias locales quedan fuera del alcance de la replicación, decisión de diseño coherente con la separación de responsabilidades: cada puesto administra sus propias cuentas y sus propias preferencias, mientras los datos institucionales se comparten.

### 7.2 Actualizador automático

El componente de actualización automática es un ejecutable independiente, sin consola, que consulta la última versión publicada, la compara con la instalada y, de existir una nueva, descarga el instalador con reintentos y verificación de tamaño y lo ejecuta en silencio. Comprende la lógica principal, una ventana de estado y un ícono de bandeja del sistema. Su función práctica es delegar el mantenimiento del software sin exigir un responsable técnico en la institución.

### 7.3 Construcción, instalación y entrega

El script de construcción genera el ejecutable y el instalador, y lee la versión desde el archivo `VERSION` como fuente única. El empaquetado emplea una herramienta de conversión a ejecutable y un generador de instaladores para Windows; el directorio de configuración del instalador contiene los recursos de la instalación. Dos flujos de integración continua automatizan la verificación —con la suite de pruebas y la comprobación de arranque del binario empaquetado— y la publicación firmada de la versión.

### 7.4 Portal de documentación y herramientas

El portal de documentación reproduce el corpus académico y técnico para su consulta en el navegador, con visor integrado de documentos, catálogo centralizado, buscador y funcionamiento autónomo sin conexión. El directorio de herramientas contiene scripts de apoyo, entre ellos el verificador de consistencia documental, el generador del paquete de documentación y los utilitarios de recursos gráficos.

---

## 8. Verificación del producto

### 8.1 Composición de la suite

La suite de pruebas comprende 32 archivos con 551 funciones de prueba, que cubren la seguridad y las credenciales, la validación y las utilidades, la nómina y los pagos, el personal y la contratación, los documentos, el acceso y la sesión, la configuración y el esquema, los reportes, la interfaz, el respaldo y la actualización, la apariencia, las incidencias y el dominio académico con su sincronización.

### 8.2 Resultados de la verificación

La ejecución del 6 de octubre de 2026 registró 551 pruebas exitosas, sin fallos ni errores, con una cobertura total del 56 % y una cobertura de la lógica de negocio del 76 % en los servicios y del 89 % en el dominio de nómina. Los verificadores estáticos —análisis de estilo, formato, ordenación de importaciones y verificación de tipos— no reportaron hallazgos. La comprobación de arranque se ejecutó con resultado satisfactorio tanto sobre una base nueva como sobre una base con el esquema anterior, y la consistencia de la documentación se verificó de forma automática.

### 8.3 Pruebas de seguridad

Las pruebas verifican la verificación de credenciales con derivación de contraseñas, la aplicación del mapa de permisos por rol, la denegación ante módulos desconocidos, la caducidad y el historial de contraseñas, y el tratamiento restringido de los archivos de documentos. La verificación de los controles de acceso constituye la evidencia que sustenta la conformidad del sistema con las exigencias normativas en materia de seguridad de la información.

---

## 9. Puntos de extensión y limitaciones

### 9.1 Puntos de extensión

La arquitectura admite la incorporación de nuevos tipos de empleado y de documento, de nuevos reportes, de nuevos métodos de pago y de la integración con sistemas externos. La extensión más relevante del periodo reciente —el dominio académico— demuestra la viabilidad de ese crecimiento: se incorporaron cinco entidades, sus repositorios, sus servicios y sus módulos de interfaz sobre la misma estructura de capas, sin modificar el núcleo de personal y nómina.

### 9.2 Limitaciones declaradas

El sistema presenta limitaciones de escalabilidad para volúmenes muy superiores a los previstos, derivadas de la elección de una base de datos embebida y de una arquitectura de escritorio de instalación local. El acceso remoto se resuelve dentro de la red local mediante el agente de sincronización, pero no existe una versión web o móvil. La integración con otros sistemas institucionales es limitada, circunstancia que puede resultar restrictiva en instituciones con ecosistemas tecnológicos consolidados. Y el número de iteraciones de la derivación de contraseñas, aunque suficiente conforme al estándar adoptado, conviene elevarlo para alinearse con las guías de seguridad más recientes, según se señala en el documento [03_BASES_LEGALES.md](03_BASES_LEGALES.md).

---

## 10. Conclusión

El software construido responde a un diseño deliberado y verificable. La arquitectura de capas, con el dominio de cálculo aislado, produjo tres efectos concretos: las reglas de negocio se prueban con independencia de la interfaz; la incorporación de funcionalidad nueva no exige refactorizaciones estructurales, como lo demuestra la extensión académica; y la sustitución de componentes queda contenida en un solo paquete, como lo demuestra el retiro completo de tres módulos con sus tablas y parámetros en la evolución hacia la versión 3.0.0.

La estructura del repositorio, la distribución del código, el modelo de datos, los servicios transversales y los componentes auxiliares conforman un producto coherente, documentado y probado. Las limitaciones declaradas no comprometen esa coherencia: delimitan con precisión el alcance del sistema y señalan, con la misma claridad, las rutas de su evolución.

---

## 11. Inventario de archivos del repositorio

El inventario siguiente permite localizar cada componente descrito en este documento.

### 11.1 Código de la aplicación (`src/`)

| Directorio | Archivos | Contenido |
|------------|----------|-----------|
| `config/` | 3 | Configuración general, rutas y sesión de base de datos |
| `gui/` | 10 | Ventana de acceso, ventana principal, módulos, tema y widgets de gráficos |
| `models/` | 16 | Entidades del dominio y enumeraciones |
| `nomina/` | 9 | Motor de cálculo, parámetros, ISR, horas extra, prestaciones, seguridad social, finiquito y tipos |
| `repositories/` | 16 | Repositorio base, búsqueda y repositorios concretos por entidad |
| `services/` | 11 | Servicios de negocio, autenticación, académico y tokens de sesión |
| `utils/` | 10 | Seguridad, auditoría, respaldos, documentos, exportación, PDF, validadores y utilidades |
| raíz | 2 | Inicializador del paquete y punto de entrada |

### 11.2 Componentes auxiliares

| Directorio | Contenido |
|------------|-----------|
| `sync_agent/` | Agente de sincronización: mezcla, captura, aplicador, agente, servidor, cliente, esquema, identidad, registro, común, configuración y punto de entrada |
| `updater/` | Lógica de actualización, ventana de estado, ícono de bandeja y configuración de empaquetado |
| `installer/` | Recursos de la instalación para Windows |
| `docs/` | Portal de documentación para consulta en el navegador |
| `tools/` | Scripts de apoyo, verificador documental y utilidades |
| `tests/` | 32 archivos con 551 funciones de prueba |
| `spec/` | Configuración de empaquetado del ejecutable |
| `.github/workflows/` | Flujos de integración, empaquetado y publicación |

### 11.3 Documentación y configuración de la raíz

| Archivo | Función |
|---------|---------|
| `README.md` | Presentación general del proyecto |
| `DOCUMENTACION_TECNICA.md` | Arquitectura, instalación, operación y mantenimiento |
| `GUIA_USUARIO.md` | Manual operativo del sistema |
| `NOTAS_DESARROLLO.md` | Bitácora de cambios y decisiones técnicas |
| `ESTRUCTURA_PROYECTO_COMPLETO.md` | Descripción de la organización del repositorio |
| `CONTRIBUTING.md` | Convenciones para el desarrollo colaborativo |
| `VERSION` | Fuente única de la versión vigente |
| `pyproject.toml` | Configuración del proyecto y de las herramientas |
| `requirements.txt` y `requirements-dev.txt` | Dependencias de ejecución y de desarrollo |
| `build.py` | Script de construcción del ejecutable y del instalador |

### 11.4 Regla de correspondencia

Todo componente descrito en este documento existe en el repositorio con la ubicación aquí indicada. Cuando la versión del repositorio evolucione, el inventario debe actualizarse de forma simultánea con la documentación técnica, conforme a la regla de mantenimiento del registro de control documental.

---

**El Autor**
[Nombre del Estudiante]

**Institución**
[Nombre de la Institución]
