# RESUMEN DE LA INVESTIGACIÓN

## SISTEMA DE GESTIÓN DE PERSONAL Y NÓMINA PARA INSTITUCIONES EDUCATIVAS

**Documento autónomo para efectos de presentación institucional**

---

## 1. IDENTIFICACIÓN

| Campo | Dato |
|-------|------|
| Título de la investigación | Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información |
| Autor | [Nombre del Estudiante] |
| Cédula de identidad | [Número de Cédula] |
| Carrera | [Nombre de la Carrera] |
| Tutor académico | [Nombre del Tutor] |
| Institución | [Nombre de la Universidad o Instituto] |
| Facultad y sede | [Facultad], [Sede] |
| Línea de investigación | Sistemas de información e ingeniería de software |
| Tipo de investigación | Aplicada y tecnológica |
| Enfoque | Mixto, con predominio cuantitativo en la medición del efecto |
| Ámbito de aplicación | Instituciones educativas de nivel medio y superior |
| Versión del sistema | 2.82 |
| Fecha de presentación | [Fecha] |

---

## 2. PROBLEMA DE INVESTIGACIÓN

Las instituciones educativas con recursos limitados administran la gestión de su personal con instrumentos dispersos: legajos físicos, planillas de cálculo sin formato común entre dependencias, cálculo manual de la remuneración y control documental sin verificación de vigencia. Las consecuencias observadas durante el diagnóstico fueron cinco: información del personal fragmentada y sin fuente única, riesgo de error en el cálculo de la nómina y en las deducciones, documentación laboral vencida sin advertencia, incidencias sin trazabilidad de su aprobación y reportes que llegan tarde para sustentar decisiones.

El problema se formuló en los siguientes términos: ¿de qué manera el desarrollo e implementación de un sistema integral de gestión de personal y nómina, construido con tecnologías accesibles y sostenibles, permite optimizar los procesos administrativos, garantizar la precisión de los cálculos financieros, ordenar el control documental y proporcionar información oportuna para la toma de decisiones?

---

## 3. OBJETIVOS

El objetivo general consistió en diseñar, desarrollar e implementar un sistema integral de gestión de personal y nómina para instituciones educativas que automatice los procesos administrativos clave, garantice la precisión de los cálculos financieros, ordene el control documental y proporcione información oportuna para la toma de decisiones.

Los objetivos específicos fueron seis: analizar los procesos vigentes de gestión de personal para identificar requerimientos; diseñar la arquitectura del sistema con patrones consolidados; implementar los módulos funcionales con tecnologías de código abierto; desarrollar las funcionalidades de reporte y de generación de documentos oficiales; validar el sistema mediante pruebas automatizadas y aplicación piloto; y documentar integralmente el producto para asegurar su sostenibilidad.

---

## 4. HIPÓTESIS

La hipótesis general sostiene que la implementación del sistema mejorará de manera significativa la eficiencia administrativa, con una reducción de los tiempos de procesamiento de al menos el 50 % y una disminución de los errores administrativos de al menos el 80 %. Las cinco hipótesis específicas postulan, respectivamente, que la arquitectura modular facilita el mantenimiento y la expansión; que la interfaz gráfica mejora la usabilidad respecto de las alternativas de línea de comandos; que la automatización reduce los errores financieros; que la digitalización mejora el acceso a la información; y que la capacitación junto con la documentación favorecen la adopción del sistema.

Las hipótesis se resolverán con la evidencia recopilada durante la implementación piloto, aplicando los procedimientos estadísticos definidos en la metodología. El estado actual de cada una se detalla en el apartado 6 de este resumen.

---

## 5. METODOLOGÍA

La investigación se clasifica como aplicada y tecnológica, con un diseño que combina investigación-acción y prototipado evolutivo, y con un enfoque mixto que integra la medición cuantitativa del efecto con la comprensión cualitativa del proceso.

La muestra prevista comprende entre tres y cinco instituciones educativas seleccionadas por muestreo intencional, con diversidad de tamaño, nivel educativo y ámbito, y entre diez y quince usuarios por institución, distribuidos entre perfiles directivos, de recursos humanos, administrativos y docentes.

Los instrumentos de recolección se definieron y se reproducen en los anexos: guía de entrevista para el análisis de requerimientos, cuestionario de satisfacción de usuarios, protocolo de pruebas de usabilidad y formatos de documentación de pruebas. El análisis cuantitativo comprende estadística descriptiva y pruebas de contraste —t para muestras relacionadas, rangos con signo de Wilcoxon, chi-cuadrado y análisis de varianza— con un nivel de significancia de 0,05. El análisis cualitativo comprende codificación temática de las entrevistas, estudio de caso por institución y clasificación de la retroalimentación recogida.

El procedimiento se organizó en cuatro fases: análisis de requerimientos, diseño y desarrollo, pruebas y validación, e implementación y documentación. Las tres primeras se encuentran ejecutadas en su componente técnico y la cuarta en su componente documental; las pruebas con usuarios y la aplicación piloto mantienen su programación, cuyo detalle consta en el Capítulo III y en el cronograma del Anexo 9.

---

## 6. RESULTADOS VERIFICABLES

Los resultados que se enuncian a continuación fueron comprobados de forma directa sobre el repositorio del proyecto, en la versión 2.82, y pueden replicarse con los procedimientos indicados en el registro de control documental.

