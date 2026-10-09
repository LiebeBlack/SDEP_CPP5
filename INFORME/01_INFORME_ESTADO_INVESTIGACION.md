# INFORME DEL ESTADO DE LA INVESTIGACIÓN DEL PROYECTO SOCIOTECNOLÓGICO

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5, versión 3.0.1, en el corpus académico (`TESIS/`) y en el repositorio vigente (`VERSION`, `pyproject.toml`).
**Fecha de elaboración:** 9 de octubre de 2026.
**Fuente única de información:** documentos y código del repositorio `SDEP_CPP5/`.
**Carácter del documento:** informe integrador. Reúne, en una sola pieza, el estado real de la investigación y remite a los doce documentos complementarios que lo desarrollan, cuyo índice maestro es [00_INDICE_GENERAL_DEL_EXPEDIENTE.md](00_INDICE_GENERAL_DEL_EXPEDIENTE.md).

---

## 1. Objeto, alcance y criterio de lectura

Este informe reúne el estado real de la investigación en el momento de su elaboración. Su propósito es triple: dejar constancia de lo que ya fue verificado y del procedimiento con que se verificó; distinguir con nitidez lo implementado de lo medido, para que ninguna afirmación se adelante a su evidencia; y señalar los pendientes con precisión suficiente para que puedan ejecutarse sin rehacer el trabajo previo.

El documento no sustituye a los capítulos del informe de grado ni al compendio del proyecto sociotecnológico: los sintetiza y los pone en correspondencia. Cada cifra que aparece aquí remite al archivo de donde proviene o al procedimiento de medida que la produjo. Cuando una afirmación no dispone de respaldo, se declara como pendiente y no se enuncia como lograda. Esa regla atraviesa el conjunto del expediente y se describe en el [registro de control documental](../TESIS/REGISTRO_CONTROL_DOCUMENTAL.md).

El informe se apoya en nueve documentos que desarrollan cada componente del marco del proyecto. La lectura completa del expediente supone recorrerlos en el orden que se indica en el apartado 8.

## 2. Identificación del proyecto

| Campo | Contenido |
|-------|-----------|
| Título | Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información |
| Línea de investigación | Sistemas de información e ingeniería de software |
| Tipo de investigación | Aplicada y tecnológica |
| Diseño | Investigación-acción combinada con prototipado evolutivo |
| Enfoque | Mixto, con predominio cuantitativo en la medición del efecto |
| Ámbito de aplicación | Instituciones educativas de nivel medio y superior |
| Jurisdicción de referencia | República Bolivariana de Venezuela |
| Autor | [Nombre del Estudiante] |
| Tutor académico | [Nombre del Tutor] |
| Institución | [Nombre de la Universidad o Instituto] |
| Versión del corpus académico | 3.0.1 ([registro de control documental](../TESIS/REGISTRO_CONTROL_DOCUMENTAL.md)) |
| Versión del repositorio | 3.0.1 ([VERSION](../VERSION), [pyproject.toml](../pyproject.toml)) |
| Estado general | Desarrollo, verificación técnica y documentación concluidos; validación de usabilidad y aplicación piloto programadas |

El corpus académico y el repositorio se encuentran en la misma versión, la 3.0.1: la extensión académica, que había quedado fuera de la documentación al cierre de la 3.0.0, fue incorporada al corpus. El apartado 6 declara esa correspondencia y consigna las cifras verificadas en cada versión.

## 3. Estado de la investigación por componente

