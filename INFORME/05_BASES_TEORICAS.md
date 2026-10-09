# BASES TEÓRICAS

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 05 del expediente del informe del estado de la investigación.

---

## 1. Introducción

Este documento expone los conceptos técnicos, científicos y de ingeniería que sustentan el diseño del sistema construido. Su propósito no es enumerar teorías, sino mostrar de qué manera cada cuerpo conceptual se tradujo en una decisión concreta y verificable dentro del producto. Cada apartado cierra con la indicación del efecto que el concepto tuvo sobre la implementación, de modo que el lector pueda comprobar la correspondencia entre el fundamento y el resultado.

Las bases teóricas se organizan en cinco áreas: la ingeniería de software, que aporta el proceso y los patrones; los sistemas de información, que aportan el inventario funcional y el modelo de capas; el desarrollo de software, que aporta el paradigma, la persistencia y la interfaz; la gestión de recursos humanos, que aporta las reglas del dominio; y la calidad y la seguridad, que aportan los criterios de verificación.

---

## 2. Ingeniería de software

### 2.1 Ciclo de vida del desarrollo de software

El ciclo de vida del desarrollo de software proporciona el marco estructurado que ordena las actividades del proyecto. Conforme a Pressman y Maxim (2019) y a Sommerville (2015), el ciclo comprende el análisis de requerimientos, el diseño del sistema, la implementación, las pruebas, el despliegue y el mantenimiento.

En este proyecto el ciclo se adoptó en su variante iterativa: cada componente se diseñó, se implementó y se probó antes de avanzar al siguiente, y la retroalimentación recogida en cada iteración alimentó la siguiente. Esa elección no es indiferente al contexto. Un desarrollo en cascada habría exigido cerrar por completo los requerimientos antes de escribir código, condición difícil de sostener cuando las necesidades se descubren en la interacción con usuarios que no están familiarizados con la descripción formal de sistemas. La variante iterativa permitió, en cambio, verificar el entendimiento del problema con cada entrega.

**Efecto en la implementación.** La secuencia de desarrollo del proyecto —modelos y repositorios, servicios de negocio, interfaz gráfica, integración y reportes— es la huella del ciclo iterativo en la organización del código. Las tres primeras fases del cronograma documentado en el anexo correspondiente se ejecutaron con este esquema.

### 2.2 Patrones arquitectónicos de diseño

Los patrones de diseño proporcionan soluciones reutilizables a problemas recurrentes de estructura. Del catálogo clásico de Gamma et al. (1994) y de las prácticas de modelado ágil de Ambler (2002), el proyecto adoptó cuatro patrones.

El patrón **Repository** abstrae el acceso a datos tras una interfaz que expone las operaciones de consulta y persistencia sin revelar los detalles del motor subyacente. Su ventaja práctica es doble: aísla al resto del sistema de las particularidades del mapeo objeto-relacional y permite sustituir el mecanismo de persistencia sin afectar la lógica de negocio.

El patrón **Service Layer** encapsula las reglas de negocio y las separa de la presentación y del acceso a datos. Cada operación de negocio tiene un punto único de entrada, lo que evita que una misma regla se reimplemente de forma divergente en varios lugares de la interfaz.

El patrón **Modelo–Vista–Controlador**, en su variante adaptada a aplicaciones de escritorio, separa el modelo de datos de la presentación y de la lógica de control. En el sistema, esa separación se materializa en la distinción entre los modelos del dominio, los servicios que aplican las reglas y los componentes de la interfaz que presentan los resultados.

La **inyección de dependencias** se emplea para que los componentes reciban sus colaboradores en lugar de construirlos internamente, condición que facilita tanto las pruebas automatizadas como la sustitución de un componente por otro.

**Efecto en la implementación.** El repositorio base genérico del que heredan los repositorios concretos, la correspondencia entre servicios y módulos funcionales y la posibilidad de probar el dominio de nómina sin levantar la interfaz son consecuencias directas de estos patrones.

### 2.3 Metodologías ágiles

Las metodologías ágiles enfatizan el desarrollo iterativo, la colaboración con los usuarios y la respuesta al cambio. Conforme a los principios del manifiesto ágil (Beck et al., 2001) y a las prácticas descritas en la guía de Scrum (Schwaber & Sutherland, 2020), el proyecto adoptó iteraciones breves con entregas incrementales de funcionalidad.

Los cuatro principios que más influyeron en el trabajo fueron la entrega continua de funcionalidad en ciclos cortos, la participación de los usuarios finales en la valoración de cada entrega, la adaptabilidad a los cambios de requerimientos y el cuidado de la calidad técnica en cada iteración.

