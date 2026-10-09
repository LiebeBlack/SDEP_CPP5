# MARCO PRÁCTICO

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 04 del expediente del informe del estado de la investigación.

---

## 1. Introducción y propósito

Este documento describe el marco práctico del proyecto: la manera en que la solución se aplica efectivamente en la institución, los procedimientos que el sistema ejecuta, la forma en que se distribuye e instala, los mecanismos que aseguran su operación sostenida y las condiciones en que se realizará la aplicación piloto. A diferencia del marco teórico, que expone los conceptos que fundamentan el diseño, el marco práctico expone lo que el sistema permite hacer y con qué procedimiento concreto se hace.

Todo lo que aquí se afirma se corresponde con funcionalidad implementada y verificada, con el sistema de distribución efectivamente configurado o con el protocolo de piloto ya definido en el Capítulo III del corpus académico. Cuando un componente permanece pendiente de ejecución —la aplicación en las instituciones y las mediciones asociadas—, se declara como tal.

---

## 2. El sistema en operación

### 2.1 Ciclo de trabajo institucional

El sistema acompaña el ciclo administrativo completo de la gestión de personal. Ese ciclo comprende la configuración inicial de la institución, el registro del personal con su documentación, el control de las incidencias y los permisos, la formalización y el seguimiento de los contratos, el cálculo y la liquidación de la nómina, y la emisión de los documentos y reportes que la institución debe producir.

La secuencia práctica de uso, tal como la guía de usuario la establece, es la siguiente.

1. **Configuración inicial.** El administrador registra los datos de la institución, los parámetros de nómina —porcentajes de deducciones, salario mínimo, techos de cotización— y las políticas de recursos humanos. Esta etapa determina el comportamiento del motor de cálculo y evita que las reglas queden incorporadas al código.
2. **Registro de empleados.** Se incorpora cada empleado con sus datos personales, laborales y de contacto, su fotografía y su clasificación por tipo, cargo y departamento.
3. **Gestión documental.** Se cargan los documentos del empleado —identificación, títulos, certificaciones, reposos— con su tipo, fecha de emisión y, cuando corresponde, fecha de vencimiento, de modo que el sistema pueda advertir los vencimientos próximos.
4. **Control de incidencias.** Se registran los permisos, reposos y ausencias con su soporte, y se recorren las etapas de aprobación o rechazo con registro del responsable de la decisión.
5. **Contratación.** Se formalizan los contratos laborales con su tipo y vigencia, se renuevan encadenadamente y se controlan los vencimientos.
6. **Procesamiento de nómina.** Se selecciona el periodo, se calcula la nómina con las incidencias aprobadas y los conceptos salariales correspondientes, se registran los pagos y se emiten los recibos y la planilla consolidada.
7. **Emisión de documentos y reportes.** Se generan constancias, fichas, reportes de nómina, de incidencias, de vencimientos y de contratos, y se exportan los listados a formatos abiertos.

Este orden no es una imposición del software, sino la descripción procedimental que resulta de la estructura del sistema: cada paso se apoya en el anterior, y el sistema permite ejecutar cada módulo de manera independiente conforme la institución vaya adoptando las distintas funciones, lo que materializa la estrategia de implantación progresiva recomendada en el Capítulo V.

### 2.2 Módulos en funcionamiento

El sistema comprende nueve módulos de navegación, accesibles con los atajos `Ctrl+1` a `Ctrl+9`.

| Orden | Módulo | Función práctica |
|-------|--------|------------------|
| 1 | Panel de control | Indicadores de nómina del mes, contratos por vencer y dotación activa, con gráficos propios |
| 2 | Empleados | Registro, consulta, actualización, búsqueda y ficha del personal |
| 3 | Documentos | Carga, vigencia, consulta y descarga de documentos del personal |
| 4 | Incidencias | Registro, soporte y flujo de aprobación de permisos, reposos y ausencias |
| 5 | Contratos | Formalización, renovación, terminación y control de vencimientos |
| 6 | Nómina | Cálculo del periodo, pagos, recibos y planilla consolidada |
| 7 | Configuración | Datos institucionales, parámetros de nómina, seguridad, auditoría y respaldos |
| 8 | Estudiantes | Legajo académico del estudiante, búsqueda y exportación |
| 9 | Calificaciones | Grados, matrículas, notas y periodos académicos |

