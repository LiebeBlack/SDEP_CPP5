# Sistema de Gestión de Personal y Nómina

Sistema completo para la gestión de personal y nómina de instituciones educativas, desarrollado en Python con interfaz gráfica CustomTkinter.

## 🚀 Características

### Gestión de Personal
- Registro completo de empleados (Docentes, Administrativos, Mantenimiento)
- Ficha de datos personales, físicos y de contacto
- Gestión de fotos de perfil
- Clasificación por tipo, cargo y departamento
- Búsqueda y filtrado avanzado

### Gestión Documental
- Carga y almacenamiento de documentos digitalizados
- Soporte para PDFs e imágenes
- Clasificación por tipo de documento
- Control de vencimientos
- Gestión de documentos por empleado

### Incidencias y Permisos
- Registro de reposos médicos, ausencias y permisos
- Sistema de aprobación/rechazo
- Gestión de documentos de soporte
- Cálculo automático de días
- Control de incidencias vigentes

### Nómina y Pagos
- Generación automática de nóminas por periodo
- Cálculo de deducciones (seguro, pensión, impuesto)
- Gestión de bonificaciones y horas extra
- Generación de recibos de pago en PDF
- Control de pagos pendientes y realizados

### Generación de Documentos
- Constancias de trabajo
- Constancias de estudios
- Recibos de pago
- Reportes de empleados
- Exportación a PDF

## 📋 Requisitos del Sistema

- Python 3.10 o superior
- Windows 10/11
- 4GB RAM mínimo
- 500MB espacio en disco

## 🔄 CI/CD Pipeline

Este proyecto cuenta con un sistema CI/CD simplificado mediante GitHub Actions:

### Características del CI/CD
- ✅ **Integración Continua**: Tests básicos automáticos
- ✅ **Construcción Automatizada**: Generación de ejecutables Windows
- ✅ **Lanzamientos Automatizados**: Releases con tags
- ✅ **Despliegues Canary**: Pre-releases de prueba

### Workflows Disponibles
- **CI Workflow**: Tests básicos en push a main/develop
- **Build Workflow**: Construcción de ejecutables Windows
- **Release Workflow**: Creación de releases con ejecutables (tags)
- **Canary Deployment**: Pre-releases automáticas (branch canary)

### Documentación del CI/CD
- 📖 [Guía Rápida de Configuración](QUICKSTART_CICD.md)
- 🔧 [Workflows GitHub Actions](.github/workflows/README.md)
- 🤝 [Guía de Contribución](CONTRIBUTING.md)
- **Notifications**: Alertas y monitoreo en tiempo real

### Documentación del CI/CD
- 📖 [Documentación Completa CI/CD](CI_CD_DOCUMENTATION.md)
- ⚡ [Guía Rápida de Configuración](QUICKSTART_CICD.md)
- 🔧 [Workflows GitHub Actions](.github/workflows/README.md)
- 🤝 [Guía de Contribución](CONTRIBUTING.md)

## �🔧 Instalación

### Entorno de Desarrollo

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd NEW TesisFinal
```

2. Crear entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Ejecutar la aplicación:
```bash
python src/main.py
```

### Construcción de Ejecutable

1. Instalar dependencias de desarrollo:
```bash
pip install -r requirements-dev.txt
```

2. Ejecutar script de construcción:
```bash
python build.py
```

3. El ejecutable se generará en `dist/SistemaGestionPersonal/`

## 📁 Estructura del Proyecto

```
project/
├── src/                  # Código fuente
│   ├── gui/              # Componentes GUI
│   ├── models/           # Modelos de datos
│   ├── services/         # Lógica de negocio
│   ├── repositories/     # Data access layer
│   ├── utils/            # Utilidades
│   └── config/           # Configuración
├── tests/                # Tests
├── assets/               # Assets externos
├── docs/                 # Documentación
├── spec/                 # PyInstaller specs
├── requirements.txt      # Dependencias
├── pyproject.toml       # Configuración Python
└── build.py             # Script de build
```

## 🗄️ Base de Datos

El sistema utiliza SQLite como base de datos local. La base de datos se crea automáticamente al iniciar la aplicación y se encuentra en el archivo `personal_management.db`.

## 📖 Uso

### Primeros Pasos

1. **Configuración Inicial**: 
   - Configure los datos de la institución en la sección "Configuración"
   - Establezca los porcentajes de deducciones para nómina

2. **Registro de Empleados**:
   - Vaya a la sección "Empleados"
   - Haga clic en "Nuevo Empleado"
   - Complete los datos personales, laborales y de contacto

3. **Gestión Documental**:
   - Seleccione un empleado
   - Vaya a "Documentos"
   - Cargue documentos digitalizados (cedulas, títulos, etc.)

4. **Incidencias**:
   - Seleccione un empleado
   - Vaya a "Incidencias"
   - Registre permisos, reposos o ausencias
   - Apruebe o rechace solicitudes

5. **Nómina**:
   - Vaya a "Nómina"
   - Seleccione el periodo
   - Genere la nómina automáticamente
   - Genere recibos de pago en PDF

## 🔐 Seguridad

- Los datos se almacenan localmente en SQLite
- No se requiere conexión a internet
- Los documentos se almacenan en el sistema de archivos local
- Se recomienda realizar copias de seguridad periódicas

## 🛠️ Desarrollo

### Ejecutar Tests

```bash
pytest tests/
```

### Formateo de Código

```bash
black src/
isort src/
```

### Linting

```bash
flake8 src/
pylint src/
```

## 📝 Configuración

### Variables de Entorno

Copie `.env.example` a `.env` y configure las variables:

```env
DATABASE_URL=sqlite:///personal_management.db
APP_NAME=Sistema de Gestión de Personal
DEBUG=False
```

### Configuración de la Aplicación

La configuración se puede modificar desde la sección "Configuración" de la aplicación:

- **General**: Nombre de la institución, dirección, contacto
- **Nómina**: Porcentajes de deducciones, salario mínimo
- **Recursos Humanos**: Días de vacaciones, horas laborales

## 🐛 Troubleshooting

### Error al iniciar la aplicación

- Verifique que Python 3.10+ esté instalado
- Instale las dependencias: `pip install -r requirements.txt`
- Verifique que los directorios `documents`, `photos`, `exports` existan

### Error de base de datos

- Elimine el archivo `personal_management.db`
- Reinicie la aplicación para recrear la base de datos

### Problemas con PyInstaller

- Asegúrese de tener PyInstaller instalado: `pip install pyinstaller`
- Verifique que el archivo `spec/app.spec` exista
- Ejecute el script `build.py`

## 📄 Licencia

Este proyecto está bajo licencia MIT.

## 👥 Autores

Desarrollado para gestión de personal en instituciones educativas.

## 📞 Soporte

Para soporte o consultas, contacte al equipo de desarrollo.

---

**Versión**: 1.0.1  
**Última actualización**: 2026
