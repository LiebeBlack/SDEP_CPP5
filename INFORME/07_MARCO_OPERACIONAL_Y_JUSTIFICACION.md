# MARCO OPERACIONAL Y JUSTIFICACIÓN E IMPORTANCIA

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 07 del expediente del informe del estado de la investigación.

---

## 1. Introducción

Este documento reúne dos componentes que la estructura clásica del proyecto sociotecnológico mantiene separados pero que guardan una relación estrecha: el marco operacional y la justificación e importancia del proyecto. El primero describe cómo se organiza la operación del sistema —los recursos que requiere, los procesos que sostiene y las responsabilidades que distribuye—. La segunda expone por qué vale la pena sostenerlo: su repercusión social, técnica y económica, y las razones que justifican la inversión de esfuerzo y recursos que el proyecto supuso.

La relación entre ambos componentes es directa. Una justificación que no pueda traducirse en una operación viable es un ideal; una operación que no responda a una necesidad justificada es un gasto. El documento se propone mostrar que el proyecto satisface ambas condiciones: tiene una razón de ser documentada y dispone de las condiciones operativas para sostenerse.

---

## 2. Marco operacional

### 2.1 Definición y alcance

El marco operacional comprende el conjunto de condiciones, recursos y procedimientos mediante los cuales el sistema se pone en funcionamiento y se mantiene en operación en una institución educativa. Comprende cuatro dimensiones: los recursos humanos y técnicos, los procesos de operación, la distribución de responsabilidades y las condiciones de sostenibilidad.

### 2.2 Recursos humanos y técnicos

La operación del sistema no exige la creación de un área de tecnología. Requiere, en cambio, la designación de un responsable con las siguientes funciones: administrar las cuentas y los roles de usuario, mantener actualizados los parámetros institucionales, verificar la ejecución de los respaldos y atender la primera línea de soporte con apoyo de la documentación entregada. Esa figura, prevista en las recomendaciones del Capítulo V, es lo que permite que el sistema se sostenga sin depender del autor original.

En el orden técnico, los recursos requeridos son los ya señalados: un equipo con Windows 10 o superior, o Linux en las versiones soportadas; cuatro gigabytes de memoria recomendada; y quinientos megabytes de espacio en disco. La aplicación funciona sin conexión a internet, salvo el actualizador automático. Cuando la institución gestiona el sistema desde varios puestos, el agente de sincronización permite replicar los datos en la red local sin exigir un servidor dedicado.

### 2.3 Procesos de operación

La operación del sistema se organiza en los procesos que se describen a continuación. Cada proceso tiene un disparador, un responsable y un resultado verificable.

| Proceso | Disparador | Responsable | Resultado |
|---------|-----------|-------------|-----------|
| Configuración institucional | Puesta en marcha o cambio normativo | Administrador | Parámetros de nómina y datos institucionales vigentes |
| Registro y actualización de personal | Incorporación o cambio de datos | Gestor de personal | Legajo del empleado actualizado |
| Carga y control documental | Ingreso de un documento | Gestor de personal | Documento registrado con su vigencia |
| Registro y aprobación de incidencias | Solicitud del empleado | Gestor y responsable de aprobación | Incidencia con estado y responsable de la decisión |
| Gestión de contratos | Alta, renovación o terminación | Gestor de personal | Contrato vigente y control de vencimientos |
| Procesamiento de nómina | Cierre del periodo | Gestor de personal | Pagos calculados, recibos y planilla emitidos |
| Respaldo y verificación | Programación automática | Administrador | Copia íntegra con política de retención |
| Revisión de auditoría | Verificación periódica | Administrador | Registro de operaciones sensibles |

### 2.4 Distribución de responsabilidades por rol

La operación se organiza en cuatro roles, cuya delimitación es una condición de seguridad y de orden administrativo.

| Rol | Alcance operativo |
|-----|-------------------|
| Administrador | Acceso a todos los módulos, configuración institucional, gestión de usuarios, respaldos y visor de auditoría |
| Gestor | Empleados, documentos, incidencias, contratos, nómina y reportes |
| Usuario | Empleados, documentos e incidencias, con actualización de registros propios |
| Solo lectura | Consulta de empleados, documentos y reportes |

Esta distribución traslada al sistema el principio de separación de funciones que la Administración Pública requiere: quien procesa la nómina no es necesariamente quien administra las cuentas, y quien consulta no puede modificar. En términos operativos, la matriz de roles reduce el riesgo de error y de uso indebido sin exigir controles manuales adicionales.

### 2.5 Condiciones de sostenibilidad operativa

