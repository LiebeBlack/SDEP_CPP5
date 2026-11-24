# SOFTWARE DESARROLLADO — CLIENTE MÓVIL ANDROID (SDEP MÓVIL)

Documento técnico-académico del componente Android. Complementa los capítulos I a IV con su arquitectura y funcionalidades inspeccionadas. El inventario actual contiene cambios locales posteriores a la revisión base declarada `3.0.1`; la evidencia 06 registra este alcance y no atribuye los cambios a un release etiquetado. Se inspeccionaron `android/README.md`, `PARIDAD_ESCRITORIO.md`, `COMPATIBILIDAD.md` y el código. No hay compilación ni ejecución de pruebas registrada para los cambios descritos.

## 1. Propósito del componente en el proyecto

SDEP Móvil es el cliente Android nativo presente en el repositorio. El código incluye flujos de captura y acceso a datos desde el teléfono; que personal institucional lo use para levantar visitas u observaciones y que elimine transcripción manual es un beneficio esperado que requiere instalación y evaluación en campo.

El componente se integra con el protocolo del nodo central (`sync_agent`), usa sesión/token e identificador de equipo, y sincroniza registros móviles. La aplicación mantiene una base Room local y cola de operaciones; la existencia de ese flujo en el código no demuestra un piloto exitoso. La app no debe describirse como equivalente al log de auditoría de escritorio: que sus operaciones se sincronicen no significa que replique todos los eventos de auditoría.

La reducción de transcripción es una hipótesis de utilidad del componente, pendiente de confirmación con observación y medición autorizadas.

## 2. Naturaleza técnica del desarrollo

SDEP Móvil es aplicación nativa, no una vista web empaquetada: está escrita en Kotlin 1.9.24 sobre Jetpack Compose (interfaz declarativa), Room (persistencia local) y Hilt (inyección de dependencias), y replica en el teléfono la lógica de sesión y de sincronización del escritorio. La decisión de nativo frente a híbrido se justifica por tres requerimientos del contexto: el funcionamiento sin red (que exige base de datos local de verdad, no caché de página), el uso de la credencial biométrica del dispositivo para proteger la sesión, y la generación de documentos PDF en el teléfono.

La medición actual comprende 97 archivos Kotlin y 22.558 líneas: 88 archivos de producción (21.892 líneas) y 9 archivos de prueba (666 líneas, 43 anotaciones `@Test`). La distribución se reproduce en `EVIDENCIAS/EVIDENCIA_06_INVENTARIO_ANDROID.md`. Son métricas estáticas, no resultados de compilación o prueba.

| Paquete | Líneas | Responsabilidad |
|---------|--------|-----------------|
| `ui` | 10.254 | Interfaz Compose: portada, módulos, formularios, registros, herramientas PDF, ajustes |
| `datos/local` | 4.488 | Room con el espejo de tablas, el aplicador de operaciones y el journal |
| `datos/repositorio` | 4.069 | Sesión, empleados, documentos, adjuntos, acciones laborales, sincronización |
| `datos/remoto` | 991 | Cliente del protocolo, descubrimiento del nodo, DTO del contrato HTTP |
| `dominio/modelo` | 660 | Protocolo, registro, roles, sesión, política de edición |
| `datos/documentos` | 511 | Constancias PDF, tipos de adjunto y herramientas locales |
| `datos/seguridad` | 391 | Bóveda de credenciales, desbloqueo biométrico, hash de contraseñas |
| `di` | 186 | Inyección de dependencias (base de datos y red) |
| `sincronizacion` | 131 | Programador y trabajo de sincronización |
| `datos/preferencias` | 72 | Preferencias de apariencia |
| Raíz | 139 | Punto de entrada (`MainActivity`, `SdepApplication`) |

## 3. Arquitectura por capas y flujo de datos

La arquitectura del teléfono replica la disciplina de capas del escritorio, con sus cuatro planos:

