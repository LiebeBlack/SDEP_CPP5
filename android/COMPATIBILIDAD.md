# Compatibilidad de datos: escritorio ↔ Android

Auditoría del 22/10/2026 sobre el código, no sobre una ejecución (ver
«Verificación»). Responde a una pregunta concreta: **¿el teléfono guarda
exactamente los mismos datos y aplica las mismas reglas que la PC?**

## 1. Cobertura por tabla

Se compararon las columnas de cada modelo SQLAlchemy (`src/models/*.py`) con las
de su entidad Room (`EntidadesEspejo.kt`, `RegistroEntity.kt`). El conteo incluye
`id`, `created_at` y `updated_at`, que el escritorio aporta desde `BaseModel`.

| Tabla | Escritorio | Android | Faltan | Extras deliberados |
|---|---:|---:|---|---|
| `empleados` | 45 | 45 | — | — |
| `documentos` | 17 | 18 | — | `contenido_hash` (binario por hash) |
| `incidencias` | 22 | 23 | — | `documento_soporte_hash` (binario por hash) |
| `contratos` | 22 | 22 | — | — |
| `pagos` | 37 | 37 | — | — |
| `configuraciones` | 9 | 9 | — | — |
| `estudiantes` | 16 | 16 | — | — |
| `periodos_academicos` | 10 | 10 | — | — |
| `grados` | 9 | 9 | — | `profesor_uuid` en lugar de `profesor_id` |
| `matriculas` | 8 | 8 | — | — |
| `notas_finales` | 9 | 9 | — | — |
| `registros_moviles` | 13 | 13 equivalentes | — | columnas locales de captura |

**Ninguna columna del escritorio falta en el teléfono.** Las tres diferencias son
intencionadas y están explicadas en el código:

- **Hashes de binarios.** El contenido de un archivo no viaja dentro del JSON:
  viaja por el canal de blobs identificado por SHA-256. El teléfono guarda la
  huella para saber qué bajar; por eso tiene una columna más que el escritorio.
- **`profesor_uuid`.** Los usuarios no se replican (cada puesto administra los
  suyos). La asignación de docente viaja como UUID global y el teléfono no la
  edita, tal como documenta `GradoEntity`.
- **`registros_moviles`.** La tabla local de captura conserva `uuid`, `estado`,
  `eliminado` y `ultimaSync` para la cola y la interfaz; el payload usa los
  nombres y reglas del escritorio (`uuid_movil`, `activo`, fechas ISO).

Quedan fuera de la replicación, a propósito: `usuarios` y `tokens_sesion`.

## 2. Tipos

No hay conversión silenciosa: cada tipo del escritorio tiene una representación
declarada en el teléfono y se traduce en `Espejo.payload` / `Espejo.aplicar`.

| Escritorio | Android | Nota |
|---|---|---|
| `Decimal(10,2)` | `Double` | Los importes ya vienen calculados por el servidor |
| `Date` / `DateTime` | `String` ISO 8601 | Comparable y ordenable; sin zona horaria |
| `Boolean` | `Int` (0/1) | Igual que SQLite en el escritorio |
| `Enum` | `String` | El valor textual del enum |
| `Text` | `String?` | — |

## 3. Reglas del protocolo

Las reglas viven en `sync_agent/registro.py` y su espejo es
`datos/local/Espejo.kt`. Se compararon una por una:

| Regla | Escritorio | Android |
|---|---|---|
| Clave natural de una columna | `cedula`, `numero`, `clave`, `uuid_movil`, `nombre` | Igual |
| Clave natural compuesta | `grados`, `matriculas`, `notas_finales` | Igual |
| Borrado lógico | `empleados`, `documentos`, `estudiantes`, `matriculas`, `registros_moviles` | Igual, con `activa` en matrículas |
| Columnas blob | `documentos.contenido_binario`, `incidencias.documento_soporte_binario` | Igual, por hash |
| Rutas locales que no viajan | `foto_ruta`, `ruta_archivo`, `documento_soporte_ruta`, `archivo_ruta` | Igual |
| Preferencias locales | `apariencia_modo`, `backup_*`, `audit_enabled`, prefijo `sync_` | **Corregido en esta auditoría** |
| `id` local nunca viaja | Sí | Igual |
| Foráneas como UUID | Sí | Igual |

La última fila era una divergencia real: el teléfono no filtraba las
preferencias del puesto al construir un payload de `configuraciones`. Hoy no se
escriben configuraciones desde el móvil, así que no había efecto visible, pero
habría enviado el tema visual o los respaldos del teléfono a toda la intranet en
cuanto existiera la pantalla de edición. `Espejo.esConfiguracionLocal` aplica
ahora la misma lista y el mismo prefijo que el escritorio.

## 4. Verificación

- Comparación estática de las columnas de los 12 modelos contra las 12 entidades
  Room, tabla por tabla.
- Pruebas nuevas: `EspejoTest` (preferencias locales) y `CatalogoTest` (listas,
  fichas y vencimientos). **No se ejecutaron**: la entrega se hizo sin compilar
  ni correr pruebas, por indicación expresa.
- Lo que esta auditoría no puede demostrar por sí sola: que la app compile y que
  el nodo acepte cada payload. Eso exige `./gradlew :app:testDebugUnitTest` y una
  sincronización real entre un puesto y el teléfono.

## 5. Qué falta para la paridad funcional

La compatibilidad de datos está cubierta y la **escritura ya funciona para
Empleados**: la cola genérica `operaciones_pendientes` guarda la operación en la
misma transacción que la ficha, con el payload del protocolo y las marcas de
mezcla locales. El resto de módulos sigue en consulta.

Para completar la paridad hace falta:

1. Repetir el patrón de `EmpleadoRepositorio` en documentos, incidencias,
   contratos, estudiantes, matrículas y notas (cada uno con sus claves
   foráneas resueltas a UUID y sus validaciones).
2. Formularios móviles para esos módulos, con la misma matriz de permisos.
3. Acciones de negocio contra `/api/v1/acciones` (nómina, incidencias,
   contratos, académico), que ya existen en el nodo y no se reimplementan.
4. Exportaciones y archivos adjuntos (PDF/Excel y descarga de documentos).

El detalle por fases está en [PARIDAD_ESCRITORIO.md](PARIDAD_ESCRITORIO.md).
