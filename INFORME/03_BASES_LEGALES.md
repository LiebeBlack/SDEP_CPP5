# BASES LEGALES

**Proyecto:** Desarrollo e implementación de un sistema de gestión de personal y nómina para instituciones educativas utilizando tecnologías de información.
**Sistema documentado:** SDEP_CPP5.
**Documento:** 03 del expediente del informe del estado de la investigación.
**Jurisdicción de aplicación de referencia:** República Bolivariana de Venezuela.

---

## 1. Presentación y criterio de consignación

Este documento consigna el fundamento jurídico del proyecto. Su propósito es doble: identificar las normas que respaldan legalmente el diseño y la operación del sistema, y establecer la correspondencia verificable entre cada exigencia normativa y el control que la implementa. Una base legal que no se traduzca en un control concreto del producto sería una enumeración decorativa; por eso el documento cierra con una tabla de trazabilidad norma–control y con la declaración expresa de las brechas que subsisten.

El marco se ordena conforme a la jerarquía del ordenamiento: la Constitución de la República Bolivariana de Venezuela (CRBV) en el nivel superior; las leyes orgánicas y especiales en el nivel inmediato; los reglamentos y resoluciones administrativas en el siguiente; y, como referencia de calidad y de seguridad, las normas técnicas internacionales que el proyecto adoptó de manera voluntaria. Esa organización responde al principio de jerarquía normativa y permite apreciar de dónde proviene cada obligación.

### 1.1 Nota de verificación normativa

La consignación de artículos se realizó sobre los textos vigentes al momento de la elaboración y con la numeración que estos emplean. Dado que las leyes venezolanas se reforman con periodicidad y que algunas de las normas aquí citadas han sido objeto de adecuaciones parciales, la versión definitiva del informe debe confrontar cada referencia con el texto publicado en la Gaceta Oficial. Las notas que acompañan a cada apartado señalan, cuando corresponde, el extremo sujeto a confirmación. El corpus académico ya registraba la identificación normativa entre los datos pendientes de completación; este documento la desarrolla y conserva el deber de verificación.

Se deja constancia de que la cita de artículos se ofrece con la extensión necesaria para sustentar la correspondencia técnica, y no como transcripción literal del articulado. La transcripción íntegra de las normas, cuando la institución la exija, se incorpora como anexo documental.

---

## 2. Jerarquía del ordenamiento aplicable

```text
┌────────────────────────────────────────────────────────────────────────┐
│ CONSTITUCIÓN DE LA REPÚBLICA BOLIVARIANA DE VENEZUELA (1999)           │
│ trabajo · educación · ciencia y tecnología · administración pública ·  │
│ información · privacidad y protección de datos                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ LEYES ORGÁNICAS Y ESPECIALES                                           │
│ LOTTT · Seguridad Social · ISLR · Educación · LOCTI · Infogobierno ·   │
│ Delitos Informáticos · LOPA · LOPCYMAT · Familia y Maternidad ·        │
│ Firmas Electrónicas                                                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ REGLAMENTOS Y RESOLUCIONES ADMINISTRATIVAS                             │
│ reglamentos de la LOTTT · resoluciones del SENIAT sobre retenciones ·  │
│ instructivos de la autoridad educativa                                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ NORMAS TÉCNICAS DE ADOPCIÓN VOLUNTARIA                                 │
│ ISO/IEC 25010 · ISO/IEC 27001 y 27002 · IEEE 829 · NIST SP 800-63B ·    │
│ OWASP ASVS y guía de almacenamiento de contraseñas                     │
└────────────────────────────────────────────────────────────────────────┘
```

*Fuente: elaboración propia conforme a la jerarquía del ordenamiento jurídico venezolano y a las normas técnicas adoptadas en el proyecto.*

---

## 3. Bases constitucionales

La Constitución de la República Bolivariana de Venezuela (CRBV, 1999) proporciona el fundamento primario del proyecto. Sus disposiciones se agrupan en cinco materias que corresponden a los cinco ámbitos en que el sistema opera.

### 3.1 Trabajo, salario y condiciones laborales

El artículo 87 consagra el derecho al trabajo y el deber de trabajar, y establece que el Estado adoptará las medidas necesarias para que toda persona pueda obtener ocupación productiva. El sistema sirve a esa garantía en un sentido instrumental preciso: contribuye a que la institución remunere a su personal con oportunidad y exactitud, condiciones sin las cuales el derecho al trabajo se vacía de contenido.

