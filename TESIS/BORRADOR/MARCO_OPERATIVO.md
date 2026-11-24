# MARCO OPERATIVO DEL PROYECTO

Plan de trabajo y control de evidencia. Las duraciones son estimaciones de planificación, no un registro de tiempo ya empleado. Ninguna actividad se marca como realizada sin su fuente verificable. No se presume que existan instituciones participantes o consentimientos.

## 1. Convenciones de estado

| Símbolo | Significado |
|---------|-------------|
| [DOC] | Artefacto/código localizado e inspeccionado; no implica ejecución ni validación externa |
| [PEN] | Pendiente de ejecución o registro |
| [REV] | Revisión documental parcial; quedan aspectos por confirmar |
| [OK] | Solo se usará cuando haya evidencia de ejecución conservada y fechada |

## 2. Plan por fases

### Fase I — Autorización y diagnóstico participativo

| Código | Actividad | Responsable previsto | Recursos | Duración estimada | Evidencia requerida | Estado |
|--------|-----------|---------------------|----------|-------------------|--------------------|--------|
| I.1 | Identificar instituciones, responsables y autorización para el proyecto | Investigador e institución | Oficios, protocolo, información de contacto | 1–2 semanas | Aceptación institucional fechada | [PEN] |
| I.2 | Revisar consentimiento, minimización, acceso y conservación de datos | Investigador y responsable institucional | Formato aprobado, protocolo de confidencialidad | Antes del trabajo de campo | Consentimientos y acuerdo de manejo de datos | [PEN] |
| I.3 | Caracterizar procesos, infraestructura y conectividad sin presuponer prácticas | Investigador y participantes | Ficha y guion revisados | 2–4 semanas | Fichas anonimizadas, fecha, rol y contexto | [PEN] |
| I.4 | Devolver hallazgos y validar requerimientos con participantes | Investigador y participantes | Taller/sesión | 1 semana | Acta, comentarios y matriz revisada | [PEN] |

### Fase II — Diseño, desarrollo y documentación

| Código | Actividad | Responsable previsto | Recursos | Duración estimada | Evidencia requerida | Estado |
|--------|-----------|---------------------|----------|-------------------|--------------------|--------|
| II.1 | Inspeccionar repositorio y fijar revisión/commit de referencia | Investigador | Git, inventarios | 1–2 días | Commit, comandos y salidas | [DOC] árbol inspeccionado; commit no fijado para el inventario |
| II.2 | Documentar arquitectura, módulos y entorno | Investigador | Código y documentación | 1–2 semanas | Referencias a archivos y versión | [DOC] |
| II.3 | Implementar mejoras necesarias según requerimientos priorizados | Investigador | Entorno de desarrollo | Variable | Cambios revisados, pruebas y commit | [PEN]/en desarrollo |
| II.4 | Mantener documentos académicos, instrumentos y evidencia | Investigador | `TESIS/BORRADOR/` | Continua | Historial de cambios y fuentes | [DOC] |

### Fase III — Verificación técnica

| Código | Actividad | Responsable previsto | Recursos | Duración estimada | Evidencia requerida | Estado |
|--------|-----------|---------------------|----------|-------------------|--------------------|--------|
| III.1 | Ejecutar `pytest tests/` en revisión identificada | Investigador | Python y dependencias declaradas | 1 día | Salida completa: N, fallos, omisiones, duración | [PEN] entorno Python no disponible en esta sesión |
| III.2 | Medir cobertura con la misma configuración y línea base | Investigador | pytest-cov, configuración | 1 día | Reporte de cobertura y versión | [PEN] |
| III.3 | Ejecutar `./gradlew :app:assembleDebug :app:testDebugUnitTest` | Investigador | JDK 17 y Android SDK | 1 día | Salida Gradle, resultado de tareas | [PEN] no hay Java/JDK ni SDK configurado en esta sesión |
| III.4 | Corregir fallos y volver a ejecutar todas las verificaciones afectadas | Investigador | Entornos anteriores | Según fallos | Registro antes/después vinculado al commit | [PEN] |

### Fase IV — Revisión normativa y privacidad

| Código | Actividad | Responsable previsto | Recursos | Duración estimada | Evidencia requerida | Estado |
|--------|-----------|---------------------|----------|-------------------|--------------------|--------|
| IV.1 | Confirmar textos oficiales, Gacetas, reformas y vigencia | Investigador; revisión del tutor | Asamblea Nacional, Gaceta Oficial y repositorios institucionales | 1–2 semanas | URL/documento, fecha de consulta y norma exacta | [REV] números de varias Gacetas contrastados; análisis integral pendiente |
| IV.2 | Verificar artículos concretos y aplicabilidad según cada entidad | Asesoría competente e institución | Textos oficiales y perfil jurídico | Según asesoría | Matriz con artículo, entidad, alcance y observaciones | [PEN] |
| IV.3 | Contrastar fórmulas, parámetros y plantillas con normas actuales | Especialista laboral/contable/tributario e institución | Casos autorizados, documentos de nómina | Antes de producción | Informe de revisión firmado | [PEN] |
| IV.4 | Revisar privacidad y seguridad del tratamiento de datos | Responsable institucional y especialista | Inventario de datos y flujos | Antes de carga real | Evaluación y controles aprobados | [PEN] |

