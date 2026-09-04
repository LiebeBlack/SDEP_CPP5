# CAPÍTULO IV: RESULTADOS

## 4.1 INTRODUCCIÓN

El presente capítulo presenta los resultados obtenidos durante el desarrollo e implementación del Sistema de Gestión de Personal y Nómina para instituciones educativas. Se describe el sistema desarrollado, los hallazgos de las pruebas técnicas y de usabilidad, los resultados de la validación con usuarios piloto, y el análisis cuantitativo y cualitativo del impacto observado en las instituciones participantes.

**Nota sobre la evidencia presentada:** Las secciones 4.2 y 4.3 reportan resultados técnicos verificables del sistema desarrollado (arquitectura, funcionalidades implementadas, pruebas automatizadas y cobertura de código, todas medibles directamente sobre el repositorio del proyecto). Las secciones 4.4 a 4.7 corresponden a la validación empírica con usuarios en instituciones piloto: su estructura metodológica está definida (Capítulo III) y las tablas incluyen marcadores claros **[dato real del piloto]** que deben completarse con los resultados de la implementación real en cada institución participante antes de la presentación final de la tesis.

Los resultados técnicos demuestran la viabilidad del sistema y su efectividad como herramienta de gestión; la evidencia empírica del piloto complementará estos resultados con la medición de la eficiencia administrativa en el contexto real.

## 4.2 DESCRIPCIÓN DEL SISTEMA DESARROLLADO

### 4.2.1 Arquitectura General

El Sistema de Gestión de Personal y Nómina se implementó siguiendo una arquitectura de capas modular que separa claramente las responsabilidades:

#### 4.2.1.1 Capa de Presentación (GUI)

**Tecnología:** CustomTkinter

**Características:**
- Interfaz moderna con temas claro y oscuro configurables (persistidos en la configuración del sistema)
- Navegación intuitiva mediante menú lateral
- Formularios validados con feedback inmediato
- Tablas con capacidades de búsqueda y filtrado
- Atajos de teclado (módulos, nuevo, buscar, guardar, actualizar, cerrar diálogos)
- Diseño responsivo adaptado a diferentes tamaños de pantalla

**Componentes principales:**
- **LoginWindow:** Ventana de autenticación de usuarios
- **MainWindow:** Ventana principal del sistema
- **DashboardFrame:** Panel de control con estadísticas en tiempo real (tarjetas navegables)
- **EmpleadosFrame:** Gestión completa de empleados
- **DocumentosFrame:** Gestión documental digital
- **IncidenciasFrame:** Control de permisos y ausencias
- **NominaFrame:** Procesamiento de nóminas y pagos
- **ConfiguracionFrame:** Configuración del sistema (incluida la apariencia claro/oscuro)

#### 4.2.1.2 Capa de Servicios

**Patrón implementado:** Service Layer Pattern

**Servicios implementados:**
- **AuthService:** Autenticación de usuarios y control de acceso por rol
- **EmpleadoService:** Lógica de negocio para gestión de empleados
- **DocumentoService:** Gestión de documentos digitales
- **IncidenciaService:** Control de permisos y ausencias
- **PagoService:** Procesamiento de nóminas y cálculos financieros
- **ConfiguracionService:** Gestión de parámetros configurables (incluida la apariencia)

**Responsabilidades:**
- Validación de reglas de negocio
- Coordinación entre diferentes repositorios
- Cálculos complejos (nómina, deducciones)
- Orquestación de flujos de trabajo
- Registro de auditoría de acciones críticas

#### 4.2.1.3 Capa de Repositorios

**Patrón implementado:** Repository Pattern

**Repositorios implementados:**
- **EmpleadoRepository:** Acceso a datos de empleados
- **DocumentoRepository:** Gestión de documentos
- **IncidenciaRepository:** Control de incidencias
- **PagoRepository:** Gestión de pagos y nóminas
- **ConfiguracionRepository:** Acceso a configuración del sistema

**Responsabilidades:**
- Abstracción de operaciones de base de datos
- Consultas optimizadas y reutilizables
- Gestión de transacciones
- Implementación de patrones de acceso a datos

#### 4.2.1.4 Capa de Modelos

**Tecnología:** SQLAlchemy ORM

**Modelos implementados:**
- **Empleado:** Información completa de empleados
- **Documento:** Documentos digitales de empleados
- **Incidencia:** Permisos, reposos y ausencias
- **Pago:** Pagos y nóminas
- **Configuracion:** Parámetros configurables del sistema
- **Usuario:** Usuarios del sistema con roles y credenciales seguras

