# ÍNDICE GENERAL

## SISTEMA DE GESTIÓN DE PERSONAL Y NÓMINA PARA INSTITUCIONES EDUCATIVAS

---

## 1. DATOS GENERALES DEL TRABAJO

| Campo | Dato |
|-------|------|
| Título | Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información |
| Autor | [Nombre del Estudiante] |
| Cédula de identidad | [Número de Cédula] |
| Carrera | [Nombre de la Carrera] |
| Tutor académico | [Nombre del Tutor] |
| Institución | [Nombre de la Universidad o Instituto] |
| Facultad y sede | [Facultad], [Sede] |
| Línea de investigación | Sistemas de información e ingeniería de software |
| Lugar y fecha de presentación | [Ciudad, País], [Fecha] |
| Versión del sistema documentado | 2.82 |

---

## 2. RESUMEN

La presente investigación tuvo como propósito diseñar, desarrollar e implementar un sistema integral de gestión de personal y nómina para instituciones educativas, con el fin de automatizar los procesos administrativos críticos, garantizar la exactitud de los cálculos financieros, ordenar el control documental y proporcionar información oportuna para la toma de decisiones, empleando tecnologías de información accesibles y sostenibles.

El sistema se construyó sobre una arquitectura de capas —presentación, servicios, repositorios, modelos, dominio de nómina y servicios transversales— con Python, SQLAlchemy y CustomTkinter, y se distribuye bajo licencia de código abierto. Comprende diez módulos funcionales que abarcan la gestión de empleados, el control documental con vencimientos, las incidencias y permisos, la asistencia y jornada, los contratos laborales, los préstamos y anticipos, el cálculo de nómina con deducciones y horas extra, las alertas y la configuración institucional. A ello se suman la autenticación con control de acceso por rol, el registro de auditoría, los respaldos, la exportación de datos y la generación de catorce tipos de documentos oficiales en formato PDF. El sistema documentado corresponde a la versión 2.82 y alberga 27 534 líneas de código fuente; su calidad técnica se respalda en una suite de 453 funciones de prueba distribuidas en veinticuatro archivos.

La metodología combinó la investigación aplicada con el desarrollo iterativo y la investigación-acción, apoyándose en instrumentos definidos y validados: entrevistas semiestructuradas, observación directa, cuestionarios de satisfacción y protocolos de usabilidad. La evidencia técnica se verificó de manera directa sobre el repositorio del proyecto, mientras que la medición del impacto en la eficiencia administrativa se obtendrá mediante la implementación piloto en un conjunto de instituciones educativas y se incorporará al capítulo de resultados conforme al diseño metodológico establecido.

**Palabras clave:** gestión de personal, nómina, instituciones educativas, ingeniería de software, arquitectura modular, tecnologías de código abierto, eficiencia administrativa.

---

## 3. ABSTRACT

The purpose of this research was to design, develop and implement a comprehensive personnel and payroll management system for educational institutions, aimed at automating critical administrative processes, ensuring the accuracy of financial calculations, organizing document control and providing timely information for decision-making, through accessible and sustainable information technologies.

The system was built on a layered architecture —presentation, services, repositories, models, payroll domain and cross-cutting services— using Python, SQLAlchemy and CustomTkinter, and it is distributed under an open-source license. It comprises ten functional modules covering personnel records, document control with expiry dates, absences and leave, attendance and working hours, employment contracts, advances and loans, payroll calculation with deductions and overtime, alerts and institutional configuration. These are complemented by role-based authentication and access control, audit logging, backup management, data export and the generation of fourteen types of official documents in PDF format. The documented system corresponds to version 2.82 and comprises 27,534 lines of source code; its technical quality is supported by a suite of 453 test functions distributed across twenty-four files.

The methodology combined applied research with iterative development and action research, supported by defined and validated instruments: semi-structured interviews, direct observation, satisfaction questionnaires and usability protocols. Technical evidence was verified directly on the project repository, whereas the measurement of impact on administrative efficiency will be obtained through pilot implementation in a set of educational institutions and will be incorporated into the results chapter in accordance with the established methodological design.

