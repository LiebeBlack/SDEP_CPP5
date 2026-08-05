#include "services/Services.h"
#include <numeric>

namespace SDEP {
namespace Services {

AttendanceService::AttendanceService(Database::AttendanceRepository& attendance_repo,
                                   StudentService& student_service,
                                   CourseService& course_service)
    : BaseService(attendance_repo),
      student_service_(student_service),
      course_service_(course_service) {}

std::vector<Models::Attendance> AttendanceService::getAllAttendance() {
    return repository_.getAll();
}

Models::Attendance AttendanceService::getAttendanceById(int id) {
    return repository_.getById(id);
}

int AttendanceService::createAttendance(const Models::Attendance& attendance) {
    if (!attendance.validate()) {
        throw ValidationError("Attendance validation failed");
    }
    
    // Validate student exists
    auto student = student_service_.getStudentById(attendance.student_id);
    if (student.id == 0) {
        throw ValidationError("Student not found");
    }
    
    // Validate course exists
    auto course = course_service_.getCourseById(attendance.course_id);
    if (course.id == 0) {
        throw ValidationError("Course not found");
    }
    
    // Set student and course names
    Models::Attendance new_attendance = attendance;
    new_attendance.student_name = student.getFullName();
    new_attendance.course_name = course.name;
    
    return repository_.create(new_attendance);
}

bool AttendanceService::updateAttendance(const Models::Attendance& attendance) {
    if (!attendance.validate()) {
        throw ValidationError("Attendance validation failed");
    }
    return repository_.update(attendance);
}

bool AttendanceService::deleteAttendance(int id) {
    return repository_.deleteById(id);
}

std::vector<Models::Attendance> AttendanceService::getAttendanceByStudent(int student_id) {
    return repository_.getByStudent(student_id);
}

std::vector<Models::Attendance> AttendanceService::getAttendanceByCourse(int course_id) {
    return repository_.getByCourse(course_id);
}

std::vector<Models::Attendance> AttendanceService::getAttendanceByDate(const std::string& date) {
    return repository_.getByDate(date);
}

std::vector<Models::Attendance> AttendanceService::getAttendanceByStudentAndCourse(int student_id, int course_id) {
    return repository_.getByStudentAndCourse(student_id, course_id);
}

bool AttendanceService::markAttendance(int student_id, int course_id, const std::string& date, const std::string& status) {
    // Validate student and course exist
    auto student = student_service_.getStudentById(student_id);
    if (student.id == 0) {
        throw ValidationError("Student not found");
    }
    
    auto course = course_service_.getCourseById(course_id);
    if (course.id == 0) {
        throw ValidationError("Course not found");
    }
    
    // Check if attendance already exists for this date
    auto existing = getAttendanceByStudentAndCourse(student_id, course_id);
    for (const auto& attendance : existing) {
        if (attendance.date == date) {
            // Update existing record
            Models::Attendance updated_attendance = attendance;
            updated_attendance.status = status;
            return repository_.update(updated_attendance);
        }
    }
    
    // Create new attendance record
    Models::Attendance attendance;
    attendance.student_id = student_id;
    attendance.student_name = student.getFullName();
    attendance.course_id = course_id;
    attendance.course_name = course.name;
    attendance.date = date;
    attendance.status = status;
    
    return repository_.create(attendance) > 0;
}

double AttendanceService::calculateAttendancePercentage(int student_id, int course_id) {
    auto attendance_records = getAttendanceByStudentAndCourse(student_id, course_id);
    
    if (attendance_records.empty()) {
        return 0.0;
    }
    
    int present_count = 0;
    for (const auto& attendance : attendance_records) {
        if (attendance.status == "Present" || attendance.status == "Late") {
            present_count++;
        }
    }
    
    return (static_cast<double>(present_count) / attendance_records.size()) * 100.0;
}

int AttendanceService::getAttendanceCount() {
    return repository_.count();
}

} // namespace Services
} // namespace SDEP