#include "gui/EmployeeDialog.h"
#include <wx/datectrl.h>
#include <wx/dateevt.h>
#include <wx/msgdlg.h>
#include <wx/splitter.h>

namespace SDEP {
namespace GUI {

wxBEGIN_EVENT_TABLE(EmployeeDialog, wxDialog)
    EVT_BUTTON(ID_EMPLOYEE_SAVE, EmployeeDialog::OnSave)
    EVT_BUTTON(ID_EMPLOYEE_CANCEL, EmployeeDialog::OnCancel)
wxEND_EVENT_TABLE()

EmployeeDialog::EmployeeDialog(wxWindow* parent, Services::EmployeeService* employee_service,
                              const Models::Employee& employee)
    : wxDialog(parent, wxID_ANY, employee.id > 0 ? "Edit Employee" : "Add Employee",
              wxDefaultPosition, wxSize(800, 600)),
      employee_service_(employee_service),
      employee_(employee),
      is_edit_mode_(employee.id > 0) {
    
    SetMinSize(wxSize(700, 500));
    
    wxPanel* panel = new wxPanel(this);
    wxBoxSizer* main_sizer = new wxBoxSizer(wxVERTICAL);
    
    wxString title = is_edit_mode_ ? "Edit Employee" : "Add New Employee";
    wxStaticText* title_text = new wxStaticText(panel, wxID_ANY, title);
    title_text->SetFont(title_text->GetFont().Larger().Bold());
    main_sizer->Add(title_text, 0, wxALL, 10);
    
    // Create notebook for organizing tabs
    notebook_ = new wxNotebook(panel, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxNB_DEFAULT);
    
    CreatePersonalPanel();
    CreateProfessionalPanel();
    CreateFinancialPanel();
    CreateAdditionalPanel();
    
    notebook_->AddPage(personal_panel_, "Personal");
    notebook_->AddPage(professional_panel_, "Professional");
    notebook_->AddPage(financial_panel_, "Financial");
    notebook_->AddPage(additional_panel_, "Additional");
    
    main_sizer->Add(notebook_, 1, wxEXPAND | wxALL, 10);
    
    // Status text
    status_text_ = new wxStaticText(panel, wxID_ANY, "");
    status_text_->SetForegroundColour(wxColour(255, 0, 0));
    main_sizer->Add(status_text_, 0, wxALL | wxALIGN_CENTER, 5);
    
    // Button panel
    wxPanel* button_panel = new wxPanel(panel);
    wxBoxSizer* button_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* save_button = new wxButton(button_panel, ID_EMPLOYEE_SAVE, "Save");
    wxButton* cancel_button = new wxButton(button_panel, ID_EMPLOYEE_CANCEL, "Cancel");
    
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

void EmployeeDialog::CreatePersonalPanel() {
    personal_panel_ = new wxPanel(notebook_);
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxFlexGridSizer* grid_sizer = new wxFlexGridSizer(2, 10, 10);
    grid_sizer->AddGrowableCol(1);
    
    // Employee Code
    grid_sizer->Add(new wxStaticText(personal_panel_, wxID_ANY, "Employee Code:"), 0, wxALIGN_RIGHT | wxALL, 5);
    employee_code_ctrl_ = new wxTextCtrl(personal_panel_, wxID_ANY);
    grid_sizer->Add(employee_code_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // First Name
    grid_sizer->Add(new wxStaticText(personal_panel_, wxID_ANY, "First Name*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    first_name_ctrl_ = new wxTextCtrl(personal_panel_, wxID_ANY);
    grid_sizer->Add(first_name_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Last Name
    grid_sizer->Add(new wxStaticText(personal_panel_, wxID_ANY, "Last Name*:"), 0, wxALIGN_RIGHT | wxALL, 5);
    last_name_ctrl_ = new wxTextCtrl(personal_panel_, wxID_ANY);
    grid_sizer->Add(last_name_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // ID Number
    grid_sizer->Add(new wxStaticText(personal_panel_, wxID_ANY, "ID Number:"), 0, wxALIGN_RIGHT | wxALL, 5);
    id_number_ctrl_ = new wxTextCtrl(personal_panel_, wxID_ANY);
    grid_sizer->Add(id_number_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Email
    grid_sizer->Add(new wxStaticText(personal_panel_, wxID_ANY, "Email:"), 0, wxALIGN_RIGHT | wxALL, 5);
    email_ctrl_ = new wxTextCtrl(personal_panel_, wxID_ANY);
    grid_sizer->Add(email_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Phone
    grid_sizer->Add(new wxStaticText(personal_panel_, wxID_ANY, "Phone:"), 0, wxALIGN_RIGHT | wxALL, 5);
    phone_ctrl_ = new wxTextCtrl(personal_panel_, wxID_ANY);
    grid_sizer->Add(phone_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Address
    grid_sizer->Add(new wxStaticText(personal_panel_, wxID_ANY, "Address:"), 0, wxALIGN_RIGHT | wxALL, 5);
    address_ctrl_ = new wxTextCtrl(personal_panel_, wxID_ANY);
    grid_sizer->Add(address_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Emergency Contact
    grid_sizer->Add(new wxStaticText(personal_panel_, wxID_ANY, "Emergency Contact:"), 0, wxALIGN_RIGHT | wxALL, 5);
    emergency_contact_ctrl_ = new wxTextCtrl(personal_panel_, wxID_ANY);
    grid_sizer->Add(emergency_contact_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    sizer->Add(grid_sizer, 1, wxEXPAND | wxALL, 10);
    personal_panel_->SetSizer(sizer);
}

void EmployeeDialog::CreateProfessionalPanel() {
    professional_panel_ = new wxPanel(notebook_);
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxFlexGridSizer* grid_sizer = new wxFlexGridSizer(2, 10, 10);
    grid_sizer->AddGrowableCol(1);
    
    // Department
    grid_sizer->Add(new wxStaticText(professional_panel_, wxID_ANY, "Department:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxArrayString departments;
    departments.Add("Administration");
    departments.Add("Academic");
    departments.Add("Finance");
    departments.Add("Human Resources");
    departments.Add("Maintenance");
    departments.Add("Security");
    departments.Add("IT Support");
    department_combo_ = new wxComboBox(professional_panel_, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, departments, wxCB_READONLY);
    grid_sizer->Add(department_combo_, 1, wxEXPAND | wxALL, 5);
    
    // Position
    grid_sizer->Add(new wxStaticText(professional_panel_, wxID_ANY, "Position:"), 0, wxALIGN_RIGHT | wxALL, 5);
    position_ctrl_ = new wxTextCtrl(professional_panel_, wxID_ANY);
    grid_sizer->Add(position_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Employment Type
    grid_sizer->Add(new wxStaticText(professional_panel_, wxID_ANY, "Employment Type:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxArrayString emp_types;
    emp_types.Add("Full-time");
    emp_types.Add("Part-time");
    emp_types.Add("Contract");
    emp_types.Add("Intern");
    employment_type_combo_ = new wxComboBox(professional_panel_, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, emp_types, wxCB_READONLY);
    grid_sizer->Add(employment_type_combo_, 1, wxEXPAND | wxALL, 5);
    
    // Hire Date
    grid_sizer->Add(new wxStaticText(professional_panel_, wxID_ANY, "Hire Date:"), 0, wxALIGN_RIGHT | wxALL, 5);
    hire_date_ctrl_ = new wxDatePickerCtrl(professional_panel_, wxID_ANY);
    grid_sizer->Add(hire_date_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Work Schedule
    grid_sizer->Add(new wxStaticText(professional_panel_, wxID_ANY, "Work Schedule:"), 0, wxALIGN_RIGHT | wxALL, 5);
    work_schedule_ctrl_ = new wxTextCtrl(professional_panel_, wxID_ANY);
    grid_sizer->Add(work_schedule_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    sizer->Add(grid_sizer, 1, wxEXPAND | wxALL, 10);
    professional_panel_->SetSizer(sizer);
}

void EmployeeDialog::CreateFinancialPanel() {
    financial_panel_ = new wxPanel(notebook_);
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxFlexGridSizer* grid_sizer = new wxFlexGridSizer(2, 10, 10);
    grid_sizer->AddGrowableCol(1);
    
    // Salary
    grid_sizer->Add(new wxStaticText(financial_panel_, wxID_ANY, "Salary:"), 0, wxALIGN_RIGHT | wxALL, 5);
    salary_ctrl_ = new wxTextCtrl(financial_panel_, wxID_ANY);
    salary_ctrl_->SetValidator(wxFloatingPointValidator<double>(2));
    grid_sizer->Add(salary_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Salary Type
    grid_sizer->Add(new wxStaticText(financial_panel_, wxID_ANY, "Salary Type:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxArrayString salary_types;
    salary_types.Add("Monthly");
    salary_types.Add("Bi-weekly");
    salary_types.Add("Weekly");
    salary_types.Add("Hourly");
    salary_type_combo_ = new wxComboBox(financial_panel_, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, salary_types, wxCB_READONLY);
    grid_sizer->Add(salary_type_combo_, 1, wxEXPAND | wxALL, 5);
    
    // Bank Name
    grid_sizer->Add(new wxStaticText(financial_panel_, wxID_ANY, "Bank Name:"), 0, wxALIGN_RIGHT | wxALL, 5);
    bank_name_ctrl_ = new wxTextCtrl(financial_panel_, wxID_ANY);
    grid_sizer->Add(bank_name_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Bank Account
    grid_sizer->Add(new wxStaticText(financial_panel_, wxID_ANY, "Bank Account:"), 0, wxALIGN_RIGHT | wxALL, 5);
    bank_account_ctrl_ = new wxTextCtrl(financial_panel_, wxID_ANY);
    grid_sizer->Add(bank_account_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Payment Method
    grid_sizer->Add(new wxStaticText(financial_panel_, wxID_ANY, "Payment Method:"), 0, wxALIGN_RIGHT | wxALL, 5);
    wxArrayString payment_methods;
    payment_methods.Add("Direct Deposit");
    payment_methods.Add("Check");
    payment_methods.Add("Cash");
    payment_method_combo_ = new wxComboBox(financial_panel_, wxID_ANY, "", wxDefaultPosition, wxDefaultSize, payment_methods, wxCB_READONLY);
    grid_sizer->Add(payment_method_combo_, 1, wxEXPAND | wxALL, 5);
    
    sizer->Add(grid_sizer, 1, wxEXPAND | wxALL, 10);
    financial_panel_->SetSizer(sizer);
}

void EmployeeDialog::CreateAdditionalPanel() {
    additional_panel_ = new wxPanel(notebook_);
    wxBoxSizer* sizer = new wxBoxSizer(wxVERTICAL);
    
    wxFlexGridSizer* grid_sizer = new wxFlexGridSizer(2, 10, 10);
    grid_sizer->AddGrowableCol(1);
    
    // Health Insurance
    grid_sizer->Add(new wxStaticText(additional_panel_, wxID_ANY, "Health Insurance:"), 0, wxALIGN_RIGHT | wxALL, 5);
    health_insurance_ctrl_ = new wxCheckBox(additional_panel_, wxID_ANY, "Enabled");
    grid_sizer->Add(health_insurance_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Life Insurance
    grid_sizer->Add(new wxStaticText(additional_panel_, wxID_ANY, "Life Insurance:"), 0, wxALIGN_RIGHT | wxALL, 5);
    life_insurance_ctrl_ = new wxCheckBox(additional_panel_, wxID_ANY, "Enabled");
    grid_sizer->Add(life_insurance_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Retirement Plan
    grid_sizer->Add(new wxStaticText(additional_panel_, wxID_ANY, "Retirement Plan:"), 0, wxALIGN_RIGHT | wxALL, 5);
    retirement_plan_ctrl_ = new wxCheckBox(additional_panel_, wxID_ANY, "Enabled");
    grid_sizer->Add(retirement_plan_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Contract Signed
    grid_sizer->Add(new wxStaticText(additional_panel_, wxID_ANY, "Contract Signed:"), 0, wxALIGN_RIGHT | wxALL, 5);
    contract_signed_ctrl_ = new wxCheckBox(additional_panel_, wxID_ANY, "Yes");
    grid_sizer->Add(contract_signed_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    // Notes
    grid_sizer->Add(new wxStaticText(additional_panel_, wxID_ANY, "Notes:"), 0, wxALIGN_RIGHT | wxALL, 5);
    notes_ctrl_ = new wxTextCtrl(additional_panel_, wxID_ANY, "", wxDefaultPosition, wxSize(-1, 100), wxTE_MULTILINE);
    grid_sizer->Add(notes_ctrl_, 1, wxEXPAND | wxALL, 5);
    
    sizer->Add(grid_sizer, 1, wxEXPAND | wxALL, 10);
    additional_panel_->SetSizer(sizer);
}

void EmployeeDialog::PopulateFields() {
    employee_code_ctrl_->SetValue(employee_.employee_code);
    first_name_ctrl_->SetValue(employee_.first_name);
    last_name_ctrl_->SetValue(employee_.last_name);
    id_number_ctrl_->SetValue(employee_.id_number);
    email_ctrl_->SetValue(employee_.email);
    phone_ctrl_->SetValue(employee_.phone);
    address_ctrl_->SetValue(employee_.address);
    emergency_contact_ctrl_->SetValue(employee_.emergency_contact);
    department_combo_->SetValue(employee_.department);
    position_ctrl_->SetValue(employee_.position);
    employment_type_combo_->SetValue(employee_.employment_type);
    work_schedule_ctrl_->SetValue(employee_.work_schedule);
    salary_ctrl_->SetValue(wxString::Format("%.2f", employee_.salary));
    salary_type_combo_->SetValue(employee_.salary_type);
    bank_name_ctrl_->SetValue(employee_.bank_name);
    bank_account_ctrl_->SetValue(employee_.bank_account);
    payment_method_combo_->SetValue(employee_.payment_method);
    health_insurance_ctrl_->SetValue(employee_.health_insurance);
    life_insurance_ctrl_->SetValue(employee_.life_insurance);
    retirement_plan_ctrl_->SetValue(employee_.retirement_plan);
    contract_signed_ctrl_->SetValue(employee_.contract_signed);
    notes_ctrl_->SetValue(employee_.notes);
    
    // Set dates if available
    if (!employee_.hire_date.empty()) {
        // Parse and set hire date
    }
}

bool EmployeeDialog::ValidateInputs() {
    if (first_name_ctrl_->GetValue().Trim().IsEmpty()) {
        status_text_->SetLabel("First name is required");
        notebook_->SetSelection(0); // Switch to personal tab
        first_name_ctrl_->SetFocus();
        return false;
    }
    
    if (last_name_ctrl_->GetValue().Trim().IsEmpty()) {
        status_text_->SetLabel("Last name is required");
        notebook_->SetSelection(0);
        last_name_ctrl_->SetFocus();
        return false;
    }
    
    wxString salary_str = salary_ctrl_->GetValue();
    if (!salary_str.IsEmpty()) {
        double salary;
        if (!salary_str.ToDouble(&salary) || salary < 0) {
            status_text_->SetLabel("Invalid salary amount");
            notebook_->SetSelection(2); // Switch to financial tab
            salary_ctrl_->SetFocus();
            return false;
        }
    }
    
    return true;
}

bool EmployeeDialog::SaveEmployee() {
    try {
        employee_.employee_code = employee_code_ctrl_->GetValue().ToStdString();
        employee_.first_name = first_name_ctrl_->GetValue().ToStdString();
        employee_.last_name = last_name_ctrl_->GetValue().ToStdString();
        employee_.id_number = id_number_ctrl_->GetValue().ToStdString();
        employee_.email = email_ctrl_->GetValue().ToStdString();
        employee_.phone = phone_ctrl_->GetValue().ToStdString();
        employee_.address = address_ctrl_->GetValue().ToStdString();
        employee_.emergency_contact = emergency_contact_ctrl_->GetValue().ToStdString();
        employee_.department = department_combo_->GetValue().ToStdString();
        employee_.position = position_ctrl_->GetValue().ToStdString();
        employee_.employment_type = employment_type_combo_->GetValue().ToStdString();
        employee_.work_schedule = work_schedule_ctrl_->GetValue().ToStdString();
        employee_.salary_type = salary_type_combo_->GetValue().ToStdString();
        employee_.bank_name = bank_name_ctrl_->GetValue().ToStdString();
        employee_.bank_account = bank_account_ctrl_->GetValue().ToStdString();
        employee_.payment_method = payment_method_combo_->GetValue().ToStdString();
        employee_.health_insurance = health_insurance_ctrl_->GetValue();
        employee_.life_insurance = life_insurance_ctrl_->GetValue();
        employee_.retirement_plan = retirement_plan_ctrl_->GetValue();
        employee_.contract_signed = contract_signed_ctrl_->GetValue();
        employee_.notes = notes_ctrl_->GetValue().ToStdString();
        
        wxString salary_str = salary_ctrl_->GetValue();
        if (!salary_str.IsEmpty()) {
            salary_str.ToDouble(&employee_.salary);
        }
        
        wxDateTime hire_date = hire_date_ctrl_->GetValue();
        employee_.hire_date = hire_date.FormatISODate().ToStdString();
        
        if (!employee_.validate()) {
            status_text_->SetLabel("Validation failed");
            return false;
        }
        
        if (is_edit_mode_) {
            if (employee_service_->updateEmployee(employee_)) {
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to update employee");
                return false;
            }
        } else {
            int new_id = employee_service_->createEmployee(employee_);
            if (new_id > 0) {
                employee_.id = new_id;
                saved_ = true;
                return true;
            } else {
                status_text_->SetLabel("Failed to create employee");
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

void EmployeeDialog::OnSave(wxCommandEvent& event) {
    if (!ValidateInputs()) {
        return;
    }
    
    if (SaveEmployee()) {
        EndModal(wxID_OK);
    }
}

void EmployeeDialog::OnCancel(wxCommandEvent& event) {
    EndModal(wxID_CANCEL);
}

} // namespace GUI
} // namespace SDEP