**Keywords:** personnel management, payroll, educational institutions, software engineering, modular architecture, open-source technologies, administrative efficiency.

---

## 4. INVENTARIO DOCUMENTAL

### 4.1 Documentos principales del informe

| Orden | Documento | Archivo | Contenido |
|-------|-----------|---------|-----------|
| 1 | Proyecto sociotecnológico | `PROYECTO_SOCIAL_TECNOLOGICO.md` | Identificación, diagnóstico social, justificación, objetivos, metodología de trabajo, cronograma, recursos, impacto esperado, riesgos, sostenibilidad y evaluación |
| 2 | Anteproyecto de tesis | `ANTEPROYECTO_TESIS.md` | Datos generales, planteamiento del problema, objetivos, hipótesis y variables, marco teórico preliminar, metodología, cronograma, presupuesto, resultados esperados y aprobación |
| 3 | Capítulo I: Planteamiento del problema | `CAPITULO_I_PLANTEAMIENTO_PROBLEMA.md` | Realidad problemática, formulación del problema, objetivos, justificación, viabilidad, alcances y limitaciones |
| 4 | Capítulo II: Marco teórico | `CAPITULO_II_MARCO_TEORICO.md` | Antecedentes internacionales, nacionales y locales, bases teóricas, bases legales, definición de términos y marco conceptual |
| 5 | Capítulo III: Metodología | `CAPITULO_III_METODOLOGIA.md` | Tipo y diseño de investigación, población y muestra, técnicas e instrumentos, procedimientos, análisis de datos, aspectos éticos, criterios de calidad y plan de contingencia |
| 6 | Capítulo IV: Resultados | `CAPITULO_IV_RESULTADOS.md` | Descripción del sistema, resultados de pruebas técnicas, usabilidad, implementación piloto, análisis comparativo, validación de hipótesis, factores de éxito y limitaciones |
| 7 | Capítulo V: Conclusiones y recomendaciones | `CAPITULO_V_CONCLUSIONES.md` | Conclusiones generales y por objetivo, recomendaciones, reflexiones, contribuciones, limitaciones y conclusiones finales |
| 8 | Bibliografía y anexos | `BIBLIOGRAFIA_ANEXOS.md` | Fuentes bibliográficas y diez anexos con instrumentos, diagramas, guía de usuario, código, resultados de pruebas y presupuesto |
| 9 | Resumen de la investigación | `RESUMEN_INVESTIGACION.md` | Documento autónomo de resumen estructurado para efectos de presentación institucional |
| 10 | Oficio de presentación del compendio y los anexos | `OFICIO_1_PRESENTACION_ANEXOS.md` | Comunicación formal que presenta el compendio del proyecto sociotecnológico y los anexos de la tesis |
| 11 | Oficio de presentación del resumen de la investigación | `OFICIO_2_PRESENTACION_RESUMEN.md` | Comunicación formal que presenta el resumen de la investigación y los archivos definitivos |
| 12 | Índice general | `INDICE_GENERAL.md` | Este documento |

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
│   ├── gui/               interfaz gráfica y diez módulos de navegación
│   ├── models/            entidades del dominio y enumeraciones
│   ├── nomina/            motor de cálculo, prestaciones y seguridad social
│   ├── repositories/      acceso a datos (patrón Repository)
│   ├── services/          reglas de negocio (patrón Service Layer)
│   ├── utils/             seguridad, auditoría, respaldos, PDF y utilidades
│   └── main.py            punto de entrada de la aplicación
├── tests/                 veinticuatro archivos con 453 funciones de prueba
├── updater/               actualización automática del sistema
├── installer/             configuración del instalador para Windows
├── docs/                  portal de documentación del proyecto
├── tools/                 scripts de apoyo
├── TESIS/                 documentación académica
├── requirements.txt       dependencias de ejecución
├── requirements-dev.txt   dependencias de desarrollo
├── pyproject.toml         configuración del proyecto y de las herramientas
├── build.py               script de construcción del ejecutable
├── VERSION                versión vigente del sistema (2.82)
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

