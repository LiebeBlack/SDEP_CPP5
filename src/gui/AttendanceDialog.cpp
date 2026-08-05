#include "gui/AttendanceDialog.h"
#include <wx/datectrl.h>
#include <wx/msgdlg.h>

namespace SDEP {
namespace GUI {

wxBEGIN_EVENT_TABLE(AttendanceDialog, wxDialog)
    EVT_BUTTON(ID_ATTENDANCE_SAVE, AttendanceDialog::OnSave)
    EVT_BUTTON(ID_ATTENDANCE_CANCEL, AttendanceDialog::OnCancel)
    EVT_COMBOBOX(ID_STUDENT_COMBO, AttendanceDialog::OnStudentChanged)
    EVT_COMBOBOX(ID_COURSE_COMBO, AttendanceDialog::OnCourseChanged)
wxEND_EVENT_TABLE()

AttendanceDialog::AttendanceDialog(wxWindow* parent, Services::AttendanceService* attendance_service,
                                  Services::StudentService* student_service,
                                  Services::CourseService* course_service,
                                  const Models::Attendance& attendance)
    : wxDialog(parent, wxID_ANY, attendance.id > 0 ? "Edit Attendance" : "Mark Attendance",
              wxDefaultPosition, wxSize(500, 300)),
      attendance_service_(attendance_service),
      student_service_(student_service),
      course_service_(course_service),
      attendance_(attendance),
      is_edit_mode_(attendance.id > 0) {
    
    SetMinSize(wxSize(400, 250));
    
    wxPanel* panel = new wxPanel(this);
    wxBoxSizer* main_sizer = new wxBoxSizer(wxVERTICAL);
    
    wxString title = is_edit_mode_ ? "Edit Attendance Record" : "Mark Student Attendance";
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
    
    // Date
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Date*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    date_ctrl_ = new wxDatePickerCtrl(panel, ID_DATE);
    date_ctrl_->SetValue(wxDateTime::Now());
    grid_sizer->Add(date_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Status
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Status*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxArrayString statuses;
    statuses.Add("Present");
    statuses.Add("Absent");
    statuses.Add("Late");
    statuses.Add("Excused");
    statuses.Add("Sick");
    status_combo_ = new wxComboBox(panel, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, statuses, wxCB_READONLY);
    status_combo_->SetSelection(0);
    grid_sizer->Add(status_combo_, 1, wxEXPAND | wxALL, 5);
    
    // Notes
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Notes:"), 0, wxALIGN_RIGHT | wxALL, 5);
    notes_ctrl_ = new wxTextCtrl(panel, wxID_ANY, "", wxDefaultPosition, wxSize(-1, 60), wxTE_MULTILINE);
    grid_sizer->Add(notes_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    main_sizer->Add(grid_sizer, 1, wxEXPAND | wxALL, 10);
    
    // Status text
    status_text_ = new wxStaticText(panel, wxID_ANY, "");
    status_text_->SetForegroundColour(wxColour(255, 0, 0));
    main_sizer->Add(status_text_, 0, wxALL | wxALIGN_CENTER, 5);
    
    // Button panel
    wxPanel* button_panel = new wxPanel(panel);
    wxBoxSizer* button_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* save_button = new wxButton(button_panel, ID_ATTENDANCE_SAVE, "Save");
    wxButton* cancel_button = new wxButton(button_panel, ID_ATTENDANCE_CANCEL, "Cancel");
    
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

void AttendanceDialog::LoadStudents() {
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

void AttendanceDialog::LoadCourses() {
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

void AttendanceDialog::PopulateFields() {
    // Select student
    if (attendance_.student_id > 0) {
        for (size_t i = 0; i < student_combo_->GetCount(); ++i) {
            wxVariant variant = student_combo_->GetClientData(i);
            if (variant.GetInteger() == attendance_.student_id) {
                student_combo_->SetSelection(i);
                break;
            }
        }
    }
    
    // Select course
    if (attendance_.course_id > 0) {
        for (size_t i = 0; i < course_combo_->GetCount(); ++i) {
            wxVariant variant = course_combo_->GetClientData(i);
            if (variant.GetInteger() == attendance_.course_id) {
                course_combo_->SetSelection(i);
                break;
            }
        }
    }
    
    // Set date
    if (!attendance_.date.empty()) {
        // Parse and set date
    }
    
    // Set status
    status_combo_->SetValue(attendance_.status);
    
    // Set notes
    notes_ctrl_->SetValue(attendance_.notes);
}

bool AttendanceDialog::ValidateInputs() {
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
    
    return true;
}

bool AttendanceDialog::SaveAttendance() {
    try {
        // Get selected student
        int student_selection = student_combo_->GetSelection();
        wxVariant student_variant = student_combo_->GetClientData(student_selection);
        attendance_.student_id = student_variant.GetInteger();
        
        // Get selected course
        int course_selection = course_combo_->GetSelection();
        wxVariant course_variant = course_combo_->GetClientData(course_selection);
        attendance_.course_id = course_variant.GetInteger();
        
        // Get date
        wxDateTime date = date_ctrl_->GetValue();
        attendance_.date = date.FormatISODate().ToStdString();
        
        // Get status
        attendance_.status = status_combo_->GetValue().ToStdString();
        
        // Get notes
        attendance_.notes = notes_ctrl_->GetValue().ToStdString();
        
        // Get student and course names
        auto student = student_service_->getStudentById(attendance_.student_id);
        attendance_.student_name = student.getFullName();
        
        auto course = course_service_->getCourseById(attendance_.course_id);
        attendance_.course_name = course.name;
        
        if (!attendance_.validate()) {
            status_text_->SetLabel("Validation failed");
            return false;
        }
        
        if (is_edit_mode_) {
            if (attendance_service_->updateAttendance(attendance_)) {
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to update attendance");
                return false;
            }
        } else {
            int new_id = attendance_service_->createAttendance(attendance_);
            if (new_id > 0) {
                attendance_.id = new_id;
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to create attendance");
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

void AttendanceDialog::OnSave(wxCommandEvent& event) {
    if (!ValidateInputs()) {
        return;
    }
    
    if (SaveAttendance()) {
        EndModal(wxID_OK);
    }
}

void AttendanceDialog::OnCancel(wxCommandEvent& event) {
    EndModal(wxID_CANCEL);
}

void AttendanceDialog::OnStudentChanged(wxCommandEvent& event) {
    // Handle student selection change if needed
    event.Skip();
}

void AttendanceDialog::OnCourseChanged(wxCommandEvent& event) {
    // Handle course selection change if needed
    event.Skip();
}

} // namespace GUI
} // namespace SDEP