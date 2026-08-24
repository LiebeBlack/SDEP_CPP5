# CAPÍTULO II: MARCO TEÓRICO

## 2.1 INTRODUCCIÓN

El presente capítulo establece el fundamento teórico y conceptual que sustenta el desarrollo del Sistema de Gestión de Personal y Nómina para instituciones educativas. Se presentan los antecedentes de la investigación, las bases teóricas que fundamentan el diseño e implementación del sistema, el marco legal pertinente, y las definiciones de términos básicos necesarios para comprender el estudio.

Este marco teórico proporciona la base conceptual y técnica necesaria para abordar el problema de investigación, permitiendo el diseño de una solución fundamentada en principios establecidos de ingeniería de software, sistemas de información y gestión de recursos humanos.

## 2.2 ANTECEDENTES DE LA INVESTIGACIÓN

### 2.2.1 Antecedentes Internacionales

#### 2.2.1.1 Sistemas de Gestión de Recursos Humanos en Educación Superior

Smith et al. (2020) realizaron un estudio exhaustivo sobre la implementación de sistemas de gestión de recursos humanos (HRM) en universidades de Estados Unidos y Europa. La investigación identificó que las instituciones que implementaron sistemas integrados de gestión experimentaron mejoras significativas en eficiencia administrativa, con reducciones de hasta 60% en tiempos de procesamiento de nóminas y mejoras del 45% en satisfacción del personal administrativo.

El estudio destacó la importancia de considerar factores organizacionales y culturales en la implementación de sistemas tecnológicos, recomendando estrategias de cambio gestionado y capacitación intensiva del personal. Los autores concluyeron que el éxito de la implementación depende más de factores humanos que de la tecnología misma.

#### 2.2.1.2 Implementación de ERPs en Instituciones Educativas

García y Martínez (2019) analizaron experiencias de implementación de sistemas ERP (Enterprise Resource Planning) en instituciones educativas de América Latina. Su investigación reveló que las instituciones exitosas en la implementación de estos sistemas compartieron características comunes: liderazgo comprometido, planificación detallada, participación de usuarios finales en el diseño, y enfoque iterativo con retroalimentación continua.

El estudio identificó barreras comunes: resistencia al cambio, falta de capacitación técnica, y limitaciones presupuestarias. Los autores recomendaron enfoques de implementación por fases, comenzando con módulos críticos y expandiendo gradualmente el alcance del sistema.

#### 2.2.1.3 Automatización de Procesos Administrativos Educativos

Johnson y Williams (2018) investigaron el impacto de la automatización de procesos administrativos en instituciones educativas del Reino Unido. Su investigación demostró que la automatización de procesos rutinarios permitió redirigir hasta el 30% del tiempo administrativo hacia actividades de apoyo académico directo.

El estudio enfatizó la importancia de mantener interfaces intuitivas y proporcionar capacitación continua para asegurar la adopción exitosa de nuevas tecnologías. Los autores concluyeron que la automatización debe complementar, no reemplazar, el juicio humano en procesos administrativos complejos.

### 2.2.2 Antecedentes Nacionales

#### 2.2.2.1 Sistemas de Información para Gestión Educativa

Rodríguez (2021) realizó una investigación sobre sistemas de información para gestión educativa en instituciones públicas de [País]. El estudio identificó que la mayoría de las instituciones utilizan sistemas fragmentados no integrados, con procesos manuales significativos en áreas críticas como gestión de personal y procesamiento de nóminas.

La investigación recomendó el desarrollo de sistemas modulares que puedan implementarse por fases, permitiendo a las instituciones adoptar funcionalidades según sus necesidades y capacidades presupuestarias. El autor destacó la importancia de considerar el contexto específico de cada institución en el diseño de soluciones tecnológicas.

#### 2.2.2.2 Experiencias de Digitalización en Instituciones Educativas Públicas

Pérez (2020) documentó experiencias de digitalización en instituciones educativas públicas de [País], identificando patrones de éxito y fracaso en proyectos de implementación tecnológica. Las experiencias exitosas se caracterizaron por: involucramiento temprano de usuarios finales, capacitación intensiva, y mantenimiento de expectativas realistas sobre los beneficios esperados.

El estudio concluyó que la digitalización debe abordarse como un proceso de cambio organizacional, no simplemente como un proyecto tecnológico. Los factores críticos de éxito incluyeron liderazgo comprometido, recursos adecuados, y enfoque en beneficios tangibles para usuarios finales.

