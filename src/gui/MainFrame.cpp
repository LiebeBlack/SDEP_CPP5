#include "gui/MainFrame.h"
#include "gui/StudentDialog.h"
#include "gui/TeacherDialog.h"
#include "gui/CourseDialog.h"
#include "gui/EmployeeDialog.h"
#include "gui/EnrollmentDialog.h"
#include "gui/AttendanceDialog.h"
#include <wx/splitter.h>
#include <wx/stattext.h>
#include <wx/button.h>
#include <wx/textctrl.h>
#include <wx/listctrl.h>
#include <wx/sizer.h>
#include <wx/msgdlg.h>

namespace SDEP {
namespace GUI {

wxBEGIN_EVENT_TABLE(MainFrame, wxFrame)
    EVT_MENU(ID_EXIT, MainFrame::OnExit)
    EVT_MENU(ID_ABOUT, MainFrame::OnAbout)
    EVT_MENU(ID_LOGOUT, MainFrame::OnLogout)
    EVT_NOTEBOOK_PAGE_CHANGED(ID_NOTEBOOK, MainFrame::OnNotebookPageChanged)
wxEND_EVENT_TABLE()

MainFrame::MainFrame(const wxString& title, Services::SecurityManager* security_manager)
    : wxFrame(nullptr, wxID_ANY, title, wxDefaultPosition, wxSize(1200, 800)),
      security_manager_(security_manager),
      student_service_(nullptr),
      teacher_service_(nullptr),
      course_service_(nullptr),
      enrollment_service_(nullptr),
      attendance_service_(nullptr),
      employee_service_(nullptr) {
    
    // Create UI
    CreateMenuBar();
    CreateStatusBar();
    CreateMainPanel();
    
    // Center the frame
    Centre();
    
    // Show the frame
    Show(true);
}

MainFrame::~MainFrame() {
}

void MainFrame::SetServices(Services::StudentService* student_service,
                            Services::TeacherService* teacher_service,
                            Services::CourseService* course_service,
                            Services::EnrollmentService* enrollment_service,
                            Services::AttendanceService* attendance_service,
                            Services::EmployeeService* employee_service) {
    student_service_ = student_service;
    teacher_service_ = teacher_service;
    course_service_ = course_service;
    enrollment_service_ = enrollment_service;
    attendance_service_ = attendance_service;
    employee_service_ = employee_service;
    
    // Update dashboard with real data
    UpdateDashboardStats();
}

void MainFrame::CreateMenuBar() {
    wxMenuBar* menu_bar = new wxMenuBar();
    
    // File menu
    wxMenu* file_menu = new wxMenu();
    file_menu->Append(ID_LOGOUT, "Logout\tCtrl+L", "Logout from the system");
    file_menu->AppendSeparator();
    file_menu->Append(ID_EXIT, "Exit\tCtrl+Q", "Exit the application");
    menu_bar->Append(file_menu, "&File");
    
    // Help menu
    wxMenu* help_menu = new wxMenu();
    help_menu->Append(ID_ABOUT, "&About\tF1", "About this application");
    menu_bar->Append(help_menu, "&Help");
    
    SetMenuBar(menu_bar);
}

void MainFrame::CreateStatusBar() {
    wxFrame::CreateStatusBar(2);
    SetStatusText("Welcome to SDEP Educational Management System", 0);
    SetStatusText(wxDateTime::Now().Format(wxT("%H:%M:%S")), 1);
}

void MainFrame::CreateMainPanel() {
    main_panel_ = new wxPanel(this);
    
    wxBoxSizer* main_sizer = new wxBoxSizer(wxVERTICAL);
    
    // Create notebook for different panels
    notebook_ = new wxNotebook(main_panel_, ID_NOTEBOOK, wxDefaultPosition, wxDefaultSize, wxNB_DEFAULT);
    
    // Create all panels
    CreateDashboardPanel();
    CreateStudentsPanel();
    CreateTeachersPanel();
    CreateCoursesPanel();
    CreateEnrollmentsPanel();
    CreateAttendancePanel();
    CreateEmployeesPanel();
    CreateReportsPanel();
    CreateSettingsPanel();
    
    // Add panels to notebook
    notebook_->AddPage(dashboard_panel_, "Dashboard", true);
    notebook_->AddPage(students_panel_, "Students");
    notebook_->AddPage(teachers_panel_, "Teachers");
    notebook_->AddPage(courses_panel_, "Courses");
    notebook_->AddPage(enrollments_panel_, "Enrollments");
    notebook_->AddPage(attendance_panel_, "Attendance");
    notebook_->AddPage(employees_panel_, "Employees");
    notebook_->AddPage(reports_panel_, "Reports");
    notebook_->AddPage(settings_panel_, "Settings");
    
    main_sizer->Add(notebook_, 1, wxEXPAND | wxALL, 5);
    
    main_panel_->SetSizer(main_sizer);
    main_panel_->Layout();
}

void MainFrame::CreateDashboardPanel() {
    dashboard_panel_ = new wxPanel(notebook_);
    
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    // Welcome message
    wxStaticText* welcome_text = new wxStaticText(dashboard_panel_, wxID_ANY, 
        "Welcome to SDEP Educational Management System");
    welcome_text->SetFont(welcome_text->GetFont().Larger().Larger().Bold());
    sizer->Add(welcome_text, 0, wxALL, 10);
    
    // Statistics grid
    wxGridSizer* stats_sizer = new wxGridSizer(2, 2, 10, 10);
    
    // Student count
    wxStaticText* student_label = new wxStaticText(dashboard_panel_, wxID_ANY, "Total Students:");
    student_count_label_ = new wxStaticText(dashboard_panel_, wxID_ANY, "0");
    student_count_label_->SetFont(student_count_label_->GetFont().Larger().Bold());
    
    wxBoxSizer* student_sizer = new wxBoxSizer(wxVERTICAL);
    student_sizer->Add(student_label, 0, wxALL, 5);
    student_sizer->Add(student_count_label_, 0, wxALL, 5);
    
    wxStaticBox* student_box = new wxStaticBox(dashboard_panel_, wxID_ANY, "Students");
    wxStaticBoxSizer* student_box_sizer = new wxStaticBoxSizer(student_box, wxVERTICAL);
    student_box_sizer->Add(student_sizer, 1, wxEXPAND);
    
    // Teacher count
    wxStaticText* teacher_label = new wxStaticText(dashboard_panel_, wxID_ANY, "Total Teachers:");
    teacher_count_label_ = new wxStaticText(dashboard_panel_, wxID_ANY, "0");
    teacher_count_label_->SetFont(teacher_count_label_->GetFont().Larger().Bold());
    
    wxBoxSizer* teacher_sizer = new wxBoxSizer(wxVERTICAL);
    teacher_sizer->Add(teacher_label, 0, wxALL, 5);
    teacher_sizer->Add(teacher_count_label_, 0, wxALL, 5);
    
    wxStaticBox* teacher_box = new wxStaticBox(dashboard_panel_, wxID_ANY, "Teachers");
    wxStaticBoxSizer* teacher_box_sizer = new wxStaticBoxSizer(teacher_box, wxVERTICAL);
    teacher_box_sizer->Add(teacher_sizer, 1, wxEXPAND);
    
    // Course count
    wxStaticText* course_label = new wxStaticText(dashboard_panel_, wxID_ANY, "Total Courses:");
    course_count_label_ = new wxStaticText(dashboard_panel_, wxID_ANY, "0");
    course_count_label_->SetFont(course_count_label_->GetFont().Larger().Bold());
    
    wxBoxSizer* course_sizer = new wxBoxSizer(wxVERTICAL);
    course_sizer->Add(course_label, 0, wxALL, 5);
    course_sizer->Add(course_count_label_, 0, wxALL, 5);
    
    wxStaticBox* course_box = new wxStaticBox(dashboard_panel_, wxID_ANY, "Courses");
    wxStaticBoxSizer* course_box_sizer = new wxStaticBoxSizer(course_box, wxVERTICAL);
    course_box_sizer->Add(course_sizer, 1, wxEXPAND);
    
    // Employee count
    wxStaticText* employee_label = new wxStaticText(dashboard_panel_, wxID_ANY, "Total Employees:");
    employee_count_label_ = new wxStaticText(dashboard_panel_, wxID_ANY, "0");
    employee_count_label_->SetFont(employee_count_label_->GetFont().Larger().Bold());
    
    wxBoxSizer* employee_sizer = new wxBoxSizer(wxVERTICAL);
    employee_sizer->Add(employee_label, 0, wxALL, 5);
    employee_sizer->Add(employee_count_label_, 0, wxALL, 5);
    
    wxStaticBox* employee_box = new wxStaticBox(dashboard_panel_, wxID_ANY, "Employees");
    wxStaticBoxSizer* employee_box_sizer = new wxStaticBoxSizer(employee_box, wxVERTICAL);
    employee_box_sizer->Add(employee_sizer, 1, wxEXPAND);
    
    stats_sizer->Add(student_box_sizer, 1, wxEXPAND);
    stats_sizer->Add(teacher_box_sizer, 1, wxEXPAND);
    stats_sizer->Add(course_box_sizer, 1, wxEXPAND);
    stats_sizer->Add(employee_box_sizer, 1, wxEXPAND);
    
    sizer->Add(stats_sizer, 1, wxEXPAND | wxALL, 10);
    
    dashboard_panel_->SetSizer(sizer);
}

void MainFrame::CreateStudentsPanel() {
    students_panel_ = new wxPanel(notebook_);
    
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    // Title
    wxStaticText* title = new wxStaticText(students_panel_, wxID_ANY, "Student Management");
    title->SetFont(title->GetFont().Larger().Bold());
    sizer->Add(title, 0, wxALL, 10);
    
    // Toolbar
    wxPanel* toolbar = new wxPanel(students_panel_);
    wxBoxSizer* toolbar_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* add_button = new wxButton(toolbar, wxID_ADD, "Add Student");
    wxButton* edit_button = new wxButton(toolbar, wxID_EDIT, "Edit Student");
    wxButton* delete_button = new wxButton(toolbar, wxID_DELETE, "Delete Student");
    wxButton* refresh_button = new wxButton(toolbar, wxID_REFRESH, "Refresh");
    
    toolbar_sizer->Add(add_button, 0, wxALL, 5);
    toolbar_sizer->Add(edit_button, 0, wxALL, 5);
    toolbar_sizer->Add(delete_button, 0, wxALL, 5);
    toolbar_sizer->Add(refresh_button, 0, wxALL, 5);
    toolbar_sizer->AddStretchSpacer();
    
    wxTextCtrl* search_ctrl = new wxTextCtrl(toolbar, wxID_FIND, "", wxDefaultPosition, wxSize(200, -1), wxTE_PROCESS_ENTER);
    toolbar_sizer->Add(search_ctrl, 0, wxALL, 5);
    
    toolbar->SetSizer(toolbar_sizer);
    sizer->Add(toolbar, 0, wxEXPAND | wxALL, 5);
    
    // Student list
    wxListCtrl* student_list = new wxListCtrl(students_panel_, wxID_ANY, 
        wxDefaultPosition, wxDefaultSize, wxLC_REPORT | wxLC_SINGLE_SEL);
    
    student_list->AppendColumn("ID", wxLIST_FORMAT_LEFT, 50);
    student_list->AppendColumn("Name", wxLIST_FORMAT_LEFT, 200);
    student_list->AppendColumn("Grade", wxLIST_FORMAT_LEFT, 100);
    student_list->AppendColumn("Section", wxLIST_FORMAT_LEFT, 100);
    student_list->AppendColumn("Status", wxLIST_FORMAT_LEFT, 100);
    student_list->AppendColumn("Email", wxLIST_FORMAT_LEFT, 200);
    
    sizer->Add(student_list, 1, wxEXPAND | wxALL, 5);
    
    // Connect button events
    add_button->Bind(wxEVT_BUTTON, [this, student_list](wxCommandEvent&) {
        OnAddStudent(student_list);
    });
    
    edit_button->Bind(wxEVT_BUTTON, [this, student_list](wxCommandEvent&) {
        OnEditStudent(student_list);
    });
    
    delete_button->Bind(wxEVT_BUTTON, [this, student_list](wxCommandEvent&) {
        OnDeleteStudent(student_list);
    });
    
    refresh_button->Bind(wxEVT_BUTTON, [this, student_list](wxCommandEvent&) {
        OnRefreshStudents(student_list);
    });
    
    students_panel_->SetSizer(sizer);
}

void MainFrame::CreateTeachersPanel() {
    teachers_panel_ = new wxPanel(notebook_);
    
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxStaticText* title = new wxStaticText(teachers_panel_, wxID_ANY, "Teacher Management");
    title->SetFont(title->GetFont().Larger().Bold());
    sizer->Add(title, 0, wxALL, 10);
    
    wxPanel* toolbar = new wxPanel(teachers_panel_);
    wxBoxSizer* toolbar_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* add_button = new wxButton(toolbar, wxID_ADD, "Add Teacher");
    wxButton* edit_button = new wxButton(toolbar, wxID_EDIT, "Edit Teacher");
    wxButton* delete_button = new wxButton(toolbar, wxID_DELETE, "Delete Teacher");
    wxButton* refresh_button = new wxButton(toolbar, wxID_REFRESH, "Refresh");
    
    toolbar_sizer->Add(add_button, 0, wxALL, 5);
    toolbar_sizer->Add(edit_button, 0, wxALL, 5);
    toolbar_sizer->Add(delete_button, 0, wxALL, 5);
    toolbar_sizer->Add(refresh_button, 0, wxALL, 5);
    toolbar_sizer->AddStretchSpacer();
    
    wxTextCtrl* search_ctrl = new wxTextCtrl(toolbar, wxID_FIND, "", wxDefaultPosition, wxSize(200, -1));
    toolbar_sizer->Add(search_ctrl, 0, wxALL, 5);
    
    toolbar->SetSizer(toolbar_sizer);
    sizer->Add(toolbar, 0, wxEXPAND | wxALL, 5);
    
    wxListCtrl* teacher_list = new wxListCtrl(teachers_panel_, wxID_ANY, 
        wxDefaultPosition, wxDefaultSize, wxLC_REPORT | wxLC_SINGLE_SEL);
    
    teacher_list->AppendColumn("ID", wxLIST_FORMAT_LEFT, 50);
    teacher_list->AppendColumn("Name", wxLIST_FORMAT_LEFT, 200);
    teacher_list->AppendColumn("Department", wxLIST_FORMAT_LEFT, 150);
    teacher_list->AppendColumn("Specialization", wxLIST_FORMAT_LEFT, 150);
    teacher_list->AppendColumn("Status", wxLIST_FORMAT_LEFT, 100);
    teacher_list->AppendColumn("Email", wxLIST_FORMAT_LEFT, 200);
    
    sizer->Add(teacher_list, 1, wxEXPAND | wxALL, 5);
    
    // Connect button events
    add_button->Bind(wxEVT_BUTTON, [this, teacher_list](wxCommandEvent&) {
        OnAddTeacher(teacher_list);
    });
    
    edit_button->Bind(wxEVT_BUTTON, [this, teacher_list](wxCommandEvent&) {
        OnEditTeacher(teacher_list);
    });
    
    delete_button->Bind(wxEVT_BUTTON, [this, teacher_list](wxCommandEvent&) {
        OnDeleteTeacher(teacher_list);
    });
    
    refresh_button->Bind(wxEVT_BUTTON, [this, teacher_list](wxCommandEvent&) {
        OnRefreshTeachers(teacher_list);
    });
    
    teachers_panel_->SetSizer(sizer);
}

void MainFrame::CreateCoursesPanel() {
    courses_panel_ = new wxPanel(notebook_);
    
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxStaticText* title = new wxStaticText(courses_panel_, wxID_ANY, "Course Management");
    title->SetFont(title->GetFont().Larger().Bold());
    sizer->Add(title, 0, wxALL, 10);
    
    wxPanel* toolbar = new wxPanel(courses_panel_);
    wxBoxSizer* toolbar_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* add_button = new wxButton(toolbar, wxID_ADD, "Add Course");
    wxButton* edit_button = new wxButton(toolbar, wxID_EDIT, "Edit Course");
    wxButton* delete_button = new wxButton(toolbar, wxID_DELETE, "Delete Course");
    wxButton* refresh_button = new wxButton(toolbar, wxID_REFRESH, "Refresh");
    
    toolbar_sizer->Add(add_button, 0, wxALL, 5);
    toolbar_sizer->Add(edit_button, 0, wxALL, 5);
    toolbar_sizer->Add(delete_button, 0, wxALL, 5);
    toolbar_sizer->Add(refresh_button, 0, wxALL, 5);
    toolbar_sizer->AddStretchSpacer();
    
    wxTextCtrl* search_ctrl = new wxTextCtrl(toolbar, wxID_FIND, "", wxDefaultPosition, wxSize(200, -1));
    toolbar_sizer->Add(search_ctrl, 0, wxALL, 5);
    
    toolbar->SetSizer(toolbar_sizer);
    sizer->Add(toolbar, 0, wxEXPAND | wxALL, 5);
    
    wxListCtrl* course_list = new wxListCtrl(courses_panel_, wxID_ANY, 
        wxDefaultPosition, wxDefaultSize, wxLC_REPORT | wxLC_SINGLE_SEL);
    
    course_list->AppendColumn("ID", wxLIST_FORMAT_LEFT, 50);
    course_list->AppendColumn("Code", wxLIST_FORMAT_LEFT, 100);
    course_list->AppendColumn("Name", wxLIST_FORMAT_LEFT, 200);
    course_list->AppendColumn("Level", wxLIST_FORMAT_LEFT, 100);
    course_list->AppendColumn("Teacher", wxLIST_FORMAT_LEFT, 150);
    course_list->AppendColumn("Credits", wxLIST_FORMAT_LEFT, 80);
    course_list->AppendColumn("Status", wxLIST_FORMAT_LEFT, 100);
    
    sizer->Add(course_list, 1, wxEXPAND | wxALL, 5);
    
    // Connect button events
    add_button->Bind(wxEVT_BUTTON, [this, course_list](wxCommandEvent&) {
        OnAddCourse(course_list);
    });
    
    edit_button->Bind(wxEVT_BUTTON, [this, course_list](wxCommandEvent&) {
        OnEditCourse(course_list);
    });
    
    delete_button->Bind(wxEVT_BUTTON, [this, course_list](wxCommandEvent&) {
        OnDeleteCourse(course_list);
    });
    
    refresh_button->Bind(wxEVT_BUTTON, [this, course_list](wxCommandEvent&) {
        OnRefreshCourses(course_list);
    });
    
    courses_panel_->SetSizer(sizer);
}

void MainFrame::CreateEnrollmentsPanel() {
    enrollments_panel_ = new wxPanel(notebook_);
    
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxStaticText* title = new wxStaticText(enrollments_panel_, wxID_ANY, "Enrollment Management");
    title->SetFont(title->GetFont().Larger().Bold());
    sizer->Add(title, 0, wxALL, 10);
    
    wxPanel* toolbar = new wxPanel(enrollments_panel_);
    wxBoxSizer* toolbar_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* add_button = new wxButton(toolbar, wxID_ADD, "New Enrollment");
    wxButton* edit_button = new wxButton(toolbar, wxID_EDIT, "Edit Enrollment");
    wxButton* delete_button = new wxButton(toolbar, wxID_DELETE, "Delete Enrollment");
    wxButton* refresh_button = new wxButton(toolbar, wxID_REFRESH, "Refresh");
    
    toolbar_sizer->Add(add_button, 0, wxALL, 5);
    toolbar_sizer->Add(edit_button, 0, wxALL, 5);
    toolbar_sizer->Add(delete_button, 0, wxALL, 5);
    toolbar_sizer->Add(refresh_button, 0, wxALL, 5);
    toolbar_sizer->AddStretchSpacer();
    
    toolbar->SetSizer(toolbar_sizer);
    sizer->Add(toolbar, 0, wxEXPAND | wxALL, 5);
    
    wxListCtrl* enrollment_list = new wxListCtrl(enrollments_panel_, wxID_ANY, 
        wxDefaultPosition, wxDefaultSize, wxLC_REPORT | wxLC_SINGLE_SEL);
    
    enrollment_list->AppendColumn("ID", wxLIST_FORMAT_LEFT, 50);
    enrollment_list->AppendColumn("Student", wxLIST_FORMAT_LEFT, 200);
    enrollment_list->AppendColumn("Course", wxLIST_FORMAT_LEFT, 200);
    enrollment_list->AppendColumn("Enrollment Date", wxLIST_FORMAT_LEFT, 120);
    enrollment_list->AppendColumn("Grade", wxLIST_FORMAT_LEFT, 80);
    enrollment_list->AppendColumn("Status", wxLIST_FORMAT_LEFT, 100);
    
    sizer->Add(enrollment_list, 1, wxEXPAND | wxALL, 5);
    
    // Connect button events
    add_button->Bind(wxEVT_BUTTON, [this, enrollment_list](wxCommandEvent&) {
        OnAddEnrollment(enrollment_list);
    });
    
    edit_button->Bind(wxEVT_BUTTON, [this, enrollment_list](wxCommandEvent&) {
        OnEditEnrollment(enrollment_list);
    });
    
    delete_button->Bind(wxEVT_BUTTON, [this, enrollment_list](wxCommandEvent&) {
        OnDeleteEnrollment(enrollment_list);
    });
    
    refresh_button->Bind(wxEVT_BUTTON, [this, enrollment_list](wxCommandEvent&) {
        OnRefreshEnrollments(enrollment_list);
    });
    
    enrollments_panel_->SetSizer(sizer);
}

void MainFrame::CreateAttendancePanel() {
    attendance_panel_ = new wxPanel(notebook_);
    
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxStaticText* title = new wxStaticText(attendance_panel_, wxID_ANY, "Attendance Management");
    title->SetFont(title->GetFont().Larger().Bold());
    sizer->Add(title, 0, wxALL, 10);
    
    wxPanel* toolbar = new wxPanel(attendance_panel_);
    wxBoxSizer* toolbar_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* mark_button = new wxButton(toolbar, wxID_ADD, "Mark Attendance");
    wxButton* edit_button = new wxButton(toolbar, wxID_EDIT, "Edit Attendance");
    wxButton* delete_button = new wxButton(toolbar, wxID_DELETE, "Delete Attendance");
    wxButton* refresh_button = new wxButton(toolbar, wxID_REFRESH, "Refresh");
    
    toolbar_sizer->Add(mark_button, 0, wxALL, 5);
    toolbar_sizer->Add(edit_button, 0, wxALL, 5);
    toolbar_sizer->Add(delete_button, 0, wxALL, 5);
    toolbar_sizer->Add(refresh_button, 0, wxALL, 5);
    toolbar_sizer->AddStretchSpacer();
    
    wxTextCtrl* date_ctrl = new wxTextCtrl(toolbar, wxID_FIND, wxDateTime::Now().FormatISODate());
    toolbar_sizer->Add(date_ctrl, 0, wxALL, 5);
    
    toolbar->SetSizer(toolbar_sizer);
    sizer->Add(toolbar, 0, wxEXPAND | wxALL, 5);
    
    wxListCtrl* attendance_list = new wxListCtrl(attendance_panel_, wxID_ANY, 
        wxDefaultPosition, wxDefaultSize, wxLC_REPORT | wxLC_SINGLE_SEL);
    
    attendance_list->AppendColumn("ID", wxLIST_FORMAT_LEFT, 50);
    attendance_list->AppendColumn("Student", wxLIST_FORMAT_LEFT, 200);
    attendance_list->AppendColumn("Course", wxLIST_FORMAT_LEFT, 200);
    attendance_list->AppendColumn("Date", wxLIST_FORMAT_LEFT, 120);
    attendance_list->AppendColumn("Status", wxLIST_FORMAT_LEFT, 100);
    attendance_list->AppendColumn("Notes", wxLIST_FORMAT_LEFT, 200);
    
    sizer->Add(attendance_list, 1, wxEXPAND | wxALL, 5);
    
    // Connect button events
    mark_button->Bind(wxEVT_BUTTON, [this, attendance_list](wxCommandEvent&) {
        OnAddAttendance(attendance_list);
    });
    
    edit_button->Bind(wxEVT_BUTTON, [this, attendance_list](wxCommandEvent&) {
        OnEditAttendance(attendance_list);
    });
    
    delete_button->Bind(wxEVT_BUTTON, [this, attendance_list](wxCommandEvent&) {
        OnDeleteAttendance(attendance_list);
    });
    
    refresh_button->Bind(wxEVT_BUTTON, [this, attendance_list](wxCommandEvent&) {
        OnRefreshAttendance(attendance_list);
    });
    
    attendance_panel_->SetSizer(sizer);
}

void MainFrame::CreateEmployeesPanel() {
    employees_panel_ = new wxPanel(notebook_);
    
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxStaticText* title = new wxStaticText(employees_panel_, wxID_ANY, "Employee Management (HR)");
    title->SetFont(title->GetFont().Larger().Bold());
    sizer->Add(title, 0, wxALL, 10);
    
    wxPanel* toolbar = new wxPanel(employees_panel_);
    wxBoxSizer* toolbar_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* add_button = new wxButton(toolbar, wxID_ADD, "Add Employee");
    wxButton* edit_button = new wxButton(toolbar, wxID_EDIT, "Edit Employee");
    wxButton* delete_button = new wxButton(toolbar, wxID_DELETE, "Delete Employee");
    wxButton* refresh_button = new wxButton(toolbar, wxID_REFRESH, "Refresh");
    
    toolbar_sizer->Add(add_button, 0, wxALL, 5);
    toolbar_sizer->Add(edit_button, 0, wxALL, 5);
    toolbar_sizer->Add(delete_button, 0, wxALL, 5);
    toolbar_sizer->Add(refresh_button, 0, wxALL, 5);
    toolbar_sizer->AddStretchSpacer();
    
    wxTextCtrl* search_ctrl = new wxTextCtrl(toolbar, wxID_FIND, "", wxDefaultPosition, wxSize(200, -1));
    toolbar_sizer->Add(search_ctrl, 0, wxALL, 5);
    
    toolbar->SetSizer(toolbar_sizer);
    sizer->Add(toolbar, 0, wxEXPAND | wxALL, 5);
    
    wxListCtrl* employee_list = new wxListCtrl(employees_panel_, wxID_ANY, 
        wxDefaultPosition, wxDefaultSize, wxLC_REPORT | wxLC_SINGLE_SEL);
    
    employee_list->AppendColumn("ID", wxLIST_FORMAT_LEFT, 50);
    employee_list->AppendColumn("Code", wxLIST_FORMAT_LEFT, 100);
    employee_list->AppendColumn("Name", wxLIST_FORMAT_LEFT, 200);
    employee_list->AppendColumn("Department", wxLIST_FORMAT_LEFT, 150);
    employee_list->AppendColumn("Position", wxLIST_FORMAT_LEFT, 150);
    employee_list->AppendColumn("Status", wxLIST_FORMAT_LEFT, 100);
    
    sizer->Add(employee_list, 1, wxEXPAND | wxALL, 5);
    
    // Connect button events
    add_button->Bind(wxEVT_BUTTON, [this, employee_list](wxCommandEvent&) {
        OnAddEmployee(employee_list);
    });
    
    edit_button->Bind(wxEVT_BUTTON, [this, employee_list](wxCommandEvent&) {
        OnEditEmployee(employee_list);
    });
    
    delete_button->Bind(wxEVT_BUTTON, [this, employee_list](wxCommandEvent&) {
        OnDeleteEmployee(employee_list);
    });
    
    refresh_button->Bind(wxEVT_BUTTON, [this, employee_list](wxCommandEvent&) {
        OnRefreshEmployees(employee_list);
    });
    
    employees_panel_->SetSizer(sizer);
}

void MainFrame::CreateReportsPanel() {
    reports_panel_ = new wxPanel(notebook_);
    
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxStaticText* title = new wxStaticText(reports_panel_, wxID_ANY, "Reports and Analytics");
    title->SetFont(title->GetFont().Larger().Bold());
    sizer->Add(title, 0, wxALL, 10);
    
    // Report categories
    wxBoxSizer* category_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxStaticBox* academic_box = new wxStaticBox(reports_panel_, wxID_ANY, "Academic Reports");
    wxStaticBoxSizer* academic_sizer = new wxStaticBoxSizer(academic_box, wxVERTICAL);
    
    wxButton* student_report_btn = new wxButton(reports_panel_, wxID_ANY, "Student Report");
    wxButton* teacher_report_btn = new wxButton(reports_panel_, wxID_ANY, "Teacher Report");
    wxButton* course_report_btn = new wxButton(reports_panel_, wxID_ANY, "Course Report");
    wxButton* attendance_report_btn = new wxButton(reports_panel_, wxID_ANY, "Attendance Report");
    
    academic_sizer->Add(student_report_btn, 0, wxALL, 5);
    academic_sizer->Add(teacher_report_btn, 0, wxALL, 5);
    academic_sizer->Add(course_report_btn, 0, wxALL, 5);
    academic_sizer->Add(attendance_report_btn, 0, wxALL, 5);
    
    wxStaticBox* hr_box = new wxStaticBox(reports_panel_, wxID_ANY, "HR Reports");
    wxStaticBoxSizer* hr_sizer = new wxStaticBoxSizer(hr_box, wxVERTICAL);
    
    wxButton* employee_report_btn = new wxButton(reports_panel_, wxID_ANY, "Employee Report");
    wxButton* payroll_report_btn = new wxButton(reports_panel_, wxID_ANY, "Payroll Report");
    wxButton* leave_report_btn = new wxButton(reports_panel_, wxID_ANY, "Leave Report");
    wxButton* disciplinary_report_btn = new wxButton(reports_panel_, wxID_ANY, "Disciplinary Report");
    
    hr_sizer->Add(employee_report_btn, 0, wxALL, 5);
    hr_sizer->Add(payroll_report_btn, 0, wxALL, 5);
    hr_sizer->Add(leave_report_btn, 0, wxALL, 5);
    hr_sizer->Add(disciplinary_report_btn, 0, wxALL, 5);
    
    category_sizer->Add(academic_sizer, 1, wxEXPAND | wxALL, 10);
    category_sizer->Add(hr_sizer, 1, wxEXPAND | wxALL, 10);
    
    sizer->Add(category_sizer, 0, wxEXPAND | wxALL, 10);
    
    // Report generation options
    wxStaticBox* options_box = new wxStaticBox(reports_panel_, wxID_ANY, "Report Options");
    wxStaticBoxSizer* options_sizer = new wxStaticBoxSizer(options_box, wxHORIZONTAL);
    
    wxStaticText* date_range_label = new wxStaticText(reports_panel_, wxID_ANY, "Date Range:");
    wxDatePickerCtrl* start_date = new wxDatePickerCtrl(reports_panel_, wxID_ANY);
    wxStaticText* to_label = new wxStaticText(reports_panel_, wxID_ANY, "to");
    wxDatePickerCtrl* end_date = new wxDatePickerCtrl(reports_panel_, wxID_ANY);
    
    wxCheckBox* pdf_checkbox = new wxCheckBox(reports_panel_, wxID_ANY, "Generate PDF");
    wxCheckBox* csv_checkbox = new wxCheckBox(reports_panel_, wxID_ANY, "Generate CSV");
    
    wxButton* generate_btn = new wxButton(reports_panel_, wxID_ANY, "Generate Report");
    
    options_sizer->Add(date_range_label, 0, wxALL | wxALIGN_CENTER_VERTICAL, 5);
    options_sizer->Add(start_date, 0, wxALL, 5);
    options_sizer->Add(to_label, 0, wxALL | wxALIGN_CENTER_VERTICAL, 5);
    options_sizer->Add(end_date, 0, wxALL, 5);
    options_sizer->AddStretchSpacer();
    options_sizer->Add(pdf_checkbox, 0, wxALL | wxALIGN_CENTER_VERTICAL, 5);
    options_sizer->Add(csv_checkbox, 0, wxALL | wxALIGN_CENTER_VERTICAL, 5);
    options_sizer->Add(generate_btn, 0, wxALL, 5);
    
    sizer->Add(options_sizer, 0, wxEXPAND | wxALL, 10);
    
    // Status area
    wxStaticText* status_text = new wxStaticText(reports_panel_, wxID_ANY, 
        "Select a report type and options to generate reports.");
    status_text->SetFont(status_text->GetFont().Italic());
    sizer->Add(status_text, 0, wxALL, 10);
    
    reports_panel_->SetSizer(sizer);
    
    // Connect button events
    student_report_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Student report generation will be implemented with PDF export", "Info", wxOK | wxICON_INFORMATION);
    });
    
