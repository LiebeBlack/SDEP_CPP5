# 02. MARCO TEÓRICO Y METODOLÓGICO

**Documento:** segundo del compendio académico.
**Sistema documentado:** SDEP_CPP5, versión 3.0.1.
**Modalidad:** proyecto factible, investigación aplicada.
**Enfoque:** cuantitativo.
**Ventana bibliográfica principal:** 2016 a 2026.

---

## 2.1 Introducción

Este documento cumple dos funciones que suelen presentarse separadas. La primera es establecer el fundamento conceptual y legal del sistema: qué se entiende por base de datos relacional, por consistencia, por sincronización, por usabilidad y por documento institucional, y de dónde proviene cada uno de esos conceptos. La segunda es fijar la metodología que convierte esos conceptos en un procedimiento verificable: qué tipo de investigación se realizó, qué se midió, con qué instrumentos, sobre qué población y con qué criterios de análisis.

La separación entre marco teórico y marco metodológico es didáctica, no real. Cada decisión de diseño que se describe en el documento 03 remite a un concepto de este documento, y cada instrumento de medición remite a una variable definida en el documento 01. El lector que necesite reconstruir una afirmación encontrará en las tablas de trazabilidad la cadena completa, desde la norma o la teoría hasta el componente que la implementa.

### 2.1.1 Nota sobre la ventana bibliográfica

La revisión priorizó fuentes publicadas entre 2016 y 2026, con énfasis en los últimos cinco años. Esa prioridad no se aplicó de forma mecánica, porque tres clases de fuentes no pueden sustituirse por publicaciones recientes sin perder precisión. La primera es la norma jurídica: una ley vale por su vigencia y no por su fecha. La segunda es la norma técnica: ISO/IEC 25010 sigue siendo la referencia de calidad de producto aunque su edición sea anterior a la ventana. La tercera es la fuente primaria de un instrumento o de una taxonomía: la escala SUS se cita por su formulación original y se interpreta con las validaciones posteriores, y la taxonomía de Bloom se cita por su revisión de 2001 y se aplica con la lectura crítica de Krathwohl (2002).

Esas excepciones se declaran en la lista de referencias con la indicación correspondiente. Fuera de ellas, toda afirmación teórica se apoya en fuentes de la ventana 2016 a 2026, y las fuentes anteriores se emplean solo para contrastar o para señalar el origen de un concepto que la literatura posterior confirmó.

## 2.2 Antecedentes

### 2.2.1 Protocolo de búsqueda

La revisión siguió un protocolo declarado antes de la lectura, con el fin de evitar la selección de fuentes que confirmaran la solución propuesta. Se consultaron Scopus, Web of Science, IEEE Xplore, ACM Digital Library, ScienceDirect y SciELO. Los términos se combinaron en tres bloques: el primero reunió *offline-first*, *local-first*, *edge database*, *SQLite* y *synchronization*; el segundo, *client-server*, *LAN*, *latency*, *throughput* y *concurrency*; el tercero, *school management*, *usability*, *SUS* y *digital transformation*. La búsqueda se limitó a trabajos publicados entre 2016 y 2026, en español o inglés, con revisión por pares o con carácter de norma técnica.

Los criterios de inclusión fueron cuatro: pertinencia directa con al menos uno de los tres bloques; descripción explícita del método o de la arquitectura; disponibilidad del texto completo; y aporte verificable a una decisión de diseño o de medición. Los criterios de exclusión fueron: trabajos sin método declarado, artículos de divulgación sin respaldo empírico, propuestas sin evaluación y duplicados. La selección final se organizó en dos grupos: antecedentes teóricos, que sustentan conceptos, y antecedentes empíricos, que reportan resultados comparables.

### 2.2.2 Antecedentes teóricos

**Software local-first.** Kleppmann, Wiggins, van Hardenberg y McGranaghan (2019) formularon los siete ideales del software local-first: que el dato resida en el dispositivo del usuario, que la colaboración funcione sin red, que el trabajo no se pierda por fallos del servicio, que el usuario conserve el control, que el sistema opere con latencia mínima, que la colaboración sea de larga duración y que los datos sobrevivan al proveedor. El trabajo es relevante porque desplaza el criterio de éxito desde la disponibilidad del servidor hacia la disponibilidad del dato en el puesto. Su limitación, que los propios autores reconocen, es que la mayoría de los sistemas existentes no cumplen el ideal de colaboración sin conflictos y recurren a soluciones intermedias.

**Consistencia en almacenamiento distribuido.** Viotti y Vukolić (2016) revisaron las garantías de consistencia de los sistemas de almacenamiento no transaccional y ordenaron el espacio entre consistencia fuerte, consistencia causal y consistencia eventual. La revisión aporta el vocabulario con el que este proyecto describe su propia garantía: convergencia eventual con resolución determinista de conflictos por campo, y no consistencia fuerte entre puestos. Esa precisión evita la afirmación, frecuente pero falsa, de que un sistema replicado puede ofrecer simultáneamente disponibilidad y consistencia fuerte ante una partición de red.

**Réplicas convergentes.** La familia de los tipos de datos replicados libres de conflictos (Shapiro, Preguiça, Baquero y Zawirski, 2011) permite que varias réplicas converjan sin coordinación. Kleppmann y Beresford (2017) propusieron una variante para JSON, con el objetivo de que varias réplicas converjan sin coordinación. Su enfoque resuelve el conflicto en la estructura del dato, mientras que el sistema de este proyecto lo resuelve en el campo y conserva el valor perdedor para revisión. La comparación es útil porque permite justificar la elección: un CRDT garantiza convergencia automática pero no ofrece una bandeja de conflictos comprensible para un administrador escolar, y la institución necesitaba poder auditar los cambios económicos.

**Patrón de registro transaccional.** Richardson (2018) describió el patrón *transactional outbox* en el contexto de los microservicios: la operación de negocio y el mensaje que la anuncia se escriben en la misma transacción, y un publicador independiente se encarga del envío. El sistema aplica ese patrón con una variante: el journal no anuncia un mensaje a un intermediario, sino que registra la operación para que el agente la replique. La variante conserva la propiedad esencial, que es la atomicidad entre el dato y su anuncio.

**Ingeniería de software y arquitectura.** Sommerville (2016) y Martin (2017) coinciden en que la separación de responsabilidades y la dirección única de las dependencias son condiciones de mantenibilidad, no adornos de diseño. El proyecto las aplica en seis capas y en un dominio de cálculo aislado. El aislamiento del dominio de nómina respecto de la interfaz y del acceso a datos permite probar las reglas de cálculo con independencia del entorno, condición que se verificó con la suite automatizada.

### 2.2.3 Antecedentes empíricos

**Transformación digital en educación superior.** Benavides et al. (2020) realizaron una revisión sistemática de la literatura sobre transformación digital en instituciones de educación superior. Identificaron como impulsores la demanda de nuevos servicios, la presión competitiva y la madurez tecnológica, y como barreras la resistencia al cambio, las limitaciones presupuestarias y las brechas de competencia digital. La revisión no estudia la sincronización de datos, pero sitúa el problema de este proyecto en un marco más amplio: la adopción depende menos de la tecnología que de la capacidad institucional para sostenerla.

**Usabilidad medida con SUS.** Lewis (2018) revisó treinta años de aplicación de la escala SUS y concluyó que su valor no reside en la precisión absoluta de la puntuación, sino en su capacidad para comparar un sistema con referencias acumuladas. Esa conclusión orientó dos decisiones: se adoptó SUS como instrumento único de usabilidad y se fijó el umbral de 70 puntos con base en la interpretación de Sauro y Lewis (2016), no en una expectativa del investigador.

**Métodos empíricos en ingeniería de software.** Ralph et al. (2020) publicaron un conjunto de estándares empíricos para la investigación en ingeniería de software, con listas de verificación por tipo de estudio. Wohlin et al. (2024) actualizaron el manual de experimentación en ingeniería de software, con énfasis en la validez y en la replicación. Ambos trabajos sustentan la estructura de la Fase IV: condiciones de prueba declaradas, instrumentos validados, análisis previsto y reporte de amenazas a la validez.

**Proyecto factible en el ámbito latinoamericano.** El Manual de trabajos de grado de la Universidad Pedagógica Experimental Libertador (UPEL, 2016) define el proyecto factible como la elaboración de una propuesta dirigida a resolver un problema de carácter práctico, con fundamento en un diagnóstico y con una evaluación de su viabilidad. Esa definición es la que se adopta en este trabajo, con una precisión adicional: el proyecto no se detiene en la propuesta, sino que construye el producto y lo evalúa con métricas.

### 2.2.4 Antecedentes regionales y estado de la cuestión

