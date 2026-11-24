# MARCO LÓGICO DEL PROYECTO

Matriz de planificación y seguimiento del proyecto. Distingue entre artefactos observables en el repositorio, verificaciones ejecutadas y actividades de campo aún no acreditadas. La existencia de un producto o formato no implica su aceptación comunitaria ni el cumplimiento de los indicadores de impacto.

## 1. Jerarquía resumida

| Nivel | Contenido |
|-------|-----------|
| Fin | Apoyar la gestión de personal, nómina y calificaciones en instituciones educativas mediante herramientas informáticas mantenibles y adaptables. El impacto comunitario requiere evaluación. |
| Objetivo del proyecto | Diseñar, desarrollar y preparar la evaluación de un sistema local multiusuario con sincronización y gestión documental. |
| Componentes | Sistema de escritorio y nodo; cliente Android; documentación e instrumentos; verificación técnica y eventual transferencia. |
| Actividades | Inspección y desarrollo técnico; revisión documental; autorización, diagnóstico, instalación, capacitación y piloto cuando se cuente con condiciones y registros. |

## 2. Matriz de marco lógico

### 2.1 Fin y objetivo

| Elemento | Fin | Objetivo del proyecto |
|----------|-----|-----------------------|
| Enunciado | Apoyar la gestión administrativa y la disponibilidad de información. | Diseñar y desarrollar el SDEP y definir una evaluación técnica y de campo reproducible. |
| Indicador | Resultados de uso, aceptación, continuidad y utilidad en instituciones (pendientes de evaluación). | Código y documentación inspeccionables; inventario y pruebas con resultados reproducibles; piloto solo si autorizado. |
| Medios de verificación | Evaluación posterior, registros de operación y acta institucional `[pendiente]`. | Repositorio; evidencias 01–06; salidas de pruebas Python/Android `[pendiente]`. |
| Supuestos/riesgos | La institución considera pertinente la solución y dispone de responsables, equipos y soporte. | Se identifica el commit exacto, se mantiene un entorno reproducible y se revisan cambios normativos. |

### 2.2 Componentes y resultados

| Componente | Producto esperado | Indicador verificable | Medios de verificación y estado |
|-----------|-----------------|------------------------|----------------------------------|
| C1. Diagnóstico y requerimientos | Diagnóstico participativo, requerimientos priorizados y devolución a la comunidad. | Instituciones/sujetos consentidos; procesos observados; requerimientos revisados por participantes. | Consentimientos, fichas, entrevistas y actas `[pendiente]`. Las cinco áreas actuales son categorías preliminares, no hallazgos acreditados. |
| C2. Diseño y producto de software | Componentes de escritorio, sincronización y Android documentados en el repositorio. | Inventario reproducible, arquitectura inspeccionable y módulos presentes. | Código y evidencia 01/03/06. La inspección no equivale a validación funcional ni de calidad. |
| C3. Verificación técnica | Ejecución documentada de las suites en entorno registrado y corrección de fallos. | Salidas reales de pytest y Gradle; fallos, omisiones, duración y cobertura con línea base. | Evidencias 02/05/06. Inventarios actuales: 625 funciones Python en 38 archivos de prueba y 43 anotaciones Android en 9 archivos; ejecución pendiente. |
| C4. Revisión normativa y privacidad | Matriz de fuentes, alcance y aspectos por revisar profesionalmente. | Fuente primaria/localizable, fecha y aspecto identificado; parámetros críticos revisados por asesores. | Capítulo II y evidencia 04. Identificación bibliográfica contrastada para algunas normas; vigencia integral, artículos y conformidad jurídica pendientes. |
| C5. Transferencia y evaluación comunitaria | Instalación, capacitación y piloto, si existe autorización institucional. | Actas, asistentes, versiones instaladas y medidas de campo documentadas. | Lista de cotejo, consentimientos y consolidado de instrumentos `[pendiente]`. |

### 2.3 Actividades y estado

