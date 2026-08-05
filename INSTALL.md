# Guía de Instalación - SDEP Educational Management System C++

## Requisitos Previos

### Windows
- Windows 10 o superior
- Visual Studio 2017 o superior (con C++ support)
- CMake 3.15 o superior
- Git

### Linux (Ubuntu/Debian)
- Ubuntu 18.04+ o Debian 11+
- GCC 7+ o Clang 5+
- CMake 3.15+
- Git

### macOS
- macOS 10.14+
- Xcode Command Line Tools
- CMake 3.15+
- Homebrew
- Git

## Instalación de Dependencias

### Windows

1. **Instalar Visual Studio**
   - Descargar desde: https://visualstudio.microsoft.com/
   - Durante instalación, seleccionar "Desktop development with C++"

2. **Instalar CMake**
   - Descargar desde: https://cmake.org/download/
   - Agregar CMake al PATH del sistema

3. **Instalar wxWidgets**
   - Descargar desde: https://www.wxwidgets.org/downloads/
   - Configurar variables de entorno para wxWidgets

4. **Instalar Git**
   - Descargar desde: https://git-scm.com/download/win

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install build-essential cmake git
sudo apt-get install libwxgtk3.0-gtk3-dev libsqlite3-dev
```

### macOS

```bash
# Instalar Xcode Command Line Tools
xcode-select --install

# Instalar Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependencias
brew install cmake wxmac sqlite3 git
```

## Compilación del Proyecto

### Clonar el Repositorio

```bash
git clone <repository-url>
cd SDEP_CPP
```

### Windows (Visual Studio)

```bash
mkdir build
cd build
cmake .. -G "Visual Studio 16 2019" -A x64
cmake --build . --config Release
```

El ejecutable se generará en `build/Release/SDEP.exe`

### Linux

```bash
mkdir build
cd build
cmake ..
make -j$(nproc)
```

El ejecutable se generará en `build/SDEP`

### macOS

```bash
mkdir build
cd build
cmake ..
make -j$(sysctl -n hw.ncpu)
```

El ejecutable se generará en `build/SDEP`

## Ejecución

### Windows
```bash
cd build/Release
./SDEP.exe
```

### Linux/macOS
```bash
cd build
./SDEP
```

## Configuración Inicial

1. **Primer Login**
   - Usuario: `admin`
   - Contraseña: `Admin123!`

2. **Cambiar Contraseña**
   - Importante: Cambiar la contraseña por defecto inmediatamente

3. **Configurar Base de Datos**
   - La base de datos se crea automáticamente en `institution.db`
   - Se puede cambiar la ruta en Configuración → Database

## Solución de Problemas

### Errores Comunes de Compilación

**Error: "wxWidgets not found"**
- Windows: Configurar `wxWidgets_ROOT_DIR` en CMake
- Linux: `sudo apt-get install libwxgtk3.0-gtk3-dev`
- macOS: `brew install wxmac`

**Error: "SQLite not found"**
- Windows: Descargar SQLite y configurar `SQLite3_DIR`
- Linux: `sudo apt-get install libsqlite3-dev`
- macOS: `brew install sqlite3`

**Error: "C++17 features not supported"**
- Actualizar el compilador a una versión que soporte C++17
- Para VS: Actualizar a Visual Studio 2017 o superior
- Para GCC: Usar GCC 7 o superior

### Errores de Ejecución

**Error: "Database connection failed"**
- Verificar permisos de escritura en el directorio
- Asegurarse de que no haya otra instancia usando la base de datos

**Error: "Failed to load services"**
- Verificar que todos los módulos estén compilados correctamente
- Revisar el log para más detalles

## Configuración Avanzada

### Variables de CMake

```bash
# Forzar compilación en modo Debug
cmake .. -DCMAKE_BUILD_TYPE=Debug

# Cambiar directorio de instalación
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local

# Habilitar warnings adicionales
cmake .. -DCMAKE_CXX_FLAGS="-Wall -Wextra"
```

### Dependencias Opcionales

El proyecto puede funcionar con las siguientes bibliotecas opcionales:

- **wxWidgets additional components**: stc, aui, html
- **SQLite extensions**: FTS5, JSON1
- **Logging libraries**: spdlog, g3log

## Verificación de Instalación

Para verificar que la instalación fue exitosa:

```bash
# Ejecutar el programa
./SDEP

# Intentar iniciar sesión con credenciales por defecto
# Usuario: admin
# Contraseña: Admin123!
```

Si el login es exitoso y el dashboard muestra las estadísticas, la instalación está correcta.

## Soporte

Para problemas de instalación, consulte:
- Documentación de wxWidgets: https://docs.wxwidgets.org/
- Documentación de CMake: https://cmake.org/documentation/
- Issues del proyecto: <repository-issues>

## Actualización

Para actualizar a una nueva versión:

```bash
cd SDEP_CPP
git pull origin main
cd build
cmake ..
make  # o cmake --build . para Windows
```