La búsqueda en SciELO y en repositorios institucionales arrojó trabajos sobre sistemas de gestión escolar y sobre digitalización administrativa, pero la mayoría describe plataformas web con conectividad permanente y no aborda el problema de la operación sin red. Esa ausencia es relevante para el presente estudio: el contexto latinoamericano presenta con frecuencia interrupciones de conectividad y equipos compartidos, y sin embargo la literatura regional sobre sistemas escolares rara vez reporta mediciones de sincronización o de tolerancia a desconexiones.

La incorporación de antecedentes locales específicos queda sujeta a la disponibilidad de los repositorios de la institución. El protocolo de búsqueda se deja documentado para que esa incorporación se realice con el mismo criterio y no mediante una selección ad hoc. Mientras esa evidencia se complete, el estado de la cuestión se sostiene en los antecedentes teóricos y empíricos descritos, que cubren los tres componentes del objeto de estudio: replicación, arquitectura y usabilidad.

### 2.2.5 Síntesis crítica

Los antecedentes convergen en cuatro conclusiones. La primera es que la disponibilidad del dato en el puesto, y no la del servidor, es el criterio que corresponde a un entorno con conectividad intermitente. La segunda es que la convergencia entre réplicas exige una regla determinista y que esa regla debe poder auditarse. La tercera es que la usabilidad se evalúa con instrumentos estandarizados y no con impresiones, y que SUS ofrece una referencia acumulada que permite interpretar una puntuación aislada. La cuarta es que la investigación en ingeniería de software exige declarar las condiciones de medición antes de ejecutarlas.

Ninguno de los trabajos revisados documenta la aplicación conjunta de esas cuatro conclusiones en una institución educativa de recursos limitados. Esa es la brecha que el proyecto ocupa. La brecha no es teórica, pues los conceptos están establecidos, sino empírica: falta un caso que muestre qué combinación de decisiones funciona en ese contexto y cuáles resultan inviables.

## 2.3 Bases teóricas

### 2.3.1 Modelo relacional y normalización

El modelo relacional representa la información mediante relaciones y restringe las operaciones a un conjunto cerrado de operadores sobre conjuntos (Date, 2019). Su adopción en este proyecto no responde a una preferencia estética: las entidades del dominio tienen claves naturales verificables, como la cédula del trabajador y la cédula del estudiante, y las relaciones entre ellas son estables y acotadas. Un trabajador acumula documentos, incidencias, contratos y pagos; un estudiante acumula matrículas y notas; una nota pertenece a una matrícula y a una materia dentro de un periodo. Esa estructura se expresa con naturalidad en tablas y claves foráneas.

El esquema se normalizó hasta la tercera forma normal. La decisión implicó separar los datos de contacto de los datos laborales, aislar las notas en una tabla propia y extraer los parámetros institucionales a una tabla de configuración. La normalización tiene un costo: algunas consultas requieren reuniones de tres o cuatro tablas. Ese costo se compensa con índices declarados sobre las columnas de búsqueda frecuente, que son la cédula, el periodo, el estado de la incidencia y la matrícula.

La integridad se sostiene en tres niveles. El primero es la declaración del esquema: claves primarias, claves foráneas y restricciones de unicidad. El segundo es la validación en la capa de servicios, que rechaza los valores inválidos antes de llegar a la base. El tercero es la validación en la interfaz, que impide el envío de formularios incompletos. La redundancia entre niveles es deliberada: la base protege la integridad aun si un servicio falla, y la interfaz evita que el usuario reciba un error técnico que no sabe interpretar.

### 2.3.2 Transacciones y propiedades ACID

Una transacción agrupa operaciones que deben confirmarse o rechazarse como una unidad. Las propiedades ACID describen ese comportamiento: atomicidad, consistencia, aislamiento y durabilidad (Kleppmann, 2017). En este proyecto la propiedad crítica es la atomicidad, porque de ella depende que el journal de sincronización no anuncie una operación que la base no confirmó.

El mecanismo se implementa en dos tiempos. Antes de confirmar la sesión, el enganche al ORM lee el historial de atributos modificados y anota qué cambió. Después de confirmar, y ya con las claves primarias disponibles, escribe la operación definitiva en el journal. Las filas del journal se añaden a la misma sesión y se confirman en la misma transacción que el dato. Si la transacción se deshace, la operación desaparece con ella. Si el equipo pierde la energía después de la confirmación, la operación ya está en el disco y se replicará en el siguiente ciclo.

La durabilidad depende de la configuración del motor y del sistema operativo. SQLite confirma la transacción en el diario antes de liberar el bloqueo, y el proyecto no desactiva la sincronización del archivo. La garantía que se ofrece es la de una transacción confirmada: si el proceso se interrumpe antes de la confirmación, SQLite revierte; si el sistema operativo completa la escritura, la operación sobrevive. El proyecto no promete durabilidad ante un fallo físico del disco, porque esa garantía depende del hardware y no del software.

### 2.3.3 SQLite, WAL y concurrencia

SQLite es una biblioteca que implementa un motor relacional completo sobre un archivo. Su modelo de concurrencia se basa en bloqueos y, en el modo de diario de reversión, un escritor bloquea a los lectores. El modo WAL (write-ahead logging) cambia ese comportamiento: las escrituras se appended a un archivo aparte y los lectores siguen viendo la última instantánea confirmada sin bloquearse (SQLite Consortium, 2024).

El nodo central activa WAL de forma explícita y fija un `busy_timeout` de treinta segundos, de modo que varias peticiones concurrentes esperan su turno en lugar de fallar con un error de base bloqueada. Los puestos conservan la configuración por defecto del motor y serializan sus escrituras a través de la sesión de SQLAlchemy y del agente. El nodo central sigue siendo un único escritor, decisión que simplifica la consistencia: no hay dos procesos que puedan confirmar la misma operación con números de secuencia distintos.

SQLite impone límites que conviene declarar. El primero es el tamaño: una base institucional con diez años de nómina y calificaciones se mantiene en el orden de cientos de megabytes, muy por debajo del límite práctico del motor. El segundo es la concurrencia: un solo escritor por archivo, razón por la cual el nodo central serializa las escrituras y los puestos escriben en su propia copia. El tercero es la red: SQLite no debe abrirse sobre un recurso compartido de red, porque los bloqueos del sistema de archivos no son confiables en esa condición. El proyecto respeta esa restricción: cada puesto tiene su archivo local y la comunicación se realiza por HTTP, no por un archivo compartido.

### 2.3.4 ORM y patrón Repository

El mapeo objeto-relacional traduce entre las tablas y los objetos del dominio. SQLAlchemy 2.x permite declarar las entidades como clases, gestionar las sesiones y construir consultas tipadas. Su uso aporta tres beneficios: elimina la concatenación de SQL en la lógica de negocio, concentra las relaciones en un solo lugar y permite sustituir el motor sin reescribir los servicios.

Sobre el ORM se aplica el patrón Repository. Un repositorio base genérico expone las operaciones comunes de consulta y persistencia, y los repositorios concretos añaden las consultas propias de cada entidad. La capa de servicios recibe sus repositorios por inyección, no los instancia. Esa decisión permite probar un servicio con un repositorio simulado y permite cambiar la implementación de una consulta sin tocar la interfaz.

El patrón tiene un límite que conviene reconocer. Un repositorio genérico tiende a exponer operaciones que no todas las entidades necesitan, y ese exceso de interfaz puede ocultar reglas del dominio. El proyecto lo mitiga manteniendo las reglas en los servicios y reservando el repositorio para el acceso a datos.

### 2.3.5 Arquitectura cliente-servidor en red local

La arquitectura cliente-servidor distribuye responsabilidades entre un nodo que provee un servicio y varios nodos que lo consumen. En una red local, la latencia depende de tres factores: el medio físico, la carga del nodo servidor y el tamaño del mensaje. Una LAN Ethernet con conmutadores dedicados presenta latencias de fracciones de milisegundo; una red Wi-Fi compartida puede multiplicar esa cifra por diez o más cuando hay interferencia.

El proyecto adopta una variante que conviene precisar. No es una arquitectura cliente-servidor clásica, en la que el cliente no tiene datos y solicita todo al servidor. Es una arquitectura de réplicas: cada cliente posee una base completa y el servidor central actúa como punto de encuentro. Esa variante se denomina a veces cliente-servidor con réplica local o arquitectura de sincronización. Su ventaja es la continuidad; su costo es la complejidad de la reconciliación.

El transporte es HTTP sobre la intranet. Se eligió porque atraviesa con facilidad los cortafuegos institucionales, porque la biblioteca estándar de Python incluye un servidor y un cliente suficientes, y porque el protocolo puede inspeccionarse con herramientas comunes. No se utilizó un intermediario de mensajes porque habría añadido un componente que la institución no puede operar.

### 2.3.6 Offline-first y local-first

