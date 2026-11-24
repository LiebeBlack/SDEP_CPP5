# EVIDENCIA 06 — INVENTARIO DEL SOFTWARE ANDROID (SDEP MÓVIL)

**Fecha de la medición:** 23/11/2026
**Objeto:** árbol de Android del repositorio disponible al momento de la medición. El directorio conserva la configuración de versión base 3.0.1, pero este inventario incluye cambios Android posteriores documentados en la sección 8; no se asume que todo corresponda al commit original 3.0.1.
**Método:** conteo de archivos, líneas y anotaciones de prueba con utilerías estándar; inspección de código, `build.gradle.kts` y `AndroidManifest.xml`. Los comandos son reproducibles.

## 1. Resultado global

| Métrica | Valor |
|---------|-------|
| Archivos Kotlin totales | 97 (88 de producción + 9 de pruebas unitarias) |
| Líneas de aplicación (producción) | 21.892 |
| Líneas de pruebas unitarias | 666 |
| Total de líneas Kotlin | 22.558 |
| Anotaciones `@Test` | 43 |
| Idioma y toolkit | Kotlin 1.9.24, Jetpack Compose, Room, Hilt |
| Identificador de aplicación | `ve.edu.sdep.movil` |
| API mínima / objetivo | 26 (Android 8.0) / 34 (Android 14) |

## 2. Líneas por paquete de producción

| Paquete | Líneas | Responsabilidad |
|---------|--------|-----------------|
| `datos/local` | 4.488 | Room: espejo de tablas, aplicador de operaciones, journal, DAO y entidades |
| `ui` | 10.254 | Jetpack Compose: pantallas, módulos, formularios, registros, PDF, ajustes |
| `datos/repositorio` | 4.069 | Sesión, empleados, documentos, adjuntos, acciones laborales, sincronización |
| `datos/remoto` | 991 | Cliente del protocolo HTTP, descubrimiento del nodo, DTO |
| `dominio/modelo` | 660 | Modelo del dominio: protocolo, registro, roles, sesión, política de edición |
| `datos/documentos` | 511 | Constancias PDF, montos y tipos de adjunto |
| `datos/seguridad` | 391 | Bóveda de credenciales, desbloqueo biométrico, hash de contraseña |
| `di` | 186 | Inyección de dependencias (módulos de base de datos y red) |
| `sincronizacion` | 131 | Programador y trabajo de sincronización (WorkManager) |
| `datos/preferencias` | 72 | Preferencias de apariencia |
| Raíz (`MainActivity`, `SdepApplication`) | 139 | Punto de entrada y configuración de la aplicación |
| **Total producción** | **21.892** | — |

Verificación aritmética: 4.488 + 10.254 + 4.069 + 991 + 660 + 511 + 391 + 186 + 131 + 72 + 139 = 21.892.

## 3. Archivos de mayor tamaño (corte por líneas)

| Archivo | Líneas | Función |
|---------|--------|---------|
| `datos/local/AplicadorEspejo.kt` | 1.110 | Aplica las operaciones recibidas sobre el espejo local |
| `datos/local/Espejo.kt` | 1.032 | Definición del espejo de datos del dispositivo |
| `ui/modulos/Catalogo.kt` | 1.008 | Catálogo de módulos, tablas y formularios |
| `ui/ajustes/PantallaAjustes.kt` | 753 | Ajustes, conexión y sincronización |
| `ui/documentos/PantallaHerramientasPdf.kt` | 746 | Herramientas PDF del teléfono |
| `datos/repositorio/SincronizacionRepositorio.kt` | 686 | Ciclo de sincronización contra el nodo central |
| `datos/local/dao/DaosEspejo.kt` | 649 | Acceso a datos del espejo |
| `datos/repositorio/DocumentosRepositorio.kt` | 566 | Documentos y constancias |
| `datos/repositorio/TablaRepositorio.kt` | 547 | Gestión dinámica de las diez tablas operativas |
| `datos/repositorio/AutenticacionRepositorio.kt` | 531 | Ingreso con contraseña o credencial biométrica |

## 4. Pruebas unitarias (9 archivos, 43 anotaciones `@Test`)

| Archivo | Área verificada |
|---------|-----------------|
| EspejoTest.kt | Aplicación y consistencia del espejo de datos |
| FechasTest.kt | Manejo de fechas |
| AparienciaTest.kt | Preferencias de apariencia |
| ProtocoloTest.kt | Contrato del protocolo con el nodo |
| HashContrasenaTest.kt | Hash de contraseñas |
| PoliticaRolesTest.kt | Matriz de roles y permisos |
| CatalogoTest.kt | Catálogo de módulos |
| FormatoTest.kt | Formato de valores en pantalla |
| AdjuntosUiTest.kt | Validación de formatos, nombres y tamaños de adjuntos |

