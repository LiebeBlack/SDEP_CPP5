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
| Compatibilidad columna a columna con los modelos del escritorio | **Hecho** | [COMPATIBILIDAD.md](COMPATIBILIDAD.md) |
| Formulario dinámico por esquema (`PRAGMA table_info`) | **Hecho** | `datos/local/EsquemaTabla.kt` |
| Escritura genérica con identidad, marcas y cola | **Hecho** | `datos/repositorio/TablaRepositorio.kt` |
| Portada por categorías y listas de tablas académicas | **Hecho** | `ui/inicio`, `ui/tablas`, `ui/formulario` |
| Panel de control y Configuración del escritorio | **Retirados del teléfono** | decisión de producto |

La app **no necesita un canal nuevo**: las lecturas salen del espejo local y las
escrituras se encolan en la misma transacción que el dato (offline-first).

---

## 2. Matriz de paridad

| Módulo escritorio | Capacidades que hay que replicar | Datos en el teléfono | Acción autoritativa en el servidor | Falta en Android |
|---|---|---|---|---|
| **Panel** | Indicadores, avisos de vencimientos, gráficos | Sí (consultas locales) | `GET /consultas/dashboard` | **No aplica**: panel del escritorio retirado del menú móvil |
| **Empleados** | Listar, buscar, ficha completa, alta, edición, baja lógica, documentos del empleado, exportar | Sí (`empleados`, `documentos`, `blobs`) | — (push) | CRUD **hecho**; exportaciones y foto, fase de cierre |
| **Documentos** | Listar, vencidos/por vencer, alta, edición, baja, descarga | Sí (metadatos + blob) | `/archivos/subir`, `/blob/{hash}` | CRUD de metadatos **hecho**; carga de archivo desde el teléfono, pendiente |
| **Incidencias** | Listar, filtrar por estado, alta, edición, baja, aprobar, rechazar | Sí | `POST /acciones/incidencias/{id}/aprobar`, `/rechazar` | CRUD **hecho**; aprobar/rechazar siguen en el servidor |
| **Contratos** | Listar, vencimientos, alta, edición, renovar, terminar, PDF | Sí | `POST /acciones/contratos/{id}/renovar`, `/terminar` | CRUD **hecho**; renovar/terminar/PDF en el servidor |
| **Nómina** | Registros de pago, detalle por empleado, marcar pagado, recibo y planilla PDF | Sí (`pagos`) | `POST /acciones/nomina/generar`, `/resumen`, `/pagos/{id}/pagado` | Registros editables **hecho**; cálculo, pago y PDF en el servidor |
| **Configuración** | Usuarios, auditoría, institución, preferencias, respaldos | Parcial (usuarios **no** se replican) | `/admin/usuarios`, `/consultas/auditoria` | **No aplica**: panel del escritorio eliminado del teléfono |
| **Estudiantes** | Listar, buscar, legajo, alta, edición, baja, exportar | Sí | — (push) | CRUD **hecho**; exportaciones pendientes |
| **Calificaciones** | Períodos, grados y secciones, matrículas, notas, consolidado, boletín, acta | Sí (salvo tokens) | `/acciones/academicos/...` | CRUD de notas, períodos, grados y matrículas **hecho**; consolidados y actas en el servidor |

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

### Estado de esta entrega: gestión dinámica de las diez tablas

La portada (`ui/inicio`) agrupa las soluciones en Personal, Académico,
Administración y Trabajo de campo. Cada módulo conserva su lista y su ficha; el
botón **Nuevo** y el lápiz de la ficha abren el formulario dinámico
(`ui/formulario`), que se construye con las columnas reales de la tabla. La
baja se hace desde el mismo formulario, con confirmación.

