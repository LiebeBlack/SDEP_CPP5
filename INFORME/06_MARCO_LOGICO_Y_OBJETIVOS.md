# MARCO LÓGICO Y OBJETIVOS

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 06 del expediente del informe del estado de la investigación.

---

## 1. Introducción

Este documento establece el marco lógico del proyecto y formula sus objetivos. El marco lógico es el instrumento que ordena la relación causal entre el problema detectado, la solución propuesta, los productos que la componen y los resultados que se esperan de ella. Su utilidad consiste en hacer explícito aquello que de otro modo quedaría supuesto: por qué cada objetivo existe, a qué problema responde y con qué indicador se reconocerá si fue alcanzado.

El documento procede en cuatro pasos. Primero, reconstruye la cadena que va del problema a los objetivos. Segundo, formula el objetivo general y los objetivos específicos con el mismo enunciado que el corpus académico emplea, para preservar la coherencia del expediente. Tercero, sitúa los objetivos en la jerarquía del marco lógico —fin, propósito y componentes—. Cuarto, relaciona cada objetivo con las hipótesis, las variables y los indicadores que permitirán resolverlo. La construcción de la matriz completa —con sus indicadores, medios de verificación y supuestos— corresponde al documento [09_MATRIZ_ENFOQUE_MARCO_LOGICO.md](09_MATRIZ_ENFOQUE_MARCO_LOGICO.md).

---

## 2. Del problema a los objetivos

### 2.1 Estructura del problema

El diagnóstico del Capítulo I identificó cinco manifestaciones críticas de la gestión de personal en las instituciones educativas de recursos limitados: la información del personal fragmentada y sin fuente única; el cálculo manual de la nómina con su carga de error; la documentación laboral sin control de vigencia; las incidencias sin trazabilidad de su aprobación; y los reportes que llegan tarde para sustentar decisiones.

Estas manifestaciones no son independientes entre sí. La ausencia de una fuente única de información obliga a reconstruir los datos cada vez que se calcula la nómina, lo que multiplica las oportunidades de error; el cálculo manual consume el tiempo que podría destinarse a la verificación; y la falta de registros sistemáticos impide auditar lo hecho y anticipar lo que debe hacerse. El problema central puede formularse así: la gestión de personal y nómina descansa sobre procedimientos manuales y datos dispersos, lo que produce información poco confiable, cálculos expuestos al error y decisiones adoptadas con datos tardíos.

Las causas del problema se agrupan en cuatro: carencia de un sistema que centralice la información; ausencia de reglas explícitas y verificables para el cálculo; falta de control sistemático sobre la vigencia documental y el flujo de las incidencias; e insuficiencia de reportes oportunos y estructurados. Sus efectos se extienden a la dimensión laboral —desconfianza del personal por errores y atrasos—, a la dimensión de control —imposibilidad de auditar— y a la dimensión de sostenibilidad —costos operativos evitables y dificultad para acreditar el cumplimiento normativo—.

### 2.2 De las causas a los medios

El marco lógico se construye invirtiendo la lectura del problema: cada causa se transforma en un medio, y cada medio en un componente del objetivo. La correspondencia es la siguiente.

| Causa del problema | Medio que la revierte | Componente del objetivo |
|--------------------|------------------------|--------------------------|
| Carencia de un sistema que centralice la información | Construcción de un sistema con fuente única de datos | Módulos de gestión de personal y documentación |
| Ausencia de reglas explícitas y verificables de cálculo | Motor de cálculo parametrizado y probado | Módulo de nómina |
| Falta de control de vigencia y del flujo de incidencias | Control documental con avisos y flujo de aprobación formal | Módulos de documentos, incidencias y contratos |
| Insuficiencia de reportes oportunos y estructurados | Generación automática de documentos y reportes | Funcionalidades de reporte y generación documental |

De esa inversión resultan los seis objetivos específicos que se formulan más adelante. El medio último —la mejora de la eficiencia administrativa— constituye el fin al que el conjunto apunta y no puede lograrse por la sola existencia del software, sino por su adopción efectiva en las instituciones.

---

## 3. Objetivo general

El objetivo general de la investigación se enuncia en los siguientes términos:

> Diseñar, desarrollar e implementar un sistema integral de gestión de personal y nómina para instituciones educativas que automatice los procesos administrativos clave, garantice la precisión de los cálculos financieros, ordene el control documental y proporcione información oportuna para la toma de decisiones, con el propósito de contribuir a la mejora de la eficiencia administrativa del sector educativo.

