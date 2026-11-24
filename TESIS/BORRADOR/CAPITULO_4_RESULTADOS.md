# CAPÍTULO IV — RESULTADOS

Este capítulo presenta los resultados reproducibles de la inspección estática del repositorio y separa de ellos las pruebas ejecutadas y la validación comunitaria. El conteo de funciones de prueba no significa que la suite haya pasado. No se encontraron registros fuente que permitan reportar un diagnóstico empírico, transferencia o resultados de campo; por tanto, se consignan como pendientes y no se interpretan como resultados.

## 4.1 Estado del diagnóstico comunitario

No se localizaron en el expediente fichas de observación aplicadas, consentimientos, actas de devolución ni entrevistas que permitan reportar resultados empíricos de la fase diagnóstica. Las cinco áreas descritas en el Capítulo I son categorías preliminares de indagación y no hallazgos confirmados de instituciones participantes. La evidencia 03 permite inspeccionar la correspondencia entre esas áreas de diseño y los módulos del repositorio, pero no prueba que los requerimientos hayan sido derivados, priorizados o validados por la comunidad. El objetivo de diagnóstico permanece pendiente de sus medios de verificación.

## 4.2 Resultados del desarrollo del sistema

### 4.2.1 Componentes inspeccionados

El repositorio declara la versión base 3.0.1 y contiene componentes de escritorio, sincronización y Android. La existencia de código y documentación se verificó por inspección; la instalación, transferencia y aceptación comunitaria no se acreditan en este expediente. Los cambios Android incorporados con posterioridad deben asociarse a una revisión o commit reproducible y no confundirse con la línea base original 3.0.1.

| Componente | Medición | Rol en la solución |
|-----------|----------|--------------------|
| Sistema de escritorio (`src/`) | 35.797 líneas Python en 7 capas | Código presente; operación institucional no verificada |
| Nodo de sincronización (`sync_agent/`) | 11.443 líneas Python | Código presente; despliegue e integración no verificados |
| Cliente Android (`android/`) | 97 archivos Kotlin, 22.558 líneas (21.892 de producción y 666 de pruebas; 43 anotaciones `@Test`) | Componente móvil inspeccionado; compilación y pruebas pendientes; detalle y limitaciones en `SOFTWARE_ANDROID.md` |

**Tabla 4.1. Componentes del repositorio y mediciones de código**

*Fuente: medición reproducida el 23/11/2026 para Android (evidencia 06) y mediciones asentadas en la evidencia 01 para Python. Los comandos de conteo y el alcance temporal constan en cada legajo.*

### 4.2.2 Arquitectura por capas

La estructura del árbol organiza las líneas contabilizadas según las capas indicadas; este conteo no confirma por sí solo la calidad de sus límites o responsabilidades:

| Capa | Líneas | Proporción |
|------|--------|------------|
| Presentación (`src/gui`) | 14.701 | 41,1 % |
| Utilidades transversales (`src/utils`) | 6.457 | 18,0 % |
| Servicios (`src/services`) | 5.512 | 15,4 % |
| Repositorios (`src/repositories`) | 2.692 | 7,5 % |
| Modelos (`src/models`) | 1.987 | 5,6 % |
| Configuración (`src/config`) | 1.719 | 4,8 % |
| Dominio de nómina (`src/nomina`) | 1.513 | 4,2 % |
| **Total** | **35.797** | 100 % |

**Tabla 4.2. Distribución de líneas Python por capa**

*Fuente: evidencia 01, conteo estático de `src/`.*

La capa de presentación concentra la mayor proporción del código contabilizado. La distribución por líneas describe tamaño relativo, pero no demuestra por sí misma calidad, mantenibilidad ni que la institución pueda sostener el sistema tras una transferencia.

### 4.2.3 Módulos funcionales identificados

