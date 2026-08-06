#include "services/Services.h"
#include <chrono>

namespace SDEP {
namespace Services {

EmployeeService::EmployeeService(Database::EmployeeRepository& repository)
    : BaseService(repository) {}

std::vector<Models::Employee> EmployeeService::getAllEmployees() {
    return repository_.getAll();
}

Models::Employee EmployeeService::getEmployeeById(int id) {
    return repository_.getById(id);
}

int EmployeeService::createEmployee(const Models::Employee& employee) {
    if (!employee.validate()) {
        throw ValidationError("Employee validation failed");
    }
    return repository_.create(employee);
}

bool EmployeeService::updateEmployee(const Models::Employee& employee) {
    if (!employee.validate()) {
        throw ValidationError("Employee validation failed");
    }
    return repository_.update(employee);
}

bool EmployeeService::deleteEmployee(int id) {
    return repository_.deleteById(id);
}

Models::Employee EmployeeService::getEmployeeByCode(const std::string& code) {
    return repository_.getByCode(code);
}

Models::Employee EmployeeService::getEmployeeByIdNumber(const std::string& id_number) {
    return repository_.getByIdNumber(id_number);
}

std::vector<Models::Employee> EmployeeService::getEmployeesByDepartment(const std::string& department) {
    return repository_.getByDepartment(department);
}

std::vector<Models::Employee> EmployeeService::getActiveEmployees() {
    return repository_.getActiveEmployees();
}

std::vector<Models::Employee> EmployeeService::searchEmployees(const std::string& query) {
    return repository_.search(query);
}

int EmployeeService::getEmployeeCount() {
    return repository_.count();
}

bool EmployeeService::terminateEmployee(int id) {
    auto employee = getEmployeeById(id);
    if (employee.id == 0) {
        throw ValidationError("Employee not found");
    }
    
    employee.employee_status = "terminated";
    return repository_.update(employee);
}

} // namespace Services
} // namespace SDEP