#ifndef ENROLLMENTDIALOG_H
#define ENROLLMENTDIALOG_H

#include <wx/wx.h>
#include "models/models.h"
#include "services/Services.h"

namespace SDEP {
namespace GUI {

class EnrollmentDialog : public wxDialog {
public:
    EnrollmentDialog(wxWindow* parent, Services::EnrollmentService* enrollment_service,
                    Services::StudentService* student_service,
                    Services::CourseService* course_service,
                    const Models::Enrollment& enrollment = Models::Enrollment());
    
    Models::Enrollment GetEnrollment() const { return enrollment_; }
    bool IsSaved() const { return saved_; }
    
private:
    Services::EnrollmentService* enrollment_service_;
    Services::StudentService* student_service_;
    Services::CourseService* course_service_;
    Models::Enrollment enrollment_;
    bool saved_ = false;
    bool is_edit_mode_;
    
    // UI components
    wxComboBox* student_combo_;
    wxComboBox* course_combo_;
    wxDatePickerCtrl* enrollment_date_ctrl_;
    wxTextCtrl* grade_ctrl_;
    wxComboBox* status_combo_;
    wxStaticText* status_text_;
    
    void OnSave(wxCommandEvent& event);
    void OnCancel(wxCommandEvent& event);
    void OnStudentChanged(wxCommandEvent& event);
    void OnCourseChanged(wxCommandEvent& event);
    
    bool ValidateInputs();
    void PopulateFields();
    void LoadStudents();
    void LoadCourses();
    bool SaveEnrollment();
    
    wxDECLARE_EVENT_TABLE();
};

enum {
    ID_ENROLLMENT_SAVE = wxID_HIGHEST + 600,
    ID_ENROLLMENT_CANCEL,
    ID_STUDENT_COMBO,
    ID_COURSE_COMBO,
    ID_ENROLLMENT_DATE
};

} // namespace GUI
} // namespace SDEP

#endif // ENROLLMENTDIALOG_H