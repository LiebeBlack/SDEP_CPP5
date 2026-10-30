# 01. INTRODUCCIÓN Y PLANTEAMIENTO DEL PROBLEMA

**Título de trabajo:** Desarrollo e implementación de un sistema de base de datos local multiusuario con sincronización híbrida y gestión documental para la administración de personal y calificaciones en instituciones educativas.

**Sistema documentado:** SDEP_CPP5, versión 3.0.1.
**Modalidad:** proyecto factible, investigación aplicada.
**Enfoque:** cuantitativo.
**Jurisdicción de referencia:** República Bolivariana de Venezuela.

---

## Nota sobre el estatuto de la evidencia

Este documento distingue tres clases de afirmaciones, y la distinción se mantiene en los tres documentos restantes. Las afirmaciones sobre el producto describen funciones que existen en el repositorio y que pueden comprobarse abriendo el código citado. Las afirmaciones sobre el diagnóstico describen hallazgos obtenidos con los instrumentos que se especifican, y se presentan con el nivel de detalle que permite el registro disponible. Las afirmaciones sobre el comportamiento del sistema en campo se formulan como hipótesis o como resultados pendientes, nunca como mediciones realizadas. Cuando una cifra depende de la aplicación en la institución, se indica con la expresión *pendiente de la Fase IV* y se acompaña del procedimiento que la producirá. Ninguna tabla de este compendio contiene valores inventados.

---

## 1.1 Presentación

La administración de una institución educativa depende de dos conjuntos de información que suelen crecer por caminos separados. El primero reúne los datos del personal: identificación, cargo, salario, documentos, reposos, permisos y contratos. El segundo reúne los datos de los estudiantes: matrícula, representante, calificaciones y boletines. En la práctica, ambos conjuntos se gestionan con instrumentos distintos, en oficinas distintas y con criterios de archivo que no siempre coinciden. Esa separación produce un efecto que la institución percibe a diario: la secretaría conoce al trabajador pero no la nota del niño, y la coordinación académica conoce la nota pero no el expediente del docente que la registró.

El proyecto que se documenta responde a ese problema con una base de datos local multiusuario. Cada equipo de la institución conserva una copia completa de la información en SQLite y sigue operando cuando la red falla; un nodo central recibe y redistribuye los cambios cuando la red está disponible. La sincronización puede ejecutarse de forma automática en segundo plano o de forma manual desde la interfaz, y en ambos casos conserva la consistencia mediante un registro transaccional de operaciones, identificadores UUID y una regla de mezcla que resuelve los conflictos campo por campo. Sobre esa base se construyeron los módulos de personal, nómina, documentos, estudiantes, calificaciones y generación de expedientes y constancias en PDF.

El capítulo presenta el diagnóstico que originó el proyecto, formula el problema y los objetivos, justifica el enfoque cuantitativo, delimita el alcance y establece las hipótesis y variables que se someterán a contraste. Los capítulos posteriores desarrollan el marco teórico y metodológico, el diseño de ingeniería y la implementación con sus pruebas.

## 1.2 Diagnóstico sociotecnológico

### 1.2.1 Contexto y actores

El diagnóstico se realizó en una institución educativa de nivel medio con tres unidades orgánicas vinculadas al objeto de estudio: dirección, secretaría y coordinación académica. La unidad de dirección autoriza procesos y responde ante la autoridad educativa; la secretaría administra el expediente del personal y elabora la nómina; la coordinación académica registra matrículas, calificaciones y boletines. A ellas se suman dos actores cuyo papel condiciona la adopción del sistema: el personal docente, que consulta su propia información y, en el caso de los docentes responsables de grado, registra notas; y el personal de apoyo administrativo, que digitaliza documentos y atiende solicitudes.

La institución no cuenta con un área de tecnología propia. Esa condición, documentada en el diagnóstico, explica por qué cualquier solución debía cumplir tres restricciones no negociables: no depender de internet, no exigir servidores dedicados y no requerir personal especializado para la operación diaria. La restricción de conectividad no es una preferencia de diseño sino una característica del entorno: la red local funciona, pero los enlaces hacia el exterior se interrumpen con frecuencia y la continuidad eléctrica no está garantizada en todos los puestos.

### 1.2.2 Método de investigación acción participativa

El diagnóstico siguió el ciclo de investigación acción participativa (IAP) en cuatro momentos. En el primero, el grupo promotor, integrado por el investigador y representantes de las tres unidades, identificó los procesos que generaban mayor carga operativa. En el segundo, se planificaron las técnicas de recolección y se acordó el calendario de visitas. En el tercero, se ejecutaron la observación, las entrevistas y el grupo focal. En el cuarto, los hallazgos se devolvieron a los participantes para su validación, y esa devolución modificó la prioridad de dos problemas que el investigador había considerado secundarios.

