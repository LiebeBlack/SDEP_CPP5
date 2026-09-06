; Instalador de "Sistema de Gestión de Personal" / SDEP_CPP5
;
; Compilación local (sin firmar, desde la raíz del proyecto):
;   ISCC.exe /DMyAppVersion=2.79 installer\setup.iss
;
; Compilación firmada (GitHub Actions - .github/workflows/release.yml):
;   ISCC.exe /DMyAppVersion=1.0.0 /DMyAppName=SDEP_CPP5 ^
;           /DMyAppExeName=SDEP_CPP5.exe /DMyOutputBaseFilename=Instalador_SDEP_CPP5 ^
;           /DSignToolPath="C:\...\signtool.exe" /DCertPath="C:\...\cert.pfx" ^
;           /DCertPassword="..." installer\setup.iss
;
; Certificado público (MiCertificadoPublico.cer):
;   Se copia a {tmp} y se importa en Cert:\LocalMachine\Root con un comando
;   de PowerShell oculto durante la instalación, de modo que el equipo
;   confíe en la autoridad autofirmada del sistema.
; Certificado privado (MiCertificadoPrivado.pfx):
;   NO viaja dentro del instalador. Solo se usa para FIRMAR el ejecutable
;   y el instalador en el CI, donde el PFX se recupera desde el secreto
;   CODE_SIGN_CERT_BASE64 y se elimina del runner al terminar.

#ifndef MyAppVersion
  #define MyAppVersion "2.79"
#endif

#ifndef MyAppName
  #define MyAppName "Sistema de Gestión de Personal"
#endif

#ifndef MyAppExeName
  #define MyAppExeName "SistemaGestionPersonal.exe"
#endif

#ifndef MyOutputBaseFilename
  #define MyOutputBaseFilename "SistemaGestionPersonal-Setup-{#MyAppVersion}"
#endif

; Nombre de la carpeta de salida de PyInstaller (spec/app.spec)
#define MyDistDir "SistemaGestionPersonal"
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
LicenseFile=..\LICENSE
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
; La importación al almacén Cert:\LocalMachine\Root exige elevación:
; el instalador siempre pide privilegios de administrador.
PrivilegesRequired=admin
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}

; Firma del instalador (y del desinstalador) cuando el CI pasa los
; parámetros por línea de comandos. Sin esos defines, la compilación
; local genera un instalador sin firmar sin ningún cambio.
;   $f = ruta del instalador generado (entre comillas)
;   $q = carácter de comilla
#ifdef SignToolPath
SignTool=GitHubSign $q{#SignToolPath}$q sign /f $q{#CertPath}$q /p $q{#CertPassword}$q /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 $f
SignedUninstaller=yes
#endif

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Certificado público: se copia a {tmp} y se elimina al terminar la instalación.
; El .cer es PÚBLICO y debe versionarse (lo empaqueta el instalador). El
; guard FileExists evita que una compilación sin el archivo falle: si no
; está presente, el instalador simplemente no importa el certificado.
#if FileExists("..\tools\MiCertificadoPublico.cer")
Source: "..\tools\MiCertificadoPublico.cer"; DestDir: "{tmp}"; Flags: deleteafterinstall
#endif

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Importa el certificado público al almacén raíz de la máquina
; (Cert:\LocalMachine\Root) para que el sistema confíe en él.
; Se ejecuta ANTES del lanzamiento de la aplicación y sin ventana.
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Import-Certificate -FilePath '{tmp}\MiCertificadoPublico.cer' -CertStoreLocation Cert:\LocalMachine\Root"""; Flags: runhidden; StatusMsg: "Instalando certificado de confianza..."
; Lanzamiento de la aplicación al finalizar
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Elimina la carpeta de datos creada por la versión portable antigua
; (junto al ejecutable). Los datos del usuario en %LOCALAPPDATA% se
; conservan para no perder información al desinstalar.
Type: dirifempty; Name: "{app}\backups"
Type: dirifempty; Name: "{app}\documents"
Type: dirifempty; Name: "{app}\exports"
Type: dirifempty; Name: "{app}\photos"
Type: dirifempty; Name: "{app}\logs"