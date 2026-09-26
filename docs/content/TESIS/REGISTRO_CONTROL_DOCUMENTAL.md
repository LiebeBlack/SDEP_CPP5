# REGISTRO DE CONTROL DOCUMENTAL

## 1. PROPÓSITO Y ALCANCE

Este registro cumple tres funciones dentro del expediente: identificar el conjunto de documentos que integran el informe, dejar constancia de las modificaciones que cada uno ha recibido y registrar las verificaciones de consistencia que se practicaron sobre el contenido. Su finalidad es permitir que un evaluador externo determine qué versión examina, de qué fuente proviene cada dato y cuáles afirmaciones se encuentran pendientes de evidencia.

El registro abarca la documentación académica contenida en el directorio `TESIS/` y su correspondencia con el código fuente del sistema, en la versión consignada en el archivo `VERSION` del repositorio.

## 2. HISTORIAL DE VERSIONES DEL SISTEMA DOCUMENTADO

| Versión | Hito documentado |
|---------|------------------|
| 1.0.4 | Versión sobre la que se ejecutó la medición de cobertura de pruebas que se conserva como referencia en el Anexo 7 |
| 2.79 | Versión en la que se documentó por primera vez la suite de 323 pruebas, la autenticación con roles y los módulos iniciales |
| 2.82 | Versión vigente al momento de esta revisión: diez módulos funcionales, motor de nómina, dominio de asistencia, contratación y préstamos, y 453 funciones de prueba |

## 3. INVENTARIO DOCUMENTAL Y ESTADO

| Documento | Archivo | Estado | Observación |
|-----------|---------|--------|-------------|
| Proyecto sociotecnológico | `PROYECTO_SOCIAL_TECNOLOGICO.md` | Actualizado | Incorpora referencias bibliográficas, indicadores con su estado y una tabla de ejecución del proyecto |
| Anteproyecto | `ANTEPROYECTO_TESIS.md` | Actualizado | Referencias unificadas con la bibliografía general y nota de actualización sobre compromisos cumplidos |
| Capítulo I | `CAPITULO_I_PLANTEAMIENTO_PROBLEMA.md` | Reestructurado | Diagnóstico anclado en instrumentos y literatura; tiempos verbales coherentes con el trabajo realizado |
| Capítulo II | `CAPITULO_II_MARCO_TEORICO.md` | Actualizado | Citas armonizadas con la lista de referencias; modelo conceptual alineado con la arquitectura real |
| Capítulo III | `CAPITULO_III_METODOLOGIA.md` | Reestructurado | Distingue fases ejecutadas y pendientes; respaldo metodológico citado |
| Capítulo IV | `CAPITULO_IV_RESULTADOS.md` | Reestructurado | Datos verificados sobre la versión 2.82; estructura de registro para la evidencia del piloto |
| Capítulo V | `CAPITULO_V_CONCLUSIONES.md` | Reestructurado | Conteos actualizados; conclusiones ajustadas al estatuto de la evidencia disponible |
| Bibliografía y anexos | `BIBLIOGRAFIA_ANEXOS.md` | Reestructurado | Referencias verificables; anexos alineados con el sistema real |
| Índice general | `INDICE_GENERAL.md` | Reestructurado | Resumen, abstract e inventario actualizados; control de datos pendientes |
| Resumen de la investigación | `RESUMEN_INVESTIGACION.md` | Nuevo | Documento autónomo de resumen estructurado |
| Oficio de presentación de anexos | `OFICIO_1_PRESENTACION_ANEXOS.md` | Nuevo | Marco integrador del compendio sociotecnológico y los anexos |
| Oficio de presentación del resumen | `OFICIO_2_PRESENTACION_RESUMEN.md` | Nuevo | Marco integrador del resumen y los archivos definitivos |
| Registro de control documental | `REGISTRO_CONTROL_DOCUMENTAL.md` | Nuevo | Este documento |

## 4. VERIFICACIONES DE CONSISTENCIA PRACTICADAS

Las comprobaciones que se relacionan a continuación se ejecutaron sobre el repositorio y sus resultados quedaron incorporados al Capítulo IV y al Anexo 7. Se consigna el procedimiento empleado para que cualquier evaluador pueda replicarlo.

