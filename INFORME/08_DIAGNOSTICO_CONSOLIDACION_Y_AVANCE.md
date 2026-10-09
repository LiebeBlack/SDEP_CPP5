# ARCHIVOS DE DIAGNÓSTICO, CONSOLIDACIÓN Y AVANCE

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 08 del expediente del informe del estado de la investigación.

---

## 1. Introducción y propósito

Este documento reúne los tres conjuntos de artefactos mediante los cuales el proyecto fundamentó su diagnóstico inicial, consolidó su avance documental y llevó registro de su progreso. Su propósito es servir de registro de trazabilidad: quien examine el expediente debe poder reconstruir con qué se diagnosticó el problema, con qué se verificó la consistencia del acervo documental y con qué se siguió el estado de cada componente.

El documento se organiza en tres partes que corresponden a esos tres conjuntos. El diagnóstico comprende los instrumentos aplicados y la lectura que de ellos resultó. La consolidación comprende los mecanismos que mantienen el acervo documental íntegro y coherente. El avance comprende la matriz de estado por componente, el registro de lo ejecutado y la lista de pendientes con su forma de incorporación.

---

## 2. Artefactos de diagnóstico

### 2.1 Diagnóstico de la situación inicial

El diagnóstico que dio origen al proyecto no se apoyó en una impresión general, sino en tres fuentes convergentes que la metodología denomina triangulación de fuentes. La primera fue la observación directa de los procesos de gestión de personal, con registro del tiempo consumido, los instrumentos utilizados y los puntos en que aparecían las dificultades. La segunda fueron las entrevistas semiestructuradas aplicadas al personal directivo, administrativo y de recursos humanos. La tercera fue la literatura especializada, que permitió contrastar si los obstáculos identificados correspondían a patrones documentados en otros contextos o constituían particularidades del caso.

La convergencia de las tres fuentes otorga al diagnóstico una solidez que ninguna por separado habría proporcionado: la observación documenta lo que ocurre, la entrevista recoge lo que los actores perciben y la literatura establece si el fenómeno es singular o recurrente. Cuando los tres coinciden, la conclusión admite un grado de confianza que no depende del criterio del investigador.

### 2.2 Instrumentos aplicados

| Instrumento | Naturaleza | Composición | Función en el diagnóstico |
|-------------|-----------|-------------|---------------------------|
| Guía de entrevista para el análisis de requerimientos | Cualitativo | Veintidós preguntas en seis bloques | Recoger los procesos vigentes, las dificultades recurrentes y las expectativas |
| Registro de observación directa | Cualitativo y cuantitativo | Notas de campo estructuradas con registro de tiempos | Comprender el trabajo real y cuantificar su carga |
| Revisión documental | Cualitativo | Análisis de literatura, normativa y sistemas existentes | Situar el caso y contrastar los hallazgos |
| Cuestionario de satisfacción | Cuantitativo | Veinte afirmaciones en escala de Likert y tres preguntas abiertas | Establecer la línea base de percepción antes de la implementación |
| Protocolo de pruebas de usabilidad | Mixto | Seis tareas representativas con registro de tiempo, éxito y errores | Evaluar la facilidad de uso del sistema |

Los instrumentos cualitativos se validarán mediante juicio de expertos, con revisión del tutor académico, y se aplicarán en una sesión previa con el fin de ajustar la redacción de las preguntas y estimar su duración efectiva. Los formatos de documentación de pruebas siguen la estructura de las recomendaciones de la norma IEEE 829-2008.

### 2.3 Hallazgos del diagnóstico

El diagnóstico identificó cinco manifestaciones críticas, que constituyen la base sobre la que se formuló el problema y se definieron los objetivos.

| Hallazgo | Manifestación observada | Consecuencia |
|----------|-------------------------|--------------|
| Información del personal fragmentada | Legajos físicos y planillas sin formato común entre dependencias | Ausencia de una fuente única de verdad sobre el personal |
| Procesamiento manual de la nómina | Deducciones calculadas individualmente y días trabajados según criterio del operador | Riesgo de error con implicaciones económicas y legales |
| Control documental deficiente | Documentación sin verificación de vigencia | Exposición a incumplimientos y auditoría inviable en la práctica |
| Gestión de incidencias sin trazabilidad | Solicitudes en papel sin estado formal de aprobación | Desconocimiento de la disponibilidad real del personal |
| Reportes tardíos y no estructurados | Compilaciones manuales con información histórica no estructurada | Decisiones adoptadas con información incompleta |

