# Auditoría de integración — 21 de octubre de 2026

## 1. Alcance y método

Se auditó la integración del **servidor de sincronización embebido**, la
**bandeja del sistema**, el **arranque automático**, el **empaquetado** y el
**instalador**, sobre la versión 3.0.1 del repositorio.

Método aplicado:

1. **Cobertura automática de todo el código Python** (`src/`, `sync_agent/`,
   `updater/`, `tools/`, `build.py`): compilación de bytecode, `flake8`,
   `black --check`, `isort --check-only`, `mypy` y la suite de pruebas.
2. **Revisión manual de los puntos de integración críticos**: arranque,
   servidor, agente, captura de cambios, autenticación central, GUI, bandeja,
   spec de PyInstaller, instalador y workflows.
3. **Validación de empaquetado real en Windows**: ejecutable `onedir`,
   actualizador `onefile` y `--selftest` del ejecutable.
4. **Revisión de seguridad básica**: búsqueda de `eval`/`exec`, `shell=True`,
   `pickle`, `yaml.load`, `verify=False`, hashes débiles, `except:` desnudos,
   secretos embebidos y dependencias rotas.

> **Límite honesto:** no se hizo una lectura manual función por función de los
> 461 archivos del repositorio (incluye Android, XML y documentación). La
> cobertura automática alcanza todos los archivos Python; la revisión manual se
> concentró en los puntos donde un fallo afecta datos, arranque, seguridad o
> instalación. El código Android no se modificó y no se compiló localmente por
> falta de SDK; su contrato HTTP quedó cubierto por las pruebas del servidor.

## 2. Hallazgos y correcciones

| # | Hallazgo | Corrección |
|---|----------|------------|
| 1 | El servidor central solo se podía iniciar con un script externo. | Se añadió `sync_agent/servidor_embebido.py` y el arranque desde `src/main.py`. |
| 2 | El teléfono habría usado cuentas iniciales distintas a las del escritorio. | El nodo central copia los usuarios locales con su mismo hash PBKDF2; solo crea las cuentas iniciales que falten. |
| 3 | El equipo podía quedar sincronizando contra un servidor remoto aunque fuera designado como nodo central. | Al arrancar el nodo local, el destino del puesto se reemplaza por el nodo local; así el teléfono y el escritorio comparten la misma base. |
| 4 | Al iniciar el servidor después del login, el agente se recreaba sin activar la captura de cambios. | El arranque tardío prepara el esquema y activa la captura antes de reiniciar el agente. |
| 5 | No existía un icono de estado del servidor. | Se reutilizó `updater/tray_icon.py`, generalizado con menú configurable y `notify`, y se integró en la ventana principal. |
| 6 | El icono no estaba incluido en el paquete Windows. | `spec/app.spec` incluye `assets/app.ico`; se verificó dentro de `dist/`. |
| 7 | El instalador no abría el puerto para el teléfono. | `installer/setup.iss` crea la regla de firewall 8765/TCP para redes privada y de dominio, y la elimina al desinstalar. |
| 8 | `docs/` quedaba desincronizado tras editar README/GUÍA y el CI habría fallado. | Se regeneró `docs/docs_data.js` y `docs/content/`; `tools/verify_docs.py` pasa. |
| 9 | La preferencia del servidor podía filtrarse entre pruebas. | `tests/conftest.py` limpia `sync_servidor_auto` en cada entorno aislado. |
| 10 | Reiniciar el nodo con otro puerto duplicaba el dispositivo del puesto. | El destino loopback se reconoce por host, se valida el token y se reutiliza el dispositivo. |

## 3. Archivos de integración revisados

