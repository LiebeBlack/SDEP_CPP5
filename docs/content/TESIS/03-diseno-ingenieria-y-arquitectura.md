# 03. DISEÑO, INGENIERÍA Y ARQUITECTURA

**Documento:** tercero del compendio académico y segundo del informe técnico.
**Sistema documentado:** SDEP_CPP5, versión 3.0.1.
**Alcance:** especificación de requerimientos, arquitectura, modelo de datos, subsistema de sincronización, módulo documental y diseño de la evaluación.

---

## 3.1 Introducción

Este documento describe la solución antes de describir su construcción. Su objeto es responder tres preguntas: qué debe hacer el sistema, cómo se organiza para hacerlo y con qué criterios se comprobará que lo hizo. Las tres respuestas se presentan con el nivel de detalle que permite reconstruir una decisión sin consultar al autor.

El diseño parte de una restricción que condiciona todas las demás: la institución no dispone de un servidor de base de datos ni de personal técnico que lo administre. Esa restricción descarta la arquitectura clásica de tres capas con un motor central y obliga a distribuir la base en los puestos. A partir de allí, cada decisión se evalúa por su efecto sobre tres atributos: continuidad operativa, consistencia de la información y costo de operación.

El documento se organiza en nueve apartados. El primero especifica los requerimientos. El segundo identifica los actores y los casos de uso. El tercero presenta la arquitectura y su despliegue en la red. El cuarto desarrolla el modelo de datos. El quinto especifica el subsistema de sincronización, que es el componente de mayor complejidad. El sexto describe el módulo de generación documental. El séptimo detalla la interfaz y el control de acceso. El octavo diseña las métricas y los instrumentos de evaluación. El noveno establece la trazabilidad entre objetivos, requerimientos, componentes y pruebas.

---

## 3.2 Requerimientos

### 3.2.1 Requerimientos funcionales

Los requerimientos se agruparon por dominio y se numeraron con un identificador estable, que se conserva en las pruebas y en la matriz de trazabilidad. La prioridad se expresa con la escala MoSCoW: debe, debería, podría.

| ID | Requerimiento | Prioridad | Módulo |
|---|---|---|---|
| RF-01 | Registrar, consultar, actualizar y desactivar trabajadores con cédula única | Debe | Empleados |
| RF-02 | Almacenar datos personales, laborales, bancarios, de salud y de contacto | Debe | Empleados |
| RF-03 | Adjuntar fotografía y documentos digitalizados al expediente | Debe | Documentos |
| RF-04 | Clasificar documentos por tipo y controlar fecha de emisión y vencimiento | Debe | Documentos |
| RF-05 | Alertar sobre documentos vencidos y próximos a vencer | Debe | Documentos |
| RF-06 | Registrar incidencias con tipo, fechas, soporte y estado de aprobación | Debe | Incidencias |
| RF-07 | Aprobar o rechazar incidencias con registro del responsable | Debe | Incidencias |
| RF-08 | Registrar contratos con tipo, vigencia, renovación y terminación | Debe | Contratos |
| RF-09 | Calcular finiquito y prestaciones al terminar un contrato | Debería | Contratos |
| RF-10 | Generar nómina por periodo con deducciones y horas extra | Debe | Nómina |
| RF-11 | Emitir recibo de pago y planilla de nómina en PDF | Debe | Nómina / PDF |
| RF-12 | Registrar estudiantes con cédula única y datos del representante | Debe | Estudiantes |
| RF-13 | Crear grados y secciones por año escolar con docente responsable | Debe | Académico |
| RF-14 | Matricular un estudiante una sola vez por grado y periodo | Debe | Académico |
| RF-15 | Registrar, corregir y eliminar notas finales por materia | Debe | Calificaciones |
| RF-16 | Cargar notas por lote en una sola transacción | Debe | Calificaciones |
| RF-17 | Consolidar el periodo, emitir boletín y acta final del grado | Debe | Calificaciones |
| RF-18 | Cerrar y reabrir periodos con bloqueo de notas | Debe | Académico |
| RF-19 | Autorizar la escritura de notas solo al administrador o al docente del grado | Debe | Calificaciones |
| RF-20 | Generar constancias de trabajo, estudios e ingresos en PDF | Debe | PDF |
| RF-21 | Generar ficha del empleado y liquidación en PDF | Debería | PDF |
| RF-22 | Generar reportes de empleados, incidencias, vencimientos y contratos | Debe | PDF |
| RF-23 | Exportar listados a Excel y CSV con codificación compatible | Debería | Exportación |
| RF-24 | Autenticar usuarios con contraseña derivada y bloquear por intentos fallidos | Debe | Seguridad |
| RF-25 | Aplicar permisos por rol y por módulo | Debe | Seguridad |
| RF-26 | Registrar en auditoría las operaciones sensibles | Debe | Auditoría |
| RF-27 | Ejecutar respaldos con verificación de integridad y restauración | Debe | Respaldos |
| RF-28 | Sincronizar automáticamente en segundo plano y bajo demanda | Debe | Sincronización |
| RF-29 | Registrar las operaciones locales en un journal transaccional | Debe | Sincronización |
| RF-30 | Resolver conflictos por campo y conservar el valor perdedor | Debe | Sincronización |
| RF-31 | Replicar binarios por hash con límite de tamaño configurable | Debería | Sincronización |
| RF-32 | Administrar dispositivos y revocar tokens desde el nodo central | Debe | Sincronización |

### 3.2.2 Requerimientos no funcionales

Los requerimientos no funcionales se expresan con una métrica y un umbral, porque una cualidad sin umbral no puede verificarse. Los valores se adoptaron antes de la construcción y se conservan en la Fase IV como criterios de aceptación.

| ID | Categoría | Requerimiento | Métrica | Umbral |
|---|---|---|---|---|
| RNF-01 | Rendimiento | Latencia de una petición en la LAN | Percentil 95 | ≤ 200 ms |
| RNF-02 | Rendimiento | Caudal de sincronización con lote de 50 operaciones | Operaciones por segundo | ≥ 100 |
| RNF-03 | Fiabilidad | Tasa de éxito ante desconexión controlada | Operaciones confirmadas / registradas | ≥ 99 % |
| RNF-04 | Fiabilidad | Recuperación tras corte de energía | Operaciones perdidas | 0 |
| RNF-05 | Consistencia | Convergencia entre puestos tras sincronizar | Filas divergentes | 0 |
| RNF-06 | Disponibilidad | Operación local sin nodo central | Funciones disponibles | 100 % de lectura y escritura local |
| RNF-07 | Usabilidad | Puntuación SUS | Media | ≥ 70 |
| RNF-08 | Seguridad | Almacenamiento de contraseñas | Derivación | PBKDF2-HMAC-SHA256, sal de 16 bytes |
| RNF-09 | Seguridad | Autorización de escritura de notas | Acceso no autorizado | 0 casos |
| RNF-10 | Mantenibilidad | Cobertura de pruebas del dominio de cálculo | Líneas | ≥ 90 % |
| RNF-11 | Portabilidad | Ejecución en Windows y Linux | Plataformas | 2 |
| RNF-12 | Capacidad | Puestos por nodo central | Puestos | ≥ 20 |
| RNF-13 | Capacidad | Tamaño de binario replicado por defecto | Megabytes | ≤ 5 |
| RNF-14 | Operación | Instalación sin servidor de aplicaciones | Dependencias externas | 0 |

