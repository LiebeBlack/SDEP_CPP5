# CAPÍTULO V: CONCLUSIONES Y RECOMENDACIONES

## 5.1 INTRODUCCIÓN

El presente capítulo expone las conclusiones que se desprenden de la investigación y las recomendaciones que de ella derivan. Se presentan, en primer lugar, las conclusiones generales referidas al desarrollo del sistema, a su arquitectura, a la metodología empleada y a las condiciones de adopción; en segundo lugar, las conclusiones específicas vinculadas a cada objetivo planteado; y, finalmente, las recomendaciones dirigidas a las instituciones educativas, a los desarrolladores e investigadores y a la comunidad académica, junto con las limitaciones que delimitan el alcance de lo afirmado.

Conviene recordar la distinción que atraviesa todo el informe y que condiciona la lectura de este capítulo. Las conclusiones sobre el producto construido se sustentan en evidencia verificable sobre el repositorio: la arquitectura implementada, los módulos operativos, la matriz de acceso por rol, las diez tablas del esquema y las 453 funciones de prueba declaradas en la versión 2.82. Las conclusiones sobre el impacto administrativo, en cambio, permanecen condicionadas a la evidencia del piloto, de modo que aquí se formulan como expectativas fundamentadas y no como hallazgos consumados. Sostener esa distinción no debilita el trabajo; por el contrario, es la condición que permite que las afirmaciones resistan la verificación.

## 5.2 CONCLUSIONES GENERALES

### 5.2.1 Sobre el Desarrollo del Sistema

La primera conclusión es que resulta viable construir un sistema integral de gestión de personal y nómina con tecnologías de código abierto, sin sacrificar por ello estándares profesionales de organización, seguridad y verificabilidad. El sistema efectivamente desarrollado se apoya en Python, SQLAlchemy, CustomTkinter, ReportLab y OpenPyXL; comprende 27 534 líneas de código organizadas en capas; implementa diez módulos funcionales con acceso diferenciado por rol; y produce documentos oficiales en formato PDF, además de respaldos, auditoría y exportaciones en formatos abiertos. De ello se sigue una implicación relevante para el sector: la calidad técnica no depende del poder de compra de la institución, sino de la disciplina de diseño y de la elección adecuada de tecnologías. Allí donde una licencia comercial resulta prohibitiva, la sustitución por componentes abiertos y por un diseño riguroso es viable y verificable.

### 5.2.2 Sobre la Eficiencia Administrativa

La segunda conclusión atiende al objeto central de la investigación. El sistema automatiza los procesos que el diagnóstico identificó como críticos —registro y actualización del personal, control documental con vencimientos, gestión de incidencias, cálculo de nómina y emisión de documentos—, de modo que las tareas manuales repetitivas y los puntos donde se concentraban los mayores riesgos de error quedan cubiertos por reglas explícitas y verificadas. La exactitud de los cálculos de nómina, deducciones, horas extra y prestaciones se comprueba de forma sistemática en la suite automatizada; ahora bien, la magnitud de la mejora en tiempos de procesamiento y en tasas de error constituye una medición empírica que se registrará en el apartado 4.5 con los datos del piloto y se contrastará con las pruebas estadísticas definidas en el apartado 3.6.1.2. En consecuencia, la conclusión que puede sostenerse hoy es la de la eliminación estructural de las causas del error —cálculo manual, transcripción repetida, ausencia de control de vencimientos—; la cuantificación de su efecto pertenece al capítulo de resultados empíricos.

### 5.2.3 Sobre la Metodología de Desarrollo

La tercera conclusión se refiere a la metodología. La combinación de desarrollo iterativo con investigación-acción resultó adecuada para un proyecto de tecnología social, porque permitió incorporar conocimiento del contexto sin renunciar al rigor técnico. La evidencia de esa adecuación es la propia trayectoria del sistema: entre la versión 2.79 y la 2.82 se incorporaron cuatro módulos funcionales —asistencia, contratos, préstamos y alertas—, un motor de nómina con reglas de seguridad social e impuesto sobre la renta, y 130 funciones de prueba adicionales, sin que fuera necesario refundar las capas preexistentes. Esa capacidad de crecer por agregación, y no por reconstrucción, es el efecto más tangible de haber mantenido ciclos cortos con verificación permanente. La satisfacción de los usuarios con la metodología empleada se medirá con el cuestionario del Anexo 2 durante el piloto.

