# SDEP Educational Management System - C++ Version v1.0

Sistema integral de gestión para instituciones educativas desarrollado en C++ moderno con wxWidgets, SQLite y arquitectura MVC limpia.

## 🎯 Características Completas

### Módulo Académico
- **Gestión de Estudiantes**: Registro, edición, búsqueda y validación completa con diálogos interactivos
- **Gestión de Profesores**: Administración del personal docente con departamentos y especializaciones
- **Gestión de Cursos**: Creación, asignación con profesores, control de créditos
- **Matrículas**: Inscripción de estudiantes en cursos con validación de requisitos
- **Asistencia**: Control de asistencia con cálculo de porcentajes y reportes

### Módulo de Recursos Humanos
- **Gestión de Empleados**: Sistema completo con 50+ campos de información organizados en tabs
- **Datos Personales**: Cédula, pasaporte, contacto de emergencia, estado civil
- **Información Profesional**: Departamentos, cargos, contratos, horarios
- **Educación y Títulos**: Gestión de certificaciones con fechas de vencimiento
- **Información Financiera**: Salarios, deducciones, bonificaciones, cuentas bancarias
- **Control de Asistencia**: Registro de entrada/salida con cálculo de horas
- **Sistema de Ausencias**: Gestión detallada con certificados médicos
- **Registros Disciplinarios**: Sistema de puntos por infracciones

### Sistema de Seguridad
- **Autenticación Robusta**: Validación de usuarios con políticas de contraseñas
- **Gestión de Sesiones**: Tokens de sesión con control de expiración
- **Auditoría Completa**: Registro de todas las acciones del sistema
- **Bloqueo de Cuentas**: Protección contra intentos fallidos
- **Historial de Contraseñas**: Prevención de reuso de contraseñas

### Interfaz Gráfica Completa
- **wxWidgets Moderno**: Interfaz nativa multiplataforma
- **Diálogos Interactivos**: Formularios completos para todas las entidades
- **Dashboard en Tiempo Real**: Estadísticas actualizadas automáticamente
- **Sistema de Reportes**: Generación de reportes académicos y de RRHH
- **Panel de Configuración**: Gestión completa de parámetros del sistema

## 🏗️ Arquitectura

### Estructura del Proyecto
```
SDEP_CPP/
├── CMakeLists.txt              # Sistema de build multiplataforma
├── README.md                   # Documentación completa
├── include/                   # Archivos de cabecera
│   ├── models/               # Modelos de datos
│   ├── database/             # Capa de base de datos
│   ├── services/             # Lógica de negocio
│   └── gui/                 # Interfaz gráfica
├── src/                      # Implementaciones
│   ├── models/               # Implementación de modelos
│   ├── database/             # Implementación de base de datos
│   ├── services/             # Implementación de servicios
│   ├── gui/                 # Implementación de GUI
│   └── main.cpp             # Punto de entrada
├── build/                    # Directorio de build
└── resources/                # Recursos de la aplicación
```

## 🛠️ Tecnologías

- **C++17**: Lenguaje principal con características modernas
- **wxWidgets**: Framework de interfaz gráfica profesional multiplataforma
- **SQLite**: Base de datos ligera y portable
- **CMake**: Sistema de build estándar
- **STL**: Contenedores y algoritmos estándar

## 📋 Requisitos del Sistema

### Desarrollo
- **Compilador**: C++17 compatible (GCC 7+, Clang 5+, MSVC 2017+)
- **CMake**: 3.15 o superior
- **wxWidgets**: 3.0 o superior
- **SQLite**: 3.x (incluido como dependencia)
- **Sistema Operativo**: Windows 10+, Linux (Ubuntu 18.04+), macOS 10.14+

### Ejecución
- **RAM**: 2GB mínimo, 4GB recomendado
- **Disco**: 50MB de espacio libre
- **Procesador**: Any modern CPU

## 🚀 Instalación y Build

### Windows (Visual Studio)

```bash
# Clonar repositorio
git clone <repository-url>
cd SDEP_CPP

# Crear directorio de build
mkdir build
cd build

# Configurar con CMake
cmake .. -G "Visual Studio 16 2019"

# Build
cmake --build . --config Release

# Ejecutar
Release\SDEP.exe
```

### Linux (GCC/Clang)

```bash
# Instalar dependencias
sudo apt-get install build-essential cmake libwxgtk3.0-gtk3-dev libsqlite3-dev

# Clonar repositorio
git clone <repository-url>
cd SDEP_CPP

# Crear directorio de build
mkdir build
cd build

# Configurar con CMake
cmake ..

# Build
make

# Ejecutar
./SDEP
```

### macOS