**Efecto en la implementación.** La capacidad de incorporar el módulo de contratación y el motor de nómina, de retirar tres módulos completos con sus tablas y parámetros, y de extender después el sistema hacia el dominio académico sin refundar las capas preexistentes constituye la evidencia más elocuente de que el desarrollo se condujo de forma incremental y disciplinada.

---

## 3. Sistemas de información

### 3.1 Sistemas de gestión de recursos humanos

Los sistemas de gestión de recursos humanos automatizan y optimizan los procesos vinculados con el personal. Conforme a Johnson, Carlson y Kavanagh (2021), sus componentes habituales son la gestión de la información de los empleados, el procesamiento de nómina, la gestión del tiempo y la asistencia, la gestión de beneficios y la generación de reportes y analíticas.

El sistema desarrollado implementa estos componentes adaptados al contexto educativo, con dos precisiones que conviene declarar. La gestión de beneficios se limita a las prestaciones y deducciones previstas en la normativa laboral de aplicación, sin cobertura de seguros privados. Y el control de tiempo se resuelve mediante el registro de incidencias y permisos, sin módulo de marcaje horario, decisión coherente con la naturaleza del trabajo docente y administrativo de las instituciones destinatarias.

**Efecto en la implementación.** El inventario funcional del sistema corresponde a estos cinco componentes, ampliado con el módulo documental y con el dominio académico incorporado posteriormente.

### 3.2 Sistemas de información educativa

Picciano (2011) define los sistemas de información educativa como aquellos diseñados específicamente para apoyar los procesos administrativos y académicos de las instituciones. El autor destaca cuatro exigencias: adaptación al contexto educativo, integración con los sistemas existentes, capacidad para facilitar la toma de decisiones y accesibilidad para usuarios con competencias tecnológicas diversas.

El sistema incorpora estas exigencias en su diseño. La adaptación al contexto se resuelve con la parametrización institucional; la accesibilidad, con una interfaz de formularios guiados y atajos de teclado; y el apoyo a la decisión, con el panel de control y los reportes consolidados. La integración con sistemas externos se reconoce como capacidad potencial y no como funcionalidad implementada, distinción que la literatura sobre adopción tecnológica hace pertinente.

**Efecto en la implementación.** El principio de accesibilidad para usuarios diversos, que Davis (1989) vincula con la intención de uso a través de la facilidad de uso percibida, orientó las decisiones de interfaz: agrupación de campos en formularios temáticos, validación inmediata y prevención de errores.

### 3.3 Arquitectura de sistemas empresariales

Laudon y Laudon (2018) describen la arquitectura de sistemas empresariales como el diseño de la infraestructura tecnológica de una organización, organizada en capas: presentación, aplicación, datos e integración. El sistema desarrollado sigue esa organización, con la particularidad de separar el dominio de cálculo de nómina como una capa propia.

Esa separación no es un adorno arquitectónico. Las reglas financieras de la nómina son la parte del sistema que más probablemente cambie, por reformas normativas o por decisiones internas, y la que más conviene mantener bajo prueba automatizada. Aislarla de la interfaz y del acceso a datos permite modificar un parámetro de cálculo sin tocar la pantalla ni la consulta, y permite probar las reglas sin levantar la aplicación.

**Efecto en la implementación.** La cobertura del dominio de nómina alcanzó el 89 % en la medición del 6 de octubre de 2026, valor compatible con un componente aislado y exhaustivamente probado; la del conjunto de servicios alcanzó el 76 %.

---

## 4. Desarrollo de software

### 4.1 Programación orientada a objetos

La programación orientada a objetos organiza el software en unidades que reúnen datos y comportamiento. Conforme a Booch (2007), sus principios fundamentales son el encapsulamiento, la herencia, el polimorfismo y la abstracción.

El sistema emplea este paradigma para modelar las entidades del dominio —empleado, documento, incidencia, contrato, pago, configuración, usuario y las entidades académicas— y las relaciones que las vinculan. El encapsulamiento se manifiesta en la exposición de interfaces públicas y la reserva de los detalles de implementación; la herencia, en la jerarquía de modelos y de repositorios; y la abstracción, en la representación de entidades complejas mediante clases con responsabilidades delimitadas.

**Efecto en la implementación.** Un modelo como el de empleado encapsula sus atributos y obligaciones —nombres, apellidos y cédula como campos obligatorios, con la cédula sujeta a unicidad—, y esa declaración se refleja directamente en el esquema de la base de datos y en las validaciones del servicio correspondiente.

### 4.2 Bases de datos relacionales