Estos hallazgos coinciden con las barreras documentadas internacionalmente para la incorporación de tecnología en el ámbito educativo —insuficiencia de equipos y programas, capacitación limitada del personal y falta de tiempo para asimilar herramientas nuevas—, y con la advertencia de que la disponibilidad de sistemas de información confiables es condición necesaria, aunque no suficiente, para mejorar la gestión. Esa coincidencia es la que permitió tratar el caso local como una instancia de un fenómeno documentado y no como una situación aislada.

### 2.4 Del diagnóstico a los requerimientos

El diagnóstico se tradujo en requerimientos funcionales y no funcionales jerarquizados según su valor y su costo de implementación. Los requerimientos funcionales corresponden a los procesos identificados como críticos: registro del personal, control documental, gestión de incidencias, contratación, cálculo de nómina, configuración institucional, generación documental y reportes. Los requerimientos no funcionales comprenden la usabilidad para usuarios con competencias heterogéneas, el funcionamiento sin conectividad permanente, la seguridad y la trazabilidad, la mantenibilidad y la portabilidad. La correspondencia entre estos requerimientos y los módulos efectivamente implementados se verifica en el documento [10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md](10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md).

---

## 3. Artefactos de consolidación

### 3.1 Función de la consolidación documental

La consolidación documental es el conjunto de mecanismos que mantienen el acervo del proyecto íntegro, coherente y verificable. Su necesidad es práctica: un expediente con doce documentos académicos y siete técnicos, más el código fuente y la suite de pruebas, no se sostiene por sí solo. Sin un registro que declare qué versión se examina, de qué fuente proviene cada dato y qué afirmaciones permanecen pendientes, el acervo se degrada en contradicciones y duplicaciones.

### 3.2 Registro de control documental

El registro de control documental cumple tres funciones: identifica el conjunto de documentos que integran el informe, deja constancia de las modificaciones que cada uno ha recibido y consigna las verificaciones de consistencia practicadas sobre el contenido. Su finalidad es permitir que un evaluador externo determine qué versión examina, de qué fuente proviene cada dato y qué afirmaciones se encuentran pendientes de evidencia.

El registro comprende además el historial de versiones del sistema documentado, que resulta decisivo para interpretar cualquier cifra del expediente.

| Versión | Hito documentado |
|---------|------------------|
| 1.0.4 | Versión sobre la que se ejecutó la medición de cobertura que se conserva como referencia |
| 2.79 | Versión en la que se documentó por primera vez la suite de 323 pruebas, la autenticación con roles y los módulos iniciales |
| 3.0.0 | Versión vigente del corpus académico: siete módulos funcionales, motor de nómina, gestión documental, incidencias y contratación, y 476 funciones de prueba |
| 3.0.1 | Versión vigente del repositorio: incorpora el dominio académico y la gestión de sesiones; 551 funciones de prueba |

### 3.3 Verificación automática de la documentación

La consolidación no se confía a la inspección manual. El proyecto incorpora un verificador que comprueba de forma automática la consistencia del acervo documental, incluidas la estructura de los documentos y la correspondencia con las copias publicadas en el portal de consulta. La ejecución de ese verificador forma parte de la evidencia técnica del proyecto y constituye un control de calidad documental poco frecuente en trabajos de este tipo.

La verificación de correspondencia se practicó sobre los veinte documentos del acervo —trece académicos y siete técnicos— mediante comparación con sus copias en el portal y recuento de las entradas declaradas en su catálogo.

### 3.4 Inventario consolidado del acervo

| Conjunto | Documentos | Ubicación |
|----------|-----------|-----------|
| Documentos académicos del informe | Trece (proyecto sociotecnológico, anteproyecto, capítulos I a V, bibliografía y anexos, resumen, dos oficios, índice y registro de control) | `TESIS/` |
| Documentos técnicos del producto | Siete (documentación técnica, guía de usuario, notas de desarrollo, estructura del proyecto, guía de contribución, inicio rápido de integración continua y presentación general) | Raíz del repositorio y `docs/content/` |
| Expediente del estado de la investigación | Diez documentos, incluido este | `INFORME/` |
| Código fuente | 77 archivos Python en `src/`, más 13 archivos del agente de sincronización | `src/`, `sync_agent/` |
| Suite de pruebas | 32 archivos con 551 funciones de prueba | `tests/` |

### 3.5 Criterios de consolidación aplicados a los textos

