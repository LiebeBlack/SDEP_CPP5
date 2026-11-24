# CAPÍTULO II — MARCO REFERENCIAL

## 2.1 Antecedentes de la investigación

### 2.1.1 Antecedentes internacionales

La administración informatizada del personal y de la nómina constituye un campo consolidado de la ingeniería de software, con una línea de desarrollo reconocible en la literatura técnica de las dos últimas décadas: sistemas de planificación de recursos empresariales con módulos de recursos humanos, software de nómina con cumplimiento normativo por país, y la migración de estas soluciones hacia modelos de servicio en la nube. Como marco de comparación, las soluciones comerciales y abiertas ofrecen distintas formas de automatizar procesos administrativos. Sus costos, requisitos de conexión y pertinencia para organizaciones pequeñas deben establecerse con fuentes y análisis comparativos concretos; este borrador no documenta una evaluación de mercado que permita afirmar exclusión o superioridad.

Entre los referentes tecnológicos que podrían analizarse figuran plataformas abiertas de gestión escolar como Gibbon, OpenSIS y Fedena. Para presentarlas como antecedentes de investigación será necesario agregar fuentes primarias o evaluaciones comparables, versiones, alcance funcional y criterios de comparación. No se concluye que carezcan de funciones laborales ni que ningún paquete extranjero atienda el marco venezolano.

### 2.1.2 Antecedentes locales

- **[pendiente de aplicación en campo]** Trabajos especiales de grado del repositorio institucional relacionados con sistemas de información, gestión de personal o nómina en instituciones educativas de la región: identificación, autor, año, método y hallazgo. La búsqueda documental en el repositorio institucional se ejecutará antes de la presentación definitiva y sus resultados se incorporarán en este apartado.

La decisión metodológica de no consignar antecedentes locales hasta disponer de su registro real obedece a la regla de integridad declarada en el índice del borrador: no se citan fuentes no verificadas.

**Nota académica:** este apartado aún requiere antecedentes internacionales y locales debidamente referenciados, con fuentes primarias y síntesis crítica. La ausencia de citas no se resuelve con afirmaciones generales sobre literatura o mercado.

## 2.2 Bases teóricas

### 2.2.1 Sistema de información administrativo

Un sistema de información administrativo es el conjunto organizado de personas, procedimientos, datos y tecnología que capta, procesa, almacena y distribuye información para soportar la operación y la toma de decisiones de una organización. En el caso de la administración de personal, son deseables propiedades como integridad (correspondencia de los datos con la realidad), trazabilidad (posibilidad de atribuir modificaciones a un usuario y momento mediante registros adecuados) y oportunidad (disponibilidad de información cuando el proceso la necesita). El diseño del sistema incorpora validaciones de registro, mecanismos de auditoría y consultas/reportes. Estas características no garantizan por sí solas la integridad de los datos ni la atribución completa de toda operación; requieren revisión y prueba en su contexto de uso.

### 2.2.2 Gestión de recursos humanos y ciclo de la nómina

La gestión de recursos humanos comprende el ciclo de incorporación, administración y desvinculación del personal. En el tramo de administración, el cálculo de la remuneración es un proceso relevante por su periodicidad y sus implicaciones laborales y contables. Sus componentes y obligaciones concretas dependen de la normativa vigente y del tipo de relación laboral. El ciclo de la nómina en el ordenamiento venezolano comprende: la determinación del salario base y de las asignaciones (horas extra con recargo por jornada, bonificaciones), las deducciones (cotizaciones al sistema de seguridad social, fondo de ahorro para viviendas y política habitacional, impuesto sobre la renta conforme a escala progresiva), las prestaciones de origen legal (aguinaldos, bono vacacional, utilidades y la garantía de prestaciones sociales con su régimen de cálculo al término de la relación laboral) y la emisión del comprobante de pago. La documentación del proyecto describe funciones y parámetros para cálculos de nómina, deducciones y prestaciones. Su correspondencia con obligaciones vigentes, incluidos supuestos y bases imponibles, requiere revisión profesional; la descripción del sistema no certifica legalidad de fórmulas o resultados.

### 2.2.3 Gestión documental y expediente del trabajador

La gestión documental aplicada al personal es la administración del expediente: captura, clasificación, almacenamiento, consulta y control de vigencia de los documentos que sustentan la relación laboral. La literatura de gestión documental aporta al proyecto dos principios incorporados en el diseño: la clasificación por tipología documental, que permite tratar de manera distinta documentos de naturaleza distinta, y el control de vencimientos, que convierte el archivo estático en un mecanismo de alerta. En el repositorio se identifican funciones de clasificación documental, carga de archivos, reportes de vencimientos y exportación. La operación, seguridad y utilidad de estas funciones deben validarse en el entorno previsto.

