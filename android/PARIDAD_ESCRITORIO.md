# Paridad Escritorio ↔ Android

Especificación de la réplica de la aplicación de escritorio en el teléfono.
Criterio de aceptación: **toda capacidad del escritorio tiene un equivalente
móvil, o queda declarada como no aplicable con su justificación**. No hay
funciones «a medias»: cada módulo entra completo (listar, buscar, ver, crear,
editar, borrar, acción de negocio, permisos y estado offline).

---

## 1. Punto de partida (lo que ya existe)

| Pieza | Estado | Evidencia |
|---|---|---|
| Espejo de las 12 tablas del escritorio en Room | **Hecho** | `datos/local/entidad/EntidadesEspejo.kt` |
| Reglas de payload (solo campos tocados, FK como UUID, rutas locales fuera) | **Hecho** | `datos/local/Espejo.kt` |
| Aplicación de operaciones remotas con marcas por campo | **Hecho** | `datos/local/AplicadorEspejo.kt` |
| DAO por entidad (empleados, documentos, incidencias, contratos, pagos, estudiantes, periodos, grados, matrículas, notas, configuraciones) | **Hecho** | `datos/local/dao/DaosEspejo.kt` |
| Cola de salida transaccional, cursor, diferidas, blobs | **Hecho** | `RegistroRepositorio`, `SincronizacionRepositorio` |
| Autenticación contra el nodo central, roles y permisos | **Hecho** | `AutenticacionRepositorio`, `dominio/PoliticaRoles` |
| Pantallas | **Solo 4** | registros, login, ajustes, conflictos |
| Resto de módulos (empleados, documentos, incidencias, contratos, nómina, académico, administración) | **Falta la interfaz** | — |

La app **no necesita un canal nuevo**: las lecturas salen del espejo local y las
escrituras se encolan en la misma transacción que el dato (offline-first).

---

## 2. Matriz de paridad

| Módulo escritorio | Capacidades que hay que replicar | Datos en el teléfono | Acción autoritativa en el servidor | Falta en Android |
|---|---|---|---|---|
| **Panel** | Indicadores (empleados, activos, documentos, incidencias, pagos), avisos de vencimientos, gráficos | Sí (consultas locales) | `GET /consultas/dashboard` | Pantalla + ViewModel |
| **Empleados** | Listar, buscar, filtrar por tipo, ficha completa, alta, edición, baja lógica, foto, documentos del empleado, exportar | Sí (`empleados`, `documentos`, `blobs`) | — (push) | Todo |
| **Documentos** | Listar, vencidos/por vencer, alta con archivo, edición, baja, descarga, exportar | Sí (metadatos + blob) | `/archivos/subir`, `/blob/{hash}` | Todo |
| **Incidencias** | Listar, filtrar por estado, alta con soporte, edición, baja, aprobar, rechazar | Sí | `POST /acciones/incidencias/{id}/aprobar`, `/rechazar` | Todo |
| **Contratos** | Listar, vigentes/por vencer/vencidos, alta, edición, renovar, terminar, PDF | Sí | `POST /acciones/contratos/{id}/renovar`, `/terminar` | Todo |
| **Nómina** | Periodos, generar nómina, resumen, detalle por empleado, marcar pagado, recibo y planilla PDF | Sí (`pagos`) | `POST /acciones/nomina/generar`, `/resumen`, `/pagos/{id}/pagado` | Todo |
| **Configuración** | Usuarios (alta/edición/bloqueo/desbloqueo), auditoría, datos de la institución, preferencias, ver estado de respaldos | Parcial (usuarios **no** se replican) | `/admin/usuarios`, `/consultas/auditoria` | Todo |
| **Estudiantes** | Listar, buscar, legajo, alta, edición, baja, exportar | Sí | — (push) | Todo |
| **Calificaciones** | Periodos (abrir/cerrar/reabrir), grados y secciones, matrículas, notas (una o por lote), consolidado, boletín, acta, tokens académicos | Sí (salvo tokens) | `/acciones/academicos/...` | Todo |

### Lo que no se replica (y por qué)

| Función del escritorio | Decisión en Android |
|---|---|
| Crear/verificar/restaurar/eliminar respaldos de la base del PC | **No aplica**: son archivos del equipo servidor. El teléfono muestra su estado y antigüedad (consulta), no los ejecuta. |
| Actualizador automático y bandeja del servidor embebido | **No aplica**: son procesos del escritorio. |
| Tema del escritorio, DPI, atajos de teclado | **No aplica**: el teléfono usa Material 3, gestos y tipografía del sistema. |
| «Adoptar datos existentes», purga de historial, exportar conflictos a JSON | **No aplica** en el teléfono (operaciones de mantenimiento del nodo). |

---

## 3. Fases de implementación

Cada fase termina con el módulo **completo** para los roles que lo usan.

### Estado de esta entrega: lectura de todos los módulos

Entregado en `ui/modulos/`: índice de módulos con la matriz de roles, panel de
control con cifras y avisos, y para **cada** módulo del escritorio su lista
(búsqueda y estados) y su ficha completa por secciones.