Las bases de datos relacionales organizan la información en tablas con relaciones explícitas. Conforme a Date (2003) y a Elmasri y Navathe (2015), sus ventajas principales son la integridad de los datos, la flexibilidad de consulta mediante el lenguaje estructurado, la escalabilidad y la estandarización del lenguaje.

El sistema utiliza una base de datos embebida con integridad referencial y un mecanismo de migración de esquema que adapta la estructura cuando una versión nueva lo requiere. La elección de un motor embebido responde a tres criterios: la aplicación es de escritorio, el volumen de información de una institución educativa es acotado —del orden de cientos de empleados— y la continuidad del servicio no debe depender de la disponibilidad de un servidor.

El esquema comprende trece tablas. Las siete del núcleo de gestión de personal y nómina corresponden a empleados, documentos, incidencias, contratos, pagos, configuraciones y usuarios; las seis restantes corresponden al dominio académico y a la gestión de sesiones: estudiantes, grados, matrículas, notas finales, periodos académicos y tokens de sesión.

**Efecto en la implementación.** El mecanismo de migración permite abrir una base creada por una versión anterior sin pérdida de información, capacidad verificada en la comprobación de arranque del producto.

### 4.3 Desarrollo de interfaces gráficas

El diseño de la interfaz determina la usabilidad de una aplicación de escritorio. Conforme a Shneiderman et al. (2016), sus principios comprenden la consistencia, la retroalimentación inmediata, la prevención de errores, la flexibilidad y eficiencia para el usuario experimentado, y la estética sobria y enfocada en la función esencial.

El sistema emplea una biblioteca de componentes gráficos que proporciona widgets modernos y personalizables sobre la base de la biblioteca estándar de interfaz de Python. La interfaz mantiene patrones consistentes, valida los datos a medida que se introducen, previene los errores mediante listas de valores admitidos y ofrece accesos rápidos por teclado para el usuario experimentado.

**Efecto en la implementación.** Los nueve módulos se acceden con una combinación de teclas común, las acciones de uso frecuente cuentan con atajos propios, y el panel de control presenta indicadores y gráficos que se dibujan sobre el lienzo del propio componente gráfico, sin incorporar dependencias adicionales.

### 4.4 Derivación de contraseñas y autenticación

La protección de las credenciales se apoya en una función de derivación de clave. El sistema emplea el algoritmo PBKDF2 con HMAC-SHA256, doscientas mil iteraciones y una sal aleatoria de dieciséis bytes, y verifica la contraseña mediante comparación en tiempo constante para evitar la filtración por análisis temporal.

Este esquema corresponde a las recomendaciones de las guías de autenticación digital en materia de funciones de derivación lentas y de sal por usuario. La alternativa —almacenar la contraseña en claro o mediante una función de resumen simple— quedaría expuesta a la recuperación de las credenciales en caso de acceso indebido a la base de datos.

**Efecto en la implementación.** El formato de credencial almacenado incluye el identificador del algoritmo, el número de iteraciones y la sal, lo que permite elevar el costo del cómputo en versiones futuras sin invalidar las credenciales existentes.

---

## 5. Gestión de recursos humanos

### 5.1 Procesamiento de nómina

El procesamiento de nómina comprende el cálculo de remuneraciones, deducciones y prestaciones. Conforme a Mathis et al. (2016), sus componentes habituales son el salario base, las deducciones legales, los beneficios, las horas extraordinarias y las retenciones.

El motor de nómina del sistema implementa estos componentes conforme a la configuración de cada institución, con parámetros que se ajustan sin modificar el código. El cálculo contempla dos modalidades de determinación del impuesto sobre la renta —una porcentual y otra por tramos progresivos con techos de cotización— y el recargo de las horas extraordinarias según la jornada en que se laboren. Las prestaciones, por su parte, comprenden el aguinaldo, el bono vacacional, las prestaciones por antigüedad, la indemnización y el preaviso, calculados de forma proporcional al tiempo servido.

**Efecto en la implementación.** La existencia de dos modalidades de cálculo del impuesto responde a la necesidad de convivir con prácticas institucionales distintas sin bifurcar el sistema, y su verificación forma parte de la suite automatizada.

### 5.2 Gestión documental

La gestión documental comprende el control de los documentos vinculados con el personal. Conforme a Guffey y Loewy (2021), sus aspectos centrales son la digitalización, el control de versiones, el control de acceso, la retención y disposición, y la búsqueda y recuperación.

El sistema implementa estas funciones con énfasis en el control de vigencia, dado que el vencimiento documental constituye uno de los riesgos administrativos señalados en el diagnóstico. Cada documento se registra con su tipo, su fecha de emisión y su fecha de vencimiento cuando corresponde, y el sistema advierte con antelación configurable sobre los que están por vencer y los ya vencidos.

