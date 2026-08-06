# Local build script for SDEP_CPP5
# This script is designed for local development on Windows

# Create build directory
if (Test-Path build) {
    Remove-Item -Recurse -Force build
}
mkdir build
cd build

# Disable GitHub Actions binary caching for local development
$env:VCPKG_BINARY_SOURCES = "clear"

# Get vcpkg root (assuming vcpkg is in a standard location or use VCPKG_ROOT if set)
$vcpkgRoot = if ($env:VCPKG_ROOT) { $env:VCPKG_ROOT } else { "C:\vcpkg" }

# Check if vcpkg exists
if (-not (Test-Path $vcpkgRoot)) {
    Write-Host "Error: vcpkg not found at $vcpkgRoot"
    Write-Host "Please install vcpkg or set VCPKG_ROOT environment variable"
    Write-Host "You can install vcpkg from: https://vcpkg.io/en/getting-started"
    exit 1
}

Write-Host "Using vcpkg at: $vcpkgRoot"

# Try to detect available generators
$useNinja = $false
try {
    $ninjaVersion = ninja --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $useNinja = $true
        Write-Host "Found Ninja, using Ninja generator"
    }
} catch {
    Write-Host "Ninja not found, will use Visual Studio generator"
}

# Configure with CMake using vcpkg toolchain
Write-Host "Configuring with CMake..."
if ($useNinja) {
    cmake .. -G "Ninja" `
        -DCMAKE_BUILD_TYPE=Release `
        -DCMAKE_TOOLCHAIN_FILE="$vcpkgRoot/scripts/buildsystems/vcpkg.cmake" `
        -DVCPKG_MANIFEST_MODE=ON
} else {
    cmake .. -G "Visual Studio 17 2022" -A x64 `
        -DCMAKE_BUILD_TYPE=Release `
        -DCMAKE_TOOLCHAIN_FILE="$vcpkgRoot/scripts/buildsystems/vcpkg.cmake" `
        -DVCPKG_MANIFEST_MODE=ON
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "CMake configuration failed"
    exit 1
}

# Build the project
Write-Host "Building project..."
if ($useNinja) {
    ninja
} else {
    cmake --build . --config Release
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed"
    exit 1
}

Write-Host "Build completed successfully!"