| Módulo | Lista | Ficha | Escritura |
|---|---|---|---|
| Panel de control | cifras y avisos | — | no aplica |
| Empleados | sí | datos personales, contacto, laboral, formación, banco, salud, emergencia | Fase 1 |
| Documentos | sí, con vencimientos | metadatos, archivo y huella | Fase 1 |
| Incidencias | sí, por estado | solicitud, aprobación, efecto en nómina, soporte | Fase 2 |
| Contratos | sí, con vencimientos | vigencia, terminación, cláusulas | Fase 2 |
| Nómina | sí, con pagos pendientes | devengos, deducciones, neto, base de cálculo | Fase 3 |
| Estudiantes | sí | expediente, representantes, matrículas, notas | Fase 4 |
| Calificaciones | sí, por grupo | período, grupo, promedio por materia, estudiantes | Fase 4 |
| Configuración | sí | parámetro completo | Fase 5 |

Las fichas leen el espejo local y no escriben: la autoridad sigue siendo el nodo
central. Con esto la **cobertura de consulta de los datos replicados es total**;
lo que resta es la escritura y las acciones de negocio, fase por fase.

Dos cosas no están y no pueden estar en esta capa: **cuentas de usuario** y
**auditoría** no se replican (solo existen en el nodo central) y la consulta de
respaldos del PC no tiene equivalente móvil. La pantalla de Configuración
muestra los parámetros institucionales replicados y las Fases 5 y 6 cubren el
resto con llamadas de solo lectura al servidor.

### Fase 0 — Fundación (bloqueante de todo lo demás)
- `ui/navegacion`: grafo con inicio de sesión ya existente + «cajón» de módulos.
- `ui/comun`: lista con búsqueda, ficha en secciones, formulario con validación,
  estado vacío, estado offline, estados de carga y error.
- `PoliticaRoles` aplicado a acciones (crear/editar/aprobar/cerrar) y a la
  visibilidad de cada módulo, igual que `MODULE_ACCESS` del escritorio.
- Formato único de fechas, moneda y cédula.

### Fase 1 — Personal
Empleados (lista, búsqueda, ficha, alta, edición, baja lógica, exportar) y
Documentos (vencimientos, archivo adjunto, descarga, alta/edición/baja).
**Lista y ficha ya entregadas**; falta la escritura.

### Fase 2 — Operación laboral
Incidencias (alta con soporte, aprobar/rechazar con nota) y Contratos
(alta, renovar, terminar, vencimientos).

### Fase 3 — Nómina
Periodos, generación y resumen contra el servidor, detalle por empleado,
marcar pagado, descarga de recibo y planilla. **El cálculo no se reimplementa
en el teléfono**: se pide al servidor, que es la única fuente de verdad del
dinero.

### Fase 4 — Académico
Estudiantes, periodos, grados, matrículas, notas (individual y por lote),
consolidado, boletín, acta, cierre/reapertura y tokens académicos.

### Fase 5 — Administración
Usuarios (alta, edición, desbloqueo), auditoría, datos de la institución y
estado de respaldos (solo consulta).

### Fase 6 — Cierre de paridad
Exportaciones, fotos, accesibilidad, pruebas instrumentadas por módulo y
revisión de la matriz contra el escritorio.

---

## 4. Decisiones de arquitectura

1. **El servidor manda en lo que no se puede recalcular**: nómina, renovación y
   terminación de contratos, aprobación de incidencias, cierre de periodos y
   tokens académicos se ejecutan en el nodo central. La app envía la petición y
   refleja la respuesta.
2. **Offline-first**: lecturas desde Room; escrituras locales + cola de salida
   en la misma transacción. Un formulario enviado sin red queda pendiente y se
   sincroniza solo.
3. **Sin reglas duplicadas**: ninguna fórmula de nómina, numeración de contratos
   ni cierre de actas se reimplementa en Kotlin.
4. **PDF e informes**: se generan en el servidor (`/archivos/pdf/{tipo}`) y se
   descargan; el teléfono solo los abre o los guarda.
5. **Permisos**: `PoliticaRoles` decide en la UI **y** en el repositorio; el
   servidor vuelve a validar en las acciones (`_autorizar_escritura`).
6. **Un módulo por fase**: nada de pantallas vacías ni botones sin acción.

---

## 5. Criterios de aceptación por módulo

- Un usuario de cada rol ve exactamente lo que su rol permite (y el repositorio
  lo impide aunque la UI se equivoque).
- Con el nodo apagado: listar, buscar, ver ficha y crear/editar funciona; la
  operación queda en cola y se confirma al volver la red.
- Sin pérdida ni sobrescritura: dos teléfonos que editan columnas distintas
  conservan ambas ediciones.
- Cada acción autoritativa refleja en pantalla lo que respondió el servidor.
- Los archivos se verifican por hash antes de mostrarse.
- Pruebas unitarias del ViewModel y de la regla de permisos de cada módulo.