### 2.2.4 Ingeniería de software: arquitectura por capas y patrones

El repositorio está organizado en capas y contiene componentes identificados como repositorios y servicios. La descripción de estructura no equivale a una evaluación de calidad de arquitectura. La separación por capas busca reducir el acoplamiento entre presentación, acceso a datos y lógica de negocio. El código incluye pruebas automatizadas, aunque sus resultados de ejecución no están registrados en este borrador. La mantenibilidad por personal institucional y la sostenibilidad tras una transferencia son hipótesis que deben evaluarse, no conclusiones derivadas solo de la arquitectura.

La correspondencia entre el diseño y el producto puede inspeccionarse en el árbol de código y medirse con el conteo asentado en `EVIDENCIAS/EVIDENCIA_01_METRICAS_CODIGO.md`. El número de líneas describe volumen, no demuestra por sí mismo calidad, mantenibilidad ni facilidad de transferencia.

### 2.2.5 Sincronización de datos y arquitectura híbrida

El diseño de sincronización híbrida busca atender escenarios de conectividad variable; la necesidad y disponibilidad de red en las instituciones previstas siguen pendientes de caracterización. El paquete `sync_agent/` contiene código del nodo y funciones de sincronización; su inventario se documenta en la evidencia 01. La inspección del diseño no prueba desempeño operacional ni despliegue comunitario.

La documentación y el código describen varias decisiones de diseño del subsistema; su comportamiento debe verificarse mediante ejecución e integración. Entre los mecanismos inspeccionables están la persistencia local y el journal, identificadores y claves de deduplicación, funciones de mezcla por campo y la API del nodo con controles de sesión. La atomicidad, convergencia de cambios, resolución de conflictos, autenticación, límites y uso de TLS dependen de la configuración y deben verificarse en pruebas técnicas, revisión de seguridad y despliegue.

El diseño prevé operación local y sincronización cuando la red está disponible. La continuidad real, la resolución de conflictos y el desempeño en una institución dependen de instalación, configuración, pruebas de campo y mantenimiento, por lo que no se presentan aquí como resultados ya validados.

### 2.2.6 Seguridad de la información y control de acceso

En el repositorio de escritorio se identifican mecanismos de autenticación, autorización por rol, auditoría y respaldo. Sus detalles de implementación deben entenderse en el contexto de los archivos inspeccionados; el inventario y la existencia de pruebas no equivalen a una auditoría independiente de seguridad. El registro de auditoría mencionado corresponde al sistema escritorio: la app móvil encola y sincroniza operaciones, y no debe asumirse que replica automáticamente todos los eventos del log de auditoría de escritorio.

El cliente móvil emplea tokens de sesión y el sistema de escritorio dispone de mecanismos de respaldo según su documentación. Estos controles reducen riesgos específicos, pero no permiten afirmar confidencialidad, integridad o disponibilidad globales sin evaluar configuración, operación, gestión de claves, acceso físico, recuperación y respuesta ante incidentes.

### 2.2.7 Subdominio académico

El sistema incorpora estudiantes, grados, inscripciones (matrículas), calificaciones finales y periodos académicos como dominio complementario de la gestión del personal, porque en las instituciones educativas el personal administrativo atiende ambos dominios con el mismo equipo. El diseño contempla autenticación, autorización para determinadas operaciones académicas y sincronización de datos. La autorización legal del tratamiento, la seguridad efectiva y la calidad de las notas dependen también de los procedimientos y responsables institucionales.

### 2.2.8 Cliente móvil nativo

El cliente Android nativo (SDEP Móvil) comprende, en la medición actual asentada en la evidencia 06, 97 archivos Kotlin y 22.558 líneas: 88 archivos y 21.892 líneas de producción, además de 9 archivos de prueba con 666 líneas y 43 anotaciones `@Test`. El cliente usa Kotlin, Jetpack Compose, Room y Hilt; su código contempla una base local, operaciones en cola, negociación de versión/capacidades, tokens de sesión y credencial biométrica. Estos conteos y características son resultado de inspección, no de compilación ni de pruebas ejecutadas. El detalle funcional, las salvaguardas y las limitaciones de verificación se exponen en `SOFTWARE_ANDROID.md` y `EVIDENCIAS/EVIDENCIA_06_INVENTARIO_ANDROID.md`; no se afirma paridad completa ni equivalencia del móvil con la auditoría del escritorio.