La sostenibilidad de la operación descansa en cuatro condiciones que el proyecto procuró explícitamente. La primera es la independencia del licenciamiento: todas las tecnologías empleadas son de código abierto, de modo que no existe un costo recurrente que pueda interrumpir la operación. La segunda es la documentación: la guía de usuario, la documentación técnica y las notas de desarrollo permiten resolver el uso cotidiano y las incidencias de primer nivel sin asistencia externa. La tercera es la actualización automática: el sistema se mantiene al día sin requerir un responsable técnico dedicado. La cuarta es la separación de los datos respecto de la instalación: la información reside en el directorio de datos del usuario, lo que protege el acervo administrativo frente a reinstalaciones.

---

## 3. Justificación de la investigación

### 3.1 Justificación teórica

La investigación aporta al campo de los sistemas de información educativa un caso documentado de aplicación de metodologías de ingeniería de software en un contexto de recursos limitados. Contribuye con conocimiento sobre tres cuestiones que rara vez se abordan de forma conjunta: las decisiones de diseño que hacen viable un sistema de gestión en instituciones sin área de tecnología propia; el efecto de aislar el dominio de cálculo financiero respecto de la interfaz y del acceso a datos; y la relación entre las condiciones organizacionales de la institución y la adopción efectiva de la herramienta.

La contribución teórica no reside únicamente en el producto, sino en el registro del proceso completo —del análisis de requerimientos a la validación técnica—, que permite examinar las decisiones adoptadas y sus consecuencias. Un caso documentado con sus aciertos y sus correcciones tiene valor para la investigación aplicada precisamente porque no oculta las tensiones del trabajo real.

### 3.2 Justificación práctica

El resultado tangible de la investigación es un sistema operativo que responde a los problemas diagnosticados. Centraliza la información del personal en una fuente única, calcula la remuneración mediante reglas explícitas y verificables, controla la vigencia de la documentación, formaliza el flujo de aprobación de las incidencias y produce los documentos oficiales que la institución debe emitir.

La utilidad práctica se sostiene sobre tres hechos verificables: el sistema existe y funciona; los procesos que automatiza son los que el diagnóstico identificó como críticos; y la aplicación piloto permitirá comprobar en condiciones reales su efecto sobre los tiempos de procesamiento y las tasas de error. La justificación práctica no se limita a la existencia del software, sino a su capacidad de sustituir un procedimiento manual por uno verificable.

### 3.3 Justificación metodológica

La investigación articula el desarrollo iterativo de software con la investigación-acción, combinación apropiada cuando el objeto de estudio es a la vez una herramienta y el contexto en que se utiliza. El aporte metodológico consiste en un procedimiento replicable —con fases, instrumentos y criterios de evaluación definidos— y en un conjunto de instrumentos validados que pueden adaptarse a proyectos similares.

La decisión de explicitar el estatuto de la evidencia en cada etapa, distinguiendo lo verificado sobre el producto de lo medido en campo, forma parte de ese aporte y responde a las exigencias de rigor del trabajo de grado. Esa disciplina metodológica es, en sí misma, un resultado transferible: enseña a separar lo que se sabe de lo que se espera.

### 3.4 Justificación social

El proyecto produce efectos sociales en tres planos. En el plano del personal de las instituciones, garantiza la oportunidad y la exactitud de la remuneración, reduce la incertidumbre sobre la propia información y disminuye la conflictividad asociada a los errores administrativos. En el plano de la comunidad educativa, libera tiempo administrativo que puede orientarse a tareas de apoyo académico. En el plano del sector, reduce la brecha tecnológica entre instituciones con distinta capacidad financiera, dado que la solución no exige inversión en licenciamiento y puede replicarse sin costo de adquisición.

La dimensión social del proyecto no es un añadido retórico. Trata sobre la remuneración de personas que prestan un servicio público y sobre la capacidad de la institución de cumplir con sus trabajadores y trabajadoras. Cuando la remuneración llega a destiempo o con errores, el efecto recae sobre la vida cotidiana de quienes trabajan y, en última instancia, sobre la continuidad y la calidad del servicio educativo.

### 3.5 Justificación económica

La justificación económica se sostiene sobre tres componentes verificables. El primero es el costo de adquisición nulo, en tanto todas las tecnologías empleadas son de código abierto. El segundo es el costo de operación, limitado al mantenimiento interno y a las actualizaciones de dependencias. El tercero es el ahorro derivado de evitar reprocesos y correcciones, cuyo orden de magnitud se estimará con las mediciones del piloto y que, aun en su estimación más conservadora, debe contrastarse con el costo de licenciamiento de las soluciones comerciales equivalentes.

