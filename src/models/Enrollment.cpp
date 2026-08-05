#include "models/models.h"
#include <sstream>

namespace SDEP {
namespace Models {

// Enrollment implementation
bool Enrollment::validate() const {
    // Validate student_id
    if (student_id <= 0) {
        return false;
    }
    
    // Validate course_id
    if (course_id <= 0) {
        return false;
    }
    
    // Validate grade
    if (grade < 0 || grade > 100) {
        return false;
    }
    
    // Validate status
    if (status.empty()) {
        return false;
    }
    
    return true;
}

std::string Enrollment::toString() const {
    std::ostringstream oss;
    oss << "Enrollment{id=" << id 
        << ", student_id=" << student_id
        << ", course_id=" << course_id
        << ", grade=" << grade
        << ", status=" << status
        << "}";
    return oss.str();
}

std::vector<std::pair<std::string, std::string>> Enrollment::toDBPairs() const {
    return {
        {"student_id", std::to_string(student_id)},
        {"student_name", student_name},
        {"course_id", std::to_string(course_id)},
        {"course_name", course_name},
        {"enrollment_date", enrollment_date},
        {"grade", std::to_string(grade)},
        {"status", status},
        {"created_at", created_at},
        {"updated_at", updated_at}
    };
}

Enrollment Enrollment::fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs) {
    Enrollment enrollment;
    for (const auto& pair : pairs) {
        if (pair.first == "id") enrollment.id = std::stoi(pair.second);
        else if (pair.first == "student_id") enrollment.student_id = std::stoi(pair.second);
        else if (pair.first == "student_name") enrollment.student_name = pair.second;
        else if (pair.first == "course_id") enrollment.course_id = std::stoi(pair.second);
        else if (pair.first == "course_name") enrollment.course_name = pair.second;
        else if (pair.first == "enrollment_date") enrollment.enrollment_date = pair.second;
        else if (pair.first == "grade") enrollment.grade = std::stod(pair.second);
        else if (pair.first == "status") enrollment.status = pair.second;
        else if (pair.first == "created_at") enrollment.created_at = pair.second;
        else if (pair.first == "updated_at") enrollment.updated_at = pair.second;
    }
    return enrollment;
}

} // namespace Models
} // namespace SDEP