### Fase V — Transferencia y piloto (condicionado a autorización)

| Código | Actividad | Responsable previsto | Recursos | Duración estimada | Evidencia requerida | Estado |
|--------|-----------|---------------------|----------|-------------------|--------------------|--------|
| V.1 | Comprobar requisitos, compatibilidad y aceptación de instalación | Investigador y TI institucional | Checklist, equipos | 1 semana | Acta de instalación y versión | [PEN] |
| V.2 | Respaldar y cargar datos con acceso mínimo | Personal institucional; apoyo técnico | Exportación, respaldo, plantillas | 1–3 semanas | Conteos, aprobación y registro de respaldo | [PEN] |
| V.3 | Revisar parámetros institucionales de nómina antes de uso | Asesor/a institucional | Normativa y datos de prueba autorizados | 1 semana | Hoja de parámetros aprobada | [PEN] |
| V.4 | Capacitar perfiles definidos y evaluar tareas | Investigador y responsables | Guía, sesiones, ejercicios | 1–2 semanas | Asistencia y evaluación consentida | [PEN] |
| V.5 | Aplicar pretest/postest solo con tareas comparables y protocolo aprobado | Investigador y participantes | Instrumentos revisados | Periodo acordado | Registros anonimizados, N y contexto | [PEN] |
| V.6 | Evaluar usabilidad/percepción y resguardar respuestas | Investigador | Protocolo, SUS/cuestionario revisados | 1 semana | Formularios y tabulación anonimizada | [PEN] |

### Fase VI — Análisis y consolidación

| Código | Actividad | Responsable previsto | Recursos | Duración estimada | Evidencia requerida | Estado |
|--------|-----------|---------------------|----------|-------------------|--------------------|--------|
| VI.1 | Tabular solo datos reales, conservando criterios y denominadores | Investigador | Registros de fase V | 1 semana | Hoja de cálculo trazable y diccionario | [PEN] |
| VI.2 | Describir tiempos, errores, usabilidad y límites | Investigador | Protocolo estadístico | 1 semana | Tablas y método reproducibles | [PEN] |
| VI.3 | Actualizar Capítulo IV y conclusiones según resultados | Investigador/tutor | Borrador y evidencia | 1–2 semanas | Texto vinculado a fuentes | [PEN] |
| VI.4 | Revisar consistencia, bibliografía, anexos y enlaces | Investigador/tutor | Expediente completo | 1–2 semanas | Lista de revisión final | [PEN] |

## 3. Recursos y condiciones por confirmar

| Categoría | Recurso | Estado de disponibilidad |
|-----------|---------|--------------------------|
| Humano | Investigador y tutor | Confirmar designación y disponibilidad |
| Humano | Personal institucional participante | No identificado/consentido en el expediente |
| Técnico | Entorno Python para pruebas | No disponible en esta sesión; configurar o usar entorno reproducible |
| Técnico | JDK 17 y Android SDK | No disponibles/configurados en esta sesión |
| Técnico | Equipos institucionales y conectividad | Por caracterizar; no presumir disponibilidad |
| Organizativo | Aprobación institucional, privacidad y respaldos | Pendiente de acordar |
| Financiero | Instalación, mantenimiento, capacitación y soporte | Presupuestar con la institución; el código abierto no elimina estos costos |

## 4. Riesgos y mitigación

| Riesgo | Impacto | Acción propuesta |
|--------|---------|------------------|
| Falta de autorización/consentimiento | Impide recolectar datos o instalar | No iniciar trabajo de campo hasta autorización; minimizar y seudonimizar datos |
| Herramientas de prueba ausentes | No se puede afirmar calidad de ejecución | Configurar entorno reproducible y conservar logs antes de cerrar resultados |
| Parámetros legales o contables desactualizados | Cálculos inapropiados para uso real | Deshabilitar uso productivo hasta revisión profesional y aprobación institucional |
| Pérdida/exposición de datos | Daño a personas e institución | Definir custodia, cifrado/acceso, copias y respuesta a incidentes; probar restauración |
| Desfase entre código y documentos | Resultados no reproducibles | Fijar commit y registrar fecha/comandos en cada legajo |
| Baja conectividad | Afecta sincronización, no debe asumirse impacto sin prueba | Caracterizar la red y probar colas/conflictos en entorno controlado |
| Cambio normativo | Requiere revisión de parámetros/procedimientos | Seguimiento de fuentes oficiales antes de cada periodo de uso |

## 5. Cronograma orientativo

El siguiente orden es una propuesta, no un calendario ejecutado. Las duraciones se definirán con la institución y no presuponen fechas de participación.

1. Autorización, consentimiento y caracterización.
2. Validación de requerimientos y revisión de instrumentos.
3. Preparación de entornos y verificación técnica reproducible.
4. Revisión jurídica/contable y privacidad antes de carga real.
5. Instalación y capacitación, si se aprueban las fases anteriores.
6. Piloto, análisis y consolidación documental.

## 6. Regla de cierre

Cada fila cambia a `[OK]` solo al registrar fecha, responsable, método, resultado real y archivo de evidencia. El inventario del código, un formato en blanco o una planificación no sustituyen evidencia de ejecución.
