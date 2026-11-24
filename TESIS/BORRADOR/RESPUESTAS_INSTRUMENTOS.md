# CONSOLIDADO DE INSTRUMENTOS Y ESTADO DE RESPUESTAS

Documento de trabajo para registrar instrumentos y respuestas únicamente después de su revisión, autorización y aplicación. Los formatos aquí descritos no implican que hayan sido validados o administrados. No se incorporan respuestas de campo ficticias.

## 1. Estado general

- Consentimientos y autorización institucional: `[pendientes de evidencia]`.
- Revisión de instrumentos por tutor/especialistas: `[pendiente de actas y ajustes]`.
- Diagnóstico, entrevistas, observación, instalación, capacitación y piloto: `[pendientes]`.
- Resultados técnicos: la inspección estática inventarió pruebas, pero no hay ejecución actual de pytest ni Gradle registrada.
- Protección de datos: antes de cualquier recolección, acordar minimización, seudonimización, acceso, conservación y eliminación con la institución.

## 2. Registro de campo

Usar códigos no identificables (por ejemplo, I-01/S-01) y no incluir cédulas, nombres, datos de nómina ni notas reales en este archivo. Guardar documentos de consentimiento por separado bajo custodia institucional.

### 2.1 Caracterización de la institución

| Código | Tipo/naturaleza institucional | Localidad general | Procesos incluidos | Equipo/conectividad | Fecha y responsable | Estado |
|--------|-------------------------------|-------------------|-------------------|--------------------|--------------------|--------|
| `[pendiente]` | | | | | | No aplicado |

### 2.2 Registro de consentimiento y participación

| Código sujeto | Rol | Consentimiento individual | Autorización institucional | Fecha | Retiro/observación |
|--------------|-----|--------------------------|----------------------------|-------|--------------------|
| `[pendiente]` | | | | | No aplicado |

## 3. Ficha de observación de procesos (pretest/postest)

Definir antes de medir: inicio y fin de cada tarea, unidades, evento de error, denominador, corrección posterior y condiciones comparables. No registrar datos identificables de empleados o estudiantes.

| Código institución | Código sujeto/rol | Tarea | Fase | Tiempo | Resultado | Error según definición | Corrección | Contexto/equipo | Fecha |
|--------------------|-------------------|-------|------|--------|-----------|-----------------------|------------|-----------------|-------|
| `[pendiente]` | | Alta de empleado | Pre / Post | | | | | | |
| `[pendiente]` | | Incorporar documento | Pre / Post | | | | | | |
| `[pendiente]` | | Registrar incidencia | Pre / Post | | | | | | |
| `[pendiente]` | | Preparar nómina de prueba | Pre / Post | | | | | | |
| `[pendiente]` | | Consolidar calificaciones de prueba | Pre / Post | | | | | | |

### 3.1 Trazabilidad

La trazabilidad se registra operación por operación y solo cuando se pueda verificar evento, usuario/rol, fecha, dato o campo afectado y fuente de auditoría. La app Android puede encolar/sincronizar operaciones, pero no se asume que ese journal sea equivalente al log de auditoría del escritorio.

| Código registro | Componente | Evento | Actor/rol seudónimo | Fecha/hora | Cambio verificable | Fuente/limitación |
|----------------|------------|--------|---------------------|------------|-------------------|------------------|
| `[pendiente]` | | | | | | No aplicado |

## 4. Protocolo de usabilidad y percepción

El protocolo de tareas y el cuestionario requieren revisión previa. No usar SUS ni interpretar promedios hasta contar con instrumento autorizado, versión aplicada, muestra y respuestas reales. Mantener respuestas por sujeto seudonimizado.

| Código sujeto | Rol | Tarea | Completada (sí/no) | Tiempo | Ayuda requerida | Dificultad/comentario | Fecha |
|--------------|-----|-------|--------------------|--------|-----------------|-----------------------|-------|
| `[pendiente]` | | | | | | | |

### 4.1 Cuestionario de percepción

| Código sujeto | Dimensión/pregunta | Respuesta | Versión del instrumento | Fecha |
|--------------|--------------------|-----------|-------------------------|-------|
| `[pendiente]` | | | | |

### 4.2 Consistencia y validez

- Revisión de contenido: `[pendiente: jueces, fecha, perfil, observaciones y cambios]`.
- Pilotaje del guion: `[pendiente]`.
- Cualquier coeficiente de confiabilidad: `[pendiente de respuestas reales y tamaño muestral adecuado]`.

## 5. Inventario técnico estático (no equivale a suite aprobada)

| Cotejo | Afirmación verificable por inspección | Estado | Evidencia |
|--------|----------------------------------------|--------|-----------|
| 1 | Existe código de autenticación y control de acceso por roles | Presente en repositorio; no es auditoría de seguridad | `src/`, `android/`; pruebas inventariadas |
| 2 | Existe código de auditoría en escritorio | Inspección de código; cobertura/operación no certificada | `src/utils/` |
| 3 | Existe código de respaldo | Inspección de código; restauración en entorno institucional pendiente | `src/`; test inventariado |
| 4 | Existe motor de cálculo de nómina | Módulos y pruebas están en árbol; fórmulas y parámetros requieren revisión normativa/profesional | `src/nomina/` |
| 5 | Existe generación de documentos/reportes | Funcionalidad descrita en documentación; ejecución y revisión de salida pendientes | `GUIA_USUARIO.md`, `src/` |
| 6 | Existe sincronización entre puestos | Código en `sync_agent/`; despliegue e integración no probados aquí | Evidencia 01 |
| 7 | Existe cliente Android y gestión de adjuntos | 97 archivos Kotlin, 22.558 líneas y 43 anotaciones `@Test`; build/test pendientes | Evidencia 06 |
| 8 | Hay 625 funciones `test_*` Python en 38 archivos de prueba | Inventario estático; ejecución pendiente | Evidencia 02 |
| 9 | Suite Python pasó sin fallos | Sin registro de ejecución | Pendiente |
| 10 | Aplicación Android compiló y pasó tests | Sin JDK/SDK y sin salida Gradle | Pendiente |
| 11 | El sistema fue instalado y aceptado por una comunidad | No hay actas/registros localizados | Pendiente |

## 6. Lista de cotejo para transferencia

| Criterio | Evidencia requerida | Estado |
|----------|---------------------|--------|
| Aprobación e instalación | Versión/commit, acta, equipos | `[pendiente]` |
| Revisión de parámetros | Hoja aprobada por profesional responsable | `[pendiente]` |
| Respaldo y recuperación | Registro de respaldo y prueba de restauración | `[pendiente]` |
| Capacitación | Agenda, versión de guía, asistencia consentida | `[pendiente]` |
| Uso piloto | Bitácora sin datos identificables | `[pendiente]` |
| Aceptación institucional | Acta de aceptación o limitaciones | `[pendiente]` |

## 7. Regla de tabulación

1. Mantener intacta la fuente original y crear una copia anonimizada para análisis.
2. Registrar versión del instrumento, fechas, denominadores, condiciones y datos faltantes.
3. No inferir causalidad a partir de un pretest-postest de un solo grupo.
4. No reemplazar celdas vacías con promedios supuestos; explicar ausencias.
5. Vincular cada tabla del Capítulo IV con datos fuente y método de cálculo reproducible.