Las técnicas aplicadas fueron cuatro. La observación no participante se realizó en la secretaría y en la coordinación académica, con registro de tiempos por tarea y de los instrumentos utilizados. La entrevista semiestructurada se aplicó a la dirección, a la secretaría y a la coordinación académica, con una guía de veintidós preguntas organizada en seis bloques. El grupo focal reunió a docentes de distintos grados para discutir el registro de calificaciones y la entrega de boletines. El análisis documental revisó los formatos vigentes, las constancias emitidas durante el último año y los registros de incidencias del personal.

La técnica de árbol de problemas se empleó para separar causas de efectos, y la matriz de priorización se empleó para ordenar las intervenciones según frecuencia, impacto y factibilidad. Ambas técnicas se aplicaron en sesión conjunta, con el fin de que la prioridad no fuera una decisión unilateral del investigador.

### 1.2.3 Hallazgos por dimensión

**Registro del personal.** El expediente del trabajador se conserva en físico y se complementa con planillas de cálculo que no siguen un formato común. La secretaría mantiene un archivo por empleado y la dirección mantiene otro con fines de control. Cuando un dato cambia, la actualización se realiza en el archivo que tenga a mano el funcionario de turno, de modo que las dos copias divergen. La búsqueda de un documento concreto exige revisar el archivador y, con frecuencia, consultar a la persona que lo archivó.

**Calificaciones.** El registro de notas se realiza en planillas por materia y por lapso. La consolidación del boletín exige transcribir las notas de cada planilla a un formato único, tarea que se ejecuta al cierre del lapso y que concentra la mayor carga de trabajo del año. La transcripción es también el punto donde se producen los errores que después obligan a corregir el boletín impreso. No existe un control formal que impida que una nota se modifique después de entregado el boletín.

**Documentos y constancias.** Las constancias de trabajo y de estudios se elaboran en procesadores de texto, con modelos que varían según quien las emite. La verificación de la vigencia de los documentos del personal, en particular títulos y certificaciones, se realiza de forma manual y solo cuando alguien recuerda revisarla. La institución no dispone de un registro que permita saber cuántos documentos están vencidos en un momento dado.

**Conectividad y continuidad.** La red local conecta los equipos de secretaría, dirección y coordinación. La conexión a internet se interrumpe con frecuencia y no existe respaldo eléctrico en todos los puestos. Cualquier solución que dependiera de un servicio remoto quedaría inutilizable en esos intervalos, circunstancia que el personal señaló de manera reiterada durante las entrevistas.

**Trabajo concurrente.** Más de una persona necesita consultar y modificar la misma información durante la jornada. La institución resolvió esa concurrencia con acuerdos informales: la secretaría trabaja primero y la coordinación después. El acuerdo funciona mientras el volumen lo permite, pero impide que la información esté disponible en el momento en que se necesita y traslada el costo de la espera al usuario.

### 1.2.4 Árbol de problemas

```text
                    EFECTOS
   Demoras en la atención     Boletines con errores     Documentos vencidos
   y en la emisión de         y reprocesos en el        sin detección
   constancias                cierre del lapso
            \                       |                       /
             \                      |                      /
              +---------------------+---------------------+
                                    |
                    PROBLEMA CENTRAL
   La información administrativa y académica se encuentra
   dispersa en instrumentos aislados, sin una fuente única
   de verdad ni control de concurrencia
                                    |
              +---------------------+---------------------+
             /                      |                      \
            /                       |                       \
   Registro duplicado        Cálculo y consolidación     Ausencia de control
   en archivos físicos       manuales por período        de vigencia y de
   y planillas               (nómina y boletines)        trazabilidad
            \                       |                       /
             \                      |                      /
              +---------------------+---------------------+
                                    |
                                 CAUSAS
   Falta de un sistema       Dependencia de la          Ausencia de
   multiusuario con          red externa y de           registros de
   concurrencia controlada   equipos dedicados          auditoría
```

La lectura del árbol permite advertir que las tres causas comparten un mismo origen: la institución nunca dispuso de un repositorio común. Automatizar una sola de las ramas habría trasladado el problema a las otras dos. Esa observación fue la que orientó la solución hacia una base de datos compartida y no hacia aplicaciones independientes por departamento.

### 1.2.5 Priorización de las intervenciones

La matriz de priorización se construyó con tres criterios y una escala de tres niveles. La frecuencia indica cuántas veces al mes se presenta el problema; el impacto indica el efecto sobre el servicio o sobre la validez de la información; la factibilidad indica la posibilidad de resolverlo con los recursos disponibles. La puntuación total se obtiene de la suma simple, con igual peso para los tres criterios, decisión que el grupo adoptó para evitar discusiones sobre ponderaciones.

