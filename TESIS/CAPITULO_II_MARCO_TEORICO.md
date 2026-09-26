# CAPÍTULO II: MARCO TEÓRICO

## 2.1 INTRODUCCIÓN

El presente capítulo establece el fundamento teórico y conceptual que sustenta el desarrollo del Sistema de Gestión de Personal y Nómina para instituciones educativas. Se presentan los antecedentes de la investigación, las bases teóricas que fundamentan el diseño e implementación del sistema, el marco legal pertinente, y las definiciones de términos básicos necesarios para comprender el estudio.

Este marco teórico proporciona la base conceptual y técnica necesaria para abordar el problema de investigación, permitiendo el diseño de una solución fundamentada en principios establecidos de ingeniería de software, sistemas de información y gestión de recursos humanos.

## 2.2 ANTECEDENTES DE LA INVESTIGACIÓN

### 2.2.1 Antecedentes Internacionales

#### 2.2.1.1 Gestión Electrónica de Recursos Humanos (e-HRM)

Bondarouk y Ruël (2009) introdujeron y delimitaron el campo de la gestión electrónica de recursos humanos (e-HRM), definiéndolo como la configuración de tecnologías de información que habilita las actividades de gestión del personal a través de la web. En su edición de un número especial de la *International Journal of Human Resource Management*, los autores identificaron los principales desafíos de la e-HRM en la era digital: la alineación entre las estrategias de negocio y las soluciones tecnológicas, la aceptación por parte de los usuarios, y la necesidad de redefinir los roles del área de recursos humanos.

El trabajo concluyó que el éxito de estos sistemas depende en gran medida de factores organizacionales y humanos —como la capacitación y la gestión del cambio— más que de la tecnología en sí misma, un hallazgo directamente relevante para la implementación de sistemas de gestión de personal en instituciones educativas.

#### 2.2.1.2 Implementación de ERPs en Instituciones de Educación Superior

Pollock y Cornford (2004) analizaron, mediante un estudio de caso en una universidad, los procesos de implementación de sistemas ERP (*Enterprise Resource Planning*). La investigación evidenció que las universidades constituyen organizaciones socialmente complejas y, en muchos sentidos, singulares, cuyos procesos administrativos no siempre se ajustan a los flujos estandarizados que asumen los sistemas comerciales.

Los autores demostraron que el éxito de la implementación depende de adaptar el sistema al contexto institucional, gestionar las expectativas de los distintos actores y acompañar el proceso con estrategias de cambio organizacional, más que de la mera instalación técnica del software.

#### 2.2.1.3 Transformación Digital de Instituciones Educativas

Benavides et al. (2020) realizaron una revisión sistemática de la literatura sobre transformación digital en instituciones de educación superior, analizando investigaciones publicadas entre 2000 y 2019. El estudio identificó los principales impulsores de la transformación digital (demanda de nuevos servicios, presión competitiva, madurez tecnológica), las barreras más frecuentes (resistencia al cambio, limitaciones presupuestarias, brechas de competencias digitales) y las tecnologías habilitadoras aplicadas en el sector educativo.

La revisión concluyó que la transformación digital debe abordarse como un proceso integral de cambio organizacional y no como la simple incorporación de herramientas tecnológicas aisladas.

### 2.2.2 Antecedentes Nacionales

En el contexto de los países en desarrollo, la literatura internacional ofrece hallazgos directamente transferibles a la realidad nacional, razón por la cual se presentan tres estudios cuyos resultados informaron el diseño del sistema. La incorporación de antecedentes locales propiamente dichos se aborda en el apartado 2.2.3, con los criterios de selección que deben satisfacer las fuentes regionales.

#### 2.2.2.1 Toma de Decisiones Basada en Datos en Países en Desarrollo

Voogt y Pieters (2019), en el número especial de la *Journal of Professional Capital and Community* dedicado a la toma de decisiones basada en datos en países en desarrollo, analizaron la influencia del sistema educativo y la cultura organizacional en el uso efectivo de los datos administrativos. El estudio concluyó que la disponibilidad de sistemas de información confiables es condición necesaria, pero no suficiente, para la mejora de la gestión educativa: se requiere además capacidad institucional para interpretar los datos y traducirlos en acciones.

