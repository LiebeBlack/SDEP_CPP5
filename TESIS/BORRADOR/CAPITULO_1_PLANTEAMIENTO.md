# CAPÍTULO I — PLANTEAMIENTO DEL PROBLEMA

## 1.1 Contexto del estudio

El presente trabajo se inscribe en el ámbito del proyecto sociocomunitario y tiene como objeto el desarrollo e implementación de un sistema de base de datos local multiusuario con sincronización híbrida y gestión documental para la administración de personal y calificaciones en instituciones educativas. El sistema objeto de estudio es el Sistema de Gestión de Personal y Nómina para Instituciones Educativas (en adelante, SDEP), en su versión 3.0.1, construido en Python con SQLAlchemy y CustomTkinter, acompañado de un cliente nativo Android y de un nodo central de sincronización entre puestos.

El proyecto toma como ámbito previsto a instituciones educativas del entorno comunitario de la institución de estudios del investigador. El expediente disponible no contiene caracterizaciones que permitan afirmar qué procedimientos administrativos, herramientas, infraestructura o limitaciones presenta cada institución. El uso de expedientes físicos, planillas, hojas de cálculo y procesos manuales se plantea como una posibilidad a verificar durante el diagnóstico, no como una descripción comprobada de todas las instituciones.

Como problema de diseño, el proyecto considera escenarios donde los recursos, la conectividad o las condiciones de contratación de servicios informáticos pueden limitar la adopción de soluciones comerciales o remotas. La existencia y relevancia de esos factores deben determinarse en cada institución; no se presume que las participantes carezcan de capacidad técnica o de negociación. La selección de operación local y sincronización híbrida se plantea como respuesta técnica a validar, no como sustituto de un análisis institucional.

### 1.1.1 Caracterización preliminar del problema y estado de la evidencia

La formulación del proyecto identificó cinco áreas que requieren estudio en las instituciones participantes: control del expediente documental, cálculo de nómina, registro de incidencias, gestión académica y respaldo y trazabilidad. En el expediente revisado para este borrador no se localizaron fichas de observación firmadas, actas de devolución ni transcripciones que acrediten una observación directa o conversaciones de campo; por ello, las siguientes descripciones se presentan como problemas por indagar y no como hallazgos empíricos ya comprobados. La caracterización y los requerimientos deberán confirmarse con instrumentos de campo antes de atribuirlos a una institución concreta.

Como hipótesis diagnóstica, se plantea que algunos expedientes de personal podrían mantenerse en papel o archivos dispersos sin un registro consolidado de vencimientos. También se examinará si los cálculos salariales y las incidencias se procesan manualmente o en hojas de cálculo, cómo se aprueban y vinculan con la nómina, y qué evidencia conserva la institución sobre sus cambios. En el ámbito académico se verificará cómo se registran estudiantes, inscripciones y notas y cómo se consolidan por periodo. Finalmente, se determinará qué respaldos existen, dónde se custodian y si puede identificarse quién realizó cada modificación.

La ficha de observación prevista en `RESPUESTAS_INSTRUMENTOS.md` y la matriz de requerimientos de `EVIDENCIAS/EVIDENCIA_03_MATRIZ_MODULOS.md` permitirán documentar cada proceso, la institución, la fecha y la fuente. Hasta que se complete esa fase, los cinco ejes son categorías de indagación del proyecto y no resultados de una investigación-acción participativa ejecutada.

### 1.1.2 Marco contextual del problema

El problema se organiza para su indagación en tres planos complementarios.

En el plano institucional, se analizarán los procesos de gestión de personal y su relación con obligaciones laborales, disponibilidad documental y control de contratos. Los efectos concretos dependen de la operación y la normativa aplicable a cada institución.

En el plano tecnológico, se examinará si las herramientas actualmente utilizadas —que podrían incluir hojas de cálculo, mensajería o documentos digitalizados— ofrecen validaciones, control de acceso, registro de cambios y coherencia entre expedientes, nómina y datos académicos. No se atribuyen deficiencias a una institución sin observación registrada.