| Verificación | Procedimiento | Resultado |
|--------------|---------------|-----------|
| Versión documentada | Lectura de `VERSION` y de `pyproject.toml` | 2.82 en ambos archivos |
| Extensión del código fuente | Recuento de líneas con `wc -l` sobre `src/` | 27 534 líneas en 73 archivos |
| Distribución por capa | Recuento por directorio | Consignada en la Tabla 4.1 del Capítulo IV |
| Número de funciones de prueba | Recuento de coincidencias de `def test_` en `tests/` | 453 funciones en 24 archivos |
| Distribución de pruebas por archivo | Recuento por archivo | Consignada en la Tabla 4.7 del Capítulo IV |
| Esquema de base de datos | Búsqueda de `__tablename__` en `src/models/` | Diez tablas |
| Módulos de interfaz | Lectura de la lista de módulos en `src/gui/main_window.py` | Diez módulos con atajos `Ctrl+1` a `Ctrl+0` |
| Matriz de acceso por rol | Lectura de `PermissionChecker` en `src/utils/security.py` | Consignada en la Tabla 4.6 del Capítulo IV |
| Parámetros de seguridad | Lectura de `SecurityValidator` | PBKDF2-HMAC-SHA256, 200 000 iteraciones, sal de 16 bytes |
| Generación documental | Recuento de métodos de generación en `src/utils/pdf_generator.py` | Catorce tipos de documento |
| Correspondencia entre citas y bibliografía | Revisión cruzada de las citas del cuerpo con la lista de referencias | Sin citas huérfanas ni entradas sin uso |

## 5. ESTADO DE LA EVIDENCIA PENDIENTE

Se relacionan los elementos cuya incorporación depende de mediciones aún no realizadas. Ninguno de ellos se declara cumplido en el informe.

1. Cobertura de pruebas re-medida sobre la versión 2.82 e informe de la última ejecución de la suite, con número de pruebas, resultado y fecha.
2. Resultados de las pruebas de rendimiento y de carga previstas en el apartado 4.3.3.
3. Resultados de las pruebas de usabilidad con sus mediciones de tiempo, éxito, errores y valoración.
4. Resultados de las encuestas de satisfacción y cálculo del coeficiente alfa de Cronbach.
5. Mediciones de tiempos de procesamiento y de tasas de error antes y después de la implementación.
6. Resultados cualitativos y lecciones aprendidas durante el piloto.
7. Tratamiento estadístico de los datos y decisión sobre cada hipótesis.
8. Antecedentes locales con fuentes verificables y normativa legal de la jurisdicción de aplicación.

## 6. CRITERIOS DE REVISIÓN APLICADOS A LOS TEXTOS

La revisión documental se rigió por cinco criterios, cuyo cumplimiento puede comprobarse sobre los archivos citados.

El primer criterio fue la verificabilidad: ninguna cifra de magnitud, ningún nombre de componente y ninguna referencia bibliográfica se aceptó sin comprobación directa sobre el repositorio o sobre la fuente citada. Las afirmaciones que no podían verificarse se reformularon como compromisos o se trasladaron a la lista de evidencia pendiente.

El segundo criterio fue la coherencia interna: se revisó que los objetivos específicos, las hipótesis, las fases metodológicas, las secciones de resultados y las conclusiones describieran el mismo proyecto, con el mismo número de módulos, la misma versión y los mismos plazos.

El tercer criterio fue la correspondencia entre citas y referencias: cada autor mencionado en el cuerpo aparece en la lista bibliográfica con su año y su edición correctos, y no se incluyeron entradas sin uso en el texto.

El cuarto criterio fue la adecuación del registro lingüístico: se revisó la concordancia, la puntuación, la acentuación y el uso de los tiempos verbales, de manera que el producto se describa en pasado cuando está concluido y en futuro solo cuando dependa del piloto.

El quinto criterio fue la honestidad del alcance: se evitó presentar como medido aquello que solo está implementado, y se evitó presentar como implementado aquello que solo está diseñado.

## 7. MANTENIMIENTO DE ESTE REGISTRO

Este registro debe actualizarse cada vez que se modifique un documento del expediente, indicando la fecha, el documento afectado y la naturaleza del cambio. Cuando la evidencia pendiente se incorpore, el informe y este registro deberán actualizarse de manera simultánea para que la constancia de verificación y el contenido verificado mantengan su correspondencia.

---

**Responsable del registro:** [Nombre del Estudiante]
**Última revisión:** [Fecha]
**Versión del sistema documentado:** 2.82