Este hallazgo respalda la decisión de acompañar la implementación del sistema con capacitación y documentación, tal como propone la presente investigación.

#### 2.2.2.2 Obstáculos para la Integración de las TIC en Educación

Pelgrum (2001) presentó los resultados de una evaluación educativa de alcance mundial (IEA) sobre los obstáculos para la integración de las tecnologías de la información y la comunicación (TIC) en la educación. El estudio identificó como principales barreras la insuficiencia de equipos y software, la limitada capacitación de los docentes y el personal administrativo, y la falta de tiempo para familiarizarse con las nuevas herramientas.

Estos obstáculos —documentados en contextos muy diversos— son consistentes con las dificultades observadas en instituciones educativas de recursos limitados y refuerzan la necesidad de soluciones tecnológicas simples, accesibles y acompañadas de formación.

#### 2.2.2.3 Software de Código Abierto en el Ámbito Educativo

Lakhan y Jhunjhunwala (2008) analizaron los patrones de adopción de software de código abierto en instituciones educativas, destacando sus beneficios económicos (eliminación de costos de licenciamiento), su flexibilidad para adaptarse a necesidades específicas y los retos asociados a su adopción (soporte técnico, curvas de aprendizaje, compatibilidad con sistemas existentes).

La investigación concluyó que las instituciones con recursos limitados pueden obtener beneficios significativos del software de código abierto cuando cuentan con documentación adecuada y capacidades técnicas mínimas, precisamente el enfoque adoptado por el presente proyecto.

### 2.2.3 Antecedentes Locales

#### 2.2.3.1 Estado de la Cuestión y Criterios de Incorporación

La revisión de antecedentes locales exige una precisión metodológica que conviene declarar de forma explícita. A diferencia de los antecedentes internacionales, que se localizan en revistas indexadas y resultan verificables de manera directa, los casos regionales se documentan con frecuencia en informes institucionales, actas de consejos directivos, memorias de gestión o repositorios de trabajos de grado cuya localización depende del acceso a fuentes primarias de cada institución. Por esa razón, este apartado se construye con los criterios que deben satisfacer los casos que se incorporen y no con atribuciones de las que no se dispone de respaldo documental.

Los antecedentes locales que se integren a la versión definitiva deberán cumplir cuatro condiciones. En primer lugar, proceder de una fuente localizable: repositorio institucional, publicación oficial, informe de gestión o documento institucional con identificación de autoría y fecha. En segundo lugar, describir una experiencia concreta de sistematización administrativa en una institución educativa de la región, con indicación de su alcance y de su estado. En tercer lugar, permitir la comparación con los hallazgos internacionales ya expuestos, de modo que aporten elementos de contraste y no solo confirmación. En cuarto lugar, declarar sus limitaciones, dado que un caso único no autoriza generalizaciones.

#### 2.2.3.2 Uso Previsto de los Antecedentes Locales

Los casos regionales cumplirán tres funciones en este informe. La primera es contextual: situarán la magnitud del déficit de sistematización administrativa en el ámbito geográfico de aplicación, con datos propios de la zona. La segunda es comparativa: permitirán contrastar si los obstáculos descritos en la literatura —resistencia al cambio, necesidad de capacitación, dependencia del liderazgo institucional— se manifiestan con la misma intensidad en el medio local. La tercera es instrumental: orientarán las decisiones de implementación, en particular la estrategia de gestión del cambio y el diseño de la capacitación.

Mientras esa evidencia local se incorpore, el apartado 8 del índice general mantiene registrada esta sección entre los datos pendientes de completación, con el objeto de que la omisión no pase inadvertida durante la revisión previa a la presentación.

### 2.2.4 Síntesis de Antecedentes

Los antecedentes revisados convergen en cinco patrones. El primero concierne al peso relativo de los factores intervinientes: el resultado de una implementación depende más de condiciones humanas y organizacionales que de la tecnología elegida, hallazgo que Bondarouk y Ruël (2009) formularon al señalar que la gestión del cambio y la capacitación explican el éxito en mayor medida que las prestaciones del sistema. El segundo se refiere a la formación: la capacitación continua aparece en todas las fuentes consultadas como condición de adopción, y Pelgrum (2001) la sitúa entre las barreras principales cuando resulta insuficiente. El tercero atañe a la estrategia de implantación: los enfoques por fases permiten aprender del uso real y ajustar el alcance, en contraste con las implantaciones simultáneas, que concentran el riesgo. El cuarto se refiere al contexto: Pollock y Cornford (2004) demostraron que las instituciones educativas no se comportan como organizaciones estandarizables y que los sistemas deben adaptarse a sus procesos en lugar de forzar la operación contraria. El quinto alude a la documentación: su disponibilidad determina la capacidad de la institución para sostener el sistema sin depender de quien lo construyó, condición que Lakhan y Jhunjhunwala (2008) identificaron como determinante en la adopción de software abierto en el ámbito educativo.