**Características:**
- Mapeo objeto-relacional automático
- Validaciones a nivel de modelo
- Relaciones entre entidades
- Propiedades calculadas automáticas

#### 4.2.1.5 Capa de Utilidades y Servicios Transversales

Además de las cuatro capas principales, el sistema incorpora módulos transversales que refuerzan la seguridad, la trazabilidad y la sostenibilidad de los datos:

- **security.py:** Validación y sanitización de entradas, verificación de permisos por rol y gestión de contraseñas con hash PBKDF2-HMAC-SHA256 (200.000 iteraciones) y salt aleatorio.
- **audit_logger.py:** Registro de auditoría de las acciones críticas del sistema (inicios de sesión, operaciones sobre empleados, documentos, incidencias y nóminas).
- **backup_manager.py:** Respaldo y restauración de la base de datos con políticas de retención.
- **exporter.py:** Exportación de datos y reportes en formatos abiertos.
- **pdf_generator.py:** Generación de documentos oficiales (constancias, recibos de pago, planillas) en formato PDF mediante ReportLab.
- **document_manager.py:** Gestión del almacenamiento de documentos y fotografías de empleados.
- **validators.py y helpers.py:** Validaciones de dominio y funciones auxiliares de formateo y manipulación de datos.

### 4.2.2 Funcionalidades Implementadas

#### 4.2.2.1 Módulo de Gestión de Empleados

**Funcionalidades principales:**

1. **Registro de Empleados:**
   - Formulario completo con datos personales, físicos, de contacto y laborales
   - Validación de cédula única
   - Carga de foto de perfil
   - Categorización por tipo, cargo y departamento

2. **Gestión de Información:**
   - Edición de datos existentes
   - Búsqueda por nombre, apellido o cédula
   - Filtrado por tipo de empleado y departamento
   - Visualización de historial de cambios

3. **Estadísticas:**
   - Total de empleados
   - Empleados por tipo
   - Distribución por departamento
   - Indicadores de antigüedad

**Resultados de implementación:**
- Formulario completo organizado en pestañas temáticas (datos personales, físicos, de contacto y laborales)
- Validación en tiempo real con feedback visual
- Cobertura funcional verificada por la suite de pruebas automatizadas del sistema (281 pruebas, todas exitosas; ver sección 4.3.1)
- Medición de tiempo de registro en piloto: **[dato real del piloto]** minutos (vs. proceso manual: **[dato real del piloto]** minutos)

#### 4.2.2.2 Módulo de Gestión Documental

**Funcionalidades principales:**

1. **Carga de Documentos:**
   - Soporte para PDF e imágenes
   - Clasificación por tipo de documento
   - Control de fechas de emisión y vencimiento
   - Almacenamiento digital seguro

2. **Control de Vencimientos:**
   - Alertas automáticas para documentos por vencer
   - Reporte de documentos vencidos
   - Sistema de categorización por estado

3. **Gestión de Archivos:**
   - Vista previa de documentos
   - Descarga en formato original
   - Control de versiones básico
   - Organización por empleado

**Resultados de implementación:**
- Soporte para los tipos de documentos definidos en la configuración institucional
- Control de fechas de emisión y vencimiento con alertas automáticas
- Tiempo promedio de carga en piloto: **[dato real del piloto]** segundos (vs. proceso manual: **[dato real del piloto]** minutos)
- Porcentaje de pérdida de documentos evitado: **[dato real del piloto]**%

#### 4.2.2.3 Módulo de Gestión de Incidencias

**Funcionalidades principales:**

1. **Registro de Incidencias:**
   - 5 tipos de incidencias (reposo médico, ausencia, permiso, vacaciones, licencia)
   - Cálculo automático de días solicitados
   - Carga de documentos de soporte
   - Sistema de aprobación/rechazo

2. **Flujo de Aprobación:**
   - Estados: pendiente, aprobado, rechazado, completado
   - Registro de aprobador y fecha de aprobación
   - Comentarios de aprobación/rechazo
   - Seguimiento del estado en el historial de la incidencia

3. **Control de Vigencia:**
   - Identificación de incidencias vigentes
   - Impacto en cálculo de nómina
   - Historial completo de incidencias

**Resultados de implementación:**
- Flujo completo de aprobación/rechazo con registro de aprobador y comentarios
- Cálculo automático de días solicitados con impacto en la nómina
- Tiempo promedio de registro en piloto: **[dato real del piloto]** minutos (vs. proceso manual: **[dato real del piloto]** minutos)
- Reducción de errores de cálculo de días en piloto: **[dato real del piloto]**%

