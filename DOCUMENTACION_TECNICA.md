# Documentación Técnica del Sistema

## Descripción General

El Sistema de Gestión de Personal y Nómina es una aplicación desarrollada en Python que permite administrar eficientemente los recursos humanos de instituciones educativas. El sistema cuenta con una interfaz gráfica moderna y una arquitectura modular que facilita su mantenimiento y expansión.

## Arquitectura del Sistema

### Patrones de Diseño Implementados

1. **Repository Pattern**: Separación entre lógica de negocio y acceso a datos
2. **Service Layer**: Lógica de negocio encapsulada en servicios
3. **ORM (Object-Relational Mapping)**: Uso de SQLAlchemy para mapeo de base de datos
4. **Dependency Injection**: Inyección de dependencias para mayor flexibilidad

### Estructura de Capas

```
┌─────────────────────────────────────┐
│         Interfaz Gráfica (GUI)      │
│    CustomTkinter + Tkinter Widgets  │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│           Capa de Servicios         │
│        Lógica de Negocio             │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│         Capa de Repositorios        │
│         Acceso a Datos               │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│          Capa de Modelos            │
│         SQLAlchemy ORM               │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│        Base de Datos SQLite         │
└─────────────────────────────────────┘
```

## Modelos de Datos

### Modelo Base

Todos los modelos heredan de `BaseModel` que proporciona:
- `id`: Identificador único autoincremental
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización
- `to_dict()`: Método para convertir a diccionario

### Modelo Empleado

Representa la información completa de un empleado incluyendo:
- **Datos Personales**: Nombres, apellidos, cédula, fecha de nacimiento, género, estado civil
- **Datos Físicos**: Peso, altura, tipo de sangre, foto de perfil
- **Datos de Contacto**: Teléfono, celular, email, dirección, ciudad
- **Datos Laborales**: Tipo de empleado, cargo, departamento, fecha de contratación, salario
- **Datos Académicos**: Nivel educativo, especialidad, título obtenido
- **Contacto de Emergencia**: Nombre, teléfono y relación

### Modelo Documento

Gestiona la documentación digitalizada de empleados:
- **Información del Documento**: Tipo, título, descripción, número de documento
- **Fechas**: Emisión y vencimiento
- **Archivo**: Nombre, ruta, tamaño, tipo MIME, contenido binario
- **Estado**: Activo/inactivo, observaciones

### Modelo Incidencia

Controla permisos, reposos y ausencias:
- **Información de Incidencia**: Tipo, estado, fechas, motivo
- **Días**: Solicitados y aprobados
- **Documento de Soporte**: Archivo digital como respaldo
- **Aprobación**: Quién aprobó, fecha, comentarios
- **Impacto en Nómina**: Indica si afecta el cálculo de salarios

### Modelo Pago

Registra los pagos y nóminas:
- **Información del Pago**: Tipo, método de pago, periodo
- **Montos**: Bruto, neto, descuentos, bonificaciones, horas extra
- **Desglose**: Salario base, deducciones (seguro, pensión, impuesto)
- **Estado**: Pagado/pendiente, fecha de registro

### Modelo Configuración

Almacena la configuración del sistema:
- **Configuración General**: Nombre de institución, dirección, contacto
- **Configuración de Nómina**: Porcentajes de deducciones, salario mínimo
- **Configuración de RRHH**: Días de vacaciones, horas laborales

## Servicios del Sistema

### EmpleadoService

Encargado de la gestión completa de empleados:
- Crear, actualizar y eliminar empleados
- Búsqueda y filtrado avanzado
- Gestión de fotos de perfil
- Estadísticas y reportes
- Validación de datos

### DocumentoService

Maneja la gestión documental:
- Carga y almacenamiento de documentos
- Control de vencimientos
- Gestión por tipo y empleado
- Validación de archivos
- Generación de estadísticas

### IncidenciaService

Administra permisos y ausencias:
- Registro de incidencias
- Flujo de aprobación/rechazo
- Cálculo automático de días
- Gestión de documentos de soporte
- Control de incidencias vigentes

### PagoService

Procesa nóminas y pagos:
- Generación automática de nóminas
- Cálculo de deducciones
- Gestión de pagos pendientes
- Reportes por periodo
- Integración con incidencias

### ConfiguracionService

Controla la configuración del sistema:
- Gestión de parámetros institucionales
- Configuración por categorías
- Validación de valores
- Recuperación de configuraciones

