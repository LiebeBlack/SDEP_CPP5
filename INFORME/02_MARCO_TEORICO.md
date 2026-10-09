# MARCO TEÓRICO

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 02 del expediente del informe del estado de la investigación.
**Fuente:** corpus académico del repositorio `SDEP_CPP5` (`TESIS/`) y código fuente verificado en `src/`.

---

## 1. Introducción

Este documento establece el fundamento teórico y conceptual que sustenta el desarrollo del Sistema de Gestión de Personal y Nómina. Expone, en primer lugar, los antecedentes de la investigación; en segundo lugar, las bases teóricas que fundamentan el diseño y la implementación; en tercer lugar, la remisión al marco legal desarrollado en el documento 03; y, finalmente, las definiciones de los términos técnicos, de dominio y metodológicos que el informe emplea, junto con el modelo conceptual del sistema efectivamente construido.

El marco teórico cumple una función de encuadre y no de adorno: cada concepto que aquí se expone se eligió porque tuvo consecuencias verificables sobre alguna decisión de diseño del producto. La estructura de capas, el aislamiento del dominio de cálculo, la estrategia de parametrización y el énfasis en la documentación son decisiones que responden a hallazgos concretos de la literatura y a las condiciones del contexto de aplicación. Exponer esa correspondencia es el propósito del documento.

El marco legal no se desarrolla aquí: por su extensión y por su naturaleza normativa, se consigna en [03_BASES_LEGALES.md](03_BASES_LEGALES.md). Las bases teóricas se profundizan en [05_BASES_TEORICAS.md](05_BASES_TEORICAS.md), y el modelo conceptual se confronta con la implementación real en [10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md](10_DISENO_Y_ESTRUCTURA_DEL_SOFTWARE.md).

---

## 2. Antecedentes de la investigación

### 2.1 Antecedentes internacionales

#### 2.1.1 Gestión electrónica de recursos humanos

Bondarouk y Ruël (2009) delimitaron el campo de la gestión electrónica de recursos humanos (*e-HRM*) como la configuración de tecnologías de información que habilita las actividades de gestión del personal. En su edición de un número especial de *The International Journal of Human Resource Management*, los autores identificaron los desafíos centrales de la disciplina: la alineación entre las estrategias institucionales y las soluciones tecnológicas, la aceptación por parte de los usuarios y la redefinición de los roles del área de recursos humanos.

La conclusión que interesa a esta investigación es de orden causal: el éxito de estos sistemas depende en mayor medida de factores organizacionales y humanos —capacitación, gestión del cambio, participación de los usuarios— que de las prestaciones técnicas de la herramienta. Esa conclusión orientó la decisión de tratar la capacitación y la documentación como componentes del producto y no como actividades accesorias.

#### 2.1.2 Implementación de sistemas integrados en instituciones de educación superior

Pollock y Cornford (2004) analizaron, mediante un estudio de caso en una universidad, los procesos de implantación de sistemas de planificación de recursos empresariales. Su hallazgo central es que las universidades constituyen organizaciones socialmente complejas y, en varios sentidos, singulares: sus procesos administrativos no se ajustan con facilidad a los flujos estandarizados que presuponen los sistemas comerciales.

De allí se desprende una orientación de diseño precisa: el sistema debe adaptarse a los procesos de la institución y no forzar la operación inversa. En la implementación desarrollada, esa orientación se materializó en la existencia de un módulo de configuración institucional que permite ajustar parámetros de nómina, políticas documentales y datos de la organización sin intervenir el código fuente.

#### 2.1.3 Transformación digital de instituciones educativas

Benavides et al. (2020) realizaron una revisión sistemática de la literatura sobre transformación digital en instituciones de educación superior, con cobertura de trabajos publicados entre 2000 y 2019. El estudio identificó tres impulsores —demanda de nuevos servicios, presión competitiva y madurez tecnológica— y tres barreras recurrentes: resistencia al cambio, limitaciones presupuestarias y brechas de competencia digital del personal.

