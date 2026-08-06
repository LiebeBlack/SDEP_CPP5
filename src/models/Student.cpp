#include "models/models.h"
#include <sstream>
#include <iomanip>
#include <algorithm>
#include <regex>
#include <chrono>
#include <format>

namespace SDEP {
namespace Models {

std::string BaseModel::getCurrentTimestamp() {
    auto now = std::time(nullptr);
    auto tm = *std::localtime(&now);
    std::ostringstream oss;
    oss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S");
    return oss.str();
}

// Student implementation
Student::Student(const std::string& fname, const std::string& lname)
    : first_name(fname), last_name(lname) {
    created_at = BaseModel::getCurrentTimestamp();
    updated_at = created_at;
}

bool Student::validate() const {
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
    
    // Validate phone format if provided
    if (!phone.empty()) {
        std::string cleaned_phone;
        for (char c : phone) {
            if (std::isdigit(c)) {
                cleaned_phone += c;
            }
        }
        if (cleaned_phone.length() < 10) {
            return false;
        }
    }
    
    // Validate grade length
    if (grade.length() > 20) {
        return false;
    }
    
    // Validate section length
    if (section.length() > 20) {
        return false;
    }
    
    return true;
}

std::string Student::toString() const {
    std::ostringstream oss;
    oss << "Student{id=" << id 
        << ", name=" << getFullName()
        << ", grade=" << grade
        << ", section=" << section
        << ", active=" << (active ? "true" : "false")
        << "}";
    return oss.str();
}

std::string Student::getFullName() const {
    return first_name + " " + last_name;
}

std::vector<std::pair<std::string, std::string>> Student::toDBPairs() const {
    return {
        {"first_name", first_name},
        {"last_name", last_name},
        {"email", email},
        {"phone", phone},
        {"address", address},
        {"enrollment_date", enrollment_date},
        {"grade", grade},
        {"section", section},
        {"active", active ? "1" : "0"},
        {"parent_name", parent_name},
        {"parent_phone", parent_phone},
        {"emergency_contact", emergency_contact},
        {"created_at", created_at},
        {"updated_at", updated_at}
    };
}

Student Student::fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs) {
    Student student;
    for (const auto& pair : pairs) {
        if (pair.first == "id") student.id = std::stoi(pair.second);
        else if (pair.first == "first_name") student.first_name = pair.second;
        else if (pair.first == "last_name") student.last_name = pair.second;
        else if (pair.first == "email") student.email = pair.second;
        else if (pair.first == "phone") student.phone = pair.second;
        else if (pair.first == "address") student.address = pair.second;
        else if (pair.first == "enrollment_date") student.enrollment_date = pair.second;
        else if (pair.first == "grade") student.grade = pair.second;
        else if (pair.first == "section") student.section = pair.second;
        else if (pair.first == "active") student.active = (pair.second == "1");
        else if (pair.first == "parent_name") student.parent_name = pair.second;
        else if (pair.first == "parent_phone") student.parent_phone = pair.second;
        else if (pair.first == "emergency_contact") student.emergency_contact = pair.second;
        else if (pair.first == "created_at") student.created_at = pair.second;
        else if (pair.first == "updated_at") student.updated_at = pair.second;
    }
    return student;
}

} // namespace Models
} // namespace SDEP