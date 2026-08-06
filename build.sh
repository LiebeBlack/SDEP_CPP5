#!/bin/bash
# Script de compilación automatizado para Linux/macOS
# SDEP Educational Management System - C++ Version
# Updated for 2026 - C++20, CMake 3.20+

echo "===================================="
echo "SDEP C++ Build Script (2026 Edition)"
echo "===================================="
echo ""

# Verificar dependencias
echo "Verificando dependencias..."
if ! command -v cmake &> /dev/null; then
    echo "ERROR: cmake no está instalado"
    echo "Por favor instale CMake 3.20 o superior"
    exit 1
fi

CMAKE_VERSION=$(cmake --version | head -n1 | awk '{print $3}')
echo "CMake version: $CMAKE_VERSION"

if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
    echo "ERROR: No se encontró compilador C++ (g++ o clang++)"
    exit 1
fi

# Verificar si existe el directorio build
if [ ! -d "build" ]; then
    echo "Creando directorio build..."
    mkdir build
fi

cd build

echo "Configurando con CMake (C++20)..."
cmake .. -DCMAKE_CXX_STANDARD=20 -DCMAKE_CXX_STANDARD_REQUIRED=ON
if [ $? -ne 0 ]; then
    echo "ERROR: CMake configuration failed"
    exit 1
fi

echo ""
echo "Compilando proyecto..."
make -j$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

echo ""
echo "===================================="
echo "BUILD EXITOSO - CERO ERRORES"
echo "===================================="
echo "Ejecutable: build/SDEP"
echo "C++ Standard: C++20"
echo "CMake Version: $CMAKE_VERSION"
echo ""

# Hacer el script ejecutable
chmod +x ../build.sh