La revisión concluye que la transformación digital debe abordarse como un proceso integral de cambio organizacional y no como la incorporación de herramientas aisladas. Esa conclusión explica por qué el proyecto se diseñó como una intervención con acompañamiento —instrumentos de recolección, capacitación prevista, documentación de usuario— y no como una simple entrega de software.

### 2.2 Antecedentes nacionales y de contexto comparable

La literatura internacional ofrece hallazgos transferibles a la realidad nacional. Se presentan tres estudios cuyas conclusiones informaron el diseño, y se declara de forma expresa el criterio con que se incorporarán los antecedentes locales propiamente dichos.

#### 2.2.1 Toma de decisiones basada en datos en países en desarrollo

Voogt y Pieters (2019) analizaron, en el número especial de *Journal of Professional Capital and Community* dedicado a la toma de decisiones basada en datos en países en desarrollo, la influencia del sistema educativo y de la cultura organizacional en el uso efectivo de los datos administrativos. Su conclusión es que la disponibilidad de sistemas de información confiables constituye condición necesaria pero no suficiente para mejorar la gestión educativa: se requiere además capacidad institucional para interpretar los datos y traducirlos en decisiones.

Esta conclusión justifica que el sistema incorpore reportes y estadísticas, y que la estrategia de adopción contemple la formación del personal en la lectura de esa información, no solo en el manejo de la herramienta.

#### 2.2.2 Obstáculos para la integración de las tecnologías de información en educación

Pelgrum (2001), a partir de una evaluación educativa de alcance mundial, identificó como principales barreras para la integración de las tecnologías de la información y la comunicación en el ámbito educativo la insuficiencia de equipos y programas, la capacitación limitada del personal y la falta de tiempo para familiarizarse con herramientas nuevas.

La consecuencia de diseño es directa: la solución debía exigir infraestructura mínima, no depender de conectividad permanente y reducir al máximo la curva de aprendizaje. La aplicación de escritorio con base de datos embebida responde exactamente a esas tres restricciones.

#### 2.2.3 Software de código abierto en el ámbito educativo

Lakhan y Jhunjhunwala (2008) analizaron los patrones de adopción de software de código abierto en instituciones educativas, con énfasis en sus beneficios económicos, su flexibilidad de adaptación y los retos asociados a su adopción. Concluyeron que las instituciones con recursos limitados pueden obtener beneficios significativos cuando disponen de documentación adecuada y de una capacidad técnica mínima.

De ese hallazgo proviene la decisión de construir el sistema íntegramente con componentes abiertos y de acompañarlo con documentación técnica y guía de usuario, de modo que la institución pueda sostenerlo sin depender de su autor original.

### 2.3 Antecedentes locales

#### 2.3.1 Estado de la cuestión y criterios de incorporación

La revisión de antecedentes locales exige una precisión metodológica que conviene declarar. A diferencia de los antecedentes internacionales, que se localizan en revistas indexadas y resultan verificables de manera directa, los casos regionales se documentan con frecuencia en informes institucionales, actas de consejos directivos, memorias de gestión o repositorios de trabajos de grado cuya localización depende del acceso a fuentes primarias de cada institución. Por esa razón, este apartado se construye con los criterios que deben satisfacer los casos que se incorporen y no con atribuciones de las que no se dispone de respaldo documental.

Los antecedentes locales que se integren a la versión definitiva deberán cumplir cuatro condiciones: proceder de una fuente localizable, con autoría y fecha identificables; describir una experiencia concreta de sistematización administrativa en una institución educativa de la región, con indicación de su alcance y su estado; permitir la comparación con los hallazgos internacionales ya expuestos, de modo que aporten contraste y no solo confirmación; y declarar sus limitaciones, dado que un caso único no autoriza generalizaciones.

#### 2.3.2 Función prevista de los antecedentes locales

Los casos regionales cumplirán tres funciones. La primera es contextual: situarán la magnitud del déficit de sistematización administrativa en el ámbito geográfico de aplicación con datos propios de la zona. La segunda es comparativa: permitirán contrastar si los obstáculos descritos en la literatura —resistencia al cambio, necesidad de capacitación, dependencia del liderazgo institucional— se manifiestan con la misma intensidad en el medio local. La tercera es instrumental: orientarán las decisiones de implementación, en particular la estrategia de gestión del cambio y el diseño de la capacitación.