Un sistema offline-first prioriza la operación local y trata la red como una mejora, no como un requisito. Un sistema local-first lleva esa prioridad al extremo: el dato primario reside en el dispositivo y la nube, si existe, es una copia (Kleppmann et al., 2019). El proyecto se aproxima al segundo modelo, con una salvedad: la copia del nodo central no es una copia secundaria, sino la referencia que permite que los puestos se encuentren.

La distinción importa para interpretar las garantías. Entre dos puestos cualesquiera no hay consistencia fuerte: un cambio registrado en el puesto A puede tardar un ciclo de sincronización en llegar al puesto B. Lo que sí se garantiza es la convergencia: si ambos puestos permanecen conectados el tiempo suficiente, ambos alcanzan el mismo estado, y ese estado es independiente del orden en que llegaron las operaciones. La garantía se apoya en un orden total determinista y en la idempotencia de la aplicación.

### 2.3.7 Outbox, idempotencia y entrega efectiva

El patrón outbox escribe la operación en una tabla de salida dentro de la misma transacción que el cambio. Un publicador lee esa tabla y envía las operaciones pendientes. Si el envío falla, la operación permanece en la tabla y se reintenta; si el envío se realiza pero la confirmación se pierde, el receptor debe poder reconocer la operación repetida y no aplicarla dos veces.

El proyecto implementa esa garantía con dos mecanismos. El primero es un identificador único por operación, que el receptor registra en una tabla de operaciones aplicadas. El segundo es una regla de comparación por campo que distingue entre un valor idéntico y un valor nuevo. El resultado se denomina entrega efectiva: la red puede entregar una operación más de una vez, pero el estado final es el mismo que si se hubiera entregado una sola vez.

La distinción entre entrega efectiva y entrega exacta no es semántica. La segunda es imposible de garantizar en un sistema que puede fallar entre el envío y la confirmación; la primera es alcanzable con idempotencia y es la que el sistema ofrece.

### 2.3.8 UUID, marcas de tiempo y relojes

Un identificador único universal (UUID) permite que dos puestos creen registros distintos sin coordinarse. El proyecto asigna un UUID a cada fila sincronizable y lo vincula a la clave natural del dominio, que sigue siendo la cédula, el número de contrato o la clave de configuración. Esa doble identidad resuelve un problema práctico: el UUID permite reconocer la misma fila entre puestos, y la clave natural permite unificar dos registros creados por separado que representan la misma persona.

Las marcas de tiempo aportan el orden de las escrituras, pero no son confiables por sí mismas. Dos relojes de la misma red pueden diferir en segundos, y un cambio de hora manual puede invertir el orden. El proyecto trata las diferencias inferiores a dos segundos como simultáneas y desempata por el identificador del equipo, que es estable. Esa decisión no elimina el problema del reloj, pero lo acota y hace que todos los nodos elijan el mismo ganador.

### 2.3.9 Documentos PDF y expedientes

Un documento institucional es una representación estable de un acto administrativo. Su valor probatorio depende de tres condiciones: que el contenido corresponda a los datos registrados, que la emisión quede asociada a un usuario y a un momento, y que el formato sea legible sin depender de la aplicación que lo produjo. El PDF cumple la tercera condición porque es un formato abierto y ampliamente soportado.

El proyecto genera los documentos con ReportLab, una biblioteca que construye el PDF a partir de primitivas de dibujo y de un motor de plantillas. La generación se realiza en el servidor local, es decir, en el mismo equipo donde reside la base, de modo que el documento se produce con los datos vigentes y no con una copia exportada. Cada emisión registra el usuario, el momento y el tipo de documento en la auditoría, y el archivo se almacena con un nombre que incluye el identificador del destinatario y la fecha.

El expediente, a diferencia de la constancia, reúne varios documentos y datos en un solo archivo. Su diseño exige un índice, una portada con la identificación de la institución y una numeración que permita citar cada sección. El proyecto lo resuelve con una plantilla multipágina y con una verificación previa de que los datos obligatorios estén completos.

### 2.3.10 Arquitectura por capas, MVP y principios de diseño

La arquitectura por capas organiza el sistema en niveles que se comunican en una sola dirección. El proyecto distingue presentación, servicios, repositorios, modelos, dominio de cálculo y servicios transversales. La regla de dependencia se respeta: ninguna capa inferior conoce a una superior, y el dominio de nómina no importa la interfaz ni el acceso a datos.

El patrón Modelo-Vista-Presentador (MVP) se adapta a la interfaz de escritorio. La vista se limita a recoger eventos y mostrar resultados; el presentador coordina los servicios y decide qué mostrar; el modelo contiene las entidades y las reglas. En la implementación, los componentes de CustomTkinter actúan como vistas y los servicios como presentadores, sin que exista una clase presentadora separada para cada pantalla. Esa simplificación es deliberada y se declara: el proyecto aplica MVP en su intención, no en su forma canónica.

Los principios de responsabilidad única, abierto-cerrado, sustitución, segregación de interfaces e inversión de dependencias se aplican de forma pragmática. El más visible es la inversión de dependencias: los servicios reciben sus colaboradores y no los construyen, lo que permite probarlos de forma aislada. El menos visible es la segregación de interfaces, que se manifiesta en repositorios pequeños y específicos en lugar de un repositorio universal.

### 2.3.11 Usabilidad y escala SUS

La usabilidad es la medida en que un producto puede ser usado por usuarios determinados para alcanzar objetivos con eficacia, eficiencia y satisfacción. La definición proviene de ISO 9241 y se operacionaliza en este proyecto con tres indicadores: tasa de éxito por tarea, tiempo por tarea y puntuación SUS.

La escala SUS fue propuesta por Brooke (1996) como un cuestionario de diez ítems con respuesta de uno a cinco. Su puntuación se calcula con una regla que alterna ítems positivos y negativos: a los ítems impares se les resta uno; a los pares se les resta el valor de la respuesta a cinco; se suman los resultados y se multiplica por 2,5. El resultado va de 0 a 100 y no debe interpretarse como un porcentaje, sino como una puntuación compuesta.

Lewis (2018) documentó que SUS es robusto con muestras pequeñas y que su utilidad principal es comparativa. Sauro y Lewis (2016) propusieron una interpretación por rangos y una escala de calificación curva. El proyecto adopta el umbral de 70 puntos como límite inferior de aceptabilidad, y reporta la media, la desviación estándar y el intervalo de confianza al 95 %. Con muestras inferiores a treinta participantes, el intervalo se calcula con la distribución t y no con la normal.

### 2.3.12 Taxonomía de Bloom

La taxonomía revisada de Bloom organiza los procesos cognitivos en seis niveles y cruza esa dimensión con cuatro tipos de conocimiento: factual, conceptual, procedimental y metacognitivo (Anderson y Krathwohl, 2001). Krathwohl (2002) explicó que la revisión sustituyó los sustantivos por verbos y que su propósito es facilitar el diseño de objetivos verificables.

El proyecto la utiliza para dos fines. El primero es comprobar que los objetivos específicos no se solapan: cada uno moviliza un proceso distinto y produce una evidencia distinta. El segundo es alinear la evaluación con el objetivo: si el OE4 exige evaluar, el instrumento no puede limitarse a registrar la opinión del usuario, sino que debe contrastar el resultado con un criterio declarado de antemano.

### 2.3.13 Métricas de rendimiento

La latencia es el tiempo entre la solicitud y la respuesta completa. Se mide en milisegundos y se resume con percentiles, no solo con la media, porque la media oculta la cola que percibe el usuario. El proyecto reporta mínimo, mediana, percentil 95, percentil 99 y máximo.

El caudal es el número de operaciones procesadas por unidad de tiempo. Se mide en operaciones por segundo y se calcula sobre un intervalo estable, descartando el calentamiento inicial. La tasa de error es la proporción de solicitudes que no obtuvieron respuesta válida. La tasa de éxito de sincronización es la proporción de operaciones registradas que el nodo central confirmó, y se calcula sobre el journal y sobre la tabla de operaciones aplicadas.

El consumo de recursos se mide con la memoria residente y el porcentaje de CPU del proceso. Ambas cifras dependen del sistema operativo y del equipo, por lo que se reportan con la especificación del entorno de prueba. La comparación entre ejecuciones solo es válida si el entorno se mantiene constante.

## 2.4 Bases legales

### 2.4.1 Criterio de consignación

El marco jurídico se ordena conforme a la jerarquía del ordenamiento venezolano: la Constitución en el nivel superior, las leyes orgánicas y especiales en el siguiente, los reglamentos y resoluciones administrativas después, y las normas técnicas de adopción voluntaria como referencia de calidad. Cada exigencia se vincula con un control del sistema en la tabla de trazabilidad del apartado 2.4.12. Una norma que no se tradujera en un control concreto sería una enumeración decorativa, y el propósito de este apartado es evitar esa enumeración.