El artículo 89 declara que el trabajo es un hecho social y goza de la protección del Estado, y enumera los principios que rigen la materia, entre ellos la irrenunciabilidad de los derechos laborales, la primacía de la realidad sobre las formas y la no discriminación. De ese artículo deriva la exigencia de que las reglas de cálculo de la remuneración no puedan alterarse por vía de un registro informal: el sistema las mantiene como parámetros explícitos y auditables.

El artículo 90 fija la jornada de trabajo en un máximo de ocho horas diarias y cuarenta y cuatro semanales para la jornada diurna. El artículo 91 reconoce el derecho al descanso y a vacaciones remuneradas. El artículo 92 establece el derecho a un salario suficiente y el principio de igual remuneración por igual trabajo. El artículo 93 remite a la ley la regulación de la estabilidad laboral y el artículo 94 garantiza la libertad de trabajo, con la protección de los derechos de quien trabaja por cuenta ajena.

De estos artículos proviene la exigencia de que el motor de cálculo distinga con precisión el salario base, las horas extraordinarias con su recargo, el descanso y las vacaciones, y de que aplique el principio de igual salario a igual trabajo sin depender del criterio particular del operador.

### 3.2 Educación y personal docente

El artículo 102 declara que la educación es un derecho humano y un deber social fundamental. El artículo 103 establece la obligatoriedad de la educación y el artículo 104 dispone que el ingreso, la promoción y la permanencia del personal docente se ajusten a la ley y a criterios de idoneidad académica.

La repercusión de estos artículos sobre el sistema es directa: el control documental con avisos de vencimiento sirve a la verificación de la idoneidad del personal —títulos, certificaciones y credenciales vigentes— y la generación de constancias y reportes se orienta al cumplimiento de las obligaciones que la institución asume ante la autoridad educativa.

### 3.3 Ciencia, tecnología e innovación

El artículo 110 reconoce el interés público de la ciencia, la tecnología, el conocimiento, la innovación y sus aplicaciones, y encomienda al Estado el desarrollo del Sistema Nacional de Ciencia y Tecnología. El proyecto se inscribe en ese mandato en la medida en que produce un bien tecnológico de utilidad social, distribuido bajo licencia abierta y documentado para su reutilización por otras instituciones.

### 3.4 Administración pública, información y control

El artículo 141 funda la Administración Pública en los principios de honestidad, participación, celeridad, eficacia, eficiencia, transparencia, rendición de cuentas y responsabilidad. El artículo 143 reconoce el derecho de los ciudadanos a ser informados de manera oportuna y veraz por la Administración. Ambos artículos sustentan dos funciones del sistema: la generación de información consolidada para la toma de decisiones y el registro de auditoría, que permite reconstruir quién hizo qué y cuándo.

### 3.5 Privacidad y protección de datos personales

El artículo 60 reconoce el derecho a la protección del honor, la vida privada, la intimidad, la propia imagen, la confidencialidad y la reputación. El artículo 48 garantiza el secreto y la inviolabilidad de las comunicaciones privadas. El artículo 28 consagra el derecho de acceso a la información y a los datos que sobre sí misma conste a toda persona en registros oficiales o privados, así como el derecho a conocer el uso que se haga de ellos y a solicitar la actualización, la rectificación o la destrucción de los erróneos: es la institución del habeas data.

De estos artículos deriva el tratamiento que el sistema da a la información del personal: acceso restringido por rol, registro de auditoría de las operaciones sensibles, confidencialidad de las credenciales —las contraseñas se almacenan derivadas, nunca en claro— y garantía de que los datos recogidos se limitan a la finalidad declarada. Venezuela no cuenta con una ley general de protección de datos personales de aplicación transversal; en su ausencia, el habeas data constitucional y las previsiones de resguardo de la información constituyen la referencia principal, y el proyecto las asume como exigencia mínima.

### 3.6 Seguridad de la información como interés del Estado

El artículo 322 declara que la seguridad de la Nación es competencia esencial del Estado y responsabilidad también de las personas naturales y jurídicas que se encuentren en el espacio geográfico nacional. El artículo 326 enuncia los principios de esa seguridad. La protección técnica de la información institucional del personal —respaldos, control de acceso y trazabilidad— se articula con ese deber general de resguardo.

