cmake_minimum_required(VERSION 3.20)
project(SDEP VERSION 1.0.0 LANGUAGES CXX)

# C++ Standard (updated for 2026 compatibility)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler flags
if(MSVC)
    add_compile_options(/W4 /permissive-)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# Find packages
find_package(wxWidgets CONFIG REQUIRED)
find_package(Threads REQUIRED)

# Try vcpkg SQLite3 first (for Windows), fall back to system package (Linux/macOS)
find_package(unofficial-sqlite3 CONFIG QUIET)
if(NOT unofficial-sqlite3_FOUND)
    find_package(SQLite3 QUIET)
    if(NOT SQLite3_FOUND)
        # Fallback to direct library linking for systems without SQLite3 package
        set(SQLite3_LIBRARIES sqlite3)
    endif()
endif()

# Check if packages are found
if(NOT Threads_FOUND)
    message(FATAL_ERROR "Threads not found")
endif()

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
)

# Add SQLite3 include directories if using system package
if(NOT unofficial-sqlite3_FOUND AND SQLite3_INCLUDE_DIRS)
    include_directories(${SQLite3_INCLUDE_DIRS})
endif()

# Source files
set(SOURCES
    src/main.cpp
    src/models/Student.cpp
    src/models/Teacher.cpp
    src/models/Course.cpp
    src/models/Enrollment.cpp
    src/models/Attendance.cpp
    src/models/Employee.cpp
    src/database/DatabaseManager.cpp
    src/database/Repositories.cpp
    src/services/StudentService.cpp
    src/services/TeacherService.cpp
    src/services/CourseService.cpp
    src/services/EnrollmentService.cpp
    src/services/AttendanceService.cpp
    src/services/EmployeeService.cpp
    src/services/SecurityManager.cpp
    src/gui/MainFrame.cpp
    src/gui/LoginDialog.cpp
    src/gui/StudentDialog.cpp
    src/gui/TeacherDialog.cpp
    src/gui/CourseDialog.cpp
    src/gui/EmployeeDialog.cpp
    src/gui/EnrollmentDialog.cpp
    src/gui/AttendanceDialog.cpp
)

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Link libraries
if(unofficial-sqlite3_FOUND)
    target_link_libraries(${PROJECT_NAME}
        PRIVATE
        wx::core
        wx::base
        wx::net
        unofficial::sqlite3::sqlite3
        Threads::Threads
    )
else()
    target_link_libraries(${PROJECT_NAME}
        PRIVATE
        wx::core
        wx::base
        wx::net
        ${SQLite3_LIBRARIES}
        Threads::Threads
    )
endif()

# Set target properties
set_target_properties(${PROJECT_NAME} PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
    WIN32_EXECUTABLE TRUE
)

# For Windows, explicitly set subsystem to WINDOWS
if(WIN32)
    set_target_properties(${PROJECT_NAME} PROPERTIES
        LINK_FLAGS "/SUBSYSTEM:WINDOWS"
    )
endif()

# Installation
install(TARGETS ${PROJECT_NAME}
    RUNTIME DESTINATION bin
)