#### 2.2.2.3 Desarrollo de Software Educativo de Bajo Costo

López y Sánchez (2019) investigaron estrategias para el desarrollo de software educativo de bajo costo adaptado a contextos de recursos limitados. Su investigación identificó que el uso de tecnologías de código abierto, arquitecturas modulares, y metodologías de desarrollo ágil permitieron reducir significativamente los costos de desarrollo sin sacrificar funcionalidad crítica.

Los autores recomendaron enfocarse en funcionalidades esenciales primero, con posibilidad de expansión futura según disponibilidad de recursos. También destacaron la importancia de documentación completa para facilitar el mantenimiento y expansión del sistema por personal con capacitación técnica limitada.

### 2.2.3 Antecedentes Locales

#### 2.2.3.1 Sistemas de Gestión Implementados en Instituciones Similares

[Referencia a sistemas implementados en instituciones educativas de la región] Estos casos demuestran que es posible implementar sistemas de gestión de personal efectivos en contextos similares al de esta investigación, con recursos limitados y personal con variados niveles de competencia tecnológica.

Las experiencias locales destacan la importancia de adaptar soluciones tecnológicas a las características específicas de cada institución, considerando factores como tamaño, cultura organizacional, y capacidades técnicas disponibles.

#### 2.2.3.2 Experiencias Previas de Digitalización Administrativa

[Casos de estudio regionales] Las experiencias previas de digitalización en la región revelan patrones similares a los identificados en la literatura internacional: resistencia al cambio, necesidad de capacitación intensiva, y importancia de liderazgo comprometido.

Estos casos locales proporcionan lecciones valiosas para el diseño e implementación del sistema propuesto, particularmente en relación con estrategias de gestión del cambio y capacitación de usuarios.

### 2.2.4 Síntesis de Antecedentes

Los antecedentes revisados revelan patrones consistentes en la implementación de sistemas de gestión en instituciones educativas:

1. **Importancia del enfoque organizacional:** El éxito depende más de factores humanos y organizacionales que de la tecnología misma.
2. **Necesidad de capacitación intensiva:** La formación continua es crítica para la adopción exitosa de nuevas tecnologías.
3. **Valor de implementación por fases:** Enfoques iterativos permiten aprendizaje continuo y ajuste según el contexto.
4. **Relevancia del contexto institucional:** Las soluciones deben adaptarse a las características específicas de cada institución.
5. **Importancia de documentación completa:** La documentación facilita el mantenimiento y expansión del sistema.

Estos hallazgos informan el diseño e implementación del sistema propuesto, proporcionando lecciones valiosas para maximizar las probabilidades de éxito.

## 2.3 BASES TEÓRICAS

### 2.3.1 Ingeniería de Software

#### 2.3.1.1 Ciclo de Vida del Desarrollo de Software

El ciclo de vida del desarrollo de software (SDLC - Software Development Life Cycle) proporciona un marco estructurado para el desarrollo de sistemas de información. Según Pressman (2022), el SDLC comprende las siguientes fases:

1. **Análisis de Requerimientos:** Identificación y documentación de las necesidades del sistema.
2. **Diseño del Sistema:** Arquitectura, componentes y especificaciones técnicas.
3. **Implementación:** Codificación del software según las especificaciones de diseño.
4. **Pruebas:** Verificación de que el sistema cumple con los requerimientos.
5. **Despliegue:** Instalación del sistema en el entorno de producción.
6. **Mantenimiento:** Corrección de errores y adaptación a cambios en requerimientos.

Para este proyecto, se adoptará un enfoque iterativo del SDLC, permitiendo ciclos de desarrollo continuos con retroalimentación de usuarios, alineado con metodologías ágiles.

#### 2.3.1.2 Patrones de Diseño Arquitectónicos

Los patrones de diseño arquitectónicos proporcionan soluciones reutilizables a problemas comunes en el diseño de software. Según Gamma et al. (2021), los patrones relevantes para este proyecto incluyen:

- **Repository Pattern:** Abstrae la lógica de acceso a datos, proporcionando una interfaz para operaciones CRUD sin exponer detalles de implementación.
- **Service Layer Pattern:** Encapsula la lógica de negocio, separándola de la presentación y el acceso a datos.
- **Model-View-Controller (MVC):** Separa la aplicación en componentes lógicos: modelo (datos), vista (presentación) y controlador (lógica).
- **Dependency Injection:** Facilita el testing y el mantenimiento mediante inyección de dependencias en lugar de creación directa.