| Componente | Estado | Evidencia disponible | Fuente |
|------------|--------|----------------------|--------|
| Planteamiento del problema y delimitación | Concluido | Diagnóstico anclado en entrevistas y observación directa, con contrastación en literatura | [CAPITULO_I_PLANTEAMIENTO_PROBLEMA.md](../TESIS/CAPITULO_I_PLANTEAMIENTO_PROBLEMA.md) |
| Marco teórico | Concluido con una sección pendiente | Antecedentes internacionales y nacionales documentados; antecedentes locales sujetos a criterios de incorporación declarados | [02_MARCO_TEORICO.md](02_MARCO_TEORICO.md) |
| Bases legales | Estructurado; verificación de vigencia pendiente | Marco normativo de la jurisdicción consignado con criterios de correspondencia técnica | [03_BASES_LEGALES.md](03_BASES_LEGALES.md) |
| Bases teóricas | Concluido | Conceptos técnicos, científicos y de ingeniería que sustentan el diseño | [05_BASES_TEORICAS.md](05_BASES_TEORICAS.md) |
| Marco lógico y objetivos | Concluido | Objetivo general y seis objetivos específicos jerarquizados | [06_MARCO_LOGICO_Y_OBJETIVOS.md](06_MARCO_LOGICO_Y_OBJETIVOS.md) |
| Marco operacional y justificación | Concluido | Repercusión social, técnica y económica documentada | [07_MARCO_OPERACIONAL_Y_JUSTIFICACION.md](07_MARCO_OPERACIONAL_Y_JUSTIFICACION.md) |
| Marco práctico | Concluido en su componente técnico | Aplicación efectiva del producto y su distribución | [04_MARCO_PRACTICO.md](04_MARCO_PRACTICO.md) |
| Metodología | Concluida en diseño; fases 1 y 2 ejecutadas | Instrumentos definidos y reproducidos en los anexos | [CAPITULO_III_METODOLOGIA.md](../TESIS/CAPITULO_III_METODOLOGIA.md) |
| Desarrollo del producto | Concluido | Sistema operativo, verificado con suite automatizada y verificación estática | [10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md](10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md) |
| Verificación técnica | Concluida el 6 de octubre de 2026 | 551 pruebas exitosas, cobertura y verificadores estáticos registrados | [CORRECCIONES_EJECUTADAS.md](../CORRECCIONES_EJECUTADAS.md) |
| Pruebas de usabilidad | Programadas | Protocolo del Anexo 3 con campos de registro | [BIBLIOGRAFIA_ANEXOS.md](../TESIS/BIBLIOGRAFIA_ANEXOS.md) |
| Aplicación piloto | Programada | Tablas de registro de medición con marcador `[por completar]` | [CAPITULO_IV_RESULTADOS.md](../TESIS/CAPITULO_IV_RESULTADOS.md) |
| Documentación del producto | Concluida y sincronizada | Documentación técnica, guía de usuario, notas de desarrollo y portal `docs/` | [DOCUMENTACION_TECNICA.md](../DOCUMENTACION_TECNICA.md), [verify_docs.py](../tools/verify_docs.py) |
| Redacción del informe | Concluida en sus capítulos; incorporación del piloto pendiente | Capítulos I a V, bibliografía y anexos | [TESIS/](../TESIS) |

La Matriz del Enfoque del Marco Lógico que ordena estos componentes en una sola estructura de resultados, indicadores, medios de verificación y supuestos se presenta en [09_MATRIZ_ENFOQUE_MARCO_LOGICO.md](09_MATRIZ_ENFOQUE_MARCO_LOGICO.md).

## 4. Evidencia verificada

Las verificaciones siguientes se practicaron sobre el repositorio con el procedimiento indicado. Las de la primera fila corresponden a la ejecución del 6 de octubre de 2026; las restantes son recuentos directos practicados el 9 de octubre de 2026 sobre el árbol de trabajo.

| Verificación | Procedimiento | Resultado |
|--------------|---------------|-----------|
| Suite de pruebas | `pytest tests/` con CPython 3.15.0rc3 | 551 pruebas, 32 archivos, 551 exitosas, 0 fallos, 0 errores (200 s) |
| Cobertura total | `pytest --cov=src` | 56 % (13 464 sentencias, 5 908 sin cubrir) |
| Cobertura de lógica de negocio | Informe por módulo de la misma ejecución | `src/services` 76 %; `src/nomina` 89 % |
| Análisis estático | `flake8`, `black --check`, `isort --check-only` | Sin hallazgos y sin cambios pendientes |
| Verificación de tipos | `mypy` | Sin errores en 98 archivos |
| Consistencia de la documentación | `tools/verify_docs.py` | Todos los chequeos superados |
| Arranque del producto | `python src/main.py --selftest` | Código de salida 0, sobre base nueva y sobre base con esquema anterior |
| Extensión del código fuente | Recuento con `wc -l` sobre `src/` | 29 475 líneas en 77 archivos Python |
| Agente de sincronización | Recuento sobre `sync_agent/` | 5 433 líneas en 13 archivos |
| Funciones de prueba | Recuento de `def test_` en `tests/test_*.py` | 551 funciones en 32 archivos, más `conftest.py` |
| Esquema de datos | Búsqueda de `__tablename__` en `src/models/` | 13 tablas |
| Módulos de interfaz | Lectura de `MODULOS` en `src/gui/main_window.py` | 9 módulos, con atajos `Ctrl+1` a `Ctrl+9` |
| Matriz de acceso | Lectura de `MODULE_ACCESS` en `src/utils/security.py` | 8 entradas; el panel de control está exento por `MODULOS_SIN_CONTROL_DE_ACCESO` |
| Generación documental | Recuento de métodos de generación en `src/utils/pdf_generator.py` | Doce tipos de documento |
| Versión vigente | Lectura de `VERSION` y de `pyproject.toml` | 3.0.1 |

Estos valores describen el repositorio en su estado actual. Los que correspondan a magnitudes estructurales conservan valor para la defensa del trabajo, pero deben presentarse con la fecha y el procedimiento que los produjeron, en los términos que el registro de control documental exige.

