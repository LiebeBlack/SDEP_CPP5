# Informes académicos — Informática (octubre de 2026)

Carpeta con los cuatro informes solicitados, en Markdown estándar y con estructura de publicación académica: título delimitado, resumen de 150–250 palabras, introducción con pregunta y objetivos, marco teórico con contraste de corrientes, desarrollo con tablas, discusión con limitaciones, conclusiones analíticas y referencias en APA 7.

| Archivo | Asignatura | Contenido | Extensión |
|---|---|---|---|
| [01_contabilidad.md](01_contabilidad.md) | Contabilidad | Principios, cuentas y tipos de cuentas, libros contables, IVA, ISLR e interés, con asientos, conciliación fiscal y cálculos de ejemplo | ~3.640 palabras |
| [02_socio_critico.md](02_socio_critico.md) | Socio Crítico | Transformación comunitaria, escuelas administrativas contrastadas, calidad de los servicios y sus modelos de medición | ~3.145 palabras |
| [03_proyecto.md](03_proyecto.md) | Proyecto | Informe de investigación, reseña institucional, objetivos, matriz de coherencia, herramientas, diseño comparado y cronograma | ~2.760 palabras |
| [04_redes_aula.md](04_redes_aula.md) | Redes de Computadoras | Diseño de red para el salón de clase: topologías comparadas, VLAN, direccionamiento, seguridad, funcionamiento y pruebas | ~3.400 palabras |

## Revisión 2: qué se corrigió

La segunda pasada se concentró en tres frentes.

**Correcciones factuales y bibliográficas.** Se precisó el título del tratado de Pacioli (*Particularis de computis et scripturis*, dentro de la *Summa de arithmetica*, 1494). Se corrigió la atribución de los tres intereses del conocimiento: corresponden a *Conocimiento e interés* (1968/1982), no a *Teoría de la acción comunicativa* (1981), que ahora aparece citada por su aporte propio, el criterio de validez deliberativa. Se sustituyó el autor erróneo de las normas ANSI/TIA (corresponden a la Telecommunications Industry Association, no a un instituto nacional de normalización) y se completó el nombre del NIST. Se reemplazó la referencia incompleta a «Koontz y O'Donnell» por la edición vigente de Koontz, Weihrich y Cannice (2012) y se añadieron las fuentes que faltaban: Mayo (1933), Bertalanffy (1968), Kano et al. (1984), Wampler (2007), McDonald (1999), Braun y Clarke (2006) y el manual UPEL (2006).

**Contraste y triangulación.** Se incorporaron tablas comparativas donde antes había una sola postura: cuatro tensiones de la medición contable (costo histórico frente a valor razonable, devengo frente a caja, fin financiero frente a fin fiscal, regla frente a juicio); cinco escuelas administrativas con su aporte y su límite; tres modelos de calidad de servicio (SERVQUAL, SERVPERF y Kano); cuatro diseños de investigación con la pregunta que responde cada uno; cuatro topologías de red y tres alternativas de separación de tráfico. Cada tabla se acompaña de una lectura crítica, no de un listado.

**Integración de citas.** Los informes 03 y 04 tenían bibliografía sin presencia en el cuerpo del texto. Ahora las fuentes metodológicas y técnicas se citan donde corresponde (proyecto factible, muestreo intencional, confiabilidad, análisis temático, modelo TCP/IP, RFC 1918).

## Revisión 3: correcciones de exactitud

La tercera pasada atendió errores concretos, no estilo.

**Cifras fiscales.** Se reemplazó la mención genérica a «alícuotas diferenciadas» por la distinción correcta entre alícuota adicional sobre bienes suntuarios y exención de la cesta básica, que no son equivalentes: la primera aumenta el tributo, la segunda lo suprime junto con el crédito fiscal. Se sustituyó la afirmación de que el ISLR corporativo «asciende al 34%» —inexacta, porque la tarifa es progresiva por tramos de unidades tributarias— por la estructura 15/22/34 con sustraendo, y se añadió una conciliación numérica que muestra por qué la tasa efectiva (23,2%) difiere de la marginal. La confusión entre ambas es el error más frecuente en los trabajos de este nivel.

**Cálculo de materiales del informe 04.** La tabla presupuestaba una sola caja de 305 metros para 26 tiradas: no alcanza. Con recorridos promedio de 25 metros el consumo ya supera los 650, y el desperdicio de instalación lleva la cifra por encima de 700, por lo que ahora se prevén tres cajas. Se ajustaron también el patch panel (24 → 48 puertos, coherente con el switch) y el número de rosetas (32 → 26: 24 puestos más dos en la pared docente), y se explicó que el aula cablea 24 puestos mientras los 30 estudiantes simultáneos se completan por Wi-Fi.