La diferencia entre RNF-01 y RNF-03 merece una aclaración. El primero mide el tiempo de una petición cuando la red funciona; el segundo mide la proporción de operaciones que sobreviven a una interrupción. Un sistema puede ser rápido y perder datos, o lento y confiable. El proyecto exige ambas cosas y por eso declara los dos umbrales por separado.

### 3.2.3 Restricciones de diseño

Las restricciones se derivan del diagnóstico y no admiten negociación. La primera es la operación sin internet: ninguna función esencial puede depender de un servicio externo. La segunda es la operación sin servidor dedicado: el nodo central debe ejecutarse en un equipo de escritorio convencional. La tercera es la compatibilidad con los equipos existentes, que incluyen versiones de Windows y distribuciones de Linux sin soporte extendido. La cuarta es la instalación sin permisos de administrador sobre la red. La quinta es la conservación de los datos históricos durante las actualizaciones.

---

## 3.3 Actores y casos de uso

### 3.3.1 Actores

| Actor | Descripción | Permisos generales |
|---|---|---|
| Administrador | Responsable de la configuración y de la seguridad | Acceso total, gestión de usuarios, reapertura de periodos, configuración de sincronización |
| Gestor | Personal de secretaría o dirección con funciones operativas | Empleados, documentos, incidencias, contratos, nómina y reportes; sin gestión de usuarios |
| Usuario | Personal administrativo o docente con consulta y registro limitado | Consulta y registro en los módulos asignados |
| Solo lectura | Personal que únicamente consulta | Consulta sin escritura |
| Docente de grado | Docente responsable de un grado | Escritura de notas del grado asignado, mediante token de sesión |
| Nodo central | Servicio de sincronización | Recibe, valida y redistribuye operaciones; no tiene interfaz de usuario |

### 3.3.2 Casos de uso principales

```text
                 +-------------------------------------------+
                 |            SISTEMA SDEP_CPP5              |
                 |                                           |
  Administrador  |  Gestionar usuarios y roles               |
  -------------->|  Configurar institución y nómina          |
                 |  Configurar y supervisar sincronización   |
                 |  Reabrir periodo académico                |
                 |                                           |
  Gestor         |  Registrar trabajador y expediente        |
  -------------->|  Registrar incidencia y aprobarla         |
                 |  Generar nómina y recibo                  |
                 |  Emitir constancia o reporte              |
                 |                                           |
  Docente        |  Registrar notas del grado asignado       |
  -------------->|  Consultar boletín y acta                 |
                 |                                           |
  Nodo central   |  Recibir push y entregar pull             |
  <------------->|  Validar token y limitar peticiones       |
                 |  Registrar conflictos y bitácora          |
                 +-------------------------------------------+
```

### 3.3.3 Casos de uso expandidos

**CU-01. Registrar un trabajador durante una desconexión.** El gestor abre el módulo de empleados, completa el formulario y confirma. El sistema valida la cédula contra la base local, escribe el registro y la operación del journal en la misma transacción, y muestra la confirmación. Si el nodo central no responde, el registro permanece en la cola y la interfaz indica el número de operaciones pendientes. El caso termina con el registro confirmado localmente, con independencia del estado de la red.

**CU-02. Sincronizar manualmente.** El usuario con permiso abre la pantalla de sincronización y pulsa «Sincronizar ahora». El sistema despierta el hilo de fondo, ejecuta un ciclo completo, recibe las operaciones del nodo central y muestra el resumen: enviadas, recibidas, conflictos y errores. Si el ciclo falla, muestra la causa y conserva las operaciones pendientes.

**CU-03. Registrar notas por lote.** El docente responsable abre el módulo de calificaciones, selecciona el grado y el periodo, carga las notas y confirma. El sistema verifica que el periodo esté abierto, que el docente tenga autorización sobre el grado, que la matrícula exista y que la calificación esté dentro de la escala. Luego escribe todas las filas en una sola transacción. Si una fila falla, no se escribe ninguna.

**CU-04. Emitir una constancia de trabajo.** El gestor selecciona al trabajador y el tipo de constancia. El sistema verifica que los datos obligatorios estén completos, genera el PDF con la plantilla institucional, registra la emisión en la auditoría y abre el archivo. Si falta un dato, muestra la lista de campos faltantes y no genera el documento.

**CU-05. Resolver un conflicto de sincronización.** El administrador abre la bandeja de conflictos, revisa el valor local y el valor remoto, y decide cuál conservar. El sistema registra la decisión, aplica el valor elegido y conserva la traza. Ningún valor se descarta sin que quede registro de la decisión.

---

## 3.4 Arquitectura

### 3.4.1 Vista de capas

La arquitectura se organiza en seis capas y un dominio de cálculo aislado. La dirección de dependencia es única: la presentación conoce a los servicios, los servicios conocen a los repositorios y al dominio, y los repositorios conocen a los modelos. Ninguna capa inferior importa una superior.

```text
+--------------------------------------------------------------------------+
| PRESENTACION · CustomTkinter                                             |
| LoginWindow · MainWindow · nueve modulos · tema claro/oscuro · atajos    |
+------------------------------------+-------------------------------------+
                                     |
+------------------------------------v-------------------------------------+
| SERVICIOS · reglas de negocio y orquestacion                             |
| auth · empleado · documento · incidencia · contrato · pago · academico  |
| nota · token de sesion · configuracion                                   |
+------------------------------------+-------------------------------------+
                                     |
+------------------------------------v-------------------------------------+
| REPOSITORIOS · patron Repository sobre repositorio base                  |
| consultas reutilizables · transacciones · paginacion                     |
+------------------------------------+-------------------------------------+
                                     |
+------------------------------------v-------------------------------------+
| MODELOS · SQLAlchemy ORM                                                 |
| trece entidades del dominio · enumeraciones · restricciones              |
+------------------------------------+-------------------------------------+
                                     |
+------------------------------------v-------------------------------------+
| DOMINIO DE NOMINA · calculo puro, sin interfaz ni base de datos          |
| motor · parametros · ISR · horas extra · prestaciones · finiquito        |
+------------------------------------+-------------------------------------+
                                     |
+------------------------------------v-------------------------------------+
| SERVICIOS TRANSVERSALES · seguridad, trazabilidad y sostenibilidad       |
| security · audit_logger · backup_manager · pdf_generator · exporter      |
+------------------------------------+-------------------------------------+
                                     |
+------------------------------------v-------------------------------------+
| PERSISTENCIA · SQLite + journal (WAL en el nodo central)                  |
+--------------------------------------------------------------------------+
```

