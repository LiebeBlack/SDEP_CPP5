# Simple build script for SDEP_CPP5 without vcpkg
# This assumes wxWidgets and SQLite3 are already installed

# Create build directory
if (Test-Path build) {
    Remove-Item -Recurse -Force build
}
mkdir build
cd build

# Configure with CMake (standard Windows build)
Write-Host "Configuring with CMake (Visual Studio)..."
cmake .. -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "CMake configuration failed"
    Write-Host "Make sure wxWidgets and SQLite3 are installed and accessible"
    exit 1
}

# Build the project
Write-Host "Building project..."
cmake --build . --config Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed"
    exit 1
}

Write-Host "Build completed successfully!"
