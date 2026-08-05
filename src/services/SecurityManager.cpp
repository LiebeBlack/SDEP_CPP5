#include "services/SecurityManager.h"
#include <algorithm>
#include <random>
#include <sstream>
#include <iomanip>
#include <cctype>

namespace SDEP {
namespace Services {

SecurityManager::SecurityManager() {
    initializeDefaultUsers();
}

void SecurityManager::initializeDefaultUsers() {
    // Create default admin user
    Models::User admin;
    admin.username = "admin";
    admin.email = "admin@sistema.edu";
    admin.password_hash = admin.hashPassword("Admin123!");
    admin.role = "admin";
    admin.is_active = true;
    admin.created_at = getCurrentTimestamp();
    admin.password_changed_at = admin.created_at;
    
    users_[admin.username] = admin;
    
    // Initialize password history for admin
    password_history_[admin.username] = {admin.password_hash};
}

bool SecurityManager::createUser(const Models::User& user) {
    if (!validatePasswordStrength(user.password_hash)) {
        return false;
    }
    
    if (userExists(user.username)) {
        return false;
    }
    
    Models::User new_user = user;
    new_user.password_hash = new_user.hashPassword(user.password_hash);
    new_user.created_at = getCurrentTimestamp();
    new_user.password_changed_at = new_user.created_at;
    
    users_[new_user.username] = new_user;
    password_history_[new_user.username] = {new_user.password_hash};
    
    logAction("create", "user", new_user.id, true, "", "");
    
    return true;
}

Models::User SecurityManager::authenticateUser(const std::string& username, 
                                               const std::string& password,
                                               const std::string& ip_address) {
    auto it = users_.find(username);
    if (it == users_.end()) {
        logAction("login", "user", 0, false, "User not found", ip_address);
        return Models::User();
    }
    
    Models::User& user = it->second;
    
    // Check if account is locked
    if (user.isLocked()) {
        logAction("login", "user", user.id, false, "Account locked", ip_address);
        return Models::User();
    }
    
    // Check if account is active
    if (!user.is_active) {
        logAction("login", "user", user.id, false, "Account inactive", ip_address);
        return Models::User();
    }
    
    // Check password
    if (user.checkPassword(password)) {
        user.resetFailedLogins();
        logAction("login", "user", user.id, true, "", ip_address);
        return user;
    } else {
        recordFailedLogin(username);
        logAction("login", "user", user.id, false, "Invalid password", ip_address);
        return Models::User();
    }
}

bool SecurityManager::logoutUser(const std::string& session_token) {
    return invalidateSession(session_token);
}

bool SecurityManager::validateSession(const std::string& session_token) {
    auto it = session_tokens_.find(session_token);
    if (it == session_tokens_.end()) {
        return false;
    }
    
    if (isSessionExpired(session_token)) {
        invalidateSession(session_token);
        return false;
    }
    
    return true;
}

bool SecurityManager::changePassword(const std::string& username, const std::string& old_password,
                                     const std::string& new_password) {
    auto it = users_.find(username);
    if (it == users_.end()) {
        return false;
    }
    
    Models::User& user = it->second;
    
    // Verify old password
    if (!user.checkPassword(old_password)) {
        logAction("password_change", "user", user.id, false, "Invalid old password", "");
        return false;
    }
    
    // Validate new password
    if (!validatePasswordStrength(new_password)) {
        logAction("password_change", "user", user.id, false, "Weak password", "");
        return false;
    }
    
    // Check password history
    if (isPasswordInHistory(username, new_password)) {
        logAction("password_change", "user", user.id, false, "Password in history", "");
        return false;
    }
    
    // Change password
    user.password_hash = user.hashPassword(new_password);
    user.password_changed_at = getCurrentTimestamp();
    user.must_change_password = false;
    
    // Update password history
    auto& history = password_history_[username];
    history.push_back(user.password_hash);
    if (history.size() > password_history_count_) {
        history.erase(history.begin());
    }
    
    logAction("password_change", "user", user.id, true, "", "");
    
    return true;
}

bool SecurityManager::validatePasswordStrength(const std::string& password) const {
    if (password.length() < password_min_length_) {
        return false;
    }
    
    bool has_upper = false;
    bool has_lower = false;
    bool has_digit = false;
    bool has_special = false;
    
    for (char c : password) {
        if (std::isupper(c)) has_upper = true;
        else if (std::islower(c)) has_lower = true;
        else if (std::isdigit(c)) has_digit = true;
        else if (!std::isalnum(c)) has_special = true;
    }
    
    if (password_require_uppercase_ && !has_upper) return false;
    if (password_require_lowercase_ && !has_lower) return false;
    if (password_require_numbers_ && !has_digit) return false;
    if (password_require_special_ && !has_special) return false;
    
    // Check blacklist
    std::string lower_password = password;
    std::transform(lower_password.begin(), lower_password.end(), lower_password.begin(), ::tolower);
    for (const auto& blacklisted : password_blacklist_) {
        if (lower_password.find(blacklisted) != std::string::npos) {
            return false;
        }
    }
    
    return true;
}

bool SecurityManager::isPasswordInHistory(const std::string& username, const std::string& password) const {
    auto it = password_history_.find(username);
    if (it == password_history_.end()) {
        return false;
    }
    
    Models::User temp_user;
    std::string new_hash = temp_user.hashPassword(password);
    
    for (const auto& old_hash : it->second) {
        if (old_hash == new_hash) {
            return true;
        }
    }
    
    return false;
}

bool SecurityManager::isAccountLocked(const std::string& username) const {
    auto it = users_.find(username);
    if (it == users_.end()) {
        return false;
    }
    
    return it->second.isLocked();
}

void SecurityManager::recordFailedLogin(const std::string& username) {
    auto it = users_.find(username);
    if (it == users_.end()) {
        return;
    }
    
    it->second.recordFailedLogin();
}

void SecurityManager::resetFailedLogins(const std::string& username) {
    auto it = users_.find(username);
    if (it == users_.end()) {
        return;
    }
    
    it->second.resetFailedLogins();
}

std::string SecurityManager::createSessionToken(const std::string& username) {
    std::string token = generateSessionToken();
    session_tokens_[token] = username;
    
    logAction("session_create", "user", users_[username].id, true, "", "");
    
    return token;
}

bool SecurityManager::invalidateSession(const std::string& session_token) {
    auto it = session_tokens_.find(session_token);
    if (it == session_tokens_.end()) {
        return false;
    }
    
    std::string username = it->second;
    session_tokens_.erase(it);
    
    logAction("session_destroy", "user", users_[username].id, true, "", "");
    
    return true;
}

void SecurityManager::invalidateAllUserSessions(const std::string& username) {
    std::vector<std::string> tokens_to_remove;
    
    for (const auto& pair : session_tokens_) {
        if (pair.second == username) {
            tokens_to_remove.push_back(pair.first);
        }
    }
    
    for (const auto& token : tokens_to_remove) {
        invalidateSession(token);
    }
}

void SecurityManager::logAction(const std::string& action, const std::string& resource_type,
                                 int resource_id, bool success, const std::string& error_message,
                                 const std::string& ip_address) {
    AuditLog log;
    log.action = action;
    log.resource_type = resource_type;
    log.resource_id = resource_id;
    log.success = success;
    log.error_message = error_message;
    log.ip_address = ip_address;
    log.timestamp = getCurrentTimestamp();
    
    audit_logs_.push_back(log);
}

std::vector<AuditLog> SecurityManager::getAuditLogs(int user_id) {
    if (user_id == 0) {
        return audit_logs_;
    }
    
    std::vector<AuditLog> filtered_logs;
    for (const auto& log : audit_logs_) {
        if (log.user_id == user_id) {
            filtered_logs.push_back(log);
        }
    }
    
    return filtered_logs;
}

Models::User SecurityManager::getUserByUsername(const std::string& username) {
    auto it = users_.find(username);
    if (it == users_.end()) {
        return Models::User();
    }
    
    return it->second;
}

bool SecurityManager::userExists(const std::string& username) const {
    return users_.find(username) != users_.end();
}

std::string SecurityManager::generateSessionToken() const {
    const std::string chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, chars.size() - 1);
    
    std::string token;
    for (int i = 0; i < 32; ++i) {
        token += chars[dis(gen)];
    }
    
    return token;
}

bool SecurityManager::isSessionExpired(const std::string& token) const {
    // Simplified - in production, implement proper session expiration
    return false;
}

void SecurityManager::cleanupExpiredSessions() {
    // Simplified - in production, implement proper cleanup
}

} // namespace Services
} // namespace SDEP