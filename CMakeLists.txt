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
find_package(wxWidgets REQUIRED COMPONENTS core base net)
find_package(unofficial-sqlite3 CONFIG REQUIRED)
find_package(Threads REQUIRED)

# Check if packages are found
if(NOT wxWidgets_FOUND)
    message(FATAL_ERROR "wxWidgets not found")
endif()
if(NOT Threads_FOUND)
    message(FATAL_ERROR "Threads not found")
endif()

# Include wxWidgets
include(${wxWidgets_USE_FILE})

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
)

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
target_link_libraries(${PROJECT_NAME}
    ${wxWidgets_LIBRARIES}
    unofficial::sqlite3::sqlite3
    ${CMAKE_THREAD_LIBS_INIT}
)

# Set target properties
set_target_properties(${PROJECT_NAME} PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
    CXX_EXTENSIONS OFF
)

# Installation
install(TARGETS ${PROJECT_NAME}
    RUNTIME DESTINATION bin
)