| Archivo | Revisión |
|---------|----------|
| `sync_agent/servidor_embebido.py` | Nuevo; ciclo de vida, puerto ocupado, auto-configuración, cuentas, cliente local, cierre. |
| `sync_agent/__init__.py` | Nuevo `reiniciar_agente`; exportaciones y parada segura. |
| `sync_agent/servidor.py` | Contrato HTTP, autenticación, núcleo, cierre. Sin cambios funcionales. |
| `sync_agent/sesiones.py` | Login con las cuentas centrales; prueba HTTP real de login. |
| `sync_agent/config.py` | Persistencia de URL, token, dispositivo y preferencia del servidor. |
| `src/main.py` | Arranque del servidor antes del agente, `--selftest`, limpieza al salir. |
| `src/gui/main_window.py` | Pregunta inicial, bandeja, notificaciones, URL, datos de conexión, inicio/parada, limpieza. |
| `src/config/database.py` | Esquema de sincronización y captura idempotente. |
| `src/services/auth_service.py` | Autenticación y política de credenciales reutilizadas por el nodo. |
| `updater/tray_icon.py` | Menú configurable, notificaciones, cierre, compatibilidad con el actualizador. |
| `spec/app.spec` | Inclusión de módulos y del icono. Build verificado. |
| `installer/setup.iss` | Regla de firewall y limpieza al desinstalar. Revisión estática; falta compilar con Inno Setup. |
| `.github/workflows/build.yml` | Pruebas, estilo, tipos, documentación, build Windows/Linux. |
| `.github/workflows/release.yml` | Firma y release; no modificado. Requiere secretos `PFX_BASE64` y `PFX_PASSWORD`. |
| `README.md`, `GUIA_SERVIDOR_LOCAL.md` | Documentación del arranque automático, cuentas y firewall. |
| `CHECKLIST_PRODUCCION.md` | Procedimiento de instalación y validación en equipos reales. |
| `tests/test_servidor_embebido.py` | 7 pruebas: arranque, ping, cuentas, login móvil, reinicio, puerto ocupado, preferencia. |
| `tests/conftest.py` | Aislamiento de la nueva preferencia. |

## 4. Validaciones ejecutadas

| Validación | Resultado |
|------------|-----------|
| `python -m compileall src sync_agent updater` | OK |
| `flake8 src sync_agent updater tools build.py` | OK |
| `black --check ...` | OK (139 archivos sin cambios) |
| `isort --check-only ...` | OK |
| `mypy src sync_agent updater tools build.py` | OK (103 archivos) |
| `pip check` | Sin dependencias rotas |
| `tools/verify_docs.py` | OK |
| Suite completa antes de los últimos retoques | 616 pruebas aprobadas |
| Pruebas del servidor embebido tras los últimos retoques | 7 aprobadas |
| Pruebas GUI tras los últimos retoques | 19 aprobadas |
| Build Windows `python build.py --exe` | OK (10.7 MB) |
| `SistemaGestionPersonal.exe --selftest` | Código 0 |
| Build del actualizador `python build.py --updater` | OK (12.4 MB) |
| Bandeja: crear, actualizar menú/estado, notificar y cerrar | OK en Windows |
| Servidor + agente + captura en el flujo de primer inicio | Servidor activo, cliente configurado, captura activa, agente activo |
| Login HTTP del móvil con la cuenta del escritorio | OK |

## 5. Pendientes y bloqueos

1. **GitHub:** los cambios no se han subido. No se ejecutó el workflow real ni
   se publicó una release firmada. Hace falta decidir rama/PR o `main`.
2. **Inno Setup:** no está instalado en este equipo, por lo que el instalador
   final no se compiló ni se ejecutó localmente. El workflow de GitHub lo
   instala con `choco install innosetup`.
3. **Producción:** no hay acceso a los equipos reales. La validación debe
   hacerse con `CHECKLIST_PRODUCCION.md` en un equipo piloto y luego en cada
   puesto.
4. **Android:** no se compiló la app Kotlin en esta sesión (falta SDK Android).
   El contrato HTTP no cambió y las pruebas del servidor/API pasan.
5. **Contraseñas posteriores:** la copia de cuentas al nodo central ocurre al
   configurarlo. Si se cambia una contraseña después en el escritorio, debe
   actualizarse también en el nodo central.

