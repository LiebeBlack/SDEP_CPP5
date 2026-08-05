#include "models/models.h"
#include <sstream>
#include <algorithm>
#include <regex>

namespace SDEP {
namespace Models {

// Employee implementation
bool Employee::validate() const {
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
    
    // Validate employee status
    if (employee_status.empty()) {
        return false;
    }
    
    return true;
}

std::string Employee::toString() const {
    std::ostringstream oss;
    oss << "Employee{id=" << id 
        << ", code=" << employee_code
        << ", name=" << getFullName()
        << ", department=" << department
        << ", position=" << position
        << ", status=" << employee_status
        << ", salary=" << salary
        << "}";
    return oss.str();
}

std::string Employee::getFullName() const {
    return first_name + " " + last_name;
}

std::vector<std::pair<std::string, std::string>> Employee::toDBPairs() const {
    return {
        {"employee_code", employee_code},
        {"first_name", first_name},
        {"last_name", last_name},
        {"id_number", id_number},
        {"passport", passport},
        {"birth_date", birth_date},
        {"gender", gender},
        {"nationality", nationality},
        {"civil_status", civil_status},
        {"email", email},
        {"phone", phone},
        {"mobile", mobile},
        {"address", address},
        {"city", city},
        {"state", state},
        {"zip_code", zip_code},
        {"emergency_contact", emergency_contact},
        {"emergency_phone", emergency_phone},
        {"department", department},
        {"position", position},
        {"hire_date", hire_date},
        {"employment_type", employment_type},
        {"employee_status", employee_status},
        {"education_level", education_level},
        {"institution", institution},
        {"degree", degree},
        {"graduation_year", graduation_year},
        {"certifications", certifications},
        {"specializations", specializations},
        {"salary", std::to_string(salary)},
        {"salary_type", salary_type},
        {"bank_name", bank_name},
        {"bank_account", bank_account},
        {"bank_account_type", bank_account_type},
        {"payment_method", payment_method},
        {"tax_id", tax_id},
        {"social_security", social_security},
        {"work_schedule", work_schedule},
        {"manager_id", std::to_string(manager_id)},
        {"location", location},
        {"contract_start", contract_start},
        {"contract_end", contract_end},
        {"health_insurance", health_insurance ? "1" : "0"},
        {"life_insurance", life_insurance ? "1" : "0"},
        {"retirement_plan", retirement_plan ? "1" : "0"},
        {"other_benefits", other_benefits},
        {"contract_signed", contract_signed ? "1" : "0"},
        {"confidentiality_signed", confidentiality_signed ? "1" : "0"},
        {"background_check", background_check ? "1" : "0"},
        {"drug_test", drug_test ? "1" : "0"},
        {"notes", notes},
        {"created_at", created_at},
        {"updated_at", updated_at}
    };
}

Employee Employee::fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs) {
    Employee employee;
    for (const auto& pair : pairs) {
        if (pair.first == "id") employee.id = std::stoi(pair.second);
        else if (pair.first == "employee_code") employee.employee_code = pair.second;
        else if (pair.first == "first_name") employee.first_name = pair.second;
        else if (pair.first == "last_name") employee.last_name = pair.second;
        else if (pair.first == "id_number") employee.id_number = pair.second;
        else if (pair.first == "passport") employee.passport = pair.second;
        else if (pair.first == "birth_date") employee.birth_date = pair.second;
        else if (pair.first == "gender") employee.gender = pair.second;
        else if (pair.first == "nationality") employee.nationality = pair.second;
        else if (pair.first == "civil_status") employee.civil_status = pair.second;
        else if (pair.first == "email") employee.email = pair.second;
        else if (pair.first == "phone") employee.phone = pair.second;
        else if (pair.first == "mobile") employee.mobile = pair.second;
        else if (pair.first == "address") employee.address = pair.second;
        else if (pair.first == "city") employee.city = pair.second;
        else if (pair.first == "state") employee.state = pair.second;
        else if (pair.first == "zip_code") employee.zip_code = pair.second;
        else if (pair.first == "emergency_contact") employee.emergency_contact = pair.second;
        else if (pair.first == "emergency_phone") employee.emergency_phone = pair.second;
        else if (pair.first == "department") employee.department = pair.second;
        else if (pair.first == "position") employee.position = pair.second;
        else if (pair.first == "hire_date") employee.hire_date = pair.second;
        else if (pair.first == "employment_type") employee.employment_type = pair.second;
        else if (pair.first == "employee_status") employee.employee_status = pair.second;
        else if (pair.first == "education_level") employee.education_level = pair.second;
        else if (pair.first == "institution") employee.institution = pair.second;
        else if (pair.first == "degree") employee.degree = pair.second;
        else if (pair.first == "graduation_year") employee.graduation_year = pair.second;
        else if (pair.first == "certifications") employee.certifications = pair.second;
        else if (pair.first == "specializations") employee.specializations = pair.second;
        else if (pair.first == "salary") employee.salary = std::stod(pair.second);
        else if (pair.first == "salary_type") employee.salary_type = pair.second;
        else if (pair.first == "bank_name") employee.bank_name = pair.second;
        else if (pair.first == "bank_account") employee.bank_account = pair.second;
        else if (pair.first == "bank_account_type") employee.bank_account_type = pair.second;
        else if (pair.first == "payment_method") employee.payment_method = pair.second;
        else if (pair.first == "tax_id") employee.tax_id = pair.second;
        else if (pair.first == "social_security") employee.social_security = pair.second;
        else if (pair.first == "work_schedule") employee.work_schedule = pair.second;
        else if (pair.first == "manager_id") employee.manager_id = std::stoi(pair.second);
        else if (pair.first == "location") employee.location = pair.second;
        else if (pair.first == "contract_start") employee.contract_start = pair.second;
        else if (pair.first == "contract_end") employee.contract_end = pair.second;
        else if (pair.first == "health_insurance") employee.health_insurance = (pair.second == "1");
        else if (pair.first == "life_insurance") employee.life_insurance = (pair.second == "1");
        else if (pair.first == "retirement_plan") employee.retirement_plan = (pair.second == "1");
        else if (pair.first == "other_benefits") employee.other_benefits = pair.second;
        else if (pair.first == "contract_signed") employee.contract_signed = (pair.second == "1");
        else if (pair.first == "confidentiality_signed") employee.confidentiality_signed = (pair.second == "1");
        else if (pair.first == "background_check") employee.background_check = (pair.second == "1");
        else if (pair.first == "drug_test") employee.drug_test = (pair.second == "1");
        else if (pair.first == "notes") employee.notes = pair.second;
        else if (pair.first == "created_at") employee.created_at = pair.second;
        else if (pair.first == "updated_at") employee.updated_at = pair.second;
    }
    return employee;
}

// User implementation
bool User::checkPassword(const std::string& password) const {
    return hashPassword(password) == password_hash;
}

std::string User::hashPassword(const std::string& password) const {
    // Simple hash for demonstration - in production use proper hashing
    std::string salt = "secure_salt_educational_system_2024";
    std::string to_hash = password + salt;
    
    unsigned int hash = 5381;
    for (char c : to_hash) {
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    }
    
    std::ostringstream oss;
    oss << std::hex << hash;
    return oss.str();
}

bool User::isLocked() const {
    if (locked_until.empty()) {
        return false;
    }
    
    // Parse timestamp and compare with current time
    // Simplified - in production use proper datetime parsing
    return false;
}

void User::recordFailedLogin() {
    failed_login_attempts++;
    if (failed_login_attempts >= 5) {
        // Set locked_until to 30 minutes from now
        // Simplified - in production use proper datetime
        locked_until = "locked";
    }
}

void User::resetFailedLogins() {
    failed_login_attempts = 0;
    locked_until.clear();
    last_login = BaseModel::getCurrentTimestamp();
}

} // namespace Models
} // namespace SDEP