#include "gui/LoginDialog.h"

namespace SDEP {
namespace GUI {

wxBEGIN_EVENT_TABLE(LoginDialog, wxDialog)
    EVT_BUTTON(ID_LOGIN_BUTTON, LoginDialog::OnLogin)
    EVT_BUTTON(ID_CANCEL_BUTTON, LoginDialog::OnCancel)
    EVT_TEXT_ENTER(wxID_ANY, LoginDialog::OnLogin)
wxEND_EVENT_TABLE()

LoginDialog::LoginDialog(wxWindow* parent, Services::SecurityManager* security_manager)
    : wxDialog(parent, wxID_ANY, "SDEP System Login", wxDefaultPosition, wxSize(400, 350)),
      security_manager_(security_manager) {
    
    // Set dialog properties
    SetMinSize(wxSize(350, 300));
    
    // Create main panel
    wxPanel* panel = new wxPanel(this);
    wxBoxSizer* main_sizer = new wxBoxSizer(wxVERTICAL);
    
    // Title
    wxStaticText* title = new wxStaticText(panel, wxID_ANY, "SDEP Educational System");
    title->SetFont(title->GetFont().Larger().Larger().Bold());
    main_sizer->Add(title, 0, wxALL | wxALIGN_CENTER, 20);
    
    wxStaticText* subtitle = new wxStaticText(panel, wxID_ANY, "Please login to continue");
    main_sizer->Add(subtitle, 0, wxALL | wxALIGN_CENTER, 5);
    
    // Username field
    wxStaticText* username_label = new wxStaticText(panel, wxID_ANY, "Username:");
    main_sizer->Add(username_label, 0, wxALL | wxALIGN_LEFT, 10);
    
    username_ctrl_ = new wxTextCtrl(panel, wxID_ANY, wxEmptyString, 
                                    wxDefaultPosition, wxSize(300, -1));
    username_ctrl_->SetFocus();
    main_sizer->Add(username_ctrl_, 0, wxALL | wxEXPAND, 5);
    
    // Password field
    wxStaticText* password_label = new wxStaticText(panel, wxID_ANY, "Password:");
    main_sizer->Add(password_label, 0, wxALL | wxALIGN_LEFT, 10);
    
    password_ctrl_ = new wxTextCtrl(panel, wxID_ANY, wxEmptyString, 
                                    wxDefaultPosition, wxSize(300, -1), wxTE_PASSWORD);
    main_sizer->Add(password_ctrl_, 0, wxALL | wxEXPAND, 5);
    
    // Status text
    status_text_ = new wxStaticText(panel, wxID_ANY, "");
    status_text_->SetForegroundColour(wxColour(255, 0, 0)); // Red color for errors
    main_sizer->Add(status_text_, 0, wxALL | wxALIGN_CENTER, 10);
    
    // Button panel
    wxPanel* button_panel = new wxPanel(panel);
    wxBoxSizer* button_sizer = new wxBoxSizer(wxHORIZONTAL);
    
    wxButton* login_button = new wxButton(button_panel, ID_LOGIN_BUTTON, "Login");
    wxButton* cancel_button = new wxButton(button_panel, ID_CANCEL_BUTTON, "Cancel");
    
    button_sizer->Add(login_button, 0, wxALL, 5);
    button_sizer->Add(cancel_button, 0, wxALL, 5);
    
    button_panel->SetSizer(button_sizer);
    main_sizer->Add(button_panel, 0, wxALL | wxALIGN_CENTER, 10);
    
    // Default credentials info
    wxStaticText* info = new wxStaticText(panel, wxID_ANY, 
        "Default credentials: admin / Admin123!");
    info->SetFont(info->GetFont().Smaller());
    main_sizer->Add(info, 0, wxALL | wxALIGN_CENTER, 10);
    
    panel->SetSizer(main_sizer);
    main_sizer->Fit(panel);
    
    // Center the dialog
    Centre();
}

void LoginDialog::OnLogin(wxCommandEvent& event) {
    wxString username = username_ctrl_->GetValue();
    wxString password = password_ctrl_->GetValue();
    
    if (username.IsEmpty() || password.IsEmpty()) {
        status_text_->SetLabel("Please enter username and password");
        return;
    }
    
    if (!security_manager_) {
        status_text_->SetLabel("Security manager not initialized");
        return;
    }
    
    // Authenticate user
    Models::User user = security_manager_->authenticateUser(
        username.ToStdString(), password.ToStdString(), "127.0.0.1");
    
    if (user.id > 0) {
        // Authentication successful
        username_ = username.ToStdString();
        session_token_ = security_manager_->createSessionToken(username_);
        authenticated_ = true;
        
        EndModal(wxID_OK);
    } else {
        // Authentication failed
        status_text_->SetLabel("Invalid username or password");
        password_ctrl_->Clear();
        password_ctrl_->SetFocus();
    }
}

void LoginDialog::OnCancel(wxCommandEvent& event) {
    EndModal(wxID_CANCEL);
}

void LoginDialog::OnKeyPress(wxKeyEvent& event) {
    if (event.GetKeyCode() == WXK_RETURN) {
        wxCommandEvent login_event(wxEVT_BUTTON, ID_LOGIN_BUTTON);
        OnLogin(login_event);
    } else {
        event.Skip();
    }
}

} // namespace GUI
} // namespace SDEP