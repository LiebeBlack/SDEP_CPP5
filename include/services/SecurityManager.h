#ifndef SECURITYMANAGER_H
#define SECURITYMANAGER_H

#include "models/models.h"
#include <string>
#include <map>
#include <vector>
#include <memory>
#include <ctime>
#include <optional>

namespace SDEP {
namespace Services {

class AuditLog {
public:
    int id = 0;
    int user_id = 0;
    std::string action;
    std::string resource_type;
    int resource_id = 0;
    std::string ip_address;
    std::string user_agent;
    std::string timestamp;
    bool success = true;
    std::string error_message;
    std::string additional_data;
};

class SecurityManager {
public:
    SecurityManager();
    
    // User management
    bool createUser(const Models::User& user);
    Models::User authenticateUser(const std::string& username, const std::string& password, 
                                  const std::string& ip_address = "");
    bool logoutUser(const std::string& session_token);
    bool validateSession(const std::string& session_token);
    
    // Password management
    bool changePassword(const std::string& username, const std::string& old_password, 
                       const std::string& new_password);
    bool validatePasswordStrength(const std::string& password) const;
    bool isPasswordInHistory(const std::string& username, const std::string& password) const;
    
    // Account security
    bool isAccountLocked(const std::string& username) const;
    void recordFailedLogin(const std::string& username);
    void resetFailedLogins(const std::string& username);
    
    // Session management
    std::string createSessionToken(const std::string& username);
    bool invalidateSession(const std::string& session_token);
    void invalidateAllUserSessions(const std::string& username);
    
    // Audit logging
    void logAction(const std::string& action, const std::string& resource_type, 
                   int resource_id, bool success, const std::string& error_message = "",
                   const std::string& ip_address = "");
    std::vector<AuditLog> getAuditLogs(int user_id = 0);
    
    // User lookup
    Models::User getUserByUsername(const std::string& username);
    bool userExists(const std::string& username) const;
    
    // Default users
    void initializeDefaultUsers();
    
private:
    std::map<std::string, Models::User> users_;
    std::map<std::string, std::string> session_tokens_; // token -> username
    std::map<std::string, std::vector<std::string>> password_history_; // username -> history
    std::vector<AuditLog> audit_logs_;
    
    // Security policies
    int password_min_length_ = 10;
    bool password_require_uppercase_ = true;
    bool password_require_lowercase_ = true;
    bool password_require_numbers_ = true;
    bool password_require_special_ = true;
    int password_history_count_ = 5;
    int max_failed_attempts_ = 5;
    int lockout_duration_minutes_ = 30;
    int session_timeout_minutes_ = 30;
    
    std::vector<std::string> password_blacklist_ = {
        "password", "123456", "qwerty", "admin", "welcome",
        "password123", "abc123", "letmein", "monkey", "dragon"
    };
    
    // Helper functions
    std::string generateSessionToken() const;
    bool isSessionExpired(const std::string& token) const;
    void cleanupExpiredSessions();
};

} // namespace Services
} // namespace SDEP

#endif // SECURITYMANAGER_H