| Problema identificado | Frecuencia | Impacto | Factibilidad | Prioridad |
|---|---|---|---|---|
| Registro del personal duplicado y sin fuente única | Alta | Alto | Alta | 1 |
| Consolidación manual de calificaciones y boletines | Alta | Alto | Alta | 2 |
| Emisión heterogénea de constancias y expedientes | Media | Alto | Alta | 3 |
| Falta de control de vigencia documental | Media | Medio | Alta | 4 |
| Registro de incidencias sin trazabilidad | Media | Medio | Media | 5 |
| Ausencia de indicadores para la dirección | Baja | Medio | Media | 6 |

Las cuatro primeras prioridades definen el alcance funcional mínimo del sistema. Las dos últimas se incorporaron como funcionalidades complementarias, porque su implementación resultaba marginal una vez construida la base de datos.

### 1.2.6 Línea base cuantitativa

La línea base se estableció con indicadores que pueden medirse antes y después de la intervención, con el mismo instrumento y en condiciones comparables. Los valores se registran en la ficha de observación técnica del anexo, y su captura corresponde a la Fase I del cronograma. La tabla siguiente define cada indicador y su unidad, de modo que la medición posterior no dependa de interpretaciones.

| Indicador | Definición operacional | Unidad | Instrumento |
|---|---|---|---|
| Tiempo de registro de un trabajador | Desde el inicio del formulario hasta la confirmación del registro | segundos | Ficha de observación técnica |
| Tiempo de búsqueda de un expediente | Desde la solicitud hasta la exhibición del documento | segundos | Ficha de observación técnica |
| Tiempo de consolidación de un boletín | Desde la recepción de las notas hasta la impresión del boletín | minutos | Ficha de observación técnica |
| Tiempo de emisión de una constancia | Desde la solicitud hasta la entrega del documento | minutos | Ficha de observación técnica |
| Tasa de error en la transcripción de notas | Notas corregidas / notas transcritas × 100 | % | Revisión documental |
| Documentos vencidos no advertidos | Documentos vencidos sin alerta / documentos vencidos × 100 | % | Revisión documental |
| Disponibilidad percibida del servicio | Jornadas con interrupción / jornadas observadas × 100 | % | Registro de incidencias |

La línea base no se limita a los tiempos. Incluye también el número de usuarios que comparten la misma información y el número de equipos disponibles, porque ambas variables condicionan la interpretación de las mediciones de concurrencia.

## 1.3 Formulación del problema

### 1.3.1 Problema general

¿De qué manera el desarrollo de un sistema de base de datos local multiusuario con sincronización híbrida y gestión documental en PDF permite optimizar los procesos administrativos de una institución educativa, medido en latencia de red, tasa de éxito de sincronización ante desconexiones, consumo de recursos y usabilidad?

### 1.3.2 Problemas específicos

1. ¿Qué requerimientos técnicos y operativos presenta la institución para sostener una base de datos compartida en su red local, y cómo se jerarquizan según su criticidad?
2. ¿Qué arquitectura de red y qué modelo de datos relacional permiten que varios puestos trabajen sobre la misma información sin depender de un servidor dedicado ni de conexión a internet?
3. ¿Cómo debe implementarse la sincronización para que los cambios registrados durante una desconexión se integren sin pérdida de datos ni duplicación cuando se restablece el enlace?
4. ¿Qué latencia, qué caudal de operaciones y qué tasa de éxito de sincronización alcanza el sistema en las condiciones de la red local de la institución?
5. ¿Qué nivel de usabilidad obtiene el sistema entre el personal administrativo y docente, medido con la escala SUS?

### 1.3.3 Justificación de la formulación

Los problemas específicos se ordenan siguiendo la secuencia de las fases metodológicas y no la de los capítulos. El primero corresponde al diagnóstico, el segundo al diseño, el tercero a la construcción y el cuarto y el quinto a la evaluación. Esa correspondencia permite que cada objetivo específico tenga un problema del que se deriva y un resultado que lo responde, condición que la matriz de trazabilidad del documento 03 verifica.

## 1.4 Objetivos de la investigación

### 1.4.1 Objetivo general

Desarrollar un sistema de base de datos local multiusuario con sincronización híbrida y gestión documental en PDF para optimizar los procesos administrativos de una institución educativa.

El objetivo general integra cuatro resultados en un solo producto: una base de datos compartida, un mecanismo de sincronización tolerante a desconexiones, un módulo de documentos institucionales y una interfaz operativa para el personal. La optimización se entiende en sentido operacional, no retórico: reducción de tiempos de proceso, disminución de errores de transcripción, eliminación de la doble captura y disponibilidad de la información durante toda la jornada.

### 1.4.2 Objetivos específicos y taxonomía de Bloom