Mientras esa evidencia se incorpore, la sección permanece registrada entre los datos pendientes de completación, con el objeto de que la omisión no pase inadvertida durante la revisión previa a la presentación.

### 2.4 Síntesis de los antecedentes

Los antecedentes revisados convergen en cinco patrones que informaron el diseño y la estrategia de implantación del sistema.

El primero concierne al peso relativo de los factores intervinientes: el resultado de una implementación depende más de condiciones humanas y organizacionales que de la tecnología elegida (Bondarouk & Ruël, 2009). El segundo se refiere a la formación: la capacitación continua aparece en todas las fuentes consultadas como condición de adopción, y su insuficiencia figura entre las barreras principales (Pelgrum, 2001). El tercero atañe a la estrategia de implantación: los enfoques por fases permiten aprender del uso real y ajustar el alcance, en contraste con las implantaciones simultáneas, que concentran el riesgo. El cuarto se refiere al contexto: las instituciones educativas no se comportan como organizaciones estandarizables y los sistemas deben adaptarse a sus procesos (Pollock & Cornford, 2004). El quinto alude a la documentación: su disponibilidad determina la capacidad de la institución para sostener el sistema sin depender de quien lo construyó (Lakhan & Jhunjhunwala, 2008).

La correspondencia entre estos patrones y las decisiones efectivamente adoptadas se resume en el cuadro siguiente.

| Hallazgo de la literatura | Decisión adoptada en el proyecto | Evidencia en el repositorio |
|---------------------------|----------------------------------|------------------------------|
| Los factores organizacionales pesan más que la tecnología | Capacitación y documentación tratadas como componentes del producto | `GUIA_USUARIO.md`, `docs/` |
| La capacitación insuficiente es barrera principal | Documentación de usuario y acompañamiento previstos en el piloto | Anexo 5 y protocolo del Anexo 3 |
| La implantación por fases concentra menos riesgo | Módulos independientes habilitados por rol y por necesidad | `MODULOS` de `src/gui/main_window.py` |
| Las instituciones no son estandarizables | Parametrización institucional sin tocar el código | `src/services/configuracion_service.py` |
| La documentación sostiene la adopción | Documentación técnica, guía de usuario y portal de consulta | `tools/verify_docs.py` |

---

## 3. Bases teóricas

Las bases teóricas se desarrollan con extensión en [05_BASES_TEORICAS.md](05_BASES_TEORICAS.md). Aquí se enuncian los cinco cuerpos conceptuales que estructuran el proyecto y la razón de su pertinencia.

**Ingeniería de software.** El proyecto se apoya en el ciclo de vida del desarrollo de software en su variante iterativa, en los patrones arquitectónicos del catálogo de Gamma et al. (1994) —con énfasis en *Repository* y *Service Layer*— y en las prácticas ágiles descritas por Beck et al. (2001) y Schwaber y Sutherland (2020). Esa combinación proporciona el marco para construir de forma incremental sin comprometer la estabilidad del producto.

**Sistemas de información.** Los sistemas de gestión de recursos humanos descritos por Johnson, Carlson y Kavanagh (2021) y los sistemas de información educativa caracterizados por Picciano (2011) aportan el inventario funcional que el producto debe cubrir y los principios de adaptación al contexto institucional. La arquitectura de sistemas empresariales de Laudon y Laudon (2018) fundamenta la organización por capas.

**Desarrollo de software.** La programación orientada a objetos según Booch (2007), las bases de datos relacionales según Date (2003) y Elmasri y Navathe (2015), y los principios de diseño de interfaces de Shneiderman et al. (2016) sostienen, respectivamente, el modelo de dominio, el esquema de datos y la capa de presentación.

