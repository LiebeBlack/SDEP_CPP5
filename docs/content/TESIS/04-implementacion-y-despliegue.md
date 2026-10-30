# 04. IMPLEMENTACIÓN Y DESPLIEGUE

**Documento:** cuarto del compendio académico y tercero del informe técnico.
**Sistema documentado:** SDEP_CPP5, versión 3.0.1.
**Alcance:** proceso de construcción, decisiones de codificación, estrategia de pruebas, protocolo de evaluación, despliegue en la red local y operación.

---

## 4.1 Introducción y estatuto de la evidencia

Este documento describe lo que se construyó, cómo se verificó y cómo se instala. La distinción entre esas tres cosas se mantiene a lo largo del texto. Las afirmaciones sobre el producto se apoyan en el código y en la estructura del repositorio. Las afirmaciones sobre pruebas describen la estrategia y las suites existentes. Las afirmaciones sobre resultados de rendimiento y usabilidad se presentan como protocolo y tablas de registro, porque su ejecución corresponde a la Fase IV y requiere la red y los usuarios de la institución.

Esa distinción no debilita el documento: lo hace verificable. Un informe que presentara cifras de latencia sin haber ejecutado la medición sería más vistoso y menos útil, y un tribunal que pidiera la trazabilidad de esas cifras no encontraría respaldo. Aquí cada tabla de resultados indica el procedimiento que la produce y el archivo donde se registra.

---

## 4.2 Entorno de desarrollo y stack

### 4.2.1 Tecnologías

| Componente | Tecnología | Versión declarada | Función |
|---|---|---|---|
| Lenguaje | Python | 3.15 o superior | Ejecución de la aplicación y del nodo central |
| ORM | SQLAlchemy | 2.0.54 o superior | Mapeo objeto-relacional y sesiones |
| Base de datos | SQLite | Integrada en Python | Persistencia local y central |
| Interfaz | CustomTkinter | 6.0.0 o superior | Componentes gráficos |
| Imágenes | Pillow | 12.0.0 o superior | Fotografías y recursos |
| PDF | ReportLab | 5.0.0 o superior | Generación de documentos |
| Exportación | OpenPyXL | 3.1.5 o superior | Archivos Excel |
| Configuración | python-dotenv | 1.2.0 o superior | Variables de entorno |
| Pruebas | pytest y pytest-cov | 9.1.0 y 7.1.0 o superiores | Suite automatizada y cobertura |
| Empaquetado | PyInstaller | 6.22.0 o superior | Ejecutable de Windows y Linux |
| Instalador | Inno Setup | 6 | Instalador de Windows |

La versión de Python se fijó en 3.15 porque el proyecto utiliza la sintaxis de tipos moderna y porque las versiones de las bibliotecas se verificaron sobre ese intérprete. Las versiones mínimas de SQLAlchemy y PyInstaller no son arbitrarias: las anteriores no declaran compatibilidad con Python 3.15 o arrastran vulnerabilidades corregidas en las versiones indicadas.

### 4.2.2 Estructura del repositorio

```text
SDEP_CPP5/
├── src/
│   ├── config/          configuración, rutas y sesión de base de datos
│   ├── gui/             nueve módulos, tema y widgets de gráficos
│   ├── models/          trece entidades y enumeraciones
│   ├── nomina/          motor de cálculo puro
│   ├── repositories/    acceso a datos
│   ├── services/        reglas de negocio
│   ├── utils/           seguridad, auditoría, respaldos, PDF y exportación
│   └── main.py          punto de entrada y autoverificación
├── sync_agent/          paquete independiente de sincronización
├── tests/               32 archivos test_*.py y conftest.py
├── updater/             actualización automática
├── installer/           configuración de Inno Setup
├── spec/                especificación de PyInstaller
├── tools/               generación y verificación de documentación
├── docs/                portal de documentación
└── TESIS/               compendio académico
```