## 6. Conclusión

La integración de escritorio, servidor embebido, bandeja y empaquetado queda
consistente y compila en Windows. El instalador final y la instalación real en
producción **no pueden declararse verificados** desde este entorno: deben
pasar por el workflow de GitHub y por el checklist en los equipos reales.

## Anexo A — Cobertura de los archivos Python

Todos los archivos de `src/`, `sync_agent/`, `updater/` y `tools/` pasaron
por `compileall`, `flake8`, `black`, `isort` y `mypy`; la suite de pruebas
ejerce los flujos principales. La columna **Revisión** distingue los puntos
que además se leyeron a mano para esta auditoría.

| Archivo | Líneas | Revisión |
|---------|-------:|----------|
| `src/__init__.py` | 8 | Estático + suite |
| `src/config/__init__.py` | 12 | Estático + suite |
| `src/config/build_info.py` | 4 | Estático + suite |
| `src/config/database.py` | 1358 | Manual + estático + suite |
| `src/config/settings.py` | 336 | Estático + suite |
| `src/gui/__init__.py` | 30 | Estático + suite |
| `src/gui/contratos_frame.py` | 978 | Estático + suite |
| `src/gui/estudiantes_frame.py` | 1314 | Estático + suite |
| `src/gui/frames.py` | 5634 | Estático + suite |
| `src/gui/login_window.py` | 442 | Manual + estático + suite |
| `src/gui/main_window.py` | 1517 | Manual + estático + suite |
| `src/gui/notas_frame.py` | 1328 | Estático + suite |
| `src/gui/theme.py` | 625 | Estático + suite |
| `src/gui/widgets/__init__.py` | 20 | Estático + suite |
| `src/gui/widgets/graficos.py` | 494 | Estático + suite |
| `src/main.py` | 634 | Manual + estático + suite |
| `src/models/__init__.py` | 71 | Estático + suite |
| `src/models/base.py` | 72 | Estático + suite |
| `src/models/configuracion.py` | 89 | Estático + suite |
| `src/models/contrato.py` | 193 | Estático + suite |
| `src/models/documento.py` | 90 | Estático + suite |
| `src/models/empleado.py` | 232 | Estático + suite |
| `src/models/enums.py` | 242 | Estático + suite |
| `src/models/estudiante.py` | 109 | Estático + suite |
| `src/models/grado.py` | 93 | Estático + suite |
| `src/models/incidencia.py` | 113 | Estático + suite |
| `src/models/matricula.py` | 73 | Estático + suite |
| `src/models/nota_final.py` | 77 | Estático + suite |
| `src/models/pago.py` | 178 | Estático + suite |
| `src/models/periodo_academico.py` | 73 | Estático + suite |
| `src/models/registro_movil.py` | 64 | Estático + suite |
| `src/models/token_sesion.py` | 79 | Estático + suite |
| `src/models/usuario.py` | 114 | Estático + suite |
| `src/nomina/__init__.py` | 115 | Estático + suite |
| `src/nomina/finiquito.py` | 213 | Estático + suite |
| `src/nomina/horas_extra.py` | 113 | Estático + suite |
| `src/nomina/isr.py` | 86 | Estático + suite |
| `src/nomina/motor.py` | 197 | Estático + suite |
| `src/nomina/parametros.py` | 178 | Estático + suite |
| `src/nomina/prestaciones.py` | 156 | Estático + suite |
| `src/nomina/seguridad_social.py` | 85 | Estático + suite |
| `src/nomina/tipos.py` | 368 | Estático + suite |
| `src/repositories/__init__.py` | 36 | Estático + suite |
| `src/repositories/base_repository.py` | 503 | Estático + suite |
| `src/repositories/busqueda.py` | 39 | Estático + suite |
| `src/repositories/configuracion_repository.py` | 70 | Estático + suite |
| `src/repositories/contrato_repository.py` | 225 | Estático + suite |
| `src/repositories/documento_repository.py` | 132 | Estático + suite |
| `src/repositories/empleado_repository.py` | 235 | Estático + suite |
| `src/repositories/estudiante_repository.py` | 159 | Estático + suite |
| `src/repositories/grado_repository.py` | 92 | Estático + suite |
| `src/repositories/incidencia_repository.py` | 210 | Estático + suite |
| `src/repositories/matricula_repository.py` | 122 | Estático + suite |
| `src/repositories/nota_final_repository.py` | 161 | Estático + suite |
| `src/repositories/pago_repository.py` | 185 | Estático + suite |
| `src/repositories/periodo_academico_repository.py` | 81 | Estático + suite |
| `src/repositories/token_sesion_repository.py` | 111 | Estático + suite |
| `src/repositories/usuario_repository.py` | 29 | Estático + suite |
| `src/services/__init__.py` | 28 | Estático + suite |
| `src/services/academico_service.py` | 581 | Estático + suite |
| `src/services/auth_service.py` | 463 | Manual + estático + suite |
| `src/services/configuracion_service.py` | 193 | Estático + suite |
| `src/services/contrato_service.py` | 650 | Estático + suite |
| `src/services/documento_service.py` | 296 | Estático + suite |
| `src/services/empleado_service.py` | 365 | Estático + suite |
| `src/services/incidencia_service.py` | 427 | Estático + suite |
| `src/services/nota_service.py` | 519 | Estático + suite |
| `src/services/pago_service.py` | 742 | Estático + suite |
| `src/services/token_sesion_service.py` | 163 | Estático + suite |
| `src/utils/__init__.py` | 99 | Estático + suite |
| `src/utils/audit_logger.py` | 539 | Estático + suite |
| `src/utils/backup_manager.py` | 645 | Estático + suite |
| `src/utils/backup_scheduler.py` | 309 | Estático + suite |
| `src/utils/document_manager.py` | 546 | Estático + suite |
| `src/utils/exporter.py` | 235 | Estático + suite |
| `src/utils/helpers.py` | 661 | Estático + suite |
| `src/utils/pdf_generator.py` | 1727 | Estático + suite |
| `src/utils/security.py` | 526 | Estático + suite |
| `src/utils/validators.py` | 300 | Estático + suite |
| `sync_agent/__init__.py` | 169 | Manual + estático + suite |
| `sync_agent/__main__.py` | 656 | Estático + suite |
| `sync_agent/agente.py` | 942 | Estático + suite |
| `sync_agent/api_acciones.py` | 1152 | Estático + suite |
| `sync_agent/aplicador.py` | 677 | Estático + suite |
| `sync_agent/captura.py` | 480 | Estático + suite |
| `sync_agent/cliente.py` | 213 | Estático + suite |
| `sync_agent/comun.py` | 254 | Estático + suite |
| `sync_agent/config.py` | 215 | Manual + estático + suite |
| `sync_agent/esquema.py` | 322 | Estático + suite |
| `sync_agent/identidad.py` | 269 | Estático + suite |
| `sync_agent/merge.py` | 382 | Estático + suite |
| `sync_agent/registro.py` | 295 | Estático + suite |
| `sync_agent/servidor.py` | 1104 | Manual + estático + suite |
| `sync_agent/servidor_embebido.py` | 482 | Manual + estático + suite |
| `sync_agent/sesiones.py` | 351 | Manual + estático + suite |
| `tools/generate_docs_bundle.py` | 320 | Estático + suite |
| `tools/make_icon.py` | 85 | Estático + suite |
| `tools/verify_docs.py` | 145 | Estático + suite |
| `updater/__init__.py` | 0 | Estático + suite |
| `updater/auto_updater.py` | 801 | Estático + suite |
| `updater/tray_icon.py` | 434 | Manual + estático + suite |
| `updater/updater_gui.py` | 277 | Estático + suite |
