# MATRIZ DEL ENFOQUE DEL MARCO LÓGICO (EML)

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 09 del expediente del informe del estado de la investigación.

---

## 1. Introducción

La Matriz del Enfoque del Marco Lógico es el instrumento que condensa, en una sola estructura, la lógica del proyecto: qué se quiere lograr y en qué niveles, cómo se reconocerá el logro, con qué evidencia se verificará y bajo qué condiciones externas se sostiene la relación causal. Su valor reside en la disciplina que impone: cada nivel del proyecto debe estar acompañado de indicadores y de medios de verificación, y cada relación causal debe declarar sus supuestos, es decir, las condiciones que deben cumplirse para que el nivel inferior produzca el superior.

El documento presenta la matriz en sus cuatro niveles —fin, propósito, componentes y actividades—, desarrolla la operacionalización de las variables, presenta las fichas de indicadores de los niveles superiores, examina los supuestos y cierra con una lectura del estado de cada nivel. La construcción de los objetivos que la matriz ordena se encuentra en [06_MARCO_LOGICO_Y_OBJETIVOS.md](06_MARCO_LOGICO_Y_OBJETIVOS.md).

---

## 2. Estructura de la matriz

La matriz se lee de abajo hacia arriba en cuanto a la causalidad y de arriba hacia abajo en cuanto a la verificación. Las actividades producen los componentes; los componentes, en conjunto, realizan el propósito; y el propósito, sostenido por sus supuestos, contribuye al fin. Para cada nivel se declaran cuatro campos: el resumen narrativo, los indicadores verificables objetivamente, los medios de verificación y los supuestos.

| Nivel | Pregunta que responde |
|-------|-----------------------|
| Fin | ¿A qué objetivo de desarrollo contribuye el proyecto? |
| Propósito | ¿Qué cambio produce el proyecto en su ámbito de intervención? |
| Componentes | ¿Qué productos debe entregar el proyecto para lograr el propósito? |
| Actividades | ¿Qué acciones se requieren para producir cada componente? |

---

## 3. Matriz del Enfoque del Marco Lógico

### 3.1 Nivel de fin

| Campo | Contenido |
|-------|-----------|
| Resumen narrativo | Contribuir a la mejora de la eficiencia administrativa y de la calidad del servicio educativo en instituciones educativas con recursos limitados, mediante la modernización de la gestión de personal y nómina |
| Indicadores | Reducción sostenida del tiempo administrativo destinado a la gestión de personal; mejora de la oportunidad y exactitud de la remuneración; incremento de la trazabilidad de los procesos |
| Medios de verificación | Mediciones del piloto; estudios de seguimiento posteriores; registros institucionales de correcciones y de tiempos |
| Supuestos | Las instituciones mantienen su compromiso con la modernización; el personal sostiene el uso del sistema; el contexto institucional no se altera de forma que invalide las mediciones |

### 3.2 Nivel de propósito

| Campo | Contenido |
|-------|-----------|
| Resumen narrativo | Sistema integral de gestión de personal y nómina diseñado, desarrollado e implementado, que automatiza los procesos administrativos clave, garantiza la precisión de los cálculos financieros, ordena el control documental y proporciona información oportuna para la toma de decisiones |
| Indicadores | Reducción de los tiempos de procesamiento de al menos el 50 %; disminución de los errores administrativos de al menos el 80 %; satisfacción de los usuarios superior al 80 % |
| Medios de verificación | Observación directa antes y después de la implementación; registro institucional de correcciones; cuestionario de satisfacción con cálculo del alfa de Cronbach; pruebas estadísticas definidas en la metodología |
| Supuestos | El sistema se adopta efectivamente en las instituciones participantes; las condiciones de medición son comparables antes y después; los datos recogidos son completos y fiables |

### 3.3 Nivel de componentes