Los siete primeros módulos corresponden al núcleo de gestión de personal y nómina; los dos últimos corresponden a la extensión académica incorporada en la versión 3.0.1. Ambos conjuntos comparten la misma estructura de seguridad, auditoría y acceso por rol.

### 2.3 Funciones documentales y de exportación

La generación documental cubre doce tipos de documento oficial en formato PDF: constancias de trabajo, de estudios y de ingresos; recibos de pago; fichas de empleado; planillas de nómina; liquidaciones; y reportes de empleados, de incidencias, de vencimientos, de contratos y de movimiento anual. La exportación de listados se realiza en formatos abiertos —hoja de cálculo y texto delimitado— compatibles con herramientas ofimáticas de uso común. Esa doble capacidad —documento formal para la constancia y formato abierto para el análisis— responde a dos necesidades distintas de la institución y evita que la información quede cautiva en un formato propietario.

### 2.4 Seguridad operativa

La operación del sistema se sostiene sobre tres controles prácticos. El acceso se gobierna por rol, con cuatro perfiles —administrador, gestor, usuario y solo lectura— que delimitan qué módulos ve cada persona y qué operaciones puede ejecutar. La trazabilidad se asegura mediante el registro de auditoría de las operaciones sensibles, con visor consultable por el administrador y capacidad de filtrado. Y la continuidad se protege mediante respaldos automáticos programados con verificación de integridad y política de retención, restaurables desde el propio módulo de configuración.

---

## 3. Distribución e instalación del producto

El sistema se distribuye en tres modalidades, cada una orientada a un tipo de destinatario. La primera es la instalación para usuarios finales en Windows mediante un instalador ejecutable; la segunda es la versión portable para Linux; la tercera es la ejecución desde el código fuente, destinada al entorno de desarrollo.

### 3.1 Instalación en Windows

El destinatario principal del producto es la institución de recursos limitados, cuyo parque informático suele estar compuesto por equipos con Windows. Por ello, la distribución se resolvió con un instalador ejecutable que no exige conocimientos técnicos: el usuario descarga `SistemaGestionPersonal-Setup-<versión>.exe` y lo ejecuta. Los datos de la aplicación —base de datos, documentos y respaldos— se almacenan en `%LOCALAPPDATA%\SistemaGestionPersonal`, separados de la instalación, de modo que una actualización del programa no pone en riesgo la información acumulada. Esta decisión práctica resulta decisiva para la sostenibilidad: la institución puede actualizar la herramienta sin temor a perder su historia administrativa.

### 3.2 Versión portable para Linux

La misma aplicación se empaqueta en un archivo comprimido para Linux, que funciona en Debian 13 y Ubuntu 24.04 LTS o superior. El binario se autoverifica bajo un servidor gráfico virtual dentro de contenedores de integración antes de publicarse, y se comprueba que la versión máxima de la biblioteca C requerida no exceda la soportada por esas distribuciones. Los datos se guardan junto al ejecutable. Esta modalidad atiende a instituciones con equipos de escritorio basados en sistemas abiertos, escenario frecuente en el ámbito educativo público.

### 3.3 Ejecución desde el código fuente

Para el entorno de desarrollo y para la institución que desee auditar el software, el sistema se ejecuta desde el código fuente con el intérprete de Python 3.15 o superior y las dependencias declaradas en `requirements.txt`. Este procedimiento es el que emplea la propia verificación técnica y el que permite reproducir la suite de pruebas.

### 3.4 Construcción y empaquetado

La construcción del ejecutable y del instalador se realiza con el script `build.py`, que ofrece modos específicos —solo ejecutable, solo actualizador, o el ciclo completo— y lee la versión desde el archivo `VERSION` como fuente única. El empaquetado emplea PyInstaller para el ejecutable y el actualizador, e Inno Setup para el instalador de Windows. Los artefactos resultantes son el ejecutable en `dist/`, el actualizador en `dist_updater/` y el instalador en `dist_installer/`.

### 3.5 Integración y entrega continua