---

## 4. Leyes orgánicas del trabajo y la seguridad social

### 4.1 Ley Orgánica del Trabajo, los Trabajadores y las Trabajadoras (LOTTT)

*Gaceta Oficial Extraordinaria N.º 6.076, del 7 de mayo de 2012.*

La LOTTT es la norma que el dominio de cálculo de nómina debe traducir en reglas verificables. Sus preceptos se vinculan con el sistema en los siguientes extremos.

El artículo 104 define el salario como la remuneración, provecho o ventaja que corresponde al trabajador por la prestación de su servicio, y precisa que comprende, entre otros conceptos, comisiones, primas, gratificaciones, participación en los beneficios, sobresueldos, bono vacacional, recargos por días feriados, horas extraordinarias, trabajo nocturno, alimentación y vivienda; define además el salario normal como la remuneración devengada de forma regular y permanente. El motor de nómina del sistema diferencia el salario base de los conceptos que lo integran y calcula el salario normal conforme a esa distinción.

El artículo 106 obliga al patrono a entregar un recibo de pago en cada oportunidad en que pague remuneraciones, con detalle de conceptos salariales y deducciones. Esta disposición fundamenta la función de generación del recibo de pago en formato PDF y la planilla consolidada de nómina.

El artículo 109 consagra el principio de igualdad salarial: a trabajo igual, en puesto, jornada y condiciones de eficiencia iguales, corresponde salario igual. El sistema lo respeta al no admitir reglas de cálculo divergentes para puestos equivalentes y al mantener la parametrización bajo control del rol administrador.

El artículo 173 establece los límites de la jornada: la diurna, comprendida entre las 5:00 a. m. y las 7:00 p. m., no puede exceder de ocho horas diarias ni de cuarenta horas semanales, y la nocturna tiene su propio límite. El artículo 178 define y delimita las horas extraordinarias, y el artículo 180 regula la elevación del límite de la jornada ordinaria en supuestos excepcionales; el artículo 179 desarrolla la prolongación excepcional de la jornada. El módulo de horas extra del sistema aplica el recargo legal sobre el salario convenido para la jornada ordinaria.

El artículo 142 regula la garantía y el cálculo de las prestaciones sociales. El módulo de prestaciones del sistema implementa el depósito periódico de la garantía y el cálculo que corresponde al egreso, conforme a la configuración institucional.

*Extremos sujetos a confirmación:* el monto del recargo por horas extraordinarias, el porcentaje de la garantía de prestaciones y los topes de deducciones aplicables se confirman contra el texto vigente y sus reformas. El sistema los mantiene como parámetros configurables, de modo que una modificación normativa no exige alterar el código.

### 4.2 Régimen de seguridad social y pensiones

*Ley Orgánica del Sistema de Seguridad Social, Gaceta Oficial N.º 37.600, del 30 de diciembre de 2002, y normas que la desarrollan.*

El sistema de seguridad social venezolano comprende los regímenes prestacionales de salud, pensiones y otras asignaciones económicas, y el régimen de seguridad y salud en el trabajo, administrados por el Instituto Venezolano de los Seguros Sociales y por el sistema de pensiones. Para el proyecto, la consecuencia es que el motor de nómina debe descontar las cotizaciones correspondientes al trabajador y calcular las aportaciones patronales con arreglo a las tasas y a los topes establecidos.

El sistema implementa estos cálculos en el módulo de seguridad social del dominio de nómina, con parámetros configurables por institución. La determinación de las tasas vigentes —que han variado por adecuación administrativa— debe confirmarse contra la normativa del organismo competente y se declara como extremo sujeto a verificación.

### 4.3 Obligaciones tributarias

*Ley de Impuesto sobre la Renta y su reglamento; Código Orgánico Tributario.*

La institución actúa como agente de retención del impuesto sobre la renta sobre los sueldos y salarios que paga a su personal. El sistema calcula la retención conforme a las tarifas y a las unidades tributarias configuradas, y genera los reportes que sustentan la declaración. La fijación anual del valor de la unidad tributaria se mantiene como parámetro de configuración, de modo que la actualización no requiere modificar el código fuente.

