#include "services/Services.h"
#include <iostream>

namespace SDEP {
namespace Services {

// Student service implementation
StudentService::StudentService(Database::StudentRepository& repository)
    : BaseService(repository) {}

std::vector<Models::Student> StudentService::getAllStudents() {
    return repository_.getAll();
}

Models::Student StudentService::getStudentById(int id) {
    return repository_.getById(id);
}

int StudentService::createStudent(const Models::Student& student) {
    if (!student.validate()) {
        throw ValidationError("Student validation failed");
    }
    return repository_.create(student);
}

bool StudentService::updateStudent(const Models::Student& student) {
    if (!student.validate()) {
        throw ValidationError("Student validation failed");
    }
    return repository_.update(student);
}

bool StudentService::deleteStudent(int id) {
    return repository_.deleteById(id);
}

std::vector<Models::Student> StudentService::getStudentsByGrade(const std::string& grade) {
    return repository_.getByGrade(grade);
}

std::vector<Models::Student> StudentService::getActiveStudents() {
    return repository_.getActiveStudents();
}

std::vector<Models::Student> StudentService::searchStudents(const std::string& name) {
    return repository_.searchByName(name);
}

int StudentService::getStudentCount() {
    return repository_.count();
}

} // namespace Services
} // namespace SDEP