## 5. Arquitectura y producto construido

El sistema se organiza en una arquitectura de capas que separa la presentación, los servicios, los repositorios, los modelos, el dominio de cálculo de nómina y los servicios transversales, sobre una base de datos SQLite con integridad referencial y migraciones. Esa separación es la que permitió probar cada nivel de forma aislada y evolucionar el producto sin reconstruirlo.

La distribución efectiva del código fuente así lo confirma: sobre los 77 archivos Python de `src/`, la capa de interfaz gráfica concentra 11 598 líneas, los servicios 4 332, las utilidades transversales 5 525, los repositorios 2 383, los modelos 1 887, el dominio de nómina 1 502 y la configuración 1 706, además del punto de entrada. El detalle de cada capa, sus patrones y su modelo de datos se desarrolla en [10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md](10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md).

Conviene retener tres hechos verificables. El dominio de cálculo de nómina está aislado de la interfaz y del acceso a datos, de modo que las reglas financieras se prueban sin levantar la aplicación. La matriz de acceso por rol administra seis módulos operativos y dos académicos, con cuatro roles —administrador, gestor, usuario y solo lectura— y con denegación explícita ante módulos desconocidos. Y la generación documental cubre doce tipos de documento oficial en formato PDF, sustituyendo la elaboración manual.

## 6. Correspondencia entre el corpus académico y el repositorio

El corpus académico y el repositorio están alineados en la versión 3.0.1. El módulo académico —estudiantes, grados, matrículas, calificaciones y periodos— había quedado fuera de la documentación en la versión 3.0.0; su incorporación al corpus eliminó la única divergencia que subsistía entre lo documentado y lo construido. Las cifras verificadas son las siguientes.

| Rasgo | Versión 3.0.0 (referencia histórica) | Versión 3.0.1 (corpus y repositorio) |
|-------|--------------------------------------|--------------------------------------|
| Módulos de interfaz | Siete módulos operativos | Nueve módulos: los siete operativos más estudiantes y calificaciones |
| Esquema de datos | Siete tablas del núcleo de personal y nómina | Trece tablas: las siete del núcleo más estudiantes, grados, matrículas, notas finales, periodos académicos y tokens de sesión |
| Funciones de prueba | 476 en veintiséis archivos | 551 en treinta y dos archivos |
| Extensión de `src/` | 23 242 líneas en 59 archivos | 29 475 líneas en 77 archivos |
| Paquete de sincronización | Documentado a nivel de descripción | 5 433 líneas en 13 archivos |

La ampliación de alcance hacia el dominio académico se realizó sobre la misma arquitectura de capas, sin refundar las capas preexistentes y sin alterar las conclusiones técnicas sobre el núcleo de personal y nómina. Los apartados 4 y 5 de este informe se refieren a la versión 3.0.1 y lo declaran así.

## 7. Pendientes y estatuto de la evidencia faltante

La evidencia pendiente no constituye una indeterminación vaga, sino un registro preparado para recibirla. Se agrupa en tres frentes.

**Evidencia del piloto.** Comprende las instituciones y los usuarios participantes, los resultados de usabilidad y de satisfacción con cálculo del alfa de Cronbach, las mediciones de tiempo y de tasa de error antes y después de la implementación, las pruebas de rendimiento y carga, los resultados cualitativos y el tratamiento estadístico con su decisión sobre cada hipótesis.

**Verificación técnica por actualizar.** Comprende la re-medición de la cobertura sobre la versión vigente y el informe formal de la última ejecución de la suite, con número de pruebas, resultado y fecha.

**Fuentes locales y normativas.** Comprenden los antecedentes locales con fuentes verificables y la confirmación de la vigencia de cada norma consignada en las bases legales frente a la Gaceta Oficial.

El procedimiento mediante el cual cada uno de estos elementos se incorporará sin romper la coherencia del conjunto se describe en [08_DIAGNOSTICO_CONSOLIDACION_Y_AVANCE.md](08_DIAGNOSTICO_CONSOLIDACION_Y_AVANCE.md).

## 8. Documentos que integran el expediente