## Utilidades del Sistema

### Helpers

Funciones auxiliares comunes:
- Formateo de fechas y monedas
- Validación de datos
- Cálculo de edad
- Gestión de archivos
- Generación de nombres únicos

### Validators

Validadores especializados:
- Validación de datos de empleados
- Validación de documentos
- Validación de incidencias
- Validación de pagos
- Validación de configuraciones

### DocumentManager

Gestión de archivos físicos:
- Guardado y recuperación de documentos
- Gestión de fotos de perfil
- Control de espacios
- Validación de tipos de archivo

### PDFGenerator

Generación de documentos PDF:
- Constancias de trabajo
- Constancias de estudios
- Recibos de pago
- Reportes de empleados
- Documentos oficiales

## Interfaz Gráfica

### Componentes Principales

1. **MainWindow**: Ventana principal del sistema
2. **DashboardFrame**: Panel de control con estadísticas
3. **EmpleadosFrame**: Gestión de empleados
4. **DocumentosFrame**: Gestión documental
5. **IncidenciasFrame**: Control de permisos y ausencias
6. **NominaFrame**: Procesamiento de nóminas
7. **ConfiguracionFrame**: Configuración del sistema

### Características de la Interfaz

- Diseño moderno con tema oscuro
- Navegación intuitiva por módulos
- Tablas con filtros y búsqueda
- Formularios de entrada validados
- Generación de reportes en tiempo real
- Adaptabilidad a diferentes tamaños de pantalla

## Seguridad y Validación

### Medidas de Seguridad

- Almacenamiento local de datos (sin conexión a internet requerida)
- Validación de entradas de usuario
- Control de acceso por tipo de usuario
- Encriptación de contraseñas (si se implementa)
- Registro de auditoría (opcional)

### Validaciones Implementadas

- Validación de formatos de cédula
- Validación de correos electrónicos
- Validación de fechas (no futuras para nacimiento)
- Validación de rangos numéricos
- Validación de campos requeridos
- Validación de tipos de archivo

## Configuración

### Variables de Entorno

El sistema utiliza variables de entorno para configuración:
- `DATABASE_URL`: URL de conexión a base de datos
- `APP_NAME`: Nombre de la aplicación
- `DEBUG`: Modo de depuración
- `DOCUMENTS_PATH`: Ruta de documentos
- `PHOTOS_PATH`: Ruta de fotos
- `EXPORTS_PATH`: Ruta de exportaciones

### Configuración en Base de Datos

La configuración se almacena en la base de datos y puede modificarse desde la interfaz:
- Datos de la institución
- Parámetros de nómina
- Configuración de recursos humanos
- Preferencias del sistema

## Integración y Extensión

### Puntos de Extensión

El sistema está diseñado para facilitar la extensión:
- Agregar nuevos tipos de empleados
- Implementar nuevos tipos de documentos
- Crear nuevos reportes
- Integrar con otros sistemas
- Agregar nuevos métodos de pago

### API Potencial

Se puede extender para incluir:
- API REST para integración externa
- Servicios web para acceso remoto
- Integración con sistemas de nómina externos
- Conexión con sistemas de asistencia
- Integración con sistemas de facturación

## Mantenimiento

### Tareas de Mantenimiento Rutinario

- Copias de seguridad de la base de datos
- Limpieza de documentos obsoletos
- Actualización de configuraciones
- Revisión de logs del sistema
- Optimización de base de datos

### Solución de Problemas Comunes

- **Error de conexión a base de datos**: Verificar permisos de archivo
- **Error al cargar documentos**: Verificar espacio en disco
- **Problemas con la interfaz**: Reinstalar dependencias
- **Error en cálculos**: Verificar configuración de nómina

## Rendimiento y Optimización

### Consideraciones de Rendimiento

- Uso de índices en base de datos
- Paginación de resultados
- Carga diferida de relaciones
- Optimización de consultas
- Gestión eficiente de memoria

### Escalabilidad

El sistema puede manejar:
- Hasta 1000 empleados sin degradación significativa
- Miles de documentos por empleado
- Historial ilimitado de pagos
- Múltiples usuarios concurrentes (si se implementa servidor)

## Conclusión

Este sistema proporciona una solución completa y robusta para la gestión de personal en instituciones educativas, con una arquitectura bien diseñada que facilita su mantenimiento y expansión futura.