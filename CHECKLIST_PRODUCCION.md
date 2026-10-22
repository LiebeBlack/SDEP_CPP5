# Checklist de instalación y validación en producción

Esta lista cubre la instalación del **Sistema de Gestión de Personal y Nómina**
con el servidor de sincronización embebido y la conexión desde **SDEP Móvil**.
Está pensada para ejecutarse primero en un equipo piloto y luego repetirse en
cada equipo real.

> **Alcance:** el instalador firmado lo genera el workflow `release.yml` de
> GitHub. En este repositorio no se puede validar una instalación real en los
> equipos de producción: esta lista es el procedimiento que debe ejecutarse en
> ellos y las evidencias que deben conservarse.

## 1. Antes de instalar

- [ ] Equipo Windows 10/11 de 64 bits, con al menos 4 GB de RAM y 500 MB libres.
- [ ] Sesión de Windows con permisos de administrador (el instalador los exige).
- [ ] Red **privada** o de dominio; no usar una red pública para el servidor.
- [ ] Puertos **8765/TCP** y **8766/UDP** libres en el equipo que será servidor.
- [ ] Copia de seguridad de `%LOCALAPPDATA%\SistemaGestionPersonal` si ya existe
      una instalación anterior.
- [ ] Verificar el instalador descargado:
      - Nombre esperado: `SistemaGestionPersonal-Setup-<versión>.exe`.
      - Firma: `Get-AuthenticodeSignature .\SistemaGestionPersonal-Setup-<versión>.exe`.
      - Estado esperado: `Valid` (la cadena de LiebeBlack se instala durante el
        proceso; si el estado es `NotTrusted`, revisar la cadena antes de seguir).
- [ ] Anotar la versión (`VERSION`) y el SHA-256 del instalador para el acta.

## 2. Instalación

- [ ] Ejecutar el instalador como administrador y completar el asistente.
- [ ] Confirmar que el instalador:
      - [ ] Instala la aplicación en `C:\Program Files\Sistema de Gestión de Personal`.
      - [ ] Instala la cadena de certificados de LiebeBlack (3 pasos).
      - [ ] Crea la regla **SDEP Servidor Sincronizacion** para TCP 8765 y la
            regla **SDEP Descubrimiento Sincronizacion** para UDP 8766, en
            redes privada y de dominio.
      - [ ] Incluye y programa `SDEP_CPP5_AutoUpdater.exe` (cada 2 días).
      - [ ] Crea el acceso directo del menú Inicio (y el de escritorio si se pidió).
- [ ] Comprobar la regla de firewall:
      `Get-NetFirewallRule -DisplayName "SDEP Servidor Sincronizacion"`.
- [ ] Comprobar la tarea programada del actualizador en el Programador de tareas.
- [ ] Abrir la aplicación y verificar que inicia sin errores.

## 3. Primer arranque y servidor para el teléfono

- [ ] Abrir la aplicación: el nodo central arranca solo, sin preguntas, incluso
      antes de iniciar sesión.
- [ ] Iniciar sesión con la cuenta administradora.
      - [ ] La barra de estado muestra la URL del servidor.
      - [ ] Aparece el icono en el área de notificación de Windows.
      - [ ] El tooltip del icono indica **Servidor activo** y la URL de red.
- [ ] Abrir el menú del icono y usar **Mostrar datos de conexión**.
      - [ ] La URL tiene el formato `http://<IP-de-red>:8765`.
      - [ ] La URL copiada con **Copiar URL para el teléfono** coincide.
- [ ] Verificar el servicio desde el propio equipo:
      `curl http://127.0.0.1:8765/api/v1/ping`.
      - [ ] Responde JSON con `"servidor": "nodo-central-sincronizacion"`.
- [ ] Verificar desde otro equipo de la red:
      `curl http://<IP-de-red>:8765/api/v1/ping`.
      - [ ] Responde; si no, revisar firewall y que la red sea privada.
- [ ] Comprobar que el nodo central creó la base y las cuentas:
      - [ ] Existe `%LOCALAPPDATA%\SistemaGestionPersonal\sync_central.db`.
      - [ ] Las cuentas del escritorio que no existían en el nodo se copiaron
            con su misma contraseña.
      - [ ] Las cuentas que ya existían en el nodo conservaron su clave.
      - [ ] Las cuentas iniciales solo aparecen si faltaban.

## 4. Conexión del teléfono

- [ ] Conectar el teléfono a la **misma red WiFi** que el equipo servidor.
- [ ] Abrir SDEP Móvil: descubre el escritorio solo (UDP 8766 y sondeo de la
      subred). No hay que escribir dirección, equipo ni token.