La separación del dominio de nómina respecto de la interfaz y del acceso a datos es la decisión de diseño con mayor efecto sobre la verificabilidad. Permite probar el cálculo con funciones puras, sin base de datos y sin ventana, y permite que una modificación de la interfaz no altere una regla de cálculo.

### 3.4.2 Patrones aplicados

| Patrón | Problema que resuelve | Implementación |
|---|---|---|
| Repository | Aislar el acceso a datos de las reglas de negocio | Repositorio base genérico y repositorios concretos por entidad |
| Service Layer | Concentrar las reglas y la orquestación | Un servicio por dominio, con un punto de entrada por operación |
| MVP adaptado | Separar la vista de la lógica de presentación | Componentes de CustomTkinter como vistas y servicios como presentadores |
| Transactional Outbox | Evitar que un cambio se pierda o se anuncie sin confirmarse | Journal escrito en la misma transacción que el dato |
| Idempotent Receiver | Evitar la doble aplicación de una operación reenviada | Tabla de operaciones aplicadas y comparación por campo |
| Dependency Injection | Permitir pruebas y sustitución de colaboradores | Servicios que reciben repositorios y clientes |
| Singleton controlado | Evitar múltiples motores y sesiones | Fábrica de sesión única en `src/config/database.py` |

### 3.4.3 Vista de despliegue en la red local

```text
                     RED LOCAL DE LA INSTITUCION

  +----------------+      +----------------+      +----------------+
  | PUESTO         |      | PUESTO         |      | PUESTO         |
  | SECRETARIA     |      | DIRECCION      |      | COORDINACION   |
  |                |      |                |      |                |
  | SQLite local   |      | SQLite local   |      | SQLite local   |
  | Agente sync    |      | Agente sync    |      | Agente sync    |
  +--------+-------+      +--------+-------+      +--------+-------+
           |                       |                       |
           |        HTTP /api/v1  |                       |
           +-----------------------+-----------------------+
                                   |
                    +--------------v---------------+
                    | NODO CENTRAL                 |
                    | ThreadingHTTPServer          |
                    | SQLite central en WAL        |
                    | Unico escritor, seq global   |
                    | Tokens por dispositivo       |
                    +--------------+---------------+
                                   |
                    +--------------v---------------+
                    | RESPALDO DIARIO              |
                    | Archivo comprimido + hash    |
                    +------------------------------+
```

El nodo central no necesita un servidor dedicado. Se ejecuta como un proceso de consola en el equipo de la secretaría, escucha en el puerto 8765 por defecto y escribe en un archivo SQLite independiente del que usa la aplicación de ese puesto. Esa separación evita que la base del nodo central compita por bloqueos con la base local del equipo que lo hospeda.

### 3.4.4 Decisiones arquitectónicas y su justificación

**Base de datos por puesto en lugar de base central única.** Una base central exigiría que todos los puestos tuvieran red en todo momento. La réplica local elimina esa dependencia y traslada el costo a la reconciliación, que el sistema resuelve con el journal y la mezcla por campo.

**HTTP en lugar de un intermediario de mensajes.** Un intermediario habría añadido un componente que la institución no puede operar y habría exigido abrir puertos adicionales. HTTP sobre la intranet utiliza la infraestructura existente y puede diagnosticarse con un navegador.

**Un solo escritor en el nodo central.** La alternativa, varios escritores con coordinación distribuida, habría introducido un consenso que el proyecto no necesita. El nodo central serializa las escrituras y asigna un número de secuencia global, lo que simplifica el orden y la depuración.

**Mezcla por campo en lugar de por fila.** La mezcla por fila descarta una edición completa cuando dos usuarios tocan columnas distintas del mismo registro. La mezcla por campo conserva ambas ediciones y solo registra conflicto cuando el choque es sobre la misma columna.

**Journal en la misma transacción.** Un journal escrito después de la confirmación podría perder la operación si el equipo falla entre ambos pasos. La escritura en la misma transacción elimina esa ventana.

---

## 3.5 Modelo de datos

### 3.5.1 Vista general

El esquema comprende trece tablas de dominio y doce tablas de sincronización. Las primeras representan la información institucional; las segundas sostienen la replicación y no se replican entre puestos, salvo las operaciones y los identificadores.

```text
 DOMINIO DE PERSONAL Y NOMINA

 +-------------+       +-------------+       +-------------+
 | EMPLEADOS   |1     *| DOCUMENTOS  |       | CONTRATOS   |
 |-------------|-------|-------------|       |-------------|
 | id          |       | id          |       | id          |
 | cedula (U)  |       | empleado_id |*     1| empleado_id |
 | nombres     |       | tipo        |       | numero (U)  |
 | apellidos   |       | vencimiento |       | vigencia    |
 | cargo       |       +-------------+       +-------------+
 | salario     |
 | activo      |       +-------------+       +-------------+
 +------+------+1     *| INCIDENCIAS |       | PAGOS       |
        |              |-------------|       |-------------|
        |              | empleado_id |       | empleado_id |
        |              | tipo        |       | periodo     |
        |              | estado      |       | neto        |
        |              +-------------+       +-------------+
        |
        |              +-------------+       +-------------+
        +-------------*| CONFIGURAC. |       | USUARIOS    |
                       | clave (U)   |       | username(U) |
                       | valor       |       | rol         |
                       +-------------+       +-------------+

 DOMINIO ACADEMICO

 +-------------+       +-------------+       +-------------+
 | ESTUDIANTES |1     *| MATRICULAS  |*     1| GRADOS      |
 |-------------|-------|-------------|-------|-------------|
 | id          |       | estudiante  |       | id          |
 | cedula (U)  |       | grado_id    |       | nombre      |
 | nombres     |       | periodo_id  |       | seccion     |
 | represent.  |       | estado      |       | docente     |
 +------+------+       +------+------+       +------+------+
        |                     |                     |
        |                     |1                    |1
        |                    *|                    *|
        |              +------v------+       +------v------+
        +-------------*| NOTAS       |       | PERIODOS    |
                       | FINALES     |       | ACADEMICOS  |
                       |-------------|       |-------------|
                       | estudiante  |       | nombre      |
                       | grado       |       | cerrado     |
                       | materia     |       +-------------+
                       | calificacion|
                       +-------------+

 SESION
 +-------------+
 | TOKENS      |  hash · usuario · grado · expiracion
 +-------------+
```

