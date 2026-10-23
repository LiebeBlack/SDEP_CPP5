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
; Documentos legales (RTF) de las páginas de licencia del asistente.
; dontcopy: no se copian durante la instalación normal; el propio asistente
; los extrae a {tmp} con ExtractTemporaryFile justo antes de mostrarlos (con
; deleteafterinstall todavía no existirían al crearse las páginas).
; Van al principio de la sección porque con SolidCompression extraer un
; archivo obliga a descomprimir todo lo anterior.
Source: "EULA_ES.rtf"; Flags: dontcopy noencryption
Source: "EULA_EN.rtf"; Flags: dontcopy noencryption
Source: "Privacy_ES.rtf"; Flags: dontcopy noencryption
Source: "Privacy_EN.rtf"; Flags: dontcopy noencryption
Source: "Terms_ES.rtf"; Flags: dontcopy noencryption
Source: "Terms_EN.rtf"; Flags: dontcopy noencryption
Source: "ThirdParty_ES.rtf"; Flags: dontcopy noencryption
Source: "ThirdParty_EN.rtf"; Flags: dontcopy noencryption

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
  EulaViewer, PrivacyViewer, TermsViewer, ThirdPartyViewer: TRichEditViewer;
  CurrentPageID: Integer;

// Indica si la página indicada puede darse por aceptada. Las páginas que no
// son de aceptación (bienvenida, carpeta de destino, etc.) no bloquean.
function PageAccepted(PageID: Integer): Boolean;
begin
  if PageID = EulaPage.ID then Result := EulaAccepted.Checked
  else if PageID = PrivacyPage.ID then Result := PrivacyAccepted.Checked
  else if PageID = TermsPage.ID then Result := TermsAccepted.Checked
  else if PageID = ThirdPartyPage.ID then Result := ThirdPartyAccepted.Checked
  else Result := True;
end;

// El botón Siguiente solo se habilita cuando la casilla de la página ACTUAL
// está marcada. Antes se exigían las cuatro a la vez y, como cada casilla vive
// en una página distinta, el asistente quedaba bloqueado en la primera.
procedure SyncNextButton;
begin
  WizardForm.NextButton.Enabled := PageAccepted(CurrentPageID);
end;

// La rueda del ratón y las flechas del teclado solo llegan a un control
// mientras éste tiene el foco. Este procedimiento se lo devuelve al visor de
// la página legal activa, de modo que el documento se pueda desplazar en
// cualquier momento sin tener que hacer clic dentro del texto antes.
procedure EnfocarVisor(Visor: TRichEditViewer);
begin
  if Visor.CanFocus then
    WizardForm.ActiveControl := Visor;
end;

procedure EnfocarPaginaLegal;
begin
  if CurrentPageID = EulaPage.ID then EnfocarVisor(EulaViewer)
  else if CurrentPageID = PrivacyPage.ID then EnfocarVisor(PrivacyViewer)
  else if CurrentPageID = TermsPage.ID then EnfocarVisor(TermsViewer)
  else if CurrentPageID = ThirdPartyPage.ID then EnfocarVisor(ThirdPartyViewer);
end;

procedure UpdateNextButton(Sender: TObject);
begin
  SyncNextButton;
  // Al marcar la casilla el foco pasa a ella y la rueda deja de desplazar el
  // texto: se le devuelve al visor para seguir leyendo con la rueda del ratón.
  EnfocarPaginaLegal;
end;

// Crea una página de documento legal con su visor RTF desplazable (barra
// vertical visible y rueda del ratón) y su casilla de aceptación, que es la
// que habilita el botón Siguiente de ESA página.
//   AfterID      : página tras la que se inserta; encadena el orden real de
//                  las cuatro páginas legales en lugar de insertarlas todas
//                  inmediatamente después de la bienvenida.
//   AcceptCaption: texto de la casilla, en el idioma del asistente.
function CreateRichTextPage(AfterID: Integer; const Title, SubTitle,
  RTFFileName, AcceptCaption: String; var AcceptCheck: TNewCheckBox;
  var AcceptViewer: TRichEditViewer): TWizardPage;
var
  Page: TWizardPage;
  RichTextViewer: TRichEditViewer;
  AcceptBox: TNewCheckBox;
  RTFData: AnsiString;