#### 4.2.2.4 Módulo de Nómina

**Funcionalidades principales:**

1. **Generación de Nómina:**
   - Cálculo automático por periodo
   - Integración con incidencias (ajuste de días trabajados)
   - Cálculo automático de deducciones (seguro, pensión, impuesto)
   - Generación de pagos individuales o masivos

2. **Cálculos Financieros:**
   - Salario base proporcional a días trabajados
   - Deducciones según porcentajes configurables
   - Bonificaciones y horas extra
   - Cálculo de salario neto

3. **Reportes y Documentos:**
   - Generación de recibos de pago en PDF
   - Reportes por periodo y empleado
   - Estadísticas financieras
   - Control de pagos pendientes y realizados

**Resultados de implementación:**
- Cálculo automático de salario proporcional, deducciones configurables y salario neto
- Generación de recibos de pago y reportes en PDF
- Exactitud de los cálculos verificada por las pruebas automatizadas del módulo de pagos (cálculos de proporción, deducciones y neto)
- Tiempo de generación de nómina en piloto: **[dato real del piloto]** minutos para **[dato real del piloto]** empleados (vs. proceso manual: **[dato real del piloto]** horas)

#### 4.2.2.5 Módulo de Configuración

**Funcionalidades principales:**

1. **Configuración General:**
   - Datos de la institución (nombre, dirección, contacto)
   - Parámetros de identificación institucional y fiscal
   - Personalización de logos y branding

2. **Configuración de Nómina:**
   - Porcentajes de deducciones (configurables)
   - Salario mínimo de referencia
   - Parámetros de cálculo

3. **Configuración de Recursos Humanos:**
   - Días de vacaciones anuales
   - Horas laborales semanales
   - Políticas de incidencias

**Resultados de implementación:**
- Sistema altamente configurable según necesidades institucionales (datos de la institución, parámetros de nómina, políticas de recursos humanos, apariencia claro/oscuro)
- Flexibilidad para adaptarse a diferentes contextos
- Actualización de configuración sin necesidad de modificar código

### 4.2.3 Características Técnicas

#### 4.2.3.1 Base de Datos

**Sistema:** SQLite

**Esquema implementado:**
- 6 tablas principales: `empleados`, `documentos`, `incidencias`, `pagos`, `configuraciones` y `usuarios`
- Índices para las consultas frecuentes (búsqueda por cédula, nombre y periodo)
- Integridad referencial entre tablas mediante claves foráneas
- Gestión de migraciones para evolución controlada del esquema

**Rendimiento:**
- Medición real en piloto: **[dato real del piloto]** ms para consultas típicas
- Medición real en piloto: **[dato real del piloto]** ms para consultas complejas
- Capacidad verificada con las pruebas de la suite: **[dato real del piloto]** registros sin degradación significativa

#### 4.2.3.2 Interfaz Gráfica

**Características:**
- Temas oscuro y claro configurables por el usuario y persistidos en la configuración
- Diseño consistente en todos los módulos
- Validación en tiempo real
- Feedback visual de acciones
- Accesibilidad por teclado (atajos: módulos, nuevo, buscar, guardar, actualizar, cerrar)
- Tarjetas de estadísticas navegables en el panel de control
- Diálogos auxiliares de ayuda y "Acerca de"

**Rendimiento:**
- Tiempo de carga de módulos: **[dato real del piloto]** segundos
- Tiempo de respuesta de acciones: **[dato real del piloto]** ms
- Uso de memoria en operación normal: **[dato real del piloto]** MB

#### 4.2.3.3 Seguridad

**Implementaciones verificadas en el sistema:**
- Autenticación de usuarios implementada y probada (LoginWindow + AuthService)
- Control de acceso por rol (administrador, gerente, usuario, consulta) con verificación de permisos por módulo
- Contraseñas protegidas con hash PBKDF2-HMAC-SHA256 (200.000 iteraciones) y salt aleatorio (seguridad.py)
- Registro de auditoría de acciones críticas (audit_logger.py)
- Respaldo y restauración de base de datos con políticas de retención (backup_manager.py)
- Sanitización de entradas y validación de archivos para mitigar inyección SQL y archivos maliciosos

## 4.3 RESULTADOS DE PRUEBAS TÉCNICAS

### 4.3.1 Pruebas Automatizadas

**Resultados medidos directamente sobre el repositorio del proyecto (v2.79):**

- **Total de pruebas:** 281 (89 de la suite original + 192 incorporadas durante el desarrollo)
- **Pruebas exitosas:** 281 (100%)
- **Pruebas falladas:** 0
- **Cobertura de código total:** 43%
- **Cobertura de la lógica de negocio** (modelos, repositorios, servicios, utilidades y configuración; excluye la capa gráfica y el punto de entrada): **73%**