La inspección del catálogo de navegación y los archivos asociados identifica nueve módulos: dashboard, empleados, documentos, incidencias, contratos, nómina, configuración, estudiantes y calificaciones. El inventario describe componentes y referencias a pruebas; sin ejecución registrada no se afirma que cada módulo haya pasado sus pruebas o que el objetivo funcional esté validado en operación.

### 4.2.4 Motor de cálculo de nómina

El código del dominio de nómina contiene módulos de cálculo de salario, horas extra, seguridad social, impuesto sobre la renta, prestaciones y finiquito. Esta inspección de estructura no certifica la corrección legal o contable de las fórmulas. Los parámetros, supuestos, redondeos y resultados deben contrastarse caso por caso con la normativa vigente y con revisión profesional antes de utilizarse para liquidaciones reales.

### 4.2.5 Matriz de correspondencia de componentes

| Área preliminar de indagación | Componente asociado | Estado de la evidencia |
|-------------------------------|--------------------|------------------------|
| Expedientes y vencimientos | Documentos | Código y pruebas referenciados en evidencia 03; sin diagnóstico institucional |
| Nómina | Motor y gestión de pagos | Código identificado; pruebas no ejecutadas; revisión profesional pendiente |
| Incidencias | Módulo de incidencias y soporte documental | Código inspeccionado; uso e integración pendientes |
| Gestión académica | Estudiantes y calificaciones | Módulos identificados; aceptación y procesos reales no validados |
| Respaldo y trazabilidad | Roles, auditoría y respaldo de escritorio | Código/documentación identificados; operación y recuperación no probadas |
| Adjuntos Android | Documentos e incidencias | Código agregado e inspeccionado; build e integración nodo pendientes |

## 4.3 Resultados de las pruebas técnicas

### 4.3.1 Suite de pruebas

El inventario estático actual cuenta 625 funciones Python con prefijo `test_` en 38 archivos de pruebas; `conftest.py` configura la suite. Las cifras describen definiciones, no ejecuciones exitosas. La tabla reproduce el conteo actual por archivo; no mide cobertura, suficiencia ni calidad de las pruebas.

**Tabla 4.3. Distribución de las funciones de prueba por archivo**

| Área / archivo | Funciones `test_*` |
|----------------|-------------------:|
| `test_academico.py` | 18 |
| `test_auth.py` | 16 |
| `test_auto_updater.py` | 20 |
| `test_backups.py` | 9 |
| `test_build.py` | 5 |
| `test_configuracion.py` | 9 |
| `test_contratos.py` | 18 |
| `test_credenciales.py` | 15 |
| `test_descubrimiento_udp.py` | 3 |
| `test_document_manager.py` | 15 |
| `test_documentos.py` | 7 |
| `test_empleados.py` | 18 |
| `test_gui_smoke.py` | 22 |
| `test_helpers.py` | 66 |
| `test_incidencias.py` | 8 |
| `test_migraciones.py` | 6 |
| `test_nomina_motor.py` | 27 |
| `test_notas.py` | 17 |
| `test_pagos.py` | 9 |
| `test_pdf_plantillas.py` | 13 |
| `test_permisos_modulos.py` | 4 |
| `test_registros_moviles.py` | 8 |
| `test_reportes.py` | 17 |
| `test_security.py` | 65 |
| `test_servidor_embebido.py` | 8 |
| `test_settings_version.py` | 4 |
| `test_sync_academico.py` | 6 |
| `test_sync_agente.py` | 7 |
| `test_sync_api_permisos.py` | 22 |
| `test_sync_auth_api.py` | 14 |
| `test_sync_captura.py` | 8 |
| `test_sync_cli.py` | 24 |
| `test_sync_integracion.py` | 10 |
| `test_sync_merge.py` | 21 |
| `test_sync_servidor.py` | 24 |
| `test_theme.py` | 15 |
| `test_tokens_sesion.py` | 11 |
| `test_validators.py` | 36 |
| **Total: 38 archivos de prueba** | **625** |

