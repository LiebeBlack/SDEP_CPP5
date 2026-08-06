#ifndef TEACHERDIALOG_H
#define TEACHERDIALOG_H

#include <wx/wx.h>
#include <wx/datectrl.h>
#include <wx/dateevt.h>
#include <wx/textctrl.h>
#include <wx/combobox.h>
#include <wx/checkbox.h>
#include "models/models.h"
#include "services/Services.h"

namespace SDEP {
namespace GUI {

class TeacherDialog : public wxDialog {
public:
    TeacherDialog(wxWindow* parent, Services::TeacherService* teacher_service,
                  const Models::Teacher& teacher = Models::Teacher());
    
    Models::Teacher GetTeacher() const { return teacher_; }
    bool IsSaved() const { return saved_; }
    
private:
    Services::TeacherService* teacher_service_;
    Models::Teacher teacher_;
    bool saved_ = false;
    bool is_edit_mode_;
    
    // UI components
    wxTextCtrl* first_name_ctrl_;
    wxTextCtrl* last_name_ctrl_;
    wxTextCtrl* email_ctrl_;
    wxTextCtrl* phone_ctrl_;
    wxComboBox* department_ctrl_;
    wxTextCtrl* specialization_ctrl_;
    wxDatePickerCtrl* hire_date_ctrl_;
    wxCheckBox* active_ctrl_;
    wxTextCtrl* salary_ctrl_;
    wxTextCtrl* qualification_ctrl_;
    wxStaticText* status_text_;
    
    void OnSave(wxCommandEvent& event);
    void OnCancel(wxCommandEvent& event);
    
    bool ValidateInputs();
    void PopulateFields();
    bool SaveTeacher();
    
    wxDECLARE_EVENT_TABLE();
};

enum {
    ID_TEACHER_SAVE = wxID_HIGHEST + 300,
    ID_TEACHER_CANCEL = wxID_HIGHEST + 301,
    ID_HIRE_DATE = wxID_HIGHEST + 302
};

} // namespace GUI
} // namespace SDEP

#endif // TEACHERDIALOG_H