| Código | Resumen narrativo | Indicadores | Medios de verificación | Supuestos |
|--------|-------------------|-------------|------------------------|-----------|
| C1 | Análisis de requerimientos concluido | Requerimientos funcionales y no funcionales identificados y priorizados; casos de uso documentados | Instrumentos aplicados y documento de requerimientos | Las instituciones facilitan el acceso a su personal y sus procesos |
| C2 | Arquitectura del sistema diseñada e implementada | Separación por capas verificada; reglas de negocio probadas de forma aislada; cobertura del dominio de cálculo del 89 % | Código fuente y suite de pruebas | Las tecnologías seleccionadas se mantienen disponibles y documentadas |
| C3 | Módulos funcionales implementados | Nueve módulos operativos con control de acceso por cuatro roles | Interfaz del sistema y matriz de permisos | Los usuarios participan en la validación de la funcionalidad |
| C4 | Reportes y documentos oficiales desarrollados | Doce tipos de documento en PDF; exportación en formatos abiertos | Generador documental del sistema | La institución identifica los documentos que requiere emitir |
| C5 | Sistema validado en su componente técnico | Suite sin fallos; verificadores estáticos sin hallazgos | Ejecución del 6 de octubre de 2026: 551 pruebas exitosas | Las dependencias se mantienen compatibles con el intérprete |
| C6 | Documentación integral elaborada | Documentación técnica, guía de usuario y portal sincronizados | Verificador documental automático | La institución designa responsables de consultar la documentación |

### 3.4 Nivel de actividades

| Componente | Actividades principales |
|------------|-------------------------|
| C1 | Revisión bibliográfica y normativa; entrevistas semiestructuradas; observación directa con registro de tiempos; consolidación y priorización de requerimientos |
| C2 | Diseño de la arquitectura de capas; selección de patrones; diseño del modelo de datos; revisión técnica con el tutor |
| C3 | Implementación de modelos y repositorios; implementación de servicios de negocio; desarrollo de la interfaz gráfica; integración de los módulos |
| C4 | Diseño de las plantillas documentales; implementación de la generación de PDF; implementación de la exportación en formatos abiertos |
| C5 | Redacción de la suite de pruebas; ejecución de pruebas unitarias y de integración; verificación estática y de tipos; pruebas de seguridad |
| C6 | Redacción de la documentación técnica y de la guía de usuario; elaboración de las notas de desarrollo; publicación del portal y verificación de consistencia |

---

## 4. Operacionalización de las variables

La matriz cobra precisión cuando las variables se traducen en dimensiones, indicadores y escalas de medición. La tabla siguiente realiza esa operacionalización.

| Variable | Tipo | Dimensión | Indicador | Escala o unidad |
|----------|------|-----------|-----------|-----------------|
| Implementación del sistema | Independiente | Presencia y uso del sistema en la institución | Módulos operativos; usuarios activos por perfil | Categórica y de razón |
| Eficiencia administrativa | Dependiente | Tiempo de procesamiento | Minutos por operación antes y después | Razón (minutos) |
| Eficiencia administrativa | Dependiente | Calidad del proceso | Tasa de error antes y después | Razón (porcentaje) |
| Eficiencia administrativa | Dependiente | Satisfacción del usuario | Puntuación por dimensión | Intervalo (1 a 5) |
| Tamaño de la institución | Control | Dotación de personal | Número de empleados | Razón (número) |
| Nivel educativo | Control | Ámbito de la institución | Básica, media o superior | Nominal |
| Ámbito | Control | Localización | Urbana o suburbana | Nominal |
| Perfil del usuario | Control | Función en la institución | Directivo, recursos humanos, administrativo o docente | Nominal |
| Competencia tecnológica | Control | Nivel autodeclarado | Baja, media o alta | Ordinal |

La distinción entre la variable independiente y la dependiente es la que sostiene la validez interna del estudio: la implementación del sistema es la intervención, y la eficiencia administrativa es el efecto que se mide antes y después, manteniendo constantes las condiciones de medición.

---

## 5. Fichas de indicadores de los niveles superiores

Las fichas precisan, para cada indicador del propósito y del fin, su definición, su fórmula cuando corresponde, su meta, su frecuencia y su fuente. Esta precisión evita la práctica, frecuente en la evaluación de proyectos, de declarar un indicador sin establecer cómo se calcula ni quién lo verifica.

### 5.1 Ficha del indicador: reducción del tiempo de procesamiento

