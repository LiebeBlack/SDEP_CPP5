# EVIDENCIA 02 — INVENTARIO DE PRUEBAS AUTOMATIZADAS

**Fecha del inventario reproducido:** 23/11/2026  
**Objeto:** definiciones de prueba del directorio `tests/`  
**Método:** conteo de funciones Python con prefijo `test_`; no se ejecutó la suite.

## 1. Resultado del inventario

| Métrica | Resultado |
|---------|-----------|
| Archivos `test_*.py` | 38 |
| Archivo de configuración compartida | `conftest.py` (no se cuenta como archivo de prueba) |
| Funciones Python `test_*` | 625 |
| Resultado de ejecución | Pendiente; el inventario no significa que las pruebas pasen |
| Cobertura de código | Pendiente de ejecutar y registrar |

## 2. Conteo actual por archivo

| Archivo | Funciones | Área principal |
|---------|----------:|----------------|
| `test_academico.py` | 18 | Gestión académica |
| `test_auth.py` | 16 | Autenticación |
| `test_auto_updater.py` | 20 | Actualizador |
| `test_backups.py` | 9 | Respaldos |
| `test_build.py` | 5 | Construcción |
| `test_configuracion.py` | 9 | Configuración institucional |
| `test_contratos.py` | 18 | Contratos |
| `test_credenciales.py` | 15 | Credenciales |
| `test_descubrimiento_udp.py` | 3 | Descubrimiento de red |
| `test_document_manager.py` | 15 | Gestión documental |
| `test_documentos.py` | 7 | Documentos |
| `test_empleados.py` | 18 | Empleados |
| `test_gui_smoke.py` | 22 | Interfaz gráfica |
| `test_helpers.py` | 66 | Utilerías |
| `test_incidencias.py` | 8 | Incidencias |
| `test_migraciones.py` | 6 | Migraciones |
| `test_nomina_motor.py` | 27 | Motor de nómina |
| `test_notas.py` | 17 | Calificaciones |
| `test_pagos.py` | 9 | Pagos |
| `test_pdf_plantillas.py` | 13 | Plantillas PDF |
| `test_permisos_modulos.py` | 4 | Permisos por módulo |
| `test_registros_moviles.py` | 8 | Registros móviles |
| `test_reportes.py` | 17 | Reportes |
| `test_security.py` | 65 | Seguridad |
| `test_servidor_embebido.py` | 8 | Servidor embebido |
| `test_settings_version.py` | 4 | Versión y configuración |
| `test_sync_academico.py` | 6 | Sincronización académica |
| `test_sync_agente.py` | 7 | Agente de sincronización |
| `test_sync_api_permisos.py` | 22 | Permisos de API de sincronización |
| `test_sync_auth_api.py` | 14 | Autenticación de API de sincronización |
| `test_sync_captura.py` | 8 | Captura de cambios |
| `test_sync_cli.py` | 24 | Cliente de sincronización |
| `test_sync_integracion.py` | 10 | Integración de sincronización |
| `test_sync_merge.py` | 21 | Fusión de datos |
| `test_sync_servidor.py` | 24 | Servidor de sincronización |
| `test_theme.py` | 15 | Tema visual |
| `test_tokens_sesion.py` | 11 | Sesiones móviles |
| `test_validators.py` | 36 | Validadores |
| **Total** | **625** | — |

## 3. Reproducción del conteo

```sh
grep -RhoE '^[[:space:]]*(async )?def test_[A-Za-z0-9_]+' tests --include='test_*.py' | wc -l
# Resultado observado: 625
find tests -maxdepth 1 -type f -name 'test_*.py' | wc -l
# Resultado observado: 38
```

La suma de las cantidades listadas en la sección 2 es 625. Los casos parametrizados pueden producir varias instancias de ejecución a partir de una sola función, por lo que este inventario no debe confundirse con el número de casos recogido por pytest.

## 4. Ejecución y cobertura

No se dispone en este expediente de una salida de ejecución de la suite completa ni de informe de cobertura correspondiente a la revisión actual. Deben ejecutarse y registrarse en el entorno adecuado, indicando fecha, versión/commit, entorno, comando exacto, pruebas pasadas/fallidas/omitidas y duración. La cobertura requiere consignar configuración, alcance de módulos y línea base comparable.

```sh
pytest tests/
pytest tests/ --cov=src --cov-report=term-missing
```

**Estado:** pendiente. No se afirma que la suite pase ni que exista un porcentaje de cobertura verificado.

## 5. Interpretación y limitaciones

El inventario muestra que existen pruebas automatizadas organizadas por componentes. La cantidad y distribución no miden por sí solas su suficiencia, independencia, cobertura o capacidad de detectar defectos. Los resultados de ejecución y cobertura deberán incorporarse solo después de correr los comandos y conservar la salida real.