Se advierte que la cita de artículos se ofrece con la extensión necesaria para sustentar la correspondencia técnica y no como transcripción literal. La versión definitiva debe confrontar cada referencia con el texto publicado en la Gaceta Oficial, porque las leyes venezolanas se reforman con periodicidad y algunas de las citadas han tenido adecuaciones parciales.

### 2.4.2 Constitución de la República Bolivariana de Venezuela

La Constitución de 1999 fija los derechos que el sistema sirve. El artículo 28 consagra el derecho de toda persona a acceder a la información y a los datos que sobre sí misma consten en registros oficiales o privados, a conocer el uso que se hace de ellos y a solicitar su actualización, rectificación o destrucción cuando sean erróneos. Es la institución del habeas data y la base del derecho de consulta que el sistema ofrece al trabajador sobre su propia ficha.

El artículo 60 reconoce el derecho a la protección del honor, la vida privada, la intimidad, la propia imagen, la confidencialidad y la reputación. El artículo 48 garantiza el secreto y la inviolabilidad de las comunicaciones privadas. Ambos sustentan el control de acceso por rol y la restricción de los archivos de documentos.

En materia laboral, el artículo 87 consagra el derecho al trabajo y el deber de trabajar; el artículo 89 declara el trabajo como hecho social protegido y enuncia los principios de irrenunciabilidad, primacía de la realidad y no discriminación; el artículo 90 fija la jornada máxima; el artículo 91 reconoce el derecho al descanso y a vacaciones remuneradas; y el artículo 92 establece el derecho a un salario suficiente y el principio de igual remuneración por igual trabajo. El motor de nómina traduce esos principios en reglas explícitas y parametrizadas.

En materia educativa, el artículo 102 declara la educación como derecho humano y deber social fundamental; el artículo 103 establece su obligatoriedad; y el artículo 104 dispone que el ingreso, la promoción y la permanencia del personal docente se ajusten a la ley y a criterios de idoneidad académica. El control documental con avisos de vencimiento sirve a la verificación de esa idoneidad.

El artículo 110 reconoce el interés público de la ciencia, la tecnología y la innovación, y el artículo 141 funda la Administración Pública en los principios de honestidad, participación, celeridad, eficacia, eficiencia, transparencia, rendición de cuentas y responsabilidad. El artículo 143 reconoce el derecho de los ciudadanos a ser informados de manera oportuna y veraz. La generación de reportes y el registro de auditoría atienden esos principios.

### 2.4.3 Ley Orgánica del Trabajo, los Trabajadores y las Trabajadoras

La LOTTT fue dictada mediante Decreto N.º 8.938 y publicada en la Gaceta Oficial Extraordinaria N.º 6.076 del 7 de mayo de 2012. El artículo 104 define el salario y el salario normal; el artículo 106 obliga al patrono a entregar un recibo de pago con detalle de conceptos y deducciones; el artículo 109 consagra la igualdad salarial; el artículo 142 regula la garantía y el cálculo de las prestaciones sociales; el artículo 173 fija los límites de la jornada; y el artículo 178 define las horas extraordinarias.

El sistema implementa esas reglas en el dominio `src/nomina`, con parámetros configurables por institución. La configuración no es una concesión a la comodidad: permite que una reforma de las tasas o de los topes se aplique sin modificar el código y sin reinstalar la aplicación. El recibo de pago y la planilla de nómina se generan en PDF y quedan registrados en la auditoría.

### 2.4.4 Ley Orgánica de Educación

La Ley Orgánica de Educación fue publicada en la Gaceta Oficial Extraordinaria N.º 5.929 del 15 de agosto de 2009. Regula los principios y valores de la educación, la organización del sistema educativo y las condiciones del ejercicio de la función docente. Para el proyecto incide en tres ámbitos: los requisitos documentales y de titulación del personal, que el módulo documental controla; la obligación de mantener registros del personal; y los reportes que la institución debe remitir a la autoridad educativa.

### 2.4.5 Ley Orgánica de Ciencia, Tecnología e Innovación

La LOCTI fue reformada mediante Decreto N.º 1.411, publicado en la Gaceta Oficial Extraordinaria N.º 6.151 del 18 de noviembre de 2014. Una reforma parcial posterior fue publicada en la Gaceta Oficial Extraordinaria N.º 6.693 del 1 de abril de 2022, según el registro oficial de la Asamblea Nacional. La ley regula el Sistema Nacional de Ciencia, Tecnología e Innovación y orienta la actividad científica hacia el desarrollo integral del país.

El proyecto se inscribe en ese marco como una contribución tecnológica de origen nacional, construida con componentes abiertos y documentada para su reutilización. La licencia MIT permite que otra institución adopte el sistema sin costo de adquisición y sin negociar una licencia comercial.

### 2.4.6 Ley de Infogobierno

La Ley de Infogobierno fue publicada en la Gaceta Oficial N.º 40.274 del 17 de octubre de 2013, con entrada en vigencia el 17 de agosto de 2014. Establece los principios y lineamientos para el uso de las tecnologías de información en el Poder Público y, en su artículo 16, promueve el empleo de tecnologías libres y estándares abiertos. Cuando la institución aplicable sea de naturaleza pública, esa promoción constituye un requisito y no solo una ventaja.

El sistema se construyó íntegramente con componentes de código abierto y exporta a formatos abiertos. Esa correspondencia es verificable en `requirements.txt` y en el módulo de exportación.

### 2.4.7 Ley Especial contra los Delitos Informáticos

La Ley Especial contra los Delitos Informáticos fue publicada en la Gaceta Oficial N.º 37.313 del 30 de octubre de 2001. Sanciona el acceso indebido a sistemas y datos, la interceptación de comunicaciones, la manipulación de datos y la violación de la privacidad de la información. El sistema previene esas conductas con autenticación obligatoria, control de acceso por rol, registro de auditoría y tratamiento restringido de los archivos.

La ley no ha sido objeto de una reforma verificada en el registro oficial consultado. Esa circunstancia se declara porque la denominación y la numeración de los tipos penales deben confirmarse contra el texto vigente antes de citarlos en un informe pericial.

### 2.4.8 Ley de Mensajes de Datos y Firmas Electrónicas

El Decreto N.º 1.204 con Rango y Fuerza de Ley de Mensajes de Datos y Firmas Electrónicas fue publicado en la Gaceta Oficial N.º 37.148 del 28 de febrero de 2001. Reconoce efectos jurídicos a los mensajes de datos y a las firmas electrónicas que reúnan los requisitos legales. El sistema deja constancia de la autoría y de la integridad de los documentos que genera mediante identificadores, marcas temporales y registros de auditoría, pero no incorpora firma electrónica certificada. Esa incorporación se registra como recomendación de evolución y no como funcionalidad entregada.

### 2.4.9 Protección de niños, niñas y adolescentes

La Ley Orgánica para la Protección de Niños, Niñas y Adolescentes fue objeto de una reforma parcial publicada en la Gaceta Oficial Extraordinaria N.º 6.185 del 8 de junio de 2015. Su principio de interés superior obliga a que toda decisión que afecte a un niño considere su beneficio integral. El sistema trata las calificaciones y los datos de representación como información de acceso restringido: solo la administración y el docente asignado al grado pueden escribir notas, y la consulta se limita a los roles autorizados.

El tratamiento de datos de niños exige una precaución adicional que el sistema no resuelve por sí solo: la institución debe definir quién puede consultar el legajo, por cuánto tiempo se conserva y cómo se atiende una solicitud de rectificación. Esas decisiones son organizacionales y se documentan en el manual de operación.

### 2.4.10 Ausencia de una ley general de protección de datos personales

La revisión de fuentes oficiales realizada para este documento no permitió verificar la promulgación de una ley general de protección de datos personales en Venezuela. El análisis publicado por la International Association of Privacy Professionals (2025) describe el régimen venezolano como fragmentado y basado en derechos constitucionales, y el relevamiento de DLA Piper (2025) confirma esa caracterización. La Sala Constitucional del Tribunal Supremo de Justicia, en la decisión N.º 1318 de 2011, interpretó el alcance del habeas data y fijó principios de tratamiento que conservan valor orientador.

La ausencia de una ley especial no significa que la información esté desprotegida. Significa que el deber de protección se deriva de la Constitución, de la LOPNNA cuando se trata de niños, de la LOTTT cuando se trata de datos laborales y de la Ley Especial contra los Delitos Informáticos cuando se trata de acceso indebido. El sistema adopta esos deberes como exigencia mínima y aplica los principios de minimización, finalidad, seguridad y trazabilidad. Esa adopción es una decisión de diseño, no una afirmación de cumplimiento de una norma que no existe.

### 2.4.11 Normas técnicas adoptadas