### 8.2 Fuentes locales

- Antecedentes locales del Capítulo II, con casos documentados de la región.
- Normativas legales vigentes en la jurisdicción de aplicación (protección de datos, código del trabajo, ley orgánica de educación y reglamento de seguridad de la información).
- Tesis y trabajos de grado del repositorio institucional relacionados con sistemas de información, gestión de personal o nómina.

### 8.3 Evidencia técnica por actualizar

- Re-medición de la cobertura de código con `pytest --cov=src` sobre la versión 2.82.
- Informe de la última ejecución de la suite de pruebas, con número de pruebas ejecutadas, resultado y fecha.

### 8.4 Evidencia del piloto

- Instituciones participantes y su caracterización.
- Usuarios participantes y distribución por perfil.
- Resultados de las pruebas de usabilidad y de las encuestas de satisfacción.
- Mediciones de tiempos y tasas de error antes y después de la implementación.
- Pruebas de rendimiento y de carga.
- Resultados cualitativos y lecciones aprendidas.
- Resultados del tratamiento estadístico y decisión sobre cada hipótesis.

Todos los marcadores `[por completar]` de los capítulos IV y V y de los anexos 3, 8 y 9 deben sustituirse por los valores efectivamente medidos antes de la presentación definitiva.

---

## 9. ÍNDICE DE TABLAS Y FIGURAS

Las tablas numeradas corresponden a los cuadros de resultados del Capítulo IV; los instrumentos y registros de los anexos se presentan como cuadros sin numeración corrida, dado que su contenido depende de la aplicación en campo. Las figuras se numeran según la sección en que aparecen.

### 9.1 Índice de tablas

| Tabla | Título | Fuente |
|-------|--------|--------|
| 4.1 | Distribución del código fuente por capa | Medición sobre `src/`, versión 2.82 |
| 4.2 | Componentes de la capa de presentación | Inspección de `src/gui/` |
| 4.3 | Registro de empleado: contraste proceso manual y sistema | Módulo de empleados y mediciones del piloto |
| 4.4 | Gestión documental: contraste proceso manual y sistema | Módulo documental y mediciones del piloto |
| 4.5 | Generación de nómina: contraste proceso manual y sistema | Motor de nómina y mediciones del piloto |
| 4.6 | Matriz de acceso por rol y módulo | `PermissionChecker` de `src/utils/security.py` |
| 4.7 | Distribución de funciones de prueba por archivo | Recuento sobre `tests/`, versión 2.82 |
| 4.8 | Cobertura de referencia medida en la versión 1.0.4 | `pytest --cov=src` sobre la versión 1.0.4 |
| 4.9 | Protocolo de rendimiento y umbrales de aceptación | Protocolo del apartado 3.4.1.5 |
| 4.10 | Composición de los participantes en las pruebas de usabilidad | Protocolo del Anexo 3 |
| 4.11 | Resultados por tarea de usabilidad | Protocolo del Anexo 3 |
| 4.12 | Satisfacción por dimensión | Cuestionario del Anexo 2 y escala SUS |
| 4.13 | Contraste de percepción antes y después de la implementación | Cuestionario del Anexo 2 |
| 4.14 | Caracterización de las instituciones piloto | Criterios del apartado 3.3.2.1 |
| 4.15 | Tiempos de procesamiento antes y después de la implementación | Observación directa del apartado 3.4.1.2 |
| 4.16 | Tasas de error antes y después de la implementación | Registro institucional de correcciones |
| 4.17 | Indicadores de satisfacción del personal | Cuestionario del Anexo 2 |
| 4.18 | Contraste con soluciones comerciales de gestión de personal | Análisis comparativo y rangos de mercado |
| 4.19 | Contraste con el proceso manual | Análisis estructural y pruebas del sistema |
| 4.20 | Indicadores de la hipótesis general | Umbrales del anteproyecto |

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
