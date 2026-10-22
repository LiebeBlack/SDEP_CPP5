# SDEP Móvil — aplicación Android del Sistema de Gestión de Personal

Aplicación nativa en Kotlin para que el personal de supervisión levante registros
de campo desde el teléfono y estos lleguen al sistema de escritorio. **No es un
sistema aparte**: se conecta al nodo central de sincronización del proyecto
Python (`sync_agent`) como un puesto más, con su token y su identificador de
equipo, y escribe en la tabla `registros_moviles` de la base institucional.

```
┌──────────────────┐        HTTP /api/v1        ┌──────────────────┐
│  SDEP Móvil      │  ping · push · pull        │  Nodo central    │
│  (Android)       │ ─────────────────────────▶ │  (Python)        │
│  Room + cola     │ ◀───────────────────────── │  SQLite + seq    │
│  offline         │  operaciones + cursor      │  merge por campo │
└──────────────────┘                            └────────┬─────────┘
                                                         │
                                              ┌──────────▼─────────┐
                                              │ Puestos de escritorio│
                                              │ SQLite + PySide/CTk │
                                              └────────────────────┘
```

## 1. Qué hace

- **Ingreso** con usuario y contraseña (PBKDF2-HMAC-SHA256, 120 000 iteraciones,
  sal aleatoria) o con huella/rostro/credencial del dispositivo.
- **Tres roles**: administrador (todo), editor (crear y editar) y consulta (solo
  lectura). La interfaz oculta lo que el rol no permite y el repositorio vuelve a
  comprobarlo antes de escribir.
- **CRUD completo de registros**: título, contenido, categoría, valor numérico,
  marcas de tiempo y estado de sincronización; búsqueda, filtro por categoría y
  borrado lógico con confirmación.
- **Funciona sin red**: cada cambio se guarda en Room y deja su operación en una
  cola de salida, en la misma transacción.
- **Consulta de todos los módulos del escritorio**: panel de control y listas y
  fichas de empleados, documentos, incidencias, contratos, nómina, estudiantes,
  calificaciones y configuración, filtradas por la misma matriz de roles. Leen
  la copia local, así que funcionan sin red; la escritura sigue en el escritorio.
- **Sincronización** con el nodo central: envío por lotes, recepción por cursor,
  reintentos con espera creciente (WorkManager) y bandeja de conflictos.
- **Material 3** con modo claro y oscuro, vinculación automática al escritorio
  y prueba de conexión con detección de desfase de reloj.

## 2. Requisitos

| Elemento | Versión |
|---|---|
| Android mínimo | 8.0 (API 26) |
| Android objetivo | 14 (API 34) |
| JDK para compilar | 17 |
| Gradle | 8.7 (lo descarga el wrapper) |
| Android Gradle Plugin | 8.5.2 |
| Kotlin | 1.9.24 |
| Compose BOM | 2024.06.00 |

## 3. Compilar e instalar

```bash
cd android
./gradlew :app:assembleDebug          # APK de depuración
./gradlew :app:testDebugUnitTest      # pruebas unitarias
```

El APK queda en `app/build/outputs/apk/debug/app-debug.apk`. Para instalarlo:

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Para distribución institucional, genere un keystore y firme la variante
`release` (`isMinifyEnabled` y `isShrinkResources` ya están activos):

```bash
keytool -genkeypair -v -keystore sdep-movil.jks -alias sdep -keyalg RSA \
        -keysize 2048 -validity 10000
```

> El proyecto se abre directamente en Android Studio (Giraffe o posterior). La
> primera sincronización descarga Gradle 8.7 y las dependencias.

## 4. Conectar el teléfono con el sistema Python

### 4.1 En el equipo que hará de nodo central

No hay que ejecutar nada a mano. La aplicación de escritorio abre el nodo
central (puerto 8765/TCP) y su difusión de descubrimiento (8766/UDP) al
arrancar. El instalador crea las reglas de firewall para redes privada y de
dominio; si se ejecuta desde el código fuente, hay que permitir esos puertos.

### 4.2 En el teléfono

1. Abra SDEP Móvil en la misma Wi-Fi que el escritorio.
2. Escriba su usuario y contraseña de la institución. **No hay nada que
   configurar**: la app descubre el escritorio por difusión UDP y, si la red la
   bloquea, sondea la subred; después pide el alta como puesto y guarda el
   token cifrado.
3. Si el equipo aún no aparece, pulse **Volver a buscar** en el aviso de la
   pantalla de ingreso. La app sigue intentando en segundo plano.
4. Al entrar, los registros creados en el teléfono aparecen en la base central
   y, desde allí, en todos los puestos de escritorio.

