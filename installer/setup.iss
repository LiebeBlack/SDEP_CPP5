; Instalador de "Sistema de Gestión de Personal" / SDEP_CPP5
;
; Compilación local (sin firmar, desde la raíz del proyecto):
;   ISCC.exe /DMyAppVersion=3.0.1 installer\setup.iss
;
; Compilación firmada (GitHub Actions - .github/workflows/release.yml):
;   ISCC.exe /DMyAppVersion=1.0.0 /DMyVersionInfo=1.0.0 ^
;           "/DMyAppName=Sistema de Gestión de Personal" ^
;           /DMyAppExeName=SDEP_CPP5.exe ^
;           /DMyOutputBaseFilename=SistemaGestionPersonal-Setup-1.0.0 ^
;           /DConFirmaCI=1 ^
;           /SGitHubSign="$qC:\...\signtool.exe$q sign /sha1 <huella> ^
;           /f $qC:\...\cert.pfx$q /p <contraseña> /fd SHA256 ^
;           /tr http://timestamp.digicert.com /td SHA256 $f" installer\setup.iss
;
; Certificados de la cadena de LiebeBlack Systems (tools\cert_01.cer ... tools\cert_04.cer):
;   cert_01 -> Raíz ("LiebeBlack Global Master Root Authority 2026")    -> LocalMachine\Root
;   cert_02 -> Intermedio N1 ("LiebeBlack Policy & Intermediate CA G1")  -> LocalMachine\CA
;   cert_03 -> Intermedio N2 ("LiebeBlack Code Signing Issuing CA v2")   -> LocalMachine\CA
;   cert_04 -> Hoja de firma de software: NO se instala. Viaja incrustada
;              en los ejecutables firmados y Windows la valida con la
;              cadena cert_01 -> cert_02 -> cert_03.
;   Los 4 .cer se copian a {tmp} (deleteafterinstall); los 3 primeros se
;   importan de forma progresiva con certutil -addstore -f durante la
;   instalación. SOLO se usan estos 4 certificados: cualquier otro .cer
;   antiguo quedó obsoleto y ELIMINADO del proyecto.
; Clave privada (PFX, secreto PFX_BASE64 en CI):
;   NO viaja dentro del instalador. Solo se usa para FIRMAR el ejecutable
;   y el instalador en el CI, donde el PFX se recupera desde el secreto
;   PFX_BASE64 y se elimina del runner al terminar.

#ifndef MyAppVersion
  #define MyAppVersion "3.0.1"
#endif

#ifndef MyVersionInfo
  #if Pos(".", MyAppVersion) == 0
    #define MyVersionInfo MyAppVersion + ".0.0"
  #else
    #define MyVersionInfo MyAppVersion + ".0"
  #endif
#endif

#ifndef MyAppName
  #define MyAppName "Sistema de Gestión de Personal"
#endif

#ifndef MyAppExeName
  #define MyAppExeName "SistemaGestionPersonal.exe"
#endif

#ifndef MyOutputBaseFilename
  #define MyOutputBaseFilename "SistemaGestionPersonal-Setup-" + MyAppVersion
#endif

#ifndef MyDistDir
  #define MyDistDir "SistemaGestionPersonal"
