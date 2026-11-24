# ÍNDICE GENERAL

## SISTEMA DE GESTIÓN DE PERSONAL Y NÓMINA PARA INSTITUCIONES EDUCATIVAS

---

## 1. DATOS GENERALES DEL TRABAJO

| Campo | Dato |
|-------|------|
| Título | Desarrollo e implementación de un sistema de base de datos local multiusuario con sincronización híbrida y gestión documental para la administración de personal y calificaciones en instituciones educativas |
| Autor | [Nombre del Estudiante] |
| Cédula de identidad | [Número de Cédula] |
| Carrera | [Nombre de la Carrera] |
| Tutor académico | [Nombre del Tutor] |
| Institución | [Nombre de la Universidad o Instituto] |
| Facultad y sede | [Facultad], [Sede] |
| Línea de investigación | Sistemas de información e ingeniería de software |
| Lugar y fecha de presentación | [Ciudad, País], [Fecha] |
| Versión del sistema documentado | 3.0.1 |

---

## 2. RESUMEN

> **Estado del documento:** resumen de trabajo basado en la revisión del repositorio al 23/11/2026. No sustituye la aprobación del tutor ni constituye un resumen final de tesis; el diagnóstico, las ejecuciones de suites y el piloto siguen pendientes.

Este trabajo describe el diseño y desarrollo de un sistema de gestión de personal, nómina y funciones académicas dirigido a instituciones educativas. El borrador separa los componentes identificados en el repositorio de las funciones cuya compilación, ejecución y aceptación institucional aún no han sido verificadas. No se anticipan mejoras de eficiencia ni exactitud de cálculos.

La inspección documentada identifica código Python para escritorio y sincronización, además de un cliente Android nativo. El árbol contiene 625 funciones Python `test_*` en 38 archivos de prueba y 97 archivos Kotlin con 22.558 líneas y 43 anotaciones `@Test`; estos conteos no equivalen a pruebas ejecutadas ni demuestran calidad o cobertura. No se cuenta con salida de pytest o Gradle en esta revisión. Tampoco se localizaron registros suficientes de diagnóstico comunitario, consentimiento, instalación, capacitación o piloto. La revisión legal es documental y parcial, no constituye dictamen ni certificación de conformidad.

La propuesta metodológica combina inspección técnica y un diseño descriptivo para una eventual fase de campo. Los instrumentos, mediciones pre/post, usabilidad y transferencia permanecen pendientes de revisión, autorización y aplicación. Los resultados deberán completarse únicamente con datos fuente y condiciones de medición registradas.

**Palabras clave:** gestión de personal, nómina, instituciones educativas, ingeniería de software, arquitectura modular, tecnologías de código abierto, eficiencia administrativa.

---

## 3. ABSTRACT

This thesis describes the design and development of a personnel, payroll and academic management system for educational institutions. The current draft distinguishes components found in the repository from functions whose build, execution and institutional acceptance have not been verified. No improvement in efficiency or calculation accuracy is presumed.

Static inspection identified Python code for desktop and synchronization components, as well as a native Android client. The repository contains 625 Python `test_*` functions in 38 test files and 97 Kotlin files with 22,558 lines and 43 `@Test` annotations; these counts do not represent executed tests or demonstrate quality or coverage. No pytest or Gradle execution output is available for this review. Sufficient records of community diagnosis, consent, installation, training or pilot use were not located. The legal review is partial and documentary; it is neither a legal opinion nor a compliance certification.

The proposed methodology combines technical inspection with a descriptive design for a potential field phase. Instruments, pre/post measurements, usability evaluation and transfer remain subject to review, authorization and application. Results must be completed only from source data and documented measurement conditions.

**Keywords:** personnel management, payroll, educational institutions, software engineering, modular architecture, open-source technologies, administrative efficiency.

---

## 4. INVENTARIO DOCUMENTAL

### 4.1 Documentos del compendio previo (requieren armonización)

Los archivos de esta tabla son piezas existentes del compendio anterior. No se certifica que sus contenidos correspondan al estado de evidencia del borrador revisado en `BORRADOR/`; sus afirmaciones deben cotejarse antes de usarlos como entrega vigente.