El Código Orgánico Tributario impone además deberes de conservación de registros por los plazos legalmente previstos, extremo que el sistema atiende mediante los pagos históricos y la política de retención de respaldos.

### 4.4 Protección de la familia, la maternidad y la paternidad

*Ley Orgánica de Protección de la Familia, la Maternidad y la Paternidad y normas conexas.*

El reposo prenatal, post natal y por paternidad, así como las demás licencias por responsabilidades familiares, se registran en el sistema como incidencias con su tipo, fechas y soporte documental, y su efecto sobre el cálculo de la remuneración se resuelve dentro del motor de nómina. La norma se cita en su denominación general y la remisión precisa a sus artículos se confirma contra el texto vigente.

---

## 5. Leyes del ámbito educativo y de ciencia y tecnología

### 5.1 Ley Orgánica de Educación (LOE)

*Gaceta Oficial Extraordinaria N.º 5.929, del 15 de agosto de 2009.*

La LOE y sus reglamentos establecen los principios y valores rectores de la educación, la organización del sistema educativo y las condiciones del ejercicio de la función docente. Para el proyecto, la norma incide en tres ámbitos: los requisitos documentales y de titulación del personal, que el módulo documental controla y advierte al vencer; las obligaciones de la institución de mantener registros de su personal; y los reportes que deben remitirse ante la autoridad educativa.

*Extremos sujetos a confirmación:* la remisión precisa a los artículos de la LOE sobre ingreso y permanencia del personal docente se confirma contra el texto vigente.

### 5.2 Ley Orgánica de Ciencia, Tecnología e Innovación (LOCTI)

*Gaceta Oficial Extraordinaria N.º 6.151, del 18 de noviembre de 2014.*

La LOCTI tiene por objeto regular el Sistema Nacional de Ciencia, Tecnología e Innovación, con el fin de orientar la actividad científica y tecnológica hacia el desarrollo integral del país. El artículo 110 de la CRBV y la LOCTI enmarcan el proyecto como una contribución tecnológica de origen nacional, construida con componentes abiertos y documentada para su reutilización; sostienen, además, su carácter de bien público antes que de producto comercial.

---

## 6. Leyes del ámbito digital y de la gestión administrativa

### 6.1 Ley de Infogobierno

*Gaceta Oficial N.º 40.274, del 17 de octubre de 2013.*

La Ley de Infogobierno establece los principios, bases y lineamientos que rigen el uso de las tecnologías de información en el Poder Público. Su artículo 1 delimita ese objeto. El artículo 16 establece el deber del Poder Público de emplear tecnologías de información libres y estándares abiertos en sus actuaciones.

La incidencia de esta ley sobre el proyecto es precisa y verificable: el sistema se construyó íntegramente con software de código abierto —Python, SQLAlchemy, CustomTkinter, ReportLab y OpenPyXL— y produce sus exportaciones en formatos abiertos, de modo que la institución no queda sujeta a licenciamiento propietario ni a formatos cerrados. Cuando la institución aplicable sea de naturaleza pública, esta correspondencia constituye un requisito normativo y no solo una ventaja técnica.

*Extremos sujetos a confirmación:* los artículos que regulan los estándares abiertos, la interoperabilidad, la accesibilidad y la seguridad de la información se citan de forma temática y su numeración exacta se confirma contra el texto vigente. La correspondencia con el artículo 16 en materia de tecnologías libres es la que se sostiene con mayor evidencia documental.

### 6.2 Ley Especial contra los Delitos Informáticos

*Gaceta Oficial N.º 37.313, del 30 de octubre de 2001, con las reformas posteriores.*

El ordenamiento sanciona las conductas que atentan contra los sistemas que utilizan tecnologías de información, entre ellas el acceso indebido a sistemas y datos, la interceptación de comunicaciones, la manipulación de datos y la violación de la privacidad de la información. El sistema previene esas conductas mediante autenticación obligatoria, control de acceso por rol, registro de auditoría de las operaciones sensibles y tratamiento restringido de los archivos de documentos. Las funciones que permiten inferir categorías delictivas constituyen, para la institución, un deber de custodia de la información del personal.

*Extremos sujetos a confirmación:* la denominación vigente de la ley y la numeración de los tipos penales deben confirmarse contra la reforma que se encuentre en vigor.

### 6.3 Ley Orgánica de Procedimientos Administrativos (LOPA)