En el plano sociocomunitario, el diseño de transferencia contempla documentación y capacitación para que la institución pueda evaluar una operación sostenible. La entrega, instalación, capacitación y capacidad de funcionamiento independiente siguen pendientes de evidencia; el reglamento universitario determinará además los requisitos de acreditación del servicio comunitario.

## 1.2 Formulación del problema

Sobre la base del diagnóstico expuesto, el problema de investigación se formula de la siguiente manera:

**¿Qué requerimientos funcionales y técnicos debe atender un sistema local multiusuario con sincronización híbrida para apoyar la gestión de personal, nómina y calificaciones de las instituciones educativas participantes, y qué resultados técnicos y de campo se observan durante su validación?**

La pregunta organiza el estudio en dos etapas: derivar y documentar requerimientos a partir de un diagnóstico participativo verificable y evaluar el producto mediante pruebas técnicas y mediciones de campo. La eficiencia (tiempo por tarea), la exactitud operativa (errores registrados bajo un criterio explícito) y la trazabilidad (identificación de quién, cuándo y qué modificó, donde el registro disponible lo permita) son dimensiones por medir. No se presume una mejora antes del piloto ni se afirma conformidad jurídica integral.

## 1.3 Objetivos de la investigación

### 1.3.1 Objetivo general

Desarrollar un sistema de base de datos local multiusuario con sincronización híbrida y gestión documental para apoyar la administración de personal y calificaciones en instituciones educativas, automatizar procesos seleccionados y permitir evaluar el control documental, la exactitud de los cálculos y la disponibilidad de información, empleando tecnologías de información cuyo acceso y sostenibilidad deberán valorarse en el contexto institucional.

### 1.3.2 Objetivos específicos

1. **Diagnosticar** el estado actual del proceso administrativo de gestión de personal, documental, de incidencias, de contratos y de calificaciones en las instituciones educativas participantes, mediante investigación-acción participativa.
2. **Analizar y especificar** los requerimientos funcionales y no funcionales del sistema a partir del diagnóstico, contrastando cada requerimiento con la legislación laboral, educativa y de infraestructura tecnológica aplicable.
3. **Diseñar** la arquitectura del software por capas, el modelo de datos, el mecanismo de sincronización híbrida entre puestos y el subsistema de generación de documentos oficiales.
4. **Implementar** los módulos de gestión de personal, documentos, incidencias, contratos, nómina, configuración, estudiantes y calificaciones, junto con los componentes de acceso y sincronización previstos.
5. **Verificar** el comportamiento del software mediante inspección, pruebas automatizadas ejecutadas y registro de resultados reproducibles.
6. **Preparar y evaluar** la transferencia a las instituciones mediante documentación, capacitación y, si existe autorización y disponibilidad, una operación piloto con instrumentos de campo.

El objetivo de diseño y desarrollo se corresponde con los artefactos técnicos localizados en el repositorio. La ejecución verificable del diagnóstico participativo, la validación institucional de requerimientos, la instalación, la capacitación y el piloto permanecen pendientes de sus registros de campo. La suite Python y el cliente Android están inventariados, pero su ejecución actual no se declara aprobada sin registrar las salidas de las pruebas. La matriz completa de objetivos, productos, actividades e indicadores se presenta en `MARCO_LOGICO.md` y la matriz operativa en `MARCO_OPERATIVO.md`.

## 1.4 Justificación de la investigación

**Justificación social.** La gestión ordenada de expedientes laborales y registros académicos puede apoyar el trabajo administrativo y la disponibilidad de información para usuarios institucionales. El beneficio concreto para trabajadores, estudiantes y comunidad deberá evaluarse en el uso real; la posibilidad de reutilizar el software dependerá de su licencia, adaptación, soporte y aceptación por cada institución.

**Justificación técnica.** El repositorio contiene tecnologías como Python, SQLAlchemy, SQLite, CustomTkinter y Kotlin, así como separación entre presentación, servicios, repositorios y dominio. Esta estructura ofrece un punto de partida inspeccionable para mantenimiento y pruebas; la suite no se ha ejecutado en el entorno de esta revisión. La operación local con sincronización híbrida se propone para contextos de conectividad variable, cuya pertinencia y desempeño deben confirmarse con las instituciones.

