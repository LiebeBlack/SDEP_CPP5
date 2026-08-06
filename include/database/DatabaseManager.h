#ifndef DATABASEMANAGER_H
#define DATABASEMANAGER_H

#include <sqlite3.h>
#include <string>
#include <vector>
#include <functional>
#include <memory>
#include <stdexcept>
#include <optional>

namespace SDEP {
namespace Database {

class DatabaseException : public std::runtime_error {
public:
    explicit DatabaseException(const std::string& message) 
        : std::runtime_error(message) {}
};

class DatabaseManager {
public:
    explicit DatabaseManager(const std::string& db_path);
    ~DatabaseManager();
    
    // Prevent copying
    DatabaseManager(const DatabaseManager&) = delete;
    DatabaseManager& operator=(const DatabaseManager&) = delete;
    
    // Connection management
    bool connect();
    void disconnect();
    bool isConnected() const;
    
    // Schema management
    bool initializeSchema();
    bool tableExists(const std::string& table_name);
    
    // Query execution
    using Row = std::vector<std::pair<std::string, std::string>>;
    using QueryResult = std::vector<Row>;
    
    QueryResult executeQuery(const std::string& query, const std::vector<std::string>& params = {});
    int executeUpdate(const std::string& query, const std::vector<std::string>& params = {});
    int executeInsert(const std::string& query, const std::vector<std::string>& params = {});
    bool executeTransaction(const std::function<bool()>& operation);
    
    // Utility functions
    std::string getLastInsertId() const;
    int getRowCount(const std::string& table_name);
    
private:
    std::string db_path_;
    sqlite3* db_;
    bool connected_;
    
    void prepareStatement(sqlite3_stmt** stmt, const std::string& query);
    void bindParameters(sqlite3_stmt* stmt, const std::vector<std::string>& params);
    Row getCurrentRow(sqlite3_stmt* stmt);
    void handleError(const std::string& operation);
};

} // namespace Database
} // namespace SDEP

#endif // DATABASEMANAGER_H