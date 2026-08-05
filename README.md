# SDEP Educational Management System - C++ Version v1.0

Sistema integral de gestión para instituciones educativas desarrollado en C++ moderno con wxWidgets, SQLite y arquitectura MVC limpia.

## 🎯 Características

### Módulo Académico
- **Gestión de Estudiantes**: Registro, edición, búsqueda y validación completa
- **Gestión de Profesores**: Administración del personal docente con departamentos
- **Gestión de Cursos**: Creación, asignación con profesores, control de créditos
- **Matrículas**: Inscripción de estudiantes en cursos con validación
- **Asistencia**: Control de asistencia con cálculo de porcentajes

### Módulo de Recursos Humanos
- **Gestión de Empleados**: Sistema completo con 50+ campos organizados en tabs
- **Datos Personales**: Cédula, pasaporte, contacto de emergencia
- **Información Profesional**: Departamentos, cargos, contratos, horarios
- **Información Financiera**: Salarios, deducciones, cuentas bancarias
- **Control de Asistencia**: Registro de entrada/salida

### Sistema de Seguridad
- **Autenticación Robusta**: Validación de usuarios con políticas de contraseñas
- **Gestión de Sesiones**: Tokens de sesión con control de expiración
- **Auditoría Completa**: Registro de todas las acciones del sistema

### Interfaz Gráfica
- **wxWidgets Moderno**: Interfaz nativa multiplataforma
- **Diálogos Interactivos**: Formularios completos para todas las entidades
- **Dashboard en Tiempo Real**: Estadísticas actualizadas automáticamente
- **Sistema de Reportes**: Generación de reportes académicos y de RRHH
- **Panel de Configuración**: Gestión completa de parámetros del sistema

## 🏗️ Arquitectura

```
SDEP_CPP/
├── CMakeLists.txt              # Sistema de build
├── build.bat                   # Script de compilación Windows
├── build.sh                    # Script de compilación Linux/macOS
├── .gitignore                  # Archivos ignorados por Git
├── include/                    # Archivos de cabecera
│   ├── models/                # Modelos de datos
│   ├── database/              # Capa de base de datos
│   ├── services/              # Lógica de negocio
│   └── gui/                   # Interfaz gráfica
├── src/                       # Implementaciones
│   ├── models/                # Implementación de modelos
│   ├── database/              # Implementación de base de datos
│   ├── services/              # Implementación de servicios
│   ├── gui/                   # Implementación de GUI
│   └── main.cpp               # Punto de entrada
└── build/                     # Directorio de build
```

## 🛠️ Tecnologías

- **C++17**: Lenguaje principal con características modernas
- **wxWidgets 3.0+**: Framework de interfaz gráfica multiplataforma
- **SQLite 3.x**: Base de datos ligera y portable
- **CMake 3.15+**: Sistema de build estándar
- **STL**: Biblioteca estándar de C++

## 📋 Requisitos del Sistema

### Windows
- Windows 10 o superior
- Visual Studio 2017 o superior (con C++ support)
- CMake 3.15 o superior
- wxWidgets 3.0 o superior

### Linux (Ubuntu/Debian)
- Ubuntu 18.04+ o Debian 11+
- GCC 7+ o Clang 5+
- CMake 3.15+
- libwxgtk3.0-gtk3-dev
- libsqlite3-dev

### macOS
- macOS 10.14+
- Xcode Command Line Tools
- CMake 3.15+
- wxmac (via Homebrew)
- sqlite3 (via Homebrew)

## 🚀 Instalación y Build

### Windows

#### Instalación de Dependencias
1. Instalar Visual Studio 2017 o superior
2. Instalar CMake desde https://cmake.org/download/
3. Instalar wxWidgets desde https://www.wxwidgets.org/downloads/

#### Compilación
```bash
# Usar el script automatizado
build.bat

# O manualmente
mkdir build
cd build
cmake .. -G "Visual Studio 16 2019" -A x64
cmake --build . --config Release
```

#### Ejecución
```bash
cd build\Release
SDEP.exe
```

### Linux

#### Instalación de Dependencias
```bash
sudo apt-get update
sudo apt-get install build-essential cmake git
sudo apt-get install libwxgtk3.0-gtk3-dev libsqlite3-dev
```

