#include "models/models.h"
#include <sstream>

namespace SDEP {
namespace Models {

// Attendance implementation
bool Attendance::validate() const {
    // Validate student_id
    if (student_id <= 0) {
        return false;
    }
    
    // Validate course_id
    if (course_id <= 0) {
        return false;
    }
    
    // Validate date
    if (date.empty()) {
        return false;
    }
    
    // Validate status
    if (status.empty()) {
        return false;
    }
    
    return true;
}

std::string Attendance::toString() const {
    std::ostringstream oss;
    oss << "Attendance{id=" << id 
        << ", student_id=" << student_id
        << ", course_id=" << course_id
        << ", date=" << date
        << ", status=" << status
        << "}";
    return oss.str();
}

std::vector<std::pair<std::string, std::string>> Attendance::toDBPairs() const {
    return {
        {"student_id", std::to_string(student_id)},
        {"student_name", student_name},
        {"course_id", std::to_string(course_id)},
        {"course_name", course_name},
        {"date", date},
        {"status", status},
        {"notes", notes},
        {"created_at", created_at}
    };
}

Attendance Attendance::fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs) {
    Attendance attendance;
    for (const auto& pair : pairs) {
        if (pair.first == "id") attendance.id = std::stoi(pair.second);
        else if (pair.first == "student_id") attendance.student_id = std::stoi(pair.second);
        else if (pair.first == "student_name") attendance.student_name = pair.second;
        else if (pair.first == "course_id") attendance.course_id = std::stoi(pair.second);
        else if (pair.first == "course_name") attendance.course_name = pair.second;
        else if (pair.first == "date") attendance.date = pair.second;
        else if (pair.first == "status") attendance.status = pair.second;
        else if (pair.first == "notes") attendance.notes = pair.second;
        else if (pair.first == "created_at") attendance.created_at = pair.second;
    }
    return attendance;
}

} // namespace Models
} // namespace SDEP