La verificación y el empaquetado se automatizan con dos flujos de integración continua. El primero, de integración y empaquetado, ejecuta la suite completa de pruebas en cada cambio sobre las ramas principales y compila las versiones de Windows y Linux, verificando el arranque del binario empaquetado; no publica releases, solo compila y verifica. El segundo, de publicación, se activa con la creación de una etiqueta de versión, aplica firma digital a todo el contenido distribuible en dos pasadas, audita que ningún archivo firmable quede sin firma y publica la versión con un único adjunto: el instalador.

La consecuencia práctica de este esquema es que ningún cambio llega a la institución sin haber pasado por la suite de pruebas y sin estar firmado. La firma digital del instalador y de los binarios es, además, un control de seguridad que protege a la institución frente a la distribución de software alterado.

---

## 4. Actualización automática

Un sistema instalado en una institución con recursos técnicos limitados no puede depender de que alguien recuerde actualizarlo. Por esa razón el proyecto incorpora un actualizador automático, empaquetado como ejecutable independiente e integrado en el instalador.

El actualizador consulta la última versión publicada, la compara con la instalada y, si existe una versión nueva, cierra la aplicación si está abierta, descarga el instalador con reintentos y verificación de tamaño, y lo ejecuta en modo silencioso. El proceso se programa para comprobar novedades cada dos días mediante el Programador de tareas de Windows, y se acompaña de una ventana de estado que muestra el progreso —comprobación, descarga con porcentaje, instalación y resultado— y de un ícono en la bandeja del sistema con menú contextual.

El actualizador constituye, en términos prácticos, un mecanismo de mantenimiento delegado: la institución no necesita un responsable técnico para conservar el software al día, y el instalador y el desinstalador se encargan de registrar y retirar la tarea programada sin intervención manual.

---

## 5. Sincronización entre puestos

### 5.1 Problema práctico que resuelve

En las instituciones observadas, la gestión de personal no la realiza una sola persona en un solo equipo: suele distribuirse entre varios puestos —secretaría, recursos humanos, dirección— que necesitan compartir la misma información. La solución de un servidor central con acceso remoto habría exigido infraestructura y conectividad que esas instituciones no garantizan. El proyecto resolvió el problema con un agente de sincronización que replica los datos entre los puestos de la red local a través de un nodo central, sin exigir servidores dedicados ni conexión permanente.

### 5.2 Garantías de diseño

El agente opera bajo seis garantías que lo hacen apto para el contexto. La escritura es siempre local: la aplicación nunca espera a la red, escribe en su base de datos y encola la operación con su marca temporal, de modo que el sistema funcione aunque la red esté caída. La captura es transaccional: la operación se registra en la misma transacción que el dato, con lo que una transacción deshecha no anuncia nada al resto de la red. La identidad es global: cada registro recibe un identificador único y se unifica por su clave natural, de manera que un registro creado en dos puestos es uno solo. La mezcla es por campo, con un orden total y determinista que garantiza la convergencia con independencia del orden de llegada de las operaciones, y que conserva ambas ediciones cuando dos puestos modifican columnas distintas. El nodo central es el único escritor autoritativo, con servicio HTTP sobre base de datos en modo de registro anticipado, autenticación por token y límite de peticiones. Y los archivos binarios viajan como resumen criptográfico y tamaño, con transferencia del contenido solo cuando no excede el límite configurado y con deduplicación en el nodo central.

### 5.3 Operación

El agente se administra con comandos simples de línea de órdenes: preparación del equipo, ejecución del agente en segundo plano, consulta de estado, listado de conflictos y operación del nodo central. La aplicación inicia el agente al arrancar y lo detiene antes de liberar las conexiones a la base de datos; la barra de estado muestra el indicador correspondiente y ofrece la acción de sincronizar de inmediato, mientras la pestaña de sincronización de la configuración concentra los parámetros por equipo, la prueba de conexión, los contadores y la bandeja de conflictos.

Desde la perspectiva práctica, esta funcionalidad convierte una limitación del contexto —la ausencia de infraestructura de red— en un problema resuelto por software de escritorio.

---

## 6. Operación y mantenimiento en la institución

### 6.1 Tareas de mantenimiento rutinario

