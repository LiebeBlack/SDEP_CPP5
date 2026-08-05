@echo off
REM Script de compilación automatizado para Windows
REM SDEP Educational Management System - C++ Version

echo ====================================
echo SDEP C++ Build Script
echo ====================================
echo.

REM Verificar si existe el directorio build
if not exist build (
    echo Creando directorio build...
    mkdir build
)

cd build

echo Configurando con CMake...
cmake .. -G "Visual Studio 16 2019" -A x64
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CMake configuration failed
    exit /b 1
)

echo.
echo Compilando proyecto...
cmake --build . --config Release
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    exit /b 1
)

echo.
echo ====================================
echo BUILD EXITOSO
echo ====================================
echo Ejecutable: build\Release\SDEP.exe
echo.

pause