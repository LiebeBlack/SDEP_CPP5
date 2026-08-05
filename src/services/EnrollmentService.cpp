#include "services/Services.h"

namespace SDEP {
namespace Services {

EnrollmentService::EnrollmentService(Database::EnrollmentRepository& enrollment_repo,
                                   StudentService& student_service,
                                   CourseService& course_service)
    : BaseService(enrollment_repo), 
      student_service_(student_service),
      course_service_(course_service) {}

std::vector<Models::Enrollment> EnrollmentService::getAllEnrollments() {
    return repository_.getAll();
}

Models::Enrollment EnrollmentService::getEnrollmentById(int id) {
    return repository_.getById(id);
}

int EnrollmentService::createEnrollment(const Models::Enrollment& enrollment) {
    if (!enrollment.validate()) {
        throw ValidationError("Enrollment validation failed");
    }
    
    // Validate student exists
    auto student = student_service_.getStudentById(enrollment.student_id);
    if (student.id == 0) {
        throw ValidationError("Student not found");
    }
    
    // Validate course exists
    auto course = course_service_.getCourseById(enrollment.course_id);
    if (course.id == 0) {
        throw ValidationError("Course not found");
    }
    
    // Set student and course names
    Models::Enrollment new_enrollment = enrollment;
    new_enrollment.student_name = student.getFullName();
    new_enrollment.course_name = course.name;
    
    return repository_.create(new_enrollment);
}

bool EnrollmentService::updateEnrollment(const Models::Enrollment& enrollment) {
    if (!enrollment.validate()) {
        throw ValidationError("Enrollment validation failed");
    }
    return repository_.update(enrollment);
}

bool EnrollmentService::deleteEnrollment(int id) {
    return repository_.deleteById(id);
}

std::vector<Models::Enrollment> EnrollmentService::getEnrollmentsByStudent(int student_id) {
    return repository_.getByStudent(student_id);
}

std::vector<Models::Enrollment> EnrollmentService::getEnrollmentsByCourse(int course_id) {
    return repository_.getByCourse(course_id);
}

std::vector<Models::Enrollment> EnrollmentService::getActiveEnrollments() {
    return repository_.getActiveEnrollments();
}

bool EnrollmentService::enrollStudentInCourse(int student_id, int course_id) {
    // Validate student and course exist
    auto student = student_service_.getStudentById(student_id);
    if (student.id == 0) {
        throw ValidationError("Student not found");
    }
    
    auto course = course_service_.getCourseById(course_id);
    if (course.id == 0) {
        throw ValidationError("Course not found");
    }
    
    // Check if already enrolled
    auto existing = getEnrollmentsByStudent(student_id);
    for (const auto& enrollment : existing) {
        if (enrollment.course_id == course_id && enrollment.status == "Active") {
            throw ValidationError("Student already enrolled in this course");
        }
    }
    
    // Create enrollment
    Models::Enrollment enrollment;
    enrollment.student_id = student_id;
    enrollment.student_name = student.getFullName();
    enrollment.course_id = course_id;
    enrollment.course_name = course.name;
    enrollment.status = "Active";
    
    return repository_.create(enrollment) > 0;
}

bool EnrollmentService::updateGrade(int enrollment_id, double grade) {
    auto enrollment = getEnrollmentById(enrollment_id);
    if (enrollment.id == 0) {
        throw ValidationError("Enrollment not found");
    }
    
    if (grade < 0 || grade > 100) {
        throw ValidationError("Grade must be between 0 and 100");
    }
    
    enrollment.grade = grade;
    return repository_.update(enrollment);
}

int EnrollmentService::getEnrollmentCount() {
    return repository_.count();
}

} // namespace Services
} // namespace SDEP