#include "services/Services.h"

namespace SDEP {
namespace Services {

TeacherService::TeacherService(Database::TeacherRepository& repository)
    : BaseService(repository) {}

std::vector<Models::Teacher> TeacherService::getAllTeachers() {
    return repository_.getAll();
}

Models::Teacher TeacherService::getTeacherById(int id) {
    return repository_.getById(id);
}

int TeacherService::createTeacher(const Models::Teacher& teacher) {
    if (!teacher.validate()) {
        throw ValidationError("Teacher validation failed");
    }
    return repository_.create(teacher);
}

bool TeacherService::updateTeacher(const Models::Teacher& teacher) {
    if (!teacher.validate()) {
        throw ValidationError("Teacher validation failed");
    }
    return repository_.update(teacher);
}

bool TeacherService::deleteTeacher(int id) {
    return repository_.deleteById(id);
}

std::vector<Models::Teacher> TeacherService::getTeachersByDepartment(const std::string& department) {
    return repository_.getByDepartment(department);
}

std::vector<Models::Teacher> TeacherService::getActiveTeachers() {
    return repository_.getActiveTeachers();
}

std::vector<Models::Teacher> TeacherService::searchTeachers(const std::string& name) {
    return repository_.searchByName(name);
}

int TeacherService::getTeacherCount() {
    return repository_.count();
}

} // namespace Services
} // namespace SDEP