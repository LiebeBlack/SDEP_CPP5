#include "models/models.h"
#include <sstream>

namespace SDEP {
namespace Models {

// Course implementation
bool Course::validate() const {
    // Validate name
    if (name.empty() || name.length() < 2) {
        return false;
    }
    if (name.length() > 200) {
        return false;
    }
    
    // Validate code
    if (code.empty() || code.length() < 2) {
        return false;
    }
    if (code.length() > 50) {
        return false;
    }
    
    // Validate credits
    if (credits < 0 || credits > 10) {
        return false;
    }
    
    return true;
}

std::string Course::toString() const {
    std::ostringstream oss;
    oss << "Course{id=" << id 
        << ", name=" << name
        << ", code=" << code
        << ", level=" << level
        << ", teacher_id=" << teacher_id
        << ", credits=" << credits
        << ", active=" << (active ? "true" : "false")
        << "}";
    return oss.str();
}

std::vector<std::pair<std::string, std::string>> Course::toDBPairs() const {
    return {
        {"name", name},
        {"code", code},
        {"level", level},
        {"description", description},
        {"teacher_id", std::to_string(teacher_id)},
        {"teacher_name", teacher_name},
        {"credits", std::to_string(credits)},
        {"active", active ? "1" : "0"},
        {"schedule", schedule},
        {"classroom", classroom},
        {"created_at", created_at},
        {"updated_at", updated_at}
    };
}

Course Course::fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs) {
    Course course;
    for (const auto& pair : pairs) {
        if (pair.first == "id") course.id = std::stoi(pair.second);
        else if (pair.first == "name") course.name = pair.second;
        else if (pair.first == "code") course.code = pair.second;
        else if (pair.first == "level") course.level = pair.second;
        else if (pair.first == "description") course.description = pair.second;
        else if (pair.first == "teacher_id") course.teacher_id = std::stoi(pair.second);
        else if (pair.first == "teacher_name") course.teacher_name = pair.second;
        else if (pair.first == "credits") course.credits = std::stoi(pair.second);
        else if (pair.first == "active") course.active = (pair.second == "1");
        else if (pair.first == "schedule") course.schedule = pair.second;
        else if (pair.first == "classroom") course.classroom = pair.second;
        else if (pair.first == "created_at") course.created_at = pair.second;
        else if (pair.first == "updated_at") course.updated_at = pair.second;
    }
    return course;
}

} // namespace Models
} // namespace SDEP