| Orden | Documento | Archivo | Contenido |
|-------|-----------|---------|-----------|
| 1 | Proyecto sociotecnológico | `PROYECTO_SOCIAL_TECNOLOGICO.md` | Identificación, diagnóstico social, justificación, objetivos, metodología de trabajo, cronograma, recursos, impacto esperado, riesgos, sostenibilidad y evaluación |
| 2 | Anteproyecto de tesis | `ANTEPROYECTO_TESIS.md` | Datos generales, planteamiento del problema, objetivos, hipótesis y variables, marco teórico preliminar, metodología, cronograma, presupuesto, resultados esperados y aprobación |
| 3 | Documento 01: Introducción y planteamiento del problema | `01-introduccion-y-planteamiento.md` | Diagnóstico sociotecnológico con IAP, formulación del problema, objetivos bajo taxonomía de Bloom y criterios SMART, justificación, alcance, hipótesis y variables |
| 4 | Documento 02: Marco teórico y metodológico | `02-marco-teorico-y-metodologico.md` | Antecedentes 2016-2026, bases teóricas, marco legal venezolano, metodología cuantitativa, fases, instrumentos y plan de análisis |
| 5 | Documento 03: Diseño, ingeniería y arquitectura | `03-diseno-ingenieria-y-arquitectura.md` | Requerimientos, casos de uso, arquitectura de red, modelo de datos, subsistema de sincronización, módulo PDF y diseño de métricas |
| 6 | Documento 04: Implementación y despliegue | `04-implementacion-y-despliegue.md` | Fases de construcción, decisiones de codificación, estrategia de pruebas, protocolo de evaluación, despliegue y operación |
| 7 | Capítulo IV: Resultados | `CAPITULO_IV_RESULTADOS.md` | Descripción del sistema, pruebas técnicas, usabilidad, piloto, análisis comparativo, hipótesis y limitaciones; no tratar como sustituto de los estados del borrador y evidencias vigentes |
| 8 | Capítulo V: Conclusiones y recomendaciones | `CAPITULO_V_CONCLUSIONES.md` | Conclusiones generales y por objetivo, recomendaciones, reflexiones, contribuciones, limitaciones y conclusiones finales |
| 9 | Bibliografía y anexos | `BIBLIOGRAFIA_ANEXOS.md` | Fuentes bibliográficas y diez anexos con instrumentos, diagramas, guía de usuario, código, resultados de pruebas y presupuesto |
| 10 | Resumen de la investigación | `RESUMEN_INVESTIGACION.md` | Documento autónomo de resumen estructurado para efectos de presentación institucional |
| 11 | Oficio de presentación del compendio y los anexos | `OFICIO_1_PRESENTACION_ANEXOS.md` | Comunicación formal que presenta el compendio del proyecto sociotecnológico y los anexos de la tesis |
| 12 | Oficio de presentación del resumen de la investigación | `OFICIO_2_PRESENTACION_RESUMEN.md` | Comunicación formal que presenta el resumen de la investigación y los archivos definitivos |
| 13 | Índice general | `INDICE_GENERAL.md` | Este documento |

Los documentos indicados en el inventario principal corresponden al compendio preexistente y deben leerse junto con el borrador de capítulos I a IV de `BORRADOR/`. Para la entrega de este borrador, sus afirmaciones deben armonizarse con los estados de evidencia y métricas vigentes de los legajos; no deben tratarse textos antiguos como resultados actuales.

### 4.3 Borrador de capítulos I a IV con soportes de planificación y evidencia

La carpeta `BORRADOR/` contiene una redacción de trabajo de los capítulos I a IV y sus soportes. Los conteos e inspecciones están fechados al 23/11/2026; las pruebas ejecutadas, la validación comunitaria y la revisión jurídica integral continúan pendientes:

| Documento | Archivo |
|-----------|---------|
| Índice del borrador y regla de integridad | `BORRADOR/INDICE_BORRADOR.md` |
| Capítulo I: Planteamiento del problema | `BORRADOR/CAPITULO_1_PLANTEAMIENTO.md` |
| Capítulo II: Marco referencial | `BORRADOR/CAPITULO_2_MARCO_REFERENCIAL.md` |
| Capítulo III: Marco metodológico | `BORRADOR/CAPITULO_3_MARCO_METODOLOGICO.md` |
| Marco lógico (matriz completa) | `BORRADOR/MARCO_LOGICO.md` |
| Marco operativo (matriz completa) | `BORRADOR/MARCO_OPERATIVO.md` |
| Consolidado de respuestas de los instrumentos | `BORRADOR/RESPUESTAS_INSTRUMENTOS.md` |
| Capítulo IV: Resultados | `BORRADOR/CAPITULO_4_RESULTADOS.md` |
| Software Android (SDEP Móvil) a fondo | `BORRADOR/SOFTWARE_ANDROID.md` |
| Legajos de evidencia (6 documentos) | `BORRADOR/EVIDENCIAS/` |

La regla de integridad del borrador: las cifras técnicas se remiten a mediciones asentadas en los legajos de evidencia; los conteos estáticos no se describen como pruebas ejecutadas y todo dato de campo sin fuente se marca como pendiente.

### 4.2 Documentos de control del proyecto

| Documento | Archivo | Función |
|-----------|---------|---------|
| Registro de control documental | `REGISTRO_CONTROL_DOCUMENTAL.md` | Historial de versiones, estado de cada documento y verificaciones de consistencia |
| Estructura del proyecto de software | `../ESTRUCTURA_PROYECTO_COMPLETO.md` | Descripción de la organización del repositorio |
| Documentación técnica | `../DOCUMENTACION_TECNICA.md` | Arquitectura, instalación, operación y mantenimiento |
| Guía de usuario | `../GUIA_USUARIO.md` | Manual operativo del sistema |
| Notas de desarrollo | `../NOTAS_DESARROLLO.md` | Bitácora de cambios y decisiones técnicas |
| Guía de contribución | `../CONTRIBUTING.md` | Convenciones para el desarrollo colaborativo |

---

## 5. ESTRUCTURA DEL REPOSITORIO DE SOFTWARE

```text
SDEP_CPP5/
├── src/
│   ├── config/            configuración, rutas y sesión de base de datos
│   ├── gui/               interfaz gráfica y nueve módulos de navegación
│   ├── models/            entidades del dominio y enumeraciones
│   ├── nomina/            motor de cálculo, prestaciones y seguridad social
│   ├── repositories/      acceso a datos (patrón Repository)
│   ├── services/          reglas de negocio (patrón Service Layer)
│   ├── utils/             seguridad, auditoría, respaldos, PDF y utilidades
│   └── main.py            punto de entrada de la aplicación
├── tests/                 38 archivos de prueba; 625 funciones test_* inventariadas
├── updater/               actualización automática del sistema
├── installer/             configuración del instalador para Windows
├── docs/                  portal de documentación del proyecto
├── tools/                 scripts de apoyo
├── TESIS/                 documentación académica
├── requirements.txt       dependencias de ejecución
├── requirements-dev.txt   dependencias de desarrollo
├── pyproject.toml         configuración del proyecto y de las herramientas
├── build.py               script de construcción del ejecutable
├── VERSION                versión vigente del sistema (3.0.1)
└── README.md              documentación general del proyecto
```

---

## 6. OFICIOS DE PRESENTACIÓN

Los dos oficios que se relacionan a continuación actúan como marco integrador de la entrega documental. El primero presenta el compendio del proyecto sociotecnológico y el conjunto de los diez anexos de la tesis. El segundo presenta el Resumen de la Investigación en su versión definitiva, junto con los archivos que lo respaldan. Ambos documentos se elaboran en formato de comunicación formal, dirigida a la autoridad académica correspondiente, y detallan de manera explícita el contenido de cada legajo para facilitar su verificación y archivo.

---

## 7. REQUISITOS DE FORMATO PARA LA PRESENTACIÓN

| Elemento | Especificación |
|----------|----------------|
| Tipo de letra | Times New Roman o Arial, cuerpo 12 |
| Interlineado | 1,5 líneas |
| Márgenes | 2,5 cm en los cuatro lados |
| Numeración | Páginas numeradas de forma consecutiva |
| Citas y referencias | Normas APA, séptima edición, o las que establezca la institución |
| Figuras y tablas | Numeradas de forma consecutiva, con título y fuente declarada |
| Anexos | Al final del informe, en el orden consignado en el inventario documental |
| Extensión estimada | 180 a 220 páginas, según el formato institucional |