El enunciado contiene cuatro resultados observables —automatización de procesos, precisión del cálculo financiero, orden del control documental y oportunidad de la información— y un propósito de mayor alcance —la mejora de la eficiencia administrativa—. Esa distinción es relevante para la lectura del estado de la investigación: los cuatro resultados observables corresponden a componentes construidos y verificados, mientras que el propósito de eficiencia es el que requiere la medición empírica del piloto.

---

## 4. Objetivos específicos

Los objetivos específicos del proyecto son seis. Se enuncian a continuación con la misma formulación del corpus académico, y se añade, para cada uno, su producto verificable y su estado de cumplimiento.

### 4.1 Objetivo Específico 1: Análisis de requerimientos

> Analizar los procesos actuales de gestión de personal en instituciones educativas para identificar requerimientos funcionales, no funcionales y restricciones técnicas, mediante entrevistas, observación directa y análisis documental.

**Producto verificable:** documento de requerimientos funcionales y no funcionales, diagramas de casos de uso y priorización de funcionalidades.
**Estado:** cumplido. El análisis se realizó con la guía de entrevista del anexo correspondiente, la observación directa con registro de tiempos y el análisis documental, y sus hallazgos quedaron incorporados al diagnóstico del Capítulo I.

### 4.2 Objetivo Específico 2: Diseño de la arquitectura

> Diseñar la arquitectura del sistema con patrones de diseño consolidados y criterios de ingeniería de software que garanticen escalabilidad, mantenibilidad y verificabilidad.

**Producto verificable:** arquitectura de capas documentada, con patrones Repository y Service, dominio de nómina aislado y modelo de datos implementado.
**Estado:** cumplido. La arquitectura quedó implementada y su capacidad de mantenimiento se comprobó en la propia evolución del sistema, que admitió la incorporación de nuevos módulos y el retiro de módulos completos sin refundar las capas preexistentes.

### 4.3 Objetivo Específico 3: Implementación de los módulos

> Implementar los módulos de gestión de personal, documentación, incidencias, contratación y nómina con interfaces usables, funcionalidad completa y validaciones integrales, empleando tecnologías de código abierto.

**Producto verificable:** módulos funcionales operativos con control de acceso por rol, validaciones y auditoría.
**Estado:** cumplido. El corpus y el repositorio comprenden nueve módulos operativos en la versión 3.0.1, con la extensión académica incorporada.

### 4.4 Objetivo Específico 4: Reportes y documentos oficiales

> Desarrollar las funcionalidades de reporte estadístico y de generación de documentos oficiales en formato PDF que la institución requiere para la toma de decisiones y el cumplimiento de sus obligaciones.

**Producto verificable:** doce tipos de documento oficial en PDF y exportación de listados en formatos abiertos.
**Estado:** cumplido. Los tipos de documento y las rutas de exportación son verificables en el generador documental del sistema.

### 4.5 Objetivo Específico 5: Validación

> Validar el sistema mediante pruebas automatizadas, pruebas de usabilidad con usuarios reales y aplicación piloto en instituciones educativas, evaluando su efecto sobre la eficiencia administrativa.

**Producto verificable:** suite de pruebas automatizadas ejecutada, protocolo de usabilidad aplicado y mediciones antes y después de la implementación.
**Estado:** parcialmente cumplido. El componente de pruebas técnicas está concluido —la suite del 6 de octubre de 2026 registró 551 pruebas exitosas—, mientras que las pruebas de usabilidad y la aplicación piloto mantienen su programación.

### 4.6 Objetivo Específico 6: Documentación

> Documentar integralmente el sistema —documentación técnica, guía de usuario, notas de desarrollo y documentos académicos— de modo que su sostenimiento y su expansión no dependan de una sola persona.

**Producto verificable:** documentación técnica, guía de usuario, notas de desarrollo, portal de consulta y verificación automática de la consistencia documental.
**Estado:** cumplido. La documentación se elaboró como componente del producto y su consistencia se verifica de forma automatizada.

---

## 5. Jerarquía del marco lógico

El marco lógico organiza los objetivos en tres niveles. El nivel superior es el fin, que expresa la contribución del proyecto a un objetivo de desarrollo más amplio. El nivel intermedio es el propósito, que corresponde al objetivo general y describe el cambio que el proyecto produce directamente. El nivel inferior son los componentes, que corresponden a los resultados de los objetivos específicos.