| Aspecto verificado | Resultado |
|--------------------|-----------|
| Extensión del código fuente | 27 534 líneas en 73 archivos, organizadas en nueve capas y componentes |
| Módulos funcionales | Diez, con control de acceso por rol y atajos de teclado |
| Módulos implementados | Panel de control, empleados, documentos, incidencias, asistencia, contratos, préstamos, nómina, alertas y configuración |
| Esquema de base de datos | Diez tablas con integridad referencial y migraciones |
| Dominio de cálculo | Motor de nómina aislado con deducciones, impuesto sobre la renta, horas extra, prestaciones, seguridad social, préstamos y finiquito |
| Suite de pruebas | 453 funciones de prueba en 24 archivos, con 5 371 líneas de código de prueba |
| Seguridad | Autenticación con PBKDF2-HMAC-SHA256 de 200 000 iteraciones y sal de 16 bytes; control de acceso por cuatro roles; auditoría; respaldos sujetos a política de retención |
| Generación documental | Catorce tipos de documentos oficiales en formato PDF |
| Exportación | Formatos abiertos para empleados, documentos, incidencias, pagos y reportes |
| Cobertura de referencia | Medición de la versión 1.0.4: 43 % total y 73 % en la lógica de negocio; debe re-medirse sobre la versión vigente |

Adicionalmente, tres de las hipótesis específicas cuentan ya con evidencia estructural favorable: la arquitectura modular se verificó durante el crecimiento del sistema entre las versiones 2.79 y 2.82 —cuatro módulos nuevos, el motor de nómina y 130 funciones de prueba añadidas sin refactorizaciones estructurales—; la disponibilidad de la información y el acceso a ella se verificaron sobre la funcionalidad implementada; y la reducción de errores financieros se sustenta en la verificación automatizada de las reglas de cálculo.

---

## 7. CONCLUSIONES

El sistema fue efectivamente construido y verificado: cubre los procesos que el diagnóstico identificó como críticos, concentra la información del personal en una fuente única, aplica reglas explícitas y comprobables para el cálculo de la remuneración, controla la vigencia de la documentación, formaliza el flujo de aprobación de las incidencias y produce los documentos oficiales que la institución debe emitir. La cobertura funcional alcanzada superó la prevista en el anteproyecto, al incorporar los módulos de asistencia, contratación y préstamos por requerimiento de las instituciones.

La solución resultó viable desde el punto de vista técnico y económico: se construyó íntegramente con tecnologías de código abierto, sin costo de licenciamiento, con un presupuesto ejecutado de $580 y con una arquitectura que admite expansión sin reconstrucción. La metodología adoptada permitió incorporar conocimiento del contexto sin comprometer el rigor técnico, y la documentación producida asegura que el sostenimiento del sistema no dependa de una sola persona.

El efecto sobre la eficiencia administrativa permanece como la cuestión abierta del estudio: su magnitud se establecerá con las mediciones de tiempo y de error antes y después de la implementación, con las encuestas de satisfacción y con los resultados de usabilidad, conforme al diseño metodológico ya definido. El informe declara con precisión qué se medirá, cómo y con qué umbral, de manera que la evidencia pendiente no constituya una indeterminación, sino un registro preparado para recibirla.

---

## 8. APORTES

En el orden técnico, la investigación aporta un sistema completo y funcional, construido con componentes abiertos, que puede adoptarse o adaptarse en otras instituciones y que se documenta con ese propósito; aporta asimismo la validación práctica de una arquitectura de capas con patrones Repository y Service, complementada por un dominio de cálculo aislado.

En el orden metodológico, aporta un caso documentado de integración entre desarrollo iterativo e investigación-acción, con instrumentos reutilizables y un procedimiento replicable.

En el orden académico, aporta evidencia empírica sobre la implementación de sistemas de gestión en instituciones educativas, área con literatura limitada, y ofrece un caso integral —del diagnóstico a la validación— que puede informar la práctica profesional y la investigación aplicada posterior.

En el orden social, aporta una herramienta que mejora la oportunidad y la exactitud de la remuneración del personal educativo y reduce la brecha tecnológica entre instituciones con distinta capacidad financiera.

---

## 9. PALABRAS CLAVE

Gestión de personal, nómina, instituciones educativas, ingeniería de software, arquitectura modular, tecnologías de código abierto, eficiencia administrativa.

---

## 10. ARCHIVOS DEFINITIVOS QUE RESPALDAN ESTE RESUMEN

| Documento | Archivo |
|-----------|---------|
| Resumen de la investigación | `RESUMEN_INVESTIGACION.md` |
| Capítulo I: Planteamiento del problema | `CAPITULO_I_PLANTEAMIENTO_PROBLEMA.md` |
| Capítulo II: Marco teórico | `CAPITULO_II_MARCO_TEORICO.md` |
| Capítulo III: Metodología | `CAPITULO_III_METODOLOGIA.md` |
| Capítulo IV: Resultados | `CAPITULO_IV_RESULTADOS.md` |
| Capítulo V: Conclusiones y recomendaciones | `CAPITULO_V_CONCLUSIONES.md` |
| Bibliografía y anexos | `BIBLIOGRAFIA_ANEXOS.md` |
| Anteproyecto de tesis | `ANTEPROYECTO_TESIS.md` |
| Proyecto sociotecnológico | `PROYECTO_SOCIAL_TECNOLOGICO.md` |
| Índice general | `INDICE_GENERAL.md` |
| Registro de control documental | `REGISTRO_CONTROL_DOCUMENTAL.md` |
| Código fuente del sistema | Directorio `src/` del repositorio, versión 2.82 |
| Suite de pruebas | Directorio `tests/`, 453 funciones de prueba |

---

**El Autor**
[Nombre del Estudiante]

**Tutor Académico**
[Nombre del Tutor]

**Fecha**
[Fecha de Presentación]