**Efecto en la implementación.** El reporte de vencimientos y el aviso configurable transforman un riesgo latente —la documentación caducada sin advertencia— en un dato visible y accionable para el administrador.

### 5.3 Gestión de incidencias y permisos

La gestión de incidencias involucra el control de ausencias, permisos y reposos. Conforme a Dessler (2020), sus consideraciones principales son la clasificación de los tipos de ausencia, el flujo de aprobación, la repercusión sobre la nómina, el cumplimiento de la normativa laboral y el historial para efectos de auditoría.

El sistema implementa un flujo completo de incidencias con control de aprobación, registro del responsable de la decisión, conservación del documento de soporte y efecto directo en el cálculo de la remuneración del periodo. La incidencia aprobada se traduce en días computables o no computables, y el motor de nómina los considera al determinar el salario proporcional.

**Efecto en la implementación.** La articulación entre el registro de la solicitud y su consecuencia sobre la nómina elimina el ajuste manual posterior, uno de los puntos donde el diagnóstico identificó mayor opacidad.

---

## 6. Calidad y seguridad del software

### 6.1 Modelo de calidad del producto

La evaluación de la calidad adopta como referencia el modelo de calidad de producto de la norma ISO/IEC 25010:2011, que define atributos como la adecuación funcional, la fiabilidad, la eficiencia de desempeño, la seguridad, la mantenibilidad, la portabilidad y la usabilidad. La aplicación de ese modelo al proyecto se detalla en el apartado 3.8.1 de la metodología.

**Efecto en la implementación.** La adecuación funcional se verifica con la suite automatizada; la mantenibilidad, con la separación por capas y la documentación; la portabilidad, con el uso de tecnologías multiplataforma y una base de datos embebida; y la seguridad, con los controles de autenticación, autorización, auditoría y tratamiento de archivos.

### 6.2 Documentación de pruebas

La norma IEEE 829-2008 establece la estructura de la documentación de pruebas de software. El proyecto adoptó esa referencia para los formatos que registran, para cada caso, la funcionalidad verificada, los datos de entrada, el resultado esperado, el resultado obtenido y el estado del caso.

**Efecto en la implementación.** La suite de pruebas automatizadas y los formatos de registro comparten esa estructura, lo que permite rastrear cualquier resultado hasta el caso que lo produjo.

### 6.3 Seguridad de la información

Las normas de la familia ISO/IEC 27000 aportan el marco de gestión y control de la seguridad de la información. El sistema traduce ese marco en un conjunto de medidas concretas: autenticación obligatoria, autorización por rol, cifrado de las credenciales mediante derivación de clave, registro de auditoría de las operaciones sensibles, respaldo con verificación de integridad y política de retención, y tratamiento restringido de los archivos de documentos.

**Efecto en la implementación.** El registro de auditoría es consultable por el administrador y exportable, condición que convierte la seguridad no solo en un control técnico, sino en un instrumento de verificación institucional.

---

## 7. Síntesis: del concepto a la decisión

La tabla siguiente condensa la correspondencia entre cada cuerpo conceptual y la decisión de diseño que produjo. Es la comprobación de que las bases teóricas no son un capítulo independiente del producto, sino su fundamento.

| Fundamento teórico | Decisión de diseño | Evidencia en el repositorio |
|--------------------|--------------------|------------------------------|
| Ciclo de vida iterativo (Pressman & Maxim) | Desarrollo por componentes con verificación previa a la integración | `src/`; suite de pruebas |
| Patrón Repository (Gamma et al.) | Repositorio base genérico y repositorios concretos | `src/repositories/` |
| Patrón Service Layer (Gamma et al.) | Servicios con reglas de negocio y punto de entrada único | `src/services/` |
| Inyección de dependencias (Ambler) | Componentes que reciben sus colaboradores | Servicios y repositorios |
| Sistemas de recursos humanos (Johnson et al.) | Inventario funcional del personal y la nómina | Módulos 1 a 7 |
| Sistemas de información educativa (Picciano) | Accesibilidad y parametrización institucional | `src/gui/`, `configuracion_service.py` |
| Arquitectura por capas (Laudon & Laudon) | Separación de presentación, servicios, datos y cálculo | Capas de `src/` |
| Orientación a objetos (Booch) | Modelo de dominio por entidades | `src/models/` |
| Bases de datos relacionales (Date; Elmasri & Navathe) | Esquema relacional con integridad y migraciones | 13 tablas |
| Principios de interfaz (Shneiderman et al.) | Formularios guiados, atajos y prevención de errores | `theme.py`, atajos `Ctrl+1` a `Ctrl+9` |
| Derivación de contraseñas (NIST SP 800-63B) | PBKDF2-HMAC-SHA256, 200 000 iteraciones, sal de 16 bytes | `src/utils/security.py` |
| Procesamiento de nómina (Mathis et al.) | Motor de cálculo con parámetros por institución | `src/nomina/` |
| Gestión documental (Guffey & Loewy) | Control de vigencia y avisos de vencimiento | `documento_service.py` |
| Gestión de incidencias (Dessler) | Flujo de aprobación con efecto en nómina | `incidencia_service.py` |
| Modelo de calidad (ISO/IEC 25010) | Criterios de calidad y su verificación | Metodología 3.8.1 |
| Documentación de pruebas (IEEE 829) | Formatos de registro de casos | Anexo 7 |
| Gestión de seguridad (ISO/IEC 27001 y 27002) | Controles de acceso, auditoría, respaldo y retención | `src/utils/` |