| Módulo | Lista | Ficha | Escritura |
|---|---|---|---|
| Empleados | sí | completa por secciones | **Hecha** (formulario dedicado de 40 campos) |
| Documentos | sí, con vencimientos | metadatos, archivo y huella | **Hecha** (metadatos) |
| Incidencias | sí, por estado | solicitud, aprobación, efecto en nómina, soporte | **Hecha** |
| Contratos | sí, con vencimientos | vigencia, terminación, cláusulas | **Hecha** |
| Nómina | sí, con pagos pendientes | devengos, deducciones, neto, base de cálculo | **Hecha** (registros) |
| Estudiantes | sí | expediente, representantes, matrículas, notas | **Hecha** |
| Calificaciones | sí, por grupo | período, grupo, promedio por materia, estudiantes | **Hecha** |
| Períodos, grados y matrículas | sí (`ui/tablas`) | — | **Hecha** |
| Panel y Configuración | — | — | **No aplica**: retirados del teléfono |

El formulario no tiene una copia de los campos: `EsquemaTabla` consulta
`PRAGMA table_info` y deduce el control (texto, número, fecha, sí/no, lista
cerrada o selector de registro padre). Si el escritorio agrega una columna y la
replicación la trae, aparece sola. La validación cubre obligatorios, números,
fechas, listas y claves foráneas; la unicidad y las reglas de negocio las sigue
resolviendo la base y el nodo central.

Las **acciones de negocio** que el escritorio ejecuta contra el servidor
(aprobar/rechazar incidencias, renovar/terminar contratos, generar nómina,
abrir/cerrar períodos, emitir tokens) no se reimplementan: el teléfono edita el
registro y el servidor conserva la autoridad. **Cuentas y auditoría** no se
replican y su pantalla se retiró con el resto del panel de escritorio.

**Respaldos:** el teléfono no genera copias locales. La base institucional y sus
respaldos automáticos viven en el nodo central; el teléfono replica el espejo y
lo restaura desde el servidor cuando hace falta.

### Fase 0 — Fundación (bloqueante de todo lo demás)
- `ui/navegacion`: grafo con inicio de sesión ya existente + «cajón» de módulos.
- `ui/comun`: lista con búsqueda, ficha en secciones, formulario con validación,
  estado vacío, estado offline, estados de carga y error.
- `PoliticaRoles` aplicado a acciones (crear/editar/aprobar/cerrar) y a la
  visibilidad de cada módulo, igual que `MODULE_ACCESS` del escritorio.
- Formato único de fechas, moneda y cédula.

### Fase 1 — Personal
**Entregado**: empleados, documentos e incidencias con lista, búsqueda, ficha,
alta, edición y baja desde el teléfono. Cada escritura guarda la fila y su
operación de salida en la misma transacción (cola `operaciones_pendientes` +
payload del protocolo) y pide un ciclo de sincronización inmediato.

Queda la **carga del archivo** de un documento desde el teléfono y la descarga
del binario; los metadatos y su huella ya se editan.

### Fase 2 — Operación laboral
**Entregado**: incidencias y contratos con alta, edición y baja; los
vencimientos y estados se siguen calculando en el servidor. Aprobar/rechazar
una incidencia y renovar/terminar un contrato siguen siendo acciones del nodo
central (el teléfono edita el registro que las origina).

### Fase 3 — Nómina
**Entregado**: los registros de pago se crean, editan y dan de baja con el
formulario dinámico. **El cálculo no se reimplementa en el teléfono**: generar
la nómina, marcar pagado y emitir recibo y planilla se piden al servidor, que
es la única fuente de verdad del dinero.

### Fase 4 — Académico
**Entregado**: estudiantes, períodos, grados, matrículas y calificaciones se
administran desde el teléfono (las tres últimas con `ui/tablas`). Consolidados,
boletines, actas y tokens académicos siguen en el servidor.

### Fase 5 — Administración
**No aplica en el teléfono**: usuarios, auditoría, institución, preferencias y
respaldos son el panel del escritorio y se retiraron del menú móvil. Los
respaldos automáticos los ejecuta el nodo central.

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