### 3.5.2 Diccionario de tablas de dominio

| Tabla | Propósito | Claves y restricciones | Campos relevantes |
|---|---|---|---|
| `empleados` | Expediente del trabajador | `cedula` única; borrado lógico con `activo` | Datos personales, laborales, bancarios, salario base |
| `documentos` | Documentos del trabajador | Clave foránea a `empleados`; tipo y vencimiento | Nombre, ruta, contenido binario, fechas |
| `incidencias` | Permisos, reposos y ausencias | Clave foránea a `empleados`; estado de aprobación | Tipo, fechas, soporte, decisión |
| `contratos` | Relación laboral | `numero` único; vigencia y estado | Tipo, inicio, fin, salario pactado, archivo |
| `pagos` | Nómina y recibos | Clave foránea a `empleados`; periodo | Bruto, deducciones, neto, horas extra |
| `configuraciones` | Parámetros institucionales | `clave` única | Valor, grupo, descripción |
| `usuarios` | Credenciales y roles | `username` único | Hash de contraseña, rol, estado, intentos |
| `estudiantes` | Legajo del estudiante | `cedula` única; borrado lógico | Nombres, nivel, representante, contacto |
| `grados` | Grados y secciones | Único por nombre, sección y año escolar | Docente responsable |
| `matriculas` | Asignación a grado y periodo | Una matrícula activa por estudiante y periodo | Estado, fecha |
| `notas_finales` | Calificaciones | Única por estudiante, grado, materia y periodo | Calificación, materia |
| `periodos_academicos` | Año escolar | Único por nombre | Inicio, fin, estado de cierre |
| `tokens_sesion` | Autorización temporal de escritura | Solo se almacena el hash | Usuario, grado, expiración |

### 3.5.3 Normalización e integridad

El esquema se normalizó hasta la tercera forma normal. La decisión separó los datos de contacto de los laborales, aisló las notas en su propia tabla y extrajo los parámetros a `configuraciones`. Esa separación evita que un cambio de dirección obligue a reescribir la nómina y que un cambio de salario altere el histórico de pagos.

La integridad se sostiene en cuatro mecanismos. El primero es la clave primaria sustituta, que no cambia aunque cambie la cédula. El segundo es la clave natural única, que impide duplicados. El tercero es la clave foránea, que impide registros huérfanos. El cuarto es la restricción de unicidad compuesta en `notas_finales` y `matriculas`, que impide dos notas para la misma materia o dos matrículas activas para el mismo estudiante.

### 3.5.4 Índices

| Índice | Tabla | Columnas | Consulta que optimiza |
|---|---|---|---|
| `ix_empleados_cedula` | `empleados` | `cedula` | Búsqueda por documento |
| `ix_empleados_activo` | `empleados` | `activo` | Dotación vigente |
| `ix_documentos_vencimiento` | `documentos` | `fecha_vencimiento` | Reporte de vencimientos |
| `ix_incidencias_empleado` | `incidencias` | `empleado_id`, `fecha_inicio` | Historial del trabajador |
| `ix_pagos_periodo` | `pagos` | `periodo`, `empleado_id` | Nómina del periodo |
| `ix_matriculas_periodo` | `matriculas` | `periodo_id`, `grado_id` | Listado por grado |
| `ix_notas_periodo` | `notas_finales` | `periodo_id`, `grado_id` | Consolidado y acta |
| `ix_sync_journal_pendiente` | `sync_journal` | `estado`, `secuencia` | Envío de pendientes |

### 3.5.5 Migraciones

El sistema no elimina tablas ni columnas durante una actualización. La rutina de migración compara el esquema declarado por los modelos con el esquema existente y agrega las columnas o tablas faltantes, conserva los datos y registra la versión aplicada. Si la migración falla, se revierte la transacción y la aplicación se detiene con un mensaje que indica la versión de origen y la versión de destino.

Esa política tiene un límite: no resuelve un cambio destructivo, como renombrar una columna con pérdida de datos. Cuando ese cambio es inevitable, se documenta en las notas de desarrollo y se ejecuta con un respaldo previo verificado.

---

## 3.6 Subsistema de sincronización

### 3.6.1 Topología y responsabilidades

La sincronización conecta tres clases de nodo. El **puesto** posee una base completa, escribe siempre en local y ejecuta un agente que envía y recibe operaciones. El **nodo central** posee la base compartida, es el único escritor de esa base y asigna un número de secuencia global a cada operación aceptada. El **dispositivo** es la identidad lógica de un puesto, representada por un identificador estable y un token que el administrador entrega una sola vez.

Un puesto nunca escribe directamente en la base del nodo central. Esa prohibición es la que permite que el nodo central sea un único escritor y que el orden de las operaciones sea una decisión suya y no el resultado de una carrera entre clientes.

### 3.6.2 Modelo de metadatos

| Tabla | Función | Campos principales |
|---|---|---|
| `sync_ids` | Identidad global de cada fila | tabla, fila local, UUID, clave natural |
| `sync_journal` | Outbox de operaciones locales | op_id, dispositivo, tabla, clase, payload, momento, secuencia, estado, intentos |
| `sync_campos` | Última versión conocida por campo | op_id, tabla, fila, campo, valor, momento, dispositivo |
| `sync_versiones` | Versión agregada de la fila | tabla, fila, momento, dispositivo, op_id |
| `sync_ops_aplicadas` | Registro de idempotencia | op_id, momento de aplicación, resultado |
| `sync_cursor` | Posición de lectura del nodo central | dispositivo, último seq recibido |
| `sync_conflictos` | Bandeja de valores perdedores | tabla, fila, campo, valor local, valor remoto, regla, revisado |
| `sync_blobs` | Índice de binarios por hash | hash, tamaño, estado, ruta |
| `sync_estado` | Estado observable del agente | habilitado, último ciclo, pendientes, último error |
| `sync_dispositivos` | Registro de puestos autorizados | id, nombre, hash de token, estado |
| `sync_ops` | Log de operaciones del nodo central | seq global, op_id, dispositivo, payload, momento |
| `sync_bitacora` | Traza de peticiones y errores | momento, dispositivo, ruta, código, detalle |

Las tablas de metadatos no se replican como datos de negocio. El nodo central conserva las suyas y cada puesto conserva las propias. La única información que viaja es la operación, su identificador y su carga útil.

### 3.6.3 Captura transaccional

La captura se instala como un enganche a los eventos de la sesión de SQLAlchemy. El proceso tiene dos tiempos.

En `before_flush`, el sistema recorre los objetos nuevos, modificados y eliminados, lee el historial de atributos y anota en la sesión qué columnas cambiaron. Todavía no conoce las claves primarias de las filas nuevas, de modo que solo prepara la intención.