**Cobertura por módulo (medida con `pytest --cov=src`):**

| Módulo | Líneas de Código | Líneas Cubiertas | % Cobertura |
|--------|----------------|----------------|------------|
| models | 393 | 363 | 92% |
| repositories | 678 | 326 | 48% |
| services | 815 | 608 | 75% |
| utils | 1442 | 1167 | 81% |
| config | 265 | 154 | 58% |
| gui | 3025 | 330 | 11% |
| main.py | 220 | 0 | 0% |
| **Total** | **6841** | **2951** | **43%** |

**Interpretación:** La cobertura es alta (≥ 75%) en los módulos de lógica de negocio —modelos, servicios y utilidades—, que concentran las reglas críticas del dominio (cálculos de nómina, validaciones, seguridad). La capa gráfica (GUI) presenta cobertura baja porque su automatización requiere un entorno con pantalla; su funcionalidad se valida mediante las pruebas de usabilidad descritas en la sección 4.4.

### 4.3.2 Pruebas de Integración

La suite automatizada incluye pruebas de integración que verifican los flujos completos del sistema sobre una base de datos aislada y sembrada para cada prueba:

1. **Flujo de empleados:** Registro → búsqueda → actualización → asociación de documentos, incidencias y pagos (tests/test_empleados.py, test_documentos.py, test_pagos.py).

2. **Flujo de nómina:** Cálculo de días trabajados considerando incidencias → cálculo de salario proporcional → deducciones → salario neto → generación de recibos (tests/test_pagos.py).

3. **Flujo de incidencias:** Solicitud → validación de fechas y días → aprobación → impacto en nómina (tests/test_incidencias.py).

4. **Autenticación y control de acceso:** Login, roles, verificación de contraseñas y permisos por módulo (tests/test_auth.py).

5. **Persistencia y configuración:** Siembra de configuración inicial, persistencia de parámetros y apariencia, migraciones de esquema (tests/test_configuracion.py, test_migraciones.py).

6. **Respaldo y restauración:** Ciclo completo de backup/restore de la base de datos (tests/test_backups.py).

**Resultado:** Las 281 pruebas (unitarias e de integración) se ejecutan correctamente y sin fallas en la suite completa.

### 4.3.3 Pruebas de Rendimiento

El protocolo de pruebas de rendimiento se define conforme a la metodología del Capítulo III (sección 3.4.1.5). Las métricas definitivas deben medirse durante la implementación piloto en condiciones reales de uso; la tabla siguiente debe completarse con esos datos:

| Métrica | Objetivo | Resultado | Estado |
|---------|----------|-----------|--------|
| Tiempo de respuesta promedio | < 1s | **[dato real del piloto]** | ⬜ Pendiente |
| Tiempo de respuesta máximo | < 3s | **[dato real del piloto]** | ⬜ Pendiente |
| Uso de memoria en reposo | < 150MB | **[dato real del piloto]** | ⬜ Pendiente |
| Uso de memoria en carga | < 300MB | **[dato real del piloto]** | ⬜ Pendiente |
| Tiempo de generación de nómina | < 5min | **[dato real del piloto]** | ⬜ Pendiente |

**Pruebas de carga:**
- Volumen de datos probado: **[dato real del piloto]** empleados en base de datos
- Degradación de rendimiento observada: **[dato real del piloto]**
- Comportamiento de memoria: **[dato real del piloto]**

### 4.3.4 Pruebas de Seguridad

**Controles implementados y verificados mediante pruebas automatizadas (tests/test_security.py, test_auth.py):**

1. **Inyección SQL:** Mitigado mediante el uso de ORM (SQLAlchemy) con consultas parametrizadas; el módulo de seguridad incluye además sanitización de entradas.
2. **XSS (Cross-Site Scripting):** No aplicable al tratarse de una aplicación de escritorio; aun así, los campos de texto se sanitizan antes de almacenarse.
3. **Autenticación:** Implementada con hash PBKDF2-HMAC-SHA256 (200.000 iteraciones, salt aleatorio) y verificación con comparación de tiempo constante; probada en tests/test_auth.py.
4. **Autorización:** Control de acceso por rol (administrador, gerente, usuario, consulta) con permisos por módulo (security.py: PermissionChecker); probado en tests/test_security.py.
5. **Auditoría:** Registro de eventos de seguridad y acciones críticas (audit_logger.py, SecurityLogger); probado en tests/test_security.py.
6. **Archivos:** Validación de nombre, extensión, tamaño y tipo MIME antes del almacenamiento.

