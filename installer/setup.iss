; Instalador de "Sistema de Gestión de Personal" / SDEP_CPP5
;
; Compilación local (sin firmar, desde la raíz del proyecto):
;   ISCC.exe /DMyAppVersion=2.79 installer\setup.iss
;
; Compilación firmada (GitHub Actions - .github/workflows/release.yml):
;   ISCC.exe /DMyAppVersion=1.0.0 /DMyVersionInfo=1.0.0 /DMyAppName=SDEP_CPP5 ^
;           /DMyAppExeName=SDEP_CPP5.exe ^
;           /DMyOutputBaseFilename=SistemaGestionPersonal-Setup-1.0.0 ^
;           /DConFirmaCI=1 ^
;           /SGitHubSign="$qC:\...\signtool.exe$q sign /sha1 <huella> ^
;           /f $qC:\...\cert.pfx$q /p <contraseña> /fd SHA256 ^
;           /tr http://timestamp.digicert.com /td SHA256 $f" installer\setup.iss
;
; Certificado público (MiCertificadoPublico.cer):
;   Se copia a {tmp} y se importa en Cert:\LocalMachine\Root con un comando
;   de PowerShell oculto durante la instalación, de modo que el equipo
;   confíe en la autoridad autofirmada del sistema.
; Certificado privado (MiCertificadoPrivado.pfx):
;   NO viaja dentro del instalador. Solo se usa para FIRMAR el ejecutable
;   y el instalador en el CI, donde el PFX se recupera desde el secreto
;   PFX_BASE64 y se elimina del runner al terminar.

#ifndef MyAppVersion
  #define MyAppVersion "2.79"
#endif

; VersionInfoVersion requiere formato #.#.# o #.#.#.# (Inno Setup).
; MyAppVersion puede ser "X.Y" (2 partes, desde el archivo VERSION).
; El workflow de Release Firmada puede pasar MyVersionInfo ya normalizado.
; Sin él, MyAppVersion se rellena hasta un formato valido (min. 3 partes).
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

; OJO: la sintaxis {#...} NO se expande dentro del valor de un #define
; (quedaría literal en el nombre, p.ej. "...-Setup-{#MyAppVersion}.exe").
; Se usa concatenación ISPP para incrustar la versión en el nombre.
#ifndef MyOutputBaseFilename
  #define MyOutputBaseFilename "SistemaGestionPersonal-Setup-" + MyAppVersion
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
VersionInfoVersion={#MyVersionInfo}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}

; Firma del instalador (y del desinstalador) cuando el CI está compilando.
;   - La directiva SignTool de Inno Setup NO admite el comando inline: exige
;     un Sign Tool NOMBRE registrado antes (opción /S de ISCC o el IDE). El
;     workflow registra 'GitHubSign' con /S"GitHubSign=..." y define
;     ConFirmaCI (ver .github/workflows/release.yml); aquí solo se referencia
;     por nombre.
;   - Sin ese registro (compilación local sin /S ni ConFirmaCI) no se firma:
;     se genera un instalador sin firmar sin ningún cambio.
;   - La definición del tool fija el certificado con /sha1 (huella hoja) o /a
;     como fallback: el PFX lleva la cadena completa y VARIOS certificados
;     resultan "aptos para firmar"; sin selección explícita signtool falla
;     con "Multiple certificates were found that meet all the given criteria".
;   - Placeholders de Inno (en la definición del tool): $f = archivo a firmar
;     (entre comillas), $q = comilla, $p = parámetros de la directiva.
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
Source: "..\dist\{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Certificado público: se copia a {tmp} y se elimina al terminar la instalación.
; El .cer es PÚBLICO y debe versionarse (lo empaqueta el instalador). El
; guard FileExists evita que una compilación sin el archivo falle: si no
; está presente, el instalador simplemente no importa el certificado.
#if FileExists("..\tools\MiCertificadoPublico.cer")
Source: "..\tools\MiCertificadoPublico.cer"; DestDir: "{tmp}"; Flags: deleteafterinstall
#endif
; Actualizador automático: se incluye en el instalador y se programa en
; el Programador de tareas de Windows para ejecutarse cada 2 días.
; La guarda FileExists permite compilar sin el .exe (el instalador
; simplemente no incluye la actualización automática en ese caso).
#if FileExists("..\dist_updater\SDEP_CPP5_AutoUpdater.exe")
Source: "..\dist_updater\SDEP_CPP5_AutoUpdater.exe"; DestDir: "{app}"; Flags: ignoreversion
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

[UninstallDelete]
; Elimina la carpeta de datos creada por la versión portable antigua
; (junto al ejecutable). Los datos del usuario en %LOCALAPPDATA% se
; conservan para no perder información al desinstalar.
Type: dirifempty; Name: "{app}\backups"
Type: dirifempty; Name: "{app}\documents"
Type: dirifempty; Name: "{app}\exports"
Type: dirifempty; Name: "{app}\photos"
Type: dirifempty; Name: "{app}\logs"