> Si el escritorio se reinstala o cambia de IP, **Ajustes → Sistema de
> escritorio → Buscar de nuevo** repite el descubrimiento. La app también se
> reempareja sola cuando el nodo rechaza el token del equipo.

### 4.3 Comprobar del lado Python

```bash
# Registros que llegaron del teléfono
py -3 -c "import sqlite3;c=sqlite3.connect('sync_central.db');print(c.execute('select titulo,categoria,valor,dispositivo from registros_moviles where activo=1').fetchall())"

# Operaciones aplicadas y conflictos
py -3 -m sync_agent estado --db sync_central.db
py -3 -m sync_agent conflictos --db sync_central.db
```

## 5. Contrato con el nodo central

La app usa los mismos tres puntos que el agente de escritorio, con las cabeceras
`Authorization: Bearer <token>` y `X-Dispositivo: <equipo>`:

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/api/v1/ping` | Versión del protocolo, hora del servidor y tablas |
| `POST` | `/api/v1/push` | Lote de hasta 200 operaciones |
| `GET` | `/api/v1/pull?cursor=N&limite=200` | Novedades posteriores al cursor |

Una operación viaja así (el `payload` es **texto JSON**, igual que lo almacena y
lo devuelve el servidor):

```json
{
  "op_id": "8d1f…",
  "tabla": "registros_moviles",
  "fila_uuid": "1c9e…",
  "operacion": "upsert",
  "payload": "{\"uuid_movil\":\"1c9e…\",\"titulo\":\"Visita 4to B\",\"actualizado_en\":\"2026-10-21T13:05:00\"}",
  "dispositivo": "movil-secretaria",
  "usuario": "ana",
  "creado_en": "2026-10-21T13:05:00"
}
```

### 5.1 Tabla `registros_moviles`

Definida en [`src/models/registro_movil.py`](../src/models/registro_movil.py) y
registrada para sincronización en [`sync_agent/registro.py`](../sync_agent/registro.py).

| Columna | Tipo | Nota |
|---|---|---|
| `uuid_movil` | texto(36) | Clave natural e identidad global |
| `titulo` | texto(200) | Obligatorio |
| `contenido` | texto | Descripción libre |
| `categoria` | texto(60) | Por omisión `general` |
| `valor` | real | Importe, cantidad o medición |
| `creado_en` / `actualizado_en` | fecha | UTC sin zona |
| `dispositivo` / `usuario` | texto | Quién y desde dónde se capturó |
| `activo` | entero | Borrado lógico |

### 5.2 Regla de oro: se envían solo los campos tocados

En un alta viajan todas las columnas no nulas. En una edición viajan únicamente
las que cambiaron, más `uuid_movil`. Si el teléfono mandara la fila completa,
pisaría las columnas que otro equipo editó mientras tanto y el motor de mezcla
por campo del nodo central no tendría nada que mezclar. Esta regla la fija
`RegistroRepositorio.guardar` y la reproduce la prueba
[`tests/test_registros_moviles.py`](../tests/test_registros_moviles.py).

## 6. Arquitectura

```
app/src/main/java/ve/edu/sdep/movil/
├── SdepApplication.kt          Hilt + WorkManager bajo demanda
├── MainActivity.kt             FragmentActivity (necesaria para BiometricPrompt)
├── dominio/
│   ├── modelo/                 Registro, Sesion, Rol, Permiso, ConfiguracionSync
│   └── PoliticaRoles           matriz de permisos comprobable
├── datos/
│   ├── local/                  Room: entidades, DAO, base de datos, fechas
│   ├── remoto/                 DTO del protocolo, Retrofit, fábrica con cabeceras
│   ├── repositorio/            Autenticación, registros, sincronización, sesión
│   └── seguridad/              PBKDF2, bóveda cifrada, BiometricPrompt
├── di/                         módulos de Hilt (base de datos y red)
├── sincronizacion/             trabajador y programador de WorkManager
└── ui/                         tema, navegación, login, registros, módulos (consulta),
                                ajustes, conflictos