*Fuente: `grep -RhoE '^[[:space:]]*(async )?def test_[A-Za-z0-9_]+' tests --include='test_*.py' | wc -l` y conteo por archivo, inspección del árbol el 23/11/2026. El inventario se conserva en la evidencia 02.*

### 4.3.2 Ejecución de la suite y cobertura

Ejecución y cobertura: `[pendientes]`. No se completará esta sección hasta contar con un intérprete Python, dependencias instaladas, versión/commit identificados y salida conservada de los comandos.

No se dispone de un registro de ejecución de pytest ni de un informe de cobertura para la revisión actual. En consecuencia, no se afirma que la suite haya pasado ni se adopta una decisión de aceptación técnica a partir del inventario. Tampoco se dispone de compilación o ejecución de pruebas Android: el entorno consultado no tiene Java/JDK ni Android SDK disponibles.

## 4.4 Fuentes legales consultadas y alcance de la revisión

La evidencia 04 registra identificaciones y fuentes públicas consultadas para algunas normas citadas en el capítulo II. Se verificaron números/fechas de publicación para las normas que allí se detallan; no se realizó una auditoría artículo por artículo, dictamen de aplicabilidad institucional, revisión de todas las normas conexas ni evaluación de conformidad del software. Los parámetros laborales y tributarios y las obligaciones sobre datos deben ser revisados por la institución y sus asesores antes de la puesta en producción.

## 4.5 Validación de campo: estado y estructura pendiente

Los análisis siguientes corresponden a una eventual fase de campo. No se encontraron respuestas ni registros de aplicación; por tanto, no son resultados obtenidos. Si se autoriza y ejecuta el piloto, se completarán con los datos fuente, número de observaciones, perfil e institución seudonimizados y condiciones de medición.

**Tabla 4.4. Estructura propuesta para resultados de campo (pendientes)**

| Resultado propuesto | Contenido | Estado |
|---------------------|-----------|--------|
| Caracterización | Institución, procesos, equipo y conectividad, en forma anonimizada | `[pendiente]` |
| Tiempos | Mediciones por tarea y etapa, con N y dispersión | `[pendiente]` |
| Errores | Conteo y denominador según definición aprobada | `[pendiente]` |
| Usabilidad | Éxito, tiempo y dificultad por tarea/persona | `[pendiente]` |
| Percepción | Respuestas del instrumento revisado y, si procede, SUS | `[pendiente]` |

### 4.5.1 Criterios de análisis de los resultados de campo

- **Tiempo por tarea:** describir mediciones pre/post, con cantidad de observaciones, mediana, dispersión y condiciones comparables; no hay un umbral de mejora confirmado.
- **Errores:** definir evento y denominador; separar errores prevenidos por validación, errores de salida y correcciones posteriores.
- **Control documental:** informar la proporción solo para documentos cargados a los que corresponda una fecha de vencimiento y exista un estado de seguimiento verificable.
- **Usabilidad y percepción:** informar SUS y respuestas únicamente después de revisar los instrumentos y conservar registros reales.
- El diseño pretest-postest sin grupo de comparación permitirá describir cambios, no atribuirlos de manera concluyente al software. Todo cálculo estadístico debe indicar muestra, método y supuestos.

*Fuente: propuesta de análisis; no hay resultados medidos.*

### 4.5.2 Inventario del componente móvil

El inventario Android actual contiene 97 archivos Kotlin y 22.558 líneas (88 archivos de producción con 21.892 líneas; 9 archivos de pruebas con 666 líneas y 43 anotaciones `@Test`). Estos valores se reproducen con los comandos del legajo 06. Se inspeccionaron configuración de Gradle y manifiesto, pero no se pudo compilar ni ejecutar las pruebas en el entorno disponible por ausencia de Java/JDK y Android SDK; por ello no se declara verificada la calidad de construcción. El detalle funcional y las limitaciones se documentan en `SOFTWARE_ANDROID.md`.

## 4.6 Análisis de los resultados frente a los objetivos