| Nivel | Enunciado | Campo de verificación |
|-------|-----------|-----------------------|
| Fin | Contribuir a la mejora de la eficiencia administrativa y de la calidad del servicio educativo en instituciones con recursos limitados, mediante la modernización de la gestión de personal y nómina | Mediciones del piloto y, en el mediano plazo, estudios de seguimiento |
| Propósito (objetivo general) | Sistema integral de gestión de personal y nómina diseñado, desarrollado e implementado, con automatización de procesos, precisión del cálculo, control documental y información oportuna | Componentes construidos y verificación técnica |
| Componente 1 | Análisis de requerimientos concluido | Instrumentos aplicados y documento de requerimientos |
| Componente 2 | Arquitectura diseñada e implementada | Código en capas y evolución documentada |
| Componente 3 | Módulos funcionales operativos | Módulos con control de acceso por rol |
| Componente 4 | Reportes y documentos oficiales | Doce tipos de documento en PDF |
| Componente 5 | Sistema validado en su componente técnico | Suite de pruebas y verificadores estáticos |
| Componente 6 | Documentación integral del producto | Documentación técnica, guía y portal |

La distinción entre niveles explica por qué la afirmación sobre el cumplimiento debe formularse con precisión: los componentes y el propósito pueden declararse alcanzados en la medida en que el producto existe y está verificado; el fin, en cambio, depende de la adopción efectiva y de la medición de su efecto, y por ello permanece vinculado al piloto.

---

## 6. Hipótesis y variables

### 6.1 Hipótesis general

La hipótesis general sostiene que la implementación del sistema mejorará de manera significativa la eficiencia administrativa, con una reducción de los tiempos de procesamiento de al menos el 50 % y una disminución de los errores administrativos de al menos el 80 %. Su resolución requiere las mediciones antes y después de la implementación y las pruebas estadísticas definidas en la metodología.

### 6.2 Hipótesis específicas

Las cinco hipótesis específicas y su estado de evidencia son los siguientes.

| Código | Hipótesis | Indicador | Estado de la evidencia |
|--------|-----------|-----------|------------------------|
| H1 | La arquitectura modular facilita el mantenimiento y la expansión | Tiempo de incorporación de una funcionalidad nueva; comprensión del código por terceros | Estructural favorable: la evolución entre 2.79 y 3.0.1 se logró sin refactorizaciones |
| H2 | La interfaz gráfica mejora la usabilidad respecto de la línea de comandos | Tiempo de aprendizaje; tasa de éxito; valoración de la interfaz | Pendiente del piloto |
| H3 | La automatización reduce los errores financieros | Verificación automatizada de las reglas; variación de la tasa de error | Estructural favorable: reglas de cálculo verificadas por la suite |
| H4 | La digitalización mejora el acceso a la información | Disponibilidad de la información en el sistema; variación del tiempo de búsqueda | Estructural favorable en la disponibilidad; magnitud pendiente del piloto |
| H5 | La capacitación y la documentación favorecen la adopción | Proporción de usuarios activos; satisfacción con la capacitación; utilidad de la documentación | Pendiente del piloto |

### 6.3 Variables

El estudio distingue tres tipos de variable. La variable independiente es la implementación del sistema de gestión de personal y nómina. La variable dependiente es la eficiencia administrativa, medida en tiempo de procesamiento, tasa de errores y satisfacción de los usuarios. Las variables de control son las características de la institución —tamaño, nivel educativo y ámbito— y el perfil y la competencia tecnológica de los usuarios, que se registran para poder comparar casos comparables. La operacionalización completa de estas variables se desarrolla en la matriz del apartado 7 del documento [09_MATRIZ_ENFOQUE_MARCO_LOGICO.md](09_MATRIZ_ENFOQUE_MARCO_LOGICO.md).

---

## 7. Indicadores por objetivo

Los indicadores permiten reconocer, con un criterio explícito, cuándo un objetivo se ha alcanzado. Se consignan a continuación agrupados por objetivo, con su meta y su medio de verificación. Los indicadores que dependen del piloto se señalan como tales.

| Objetivo | Indicador | Meta | Medio de verificación |
|----------|-----------|------|------------------------|
| General | Reducción del tiempo de procesamiento | Al menos 50 % | Mediciones antes y después del piloto |
| General | Reducción de la tasa de error administrativo | Al menos 80 % | Registro institucional de correcciones |
| Específico 1 | Requerimientos identificados y priorizados | Documento de requerimientos con casos de uso | Instrumentos aplicados y documento |
| Específico 2 | Arquitectura implementada y verificable | Separación por capas con reglas probadas de forma aislada | Código y cobertura del dominio de nómina (89 %) |
| Específico 3 | Cobertura funcional de los módulos previstos | Módulos operativos con control de acceso por rol | Módulos de la interfaz y matriz de acceso |
| Específico 4 | Documentos oficiales generables | Doce tipos de documento en PDF | Generador documental |
| Específico 5 | Pruebas técnicas exitosas | Suite sin fallos | Ejecución del 6 de octubre de 2026: 551 exitosas |
| Específico 5 | Validación con usuarios | Pruebas de usabilidad aplicadas y satisfacción superior al 80 % | Protocolo del anexo y cuestionario |
| Específico 6 | Documentación completa y consistente | Documentación técnica, guía y portal sincronizados | Verificación documental automatizada |