El apartado 5 de este documento presenta el desglose del presupuesto ejecutado y de los costos anuales estimados de operación, que son la base cuantitativa de esta justificación.

### 3.6 Justificación académica y tecnológica

En el orden académico, el proyecto representa una oportunidad de aplicar conocimientos de ingeniería de software en un contexto real, de desarrollar competencias en el diseño de aplicaciones de gestión y de generar conocimiento aplicado en un área con literatura limitada. En el orden tecnológico, emplea componentes maduros, documentados y abiertos —lenguaje de programación, capa de mapeo objeto-relacional, biblioteca de interfaz, generador de documentos y biblioteca de hojas de cálculo—, condición que la literatura identifica como favorable para las instituciones con recursos limitados cuando existe documentación suficiente y una capacidad técnica mínima.

---

## 4. Importancia y repercusión del proyecto

### 4.1 Repercusión social

La repercusión social del proyecto se manifiesta en cinco frentes. Mejora las condiciones laborales al garantizar pagos oportunos y correctos. Fortalece la transparencia administrativa al permitir auditar los procesos y reconstruir las decisiones. Reduce la carga administrativa que consume tiempo susceptible de destinarse a la actividad académica. Democratiza el acceso a herramientas modernas de gestión en instituciones con recursos limitados. Y contribuye a la continuidad de un registro histórico ordenado de la vida laboral del personal, condición para el ejercicio de sus derechos.

### 4.2 Repercusión técnica

La repercusión técnica se verifica en el propio producto. El proyecto deja un sistema funcional, organizado en capas, con dominio de cálculo aislado y probado, con control de acceso por rol, auditoría, respaldos y generación documental; y deja, además, un conjunto de criterios de diseño y de verificación reutilizables en proyectos similares. La validación práctica de una arquitectura de capas con los patrones Repository y Service, complementada por un dominio de cálculo aislado, constituye una contribución técnica transferible con independencia del sistema que la materializa.

A ello se añaden dos capacidades que responden a restricciones reales del contexto: el agente de sincronización entre puestos, que resuelve la gestión distribuida sin red garantizada, y la distribución portátil para Windows y Linux, que amplía el universo de instituciones en que el sistema puede operar.

### 4.3 Repercusión económica

La repercusión económica se apoya en dos hechos cuantificables. Por un lado, la eliminación del costo de licenciamiento: al construirse íntegramente con componentes abiertos, el sistema no genera una erogación recurrente por el derecho de uso, que es precisamente el rubro que vuelve prohibitivas las soluciones comerciales para las instituciones de recursos limitados. Por otro, la reducción del costo operativo derivado de los reprocesos y de las correcciones, que se traduce en horas administrativas que dejan de destinarse a la enmienda de errores.

La comparación con las soluciones comerciales se consigna en el análisis comparativo del Capítulo IV, cuya magnitud debe confirmarse mediante cotización específica, dado que los precios de las suites comerciales de gestión varían según el número de usuarios y las condiciones contractuales. Esa cautela metodológica no debilita la conclusión: aun con la horquilla más conservadora, el costo de licenciamiento comercial supera en órdenes de magnitud el costo de operación anual del sistema desarrollado.

---

## 5. Viabilidad y sostenibilidad

### 5.1 Viabilidad

El proyecto resultó viable en sus cuatro dimensiones. La viabilidad técnica se apoya en tecnologías maduras, documentadas, sin licenciamiento y multiplataforma. La viabilidad operativa se sostiene en el acuerdo con las instituciones participantes, en la existencia de instrumentos de recolección definidos y en la disponibilidad de una guía de usuario y de material de capacitación. La viabilidad económica se deriva de la ejecución con recursos propios y de la ausencia de costos de licenciamiento. La viabilidad temporal se apoya en un cronograma de ocho meses organizado en cuatro fases, cuya ejecución se completó en el componente técnico conforme a lo previsto.

### 5.2 Presupuesto ejecutado

El proyecto se ejecutó con recursos propios del investigador, sin financiamiento externo. El desglose del costo incurrido es el siguiente.

| Concepto | Costo | Fuente de financiamiento |
|----------|-------|--------------------------|
| Tiempo del investigador | $0 | Recursos propios, no remunerados |
| Equipo de desarrollo | $0 | Equipo preexistente |
| Licencias de software | $0 | Componentes de código abierto |
| Material de oficina | $50 | Recursos propios |
| Impresión de documentación | $30 | Recursos propios |
| Transporte para visitas a instituciones | $500 | Recursos propios |
| **Total del desarrollo** | **$580** | |

