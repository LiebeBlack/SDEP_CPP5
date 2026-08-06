# Local Build Instructions

The project is configured for GitHub Actions CI/CD, but for local development you need to use alternative build scripts.

## Build Script Options

### Option 1: Using vcpkg (Recommended)
**Script:** `build_local.ps1`

This script uses vcpkg to manage dependencies and will automatically download and build wxWidgets and SQLite3.

**Prerequisites:**
- Install vcpkg from https://vcpkg.io/en/getting-started
- Set the `VCPKG_ROOT` environment variable to your vcpkg installation path
- Or ensure vcpkg is installed at `C:\vcpkg`

**Usage:**
```powershell
.\build_local.ps1
```

### Option 2: Using pre-installed dependencies
**Script:** `build_simple.ps1`

This script assumes you have already installed wxWidgets and SQLite3 on your system and they are accessible to CMake.

**Prerequisites:**
- wxWidgets installed and accessible via CMAKE_PREFIX_PATH or standard system paths
- SQLite3 installed and accessible via CMAKE_PREFIX_PATH or standard system paths

**Usage:**
```powershell
.\build_simple.ps1
```

## Common Issues

### GitHub Actions Build Script Issues
The original build command in the CI workflow is designed for GitHub Actions and will fail locally due to:
1. **Missing GitHub Actions environment variables** - The vcpkg binary caching requires `ACTIONS_RUNTIME_TOKEN` and `ACTIONS_CACHE_URL` which are only available in GitHub Actions
2. **Missing Ninja build system** - The CI uses Ninja which may not be installed locally
3. **GitHub Actions-specific vcpkg configuration** - The vcpkg setup uses GitHub Actions caching that doesn't work locally

### Solution
The local build scripts (`build_local.ps1` and `build_simple.ps1`) are configured to work around these issues by:
- Disabling GitHub Actions binary caching (`VCPKG_BINARY_SOURCES=clear`)
- Detecting available build tools (Ninja or Visual Studio)
- Using local vcpkg installation instead of GitHub Actions setup

## Manual Build Steps

If you prefer to build manually:

1. **Create build directory:**
   ```powershell
   mkdir build
   cd build
   ```

2. **Configure CMake (with vcpkg):**
   ```powershell
   cmake .. -G "Visual Studio 17 2022" -A x64 `
       -DCMAKE_BUILD_TYPE=Release `
       -DCMAKE_TOOLCHAIN_FILE="$env:VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake"
   ```

3. **Build:**
   ```powershell
   cmake --build . --config Release
   ```

## Installing Dependencies

### wxWidgets
- **With vcpkg:** Automatically handled by `build_local.ps1`
- **Manual:** Download from https://www.wxwidgets.org/downloads/ and install to a standard location

### SQLite3
- **With vcpkg:** Automatically handled by `build_local.ps1`
- **Manual:** Download from https://www.sqlite.org/download.html or use package manager

## Development Notes

- The project requires C++20 support
- On Windows, Visual Studio 2022 is recommended
- The CMakeLists.txt specifies wxWidgets components: core, base, net
- SQLite3 is used for database operations