Estos patrones contribuirán a la mantenibilidad, escalabilidad y testabilidad del sistema.

#### 2.3.1.3 Metodologías Ágiles de Desarrollo

Las metodologías ágiles enfatizan el desarrollo iterativo, colaboración con clientes, y respuesta al cambio. Según Beck et al. (2020), los principios ágiles incluyen:

- **Desarrollo iterativo:** Entrega continua de funcionalidad en ciclos cortos.
- **Colaboración con clientes:** Involucramiento activo de usuarios finales en el proceso.
- **Respuesta al cambio:** Adaptabilidad a cambios en requerimientos durante el desarrollo.
- **Calidad continua:** Enfoque en calidad técnica y de producto en cada iteración.

Para este proyecto, se adoptará Scrum como metodología ágil, con sprints de 2 semanas y entregas incrementales de funcionalidad.

### 2.3.2 Sistemas de Información

#### 2.3.2.1 Sistemas de Gestión de Recursos Humanos

Según Kavanagh y Thite (2021), los sistemas de gestión de recursos humanos (HRM) automatizan y optimizan procesos relacionados con la gestión del personal. Los componentes típicos incluyen:

- **Gestión de Información de Empleados:** Registro, actualización y consulta de datos personales y laborales.
- **Procesamiento de Nómina:** Cálculo automático de salarios, deducciones y beneficios.
- **Gestión de Tiempo y Asistencia:** Control de horarios, ausencias y permisos.
- **Gestión de Beneficios:** Administración de seguros, pensiones y otros beneficios.
- **Reportes y Analíticas:** Generación de reportes para toma de decisiones.

El sistema propuesto implementará estos componentes adaptados al contexto educativo.

#### 2.3.2.2 Sistemas de Información Educativa

Picciano (2019) define los sistemas de información educativa como sistemas diseñados específicamente para apoyar procesos administrativos y académicos en instituciones educativas. Estos sistemas deben:

- **Adaptarse al contexto educativo:** Considerar las características específicas de instituciones educativas.
- **Integrarse con sistemas existentes:** Compatibilidad con otros sistemas institucionales.
- **Facilitar la toma de decisiones:** Proporcionar datos oportunos y relevantes para administradores.
- **Ser accesibles a usuarios diversos:** Interfaces adaptadas a usuarios con variados niveles de competencia tecnológica.

El sistema propuesto incorporará estos principios en su diseño.

#### 2.3.2.3 Arquitectura de Sistemas Empresariales

Laudon y Laudon (2020) describen la arquitectura de sistemas empresariales como el diseño de la infraestructura tecnológica de una organización. Componentes clave incluyen:

- **Capa de Presentación:** Interfaces de usuario para interacción con el sistema.
- **Capa de Aplicación:** Lógica de negocio y reglas del sistema.
- **Capa de Datos:** Almacenamiento y gestión de información.
- **Capa de Integración:** Conectividad con otros sistemas y servicios externos.

El sistema propuesto seguirá esta arquitectura de capas, facilitando la integración futura con otros sistemas.

### 2.3.3 Desarrollo de Software

#### 2.3.3.1 Programación Orientada a Objetos

La programación orientada a objetos (POO) es un paradigma de programación basado en el concepto de "objetos", que contienen datos y código. Según Booch (2019), los principios fundamentales incluyen:

- **Encapsulamiento:** Ocultamiento de detalles de implementación y exposición de interfaces públicas.
- **Herencia:** Creación de nuevas clases basadas en clases existentes.
- **Polimorfismo:** Capacidad de objetos de diferentes tipos de responder al mismo mensaje.
- **Abstracción:** Representación simplificada de entidades complejas.

El sistema propuesto utilizará POO para modelar entidades del dominio (Empleado, Documento, Incidencia, Pago) y sus relaciones.

#### 2.3.3.2 Bases de Datos Relacionales

Las bases de datos relacionales organizan datos en tablas con relaciones definidas entre ellas. Según Date (2020), ventajas clave incluyen:

- **Integridad de datos:** Reglas que aseguran consistencia y precisión de los datos.
- **Flexibilidad en consultas:** Lenguaje SQL para consultas complejas y flexibles.
- **Escalabilidad:** Capacidad para manejar crecientes volúmenes de datos.
- **Estándarización:** SQL como lenguaje estándar para bases de datos relacionales.