| Orden | Documento | Contenido |
|-------|-----------|-----------|
| 00 | [00_INDICE_GENERAL_DEL_EXPEDIENTE.md](00_INDICE_GENERAL_DEL_EXPEDIENTE.md) | Índice maestro: integración, inventario y convenciones del expediente |
| 01 | [01_INFORME_ESTADO_INVESTIGACION.md](01_INFORME_ESTADO_INVESTIGACION.md) | Este informe integrador |
| 02 | [02_MARCO_TEORICO.md](02_MARCO_TEORICO.md) | Antecedentes, teoría y marco conceptual |
| 03 | [03_BASES_LEGALES.md](03_BASES_LEGALES.md) | CRBV, leyes orgánicas y normativa técnica |
| 04 | [04_MARCO_PRACTICO.md](04_MARCO_PRACTICO.md) | Aplicación efectiva, distribución y operación |
| 05 | [05_BASES_TEORICAS.md](05_BASES_TEORICAS.md) | Conceptos técnicos, científicos y de ingeniería |
| 06 | [06_MARCO_LOGICO_Y_OBJETIVOS.md](06_MARCO_LOGICO_Y_OBJETIVOS.md) | Objetivo general y objetivos específicos |
| 07 | [07_MARCO_OPERACIONAL_Y_JUSTIFICACION.md](07_MARCO_OPERACIONAL_Y_JUSTIFICACION.md) | Justificación e importancia: repercusión social, técnica y económica |
| 08 | [08_DIAGNOSTICO_CONSOLIDACION_Y_AVANCE.md](08_DIAGNOSTICO_CONSOLIDACION_Y_AVANCE.md) | Archivos de diagnóstico, consolidación y avance |
| 09 | [09_MATRIZ_ENFOQUE_MARCO_LOGICO.md](09_MATRIZ_ENFOQUE_MARCO_LOGICO.md) | Matriz del Enfoque del Marco Lógico |
| 10 | [10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md](10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md) | Diseño y estructuración del software construido |
| 11 | [11_PORTADA_Y_PRESENTACION_OFICIAL.md](11_PORTADA_Y_PRESENTACION_OFICIAL.md) | Portada, oficio de remisión y fórmulas de aprobación |
| 12 | [12_ANEXOS_DEL_EXPEDIENTE.md](12_ANEXOS_DEL_EXPEDIENTE.md) | Instrumentos, diagramas, inventario del código y presupuesto |

El expediente académico completo —capítulos, anexos, resumen y oficios— se conserva en el directorio [TESIS/](../TESIS) y su reflejo para consulta en el navegador en el portal [docs/](../docs).

## 9. Conclusión del estado

El proyecto se encuentra ejecutado y verificado en su componente técnico y documentado en su integridad. El sistema está operativo, organizado en capas, con dominio de cálculo aislado, control de acceso por rol, auditoría, respaldos y una suite de pruebas que cubre las reglas críticas. La conclusión que puede sostenerse hoy es la eliminación estructural de las causas del error administrativo —cálculo manual, transcripción repetida y ausencia de control de vencimientos—; la cuantificación de su efecto sobre la eficiencia pertenece al capítulo de resultados empíricos y se obtendrá con la evidencia del piloto conforme al diseño metodológico ya definido.

---

## 10. Verificación de correspondencia entre el expediente y el repositorio

El expediente no afirma nada que no pueda confrontarse con un artefacto del repositorio. La tabla siguiente establece, para cada documento, el artefacto contra el cual se verifica y el procedimiento de comprobación.

| Documento | Artefacto de verificación | Procedimiento |
|-----------|---------------------------|---------------|
| 01 Informe del estado | Repositorio completo | Recuentos directos y ejecución registrada |
| 02 Marco teórico | `src/` y arquitectura implementada | Inspección de la estructura de capas |
| 03 Bases legales | `src/nomina/`, `src/utils/security.py` | Correspondencia norma–control del apartado 8 |
| 04 Marco práctico | Guía de usuario, actualizador y agente de sincronización | Lectura de la funcionalidad y de los procedimientos |
| 05 Bases teóricas | Código de cada capa | Confrontación de cada fundamento con su decisión |
| 06 Marco lógico y objetivos | Corpus académico y código | Cotejo de enunciados con el corpus |
| 07 Marco operacional | Presupuesto y documentación técnica | Lectura de las tablas de costo y operación |
| 08 Diagnóstico y avance | Instrumentos y verificador documental | Cotejo de instrumentos y ejecución del verificador |
| 09 Matriz EML | Objetivos y umbrales del anteproyecto | Cotejo de indicadores con los umbrales declarados |
| 10 Diseño del software | `src/`, `sync_agent/`, `tests/` | Recuentos de archivos, líneas y tablas |

### 10.1 Lista de comprobación previa a la presentación

Antes de la presentación definitiva del expediente debe verificarse lo siguiente: que los campos entre corchetes estén completados; que las cifras estructurales correspondan a la versión declarada; que los enlaces entre documentos resuelvan; que la evidencia del piloto se haya incorporado o se declare como pendiente con su causa; y que la vigencia de las normas citadas se haya confrontado con la Gaceta Oficial.

---

**El Autor**
[Nombre del Estudiante]

**Tutor Académico**
[Nombre del Tutor]

**Institución**
[Nombre de la Institución]

**Fecha**
9 de octubre de 2026
