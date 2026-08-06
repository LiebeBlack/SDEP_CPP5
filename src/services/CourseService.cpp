#include "services/Services.h"
#include <chrono>

namespace SDEP {
namespace Services {

CourseService::CourseService(Database::CourseRepository& course_repo, 
                            Database::TeacherRepository& teacher_repo)
    : BaseService(course_repo), teacher_repo_(teacher_repo) {}

std::vector<Models::Course> CourseService::getAllCourses() {
    return repository_.getAll();
}

Models::Course CourseService::getCourseById(int id) {
    return repository_.getById(id);
}

int CourseService::createCourse(const Models::Course& course) {
    if (!course.validate()) {
        throw ValidationError("Course validation failed");
    }
    
    // Validate teacher exists if teacher_id is set
    if (course.teacher_id > 0) {
        auto teacher = teacher_repo_.getById(course.teacher_id);
        if (teacher.id == 0) {
            throw ValidationError("Teacher not found");
        }
    }
    
    return repository_.create(course);
}

bool CourseService::updateCourse(const Models::Course& course) {
    if (!course.validate()) {
        throw ValidationError("Course validation failed");
    }
    
    // Validate teacher exists if teacher_id is set
    if (course.teacher_id > 0) {
        auto teacher = teacher_repo_.getById(course.teacher_id);
        if (teacher.id == 0) {
            throw ValidationError("Teacher not found");
        }
    }
    
    return repository_.update(course);
}

bool CourseService::deleteCourse(int id) {
    return repository_.deleteById(id);
}

std::vector<Models::Course> CourseService::getCoursesByLevel(const std::string& level) {
    return repository_.getByLevel(level);
}

std::vector<Models::Course> CourseService::getCoursesByTeacher(int teacher_id) {
    return repository_.getByTeacher(teacher_id);
}

std::vector<Models::Course> CourseService::getActiveCourses() {
    return repository_.getActiveCourses();
}

Models::Course CourseService::getCourseByCode(const std::string& code) {
    return repository_.getByCode(code);
}

int CourseService::getCourseCount() {
    return repository_.count();
}

} // namespace Services
} // namespace SDEP