La formulación de los objetivos específicos respeta la secuencia lógica del proyecto y, al mismo tiempo, declara el nivel cognitivo que exige cada uno. Se empleó la taxonomía revisada de Bloom (Anderson y Krathwohl, 2001), cuya dimensión de proceso distingue recordar, comprender, aplicar, analizar, evaluar y crear. La tabla siguiente relaciona cada objetivo con el verbo, el proceso cognitivo, el tipo de conocimiento movilizado y la evidencia que permite verificarlo.

| N.º | Objetivo específico | Verbo | Proceso Bloom | Conocimiento | Evidencia de logro |
|---|---|---|---|---|---|
| OE1 | Diagnosticar los requerimientos técnicos y operativos de la institución mediante levantamiento de información. | Diagnosticar | Analizar (4) | Conceptual y procedimental | Informe de diagnóstico con requerimientos jerarquizados y línea base |
| OE2 | Diseñar la arquitectura de red local cliente-servidor y el modelo de datos relacional. | Diseñar | Crear (6), subproceso planificar | Procedimental | Documento de arquitectura, modelo entidad-relación y diccionario de datos |
| OE3 | Construir el software informático integrando el módulo de sincronización offline-first y la generación de PDF. | Construir | Crear (6), subprocesos generar y producir | Procedimental | Producto ejecutable, módulos funcionales y suite de pruebas |
| OE4 | Evaluar el rendimiento, la latencia de red, la tasa de éxito de sincronización y la usabilidad mediante métricas cuantitativas. | Evaluar | Evaluar (5) | Metacognitivo | Tablas de resultados, contraste de hipótesis y puntuación SUS |

La progresión cognitiva requiere una aclaración, porque el orden de los objetivos no coincide con el orden numérico de la taxonomía. El OE1 exige analizar una realidad desagregándola en componentes, lo que corresponde al nivel 4. El OE2 y el OE3 pertenecen ambos al nivel 6, pues diseñar y construir son dos subprocesos de la creación: el primero planifica la solución y el segundo la produce. La diferencia entre ellos no es de nivel sino de exigencia procedimental, ya que el OE3 obliga a coordinar decisiones de concurrencia, persistencia y sincronización que el diseño solo anticipa. El OE4 desciende al nivel 5 porque evaluar implica emitir un juicio con criterios explícitos sobre el artefacto ya construido. Esa secuencia, analizar para comprender, crear para resolver y evaluar para juzgar, es la que corresponde a un proyecto factible y no a una escala de dificultad creciente en sentido estricto.

### 1.4.3 Contraste con criterios SMART

| Objetivo | Específico | Medible | Alcanzable | Relevante | Temporal |
|---|---|---|---|---|---|
| OE1 | Se limita a requerimientos técnicos y operativos de una institución | Queda medido por el número de requerimientos validados y por la línea base | Depende de acceso a la institución, ya acordado | Condiciona el diseño | Fase I, semanas 1 a 6 |
| OE2 | Se limita a arquitectura de red y modelo de datos | Se verifica con el modelo y el diccionario aprobados | Usa tecnologías disponibles y documentadas | Determina la viabilidad técnica | Fase II, semanas 7 a 12 |
| OE3 | Se limita a sincronización y PDF, además de los módulos que los soportan | Se verifica con pruebas automatizadas y con el producto instalado | El equipo y el tiempo disponible lo permiten | Es el núcleo del proyecto | Fase III, semanas 13 a 26 |
| OE4 | Se limita a rendimiento, latencia, éxito de sincronización y usabilidad | Se verifica con instrumentos numéricos y pruebas estadísticas | Requiere usuarios y equipos, ambos disponibles | Permite concluir sobre el objetivo general | Fase IV, semanas 27 a 34 |

La delimitación temporal se apoya en un cronograma de treinta y cuatro semanas, que se detalla en el documento 02. La revisión de los objetivos con los criterios SMART obligó a eliminar dos formulaciones iniciales que no podían medirse: «mejorar la calidad del servicio» y «facilitar el trabajo del personal». Ninguna de las dos admitía un indicador verificable, y ambas se sustituyeron por las variables que se definen en el apartado 1.6.

## 1.5 Justificación

### 1.5.1 Justificación teórica

El proyecto aporta un caso documentado de replicación de datos en una red local sin servidor de base de datos dedicado. La literatura sobre sistemas local-first describe los principios generales de la propiedad del dato y la colaboración sin conexión (Kleppmann et al., 2019), pero son escasos los reportes que muestran cómo se aplican esos principios en una institución educativa con equipos heterogéneos, conectividad intermitente y personal sin formación técnica. El proyecto documenta esa aplicación y expone las decisiones que resultaron viables y las que no.

