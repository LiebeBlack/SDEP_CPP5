#ifndef MAINFRAME_H
#define MAINFRAME_H

#include <wx/wx.h>
#include <wx/listctrl.h>
#include <wx/notebook.h>
#include <wx/datectrl.h>
#include <wx/spinctrl.h>
#include <wx/panel.h>
#include "services/Services.h"

namespace SDEP {
namespace GUI {

class MainFrame : public wxFrame {
public:
    MainFrame(const wxString& title, Services::SecurityManager* security_manager);
    virtual ~MainFrame();
    
    void SetServices(Services::StudentService* student_service,
                    Services::TeacherService* teacher_service,
                    Services::CourseService* course_service,
                    Services::EnrollmentService* enrollment_service,
                    Services::AttendanceService* attendance_service,
                    Services::EmployeeService* employee_service);
    
private:
    // UI components
    wxPanel* main_panel_;
    wxNotebook* notebook_;
    wxStatusBar* status_bar_;
    
    // Service pointers
    Services::StudentService* student_service_;
    Services::TeacherService* teacher_service_;
    Services::CourseService* course_service_;
    Services::EnrollmentService* enrollment_service_;
    Services::AttendanceService* attendance_service_;
    Services::EmployeeService* employee_service_;
    Services::SecurityManager* security_manager_;
    
    // Panels
    wxPanel* dashboard_panel_;
    wxPanel* students_panel_;
    wxPanel* teachers_panel_;
    wxPanel* courses_panel_;
    wxPanel* enrollments_panel_;
    wxPanel* attendance_panel_;
    wxPanel* employees_panel_;
    wxPanel* reports_panel_;
    wxPanel* settings_panel_;
    
    // Dashboard labels
    wxStaticText* student_count_label_;
    wxStaticText* teacher_count_label_;
    wxStaticText* course_count_label_;
    wxStaticText* employee_count_label_;
    
    // Event handlers
    void OnNotebookPageChanged(wxBookCtrlEvent& event);
    void OnExit(wxCommandEvent& event);
    void OnAbout(wxCommandEvent& event);
    void OnLogout(wxCommandEvent& event);
    
    // Student event handlers
    void OnAddStudent(wxListCtrl* list_ctrl);
    void OnEditStudent(wxListCtrl* list_ctrl);
    void OnDeleteStudent(wxListCtrl* list_ctrl);
    void OnRefreshStudents(wxListCtrl* list_ctrl);
    
    // Teacher event handlers
    void OnAddTeacher(wxListCtrl* list_ctrl);
    void OnEditTeacher(wxListCtrl* list_ctrl);
    void OnDeleteTeacher(wxListCtrl* list_ctrl);
    void OnRefreshTeachers(wxListCtrl* list_ctrl);
    
    // Course event handlers
    void OnAddCourse(wxListCtrl* list_ctrl);
    void OnEditCourse(wxListCtrl* list_ctrl);
    void OnDeleteCourse(wxListCtrl* list_ctrl);
    void OnRefreshCourses(wxListCtrl* list_ctrl);
    
    // Employee event handlers
    void OnAddEmployee(wxListCtrl* list_ctrl);
    void OnEditEmployee(wxListCtrl* list_ctrl);
    void OnDeleteEmployee(wxListCtrl* list_ctrl);
    void OnRefreshEmployees(wxListCtrl* list_ctrl);
    
    // Enrollment event handlers
    void OnAddEnrollment(wxListCtrl* list_ctrl);
    void OnEditEnrollment(wxListCtrl* list_ctrl);
    void OnDeleteEnrollment(wxListCtrl* list_ctrl);
    void OnRefreshEnrollments(wxListCtrl* list_ctrl);
    
    // Attendance event handlers
    void OnAddAttendance(wxListCtrl* list_ctrl);
    void OnEditAttendance(wxListCtrl* list_ctrl);
    void OnDeleteAttendance(wxListCtrl* list_ctrl);
    void OnRefreshAttendance(wxListCtrl* list_ctrl);
    
    // UI creation methods
    void CreateMenuBar();
    void SetupStatusBar();
    void CreateMainPanel();
    void CreateDashboardPanel();
    void CreateStudentsPanel();
    void CreateTeachersPanel();
    void CreateCoursesPanel();
    void CreateEnrollmentsPanel();
    void CreateAttendancePanel();
    void CreateEmployeesPanel();
    void CreateReportsPanel();
    void CreateSettingsPanel();
    
    // Helper methods
    void UpdateDashboardStats();
    wxString GetCurrentUserInfo();
    
    wxDECLARE_EVENT_TABLE();
};

enum {
    ID_EXIT = wxID_EXIT,
    ID_ABOUT = wxID_ABOUT,
    ID_LOGOUT = wxID_HIGHEST + 1,
    ID_NOTEBOOK
};

} // namespace GUI
} // namespace SDEP

#endif // MAINFRAME_H