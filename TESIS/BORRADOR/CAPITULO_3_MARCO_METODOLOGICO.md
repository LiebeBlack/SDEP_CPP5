# CAPÍTULO III — MARCO METODOLÓGICO

## 3.1 Naturaleza y tipo de investigación

La investigación es **aplicada y de desarrollo tecnológico**: se orienta a diseñar y construir una solución informática para procesos administrativos concretos. El producto de software y su documentación pueden inspeccionarse en el repositorio; la instalación y transferencia a una comunidad no se consideran logradas sin registros de aceptación, capacitación y operación.

La modalidad propuesta es la de un **proyecto factible con componente sociocomunitario**. En este borrador hay evidencia de factibilidad técnica del diseño y de la implementación a nivel de código, pero no se presentan como demostradas la factibilidad operativa en una institución, la aceptación comunitaria ni la conformidad jurídica. La transferencia y el piloto se mantienen como fases pendientes. Los requisitos de acreditación del servicio comunitario corresponden además al reglamento de la institución universitaria y deben confirmarse con ella.

## 3.2 Enfoque y diseño

**Enfoque propuesto: mixto, con predominio descriptivo.** La evaluación técnica utiliza inventario cuantitativo de código y pruebas automatizadas; la fase comunitaria prevista combina observación documentada y participación de los actores con mediciones de tiempo, errores, usabilidad y percepción. Como el diagnóstico participativo y el piloto carecen todavía de sus registros fuente en el expediente, el enfoque mixto describe el diseño pendiente y no una recolección ya efectuada. La operacionalización está en `MARCO_LOGICO.md`.

**Diseño de evaluación propuesto.** Para la fase de campo se plantea una comparación pretest-postest en un solo grupo, sin asignación aleatoria ni grupo de control. Sus resultados, si se recolectan, permitirán describir cambios en las tareas observadas; no bastarán por sí solos para atribuir causalidad. El inventario y las pruebas técnicas son una evaluación del producto separada de esa comparación. El protocolo de rendimiento se considera planificado hasta que se registren las condiciones del equipo, datos, repeticiones y resultados.

**Componente participativo previsto.** La participación del personal en el diagnóstico, validación de requerimientos y transferencia es parte del diseño sociocomunitario. No se denomina investigación-acción participativa ejecutada hasta que existan actas, fichas y decisiones de iteración validadas por los participantes.

## 3.3 Contexto y unidades de estudio

### 3.3.1 Contexto

El contexto previsto es el de instituciones educativas del entorno comunitario de la institución de estudios. No se dispone en el expediente de un registro de instituciones que permita afirmar su participación efectiva o describir su infraestructura, organización, conectividad y procedimientos. Tales características deben levantarse y documentarse antes de delimitar el contexto empírico.

### 3.3.2 Población y muestra

**Población de campo prevista:** personal administrativo y directivo que realice los procesos de personal, documentos, incidencias, contratos, nómina o registro académico en las instituciones que autoricen la participación. El marco y tamaño de la población, así como el periodo de observación y los registros elegibles, no se han determinado todavía.

**Selección prevista:** intencional, condicionada a la pertinencia del rol, autorización institucional e individual, y disponibilidad de equipo compatible. No se presenta una muestra efectiva ni una caracterización mientras no se realice el reclutamiento y se documente el consentimiento.

- Instituciones con participación documentada: `[pendiente]`
- Sujetos consentidos y distribución por perfil: `[pendiente]`
- Periodo y volumen de registros observados: `[pendiente]`

**Objeto de evaluación técnica:** los componentes del repositorio inspeccionados. La existencia de un inventario de código no significa que cada módulo haya pasado una ejecución automatizada ni una prueba operacional.

## 3.4 Técnicas e instrumentos de recolección

| Técnica | Instrumento | Aplicación | Variable que atiende |
|---------|-------------|-----------|---------------------|
| Observación directa | Ficha de observación del proceso administrativo | Diagnóstico y, si se implanta el piloto, pretest y postest | Tiempos, errores observables y disponibilidad de registro de cambios |
| Registro de métricas | Ficha de registro de métricas técnicas | Sobre el repositorio del software | Calidad técnica del producto |
| Lista de cotejo | Lista de verificación de requerimientos, controles y fuentes normativas | Inspección documental; transferencia cuando ocurra | Cobertura técnica y estado de revisión normativa (no certifica conformidad) |
| Encuesta | Cuestionario de percepción antes y después, con escala de aceptación | Fase de campo | Percepción de eficiencia, satisfacción |
| Prueba de usabilidad | Protocolo de tareas cronometradas y cuestionario SUS | Fase de campo | Usabilidad |
| Prueba técnica automatizada | Suite Python y pruebas unitarias Android | Inventario disponible; ejecución pendiente de registrar | Comportamiento bajo los casos automatizados |