El aporte se concentra en tres cuestiones. La primera es la captura transaccional de cambios: el registro de la operación se escribe en la misma transacción que el dato, de modo que no puede existir una edición sin su operación de sincronización ni una operación que anuncie un cambio no confirmado. La segunda es la resolución de conflictos por campo, que permite conservar dos ediciones simultáneas sobre columnas distintas de la misma fila. La tercera es la separación entre el motor de mezcla, escrito como funciones puras, y el transporte HTTP, que permite probar la convergencia sin levantar la red.

### 1.5.2 Justificación práctica

El sistema resuelve los cuatro problemas priorizados en el diagnóstico. Centraliza el expediente del trabajador y la ficha del estudiante en una base única; sustituye la transcripción de notas por un consolidado que se calcula sobre los datos registrados; genera constancias y expedientes con plantillas uniformes; y advierte sobre los documentos próximos a vencer. Cada una de esas funciones existe en el producto y se describe con su ubicación en el código en el documento 03.

La contribución práctica más importante no es la suma de funciones, sino la continuidad operativa. La institución puede seguir registrando notas y movimientos de personal durante un corte de red o un apagón, y los cambios se integran cuando el servicio vuelve. Esa propiedad es la que justifica el costo de construir un subsistema de sincronización en lugar de una aplicación de escritorio convencional.

### 1.5.3 Justificación social

La institución educativa administra información de dos poblaciones vulnerables en distinto grado: los trabajadores, cuyos datos salariales y de salud circulan por la secretaría, y los niños, cuyas calificaciones y datos de representación se conservan en la coordinación académica. Un sistema que restringe el acceso por rol, registra las operaciones sensibles y conserva la trazabilidad de cada cambio protege a ambas poblaciones. El proyecto no se limita a automatizar: sustituye un esquema de confianza interpersonal por un esquema de permisos verificables.

El efecto social se extiende al personal. La disponibilidad inmediata de la constancia de trabajo, del recibo de pago y del boletín reduce la dependencia de favores y de horarios de oficina, y disminuye la conflictividad que suele acompañar a los errores de liquidación.

### 1.5.4 Justificación tecnológica

El proyecto demuestra que es posible sostener una base de datos multiusuario sin adquirir un servidor de base de datos ni contratar un servicio en la nube. La combinación de SQLite en modo WAL, un nodo central que actúa como único escritor de la copia compartida y un agente que replica por HTTP sobre la intranet reduce el costo de infraestructura a los equipos que la institución ya posee. Esa decisión no es una limitación impuesta por el presupuesto: es una arquitectura deliberada para un entorno donde la conexión externa no es confiable.

### 1.5.5 Justificación metodológica

El proyecto articula la modalidad de proyecto factible con un diseño cuantitativo. El diagnóstico produce requerimientos y una línea base; el diseño produce especificaciones verificables; la construcción produce un artefacto sometido a pruebas automatizadas; y la evaluación produce mediciones de latencia, caudal, tasa de éxito y usabilidad. Cada fase deja un producto que la siguiente consume, de modo que la trazabilidad entre objetivo, requerimiento, componente y prueba puede reconstruirse sin depender de la memoria del investigador.

### 1.5.6 Justificación económica

El costo de adquisición del software es nulo, porque todas las tecnologías empleadas son de código abierto y se distribuyen con licencia MIT. El costo de operación se reduce al mantenimiento del nodo central, que puede ejecutarse en un equipo de la propia institución, y a la actualización periódica de dependencias. El ahorro proviene de tres fuentes: la eliminación de la doble captura, la reducción del tiempo de consolidación de boletines y la disminución de reprocesos por errores de transcripción. La cuantificación de esas tres fuentes corresponde a la Fase IV y se obtiene con la misma ficha de observación que estableció la línea base.

### 1.5.7 Justificación del enfoque cuantitativo

La elección del enfoque cuantitativo no deriva de una preferencia epistemológica, sino de la naturaleza de las variables que el objetivo general compromete. El objetivo promete optimizar procesos administrativos, y esa promesa solo puede sostenerse con magnitudes comparables antes y después de la intervención. Un testimonio sobre la rapidez percibida no permite afirmar que el tiempo de consolidación disminuyó; una medición cronometrada sí.

Las variables del estudio son numéricas y tienen unidad de medida. La latencia se expresa en milisegundos y se calcula como la diferencia entre el instante en que se envía una petición y el instante en que se recibe la respuesta completa. El caudal se expresa en operaciones por segundo. La tasa de éxito de sincronización se expresa como porcentaje y se calcula dividiendo las operaciones confirmadas por el nodo central entre las operaciones registradas durante el intervalo de observación. El consumo de recursos se expresa en megabytes de memoria residente y en porcentaje de CPU. La usabilidad se expresa en una puntuación SUS de 0 a 100, que se obtiene de un cuestionario estructurado de diez ítems y se analiza con estadística descriptiva e inferencial.

