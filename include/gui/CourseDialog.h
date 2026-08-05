#ifndef COURSEDIALOG_H
#define COURSEDIALOG_H

#include <wx/wx.h>
#include "models/models.h"
#include "services/Services.h"

namespace SDEP {
namespace GUI {

class CourseDialog : public wxDialog {
public:
    CourseDialog(wxWindow* parent, Services::CourseService* course_service,
                 Services::TeacherService* teacher_service,
                 const Models::Course& course = Models::Course());
    
    Models::Course GetCourse() const { return course_; }
    bool IsSaved() const { return saved_; }
    
private:
    Services::CourseService* course_service_;
    Services::TeacherService* teacher_service_;
    Models::Course course_;
    bool saved_ = false;
    bool is_edit_mode_;
    
    // UI components
    wxTextCtrl* name_ctrl_;
    wxTextCtrl* code_ctrl_;
    wxComboBox* level_ctrl_;
    wxTextCtrl* description_ctrl_;
    wxComboBox* teacher_combo_;
    wxTextCtrl* credits_ctrl_;
    wxTextCtrl* schedule_ctrl_;
    wxTextCtrl* classroom_ctrl_;
    wxCheckBox* active_ctrl_;
    wxStaticText* status_text_;
    
    void OnSave(wxCommandEvent& event);
    void OnCancel(wxCommandEvent& event);
    void OnTeacherChanged(wxCommandEvent& event);
    
    bool ValidateInputs();
    void PopulateFields();
    void LoadTeachers();
    bool SaveCourse();
    
    wxDECLARE_EVENT_TABLE();
};

enum {
    ID_COURSE_SAVE = wxID_HIGHEST + 400,
    ID_COURSE_CANCEL,
    ID_TEACHER_COMBO
};

} // namespace GUI
} // namespace SDEP

#endif // COURSEDIALOG_H