#include "gui/TeacherDialog.h"
#include <wx/datectrl.h>
#include <wx/dateevt.h>
#include <wx/msgdlg.h>

namespace SDEP {
namespace GUI {

wxBEGIN_EVENT_TABLE(TeacherDialog, wxDialog)
    EVT_BUTTON(ID_TEACHER_SAVE, TeacherDialog::OnSave)
    EVT_BUTTON(ID_TEACHER_CANCEL, TeacherDialog::OnCancel)
wxEND_EVENT_TABLE()

TeacherDialog::TeacherDialog(wxWindow* parent, Services::TeacherService* teacher_service,
                            const Models::Teacher& teacher)
    : wxDialog(parent, wxID_ANY, teacher.id > 0 ? "Edit Teacher" : "Add Teacher",
              wxDefaultPosition, wxSize(600, 450)),
      teacher_service_(teacher_service),
      teacher_(teacher),
      is_edit_mode_(teacher.id > 0) {
    
    SetMinSize(wxSize(500, 400));
    
    wxPanel* panel = new wxPanel(this);
    wxBoxSizer* main_sizer = new wxBoxSizer(wxVERTICAL);
    
    wxString title = is_edit_mode_ ? "Edit Teacher" : "Add New Teacher";
    wxStaticText* title_text = new wxStaticText(panel, wxID_ANY, title);
    title_text->SetFont(title_text->GetFont().Larger().Bold());
    main_sizer->Add(title_text, 0, wxALL, 10);
    
    wxFlexGridSizer* grid_sizer = new wxFlexGridSizer(2, 10, 10);
    grid_sizer->AddGrowableCol(1);
    
    // First Name
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "First Name*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    first_name_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(first_name_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Last Name
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Last Name*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    last_name_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(last_name_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Email
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Email:"), 0, wxALIGN_RIGHT | wxALL, 5);
    email_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(email_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Phone
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Phone:"), 0, wxALIGN_RIGHT | wxALL, 5);
    phone_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(phone_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Department
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Department:"), 0, wxALIGN_RIGHT | wxALL, 5);
    department_ctrl_ = new wxComboBox(panel, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, wxArrayString(), wxCB_READONLY);
    grid_sizer->Add(department_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Specialization
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Specialization:"), 0, wxALIGN_RIGHT | wxALL, 5);
    specialization_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(specialization_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Hire Date
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Hire Date:"), 0, wxALIGN_RIGHT | wxALL, 5);
    hire_date_ctrl_ = new wxDatePickerCtrl(panel, ID_HIRE_DATE);
    grid_sizer->Add(hire_date_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Salary
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Salary:"), 0, wxALIGN_RIGHT | wxALL, 5);
    salary_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    salary_ctrl_->SetValidator(wxFloatingPointValidator<double>(2));
    grid_sizer->Add(salary_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Qualification
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Qualification:"), 0, wxALIGN_RIGHT | wxALL, 5);
    qualification_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(qualification_ctrl_, 1, wxEXPAND | wxALL, 5);
    
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
    
    wxButton* save_button = new wxButton(button_panel, ID_TEACHER_SAVE, "Save");
    wxButton* cancel_button = new wxButton(button_panel, ID_TEACHER_CANCEL, "Cancel");
    
    button_sizer->Add(save_button, 0, wxALL, 5);
    button_sizer->Add(cancel_button, 0, wxALL, 5);
    
    button_panel->SetSizer(button_sizer);
    main_sizer->Add(button_panel, 0, wxALL | wxALIGN_CENTER, 10);
    
    panel->SetSizer(main_sizer);
    main_sizer->Fit(panel);
    
    // Add department options
    wxArrayString departments;
    departments.Add("Mathematics");
    departments.Add("Science");
    departments.Add("Languages");
    departments.Add("Social Studies");
    departments.Add("Arts");
    departments.Add("Physical Education");
    departments.Add("Technology");
    department_ctrl_->Append(departments);
    
    if (is_edit_mode_) {
        PopulateFields();
    }
    
    Centre();
}

void TeacherDialog::PopulateFields() {
    first_name_ctrl_->SetValue(teacher_.first_name);
    last_name_ctrl_->SetValue(teacher_.last_name);
    email_ctrl_->SetValue(teacher_.email);
    phone_ctrl_->SetValue(teacher_.phone);
    department_ctrl_->SetValue(teacher_.department);
    specialization_ctrl_->SetValue(teacher_.specialization);
    salary_ctrl_->SetValue(wxString::Format("%.2f", teacher_.salary));
    qualification_ctrl_->SetValue(teacher_.qualification);
    active_ctrl_->SetValue(teacher_.active);
    
    if (!teacher_.hire_date.empty()) {
        // Parse and set hire date
    }
}

bool TeacherDialog::ValidateInputs() {
    if (first_name_ctrl_->GetValue().Trim().IsEmpty()) {
        status_text_->SetLabel("First name is required");
        first_name_ctrl_->SetFocus();
        return false;
    }
    
    if (last_name_ctrl_->GetValue().Trim().IsEmpty()) {
        status_text_->SetLabel("Last name is required");
        last_name_ctrl_->SetFocus();
        return false;
    }
    
    wxString salary_str = salary_ctrl_->GetValue();
    if (!salary_str.IsEmpty()) {
        double salary;
        if (!salary_str.ToDouble(&salary) || salary < 0) {
            status_text_->SetLabel("Invalid salary amount");
            salary_ctrl_->SetFocus();
            return false;
        }
    }
    
    return true;
}

bool TeacherDialog::SaveTeacher() {
    try {
        teacher_.first_name = first_name_ctrl_->GetValue().ToStdString();
        teacher_.last_name = last_name_ctrl_->GetValue().ToStdString();
        teacher_.email = email_ctrl_->GetValue().ToStdString();
        teacher_.phone = phone_ctrl_->GetValue().ToStdString();
        teacher_.department = department_ctrl_->GetValue().ToStdString();
        teacher_.specialization = specialization_ctrl_->GetValue().ToStdString();
        teacher_.active = active_ctrl_->GetValue();
        teacher_.qualification = qualification_ctrl_->GetValue().ToStdString();
        
        wxString salary_str = salary_ctrl_->GetValue();
        if (!salary_str.IsEmpty()) {
            salary_str.ToDouble(&teacher_.salary);
        }
        
        wxDateTime hire_date = hire_date_ctrl_->GetValue();
        teacher_.hire_date = hire_date.FormatISODate().ToStdString();
        
        if (!teacher_.validate()) {
            status_text_->SetLabel("Validation failed");
            return false;
        }
        
        if (is_edit_mode_) {
            if (teacher_service_->updateTeacher(teacher_)) {
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to update teacher");
                return false;
            }
        } else {
            int new_id = teacher_service_->createTeacher(teacher_);
            if (new_id > 0) {
                teacher_.id = new_id;
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to create teacher");
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

void TeacherDialog::OnSave(wxCommandEvent& event) {
    if (!ValidateInputs()) {
        return;
    }
    
    if (SaveTeacher()) {
        EndModal(wxID_OK);
    }
}

void TeacherDialog::OnCancel(wxCommandEvent& event) {
    EndModal(wxID_CANCEL);
}

} // namespace GUI
} // namespace SDEP