El enfoque cuantitativo también impone una disciplina sobre el diseño. Las condiciones de prueba se fijan antes de ejecutarlas, los instrumentos se validan antes de aplicarlos y los criterios de aceptación se declaran antes de conocer los resultados. Esa anticipación es la que impide que el investigador ajuste los umbrales a los datos obtenidos, práctica que invalidaría cualquier conclusión sobre rendimiento.

Se descartó el enfoque mixto por tres razones. La primera es que el objeto de evaluación es un artefacto y no una práctica social, de modo que las categorías cualitativas aportarían contexto pero no evidencia sobre el cumplimiento de los objetivos. La segunda es que el número de participantes previsto permite análisis estadísticos descriptivos y contrastes no paramétricos, pero no alcanza para una saturación teórica que justifique un componente cualitativo con pretensión de rigor. La tercera es de coherencia interna: si los objetivos se formulan con verbos medibles y las hipótesis se expresan como relaciones entre variables numéricas, un análisis interpretativo introduciría un criterio de validación distinto del que el propio diseño establece.

## 1.6 Hipótesis y variables

### 1.6.1 Hipótesis general

**H1.** El sistema de base de datos local multiusuario con sincronización híbrida reduce el tiempo de los procesos administrativos seleccionados, mantiene una tasa de éxito de sincronización igual o superior al 99 % ante interrupciones controladas de red y obtiene una puntuación SUS igual o superior a 70 puntos.

**H0.** El sistema no produce reducción en los tiempos de proceso, o su tasa de éxito de sincronización es inferior al 99 %, o su puntuación SUS es inferior a 70 puntos.

Los umbrales no son arbitrarios. El 99 % de éxito se adoptó porque una pérdida superior a una operación por cada cien obligaría a revisar manualmente el journal en cada jornada. La puntuación de 70 corresponde al límite inferior de la categoría aceptable en la interpretación de la escala SUS (Sauro y Lewis, 2016). La reducción de tiempos se contrastará con la prueba que corresponda a la distribución observada, según se especifica en el documento 02.

### 1.6.2 Hipótesis específicas

| Código | Hipótesis | Variable independiente | Variable dependiente | Prueba prevista |
|---|---|---|---|---|
| HE1 | El tiempo de registro de un trabajador disminuye al menos 50 % respecto de la línea base. | Uso del sistema | Tiempo de registro (s) | t de muestras relacionadas o Wilcoxon |
| HE2 | El tiempo de consolidación de un boletín disminuye al menos 60 %. | Uso del sistema | Tiempo de consolidación (min) | t o Wilcoxon |
| HE3 | La tasa de error de transcripción de notas se reduce a menos de 1 %. | Uso del sistema | Notas corregidas / transcritas | Chi-cuadrado |
| HE4 | La tasa de éxito de sincronización es igual o superior a 99 % con interrupciones controladas. | Condición de red | Operaciones confirmadas / registradas | Intervalo de confianza para una proporción |
| HE5 | La latencia media de las peticiones en la LAN es inferior a 200 ms. | Carga y tamaño de lote | Latencia (ms) | Estadística descriptiva y prueba de normalidad |
| HE6 | La puntuación SUS es igual o superior a 70 puntos. | Uso del sistema | Puntuación SUS (0 a 100) | t de una muestra o Wilcoxon |

### 1.6.3 Operacionalización de variables

| Variable | Definición conceptual | Dimensión | Indicador | Escala | Instrumento |
|---|---|---|---|---|---|
| Tiempo de proceso | Duración de una tarea administrativa desde su inicio hasta su confirmación | Eficiencia | Segundos o minutos por tarea | Razón | Ficha de observación técnica |
| Latencia de red | Tiempo transcurrido entre la solicitud y la respuesta completa | Rendimiento | Milisegundos | Razón | Ficha de registro de métricas |
| Caudal | Operaciones procesadas por unidad de tiempo | Rendimiento | Operaciones por segundo | Razón | Ficha de registro de métricas |
| Tasa de éxito de sincronización | Proporción de operaciones registradas que el nodo central confirma | Fiabilidad | Porcentaje | Razón | Consulta al journal y al nodo central |
| Consumo de recursos | Memoria residente y CPU utilizados por el proceso | Eficiencia | MB y porcentaje | Razón | Monitor del sistema operativo |
| Usabilidad | Facilidad de uso percibida por el usuario | Usabilidad | Puntuación SUS | Intervalo (0 a 100) | Cuestionario SUS |
| Exactitud de la información | Correspondencia entre el dato registrado y el hecho que representa | Calidad | Porcentaje de registros correctos | Razón | Revisión documental |