| Campo | Contenido |
|-------|-----------|
| Definición | Variación porcentual del tiempo promedio requerido para completar una operación administrativa representativa |
| Fórmula | ((tiempo medio antes − tiempo medio después) / tiempo medio antes) × 100 |
| Meta | Reducción de al menos el 50 % |
| Frecuencia de medición | Una antes de la implementación y una al concluir el periodo de uso acompañado |
| Fuente | Observación directa conforme al procedimiento metodológico |
| Responsable | Investigador, con presencia del personal de la institución |

### 5.2 Ficha del indicador: reducción de la tasa de error

| Campo | Contenido |
|-------|-----------|
| Definición | Variación porcentual de la proporción de operaciones que requieren corrección posterior |
| Fórmula | ((tasa de error antes − tasa de error después) / tasa de error antes) × 100 |
| Meta | Disminución de al menos el 80 % |
| Frecuencia de medición | Antes y después de la implementación, con la misma ventana temporal |
| Fuente | Registro institucional de correcciones y reconstrucción por observación |
| Responsable | Investigador, con validación de la institución |

### 5.3 Ficha del indicador: satisfacción del usuario

| Campo | Contenido |
|-------|-----------|
| Definición | Valoración media de la experiencia de uso por dimensión y en su conjunto |
| Fórmula | Media aritmética de las respuestas por dimensión, sobre escala de uno a cinco; complementada con el alfa de Cronbach |
| Meta | Superior al 80 % de valoración favorable |
| Frecuencia de medición | Antes (línea base) y después de la implementación |
| Fuente | Cuestionario de satisfacción del anexo correspondiente |
| Responsable | Investigador, con garantía de anonimato del respondiente |

### 5.4 Ficha del indicador: cobertura funcional

| Campo | Contenido |
|-------|-----------|
| Definición | Proporción de los procesos identificados como críticos que el sistema cubre con funcionalidad operativa |
| Fórmula | (procesos cubiertos / procesos identificados) × 100 |
| Meta | Cobertura de los procesos críticos diagnosticados |
| Frecuencia de medición | Verificación única sobre la versión construida |
| Fuente | Módulos del sistema e informe de verificación técnica |
| Responsable | Investigador |

---

## 6. Supuestos, riesgos y condiciones de validez

### 6.1 Análisis de los supuestos

Los supuestos son las condiciones externas que deben cumplirse para que la relación causal de la matriz se sostenga. No son parte del control del proyecto, pero sí de su viabilidad. Se examinan a continuación con su nivel de riesgo y la medida prevista para atenderlos.

| Supuesto | Nivel al que afecta | Riesgo | Medida prevista |
|----------|---------------------|--------|-----------------|
| Las instituciones facilitan el acceso a su personal y sus procesos | C1 | Medio | Acuerdos formalizados desde el inicio y demostración temprana del valor |
| Los usuarios participan en la validación | C3, propósito | Medio | Diseño de sesiones acotadas y capacitación previa |
| El sistema se adopta efectivamente | Propósito, fin | Medio | Capacitación segmentada, usuarios referentes y continuidad del procedimiento anterior |
| Las mediciones son comparables antes y después | Propósito | Bajo | Registro del mismo procedimiento e instrumentos en ambos momentos |
| Las dependencias tecnológicas se mantienen disponibles | C2, C5 | Bajo | Uso de componentes maduros y documentados; verificación en integración continua |
| El contexto institucional no se altera de forma invalidante | Fin | Medio | Registro de las condiciones del entorno durante el piloto |

### 6.2 Riesgos declarados

Los riesgos identificados se agrupan en cuatro categorías, con su estrategia de mitigación. En el orden técnico, las dificultades imprevistas del desarrollo se atendieron con prototipado temprano y tecnologías maduras. En el orden de la participación, la dificultad para incorporar instituciones se mitiga con acuerdos formalizados e instituciones alternativas previstas. En el orden temporal, el retraso se gestiona con priorización estricta de las funcionalidades esenciales. En el orden de la calidad, el riesgo de un producto que no satisfaga las expectativas se controla con verificación continua y validación temprana.

### 6.3 Condiciones de validez

La matriz declara cuatro condiciones que delimitan su validez. La primera es el tamaño de la muestra, previsto entre tres y cinco instituciones, que restringe la generalización estadística. La segunda es la duración del periodo de evaluación, breve para observar efectos sostenidos. La tercera es la especificidad geográfica y cultural del contexto, que condiciona la transferibilidad de los hallazgos. La cuarta es la posición del investigador como desarrollador del sistema evaluado, circunstancia que se contrarresta con la triangulación de fuentes y con la distinción sostenida entre lo verificado sobre el producto y lo medido con los usuarios.