Estos cinco hallazgos informaron las decisiones de diseño y de implementación del sistema desarrollado y orientan, además, la estrategia de acompañamiento prevista para la fase piloto.

## 2.3 BASES TEÓRICAS

### 2.3.1 Ingeniería de Software

#### 2.3.1.1 Ciclo de Vida del Desarrollo de Software

El ciclo de vida del desarrollo de software (SDLC, *Software Development Life Cycle*) proporciona un marco estructurado para el desarrollo de sistemas de información. Según Pressman y Maxim (2019) y Sommerville (2015), el ciclo comprende las fases siguientes:

1. **Análisis de Requerimientos:** Identificación y documentación de las necesidades del sistema.
2. **Diseño del Sistema:** Arquitectura, componentes y especificaciones técnicas.
3. **Implementación:** Codificación del software según las especificaciones de diseño.
4. **Pruebas:** Verificación de que el sistema cumple con los requerimientos.
5. **Despliegue:** Instalación del sistema en el entorno de producción.
6. **Mantenimiento:** Corrección de errores y adaptación a cambios en requerimientos.

En este proyecto se adoptó un enfoque iterativo del ciclo de vida, con ciclos breves de desarrollo y retroalimentación de usuarios, en consonancia con los principios ágiles.

#### 2.3.1.2 Patrones de Diseño Arquitectónicos

Los patrones de diseño arquitectónicos proporcionan soluciones reutilizables a problemas comunes en el diseño de software. De acuerdo con el catálogo clásico de Gamma et al. (1994) y con las prácticas de modelado ágil descritas por Ambler (2002), los patrones adoptados en este proyecto fueron los siguientes:

- **Repository Pattern:** Abstrae la lógica de acceso a datos, proporcionando una interfaz para operaciones CRUD sin exponer detalles de implementación.
- **Service Layer Pattern:** Encapsula la lógica de negocio, separándola de la presentación y el acceso a datos.
- **Model-View-Controller (MVC):** Separa la aplicación en componentes lógicos: modelo (datos), vista (presentación) y controlador (lógica).
- **Dependency Injection:** Facilita el testing y el mantenimiento mediante inyección de dependencias en lugar de creación directa.

Estos patrones contribuyeron a la mantenibilidad, la escalabilidad y la verificabilidad del sistema, en los términos que el Capítulo IV documenta.

#### 2.3.1.3 Metodologías Ágiles de Desarrollo

Las metodologías ágiles enfatizan el desarrollo iterativo, colaboración con clientes, y respuesta al cambio. Según Beck et al. (2001), los principios ágiles incluyen:

- **Desarrollo iterativo:** Entrega continua de funcionalidad en ciclos cortos.
- **Colaboración con clientes:** Involucramiento activo de usuarios finales en el proceso.
- **Respuesta al cambio:** Adaptabilidad a cambios en requerimientos durante el desarrollo.
- **Calidad continua:** Enfoque en calidad técnica y de producto en cada iteración.

El proyecto adoptó un esquema de iteraciones breves con entregas incrementales de funcionalidad, conforme a los planteamientos de Beck et al. (2001) y a las prácticas descritas por Schwaber y Sutherland (2020).

### 2.3.2 Sistemas de Información

#### 2.3.2.1 Sistemas de Gestión de Recursos Humanos

Según Johnson, Carlson y Kavanagh (2021), los sistemas de gestión de recursos humanos automatizan y optimizan los procesos vinculados con el personal. Sus componentes habituales son los siguientes:

- **Gestión de Información de Empleados:** Registro, actualización y consulta de datos personales y laborales.
- **Procesamiento de Nómina:** Cálculo automático de salarios, deducciones y beneficios.
- **Gestión de Tiempo y Asistencia:** Control de horarios, ausencias y permisos.
- **Gestión de Beneficios:** Administración de seguros, pensiones y otros beneficios.
- **Reportes y Analíticas:** Generación de reportes para toma de decisiones.

El sistema desarrollado implementa estos componentes adaptados al contexto educativo, con la salvedad de que la gestión de beneficios se limita a las prestaciones y deducciones previstas en la normativa laboral de aplicación.

#### 2.3.2.2 Sistemas de Información Educativa

Picciano (2011) define los sistemas de información educativa como aquellos diseñados específicamente para apoyar los procesos administrativos y académicos de las instituciones. Según el autor, estos sistemas deben:

- **Adaptarse al contexto educativo:** Considerar las características específicas de instituciones educativas.
- **Integrarse con sistemas existentes:** Compatibilidad con otros sistemas institucionales.
- **Facilitar la toma de decisiones:** Proporcionar datos oportunos y relevantes para administradores.
- **Ser accesibles a usuarios diversos:** Interfaces adaptadas a usuarios con variados niveles de competencia tecnológica.

El sistema desarrollado incorpora estos principios en su diseño, en particular la adaptación al contexto institucional y la accesibilidad para usuarios con competencias tecnológicas diversas, condición que la literatura sobre aceptación tecnológica vincula de manera directa con la intención de uso (Davis, 1989).

#### 2.3.2.3 Arquitectura de Sistemas Empresariales

Laudon y Laudon (2018) describen la arquitectura de sistemas empresariales como el diseño de la infraestructura tecnológica de una organización. Sus componentes característicos son los siguientes:

- **Capa de Presentación:** Interfaces de usuario para interacción con el sistema.
- **Capa de Aplicación:** Lógica de negocio y reglas del sistema.
- **Capa de Datos:** Almacenamiento y gestión de información.
- **Capa de Integración:** Conectividad con otros sistemas y servicios externos.

El sistema desarrollado sigue esta arquitectura de capas, decisión que facilita tanto la prueba aislada de cada nivel como la integración futura con otros sistemas institucionales.

### 2.3.3 Desarrollo de Software

#### 2.3.3.1 Programación Orientada a Objetos

La programación orientada a objetos es un paradigma que organiza el software en unidades que reúnen datos y comportamiento. Según Booch (2007), sus principios fundamentales son los siguientes:

- **Encapsulamiento:** Ocultamiento de detalles de implementación y exposición de interfaces públicas.
- **Herencia:** Creación de nuevas clases basadas en clases existentes.
- **Polimorfismo:** Capacidad de objetos de diferentes tipos de responder al mismo mensaje.
- **Abstracción:** Representación simplificada de entidades complejas.

El sistema emplea este paradigma para modelar las entidades del dominio —empleado, documento, incidencia, asistencia, contrato, préstamo, pago, horario, configuración y usuario— y las relaciones que las vinculan.

#### 2.3.3.2 Bases de Datos Relacionales

Las bases de datos relacionales organizan la información en tablas con relaciones explícitas entre ellas. Según Date (2003) y Elmasri y Navathe (2015), sus ventajas principales son las siguientes:

- **Integridad de datos:** Reglas que aseguran consistencia y precisión de los datos.
- **Flexibilidad en consultas:** Lenguaje SQL para consultas complejas y flexibles.
- **Escalabilidad:** Capacidad para manejar crecientes volúmenes de datos.
- **Estandarización:** SQL como lenguaje estándar para bases de datos relacionales.

El sistema utiliza SQLite como motor relacional y SQLAlchemy como capa de mapeo objeto-relacional, elección coherente con un despliegue local y con un volumen de información acotado.

#### 2.3.3.3 Desarrollo de Interfaces Gráficas

El desarrollo de interfaces gráficas resulta determinante para la usabilidad de las aplicaciones de escritorio. Según Shneiderman et al. (2016), los principios de diseño de interfaces comprenden:

- **Consistencia:** Mantener patrones consistentes en toda la interfaz.
- **Feedback inmediato:** Respuestas rápidas a acciones del usuario.
- **Prevención de errores:** Diseño que minimiza la posibilidad de errores del usuario.
- **Flexibilidad y eficiencia:** Accesos rápidos para usuarios expertos.
- **Estética y minimalismo:** Diseño limpio y enfocado en funcionalidad esencial.