## 5. Configuración de construcción verificada

| Elemento | Valor (de `build.gradle.kts` y `gradle-wrapper.properties`) |
|----------|------------------------------------------------------------|
| Gradle | 8.7 (wrapper) |
| Android Gradle Plugin | 8.5.2 |
| Kotlin | 1.9.24 |
| Compose BOM | 2024.06.00 |
| JDK de compilación | 17 |
| minSdk / targetSdk | 26 / 34 |
| Variante release | minificado y recorte de recursos activos (`isMinifyEnabled`, `isShrinkResources`) |

## 6. Permisos declarados (AndroidManifest.xml)

| Permiso | Función |
|---------|---------|
| `INTERNET` | Comunicación con el nodo central de la institución |
| `ACCESS_NETWORK_STATE` | Verificación de disponibilidad de red para sincronizar |
| `USE_BIOMETRIC` / `USE_FINGERPRINT` | Desbloqueo de sesión con credencial del dispositivo |

El manifiesto declara además un proveedor de archivos privado (`${applicationId}.archivos`) para compartir los PDF generados sin exponer rutas, y reglas de respaldo y extracción restringidas (`reglas_respaldo.xml`, `reglas_extraccion.xml`) junto con una configuración de seguridad de red (`seguridad_red.xml`).

## 7. Reproducción de la medición

```text
$ find android -name "*.kt" | wc -l                    → 97
$ find android -name "*.kt" | xargs wc -l | tail -1    → 22558 total
$ find app/src/main/java -name "*.kt" | wc -l         → 88
$ find app/src/test -name "*.kt" | wc -l               → 9
$ grep -Rho "@Test" app/src/test --include="*.kt" | wc -l → 43
$ find app/src/main/java/ve/edu/sdep/movil -maxdepth 1 -type f -name '*.kt' -print0 | xargs -0 wc -l | tail -1 → 139 total (raíz)
$ find app/src/test -name "*.kt" -print0 | xargs -0 wc -l | tail -1 → 666 total
```

## 8. Cambios Android incluidos en la medición

| Cambio | Archivos principales | Observación |
|--------|----------------------|-------------|
| Adjuntar, reemplazar y abrir/compartir soportes de documentos e incidencias | `datos/repositorio/AdjuntosRepositorio.kt`, `ui/modulos/AdjuntosViewModel.kt`, `ui/modulos/AdjuntosUi.kt`, `ui/modulos/PantallaFichaModulo.kt` | Contenido por hash, cola local y canal de binarios. Se corrigió además la rama de selección inicial cuando el registro no tenía adjunto. |
| Subida de binarios de `incidencias` | `datos/repositorio/SincronizacionRepositorio.kt` | El canal de subida contempla documentos e incidencias. |
| Consultas DAO de metadatos de adjuntos | `datos/local/dao/DaosEspejo.kt`, `datos/local/entidad/EntidadesEspejo.kt` | Se separa lectura de metadatos y lectura de BLOB. |
| Validación de tipos y pruebas unitarias de reglas puras | `datos/documentos/TipoAdjunto.kt`, `app/src/test/.../AdjuntosUiTest.kt` | Acepta PDF, JPEG y PNG tras validar extensión/MIME y firma; no es análisis antivirus ni validación integral de archivos. |

Las métricas de las secciones 1 a 4 fueron recontadas después de incorporar los cambios indicados en la sección 8. Los componentes nuevos no tienen compilación ni pruebas ejecutadas registradas. El límite de 8 MB es el límite de selección desde esta interfaz móvil; no se declara como límite del nodo.

**Estado de verificación:** inspección estática y conteo reproducible; compilación y ejecución de pruebas Android pendientes. No distribuir el APK con base en este inventario solamente. El comando de cierre es `./gradlew :app:assembleDebug :app:testDebugUnitTest` en un entorno con JDK 17 y Android SDK configurados.

## 9. Nota de concordancia

La cifra de 22.539 líneas de la re-medición inmediatamente anterior precedía a los últimos cambios locales de validación y aislamiento de estado. El conteo actual es de 22.558 líneas; el número de archivos se mantiene en 97. Las métricas dependen del estado del árbol y no se atribuyen a un commit/tag de lanzamiento sin identificarlo.