| Norma | Materia | Aplicación verificable |
|---|---|---|
| ISO/IEC 25010:2011 | Calidad de producto de software | Criterios de adecuación funcional, fiabilidad, eficiencia, seguridad, mantenibilidad, portabilidad y usabilidad |
| ISO/IEC 27001:2022 | Gestión de seguridad de la información | Control de acceso, auditoría, respaldos y tratamiento de archivos |
| IEEE 829-2008 | Documentación de pruebas | Estructura de las fichas de caso de prueba |
| IEEE 802.3 | Ethernet | Medio físico y velocidad de la red local |
| OWASP ASVS 5.0 | Verificación de seguridad de aplicaciones | Revisión de autenticación, sesión, validación de entrada y control de acceso |
| NIST SP 800-63B | Autenticación digital | Derivación PBKDF2-HMAC-SHA256 con sal aleatoria y comparación en tiempo constante |

La adopción de estas normas es voluntaria y se declara como tal. Su valor consiste en que fijan un nivel de exigencia verificable y permiten comparar el producto con un estándar reconocido, no en que otorguen una certificación que el proyecto no ha solicitado.

### 2.4.12 Trazabilidad entre la norma y el control

| Exigencia normativa | Fuente | Control implementado | Ubicación |
|---|---|---|---|
| Acceso del trabajador a sus propios datos | CRBV, art. 28 | Consulta de la ficha propia y auditoría de cambios | `src/services/empleado_service.py`, `src/utils/audit_logger.py` |
| Confidencialidad de datos personales y salariales | CRBV, arts. 48 y 60 | Acceso por rol, contraseñas derivadas, archivos restringidos | `src/utils/security.py`, `src/utils/document_manager.py` |
| Remuneración oportuna y exacta | CRBV, arts. 87, 89 y 92 | Motor de cálculo con reglas explícitas y verificadas | `src/nomina/` |
| Recibo de pago detallado | LOTTT, art. 106 | Recibo y planilla en PDF | `src/utils/pdf_generator.py` |
| Igual salario por igual trabajo | CRBV, art. 92; LOTTT, art. 109 | Parametrización única por puesto | `src/nomina/parametros.py` |
| Jornada y horas extraordinarias | LOTTT, arts. 173 y 178 | Recargos configurables por tipo de jornada | `src/nomina/horas_extra.py` |
| Prestaciones sociales | LOTTT, art. 142 | Cálculo y provisión de prestaciones | `src/nomina/prestaciones.py` |
| Idoneidad y documentación del personal docente | CRBV, art. 104; LOE | Control de vigencia documental | `src/services/documento_service.py` |
| Información oportuna para la dirección | CRBV, arts. 141 y 143 | Reportes consolidados y panel de control | `src/utils/pdf_generator.py`, `src/gui/` |
| Interés superior del niño | LOPNNA (2015) | Acceso restringido a notas y autorización por token | `src/services/nota_service.py`, `src/services/token_sesion_service.py` |
| Tecnologías libres y formatos abiertos | Ley de Infogobierno, art. 16 | Componentes abiertos y exportación a XLSX y CSV | `requirements.txt`, `src/utils/exporter.py` |
| Protección frente a acceso indebido | Ley contra Delitos Informáticos | Autenticación, autorización y auditoría | `src/services/auth_service.py`, `src/utils/audit_logger.py` |
| Constancia de los actos emitidos | Ley de Mensajes de Datos y Firmas Electrónicas | PDF uniforme con identificadores y trazabilidad | `src/utils/pdf_generator.py` |
| Seguridad y salud en el trabajo | LOPCYMAT | Registro de reposos y control de vigencia | `src/services/incidencia_service.py` |
| Gestión de seguridad de la información | ISO/IEC 27001:2022 | Controles de acceso, respaldo y retención | `src/utils/` |

### 2.4.13 Brechas jurídicas declaradas

Se identifican cuatro brechas. La primera es la ausencia de una ley general de protección de datos, ya explicada. La segunda es la firma electrónica certificada, que no se implementó. La tercera es la confirmación de la vigencia y numeración de todas las normas citadas contra la Gaceta Oficial, tarea que corresponde a la revisión previa a la presentación. La cuarta es la definición institucional de plazos de retención y de procedimientos de rectificación, que el sistema puede soportar pero no puede decidir por la institución.

## 2.5 Definición de términos

| Término | Definición operativa en este proyecto |
|---|---|
| Base de datos local | Archivo SQLite que reside en el equipo del usuario y contiene la información completa de la institución. |
| Nodo central | Servicio HTTP que actúa como único escritor de la copia compartida y como punto de encuentro entre puestos. |
| Puesto | Equipo de la institución que ejecuta la aplicación y sincroniza con el nodo central. |
| Sincronización híbrida | Combinación de un ciclo automático en segundo plano y de una ejecución manual solicitada por el usuario. |
| Journal | Tabla que registra las operaciones pendientes de replicación en la misma transacción que el dato. |
| Outbox | Patrón de diseño que escribe la operación y el dato en una sola transacción para su envío posterior. |
| UUID | Identificador único universal que permite reconocer una fila entre puestos sin coordinación. |
| Clave natural | Atributo del dominio que identifica un registro de forma legible, como la cédula o el número de contrato. |
| Mezcla por campo | Resolución de conflictos que decide cada columna por separado y conserva las ediciones sobre columnas distintas. |
| Convergencia | Propiedad por la cual dos réplicas alcanzan el mismo estado cuando han recibido las mismas operaciones. |
| Latencia | Tiempo transcurrido entre la solicitud y la respuesta completa. |
| Caudal | Número de operaciones procesadas por unidad de tiempo. |
| Tasa de éxito de sincronización | Proporción de operaciones registradas que el nodo central confirma. |
| SUS | Escala de usabilidad del sistema, cuestionario de diez ítems con puntuación de 0 a 100. |
| Proyecto factible | Modalidad de investigación aplicada que diagnostica un problema, propone una solución y evalúa su viabilidad. |

## 2.6 Variables y plan de medición

### 2.6.1 Clasificación de las variables

La variable independiente es la implementación del sistema, que se introduce una sola vez y se evalúa en dos momentos. Las variables dependientes son el tiempo de proceso, la latencia, el caudal, la tasa de error, la tasa de éxito de sincronización, el consumo de recursos, la exactitud de la información y la usabilidad. Las variables de control son el equipo utilizado, la topología de red, el tamaño de los lotes, el número de usuarios concurrentes y la versión del sistema. Las variables extrañas que se reconocen son la curva de aprendizaje del usuario, la carga administrativa del periodo y las condiciones de la red institucional.

### 2.6.2 Matriz de operacionalización

| Variable | Dimensión | Indicador | Fórmula o unidad | Instrumento | Estadístico |
|---|---|---|---|---|---|
| Tiempo de registro | Eficiencia | Segundos por registro | t_fin − t_inicio | Ficha de observación | Media, mediana, DE, IC 95 % |
| Tiempo de búsqueda | Eficiencia | Segundos por expediente | t_fin − t_inicio | Ficha de observación | Media, mediana, DE |
| Tiempo de consolidación | Eficiencia | Minutos por boletín | t_fin − t_inicio | Ficha de observación | Media, mediana, DE |
| Tasa de error de transcripción | Calidad | Porcentaje | (notas corregidas / notas transcritas) × 100 | Revisión documental | Proporción, chi-cuadrado |
| Latencia | Rendimiento | Milisegundos | t_respuesta − t_solicitud | Ficha de métricas | p50, p95, p99, media, DE |
| Caudal | Rendimiento | Operaciones por segundo | operaciones / segundos | Ficha de métricas | Media, DE |
| Tasa de éxito de sincronización | Fiabilidad | Porcentaje | (ops confirmadas / ops registradas) × 100 | Journal y nodo central | Proporción, IC exacto |
| Memoria residente | Eficiencia | Megabytes | Lectura del monitor | Ficha de métricas | Media, máximo |
| CPU | Eficiencia | Porcentaje | Lectura del monitor | Ficha de métricas | Media, máximo |
| Usabilidad | Usabilidad | Puntos SUS | Suma transformada × 2,5 | Cuestionario SUS | Media, DE, IC 95 %, t o Wilcoxon |

### 2.6.3 Regla de redondeo y reporte

Los tiempos se reportan en milisegundos con un decimal para la latencia y en segundos con dos decimales para las tareas administrativas. Los porcentajes se reportan con dos decimales. Las puntuaciones SUS se reportan con un decimal. Toda tabla de resultados incluye el tamaño de la muestra, la medida de tendencia central, la medida de dispersión y el intervalo de confianza. La media sola no se considera un resultado suficiente.

## 2.7 Metodología

### 2.7.1 Enfoque cuantitativo

El enfoque cuantitativo se caracteriza por la formulación de hipótesis que se contrastan con datos numéricos, por la definición operacional de las variables antes de la recolección y por el uso de procedimientos estadísticos para estimar la magnitud y la incertidumbre de los resultados (Hernández-Sampieri y Mendoza, 2018). El proyecto cumple las tres condiciones.

