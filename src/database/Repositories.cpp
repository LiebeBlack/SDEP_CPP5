#include "database/Repositories.h"
#include <sstream>
#include <algorithm>

namespace SDEP {
namespace Database {

// Student repository implementation
StudentRepository::StudentRepository(DatabaseManager& db)
    : BaseRepository(db, "students") {}

std::vector<Models::Student> StudentRepository::getAll() {
    auto result = db_.executeQuery("SELECT * FROM students", {});
    std::vector<Models::Student> students;
    
    for (const auto& row : result) {
        students.push_back(Models::Student::fromDBPairs(row));
    }
    
    return students;
}

Models::Student StudentRepository::getById(int id) {
    auto result = db_.executeQuery("SELECT * FROM students WHERE id = ?", {std::to_string(id)});
    
    if (!result.empty()) {
        return Models::Student::fromDBPairs(result[0]);
    }
    
    return Models::Student(); // Return empty student
}

int StudentRepository::create(const Models::Student& student) {
    auto pairs = student.toDBPairs();
    std::vector<std::string> columns;
    std::vector<std::string> values;
    
    for (const auto& pair : pairs) {
        if (pair.first != "id") { // Skip auto-increment ID
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    
    std::string query = buildInsertQuery(columns);
    return db_.executeInsert(query, values);
}

bool StudentRepository::update(const Models::Student& student) {
    auto pairs = student.toDBPairs();
    std::vector<std::string> columns;
    std::vector<std::string> values;
    
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    
    values.push_back(std::to_string(student.id)); // Add ID for WHERE clause
    
    std::string query = buildUpdateQuery(columns);
    return db_.executeUpdate(query, values) > 0;
}

bool StudentRepository::deleteById(int id) {
    return db_.executeUpdate("DELETE FROM students WHERE id = ?", {std::to_string(id)}) > 0;
}

int StudentRepository::count() {
    return db_.getRowCount("students");
}

std::vector<Models::Student> StudentRepository::getByGrade(const std::string& grade) {
    auto result = db_.executeQuery("SELECT * FROM students WHERE grade = ?", {grade});
    std::vector<Models::Student> students;
    
    for (const auto& row : result) {
        students.push_back(Models::Student::fromDBPairs(row));
    }
    
    return students;
}

std::vector<Models::Student> StudentRepository::getActiveStudents() {
    auto result = db_.executeQuery("SELECT * FROM students WHERE active = 1", {});
    std::vector<Models::Student> students;
    
    for (const auto& row : result) {
        students.push_back(Models::Student::fromDBPairs(row));
    }
    
    return students;
}

std::vector<Models::Student> StudentRepository::searchByName(const std::string& name) {
    auto result = db_.executeQuery("SELECT * FROM students WHERE first_name LIKE ? OR last_name LIKE ?", 
                                   {"%" + name + "%", "%" + name + "%"});
    std::vector<Models::Student> students;
    
    for (const auto& row : result) {
        students.push_back(Models::Student::fromDBPairs(row));
    }
    
    return students;
}

// Teacher repository implementation
TeacherRepository::TeacherRepository(DatabaseManager& db)
    : BaseRepository(db, "teachers") {}

std::vector<Models::Teacher> TeacherRepository::getAll() {
    auto result = db_.executeQuery("SELECT * FROM teachers", {});
    std::vector<Models::Teacher> teachers;
    
    for (const auto& row : result) {
        teachers.push_back(Models::Teacher::fromDBPairs(row));
    }
    
    return teachers;
}

Models::Teacher TeacherRepository::getById(int id) {
    auto result = db_.executeQuery("SELECT * FROM teachers WHERE id = ?", {std::to_string(id)});
    
    if (!result.empty()) {
        return Models::Teacher::fromDBPairs(result[0]);
    }
    
    return Models::Teacher();
}

int TeacherRepository::create(const Models::Teacher& teacher) {
    auto pairs = teacher.toDBPairs();
    std::vector<std::string> columns;
    std::vector<std::string> values;
    
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    
    std::string query = buildInsertQuery(columns);
    return db_.executeInsert(query, values);
}

bool TeacherRepository::update(const Models::Teacher& teacher) {
    auto pairs = teacher.toDBPairs();
    std::vector<std::string> columns;
    std::vector<std::string> values;
    
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    
    values.push_back(std::to_string(teacher.id));
    
    std::string query = buildUpdateQuery(columns);
    return db_.executeUpdate(query, values) > 0;
}

bool TeacherRepository::deleteById(int id) {
    return db_.executeUpdate("DELETE FROM teachers WHERE id = ?", {std::to_string(id)}) > 0;
}

int TeacherRepository::count() {
    return db_.getRowCount("teachers");
}

std::vector<Models::Teacher> TeacherRepository::getByDepartment(const std::string& department) {
    auto result = db_.executeQuery("SELECT * FROM teachers WHERE department = ?", {department});
    std::vector<Models::Teacher> teachers;
    
    for (const auto& row : result) {
        teachers.push_back(Models::Teacher::fromDBPairs(row));
    }
    
    return teachers;
}

std::vector<Models::Teacher> TeacherRepository::getActiveTeachers() {
    auto result = db_.executeQuery("SELECT * FROM teachers WHERE active = 1", {});
    std::vector<Models::Teacher> teachers;
    
    for (const auto& row : result) {
        teachers.push_back(Models::Teacher::fromDBPairs(row));
    }
    
    return teachers;
}

std::vector<Models::Teacher> TeacherRepository::searchByName(const std::string& name) {
    auto result = db_.executeQuery("SELECT * FROM teachers WHERE first_name LIKE ? OR last_name LIKE ?", 
                                   {"%" + name + "%", "%" + name + "%"});
    std::vector<Models::Teacher> teachers;
    
    for (const auto& row : result) {
        teachers.push_back(Models::Teacher::fromDBPairs(row));
    }
    
    return teachers;
}

// Course repository implementation
CourseRepository::CourseRepository(DatabaseManager& db)
    : BaseRepository(db, "courses") {}

std::vector<Models::Course> CourseRepository::getAll() {
    auto result = db_.executeQuery("SELECT * FROM courses", {});
    std::vector<Models::Course> courses;
    
    for (const auto& row : result) {
        courses.push_back(Models::Course::fromDBPairs(row));
    }
    
    return courses;
}

Models::Course CourseRepository::getById(int id) {
    auto result = db_.executeQuery("SELECT * FROM courses WHERE id = ?", {std::to_string(id)});
    
    if (!result.empty()) {
        return Models::Course::fromDBPairs(result[0]);
    }
    
    return Models::Course();
}

int CourseRepository::create(const Models::Course& course) {
    auto pairs = course.toDBPairs();
    std::vector<std::string> columns;
    std::vector<std::string> values;
    
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    
    std::string query = buildInsertQuery(columns);
    return db_.executeInsert(query, values);
}

bool CourseRepository::update(const Models::Course& course) {
    auto pairs = course.toDBPairs();
    std::vector<std::string> columns;
    std::vector<std::string> values;
    
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    
    values.push_back(std::to_string(course.id));
    
    std::string query = buildUpdateQuery(columns);
    return db_.executeUpdate(query, values) > 0;
}

bool CourseRepository::deleteById(int id) {
    return db_.executeUpdate("DELETE FROM courses WHERE id = ?", {std::to_string(id)}) > 0;
}

int CourseRepository::count() {
    return db_.getRowCount("courses");
}

std::vector<Models::Course> CourseRepository::getByLevel(const std::string& level) {
    auto result = db_.executeQuery("SELECT * FROM courses WHERE level = ?", {level});
    std::vector<Models::Course> courses;
    
    for (const auto& row : result) {
        courses.push_back(Models::Course::fromDBPairs(row));
    }
    
    return courses;
}

std::vector<Models::Course> CourseRepository::getByTeacher(int teacher_id) {
    auto result = db_.executeQuery("SELECT * FROM courses WHERE teacher_id = ?", {std::to_string(teacher_id)});
    std::vector<Models::Course> courses;
    
    for (const auto& row : result) {
        courses.push_back(Models::Course::fromDBPairs(row));
    }
    
    return courses;
}

std::vector<Models::Course> CourseRepository::getActiveCourses() {
    auto result = db_.executeQuery("SELECT * FROM courses WHERE active = 1", {});
    std::vector<Models::Course> courses;
    
    for (const auto& row : result) {
        courses.push_back(Models::Course::fromDBPairs(row));
    }
    
    return courses;
}

Models::Course CourseRepository::getByCode(const std::string& code) {
    auto result = db_.executeQuery("SELECT * FROM courses WHERE code = ?", {code});
    
    if (!result.empty()) {
        return Models::Course::fromDBPairs(result[0]);
    }
    
    return Models::Course();
}

// Simplified implementations for remaining repositories
EnrollmentRepository::EnrollmentRepository(DatabaseManager& db)
    : BaseRepository(db, "enrollments") {}

std::vector<Models::Enrollment> EnrollmentRepository::getAll() {
    auto result = db_.executeQuery("SELECT * FROM enrollments", {});
    std::vector<Models::Enrollment> enrollments;
    
    for (const auto& row : result) {
        enrollments.push_back(Models::Enrollment::fromDBPairs(row));
    }
    
    return enrollments;
}

Models::Enrollment EnrollmentRepository::getById(int id) {
    auto result = db_.executeQuery("SELECT * FROM enrollments WHERE id = ?", {std::to_string(id)});
    if (!result.empty()) return Models::Enrollment::fromDBPairs(result[0]);
    return Models::Enrollment();
}

int EnrollmentRepository::create(const Models::Enrollment& enrollment) {
    auto pairs = enrollment.toDBPairs();
    std::vector<std::string> columns, values;
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    return db_.executeInsert(buildInsertQuery(columns), values);
}

bool EnrollmentRepository::update(const Models::Enrollment& enrollment) {
    auto pairs = enrollment.toDBPairs();
    std::vector<std::string> columns, values;
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    values.push_back(std::to_string(enrollment.id));
    return db_.executeUpdate(buildUpdateQuery(columns), values) > 0;
}

bool EnrollmentRepository::deleteById(int id) {
    return db_.executeUpdate("DELETE FROM enrollments WHERE id = ?", {std::to_string(id)}) > 0;
}

int EnrollmentRepository::count() { return db_.getRowCount("enrollments"); }
std::vector<Models::Enrollment> EnrollmentRepository::getByStudent(int student_id) {
    auto result = db_.executeQuery("SELECT * FROM enrollments WHERE student_id = ?", {std::to_string(student_id)});
    std::vector<Models::Enrollment> enrollments;
    for (const auto& row : result) enrollments.push_back(Models::Enrollment::fromDBPairs(row));
    return enrollments;
}
std::vector<Models::Enrollment> EnrollmentRepository::getByCourse(int course_id) {
    auto result = db_.executeQuery("SELECT * FROM enrollments WHERE course_id = ?", {std::to_string(course_id)});
    std::vector<Models::Enrollment> enrollments;
    for (const auto& row : result) enrollments.push_back(Models::Enrollment::fromDBPairs(row));
    return enrollments;
}
std::vector<Models::Enrollment> EnrollmentRepository::getActiveEnrollments() {
    auto result = db_.executeQuery("SELECT * FROM enrollments WHERE status = 'Active'", {});
    std::vector<Models::Enrollment> enrollments;
    for (const auto& row : result) enrollments.push_back(Models::Enrollment::fromDBPairs(row));
    return enrollments;
}

// Attendance repository (simplified)
AttendanceRepository::AttendanceRepository(DatabaseManager& db)
    : BaseRepository(db, "attendance") {}

std::vector<Models::Attendance> AttendanceRepository::getAll() {
    auto result = db_.executeQuery("SELECT * FROM attendance", {});
    std::vector<Models::Attendance> attendance;
    for (const auto& row : result) attendance.push_back(Models::Attendance::fromDBPairs(row));
    return attendance;
}

Models::Attendance AttendanceRepository::getById(int id) {
    auto result = db_.executeQuery("SELECT * FROM attendance WHERE id = ?", {std::to_string(id)});
    if (!result.empty()) return Models::Attendance::fromDBPairs(result[0]);
    return Models::Attendance();
}

int AttendanceRepository::create(const Models::Attendance& attendance) {
    auto pairs = attendance.toDBPairs();
    std::vector<std::string> columns, values;
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    return db_.executeInsert(buildInsertQuery(columns), values);
}

bool AttendanceRepository::update(const Models::Attendance& attendance) {
    auto pairs = attendance.toDBPairs();
    std::vector<std::string> columns, values;
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    values.push_back(std::to_string(attendance.id));
    return db_.executeUpdate(buildUpdateQuery(columns), values) > 0;
}

bool AttendanceRepository::deleteById(int id) {
    return db_.executeUpdate("DELETE FROM attendance WHERE id = ?", {std::to_string(id)}) > 0;
}

int AttendanceRepository::count() { return db_.getRowCount("attendance"); }
std::vector<Models::Attendance> AttendanceRepository::getByStudent(int student_id) {
    auto result = db_.executeQuery("SELECT * FROM attendance WHERE student_id = ?", {std::to_string(student_id)});
    std::vector<Models::Attendance> attendance;
    for (const auto& row : result) attendance.push_back(Models::Attendance::fromDBPairs(row));
    return attendance;
}
std::vector<Models::Attendance> AttendanceRepository::getByCourse(int course_id) {
    auto result = db_.executeQuery("SELECT * FROM attendance WHERE course_id = ?", {std::to_string(course_id)});
    std::vector<Models::Attendance> attendance;
    for (const auto& row : result) attendance.push_back(Models::Attendance::fromDBPairs(row));
    return attendance;
}
std::vector<Models::Attendance> AttendanceRepository::getByDate(const std::string& date) {
    auto result = db_.executeQuery("SELECT * FROM attendance WHERE date = ?", {date});
    std::vector<Models::Attendance> attendance;
    for (const auto& row : result) attendance.push_back(Models::Attendance::fromDBPairs(row));
    return attendance;
}
std::vector<Models::Attendance> AttendanceRepository::getByStudentAndCourse(int student_id, int course_id) {
    auto result = db_.executeQuery("SELECT * FROM attendance WHERE student_id = ? AND course_id = ?", 
                                   {std::to_string(student_id), std::to_string(course_id)});
    std::vector<Models::Attendance> attendance;
    for (const auto& row : result) attendance.push_back(Models::Attendance::fromDBPairs(row));
    return attendance;
}

// Employee repository (simplified)
EmployeeRepository::EmployeeRepository(DatabaseManager& db)
    : BaseRepository(db, "employees") {}

std::vector<Models::Employee> EmployeeRepository::getAll() {
    auto result = db_.executeQuery("SELECT * FROM employees", {});
    std::vector<Models::Employee> employees;
    for (const auto& row : result) employees.push_back(Models::Employee::fromDBPairs(row));
    return employees;
}

Models::Employee EmployeeRepository::getById(int id) {
    auto result = db_.executeQuery("SELECT * FROM employees WHERE id = ?", {std::to_string(id)});
    if (!result.empty()) return Models::Employee::fromDBPairs(result[0]);
    return Models::Employee();
}

int EmployeeRepository::create(const Models::Employee& employee) {
    auto pairs = employee.toDBPairs();
    std::vector<std::string> columns, values;
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    return db_.executeInsert(buildInsertQuery(columns), values);
}

bool EmployeeRepository::update(const Models::Employee& employee) {
    auto pairs = employee.toDBPairs();
    std::vector<std::string> columns, values;
    for (const auto& pair : pairs) {
        if (pair.first != "id") {
            columns.push_back(pair.first);
            values.push_back(pair.second);
        }
    }
    values.push_back(std::to_string(employee.id));
    return db_.executeUpdate(buildUpdateQuery(columns), values) > 0;
}

bool EmployeeRepository::deleteById(int id) {
    return db_.executeUpdate("UPDATE employees SET employee_status = 'terminated' WHERE id = ?", 
                             {std::to_string(id)}) > 0;
}

int EmployeeRepository::count() { return db_.getRowCount("employees"); }
Models::Employee EmployeeRepository::getByCode(const std::string& code) {
    auto result = db_.executeQuery("SELECT * FROM employees WHERE employee_code = ?", {code});
    if (!result.empty()) return Models::Employee::fromDBPairs(result[0]);
    return Models::Employee();
}
Models::Employee EmployeeRepository::getByIdNumber(const std::string& id_number) {
    auto result = db_.executeQuery("SELECT * FROM employees WHERE id_number = ?", {id_number});
    if (!result.empty()) return Models::Employee::fromDBPairs(result[0]);
    return Models::Employee();
}
std::vector<Models::Employee> EmployeeRepository::getByDepartment(const std::string& department) {
    auto result = db_.executeQuery("SELECT * FROM employees WHERE department = ? AND employee_status = 'active'", 
                                   {department});
    std::vector<Models::Employee> employees;
    for (const auto& row : result) employees.push_back(Models::Employee::fromDBPairs(row));
    return employees;
}
std::vector<Models::Employee> EmployeeRepository::getActiveEmployees() {
    auto result = db_.executeQuery("SELECT * FROM employees WHERE employee_status = 'active'", {});
    std::vector<Models::Employee> employees;
    for (const auto& row : result) employees.push_back(Models::Employee::fromDBPairs(row));
    return employees;
}
std::vector<Models::Employee> EmployeeRepository::search(const std::string& query) {
    auto result = db_.executeQuery(
        "SELECT * FROM employees WHERE (first_name LIKE ? OR last_name LIKE ? OR employee_code LIKE ? OR id_number LIKE ?) AND employee_status = 'active'",
        {"%" + query + "%", "%" + query + "%", "%" + query + "%", "%" + query + "%"});
    std::vector<Models::Employee> employees;
    for (const auto& row : result) employees.push_back(Models::Employee::fromDBPairs(row));
    return employees;
}

} // namespace Database
} // namespace SDEP