#include "models/models.h"
#include <sstream>
#include <algorithm>
#include <regex>
#include <chrono>

namespace SDEP {
namespace Models {

// Teacher implementation
Teacher::Teacher(const std::string& fname, const std::string& lname)
    : first_name(fname), last_name(lname) {
    created_at = BaseModel::getCurrentTimestamp();
    updated_at = created_at;
}

bool Teacher::validate() const {
    // Validate first name
    if (first_name.empty() || first_name.length() < 2) {
        return false;
    }
    if (first_name.length() > 100) {
        return false;
    }
    
    // Validate last name
    if (last_name.empty() || last_name.length() < 2) {
        return false;
    }
    if (last_name.length() > 100) {
        return false;
    }
    
    // Validate email format if provided
    if (!email.empty()) {
        std::regex email_regex(R"(^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$)");
        if (!std::regex_match(email, email_regex)) {
            return false;
        }
    }
    
    // Validate salary
    if (salary < 0) {
        return false;
    }
    
    return true;
}

std::string Teacher::toString() const {
    std::ostringstream oss;
    oss << "Teacher{id=" << id 
        << ", name=" << getFullName()
        << ", department=" << department
        << ", specialization=" << specialization
        << ", active=" << (active ? "true" : "false")
        << ", salary=" << salary
        << "}";
    return oss.str();
}

std::string Teacher::getFullName() const {
    return first_name + " " + last_name;
}

std::vector<std::pair<std::string, std::string>> Teacher::toDBPairs() const {
    return {
        {"first_name", first_name},
        {"last_name", last_name},
        {"email", email},
        {"phone", phone},
        {"department", department},
        {"specialization", specialization},
        {"hire_date", hire_date},
        {"active", active ? "1" : "0"},
        {"salary", std::to_string(salary)},
        {"qualification", qualification},
        {"created_at", created_at},
        {"updated_at", updated_at}
    };
}

Teacher Teacher::fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs) {
    Teacher teacher;
    for (const auto& pair : pairs) {
        if (pair.first == "id") teacher.id = std::stoi(pair.second);
        else if (pair.first == "first_name") teacher.first_name = pair.second;
        else if (pair.first == "last_name") teacher.last_name = pair.second;
        else if (pair.first == "email") teacher.email = pair.second;
        else if (pair.first == "phone") teacher.phone = pair.second;
        else if (pair.first == "department") teacher.department = pair.second;
        else if (pair.first == "specialization") teacher.specialization = pair.second;
        else if (pair.first == "hire_date") teacher.hire_date = pair.second;
        else if (pair.first == "active") teacher.active = (pair.second == "1");
        else if (pair.first == "salary") teacher.salary = std::stod(pair.second);
        else if (pair.first == "qualification") teacher.qualification = pair.second;
        else if (pair.first == "created_at") teacher.created_at = pair.second;
        else if (pair.first == "updated_at") teacher.updated_at = pair.second;
    }
    return teacher;
}

} // namespace Models
} // namespace SDEP