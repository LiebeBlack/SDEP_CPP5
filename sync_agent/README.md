# Agente de Sincronización de Datos (SDEP-CPP5)

Paquete **independiente** que replica de forma bidireccional los datos del
Sistema de Gestión de Personal entre los puestos de la intranet de un colegio
y un nodo central. Funciona en segundo plano, no bloquea la interfaz y —lo más
importante— **nunca deja de escribir en el SQLite local**: si se cae la red, el
usuario sigue trabajando y sus cambios quedan encolados con su marca de tiempo.

```
py -3 -m sync_agent init        # prepara este equipo
py -3 -m sync_agent agente      # sincroniza en segundo plano
py -3 -m sync_agent estado      # resumen del equipo
```

---

## 1. Qué se replica y qué no

| Tabla | Se replica | Notas |
|---|---|---|
| `empleados` | Sí | Clave natural: `cedula`. Borrado lógico (`activo`) |
| `documentos` | Sí | Metadatos siempre; el archivo viaja si no supera el límite |
| `incidencias` | Sí | Igual que documentos (soporte adjunto) |
| `contratos` | Sí | Clave natural: `numero` |
| `pagos` | Sí | Los importes son el caso que más conflictos genera (ver §4) |
| `configuraciones` | Parcial | Se replica, **salvo** las preferencias de cada puesto |
| `usuarios` | **No** | Cada puesto administra sus propias cuentas |

Tampoco viajan las preferencias locales: `apariencia_modo`, `backup_enabled`,
`backup_interval_hours`, `audit_enabled` y cualquier clave `sync_*`. Tema
visual, respaldos y ajustes del agente son decisiones de cada equipo, no datos
institucionales.

Las **rutas locales** de archivos (`foto_ruta`, `ruta_archivo`,
`contratos.archivo_ruta`) no se replican: apuntan a una carpeta de este
computador. El contenido en sí sí viaja, identificado por su hash.

---

## 2. Cómo funciona por dentro

```
        puesto A                     nodo central                    puesto B
  ┌──────────────────┐            ┌──────────────────┐          ┌──────────────────┐
  │ SQLite local     │            │ SQLite central   │          │ SQLite local     │
  │  (escritura      │  push ───▶ │  (único escritor)│ ◀─── push│  (escritura      │
  │   SIEMPRE)       │            │  seq autoritativo│          │   SIEMPRE)       │
  │  journal + marcas│ ◀── pull ─ │  log de ops      │ ── pull ─▶│  journal + marcas│
  └──────────────────┘            └──────────────────┘          └──────────────────┘
        captura del ORM                mezcla por campo              captura del ORM
```

* **Captura**: un enganche a los eventos de `Session` anota qué cambió antes de
  que el ORM vuelva a la base. La operación se guarda en el journal **en la
  misma transacción** que el dato: si la transacción se deshace, la operación
  tampoco se anuncia (nunca se replica algo que no se confirmó).
* **Identidad global**: cada fila recibe un UUID (`sync_ids`). Así el mismo
  empleado creado en dos puestos es una sola fila, unida por su **clave
  natural** (`empleados.cedula`, `contratos.numero`, `configuraciones.clave`).
* **Mezcla por campo**: dos puestos que editan columnas distintas del mismo
  registro conservan **ambas** ediciones. Solo cuando tocan la misma columna hay
  un ganador y un conflicto registrado.
* **Nodo central**: único escritor de la base compartida, con su `seq` global.
  Los puestos nunca escriben en él de forma directa.

### Offline y online

El agente nunca espera a la red para dejar escribir al usuario. Un ciclo dura
milisegundos si no hay nada que hacer, y la espera es interrumpible (el botón
«Sincronizar ahora» despierta el hilo, no lo reinicia). Si el nodo central no
responde, la espera crece: 30 s, 60 s, 120 s… hasta 5 minutos, con algo de azar
para que todos los puestos del colegio no golpeen el servidor a la vez cuando
vuelve la red.

---

## 3. Puesta en marcha

### 3.1 En el nodo central (una sola vez)

```bash
# Crea la base central y arranca el servicio (por defecto, puerto 8765)
py -3 -m sync_agent servidor --db sqlite:///central.db --host 0.0.0.0 --puerto 8765

# En otra consola: da de alta cada puesto y guarde el token que se muestra
py -3 -m sync_agent dispositivos --db sqlite:///central.db --crear "Secretaría"
```

El token **solo se muestra una vez**: en la base queda su hash (PBKDF2). Si se
pierde, revoque el puesto y cree otro.

```bash
py -3 -m sync_agent dispositivos --db sqlite:///central.db --listar
py -3 -m sync_agent dispositivos --db sqlite:///central.db --revocar <ID>
py -3 -m sync_agent servidor --db sqlite:///central.db --purgar-historial 180
py -3 -m sync_agent servidor --db sqlite:///central.db --exportar-conflictos conflictos.json
```

Con certificado propio (intranet con TLS):

```bash
py -3 -m sync_agent servidor --db sqlite:///central.db --cert servidor.pem --key servidor.key
```

### 3.2 En cada puesto

Desde la aplicación: **Configuración → Sincronización** (solo administradores).
Se pegan la dirección del servidor, el token y el identificador del equipo que
entregó el administrador, se marca «Sincronizar este equipo con la intranet» y
se guarda. La propia pantalla ofrece «Probar conexión», los contadores de
pendientes y conflictos, y «Adoptar datos existentes».

O por consola, si se prefiere automatizar el despliegue:

```bash
set SDP_SYNC_ACTIVADO=true
set SDP_SYNC_URL=http://servidor-central:8765
set SDP_SYNC_TOKEN=<token>
set SDP_SYNC_EQUIPO=Secretaría
py -3 -m sync_agent init
py -3 -m sync_agent agente
```

### 3.3 Adoptar los datos que ya existían

Un puesto que ya venía trabajando tiene empleados, documentos y pagos cargados
**antes** de que existiera el agente. Nadie los ha modificado desde entonces, así
que nada los anunciaría al resto de la red: `adoptar_existentes()` les da
identidad global y una operación base que los pone en circulación. Es seguro
repetirlo (es idempotente) y no modifica ningún dato.

Se ejecuta solo, la primera vez que se activa la sincronización, y también a
mano con `py -3 -m sync_agent init` o con el botón «Adoptar datos existentes».

---

## 4. Conflictos: nada se descarta en silencio

Cuando dos puestos escriben **el mismo campo** del mismo registro, se elige un
ganador con un orden total y determinista —`(momento, equipo, operación)`— y el
valor perdedor queda en la bandeja de conflictos con la regla aplicada. Como el
orden es total, **todos los nodos eligen al mismo ganador sin importar el orden
en que lleguen las operaciones**: el sistema converge.

Dos escrituras se consideran simultáneas si difieren en menos de 2 segundos
(los relojes de dos computadores nunca están perfectamente sincronizados); en
ese caso desempata el identificador del equipo, que es estable.

Los campos económicos (`salario_base`, montos de pago, salario pactado) generan
conflicto **aunque gane el valor remoto**: un cambio de salario que se pisa
merece poder auditarse.

```bash
py -3 -m sync_agent conflictos            # pendientes de revisión
py -3 -m sync_agent conflictos --todos    # incluye los ya revisados
py -3 -m sync_agent conflictos --json
```

### Borrados

Un borrado es una escritura más: gana el más reciente. Pero una **edición
posterior a un borrado revive la fila** —perder un dato recién editado es peor
que resucitar un registro borrado por error— y la decisión queda registrada. En
`empleados`, `documentos` e `incidencias` el «borrado» del sistema es lógico
(`activo = 0`); en `pagos` y `contratos` es físico.

---

## 5. Archivos y binarios

Los binarios (`documentos.contenido_binario`,
`incidencias.documento_soporte_binario`) se replican como **hash + tamaño**
siempre, y el contenido real se transfiere solo si no supera el límite
configurado (5 MB por defecto, `SDP_SYNC_BINARIO_MAX` o el campo de la
pantalla). Así una digitalización pesada no bloquea el ciclo ni llena la
intranet; su ficha, su nombre y su hash llegan igual.

Los archivos se guardan deduplicados por hash en el nodo central, lo que hace
que reenviar un lote sea siempre seguro.

---

## 6. Privacidad y seguridad

* El token se guarda **hasheado** (PBKDF2 vía `SecurityValidator`); nunca se
  puede recuperar, solo reemplazar.
* El nodo central exige el token en cada petición (cabeceras `Authorization`
  y `X-Dispositivo`) y aplica un límite de peticiones por minuto.
* **TLS es opcional pero recomendable**: sin certificado, el token viaja en
  claro por la intranet.
* La sincronización respeta el aislamiento por puesto: cada equipo solo recibe
  lo que corresponde a su token y puede revocarse en cualquier momento.
* Las operaciones se registran en la auditoría del sistema
  (`AuditEventType.SYNC_ACTIVITY`) y en la bitácora del nodo central.

---

## 7. Diagnóstico

| Síntoma | Qué mirar |
|---|---|
| «Sincronización: inactiva» en la barra de estado | Falta dirección, token o identificador; la pestaña de Sincronización los enumera |
| «token rechazado» | El token no coincide o el puesto fue revocado: vuelva a darlo de alta |
| «sin conexión» | El servicio del nodo central no responde o el puerto está bloqueado |
| Pendientes que no bajan | Revise el registro (`logs/`) y `py -3 -m sync_agent estado` |
| Conflictos que se acumulan | Son escrituras que compitieron: revíselos con `conflictos` |

```bash
py -3 -m sync_agent estado --json    # configuración, pendientes, cursor, desfase de reloj
py -3 -m sync_agent agente --una-vez # un solo ciclo, útil para probar
```

---

## 8. Código

| Módulo | Responsabilidad |
|---|---|
| `comun.py` | Utilidades puras: UUID, hash, serialización con etiquetas de tipo |
| `registro.py` | Descripción declarativa de qué se replica de cada tabla |
| `merge.py` | Motor de mezcla (**funciones puras**, sin base de datos) |
| `esquema.py` | Tablas propias del agente (journal, identidad, marcas, blobs) |
| `identidad.py` | Traducción entre identidad global (UUID) e ids locales |
| `captura.py` | Enganche al ORM: journal por evento, en la misma transacción |
| `aplicador.py` | Aplica lo que llega de la red (lo comparten cliente y servidor) |
| `cliente.py` | Cliente HTTP (biblioteca estándar) del protocolo |
| `agente.py` | Hilo de fondo: ciclo, reintentos, estado observable |
| `servidor.py` | Nodo central: servicio HTTP y su lógica |
| `config.py` | Configuración por equipo (config.json + variables de entorno) |
| `__main__.py` | Interfaz de línea de comandos |

Pruebas: `tests/test_sync_merge.py`, `test_sync_captura.py`,
`test_sync_agente.py`, `test_sync_servidor.py` y `test_sync_integracion.py`.
