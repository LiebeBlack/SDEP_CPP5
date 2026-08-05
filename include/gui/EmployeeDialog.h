#ifndef EMPLOYEEDIALOG_H
#define EMPLOYEEDIALOG_H

#include <wx/wx.h>
#include "models/models.h"
#include "services/Services.h"

namespace SDEP {
namespace GUI {

class EmployeeDialog : public wxDialog {
public:
    EmployeeDialog(wxWindow* parent, Services::EmployeeService* employee_service,
                  const Models::Employee& employee = Models::Employee());
    
    Models::Employee GetEmployee() const { return employee_; }
    bool IsSaved() const { return saved_; }
    
private:
    Services::EmployeeService* employee_service_;
    Models::Employee employee_;
    bool saved_ = false;
    bool is_edit_mode_;
    
    // Notebook for organizing many fields
    wxNotebook* notebook_;
    
    // Panels
    wxPanel* personal_panel_;
    wxPanel* professional_panel_;
    wxPanel* financial_panel_;
    wxPanel* additional_panel_;
    
    // Personal info
    wxTextCtrl* employee_code_ctrl_;
    wxTextCtrl* first_name_ctrl_;
    wxTextCtrl* last_name_ctrl_;
    wxTextCtrl* id_number_ctrl_;
    wxTextCtrl* passport_ctrl_;
    wxDatePickerCtrl* birth_date_ctrl_;
    wxComboBox* gender_combo_;
    wxTextCtrl* nationality_ctrl_;
    wxComboBox* civil_status_combo_;
    wxTextCtrl* email_ctrl_;
    wxTextCtrl* phone_ctrl_;
    wxTextCtrl* mobile_ctrl_;
    wxTextCtrl* address_ctrl_;
    wxTextCtrl* city_ctrl_;
    wxTextCtrl* state_ctrl_;
    wxTextCtrl* zip_code_ctrl_;
    wxTextCtrl* emergency_contact_ctrl_;
    wxTextCtrl* emergency_phone_ctrl_;
    
    // Professional info
    wxComboBox* department_combo_;
    wxTextCtrl* position_ctrl_;
    wxDatePickerCtrl* hire_date_ctrl_;
    wxComboBox* employment_type_combo_;
    wxComboBox* employee_status_combo_;
    wxTextCtrl* education_level_ctrl_;
    wxTextCtrl* institution_ctrl_;
    wxTextCtrl* degree_ctrl_;
    wxTextCtrl* graduation_year_ctrl_;
    wxTextCtrl* certifications_ctrl_;
    wxTextCtrl* specializations_ctrl_;
    wxTextCtrl* work_schedule_ctrl_;
    wxTextCtrl* location_ctrl_;
    wxDatePickerCtrl* contract_start_ctrl_;
    wxDatePickerCtrl* contract_end_ctrl_;
    
    // Financial info
    wxTextCtrl* salary_ctrl_;
    wxComboBox* salary_type_combo_;
    wxTextCtrl* bank_name_ctrl_;
    wxTextCtrl* bank_account_ctrl_;
    wxComboBox* bank_account_type_combo_;
    wxComboBox* payment_method_combo_;
    wxTextCtrl* tax_id_ctrl_;
    wxTextCtrl* social_security_ctrl_;
    
    // Additional info
    wxCheckBox* health_insurance_ctrl_;
    wxCheckBox* life_insurance_ctrl_;
    wxCheckBox* retirement_plan_ctrl_;
    wxTextCtrl* other_benefits_ctrl_;
    wxCheckBox* contract_signed_ctrl_;
    wxCheckBox* confidentiality_signed_ctrl_;
    wxCheckBox* background_check_ctrl_;
    wxCheckBox* drug_test_ctrl_;
    wxTextCtrl* notes_ctrl_;
    
    wxStaticText* status_text_;
    
    void OnSave(wxCommandEvent& event);
    void OnCancel(wxCommandEvent& event);
    
    bool ValidateInputs();
    void PopulateFields();
    void CreatePersonalPanel();
    void CreateProfessionalPanel();
    void CreateFinancialPanel();
    void CreateAdditionalPanel();
    bool SaveEmployee();
    
    wxDECLARE_EVENT_TABLE();
};

enum {
    ID_EMPLOYEE_SAVE = wxID_HIGHEST + 500,
    ID_EMPLOYEE_CANCEL
};

} // namespace GUI
} // namespace SDEP

#endif // EMPLOYEEDIALOG_H