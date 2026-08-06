#ifndef REPOSITORIES_H
#define REPOSITORIES_H

#include "database/DatabaseManager.h"
#include "models/models.h"
#include <vector>
#include <memory>
#include <string>
#include <sstream>
#include <optional>

namespace SDEP {
namespace Database {

// Base repository template
template<typename T>
class BaseRepository {
public:
    explicit BaseRepository(DatabaseManager& db, const std::string& table_name)
        : db_(db), table_name_(table_name) {}
    
    virtual ~BaseRepository() = default;
    
    // CRUD operations
    virtual std::vector<T> getAll() = 0;
    virtual T getById(int id) = 0;
    virtual int create(const T& entity) = 0;
    virtual bool update(const T& entity) = 0;
    virtual bool deleteById(int id) = 0;
    virtual int count() = 0;
    
protected:
    DatabaseManager& db_;
    std::string table_name_;
    
public:
    std::string buildInsertQuery(const std::vector<std::string>& columns) const {
        std::ostringstream oss;
        oss << "INSERT INTO " << table_name_ << " (";
        
        for (size_t i = 0; i < columns.size(); ++i) {
            if (i > 0) oss << ", ";
            oss << columns[i];
        }
        
        oss << ") VALUES (";
        for (size_t i = 0; i < columns.size(); ++i) {
            if (i > 0) oss << ", ";
            oss << "?";
        }
        oss << ")";
        
        return oss.str();
    }
    
    std::string buildUpdateQuery(const std::vector<std::string>& columns) const {
        std::ostringstream oss;
        oss << "UPDATE " << table_name_ << " SET ";
        
        for (size_t i = 0; i < columns.size(); ++i) {
            if (i > 0) oss << ", ";
            oss << columns[i] << " = ?";
        }
        
        oss << " WHERE id = ?";
        return oss.str();
    }
};

// Student repository
class StudentRepository : public BaseRepository<Models::Student> {
public:
    explicit StudentRepository(DatabaseManager& db);
    
    std::vector<Models::Student> getAll() override;
    Models::Student getById(int id) override;
    int create(const Models::Student& student) override;
    bool update(const Models::Student& student) override;
    bool deleteById(int id) override;
    int count() override;
    
    // Specific queries
    std::vector<Models::Student> getByGrade(const std::string& grade);
    std::vector<Models::Student> getActiveStudents();
    std::vector<Models::Student> searchByName(const std::string& name);
};

// Teacher repository
class TeacherRepository : public BaseRepository<Models::Teacher> {
public:
    explicit TeacherRepository(DatabaseManager& db);
    
    std::vector<Models::Teacher> getAll() override;
    Models::Teacher getById(int id) override;
    int create(const Models::Teacher& teacher) override;
    bool update(const Models::Teacher& teacher) override;
    bool deleteById(int id) override;
    int count() override;
    
    // Specific queries
    std::vector<Models::Teacher> getByDepartment(const std::string& department);
    std::vector<Models::Teacher> getActiveTeachers();
    std::vector<Models::Teacher> searchByName(const std::string& name);
};

// Course repository
class CourseRepository : public BaseRepository<Models::Course> {
public:
    explicit CourseRepository(DatabaseManager& db);
    
    std::vector<Models::Course> getAll() override;
    Models::Course getById(int id) override;
    int create(const Models::Course& course) override;
    bool update(const Models::Course& course) override;
    bool deleteById(int id) override;
    int count() override;
    
    // Specific queries
    std::vector<Models::Course> getByLevel(const std::string& level);
    std::vector<Models::Course> getByTeacher(int teacher_id);
    std::vector<Models::Course> getActiveCourses();
    Models::Course getByCode(const std::string& code);
};

// Enrollment repository
class EnrollmentRepository : public BaseRepository<Models::Enrollment> {
public:
    explicit EnrollmentRepository(DatabaseManager& db);
    
    std::vector<Models::Enrollment> getAll() override;
    Models::Enrollment getById(int id) override;
    int create(const Models::Enrollment& enrollment) override;
    bool update(const Models::Enrollment& enrollment) override;
    bool deleteById(int id) override;
    int count() override;
    
    // Specific queries
    std::vector<Models::Enrollment> getByStudent(int student_id);
    std::vector<Models::Enrollment> getByCourse(int course_id);
    std::vector<Models::Enrollment> getActiveEnrollments();
};

// Attendance repository
class AttendanceRepository : public BaseRepository<Models::Attendance> {
public:
    explicit AttendanceRepository(DatabaseManager& db);
    
    std::vector<Models::Attendance> getAll() override;
    Models::Attendance getById(int id) override;
    int create(const Models::Attendance& attendance) override;
    bool update(const Models::Attendance& attendance) override;
    bool deleteById(int id) override;
    int count() override;
    
    // Specific queries
    std::vector<Models::Attendance> getByStudent(int student_id);
    std::vector<Models::Attendance> getByCourse(int course_id);
    std::vector<Models::Attendance> getByDate(const std::string& date);
    std::vector<Models::Attendance> getByStudentAndCourse(int student_id, int course_id);
};

// Employee repository (HR)
class EmployeeRepository : public BaseRepository<Models::Employee> {
public:
    explicit EmployeeRepository(DatabaseManager& db);
    
    std::vector<Models::Employee> getAll() override;
    Models::Employee getById(int id) override;
    int create(const Models::Employee& employee) override;
    bool update(const Models::Employee& employee) override;
    bool deleteById(int id) override;
    int count() override;
    
    // Specific queries
    Models::Employee getByCode(const std::string& code);
    Models::Employee getByIdNumber(const std::string& id_number);
    std::vector<Models::Employee> getByDepartment(const std::string& department);
    std::vector<Models::Employee> getActiveEmployees();
    std::vector<Models::Employee> search(const std::string& query);
};

} // namespace Database
} // namespace SDEP

#endif // REPOSITORIES_H