#endif
#define MyAppPublisher "LiebeBlack"
#define MyAppURL "https://github.com/LiebeBlack/SDEP_CPP5"
#define MyAppId "{{8C1E9F5A-3B6D-4A2E-9C41-D7F06B2A5E91}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Licencia personalizada mediante páginas de asistente (ver [Code])
; LicenseFile=..\LICENSE
OutputDir=..\dist_installer
OutputBaseFilename={#MyOutputBaseFilename}
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
PrivilegesRequired=admin
CloseApplications=force
RestartApplications=no
VersionInfoVersion={#MyVersionInfo}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}

#ifndef ConFirmaCI
SignedUninstaller=no
#endif
#ifdef ConFirmaCI
SignTool=GitHubSign
SignedUninstaller=yes
#endif

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
#if !FileExists("..\dist\" + MyDistDir + "\" + MyAppExeName)
  #pragma error "Falta el ejecutable principal compilado; genere primero el paquete con PyInstaller."
#endif
#if !FileExists("..\dist_updater\SDEP_CPP5_AutoUpdater.exe")
  #pragma error "Falta el actualizador; genere primero dist_updater\SDEP_CPP5_AutoUpdater.exe."
#endif
Source: "..\dist\{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Cadena de certificados de LiebeBlack Systems: se copian a {tmp} y se
; eliminan al terminar la instalación (deleteafterinstall). Los .cer son
; PÚBLICOS y deben versionarse. El #pragma error hace FALLAR LA COMPILACIÓN
; si falta alguno.
#if FileExists("..\tools\cert_01.cer")
Source: "..\tools\cert_01.cer"; DestDir: "{tmp}"; Flags: deleteafterinstall
#endif
#if FileExists("..\tools\cert_02.cer")
Source: "..\tools\cert_02.cer"; DestDir: "{tmp}"; Flags: deleteafterinstall
#endif
#if FileExists("..\tools\cert_03.cer")
Source: "..\tools\cert_03.cer"; DestDir: "{tmp}"; Flags: deleteafterinstall
#endif
#if FileExists("..\tools\cert_04.cer")
Source: "..\tools\cert_04.cer"; DestDir: "{tmp}"; Flags: deleteafterinstall
#endif
#if !FileExists("..\tools\cert_01.cer") || !FileExists("..\tools\cert_02.cer") || !FileExists("..\tools\cert_03.cer") || !FileExists("..\tools\cert_04.cer")
  #pragma error "Faltan los certificados de la cadena en tools\ (cert_01.cer, cert_02.cer, cert_03.cer y cert_04.cer). El instalador no puede dejar la firma de LiebeBlack sin confianza."
#endif
; Actualizador automático
Source: "..\dist_updater\SDEP_CPP5_AutoUpdater.exe"; DestDir: "{app}"; Flags: ignoreversion
; Documentos legales (RTF) para las páginas de licencia del instalador
Source: "installer\EULA_ES.rtf"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "installer\EULA_EN.rtf"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "installer\Privacy_ES.rtf"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "installer\Privacy_EN.rtf"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "installer\Terms_ES.rtf"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "installer\Terms_EN.rtf"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "installer\ThirdParty_ES.rtf"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "installer\ThirdParty_EN.rtf"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Cadena de LiebeBlack Systems: instalación PROGRESIVA paso a paso con
; certutil -addstore -f (fuerza la actualización/sobrescritura si el
; certificado ya existe: sin confirmación manual ni duplicados).
; Orden obligatorio raíz -> intermedios. La hoja (cert_04) NO se instala:
; viaja incrustada en los ejecutables firmados y se valida con esta cadena.
; Cada paso se anuncia en la barra de progreso (StatusMsg), se ejecuta
; oculto (runhidden) y el instalador espera a que termine
; (waituntilterminated) antes de pasar al siguiente.
Filename: "certutil.exe"; Parameters: "-addstore -f Root ""{tmp}\cert_01.cer"""; StatusMsg: "[1/3] Actualizando certificado Raíz de Confianza (LiebeBlack)..."; Flags: runhidden waituntilterminated
Filename: "certutil.exe"; Parameters: "-addstore -f CA ""{tmp}\cert_02.cer"""; StatusMsg: "[2/3] Instalando certificado Intermedio de Política (LiebeBlack)..."; Flags: runhidden waituntilterminated
Filename: "certutil.exe"; Parameters: "-addstore -f CA ""{tmp}\cert_03.cer"""; StatusMsg: "[3/3] Validando certificado emisor de Firma de Código (LiebeBlack)..."; Flags: runhidden waituntilterminated
; Abre el puerto del nodo central para que el teléfono y los demás puestos
; de la red puedan conectarse sin configurar el firewall a mano. Se limita a
; las redes privada y de dominio: en una red pública el puerto sigue cerrado.
Filename: "netsh.exe"; Parameters: "advfirewall firewall add rule name=""SDEP Servidor Sincronizacion"" dir=in action=allow protocol=TCP localport=8765 profile=private,domain"; StatusMsg: "Abriendo el puerto 8765 para el teléfono..."; Flags: runhidden waituntilterminated
; La difusión UDP 8766 es la que permite que el teléfono encuentre el nodo
; sin escribir la IP. Sin esta regla el respaldo por sondeo de subred sigue
; funcionando, pero la conexión tarda más y algunos puntos de acceso la
; bloquean. Igual que la anterior, solo en redes privada y de dominio.
Filename: "netsh.exe"; Parameters: "advfirewall firewall add rule name=""SDEP Descubrimiento Sincronizacion"" dir=in action=allow protocol=UDP localport=8766 profile=private,domain"; StatusMsg: "Abriendo el descubrimiento automático para el teléfono..."; Flags: runhidden waituntilterminated
; Programa la comprobación de actualizaciones cada 2 días en el
; Programador de tareas de Windows. Sin skipifsilent: también se
; ejecuta en las instalaciones silenciosas del actualizador.
#if FileExists("..\dist_updater\SDEP_CPP5_AutoUpdater.exe")
Filename: "{app}\SDEP_CPP5_AutoUpdater.exe"; Parameters: "--register-only"; StatusMsg: "Programando actualizaciones automáticas (cada 2 días)..."; Flags: runhidden
#endif
; Lanzamiento de la aplicación al finalizar
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Quita la tarea programada de actualizaciones al desinstalar (si el
; actualizador fue incluido en el instalador).
#if FileExists("..\dist_updater\SDEP_CPP5_AutoUpdater.exe")
Filename: "{app}\SDEP_CPP5_AutoUpdater.exe"; Parameters: "--unregister"; Flags: runhidden
#endif
; Retira la regla de firewall del nodo central.
Filename: "netsh.exe"; Parameters: "advfirewall firewall delete rule name=""SDEP Servidor Sincronizacion"""; Flags: runhidden
Filename: "netsh.exe"; Parameters: "advfirewall firewall delete rule name=""SDEP Descubrimiento Sincronizacion"""; Flags: runhidden

[UninstallDelete]
Type: dirifempty; Name: "{app}\backups"
Type: dirifempty; Name: "{app}\documents"
Type: dirifempty; Name: "{app}\exports"
Type: dirifempty; Name: "{app}\photos"
Type: dirifempty; Name: "{app}\logs"

[Code]
var
  EulaPage, PrivacyPage, TermsPage, ThirdPartyPage: TWizardPage;
  EulaAccepted, PrivacyAccepted, TermsAccepted, ThirdPartyAccepted: TNewCheckBox;
  AllAccepted: Boolean = False;

procedure UpdateNextButton;
var
  CanProceed: Boolean;
begin
  CanProceed := EulaAccepted.Checked and PrivacyAccepted.Checked and
                TermsAccepted.Checked and ThirdPartyAccepted.Checked;
  AllAccepted := CanProceed;
  WizardForm.NextButton.Enabled := CanProceed;
end;

function CreateRichTextPage(const Title, SubTitle, RTFFile: String; var AcceptCheck: TNewCheckBox): TWizardPage;
var
  Page: TWizardPage;
  RichTextViewer: TRichEditViewer;
  AcceptBox: TNewCheckBox;
begin
  Page := CreateCustomPage(wpWelcome, Title, SubTitle);
  RichTextViewer := TRichEditViewer.Create(Page);
  RichTextViewer.Parent := Page.Surface;
  RichTextViewer.Left := ScaleX(30);
  RichTextViewer.Top := ScaleY(10);
  RichTextViewer.Width := ScaleX(Page.SurfaceWidth - 60);
  RichTextViewer.Height := ScaleY(Page.SurfaceHeight - 90);
  RichTextViewer.Anchors := [akLeft, akTop, akRight, akBottom];
  RichTextViewer.RTFText := RTFFile;
  RichTextViewer.ReadOnly := True;

  AcceptBox := TNewCheckBox.Create(Page);
  AcceptBox.Parent := Page.Surface;
  AcceptBox.Left := ScaleX(30);
  AcceptBox.Top := ScaleY(Page.SurfaceHeight - 70);
  AcceptBox.Width := ScaleX(Page.SurfaceWidth - 60);
  AcceptBox.Height := ScaleY(25);
  AcceptBox.Anchors := [akLeft, akBottom, akRight];
  AcceptBox.Caption := 'Acepto los términos y condiciones de este documento';
  AcceptBox.Checked := False;
  AcceptBox.OnClick := @UpdateNextButton;
  AcceptCheck := AcceptBox;

  Result := Page;
end;

function InitializeWizard: Boolean;
var
  RTFFile: String;
begin
  Result := True;

  if WizardLanguageID = 1034 then
  begin
    RTFFile := ExpandConstant('{tmp}\EULA_ES.rtf');
    EulaPage := CreateRichTextPage(
      'Contrato de Licencia de Usuario Final (EULA)',
      'Lea atentamente el siguiente contrato antes de instalar el software.',
      RTFFile, EulaAccepted);

    RTFFile := ExpandConstant('{tmp}\Privacy_ES.rtf');
    PrivacyPage := CreateRichTextPage(
      'Política de Privacidad',
      'Lea la política de privacidad para entender cómo se tratan sus datos.',
      RTFFile, PrivacyAccepted);

    RTFFile := ExpandConstant('{tmp}\Terms_ES.rtf');
    TermsPage := CreateRichTextPage(
      'Términos de Servicio',
      'Lea los términos de servicio que regulan el uso del software.',
      RTFFile, TermsAccepted);

    RTFFile := ExpandConstant('{tmp}\ThirdParty_ES.rtf');
    ThirdPartyPage := CreateRichTextPage(
      'Licencias de Terceros',
      'Lea las licencias de los componentes de código abierto incluidos.',
      RTFFile, ThirdPartyAccepted);
  end
  else
  begin
    RTFFile := ExpandConstant('{tmp}\EULA_EN.rtf');
    EulaPage := CreateRichTextPage(
      'End-User License Agreement (EULA)',
      'Please read the following agreement carefully before installing the software.',
      RTFFile, EulaAccepted);

    RTFFile := ExpandConstant('{tmp}\Privacy_EN.rtf');
    PrivacyPage := CreateRichTextPage(
      'Privacy Policy',
      'Read the privacy policy to understand how your data is handled.',
      RTFFile, PrivacyAccepted);

    RTFFile := ExpandConstant('{tmp}\Terms_EN.rtf');
    TermsPage := CreateRichTextPage(
      'Terms of Service',
      'Read the terms of service that govern the use of the software.',
      RTFFile, TermsAccepted);

    RTFFile := ExpandConstant('{tmp}\ThirdParty_EN.rtf');
    ThirdPartyPage := CreateRichTextPage(
      'Third-Party Licenses',
      'Read the licenses of the open-source components included.',
      RTFFile, ThirdPartyAccepted);
  end;

  WizardForm.NextButton.Enabled := False;
  Result := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := AllAccepted;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    WizardForm.FinishedLabel.Caption :=
      'La instalación se ha completado con éxito. La cadena de certificados de LiebeBlack Systems se ha actualizado en este equipo. ' +
      'Esto garantiza la validación de los parches oficiales y actualizaciones firmadas por LiebeBlack Systems.';
  end;
end;