La separación entre `src/` y `sync_agent/` es deliberada. El agente puede ejecutarse solo, con el comando `python -m sync_agent`, o embebido en la aplicación mediante el enganche al ORM. Esa independencia permite probar el motor de mezcla sin levantar la interfaz y permite que la aplicación siga funcionando si la sincronización se desactiva.

### 4.2.3 Distribución del código

El recuento medido sobre la versión 3.0.1 asigna 33 601 líneas a `src/`, distribuidas en 81 archivos, 10 904 líneas a `sync_agent/` en 19 archivos y 18 635 líneas al cliente Android en 82 archivos Kotlin. La mayor proporción corresponde a la interfaz, con 13 266 líneas, seguida por los servicios transversales, con 5 525, y por los servicios de negocio, con 4 332. El dominio de nómina, que concentra las reglas de cálculo, ocupa 1 502 líneas y no depende de la interfaz ni del acceso a datos.

| Capa | Archivos | Líneas | Proporción |
|---|---|---|---|
| Presentación | 10 | 13 266 | 39,5 % |
| Servicios transversales | 10 | 5 963 | 17,7 % |
| Servicios de negocio | 11 | 5 378 | 16,0 % |
| Repositorios | 16 | 2 599 | 7,7 % |
| Modelos | 17 | 1 969 | 5,9 % |
| Configuración | 3 | 1 719 | 5,1 % |
| Dominio de nómina | 9 | 1 513 | 4,5 % |
| Seguridad de contexto | 3 | 409 | 1,2 % |
| Entrada y paquete | 2 | 785 | 2,3 % |
| **Total** | **81** | **33 601** | **100 %** |

*Fuente: recuento con `wc -l` sobre `src/` el 30 de octubre de 2026, versión 3.0.1. Las cifras anteriores (77 archivos y 29 475 líneas) correspondían al corte del 9 de octubre y quedaron superadas por las incorporaciones posteriores.*

---

## 4.3 Fases de construcción

### 4.3.1 Organización del trabajo

La construcción se organizó en iteraciones de dos semanas. Cada iteración cerraba con una versión ejecutable, una suite de pruebas en verde y una nota de desarrollo que registraba las decisiones y los defectos conocidos. Las notas se conservan en `NOTAS_DESARROLLO.md` y son la fuente primaria de este apartado.

| Iteración | Semanas | Contenido | Entregable |
|---|---|---|---|
| 1 | 13 a 14 | Modelos, configuración, base de datos y autenticación | Login funcional y esquema inicial |
| 2 | 15 a 16 | Empleados, documentos y auditoría | Expediente del trabajador |
| 3 | 17 a 18 | Incidencias, contratos y reportes | Módulos de personal completos |
| 4 | 19 a 20 | Dominio de nómina y recibos | Cálculo y PDF de nómina |
| 5 | 21 a 22 | Estudiantes, grados y matrículas | Dominio académico |
| 6 | 23 a 24 | Calificaciones, boletín y acta | Módulo de notas |
| 7 | 25 a 26 | Sincronización, respaldos y empaquetado | Producto instalable |

La secuencia no fue casual. Los módulos de personal se construyeron antes que los académicos porque el esquema de sincronización se probó primero sobre entidades simples y luego se extendió a las notas, que tienen más claves foráneas y más restricciones de autorización. Esa progresión permitió corregir el journal con un volumen manejable de casos antes de incorporar el dominio académico.

### 4.3.2 Decisiones de codificación

**Tipos explícitos en el dominio de cálculo.** Los importes se representan con `Decimal`, no con `float`. La decisión evita los errores de redondeo que aparecen al sumar deducciones y se verificó con pruebas que comparan el total calculado con el total esperado al centavo.

**Validación en tres niveles.** La interfaz impide el envío de formularios incompletos, el servicio rechaza los valores fuera de rango y la base impone las restricciones de unicidad y de clave foránea. La redundancia es intencional: cada nivel protege contra un tipo distinto de error.

**Separación del cálculo y de la persistencia.** El paquete `src/nomina` recibe parámetros y devuelve resultados; no consulta la base ni escribe en ella. Los servicios leen la configuración, llaman al motor y persisten el resultado. Esa separación permitió probar el cálculo con parámetros fijos y detectar los casos límite de topes y recargos.