```

- **Offline-first:** la escritura local manda; la red es un replicador.
- **Transacción única:** registro + operación de cola se escriben juntos. Si la
  transacción falla, no queda ni el dato ni el anuncio.
- **Un solo candado de sincronización:** la periódica y el botón manual no se
  pisan.
- **Estado en `StateFlow`:** las pantallas no consultan la base a mano; observan.

## 7. Seguridad

| Riesgo | Medida |
|---|---|
| Robo de la base local | Contraseñas con PBKDF2 + sal; tokens con SHA-256 |
| Robo del teléfono | Sesión solo en memoria; al cerrar la app hay que entrar |
| Token del nodo legible | `EncryptedSharedPreferences` con clave en el Keystore |
| Suplantación por huella | El sensor solo desbloquea una llave aleatoria, no la contraseña |
| Pantalla bloqueada por rol | `PoliticaRoles` en UI **y** en el repositorio |
| Respaldo automático | `allowBackup=false` y reglas de exclusión total |
| Red local sin TLS | Aviso en la documentación y opción de certificado propio |

No se guarda la contraseña en ningún momento. El token biométrico se genera con
dos UUID (256 bits de entropía), se guarda hasheado en Room y en claro solo en la
bóveda cifrada.

## 8. Sincronización y conflictos

1. **Push** de la cola (lotes de 200). El servidor responde qué aplicó y qué
   rechazó; lo aplicado se borra de la cola, lo rechazado se conserva con motivo.
2. **Pull** desde el cursor guardado, página a página, hasta que `hay_mas` sea
   falso. El cursor se persiste tras cada página.
3. **Aplicación local** de lo recibido, con dos protecciones:
   - si el registro tiene cambios propios sin enviar, **no se pisa**: se anota el
     choque y la operación propia sigue en cola (el nodo central decidirá);
   - si la escritura remota es más antigua que la local, se anota y se descarta.
4. **Nada se descarta en silencio**: los choques quedan en **Ajustes →
   Conflictos**, con el valor de cada lado y la fecha.

El nodo central sigue siendo el árbitro: allí se mezcla campo por campo y se
registran los conflictos del sistema completo. El teléfono no reimplementa ese
árbitro; conserva su trabajo y señala las diferencias.

## 9. Pruebas

```bash
./gradlew :app:testDebugUnitTest
```

| Archivo | Qué fija |
|---|---|
| `HashContrasenaTest` | Derivación, sal, comparación en tiempo constante, formato inválido |
| `PoliticaRolesTest` | Matriz completa de permisos y degradación de roles desconocidos |
| `FechasTest` | Ida y vuelta sin zona horaria y tolerancia a formatos del servidor |
| `ProtocoloTest` | Nombres `snake_case`, `payload` como texto, respuestas de push/pull |
| `CatalogoTest` | Vencimientos y avisos del panel, búsqueda y ficha del empleado |

Del lado Python, `tests/test_registros_moviles.py` comprueba el mismo contrato:
columnas que envía el móvil, alta desde el teléfono, unificación por clave
natural, mezcla por campo, borrado lógico e idempotencia.

## 10. Limitaciones conocidas

- **Los módulos son de solo consulta.** El teléfono ya replica las doce tablas
  del escritorio y los muestra todos (panel, empleados, documentos,
  incidencias, contratos, nómina, estudiantes, calificaciones y configuración),
  pero todavía no permite crear, editar, aprobar ni marcar pagos: eso se hace en
  el escritorio y llegará por fases (ver `PARIDAD_ESCRITORIO.md`).
- **Cuentas y auditoría no se replican.** Viven solo en el nodo central; la
  pantalla de Configuración muestra los parámetros institucionales replicados.
- **La pantalla de conflictos no edita.** Muestra qué se pisó y permite marcarlo
  como revisado; la corrección se hace en el registro.
- **Sin recuperación de contraseña.** Las cuentas son locales; un administrador
  crea otra cuenta si alguien la olvida. No hay correo ni servidor de identidad.
- **TLS opcional.** La intranet suele usar HTTP; con certificado propio la app
  confía en las anclas del sistema y en las que instale el administrador.
- **Periodo mínimo de 15 minutos** para la sincronización en segundo plano: es el
  límite que impone Android a WorkManager. El botón manual no tiene ese límite.

## 11. Diagnóstico

| Síntoma | Causa probable | Solución |
|---|---|---|
| «No se encontró el sistema de escritorio» | Servicio apagado o teléfono en otra red | Abrir la aplicación de escritorio; pulsar «Volver a buscar» |
| «Sin conexión con el nodo central» | El equipo cambió de IP o se cerró el servicio | «Buscar de nuevo» en Ajustes; la app se reempareja sola |
| «El token no es válido o fue revocado» | El nodo se reinstaló o el puesto fue revocado | Se renueva automáticamente; si persiste, «Buscar de nuevo» |
| «La dirección no corresponde al nodo central (404)» | Un servicio ajeno ocupa el puerto 8765 | Liberar el puerto; la app descarta hosts que no se identifican |
| Aviso de reloj desfasado | Hora del teléfono muy adelantada | Activar hora automática; un reloj adelantado gana conflictos |
| Cambios que no llegan | Sincronización desactivada en Ajustes | Activar el interruptor (se guarda al instante) |
| Conflictos que se acumulan | Dos equipos editaron el mismo campo | Revisarlos y corregir el registro |
