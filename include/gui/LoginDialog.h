#ifndef LOGINDIALOG_H
#define LOGINDIALOG_H

#include <wx/wx.h>
#include "services/Services.h"

namespace SDEP {
namespace GUI {

class LoginDialog : public wxDialog {
public:
    LoginDialog(wxWindow* parent, Services::SecurityManager* security_manager);
    
    std::string GetUsername() const { return username_; }
    std::string GetSessionToken() const { return session_token_; }
    bool IsAuthenticated() const { return authenticated_; }
    
private:
    Services::SecurityManager* security_manager_;
    
    wxTextCtrl* username_ctrl_;
    wxTextCtrl* password_ctrl_;
    wxStaticText* status_text_;
    
    std::string username_;
    std::string session_token_;
    bool authenticated_ = false;
    
    void OnLogin(wxCommandEvent& event);
    void OnCancel(wxCommandEvent& event);
    void OnKeyPress(wxKeyEvent& event);
    
    wxDECLARE_EVENT_TABLE();
};

enum {
    ID_LOGIN_BUTTON = wxID_HIGHEST + 100,
    ID_CANCEL_BUTTON
};

} // namespace GUI
} // namespace SDEP

#endif // LOGINDIALOG_H