La variable independiente del estudio es la implementación del sistema, que se manipula en una sola dirección: se introduce en la institución y se compara la situación posterior con la línea base. No se trata de un experimento con grupo de control, y esa circunstancia se declara como limitación en el apartado 1.8.

## 1.7 Alcance

### 1.7.1 Alcance funcional

El sistema comprende nueve módulos operativos y un conjunto de servicios transversales. Los módulos son: panel de control, empleados, documentos, incidencias, contratos, nómina, configuración institucional, estudiantes y calificaciones. Los servicios transversales son autenticación con roles, auditoría, respaldos, exportación a formatos abiertos, generación de PDF y sincronización entre puestos.

En materia de personal, el alcance incluye el expediente completo del trabajador, el control de documentos con vencimiento, el registro de incidencias con flujo de aprobación, la gestión de contratos con renovación y finiquito, y el cálculo de nómina con deducciones, horas extra, prestaciones y aguinaldo. En materia académica, incluye el legajo del estudiante con cédula única, la estructura de grados y secciones por año escolar, la matrícula con una sola inscripción activa por estudiante y periodo, el registro de calificaciones por materia, el consolidado del periodo, el boletín por estudiante y el acta final del grado.

En materia documental, el alcance incluye la generación de constancias de trabajo y de estudios, la ficha del empleado, el recibo de pago, la planilla de nómina, los reportes de incidencias, vencimientos y contratos, y la exportación de listados a Excel y CSV. La generación de PDF se realiza con plantillas institucionales y deja constancia del usuario que la solicitó y del momento en que se produjo.

En materia de sincronización, el alcance incluye la replicación bidireccional de las tablas de personal, documentos, incidencias, contratos, pagos, configuraciones y del dominio académico; la captura transaccional de cambios; la asignación de identidad global por UUID y clave natural; la mezcla por campo con registro de conflictos; la sincronización automática en segundo plano y la sincronización manual; y la operación del nodo central en la intranet.

### 1.7.2 Alcance técnico

El sistema se distribuye como aplicación de escritorio para Windows y Linux, con base de datos SQLite embebida y SQLAlchemy como capa de mapeo. El nodo central se ejecuta con la biblioteca estándar de Python y no requiere servidor de aplicaciones ni motor de base de datos externo. La red de operación es una LAN Ethernet o Wi-Fi institucional, con un máximo previsto de veinte puestos por nodo central, cifra que se adopta como supuesto de diseño y que la Fase IV verificará con las pruebas de concurrencia.

### 1.7.3 Fuera del alcance

La aplicación móvil nativa forma parte del alcance entregado: el cliente Android SDEP Móvil y el nodo central de sincronización se construyeron junto con el puesto de escritorio y comparten su mismo modelo de datos y su mismo protocolo. Quedan fuera del alcance la sincronización con servicios en la nube, la integración con plataformas externas de gestión escolar, la interfaz web en navegador, la firma electrónica certificada y el marcaje horario del personal. La arquitectura deja preparados los puntos de extensión para una terminal secundaria de solo lectura, pero esa terminal no forma parte del producto entregado. La exclusión se declara para evitar que el lector atribuya al sistema funciones que no fueron construidas.

## 1.8 Limitaciones

La primera limitación es de diseño. El estudio no dispone de grupo de control, de modo que las diferencias observadas entre la línea base y la medición posterior no pueden atribuirse con certeza absoluta a la intervención. La comparación se refuerza con la constancia de que las tareas, los instrumentos y los participantes son los mismos, pero la validez interna queda sujeta a esa condición.

La segunda limitación es de muestra. La institución participante es una sola, y el número de usuarios se sitúa entre veinte y treinta. Esa cifra permite análisis descriptivos y contrastes no paramétricos, pero no autoriza generalizaciones sobre el conjunto de las instituciones educativas del país.

La tercera es de infraestructura. Las mediciones de latencia y caudal se realizan sobre la red de la institución, con la topología y el equipamiento disponibles. Los resultados describen esa red y no una red ideal de laboratorio.

La cuarta es de alcance temporal. El periodo de observación posterior a la implementación abarca un lapso académico completo, lo que permite medir el cierre de notas y la emisión de boletines, pero no permite evaluar el comportamiento del sistema a lo largo de varios años ni la acumulación de datos históricos.

La quinta es de naturaleza jurídica. La institución trata datos de niños y de trabajadores, y el ordenamiento venezolano no cuenta con una ley general de protección de datos personales. El sistema adopta los principios del habeas data constitucional y las previsiones de la Ley Orgánica para la Protección de Niños, Niñas y Adolescentes, pero no puede invocar una norma especial que no existe. Esa circunstancia se analiza en el documento 02 y se declara aquí para que no se interprete como una omisión.