begin
  Page := CreateCustomPage(AfterID, Title, SubTitle);
  RichTextViewer := TRichEditViewer.Create(Page);
  RichTextViewer.Parent := Page.Surface;
  RichTextViewer.Anchors := [akLeft, akTop, akRight, akBottom];
  RichTextViewer.Left := ScaleX(30);
  RichTextViewer.Top := ScaleY(10);
  // SurfaceWidth/SurfaceHeight ya están en píxeles reales (crecen con la
  // escala de Windows). ScaleX/ScaleY solo debe aplicarse a los MARGENES:
  // escalar la superficie entera duplicaba el factor DPI y el visor se salía
  // por la derecha al 125 %/150 %, cortando el texto legal por la derecha.
  RichTextViewer.Width := Page.SurfaceWidth - ScaleX(60);
  RichTextViewer.Height := Page.SurfaceHeight - ScaleY(90);
  // Documento legal largo: se ajusta al ancho del visor y se desplaza con la
  // barra vertical, que así queda siempre visible. Antes iba con el ajuste de
  // línea desactivado y sin barra horizontal, de modo que los párrafos largos
  // se cortaban por la derecha.
  RichTextViewer.WordWrap := True;
  RichTextViewer.ScrollBars := ssVertical;
  RichTextViewer.ReadOnly := True;

  // El RTF viaja con dontcopy: se extrae a {tmp} y su contenido se carga como
  // ÚLTIMO paso del visor. Asignar la ruta a RTFText mostraba basura, y toda
  // propiedad que recree la ventana DESPUÉS de RTFText (ScrollBars, WordWrap)
  // borraría el formato del documento cargado.
  ExtractTemporaryFile(RTFFileName);
  if LoadStringFromFile(ExpandConstant('{tmp}\' + RTFFileName), RTFData) then
    RichTextViewer.RTFText := RTFData;
  AcceptViewer := RichTextViewer;

  AcceptBox := TNewCheckBox.Create(Page);
  AcceptBox.Parent := Page.Surface;
  AcceptBox.Anchors := [akLeft, akBottom, akRight];
  // Mismos márgenes que el visor, con la superficie ya en píxeles: antes la
  // casilla se calculaba con ScaleY sobre píxeles y salía fuera de la página.
  AcceptBox.Left := ScaleX(30);
  AcceptBox.Top := Page.SurfaceHeight - ScaleY(70);
  AcceptBox.Width := Page.SurfaceWidth - ScaleX(60);
  AcceptBox.Height := ScaleY(25);
  AcceptBox.Caption := AcceptCaption;
  AcceptBox.Checked := False;
  AcceptBox.OnClick := @UpdateNextButton;
  AcceptCheck := AcceptBox;

  Result := Page;
end;

// ActiveLanguage devuelve el Name declarado en [Languages] ('spanish' o
// 'english'); WizardLanguageID no existe en Inno Setup.
procedure InitializeWizard;
begin
  // Las cuatro páginas se ENCADENAN por AfterID (EULA -> Privacidad ->
  // Términos -> Terceros). Usar wpWelcome en las cuatro hacía que el
  // asistente las insertara todas justo tras la bienvenida, invirtiendo el
  // orden de lectura de los documentos legales.
  if ActiveLanguage = 'spanish' then
  begin
    EulaPage := CreateRichTextPage(wpWelcome,
      'Contrato de Licencia de Usuario Final (EULA)',
      'Lea atentamente el siguiente contrato antes de instalar el software.',
      'EULA_ES.rtf',
      'Acepto el contrato de licencia de usuario final (EULA)',
      EulaAccepted, EulaViewer);

    PrivacyPage := CreateRichTextPage(EulaPage.ID,
      'Política de Privacidad',
      'Lea la política de privacidad para entender cómo se tratan sus datos.',
      'Privacy_ES.rtf',
      'Acepto la política de privacidad',
      PrivacyAccepted, PrivacyViewer);

    TermsPage := CreateRichTextPage(PrivacyPage.ID,
      'Términos de Servicio',
      'Lea los términos de servicio que regulan el uso del software.',
      'Terms_ES.rtf',
      'Acepto los términos de servicio',
      TermsAccepted, TermsViewer);

    ThirdPartyPage := CreateRichTextPage(TermsPage.ID,
      'Licencias de Terceros',
      'Lea las licencias de los componentes de código abierto incluidos.',
      'ThirdParty_ES.rtf',
      'Acepto las licencias de los componentes de terceros',
      ThirdPartyAccepted, ThirdPartyViewer);
  end
  else
  begin
    EulaPage := CreateRichTextPage(wpWelcome,
      'End-User License Agreement (EULA)',
      'Please read the following agreement carefully before installing the software.',
      'EULA_EN.rtf',
      'I accept the end-user license agreement (EULA)',
      EulaAccepted, EulaViewer);

    PrivacyPage := CreateRichTextPage(EulaPage.ID,
      'Privacy Policy',
      'Read the privacy policy to understand how your data is handled.',
      'Privacy_EN.rtf',
      'I accept the privacy policy',
      PrivacyAccepted, PrivacyViewer);

    TermsPage := CreateRichTextPage(PrivacyPage.ID,
      'Terms of Service',
      'Read the terms of service that govern the use of the software.',
      'Terms_EN.rtf',
      'I accept the terms of service',
      TermsAccepted, TermsViewer);

    ThirdPartyPage := CreateRichTextPage(TermsPage.ID,
      'Third-Party Licenses',
      'Read the licenses of the open-source components included.',
      'ThirdParty_EN.rtf',
      'I accept the third-party licenses',
      ThirdPartyAccepted, ThirdPartyViewer);
  end;

  SyncNextButton;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  CurrentPageID := CurPageID;
  SyncNextButton;
  // El visor RTF solo recibe la rueda del ratón (y las flechas) si tiene el
  // foco. Inno Setup dispara este evento DESPUÉS de mostrar la página, que es
  // el momento correcto para enfocarla: así la rueda desplaza el documento
  // legal en cuanto aparece, sin necesidad de hacer clic dentro del texto.
  // No se usa SetFocus: ese método no está expuesto en el Pascal Script de
  // Inno Setup y no compilaría; WizardForm.ActiveControl sí lo está.
  EnfocarPaginaLegal;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := PageAccepted(CurPageID);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Texto final en el idioma del asistente: antes se escribía siempre en
    // español, también cuando se instalaba en inglés.
    if ActiveLanguage = 'spanish' then
      WizardForm.FinishedLabel.Caption :=
        'La instalación se ha completado con éxito. La cadena de certificados de LiebeBlack Systems se ha actualizado en este equipo. ' +
        'Esto garantiza la validación de los parches oficiales y de las actualizaciones firmadas por LiebeBlack Systems.'
    else
      WizardForm.FinishedLabel.Caption :=
        'Setup has completed successfully. The LiebeBlack Systems certificate chain has been updated on this computer. ' +
        'This ensures the validation of official patches and updates signed by LiebeBlack Systems.';
  end;
end;