**Captura por eventos del ORM.** El journal no depende de que cada servicio llame a una función de registro. Se engancha a los eventos de la sesión, de modo que un CRUD nuevo queda capturado sin modificar el servicio. La decisión reduce el riesgo de olvido y se verificó con pruebas que crean entidades desde servicios distintos.

**Errores del dominio con nombre propio.** Las reglas de negocio lanzan excepciones específicas, no excepciones genéricas. La interfaz las traduce a mensajes comprensibles y la auditoría registra el código. Esa práctica permitió distinguir en los registros entre un error del usuario y un defecto del sistema.

### 4.3.3 Fragmentos representativos

El enganche de captura se registra una sola vez y cubre todas las sesiones:

```python
event.listen(Session, "before_flush", _antes_de_confirmar)
event.listen(Session, "after_flush_postexec", _despues_de_confirmar)
```

La espera tras un fallo crece de forma exponencial y lleva azar para desincronizar los reintentos de los puestos:

```python
base: int = min(30 * (2 ** max(0, fallos - 1)), ESPERA_MAXIMA)
return base + random.uniform(0, min(5.0, base * 0.1))
```

La simultaneidad de dos escrituras se define con una tolerancia de dos segundos, porque los relojes de dos equipos no están perfectamente sincronizados:

```python
EPSILON_RELOJ = timedelta(seconds=2)
```

Los parámetros de nómina tienen valores por defecto conservadores, de modo que una configuración incompleta no impide calcular:

```python
VALORES_POR_DEFECTO = {
    "porcentaje_seguro": 4.5,
    "porcentaje_pension": 5.0,
    "porcentaje_impuesto": 0.0,
    "recargo_hora_extra_diurna": 25.0,
    "recargo_hora_extra_nocturna": 50.0,
    "recargo_hora_extra_feriada": 100.0,
}
```

Estos fragmentos no son ejemplos ilustrativos: son líneas del producto y pueden localizarse en los archivos citados. La selección se hizo por su valor explicativo, no por su complejidad.

---

## 4.4 Estrategia de pruebas

### 4.4.1 Niveles

La suite se organiza en cuatro niveles. Las pruebas unitarias verifican funciones y reglas aisladas. Las de integración verifican la interacción entre servicios, repositorios y base de datos. Las de sincronización levantan un nodo central real en un puerto libre y comprueban el recorrido completo, desde el alta local hasta la recepción en otro puesto. Las de interfaz comprueban que las ventanas se construyen y que los permisos se aplican.

| Nivel | Propósito | Ejemplos de archivos |
|---|---|---|
| Unitario | Reglas y cálculos | `test_nomina_motor.py`, `test_validators.py`, `test_helpers.py` |
| Integración | Servicios y base de datos | `test_empleados.py`, `test_academico.py`, `test_pagos.py` |
| Sincronización | Journal, mezcla, servidor y agente | `test_sync_captura.py`, `test_sync_merge.py`, `test_sync_servidor.py`, `test_sync_integracion.py` |
| Interfaz | Construcción y permisos | `test_gui_smoke.py`, `test_permisos_modulos.py` |
| Seguridad | Credenciales y sesiones | `test_security.py`, `test_auth.py`, `test_tokens_sesion.py` |
| Respaldos y configuración | Integridad y migraciones | `test_backups.py`, `test_migraciones.py`, `test_configuracion.py` |

La suite comprende 32 archivos `test_*.py` y un archivo `conftest.py` que aísla el almacenamiento y la base de cada prueba. El aislamiento es una condición de confiabilidad: sin él, una prueba que crea un empleado alteraría el resultado de la siguiente.

### 4.4.2 Casos críticos

Los casos que la suite cubre con mayor detalle son los que sostienen las garantías del sistema. En nómina se verifican proporcionalidad, topes, redondeo, recargos por jornada y prestaciones. En sincronización se verifican la captura en la misma transacción, la idempotencia, la mezcla por campo, la convergencia, el conflicto en campos sensibles, la revocación de token y la recuperación tras un fallo del servidor. En seguridad se verifican la derivación de contraseñas, el bloqueo por intentos fallidos, la caducidad y el alcance del token académico.

