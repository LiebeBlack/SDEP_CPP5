#include <wx/wx.h>
#include "database/DatabaseManager.h"
#include "database/Repositories.h"
#include "services/Services.h"
#include "gui/MainFrame.h"
#include "gui/LoginDialog.h"
#include <iostream>
#include <memory>

namespace SDEP {

class SDEPApp : public wxApp {
public:
    virtual bool OnInit() override;
    virtual int OnExit() override;
    
private:
    // Core components
    std::unique_ptr<Database::DatabaseManager> db_manager_;
    
    // Repositories
    std::unique_ptr<Database::StudentRepository> student_repo_;
    std::unique_ptr<Database::TeacherRepository> teacher_repo_;
    std::unique_ptr<Database::CourseRepository> course_repo_;
    std::unique_ptr<Database::EnrollmentRepository> enrollment_repo_;
    std::unique_ptr<Database::AttendanceRepository> attendance_repo_;
    std::unique_ptr<Database::EmployeeRepository> employee_repo_;
    
    // Services
    std::unique_ptr<Services::StudentService> student_service_;
    std::unique_ptr<Services::TeacherService> teacher_service_;
    std::unique_ptr<Services::CourseService> course_service_;
    std::unique_ptr<Services::EnrollmentService> enrollment_service_;
    std::unique_ptr<Services::AttendanceService> attendance_service_;
    std::unique_ptr<Services::EmployeeService> employee_service_;
    std::unique_ptr<Services::SecurityManager> security_manager_;
    
    // GUI
    GUI::MainFrame* main_frame_;
    
    bool InitializeDatabase();
    bool InitializeServices();
    bool ShowLoginDialog();
    bool ShowMainFrame();
};

wxIMPLEMENT_APP(SDEPApp);

bool SDEPApp::OnInit() {
    if (!wxApp::OnInit()) {
        return false;
    }
    
    std::cout << "Initializing SDEP Educational Management System..." << std::endl;
    
    // Initialize database
    if (!InitializeDatabase()) {
        wxMessageBox("Failed to initialize database. Check logs for details.", 
                     "Database Error", wxOK | wxICON_ERROR);
        return false;
    }
    
    // Initialize services
    if (!InitializeServices()) {
        wxMessageBox("Failed to initialize services. Check logs for details.", 
                     "Service Error", wxOK | wxICON_ERROR);
        return false;
    }
    
    // Show login dialog
    if (!ShowLoginDialog()) {
        return false; // User cancelled or login failed
    }
    
    // Show main frame
    if (!ShowMainFrame()) {
        return false;
    }
    
    std::cout << "SDEP System initialized successfully." << std::endl;
    return true;
}

int SDEPApp::OnExit() {
    std::cout << "Shutting down SDEP System..." << std::endl;
    
    // Cleanup is handled by smart pointers
    return wxApp::OnExit();
}

bool SDEPApp::InitializeDatabase() {
    try {
        std::cout << "Initializing database..." << std::endl;
        
        // Create database manager
        db_manager_ = std::make_unique<Database::DatabaseManager>("institution.db");
        
        // Connect to database
        if (!db_manager_->connect()) {
            std::cerr << "Failed to connect to database" << std::endl;
            return false;
        }
        
        // Initialize schema
        if (!db_manager_->initializeSchema()) {
            std::cerr << "Failed to initialize database schema" << std::endl;
            return false;
        }
        
        std::cout << "Database initialized successfully" << std::endl;
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "Database initialization error: " << e.what() << std::endl;
        return false;
    }
}

bool SDEPApp::InitializeServices() {
    try {
        std::cout << "Initializing services..." << std::endl;
        
        // Create repositories
        student_repo_ = std::make_unique<Database::StudentRepository>(*db_manager_);
        teacher_repo_ = std::make_unique<Database::TeacherRepository>(*db_manager_);
        course_repo_ = std::make_unique<Database::CourseRepository>(*db_manager_);
        enrollment_repo_ = std::make_unique<Database::EnrollmentRepository>(*db_manager_);
        attendance_repo_ = std::make_unique<Database::AttendanceRepository>(*db_manager_);
        employee_repo_ = std::make_unique<Database::EmployeeRepository>(*db_manager_);
        
        // Create services
        student_service_ = std::make_unique<Services::StudentService>(*student_repo_);
        teacher_service_ = std::make_unique<Services::TeacherService>(*teacher_repo_);
        course_service_ = std::make_unique<Services::CourseService>(*course_repo_, *teacher_repo_);
        enrollment_service_ = std::make_unique<Services::EnrollmentService>(
            *enrollment_repo_, *student_service_, *course_service_);
        attendance_service_ = std::make_unique<Services::AttendanceService>(
            *attendance_repo_, *student_service_, *course_service_);
        employee_service_ = std::make_unique<Services::EmployeeService>(*employee_repo_);
        
        // Create security manager
        security_manager_ = std::make_unique<Services::SecurityManager>();
        
        std::cout << "Services initialized successfully" << std::endl;
        return true;
        
    } catch (const std::exception& e) {
        std::cerr << "Service initialization error: " << e.what() << std::endl;
        return false;
    }
}

bool SDEPApp::ShowLoginDialog() {
    std::cout << "Showing login dialog..." << std::endl;
    
    GUI::LoginDialog login_dialog(nullptr, security_manager_.get());
    
    if (login_dialog.ShowModal() == wxID_OK) {
        std::cout << "Login successful for user: " << login_dialog.GetUsername() << std::endl;
        return true;
    } else {
        std::cout << "Login cancelled or failed" << std::endl;
        return false;
    }
}

bool SDEPApp::ShowMainFrame() {
    std::cout << "Creating main application window..." << std::endl;
    
    main_frame_ = new GUI::MainFrame("SDEP Educational Management System v1.0", 
                                     security_manager_.get());
    
    // Set services
    main_frame_->SetServices(
        student_service_.get(),
        teacher_service_.get(),
        course_service_.get(),
        enrollment_service_.get(),
        attendance_service_.get(),
        employee_service_.get()
    );
    
    return true;
}

} // namespace SDEP