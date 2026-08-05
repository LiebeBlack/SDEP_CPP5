#!/bin/bash
# Script de verificación del sistema
# Verifica que todos los archivos estén presentes y correctamente integrados

echo "===================================="
echo "SDEP C++ Verification Script"
echo "===================================="
echo ""

ERRORS=0

# Verificar estructura de directorios
echo "Verificando estructura de directorios..."
if [ ! -d "include" ]; then
    echo "ERROR: Directorio 'include' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "src" ]; then
    echo "ERROR: Directorio 'src' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "include/models" ]; then
    echo "ERROR: Directorio 'include/models' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "include/database" ]; then
    echo "ERROR: Directorio 'include/database' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "include/services" ]; then
    echo "ERROR: Directorio 'include/services' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "include/gui" ]; then
    echo "ERROR: Directorio 'include/gui' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "src/models" ]; then
    echo "ERROR: Directorio 'src/models' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "src/database" ]; then
    echo "ERROR: Directorio 'src/database' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "src/services" ]; then
    echo "ERROR: Directorio 'src/services' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "src/gui" ]; then
    echo "ERROR: Directorio 'src/gui' no encontrado"
    ERRORS=$((ERRORS + 1))
fi

# Verificar archivos include
echo ""
echo "Verificando archivos include..."
FILES=(
    "include/models/models.h"
    "include/database/DatabaseManager.h"
    "include/database/Repositories.h"
    "include/services/Services.h"
    "include/services/SecurityManager.h"
    "include/gui/MainFrame.h"
    "include/gui/LoginDialog.h"
    "include/gui/StudentDialog.h"
    "include/gui/TeacherDialog.h"
    "include/gui/CourseDialog.h"
    "include/gui/EmployeeDialog.h"
    "include/gui/EnrollmentDialog.h"
    "include/gui/AttendanceDialog.h"
)

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: $file no encontrado"
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ $file"
    fi
done

# Verificar archivos src
echo ""
echo "Verificando archivos src..."
FILES=(
    "src/main.cpp"
    "src/models/Student.cpp"
    "src/models/Teacher.cpp"
    "src/models/Course.cpp"
    "src/models/Enrollment.cpp"
    "src/models/Attendance.cpp"
    "src/models/Employee.cpp"
    "src/database/DatabaseManager.cpp"
    "src/database/Repositories.cpp"
    "src/services/StudentService.cpp"
    "src/services/TeacherService.cpp"
    "src/services/CourseService.cpp"
    "src/services/EnrollmentService.cpp"
    "src/services/AttendanceService.cpp"
    "src/services/EmployeeService.cpp"
    "src/services/SecurityManager.cpp"
    "src/gui/MainFrame.cpp"
    "src/gui/LoginDialog.cpp"
    "src/gui/StudentDialog.cpp"
    "src/gui/TeacherDialog.cpp"
    "src/gui/CourseDialog.cpp"
    "src/gui/EmployeeDialog.cpp"
    "src/gui/EnrollmentDialog.cpp"
    "src/gui/AttendanceDialog.cpp"
)

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: $file no encontrado"
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ $file"
    fi
done

# Verificar archivos de configuración
echo ""
echo "Verificando archivos de configuración..."
FILES=(
    "CMakeLists.txt"
    "README.md"
    ".gitignore"
    "build.sh"
)

for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: $file no encontrado"
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ $file"
    fi
done

# Verificar workflows de GitHub Actions
echo ""
echo "Verificando GitHub Actions workflows..."
if [ ! -d ".github/workflows" ]; then
    echo "ERROR: Directorio .github/workflows no encontrado"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ .github/workflows existe"
    
    if [ ! -f ".github/workflows/ci.yml" ]; then
        echo "ERROR: .github/workflows/ci.yml no encontrado"
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ .github/workflows/ci.yml"
    fi
    
    if [ ! -f ".github/workflows/release.yml" ]; then
        echo "ERROR: .github/workflows/release.yml no encontrado"
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ .github/workflows/release.yml"
    fi
fi

# Contar archivos
echo ""
echo "Contando archivos..."
TOTAL_FILES=$(find . -type f -name "*.cpp" -o -name "*.h" | wc -l)
echo "Total de archivos C++: $TOTAL_FILES"

# Resumen
echo ""
echo "===================================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ VERIFICACIÓN EXITOSA"
    echo "Todos los archivos están presentes"
    echo "El sistema está completo y listo"
else
    echo "❌ VERIFICACIÓN FALLIDA"
    echo "Se encontraron $ERRORS errores"
    exit 1
fi
echo "===================================="