La primera condición se satisface con las hipótesis del apartado 1.6, que expresan relaciones entre variables con umbrales declarados. La segunda se satisface con la matriz de operacionalización del apartado 2.6.2, que asigna a cada variable una fórmula, un instrumento y un estadístico. La tercera se satisface con el plan de análisis del apartado 2.7.8, que se fijó antes de la recolección y que incluye pruebas de normalidad, contrastes no paramétricos cuando corresponden y medidas de tamaño del efecto.

El enfoque cuantitativo no implica desinterés por el contexto. Implica que el contexto se documenta para interpretar los números, no para sustituirlos. Cuando una medición resulte anómala, la explicación se buscará en el registro de observación y no en una impresión general.

### 2.7.2 Tipo y modalidad de investigación

La investigación es aplicada porque resuelve un problema práctico con conocimiento disponible, y tecnológica porque su resultado principal es un artefacto de software. Se adopta la modalidad de proyecto factible en el sentido del manual de la UPEL (2016): diagnóstico, planteamiento de la propuesta, construcción y evaluación de la viabilidad. El proyecto agrega una etapa de evaluación empírica que el manual no exige de forma explícita, pero que la naturaleza cuantitativa del estudio requiere.

La investigación no es experimental en sentido estricto. No se manipula una variable con grupo de control aleatorizado ni se aísla el efecto de todas las variables extrañas. Es un estudio preexperimental de un solo grupo con mediciones antes y después, complementado con un diseño factorial para las pruebas de rendimiento, en el que las condiciones sí se controlan porque se ejecutan sobre el mismo equipo y la misma red.

### 2.7.3 Diseño de la investigación

El diseño comprende tres componentes.

**Componente descriptivo transversal.** Se aplica en la Fase I para caracterizar la situación inicial: procesos, tiempos, instrumentos, volumen de información, número de usuarios y condiciones de la red. No manipula variables y su propósito es establecer la línea base.

**Componente preexperimental pretest-postest.** Se aplica en la Fase IV sobre las tareas administrativas seleccionadas. Los mismos participantes ejecutan las mismas tareas antes y después de la implementación, con los mismos instrumentos. La comparación se realiza con pruebas de muestras relacionadas. La ausencia de grupo de control se declara como amenaza a la validez interna y se mitiga con la constancia de que las condiciones de la tarea no cambiaron.

**Componente factorial para el rendimiento.** Se aplica en la Fase IV sobre el subsistema de sincronización. Los factores son el tamaño del lote, con cuatro niveles (1, 10, 50 y 100 operaciones), y el número de clientes concurrentes, con tres niveles (1, 4 y 8). El diseño es factorial completo de 4 × 3, con treinta repeticiones por celda para el caudal y trescientas peticiones por condición para la caracterización de la latencia. La variable de respuesta es la latencia; se registran además el caudal y la tasa de error. La elección de treinta repeticiones se apoya en el teorema central del límite; las trescientas peticiones permiten estimar el percentil 99 con estabilidad.

```text
                     Clientes concurrentes
                1            4            8
          +-----------+-----------+-----------+
 Lote   1 |  30 reps  |  30 reps  |  30 reps  |
          +-----------+-----------+-----------+
       10 |  30 reps  |  30 reps  |  30 reps  |
          +-----------+-----------+-----------+
       50 |  30 reps  |  30 reps  |  30 reps  |
          +-----------+-----------+-----------+
      100 |  30 reps  |  30 reps  |  30 reps  |
          +-----------+-----------+-----------+
```

El orden de ejecución se aleatoriza dentro de cada celda para evitar que el calentamiento del sistema o la caché del sistema operativo favorezcan siempre la primera condición. Antes de cada celda se ejecuta una ronda de descarte de cinco repeticiones, cuyos valores no se registran.

### 2.7.4 Población y muestra

**Población.** El personal administrativo y docente de la institución que participa en los procesos de registro de personal, emisión de documentos o registro de calificaciones. La población se delimita al inicio de la Fase I con la plantilla de la institución y se reporta su tamaño como N.

**Muestra para las tareas administrativas.** Se calcula con la fórmula para población finita:

```text
n = (N · Z² · p · q) / (e² · (N − 1) + Z² · p · q)

donde Z = 1,96 para un nivel de confianza del 95 %,
p = q = 0,5 para máxima varianza,
e = 0,05 para un error máximo del 5 %.
```

Para una población de 40 personas, la fórmula produce 36,3, que se redondea a 37. Si la población fuese de 25, produciría 23,5, que se redondea a 24. El valor definitivo se calcula en la Fase I con el N real y se reporta en el informe. Cuando el cálculo arroje un valor superior al número de personas disponibles, se trabaja con la población completa y se declara como censo.

**Muestra para usabilidad.** Se seleccionan entre 20 y 30 usuarios por muestreo intencional, cubriendo los perfiles de secretaría, dirección, coordinación académica y docencia. El tamaño se justifica por la necesidad de estimar una media con un intervalo de confianza aceptable y por la literatura sobre SUS, que reporta estabilidad con muestras de esa magnitud (Lewis, 2018; Sauro y Lewis, 2016). Para la prueba formativa de tareas se aplica el criterio de saturación de problemas, que suele alcanzarse con cinco a ocho participantes por perfil (Nielsen, 2012).

**Muestra para rendimiento.** No se selecciona una muestra de personas. Se ejecuta la matriz completa de condiciones, con treinta repeticiones por celda, y se reporta el número total de mediciones.

### 2.7.5 Fases metodológicas

#### Fase I. Diagnóstico

**Duración:** semanas 1 a 6.
**Objetivo asociado:** OE1.
**Actividades:** revisión documental; observación no participante en secretaría y coordinación; entrevistas semiestructuradas a dirección, secretaría y coordinación; grupo focal con docentes; árbol de problemas; matriz de priorización; medición de la línea base.
**Productos:** informe de diagnóstico, catálogo de requerimientos jerarquizados, línea base cuantitativa, acta de validación con los participantes.
**Criterio de cierre:** los requerimientos fueron validados por la institución y la línea base quedó registrada con el instrumento del anexo.

#### Fase II. Diseño

**Duración:** semanas 7 a 12.
**Objetivo asociado:** OE2.
**Actividades:** definición de la arquitectura de red; diseño del modelo entidad-relación; normalización; diseño del journal y del protocolo de sincronización; diseño de las plantillas de PDF; diseño de la interfaz y de la matriz de permisos; revisión de consistencia entre requerimientos y componentes.
**Productos:** documento de arquitectura, modelo de datos, diccionario de datos, especificación del protocolo, prototipos de pantalla, matriz de trazabilidad.
**Criterio de cierre:** cada requerimiento prioritario tiene un componente asignado y una prueba prevista.

#### Fase III. Ejecución

**Duración:** semanas 13 a 26.
**Objetivo asociado:** OE3.
**Actividades:** implementación por iteraciones; construcción de los módulos de personal, documentos, incidencias, contratos, nómina, estudiantes y calificaciones; implementación del journal, del motor de mezcla y del nodo central; integración de la generación de PDF; pruebas unitarias, de integración y de interfaz; corrección de defectos.
**Productos:** producto ejecutable, suite de pruebas, manual de instalación, guía de usuario.
**Criterio de cierre:** la suite automatizada se ejecuta sin fallos y el producto se instala en un equipo de la institución.

#### Fase IV. Evaluación

**Duración:** semanas 27 a 34.
**Objetivo asociado:** OE4.
**Actividades:** ejecución del banco de pruebas de latencia y concurrencia; prueba de desconexión controlada; medición de tiempos administrativos; aplicación del cuestionario SUS; análisis estadístico; contraste de hipótesis; redacción de resultados y conclusiones.
**Productos:** tablas de resultados, informe de evaluación, conjunto de datos anonimizado, conclusiones y recomendaciones.
**Criterio de cierre:** todas las hipótesis se reportan como aceptadas o rechazadas con su estadístico y su intervalo de confianza.

### 2.7.6 Técnicas e instrumentos

| Instrumento | Qué mide | Estructura | Momento de aplicación |
|---|---|---|---|
| Ficha de observación técnica | Tiempos y pasos de una tarea administrativa | Encabezado, tarea, cronómetro, observaciones | Fase I y Fase IV |
| Ficha de registro de métricas | Latencia, caudal, errores y recursos | Identificación de la corrida, condición, repetición, valores | Fase IV |
| Lista de cotejo de requerimientos | Cumplimiento funcional | Requerimiento, criterio, evidencia, estado | Fase II y Fase III |
| Cuestionario SUS | Usabilidad percibida | Diez ítems, escala de 1 a 5 | Fase IV |
| Guion de pruebas de tareas | Éxito y errores por tarea | Tarea, criterio de éxito, tiempo límite, registro | Fase IV |
| Matriz de trazabilidad | Correspondencia objetivo-requerimiento-prueba | Cuatro columnas y evidencia | Fase II a Fase IV |
| Registro de desconexión | Tasa de éxito ante cortes | Hora, duración del corte, operaciones, resultado | Fase IV |