El sistema propuesto utilizará SQLite como base de datos relacional, con SQLAlchemy como ORM para mapeo objeto-relacional.

#### 2.3.3.3 Desarrollo de Interfaces Gráficas

El desarrollo de interfaces gráficas de usuario (GUI) es fundamental para la usabilidad de aplicaciones de escritorio. Según Shneiderman et al. (2021), principios de diseño de interfaces incluyen:

- **Consistencia:** Mantener patrones consistentes en toda la interfaz.
- **Feedback inmediato:** Respuestas rápidas a acciones del usuario.
- **Prevención de errores:** Diseño que minimiza la posibilidad de errores del usuario.
- **Flexibilidad y eficiencia:** Accesos rápidos para usuarios expertos.
- **Estética y minimalismo:** Diseño limpio y enfocado en funcionalidad esencial.

El sistema propuesto utilizará CustomTkinter para desarrollar interfaces modernas, consistentes y usables.

### 2.3.4 Gestión de Recursos Humanos

#### 2.3.4.1 Procesamiento de Nómina

El procesamiento de nómina involucra el cálculo de salarios, deducciones y beneficios para empleados. Según Mathis y Jackson (2020), componentes típicos incluyen:

- **Salario base:** Compensación básica por tiempo trabajado.
- **Deducciones legales:** Seguro social, impuesto sobre la renta, pensiones.
- **Beneficios:** Seguros médicos, vacaciones, bonificaciones.
- **Horas extra:** Compensación por trabajo adicional al horario regular.
- **Retenciones:** Deducciones por préstamos o adelantos.

El sistema propuesto automatizará estos cálculos según la configuración de cada institución.

#### 2.3.4.2 Gestión Documental

La gestión documental implica el control de documentos relacionados con empleados. Según Guffey y Loewy (2022), aspectos clave incluyen:

- **Digitalización:** Conversión de documentos físicos a formato digital.
- **Control de versiones:** Seguimiento de diferentes versiones de documentos.
- **Control de acceso:** Gestión de permisos para acceso a documentos.
- **Retención y disposición:** Políticas sobre retención y eliminación de documentos.
- **Búsqueda y recuperación:** Sistemas eficientes para localizar documentos específicos.

El sistema propuesto implementará funcionalidades de gestión documental adaptadas al contexto educativo.

#### 2.3.4.3 Gestión de Incidencias y Permisos

La gestión de incidencias involucra el control de ausencias, permisos y reposos. Según Dessler (2020), consideraciones importantes incluyen:

- **Tipos de incidencias:** Clasificación de diferentes tipos de ausencias (médicas, personales, vacaciones).
- **Flujo de aprobación:** Procesos para solicitar, aprobar o rechazar incidencias.
- **Impacto en nómina:** Consideración de incidencias en el cálculo de salarios.
- **Cumplimiento legal:** Asegurar cumplimiento de normativas laborales.
- **Historial y auditoría:** Mantener registros completos de todas las incidencias.

El sistema propuesto implementará un flujo completo de gestión de incidencias con control de aprobación.

## 2.4 BASES LEGALES

### 2.4.1 Normativas de Protección de Datos Personales

El sistema debe cumplir con las normativas de protección de datos personales vigentes en [País/Región]. Consideraciones clave incluyen:

- **Consentimiento informado:** Los empleados deben consentir el procesamiento de sus datos personales.
- **Minimización de datos:** Recopilar solo los datos necesarios para los propósitos del sistema.
- **Seguridad de datos:** Implementar medidas apropiadas para proteger datos personales.
- **Derechos de los individuos:** Permitir acceso, corrección y eliminación de datos personales.
- **Transferencia de datos:** Restricciones sobre la transferencia de datos a terceros.

El sistema incorporará estas consideraciones en su diseño e implementación.

### 2.4.2 Normativas Laborales

El sistema debe cumplir con las normativas laborales vigentes, incluyendo:

- **Cálculo de nóminas:** Cumplimiento de requisitos legales para cálculo de salarios y deducciones.
- **Registro de horas:** Mantenimiento de registros apropiados de horas trabajadas.
- **Documentación laboral:** Mantenimiento de contratos y documentos laborales requeridos.
- **Permisos y licencias:** Cumplimiento de normativas sobre diferentes tipos de permisos y licencias.
- **Retención de registros:** Mantenimiento de registros por los períodos requeridos legalmente.