1. **Capa remota (`datos/remoto`):** el único punto de contacto con la red. Implementa el cliente del contrato HTTP del nodo (`ProtocoloApi.kt`, `ApiSyncFactory.kt`, `Dtos.kt`), la gestión de errores HTTP (`ErroresHttp.kt`, `ApiAcciones.kt`) y el descubrimiento del nodo en la red local (`Descubrimiento.kt`).
2. **Capa local (`datos/local`):** la base del funcionamiento sin conexión. Contiene la base de datos del espejo (`BaseDatosSdep.kt`, `Espejo.kt`, `EsquemaTabla.kt`), los DAO (`dao/`), las entidades (`entidad/`) y el aplicador de operaciones (`AplicadorEspejo.kt`, el archivo de mayor tamaño del componente, 1.110 líneas), que es el mismo aplicador conceptual del nodo: decide columna por columna con el orden total determinista.
3. **Capa de repositorios (`datos/repositorio`):** once repositorios que concentran las reglas de sesión, autenticación, empleados, documentos, acciones laborales, configuración, tablas, registros y sincronización (`SincronizacionRepositorio.kt`, 681 líneas).
4. **Capa de presentación (`ui`):** pantallas Compose organizadas por función (login, inicio, módulos, fichas y listas, registros, editor, herramientas PDF, conflictos, ajustes, perfil), cada una con su ViewModel.

El flujo de datos característico es el siguiente: el usuario registra o edita en la interfaz; el repositorio valida el permiso del rol, escribe en Room y deja la operación en la cola de salida, todo en la misma transacción; el programador de sincronización transporta la cola al nodo central cuando hay red; el nodo fusiona la operación con el orden total determinista y devuelve el avance de cursor; el teléfono aplica las operaciones recibidas sobre su espejo. La escritura nunca queda atrapada esperando la red: si el envío falla, la operación permanece en cola y se reintenta con espera creciente.

## 4. Garantías de diseño del cliente móvil

Cinco características de diseño identificables en documentación y código (pendientes de validación de ejecución e integración):

**Diseño local-first.** El código de repositorios guarda operaciones en Room y mantiene una cola para sincronización. La operación sin red debe probarse en un dispositivo real para establecer qué funciones están disponibles y con qué límites.

**Protocolo de sincronización.** El cliente usa DTO/API y mecanismos de aplicación/mezcla definidos en el proyecto. La compatibilidad y deduplicación deben verificarse con pruebas de integración entre la revisión móvil y la versión concreta del nodo.

**Negociación de capacidades.** El código implementa consulta de versión/capacidades del protocolo y adapta módulos según lo anunciado por el nodo. Este diseño reduce ciertos riesgos de incompatibilidad, pero no garantiza ausencia de fallos; se requieren pruebas con versiones concretas.

**Nombres que no se replican.** El docente asignado a un grado viaja como identificador global de su cuenta y su nombre se resuelve contra `/api/v1/consultas/docentes`, con caché en el teléfono. La asignación se lee en listas y fichas pero nunca se edita desde el móvil: la referencia de autoridad del dato permanece en el escritorio.

**Conexión prevista al nodo institucional.** El manifiesto declara permisos de red y el cliente configura el nodo. La ausencia de servicios externos debe confirmarse mediante inspección completa de dependencias, código y tráfico antes de hacer una afirmación de privacidad absoluta.

## 5. Seguridad en el dispositivo

La capa `datos/seguridad` contiene una bóveda de credenciales (`Boveda.kt`), lógica de autenticación biométrica (`AutenticadorBiometrico.kt`) y utilidades de hash (`HashContrasena.kt`). El funcionamiento y nivel de protección efectivos dependen de configuración, claves, versión de Android, dispositivo y pruebas; no se presentan como auditados.

El modelo móvil contempla roles y comprobaciones de permiso en interfaz y repositorios. La prueba `PoliticaRolesTest.kt` existe en el árbol; su ejecución y la cobertura de todas las rutas no están verificadas. Las salvaguardas técnicas no sustituyen controles del servidor ni una revisión de seguridad.

El manifiesto referencia reglas de respaldo/extracción y configuración de seguridad de red (`reglas_respaldo.xml`, `reglas_extraccion.xml`, `seguridad_red.xml`). El cliente usa tokens de sesión; la presencia de pruebas de tokens en el proyecto de escritorio no valida por sí misma la emisión, almacenamiento o expiración en el cliente móvil.

## 6. Funcionalidad entregada al usuario móvil