Los instrumentos se reproducen en los anexos del compendio. La ficha de observación técnica se validó con una prueba piloto en la propia institución antes de la Fase I, con el fin de ajustar la redacción y estimar la duración de cada registro. El cuestionario SUS se aplica en su versión traducida al español y se verifica la comprensión de los ítems en la sesión de prueba, sin modificar su contenido, porque una modificación invalidaría la comparación con las referencias acumuladas.

### 2.7.7 Procedimiento de medición

#### 2.7.7.1 Latencia y caudal

El banco de pruebas se ejecuta sobre la red de la institución, con el nodo central en el equipo designado y el cliente en un puesto de la misma red. Antes de la corrida se verifica que no haya procesos ajenos consumiendo ancho de banda y que la hora de ambos equipos esté sincronizada.

El procedimiento consta de seis pasos. Primero, se inicia el nodo central y se espera a que responda la ruta de diagnóstico. Segundo, se ejecuta una ronda de calentamiento de cincuenta peticiones que no se registra. Tercero, se ejecutan trescientas peticiones de diagnóstico y se registra el tiempo de cada una con un reloj monotónico. Cuarto, se ejecutan las combinaciones de tamaño de lote y concurrencia de la matriz factorial. Quinto, se registra el consumo de memoria y CPU del proceso del nodo central cada segundo durante la corrida. Sexto, se exportan los registros a CSV y se calculan los estadísticos con el guion de análisis.

La latencia se calcula con la diferencia entre el instante anterior al envío y el instante posterior a la recepción completa del cuerpo. Se usa un reloj monotónico para evitar que un ajuste de hora del sistema altere la medición. El caudal se calcula dividiendo el número de operaciones confirmadas entre la duración total de la celda, excluido el calentamiento.

#### 2.7.7.2 Tasa de éxito ante desconexión

La prueba se ejecuta en diez ciclos. Cada ciclo comprende cinco pasos. Primero, se sincronizan ambos puestos y se verifica que el journal esté vacío. Segundo, se interrumpe el servicio del nodo central, sea deteniendo el proceso o bloqueando el puerto, y se confirma que el puesto no puede alcanzarlo. Tercero, se registran doscientas operaciones por puesto con una mezcla declarada de altas, ediciones y cambios de estado en personal, notas y documentos. Cuarto, se verifica que las doscientas operaciones se hayan confirmado localmente y que el journal tenga exactamente esas operaciones pendientes. Quinto, se restablece el servicio y se ejecutan ciclos de sincronización hasta que el journal quede vacío.

La tasa de éxito se calcula con la fórmula:

```text
TE = (operaciones confirmadas por el nodo central / operaciones registradas) × 100
```

Se considera fallo toda operación que, tras veinte ciclos de sincronización, no haya sido confirmada. También se considera fallo la duplicación de una fila o la divergencia de un campo respecto del valor esperado. La verificación de convergencia se realiza con una consulta de comparación entre la base del puesto y la base central, campo por campo, sobre las filas afectadas.

#### 2.7.7.3 Tiempos administrativos

Cada participante ejecuta la tarea asignada tres veces: una de práctica, cuyas mediciones se descartan, y dos que se registran. El observador cronometra desde la indicación de inicio hasta la confirmación del resultado por parte del participante. No se ayuda al participante durante la ejecución, salvo que se trate de un bloqueo que impida continuar, circunstancia que se anota como incidencia. La tarea se ejecuta en el mismo equipo y con el mismo conjunto de datos antes y después de la implementación.

#### 2.7.7.4 Usabilidad

La sesión de usabilidad se realiza en tres partes. En la primera se explica el propósito y se firma el consentimiento. En la segunda, el participante ejecuta seis tareas representativas mientras verbaliza su proceso. En la tercera, responde el cuestionario SUS y tres preguntas abiertas de cierre. El observador registra el tiempo por tarea, el número de errores y el tipo de error, sin intervenir en la ejecución.

La puntuación SUS se calcula por participante y luego se agrega. Para cada ítem impar se resta uno a la respuesta; para cada ítem par se resta la respuesta a cinco; se suman los diez resultados y se multiplica por 2,5. El resultado agregado se reporta con media, desviación estándar e intervalo de confianza al 95 %. Se contrasta la hipótesis de que la media sea igual o superior a 70 con una prueba t de una muestra o con la prueba de rangos con signo de Wilcoxon si no se verifica la normalidad.

### 2.7.8 Procesamiento y análisis de datos

El análisis se organiza en cuatro etapas. La primera es la depuración: se eliminan registros incompletos, se documenta el motivo de cada eliminación y se verifica que no superen el 5 % del total. La segunda es el análisis descriptivo: media, mediana, desviación estándar, mínimo, máximo, percentiles 95 y 99, y distribución de frecuencias. La tercera es la verificación de supuestos: prueba de Shapiro-Wilk para normalidad y prueba de Levene para homogeneidad de varianzas. La cuarta es el contraste de hipótesis.

| Objetivo del contraste | Prueba | Supuesto | Alternativa |
|---|---|---|---|
| Comparar tiempos antes y después | t de muestras relacionadas | Diferencias normales | Wilcoxon |
| Comparar proporciones de error | Chi-cuadrado de independencia | Frecuencias esperadas ≥ 5 | Prueba exacta de Fisher |
| Comparar latencia entre condiciones | ANOVA de un factor | Normalidad y homocedasticidad | Kruskal-Wallis |
| Comparar dos condiciones de carga | t de muestras independientes | Normalidad e igualdad de varianzas | Mann-Whitney |
| Estimar una proporción | Intervalo de Wilson | Muestra grande | Intervalo exacto de Clopper-Pearson |
| Contrastar una media contra un umbral | t de una muestra | Normalidad | Wilcoxon |

El nivel de significancia se fija en 0,05. Cuando se realizan comparaciones múltiples sobre el mismo conjunto de datos, se aplica la corrección de Holm para controlar la tasa de error por familia. La significancia estadística se reporta junto con el tamaño del efecto: d de Cohen para las comparaciones de medias y r de Rosenthal para las pruebas no paramétricas. Un resultado significativo con tamaño del efecto pequeño se interpreta como una diferencia real pero de escasa relevancia práctica, y así se declara.

El análisis se ejecuta con Python y sus bibliotecas de cálculo, y los guiones se conservan junto con los datos anonimizados para permitir la replicación. Los datos crudos no se publican: se publica la matriz agregada y el diccionario de variables.

### 2.7.9 Validez y confiabilidad

La validez de contenido se aseguró con la revisión de los instrumentos por el tutor académico y por un docente de la especialidad, y con la prueba piloto de la ficha de observación. La validez de constructo de la usabilidad se apoya en la escala SUS, que cuenta con décadas de validación acumulada (Lewis, 2018). La validez interna se sostiene en la constancia de tareas, instrumentos y participantes entre las dos mediciones, y se ve amenazada por la ausencia de grupo de control, el efecto de aprendizaje y la maduración del usuario.

La validez externa es limitada por el número de instituciones. El estudio describe el comportamiento del sistema en un contexto y no pretende extrapolarlo sin reservas. La confiabilidad se sostiene en la repetición de las mediciones, en la documentación de las condiciones y en la conservación de los registros. Para las pruebas de rendimiento, la confiabilidad se estima con la desviación estándar entre repeticiones y con el coeficiente de variación; una celda con coeficiente superior al 20 % se repite.

### 2.7.10 Aspectos éticos

La participación es voluntaria y se formaliza con un consentimiento informado que explica el propósito, los procedimientos, la duración, los riesgos y el derecho a retirarse sin consecuencia. Los datos se anonimizan antes del análisis: los nombres se sustituyen por códigos y las cédulas se eliminan de la matriz de trabajo. Los registros crudos se conservan en un equipo con acceso restringido y se destruyen al concluir el periodo de retención acordado con la institución.

El tratamiento de datos de niños exige una precaución adicional. Las calificaciones se analizan de forma agregada y nunca se reporta la nota de un estudiante identificable. Los datos de representantes no se incluyen en la matriz de investigación. La institución autoriza por escrito el acceso a la información y designa un responsable de custodia.

El investigador declara no tener vínculo comercial con las tecnologías empleadas ni con la institución participante distinto del académico. El software se distribuye con licencia MIT y no genera regalías.

### 2.7.11 Cronograma

| Fase | Semanas | Actividades principales | Producto |
|---|---|---|---|
| I. Diagnóstico | 1 a 6 | Observación, entrevistas, grupo focal, línea base | Informe de diagnóstico |
| II. Diseño | 7 a 12 | Arquitectura, modelo de datos, protocolo, plantillas | Documento de diseño |
| III. Ejecución | 13 a 26 | Construcción, integración, pruebas, corrección | Producto ejecutable |
| IV. Evaluación | 27 a 34 | Banco de pruebas, desconexión, SUS, análisis | Informe de resultados |
| Contingencia | 35 a 36 | Repetición de mediciones y ajustes | Informe final |