**Gestión de recursos humanos.** El procesamiento de nómina, la gestión documental y la administración de incidencias se apoyan en Mathis et al. (2016), Guffey y Loewy (2021) y Dessler (2020), respectivamente. De allí proviene la enumeración de los conceptos que el motor de cálculo debe contemplar: salario base, deducciones legales, beneficios, horas extra y retenciones.

**Aceptación tecnológica.** El modelo de Davis (1989) sobre utilidad percibida y facilidad de uso percibida fundamenta la evaluación de usabilidad y satisfacción prevista para el piloto, y explica por qué la interfaz se diseñó con formularios guiados, prevención de errores y accesos rápidos.

---

## 4. Marco legal

El sistema opera sobre datos personales, laborales, documentales y salariales del personal de instituciones educativas, y por ello queda sujeto a un conjunto normativo que no es accesorio al diseño. El desarrollo completo de ese marco —artículos de la Constitución de la República Bolivariana de Venezuela, leyes orgánicas del trabajo, la seguridad social, la educación, la ciencia y tecnología, el infogobierno y la normativa técnica de calidad y seguridad de la información— se consigna en [03_BASES_LEGALES.md](03_BASES_LEGALES.md).

Aquí basta retener el principio que gobierna esa relación: cada exigencia normativa se tradujo en un control verificable del sistema, y la trazabilidad entre norma y control se presenta en una tabla de correspondencia en el documento 03. Los cuatro criterios que orientan el diseño en materia de protección de datos son el consentimiento informado, la minimización de los datos recogidos, la seguridad de la información y la garantía de los derechos de acceso, rectificación y supresión. El sistema los atiende mediante control de acceso por rol, registro de auditoría, respaldos sujetos a política de retención y limitación de los datos almacenados a la finalidad declarada.

---

## 5. Definición de términos básicos

### 5.1 Términos técnicos

**Sistema de gestión de personal.** Aplicación informática destinada a administrar la información y los procesos vinculados con los empleados de una organización.

**Nómina.** Proceso sistemático de cálculo y liquidación de salarios, beneficios y deducciones correspondientes a un periodo.

**Mapeo objeto-relacional (ORM).** Técnica que traduce entre estructuras relacionales y objetos del lenguaje de programación, de modo que el dominio se exprese en clases y no en sentencias de consulta dispersas.

**Arquitectura modular.** Enfoque de diseño que divide el sistema en componentes independientes pero interconectados, cada uno con una responsabilidad delimitada.

**Interfaz gráfica de usuario.** Sistema visual de interacción mediante ventanas, formularios, iconos y menús, orientado a usuarios con competencias informáticas heterogéneas.

**Repositorio.** Capa que abstrae el acceso a datos y expone operaciones de consulta y persistencia sin revelar detalles del motor subyacente.

**Servicio.** Capa que implementa las reglas de negocio del dominio y media entre la presentación y el acceso a datos.

**Dominio de cálculo.** Conjunto de módulos que implementa las reglas financieras de la nómina de forma aislada de la interfaz y de la persistencia, condición que permite probarlas de manera independiente.

**Migración de esquema.** Procedimiento mediante el cual la base de datos se adapta a una nueva versión del sistema sin pérdida de información.

### 5.2 Términos de dominio

**Empleado.** Persona incorporada a la institución educativa para desempeñar funciones determinadas, con relación laboral registrada en el sistema.

**Documento.** Registro oficial asociado a un empleado —identificación, título, certificado, reposo— con tipo, fecha de emisión, fecha de vencimiento y archivo digital asociado.

**Incidencia.** Evento que afecta la asistencia o la disponibilidad del empleado —permiso, reposo médico, ausencia, vacaciones— y que, una vez aprobado, incide en el cálculo de la remuneración del periodo.

**Deducción.** Monto descontado del salario por concepto legal o contractual: seguridad social, pensión, impuesto sobre la renta y retenciones autorizadas.

**Bonificación.** Monto adicional al salario base otorgado por concepto de horas extraordinarias, desempeño u otras causas previstas en la configuración institucional.

**Periodo de nómina.** Intervalo para el cual se calcula y liquida la remuneración, típicamente mensual o quincenal.