La pantalla de inicio agrupa las tareas en cuatro soluciones —Personal, Académico, Administración y Trabajo de campo— y cada tarjeta abre la lista, la tabla académica o la captura de campo que corresponda al rol de la cuenta. La gestión de datos es dinámica: el formulario se genera con el esquema real de la base (lectura de `PRAGMA table_info`), sobre las diez tablas operativas —empleados, documentos, incidencias, contratos, pagos, estudiantes, periodos, grados, matrículas y calificaciones—, de modo que una columna nueva incorporada en el escritorio aparece en el teléfono sin modificar código. La alta, edición y baja dependen del permiso de la cuenta.

Tres funciones presentes en el código merecen descripción; su utilidad efectiva depende de validación funcional y uso autorizado:

- **Flujo de adjuntos de documentos e incidencias.** En el código de `AdjuntosRepositorio` y la ficha se implementan selección, reemplazo y lectura de archivos de registros existentes, con comprobación SHA-256 y consulta por metadatos. El límite de selección móvil es 8 MB y no se atribuye al nodo central. El código encola referencias para el canal de binarios y la sincronización incluye los binarios de `documentos` e `incidencias`; esta revisión estática no comprueba operación offline, transacción completa, apertura en aplicaciones receptoras ni integración con el nodo. También se modificó el sincronizador para contemplar la tabla `incidencias`, antes excluida de la rama de subida revisada.

- **Constancias y herramientas PDF en el teléfono.** El árbol incluye generador de constancias (`datos/documentos/`, `PdfConstanciaLocal.kt`) y herramientas PDF. Existe un flujo para compartir mediante proveedor de archivos. La generación, permisos de URI, compatibilidad con aplicaciones receptoras y utilidad del proceso requieren pruebas en dispositivos.
- **Bandeja de conflictos.** Los choques de edición que la mezcla por campo no puede resolver de forma transparente quedan visibles en una pantalla dedicada (`ui/conflictos/`), con el valor perdedor registrado, de modo que el personal puede decidir con información y no a ciegas.

El código programa trabajo periódico de sincronización con WorkManager, además de operaciones por lotes y recepción por cursor. Los intervalos, reintentos, comportamiento ante fallos, restauración del espejo y estrategia de respaldo deben verificarse en ejecución. No se localizó evidencia de un piloto Android ni de restauración probada.

## 7. Interfaz y presentación

La interfaz usa Material 3 con modo claro y oscuro, siguiendo el tema visual del escritorio para que el sistema sea reconocible en sus tres presentaciones (escritorio, web del nodo y teléfono). La vinculación con el escritorio se hace por emparejamiento con prueba de conexión, que incluye la detección del desfase de reloj entre el teléfono y el nodo, dato que la mezcla por marca de tiempo necesita conocer.

## 8. Calidad técnica del componente

El árbol contiene 43 anotaciones `@Test` en 9 archivos, incluido `AdjuntosUiTest.kt`, que cubre algunas reglas puras de formato y presentación. Estas cifras son un inventario; no se dispone de ejecución satisfactoria. El comando previsto es `./gradlew :app:assembleDebug :app:testDebugUnitTest`, en un entorno con JDK 17 y Android SDK.

Los archivos de configuración indican API mínima 26, objetivo 34, JDK 17 y Gradle 8.7 vía wrapper, además de opciones de minificación/recorte en release. No se generó APK ni se verificó su firma o instalación. La distribución interna es una modalidad prevista, sujeta a procedimientos institucionales.

## 9. Paridad y compatibilidad con el resto del sistema

El proyecto mantiene `android/PARIDAD_ESCRITORIO.md` y `android/COMPATIBILIDAD.md` como documentación de diseño y compatibilidad prevista. Deben actualizarse con las pruebas efectivamente ejecutadas; no garantizan por sí mismos que distintas versiones del teléfono y nodo puedan operar sin incidentes.

## 10. Resultado del componente frente al objetivo del proyecto

El código móvil es un componente del producto inspeccionado. No hay evidencia suficiente para concluir que haya sido instalado, aceptado o utilizado por las instituciones, que elimine pasos de transcripción o que preserve en el teléfono todas las garantías del escritorio. Esos beneficios y límites deben evaluarse mediante pruebas de integración, revisión de permisos y un piloto autorizado.

---
**Fuentes:** directorio `android/` (código y documentación de desarrollo); `DOCUMENTACION_TECNICA.md` del repositorio (apartado de aplicación móvil); mediciones de `EVIDENCIAS/EVIDENCIA_06_INVENTARIO_ANDROID.md`.