La revisión documental se rigió por cinco criterios. El primero fue la verificabilidad: ninguna cifra de magnitud, nombre de componente o referencia bibliográfica se aceptó sin comprobación directa. El segundo fue la coherencia interna: se verificó que objetivos, hipótesis, fases metodológicas, resultados y conclusiones describieran el mismo proyecto. El tercero fue la correspondencia entre citas y referencias. El cuarto fue la adecuación del registro lingüístico, con el producto descrito en pasado cuando está concluido y en futuro solo cuando depende del piloto. El quinto fue la honestidad del alcance: no presentar como medido lo que solo está implementado, ni como implementado lo que solo está diseñado.

---

## 4. Artefactos de avance

### 4.1 Matriz de avance por componente

La matriz siguiente sintetiza el estado de cada componente del proyecto, con la evidencia que lo respalda y la fuente en que consta.

| Componente | Estado | Evidencia | Fuente |
|------------|--------|-----------|--------|
| Diagnóstico y planteamiento del problema | Concluido | Instrumentos aplicados y diagnóstico triangulado | Capítulo I |
| Análisis de requerimientos | Concluido | Requerimientos funcionales y no funcionales priorizados | Capítulo I y anexo de instrumentos |
| Diseño de la arquitectura | Concluido e implementado | Arquitectura de capas y patrones | Capítulo IV y código |
| Desarrollo de módulos | Concluido | Siete módulos operativos en 3.0.0; nueve en 3.0.1 | Capítulo IV e interfaz |
| Reportes y documentos oficiales | Concluido | Doce tipos de documento en PDF | Generador documental |
| Pruebas técnicas | Concluido | 551 pruebas exitosas y verificadores estáticos | Ejecución del 6 de octubre de 2026 |
| Pruebas de usabilidad | Programadas | Protocolo de seis tareas con campos de registro | Anexo de usabilidad |
| Aplicación piloto | Programada | Tablas de medición con marcador por completar | Capítulo IV |
| Validación de hipótesis | Parcial | Indicadores definidos; componente estructural verificado | Capítulo IV |
| Documentación | Concluida y sincronizada | Documentos técnicos y académicos verificados | Verificador documental |
| Redacción del informe | Concluida salvo el piloto | Capítulos I a V, bibliografía y anexos | `TESIS/` |

### 4.2 Cronograma y estado de ejecución

El cronograma previsto abarcó ocho meses distribuidos en cuatro fases. El estado de ejecución es el siguiente: el análisis de requerimientos y el diseño y desarrollo se completaron; las pruebas técnicas se ejecutaron en su totalidad; la documentación se concluyó; y las pruebas con usuarios y la aplicación piloto mantienen su programación.

| Fase | Periodo previsto | Estado |
|------|------------------|--------|
| 1. Análisis de requerimientos | Meses 1 y 2 | Ejecutada |
| 2. Diseño y desarrollo | Meses 3 a 6 | Ejecutada |
| 3. Pruebas y validación | Mes 7 | Parcialmente ejecutada: pruebas técnicas concluidas; usabilidad y piloto programados |
| 4. Implementación y documentación | Mes 8 | Documentación ejecutada; implementación en instituciones programada |

El cronograma detallado por semanas, con responsable y estado de cada actividad, se conserva en el anexo correspondiente del informe.

### 4.3 Verificaciones de avance practicadas

Las comprobaciones siguientes se ejecutaron sobre el repositorio y sus resultados quedaron incorporados al expediente.

| Verificación | Procedimiento | Resultado |
|--------------|---------------|-----------|
| Versión documentada | Lectura de `VERSION` y `pyproject.toml` | 3.0.1 en ambos |
| Extensión del código | Recuento de líneas | 29 475 líneas en 77 archivos Python |
| Distribución por capa | Recuento por directorio | Interfaz 11 598; utilidades 5 525; servicios 4 332; repositorios 2 383; modelos 1 887; configuración 1 706; nómina 1 502 |
| Funciones de prueba | Recuento de definiciones de prueba | 551 en 32 archivos |
| Esquema de base de datos | Búsqueda de nombres de tabla | 13 tablas |
| Módulos de interfaz | Lectura de la lista de módulos | 9 módulos con atajos `Ctrl+1` a `Ctrl+9` |
| Matriz de acceso | Lectura del mapa de permisos | 8 entradas y cuatro roles |
| Parámetros de seguridad | Lectura del validador | PBKDF2-HMAC-SHA256, 200 000 iteraciones, sal de 16 bytes |
| Análisis estático | Ejecución de verificadores | Sin hallazgos en los archivos verificados |
| Consistencia documental | Verificador automático | Todos los chequeos superados |

### 4.4 Registro de pendientes y forma de incorporación