## 1.9 Viabilidad

### 1.9.1 Viabilidad técnica

El proyecto es viable porque las tecnologías empleadas son maduras y están documentadas: Python, SQLAlchemy, SQLite, CustomTkinter, ReportLab y OpenPyXL. La arquitectura de capas permite desarrollar y probar cada componente por separado. El nodo central utiliza la biblioteca estándar de Python, lo que elimina dependencias adicionales en el equipo que lo hospeda. La sincronización se apoya en HTTP sobre la intranet, protocolo que la institución ya utiliza para compartir impresoras y archivos.

### 1.9.2 Viabilidad operativa

La institución dispone de los equipos, la red y el personal que operará el sistema. La instalación se realiza con un ejecutable y no requiere permisos de administrador sobre un servidor. La capacitación se limita a dos sesiones por perfil de usuario y a una guía escrita. El nodo central puede alojarse en el equipo de la secretaría, con respaldo diario en un dispositivo externo.

### 1.9.3 Viabilidad económica

El costo de licenciamiento es nulo. El costo de operación se reduce al consumo eléctrico del equipo central y al mantenimiento preventivo. El proyecto se ejecuta con recursos del investigador y con el equipamiento existente. La estimación detallada se presenta en el documento 02, junto con el cronograma.

### 1.9.4 Viabilidad temporal

El cronograma comprende treinta y cuatro semanas distribuidas en cuatro fases. La Fase I ocupa seis semanas, la Fase II seis, la Fase III catorce y la Fase IV ocho. La distribución reserva un margen de dos semanas para contingencias y coincide con el calendario académico, de modo que el cierre de lapso ocurre durante la Fase IV y no durante la construcción.

## 1.10 Aporte sociotecnológico

El proyecto se inscribe en la tradición de los proyectos sociotecnológicos porque no se limita a introducir una herramienta: modifica la forma en que la institución custodia y comparte su información. Antes de la intervención, la información pertenecía a quien la archivaba. Después, pertenece a la institución y su acceso se rige por roles. Ese cambio es tecnológico y organizacional a la vez, y su sostenibilidad depende de que el personal comprenda las reglas de acceso y de que la dirección asuma la responsabilidad de administrarlas.

El aporte se concreta en tres productos. El primero es un sistema operativo que la institución puede mantener sin depender de su desarrollador. El segundo es un conjunto de instrumentos de medición que permiten evaluar el sistema en el futuro con los mismos criterios. El tercero es un modelo de sincronización documentado que otras instituciones con restricciones similares pueden replicar.

## 1.11 Conclusiones del capítulo

El diagnóstico mostró que la institución no enfrenta problemas aislados sino una causa común: la ausencia de un repositorio compartido con reglas de acceso y de concurrencia. Esa lectura permitió formular un objetivo general que integra base de datos, sincronización y documentos, en lugar de un conjunto de aplicaciones independientes que habrían reproducido la dispersión original.

La formulación de los objetivos adoptó la taxonomía de Bloom y los criterios SMART, y ese ejercicio obligó a descartar dos formulaciones que no admitían verificación. Las hipótesis y las variables se definieron con unidad de medida, instrumento y prueba estadística, de modo que la evaluación de la Fase IV no dependa de interpretaciones posteriores. El enfoque cuantitativo se justificó por la naturaleza numérica de las variables y por la necesidad de comparar la línea base con el desempeño del sistema.

El alcance quedó delimitado en nueve módulos de escritorio, seis servicios transversales, un cliente Android nativo y un nodo central de sincronización, con exclusión expresa de la nube, la interfaz web en navegador y la firma electrónica certificada. Las limitaciones se declararon antes de conocer los resultados, condición que protege la credibilidad de las conclusiones. El capítulo siguiente desarrolla el marco teórico que sustenta estas decisiones y la metodología que las convierte en un procedimiento replicable.

## 1.12 Referencias citadas

Anderson, L. W., y Krathwohl, D. R. (Eds.). (2001). *A taxonomy for learning, teaching, and assessing: A revision of Bloom's taxonomy of educational objectives*. Longman.

Kleppmann, M., Wiggins, A., van Hardenberg, P., y McGranaghan, M. (2019). Local-first software: You own your data, in spite of the cloud. En *Proceedings of the 2019 ACM SIGPLAN International Symposium on New Ideas, New Paradigms, and Reflections on Programming and Software* (pp. 154-178). ACM. https://doi.org/10.1145/3359591.3359737

Sauro, J., y Lewis, J. R. (2016). *Quantifying the user experience: Practical statistics for user research* (2.ª ed.). Morgan Kaufmann.

La lista completa de fuentes del compendio se consigna en el documento 02, apartado 2.9.