El expediente de anexos (`../../TESIS/BIBLIOGRAFIA_ANEXOS.md`) contiene los instrumentos propuestos; el estado de aplicación y el consolidado de respuestas se registran en `RESPUESTAS_INSTRUMENTOS.md`. Tener un formato preparado no equivale a haberlo validado por jueces ni aplicado.

### 3.4.1 Diseño de la medición

**3.4.1.1 Pretest.** En cada institución participante se observa el proceso manual y se registran: tiempo de ejecución de cada tarea administrativa representativa (registro de un empleado, carga de un documento, registro de una incidencia, generación de una nómina del periodo, consolidación de calificaciones de un grado), número de errores detectados en los registros del periodo, y disponibilidad de trazabilidad de las modificaciones.

**3.4.1.2 Postest propuesto.** Solo después de instalación autorizada, capacitación y operación suficiente se repetirían las mismas tareas con el sistema. Se deben conservar las definiciones, equipo de medición, unidades, condiciones y criterios del pretest. Las validaciones del sistema no se equiparan automáticamente con errores reales evitados: se registrarán por separado los errores de salida detectados, las correcciones posteriores y las advertencias de validación. La trazabilidad se evaluará únicamente para operaciones cuyo evento, actor, fecha y cambio puedan comprobarse en el mecanismo efectivamente disponible; no se asumirá que una operación en cola Android equivale a una entrada en el log de auditoría del escritorio.

**3.4.1.3 Pruebas de usabilidad.** Cada sujeto participante ejecuta un guion de tareas representativas del módulo asignado a su perfil. Se registran tiempo, éxito o fracaso de la tarea, y dificultad declarada. Al cierre se aplica el cuestionario de escala de aceptación de sistemas (SUS), cuya puntuación se interpreta según el baremo publicado de la escala.

**3.4.1.4 Pruebas técnicas.** El inventario estático de la versión revisada registra 625 funciones Python cuyo nombre comienza con `test_` en 38 archivos `test_*.py`, además de `conftest.py`; la suite Android contiene 43 anotaciones `@Test` en 9 archivos Kotlin. Estas cifras cuentan definiciones y anotaciones, no resultados aprobados. No se localizó un informe actual de ejecución ni cobertura; ambos permanecen pendientes. El criterio previsto es registrar el resumen real de ejecución, fallos y omisiones, y comparar la cobertura con una línea base obtenida mediante el mismo comando y configuración.

**3.4.1.5 Pruebas de rendimiento.** Protocolo factorial sobre volumen de registros: tiempos de respuesta de las operaciones de consulta y de registro con cargas de datos progresivas. El protocolo y sus umbrales de aceptación se fijan antes de la medición:

**Tabla 3.1. Protocolo de rendimiento y umbrales de aceptación**

| Nivel de carga | Registros por tabla | Operaciones medidas | Umbral de aceptación |
|----------------|--------------------|---------------------|----------------------|
| Bajo | 50 empleados; 200 documentos; 100 incidencias | Apertura de módulo; búsqueda; generación de nómina | Respuesta instantánea a la percepción (menos de 1 segundo) |
| Medio | 200 empleados; 800 documentos; 400 incidencias | Ídem | Menos de 2 segundos por operación |
| Alto | 500 empleados; 2.000 documentos; 1.000 incidencias | Ídem, más exportación y reporte PDF | Menos de 5 segundos por operación |

*Fuente: protocolo propio del proyecto. Los umbrales se registran con el equipo real de la institución, no con equipo de laboratorio, porque la validez del umbral es operativa y no teórica.*

### 3.4.2 Validez y confiabilidad

La **validez de contenido** aún no está acreditada: no se encontraron actas ni dictámenes de jueces sobre los instrumentos. Se propone someterlos a revisión del tutor y especialistas en administración de personal y software, registrar sus observaciones y documentar los ajustes antes de aplicarlos.

La **confiabilidad** del cuestionario no está calculada. Si el tamaño y la naturaleza de la muestra lo permiten, se estimará la consistencia interna sobre respuestas reales y se informará el método, tamaño muestral y limitaciones; ningún umbral sustituye una interpretación contextual. El guion de tareas también debe pilotearse y documentarse antes de su uso.

Las métricas técnicas requieren procedimientos reproducibles, entorno descrito y salidas conservadas. La inspección estática y el conteo de pruebas no constituyen por sí solos una ejecución ni validación de comportamiento.

