cmake_minimum_required(VERSION 3.15)
project(SDEP VERSION 1.0.0 LANGUAGES CXX)

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler flags
if(MSVC)
    add_compile_options(/W4)
else()
    add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find packages
find_package(wxWidgets REQUIRED COMPONENTS core base net)
find_package(SQLite3 REQUIRED)
find_package(Threads REQUIRED)

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
add_executable(${PROJECT_NAME} WIN32 ${SOURCES})

# Link libraries
target_link_libraries(${PROJECT_NAME}
    ${wxWidgets_LIBRARIES}
    ${SQLITE3_LIBRARIES}
    ${CMAKE_THREAD_LIBS_INIT}
)

# Copy resources to build directory
add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_SOURCE_DIR}/resources $<TARGET_FILE_DIR:${PROJECT_NAME}>/resources
)

# Installation
install(TARGETS ${PROJECT_NAME}
    RUNTIME DESTINATION bin
)
