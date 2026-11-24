# EVIDENCIA 03 — MATRIZ DE MÓDULOS, REQUERIMIENTOS Y BASES LEGALES

**Objeto:** inventario estático del producto y mapa preliminar entre áreas de indagación y componentes. No acredita que el diagnóstico se haya aplicado ni que la comunidad haya validado requerimientos.
**Fuente de inspección:** `src/gui/` (navegación), `src/services/`, `src/models/`, `src/nomina/`, `GUIA_USUARIO.md` y `DOCUMENTACION_TECNICA.md`. La tabla de pruebas identifica archivos existentes; sus funciones no se consideran ejecutadas.

## 1. Inventario de módulos de navegación

Los nueve módulos accedidos con Ctrl+1 … Ctrl+9, según la guía de usuario:

| Nº | Módulo | Entidades del modelo (`src/models/`) | Servicio (`src/services/`) | Pruebas |
|----|--------|--------------------------------------|-----------------------------|---------|
| 1 | Dashboard | — | — | test_gui_smoke.py |
| 2 | Empleados | empleado.py | empleado_service.py | test_empleados.py (18) |
| 3 | Documentos | documento.py | documento_service.py | test_documentos.py (7), test_document_manager.py (15) |
| 4 | Incidencias | incidencia.py | incidencia_service.py | test_incidencias.py (8) |
| 5 | Contratos | contrato.py | contrato_service.py | test_contratos.py (18) |
| 6 | Nómina | pago.py | pago_service.py | test_pagos.py (9), test_nomina_motor.py (27) |
| 7 | Configuración | configuracion.py | configuracion_service.py | test_configuracion.py (9) |
| 8 | Estudiantes | estudiante.py, grado.py, matricula.py, periodo_academico.py | academico_service.py | test_academico.py (18) |
| 9 | Calificaciones | nota_final.py | nota_service.py | test_notas.py (17) |

Entidades transversales: usuario.py, token_sesion.py, registro_movil.py, enums.py, base.py.

## 2. Correspondencia diagnóstico → módulo

| Área preliminar a indagar (Capítulo I) | Componente del repositorio asociado | Inspección estática; no es validación de campo |
|----------------------------------|----------------------|--------------|
| 1. Falta de control del expediente documental | Módulo de documentos con clasificación por tipología, vencimientos y reporte PDF de vencidos y por vencer; exportación a Excel/CSV | test_documentos.py, test_reportes.py |
| 2. Fragilidad del cálculo de nómina | Motor de nómina (`src/nomina/`: motor.py, isr.py, horas_extra.py, prestaciones.py, seguridad_social.py, finiquito.py, parametros.py) con dos modalidades de ISR y techos de cotización; recibos y planilla en PDF | test_nomina_motor.py (27), test_pagos.py |
| 3. Ausencia de trazabilidad en las incidencias | Módulo de incidencias con reposos, ausencias, permisos, aprobación/rechazo, cómputo de días y documentos de soporte | test_incidencias.py |
| 4. Dispersión del registro académico | Módulos de estudiantes y calificaciones: grados, inscripciones, periodos, notas finales con autorización de edición | test_academico.py, test_notas.py |
| 5. Ausencia de respaldo y trazabilidad | Autenticación por rol (`PermissionChecker`), auditoría, respaldos programados, tokens de sesión, respaldo y restauración de base de datos | test_security.py (65), test_backups.py, test_auth.py |

## 3. Componentes de respuesta comunitaria

| Componente | Líneas / tamaño | Función en la transferencia |
|-----------|-----------------|------------------------------|
| Cliente Android (`android/`) | 97 archivos Kotlin, 22.558 líneas; 88 producción y 9 pruebas | Inventario estático actual; build y tests pendientes (evidencia 06) |
| Nodo de sincronización (`sync_agent/`) | 11.443 líneas | Operación multiusuario en red local sin conexión permanente |
| Actualizador automático (`updater/`) | — | Mantenimiento de versión sin intervención recurrente |
| Motor de plantillas Markdown→PDF | — | Constancias con redacción propia de la institución |

## 4. Catálogo de documentos oficiales generables

Según la guía de usuario, el sistema genera 13 tipos de documento oficial en PDF, entre ellos: constancia de ingresos, recibo de pago, planilla de nómina, liquidación, reporte de incidencias, reporte de vencimientos documentales y reporte de contratos; además de constancias desde plantillas Markdown institucionales y reportes tabulares con pie institucional.

## 5. Base legal por módulo

| Módulo | Norma principal | Artículos/asuntos que atiende | Estado de confrontación |
|--------|----------------|-------------------------------|--------------------------|
| Contratos e incidencias | LOTTT, Decreto N.º 8.938, G.O. Ext. 6.076, 07/05/2012 | Materias laborales relacionadas | Identificación contrastada; artículos y aplicabilidad por revisar |
| Nómina — seguridad social | Ley Orgánica del Sistema de Seguridad Social, G.O. 37.600, 30/12/2002; reforma parcial G.O. 39.912, 30/04/2012 | Materias de cotización relacionadas | Fuentes identificadas; normas prestacionales, tasas y parámetros requieren revisión profesional |
| Nómina — ISR | Reforma de ISLR, G.O. Ext. 6.210, 30/12/2015 | Retención y régimen tributario | Identificación contrastada; parámetros y régimen completo por revisar |
| Estudiantes y calificaciones | Ley Orgánica de Educación, G.O. Ext. 5.929, 15/08/2009 | Registro académico | Identificación contrastada; artículos/procedimientos por revisar |
| Datos de estudiantes | LOPNNA, publicación inicial G.O. 5.266, 02/10/1998; reforma G.O. Ext. 6.185, 08/06/2015 | Protección integral e interés superior | Fuentes contrastadas; tratamiento institucional y otras reformas por revisar |
| Tecnologías en sector público | Ley de Infogobierno, G.O. 40.274, 17/10/2013 | Uso de TI según ámbito de aplicación | Identificación contrastada; aplicabilidad institucional por determinar |
| Servicio comunitario | Ley de Servicio Comunitario del Estudiante de Educación Superior, G.O. 38.272, 14/09/2005 | Requisitos académicos del proyecto | Identificación contrastada; reglamento universitario por confirmar |
| Ciencia, tecnología e innovación | LOCTI, Decreto 1.411, G.O. Ext. 6.151 (2014), reforma G.O. Ext. 6.693 (2022) | Contexto de desarrollo | Identificación documental parcial; no se deduce obligación de licencia abierta |

**Nota:** los números y fechas indicados se contrastaron parcialmente con fuentes listadas en `EVIDENCIAS/EVIDENCIA_04_FUENTES_LEGALES.md`. Esta matriz no constituye dictamen ni certificación. Deben revisarse los textos vigentes, artículos pertinentes, aplicabilidad según la institución, normas sectoriales conexas y parámetros del software con asesoría competente.