```bash
# Instalar dependencias con Homebrew
brew install cmake wxmac sqlite3

# Clonar repositorio
git clone <repository-url>
cd SDEP_CPP

# Crear directorio de build
mkdir build
cd build

# Configurar con CMake
cmake ..

# Build
make

# Ejecutar
./SDEP.app
```

## 🔐 Credenciales por Defecto

- **Usuario**: admin
- **Contraseña**: Admin123!

⚠️ **IMPORTANTE**: Cambiar la contraseña por defecto en primer uso

## 📝 Uso

### Primeros Pasos

1. **Iniciar Sesión**: Use las credenciales por defecto
2. **Explorar Dashboard**: Revise las estadísticas del sistema
3. **Cambiar Contraseña**: Acceda a Configuración → Seguridad → Cambiar Contraseña
4. **Crear Usuarios**: Agregue usuarios con roles apropiados
5. **Configurar Sistema**: Configure parámetros institucionales

### Gestión de Estudiantes

1. Navegue a la pestaña "Students"
2. Click en "Add Student" para registrar nuevo estudiante
3. Complete el formulario con información personal, académica y de contacto
4. Use "Edit Student" para modificar registros existentes
5. Use "Delete Student" para eliminar registros (con confirmación)
6. Use "Refresh" para actualizar la lista
7. Use la búsqueda para encontrar estudiantes específicos

### Gestión de Profesores

1. Navegue a la pestaña "Teachers"
2. Click en "Add Teacher" para registrar nuevo profesor
3. Seleccione departamento, especialización y salarios
4. Configure fechas de contratación y calificaciones
5. Edite y elimine registros según sea necesario

### Gestión de Cursos

1. Navegue a la pestaña "Courses"
2. Click en "Add Course" para crear nuevo curso
3. Asigne un profesor responsable del curso
4. Configure créditos, horario y aula
5. Establezca el nivel educativo

### Matrículas

1. Navegue a la pestaña "Enrollments"
2. Click en "New Enrollment"
3. Seleccione estudiante y curso de los dropdowns
4. Establezca fecha de matrícula
5. Sistema valida automáticamente que el estudiante no esté matriculado previamente

### Control de Asistencia

1. Navegue a la pestaña "Attendance"
2. Seleccione la fecha
3. Click en "Mark Attendance"
4. Seleccione estudiante, curso y estado de asistencia
5. Agregue notas si es necesario
6. Sistema calcula automáticamente porcentajes de asistencia

### Gestión de Empleados (RRHH)

1. Navegue a la pestaña "Employees"
2. Click en "Add Employee" para abrir el formulario completo
3. Complete información en 4 tabs organizados:
   - **Personal**: Datos básicos, contacto, emergencia
   - **Professional**: Departamento, cargo, contratos
   - **Financial**: Salarios, bancos, método de pago
   - **Additional**: Beneficios, seguros, contratos

### Reportes

1. Navegue a la pestaña "Reports"
2. Seleccione categoría de reporte (Académico o RRHH)
3. Elija tipo de reporte específico
4. Configure rango de fechas
5. Seleccione formato de exportación (PDF/CSV)
6. Click en "Generate Report"

### Configuración

1. Navegue a la pestaña "Settings"
2. **General**: Configure nombre de institución, año académico
3. **Security**: Configure políticas de contraseñas y sesiones
4. **Database**: Configure rutas de base de datos y backups
5. Click en "Save Settings" para aplicar cambios

## 🎨 Características de la Implementación

### Código Limpio y Profesional
- **Validación Completa**: Todos los modelos tienen validación robusta
- **Manejo de Errores**: Excepciones personalizadas y manejo graceful
- **Logging**: Sistema de logging completo para debugging
- **Memory Management**: Uso de smart pointers y RAII
- **Type Safety**: Aprovechamiento de tipos fuertes de C++

### Interfaz de Usuario Moderna
- **Diálogos Modales**: Formularios completos con validación en tiempo real
- **Validación Visual**: Feedback inmediato de errores de entrada
- **Responsive Layout**: Interfaz adaptable a diferentes tamaños
- **Navegación Intuitiva**: Organización clara por funcionalidad
- **Accesibilidad**: Soporte para navegación por teclado

### Seguridad Robusta
- **Políticas de Contraseñas**: Configurables y robustas
- **Sesiones Seguras**: Tokens con expiración
- **Auditoría**: Registro completo de acciones
- **Protección contra Ataques**: Validación de entrada y sanitización

## 📄 Licencia

Este software es propietario. Todos los derechos reservados.

## 👥 Soporte

Para reportar problemas o solicitar soporte, contacte al equipo de desarrollo.

---

**Versión**: 1.0.0  
**Fecha**: 2026-08-05  
**Estado**: Production Ready ✅  
**Lenguaje**: C++17  
**Framework GUI**: wxWidgets  
**Base de Datos**: SQLite  
**Arquitectura**: MVC con Repository Pattern