### 4.4.3 Integración continua

El flujo de integración ejecuta la suite completa en cada push a las ramas principales y compila el ejecutable en Windows y Linux. La compilación de Linux se realiza en un contenedor Debian 13 y se autoverifica con una ejecución sin interfaz. El flujo de publicación firma los binarios y genera el instalador. La documentación se verifica con un paso que comprueba que el catálogo del portal esté sincronizado con los archivos Markdown.

Ese paso es relevante para este compendio: si un documento se modifica y no se regenera el catálogo, la integración falla. La regla evita que el portal muestre una versión anterior del texto que el lector cree estar leyendo.

### 4.4.4 Cobertura y criterio de aceptación

La cobertura se mide con `pytest --cov=src`. El criterio de aceptación del proyecto es del 80 % global y del 90 % para el dominio de nómina. La cifra de cobertura no se reporta aquí porque corresponde a una ejecución sobre la versión final y debe re-medirse antes de la presentación. Un porcentaje copiado de una versión anterior no describiría el producto que se entrega.

---

## 4.5 Ejecución del protocolo de evaluación

### 4.5.1 Condiciones de la corrida

Toda tabla de resultados debe leerse junto con las condiciones en que se obtuvo. El formato siguiente se completa antes de cada sesión y se conserva como encabezado del archivo de datos.

| Campo | Valor |
|---|---|
| Fecha y hora de la corrida | Pendiente de la Fase IV |
| Versión del sistema | 3.0.1 |
| Equipo del nodo central | Pendiente de registro |
| Equipo cliente | Pendiente de registro |
| Sistema operativo | Pendiente de registro |
| Tipo de red | LAN conmutada o Wi-Fi institucional |
| Dirección del nodo central | Pendiente de registro |
| Número de clientes concurrentes | Según matriz factorial |
| Tamaño de lote | 1, 10, 50 y 100 operaciones |
| Repeticiones por celda | 30 |
| Calentamiento | 5 repeticiones descartadas |

La ficha se completa con la especificación de hardware, porque la latencia y el consumo de recursos no son comparables entre equipos con distinta memoria o distinto procesador. Si la corrida se repite en otro equipo, se abre una ficha nueva y no se mezclan los registros.

### 4.5.2 Latencia

