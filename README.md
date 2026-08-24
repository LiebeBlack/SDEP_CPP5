# Sistema de Gestión de Personal y Nómina

Sistema completo para la gestión de personal y nómina de instituciones educativas, desarrollado en Python con interfaz gráfica CustomTkinter.

## 🎯 Objetivo del Proyecto

Este sistema proporciona una solución integral para la administración de recursos humanos en instituciones educativas, permitiendo gestionar empleados, documentos, incidencias, permisos y nóminas de manera eficiente y organizada.

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

## 🏗️ Arquitectura del Sistema

El sistema sigue una arquitectura en capas separando la lógica de negocio, acceso a datos e interfaz de usuario:

- **Capa de Modelos**: Define la estructura de datos usando SQLAlchemy ORM
- **Capa de Repositorios**: Maneja el acceso a la base de datos
- **Capa de Servicios**: Contiene la lógica de negocio
- **Capa de GUI**: Interfaz gráfica con CustomTkinter
- **Capa de Utilidades**: Funciones auxiliares y helpers

## 🔄 CI/CD Pipeline

Este proyecto cuenta con un sistema CI/CD automatizado mediante GitHub Actions:

### Características del CI/CD
- ✅ **Pre-releases Automáticas**: Cada push a develop crea un release pre-release
- ✅ **Construcción Automatizada**: Generación de ejecutables Windows
- ✅ **Releases Controlados**: Releases oficiales con tags manuales
- ✅ **Ejecutables Automáticos**: Cada release incluye el ejecutable

### Workflows Disponibles
- **Build Workflow**: Construcción + Pre-releases automáticas (push a develop)
- **Release Workflow**: Releases oficiales con ejecutables (tags manuales)

### Documentación del CI/CD
- 📖 [Guía Rápida de Configuración](QUICKSTART_CICD.md)
- 🔧 [Workflows GitHub Actions](.github/workflows/README.md)
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
cd SDEP_CPP5
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
SDEP_CPP5/
├── src/                        # Código fuente principal
│   ├── gui/                    # Interfaz gráfica de usuario
│   │   ├── main_window.py      # Ventana principal
│   │   └── frames.py           # Frames de cada módulo
│   ├── models/                 # Modelos de datos (ORM)
│   │   ├── base.py             # Modelo base
│   │   ├── enums.py            # Enumeraciones
│   │   ├── empleado.py        # Modelo de empleado
│   │   ├── documento.py       # Modelo de documento
│   │   ├── incidencia.py       # Modelo de incidencia
│   │   ├── pago.py            # Modelo de pago
│   │   └── configuracion.py    # Modelo de configuración
│   ├── repositories/           # Acceso a datos
│   │   ├── base_repository.py  # Repositorio base
│   │   ├── empleado_repository.py
│   │   ├── documento_repository.py
│   │   ├── incidencia_repository.py
│   │   ├── pago_repository.py
│   │   └── configuracion_repository.py
│   ├── services/               # Lógica de negocio
│   │   ├── empleado_service.py
│   │   ├── documento_service.py
│   │   ├── incidencia_service.py
│   │   ├── pago_service.py
│   │   └── configuracion_service.py
│   ├── utils/                  # Utilidades y helpers
│   │   ├── helpers.py          # Funciones auxiliares
│   │   ├── validators.py      # Validadores
│   │   ├── document_manager.py # Gestión de documentos
│   │   └── pdf_generator.py    # Generación de PDFs
│   ├── config/                 # Configuración
│   │   ├── settings.py         # Configuración general
│   │   └── database.py         # Configuración de base de datos
│   └── main.py                 # Punto de entrada
├── tests/                      # Pruebas unitarias
├── requirements.txt            # Dependencias del proyecto
├── requirements-dev.txt        # Dependencias de desarrollo
├── pyproject.toml             # Configuración del proyecto
├── build.py                   # Script de construcción
└── .env.example               # Ejemplo de variables de entorno
```

## 🗄️ Base de Datos

El sistema utiliza SQLite como base de datos local. La base de datos se crea automáticamente al iniciar la aplicación y se encuentra en el archivo `personal_management.db`.

### Tablas Principales:
- **empleados**: Información completa de empleados
- **documentos**: Documentos digitalizados de empleados
- **incidencias**: Permisos, reposos y ausencias
- **pagos**: Registro de nóminas y pagos
- **configuraciones**: Configuración del sistema

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

## � Flujo de Trabajo

1. **Configuración Inicial**: Al iniciar el sistema por primera vez, configure los datos de la institución
2. **Registro de Empleados**: Agregue los empleados con sus datos personales y laborales
3. **Gestión Documental**: Cargue los documentos requeridos para cada empleado
4. **Control de Incidencias**: Registre permisos, reposos y ausencias
5. **Procesamiento de Nómina**: Genere nóminas periódicas y emita recibos de pago

## �📝 Configuración

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

**Versión**: 1.0.2  
**Última actualización**: 2026