En `after_flush_postexec`, las claves primarias ya existen. El sistema escribe en `sync_journal` la operación definitiva, en `sync_campos` la versión de cada campo modificado y en `sync_versiones` la versión agregada de la fila. Esas escrituras se añaden a la misma sesión y se confirman con la transacción del dato.

```text
  SERVICIO
     |  session.add(empleado)
     v
  SQLAlchemy
     |  before_flush  -> se anota que cedula y cargo cambiaron
     |  flush         -> INSERT en empleados
     |  after_flush   -> INSERT en sync_journal + sync_campos + sync_versiones
     v
  COMMIT  --------------------------------------------+
     |                                                  |
     +--> si el commit falla, el journal se deshace     |
     +--> si el commit confirma, la operacion existe    |
                                                        v
                                              el agente la enviara
```

La consecuencia practica es que no puede existir una edicion sin operacion ni una operacion sin edicion. Un corte de energia entre el flush y el commit deshace ambos. Un corte despues del commit conserva ambos.

### 3.6.4 Identidad global

Cada fila sincronizable recibe un UUID en `sync_ids` y conserva su clave natural. La relación se establece en el primer registro y se reutiliza en las siguientes operaciones. Cuando dos puestos crean por separado un registro con la misma clave natural, el nodo central los unifica y conserva el UUID del primero que llegó, sin duplicar la fila.

La doble identidad resuelve dos problemas distintos. El UUID permite reconocer la misma fila entre puestos aunque las claves primarias locales difieran. La clave natural permite advertir que dos filas distintas representan al mismo trabajador o al mismo estudiante. Sin la primera, la replicación dependería de identificadores locales que colisionan; sin la segunda, la base acumularía duplicados que ninguna consulta podría reconciliar.

### 3.6.5 Protocolo HTTP

El nodo central expone cuatro rutas versionadas. Todas exigen el token del dispositivo en la cabecera `Authorization` y su identificador en `X-Dispositivo`.

| Ruta | Método | Función | Respuesta |
|---|---|---|---|
| `/api/v1/ping` | GET | Diagnóstico y verificación de credenciales | Estado, versión, hora del servidor |
| `/api/v1/push` | POST | Enviar un lote de operaciones | Resultado por operación y secuencia asignada |
| `/api/v1/pull` | GET | Recibir operaciones posteriores a un cursor | Lote de operaciones y cursor siguiente |
| `/api/v1/blob/{hash}` | GET y POST | Descargar o cargar un binario | Contenido o confirmación |

El intercambio de `push` es idempotente. Si el cliente reenvía un lote porque perdió la respuesta, el servidor reconoce las operaciones por su `op_id`, no las aplica de nuevo y devuelve el mismo resultado. El intercambio de `pull` es paginado: el cliente envía su cursor y el servidor devuelve un lote acotado con el cursor siguiente. La paginación evita que un puesto que estuvo desconectado durante semanas reciba un lote de tamaño inmanejable.

```text
  PUESTO A                       NODO CENTRAL                      PUESTO B
  --------                       ------------                      --------
  journal pendiente
       |
       |  POST /push  (lote, token, dispositivo)
       +------------------------------>
                                      | valida token
                                      | verifica op_id repetido
                                      | aplica y asigna seq global
                                      | registra conflicto si corresponde
       <------------------------------+
       |  resultado por operacion
       |  marca journal como confirmado
       |
       |  GET /pull?cursor=N
       +------------------------------>
                                      | devuelve operaciones > N
       <------------------------------+
       |  aplica mezcla por campo
       |  actualiza cursor
                                                          (ciclo equivalente)
```

### 3.6.6 Algoritmo de mezcla

La mezcla se decide por campo y no por fila. Para cada campo se comparan la última versión conocida y la que llega, con un orden total y determinista:

```text
orden(a, b) = comparar (momento, dispositivo, op_id)

si |momento(a) - momento(b)| <= 2 s:
    se consideran simultaneas y desempata el identificador de dispositivo

si valor_remoto == valor_local:
    no hay cambio
si orden(remoto) > orden(local):
    gana el remoto y se actualiza la version del campo
si orden(remoto) < orden(local):
    se ignora el remoto y se registra como conflicto si el campo es sensible
si el campo esta en CAMPOS_SENSIBLES:
    se registra conflicto aunque gane el remoto
```

El orden es total porque la terna incluye el identificador de la operación, que es único. Esa propiedad garantiza que todos los nodos elijan el mismo ganador sin importar el orden de llegada, condición necesaria para la convergencia.

Las reglas de borrado se apartan del orden general en un caso. Si una fila fue borrada y después llega una edición posterior al borrado, la fila revive. La decisión se registra y se explica: perder un dato recién editado es más grave que resucitar un registro borrado por error.

### 3.6.7 Aplicación idempotente y operaciones diferidas

Antes de aplicar una operación, el receptor consulta `sync_ops_aplicadas`. Si el `op_id` ya existe, devuelve el resultado anterior y no toca los datos. Esa consulta es la que convierte una entrega repetida en una entrega efectiva.

Una operación puede llegar antes que la fila de la que depende. El caso típico es una nota que referencia una matrícula creada en otro puesto y que aún no llegó. El sistema no la descarta: la guarda en una cola de diferidas y la reintenta al final del ciclo. Si la dependencia no llega después de varios ciclos, la operación queda marcada para revisión y se informa en el estado del agente.

### 3.6.8 Ciclo automático y sincronización manual

El agente se ejecuta en un hilo de fondo. Cada ciclo hace tres cosas: envía los pendientes, recibe las operaciones nuevas y reintenta las diferidas. La espera entre ciclos es un evento interrumpible, de modo que el botón «Sincronizar ahora» despierta el hilo sin reiniciarlo.

Cuando el ciclo falla, la espera crece de forma exponencial: 30 segundos, 60, 120, 240 y 300 como máximo. A cada espera se le suma un azar de hasta el 10 % del valor base, con un tope de 5 segundos. El azar evita que todos los puestos de la institución golpeen el servidor al mismo tiempo cuando vuelve la red. Cuando el ciclo tiene éxito, la espera vuelve al intervalo configurado.

| Estado | Condición | Efecto sobre el usuario |
|---|---|---|
| Inactivo | Sincronización no configurada | Trabaja en local, sin aviso de error |
| Sincronizando | Ciclo en curso | Indicador de actividad |
| Correcto | Último ciclo sin errores | Contadores actualizados |
| Sin conexión | El nodo central no responde | Aviso discreto y contador de pendientes |
| Error de token | Credencial rechazada | Aviso persistente y detención del ciclo |

### 3.6.9 Seguridad del canal

El token del dispositivo se almacena en el nodo central como un hash PBKDF2 con sal. No se puede recuperar, solo reemplazar. Cada petición se valida contra ese hash y contra el estado del dispositivo, de modo que revocar un puesto surte efecto en la siguiente petición.