---

## 8. Coherencia entre objetivos, hipótesis y metodología

La coherencia interna del proyecto exige que objetivos, hipótesis y fases metodológicas describan el mismo trabajo. La correspondencia se establece en la tabla siguiente.

| Objetivo específico | Hipótesis asociada | Fase metodológica | Sección de resultados |
|---------------------|--------------------|--------------------|------------------------|
| 1. Análisis de requerimientos | — | Fase 1 (ejecutada) | 1.2.2 y 2.2 del informe |
| 2. Diseño de la arquitectura | H1 | Fase 2 (ejecutada) | 4.2.1 del Capítulo IV |
| 3. Implementación de módulos | H3, H4 | Fase 2 (ejecutada) | 4.2.2 del Capítulo IV |
| 4. Reportes y documentos | H4 | Fase 2 (ejecutada) | 4.2.1.6 del Capítulo IV |
| 5. Validación | H2, H3, H5 y general | Fase 3 (parcial) | 4.3 y 4.4 a 4.7 del Capítulo IV |
| 6. Documentación | H5 | Fase 4 (documentación ejecutada) | 5.3.6 del Capítulo V |

Al cruzar la tabla se advierte que la única fase con cumplimiento parcial es la tercera, y que su componente faltante —la validación con usuarios y la aplicación piloto— es precisamente el que resuelve la hipótesis general y las hipótesis H2 y H5. Esa constatación confirma la solidez de la estructura lógica del proyecto: no hay objetivos sin método ni hipótesis sin indicador, y el cumplimiento pendiente se concentra en un único componente identificado.

---

## 9. Conclusión

El marco lógico del proyecto encadena de manera explícita el problema diagnosticado, la solución construida y los resultados esperados. El objetivo general enuncia el propósito y los seis objetivos específicos detallan los componentes que lo realizan; las hipótesis traducen el propósito en afirmaciones contrastables; y los indicadores establecen con qué criterio se reconocerá su cumplimiento.

El balance del estado es claro: los componentes del producto y su verificación técnica están cumplidos, y el único tramo pendiente es la aplicación en campo que resolverá la magnitud del efecto sobre la eficiencia administrativa. Esa pendiente no compromete la validez del proyecto: la estructura lógica está completa y los instrumentos para cerrarla están definidos.

---

## 10. Cuadro integrado de coherencia

Este cuadro reúne, en una sola vista, la cadena completa que va del objetivo al supuesto. Permite comprobar que cada objetivo específico tiene un producto, un indicador, un medio de verificación y un supuesto declarado, y que ninguno queda huérfano.

| Objetivo específico | Producto | Indicador | Medio de verificación | Supuesto |
|---------------------|----------|-----------|------------------------|----------|
| 1. Analizar los procesos y los requerimientos | Documento de requerimientos y casos de uso | Requerimientos identificados y priorizados | Instrumentos aplicados | Las instituciones facilitan el acceso a su personal y sus procesos |
| 2. Diseñar la arquitectura | Arquitectura de capas con patrones | Separación verificada y reglas probadas de forma aislada | Código y cobertura del dominio de nómina | Las tecnologías se mantienen disponibles y documentadas |
| 3. Implementar los módulos | Módulos con validaciones y control de acceso | Cobertura funcional de los procesos críticos | Interfaz y matriz de permisos | Los usuarios participan en la validación |
| 4. Desarrollar reportes y documentos | Doce tipos de documento y exportación abierta | Documentos oficiales generables | Generador documental | La institución identifica los documentos que requiere |
| 5. Validar el sistema | Suite ejecutada y protocolo de usabilidad aplicado | Pruebas sin fallos; satisfacción superior al 80 % | Ejecución registrada y cuestionario | Las condiciones de medición son comparables |
| 6. Documentar el producto | Documentación técnica, guía y portal | Documentación completa y consistente | Verificador documental | La institución designa responsables de consulta |

### 10.1 Lectura del cuadro

La lectura vertical de cada fila muestra que el objetivo no es un enunciado aislado, sino el nodo de una cadena verificable. La lectura horizontal de cada columna muestra que ningún indicador carece de medio de verificación ni ningún medio de supuesto. El único objetivo con cumplimiento parcial es el quinto, y su componente pendiente —la validación con usuarios— es el que sostiene la resolución de la hipótesis general. Esa concentración del pendiente en un único punto es un indicio de la solidez de la estructura lógica del proyecto.

---

**El Autor**
[Nombre del Estudiante]

**Tutor Académico**
[Nombre del Tutor]