## 2.3 Bases legales

La presente sección identifica normas relacionadas con la gestión laboral y académica en Venezuela. Las fechas y números de Gaceta se contrastaron documentalmente con los registros y textos listados en `EVIDENCIAS/EVIDENCIA_04_FUENTES_LEGALES.md` al 23 de noviembre de 2026. La identificación de una ley no equivale a una opinión jurídica ni a certificación del software. La aplicabilidad depende de la naturaleza de la institución, su relación con los usuarios y el tratamiento concreto de datos. Los parámetros de nómina, las plantillas documentales y los procedimientos deberán ser revisados y aprobados por la institución y sus asesores profesionales antes de usarse para producir efectos laborales o tributarios.

### 2.3.1 Constitución de la República Bolivariana de Venezuela

La Constitución de la República Bolivariana de Venezuela, Gaceta Oficial Extraordinaria N.º 5.453 del 24 de marzo de 2000, fundamenta el trabajo en tres de sus disposiciones: el derecho al trabajo y a la protección del trabajador, que exige la correcta y oportuna remuneración; el derecho a la educación y la obligación de las instituciones educativas de rendir cuentas del proceso de evaluación; y el acceso a los servicios de información, que orienta la incorporación de las tecnologías al servicio de la administración pública educativa.

### 2.3.2 Ley Orgánica del Trabajo, los Trabajadores y las Trabajadoras

La LOTTT fue dictada mediante Decreto N.º 8.938 y publicada en la Gaceta Oficial Extraordinaria N.º 6.076 del 7 de mayo de 2012. El registro de la Asamblea Nacional la identifica con vigencia total. Sus disposiciones son pertinentes a la gestión de salarios, jornada, vacaciones, prestaciones y terminación laboral. Los módulos de contratos, incidencias y nómina registran o procesan información relacionada con esos asuntos. La presencia de un campo o una fórmula no demuestra, por sí sola, conformidad con todas las obligaciones legales actuales; la configuración y los resultados deben ser revisados para cada institución por profesionales competentes.

### 2.3.3 Sistema de Seguridad Social y normativa conexa

La Ley Orgánica del Sistema de Seguridad Social fue publicada originalmente en la Gaceta Oficial N.º 37.600 del 30 de diciembre de 2002 y tuvo una reforma parcial publicada en la Gaceta Oficial N.º 39.912 del 30 de abril de 2012. Estas referencias están registradas por la Asamblea Nacional y la OIT. La norma es pertinente a las cotizaciones y aportes, pero no determina por sí sola todas las tasas, bases imponibles y topes aplicables. Antes de utilizar el módulo para cálculos reales, la institución debe validar los parámetros contra las normas sectoriales vigentes y el criterio profesional laboral y contable. La parametrización facilita el mantenimiento, pero no certifica la exactitud jurídica del valor cargado.

### 2.3.4 Impuesto sobre la Renta y su reglamento

El Decreto con Rango, Valor y Fuerza de Ley de Reforma Parcial de la Ley de Impuesto sobre la Renta fue publicado en la Gaceta Oficial Extraordinaria N.º 6.210 del 30 de diciembre de 2015; la Asamblea Nacional señala su vigencia desde el 31 de diciembre de 2015. Esta cita corrige la referencia de 1999 de versiones anteriores. Las retenciones efectivas pueden depender de reglamentos, providencias y parámetros vigentes para el periodo; la fórmula y los parámetros del sistema deben ser revisados antes de utilizarlos en liquidaciones reales. Las pruebas del algoritmo acreditan su comportamiento frente a casos ensayados, no conformidad tributaria.

### 2.3.5 Ley Orgánica de Educación

La Ley Orgánica de Educación, Gaceta Oficial N.º 5.929 Extraordinaria del 15 de agosto de 2009, fundamenta el subdominio académico del sistema: la evaluación como parte integrante del proceso educativo con fines de diagnóstico, formación y promoción, y la necesidad de que las instituciones lleven el registro sistemático del rendimiento estudiantil. El módulo de calificaciones contempla el registro de notas asociado a estudiantes y periodos académicos; la validez de los datos depende de procesos y responsables institucionales.

### 2.3.6 Ley Orgánica para la Protección de Niños, Niñas y Adolescentes