El nodo central aplica un límite de peticiones por minuto y por dispositivo. El límite no sustituye la autenticación: evita que un token comprometido se use para saturar el servicio. El canal puede cifrarse con TLS si la institución instala un certificado; sin TLS, el token viaja en claro por la intranet y esa circunstancia se advierte en el manual de operación.

### 3.6.10 Garantías y límites

| Propiedad | Garantía | Condición |
|---|---|---|
| Atomicidad local | El dato y su operación se confirman juntos | Siempre |
| Durabilidad local | La operación confirmada sobrevive a un corte de energía | Transacción confirmada y escritura completada por el sistema operativo |
| Entrega efectiva | Una operación repetida no altera el estado | `sync_ops_aplicadas` |
| Convergencia | Dos puestos alcanzan el mismo estado | Ambos reciben todas las operaciones |
| Consistencia fuerte entre puestos | No se garantiza | Requeriría coordinación en línea |
| Orden causal global | No se garantiza | El orden es por campo, no por transacción |
| Reloj sincronizado | No se garantiza | Se toleran 2 s de desfase |

La tabla declara lo que el sistema no hace, y esa declaración es tan importante como la anterior. Un informe que atribuyera consistencia fuerte a esta arquitectura sería incorrecto. La garantía real es convergencia eventual con resolución determinista y trazabilidad de los conflictos.

### 3.6.11 Puntos de extensión para terminales secundarios

El protocolo HTTP se diseñó como un contrato estable y versionado, no como un detalle interno del agente. Esa decisión permite que un terminal secundario consulte la información sin modificar el núcleo del sistema. Las rutas `/api/v1/ping`, `/api/v1/pull` y `/api/v1/blob` bastan para construir una terminal de solo lectura: el terminal se autentica con un token de dispositivo, solicita las operaciones posteriores a su cursor, las aplica en una base local y conserva el cursor para la siguiente sesión.

Una terminal de este tipo requiere cuatro elementos que el producto no incluye. El primero es un ámbito de token de solo lectura, que el nodo central aún no distingue del token de escritura. El segundo es un catálogo de consultas por dominio, porque el protocolo actual entrega operaciones y no vistas consolidadas. El tercero es una política de retención en el terminal, que debe purgar las operaciones antiguas para no crecer sin límite. El cuarto es TLS obligatorio si el terminal opera fuera de la red local.

La aplicación móvil se documenta como arquitectura proyectada y no como funcionalidad entregada. Un cliente móvil exigiría, además de lo anterior, almacenamiento cifrado del token, una cola de salida propia para las operaciones que se registren sin red y una interfaz de resolución de conflictos equivalente a la bandeja del escritorio. Nada de eso se construyó. Lo que existe es el contrato que permitiría construirlo sin reescribir el nodo central, y esa es la contribución de diseño que este apartado declara.

### 3.6.12 Fallos previstos y recuperación

| Fallo | Detección | Recuperación |
|---|---|---|
| Corte de red durante el push | Excepción de red en el cliente | Reintento con espera creciente; el journal conserva el lote |
| Corte de energía en el puesto | La transacción no se confirma | SQLite revierte al último estado consistente |
| Corte de energía en el nodo central | La transacción no se confirma | WAL revierte; las operaciones no confirmadas se reenvían |
| Respuesta perdida después del push | El cliente no recibe confirmación | Reenvío idempotente; el servidor reconoce el `op_id` |
| Token revocado | Respuesta 401 | El agente se detiene y muestra el error |
| Binario mayor que el límite | Verificación de tamaño | Se replica la ficha y el hash, no el contenido |
| Reloj desfasado | Diferencia menor a 2 s tratada como simultánea | Desempate por dispositivo |
| Operación huérfana | Falta la fila padre | Cola de diferidas y reintento |

---

## 3.7 Módulo de generación documental

### 3.7.1 Arquitectura del módulo

El módulo se construyó con ReportLab y su capa de composición Platypus. La generación se organiza en cuatro etapas: verificación de datos obligatorios, construcción de la historia de componentes, renderizado a PDF y registro de la emisión. La verificación ocurre antes de abrir el archivo, de modo que un documento incompleto no llega a generarse.

```text
  SERVICIO DEL DOMINIO
        |  solicita constancia(empleado, tipo)
        v
  PDFGenerator
        |  1. lee la configuracion institucional
        |  2. verifica campos obligatorios
        |  3. construye la historia (parrafos, tablas, firmas)
        |  4. renderiza el PDF
        |  5. devuelve la ruta
        v
  AUDITORIA  -> usuario, tipo, destinatario, momento
        |
        v
  ARCHIVO    -> exports/AAAA/MM/tipo_cedula_fecha.pdf
```

### 3.7.2 Catálogo de documentos

| Documento | Contenido | Uso institucional |
|---|---|---|
| Constancia de trabajo | Identificación, cargo, fecha de ingreso, salario | Trámites del trabajador |
| Constancia de estudios | Identificación del estudiante, grado, periodo | Trámites del estudiante |
| Constancia de ingresos | Ingresos del periodo y deducciones | Trámites bancarios o crediticios |
| Recibo de pago | Conceptos, deducciones y neto | Obligación laboral |
| Ficha del empleado | Datos personales, laborales, bancarios, salud y familia | Expediente interno |
| Planilla de nómina | Una fila por trabajador y totales | Control contable |
| Reporte de empleados | Listado con filtros y totales | Dirección |
| Reporte de incidencias | Incidencias por trabajador o generales | Control de personal |
| Reporte de vencimientos | Documentos vencidos y por vencer | Auditoría documental |
| Reporte de contratos | Vigencia, renovaciones y vencimientos | Gestión laboral |
| Liquidación | Prestaciones, vacaciones y finiquito | Terminación de la relación |
| Movimiento anual del empleado | Pagos y conceptos del año | Declaración tributaria |

### 3.7.3 Reglas de composición

Las plantillas comparten un encabezado con la identificación de la institución, un cuerpo con los datos del destinatario y un pie con la fecha de emisión y la página. La configuración institucional se lee de la tabla `configuraciones`, de modo que un cambio de nombre, dirección o autoridad no exige modificar el código.

El texto se escapa antes de incorporarse al PDF para evitar que un carácter especial rompa la composición. Los importes se formatean con separador de miles y dos decimales. Las fechas se expresan en formato largo en español. Las firmas se representan con líneas y cargos, no con imágenes escaneadas, para que el documento pueda reimprimirse sin pérdida de calidad.

### 3.7.4 Integridad y trazabilidad

