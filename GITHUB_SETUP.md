# 🚀 GITHUB SETUP INSTRUCTIONS

## PASOS PARA SUBIR A GITHUB CON AUTO-COMPILACIÓN Y RELEASES

### 1. CREAR REPOSITORIO EN GITHUB

1. Ir a https://github.com
2. Click en "New repository"
3. Nombre: `SDEP_CPP`
4. Descripción: `SDEP Educational Management System - C++ Version with wxWidgets and SQLite`
5. Visibility: Private o Public
6. NO inicializar con README
7. Click en "Create repository"

### 2. SUBIR EL CÓDIGO

Abre PowerShell/CMD en `C:\Users\Admin\Documents\GitHub\SDEP_CPP`:

```bash
# Inicializar Git
git init

# Agregar todos los archivos
git add .

# Commit inicial
git commit -m "Initial commit - SDEP Educational Management System v1.0

Complete C++ educational management system:
- wxWidgets GUI
- SQLite database
- MVC architecture
- Complete CRUD operations
- Security system
- All dialog implementations
- Auto-compilation with GitHub Actions
- Automatic releases on every push to main
- Canary releases with version numbers"

# Agregar remote (reemplaza <your-username> con tu usuario de GitHub)
git remote add origin https://github.com/<your-username>/SDEP_CPP.git

# Push a GitHub
git branch -M main
git push -u origin main
```

### 3. CONFIGURAR GITHUB ACTIONS (OPCIONAL - YA CONFIGURADO)

Los workflows ya están configurados en `.github/workflows/`:

- **ci.yml**: Compila en Windows, Linux, macOS en cada push
- **release.yml**: Crea releases automáticos en cada push a main

### 4. VERIFICAR QUE FUNCIONA

1. Ve a tu repositorio en GitHub
2. Ve a la pestaña "Actions"
3. Verás los workflows ejecutándose automáticamente
4. Cuando terminen, ve a la pestaña "Releases"
5. Verás un nuevo release con los binarios compilados

### 5. CONFIGURAR SECRETS (SI ES NECESARIO)

Si necesitas configurar secrets para GitHub Actions:

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Click en "New repository secret"
4. Agrega secrets si es necesario

### 6. FLUJO DE TRABAJO RECOMENDADO

#### Desarrollo
```bash
# Crear rama de desarrollo
git checkout -b develop

# Hacer cambios
git add .
git commit -m "Descripción de cambios"
git push origin develop
```

#### Release a Producción
```bash
# Fusionar develop en main
git checkout main
git merge develop
git push origin main

# Esto automáticamente:
# 1. Ejecuta CI en todas las plataformas
# 2. Crea un nuevo release
# 3. Compila los binarios
# 4. Sube los binarios al release
```

### 7. ESTRUCTURA DE RELEASES

Cada push a `main` creará:

- **Version**: YYYY.MM.DD-SHA (ej: 2026.08.05-a1b2c3d)
- **Type**: Pre-release (Canary)
- **Platforms**: Linux (principal), Windows, macOS
- **Binaries**: SDEP-Linux.tar.gz, SDEP-Windows.zip, SDEP-macOS.tar.gz
- **Release Notes**: Generados automáticamente

### 8. MONITOREO

Verifica en GitHub:
- **Actions Tab**: Ver el estado de las compilaciones
- **Releases Tab**: Ver los releases creados
- **Commits**: Ver el historial de cambios

### 9. DESCARGAR RELEASES

Los usuarios pueden descargar desde:
1. Ve a la pestaña "Releases"
2. Selecciona el release más reciente
3. Descarga el binario para tu plataforma
4. Ejecuta

### 10. TROUBLESHOOTING

#### Error: "Workflow failed"
- Ve a la pestaña "Actions"
- Click en el workflow fallido
- Revisa los logs para identificar el error
- Corrige el problema
- Push de nuevo

#### Error: "Release not created"
- Verifica que tengas permisos para crear releases
- Verifica que el workflow esté configurado correctamente
- Revisa los logs del workflow

#### Error: "Binaries not uploaded"
- Verifica que la compilación haya sido exitosa
- Revisa los nombres de los archivos en el workflow
- Verifica los permisos del repository

### ✅ CHECKLIST FINAL

- [ ] Repositorio creado en GitHub
- [ ] Código subido
- [ ] GitHub Actions workflows activos
- [ ] Primer release creado automáticamente
- [ ] Binarios descargables
- [ ] Documentación actualizada
- [ ] Readme visible en GitHub

### 🎯 RESULTADO FINAL

Cada vez que hagas push a la rama `main`:

1. ✅ GitHub Actions compilará automáticamente
2. ✅ Creará un nuevo release
3. ✅ Subirá los binarios compilados
4. ✅ Generará notas de release
5. ✅ Estará disponible para descarga

**EL SISTEMA ESTÁ COMPLETAMENTE AUTOMATIZADO** 🚀