El sistema desarrollado emplea CustomTkinter para construir una interfaz consistente, con validación inmediata, prevención de errores y accesos rápidos para usuarios experimentados.

### 2.3.4 Gestión de Recursos Humanos

#### 2.3.4.1 Procesamiento de Nómina

El procesamiento de nómina comprende el cálculo de remuneraciones, deducciones y prestaciones del personal. Según Mathis et al. (2016), los componentes habituales son los siguientes:

- **Salario base:** Compensación básica por tiempo trabajado.
- **Deducciones legales:** Seguro social, impuesto sobre la renta, pensiones.
- **Beneficios:** Seguros médicos, vacaciones, bonificaciones.
- **Horas extra:** Compensación por trabajo adicional al horario regular.
- **Retenciones:** Deducciones por préstamos o adelantos.

El sistema automatiza estos cálculos conforme a la configuración de cada institución, con parámetros que pueden ajustarse sin modificar el código fuente.

#### 2.3.4.2 Gestión Documental

La gestión documental comprende el control de los documentos vinculados con el personal. Según Guffey y Loewy (2021), sus aspectos centrales son los siguientes:

- **Digitalización:** Conversión de documentos físicos a formato digital.
- **Control de versiones:** Seguimiento de diferentes versiones de documentos.
- **Control de acceso:** Gestión de permisos para acceso a documentos.
- **Retención y disposición:** Políticas sobre retención y eliminación de documentos.
- **Búsqueda y recuperación:** Sistemas eficientes para localizar documentos específicos.

El sistema implementa estas funcionalidades con especial énfasis en el control de vigencia, dado que el vencimiento documental constituye uno de los riesgos administrativos señalados en el diagnóstico inicial.

#### 2.3.4.3 Gestión de Incidencias y Permisos

La gestión de incidencias involucra el control de ausencias, permisos y reposos. Según Dessler (2020), consideraciones importantes incluyen:

- **Tipos de incidencias:** Clasificación de diferentes tipos de ausencias (médicas, personales, vacaciones).
- **Flujo de aprobación:** Procesos para solicitar, aprobar o rechazar incidencias.
- **Impacto en nómina:** Consideración de incidencias en el cálculo de salarios.
- **Cumplimiento legal:** Asegurar cumplimiento de normativas laborales.
- **Historial y auditoría:** Mantener registros completos de todas las incidencias.

El sistema implementa un flujo completo de gestión de incidencias con control de aprobación, registro del responsable de la decisión y efecto directo en el cálculo de la nómina.

## 2.4 BASES LEGALES

### 2.4.1 Normativas de Protección de Datos Personales

El sistema debe cumplir con las normativas de protección de datos personales vigentes en la jurisdicción de aplicación, cuya identificación concreta figura entre los datos pendientes de completación señalados en el apartado 8 del índice general. Los criterios que orientan el diseño en esta materia son los siguientes:

- **Consentimiento informado:** Los empleados deben consentir el procesamiento de sus datos personales.
- **Minimización de datos:** Recopilar solo los datos necesarios para los propósitos del sistema.
- **Seguridad de datos:** Implementar medidas apropiadas para proteger datos personales.
- **Derechos de los individuos:** Permitir acceso, corrección y eliminación de datos personales.
- **Transferencia de datos:** Restricciones sobre la transferencia de datos a terceros.

El sistema atiende estos criterios mediante control de acceso por rol, registro de auditoría de las operaciones sensibles, respaldo cifrado por ubicación restringida y minimización de los datos almacenados, al margen de que la consignación de la norma específica corresponda completarse con la legislación aplicable.

### 2.4.2 Normativas Laborales

El sistema debe cumplir con las normativas laborales vigentes en la jurisdicción de aplicación, entre cuyos extremos se cuentan:

- **Cálculo de nóminas:** Cumplimiento de requisitos legales para cálculo de salarios y deducciones.
- **Registro de horas:** Mantenimiento de registros apropiados de horas trabajadas.
- **Documentación laboral:** Mantenimiento de contratos y documentos laborales requeridos.
- **Permisos y licencias:** Cumplimiento de normativas sobre diferentes tipos de permisos y licencias.
- **Retención de registros:** Mantenimiento de registros por los períodos requeridos legalmente.

