# EVIDENCIA 05 — BITÁCORA DE VERIFICACIÓN Y PENDIENTES

Registro de comandos, consultas documentales e inspecciones practicadas sobre el árbol de trabajo disponible el 23/11/2026. Distingue explícitamente inventario, inspección y ejecución; solo esta última permite reportar el resultado de una suite.

## 1. Verificaciones registradas

| Fecha | Verificación | Método | Resultado observado | Referencia/limitación |
|-------|--------------|--------|---------------------|-----------------------|
| 23/11/2026 | Versión declarada | Lectura de `VERSION` | `3.0.1` | Evidencia 01; no identifica por sí sola el commit del árbol modificado |
| 23/11/2026 | Código Python por capa | `find src -name '*.py' ... wc -l` | 35.797 líneas | Evidencia 01; conteo estático |
| 23/11/2026 | Nodo de sincronización | `find sync_agent -name '*.py' ... wc -l` | 11.443 líneas | Evidencia 01; conteo estático |
| 23/11/2026 | Funciones Python de prueba | `grep -RhoE '^[[:space:]]*(async )?def test_[A-Za-z0-9_]+' tests --include='test_*.py' \| wc -l` | 625 funciones en 38 archivos `test_*.py`; `conftest.py` adicional | Evidencias 02/04 del inventario; no se ejecutó pytest |
| 23/11/2026 | Inventario Android actual (primer corte) | `find android -name '*.kt'` y conteo de líneas | 97 archivos; 22.539 líneas | Corte anterior a los últimos cambios locales de validación; sustituido abajo |
| 23/11/2026 | Recuento Android de cierre | `find android -type f -name '*.kt'` y conteo con `wc -l` | 97 archivos; 22.558 líneas: 88 archivos de producción (21.892 líneas) y 9 de prueba (666 líneas) | Evidencia 06; árbol local con cambios posteriores a la versión base |
| 23/11/2026 | Anotaciones de prueba Android | `grep -Rho '@Test' android/app/src/test --include='*.kt' \| wc -l` | 43 anotaciones | Evidencia 06; no equivale a ejecución satisfactoria |
| 23/11/2026 | Inspección de adjuntos Android | Lectura de repositorio, UI, VM, DAO, entidades y sincronizador | Se identificaron lectura por metadatos, comprobación SHA-256 y canal para documentos/incidencias; corregida rama de primer adjunto y limpieza/aislamiento de estado de ficha | Inspección estática; sin compilación/pruebas ejecutadas |
| 23/11/2026 | Fuentes normativas web | Consulta de Asamblea Nacional, OIT/NATLEX, SUSCERTE/CNTI y repositorios institucionales | Se corrigieron identificaciones de Servicio Comunitario, Infogobierno, LOPNNA, ISLR y LOCTI; se registraron URLs | Evidencia 04; revisión documental parcial, no dictamen legal |
| 23/11/2026 | Build Android (intento) | `cd android && ./gradlew :app:assembleDebug :app:testDebugUnitTest` | El wrapper inicia, pero falla antes de Gradle: `JAVA_HOME is not set and no 'java' command could be found in your PATH` | No se compiló ni ejecutó test Android; revisar JDK y SDK después |
| 23/11/2026 | Disponibilidad Python/pytest | `python --version`; `python -m pytest tests/` | El alias informa que Python no está instalado; no hay intérprete utilizable | No se ejecutó suite Python |

## 2. Pruebas y validaciones no ejecutadas

| Validación | Comando/procedimiento | Estado |
|-----------|------------------------|--------|
| Suite Python | `pytest tests/` | Pendiente: preparar intérprete Python y dependencias del proyecto; conservar salida real |
| Cobertura Python | `pytest tests/ --cov=src --cov-report=term-missing` | Pendiente; definir configuración y línea base comparable |
| Compilación y pruebas Android | `cd android && ./gradlew :app:assembleDebug :app:testDebugUnitTest` | Intento realizado; bloqueado al inicio por falta de Java/JDK. Configurar JDK 17 y Android SDK para reintentar |
| Pruebas de integración de adjuntos | Flujo real app–nodo: adjuntar, reemplazar, descargar, abrir, offline y permisos | Pendiente; inspección estática no sustituye prueba de integración |
| Campo, usabilidad y transferencia | Consentimientos, observaciones, instalación, capacitación, SUS/pre-post | Pendiente; no hay registros fuente en el expediente |
| Revisión jurídica | Cotejo completo de artículos, reformas, aplicabilidad y cálculos con especialista | Pendiente; evidencia 04 registra solo revisión documental parcial |

## 3. Procedimiento de actualización

1. Antes de ejecutar, anotar fecha, commit/tag y entorno (SO, versiones de Python/JDK/Gradle/SDK y dependencias).
2. Ejecutar los comandos de la sección 2 y conservar la salida íntegra como evidencia del mismo commit.
3. Registrar conteo de pruebas, pasadas, fallidas, omitidas y duración; diferenciar definición de prueba de caso parametrizado.
4. Repetir tras cada corrección; no reemplazar resultados previos, sino añadir una entrada con la nueva revisión.
5. Actualizar los capítulos solo con resultados observados y revisar las referencias cruzadas.
6. Para campo, usar datos minimizados/seudonimizados con autorización, instrumento validado y registro de condiciones.

**Regla de cierre:** no se declara una prueba, instalación, validación comunitaria o revisión legal como ejecutada si no existe salida o documento fuente fechado, identificable y revisable.
