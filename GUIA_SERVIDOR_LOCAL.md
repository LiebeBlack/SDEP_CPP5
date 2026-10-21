# Guía de Uso del Servidor de Sincronización en Computadora Local

Esta guía explica cómo ejecutar el servidor de sincronización en cualquier computadora sin necesidad de configuración compleja o un servidor dedicado. El servidor está configurado para aceptar conexiones desde **cualquier dispositivo en la red local**, incluyendo:

- ✅ Otras computadoras con el mismo programa
- ✅ Aplicación Android (SDEP Móvil)
- ✅ Cualquier dispositivo conectado a la misma red WiFi

## Requisitos Previos

- Python 3.8 o superior
- Las dependencias del proyecto ya instaladas (ver `requirements.txt` o usar el entorno virtual)

## Opción 1: Usar el Script de Inicialización Automática (Recomendado)

El script `iniciar_servidor.py` configura todo automáticamente:

### Inicio Básico

```bash
python iniciar_servidor.py
```

Esto:
- Crea la base de datos `sync_central.db` si no existe
- Inicializa el esquema necesario
- Crea 4 usuarios por defecto
- Crea un dispositivo por defecto
- Inicia el servidor en el puerto 8765

### Usuarios Por Defecto

El script crea estos usuarios automáticamente:

| Usuario | Contraseña | Rol | Descripción |
|---------|------------|-----|-------------|
| admin | Admin1234 | admin | Administrador total del sistema |
| manager | Gestor1234 | manager | Gestor con permisos de edición |
| user | Usuario1234 | user | Usuario estándar (lectura limitada) |
| viewer | Lector1234 | viewer | Solo lectura |

**IMPORTANTE:** Cambie estas contraseñas después del primer inicio por seguridad.

### Opciones Avanzadas

```bash
# Usar un archivo de configuración personalizado
python iniciar_servidor.py --config mi_config.json

# Solo inicializar la base de datos sin iniciar el servidor
python iniciar_servidor.py --solo-inicializar

# No crear usuarios por defecto
python iniciar_servidor.py --sin-usuarios

# No crear dispositivo por defecto
python iniciar_servidor.py --sin-dispositivo
```

## Opción 2: Usar el Módulo sync_agent

### Modo Autoconfigurado

```bash
# Iniciar servidor con configuración por defecto
py -3 -m sync_agent autoconfig

# Iniciar con usuarios por defecto
py -3 -m sync_agent autoconfig --crear-usuarios

# Iniciar con usuarios y dispositivo
py -3 -m sync_agent autoconfig --crear-usuarios --crear-dispositivo "Mi Computadora"

# Configurar puerto y host personalizados
py -3 -m sync_agent autoconfig --host 127.0.0.1 --puerto 9000 --crear-usuarios
```

### Modo Servidor Manual

```bash
# Iniciar servidor con configuración manual
py -3 -m sync_agent servidor --db sqlite:///central.db --host 0.0.0.0 --puerto 8765

# Crear un dispositivo después
py -3 -m sync_agent servidor --db sqlite:///central.db --crear-dispositivo "Puesto 1"

# Listar dispositivos registrados
py -3 -m sync_agent dispositivos --db sqlite:///central.db --listar
```

## Archivo de Configuración

Puede crear un archivo JSON para personalizar la configuración:

```json
{
  "db": "sqlite:///sync_central.db",
  "blobs": "sync_blobs",
  "host": "0.0.0.0",
  "puerto": 8765,
  "certificado": null,
  "clave": null,
  "max_ops_por_lote": 500,
  "max_bytes_peticion": 3145728,
  "max_bytes_blob": 67108864,
  "peticiones_por_minuto": 120
}
```

Luego úselo con:

```bash
python iniciar_servidor.py --config mi_config.json
```

## Conectar Clientes al Servidor

Una vez que el servidor está en ejecución, aceptará conexiones desde cualquier dispositivo en la red local. El servidor mostrará automáticamente la IP local al iniciar.

### URL de Conexión

El servidor mostrará dos URLs:

```
Desde esta computadora: http://127.0.0.1:8765
Desde otros dispositivos: http://192.168.1.XXX:8765
```

**IMPORTANTE**: Para conectar desde Android u otros equipos, use la segunda URL con la IP local (no 127.0.0.1).

### Desde la Aplicación de Escritorio (Otro PC en la Red)

1. Abra Configuración → Sincronización
2. Configure:
   - URL del servidor: `http://IP_DEL_SERVIDOR:8765` (ej: `http://192.168.1.100:8765`)
   - Token: el token que se mostró al crear el dispositivo
3. Active la sincronización

### Desde Otro Equipo

```bash
# Inicializar el cliente
py -3 -m sync_agent init

# Configurar conexión (variables de entorno)
export SDP_SYNC_URL="http://IP_DEL_SERVIDOR:8765"
export SDP_SYNC_TOKEN="TOKEN_DEL_DISPOSITIVO"
export SDP_SYNC_ACTIVADO="true"

# O configurar desde la interfaz gráfica
```