El sistema contribuye al cumplimiento de estas disposiciones mediante el cálculo parametrizado, el registro de jornada y el control de vencimientos documentales.

### 2.4.3 Normativas Educativas

Las instituciones educativas están sujetas a normativas específicas que afectan la gestión de personal:

- **Requisitos de personal:** Cualificaciones y certificaciones requeridas para diferentes roles.
- **Documentación de personal:** Documentos requeridos para diferentes categorías de empleados.
- **Reportes obligatorios:** Información que debe reportarse a autoridades educativas.
- **Estándares de calidad:** Normativas sobre calidad de servicios educativos.

El sistema contribuye al cumplimiento de estas disposiciones mediante el control documental con alertas de vencimiento y la generación de los reportes previstos en la configuración institucional.

### 2.4.4 Estándares de Seguridad Informática

El sistema debe observar estándares de seguridad informática en la protección de la información, según los extremos siguientes:

- **Autenticación:** Control de acceso al sistema mediante autenticación de usuarios.
- **Autorización:** Gestión de permisos basada en roles y responsabilidades.
- **Encriptación:** Protección de datos sensibles mediante encriptación apropiada.
- **Auditoría:** Registro de actividades del sistema para fines de auditoría.
- **Respaldo y recuperación:** Procedimientos para respaldo y recuperación de datos.

El sistema implementa estas medidas con el fin de proteger la información del personal y de la institución, y su verificación se documenta en el apartado 4.3.4 del Capítulo IV.

## 2.5 DEFINICIÓN DE TÉRMINOS BÁSICOS

### 2.5.1 Términos Técnicos

- **Sistema de Gestión de Personal:** Aplicación informática diseñada para administrar información y procesos relacionados con empleados de una organización.

- **Nómina:** Proceso sistemático de cálculo y distribución de salarios, beneficios y deducciones a empleados.

- **ORM (Object-Relational Mapping):** Técnica de programación que convierte datos entre sistemas de tipos incompatibles en bases de datos relacionales y lenguajes de programación orientados a objetos.

- **Arquitectura Modular:** Enfoque de diseño de software que divide un sistema en componentes independientes pero interconectados.

- **Interfaz Gráfica de Usuario (GUI):** Sistema visual de interacción entre usuario y computadora mediante gráficos, iconos y menús.

- **Repositorio:** Capa de acceso a datos que abstrae las operaciones de base de datos y proporciona una interfaz para manipulación de objetos del dominio.

- **Servicio:** Capa de lógica de negocio que implementa reglas y procesos del dominio, actuando como intermediario entre la presentación y el acceso a datos.

- **MVC (Model-View-Controller):** Patrón arquitectónico que separa la aplicación en tres componentes principales: modelo (datos), vista (presentación) y controlador (lógica).

- **SQLAlchemy:** Biblioteca ORM de código abierto para Python que facilita la interacción con bases de datos SQL.

- **CustomTkinter:** Biblioteca de interfaz gráfica para Python basada en Tkinter que proporciona widgets modernos y personalizables.

### 2.5.2 Términos de Dominio

- **Empleado:** Persona contratada por una institución educativa para desempeñar funciones específicas.

- **Documento:** Registro físico o digital que contiene información oficial relacionada con un empleado (cédula, título, certificado, etc.).

- **Incidencia:** Evento que afecta la asistencia o disponibilidad de un empleado (permiso, reposo médico, ausencia, vacaciones).

- **Deducción:** Monto descontado del salario de un empleado por concepto legal o contractual (seguro social, pensión, impuesto).

- **Bonificación:** Monto adicional al salario base otorgado por desempeño excepcional, horas extra u otros conceptos.

- **Periodo de Nómina:** Intervalo de tiempo para el cual se calcula y procesa el pago a empleados (generalmente mensual o quincenal).

- **Reporte:** Documento que presenta información resumida o detallada sobre un aspecto específico del sistema (estadísticas de personal, resumen de nómina, etc.).

### 2.5.3 Términos Metodológicos

- **Investigación-Acción:** Metodología de investigación que combina acción real con reflexión sobre esa acción para generar conocimiento.

- **Prototipado Evolutivo:** Enfoque de desarrollo que crea prototipos sucesivos con retroalimentación continua de usuarios.