Cada emisión se registra en la auditoría con el usuario, el tipo de documento, el destinatario y el momento. El archivo se nombra con el tipo, la cédula y la fecha, y se almacena en una carpeta organizada por año y mes. El sistema no sobrescribe un documento anterior: si se emite dos veces la misma constancia, se generan dos archivos con marcas de tiempo distintas.

El PDF no incorpora firma electrónica certificada. Esa ausencia se declara en el apartado 2.4.8 y se registra como recomendación de evolución. Lo que sí incorpora es la constancia de quién lo emitió y cuándo, que es la condición mínima para que el documento pueda auditarse.

---

## 3.8 Diseño de la interfaz y control de acceso

### 3.8.1 Organización de la interfaz

La ventana principal se organiza en una barra lateral de navegación, un área de contenido y una barra de estado. La barra lateral contiene nueve módulos: panel de control, empleados, documentos, incidencias, contratos, nómina, configuración, estudiantes y calificaciones. Cada módulo se activa con un atajo de teclado, del `Ctrl+1` al `Ctrl+9`, y conserva su estado al cambiar de sección.

El panel de control resume los indicadores que la dirección consulta con mayor frecuencia: dotación activa, nómina del mes, contratos por vencer y documentos vencidos. Los indicadores son tarjetas navegables: al pulsar una tarjeta se abre el módulo correspondiente con el filtro aplicado. Esa decisión reduce el número de clics entre la detección de un problema y su atención.

### 3.8.2 Matriz de permisos

| Módulo | Administrador | Gestor | Usuario | Solo lectura | Docente de grado |
|---|---|---|---|---|---|
| Panel de control | Total | Total | Consulta | Consulta | Consulta |
| Empleados | Total | Total | Consulta | Consulta | Sin acceso |
| Documentos | Total | Total | Consulta | Consulta | Sin acceso |
| Incidencias | Total | Total | Registro | Consulta | Sin acceso |
| Contratos | Total | Total | Consulta | Consulta | Sin acceso |
| Nómina | Total | Total | Consulta | Consulta | Sin acceso |
| Configuración | Total | Consulta | Sin acceso | Sin acceso | Sin acceso |
| Estudiantes | Total | Total | Consulta | Consulta | Consulta |
| Calificaciones | Total | Total | Consulta | Consulta | Escritura del grado |

La matriz se implementa con un verificador de permisos que consulta el rol antes de habilitar una acción y antes de ejecutarla en el servicio. La doble verificación es deliberada: la interfaz evita que el usuario intente una acción que no puede realizar, y el servicio impide que una llamada directa omita la restricción.

### 3.8.3 Autorización de escritura de notas

La escritura de calificaciones tiene un control adicional. El administrador o el docente responsable del grado reciben un token de sesión de una jornada, que se almacena en la base solo como hash. El servicio de notas exige el token, verifica que el grado coincida con el grado del usuario y que el periodo esté abierto. Si el periodo se cerró, la escritura se rechaza aunque el token sea válido. La reapertura requiere rol administrador y queda registrada en la auditoría.

Ese diseño responde a un riesgo concreto: una nota modificada después de la entrega del boletín no puede detectarse por comparación visual si no existe un control de estado. El cierre del periodo convierte el acto de calificar en un acto con fecha de término.

### 3.8.4 Accesibilidad y prevención de errores

La interfaz no depende del ratón. Todos los formularios se recorren con `Tab`, los botones principales tienen atajo y las tablas permiten navegación con teclado. Los mensajes de error se expresan en lenguaje natural y señalan el campo que debe corregirse. Las acciones destructivas piden confirmación y las operaciones por lote muestran un resumen antes de ejecutarse.

El contraste se verificó en los dos temas, claro y oscuro. Las etiquetas no dependen solo del color para transmitir estado: los documentos vencidos se marcan con texto además de con color, y las alertas de sincronización incluyen un mensaje escrito.

---

## 3.9 Diseño de la evaluación cuantitativa

### 3.9.1 Principio de diseño

La evaluación se diseñó antes de construir el sistema, no después. Cada métrica tiene una definición, un instrumento, una condición de prueba y un umbral. Esa anticipación impide que el investigador elija la métrica que favorece al producto y permite que un tercero repita la medición con los mismos criterios.

### 3.9.2 Pruebas de latencia y caudal

| ID | Caso | Condición | Entrada | Métrica | Umbral | Repeticiones |
|---|---|---|---|---|---|---|
| LAT-01 | Diagnóstico en reposo | 1 cliente, sin carga | 1 petición ping | p95 | ≤ 50 ms | 300 |
| LAT-02 | Push de lote pequeño | 1 cliente | 1 operación | p95 | ≤ 100 ms | 300 |
| LAT-03 | Push de lote medio | 1 cliente | 10 operaciones | p95 | ≤ 200 ms | 300 |
| LAT-04 | Push de lote grande | 1 cliente | 50 operaciones | p95 | ≤ 500 ms | 300 |
| LAT-05 | Pull paginado | 1 cliente | 100 operaciones | p95 | ≤ 300 ms | 300 |
| LAT-06 | Concurrencia baja | 4 clientes | 50 operaciones | p95 | ≤ 800 ms | 300 |
| LAT-07 | Concurrencia alta | 8 clientes | 50 operaciones | p95 | ≤ 1500 ms | 300 |
| CAU-01 | Caudal sostenido | 1 cliente | 50 operaciones | ops/s | ≥ 100 | 30 |
| CAU-02 | Caudal con 4 clientes | 4 clientes | 50 operaciones | ops/s | ≥ 300 | 30 |
| ERR-01 | Tasa de error | 8 clientes | 100 operaciones | % | ≤ 1 % | 30 |

Los umbrales de latencia se fijaron con un margen sobre la latencia esperada de una LAN conmutada. El de 50 ms para el diagnóstico es holgado incluso para una red Wi-Fi con interferencia. El de 1500 ms para la condición de mayor concurrencia reconoce que el nodo central serializa las escrituras y que ocho clientes compiten por el mismo recurso.

### 3.9.3 Pruebas de éxito ante desconexión

| ID | Caso | Condición | Entrada | Métrica | Umbral |
|---|---|---|---|---|---|
| SYN-01 | Corte durante la escritura | Nodo central detenido | 200 operaciones por puesto | Confirmación local | 100 % |
| SYN-02 | Reconexión y drenaje | Nodo central restablecido | Journal pendiente | Tasa de éxito | ≥ 99 % |
| SYN-03 | Reenvío del mismo lote | Respuesta perdida simulada | Lote repetido | Duplicados | 0 |
| SYN-04 | Convergencia de campos | Dos puestos editan columnas distintas | 50 filas | Filas divergentes | 0 |
| SYN-05 | Conflicto en campo sensible | Dos puestos editan salario | 1 fila | Conflictos registrados | 1 por choque |
| SYN-06 | Operación huérfana | Nota sin matrícula | 1 operación | Reintento exitoso | 100 % |
| SYN-07 | Corte de energía simulado | Proceso terminado sin cierre | 100 operaciones | Operaciones perdidas | 0 |

