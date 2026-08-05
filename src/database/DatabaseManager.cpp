#include "database/DatabaseManager.h"
#include <iostream>
#include <sstream>

namespace SDEP {
namespace Database {

DatabaseManager::DatabaseManager(const std::string& db_path)
    : db_path_(db_path), db_(nullptr), connected_(false) {
}

DatabaseManager::~DatabaseManager() {
    disconnect();
}

bool DatabaseManager::connect() {
    if (connected_) {
        return true;
    }
    
    int result = sqlite3_open(db_path_.c_str(), &db_);
    if (result != SQLITE_OK) {
        handleError("Failed to open database");
        return false;
    }
    
    // Enable foreign keys
    executeUpdate("PRAGMA foreign_keys = ON", {});
    
    // Enable WAL mode for better concurrency
    executeUpdate("PRAGMA journal_mode = WAL", {});
    
    connected_ = true;
    return true;
}

void DatabaseManager::disconnect() {
    if (connected_ && db_) {
        sqlite3_close(db_);
        db_ = nullptr;
        connected_ = false;
    }
}

bool DatabaseManager::isConnected() const {
    return connected_;
}

bool DatabaseManager::initializeSchema() {
    if (!connected_) {
        return false;
    }
    
    try {
        // Students table
        executeUpdate(R"(
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                enrollment_date TEXT,
                grade TEXT,
                section TEXT,
                active BOOLEAN DEFAULT 1,
                parent_name TEXT,
                parent_phone TEXT,
                emergency_contact TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        )", {});
        
        // Teachers table
        executeUpdate(R"(
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                department TEXT,
                specialization TEXT,
                hire_date TEXT,
                active BOOLEAN DEFAULT 1,
                salary REAL DEFAULT 0.0,
                qualification TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        )", {});
        
        // Courses table
        executeUpdate(R"(
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE,
                level TEXT,
                description TEXT,
                teacher_id INTEGER,
                teacher_name TEXT,
                credits INTEGER DEFAULT 0,
                active BOOLEAN DEFAULT 1,
                schedule TEXT,
                classroom TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id)
            )
        )", {});
        
        // Enrollments table
        executeUpdate(R"(
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                student_name TEXT,
                course_id INTEGER NOT NULL,
                course_name TEXT,
                enrollment_date TEXT,
                grade REAL,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        )", {});
        
        // Attendance table
        executeUpdate(R"(
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                student_name TEXT,
                course_id INTEGER NOT NULL,
                course_name TEXT,
                date TEXT NOT NULL,
                status TEXT DEFAULT 'Present',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            )
        )", {});
        
        // Employees table (HR)
        executeUpdate(R"(
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_code TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                id_number TEXT,
                passport TEXT,
                birth_date TEXT,
                gender TEXT,
                nationality TEXT,
                civil_status TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                mobile TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                emergency_contact TEXT,
                emergency_phone TEXT,
                department TEXT,
                position TEXT,
                hire_date TEXT,
                employment_type TEXT,
                employee_status TEXT DEFAULT 'active',
                education_level TEXT,
                institution TEXT,
                degree TEXT,
                graduation_year TEXT,
                certifications TEXT,
                specializations TEXT,
                salary REAL DEFAULT 0.0,
                salary_type TEXT,
                bank_name TEXT,
                bank_account TEXT,
                bank_account_type TEXT,
                payment_method TEXT,
                tax_id TEXT,
                social_security TEXT,
                work_schedule TEXT,
                manager_id INTEGER,
                location TEXT,
                contract_start TEXT,
                contract_end TEXT,
                health_insurance BOOLEAN DEFAULT 0,
                life_insurance BOOLEAN DEFAULT 0,
                retirement_plan BOOLEAN DEFAULT 0,
                other_benefits TEXT,
                contract_signed BOOLEAN DEFAULT 0,
                confidentiality_signed BOOLEAN DEFAULT 0,
                background_check BOOLEAN DEFAULT 0,
                drug_test BOOLEAN DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        )", {});
        
        // Users table for authentication
        executeUpdate(R"(
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                department TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                two_factor_enabled BOOLEAN DEFAULT 0,
                two_factor_secret TEXT,
                password_changed_at TIMESTAMP,
                must_change_password BOOLEAN DEFAULT 0
            )
        )", {});
        
        return true;
    } catch (const DatabaseException& e) {
        std::cerr << "Schema initialization error: " << e.what() << std::endl;
        return false;
    }
}