*Fuente: elaboración propia a partir de las fuentes citadas y del código implementado.*

---

## 8. Conclusión

Las bases teóricas del proyecto se articulan en un cuerpo coherente: la ingeniería de software aporta el proceso y los patrones; los sistemas de información, el inventario funcional y el modelo de capas; el desarrollo de software, el paradigma, la persistencia y la interfaz; la gestión de recursos humanos, las reglas del dominio; y las normas de calidad y seguridad, los criterios de verificación. Cada uno de esos cuerpos deja una huella comprobable en el producto construido, conforme lo demuestra la tabla de síntesis del apartado 7.

La consecuencia que interesa retener es de orden práctico: las decisiones de diseño del sistema no responden a preferencias estilísticas, sino a fundamentos identificables y verificables. Esa característica es la que permite que la arquitectura se explique, se audite y se sostenga sin depender de quien la concibió.

---

## 9. Glosario técnico ampliado

Se reúnen a continuación los términos técnicos que el cuerpo del documento emplea, con una definición orientada a su uso en el proyecto.

**Algoritmo de derivación de clave.** Función que transforma una contraseña en un valor almacenable aplicando un cómputo deliberadamente costoso y una sal por usuario, de modo que la recuperación de la contraseña original resulte inviable en la práctica. El sistema emplea PBKDF2 con HMAC-SHA256.

**Sal (salt).** Valor aleatorio por usuario que se incorpora al cálculo de la derivación para impedir que dos contraseñas idénticas produzcan el mismo valor almacenado y para neutralizar las tablas precalculadas.

**Comparación en tiempo constante.** Técnica de verificación que emplea el mismo tiempo de cómputo con independencia del grado de coincidencia, con el fin de no filtrar información por el tiempo de respuesta.

**Integridad referencial.** Propiedad del esquema relacional que impide que existan registros hijos sin su registro padre, y que preserva la coherencia de las relaciones.

**Migración de esquema.** Procedimiento que adapta la estructura de la base de datos a una versión nueva del sistema, preservando la información existente.

**Registro anticipado (WAL).** Modo de operación de la base de datos que escribe las modificaciones en un archivo de registro antes de aplicarlas, lo que mejora la concurrencia y la resistencia frente a interrupciones.

**Orden total determinista.** Criterio que asigna a cada operación un orden inequívoco e independiente del momento de llegada, condición que garantiza que la mezcla de datos concurrentes converja al mismo resultado en todos los puestos.

**Inyección de dependencias.** Práctica por la que un componente recibe sus colaboradores en lugar de construirlos internamente, lo que facilita la sustitución de componentes y las pruebas.

**Cobertura de pruebas.** Proporción del código ejecutada por la suite de pruebas; se emplea como indicador de la extensión de la verificación, no como medida de su calidad.

**Prueba de integración.** Verificación que comprueba el comportamiento conjunto de varios componentes, a diferencia de la prueba unitaria, que aísla uno solo.

**Triangulación.** Contraste de hallazgos procedentes de fuentes, instrumentos y casos distintos, orientado a distinguir los patrones comunes de las particularidades locales.

**Modelo de calidad de producto.** Conjunto estructurado de atributos —adecuación funcional, fiabilidad, eficiencia, seguridad, mantenibilidad, portabilidad y usabilidad— con que se evalúa la calidad de un producto de software. En el proyecto se adopta el de la norma ISO/IEC 25010:2011.

---

**El Autor**
[Nombre del Estudiante]

**Institución**
[Nombre de la Institución]