La ley fue publicada inicialmente en la Gaceta Oficial N.º 5.266 del 2 de octubre de 1998 y reformada, entre otras oportunidades, mediante la Gaceta Oficial Extraordinaria N.º 6.185 del 8 de junio de 2015. Los principios de interés superior y protección integral son pertinentes al tratamiento de información académica. El control de acceso por rol y el almacenamiento local son salvaguardas técnicas del sistema; no acreditan por sí mismos cumplimiento integral de la norma. La institución debe definir la finalidad, autorización, acceso, conservación y respuesta ante incidentes que correspondan a sus tratamientos de datos.

### 2.3.7 Ley de Infogobierno

La Ley de Infogobierno se publicó en la Gaceta Oficial N.º 40.274 del 17 de octubre de 2013. La Asamblea Nacional define su objeto en relación con el Poder Público y el Poder Popular. Su aplicación directa debe determinarse según la naturaleza jurídica y funciones de cada institución, no presumirse para todo centro educativo. El sistema incorpora tecnologías abiertas, auditoría, control de acceso y respaldos como características de diseño; estas no constituyen por sí mismas certificación de cumplimiento.

### 2.3.8 Ley de Servicio Comunitario Estudiantil

La Ley de Servicio Comunitario del Estudiante de Educación Superior se publicó en la Gaceta Oficial N.º 38.272 del 14 de septiembre de 2005, según el registro de la Asamblea Nacional y la Universidad de Los Andes. Esta referencia sustituye la identificación errónea que aparecía en borradores previos. La acreditación concreta del servicio —horas, proyecto aprobado, tutoría, informe y evaluación— se rige además por el reglamento de la institución universitaria y debe verificarse con ella; la entrega del software no sustituye esos requisitos.

### 2.3.9 Ley Orgánica de Ciencia, Tecnología e Innovación

La reforma de la Ley Orgánica de Ciencia, Tecnología e Innovación consignada en el expediente corresponde al Decreto N.º 1.411, publicado en la Gaceta Oficial Extraordinaria N.º 6.151 del 18 de noviembre de 2014. La aplicabilidad de sus disposiciones y la vigencia de reformas posteriores deben confirmarse antes de formular conclusiones jurídicas. La licencia de código abierto y la selección de tecnologías abiertas son decisiones del proyecto; no se atribuyen como obligación legal sin artículo específico que lo sustente.

## 2.4 Bases conceptuales

Las definiciones operativas del trabajo, dispuestas alfabéticamente, se refieren al sentido con que cada término se usa en esta investigación:

| Término | Definición operativa |
|---------|---------------------|
| Auditoría | Registro cronológico de las acciones de los usuarios sobre el sistema, consultable y no editable desde los módulos operativos |
| Cota (techo) de cotización | Límite del salario imponible sobre el cual no se aplican cotizaciones de seguridad social, conforme a la norma vigente |
| Expediente | Conjunto de documentos clasificados correspondientes a un empleado |
| Horas extra | Horas laboradas fuera de la jornada ordinaria, remuneradas con recargo según la naturaleza de la jornada (diurna, nocturna, feriada) |
| Incidencia | Todo suceso que afecta la prestación del servicio del empleado: reposo médico, ausencia, permiso |
| Modalidad porcentual | Modo histórico de determinación del impuesto sobre la renta aplicando un porcentaje sobre el salario declarado |
| Modalidad por tramos | Modo de determinación del impuesto aplicando la escala progresiva por tramos de renta con techos de cotización |
| Nodo central | Instancia de sincronización que captura, fusiona y redistribuye los cambios de los puestos en la red local |
| Prestaciones sociales | Garantía legal de participación en el patrimonio de la empresa, con régimen de cálculo al término de la relación laboral |
| Prestaciones de origen legal | Aguinaldo, bono vacacional y utilidades exigibles por la ley al cierre del periodo |
| Token de sesión | Credencial de duración limitada que autentica una sesión del cliente móvil sin conservar la contraseña |
| Sincronización híbrida | Modelo de operación en que cada puesto trabaja con base local y sincroniza con el nodo central cuando la red está disponible |
| Trazabilidad | Propiedad de toda modificación de datos de ser atribuible a un usuario, una fecha y una acción registradas |
| Usabilidad | Medida de la facilidad con que el personal administrativo ejecuta sus tareas con el sistema, operacionalizada por el cuestionario SUS |

---
**Fuentes de este capítulo:** documentación y código inspeccionados del repositorio; registros legislativos y copias institucionales señalados en la evidencia 04; y mediciones propias asentadas en `EVIDENCIAS/`. Los antecedentes académicos y bibliográficos locales pendientes no se sustituyen por referencias no verificadas. Las referencias legales describen pertinencia temática y no constituyen dictamen de conformidad.
