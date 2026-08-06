#ifndef ATTENDANCEDIALOG_H
#define ATTENDANCEDIALOG_H

#include <wx/wx.h>
#include <wx/datectrl.h>
#include <wx/dateevt.h>
#include <wx/textctrl.h>
#include <wx/combobox.h>
#include "models/models.h"
#include "services/Services.h"

namespace SDEP {
namespace GUI {

class AttendanceDialog : public wxDialog {
public:
    AttendanceDialog(wxWindow* parent, Services::AttendanceService* attendance_service,
                    Services::StudentService* student_service,
                    Services::CourseService* course_service,
                    const Models::Attendance& attendance = Models::Attendance());
    
    Models::Attendance GetAttendance() const { return attendance_; }
    bool IsSaved() const { return saved_; }
    
private:
    Services::AttendanceService* attendance_service_;
    Services::StudentService* student_service_;
    Services::CourseService* course_service_;
    Models::Attendance attendance_;
    bool saved_ = false;
    bool is_edit_mode_;
    
    // UI components
    wxComboBox* student_combo_;
    wxComboBox* course_combo_;
    wxDatePickerCtrl* date_ctrl_;
    wxComboBox* status_combo_;
    wxTextCtrl* notes_ctrl_;
    wxStaticText* status_text_;
    
    void OnSave(wxCommandEvent& event);
    void OnCancel(wxCommandEvent& event);
    void OnStudentChanged(wxCommandEvent& event);
    void OnCourseChanged(wxCommandEvent& event);
    
    bool ValidateInputs();
    void PopulateFields();
    void LoadStudents();
    void LoadCourses();
    bool SaveAttendance();
    
    wxDECLARE_EVENT_TABLE();
};

enum {
    ID_ATTENDANCE_SAVE = wxID_HIGHEST + 700,
    ID_ATTENDANCE_CANCEL = wxID_HIGHEST + 701,
    ID_ATTENDANCE_STUDENT_COMBO = wxID_HIGHEST + 702,
    ID_ATTENDANCE_COURSE_COMBO = wxID_HIGHEST + 703,
    ID_ATTENDANCE_DATE = wxID_HIGHEST + 704
};

} // namespace GUI
} // namespace SDEP

#endif // ATTENDANCEDIALOG_H