### 5.2.4 Sobre la Arquitectura del Sistema

La cuarta conclusión confirma el valor del diseño arquitectónico adoptado. La separación en capas con los patrones Repository y Service, complementada con el aislamiento del dominio de cálculo de nómina, produjo tres efectos concretos: las reglas de negocio pudieron probarse con independencia de la interfaz; la incorporación de funcionalidades nuevas no obligó a refactorizaciones estructurales; y la sustitución de componentes —por ejemplo, la ampliación del motor de cálculo— quedó contenida en un solo paquete. La prueba más exigente de una arquitectura es su comportamiento ante el cambio, y en este caso el cambio fue considerable y el costo de adaptación resultó acotado.

### 5.2.5 Sobre la Usabilidad y la Adopción

La quinta conclusión sostiene que la adopción de un sistema de gestión por personal con competencias digitales heterogéneas depende de tres condiciones simultáneas: una interfaz que no exija conocimiento informático previo, una capacitación segmentada por perfil y una documentación de consulta disponible en el puesto de trabajo. El diseño del sistema atendió la primera condición con formularios guiados, atajos de teclado, menús contextuales y apariencia configurable; la segunda y la tercera se abordarán con el protocolo del Anexo 3 y la guía de usuario. La comprobación empírica de estas condiciones —tasa de adopción, tiempo de aprendizaje y satisfacción con la capacitación— corresponde al piloto.

## 5.3 CONCLUSIONES ESPECÍFICAS POR OBJETIVO

### 5.3.1 Objetivo Específico 1: Análisis de Requerimientos

El análisis de los procesos actuales de gestión de personal permitió identificar requerimientos que difícilmente habrían surgido de una especificación teórica. Tres hallazgos resultaron determinantes. El primero es la prioridad que los usuarios asignan a la simplicidad por encima de la sofisticación: un módulo adicional se percibe como valor únicamente cuando su uso es evidente. El segundo es la importancia de integrar el sistema a los procesos ya existentes en lugar de imponer flujos nuevos, criterio que orientó el diseño de la configuración institucional. El tercero es el peso de la continuidad del servicio: la institución necesita operar aunque el responsable habitual no esté presente, lo que justifica la auditoría, los respaldos y la documentación. De estos hallazgos se desprende la recomendación de invertir tiempo significativo en el trabajo de campo previo, aun cuando retrase el inicio de la codificación.

### 5.3.2 Objetivo Específico 2: Diseño de la Arquitectura

El diseño arquitectónico cumplió su propósito en los términos expuestos en el apartado 5.2.4: separación clara de responsabilidades, verificabilidad de cada capa y capacidad de evolución sin reconstrucción. La validación de este objetivo descansa en hechos comprobables: la suite de 453 funciones de prueba se apoya en esa separación, y la incorporación sucesiva de módulos no alteró la estructura de capas. La recomendación derivada es que los proyectos de complejidad media reserven una fase explícita de diseño antes de codificar, pues el costo de esa fase es menor que el de corregir una estructura inadecuada una vez que el sistema está en uso.

### 5.3.3 Objetivo Específico 3: Implementación de los Módulos

La implementación modular permitió entregar funcionalidad utilizable de forma progresiva y validar cada módulo antes de avanzar hacia el siguiente. Los módulos de empleados, documentos, incidencias, asistencia, contratos, préstamos, nómina, alertas y configuración operan de manera integrada y comparten un mismo esquema de seguridad y auditoría. La consecuencia práctica de este enfoque es que la institución puede comenzar a trabajar con los procesos esenciales mientras se completa el resto, lo que reduce el riesgo de una implantación simultánea de todo el sistema.

### 5.3.4 Objetivo Específico 4: Reportes y Documentos Oficiales