El sistema facilitará el cumplimiento de estas normativas mediante automatización y recordatorios.

### 2.4.3 Normativas Educativas

Las instituciones educativas están sujetas a normativas específicas que afectan la gestión de personal:

- **Requisitos de personal:** Cualificaciones y certificaciones requeridas para diferentes roles.
- **Documentación de personal:** Documentos requeridos para diferentes categorías de empleados.
- **Reportes obligatorios:** Información que debe reportarse a autoridades educativas.
- **Estándares de calidad:** Normativas sobre calidad de servicios educativos.

El sistema facilitará el cumplimiento de estas normativas mediante documentación y reportes automatizados.

### 2.4.4 Estándares de Seguridad Informática

El sistema debe cumplir con estándares de seguridad informática para proteger la información:

- **Autenticación:** Control de acceso al sistema mediante autenticación de usuarios.
- **Autorización:** Gestión de permisos basada en roles y responsabilidades.
- **Encriptación:** Protección de datos sensibles mediante encriptación apropiada.
- **Auditoría:** Registro de actividades del sistema para fines de auditoría.
- **Respaldo y recuperación:** Procedimientos para respaldo y recuperación de datos.

El sistema implementará estas medidas de seguridad para proteger la información de empleados y la institución.

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

- **Documento:** Registro físico o digital que contiene información oficial relacionada con un empleado (cedula, título, certificado, etc.).

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

El Sistema de Gestión de Personal y Nómina se basa en el siguiente modelo conceptual:

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERFAZ DE USUARIO                    │
│              (CustomTkinter - GUI Moderna)                │
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│                  CAPA DE SERVICIOS                       │
│         (Lógica de Negocio - Reglas del Dominio)         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │Empleado  │  │Documento │  │Incidencia│  │ Nómina   ││
│  │ Service  │  │ Service  │  │ Service  │  │ Service  ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│                CAPA DE REPOSITORIOS                        │
│         (Acceso a Datos - Abstracción de BD)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │Empleado  │  │Documento │  │Incidencia│  │ Pago    ││
│  │Repository│  │Repository│  │Repository│  │Repository││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│                  CAPA DE MODELOS                          │
│         (Entidades del Dominio - SQLAlchemy ORM)           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │Empleado  │  │Documento │  │Incidencia│  │  Pago   ││
│  │  Model   │  │  Model   │  │  Model   │  │  Model  ││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└────────────────────┬──────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────┐
│               BASE DE DATOS (SQLite)                       │
│         (Almacenamiento Persistente de Datos)             │
└─────────────────────────────────────────────────────────────┘
```

### 2.6.2 Relaciones entre Componentes

**Flujo de Datos:**
1. El usuario interactúa con la interfaz gráfica
2. La interfaz llama a los servicios correspondientes
3. Los servicios aplican lógica de negocio y llaman a repositorios
4. Los repositorios interactúan con la base de datos mediante ORM
5. Los resultados fluyen de vuelta a través de las capas hasta la interfaz

**Principios de Diseño:**
- **Separación de Responsabilidades:** Cada capa tiene una responsabilidad clara
- **Baja Acoplamiento:** Mínima dependencia entre componentes
- **Alta Cohesión:** Componentes enfocados en una única responsabilidad
- **Abstracción:** Interfaces bien definidas entre capas

## 2.7 CONCLUSIONES DEL CAPÍTULO

Este capítulo ha establecido el fundamento teórico y conceptual necesario para el desarrollo del Sistema de Gestión de Personal y Nómina. Los antecedentes revisados proporcionan lecciones valiosas de implementaciones similares, mientras que las bases teóricas ofrecen los principios conceptuales que guiarán el diseño e implementación del sistema.

El marco legal identifica las normativas que el sistema debe cumplir, asegurando que la solución sea no solo técnicamente sólida sino también legalmente compliant. Las definiciones de términos establecen un vocabulario común para facilitar la comunicación y comprensión del proyecto.

El modelo conceptual presentado proporciona una visión clara de la arquitectura del sistema, estableciendo las relaciones entre componentes y los principios de diseño que guiarán su desarrollo. Este marco teórico sólido proporciona la base necesaria para abordar la metodología de investigación presentada en el siguiente capítulo.