*Gaceta Oficial N.º 2.818 Extraordinario, del 1 de julio de 1981.*

La LOPA regula el procedimiento administrativo de la Administración Pública. Cuando la institución es de naturaleza pública, los actos que emite —constancias, certificaciones y liquidaciones— son actos administrativos sujetos a las exigencias de motivación, registro y notificación. La generación uniforme de documentos en formato PDF y el registro de auditoría contribuyen a la constancia y a la trazabilidad de esos actos.

### 6.4 Ley de Firmas Electrónicas

*Gaceta Oficial N.º 37.148, del 28 de febrero de 2001.*

La ley otorga a la firma electrónica, cuando reúne los requisitos legales, la misma eficacia probatoria que la firma autógrafa. El sistema contempla la constancia de autoría y de integridad de los documentos que genera mediante identificadores, marcas temporales y registros de auditoría. La incorporación de firma electrónica certificada a los documentos emitidos se registra como recomendación de evolución, no como funcionalidad implementada.

### 6.5 Ley Orgánica de Prevención, Condiciones y Medio Ambiente de Trabajo (LOPCYMAT)

*Gaceta Oficial N.º 38.236, del 26 de julio de 2005.*

La LOPCYMAT regula la seguridad y salud en el trabajo y el régimen de los reposos y las certificaciones de incapacidad. El sistema registra los reposos médicos como incidencias con soporte documental y controla la vigencia de los certificados, de modo que la institución pueda acreditar el cumplimiento de sus deberes en esta materia.

---

## 7. Normativa técnica y estándares adoptados

Además del ordenamiento jurídico propiamente dicho, el proyecto adoptó de manera voluntaria un conjunto de normas técnicas que fijan el nivel de calidad y de seguridad exigible al producto. Su adopción no es decorativa: cada una se traduce en una decisión de diseño o en un procedimiento de verificación.

| Norma | Materia | Aplicación en el proyecto |
|-------|---------|----------------------------|
| ISO/IEC 25010:2011 | Modelo de calidad de producto de software | Criterios de calidad del apartado 3.8.1 de la metodología: adecuación funcional, fiabilidad, eficiencia, seguridad, mantenibilidad, portabilidad y usabilidad |
| ISO/IEC 27001 e ISO/IEC 27002 | Gestión y controles de seguridad de la información | Control de acceso por rol, auditoría, respaldos sujetos a retención y tratamiento restringido de archivos |
| IEEE 829-2008 | Documentación de pruebas de software | Estructura de los formatos de registro de pruebas de los anexos |
| NIST SP 800-63B | Directrices de autenticación digital | Derivación de contraseñas con PBKDF2-HMAC-SHA256 y sal aleatoria; comparación en tiempo constante |
| OWASP ASVS y guía de almacenamiento de contraseñas | Verificación de seguridad de aplicaciones | Recomendación de referencia para el número de iteraciones del algoritmo de derivación |
| PEP 8 | Estilo del código Python | Verificación estática con `flake8`, `black` e `isort` |

En materia de derivación de contraseñas conviene una precisión de rigor. El sistema emplea PBKDF2-HMAC-SHA256 con 200 000 iteraciones y sal de 16 bytes. Ese valor excede el mínimo histórico recomendado por el NIST y resulta adecuado para una aplicación de escritorio; sin embargo, las guías más recientes de OWASP recomiendan un número de iteraciones más elevado para este mismo algoritmo. Se consigna el hecho como brecha de endurecimiento verificable y se registra la elevación del parámetro entre las recomendaciones de evolución, sin que ello altere la conformidad con el estándar de autenticación adoptado.

---

## 8. Trazabilidad entre la norma y el control del sistema

La tabla siguiente establece la correspondencia entre cada exigencia normativa y el componente del sistema que la atiende. Es el núcleo verificable de este documento: permite comprobar que ninguna obligación se invocó sin traducción técnica.