Las funcionalidades de reporte y de generación documental se materializaron en catorce tipos de documentos PDF, entre los que figuran constancias de trabajo y de ingresos, recibos de pago, fichas de empleado, planillas de nómina, liquidaciones y reportes de incidencias, vencimientos, asistencia, contratos y préstamos. Su valor reside en que sustituyen una elaboración manual lenta y sujeta a variación por una generación automática y uniforme, condición apreciable tanto para la gestión interna como para la atención al personal. La valoración que los usuarios asignen a esta funcionalidad se registrará durante el piloto.

### 5.3.5 Objetivo Específico 5: Validación con Usuarios

La validación con usuarios reales orientó decisiones de diseño concretas antes de la implementación definitiva, entre ellas la agrupación de campos en formularios temáticos, la visibilidad de las opciones de exportación y la claridad del flujo de aprobación de incidencias. El diseño metodológico prevé que este proceso continúe durante el piloto, con el protocolo del Anexo 3, y que los obstáculos detectados se documenten junto con la corrección introducida, de modo que la trazabilidad entre hallazgo e intervención quede registrada.

### 5.3.6 Objetivo Específico 6: Documentación

La documentación del sistema se elaboró como componente del producto y no como anexo posterior. El conjunto comprende la documentación técnica, la guía de usuario, las notas de desarrollo y los documentos académicos que integran este informe. La conclusión que se obtiene de esta experiencia es que la documentación oportuna reduce la dependencia del autor del sistema, condición indispensable para que una institución con recursos técnicos limitados pueda sostenerlo en el tiempo. La utilidad percibida de la documentación se medirá con el instrumento del Anexo 2.

## 5.4 RECOMENDACIONES

### 5.4.1 Recomendaciones para la Implementación en Instituciones Educativas

La primera recomendación es implementar el sistema por fases, comenzando por los módulos de personal y nómina, que concentran el mayor volumen de trabajo administrativo y el mayor riesgo de error. El fundamento de esta recomendación es que el valor se percibe antes y la resistencia al cambio disminuye cuando el personal comprueba un beneficio concreto en su propia carga de trabajo.

La segunda recomendación es invertir en capacitación segmentada por perfil, distinguiendo entre quienes operan el sistema de manera intensiva y quienes lo consultan de forma ocasional. Dado que los roles definidos en el sistema delimitan funciones distintas, una capacitación homogénea resultaría ineficiente y, probablemente, insuficiente.

La tercera recomendación es designar referentes internos por institución, personas con disposición y competencia para resolver dudas de primer nivel y sostener el uso cotidiano del sistema. La experiencia documentada en la literatura sobre adopción tecnológica coincide en que estos referentes multiplican el conocimiento con mayor eficacia que la asistencia externa.

La cuarta recomendación es mantener el procedimiento anterior como respaldo durante los primeros meses de operación, mientras se consolida la confianza en el sistema. Esta previsión protege la continuidad del servicio ante cualquier contingencia técnica y reduce la ansiedad del personal durante la transición.

### 5.4.2 Recomendaciones para el Desarrollo y la Evolución del Sistema

En el plano del desarrollo, se recomienda conservar la práctica de verificación automatizada como condición de cada cambio, dado que la suite existente constituye la principal garantía de estabilidad y su valor depende de que se mantenga actualizada. Se recomienda asimismo preservar la separación entre dominio de cálculo y las demás capas, pues es la que permite modificar reglas de nómina sin afectar la interfaz ni el acceso a datos.

En cuanto a la evolución funcional, las prioridades se ordenan según el valor que aportan a las instituciones destinatarias. Las de mayor urgencia son tres: el desarrollo de una interfaz web que habilite el acceso remoto, la integración con sistemas de control de asistencia y la posibilidad de que los usuarios compongan reportes a medida. En un segundo nivel se sitúan la aplicación móvil, el soporte para varias instituciones en una misma instalación, la integración con sistemas contables y la notificación automática por correo electrónico o mensajería. En un nivel diferido quedan la analítica predictiva y los portales de autoservicio para el personal.

En el plano técnico se recomienda evaluar la migración desde SQLite hacia un motor de base de datos con mayor concurrencia cuando el volumen o el número de usuarios simultáneos lo justifique, incorporar mecanismos de caché para las consultas repetitivas y habilitar el procesamiento asíncrono de las tareas más costosas, como la generación masiva de documentos.

### 5.4.3 Recomendaciones para la Investigación Futura