## 2.8 Conclusiones del capítulo

El marco teórico permitió establecer que el proyecto no inventa un modelo de sincronización, sino que aplica principios documentados de software local-first y de replicación con convergencia eventual. La diferencia con la literatura está en el contexto y en la combinación: una institución educativa, una red local sin servidor dedicado y un personal sin formación técnica. Esa combinación es la que justifica el estudio y la que permite aportar un caso verificable.

El marco legal se construyó sobre el ordenamiento venezolano y se completó con las normas técnicas adoptadas de forma voluntaria. La tabla de trazabilidad obligó a que cada exigencia invocada tuviera un control concreto en el código, y ese ejercicio reveló una brecha que el documento declara: la ausencia de una ley general de protección de datos personales. El sistema aplica los principios constitucionales y de la LOPNNA, pero no puede atribuirse el cumplimiento de una norma que no existe.

La metodología quedó definida como cuantitativa, aplicada, tecnológica y de proyecto factible, con un diseño que combina un componente descriptivo, uno preexperimental y uno factorial. Las variables, los instrumentos, las fases y el plan de análisis se fijaron antes de la recolección. Esa anticipación es la condición que permite afirmar, en la Fase IV, que los resultados no fueron ajustados para confirmar las hipótesis.

## 2.9 Referencias

Anderson, L. W., y Krathwohl, D. R. (Eds.). (2001). *A taxonomy for learning, teaching, and assessing: A revision of Bloom's taxonomy of educational objectives*. Longman. [Fuente primaria de la taxonomía, anterior a la ventana.]

Benavides, L. M. C., Tamayo Arias, J. A., Arango Serna, M. D., Branch Bedoya, J. W., y Burgos, D. (2020). Digital transformation in higher education institutions: A systematic literature review. *Sensors, 20*(11), 3291. https://doi.org/10.3390/s20113291

Brooke, J. (1996). SUS: A quick and dirty usability scale. En P. W. Jordan, B. Thomas, B. A. Weerdmeester y I. L. McClelland (Eds.), *Usability evaluation in industry* (pp. 189-194). Taylor & Francis. [Fuente primaria de la escala SUS.]

Date, C. J. (2019). *Database design and relational theory: Normal forms and all that jazz* (2.ª ed.). Apress.

DLA Piper. (2025). *Data protection laws of the world: Venezuela*. https://www.dlapiperdataprotection.com/

Hernández-Sampieri, R., y Mendoza, C. P. (2018). *Metodología de la investigación: Las rutas cuantitativa, cualitativa y mixta*. McGraw-Hill.

International Association of Privacy Professionals. (2025, 19 de agosto). *Venezuela data breach highlights scattered privacy regulation*. https://iapp.org/news/a/venezuela-data-breach-highlights-scattered-privacy-regulation

Institute of Electrical and Electronics Engineers. (2008). *IEEE 829-2008. IEEE standard for software and system test documentation*. IEEE.

Institute of Electrical and Electronics Engineers. (2022). *IEEE 802.3-2022. IEEE standard for Ethernet*. IEEE.

International Organization for Standardization. (2011). *ISO/IEC 25010:2011. Systems and software engineering. Systems and software quality requirements and evaluation (SQuaRE). System and software quality models*.

International Organization for Standardization. (2022). *ISO/IEC 27001:2022. Information security, cybersecurity and privacy protection. Information security management systems. Requirements*.

Kleppmann, M. (2017). *Designing data-intensive applications: The big ideas behind reliable, scalable, and maintainable systems*. O'Reilly Media.

Kleppmann, M., y Beresford, A. R. (2017). A conflict-free replicated JSON datatype. *IEEE Transactions on Parallel and Distributed Systems, 28*(10), 2733-2746. https://doi.org/10.1109/TPDS.2017.2697382

Kleppmann, M., Wiggins, A., van Hardenberg, P., y McGranaghan, M. (2019). Local-first software: You own your data, in spite of the cloud. En *Proceedings of the 2019 ACM SIGPLAN International Symposium on New Ideas, New Paradigms, and Reflections on Programming and Software* (pp. 154-178). ACM. https://doi.org/10.1145/3359591.3359737

Krathwohl, D. R. (2002). A revision of Bloom's taxonomy: An overview. *Theory into Practice, 41*(4), 212-218. https://doi.org/10.1207/s15430421tip4104_2

Lewis, J. R. (2018). The System Usability Scale: Past, present, and future. *International Journal of Human-Computer Interaction, 34*(7), 577-590. https://doi.org/10.1080/10447318.2018.1455307

Martin, R. C. (2017). *Clean architecture: A craftsman's guide to software structure and design*. Prentice Hall.

National Institute of Standards and Technology. (2017). *Digital identity guidelines: Authentication and lifecycle management* (NIST Special Publication 800-63B). https://doi.org/10.6028/NIST.SP.800-63b

Nielsen, J. (2012). *How many test users in a usability study?* Nielsen Norman Group. https://www.nngroup.com/articles/how-many-test-users/

OWASP Foundation. (2025). *OWASP Application Security Verification Standard 5.0*. https://owasp.org/www-project-application-security-verification-standard/

Ralph, P., Baltes, S., Bianculli, D., D'Amorim, M., Ernst, N., Fairbanks, J., ... y Wiese, I. (2020). *Empirical standards for software engineering research*. arXiv. https://arxiv.org/abs/2010.03525

Richardson, C. (2018). *Microservices patterns: With examples in Java*. Manning Publications.

Sauro, J., y Lewis, J. R. (2016). *Quantifying the user experience: Practical statistics for user research* (2.ª ed.). Morgan Kaufmann.

Shapiro, M., Preguiça, N., Baquero, C., y Zawirski, M. (2011). Conflict-free replicated data types. En *Stabilization, Safety, and Security of Distributed Systems* (pp. 386-400). Springer. [Contraste teórico, anterior a la ventana.]

Sommerville, I. (2016). *Software engineering* (10.ª ed.). Pearson.

SQLite Consortium. (2024). *Write-ahead logging*. https://www.sqlite.org/wal.html

Universidad Pedagógica Experimental Libertador. (2016). *Manual de trabajos de grado de especialización y maestría y tesis doctorales* (5.ª ed.). UPEL.

Viotti, P., y Vukolić, M. (2016). Consistency in non-transactional distributed storage systems. *ACM Computing Surveys, 49*(1), 1-34. https://doi.org/10.1145/2926965

Wohlin, C., Runeson, P., Höst, M., Ohlsson, M. C., Regnell, B., y Wesslén, A. (2024). *Experimentation in software engineering* (2.ª ed.). Springer. https://doi.org/10.1007/978-3-662-69306-3

### 2.9.1 Normativa citada

Asamblea Nacional Constituyente. (1999). *Constitución de la República Bolivariana de Venezuela*. Gaceta Oficial N.º 36.860.

Asamblea Nacional. (2001). *Ley Especial contra los Delitos Informáticos*. Gaceta Oficial N.º 37.313.

Asamblea Nacional. (2001). *Decreto N.º 1.204 con Rango y Fuerza de Ley de Mensajes de Datos y Firmas Electrónicas*. Gaceta Oficial N.º 37.148.

Asamblea Nacional. (2005). *Ley Orgánica de Prevención, Condiciones y Medio Ambiente de Trabajo*. Gaceta Oficial N.º 38.236.

Asamblea Nacional. (2009). *Ley Orgánica de Educación*. Gaceta Oficial Extraordinaria N.º 5.929.

Asamblea Nacional. (2012). *Decreto N.º 8.938, Ley Orgánica del Trabajo, los Trabajadores y las Trabajadoras*. Gaceta Oficial Extraordinaria N.º 6.076.

Asamblea Nacional. (2013). *Ley de Infogobierno*. Gaceta Oficial N.º 40.274.

Asamblea Nacional. (2014). *Decreto N.º 1.411, Ley Orgánica de Ciencia, Tecnología e Innovación*. Gaceta Oficial Extraordinaria N.º 6.151.

Asamblea Nacional. (2015). *Ley de Reforma Parcial de la Ley Orgánica para la Protección de Niños, Niñas y Adolescentes*. Gaceta Oficial Extraordinaria N.º 6.185.

Asamblea Nacional. (2022). *Ley Orgánica de Reforma Parcial de la Ley Orgánica de Ciencia, Tecnología e Innovación*. Gaceta Oficial Extraordinaria N.º 6.693.

Tribunal Supremo de Justicia, Sala Constitucional. (2011). *Decisión N.º 1318*. https://historico.tsj.gob.ve/