| Exigencia normativa | Norma y artículo | Control implementado | Ubicación en el código |
|---------------------|------------------|----------------------|------------------------|
| Remuneración oportuna y exacta | CRBV 87, 89, 92 | Motor de cálculo con reglas explícitas y verificadas | `src/nomina/` |
| Igual salario por igual trabajo | CRBV 92; LOTTT 109 | Parametrización única por puesto, sin reglas divergentes | `src/nomina/parametros.py` |
| Jornada y horas extraordinarias | CRBV 90; LOTTT 173, 178, 180 | Módulo de horas extra con recargo legal configurable | `src/nomina/horas_extra.py` |
| Recibo de pago detallado | LOTTT 106 | Generación de recibo de pago y planilla de nómina en PDF | `src/utils/pdf_generator.py` |
| Prestaciones sociales | CRBV 89; LOTTT 142 | Módulo de prestaciones y provisión periódica | `src/nomina/prestaciones.py` |
| Seguridad social y pensiones | LOSSS y normas conexas | Deducciones de seguridad social parametrizadas | `src/nomina/seguridad_social.py` |
| Retención del impuesto sobre la renta | Ley de ISLR; COT | Cálculo del ISR por tarifa y unidad tributaria | `src/nomina/isr.py` |
| Conservación de registros | COT | Pagos históricos y política de retención de respaldos | `src/utils/backup_manager.py` |
| Requisitos documentales del personal | CRBV 104; LOE | Control documental con avisos de vencimiento | `src/services/documento_service.py` |
| Información oportuna y veraz | CRBV 141, 143 | Reportes consolidados y panel de control | `src/utils/pdf_generator.py`, `src/gui/` |
| Acceso y rectificación de datos propios | CRBV 28 | Consulta de la información del empleado y auditoría de cambios | `src/utils/audit_logger.py` |
| Privacidad y confidencialidad | CRBV 48, 60 | Acceso por rol, contraseñas derivadas, archivos restringidos | `src/utils/security.py`, `src/utils/document_manager.py` |
| Tecnologías libres y estándares abiertos | Ley de Infogobierno, art. 16 | Componentes de código abierto y exportación en formatos abiertos | `requirements.txt`, `src/utils/exporter.py` |
| Protección frente a conductas ilícitas informáticas | Ley Especial contra los Delitos Informáticos | Autenticación, autorización y registro de auditoría | `src/services/auth_service.py`, `src/utils/audit_logger.py` |
| Constancia de los actos emitidos | LOPA | Documentos PDF uniformes y trazabilidad de generación | `src/utils/pdf_generator.py` |
| Seguridad y salud en el trabajo | LOPCYMAT | Registro de reposos y control de vigencia de certificados | `src/services/incidencia_service.py` |
| Gestión de la seguridad de la información | ISO/IEC 27001 y 27002 | Controles de acceso, respaldo, auditoría y retención | `src/utils/` |

*Fuente: elaboración propia a partir de la normativa citada y del código implementado, repositorio en versión 3.0.1.*

---

## 9. Brechas y verificación pendiente

La honestidad del alcance exige declarar lo que no está cubierto o lo que requiere confirmación. Se identifican cinco extremos.

El primero es la confirmación de vigencia y numeración de las normas citadas, según la nota del apartado 1.1. Ninguna afirmación de este documento debe presentarse como definitiva sin esa confrontación con la Gaceta Oficial.

El segundo es la ausencia de una ley general de protección de datos personales en la jurisdicción de referencia. El sistema atiende los principios que el habeas data constitucional impone, pero no puede invocar una norma especial que no existe. Esta circunstancia se declara para que el lector no presuma una conformidad que dependería de un cuerpo legal inexistente.

El tercero es el nivel de iteraciones de la derivación de contraseñas, ya señalado en el apartado 7, que conviene elevar para alinearse con las guías de seguridad más recientes.

El cuarto es la firma electrónica certificada, que no se encuentra implementada y se registra como recomendación de evolución.

El quinto es la confirmación de los parámetros cuantitativos de la normativa laboral y tributaria vigentes —tasas, topes, tarifas y valores de la unidad tributaria—, que el sistema trata como configuración y que deben actualizarse conforme a las disposiciones del período en que se apliquen.

---

## 10. Conclusión

El proyecto se sustenta en un marco jurídico identificable y coherente con su objeto. La Constitución de la República Bolivariana de Venezuela fija los derechos y principios que el sistema sirve —el trabajo y su remuneración, la educación, la ciencia y la tecnología, la información veraz y la privacidad—. Las leyes orgánicas y especiales traducen esos principios en reglas operativas que el dominio de cálculo y las funciones documentales implementan. La normativa técnica adoptada fija el nivel de calidad y de seguridad exigible al producto. Y la tabla de trazabilidad del apartado 8 permite comprobar, uno por uno, que cada exigencia invocada tiene un control que la atiende.