## 3.5 Operacionalización de variables

La operacionalización se presenta en matriz en el archivo `MARCO_LOGICO.md` (apartados 6 y 7). En síntesis:

- **Intervención prevista:** uso del sistema en tareas seleccionadas, definido por condiciones de instalación, versión, capacitación y periodo; no se presume implementado en campo.
- **Resultados de campo por medir:** tiempo por tarea; errores registrados según definición acordada; proporción de documentos incorporados con fecha de vencimiento válida y seguimiento habilitado; éxito y tiempo de tareas de usabilidad; percepción mediante instrumento revisado.
- **Variables de contexto:** institución, perfil, tarea, experiencia previa, volumen y periodo. Dadas la muestra intencional y la ausencia prevista de grupo de control, los cambios se describirán sin inferencia causal fuerte.

## 3.6 Fases del proyecto

**Fase I — Diagnóstico participativo propuesto.** Consentimiento, observación, entrevistas o devolución a participantes, caracterización y derivación de requerimientos. Producto esperado: registros de diagnóstico validados. Estado: pendiente de evidencia de campo; las cinco áreas actuales son categorías de indagación.

**Fase II — Diseño y desarrollo.** El repositorio contiene el sistema de versión base 3.0.1, documentación y código de cliente Android. Estado: artefactos inspeccionados; la ejecución actual de las suites y la validación institucional no se han verificado. Cambios posteriores de Android se detallan en la evidencia 06, por lo que no se debe atribuir todo el código móvil a la línea base 3.0.1 sin versionar el commit.

**Fase III — Transferencia y operación piloto.** Instalación autorizada, configuración, capacitación, pilotaje e instrumentos. Estado: pendiente de aplicación y de sus registros.

**Fase IV — Análisis y consolidación.** Tabulación de registros, descripción de resultados y revisión de objetivos. Estado: pendiente de la fase III. El capítulo actual reporta solo inventarios técnicos reproducibles, no resultados de impacto.

## 3.7 Matrices de planificación

La planificación del proyecto en dos matrices de gestión se entrega en archivos propios, para su uso operativo durante la ejecución:

1. **Marco lógico** (`MARCO_LOGICO.md`): jerarquía de objetivos, propósitos, productos, actividades, indicadores verificables, medios de verificación y supuestos.
2. **Marco operativo** (`MARCO_OPERATIVO.md`): actividades por fase con responsables, recursos, tiempos, técnicas y evidencia esperada de cada actividad.

## 3.8 Consideraciones éticas

La fase de campo deberá aplicar cuatro compromisos: (1) obtener y archivar el consentimiento informado institucional e individual antes de observar o recolectar datos; (2) minimizar los datos personales, limitar su acceso y acordar su custodia y conservación; la operación local no elimina por sí sola los deberes de confidencialidad; (3) evitar interferir en las decisiones administrativas; y (4) no incorporar datos de campo sin registro fuente. No se afirma que los consentimientos ni la aprobación institucional existan hasta que se aporten.

## 3.9 Hipótesis

**Proposición general de evaluación.** El sistema puede apoyar la gestión de personal, nómina y calificaciones; el grado en que modifica tiempos, errores, control documental, usabilidad o percepción debe establecerse con mediciones reales y comparables.

**Criterios de evaluación propuestos.**

1. Describir el cambio de tiempo por tarea entre mediciones pre y post, con número de observaciones, mediana, dispersión y condiciones. No se fija una reducción del 50 % sin justificación previa ni evidencia piloto.
2. Comparar errores detectados bajo una definición y denominador explícitos, diferenciando errores encontrados antes del registro, correcciones posteriores y validaciones preventivas.
3. Calcular la cobertura de vencimientos sobre el conjunto de documentos efectivamente cargados, distinguiendo tipos que requieren fecha de caducidad por regla institucional.
4. Informar resultados del SUS y de tareas por sujeto solo después de revisar el instrumento, aplicarlo y preservar sus registros.
5. Informar el resultado de cada suite únicamente tras ejecutar el comando en el entorno registrado; el inventario de 625 pruebas Python y 43 pruebas Android no decide este criterio.

Los criterios de campo y la ejecución automatizada permanecen pendientes. No se declaran hipótesis confirmadas en este borrador.

---
**Fuentes de este capítulo:** instrumentos propuestos en los anexos, estado de evidencia asentado en los legajos 01–06 y documentación técnica inspeccionada. Los procedimientos de campo aquí descritos son planes mientras no estén acompañados de sus registros.