**Prestaciones sociales.** Beneficio laboral acumulado a favor del trabajador conforme a la normativa aplicable, cuyo cálculo y provisión el sistema registra.

**Vigencia documental.** Condición de un documento cuyo plazo no ha expirado; el sistema advierte con antelación configurable sobre los vencimientos próximos.

**Reporte.** Documento que presenta información resumida o detallada sobre un aspecto del sistema, destinado a la toma de decisiones o al cumplimiento de una obligación.

### 5.3 Términos metodológicos

**Investigación-acción.** Metodología que articula la intervención en un contexto real con la reflexión sobre esa intervención para producir conocimiento.

**Prototipado evolutivo.** Enfoque de desarrollo que construye versiones sucesivas del producto incorporando la retroalimentación recogida en cada ciclo.

**Pruebas de usabilidad.** Evaluación sistemática del sistema por usuarios reales, con tareas representativas y registro de tiempo, éxito, errores y comentarios.

**Verificación técnica.** Comprobación automatizada y reproducible de que el sistema cumple sus especificaciones funcionales y no funcionales.

**Triangulación.** Contraste de hallazgos procedentes de fuentes, instrumentos y casos distintos, con el fin de distinguir los patrones comunes de las particularidades locales.

---

## 6. Marco conceptual del sistema

### 6.1 Modelo conceptual

El sistema se organiza conforme al modelo de capas que se representa a continuación. El diagrama corresponde a la arquitectura efectivamente implementada en `src/`, no a un diseño previsto y no realizado.

**Figura 2.1. Modelo conceptual por capas del sistema**

```text
┌────────────────────────────────────────────────────────────────────────┐
│ CAPA DE PRESENTACIÓN · CustomTkinter                                   │
│ LoginWindow · MainWindow · nueve módulos con acceso por rol y atajos   │
│ Ctrl+1 … Ctrl+9: panel de control, empleados, documentos, incidencias, │
│ contratos, nómina, configuración, estudiantes y calificaciones         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE SERVICIOS · reglas de negocio y orquestación de flujos         │
│ auth · empleado · documento · incidencia · contrato · pago ·           │
│ configuración · académico · notas · token de sesión                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE REPOSITORIOS · patrón Repository sobre repositorio base        │
│ repositorios concretos con consultas reutilizables y transacciones     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE MODELOS · SQLAlchemy ORM                                       │
│ empleados · documentos · incidencias · contratos · pagos ·             │
│ configuraciones · usuarios · estudiantes · grados · matrículas ·       │
│ notas finales · periodos académicos · tokens de sesión                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ DOMINIO DE NÓMINA · cálculo aislado de la interfaz y del acceso a datos│
│ motor · parámetros · impuesto sobre la renta · horas extra ·           │
│ prestaciones · seguridad social · finiquito                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ SERVICIOS TRANSVERSALES · seguridad, trazabilidad y sostenibilidad     │
│ security · audit_logger · backup_manager · backup_scheduler ·          │
│ pdf_generator · document_manager · exporter · validators ·             │
│ helpers · actualizador automático                                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ BASE DE DATOS · SQLite con integridad referencial y migraciones        │
└────────────────────────────────────────────────────────────────────────┘
```

*Fuente: elaboración propia a partir de la arquitectura implementada en `src/`, repositorio en versión 3.0.1.*

### 6.2 Relaciones entre componentes

El flujo de una operación típica recorre las capas en el orden siguiente. El usuario interactúa con la interfaz gráfica, que verifica previamente sus permisos sobre el módulo solicitado. La interfaz invoca al servicio correspondiente y le entrega los datos del formulario. El servicio valida las reglas del dominio y, cuando la operación lo requiere, delega el cálculo en el dominio de nómina. El servicio consulta o persiste la información a través de los repositorios, que operan sobre el mapeo objeto-relacional. Los resultados retornan por las mismas capas hasta la interfaz, y las operaciones sensibles quedan registradas en la auditoría.