Las brechas declaradas en el apartado 9 no debilitan el marco: lo delimitan con precisión. La confirmación de la vigencia normativa y de los parámetros cuantitativos es una tarea de verificación, no una carencia de fundamento, y su ejecución queda registrada entre los pendientes del expediente conforme al documento [08_DIAGNOSTICO_CONSOLIDACION_Y_AVANCE.md](08_DIAGNOSTICO_CONSOLIDACION_Y_AVANCE.md).

---

## 11. Cuadro resumen normativo

El cuadro siguiente concentra, en una sola vista, la totalidad de las normas invocadas con su identificación, los artículos citados y su estado de verificación. Es el instrumento que permite cerrar la brecha declarada en el apartado 9 mediante una sola revisión contra la Gaceta Oficial.

| Norma | Identificación | Artículos citados | Estado |
|-------|----------------|-------------------|--------|
| Constitución de la República Bolivariana de Venezuela | 1999 | 28, 48, 60, 87, 88, 89, 90, 91, 92, 93, 94, 102, 103, 104, 110, 141, 143, 322, 326 | Verificado por materia; numeración consolidada |
| LOTTT | G.O. Extraordinaria 6.076 del 07/05/2012 | 104, 106, 109, 142, 173, 178, 179, 180, 190 | Artículos de salario, jornada, horas extra y prestaciones verificados |
| Lottt — parámetros cuantitativos | Reformas y adecuaciones | Recargos, topes y tarifas | Por verificar contra el texto vigente |
| Ley Orgánica del Sistema de Seguridad Social | G.O. 37.600 del 30/12/2002 | Régimen prestacional y cotizaciones | Identificación general verificada |
| Ley de Impuesto sobre la Renta | Reformas del período vigente | Retención sobre sueldos y salarios | Por confirmar la reforma aplicable |
| Código Orgánico Tributario | Reforma vigente | Conservación de registros | Identificación general verificada |
| Ley Orgánica de Educación | G.O. Extraordinaria 5.929 del 15/08/2009 | Requisitos documentales y de personal | Por confirmar la numeración de los artículos de personal |
| LOCTI | G.O. Extraordinaria 6.151 del 18/11/2014 | Objeto y fines | Identificación general verificada |
| Ley de Infogobierno | G.O. 40.274 del 17/10/2013 | 1, 16 (tecnologías libres y estándares abiertos) | Artículo 16 verificado por fuente secundaria; resto por confirmar |
| Ley Especial contra los Delitos Informáticos | G.O. 37.313 del 30/10/2001 | Tipos penales informáticos | Denominación vigente por confirmar según reforma |
| LOPA | G.O. 2.818 Extraordinario del 01/07/1981 | Procedimiento administrativo | Identificación general verificada |
| Ley de Firmas Electrónicas | G.O. 37.148 del 28/02/2001 | Eficacia probatoria | Identificación general verificada |
| LOPCYMAT | G.O. 38.236 del 26/07/2005 | Seguridad y salud en el trabajo | Identificación general verificada |
| ISO/IEC 25010:2011 | Norma internacional | Modelo de calidad de producto | Verificada |
| ISO/IEC 27001 y 27002 | Normas internacionales | Controles de seguridad | Verificadas como referencia |
| IEEE 829-2008 | Norma internacional | Documentación de pruebas | Verificada |
| NIST SP 800-63B | Guía técnica | Autenticación digital | Verificada como referencia |
| OWASP (ASVS y guía de contraseñas) | Guía técnica | Número de iteraciones recomendado | Verificada como referencia |

### 11.1 Instrucción de cierre de la brecha normativa

La revisión definitiva consiste en localizar cada norma en su Gaceta Oficial, confirmar la numeración de los artículos citados y corregir cualquier discrepancia. Las normas cuyo estado se declara verificado requieren solo una confirmación de vigencia; las declaradas por confirmar requieren la localización del artículo exacto. Una vez practicada esta revisión, la columna de estado se actualiza y el apartado 9 de este documento se ajusta en consecuencia.

---

**El Autor**
[Nombre del Estudiante]

**Tutor Académico**
[Nombre del Tutor]

**Institución**
[Nombre de la Institución]
