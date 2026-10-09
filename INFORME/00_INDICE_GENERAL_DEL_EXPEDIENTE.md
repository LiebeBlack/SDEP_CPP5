# ÍNDICE GENERAL DEL EXPEDIENTE

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 00 del expediente del informe del estado de la investigación.
**Fecha de elaboración:** 9 de octubre de 2026.

---

## 1. Propósito del expediente

El presente expediente reúne, en trece documentos, el estado real de la investigación y la totalidad del marco que la sustenta. Su finalidad es doble: servir de instrumento de trabajo interno para el autor y de cuerpo verificable para la instancia evaluadora. Cada documento es autónomo —puede leerse por separado— y, a la vez, forma parte de un conjunto articulado cuyas remisiones cruzadas permiten reconstruir cualquier afirmación hasta su fuente.

La regla que gobierna el expediente es una sola y se repite en cada documento: se describe como verificado únicamente aquello que fue comprobado con un procedimiento declarado; lo que está implementado pero no medido se declara implementado; y lo que depende de la ejecución del piloto se declara pendiente. Esa disciplina es la que permite afirmar que el expediente no contiene atribuciones sin respaldo.

---

## 2. Datos generales del trabajo

| Campo | Contenido |
|-------|-----------|
| Título | Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información |
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
| Jurisdicción de referencia | República Bolivariana de Venezuela |
| Versión del sistema documentado | 3.0.1, tanto en el corpus académico como en el repositorio |
| Lugar y fecha de presentación | [Ciudad, País], [Fecha] |

---

## 3. Inventario de los documentos del expediente

| Orden | Documento | Archivo | Contenido | Extensión |
|-------|-----------|---------|-----------|-----------|
| 00 | Índice general del expediente | `00_INDICE_GENERAL_DEL_EXPEDIENTE.md` | Este documento: integración, inventario y convenciones | — |
| 01 | Informe del estado de la investigación | `01_INFORME_ESTADO_INVESTIGACION.md` | Síntesis integradora del estado por componente, evidencia verificada y pendientes | 177 líneas |
| 02 | Marco teórico | `02_MARCO_TEORICO.md` | Antecedentes, bases teóricas, definiciones y modelo conceptual | 278 líneas |
| 03 | Bases legales | `03_BASES_LEGALES.md` | CRBV, leyes orgánicas, normativa técnica, trazabilidad norma–control y cuadro resumen normativo | 306 líneas |
| 04 | Marco práctico | `04_MARCO_PRACTICO.md` | Operación, distribución, sincronización, procedimiento del piloto y guía operativa | 225 líneas |
| 05 | Bases teóricas | `05_BASES_TEORICAS.md` | Conceptos técnicos, científicos y de ingeniería del diseño, con glosario ampliado | 237 líneas |
| 06 | Marco lógico y objetivos | `06_MARCO_LOGICO_Y_OBJETIVOS.md` | Objetivo general, objetivos específicos, hipótesis, variables y cuadro de coherencia | 209 líneas |
| 07 | Marco operacional y justificación | `07_MARCO_OPERACIONAL_Y_JUSTIFICACION.md` | Operación, repercusión social, técnica y económica, y análisis costo–beneficio | 199 líneas |
| 08 | Diagnóstico, consolidación y avance | `08_DIAGNOSTICO_CONSOLIDACION_Y_AVANCE.md` | Instrumentos de diagnóstico, consolidación documental, matriz de avance y plantillas de registro | 239 líneas |
| 09 | Matriz del Enfoque del Marco Lógico | `09_MATRIZ_ENFOQUE_MARCO_LOGICO.md` | Matriz EML en cuatro niveles, indicadores, supuestos y versión compacta | 215 líneas |
| 10 | Diseño y estructura del software | `10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md` | Arquitectura, capas, modelo de datos, módulos, servicios e inventario de archivos | 348 líneas |
| 11 | Portada y presentación oficial | `11_PORTADA_Y_PRESENTACION_OFICIAL.md` | Portada, oficio de remisión, control de versiones y fórmulas de aprobación | 145 líneas |
| 12 | Anexos del expediente | `12_ANEXOS_DEL_EXPEDIENTE.md` | Instrumentos, diagramas, inventario del código, cuadro normativo y presupuesto | 330 líneas |

---

## 4. Mapa de dependencias entre documentos

La lectura del expediente puede seguirse en el orden numérico. Las dependencias entre documentos son las siguientes.