Los documentos del repositorio se encuentran en formato Markdown; para la presentación oficial se convierten a los formatos exigidos por la institución respetando las especificaciones anteriores.

---

## 8. CONTROL DE DATOS PENDIENTES DE COMPLETACIÓN

Los campos señalados con corchetes en los documentos del informe corresponden a información que solo puede aportar el autor o que depende de la ejecución del piloto. Se relacionan a continuación agrupados por naturaleza, con el fin de que la revisión previa a la presentación resulte verificable.

### 8.1 Datos de identificación institucional

- Nombre completo del autor, número de cédula, carrera, semestre y correo electrónico.
- Nombre, título académico y especialidad del tutor.
- Denominación de la universidad, facultad y sede; línea de investigación.
- Ciudad, país y fechas de inicio, presentación y aprobación.
- Firmas del autor, del tutor, del coordinador de carrera y del director de facultad.

### 8.2 Fuentes y revisión jurídica

- Antecedentes locales del Capítulo II, con referencias bibliográficas verificables del repositorio institucional o de la región.
- Revisión jurídica integral: cotejo de vigencia y reformas, artículos, aplicabilidad institucional y revisión profesional de parámetros y documentos; la evidencia 04 consigna fuentes consultadas para varias referencias, pero no dictamen ni certificación.
- Tesis y trabajos de grado del repositorio institucional relacionados con sistemas de información, gestión de personal o nómina.

### 8.3 Evidencia técnica por actualizar

- Preparar el entorno y registrar la ejecución de `pytest tests/` y cobertura con versión/commit, dependencias, fecha y salidas reales.
- Configurar JDK 17 y Android SDK; registrar compilación y ejecución de `./gradlew :app:assembleDebug :app:testDebugUnitTest`.

### 8.4 Evidencia del piloto

- Instituciones participantes y su caracterización.
- Usuarios participantes y distribución por perfil.
- Resultados de las pruebas de usabilidad y de las encuestas de satisfacción.
- Mediciones de tiempos y tasas de error antes y después de la implementación.
- Pruebas de rendimiento y de carga.
- Resultados cualitativos y lecciones aprendidas.
- Resultados del tratamiento estadístico y decisión sobre cada hipótesis.

Los marcadores pendientes de resultados, capítulos y anexos deben completarse únicamente con registros fuente autorizados; de no realizarse las actividades de campo, deben mantenerse como limitaciones explícitas.

---

## 9. ÍNDICE DE TABLAS Y FIGURAS

Las tablas numeradas corresponden a los cuadros de resultados del Capítulo IV; los instrumentos y registros de los anexos se presentan como cuadros sin numeración corrida, dado que su contenido depende de la aplicación en campo. Las figuras se numeran según la sección en que aparecen.

### 9.1 Índice de tablas

| Tabla | Título | Fuente/estado |
|-------|--------|---------------|
| 4.1 | Componentes del repositorio y mediciones de código | Evidencias 01 y 06; inventario estático |
| 4.2 | Distribución de líneas Python por capa | Evidencia 01; conteo estático de `src/` |
| 4.3 | Distribución de funciones de prueba por archivo | Evidencia 02; inventario, no ejecución |
| 4.4 | Estructura propuesta para resultados de campo | Pendiente de autorización y aplicación; no contiene resultados |

### 9.2 Índice de figuras

| Figura | Título | Ubicación |
|--------|--------|-----------|
| 2.1 | Modelo conceptual por capas del sistema | Apartado 2.6.1 del Capítulo II |
| 6.1 | Arquitectura de capas del sistema | Anexo 4 |
| 6.2 | Modelo entidad-relación | Anexo 4 |
| 6.3 | Flujo de generación de nómina | Anexo 4 |
| 6.4 | Flujo de autenticación y control de acceso | Anexo 4 |
| 6.5 | Flujo de respaldo y restauración de la base de datos | Anexo 4 |

---

**El Autor**
[Nombre del Estudiante]

**Institución**
[Nombre de la Institución]

**Versión del documento:** 2.0
