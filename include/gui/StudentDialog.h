#ifndef STUDENTDIALOG_H
#define STUDENTDIALOG_H

#include <wx/wx.h>
#include <wx/datectrl.h>
#include <wx/textctrl.h>
#include <wx/combobox.h>
#include <wx/checkbox.h>
#include "models/models.h"
#include "services/Services.h"

namespace SDEP {
namespace GUI {

class StudentDialog : public wxDialog {
public:
    StudentDialog(wxWindow* parent, Services::StudentService* student_service,
                  const Models::Student& student = Models::Student());
    
    Models::Student GetStudent() const { return student_; }
    bool IsSaved() const { return saved_; }
    
private:
    Services::StudentService* student_service_;
    Models::Student student_;
    bool saved_ = false;
    bool is_edit_mode_;
    
    // UI components
    wxTextCtrl* first_name_ctrl_;
    wxTextCtrl* last_name_ctrl_;
    wxTextCtrl* email_ctrl_;
    wxTextCtrl* phone_ctrl_;
    wxTextCtrl* address_ctrl_;
    wxTextCtrl* enrollment_date_ctrl_;
    wxTextCtrl* grade_ctrl_;
    wxTextCtrl* section_ctrl_;
    wxCheckBox* active_ctrl_;
    wxTextCtrl* parent_name_ctrl_;
    wxTextCtrl* parent_phone_ctrl_;
    wxTextCtrl* emergency_contact_ctrl_;
    wxStaticText* status_text_;
    
    void OnSave(wxCommandEvent& /* event */);
    void OnCancel(wxCommandEvent& /* event */);
    
    bool ValidateInputs();
    void PopulateFields();
    bool SaveStudent();
    
    wxDECLARE_EVENT_TABLE();
};

enum {
    ID_STUDENT_SAVE_BUTTON = wxID_HIGHEST + 200,
    ID_STUDENT_CANCEL_BUTTON = wxID_HIGHEST + 201
};

} // namespace GUI
} // namespace SDEP

#endif // STUDENTDIALOG_H