**Vacío técnico del 802.1X.** El diseño exigía WPA3-Enterprise sin servidor de autenticación, lo que es inviable. Se incorporó RADIUS alojado en el servidor de recursos, con su consecuencia operativa: si el servicio cae, las sesiones establecidas sobreviven pero las nuevas asociaciones fallan.

**Auditoría de citas.** Se verificó la correspondencia en ambos sentidos. Faltaban en la bibliografía las referencias a Pacioli (1494), citado en el cuerpo del informe 01; y estaban en la bibliografía sin aparecer en el texto Balestrini (2006), Bernal (2010), Elliot (2000), Stake (1995), Tamayo y Tamayo (2003) en el 03, y NIST (2009), ISO/IEC (2022), TIA (2015, 2018), Cisco (2020), Kurose y Ross (2017) y la Ley de Delitos Informáticos en el 04. Todas quedaron integradas donde aportan, no como adorno. Se completaron además los datos de Gaceta de las tres leyes venezolanas del informe 02.

## Antes de entregar

1. **Reemplazar los marcadores.** Todo dato desconocido aparece entre corchetes: `[Nombre y apellidos]`, `[C.I.]`, `[Docente]`, y en el informe de proyecto `[NOMBRE DE LA INSTITUCIÓN]`, `[SECTOR]`, `[CIUDAD/ESTADO]`, `[N.º]`, etc. Basta una búsqueda de `[` para localizarlos todos.
2. **Verificar la vigencia legal.** Las referencias a leyes venezolanas (IVA, ISLR, Código Orgánico Tributario, consejos comunales) describen el marco al momento de redacción; las alícuotas y providencias cambian con frecuencia. Confirmar en Gaceta Oficial antes de la defensa.
3. **Ajustar los datos institucionales del informe 03.** La reseña, la población y el proceso descritos son un andamiaje: deben sustituirse por la información real de la institución donde se ejecuta el proyecto.
4. **Revisar la memoria de cálculo del diseño de red.** El informe 04 propone una solución técnicamente viable, pero las cotizaciones y la medición de cobertura deben corresponder al aula concreta.

## Extensión

Los cuatro informes quedaron por encima del rango de 8–10 páginas acordado inicialmente (12–14 equivalentes, contando las tablas). Las revisiones añadieron contraste y evidencia sin recortar el cuerpo existente. Si la entrega exige un límite estricto, conviene reducir la sección de discusión de cada informe antes que el marco teórico o las tablas: allí se concentra la prosa ampliable y no la evidencia.

El crecimiento más marcado está en el informe 04, donde las correcciones de materiales y de autenticación añadieron explicación técnica. Si el docente pide exactamente diez páginas, ese es el primer candidato a recorte: los apartados 5.2 y 5.3 pueden condensarse sin perder el diseño.

## Conversión a Word

Con Pandoc instalado:

```bash
pandoc 01_contabilidad.md -o 01_contabilidad.docx
pandoc 02_socio_critico.md -o 02_socio_critico.docx
pandoc 03_proyecto.md -o 03_proyecto.docx
pandoc 04_redes_aula.md -o 04_redes_aula.docx
```

Para conservar tipografía institucional, generar primero una plantilla y reutilizarla:

```bash
pandoc -o plantilla.docx --print-default-data-file reference.docx
pandoc 01_contabilidad.md --reference-doc=plantilla.docx -o 01_contabilidad.docx
```

## Criterios de redacción aplicados

Los textos evitan fórmulas de transición mecánicas y resúmenes de cierre convencionales; cada apartado finaliza con una implicación analítica. La longitud de las oraciones alterna deliberadamente, el lenguaje académico se mantiene prudente en las afirmaciones empíricas y las referencias se presentan en APA 7. Las negritas se reservan para conceptos técnicos y las cursivas para términos en latín, extranjeros o títulos de obra.

## Referencias y honestidad bibliográfica

Las fuentes citadas son obras y normas verificables. Dos entradas conservan la marca `(s. f.)` porque no fue posible confirmar la fecha exacta de la versión consultada (VEN-NIF y tasas del BCV). Antes de entregar, conviene abrir cada referencia y completar el dato faltante; un jurado atento suele revisar la correspondencia entre cita y bibliografía.