Los pendientes se agrupan por naturaleza y cada uno declara el procedimiento mediante el cual se incorporará al expediente.

| Pendiente | Naturaleza | Forma de incorporación |
|-----------|-----------|------------------------|
| Datos de identificación institucional | Documental | Sustituir los campos entre corchetes en los documentos del expediente |
| Antecedentes locales | Documental | Incorporar casos con fuente localizable conforme a los criterios declarados |
| Confirmación de vigencia normativa | Documental | Confrontar cada norma con la Gaceta Oficial |
| Re-medición de la cobertura | Técnica | Ejecutar la cobertura sobre la versión vigente y sustituir el valor |
| Informe de la última ejecución de la suite | Técnica | Adjuntar el reporte con número de pruebas, resultado y fecha |
| Resultados de usabilidad | Empírica | Aplicar el protocolo y registrar tiempos, éxito, errores y valoración |
| Resultados de satisfacción | Empírica | Aplicar el cuestionario y calcular el alfa de Cronbach |
| Mediciones de tiempo y error | Empírica | Registrar antes y después de la implementación |
| Pruebas de rendimiento y carga | Empírica | Aplicar el protocolo durante el piloto |
| Tratamiento estadístico e hipótesis | Empírica | Aplicar las pruebas definidas y decidir cada hipótesis |

### 4.5 Regla de incorporación de la evidencia pendiente

La incorporación de la evidencia pendiente sigue una regla que preserva la coherencia del conjunto: ningún valor se estima ni se presume. Cada marcador se sustituye por el valor efectivamente medido; cuando una medición no se realice, el apartado correspondiente declara la causa y ajusta el alcance de la conclusión, en lugar de rellenar el vacío con una aproximación. Esta regla es la que permite que el informe conserve su valor probatorio una vez incorporados los datos del piloto.

---

## 5. Conclusión

El proyecto dispone de un aparato de diagnóstico, consolidación y avance completo y verificable. El diagnóstico se construyó por triangulación de fuentes y sus hallazgos son consistentes con la literatura. La consolidación se apoya en un registro de control documental y en un verificador automático que mantiene la coherencia del acervo. El avance queda registrado en una matriz por componente, en el estado de ejecución del cronograma y en una lista de pendientes que declara, para cada uno, cómo se incorporará.

Lo que resta no es una carencia de método, sino la ejecución del componente empírico cuyo procedimiento ya está definido. La distinción entre lo ejecutado y lo pendiente, sostenida a lo largo de todo el expediente, es la garantía de que el informe podrá cerrarse sin rehacer el trabajo previo y sin renunciar a su rigor.

---

## 6. Plantillas de registro del avance

Con el fin de que la incorporación de la evidencia pendiente sea uniforme, se consignan las plantillas de registro que se emplearán durante el piloto. Su formato sigue el de los instrumentos del corpus académico.

### 6.1 Plantilla de registro de tiempos

| Campo | Registro |
|-------|----------|
| Institución | |
| Proceso observado | |
| Condición (antes / después) | |
| Fecha y hora | |
| Participante y perfil | |
| Tiempo observado (minutos) | |
| Observaciones | |

### 6.2 Plantilla de registro de errores

| Campo | Registro |
|-------|----------|
| Institución | |
| Tipo de operación | |
| Volumen de operaciones del periodo | |
| Número de operaciones con corrección | |
| Tasa de error (porcentaje) | |
| Fuente del registro | |

### 6.3 Plantilla de resultado por tarea de usabilidad

| Campo | Registro |
|-------|----------|
| Participante y perfil | |
| Tarea (1 a 6) | |
| Tiempo de ejecución | |
| Resultado (éxito / éxito con ayuda / fallo) | |
| Número y naturaleza de los errores | |
| Comentarios del participante | |

### 6.4 Plantilla de decisión sobre hipótesis

| Campo | Registro |
|-------|----------|
| Hipótesis | |
| Indicador y umbral | |
| Valor observado | |
| Prueba estadística aplicada | |
| Estadístico, grados de libertad y valor de probabilidad | |
| Decisión (se acepta / se rechaza / evidencia insuficiente) | |
| Observaciones sobre relevancia práctica | |

### 6.5 Regla de llenado

Las plantillas se llenan en el momento de la observación y no por reconstrucción posterior. Cuando un campo no pueda completarse, se deja constancia del motivo en lugar de estimarlo. Esta regla preserva la trazabilidad entre el dato registrado y la conclusión que de él se derive.

---

**El Autor**
[Nombre del Estudiante]

**Tutor Académico**
[Nombre del Tutor]