La primera línea de investigación sugerida es la evaluación del impacto a mediano plazo, dado que la presente investigación mide el efecto inmediato de la implementación; los efectos sobre las prácticas administrativas y sobre la calidad del servicio educativo probablemente requieran observación prolongada. La segunda línea es la comparación entre estrategias de implantación —simultánea frente a progresiva—, con el fin de establecer cuál produce mejores resultados según el tamaño y la cultura de la institución. La tercera es la construcción de marcos de referencia específicos para sistemas de gestión educativa, aprovechando el hecho de que buena parte de los requerimientos se repiten entre instituciones. La cuarta línea, de mayor alcance, es el estudio del efecto indirecto sobre la calidad educativa, esto es, el destino que los recursos administrativos liberados reciben efectivamente en la actividad pedagógica. La quinta es el análisis de los factores culturales y organizacionales que condicionan la adopción tecnológica en contextos socioeconómicos diversos.

Metodológicamente se recomienda privilegiar estudios longitudinales con mediciones en varios momentos, investigaciones comparativas entre instituciones públicas y privadas o entre ámbitos urbanos y rurales, y análisis de costo-beneficio que cuantifiquen el retorno de la inversión en cada estrategia de implementación.

## 5.5 REFLEXIONES SOBRE EL PROCESO DE INVESTIGACIÓN

### 5.5.1 Lecciones Aprendidas

Del componente técnico del proyecto se desprenden tres lecciones. La primera es que, en contextos de recursos limitados, la simplicidad técnica supera a la sofisticación innecesaria: las funcionalidades que exigen infraestructura avanzada rara vez se adoptan, mientras que las simples se incorporan con naturalidad. La segunda es que la documentación continua posee el mismo valor que el código para la sostenibilidad del sistema, pues sin ella el conocimiento se concentra en una sola persona y el sistema se vuelve vulnerable a su ausencia. La tercera es que las pruebas con usuarios revelan obstáculos que las pruebas técnicas no pueden detectar, porque estas últimas verifican que el sistema funcione, no que resulte comprensible para quien lo usa.

Del componente organizacional se desprenden otras tres lecciones. El respaldo de la dirección es necesario pero insuficiente sin la participación de quienes ejecutan el trabajo diario. La resistencia al cambio constituye una reacción previsible y manejable cuando se comunica con claridad, se capacita con oportunidad y se demuestran beneficios tangibles. Los referentes internos resultan más persuasivos que cualquier argumento externo, porque hablan desde la experiencia compartida del propio equipo.

### 5.5.2 Desafíos Enfrentados

Los desafíos técnicos se concentraron en tres frentes: equilibrar la amplitud funcional con la simplicidad de uso, lo que se resolvió agrupando funcionalidad afín y restringiendo los módulos sensibles a los roles competentes; adaptar el sistema a políticas institucionales distintas, resuelto mediante parámetros configurables sin intervención del código; y sostener el rendimiento con volúmenes de datos crecientes, atendido con índices, consultas optimizadas y pruebas de carga previstas para el piloto.

Los desafíos organizacionales fueron de naturaleza distinta: superar el escepticismo inicial, gestionar expectativas realistas sobre las capacidades del sistema y coordinar tiempos y prioridades entre instituciones con calendarios propios. En los tres casos la respuesta eficaz fue la comunicación temprana y la demostración de resultados parciales antes de la implantación completa.

### 5.5.3 Aspectos que se Abordarían de Otro Modo

Tres decisiones se revisarían en una nueva iteración del proyecto. La primera es la incorporación de los usuarios al proceso de diseño, que ocurrió principalmente durante la validación; una participación más temprana habría evitado algunos rediseños de formularios. La segunda es la duración del periodo de observación, que conviene extender para captar patrones de uso que no se manifiestan en el corto plazo. La tercera es el desarrollo temprano de las capacidades de reporte, dado que fueron las funcionalidades mejor valoradas y, sin embargo, se incorporaron en una etapa avanzada del cronograma.

## 5.6 CONTRIBUCIONES DEL ESTUDIO

### 5.6.1 Contribuciones Técnicas