| ID | Condición | n | Mínimo (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Máximo (ms) | Cumple |
|---|---|---|---|---|---|---|---|---|
| LAT-01 | Ping en reposo | 300 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| LAT-02 | Push de 1 operación | 300 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| LAT-03 | Push de 10 operaciones | 300 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| LAT-04 | Push de 50 operaciones | 300 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| LAT-05 | Pull de 100 operaciones | 300 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| LAT-06 | Push con 4 clientes | 300 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| LAT-07 | Push con 8 clientes | 300 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |

El reporte incluye el coeficiente de variación de cada celda. Si supera el 20 %, la celda se repite y se informa la causa probable: interferencia en la red, proceso ajeno consumiendo recursos o calentamiento insuficiente.

### 4.5.3 Tasa de éxito ante desconexión

| Ciclo | Operaciones registradas | Confirmadas | Tasa (%) | Duplicados | Divergencias | Observaciones |
|---|---|---|---|---|---|---|
| 1 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| 2 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| 3 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| 4 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| 5 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| 6 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| 7 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| 8 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| 9 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| 10 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| **Total** | **4000** | **Pendiente** | **Pendiente** | **0 esperado** | **0 esperado** | Dos puestos por ciclo |

La tasa acumulada se calcula sobre el total y se reporta con su intervalo de confianza exacto. Un resultado de 100 % en diez ciclos con 400 operaciones por ciclo no demuestra que el sistema nunca pierda una operación; demuestra que, en esas condiciones, la pérdida observada fue cero. La distinción se explicita en las conclusiones.

### 4.5.4 Consumo de recursos

| ID | Escenario | Memoria media (MB) | Memoria máxima (MB) | CPU media (%) | CPU máxima (%) | Cumple |
|---|---|---|---|---|---|---|
| REC-01 | Reposo | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| REC-02 | Nómina de 100 trabajadores | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| REC-03 | Sincronización de 1000 operaciones | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| REC-04 | Generación de 100 PDF | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |

El consumo se registra con el monitor del sistema operativo y con una lectura por segundo. La memoria se reporta como residente, no como memoria virtual, porque la segunda incluye reservas que el proceso no utiliza.

### 4.5.5 Tiempos administrativos

| Tarea | n | Antes: media (s) | Antes: DE | Después: media (s) | Después: DE | Reducción (%) | Prueba | p | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| Registro de trabajador | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | t o Wilcoxon | Pendiente | Pendiente |
| Búsqueda de expediente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | t o Wilcoxon | Pendiente | Pendiente |
| Consolidación de boletín | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | t o Wilcoxon | Pendiente | Pendiente |
| Emisión de constancia | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | t o Wilcoxon | Pendiente | Pendiente |

La reducción porcentual se calcula como `(media_antes − media_después) / media_antes × 100`. Un valor negativo indicaría que el sistema fue más lento, y se reportaría como tal. El informe no oculta los resultados desfavorables.

### 4.5.6 Plantilla de reporte estadístico

| Elemento | Contenido requerido |
|---|---|
| Hipótesis | Código y enunciado |
| Prueba aplicada | Nombre y justificación |
| Supuestos verificados | Shapiro-Wilk y Levene, con sus valores |
| Estadístico | Valor y grados de libertad |
| Valor p | Con cuatro decimales |
| Tamaño del efecto | d de Cohen o r de Rosenthal |
| Intervalo de confianza | 95 % |
| Decisión | Aceptar o rechazar la hipótesis nula |
| Interpretación | Magnitud y relevancia práctica |

La plantilla se aplica a cada hipótesis y se reproduce en el anexo de resultados. Una tabla que solo reporte el valor p no permite juzgar la magnitud del efecto, y una que solo reporte la media no permite juzgar la incertidumbre.

### 4.5.7 Usabilidad

La puntuación SUS se calcula por participante con la regla del apartado 2.7.7.4. El resumen se presenta así:

| Participante | Perfil | Puntuación SUS | Tareas exitosas (de 6) | Tiempo total (min) | Errores |
|---|---|---|---|---|---|
| P-01 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| P-02 | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| ... | ... | ... | ... | ... | ... |
| **Media** | | **Pendiente** | **Pendiente** | **Pendiente** | **Pendiente** |
| **DE** | | **Pendiente** | | | |
| **IC 95 %** | | **Pendiente** | | | |

Para interpretar la media se utiliza la escala de calificación curva de Sauro y Lewis (2016), que traduce la puntuación a una nota comparable con una escala escolar:

| Rango SUS | Calificación | Interpretación |
|---|---|---|
| 84,1 a 100 | A+ | Excelente |
| 80,8 a 84,0 | A | Excelente |
| 71,1 a 80,7 | B | Buena |
| 65,0 a 71,0 | C | Aceptable con reservas |
| 51,7 a 64,9 | D | Baja |
| 0 a 51,6 | F | Inaceptable |

La escala se cita como referencia de interpretación y no como un estándar absoluto. Un sistema con 72 puntos es aceptable para una aplicación administrativa y puede ser insuficiente para una aplicación de uso masivo. El informe declara el contexto antes de emitir el juicio.

### 4.5.8 Amenazas a la validez

| Tipo | Amenaza | Mitigación |
|---|---|---|
| Interna | Efecto de aprendizaje entre la medición inicial y la final | Tarea de práctica y orden contrabalanceado |
| Interna | Maduración del usuario por la capacitación | Capacitación previa a ambas mediciones |
| Interna | Ausencia de grupo de control | Declaración explícita y comparación con la línea base |
| Externa | Una sola institución | Descripción detallada del contexto para permitir transferencia |
| Externa | Equipos heterogéneos | Registro de la especificación de cada equipo |
| De constructo | SUS mide percepción, no eficiencia | Complemento con tiempos y tasa de éxito por tarea |
| De conclusión | Múltiples comparaciones | Corrección de Holm |
| De fiabilidad | Variabilidad de la red | Repeticiones y reporte del coeficiente de variación |

---

## 4.6 Despliegue en la red local

### 4.6.1 Requisitos previos

| Requisito | Especificación mínima | Verificación |
|---|---|---|
| Equipo del nodo central | 4 GB de RAM, disco con 2 GB libres, conexión por cable | Comprobación del sistema |
| Equipos de los puestos | 4 GB de RAM, Windows 10 u 11, o Linux con glibc 2.41 | Comprobación del sistema |
| Red | LAN con conmutador o Wi-Fi institucional | Prueba de ping entre equipos |
| Dirección del nodo central | IP fija o reserva DHCP | Reserva en el router |
| Puerto | 8765/TCP abierto en el cortafuegos del servidor | Prueba de conexión |
| Espacio de respaldo | Dispositivo externo o carpeta de red | Verificación de escritura |

La dirección IP fija es un requisito práctico. Si el nodo central cambia de dirección, cada puesto deja de sincronizar hasta que se actualice la configuración. La reserva DHCP por dirección MAC es una alternativa aceptable y suele ser más fácil de administrar que una configuración manual.

### 4.6.2 Instalación del nodo central

Los pasos se ejecutan una sola vez, en el equipo designado.

1. Copiar la carpeta del sistema o ejecutar el instalador en el equipo central.
2. Abrir una consola en la carpeta del sistema.
3. Crear la base central y arrancar el servicio:

```bash
py -3 -m sync_agent servidor --db sqlite:///central.db --host 0.0.0.0 --puerto 8765
```

4. En otra consola, registrar cada puesto y guardar el token que se muestra:

```bash
py -3 -m sync_agent dispositivos --db sqlite:///central.db --crear "Secretaria"
py -3 -m sync_agent dispositivos --db sqlite:///central.db --crear "Direccion"
py -3 -m sync_agent dispositivos --db sqlite:///central.db --crear "Coordinacion"
```

5. Verificar el registro:

```bash
py -3 -m sync_agent dispositivos --db sqlite:///central.db --listar
```

El token se muestra una sola vez. En la base queda su hash y no existe un procedimiento para recuperarlo. Si se pierde, se revoca el dispositivo y se crea uno nuevo.

6. Programar el arranque del servicio con el Programador de tareas de Windows o con una unidad de systemd en Linux.
7. Configurar el respaldo diario de `central.db` y de la carpeta de binarios.

### 4.6.3 Instalación en los puestos

1. Ejecutar el instalador de Windows o descomprimir la versión portable de Linux.
2. Iniciar la aplicación con una cuenta de administrador.
3. Abrir `Configuración` y luego `Sincronización`.
4. Introducir la dirección del nodo central, el token y el identificador del equipo.
5. Marcar la casilla de sincronización y guardar.
6. Pulsar `Probar conexión` y verificar la respuesta.
7. Pulsar `Adoptar datos existentes` si el puesto ya tenía información cargada antes de la sincronización.
8. Ejecutar `Sincronizar ahora` y comprobar que el contador de pendientes llega a cero.

La adopción de datos existentes es idempotente. Otorga identidad global a las filas que ya estaban en la base y las pone en circulación sin modificar su contenido. Ejecutarla dos veces no duplica registros.

### 4.6.4 Configuración por variables de entorno

Para un despliegue automatizado se pueden usar las variables siguientes en lugar de la pantalla de configuración:

```bash
set SDP_SYNC_ACTIVADO=true
set SDP_SYNC_URL=http://servidor-central:8765
set SDP_SYNC_TOKEN=<token-entregado-por-el-administrador>
set SDP_SYNC_EQUIPO=Secretaria
py -3 -m sync_agent init
py -3 -m sync_agent agente
```

El token no debe quedar escrito en un archivo versionado ni en una captura de pantalla. La configuración por variables se recomienda para el despliegue inicial y no para la operación diaria.

### 4.6.5 TLS y cortafuegos

Sin TLS, el token viaja en claro por la intranet. En una red cableada con acceso restringido el riesgo es acotado, pero no nulo: cualquier equipo conectado al mismo conmutador podría capturar el tráfico. Si la institución dispone de un certificado, el nodo central se inicia con las opciones correspondientes:

```bash
py -3 -m sync_agent servidor --db sqlite:///central.db --host 0.0.0.0 --puerto 8765 --cert servidor.pem --key servidor.key
```

El certificado debe incluir el nombre o la dirección que los puestos utilizan para conectarse. Un certificado emitido para un nombre distinto provoca un error de validación que el agente reporta como fallo de conexión.

### 4.6.6 Respaldo y restauración

El respaldo del nodo central comprende dos elementos: el archivo `central.db` y la carpeta de binarios. El primero contiene las operaciones y las filas; la segunda, los documentos y fotografías deduplicados por hash. Un respaldo que incluya solo la base deja los documentos sin contenido.

| Actividad | Frecuencia | Procedimiento | Verificación |
|---|---|---|---|
| Respaldo automático del puesto | Diario | Copia comprimida de la base local | Apertura del archivo y consulta de conteo |
| Respaldo del nodo central | Diario | Copia de `central.db` y de la carpeta de binarios | Restauración en un equipo de prueba |
| Respaldo externo | Semanal | Copia a un dispositivo extraíble | Verificación de integridad |
| Prueba de restauración | Mensual | Restauración completa en un equipo aislado | Comparación de conteos y de totales |

La prueba de restauración es la parte que suele omitirse y la que determina si el respaldo sirve. Un archivo que se copia todos los días pero nunca se restaura es una promesa, no una garantía.

### 4.6.7 Actualización y reversión

La actualización se realiza con el instalador de la nueva versión. Antes de instalarla se ejecuta un respaldo verificado y se comprueba que la versión de destino sea compatible con el esquema. Si la migración falla, el sistema se detiene y muestra la versión de origen y la de destino; en ese caso se restaura el respaldo y se conserva el archivo dañado para diagnóstico.

La reversión a una versión anterior solo es segura si la migración no agregó columnas que la versión anterior no conoce. Esa condición se verifica en el laboratorio antes de desplegar y se documenta en la nota de la versión.

### 4.6.8 Lista de verificación del despliegue

- [ ] El nodo central responde en `/api/v1/ping` desde otro equipo.
- [ ] Cada puesto tiene un token propio y un identificador distinto.
- [ ] La prueba de conexión es exitosa en todos los puestos.
- [ ] La adopción de datos existentes se ejecutó donde correspondía.
- [ ] El contador de pendientes llega a cero tras la primera sincronización.
- [ ] Se creó un trabajador en un puesto y se verificó su aparición en otro.
- [ ] Se registró una nota en un puesto y se verificó su aparición en otro.
- [ ] Se generó una constancia y se verificó el PDF.
- [ ] Se ejecutó un respaldo y se restauró en un equipo de prueba.
- [ ] Se revocó un token de prueba y se confirmó que el puesto dejó de sincronizar.
- [ ] El puerto 8765 está cerrado hacia fuera de la red local.
- [ ] La capacitación se realizó con los perfiles que operarán el sistema.

---

## 4.7 Operación y mantenimiento

### 4.7.1 Rutina diaria

La rutina diaria comprende tres verificaciones. La primera es el estado de sincronización de cada puesto: el indicador debe mostrar el último ciclo exitoso y un número de pendientes bajo. La segunda es el estado del respaldo: el archivo del día debe existir y tener un tamaño coherente. La tercera es la revisión de la bandeja de conflictos, que debe quedar vacía o con casos justificados.

### 4.7.2 Rutina semanal

La rutina semanal comprende la revisión de documentos próximos a vencer, la verificación de contratos por vencer y la comprobación de que los usuarios activos correspondan al personal vigente. Esa última verificación es una medida de seguridad: una cuenta de un trabajador que ya no labora en la institución debe desactivarse, no solo bloquearse.

### 4.7.3 Rutina mensual

La rutina mensual comprende la prueba de restauración, la revisión de la bitácora del nodo central y la purga de historial de sincronización con una retención declarada. La purga no elimina las filas de dominio: elimina las operaciones antiguas que ya fueron aplicadas y que solo ocupan espacio.

### 4.7.4 Catálogo de incidentes

| Síntoma | Causa probable | Acción |
|---|---|---|
| El puesto indica «sin conexión» | Servicio detenido o puerto bloqueado | Verificar el servicio y el cortafuegos |
| El puesto indica error de token | Token revocado o mal copiado | Solicitar un token nuevo al administrador |
| Los pendientes no bajan | Operación huérfana o conflicto | Revisar el estado del agente y la bandeja de conflictos |
| El nodo central no inicia | Puerto ocupado o base bloqueada | Cambiar el puerto o cerrar el proceso anterior |
| Un documento no se genera | Datos obligatorios incompletos | Completar la ficha y reintentar |
| La nómina muestra una deducción inesperada | Parámetro mal configurado | Revisar la configuración y recalcular |
| El rendimiento decae | Base crecida sin mantenimiento | Ejecutar compactación y purgar historial |

### 4.7.5 Actualización automática

El instalador incluye un actualizador que comprueba la existencia de una versión nueva cada dos días y la instala en silencio. El actualizador muestra una ventana de estado, registra el resultado y permite buscar actualizaciones de forma manual. La actualización automática no debe confundirse con la sincronización: la primera actualiza el programa, la segunda replica los datos.

La institución puede desactivar la actualización automática si su política de cambios exige validar cada versión. En ese caso, la actualización se realiza con el instalador y con el procedimiento del apartado 4.6.7.

---

## 4.8 Limitaciones y riesgos de la implementación

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Corte de energía durante una escritura | Media | Alto | Transacción por operación, WAL en el nodo central y respaldo diario |
| Token comprometido | Baja | Alto | Revocación inmediata, TLS recomendado, límite de peticiones |
| Reloj desfasado entre puestos | Media | Medio | Tolerancia de 2 s y desempate por dispositivo |
| Base central corrupta | Baja | Alto | Respaldo verificado y prueba de restauración mensual |
| Usuario sin capacitación | Media | Medio | Dos sesiones por perfil y guía escrita |
| Cambio de dirección del nodo central | Media | Medio | IP fija o reserva DHCP documentada |
| Crecimiento del journal | Baja | Medio | Purga con retención declarada |
| Dependencia de una sola persona | Media | Alto | Documentación técnica y guía de operación |

El riesgo de dependencia de una sola persona es el más subestimado. Un sistema técnicamente sólido que solo su desarrollador sabe operar deja a la institución en una posición vulnerable. La documentación y la capacitación no son anexos del proyecto: son parte de su viabilidad.

---

## 4.9 Conclusiones del capítulo

La implementación se organizó en siete iteraciones y produjo un producto instalable, con una suite de pruebas que cubre los dominios críticos y un flujo de integración que compila y verifica en dos plataformas. La separación entre la aplicación y el agente de sincronización permitió probar el motor de mezcla de forma aislada y mantener la aplicación utilizable cuando la sincronización se desactiva.

El despliegue se documentó con pasos verificables, comandos concretos y una lista de comprobación. Esa documentación es la que permite que la institución opere el sistema sin depender del autor y la que permite que un evaluador reproduzca la instalación.

Las tablas de resultados quedaron preparadas con sus condiciones, fórmulas y criterios de aceptación. La Fase IV las completará con las mediciones de la red y de los usuarios. Hasta entonces, el documento afirma lo que puede sostenerse: el sistema existe, está probado en sus reglas y está listo para medirse. La evaluación dirá si esas reglas se traducen en la mejora operativa que el objetivo general promete.