La prueba SYN-07 se ejecuta terminando el proceso del puesto de forma abrupta después de confirmar las operaciones. Al reiniciar, el journal debe conservar exactamente las operaciones confirmadas y ninguna de las no confirmadas.

### 3.9.4 Pruebas de consumo de recursos

| ID | Caso | Condición | Métrica | Umbral |
|---|---|---|---|---|
| REC-01 | Reposo | Aplicación abierta sin uso | Memoria residente | ≤ 250 MB |
| REC-02 | Nómina de 100 trabajadores | Generación completa | Memoria y CPU | ≤ 500 MB y ≤ 60 % |
| REC-03 | Sincronización de 1000 operaciones | Lote acumulado | Memoria del nodo central | ≤ 300 MB |
| REC-04 | Generación de 100 PDF | Constancias en serie | Tiempo total y memoria | ≤ 120 s y ≤ 400 MB |

Los umbrales de recursos se fijaron sobre los equipos de la institución, que disponen de 4 GB de memoria. Un consumo superior dejaría al equipo sin margen para el sistema operativo y la aplicación de oficina.

### 3.9.5 Pruebas de usabilidad

| ID | Tarea | Criterio de éxito | Tiempo límite |
|---|---|---|---|
| U-01 | Registrar un trabajador nuevo | Registro confirmado con cédula válida | 4 min |
| U-02 | Localizar un documento y su vencimiento | Documento visible con fecha | 2 min |
| U-03 | Registrar una incidencia y aprobarla | Incidencia en estado aprobado | 3 min |
| U-04 | Generar una constancia de trabajo | PDF abierto con datos correctos | 2 min |
| U-05 | Cargar las notas de un grado | Lote guardado sin errores | 6 min |
| U-06 | Sincronizar manualmente y leer el estado | Ciclo ejecutado y estado interpretado | 2 min |

Cada tarea se evalúa con tres indicadores: éxito dicotómico, tiempo hasta la confirmación y número de errores. Se registra también el tipo de error, según una taxonomía de cuatro categorías: error de comprensión, error de navegación, error de captura y error del sistema.

### 3.9.6 Instrumento SUS

El cuestionario se aplica después de la sesión de tareas. Cada afirmación se responde con una escala de 1 a 5, donde 1 es «muy en desacuerdo» y 5 es «muy de acuerdo».

| N.º | Afirmación |
|---|---|
| 1 | Creo que me gustaría usar este sistema con frecuencia. |
| 2 | Encontré el sistema innecesariamente complejo. |
| 3 | Pensé que el sistema era fácil de usar. |
| 4 | Creo que necesitaría apoyo técnico para poder usar este sistema. |
| 5 | Encontré las diversas funciones del sistema bien integradas. |
| 6 | Pensé que había demasiada inconsistencia en el sistema. |
| 7 | Imagino que la mayoría de las personas aprendería a usar este sistema muy rápidamente. |
| 8 | Encontré el sistema muy incómodo de usar. |
| 9 | Me sentí muy seguro al usar el sistema. |
| 10 | Necesité aprender muchas cosas antes de poder empezar a usar el sistema. |

La puntuación se calcula con la regla descrita en el apartado 2.7.7.4. El cuestionario no se modifica en su contenido, porque una adaptación invalidaría la comparación con las referencias acumuladas.

### 3.9.7 Fichas de registro

La **ficha de observación técnica** contiene siete campos: identificador de la observación, fecha y hora, tarea, participantes, hora de inicio, hora de fin y observaciones. El tiempo se calcula por diferencia y se anota en segundos. La ficha se firma al final de la jornada por el observador y por el responsable de la unidad.

La **ficha de registro de métricas** contiene nueve campos: identificador de la corrida, fecha, equipo cliente, equipo servidor, condición de red, tamaño de lote, número de clientes, repetición y valores medidos. Cada fila del archivo de resultados corresponde a una repetición, de modo que el análisis pueda recalcularse sin depender de resúmenes intermedios.

La **ficha de desconexión** contiene seis campos: ciclo, hora de corte, duración, operaciones registradas por puesto, operaciones confirmadas al restablecer y observaciones. La tasa de éxito se calcula al final del ciclo y se acumula en el informe.

---

## 3.10 Trazabilidad

| Objetivo | Requerimientos | Componentes | Pruebas | Instrumento |
|---|---|---|---|---|
| OE1 Diagnosticar | RF-01 a RF-32 como insumo | Módulos existentes y procesos relevados | No aplica | Ficha de observación y guía de entrevista |
| OE2 Diseñar | RNF-01 a RNF-14 | Arquitectura, modelo de datos, protocolo | Revisión de consistencia | Matriz de trazabilidad |
| OE3 Construir | RF-01 a RF-32 | `src/`, `sync_agent/` | Suite automatizada | Lista de cotejo |
| OE4 Evaluar | RNF-01 a RNF-07 | Nodo central, agente, interfaz | LAT, SYN, REC, U, SUS | Fichas y cuestionario |

La matriz se completa en la Fase IV con la columna de evidencia, que indica el archivo de resultados y la fecha de ejecución. Una fila sin evidencia se reporta como pendiente y no como cumplida.

---

## 3.11 Conclusiones del capítulo

El diseño respondió a la restricción de la institución con una arquitectura de réplicas: cada puesto conserva la base completa y el nodo central actúa como punto de encuentro. Esa decisión permite la operación sin red y traslada la complejidad a la sincronización, que el sistema resuelve con un journal transaccional, identidad global y mezcla por campo.

La especificación se hizo verificable. Los requerimientos tienen identificador y prioridad; los no funcionales tienen métrica y umbral; los casos de uso describen el flujo con sus excepciones; y las pruebas tienen condición, entrada, repetición y criterio de aceptación. Esa estructura es la que permite que la Fase IV reporte resultados y no impresiones.

El diseño también declaró sus límites. La consistencia fuerte entre puestos no se garantiza, el reloj no se asume sincronizado y la firma electrónica no se implementó. Un documento de arquitectura que ocultara esos límites sería más tranquilizador y menos útil. El capítulo siguiente describe cómo se construyó lo aquí especificado y cómo se verificó.

## 3.12 Referencias citadas

International Organization for Standardization. (2018). *ISO 9241-11:2018. Ergonomics of human-system interaction. Part 11: Usability: Definitions and concepts*.

Sauro, J., y Lewis, J. R. (2016). *Quantifying the user experience: Practical statistics for user research* (2.ª ed.). Morgan Kaufmann.

La lista completa de fuentes del compendio se consigna en el documento 02, apartado 2.9.