### Para Aplicación Móvil Android

La aplicación móvil usa el protocolo 2 con autenticación de usuario:

1. **Configurar la URL del servidor**:
   - Abra la app Android
   - Vaya a Configuración → Servidor
   - Ingrese la URL: `http://IP_LOCAL_DEL_SERVIDOR:8765`
   - Ejemplo: `http://192.168.1.100:8765`

2. **Autenticación de usuario**:
   - Usuario: uno de los usuarios creados (admin, manager, user, viewer)
   - Contraseña: la contraseña correspondiente
   - Ejemplo: `admin` / `Admin1234`

3. **Verificar conexión**:
   - La app debería poder hacer login
   - Ver los indicadores del dashboard
   - Sincronizar datos

**NOTA**: La IP del servidor puede cambiar si se reinicia el router o si la computadora se conecta a otra red. Verifique la IP actual ejecutando el servidor o usando `ipconfig` (Windows) o `ifconfig` (Linux/Mac).

## Script de Verificación de Red

El proyecto incluye un script auxiliar para verificar que el servidor está correctamente configurado para conexiones de red:

```bash
python verificar_red.py
```

Este script verifica:
- ✅ IP local de la computadora
- ✅ Si el puerto 8765 está en uso
- ✅ Si el servidor responde en localhost (127.0.0.1)
- ✅ Si el servidor responde en la IP local (para Android/otros PCs)

Si el servidor está correctamente configurado, mostrará:
```
✅ El servidor está correctamente configurado para red local
   Android y otros PCs deberían poder conectarse
```

Si hay problemas, el script indicará qué corregir.

## Encontrar la IP Local del Servidor

### Método 1: El Servidor la Muestra Automáticamente

Al iniciar el servidor con `python iniciar_servidor.py` o `py -3 -m sync_agent autoconfig`, el servidor mostrará:

```
URLS PARA CONEXIÓN:
  Desde esta computadora: http://127.0.0.1:8765
  Desde Android y otros equipos: http://192.168.1.100:8765
```

Use la segunda URL para conectar desde otros dispositivos.

### Método 2: Desde Windows

```cmd
ipconfig
```

Busque la sección "Adaptador de LAN inalámbrica" o "Adaptador de Ethernet" y tome la "Dirección IPv4".

### Método 3: Desde Linux/Mac

```bash
ifconfig
# o
ip addr show
```

Busque la dirección IPv4 en la interfaz de red activa (wlan0, eth0, etc.).

## Verificar que el Servidor Funciona

### Prueba con curl

```bash
# Verificar que el servidor responde
curl http://localhost:8765/api/v1/ping

# Respuesta esperada:
# {
#   "servidor": "nodo-central-sincronizacion",
#   "version_protocolo": "2",
#   "hora": "2026-10-21T12:00:00",
#   "tablas": [...],
#   "acciones": [...]
# }
```

### Login de Usuario

```bash
# Probar login
curl -X POST http://localhost:8765/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Dispositivo: equipo-test" \
  -d '{"username": "admin", "password": "Admin1234"}'
```

## Gestión del Servidor

### Ver Dispositivos Registrados

```bash
py -3 -m sync_agent dispositivos --db sqlite:///sync_central.db --listar
```

### Revocar un Dispositivo

```bash
py -3 -m sync_agent dispositivos --db sqlite:///sync_central.db --revocar ID_DISPOSITIVO
```

### Ver Sesiones Activas

```bash
py -3 -m sync_agent sesiones --db sqlite:///sync_central.db --listar
```

### Revocar Sesiones de un Usuario

```bash
py -3 -m sync_agent sesiones --db sqlite:///sync_central.db --revocar-usuario admin
```

## Consideraciones de Seguridad

### Para Uso en Red Local

1. **Cambiar contraseñas por defecto** inmediatamente
2. Usar un firewall para limitar acceso a la red local
3. Considerar usar HTTPS con certificados TLS

### Para Uso en Internet

**NO RECOMENDADO** sin configuración adicional:

1. Configurar HTTPS con certificados válidos
2. Usar una base de datos más robusta (PostgreSQL, MySQL)
3. Configurar autenticación adicional
4. Implementar rate limiting más estricto
5. Usar un servidor web reverso (nginx, Apache)

### Archivo de Configuración con TLS

```json
{
  "db": "sqlite:///sync_central.db",
  "blobs": "sync_blobs",
  "host": "0.0.0.0",
  "puerto": 8765,
  "certificado": "/ruta/a/certificado.pem",
  "clave": "/ruta/a/clave_privada.pem"
}
```

## Solución de Problemas

### El servidor no inicia

- Verifique que el puerto 8765 no esté en uso por otra aplicación
- Compruebe permisos de escritura en el directorio
- Revise el log de errores

### Los clientes no pueden conectarse

