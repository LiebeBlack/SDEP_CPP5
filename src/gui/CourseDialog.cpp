#include "gui/CourseDialog.h"
#include <wx/msgdlg.h>

namespace SDEP {
namespace GUI {

wxBEGIN_EVENT_TABLE(CourseDialog, wxDialog)
    EVT_BUTTON(ID_COURSE_SAVE, CourseDialog::OnSave)
    EVT_BUTTON(ID_COURSE_CANCEL, CourseDialog::OnCancel)
    EVT_COMBOBOX(ID_TEACHER_COMBO, CourseDialog::OnTeacherChanged)
wxEND_EVENT_TABLE()

CourseDialog::CourseDialog(wxWindow* parent, Services::CourseService* course_service,
                          Services::TeacherService* teacher_service,
                          const Models::Course& course)
    : wxDialog(parent, wxID_ANY, course.id > 0 ? "Edit Course" : "Add Course",
              wxDefaultPosition, wxSize(600, 500)),
      course_service_(course_service),
      teacher_service_(teacher_service),
      course_(course),
      is_edit_mode_(course.id > 0) {
    
    SetMinSize(wxSize(500, 450));
    
    wxPanel* panel = new wxPanel(this);
    wxBoxSizer* main_sizer = new wxBoxSizer(wxVERTICAL);
    
    wxString title = is_edit_mode_ ? "Edit Course" : "Add New Course";
    wxStaticText* title_text = new wxStaticText(panel, wxID_ANY, title);
    title_text->SetFont(title_text->GetFont().Larger().Bold());
    main_sizer->Add(title_text, 0, wxALL, 10);
    
    wxFlexGridSizer* grid_sizer = new wxFlexGridSizer(2, 10, 10);
    grid_sizer->AddGrowableCol(1);
    
    // Course Name
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Course Name*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    name_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(name_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Course Code
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Course Code*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    code_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(code_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Level
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Level:"), 0, wxALIGN_RIGHT | wxALL, 5);
    level_ctrl_ = new wxComboBox(panel, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, wxArrayString(), wxCB_READONLY);
    grid_sizer->Add(level_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Description
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Description:"), 0, wxALIGN_RIGHT | wxALL, 5);
    description_ctrl_ = new wxTextCtrl(panel, wxID_ANY, "", wxDefaultPosition, wxSize(-1, 60), wxTE_MULTILINE);
    grid_sizer->Add(description_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Teacher
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Teacher:"), 0, wxALIGN_RIGHT | wxALL, 5);
    teacher_combo_ = new wxComboBox(panel, ID_TEACHER_COMBO);
    LoadTeachers();
    grid_sizer->Add(teacher_combo_, 1, wxEXPAND | wxALL, 5);
    
    // Credits
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Credits:"), 0, wxALIGN_RIGHT | wxALL, 5);
    credits_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    // Note: wxIntegerValidator is not available in all wxWidgets versions
    // Validation will be done in ValidateInputs() method
    grid_sizer->Add(credits_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Schedule
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Schedule:"), 0, wxALIGN_RIGHT | wxALL, 5);
    schedule_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(schedule_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Classroom
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Classroom:"), 0, wxALIGN_RIGHT | wxALL, 5);
    classroom_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(classroom_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Active
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Active:"), 0, wxALIGN_RIGHT | wxALL, 5);
    active_ctrl_ = new wxCheckBox(panel, wxID_ANY, "Active");
    active_ctrl_->SetValue(true);
    grid_sizer->Add(active_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    main_sizer->Add(grid_sizer, 1, wxEXPAND | wxALL, 10);
    
    // Status text
    status_text_ = new wxStaticText(panel, wxID_ANY, "");
    status_text_->SetForegroundColour(wxColour(255, 0, 0));
    main_sizer->Add(status_text_, 0, wxALL | wxALIGN_CENTER, 5);
    
    // Button panel
    wxPanel* button_panel = new wxPanel(panel);
    wxBoxSizer* button_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* save_button = new wxButton(button_panel, ID_COURSE_SAVE, "Save");
    wxButton* cancel_button = new wxButton(button_panel, ID_COURSE_CANCEL, "Cancel");
    
    button_sizer->Add(save_button, 0, wxALL, 5);
    button_sizer->Add(cancel_button, 0, wxALL, 5);
    
    button_panel->SetSizer(button_sizer);
    main_sizer->Add(button_panel, 0, wxALL | wxALIGN_CENTER, 10);
    
    panel->SetSizer(main_sizer);
    main_sizer->Fit(panel);
    
    // Add level options
    wxArrayString levels;
    levels.Add("Elementary");
    levels.Add("Middle School");
    levels.Add("High School");
    levels.Add("University");
    levels.Add("Professional");
    level_ctrl_->Append(levels);
    
    if (is_edit_mode_) {
        PopulateFields();
    }
    
    Centre();
}

void CourseDialog::LoadTeachers() {
    if (!teacher_service_) {
        return;
    }
    
    try {
        auto teachers = teacher_service_->getAllTeachers();
        teacher_combo_->Clear();
        teacher_combo_->Append("", wxVariant(0)); // No teacher option
        
        for (const auto& teacher : teachers) {
            wxString teacher_name = wxString::Format("%s %s", 
                teacher.first_name, teacher.last_name);
            teacher_combo_->Append(teacher_name, wxVariant(teacher.id));
        }
        
        teacher_combo_->SetSelection(0);
        
    } catch (const std::exception& e) {
        wxMessageBox("Failed to load teachers: " + wxString(e.what()), "Error", wxOK | wxICON_ERROR);
    }
}

void CourseDialog::PopulateFields() {
    name_ctrl_->SetValue(course_.name);
    code_ctrl_->SetValue(course_.code);
    level_ctrl_->SetValue(course_.level);
    description_ctrl_->SetValue(course_.description);
    credits_ctrl_->SetValue(wxString::Format("%d", course_.credits));
    schedule_ctrl_->SetValue(course_.schedule);
    classroom_ctrl_->SetValue(course_.classroom);
    active_ctrl_->SetValue(course_.active);
    
    // Select teacher
    if (course_.teacher_id > 0) {
        for (size_t i = 0; i < teacher_combo_->GetCount(); ++i) {
            wxVariant variant = teacher_combo_->GetClientData(i);
            if (variant.GetInteger() == course_.teacher_id) {
                teacher_combo_->SetSelection(i);
                break;
            }
        }
    }
}

bool CourseDialog::ValidateInputs() {
    if (name_ctrl_->GetValue().Trim().IsEmpty()) {
        status_text_->SetLabel("Course name is required");
        name_ctrl_->SetFocus();
        return false;
    }
    
    if (code_ctrl_->GetValue().Trim().IsEmpty()) {
        status_text_->SetLabel("Course code is required");
        code_ctrl_->SetFocus();
        return false;
    }
    
    wxString credits_str = credits_ctrl_->GetValue();
    if (!credits_str.IsEmpty()) {
        int credits;
        if (!credits_str.ToInt(&credits) || credits < 0 || credits > 10) {
            status_text_->SetLabel("Credits must be between 0 and 10");
            credits_ctrl_->SetFocus();
            return false;
        }
    }
    
    return true;
}

bool CourseDialog::SaveCourse() {
    try {
        course_.name = name_ctrl_->GetValue().ToStdString();
        course_.code = code_ctrl_->GetValue().ToStdString();
        course_.level = level_ctrl_->GetValue().ToStdString();
        course_.description = description_ctrl_->GetValue().ToStdString();
        course_.schedule = schedule_ctrl_->GetValue().ToStdString();
        course_.classroom = classroom_ctrl_->GetValue().ToStdString();
        course_.active = active_ctrl_->GetValue();
        
        wxString credits_str = credits_ctrl_->GetValue();
        if (!credits_str.IsEmpty()) {
            credits_str.ToInt(&course_.credits);
        }
        
        // Get selected teacher
        int selection = teacher_combo_->GetSelection();
        if (selection != wxNOT_FOUND) {
            wxVariant variant = teacher_combo_->GetClientData(selection);
            course_.teacher_id = variant.GetInteger();
            
            if (course_.teacher_id > 0) {
                auto teacher = teacher_service_->getTeacherById(course_.teacher_id);
                course_.teacher_name = teacher.getFullName();
            }
        }
        
        if (!course_.validate()) {
            status_text_->SetLabel("Validation failed");
            return false;
        }
        
        if (is_edit_mode_) {
            if (course_service_->updateCourse(course_)) {
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to update course");
                return false;
            }
        } else {
            int new_id = course_service_->createCourse(course_);
            if (new_id > 0) {
                course_.id = new_id;
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to create course");
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

void CourseDialog::OnSave(wxCommandEvent& /* event */) {
    if (!ValidateInputs()) {
        return;
    }
    
    if (SaveCourse()) {
        EndModal(wxID_OK);
    }
}

void CourseDialog::OnCancel(wxCommandEvent& /* event */) {
    EndModal(wxID_CANCEL);
}

void CourseDialog::OnTeacherChanged(wxCommandEvent& event) {
    // Handle teacher selection change if needed
    event.Skip();
}

} // namespace GUI
} // namespace SDEP