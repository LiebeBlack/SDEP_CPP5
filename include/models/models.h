#ifndef MODELS_H
#define MODELS_H

#include <string>
#include <vector>
#include <memory>
#include <ctime>

namespace SDEP {
namespace Models {

// Base model class
class BaseModel {
public:
    int id = 0;
    std::string created_at;
    std::string updated_at;

    virtual ~BaseModel() = default;
    virtual bool validate() const = 0;
    virtual std::string toString() const = 0;
    
protected:
    static std::string getCurrentTimestamp();
};

// Student model
class Student : public BaseModel {
public:
    std::string first_name;
    std::string last_name;
    std::string email;
    std::string phone;
    std::string address;
    std::string enrollment_date;
    std::string grade;
    std::string section;
    bool active = true;
    std::string parent_name;
    std::string parent_phone;
    std::string emergency_contact;

    Student() = default;
    Student(const std::string& fname, const std::string& lname);
    
    bool validate() const override;
    std::string toString() const override;
    std::string getFullName() const;
    
    // Serialization
    std::vector<std::pair<std::string, std::string>> toDBPairs() const;
    static Student fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs);
};

// Teacher model
class Teacher : public BaseModel {
public:
    std::string first_name;
    std::string last_name;
    std::string email;
    std::string phone;
    std::string department;
    std::string specialization;
    std::string hire_date;
    bool active = true;
    double salary = 0.0;
    std::string qualification;

    Teacher() = default;
    Teacher(const std::string& fname, const std::string& lname);
    
    bool validate() const override;
    std::string toString() const override;
    std::string getFullName() const;
    
    std::vector<std::pair<std::string, std::string>> toDBPairs() const;
    static Teacher fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs);
};

// Course model
class Course : public BaseModel {
public:
    std::string name;
    std::string code;
    std::string level;
    std::string description;
    int teacher_id = 0;
    std::string teacher_name;
    int credits = 0;
    bool active = true;
    std::string schedule;
    std::string classroom;

    Course() = default;
    
    bool validate() const override;
    std::string toString() const override;
    
    std::vector<std::pair<std::string, std::string>> toDBPairs() const;
    static Course fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs);
};

// Enrollment model
class Enrollment : public BaseModel {
public:
    int student_id = 0;
    std::string student_name;
    int course_id = 0;
    std::string course_name;
    std::string enrollment_date;
    double grade = 0.0;
    std::string status = "Active";

    Enrollment() = default;
    
    bool validate() const override;
    std::string toString() const override;
    
    std::vector<std::pair<std::string, std::string>> toDBPairs() const;
    static Enrollment fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs);
};

// Attendance model
class Attendance : public BaseModel {
public:
    int student_id = 0;
    std::string student_name;
    int course_id = 0;
    std::string course_name;
    std::string date;
    std::string status = "Present";
    std::string notes;

    Attendance() = default;
    
    bool validate() const override;
    std::string toString() const override;
    
    std::vector<std::pair<std::string, std::string>> toDBPairs() const;
    static Attendance fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs);
};

// Employee model (HR)
class Employee : public BaseModel {
public:
    std::string employee_code;
    std::string first_name;
    std::string last_name;
    std::string id_number;
    std::string passport;
    std::string birth_date;
    std::string gender;
    std::string nationality;
    std::string civil_status;
    std::string email;
    std::string phone;
    std::string mobile;
    std::string address;
    std::string city;
    std::string state;
    std::string zip_code;
    std::string emergency_contact;
    std::string emergency_phone;
    std::string department;
    std::string position;
    std::string hire_date;
    std::string employment_type;
    std::string employee_status = "active";
    std::string education_level;
    std::string institution;
    std::string degree;
    std::string graduation_year;
    std::string certifications;
    std::string specializations;
    double salary = 0.0;
    std::string salary_type;
    std::string bank_name;
    std::string bank_account;
    std::string bank_account_type;
    std::string payment_method;
    std::string tax_id;
    std::string social_security;
    std::string work_schedule;
    int manager_id = 0;
    std::string location;
    std::string contract_start;
    std::string contract_end;
    bool health_insurance = false;
    bool life_insurance = false;
    bool retirement_plan = false;
    std::string other_benefits;
    bool contract_signed = false;
    bool confidentiality_signed = false;
    bool background_check = false;
    bool drug_test = false;
    std::string notes;

    Employee() = default;
    
    bool validate() const override;
    std::string toString() const override;
    std::string getFullName() const;
    
    std::vector<std::pair<std::string, std::string>> toDBPairs() const;
    static Employee fromDBPairs(const std::vector<std::pair<std::string, std::string>>& pairs);
};

// User model for authentication
class User {
public:
    int id = 0;
    std::string username;
    std::string email;
    std::string password_hash;
    std::string role = "user";
    std::string department;
    bool is_active = true;
    std::string created_at;
    std::string last_login;
    int failed_login_attempts = 0;
    std::string locked_until;
    bool two_factor_enabled = false;
    std::string two_factor_secret;
    std::string password_changed_at;
    bool must_change_password = false;
    
    bool checkPassword(const std::string& password) const;
    std::string hashPassword(const std::string& password) const;
    bool isLocked() const;
    void recordFailedLogin();
    void resetFailedLogins();
};

} // namespace Models
} // namespace SDEP

#endif // MODELS_H