| Objetivo específico | Resultado observado/pendiente | Evidencia |
|---------------------|----------------------|-----------|
| 1. Diagnosticar | Pendiente: faltan fichas, actas y registros que acrediten el diagnóstico participativo | Evidencia 05 y respuestas de campo pendientes |
| 2. Analizar requerimientos | Hay documentación técnica y matriz de módulos; su derivación y validación comunitaria no están documentadas. Fuentes legales corregidas a nivel de identificación, sin dictamen de conformidad | Evidencias 03 y 04 |
| 3. Diseñar la arquitectura | Código y documentación inspeccionados; los conteos son inventario y no una prueba de calidad o mantenibilidad | Evidencia 01 |
| 4. Implementar módulos | Se inspecciona el catálogo de nueve módulos; no consta prueba funcional ejecutada ni transferencia institucional | Evidencia 03 |
| 5. Validar | 625 funciones Python inventariadas y 43 anotaciones Android; ejecuciones y cobertura pendientes; piloto de campo pendiente | Evidencias 02, 05 y 06 |
| 6. Documentar y transferir | Documentación presente en el repositorio; entrega, capacitación e instalaciones no acreditadas | Matriz operativa y registros pendientes |

## 4.7 Discusión

Los resultados técnicos del primer plano del capítulo sustentan dos afirmaciones que conviene separar.

La evidencia disponible permite describir el producto y sus componentes, no concluir completitud frente a requerimientos comunitarios, mantenibilidad independiente ni sostenibilidad después de una transferencia. La matriz de módulos es una correspondencia del diseño con áreas de problema planteadas; al faltar fichas de diagnóstico y validación de participantes, no prueba que esos requerimientos hayan surgido de un proceso comunitario. La suite inventariada aporta una base para validación, pero sin su ejecución y sin evaluación de cobertura no acredita que el sistema esté libre de defectos.

Los resultados de campo no están disponibles en el expediente y no permiten aceptar ni rechazar una mejora de eficiencia, exactitud, usabilidad o satisfacción. El diseño propuesto deberá revisarse antes del piloto: emparejamiento de tareas, criterios de conteo de errores, protección de datos personales y equivalencia de condiciones. Anticipar resultados sería sustituir evidencia por expectativa.

## 4.8 Limitaciones de los resultados

1. Las métricas del software corresponden a la fecha de medición; cualquier evolución del repositorio exige re-medición con los comandos de la evidencia 01.
2. La ejecución completa de la suite y la cobertura Python, así como la compilación y pruebas Android, no están registradas en este entorno; el capítulo no las anticipa.
3. Los resultados de campo dependen de la ejecución de la fase III según la matriz operativa; su ausencia no se suple con estimaciones.
4. Se contrastaron referencias bibliográficas/números de Gaceta de varias normas con registros legislativos y fuentes institucionales. Quedan pendientes revisión integral de vigencia y reformas conexas, artículos concretos, aplicabilidad a cada institución y revisión jurídica de fórmulas y plantillas; no hay certificación de cumplimiento.

## 4.9 Conclusiones parciales

1. La inspección acredita la existencia de código y documentación para los componentes de escritorio, sincronización y Android, y permite registrar sus métricas de inventario. No acredita por sí sola funcionamiento correcto en campo, aceptación institucional ni transferencia.
2. La suite Python (625 funciones inventariadas) y las pruebas Android (43 anotaciones `@Test`) no tienen resultado de ejecución registrado en este borrador; no se concluye aprobación técnica.
3. Diagnóstico participativo, instalación, capacitación, revisión de instrumentos y piloto permanecen pendientes. En consecuencia, no se concluye que el sistema haya mejorado tiempos, exactitud, control documental, usabilidad o satisfacción.

---
**Fuentes de este capítulo:** inventarios y bitácora de `EVIDENCIAS/`, código y documentación inspeccionados. El consolidado de instrumentos no contiene respuestas de campo.