---

## 7. Estado de la matriz

La lectura del estado de la matriz por nivel arroja un resultado claro. Los componentes C1, C2, C3, C4 y C6 se encuentran realizados y verificables. El componente C5 está realizado en su parte técnica y pendiente en su parte empírica. El propósito y el fin permanecen condicionados a esa parte empírica.

| Nivel | Estado | Explicación |
|-------|--------|-------------|
| Fin | Pendiente de medición | Requiere la evidencia del piloto y, en el mediano plazo, estudios de seguimiento |
| Propósito | Cumplido en los componentes; magnitud de efecto pendiente | El sistema existe y está verificado; la reducción de tiempos y errores requiere medición |
| Componentes | C1 a C4 y C6 cumplidos; C5 parcial | Los productos existen; la validación empírica de C5 está programada |
| Actividades | Ejecutadas en su componente técnico | El cronograma se cumplió en las fases ejecutadas |

---

## 8. Conclusión

La Matriz del Enfoque del Marco Lógico ordena el proyecto en una estructura de cuatro niveles cuya lógica causal es explícita y cuyos indicadores, medios de verificación y supuestos están declarados. La matriz permite constatar dos cosas a la vez: que los productos comprometidos existen y son verificables, y que la magnitud del efecto sobre la eficiencia administrativa permanece como la única determinación pendiente.

Esa constatación no debilita el proyecto, sino que lo precisa. Un proyecto que declara con exactitud qué ha logrado, qué le resta y con qué criterio se reconocerá el logro final posee la propiedad que se espera de un instrumento de gestión: la de permitir su evaluación sin ambigüedades. La matriz es, en ese sentido, la síntesis verificable de todo el expediente.

---

## 9. Matriz resumida en una página

La tabla siguiente condensa la matriz completa en su forma de lectura más compacta, apta para su presentación en una sola página.

| Nivel | Resumen narrativo | Indicadores | Medios de verificación | Supuestos |
|-------|-------------------|-------------|------------------------|-----------|
| Fin | Mejorar la eficiencia administrativa y la calidad del servicio educativo mediante la modernización de la gestión de personal y nómina | Reducción sostenida del tiempo administrativo; mejora de la oportunidad y exactitud de la remuneración | Mediciones del piloto y estudios de seguimiento | Las instituciones sostienen el uso; el contexto no invalida las mediciones |
| Propósito | Sistema integral diseñado, desarrollado e implementado que automatiza procesos, garantiza el cálculo, ordena el control documental y provee información oportuna | Reducción del tiempo ≥ 50 %; reducción de errores ≥ 80 %; satisfacción > 80 % | Observación antes y después; registro de correcciones; cuestionario y pruebas estadísticas | El sistema se adopta; las mediciones son comparables |
| C1 | Análisis de requerimientos | Requerimientos priorizados y casos de uso | Instrumentos y documento | Acceso al personal y a los procesos |
| C2 | Arquitectura diseñada e implementada | Separación por capas; dominio de cálculo probado al 89 % | Código y suite | Tecnologías disponibles |
| C3 | Módulos implementados | Nueve módulos con cuatro roles | Interfaz y matriz de permisos | Participación de los usuarios |
| C4 | Reportes y documentos | Doce tipos de documento en PDF | Generador documental | La institución conoce sus documentos |
| C5 | Validación técnica | Suite sin fallos | Ejecución del 6 de octubre de 2026 | Dependencias compatibles |
| C6 | Documentación integral | Documentación sincronizada | Verificador documental | Responsables de consulta designados |

### 9.1 Uso previsto de esta matriz

Esta versión compacta se destina a la presentación oral y a la revisión rápida por parte de la instancia evaluadora. Para el trabajo de verificación detallado se emplea la matriz completa de los apartados 3 a 6, que contiene las fichas de indicadores y el análisis pormenorizado de los supuestos.

---

**El Autor**
[Nombre del Estudiante]

**Tutor Académico**
[Nombre del Tutor]
