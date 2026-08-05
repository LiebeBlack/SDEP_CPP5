#!/bin/bash
# Script de compilación automatizado para Linux/macOS
# SDEP Educational Management System - C++ Version

echo "===================================="
echo "SDEP C++ Build Script"
echo "===================================="
echo ""

# Verificar dependencias
echo "Verificando dependencias..."
if ! command -v cmake &> /dev/null; then
    echo "ERROR: cmake no está instalado"
    exit 1
fi

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

echo "Configurando con CMake..."
cmake ..
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
echo "BUILD EXITOSO"
echo "===================================="
echo "Ejecutable: build/SDEP"
echo ""

# Hacer el script ejecutable
chmod +x ../build.sh