```text
00 Índice general
 ├── 01 Informe del estado  ── síntesis y remisión a todos
 │    ├── 02 Marco teórico        ── fundamento conceptual
 │    │    └── 03 Bases legales    ── fundamento normativo
 │    ├── 05 Bases teóricas       ── fundamento técnico y científico
 │    ├── 06 Marco lógico         ── objetivos, hipótesis y variables
 │    │    └── 09 Matriz EML       ── indicadores, medios y supuestos
 │    ├── 07 Marco operacional    ── operación y justificación
 │    ├── 04 Marco práctico       ── aplicación y distribución
 │    ├── 08 Diagnóstico y avance ── trazabilidad y estado
 │    ├── 10 Diseño del software  ── producto construido
 │    ├── 11 Portada y presentación
 │    └── 12 Anexos del expediente
```

Cada documento remite a los que le dan continuidad, de modo que ninguna afirmación queda aislada de su fundamento.

---

## 5. Convenciones del expediente

### 5.1 Convenciones de cita de cifras

Toda cifra estructural del expediente se consigna con la versión del sistema a la que pertenece. Cuando una cifra proviene de una medición, se indica el procedimiento y la fecha. Las magnitudes del corpus académico y del repositorio corresponden a la versión 3.0.1, que es a la vez la versión documentada y la vigente. Cuando una cifra de una versión anterior se conserva como referencia, se declara expresamente.

### 5.2 Convenciones de remisión

Las remisiones internas usan el número y el nombre del documento. Las remisiones al corpus académico usan la ruta dentro de `TESIS/`. Las remisiones al código usan la ruta dentro del repositorio. Los campos entre corchetes señalan información que solo el autor puede aportar o que depende de la ejecución del piloto.

### 5.3 Glosario de siglas

| Sigla | Significado |
|-------|-------------|
| CRBV | Constitución de la República Bolivariana de Venezuela |
| EML | Enfoque del Marco Lógico |
| GUI | Interfaz gráfica de usuario |
| ISR | Impuesto sobre la renta |
| ISLR | Impuesto sobre la renta (denominación de la ley) |
| IVO | Indicador verificable objetivamente |
| LOCTI | Ley Orgánica de Ciencia, Tecnología e Innovación |
| LOE | Ley Orgánica de Educación |
| LOPA | Ley Orgánica de Procedimientos Administrativos |
| LOPCYMAT | Ley Orgánica de Prevención, Condiciones y Medio Ambiente de Trabajo |
| LOSSS | Ley Orgánica del Sistema de Seguridad Social |
| LOTTT | Ley Orgánica del Trabajo, los Trabajadores y las Trabajadoras |
| MVC | Modelo–Vista–Controlador |
| ORM | Mapeo objeto-relacional |
| PBKDF2 | Función de derivación de clave basada en contraseña |
| SDLC | Ciclo de vida del desarrollo de software |
| SUS | Escala de usabilidad del sistema |

### 5.4 Advertencia sobre la naturaleza del expediente

Este expediente es un instrumento de trabajo del proyecto sociotecnológico y académico. Se elaboró enteramente a partir de los documentos y del código que constan en el repositorio `SDEP_CPP5`. Las afirmaciones sobre el producto se apoyan en verificación directa; las que dependen de la aplicación en campo se declaran como programadas.

---

## 6. Estado de consolidación del expediente

| Aspecto | Estado |
|---------|--------|
| Documentos redactados | Trece, completos |
| Coherencia de cifras entre documentos | Verificada |
| Remisiones cruzadas | Verificadas: sin enlaces rotos |
| Estructura de cada documento | Verificada: secciones y cierres completos |
| Verificación del código | Pendiente de entorno con intérprete de Python; la revisión estática por inspección no detectó defectos evidentes |
| Evidencia del piloto | Programada conforme al documento 04 |

---

## 7. Cómo leer este expediente

Para una revisión de conjunto se recomienda leer el documento 01, que sintetiza el estado y remite a los demás. Para una revisión del fundamento, los documentos 02, 03, 05 y 06. Para una revisión de la lógica de la intervención, los documentos 06, 07 y 09. Para una revisión del producto, los documentos 04, 08 y 10. Para una revisión de la trazabilidad y del estado del avance, los documentos 08 y 09.

---

**El Autor**
[Nombre del Estudiante]

**Tutor Académico**
[Nombre del Tutor]

**Institución**
[Nombre de la Universidad o Instituto]