El sostenimiento del sistema en operación comprende cinco tareas periódicas: la verificación de los respaldos automáticos y de su integridad; la depuración de documentos obsoletos conforme a la política de retención; la revisión de los registros de auditoría para detectar operaciones anómalas; la actualización de los parámetros institucionales cuando cambien las condiciones normativas o internas; y el mantenimiento de la base de datos, que el sistema realiza de forma automática al iniciar. Estas tareas no requieren conocimiento de programación, y su ejecución está descrita en la documentación técnica y en la guía de usuario que acompañan al producto.

### 6.2 Solución de problemas frecuentes

La documentación del sistema prevé las incidencias más comunes de la operación y su tratamiento: dificultad de arranque por dependencias o versión del intérprete, error de apertura de la base de datos con su procedimiento de restauración del respaldo más reciente, falta de respuesta de la interfaz y su relación con los recursos del equipo, restablecimiento de contraseña por el administrador, rechazo de un documento por extensión o tamaño y ausencia de avisos de vencimiento por configuración incorrecta del umbral. La previsión de estas situaciones forma parte del marco práctico: un sistema que se adopta en una institución sin área técnica debe traer resuelta la primera línea de soporte.

### 6.3 Requisitos de operación

Los requisitos prácticos de operación son deliberadamente modestos: Windows 10 o superior, o bien Linux Debian 13 / Ubuntu 24.04 LTS o superior; Python 3.15 o superior cuando se ejecute desde el código fuente; cuatro gigabytes de memoria recomendada y quinientos megabytes de espacio en disco. La aplicación funciona sin conexión a internet, salvo el actualizador automático, que la consulta de forma opcional. Esta austeridad de requisitos responde directamente a la barrera de infraestructura documentada en el diagnóstico y es condición de viabilidad en el contexto de aplicación.

---

## 7. Aplicación piloto: procedimiento práctico

### 7.1 Alcance y participantes

La aplicación piloto se realizará en un conjunto de entre tres y cinco instituciones educativas seleccionadas por muestreo intencional, con diversidad de tamaño, nivel educativo y ámbito, y con la participación de entre diez y quince usuarios por institución. El procedimiento práctico comprende la instalación en los equipos de cada institución, la migración de sus datos, la configuración particular de sus parámetros, la capacitación segmentada por perfil, el período de uso acompañado y la evaluación de cierre.

### 7.2 Instrumentos aplicables

El piloto emplea cuatro instrumentos ya definidos y reproducidos en los anexos. La guía de entrevista para el análisis de requerimientos, con veintidós preguntas organizadas en seis bloques. El cuestionario de satisfacción, con veinte afirmaciones cerradas en escala de uno a cinco y tres preguntas abiertas, aplicable antes y después de la implementación para medir la variación de la percepción. El protocolo de pruebas de usabilidad, con seis tareas representativas —registrar un empleado, localizarlo por su cédula, generar la nómina de un periodo, emitir un recibo de pago, cargar un documento con fecha de vencimiento y registrar y aprobar una incidencia— evaluadas mediante tiempo de ejecución, tasa de éxito, número y naturaleza de los errores y comentarios del participante. Y los formatos de documentación de pruebas, que registran para cada caso la funcionalidad verificada, los datos de entrada, el resultado esperado, el resultado obtenido y su estado.

### 7.3 Mediciones previstas

La aplicación piloto producirá cuatro tipos de medición práctica: los tiempos de procesamiento antes y después de la implementación, registrados por observación directa; las tasas de error antes y después, reconstruidas a partir del registro institucional de correcciones; los indicadores de satisfacción del personal por dimensión; y las métricas técnicas de rendimiento y de comportamiento bajo volumen creciente de datos. El contraste estadístico de estas mediciones se practicará con las pruebas definidas en la metodología, con un nivel de significancia de 0,05, distinguiendo de manera explícita entre significancia estadística y relevancia práctica.

### 7.4 Previsiones de contingencia aplicables al piloto

El plan de contingencia previsto contempla cuatro frentes que se aplican durante el piloto: la continuidad del procedimiento anterior como respaldo durante los primeros meses de operación; la designación de usuarios referentes por institución para resolver dudas de primer nivel; la priorización de las funcionalidades esenciales si surgiera una restricción de tiempo; y la comunicación anticipada de cualquier modificación del cronograma. Estas previsiones no son hipotéticas: responden a los riesgos identificados en el compendio del proyecto sociotecnológico y a la experiencia documentada sobre adopción tecnológica.

