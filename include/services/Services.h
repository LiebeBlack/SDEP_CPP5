#ifndef SERVICES_H
#define SERVICES_H

#include "models/models.h"
#include "database/Repositories.h"
#include <vector>
#include <memory>
#include <string>
#include <stdexcept>

namespace SDEP {
namespace Services {

class ValidationError : public std::runtime_error {
public:
    explicit ValidationError(const std::string& message) 
        : std::runtime_error(message) {}
};

// Base service class
template<typename T, typename Repo>
class BaseService {
public:
    explicit BaseService(Repo& repository) : repository_(repository) {}
    
    virtual ~BaseService() = default;
    
    virtual std::vector<T> getAll() {
        return repository_.getAll();
    }
    
    virtual T getById(int id) {
        return repository_.getById(id);
    }
    
    virtual int create(T entity) {
        if (!entity.validate()) {
            throw ValidationError("Validation failed");
        }
        return repository_.create(entity);
    }
    
    virtual bool update(T entity) {
        if (!entity.validate()) {
            throw ValidationError("Validation failed");
        }
        return repository_.update(entity);
    }
    
    virtual bool deleteById(int id) {
        return repository_.deleteById(id);
    }
    
    virtual int count() {
        return repository_.count();
    }
    
protected:
    Repo& repository_;
};

// Student service
class StudentService : public BaseService<Models::Student, Database::StudentRepository> {
public:
    explicit StudentService(Database::StudentRepository& repository);
    
    std::vector<Models::Student> getAllStudents();
    Models::Student getStudentById(int id);
    int createStudent(const Models::Student& student);
    bool updateStudent(const Models::Student& student);
    bool deleteStudent(int id);
    
    // Specific operations
    std::vector<Models::Student> getStudentsByGrade(const std::string& grade);
    std::vector<Models::Student> getActiveStudents();
    std::vector<Models::Student> searchStudents(const std::string& name);
    int getStudentCount();
};

// Teacher service
class TeacherService : public BaseService<Models::Teacher, Database::TeacherRepository> {
public:
    explicit TeacherService(Database::TeacherRepository& repository);
    
    std::vector<Models::Teacher> getAllTeachers();
    Models::Teacher getTeacherById(int id);
    int createTeacher(const Models::Teacher& teacher);
    bool updateTeacher(const Models::Teacher& teacher);
    bool deleteTeacher(int id);
    
    // Specific operations
    std::vector<Models::Teacher> getTeachersByDepartment(const std::string& department);
    std::vector<Models::Teacher> getActiveTeachers();
    std::vector<Models::Teacher> searchTeachers(const std::string& name);
    int getTeacherCount();
};

// Course service
class CourseService : public BaseService<Models::Course, Database::CourseRepository> {
public:
    explicit CourseService(Database::CourseRepository& course_repo, 
                          Database::TeacherRepository& teacher_repo);
    
    std::vector<Models::Course> getAllCourses();
    Models::Course getCourseById(int id);
    int createCourse(const Models::Course& course);
    bool updateCourse(const Models::Course& course);
    bool deleteCourse(int id);
    
    // Specific operations
    std::vector<Models::Course> getCoursesByLevel(const std::string& level);
    std::vector<Models::Course> getCoursesByTeacher(int teacher_id);
    std::vector<Models::Course> getActiveCourses();
    Models::Course getCourseByCode(const std::string& code);
    int getCourseCount();
    
private:
    Database::TeacherRepository& teacher_repo_;
};

// Enrollment service
class EnrollmentService : public BaseService<Models::Enrollment, Database::EnrollmentRepository> {
public:
    explicit EnrollmentService(Database::EnrollmentRepository& enrollment_repo,
                             StudentService& student_service,
                             CourseService& course_service);
    
    std::vector<Models::Enrollment> getAllEnrollments();
    Models::Enrollment getEnrollmentById(int id);
    int createEnrollment(const Models::Enrollment& enrollment);
    bool updateEnrollment(const Models::Enrollment& enrollment);
    bool deleteEnrollment(int id);
    
    // Specific operations
    std::vector<Models::Enrollment> getEnrollmentsByStudent(int student_id);
    std::vector<Models::Enrollment> getEnrollmentsByCourse(int course_id);
    std::vector<Models::Enrollment> getActiveEnrollments();
    bool enrollStudentInCourse(int student_id, int course_id);
    bool updateGrade(int enrollment_id, double grade);
    int getEnrollmentCount();
    
private:
    StudentService& student_service_;
    CourseService& course_service_;
};

// Attendance service
class AttendanceService : public BaseService<Models::Attendance, Database::AttendanceRepository> {
public:
    explicit AttendanceService(Database::AttendanceRepository& attendance_repo,
                             StudentService& student_service,
                             CourseService& course_service);
    
    std::vector<Models::Attendance> getAllAttendance();
    Models::Attendance getAttendanceById(int id);
    int createAttendance(const Models::Attendance& attendance);
    bool updateAttendance(const Models::Attendance& attendance);
    bool deleteAttendance(int id);
    
    // Specific operations
    std::vector<Models::Attendance> getAttendanceByStudent(int student_id);
    std::vector<Models::Attendance> getAttendanceByCourse(int course_id);
    std::vector<Models::Attendance> getAttendanceByDate(const std::string& date);
    std::vector<Models::Attendance> getAttendanceByStudentAndCourse(int student_id, int course_id);
    bool markAttendance(int student_id, int course_id, const std::string& date, const std::string& status);
    double calculateAttendancePercentage(int student_id, int course_id);
    int getAttendanceCount();
    
private:
    StudentService& student_service_;
    CourseService& course_service_;
};

// Employee service (HR)
class EmployeeService : public BaseService<Models::Employee, Database::EmployeeRepository> {
public:
    explicit EmployeeService(Database::EmployeeRepository& repository);
    
    std::vector<Models::Employee> getAllEmployees();
    Models::Employee getEmployeeById(int id);
    int createEmployee(const Models::Employee& employee);
    bool updateEmployee(const Models::Employee& employee);
    bool deleteEmployee(int id);
    
    // Specific operations
    Models::Employee getEmployeeByCode(const std::string& code);
    Models::Employee getEmployeeByIdNumber(const std::string& id_number);
    std::vector<Models::Employee> getEmployeesByDepartment(const std::string& department);
    std::vector<Models::Employee> getActiveEmployees();
    std::vector<Models::Employee> searchEmployees(const std::string& query);
    int getEmployeeCount();
    bool terminateEmployee(int id);
};

} // namespace Services
} // namespace SDEP

#endif // SERVICES_H