**Justificación normativa.** El sistema trata materias laborales, tributarias, educativas y de datos personales para las que existen normas venezolanas pertinentes. El capítulo II identifica algunas de ellas y la evidencia 04 registra fuentes consultadas. No se ha certificado que el software, sus parámetros o documentos cumplan íntegramente ese marco; la institución deberá revisar la aplicabilidad, vigencia y configuración con asesoría competente.

**Justificación económica.** El uso de componentes abiertos puede evitar ciertos costos de licenciamiento, pero la institución deberá valorar instalación, adaptación, soporte, capacitación, seguridad, infraestructura y mantenimiento. No se cuenta con un análisis comparativo de costos ni con datos para afirmar que la implantación sea gratuita o que todos los recursos estén cubiertos por el servicio comunitario.

**Justificación académica.** El trabajo articula el desarrollo de software y la elaboración de instrumentos con una evaluación reproducible. La contribución académica final deberá incluir la revisión del tutor y, si se realizan, evidencias de validación y transferencia; no se afirma que ya exista capacidad instalada en una comunidad.

## 1.5 Alcance del trabajo

El objeto técnico inspeccionado comprende:

1. El sistema de escritorio SDEP cuyo archivo `VERSION` declara `3.0.1`, con módulos de personal, documentos, incidencias, contratos, nómina, configuración y gestión académica, entre otros.
2. El cliente móvil Android y sus pantallas, repositorios, persistencia local, sincronización y flujos de adjuntos inspeccionados.
3. El nodo central de sincronización y los módulos presentes en `sync_agent/`.
4. La documentación técnica y de usuario localizada en el repositorio.
5. Las pruebas Python y Android inventariadas, cuya ejecución actual no está registrada en este borrador.

Este alcance describe componentes presentes, no afirma instalación, aceptación, transferencia ni calidad certificada.

Queda pendiente para una fase autorizada de campo la evaluación de tiempos, errores, usabilidad y percepción en instituciones reales. Este borrador no reporta una instalación ni un piloto. También queda fuera el análisis de funcionalidades posteriores al estado del repositorio inventariado en este documento.

## 1.6 Límites del estudio

1. **Límite geográfico:** el ámbito comunitario previsto es el entorno de la institución de estudios; mientras no existan consentimientos y registros, no se identifican instituciones como participantes efectivos ni se generalizan resultados.
2. **Límite temporal:** el inventario técnico se refiere a la versión 3.0.1 y a los cambios Android asentados en la evidencia 06; cualquier cambio posterior exige nueva medición.
3. **Límite normativo:** las referencias legales identifican normas pertinentes; el cotejo documental no equivale a dictamen de aplicabilidad ni a certificación de cumplimiento por el software.
4. **Límite de evidencia:** la aplicación de instrumentos, la transferencia y la validación de campo permanecen pendientes cuando no se adjunte el registro fuente; no se incluyen valores simulados.

## 1.7 Organización del trabajo

El trabajo se organiza en cuatro capítulos más los soportes de planificación y evidencia. El Capítulo I plantea el problema y el estado de la evidencia disponible. El Capítulo II desarrolla el marco referencial y las normas pertinentes identificadas. El Capítulo III expone el diseño metodológico, con instrumentos de campo aún pendientes de aplicación. El Capítulo IV presenta inventarios técnicos reproducibles y separa las verificaciones pendientes de los resultados empíricos no disponibles. Acompañan al cuerpo el marco lógico, el marco operativo, las evidencias, el consolidado de instrumentos y la bibliografía.

---
**Fuente de las afirmaciones de este capítulo:** inspección del repositorio y de los documentos existentes `README.md`, `GUIA_USUARIO.md` y `DOCUMENTACION_TECNICA.md`; mediciones reproducibles asentadas en `EVIDENCIAS/`. El diagnóstico empírico, los consentimientos y los registros de campo no se encontraron en el material disponible para este borrador y permanecen pendientes.
