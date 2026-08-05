#include "gui/EnrollmentDialog.h"
#include <wx/datectrl.h>
#include <wx/msgdlg.h>

namespace SDEP {
namespace GUI {

wxBEGIN_EVENT_TABLE(EnrollmentDialog, wxDialog)
    EVT_BUTTON(ID_ENROLLMENT_SAVE, EnrollmentDialog::OnSave)
    EVT_BUTTON(ID_ENROLLMENT_CANCEL, EnrollmentDialog::OnCancel)
    EVT_COMBOBOX(ID_STUDENT_COMBO, EnrollmentDialog::OnStudentChanged)
    EVT_COMBOBOX(ID_COURSE_COMBO, EnrollmentDialog::OnCourseChanged)
wxEND_EVENT_TABLE()

EnrollmentDialog::EnrollmentDialog(wxWindow* parent, Services::EnrollmentService* enrollment_service,
                                 Services::StudentService* student_service,
                                 Services::CourseService* course_service,
                                 const Models::Enrollment& enrollment)
    : wxDialog(parent, wxID_ANY, enrollment.id > 0 ? "Edit Enrollment" : "New Enrollment",
              wxDefaultPosition, wxSize(500, 350)),
      enrollment_service_(enrollment_service),
      student_service_(student_service),
      course_service_(course_service),
      enrollment_(enrollment),
      is_edit_mode_(enrollment.id > 0) {
    
    SetMinSize(wxSize(400, 300));
    
    wxPanel* panel = new wxPanel(this);
    wxBoxSizer* main_sizer = new wxBoxSizer(wxVERTICAL);
    
    wxString title = is_edit_mode_ ? "Edit Enrollment" : "New Student Enrollment";
    wxStaticText* title_text = new wxStaticText(panel, wxID_ANY, title);
    title_text->SetFont(title_text->GetFont().Larger().Bold());
    main_sizer->Add(title_text, 0, wxALL, 10);
    
    wxFlexGridSizer* grid_sizer = new wxFlexGridSizer(2, 10, 10);
    grid_sizer->AddGrowableCol(1);
    
    // Student
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Student*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    student_combo_ = new wxComboBox(panel, ID_STUDENT_COMBO);
    LoadStudents();
    grid_sizer->Add(student_combo_, 1, wxEXPAND | wxALL, 5);
    
    // Course
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Course*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    course_combo_ = new wxComboBox(panel, ID_COURSE_COMBO);
    LoadCourses();
    grid_sizer->Add(course_combo_, 1, wxEXPAND | wxALL, 5);
    
    // Enrollment Date
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Enrollment Date:"), 0, wxALIGN_RIGHT | wxALL, 5);
    enrollment_date_ctrl_ = new wxDatePickerCtrl(panel, ID_ENROLLMENT_DATE);
    enrollment_date_ctrl_->SetValue(wxDateTime::Now());
    grid_sizer->Add(enrollment_date_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Grade
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Grade:"), 0, wxALIGN_RIGHT | wxALL, 5);
    grade_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grade_ctrl_->SetValidator(wxFloatingPointValidator<double>(2, 0.0, 100.0));
    grid_sizer->Add(grade_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Status
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Status:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxArrayString statuses;
    statuses.Add("Active");
    statuses.Add("Inactive");
    statuses.Add("Completed");
    statuses.Add("Dropped");
    statuses.Add("Suspended");
    status_combo_ = new wxComboBox(panel, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, statuses, wxCB_READONLY);
    status_combo_->SetSelection(0);
    grid_sizer->Add(status_combo_, 1, wxEXPAND | wxALL, 5);
    
    main_sizer->Add(grid_sizer, 1, wxEXPAND | wxALL, 10);
    
    // Status text
    status_text_ = new wxStaticText(panel, wxID_ANY, "");
    status_text_->SetForegroundColour(wxColour(255, 0, 0));
    main_sizer->Add(status_text_, 0, wxALL | wxALIGN_CENTER, 5);
    
    // Button panel
    wxPanel* button_panel = new wxPanel(panel);
    wxBoxSizer* button_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* save_button = new wxButton(button_panel, ID_ENROLLMENT_SAVE, "Save");
    wxButton* cancel_button = new wxButton(button_panel, ID_ENROLLMENT_CANCEL, "Cancel");
    
    button_sizer->Add(save_button, 0, wxALL, 5);
    button_sizer->Add(cancel_button, 0, wxALL, 5);
    
    button_panel->SetSizer(button_sizer);
    main_sizer->Add(button_panel, 0, wxALL | wxALIGN_CENTER, 10);
    
    panel->SetSizer(main_sizer);
    main_sizer->Fit(panel);
    
    if (is_edit_mode_) {
        PopulateFields();
    }
    
    Centre();
}

void EnrollmentDialog::LoadStudents() {
    if (!student_service_) {
        return;
    }
    
    try {
        auto students = student_service_->getActiveStudents();
        student_combo_->Clear();
        
        for (const auto& student : students) {
            wxString student_name = wxString::Format("%s %s (%s)", 
                student.first_name, student.last_name, student.grade);
            student_combo_->Append(student_name, wxVariant(student.id));
        }
        
        if (!student_combo_->IsEmpty()) {
            student_combo_->SetSelection(0);
        }
        
    } catch (const std::exception& e) {
        wxMessageBox("Failed to load students: " + wxString(e.what()), "Error", wxOK | wxICON_ERROR);
    }
}

void EnrollmentDialog::LoadCourses() {
    if (!course_service_) {
        return;
    }
    
    try {
        auto courses = course_service_->getActiveCourses();
        course_combo_->Clear();
        
        for (const auto& course : courses) {
            wxString course_name = wxString::Format("%s - %s", course.code, course.name);
            course_combo_->Append(course_name, wxVariant(course.id));
        }
        
        if (!course_combo_->IsEmpty()) {
            course_combo_->SetSelection(0);
        }
        
    } catch (const std::exception& e) {
        wxMessageBox("Failed to load courses: " + wxString(e.what()), "Error", wxOK | wxICON_ERROR);
    }
}

void EnrollmentDialog::PopulateFields() {
    // Select student
    if (enrollment_.student_id > 0) {
        for (size_t i = 0; i < student_combo_->GetCount(); ++i) {
            wxVariant variant = student_combo_->GetClientData(i);
            if (variant.GetInteger() == enrollment_.student_id) {
                student_combo_->SetSelection(i);
                break;
            }
        }
    }
    
    // Select course
    if (enrollment_.course_id > 0) {
        for (size_t i = 0; i < course_combo_->GetCount(); ++i) {
            wxVariant variant = course_combo_->GetClientData(i);
            if (variant.GetInteger() == enrollment_.course_id) {
                course_combo_->SetSelection(i);
                break;
            }
        }
    }
    
    // Set enrollment date
    if (!enrollment_.enrollment_date.empty()) {
        // Parse and set date
    }
    
    // Set grade
    if (enrollment_.grade > 0) {
        grade_ctrl_->SetValue(wxString::Format("%.2f", enrollment_.grade));
    }
    
    // Set status
    status_combo_->SetValue(enrollment_.status);
}

bool EnrollmentDialog::ValidateInputs() {
    int student_selection = student_combo_->GetSelection();
    if (student_selection == wxNOT_FOUND) {
        status_text_->SetLabel("Please select a student");
        student_combo_->SetFocus();
        return false;
    }
    
    int course_selection = course_combo_->GetSelection();
    if (course_selection == wxNOT_FOUND) {
        status_text_->SetLabel("Please select a course");
        course_combo_->SetFocus();
        return false;
    }
    
    wxString grade_str = grade_ctrl_->GetValue();
    if (!grade_str.IsEmpty()) {
        double grade;
        if (!grade_str.ToDouble(&grade) || grade < 0 || grade > 100) {
            status_text_->SetLabel("Grade must be between 0 and 100");
            grade_ctrl_->SetFocus();
            return false;
        }
    }
    
    return true;
}

bool EnrollmentDialog::SaveEnrollment() {
    try {
        // Get selected student
        int student_selection = student_combo_->GetSelection();
        wxVariant student_variant = student_combo_->GetClientData(student_selection);
        enrollment_.student_id = student_variant.GetInteger();
        
        // Get selected course
        int course_selection = course_combo_->GetSelection();
        wxVariant course_variant = course_combo_->GetClientData(course_selection);
        enrollment_.course_id = course_variant.GetInteger();
        
        // Get enrollment date
        wxDateTime enrollment_date = enrollment_date_ctrl_->GetValue();
        enrollment_.enrollment_date = enrollment_date.FormatISODate().ToStdString();
        
        // Get grade
        wxString grade_str = grade_ctrl_->GetValue();
        if (!grade_str.IsEmpty()) {
            grade_str.ToDouble(&enrollment_.grade);
        }
        
        // Get status
        enrollment_.status = status_combo_->GetValue().ToStdString();
        
        // Get student and course names
        auto student = student_service_->getStudentById(enrollment_.student_id);
        enrollment_.student_name = student.getFullName();
        
        auto course = course_service_->getCourseById(enrollment_.course_id);
        enrollment_.course_name = course.name;
        
        if (!enrollment_.validate()) {
            status_text_->SetLabel("Validation failed");
            return false;
        }
        
        if (is_edit_mode_) {
            if (enrollment_service_->updateEnrollment(enrollment_)) {
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to update enrollment");
                return false;
            }
        } else {
            int new_id = enrollment_service_->createEnrollment(enrollment_);
            if (new_id > 0) {
                enrollment_.id = new_id;
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to create enrollment");
                return false;
            }
        }
        
    } catch (const Services::ValidationError& e) {
        status_text_->SetLabel(wxString(e.what()));
        return false;
    } catch (const std::exception& e) {
        status_text_->SetLabel(wxString("Error: ") + e.what());
        return false;
    }
}

void EnrollmentDialog::OnSave(wxCommandEvent& event) {
    if (!ValidateInputs()) {
        return;
    }
    
    if (SaveEnrollment()) {
        EndModal(wxID_OK);
    }
}

void EnrollmentDialog::OnCancel(wxCommandEvent& event) {
    EndModal(wxID_CANCEL);
}

void EnrollmentDialog::OnStudentChanged(wxCommandEvent& event) {
    // Handle student selection change if needed
    event.Skip();
}

void EnrollmentDialog::OnCourseChanged(wxCommandEvent& event) {
    // Handle course selection change if needed
    event.Skip();
}

} // namespace GUI
} // namespace SDEP