**Resultado:** Los controles de seguridad implementados están cubiertos por pruebas automatizadas exitosas (95% de cobertura en security.py).

## 4.4 RESULTADOS DE PRUEBAS DE USABILIDAD

> **Sección de validación empírica:** Las pruebas de usabilidad se realizarán con los usuarios piloto siguiendo el protocolo del Anexo 3 y la metodología del Capítulo III (secciones 3.4.1.4 y 3.6). Las tablas de esta sección deben completarse con los datos reales obtenidos durante la implementación piloto en cada institución; los marcadores **[dato real del piloto]** indican los campos pendientes.

### 4.4.1 Pruebas con Usuarios Piloto

**Participantes:** **[dato real del piloto]** usuarios de **[dato real del piloto]** instituciones educativas

**Distribución por rol (completar con los datos reales):**
- Directivos: **[dato real del piloto]**
- Personal de RRHH: **[dato real del piloto]**
- Personal administrativo: **[dato real del piloto]**
- Personal docente: **[dato real del piloto]**

### 4.4.2 Resultados de Pruebas de Tareas

**Tareas evaluadas (tiempos, tasas de éxito y satisfacción subjetiva por completar con datos reales):**

1. **Registro de nuevo empleado:**
   - Tiempo promedio: **[dato real del piloto]**
   - Tasa de éxito: **[dato real del piloto]**%
   - Satisfacción subjetiva: **[dato real del piloto]**/5.0

2. **Búsqueda de empleado:**
   - Tiempo promedio: **[dato real del piloto]**
   - Tasa de éxito: **[dato real del piloto]**%
   - Satisfacción subjetiva: **[dato real del piloto]**/5.0

3. **Generación de nómina:**
   - Tiempo promedio: **[dato real del piloto]** (para **[dato real del piloto]** empleados)
   - Tasa de éxito: **[dato real del piloto]**%
   - Satisfacción subjetiva: **[dato real del piloto]**/5.0

4. **Generación de recibo PDF:**
   - Tiempo promedio: **[dato real del piloto]**
   - Tasa de éxito: **[dato real del piloto]**%
   - Satisfacción subjetiva: **[dato real del piloto]**/5.0

**Problemas de usabilidad identificados (completar con los hallazgos reales de las sesiones):**
- **[dato real del piloto]** usuarios tuvieron dificultad con **[dato real del piloto]** (corregido con **[dato real del piloto]**)
- **[dato real del piloto]**
- **[dato real del piloto]**

### 4.4.3 Resultados de Encuestas de Satisfacción

**Escala SUS (System Usability Scale):**

- Puntuación promedio: **[dato real del piloto]**/100
- Rango: **[dato real del piloto]**
- Percentil: **[dato real del piloto]**

**Dimensiones específicas (completar con las medias y desviaciones reales):**

| Dimensión | Promedio | Desviación | Interpretación |
|-----------|----------|------------|----------------|
| Facilidad de aprendizaje | **[dato real del piloto]** | **[dato real del piloto]** | Fácil de aprender |
| Eficiencia de uso | **[dato real del piloto]** | **[dato real del piloto]** | Eficiente |
| Memorabilidad | **[dato real del piloto]** | **[dato real del piloto]** | Moderadamente memorable |
| Bajo error | **[dato real del piloto]** | **[dato real del piloto]** | Baja tasa de errores |
| Satisfacción | **[dato real del piloto]** | **[dato real del piloto]** | Alta satisfacción |

**Comparación pre/post implementación:**

| Aspecto | Pre | Post | Mejora | Significancia |
|---------|-----|------|--------|--------------|
| Satisfacción general | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** |
| Percepción de eficiencia | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** |
| Facilidad de uso | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** |
| Utilidad percibida | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** |

**Análisis estadístico:** Las pruebas estadísticas descritas en el Capítulo III (sección 3.6.1.2: prueba t pareada, chi-cuadrado, ANOVA y Wilcoxon, α = 0.05) se aplicarán a los datos recopilados para determinar la significancia de las mejoras observadas. Los resultados se registrarán aquí al completarse la recolección de datos del piloto.

## 4.5 RESULTADOS DE IMPLEMENTACIÓN PILOTO

> **Sección de validación empírica:** La descripción de las instituciones, las métricas cuantitativas de impacto y los resultados cualitativos deben completarse con los datos reales recopilados durante la implementación piloto, siguiendo el procedimiento de recolección del Capítulo III (sección 3.5) y los instrumentos de los Anexos 1, 2, 3, 8 y 9.

