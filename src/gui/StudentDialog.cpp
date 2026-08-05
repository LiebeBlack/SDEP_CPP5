#include "gui/StudentDialog.h"
#include <wx/datectrl.h>
#include <wx/dateevt.h>
#include <wx/msgdlg.h>
#include <wx/valtext.h>

namespace SDEP {
namespace GUI {

wxBEGIN_EVENT_TABLE(StudentDialog, wxDialog)
    EVT_BUTTON(ID_SAVE_BUTTON, StudentDialog::OnSave)
    EVT_BUTTON(ID_CANCEL_BUTTON, StudentDialog::OnCancel)
    EVT_DATE_CHANGED(ID_ENROLLMENT_DATE, StudentDialog::OnDateChanged)
wxEND_EVENT_TABLE()

StudentDialog::StudentDialog(wxWindow* parent, Services::StudentService* student_service,
                            const Models::Student& student)
    : wxDialog(parent, wxID_ANY, student.id > 0 ? "Edit Student" : "Add Student",
              wxDefaultPosition, wxSize(600, 500)),
      student_service_(student_service),
      student_(student),
      is_edit_mode_(student.id > 0) {
    
    SetMinSize(wxSize(500, 450));
    
    // Create main panel
    wxPanel* panel = new wxPanel(this);
    wxBoxSizer* main_sizer = new wxBoxSizer(wxVERTICAL);
    
    // Title
    wxString title = is_edit_mode_ ? "Edit Student" : "Add New Student";
    wxStaticText* title_text = new wxStaticText(panel, wxID_ANY, title);
    title_text->SetFont(title_text->GetFont().Larger().Bold());
    main_sizer->Add(title_text, 0, wxALL, 10);
    
    // Form grid
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
    
    // Address
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Address:"), 0, wxALIGN_RIGHT | wxALL, 5);
    address_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(address_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Enrollment Date
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Enrollment Date:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxDatePickerCtrl* date_ctrl = new wxDatePickerCtrl(panel, ID_ENROLLMENT_DATE);
    grid_sizer->Add(date_ctrl, 1, wxEXPAND | wxALL, 5);
    
    // Grade
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Grade:"), 0, wxALIGN_RIGHT | wxALL, 5);
    grade_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(grade_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Section
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Section:"), 0, wxALIGN_RIGHT | wxALL, 5);
    section_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(section_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Active
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Active:"), 0, wxALIGN_RIGHT | wxALL, 5);
    active_ctrl_ = new wxCheckBox(panel, wxID_ANY, "Active");
    active_ctrl_->SetValue(true);
    grid_sizer->Add(active_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Parent Name
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Parent Name:"), 0, wxALIGN_RIGHT | wxALL, 5);
    parent_name_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(parent_name_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Parent Phone
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Parent Phone:"), 0, wxALIGN_RIGHT | wxALL, 5);
    parent_phone_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(parent_phone_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Emergency Contact
    grid_sizer->Add(new wxStaticText(panel, wxID_ANY, "Emergency Contact:"), 0, wxALIGN_RIGHT | wxALL, 5);
    emergency_contact_ctrl_ = new wxTextCtrl(panel, wxID_ANY);
    grid_sizer->Add(emergency_contact_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    main_sizer->Add(grid_sizer, 1, wxEXPAND | wxALL, 10);
    
    // Status text
    status_text_ = new wxStaticText(panel, wxID_ANY, "");
    status_text_->SetForegroundColour(wxColour(255, 0, 0));
    main_sizer->Add(status_text_, 0, wxALL | wxALIGN_CENTER, 5);
    
    // Button panel
    wxPanel* button_panel = new wxPanel(panel);
    wxBoxSizer* button_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* save_button = new wxButton(button_panel, ID_SAVE_BUTTON, "Save");
    wxButton* cancel_button = new wxButton(button_panel, ID_CANCEL_BUTTON, "Cancel");
    
    button_sizer->Add(save_button, 0, wxALL, 5);
    button_sizer->Add(cancel_button, 0, wxALL, 5);
    
    button_panel->SetSizer(button_sizer);
    main_sizer->Add(button_panel, 0, wxALL | wxALIGN_CENTER, 10);
    
    panel->SetSizer(main_sizer);
    main_sizer->Fit(panel);
    
    // Populate fields if editing
    if (is_edit_mode_) {
        PopulateFields();
    }
    
    // Center the dialog
    Centre();
}

void StudentDialog::PopulateFields() {
    first_name_ctrl_->SetValue(student_.first_name);
    last_name_ctrl_->SetValue(student_.last_name);
    email_ctrl_->SetValue(student_.email);
    phone_ctrl_->SetValue(student_.phone);
    address_ctrl_->SetValue(student_.address);
    grade_ctrl_->SetValue(student_.grade);
    section_ctrl_->SetValue(student_.section);
    active_ctrl_->SetValue(student_.active);
    parent_name_ctrl_->SetValue(student_.parent_name);
    parent_phone_ctrl_->SetValue(student_.parent_phone);
    emergency_contact_ctrl_->SetValue(student_.emergency_contact);
    
    // Set enrollment date if available
    if (!student_.enrollment_date.empty()) {
        // Parse date string and set to date picker
        // This would need proper date parsing
    }
}

bool StudentDialog::ValidateInputs() {
    if (first_name_ctrl_->GetValue().Trim().IsEmpty()) {
        status_text_->SetLabel("First name is required");
        first_name_ctrl_->SetFocus();
        return false;
    }
    
    if (first_name_ctrl_->GetValue().Length() < 2) {
        status_text_->SetLabel("First name must be at least 2 characters");
        first_name_ctrl_->SetFocus();
        return false;
    }
    
    if (last_name_ctrl_->GetValue().Trim().IsEmpty()) {
        status_text_->SetLabel("Last name is required");
        last_name_ctrl_->SetFocus();
        return false;
    }
    
    if (last_name_ctrl_->GetValue().Length() < 2) {
        status_text_->SetLabel("Last name must be at least 2 characters");
        last_name_ctrl_->SetFocus();
        return false;
    }
    
    wxString email = email_ctrl_->GetValue().Trim();
    if (!email.IsEmpty()) {
        // Basic email validation
        if (!email.Contains("@") || !email.Contains(".")) {
            status_text_->SetLabel("Invalid email format");
            email_ctrl_->SetFocus();
            return false;
        }
    }
    
    return true;
}

bool StudentDialog::SaveStudent() {
    try {
        // Update student object
        student_.first_name = first_name_ctrl_->GetValue().ToStdString();
        student_.last_name = last_name_ctrl_->GetValue().ToStdString();
        student_.email = email_ctrl_->GetValue().ToStdString();
        student_.phone = phone_ctrl_->GetValue().ToStdString();
        student_.address = address_ctrl_->GetValue().ToStdString();
        student_.grade = grade_ctrl_->GetValue().ToStdString();
        student_.section = section_ctrl_->GetValue().ToStdString();
        student_.active = active_ctrl_->GetValue();
        student_.parent_name = parent_name_ctrl_->GetValue().ToStdString();
        student_.parent_phone = parent_phone_ctrl_->GetValue().ToStdString();
        student_.emergency_contact = emergency_contact_ctrl_->GetValue().ToStdString();
        
        // Get enrollment date from date picker
        wxDatePickerCtrl* date_ctrl = static_cast<wxDatePickerCtrl*>(FindWindow(ID_ENROLLMENT_DATE));
        if (date_ctrl) {
            wxDateTime date = date_ctrl->GetValue();
            student_.enrollment_date = date.FormatISODate().ToStdString();
        }
        
        // Validate
        if (!student_.validate()) {
            status_text_->SetLabel("Validation failed");
            return false;
        }
        
        // Save through service
        if (is_edit_mode_) {
            if (student_service_->updateStudent(student_)) {
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to update student");
                return false;
            }
        } else {
            int new_id = student_service_->createStudent(student_);
            if (new_id > 0) {
                student_.id = new_id;
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to create student");
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

void StudentDialog::OnSave(wxCommandEvent& event) {
    if (!ValidateInputs()) {
        return;
    }
    
    if (SaveStudent()) {
        EndModal(wxID_OK);
    }
}

void StudentDialog::OnCancel(wxCommandEvent& event) {
    EndModal(wxID_CANCEL);
}

void StudentDialog::OnDateChanged(wxDateEvent& event) {
    // Handle date change if needed
    event.Skip();
}

} // namespace GUI
} // namespace SDEP