#### Compilación
```bash
# Usar el script automatizado
chmod +x build.sh
./build.sh

# O manualmente
mkdir build
cd build
cmake ..
make -j$(nproc)
```

#### Ejecución
```bash
cd build
./SDEP
```

### macOS

#### Instalación de Dependencias
```bash
# Instalar Xcode Command Line Tools
xcode-select --install

# Instalar Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependencias
brew install cmake wxmac sqlite3 git
```

#### Compilación
```bash
# Usar el script automatizado
chmod +x build.sh
./build.sh

# O manualmente
mkdir build
cd build
cmake ..
make -j$(sysctl -n hw.ncpu)
```

#### Ejecución
```bash
cd build
./SDEP
```

## 🔐 Credenciales por Defecto

- **Usuario**: admin
- **Contraseña**: Admin123!

⚠️ **IMPORTANTE**: Cambiar la contraseña por defecto en primer uso

## 📝 Uso

### Primeros Pasos

1. **Iniciar Sesión**: Use las credenciales por defecto
2. **Explorar Dashboard**: Revise las estadísticas del sistema
3. **Cambiar Contraseña**: Acceda a Configuración → Seguridad
4. **Crear Usuarios**: Agregue usuarios con roles apropiados
5. **Configurar Sistema**: Configure parámetros institucionales

### Gestión de Estudiantes

1. Navegue a la pestaña "Students"
2. Click en "Add Student" para registrar nuevo estudiante
3. Complete el formulario con información personal y académica
4. Use "Edit Student" para modificar registros existentes
5. Use "Delete Student" para eliminar registros

### Gestión de Profesores

1. Navegue a la pestaña "Teachers"
2. Click en "Add Teacher" para registrar nuevo profesor
3. Seleccione departamento, especialización y salarios
4. Configure fechas de contratación y calificaciones

### Gestión de Cursos

1. Navegue a la pestaña "Courses"
2. Click en "Add Course" para crear nuevo curso
3. Asigne un profesor responsable del curso
4. Configure créditos, horario y aula

### Matrículas

1. Navegue a la pestaña "Enrollments"
2. Click en "New Enrollment"
3. Seleccione estudiante y curso de los dropdowns
4. Sistema valida automáticamente la matrícula

### Control de Asistencia

1. Navegue a la pestaña "Attendance"
2. Seleccione la fecha
3. Click en "Mark Attendance"
4. Seleccione estudiante, curso y estado de asistencia

### Gestión de Empleados (RRHH)

1. Navegue a la pestaña "Employees"
2. Click en "Add Employee" para abrir el formulario completo
3. Complete información en 4 tabs organizados

## 🎨 Características de la Implementación

### Código Limpio y Profesional
- **Validación Completa**: Todos los modelos tienen validación robusta
- **Manejo de Errores**: Excepciones personalizadas y manejo graceful
- **Memory Management**: Uso de smart pointers y RAII
- **Type Safety**: Aprovechamiento de tipos fuertes de C++

### Interfaz de Usuario Moderna
- **Diálogos Modales**: Formularios completos con validación en tiempo real
- **Validación Visual**: Feedback inmediato de errores de entrada
- **Responsive Layout**: Interfaz adaptable a diferentes tamaños
- **Navegación Intuitiva**: Organización clara por funcionalidad

### Seguridad Robusta
- **Políticas de Contraseñas**: Configurables y robustas
- **Sesiones Seguras**: Tokens con expiración
- **Auditoría**: Registro completo de acciones
- **Protección contra Ataques**: Validación de entrada y sanitización

## 🐛 Solución de Problemas

### Errores Comunes

**Error: wxWidgets not found**
- Windows: Configurar `wxWidgets_ROOT_DIR` en CMake
- Linux: `sudo apt-get install libwxgtk3.0-gtk3-dev`
- macOS: `brew install wxmac`

**Error: SQLite not found**
- Windows: Descargar SQLite y configurar `SQLite3_DIR`
- Linux: `sudo apt-get install libsqlite3-dev`
- macOS: `brew install sqlite3`

**Error: C++17 features not supported**
- Actualizar el compilador a una versión que soporte C++17
- Para VS: Actualizar a Visual Studio 2017 o superior
- Para GCC: Usar GCC 7 o superior

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