---

## 8. Conclusión

El marco práctico del proyecto se sostiene sobre cuatro capacidades verificables. El sistema cubre el ciclo administrativo completo de la gestión de personal y nómina y produce los documentos oficiales que la institución requiere. Se distribuye en condiciones que no exigen infraestructura ni conocimiento técnico especializado, con instalación asistida, versión portable y actualización automática. Resuelve una limitación concreta del contexto —la gestión distribuida entre puestos sin red garantizada— mediante un agente de sincronización con garantías de convergencia. Y trae resuelta su primera línea de soporte mediante la documentación de operación y mantenimiento.

Lo que resta es la ejecución de la aplicación piloto, cuyo procedimiento práctico está íntegramente definido en el apartado 7. La distancia entre el estado actual y la evidencia empírica no es de diseño ni de preparación, sino de aplicación en campo; esa distinción es la que permite afirmar que el proyecto está listo para su validación final.

---

## 9. Guía operativa resumida por módulo

Este apartado reúne el procedimiento operativo de cada módulo en pasos concretos, con el fin de que la institución disponga de una guía de referencia rápida que complemente la guía de usuario completa.

### 9.1 Empleados

1. Abrir el módulo con `Ctrl+2` o desde el menú lateral.
2. Pulsar «Nuevo Empleado» (`Ctrl+N`).
3. Completar los datos personales, laborales y de contacto; cargar la fotografía si se dispone de ella.
4. Guardar. El sistema verifica la unicidad de la cédula antes de persistir.
5. Para consultar, usar el buscador (`Ctrl+F`) o el filtro por tipo y departamento.
6. Para emitir la ficha, seleccionar el empleado y generar el documento.

### 9.2 Documentos

1. Con un empleado seleccionado, abrir el módulo de documentos.
2. Cargar el archivo admitido (documento o imagen) e indicar tipo, fecha de emisión y, cuando corresponda, fecha de vencimiento.
3. Guardar. El sistema clasifica el documento y calcula su estado de vigencia.
4. Consultar el reporte de vencimientos para conocer los documentos vencidos y próximos a vencer.

### 9.3 Incidencias

1. Registrar la solicitud con su tipo, fechas y motivo, y adjuntar el soporte.
2. El sistema computa los días de la incidencia.
3. Recorrer el flujo de aprobación; la decisión queda registrada con el responsable y su comentario.
4. Las incidencias aprobadas se consideran en el cálculo de la nómina del periodo.

### 9.4 Contratos

1. Registrar el contrato con su tipo y vigencia; el sistema asigna la numeración y controla la unicidad del contrato vigente por empleado.
2. Para renovar, usar la renovación encadenada al contrato anterior.
3. Para terminar, proceder a la terminación con el finiquito correspondiente.
4. Consultar el reporte de contratos por vencer y vencidos.

### 9.5 Nómina

1. Abrir el módulo (`Ctrl+6`) y seleccionar el periodo.
2. Ejecutar el cálculo; el sistema considera las incidencias aprobadas y aplica las reglas del dominio.
3. Revisar los pagos generados y corregir lo que corresponda antes de confirmar.
4. Emitir el recibo individual y la planilla consolidada.
5. Registrar los pagos efectivamente entregados.

### 9.6 Configuración

1. Completar los datos institucionales.
2. Ajustar los parámetros de nómina —porcentajes, topes, tarifas— y las políticas de recursos humanos.
3. Gestionar usuarios y roles; consultar el visor de auditoría.
4. Configurar la apariencia, la contraseña propia y las operaciones de respaldo y restauración.

### 9.7 Estudiantes y calificaciones

1. Registrar el estudiante y asignarlo a un grado y periodo mediante la matrícula.
2. Registrar las calificaciones por materia y periodo; la escritura requiere autorización por token del docente asignado o del administrador.
3. Generar el consolidado del periodo y el boletín por estudiante.
4. Cerrar el periodo para bloquear las notas; la reapertura queda restringida al administrador.

---

**El Autor**
[Nombre del Estudiante]

**Institución**
[Nombre de la Institución]