### 5.3 Costos de operación estimados

El costo anual estimado de operación por institución permite apreciar la carga económica que el sistema impone una vez implantado.

| Concepto | Costo anual | Fundamento |
|----------|-------------|------------|
| Licenciamiento de software | $0 | Todas las tecnologías empleadas son de código abierto |
| Servidor dedicado | $0 | Aplicación de instalación local, sin servidor |
| Actualizaciones de seguridad | $50 | Revisión periódica de dependencias |
| Soporte técnico externo | $0 | Soporte comunitario y documentación propia |
| Capacitación de nuevos usuarios | $200 | Sesiones de inducción y actualización |
| **Total anual estimado** | **$250** | |

### 5.4 Sostenibilidad

La sostenibilidad técnica descansa en la arquitectura modular, en la documentación completa y en la suite de pruebas, tres condiciones que permiten mantener y ampliar el sistema sin depender de su autor original. La sostenibilidad económica deriva del uso exclusivo de tecnologías de código abierto, sin licenciamiento recurrente ni dependencia de proveedores. La sostenibilidad social se apoya en la capacitación y en la documentación de usuario, que habilitan la autonomía del personal de la institución, y en la figura del usuario referente interno. La sostenibilidad académica se sustenta en la posibilidad de que el sistema y la investigación sirvan de base a proyectos posteriores.

---

## 6. Conclusión

El marco operacional demuestra que el sistema puede sostenerse en operación con recursos modestos y sin área técnica dedicada: requiere un responsable designado, infraestructura mínima y el apoyo de la documentación entregada. La justificación demuestra que el proyecto responde a una necesidad documentada en sus dimensiones teórica, práctica, metodológica, social, económica, académica y tecnológica. La repercusión social, técnica y económica del proyecto es verificable en el producto y cuantificable en el presupuesto.

La articulación entre ambas partes es el mensaje central de este documento: el proyecto no solo está justificado, sino que dispone de las condiciones para sostener en el tiempo aquello que justifica. Un sistema que resuelve un problema real y que puede mantenerse con recursos mínimos satisface, simultáneamente, la exigencia de pertinencia y la de viabilidad.

---

## 7. Análisis costo–beneficio ampliado

### 7.1 Estructura del análisis

El análisis costo–beneficio del proyecto se organiza en tres horizontes: el costo de construcción, ya incurrido; el costo anual de operación, estimado; y el beneficio, cuya cuantificación depende de las mediciones del piloto. La estructura se presenta de modo que cada magnitud declare su origen y su grado de certeza.

| Componente | Magnitud | Naturaleza | Estado |
|------------|----------|------------|--------|
| Costo de construcción | $580 | Incurrida | Verificada |
| Costo anual de operación por institución | $250 estimados | Proyectada | Estimada |
| Costo de licenciamiento | $0 | Verificada | Ausente por diseño |
| Beneficio por ahorro de tiempo | Por medir en el piloto | Proyectada | Pendiente |
| Beneficio por reducción de errores | Por medir en el piloto | Proyectada | Pendiente |
| Beneficio por eliminación de licenciamiento | Diferencial frente a suites comerciales | Comparativa | Sujeta a cotización |

### 7.2 Comparación con la alternativa comercial

La alternativa a la solución desarrollada es la adquisición de una suite comercial de gestión de personal y nómina. Esa alternativa impone un costo de licenciamiento recurrente que crece con el número de usuarios y que, en el segmento de las instituciones educativas de recursos limitados, resulta habitualmente prohibitivo. Frente a ello, el sistema desarrollado no solo elimina ese costo, sino que preserva la información en formatos abiertos y bajo el control de la institución.

La comparación cuantitativa exacta requiere una cotización específica, que se consigna entre los extremos sujetos a verificación. No obstante, la dirección del resultado no depende de esa precisión: un costo anual de operación de doscientos cincuenta dólares se sitúa, por su orden de magnitud, muy por debajo de cualquier licenciamiento comercial equivalente.

### 7.3 Criterio de decisión

El proyecto se considera económicamente justificado si el costo anual de operación resulta inferior al costo de licenciamiento de la alternativa comercial y si el ahorro derivado de la reducción de errores y reprocesos, una vez medido, resulta positivo. La primera condición es verificable de inmediato; la segunda se resolverá con la evidencia del piloto. La estructura del análisis permite incorporar esa evidencia sin modificar el razonamiento: basta sustituir las magnitudes proyectadas por las efectivamente medidas.

---

**El Autor**
[Nombre del Estudiante]

**Institución**
[Nombre de la Institución]
