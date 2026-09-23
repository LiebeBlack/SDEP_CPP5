# Guía de Usuario - Sistema de Gestión de Personal

## Bienvenido al Sistema

Este sistema ha sido diseñado para simplificar la administración de personal en instituciones educativas. Con esta guía aprenderá a utilizar todas las funcionalidades disponibles de manera eficiente.

## Primeros Pasos

### Instalación

1. Asegúrese de tener Python 3.15 o superior instalado
2. Descargue o clone el repositorio del proyecto
3. Instale las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```
4. Ejecute la aplicación:
   ```bash
   python src/main.py
   ```

### Configuración Inicial

Al iniciar el sistema por primera vez, deberá configurar los datos básicos de su institución:

1. Vaya a la sección **Configuración**
2. Complete los datos generales:
   - Nombre de la institución
   - RUC (si aplica)
   - Dirección física
   - Teléfono de contacto
   - Correo electrónico
3. Configure los parámetros de nómina:
   - Porcentaje de seguro social
   - Porcentaje de pensión
   - Porcentaje de impuesto
   - Salario mínimo
4. Configure los parámetros de recursos humanos:
   - Días de vacaciones anuales
   - Horas laborales semanales

## Gestión de Empleados

### Registrar un Nuevo Empleado

1. Vaya a la sección **Empleados**
2. Haga clic en el botón **Nuevo Empleado**
3. Complete la información en las pestañas disponibles:

**Pestaña Datos Personales:**
- Nombres y apellidos
- Cédula de identidad
- Fecha de nacimiento
- Género
- Estado civil
- Nacionalidad

**Pestaña Datos Físicos:**
- Peso (kg)
- Altura (cm)
- Tipo de sangre
- Foto de perfil (opcional)

**Pestaña Datos de Contacto:**
- Teléfono fijo
- Teléfono celular
- Correo electrónico
- Dirección completa
- Ciudad y estado
- Código postal

**Pestaña Datos Laborales:**
- Tipo de empleado (Docente, Administrativo, Mantenimiento)
- Cargo que desempeña
- Departamento
- Fecha de contratación
- Salario base mensual

**Pestaña Datos Académicos:**
- Nivel educativo
- Especialidad
- Título obtenido

**Pestaña Contacto de Emergencia:**
- Nombre del contacto
- Teléfono
- Relación con el empleado

4. Haga clic en **Guardar** para registrar el empleado

### Buscar y Filtrar Empleados

- **Búsqueda**: Use el campo de búsqueda para encontrar por nombre, apellido o cédula
- **Filtro por Tipo**: Seleccione el tipo de empleado para filtrar la lista
- **Actualización**: Haga clic en **Actualizar** para recargar la lista

### Editar Información de Empleado

1. Seleccione el empleado de la lista
2. Haga clic en **Editar**
3. Modifique la información necesaria
4. Guarde los cambios

### Desactivar un Empleado

1. Seleccione el empleado de la lista
2. Haga clic en **Eliminar**
3. Confirme la acción
   - **Nota**: Esto solo desactiva el empleado, no elimina su información

### Ficha del Empleado (PDF)

1. Haga clic derecho sobre el empleado en la lista
2. Elija **Ficha del Empleado (PDF)**
3. Guarde el archivo; incluye datos personales, de contacto, laborales, académicos, bancarios, de salud y familiares

### Exportar Listado de Empleados

1. Haga clic en **Exportar** (junto a Reporte PDF)
2. Elija el formato: **Excel (.xlsx)** o **CSV**
3. El archivo incluye los empleados visibles según la búsqueda y el filtro aplicados

## Gestión Documental

### Cargar Documentos

1. Seleccione un empleado de la lista de empleados
2. Vaya a la sección **Documentos**
3. Haga clic en **Nuevo Documento**
4. Complete la información:
   - Tipo de documento (Cédula, Título, Certificado, etc.)
   - Título del documento
   - Descripción (opcional)
   - Número de documento (si aplica)
   - Fecha de emisión
   - Fecha de vencimiento (si aplica)
5. Seleccione el archivo digitalizado
6. Haga clic en **Guardar**

### Tipos de Documentos Comunes

- **Cédula**: Documento de identidad
- **Título**: Título académico
- **Certificado**: Certificados diversos
- **Reposo**: Documentos médicos
- **Expediente**: Documentos generales
- **Otro**: Otros tipos de documentos

### Control de Vencimientos

El sistema le alertará sobre:
- Documentos vencidos
- Documentos por vencer en los próximos 30 días
- Documentos vigentes

Para generar el reporte en PDF:
1. Haga clic en **Control de Vencimientos**
2. El reporte incluye documentos vencidos y por vencer, con el estado de cada uno

### Exportar Documentos

1. Haga clic en **Exportar**
2. Elija **Excel (.xlsx)** o **CSV**
3. El archivo contiene los documentos del empleado seleccionado (o todos)

### Ver y Descargar Documentos

1. Seleccione el documento de la lista
2. Haga clic en **Ver** para visualizarlo
3. Haga clic en **Descargar** para guardar una copia

## Gestión de Incidencias

### Registrar una Incidencia

1. Seleccione un empleado
2. Vaya a la sección **Incidencias**
3. Haga clic en **Nueva Incidencia**
4. Complete la información:
   - Tipo de incidencia (Reposo médico, Ausencia, Permiso, Vacaciones, Licencia)
   - Fecha de inicio
   - Fecha de fin
   - Motivo detallado
   - Descripción adicional (opcional)
   - Adjunte documento de soporte (si aplica)
5. Haga clic en **Guardar**

### Tipos de Incidencias

- **Reposo Médico**: Ausencia por razones de salud
- **Ausencia**: Falta no justificada
- **Permiso**: Ausencia autorizada
- **Vacaciones**: Descanso programado
- **Licencia**: Ausencia prolongada

### Flujo de Aprobación

1. Las incidencias se registran con estado **Pendiente**
2. El administrador puede:
   - **Aprobar**: Acepta la incidencia
   - **Rechazar**: Deniega la incidencia
   - **Completar**: Marca como finalizada
3. Al aprobar, puede especificar:
   - Quién aprueba
   - Comentarios de aprobación
   - Días aprobados (pueden diferir de los solicitados)

### Reporte y Exportación de Incidencias

- **Reporte PDF**: genera el reporte de las incidencias del empleado
  seleccionado (o de todas si no hay ninguno seleccionado)
- **Exportar**: guarda el listado en Excel (.xlsx) o CSV

### Incidencias Vigentes

El sistema muestra automáticamente las incidencias que están activas en el momento actual.

## Gestión de Nómina

### Generar Nómina

1. Vaya a la sección **Nómina**
2. Defina el periodo:
   - Fecha de inicio del periodo
   - Fecha de fin del periodo
3. Seleccione las opciones:
   - **Generar para todos los empleados**: Procesa toda la nómina
   - **Generar para empleado específico**: Procesa solo un empleado
4. Haga clic en **Generar Nómina**

### Cálculo Automático

El sistema calcula automáticamente:
- Días trabajados (considerando incidencias)
- Salario proporcional al periodo
- Deducciones:
  - Seguro social (según porcentaje configurado)
  - Pensión (según porcentaje configurado)
  - Impuesto (según porcentaje configurado o tabla por tramos)
- Aportes patronales (costo de la institución, no se descuentan)
- Bonificaciones, aguinaldo, bono vacacional y horas extra
- Cuota del préstamo o anticipo activo, recortada al tope sobre el neto
- Salario neto a pagar (nunca negativo)

### Modalidades de Cálculo

El parámetro **Modalidad de cálculo** de Configuración permite elegir:

- **Porcentaje**: aplica los porcentajes configurados sobre el salario base
  (los valores por defecto reproducen el cálculo histórico del sistema).
- **Tramos**: activa el motor completo: tabla progresiva de impuesto
  (cuota fija más tasa sobre el excedente), techos de cotización para
  seguro y pensión, recargos de horas extra y base gravable de la renta
  calculada sobre los ingresos menos los aportes exentos.

Revise la tabla de tramos en Configuración antes de activar esta
modalidad: la pantalla avisa si los rangos se solapan o falta algún
tramo.

### Ver Pagos

1. La lista muestra todos los pagos generados
2. Puede filtrar por:
   - Estado (Pagado/Pendiente)
   - Periodo
   - Empleado específico
3. Los pagos pendientes se marcan en rojo

### Generar Recibo de Pago

1. Seleccione un pago de la lista
2. Haga clic en **Generar Recibo**
3. El sistema creará un PDF con:
   - Datos del empleado
   - Detalle del periodo
   - Desglose de ingresos y deducciones
   - Monto neto a recibir
4. Guarde o imprima el recibo

### Planilla de Nómina (PDF)

1. Aplique el filtro de estado deseado (Todos/Pendientes/Pagados)
2. Haga clic en **Planilla PDF**
3. El sistema genera el resumen del periodo con:
   - Un fila por empleado: salario base, extras, ISSS, AFP, ISR, otras deducciones y neto
   - Fila de **totales** al final

### Exportar Pagos

1. Haga clic en **Exportar** (junto a Planilla PDF)
2. Elija **Excel (.xlsx)** o **CSV**
3. El archivo contiene todos los pagos visibles según el filtro de estado

### Marcar Pagos como Realizados

1. Seleccione los pagos pendientes
2. Haga clic en **Marcar como Pagado**
3. El sistema registrará la fecha de pago

## Control de Asistencia

Permite registrar la jornada real de cada empleado y calcular horas
trabajadas, tardanzas y horas extra sin hacer cuentas a mano.

### Registrar una Jornada

1. Vaya a **Asistencia** y pulse **➕ Registrar jornada**
2. Seleccione el empleado, la fecha y las horas de entrada y salida
3. Verifique la **vista previa** (horas calculadas y minutos de tardanza)
4. Elija el tipo (o deje **Automático**: el sistema deduce presencia,
   tardanza o ausencia) y guarde

Si el empleado tiene un **horario** cargado para ese día, la tardanza y
las horas previstas se calculan contra ese horario; si no, se usan las
horas de entrada y salida por defecto de Configuración.

### Horas Extra

Las horas que exceden la jornada se clasifican solas para que la nómina
las pague con el recargo correcto:

- **Diurnas** (recargo normal)
- **Nocturnas** (jornada nocturna o mixta)
- **Feriadas**: trabajar en feriado o en día de descanso (todo lo
  trabajado se considera extra)

Los días de descanso y los feriados se configuran en Configuración.

### Aplicar Incidencias Aprobadas

El botón **✅ Aplicar incidencias** marca como justificados los días
cubiertos por incidencias aprobadas (vacaciones, reposos, permisos) en el
rango de fechas elegido. Puede pulsarlo tantas veces como quiera: no
reescribe los días ya marcados.

### Consultar y Exportar

- Ajuste el rango **Desde/Hasta** y filtre por empleado para ver el detalle
- El resumen inferior muestra horas trabajadas, horas extra, faltas,
  tardanzas y días trabajados del período
- **📊 Exportar** guarda el listado en Excel y **📄 Reporte PDF** genera el
  informe de asistencia del período con su resumen

## Contratos Laborales

### Crear un Contrato

1. Vaya a **Contratos** y pulse **➕ Nuevo contrato**
2. Seleccione el empleado, el tipo (indefinido, temporal, por obra o
   pasantía), el cargo, el salario pactado, las horas semanales y las
   fechas
3. Guarde: el sistema genera el número de contrato y sincroniza el cargo
   y el salario del empleado con lo pactado

Un empleado no puede tener dos contratos vigentes a la vez: renueve o
termine el actual antes de crear otro.

### Renovar

Seleccione el contrato y pulse **🔄 Renovar**. El nuevo contrato arranca el
día siguiente al vencimiento del anterior, queda enlazado a él y puede
pactar un salario distinto. El contrato anterior pasa a **Renovado**.

### Terminar con Finiquito

1. Seleccione el contrato y pulse **🛑 Terminar**
2. Indique el motivo (renuncia, despido, egreso…) y la fecha efectiva
3. Pulse **Calcular finiquito** para revisar el desglose antes de confirmar
4. Confirme: el contrato pasa a **Terminado** y, si lo deja marcado, el
   sistema registra el **pago de liquidación** en Nómina (las prestaciones
   y la indemnización no llevan aportes de seguridad social)

El finiquito incluye prestaciones por antigüedad, indemnización, preaviso,
vacaciones no disfrutadas, bono vacacional y aguinaldo proporcional, menos
los anticipos pendientes.

### Seguimiento

- El filtro **Por vencer** muestra los contratos próximos a su fecha de
  fin (según el umbral configurado) y **Vencidos** los que ya pasaron su
  fecha sin cerrarse
- El resumen inferior indica cuántos contratos vigentes hay y el monto
  mensual comprometido
- **📊 Exportar** y **📄 Reporte PDF** entregan el listado mostrado

## Anticipos y Préstamos

### Registrar una Solicitud

1. Vaya a **Préstamos** y pulse **➕ Nueva solicitud**
2. Elija el empleado, el tipo (**anticipo** de una sola cuota o
   **préstamo** en varias cuotas), el monto y el número de cuotas
3. El diálogo muestra el **monto máximo** según el salario y la cuota
   estimada; al guardar, el sistema valida el tope de descuento

### Aprobar o Rechazar

- **✅ Aprobar** habilita el descuento automático del préstamo en la nómina
- **❌ Rechazar** cierra la solicitud indicando el motivo

### Seguimiento

- Las columnas muestran monto, cuota, cuotas pagadas, saldo y avance
- **📋 Plan de pagos** abre la amortización cuota por cuota del préstamo
  seleccionado (la última cuota ajusta el redondeo para que la suma sea
  exactamente el monto otorgado)
- El filtro **Rechazados o cancelados** agrupa las operaciones anuladas

En la nómina, la cuota se descuenta respetando el tope porcentual sobre el
neto del empleado, para que nunca se quede sin remuneración disponible.

## Alertas del Sistema

El módulo **Alertas** (y el panel del Dashboard) reúne los avisos que
requieren acción, ordenados por severidad:

- **Críticas**: contratos vencidos sin cerrar, incidencias pendientes
  antiguas, ausencia de respaldos
- **Advertencias**: documentos y contratos por vencer, empleados sin
  contrato vigente, préstamos por aprobar, pagos pendientes antiguos,
  contraseñas caducadas
- **Informativas**: jornadas sin registrar, ausentismo elevado

Cada alerta indica cuántos casos agrupa y en qué módulo se resuelve. Pulse
**↗ Ir al módulo** (o haga doble clic) para resolverla, filtre por
categoría y use **📄 Reporte PDF** para exportar el listado.

## Configuración del Sistema

### Configuración General

Modifique los datos de su institución:
- Nombre de la institución
- Datos de contacto
- Información fiscal

### Configuración de Nómina

Ajuste las deducciones del período:
- **Modalidad de cálculo**: `porcentaje` (histórica) o `tramos`
- **Seguro Social** y **Pensión**: porcentajes deducidos al empleado y sus
  techos mensuales (0 = sin techo)
- **Impuesto**: porcentaje, o tabla de tramos cuando la modalidad es por
  tramos (límite inferior, límite superior, tasa y cuota fija)
- **Aportes patronales**: porcentajes a cargo de la institución
- **Recargos de horas extra**: diurna, nocturna y feriada
- **Días de aguinaldo, bono vacacional, prestaciones y preaviso**
- **Tope de la cuota de préstamo**: porcentaje máximo sobre el neto
- **Salario mínimo**: valor de referencia para cálculos

### Configuración de Recursos Humanos

Defina las políticas de personal y asistencia:
- **Horas laborales**: jornada diaria y horas semanales de referencia
- **Hora de entrada y salida por defecto**: se usan cuando el empleado no
  tiene horario cargado
- **Tolerancia de asistencia**: minutos de gracia antes de marcar tardanza
- **Días de descanso**: días de la semana no laborables
- **Feriados**: fechas que se pagan como hora feriada
- **Umbrales de aviso**: contratos y documentos por vencer, ausentismo,
  horas extra semanales, pagos pendientes antiguos
- **Respaldos automáticos**: interruptor e intervalo en horas
- **Credenciales**: caducidad, historial de contraseñas, intentos
  permitidos y minutos de bloqueo

### Cambiar Contraseña

1. Haga clic en **Cambiar Contraseña** (abajo en Configuración)
2. Ingrese la contraseña actual y la nueva (mínimo 6 caracteres)
3. Confirme la nueva contraseña y guarde

Política de credenciales del sistema:

- Tras varios intentos fallidos la cuenta se bloquea temporalmente; un
  administrador puede desbloquearla de inmediato.
- Las contraseñas caducan según los días configurados y el sistema pide
  el cambio; no se puede repetir la contraseña vigente ni las últimas
  registradas.
- Las cuentas nuevas y las restablecidas por el administrador exigen
  cambiar la contraseña en el siguiente inicio de sesión.

### Apariencia (Tema Oscuro/Claro)

El botón ☀️/**🌙** de la cabecera alterna entre el tema oscuro (por
defecto) y el tema claro. La preferencia se guarda automáticamente y se
recupera en el siguiente inicio de sesión, incluyendo la ventana de
acceso.

### Ayuda y Acerca de

- **Ayuda**: abre una guía rápida con los módulos, atajos de teclado y
  consejos de uso.
- **Acerca de**: muestra la versión del sistema, los roles disponibles
  y detalles técnicos.

Ambas ventanas están disponibles desde la cabecera de la ventana
principal y se cierran con **Esc** o el botón **Cerrar**.

### Visor de Auditoría (solo administradores)

La pestaña **Auditoría** muestra los eventos recientes del sistema:
- Filtre por tipo de evento (inicio de sesión, respaldos, cambios, errores)
- Use **Actualizar** para recargar y **Exportar** para guardar el listado
  en Excel (.xlsx) o CSV
- **Doble clic** en una fila abre el detalle completo del evento (datos
  técnicos, dirección IP y errores asociados)
- El botón **Manual** abre la guía de uso de la sección: qué se registra,
  cómo leer cada columna y recomendaciones de revisión periódica

## Panel de Control (Dashboard)

El Dashboard proporciona una vista general del sistema:

### Estadísticas en Tiempo Real

- **Total de Empleados**: Cantidad de empleados registrados
- **Empleados Activos**: Empleados actualmente laborando
- **Documentos**: Total de documentos en el sistema
- **Incidencias Pendientes**: Solicitudes por aprobar
- **Pagos Pendientes**: Nóminas por procesar

### Indicadores y Gráficos

Debajo de las tarjetas, el panel muestra el estado del período:

- **Nómina del mes**: total neto pagado y cantidad de pagos
- **Ausentismo del mes**: porcentaje de faltas sobre los registros
- **Contratos por vencer**: contratos próximos a su fecha de fin y
  empleados sin contrato vigente
- **Saldo por cobrar**: préstamos y anticipos activos
- **Gráficos**: empleados activos por departamento, contratos por tipo y
  egresos netos de los últimos seis meses
- **Panel de alertas**: las alertas vigentes con un botón para ir al
  módulo donde se resuelven (el módulo **Alertas** las muestra todas)

### Acciones Rápidas

Accesos directos a las funciones más utilizadas:
- Registrar nuevo empleado
- Cargar documento
- Crear incidencia
- Registrar jornada
- Consultar contratos
- Generar nómina

## Generación de Reportes

### Constancia de Trabajo

1. Seleccione un empleado
2. Haga clic en **Generar Constancia de Trabajo**
3. El sistema crea un PDF oficial con:
   - Datos de la institución
   - Información del empleado
   - Fecha de contratación
   - Cargo y departamento
   - Salario actual
   - Espacio para firma y sello

### Constancia de Estudios

1. Seleccione un empleado
2. Haga clic en **Generar Constancia de Estudios**
3. El documento incluye:
   - Datos académicos del empleado
   - Títulos obtenidos
   - Fechas de graduación

### Reporte de Empleados

Genere reportes que incluyen:
- Lista completa de empleados
- Filtrado por departamento o tipo
- Estadísticas por categoría
- Exportación a PDF

## Buenas Prácticas

### Seguridad de Datos

- Realice copias de seguridad periódicas de la base de datos
- Mantenga los documentos originales en lugar seguro
- Utilice contraseñas seguras si se implementa control de acceso
- Actualice regularmente la información de los empleados

### Mantenimiento de Documentos

- Cargue documentos de alta calidad
- Verifique que los documentos sean legibles
- Mantenga actualizados los documentos vencidos
- Organice por tipo y fecha

### Gestión de Incidencias

- Aprobar o rechazar incidencias oportunamente
- Documente apropiadamente los motivos
- Mantenga los documentos de soporte actualizados
- Revise regularmente las incidencias pendientes

### Procesamiento de Nómina

- Genere nóminas en fechas establecidas
- Verifique los cálculos antes de procesar
- Mantenga registros de todos los pagos
- Genere recibos para cada pago

## Solución de Problemas

### Problemas Comunes

**El sistema no inicia:**
- Verifique que Python esté instalado correctamente
- Asegúrese de tener todas las dependencias instaladas
- Verifique los permisos de los archivos

**No puedo guardar cambios:**
- Verifique que los campos requeridos estén completos
- Revise el formato de los datos (fechas, números)
- Asegúrese de tener permisos de escritura

**Los documentos no se cargan:**
- Verifique el tamaño del archivo (máximo 50MB)
- Confirme que el formato sea compatible (PDF, imágenes)
- Revise el espacio disponible en disco

**Error en cálculos de nómina:**
- Verifique la configuración de porcentajes
- Revise los datos del empleado
- Compruebe las incidencias en el periodo

### Obtener Ayuda

Si encuentra problemas que no puede resolver:
1. Revise esta guía de usuario
2. Consulte la documentación técnica
3. Contacte al administrador del sistema
4. Revise los logs del sistema para detalles del error

## Atajos de Teclado

Los atajos permiten moverse y trabajar sin usar el ratón. Se aplican en
el módulo que esté visible en ese momento:

| Atajo | Acción |
| --- | --- |
| **Ctrl+1 … Ctrl+6** | Navegar directamente a cada módulo: 1 Dashboard, 2 Empleados, 3 Documentos, 4 Incidencias, 5 Nómina, 6 Configuración |
| **Ctrl+N** | Nuevo registro del módulo activo (Empleado, Documento, Incidencia, Pago, Usuario) |
| **Ctrl+F** | Enfocar la búsqueda (Empleados) o el filtro del módulo activo |
| **Ctrl+S** | Guardar cambios en el módulo de Configuración |
| **F5** | Actualizar la lista o los datos del módulo activo |
| **Esc** | Cerrar cuadros de diálogo; en la ventana principal, limpiar la selección de la tabla |

**Nota**: algunos atajos solo están disponibles en los módulos que
soportan la acción (por ejemplo, Ctrl+N no tiene efecto en el
Dashboard). Los diálogos abiertos (formularios, confirmaciones)
capturan el teclado mientras están visibles, por lo que los atajos de
la ventana principal se reactivan al cerrarlos.

## Actualizaciones del Sistema

El sistema puede recibir actualizaciones que incluyan:
- Nuevas funcionalidades
- Mejoras en la interfaz
- Corrección de errores
- Optimizaciones de rendimiento

### Actualización automática (cada 2 días)

Si instaló el sistema con el instalador de Windows, el **actualizador
automático** ya viene incluido y programado:

- **Frecuencia**: comprueba novedades **cada 2 días a las 09:00** (a
  través del Programador de tareas de Windows).
- **Ventana de estado**: al comprobar muestra una ventana que informa
  todo lo que hace: *comprobando actualizaciones*, *descargando* (con
  porcentaje y tamaño), *instalando* y el resultado final (*ya está
  actualizado* o *actualización completada*). Si hay un error, lo
  muestra claramente.
- **Bandeja del sistema**: mientras trabaja aparece un ícono en la
  barra inferior derecha de Windows (junto al reloj). Con clic derecho
  ofrece las opciones *Buscar actualizaciones ahora*, *Mostrar ventana*
  y *Salir*.
- **Instalación automática**: si hay una versión más nueva, se descarga
  e instala en silencio; si la aplicación está abierta, se cierra con un
  aviso antes de actualizar.

También puede ejecutar el actualizador manualmente haciendo doble clic en
`SDEP_CPP5_AutoUpdater.exe` (ubicado en la carpeta de instalación).

Se recomienda mantener el sistema actualizado para aprovechar las mejoras.

## Conclusión

Este sistema ha sido diseñado para ser intuitivo y eficiente. Con la práctica, podrá administrar la información de personal de manera rápida y precisa. Si tiene sugerencias para mejorar el sistema, no dude en comunicarlas al equipo de desarrollo.

---

**Versión del Sistema**: 2.82  
**Última Actualización**: 2026