La investigación aporta, en primer lugar, la demostración de que un sistema de gestión de personal y nómina con cobertura funcional amplia puede construirse íntegramente con componentes de código abierto y sostenerse sin costos de licenciamiento. Aporta, en segundo lugar, la validación práctica de una arquitectura de capas con patrones Repository y Service complementada por un dominio de cálculo aislado, combinación que resultó adecuada para un sistema de gestión en un contexto de recursos limitados. Aporta, en tercer lugar, un sistema completo y funcional que puede adoptarse o adaptarse en otras instituciones y que queda documentado con ese propósito.

### 5.6.2 Contribuciones Metodológicas

En el plano metodológico, el estudio aporta un caso documentado de integración entre desarrollo iterativo de software e investigación-acción, con instrumentos de recolección definidos y disponibles para su reutilización. Aporta además un conjunto de instrumentos —guía de entrevista, cuestionario de satisfacción, protocolo de pruebas de usabilidad y formatos de registro— que pueden adaptarse a otros proyectos de tecnología social, y una descripción completa del proceso de desarrollo que sirve como referencia procedimental.

### 5.6.3 Contribuciones Académicas

La contribución académica principal reside en la generación de conocimiento empírico sobre la implementación de sistemas de gestión en instituciones educativas, área en la que la literatura disponible resulta limitada. El estudio identifica asimismo factores de éxito propios del contexto educativo y ofrece un caso de estudio integral —desde el diagnóstico hasta la validación— que puede informar tanto la práctica profesional como la investigación aplicada posterior.

## 5.7 LIMITACIONES DEL ESTUDIO

### 5.7.1 Limitaciones Metodológicas

La primera limitación es el tamaño de la muestra, previsto entre tres y cinco instituciones, lo que restringe la generalización de los resultados a contextos sensiblemente distintos en tamaño, tipo o ubicación. La segunda es la duración del periodo de evaluación, que resulta breve para observar efectos sostenidos; los beneficios inmediatos podrían no mantenerse en el mediano plazo sin acompañamiento institucional. La tercera es la especificidad geográfica y cultural del contexto, que condiciona la transferibilidad de los hallazgos a realidades organizacionales distintas.

### 5.7.2 Limitaciones Técnicas

El sistema presenta limitaciones de escalabilidad para volúmenes muy superiores a los previstos, derivadas de la elección de SQLite y de una arquitectura de escritorio de instalación local. Carece asimismo de versión web o móvil, lo que restringe el acceso remoto y el uso desde dispositivos portátiles, y ofrece una integración limitada con otros sistemas institucionales, circunstancia que puede resultar restrictiva en instituciones con ecosistemas tecnológicos ya consolidados.

### 5.7.3 Limitaciones de Recursos

El proyecto dependió del tiempo y de los recursos del investigador, sin financiamiento externo, lo que acotó la escala de algunas actividades —en particular la capacitación extensiva y el soporte continuo— y obligó a priorizar el desarrollo del producto sobre otras líneas de trabajo igualmente valiosas.

## 5.8 CONCLUSIONES FINALES

### 5.8.1 Sobre el Logro de los Objetivos

El objetivo general de la investigación se cumplió en los términos delimitados por la evidencia: se diseñó, se desarrolló y se dejó listo para implementación un sistema integral de gestión de personal y nómina que automatiza los procesos administrativos clave, aplica reglas verificadas para el cálculo financiero, ordena el control documental y ofrece información para la toma de decisiones. Los seis objetivos específicos se cumplieron igualmente: el análisis de requerimientos se realizó con instrumentos definidos y aplicados; el diseño arquitectónico quedó implementado y documentado; los módulos funcionales operan de manera integrada; las funcionalidades de reporte se materializaron en catorce tipos de documento; la validación técnica se sostiene en una suite de 453 funciones de prueba; y la documentación del sistema está completa y disponible.

### 5.8.2 Sobre la Validación de Hipótesis