Los principios de diseño que gobiernan esa organización son cuatro: separación de responsabilidades, con una función delimitada por capa; bajo acoplamiento, con dependencias mínimas entre componentes; alta cohesión, con cada módulo enfocado en una sola responsabilidad; y abstracción mediante interfaces bien definidas entre capas.

### 6.3 Consecuencias verificables del modelo

El modelo no es una declaración de intenciones. Sus consecuencias se comprueban en tres hechos documentados. Primero, las reglas de nómina se prueban sin levantar la interfaz: la cobertura del dominio de cálculo alcanza el 89 % en la medición del 6 de octubre de 2026. Segundo, la incorporación y el retiro de módulos no exigió refundar las capas preexistentes entre las versiones 2.79 y 3.0.0, y la extensión posterior hacia el dominio académico se realizó sobre la misma estructura. Tercero, la sustitución de componentes quedó contenida en un solo paquete, como lo demuestra el retiro completo de tres módulos con sus tablas, columnas y parámetros.

---

## 7. Conclusiones del documento

El marco teórico expuesto proporciona la base conceptual del proyecto y permite leer cada decisión de diseño como respuesta a un hallazgo documentado. Los antecedentes internacionales fijan el peso de los factores organizacionales, la necesidad de adaptación al contexto educativo y el valor de la documentación como condición de sostenibilidad. Las bases teóricas aportan los instrumentos de la ingeniería de software, de los sistemas de información y de la gestión de recursos humanos con que se construyó el producto. El marco legal, desarrollado por separado, fija las exigencias normativas que el sistema traduce en controles verificables. Las definiciones establecen un vocabulario común, y el modelo conceptual describe la arquitectura efectivamente construida.

Con esos elementos queda delimitado el terreno sobre el que operan los documentos siguientes: el marco legal en [03_BASES_LEGALES.md](03_BASES_LEGALES.md), el marco práctico en [04_MARCO_PRACTICO.md](04_MARCO_PRACTICO.md) y el desarrollo conceptual detallado en [05_BASES_TEORICAS.md](05_BASES_TEORICAS.md).

---

## 8. Vigencia y actualización del marco teórico

El marco teórico no es un cuerpo inmóvil: los antecedentes, las prácticas de ingeniería y las normas técnicas evolucionan. Este apartado establece los criterios con que el marco debe revisarse para conservar su pertinencia.

### 8.1 Criterios de revisión

La revisión de los antecedentes internacionales procede cuando aparece literatura posterior que cuestione o amplíe los hallazgos citados. La de las bases teóricas procede cuando las prácticas de ingeniería adoptadas cambian de forma sustantiva —por ejemplo, la aparición de un patrón arquitectónico que sustituya con ventaja a los empleados—. La de las normas técnicas procede cuando se publica una edición nueva de las normas de calidad o de seguridad citadas. Y la de los antecedentes locales procede conforme se incorporen los casos regionales según los criterios ya declarados.

### 8.2 Horizonte de vigencia de cada cuerpo teórico

| Cuerpo teórico | Horizonte de vigencia estimado | Motivo de revisión |
|----------------|-------------------------------|--------------------|
| Antecedentes sobre gestión electrónica de recursos humanos | Amplio | Los hallazgos sobre factores organizacionales son estables |
| Antecedentes sobre implantación de sistemas en universidades | Amplio | La complejidad organizacional del sector educativo es persistente |
| Bases teóricas de ingeniería de software | Medio | Los patrones consolidados evolucionan con lentitud |
| Normas de calidad y seguridad | Medio | Se revisan periódicamente con nuevas ediciones |
| Antecedentes locales | Inmediato | Pendientes de incorporación conforme a los criterios declarados |

### 8.3 Regla de actualización

Toda actualización del marco teórico debe conservar la correspondencia entre citas y referencias y no debe introducir fuentes sin verificación. Cuando un hallazgo nuevo contradiga una afirmación del marco, la contradicción se documenta en lugar de suprimirse, pues las tensiones entre fuentes suelen contener la información más útil para interpretar el fenómeno.

---

**El Autor**
[Nombre del Estudiante]

**Institución**
[Nombre de la Institución]
