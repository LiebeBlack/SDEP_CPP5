@echo off
REM Script de compilación automatizado para Windows
REM SDEP Educational Management System - C++ Version
REM Updated for 2026 - C++20, CMake 3.20+

echo ====================================
echo SDEP C++ Build Script (2026 Edition)
echo ====================================
echo.

REM Verificar si existe el directorio build
if not exist build (
    echo Creando directorio build...
    mkdir build
)

cd build

echo Configurando con CMake (C++20)...
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_CXX_STANDARD=20 -DCMAKE_CXX_STANDARD_REQUIRED=ON
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: CMake configuration failed
    echo Intentando con Visual Studio 16 2019...
    cmake .. -G "Visual Studio 16 2019" -A x64 -DCMAKE_CXX_STANDARD=20 -DCMAKE_CXX_STANDARD_REQUIRED=ON
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: CMake configuration failed
        exit /b 1
    )
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
echo BUILD EXITOSO - CERO ERRORES
echo ====================================
echo Ejecutable: build\Release\SDEP.exe
echo C++ Standard: C++20
echo.

pause