- [ ] Si no aparece, pulsar **Volver a buscar**.
- [ ] Iniciar sesión con el **mismo usuario y contraseña** usado en el escritorio.
- [ ] Verificar:
      - [ ] El login responde y el teléfono muestra el panel.
      - [ ] El teléfono puede consultar los datos existentes.
      - [ ] Un alta o edición hecha en el teléfono aparece en el escritorio
            después de sincronizar.
      - [ ] Un alta o edición hecha en el escritorio aparece en el teléfono.
      - [ ] Si se prueba en modo avión, el teléfono sigue operando y sincroniza
            al recuperar la red.
- [ ] Probar el cierre y la reapertura de la aplicación:
      - [ ] Al reabrir, el servidor arranca solo y el icono vuelve a aparecer.
      - [ ] La URL y las cuentas siguen siendo válidas.
- [ ] Probar **Detener servidor y desactivar autoarranque** en el icono:
      - [ ] El teléfono deja de conectar.
      - [ ] **Iniciar servidor en este equipo** lo vuelve a habilitar.

## 5. Validación funcional del sistema

- [ ] Panel de control: indicadores y gráficos cargan.
- [ ] Empleados: alta, edición, búsqueda y foto.
- [ ] Documentos: carga, descarga y control de vencimientos.
- [ ] Incidencias: registro, aprobación y reporte.
- [ ] Contratos: alta, renovación, terminación y reporte.
- [ ] Nómina: generación del periodo, recibo PDF y planilla.
- [ ] Estudiantes, grados, matrículas y calificaciones.
- [ ] Exportaciones a Excel/CSV y reportes PDF.
- [ ] Configuración: tema, usuarios, respaldos y auditoría.
- [ ] Cierre de sesión y nuevo inicio de sesión.
- [ ] Cierre de la aplicación: confirmar que el servidor también se detiene.

## 6. Seguridad y respaldos

- [ ] Cambiar las contraseñas iniciales que sigan vigentes.
- [ ] Confirmar que el nodo central no queda expuesto a Internet.
- [ ] Confirmar que la regla de firewall solo cubre redes privada/dominio.
- [ ] Crear un respaldo manual y verificar que aparece en la lista.
- [ ] Verificar la rotación y la restauración en un equipo de prueba.
- [ ] Revisar el visor de auditoría (solo administradores).

## 7. Actualizador y mantenimiento

- [ ] Ejecutar `SDEP_CPP5_AutoUpdater.exe --check` (o el menú del icono del
      actualizador) y confirmar que consulta la Release.
- [ ] Confirmar que la tarea programada sigue activa tras reiniciar Windows.
- [ ] Programar una ventana de mantenimiento para futuras actualizaciones.

## 8. Evidencias a conservar

- [ ] Versión instalada y SHA-256 del instalador.
- [ ] Captura del icono de bandeja con estado **Servidor activo**.
- [ ] Salida de `curl /api/v1/ping` desde el equipo y desde el teléfono/otro PC.
- [ ] Captura de la regla de firewall y de la tarea programada.
- [ ] Resultado de `SistemaGestionPersonal.exe --selftest` (código 0).
- [ ] Acta de las pruebas de sincronización escritorio ↔ teléfono.
- [ ] Copia del respaldo inicial.

## 9. Limitaciones conocidas

- El servidor se detiene al cerrar la aplicación; para que el teléfono tenga el
  nodo disponible, la aplicación debe quedar abierta.
- Las cuentas del escritorio se copian al nodo central **al configurarlo**. Si
  después se cambia una contraseña en el escritorio, hay que actualizarla
  también en el nodo central (o cambiarla desde el teléfono).
- El arranque automático del **sistema con Windows** no está incluido; solo se
  abre el servidor cuando se abre la aplicación.
- La regla de firewall del instalador cubre redes privada y de dominio. En una
  red pública el puerto permanece cerrado por diseño.
- El instalador y la firma se generan en GitHub; este repositorio no ejecuta
  una instalación real en los equipos de producción.

## 10. Rollback

- [ ] Si falla la validación, detener la aplicación y restaurar el respaldo de
      `%LOCALAPPDATA%\SistemaGestionPersonal`.
- [ ] Desinstalar desde “Aplicaciones instaladas”; el desinstalador retira la
      tarea del actualizador y la regla de firewall.
- [ ] Los datos de `%LOCALAPPDATA%\SistemaGestionPersonal` se conservan al
      desinstalar; no borrarlos sin respaldo.
- [ ] Documentar el fallo, la versión y los pasos para reproducirlo.