- **Pruebas de Usabilidad:** Evaluación sistemática de un sistema por usuarios reales para identificar problemas de usabilidad.

- **Validación:** Proceso de evaluar si un sistema cumple con los requerimientos y necesidades de los usuarios.

- **Métricas de Rendimiento:** Medidas cuantitativas del desempeño técnico de un sistema (tiempo de respuesta, uso de recursos, etc.).

## 2.6 MARCO CONCEPTUAL

### 2.6.1 Modelo Conceptual del Sistema

El Sistema de Gestión de Personal y Nómina se organiza conforme al modelo conceptual que representa la Figura 2.1.

**Figura 2.1. Modelo conceptual por capas del sistema**

```text
┌────────────────────────────────────────────────────────────────────────┐
│ CAPA DE PRESENTACIÓN · CustomTkinter                                   │
│ LoginWindow · MainWindow · diez módulos con acceso por rol y atajos    │
│ Ctrl+1 … Ctrl+0: panel de control, empleados, documentos, incidencias, │
│ asistencia, contratos, préstamos, nómina, alertas y configuración      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE SERVICIOS · reglas de negocio y orquestación de flujos         │
│ autenticación · empleados · documentos · incidencias · asistencia ·    │
│ contratos · préstamos · nómina · alertas · configuración               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE REPOSITORIOS · patrón Repository sobre repositorio base        │
│ diez repositorios concretos con consultas reutilizables y transacciones│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ CAPA DE MODELOS · SQLAlchemy ORM                                       │
│ empleados · documentos · incidencias · asistencias · contratos ·       │
│ prestamos · pagos · horarios · configuraciones · usuarios              │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ DOMINIO DE NÓMINA · cálculo aislado de la interfaz y del acceso a datos│
│ motor · parámetros · impuesto sobre la renta · horas extra ·           │
│ prestaciones · seguridad social · préstamos · finiquito                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ SERVICIOS TRANSVERSALES · seguridad, trazabilidad y sostenibilidad     │
│ security · audit_logger · backup_manager · backup_scheduler ·          │
│ pdf_generator · document_manager · exporter · jornada · validators ·   │
│ helpers · actualizador automático                                      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ BASE DE DATOS · SQLite con integridad referencial y migraciones        │
└────────────────────────────────────────────────────────────────────────┘
```

*Fuente: elaboración propia a partir de la arquitectura implementada en `src/`, versión 2.82.*

### 2.6.2 Relaciones entre Componentes

**Flujo de datos del sistema:**
1. El usuario interactúa con la interfaz gráfica, que verifica previamente sus permisos sobre el módulo solicitado.
2. La interfaz invoca al servicio correspondiente y le entrega los datos del formulario.
3. El servicio valida las reglas del dominio y, cuando la operación lo requiere, delega el cálculo en el dominio de nómina.
4. El servicio consulta o persiste la información a través de los repositorios, que operan sobre el ORM.
5. Los resultados retornan por las mismas capas hasta la interfaz, y las operaciones sensibles quedan registradas en la auditoría.

**Principios de Diseño:**
- **Separación de Responsabilidades:** Cada capa tiene una responsabilidad clara
- **Bajo Acoplamiento:** Mínima dependencia entre componentes
- **Alta Cohesión:** Componentes enfocados en una única responsabilidad
- **Abstracción:** Interfaces bien definidas entre capas

## 2.7 CONCLUSIONES DEL CAPÍTULO

Este capítulo ha establecido el fundamento teórico y conceptual necesario para el desarrollo del Sistema de Gestión de Personal y Nómina. Los antecedentes revisados proporcionan lecciones valiosas de implementaciones similares, mientras que las bases teóricas ofrecen los principios conceptuales que guiarán el diseño e implementación del sistema.

El marco legal identifica las normativas que el sistema debe cumplir, asegurando que la solución sea no solo técnicamente sólida sino también legalmente conforme. Las definiciones de términos establecen un vocabulario común para facilitar la comunicación y comprensión del proyecto.

El modelo conceptual presentado describe la arquitectura efectivamente construida, establece las relaciones entre sus componentes y explicita los principios de diseño que rigieron su desarrollo. Este marco teórico sólido proporciona la base necesaria para abordar la metodología de investigación presentada en el siguiente capítulo.