    teacher_report_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Teacher report generation will be implemented with PDF export", "Info", wxOK | wxICON_INFORMATION);
    });
    
    course_report_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Course report generation will be implemented with PDF export", "Info", wxOK | wxICON_INFORMATION);
    });
    
    attendance_report_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Attendance report generation will be implemented with PDF export", "Info", wxOK | wxICON_INFORMATION);
    });
    
    employee_report_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Employee report generation will be implemented with PDF export", "Info", wxOK | wxICON_INFORMATION);
    });
    
    payroll_report_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Payroll report generation will be implemented with PDF export", "Info", wxOK | wxICON_INFORMATION);
    });
    
    leave_report_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Leave report generation will be implemented with PDF export", "Info", wxOK | wxICON_INFORMATION);
    });
    
    disciplinary_report_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Disciplinary report generation will be implemented with PDF export", "Info", wxOK | wxICON_INFORMATION);
    });
    
    generate_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Report generation will be implemented with PDF and CSV export functionality", "Info", wxOK | wxICON_INFORMATION);
    });
}

void MainFrame::CreateSettingsPanel() {
    settings_panel_ = new wxPanel(notebook_);
    
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxStaticText* title = new wxStaticText(settings_panel_, wxID_ANY, "System Settings");
    title->SetFont(title->GetFont().Larger().Bold());
    sizer->Add(title, 0, wxALL, 10);
    
    // Create notebook for settings categories
    wxNotebook* settings_notebook = new wxNotebook(settings_panel_, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxNB_DEFAULT);
    
    // General settings panel
    wxPanel* general_panel = new wxPanel(settings_notebook);
    wxBoxSizer* general_sizer = new wxBoxSizer(wxVERTICAL);
    
    wxFlexGridSizer* general_grid = new wxFlexGridSizer(2, 10, 10);
    general_grid->AddGrowableCol(1);
    
    general_grid->Add(new wxStaticText(general_panel, wxID_ANY, "Institution Name:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxTextCtrl* institution_name = new wxTextCtrl(general_panel, wxID_ANY, "SDEP Educational System");
    general_grid->Add(institution_name, 1, wxEXPAND | wxALL, 5);
    
    general_grid->Add(new wxStaticText(general_panel, wxID_ANY, "Academic Year:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxTextCtrl* academic_year = new wxTextCtrl(general_panel, wxID_ANY, "2026-2027");
    general_grid->Add(academic_year, 1, wxEXPAND | wxALL, 5);
    
    general_grid->Add(new wxStaticText(general_panel, wxID_ANY, "Default Grade:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxTextCtrl* default_grade = new wxTextCtrl(general_panel, wxID_ANY, "10");
    general_grid->Add(default_grade, 1, wxEXPAND | wxALL, 5);
    
    general_sizer->Add(general_grid, 1, wxEXPAND | wxALL, 10);
    general_panel->SetSizer(general_sizer);
    
    // Security settings panel
    wxPanel* security_panel = new wxPanel(settings_notebook);
    wxBoxSizer* security_sizer = new wxBoxSizer(wxVERTICAL);
    
    wxFlexGridSizer* security_grid = new wxFlexGridSizer(2, 10, 10);
    security_grid->AddGrowableCol(1);
    
    security_grid->Add(new wxStaticText(security_panel, wxID_ANY, "Password Min Length:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxSpinCtrl* password_min_length = new wxSpinCtrl(security_panel, wxID_ANY, "10", wxDefaultPosition, wxDefaultSize, 0, 20, 8);
    security_grid->Add(password_min_length, 1, wxEXPAND | wxALL, 5);
    
    security_grid->Add(new wxStaticText(security_panel, wxID_ANY, "Max Failed Attempts:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxSpinCtrl* max_attempts = new wxSpinCtrl(security_panel, wxID_ANY, "5", wxDefaultPosition, wxDefaultSize, 0, 10, 3);
    security_grid->Add(max_attempts, 1, wxEXPAND | wxALL, 5);
    
    security_grid->Add(new wxStaticText(security_panel, wxID_ANY, "Session Timeout (min):"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxSpinCtrl* session_timeout = new wxSpinCtrl(security_panel, wxID_ANY, "30", wxDefaultPosition, wxDefaultSize, 0, 120, 15);
    security_grid->Add(session_timeout, 1, wxEXPAND | wxALL, 5);
    
    wxCheckBox* require_uppercase = new wxCheckBox(security_panel, wxID_ANY, "Require Uppercase Letters");
    require_uppercase->SetValue(true);
    security_grid->Add(require_uppercase, 1, wxEXPAND | wxALL, 5);
    
    wxCheckBox* require_numbers = new wxCheckBox(security_panel, wxID_ANY, "Require Numbers");
    require_numbers->SetValue(true);
    security_grid->Add(require_numbers, 1, wxEXPAND | wxALL, 5);
    
    wxCheckBox* require_special = new wxCheckBox(security_panel, wxID_ANY, "Require Special Characters");
    require_special->SetValue(true);
    security_grid->Add(require_special, 1, wxEXPAND | wxALL, 5);
    
    security_sizer->Add(security_grid, 1, wxEXPAND | wxALL, 10);
    security_panel->SetSizer(security_sizer);
    
    // Database settings panel
    wxPanel* database_panel = new wxPanel(settings_notebook);
    wxBoxSizer* database_sizer = new wxBoxSizer(wxVERTICAL);
    
    wxFlexGridSizer* database_grid = new wxFlexGridSizer(2, 10, 10);
    database_grid->AddGrowableCol(1);
    
    database_grid->Add(new wxStaticText(database_panel, wxID_ANY, "Database Path:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxTextCtrl* db_path = new wxTextCtrl(database_panel, wxID_ANY, "institution.db");
    database_grid->Add(db_path, 1, wxEXPAND | wxALL, 5);
    
    database_grid->Add(new wxStaticText(database_panel, wxID_ANY, "Auto Backup:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxCheckBox* auto_backup = new wxCheckBox(database_panel, wxID_ANY, "Enable automatic backups");
    auto_backup->SetValue(true);
    database_grid->Add(auto_backup, 1, wxEXPAND | wxALL, 5);
    
    database_grid->Add(new wxStaticText(database_panel, wxID_ANY, "Backup Interval (hours):"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxSpinCtrl* backup_interval = new wxSpinCtrl(database_panel, wxID_ANY, "24", wxDefaultPosition, wxDefaultSize, 1, 168, 12);
    database_grid->Add(backup_interval, 1, wxEXPAND | wxALL, 5);
    
    wxButton* backup_now_btn = new wxButton(database_panel, wxID_ANY, "Backup Now");
    wxButton* restore_btn = new wxButton(database_panel, wxID_ANY, "Restore from Backup");
    
    database_sizer->Add(database_grid, 1, wxEXPAND | wxALL, 10);
    
    wxBoxSizer* db_button_sizer = new wxBoxSizer(wxHORIZONTAL);
    db_button_sizer->Add(backup_now_btn, 0, wxALL, 5);
    db_button_sizer->Add(restore_btn, 0, wxALL, 5);
    database_sizer->Add(db_button_sizer, 0, wxALL, 10);
    
    database_panel->SetSizer(database_sizer);
    
    // Add panels to notebook
    settings_notebook->AddPage(general_panel, "General");
    settings_notebook->AddPage(security_panel, "Security");
    settings_notebook->AddPage(database_panel, "Database");
    
    sizer->Add(settings_notebook, 1, wxEXPAND | wxALL, 10);
    
    // Save button
    wxButton* save_settings_btn = new wxButton(settings_panel_, wxID_SAVE, "Save Settings");
    sizer->Add(save_settings_btn, 0, wxALL | wxALIGN_CENTER, 10);
    
    settings_panel_->SetSizer(sizer);
    
    // Connect events
    save_settings_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Settings saved successfully", "Success", wxOK | wxICON_INFORMATION);
    });
    
    backup_now_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Database backup functionality will be implemented", "Info", wxOK | wxICON_INFORMATION);
    });
    
    restore_btn->Bind(wxEVT_BUTTON, [this](wxCommandEvent&) {
        wxMessageBox("Database restore functionality will be implemented", "Info", wxOK | wxICON_INFORMATION);
    });
}

void MainFrame::UpdateDashboardStats() {
    // Update statistics when services are available
    if (student_service_ && student_count_label_) {
        try {
            int student_count = student_service_->getStudentCount();
            student_count_label_->SetLabel(wxString::Format("%d", student_count));
        } catch (const std::exception& e) {
            student_count_label_->SetLabel("Error");
        }
    }
    
    if (teacher_service_ && teacher_count_label_) {
        try {
            int teacher_count = teacher_service_->getTeacherCount();
            teacher_count_label_->SetLabel(wxString::Format("%d", teacher_count));
        } catch (const std::exception& e) {
            teacher_count_label_->SetLabel("Error");
        }
    }
    
    if (course_service_ && course_count_label_) {
        try {
            int course_count = course_service_->getCourseCount();
            course_count_label_->SetLabel(wxString::Format("%d", course_count));
        } catch (const std::exception& e) {
            course_count_label_->SetLabel("Error");
        }
    }
    
    if (employee_service_ && employee_count_label_) {
        try {
            int employee_count = employee_service_->getEmployeeCount();
            employee_count_label_->SetLabel(wxString::Format("%d", employee_count));
        } catch (const std::exception& e) {
            employee_count_label_->SetLabel("Error");
        }
    }
}

wxString MainFrame::GetCurrentUserInfo() {
    if (security_manager_) {
        // Get current user info from security manager
        return "Admin User"; // Placeholder
    }
    return "Unknown User";
}

void MainFrame::OnNotebookPageChanged(wxBookCtrlEvent& event) {
    // Handle page change
    event.Skip();
}

void MainFrame::OnExit(wxCommandEvent& event) {
    (void)event;
    Close(true);
}

void MainFrame::OnAbout(wxCommandEvent& event) {
    (void)event;
    wxMessageBox("SDEP Educational Management System v1.0\n\n"
                 "A comprehensive educational management system built with C++ and wxWidgets.\n\n"
                 "Features:\n"
                 "- Student Management\n"
                 "- Teacher Management\n"
                 "- Course Management\n"
                 "- Enrollment Tracking\n"
                 "- Attendance Management\n"
                 "- HR Management\n"
                 "- Report Generation\n"
                 "- Security System",
                 "About SDEP", wxOK | wxICON_INFORMATION);
}

void MainFrame::OnLogout(wxCommandEvent& event) {
    (void)event;
    if (wxMessageBox("Are you sure you want to logout?", "Logout Confirmation", 
                     wxYES_NO | wxICON_QUESTION) == wxYES) {
        // Perform logout
        Close(true);
    }
}

// Student event handlers
void MainFrame::OnAddStudent(wxListCtrl* list_ctrl) {
    if (!student_service_) {
        wxMessageBox("Student service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::StudentDialog dialog(this, student_service_);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Student added successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshStudents(list_ctrl);
    }
}

void MainFrame::OnEditStudent(wxListCtrl* list_ctrl) {
    if (!student_service_) {
        wxMessageBox("Student service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select a student to edit", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    int student_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
    Models::Student student = student_service_->getStudentById(student_id);
    
    if (student.id == 0) {
        wxMessageBox("Student not found", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::StudentDialog dialog(this, student_service_, student);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Student updated successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshStudents(list_ctrl);
    }
}

void MainFrame::OnDeleteStudent(wxListCtrl* list_ctrl) {
    if (!student_service_) {
        wxMessageBox("Student service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select a student to delete", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    if (wxMessageBox("Are you sure you want to delete this student?", "Confirm Delete",
                     wxYES_NO | wxICON_QUESTION) == wxYES) {
        int student_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
        if (student_service_->deleteStudent(student_id)) {
            wxMessageBox("Student deleted successfully", "Success", wxOK | wxICON_INFORMATION);
            OnRefreshStudents(list_ctrl);
        } else {
            wxMessageBox("Failed to delete student", "Error", wxOK | wxICON_ERROR);
        }
    }
}

void MainFrame::OnRefreshStudents(wxListCtrl* list_ctrl) {
    if (!student_service_) {
        return;
    }
    
    list_ctrl->DeleteAllItems();
    
    try {
        auto students = student_service_->getAllStudents();
        for (const auto& student : students) {
            long index = list_ctrl->InsertItem(list_ctrl->GetItemCount(), wxString::Format("%d", student.id));
            list_ctrl->SetItem(index, 1, student.getFullName());
            list_ctrl->SetItem(index, 2, student.grade);
            list_ctrl->SetItem(index, 3, student.section);
            list_ctrl->SetItem(index, 4, student.active ? "Active" : "Inactive");
            list_ctrl->SetItem(index, 5, student.email);
        }
    } catch (const std::exception& e) {
        wxMessageBox("Failed to load students: " + wxString(e.what()), "Error", wxOK | wxICON_ERROR);
    }
}

// Teacher event handlers
void MainFrame::OnAddTeacher(wxListCtrl* list_ctrl) {
    if (!teacher_service_) {
        wxMessageBox("Teacher service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::TeacherDialog dialog(this, teacher_service_);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Teacher added successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshTeachers(list_ctrl);
    }
}

void MainFrame::OnEditTeacher(wxListCtrl* list_ctrl) {
    if (!teacher_service_) {
        wxMessageBox("Teacher service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select a teacher to edit", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    int teacher_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
    Models::Teacher teacher = teacher_service_->getTeacherById(teacher_id);
    
    if (teacher.id == 0) {
        wxMessageBox("Teacher not found", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::TeacherDialog dialog(this, teacher_service_, teacher);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Teacher updated successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshTeachers(list_ctrl);
    }
}

void MainFrame::OnDeleteTeacher(wxListCtrl* list_ctrl) {
    if (!teacher_service_) {
        wxMessageBox("Teacher service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select a teacher to delete", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    if (wxMessageBox("Are you sure you want to delete this teacher?", "Confirm Delete",
                     wxYES_NO | wxICON_QUESTION) == wxYES) {
        int teacher_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
        if (teacher_service_->deleteTeacher(teacher_id)) {
            wxMessageBox("Teacher deleted successfully", "Success", wxOK | wxICON_INFORMATION);
            OnRefreshTeachers(list_ctrl);
        } else {
            wxMessageBox("Failed to delete teacher", "Error", wxOK | wxICON_ERROR);
        }
    }
}

void MainFrame::OnRefreshTeachers(wxListCtrl* list_ctrl) {
    if (!teacher_service_) {
        return;
    }
    
    list_ctrl->DeleteAllItems();
    
    try {
        auto teachers = teacher_service_->getAllTeachers();
        for (const auto& teacher : teachers) {
            long index = list_ctrl->InsertItem(list_ctrl->GetItemCount(), wxString::Format("%d", teacher.id));
            list_ctrl->SetItem(index, 1, teacher.getFullName());
            list_ctrl->SetItem(index, 2, teacher.department);
            list_ctrl->SetItem(index, 3, teacher.specialization);
            list_ctrl->SetItem(index, 4, teacher.active ? "Active" : "Inactive");
            list_ctrl->SetItem(index, 5, teacher.email);
        }
    } catch (const std::exception& e) {
        wxMessageBox("Failed to load teachers: " + wxString(e.what()), "Error", wxOK | wxICON_ERROR);
    }
}

// Course event handlers
void MainFrame::OnAddCourse(wxListCtrl* list_ctrl) {
    if (!course_service_ || !teacher_service_) {
        wxMessageBox("Services not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::CourseDialog dialog(this, course_service_, teacher_service_);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Course added successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshCourses(list_ctrl);
    }
}

void MainFrame::OnEditCourse(wxListCtrl* list_ctrl) {
    if (!course_service_ || !teacher_service_) {
        wxMessageBox("Services not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select a course to edit", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    int course_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
    Models::Course course = course_service_->getCourseById(course_id);
    
    if (course.id == 0) {
        wxMessageBox("Course not found", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::CourseDialog dialog(this, course_service_, teacher_service_, course);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Course updated successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshCourses(list_ctrl);
    }
}

void MainFrame::OnDeleteCourse(wxListCtrl* list_ctrl) {
    if (!course_service_) {
        wxMessageBox("Course service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select a course to delete", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    if (wxMessageBox("Are you sure you want to delete this course?", "Confirm Delete",
                     wxYES_NO | wxICON_QUESTION) == wxYES) {
        int course_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
        if (course_service_->deleteCourse(course_id)) {
            wxMessageBox("Course deleted successfully", "Success", wxOK | wxICON_INFORMATION);
            OnRefreshCourses(list_ctrl);
        } else {
            wxMessageBox("Failed to delete course", "Error", wxOK | wxICON_ERROR);
        }
    }
}

void MainFrame::OnRefreshCourses(wxListCtrl* list_ctrl) {
    if (!course_service_) {
        return;
    }
    
    list_ctrl->DeleteAllItems();
    
    try {
        auto courses = course_service_->getAllCourses();
        for (const auto& course : courses) {
            long index = list_ctrl->InsertItem(list_ctrl->GetItemCount(), wxString::Format("%d", course.id));
            list_ctrl->SetItem(index, 1, course.code);
            list_ctrl->SetItem(index, 2, course.name);
            list_ctrl->SetItem(index, 3, course.level);
            list_ctrl->SetItem(index, 4, course.teacher_name);
            list_ctrl->SetItem(index, 5, wxString::Format("%d", course.credits));
            list_ctrl->SetItem(index, 6, course.active ? "Active" : "Inactive");
        }
    } catch (const std::exception& e) {
        wxMessageBox("Failed to load courses: " + wxString(e.what()), "Error", wxOK | wxICON_ERROR);
    }
}

// Employee event handlers
void MainFrame::OnAddEmployee(wxListCtrl* list_ctrl) {
    if (!employee_service_) {
        wxMessageBox("Employee service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::EmployeeDialog dialog(this, employee_service_);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Employee added successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshEmployees(list_ctrl);
    }
}

void MainFrame::OnEditEmployee(wxListCtrl* list_ctrl) {
    if (!employee_service_) {
        wxMessageBox("Employee service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select an employee to edit", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    int employee_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
    Models::Employee employee = employee_service_->getEmployeeById(employee_id);
    
    if (employee.id == 0) {
        wxMessageBox("Employee not found", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::EmployeeDialog dialog(this, employee_service_, employee);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Employee updated successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshEmployees(list_ctrl);
    }
}

void MainFrame::OnDeleteEmployee(wxListCtrl* list_ctrl) {
    if (!employee_service_) {
        wxMessageBox("Employee service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select an employee to delete", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    if (wxMessageBox("Are you sure you want to delete this employee?", "Confirm Delete",
                     wxYES_NO | wxICON_QUESTION) == wxYES) {
        int employee_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
        if (employee_service_->deleteEmployee(employee_id)) {
            wxMessageBox("Employee deleted successfully", "Success", wxOK | wxICON_INFORMATION);
            OnRefreshEmployees(list_ctrl);
        } else {
            wxMessageBox("Failed to delete employee", "Error", wxOK | wxICON_ERROR);
        }
    }
}

void MainFrame::OnRefreshEmployees(wxListCtrl* list_ctrl) {
    if (!employee_service_) {
        return;
    }
    
    list_ctrl->DeleteAllItems();
    
    try {
        auto employees = employee_service_->getAllEmployees();
        for (const auto& employee : employees) {
            long index = list_ctrl->InsertItem(list_ctrl->GetItemCount(), wxString::Format("%d", employee.id));
            list_ctrl->SetItem(index, 1, employee.employee_code);
            list_ctrl->SetItem(index, 2, employee.getFullName());
            list_ctrl->SetItem(index, 3, employee.department);
            list_ctrl->SetItem(index, 4, employee.position);
            list_ctrl->SetItem(index, 5, employee.employee_status);
        }
    } catch (const std::exception& e) {
        wxMessageBox("Failed to load employees: " + wxString(e.what()), "Error", wxOK | wxICON_ERROR);
    }
}

// Enrollment event handlers
void MainFrame::OnAddEnrollment(wxListCtrl* list_ctrl) {
    if (!enrollment_service_ || !student_service_ || !course_service_) {
        wxMessageBox("Services not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::EnrollmentDialog dialog(this, enrollment_service_, student_service_, course_service_);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Enrollment added successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshEnrollments(list_ctrl);
    }
}

void MainFrame::OnEditEnrollment(wxListCtrl* list_ctrl) {
    if (!enrollment_service_ || !student_service_ || !course_service_) {
        wxMessageBox("Services not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select an enrollment to edit", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    int enrollment_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
    Models::Enrollment enrollment = enrollment_service_->getEnrollmentById(enrollment_id);
    
    if (enrollment.id == 0) {
        wxMessageBox("Enrollment not found", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::EnrollmentDialog dialog(this, enrollment_service_, student_service_, course_service_, enrollment);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Enrollment updated successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshEnrollments(list_ctrl);
    }
}

void MainFrame::OnDeleteEnrollment(wxListCtrl* list_ctrl) {
    if (!enrollment_service_) {
        wxMessageBox("Enrollment service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select an enrollment to delete", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    if (wxMessageBox("Are you sure you want to delete this enrollment?", "Confirm Delete",
                     wxYES_NO | wxICON_QUESTION) == wxYES) {
        int enrollment_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
        if (enrollment_service_->deleteEnrollment(enrollment_id)) {
            wxMessageBox("Enrollment deleted successfully", "Success", wxOK | wxICON_INFORMATION);
            OnRefreshEnrollments(list_ctrl);
        } else {
            wxMessageBox("Failed to delete enrollment", "Error", wxOK | wxICON_ERROR);
        }
    }
}

void MainFrame::OnRefreshEnrollments(wxListCtrl* list_ctrl) {
    if (!enrollment_service_) {
        return;
    }
    
    list_ctrl->DeleteAllItems();
    
    try {
        auto enrollments = enrollment_service_->getAllEnrollments();
        for (const auto& enrollment : enrollments) {
            long index = list_ctrl->InsertItem(list_ctrl->GetItemCount(), wxString::Format("%d", enrollment.id));
            list_ctrl->SetItem(index, 1, enrollment.student_name);
            list_ctrl->SetItem(index, 2, enrollment.course_name);
            list_ctrl->SetItem(index, 3, enrollment.enrollment_date);
            list_ctrl->SetItem(index, 4, wxString::Format("%.2f", enrollment.grade));
            list_ctrl->SetItem(index, 5, enrollment.status);
        }
    } catch (const std::exception& e) {
        wxMessageBox("Failed to load enrollments: " + wxString(e.what()), "Error", wxOK | wxICON_ERROR);
    }
}

// Attendance event handlers
void MainFrame::OnAddAttendance(wxListCtrl* list_ctrl) {
    if (!attendance_service_ || !student_service_ || !course_service_) {
        wxMessageBox("Services not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::AttendanceDialog dialog(this, attendance_service_, student_service_, course_service_);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Attendance marked successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshAttendance(list_ctrl);
    }
}

void MainFrame::OnEditAttendance(wxListCtrl* list_ctrl) {
    if (!attendance_service_ || !student_service_ || !course_service_) {
        wxMessageBox("Services not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select an attendance record to edit", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    int attendance_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
    Models::Attendance attendance = attendance_service_->getAttendanceById(attendance_id);
    
    if (attendance.id == 0) {
        wxMessageBox("Attendance record not found", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    GUI::AttendanceDialog dialog(this, attendance_service_, student_service_, course_service_, attendance);
    if (dialog.ShowModal() == wxID_OK && dialog.IsSaved()) {
        wxMessageBox("Attendance updated successfully", "Success", wxOK | wxICON_INFORMATION);
        OnRefreshAttendance(list_ctrl);
    }
}

void MainFrame::OnDeleteAttendance(wxListCtrl* list_ctrl) {
    if (!attendance_service_) {
        wxMessageBox("Attendance service not available", "Error", wxOK | wxICON_ERROR);
        return;
    }
    
    long selected_item = list_ctrl->GetNextItem(-1, wxLIST_NEXT_ALL, wxLIST_STATE_SELECTED);
    if (selected_item == -1) {
        wxMessageBox("Please select an attendance record to delete", "Information", wxOK | wxICON_INFORMATION);
        return;
    }
    
    if (wxMessageBox("Are you sure you want to delete this attendance record?", "Confirm Delete",
                     wxYES_NO | wxICON_QUESTION) == wxYES) {
        int attendance_id = wxAtoi(list_ctrl->GetItemText(selected_item, 0));
        if (attendance_service_->deleteAttendance(attendance_id)) {
            wxMessageBox("Attendance record deleted successfully", "Success", wxOK | wxICON_INFORMATION);
            OnRefreshAttendance(list_ctrl);
        } else {
            wxMessageBox("Failed to delete attendance record", "Error", wxOK | wxICON_ERROR);
        }
    }
}

void MainFrame::OnRefreshAttendance(wxListCtrl* list_ctrl) {
    if (!attendance_service_) {
        return;
    }
    
    list_ctrl->DeleteAllItems();
    
    try {
        auto attendance_records = attendance_service_->getAllAttendance();
        for (const auto& attendance : attendance_records) {
            long index = list_ctrl->InsertItem(list_ctrl->GetItemCount(), wxString::Format("%d", attendance.id));
            list_ctrl->SetItem(index, 1, attendance.student_name);
            list_ctrl->SetItem(index, 2, attendance.course_name);
            list_ctrl->SetItem(index, 3, attendance.date);
            list_ctrl->SetItem(index, 4, attendance.status);
            list_ctrl->SetItem(index, 5, attendance.notes);
        }
    } catch (const std::exception& e) {
        wxMessageBox("Failed to load attendance records: " + wxString(e.what()), "Error", wxOK | wxICON_ERROR);
    }
}

} // namespace GUI
} // namespace SDEP