- Verifique que el firewall permita conexiones al puerto 8765 (ver sección "Configuración de Firewall")
- Use `0.0.0.0` como host para aceptar conexiones de cualquier IP
- Pruebe con `curl` desde el cliente: `curl http://IP_SERVIDOR:8765/api/v1/ping`
- Asegúrese de que todos los dispositivos estén en la misma red WiFi
- Verifique que la IP del servidor sea correcta (puede cambiar al reiniciar el router)
- Desactive temporalmente el firewall para pruebas (no recomendado en producción)

### La app Android no puede conectarse

- **Verifique que esté en la misma red WiFi**: El servidor y el Android deben estar conectados a la misma red
- **Use la IP correcta**: No use 127.0.0.1 desde Android, use la IP local del servidor (ej: 192.168.1.100)
- **Verifique el firewall**: El puerto 8765 debe estar abierto en el servidor
- **Pruebe la conexión desde otro PC**: Si otro PC en la red no puede conectarse, el problema es del servidor/firewall
- **Verifique que el servidor esté ejecutándose**: El servidor debe estar activo cuando la app intenta conectarse
- **Desactive datos móviles**: Asegúrese de que el Android esté usando WiFi, no datos móviles

- Verifique que el firewall permite conexiones al puerto 8765
- Use `0.0.0.0` como host para aceptar conexiones de cualquier IP
- Pruebe con `curl` desde el cliente: `curl http://IP_SERVIDOR:8765/api/v1/ping`

### Error de base de datos

- Asegúrese de que el directorio de la base de datos existe
- Verifique permisos de escritura
- Si hay corrupción, elimine `sync_central.db` y `sync_blobs/` y reinicie

## Configuración de Firewall (Importante para Red Local)

Para que otros dispositivos en la red puedan conectarse al servidor, el firewall debe permitir conexiones en el puerto 8765.

### Windows

```powershell
# Permitir conexiones entrantes en el puerto 8765
New-NetFirewallRule -DisplayName "SDEP Servidor Sincronización" -Direction Inbound -LocalPort 8765 -Protocol TCP -Action Allow
```

O desde la interfaz gráfica:
1. Abra "Firewall de Windows Defender con seguridad avanzada"
2. Reglas de entrada → Nueva regla
3. Puerto → TCP → Puertos locales específicos: 8765
4. Permitir la conexión
5. Nombre: "SDEP Servidor Sincronización"

### Linux (UFW)

```bash
sudo ufw allow 8765/tcp
sudo ufw reload
```

### Linux (firewalld)

```bash
sudo firewall-cmd --permanent --add-port=8765/tcp
sudo firewall-cmd --reload
```

### Verificar Conexión desde Otro Dispositivo

Desde otra computadora en la red:

```bash
# Prueba de conexión
curl http://IP_DEL_SERVIDOR:8765/api/v1/ping

# Si funciona, debería mostrar:
# {"servidor": "nodo-central-sincronizacion", "version_protocolo": "2", ...}
```

## Configuración Avanzada

### Cambiar el Puerto

```bash
python iniciar_servidor.py --config <(echo '{"puerto": 9000}')
```

O cree un archivo de configuración con el puerto deseado.

### Usar PostgreSQL en lugar de SQLite

```json
{
  "db": "postgresql://usuario:password@localhost:5432/sync_central",
  "blobs": "/ruta/a/blobs",
  "host": "0.0.0.0",
  "puerto": 8765
}
```

### Limitar Tasa de Peticiones

```json
{
  "peticiones_por_minuto": 60
}
```

## Arquitectura

El servidor tiene tres componentes principales:

1. **Núcleo Central** (`NucleoCentral`): Lógica de negocio independiente del transporte
2. **Servidor HTTP** (`ServidorSync`): Manejo de peticiones HTTP/HTTPS
3. **API de Acciones** (`ApiAcciones`): Protocolo 2 para autenticación de usuarios y acciones de negocio

Todo se ejecuta en un solo proceso sin dependencias externas complejas.

## Detener el Servidor

Presione `Ctrl+C` en la terminal donde está ejecutándose el servidor. Esto apagará el servidor de manera ordenada.

## Resumen Rápido

```bash
# Inicio rápido en 5 segundos
python iniciar_servidor.py

# El servidor mostrará automáticamente:
# URL local: http://127.0.0.1:8765
# URL para Android/otros PCs: http://192.168.1.XXX:8765

# Verificar estado desde otro PC
curl http://IP_DEL_SERVIDOR:8765/api/v1/ping
```

## Checklist para Conexión Exitosa

Antes de conectar Android u otros equipos:

- [ ] Servidor ejecutándose con `python iniciar_servidor.py`
- [ ] Firewall permite conexiones en puerto 8765
- [ ] Todos los dispositivos en la misma red WiFi
- [ ] IP local del servidor identificada (el servidor la muestra al iniciar)
- [ ] Desde Android: usar la IP local, NO 127.0.0.1
- [ ] Dispositivo creado en el servidor (se crea automáticamente con el script)
- [ ] Token del dispositivo guardado (se muestra al crear el dispositivo)

El servidor ahora está listo para aceptar conexiones de puestos de escritorio y aplicaciones móviles en la red local.