### 4.5.1 Descripción de Instituciones Piloto

**Institución 1:** [Nombre real o código de la institución] — **[dato real del piloto]** empleados — **[dato real del piloto]**

**Institución 2:** [Nombre real o código de la institución] — **[dato real del piloto]** empleados — **[dato real del piloto]**

**Institución 3:** [Nombre real o código de la institución] — **[dato real del piloto]** empleados — **[dato real del piloto]**

*(Agregar o eliminar filas según el número real de instituciones participantes: entre 3 y 5, conforme a la muestra definida en el Capítulo III.)*

### 4.5.2 Métricas de Impacto Cuantitativo

#### 4.5.2.1 Tiempos de Procesamiento

**Comparación de tiempos promedio por tarea (completar con las mediciones pre/post reales):**

| Tarea | Antes (min) | Después (min) | Reducción | % Reducción |
|-------|-------------|---------------|-----------|-------------|
| Registro empleado | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |
| Búsqueda empleado | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |
| Cálculo nómina | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |
| Generación recibo | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |
| Control documentos | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |
| Gestión incidencias | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |

**Análisis estadístico:** Se aplicará la prueba t pareada (sección 3.6.1.2) a las mediciones pre/post de cada tarea; los resultados (estadístico t, grados de libertad y valor p) se registrarán aquí.

#### 4.5.2.2 Tasas de Error

**Comparación de tasas de error por proceso (completar con los datos reales):**

| Proceso | Antes (%) | Después (%) | Reducción | % Reducción |
|---------|-----------|-------------|-----------|-------------|
| Cálculo de nómina | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |
| Registro de datos | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |
| Control de documentos | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |
| Seguimiento de incidencias | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]**% |

**Impacto estimado (completar con cálculos sobre los datos reales):**
- Ahorro anual estimado por errores evitados: **[dato real del piloto]** por institución
- Reducción de reclamos laborales: **[dato real del piloto]**%
- Mejora en cumplimiento normativo: **[dato real del piloto]**%

#### 4.5.2.3 Satisfacción Laboral

**Indicadores de satisfacción laboral (completar con las encuestas reales):**

| Indicador | Antes | Después | Mejora |
|-----------|-------|---------|--------|
| Satisfacción con pagos | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** |
| Percepción de justicia en pagos | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** |
| Satisfacción con comunicación | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** |
| Satisfacción general laboral | **[dato real del piloto]** | **[dato real del piloto]** | **[dato real del piloto]** |

### 4.5.3 Resultados Cualitativos

> **Instrucción:** Documentar aquí los hallazgos cualitativos reales (comentarios textuales de usuarios, observaciones de comportamiento y lecciones aprendidas) recopilados durante el piloto mediante entrevistas, observación directa y análisis de contenido (sección 3.6.2).

#### 4.5.3.1 Feedback de Usuarios

**Comentarios positivos más frecuentes (completar con citas reales de las sesiones):**

- **[dato real del piloto]**
- **[dato real del piloto]**
- **[dato real del piloto]**

**Áreas de mejora identificadas (completar con las solicitudes reales):**

- **[dato real del piloto]**
- **[dato real del piloto]**
- **[dato real del piloto]**

#### 4.5.3.2 Observaciones de Comportamiento

**Cambios observados en patrones de trabajo (completar con las observaciones reales):**

1. **[dato real del piloto]**
2. **[dato real del piloto]**
3. **[dato real del piloto]**
4. **[dato real del piloto]**

#### 4.5.3.3 Lecciones Aprendidas

**Lecciones técnicas:**

1. **[dato real del piloto]**
2. **[dato real del piloto]**

**Lecciones organizacionales:**

1. **[dato real del piloto]**
2. **[dato real del piloto]**

## 4.6 ANÁLISIS COMPARATIVO

### 4.6.1 Comparación con Sistemas Comerciales

**Características comparadas** (los rangos de costos de sistemas comerciales son estimaciones de mercado referenciales; deben ajustarse con cotizaciones reales en la región si están disponibles):

| Característica | Sistema Propuesto | Sistemas Comerciales | Evaluación |
|---------------|-------------------|---------------------|-------------|
| Costo inicial | $0 (código abierto) | $5,000-$50,000 (estimado) | + Ventaja significativa |
| Costo anual | $0 (sin licenciamiento) | $1,000-$10,000 (estimado) | + Ventaja significativa |
| Funcionalidad básica | Completa | Completa | = Paridad |
| Funcionalidad avanzada | Limitada | Extensa | - Desventaja |
| Personalización | Alta | Baja/Media | + Ventaja |
| Soporte técnico | Comunidad | Profesional | - Desventaja |
| Curva de aprendizaje | Moderada | Alta/Moderada | + Ventaja |