bool DatabaseManager::tableExists(const std::string& table_name) {
    std::string query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?";
    auto result = executeQuery(query, {table_name});
    return !result.empty();
}

DatabaseManager::QueryResult DatabaseManager::executeQuery(
    const std::string& query, 
    const std::vector<std::string>& params) {
    
    if (!connected_) {
        throw DatabaseException("Database not connected");
    }
    
    sqlite3_stmt* stmt = nullptr;
    prepareStatement(&stmt, query);
    bindParameters(stmt, params);
    
    QueryResult result;
    
    int step_result;
    while ((step_result = sqlite3_step(stmt)) == SQLITE_ROW) {
        result.push_back(getCurrentRow(stmt));
    }
    
    if (step_result != SQLITE_DONE) {
        sqlite3_finalize(stmt);
        handleError("Query execution failed");
        throw DatabaseException("Query execution failed");
    }
    
    sqlite3_finalize(stmt);
    return result;
}

int DatabaseManager::executeUpdate(
    const std::string& query, 
    const std::vector<std::string>& params) {
    
    if (!connected_) {
        throw DatabaseException("Database not connected");
    }
    
    sqlite3_stmt* stmt = nullptr;
    prepareStatement(&stmt, query);
    bindParameters(stmt, params);
    
    int result = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    
    if (result != SQLITE_DONE) {
        handleError("Update execution failed");
        throw DatabaseException("Update execution failed");
    }
    
    return sqlite3_changes(db_);
}

int DatabaseManager::executeInsert(
    const std::string& query, 
    const std::vector<std::string>& params) {
    
    executeUpdate(query, params);
    return static_cast<int>(sqlite3_last_insert_rowid(db_));
}

bool DatabaseManager::executeTransaction(const std::function<bool()>& operation) {
    if (!connected_) {
        return false;
    }
    
    try {
        executeUpdate("BEGIN TRANSACTION", {});
        
        bool success = operation();
        
        if (success) {
            executeUpdate("COMMIT", {});
        } else {
            executeUpdate("ROLLBACK", {});
        }
        
        return success;
    } catch (const DatabaseException& e) {
        try {
            executeUpdate("ROLLBACK", {});
        } catch (...) {
            // Ignore rollback errors
        }
        return false;
    }
}

std::string DatabaseManager::getLastInsertId() const {
    return std::to_string(sqlite3_last_insert_rowid(db_));
}

int DatabaseManager::getRowCount(const std::string& table_name) {
    std::string query = "SELECT COUNT(*) as count FROM " + table_name;
    auto result = executeQuery(query, {});
    
    if (!result.empty() && !result[0].empty()) {
        return std::stoi(result[0][0].second);
    }
    
    return 0;
}

void DatabaseManager::prepareStatement(sqlite3_stmt** stmt, const std::string& query) {
    int result = sqlite3_prepare_v2(db_, query.c_str(), -1, stmt, nullptr);
    if (result != SQLITE_OK) {
        handleError("Statement preparation failed");
        throw DatabaseException("Statement preparation failed");
    }
}

void DatabaseManager::bindParameters(sqlite3_stmt* stmt, const std::vector<std::string>& params) {
    for (size_t i = 0; i < params.size(); ++i) {
        int result = sqlite3_bind_text(stmt, static_cast<int>(i + 1), 
                                       params[i].c_str(), -1, SQLITE_TRANSIENT);
        if (result != SQLITE_OK) {
            sqlite3_finalize(stmt);
            handleError("Parameter binding failed");
            throw DatabaseException("Parameter binding failed");
        }
    }
}

DatabaseManager::Row DatabaseManager::getCurrentRow(sqlite3_stmt* stmt) {
    Row row;
    int column_count = sqlite3_column_count(stmt);
    
    for (int i = 0; i < column_count; ++i) {
        const char* name = sqlite3_column_name(stmt, i);
        const char* value = reinterpret_cast<const char*>(sqlite3_column_text(stmt, i));
        
        row.emplace_back(name, value ? value : "");
    }
    
    return row;
}

void DatabaseManager::handleError(const std::string& operation) {
    if (db_) {
        std::string error_msg = sqlite3_errmsg(db_);
        std::cerr << operation << ": " << error_msg << std::endl;
    }
}

} // namespace Database
} // namespace SDEP