| Fase | Actividades | Evidencia de cierre | Estado actual |
|------|-------------|---------------------|---------------|
| I. Diagnóstico | Solicitar autorizaciones; caracterizar institución; observar procesos; devolver hallazgos y validar requerimientos. | Consentimientos, fichas, entrevistas/actas y matriz validada. | Pendiente de registros de campo. |
| II. Diseño y desarrollo | Inspeccionar requisitos; diseñar capas/datos; desarrollar componentes; documentar. | Código, documentos y revisión con commit. | Artefactos presentes; el estado del árbol incluye cambios locales no etiquetados como versión de lanzamiento. |
| III. Verificación técnica | Ejecutar suite Python; compilar/probar Android; registrar entorno, fallos y cobertura; corregir y volver a ejecutar. | Salidas, reportes y commit evaluado. | Pendiente: no consta ejecución actual de pytest ni Gradle. |
| IV. Revisión normativa | Identificar texto oficial, reformas, artículos y aplicabilidad; revisar parámetros con asesoría institucional. | Registro de fuentes, fecha, alcance y observaciones. | Revisión documental parcial; dictamen y certificación no realizados. |
| V. Transferencia/piloto | Obtener consentimientos; instalar; configurar; capacitar; medir pre/post y usabilidad. | Actas, bitácoras e instrumentos completados. | Pendiente. |
| VI. Análisis y cierre | Describir resultados y límites; actualizar conclusiones; revisión académica. | Tablas vinculadas a datos fuente y aprobación. | Pendiente de fases previas. |

## 3. Operacionalización para evaluación futura

| Dimensión | Definición operativa | Indicador / evidencia | Instrumento | Precaución |
|-----------|----------------------|----------------------|------------|------------|
| Implementación | Versión instalada y habilitada para tareas autorizadas. | Versión/commit, lista de cotejo, acta. | Registro de instalación. | No confundir pantalla visible con uso en producción. |
| Tiempo | Duración de una tarea comparable desde inicio hasta finalización según protocolo. | Segundos/minutos por observación; mediana y dispersión. | Ficha cronometrada. | Emparejar tarea, equipo, datos y entrenamiento; reportar N. |
| Errores | Incidencias de datos/cálculos definidas antes de medir. | Conteo y denominador; correcciones posteriores. | Revisión de registros bajo autorización. | Separar validaciones preventivas, errores de salida y correcciones; no usar conceptos intercambiables. |
| Cobertura documental | Documentos elegibles con metadatos y seguimiento de vencimiento completos. | Proporción sobre documentos elegibles cargados. | Reporte/lista de cotejo. | Definir elegibilidad; no asumir que todo documento vence. |
| Usabilidad | Éxito, tiempo y dificultad de tareas, más SUS si se revisa/aplica. | Resultado por sujeto y tarea; puntuación SUS. | Guion y cuestionario. | Instrumento y protocolo deben revisarse/pilotearse; muestra pequeña no generalizable. |
| Percepción | Opinión de usuarios sobre dimensiones definidas. | Respuestas ordinales por dimensión. | Cuestionario revisado. | No reemplaza mediciones objetivas ni se presenta sin respuestas. |
| Calidad técnica | Comportamiento cubierto por pruebas automatizadas en una revisión concreta. | Ejecutadas/pasadas/fallidas/omitidas; cobertura/configuración. | pytest y Gradle. | Conteo de funciones/anotaciones no es resultado de ejecución ni cobertura. |

## 4. Supuestos y riesgos

1. Se obtienen autorizaciones y consentimientos antes de recolectar datos personales.
2. La institución determina responsables, finalidad, custodia y conservación de la información.
3. Existe un equipo y entorno compatibles para instalar y probar cada componente.
4. La normativa y los parámetros se revisan para el periodo e institución concretos; no se presume estabilidad regulatoria.
5. La disponibilidad de tiempo y el soporte institucional para el piloto deben confirmarse, no darse por hechos.

La matriz operativa (`MARCO_OPERATIVO.md`) propone responsables, recursos y secuencia; cada estado se actualizará solo con evidencia registrada.