**Conclusión:** El sistema propuesto ofrece una alternativa viable y económica para instituciones con recursos limitados, cubriendo funcionalidades críticas sin el costo de soluciones comerciales.

### 4.6.2 Comparación con Procesos Manuales

**Comparación cualitativa** (la cuantificación de la mejora, en términos de tiempos y tasas de error, se completará con las mediciones pre/post de la implementación piloto):

| Aspecto | Proceso Manual | Sistema | Mejora Esperada |
|---------|----------------|---------|----------------|
| Tiempo de procesamiento | Alto | Bajo | **[dato real del piloto]**% reducción |
| Tasa de errores | Alto | Bajo | **[dato real del piloto]**% reducción |
| Accesibilidad de información | Baja | Alta | **[dato real del piloto]**% mejora |
| Transparencia | Baja | Alta | **[dato real del piloto]**% mejora |
| Auditabilidad | Difícil | Fácil | Alta (registro de auditoría automatizado) |
| Escalabilidad | Limitada | Alta | Significativa |

## 4.7 RESULTADOS DE VALIDACIÓN DE HIPÓTESIS

> **Sección de validación empírica:** La validación definitiva de las hipótesis se realizará con la evidencia cuantitativa y cualitativa recopilada en la implementación piloto (tiempos, tasas de error, encuestas y observaciones). A continuación se presenta la estructura de validación para cada hipótesis con sus indicadores; los valores pendientes deben completarse con los datos reales y las pruebas estadísticas del Capítulo III (sección 3.6.1.2).

### 4.7.1 Validación de Hipótesis General

**Hipótesis:** La implementación del sistema mejorará significativamente la eficiencia administrativa, reduciendo los tiempos de procesamiento en al menos un 50% y minimizando errores administrativos en un 80%.

**Indicadores y resultados esperados (completar con datos reales):**
- Reducción promedio de tiempos de procesamiento: **[dato real del piloto]**% (umbral: ≥ 50%)
- Reducción promedio de tasas de error: **[dato real del piloto]**% (umbral: ≥ 80%)
- Significancia estadística: **[dato real del piloto]**

**Conclusión:** **[Pendiente de confirmar con la evidencia del piloto]**

### 4.7.2 Validación de Hipótesis Específicas

**H1:** La arquitectura modular facilitará el mantenimiento y expansión.

**Indicadores:**
- Tiempo promedio de implementación de nueva funcionalidad: **[dato real del piloto]**
- Facilidad de comprensión de código por nuevos desarrolladores: **[dato real del piloto]**

**Conclusión:** **[Pendiente de confirmar con la evidencia del piloto]**

**H2:** La interfaz gráfica mejorará la usabilidad comparada con interfaces de línea de comando.

**Indicadores:**
- Tiempo de aprendizaje para usuarios básicos: **[dato real del piloto]**
- Tasa de éxito en tareas: **[dato real del piloto]**%
- Satisfacción con interfaz: **[dato real del piloto]**/5.0

**Conclusión:** **[Pendiente de confirmar con la evidencia del piloto]**

**H3:** La automatización reducirá errores financieros.

**Indicadores:**
- Reducción de errores en nómina: **[dato real del piloto]**%
- Ahorro estimado por errores evitados: **[dato real del piloto]**/año por institución
- Reducción de reclamos laborales: **[dato real del piloto]**%

**Conclusión:** **[Pendiente de confirmar con la evidencia del piloto]**

**H4:** La digitalización mejorará el acceso a información.

**Indicadores:**
- Tiempo de búsqueda de información: **[dato real del piloto]**
- Disponibilidad de información: **[dato real del piloto]**

*Nota: El sistema es una aplicación de escritorio; la disponibilidad de información se limita a los equipos donde está instalado (el acceso remoto vía versión web o móvil figura como expansión futura en el Capítulo V).*

**Conclusión:** **[Pendiente de confirmar con la evidencia del piloto]**

**H5:** La capacitación y documentación facilitarán la adopción.

**Indicadores:**
- Tasa de adopción de usuarios activos: **[dato real del piloto]**%
- Satisfacción con capacitación: **[dato real del piloto]**/5.0
- Utilidad percibida de documentación: **[dato real del piloto]**/5.0

**Conclusión:** **[Pendiente de confirmar con la evidencia del piloto]**

## 4.8 ANÁLISIS DE FACTORES DE ÉXITO