La resolución definitiva de las hipótesis requiere la evidencia del piloto, y así se declara en el apartado 4.7. La hipótesis general —reducción de tiempos de al menos el 50 % y de errores de al menos el 80 %— se contrastará con las mediciones antes y después de la implementación y con las pruebas estadísticas previstas. Las cinco hipótesis específicas disponen de indicadores ya definidos: la hipótesis sobre la arquitectura cuenta con evidencia estructural favorable, verificable en la evolución del sistema entre las versiones 2.79 y 2.82; las hipótesis sobre usabilidad, reducción de errores financieros, acceso a la información y adopción se resolverán con los datos que se recojan en las instituciones participantes.

### 5.8.3 Sobre el Impacto del Proyecto

El impacto técnico es verificable y favorable: el sistema se encuentra funcional, organizado en capas, con diez módulos operativos, control de acceso por rol, auditoría, respaldos y una suite de 453 funciones de prueba que cubren las reglas críticas del dominio. El impacto operativo y el impacto social —mejora en la oportunidad y exactitud de los pagos, reducción de la carga administrativa y optimización de los recursos destinados a tareas de apoyo— se medirán con la evidencia del piloto, conforme a los apartados 4.5 y 4.6. El impacto académico consiste en una investigación aplicada documentada y reproducible, con instrumentos disponibles para su reutilización.

### 5.8.4 Sobre la Sostenibilidad del Proyecto

La sostenibilidad técnica descansa en la arquitectura modular, en la documentación completa y en la suite de pruebas, tres condiciones que permiten mantener y ampliar el sistema sin depender de su autor original. La sostenibilidad económica deriva del uso exclusivo de tecnologías de código abierto, sin licenciamiento recurrente ni dependencia de proveedores. La sostenibilidad social se apoya en la capacitación y en la documentación de usuario, que habilitan la autonomía del personal de la institución. La sostenibilidad académica se sustenta en la posibilidad de que el sistema y la investigación sirvan de base a proyectos posteriores, tal como se propone en el apartado 5.4.3.

## 5.9 RECOMENDACIONES FINALES

A las instituciones educativas se recomienda evaluar el sistema a la luz de sus necesidades concretas, su disponibilidad de recursos y su cultura organizacional; implementarlo de forma progresiva, comenzando por los procesos de mayor volumen; invertir en capacitación y en buenas prácticas de gestión, no solo en el manejo de las herramientas; conservar los procedimientos anteriores como respaldo durante la transición; y mantener un canal de retroalimentación que alimente las mejoras futuras del sistema.

A los desarrolladores e investigadores se recomienda incorporar a los usuarios desde las primeras etapas del proyecto y no solo en la validación; reservar tiempo suficiente para el diseño arquitectónico; documentar a medida que se construye; verificar empíricamente las decisiones de diseño en contextos reales y no únicamente en condiciones controladas; y considerar la sostenibilidad como criterio de diseño desde el inicio.

A la comunidad académica se recomienda profundizar en el estudio del efecto de los sistemas de gestión sobre la calidad educativa, desarrollar marcos de referencia específicos para el sector, explorar la aplicación de técnicas de analítica avanzada a la gestión del personal educativo, investigar los factores culturales y organizacionales que condicionan la adopción tecnológica y construir métricas e indicadores que permitan comparar la calidad y el impacto de este tipo de sistemas entre instituciones y contextos.

## 5.10 PALABRAS FINALES

El desarrollo de este sistema y la investigación que lo acompaña confirman que la tecnología disponible de forma abierta, combinada con rigor metodológico, alcanza resultados comparables a los de las soluciones comerciales en aquellos procesos que concentran el trabajo administrativo de una institución educativa. El producto construido quedó funcional, documentado y verificado; el efecto de su implementación sobre la eficiencia administrativa quedará establecido cuando la evidencia del piloto se incorpore al informe, conforme al diseño metodológico ya definido.

Más allá del resultado técnico, el trabajo deja una constatación de orden práctico: la distancia entre una institución con recursos limitados y una gestión moderna de su personal no se cierra con inversión en licencias, sino con decisiones de diseño acertadas, documentación suficiente y acompañamiento real a quienes usarán el sistema. Si el sistema se sostiene en el tiempo y la investigación asociada sirve de referencia a proyectos similares, el propósito que dio origen a este trabajo habrá quedado cumplido.

---

**El Autor**
[Nombre del Estudiante]

**Fecha:** [Fecha de Presentación]
**Lugar:** [Institución, Ciudad, País]