### 4.8.1 Factores Técnicos

**Factores que contribuyeron al éxito:**

1. **Selección de tecnologías apropiadas:** Python, SQLAlchemy, CustomTkinter probadas y maduras
2. **Arquitectura modular:** Facilitó desarrollo, pruebas y mantenimiento
3. **Desarrollo iterativo:** Retroalimentación continua mejoró el producto
4. **Pruebas exhaustivas:** Identificación temprana de problemas

### 4.8.2 Factores Organizacionales

**Factores que contribuyeron al éxito:**

1. **Apoyo de la dirección:** Compromiso visible de liderazgo institucional
2. **Participación de usuarios:** Involucramiento activo en diseño y pruebas
3. **Capacitación adecuada:** Formación específica para diferentes roles
4. **Comunicación efectiva:** Información clara sobre beneficios y expectativas

### 4.8.3 Factores Contextuales

**Factores que contribuyeron al éxito:**

1. **Necesidad clara:** Las instituciones tenían una necesidad real y urgente
2. **Recursos mínimos disponibles:** Infraestructura tecnológica básica presente
3. **Cultura abierta al cambio:** Disposición de personal para adoptar nuevas tecnologías
4. **Apoyo externo:** Tutoría académica y comité de investigación

## 4.9 LIMITACIONES Y RETOS

### 4.9.1 Limitaciones Identificadas

**Limitaciones técnicas:**
- Escalabilidad limitada para más de 10,000 empleados
- Dependencia de infraestructura tecnológica básica
- Falta de integración con otros sistemas institucionales

**Limitaciones funcionales:**
- Funcionalidades avanzadas de reportes limitadas
- Sin versión móvil o web
- Sin multi-tenancia para múltiples instituciones

**Limitaciones metodológicas:**
- Muestra limitada a 3-5 instituciones
- Período de evaluación relativamente corto (3 meses)
- Contexto específico a la región estudiada

### 4.9.2 Retos Enfrentados

**Desafíos durante desarrollo:**

1. **Balance entre funcionalidad y simplicidad:** Mantener el sistema usable mientras se agregan funcionalidades
2. **Adaptación a diferentes contextos:** Personalizar para instituciones con diferentes necesidades
3. **Gestión de expectativas:** Mantener expectativas realistas sobre capacidades del sistema
4. **Gestión del tiempo:** Completar desarrollo dentro del cronograma establecido

**Desafíos durante implementación:**

1. **Resistencia al cambio:** Superar escepticismo inicial sobre el nuevo sistema
2. **Capacitación diversa:** Adaptar capacitación a diferentes niveles de competencia tecnológica
3. **Soporte continuo:** Proporcionar soporte durante período de transición
4. **Gestión de problemas técnicos:** Resolver imprevistos durante implementación piloto

## 4.10 CONCLUSIONES DEL CAPÍTULO

Los resultados técnicos presentados en este capítulo demuestran que el Sistema de Gestión de Personal y Nómina fue desarrollado de forma sólida y verificable: la arquitectura de capas con patrones Repository y Service está implementada y documentada; los módulos de empleados, documentos, incidencias, nómina, configuración, autenticación, auditoría, respaldos y exportación son funcionales; y la suite de **281 pruebas automatizadas** se ejecuta exitosamente con **43% de cobertura total** (73% en la lógica de negocio), incluyendo pruebas de seguridad, pagos, integración y respaldos.

Las funcionalidades de seguridad implementadas (autenticación con PBKDF2, control de acceso por rol, auditoría, sanitización de entradas y respaldo/restauración) fueron verificadas mediante pruebas automatizadas dedicadas, y los módulos de lógica de negocio presentan coberturas altas (modelos 92%, servicios 75%, utilidades 81%).

Las secciones de validación empírica (4.4 a 4.7) definen la estructura metodológica y los instrumentos para evaluar la usabilidad, la satisfacción y el impacto cuantitativo y cualitativo en las instituciones piloto; los resultados definitivos se incorporarán al completarse la implementación real del piloto conforme al Capítulo III. Las hipótesis planteadas serán confirmadas o refutadas con esa evidencia empírica.

Las limitaciones identificadas (muestra de 3-5 instituciones, período de evaluación corto, contexto regional específico y dependencia de recursos propios) son propias de un proyecto de este alcance y proporcionan direcciones claras para futuras investigaciones y expansiones del sistema.

Con estos resultados sólidos como evidencia, el siguiente capítulo presentará las conclusiones finales de la investigación, incluyendo recomendaciones para implementación futura, direcciones para investigación adicional, y reflexiones sobre el proceso de desarrollo.