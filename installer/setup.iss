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
; La instalación de la cadena en Cert:\LocalMachine\Root y
; Cert:\LocalMachine\CA (confianza de la MÁQUINA, para todos los usuarios)
; exige elevación: el instalador siempre pide privilegios de administrador.
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
; Cadena de certificados de LiebeBlack Systems: se copian a {tmp} y se
; eliminan al terminar la instalación (deleteafterinstall). Los .cer son
; PÚBLICOS y deben versionarse. El #pragma error hace FALLAR LA COMPILACIÓN
; si falta alguno: es preferible a distribuir un instalador que deja la
; firma de LiebeBlack sin confianza en los equipos cliente.
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

[Code]
// Notificación final: informa que la cadena de certificados de LiebeBlack
// Systems quedó actualizada en este equipo (garantiza que Windows valide
// las firmas digitales de los parches oficiales y actualizaciones).
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    WizardForm.FinishedLabel.Caption :=
      'La cadena de certificados de LiebeBlack Systems se ha actualizado con éxito en este equipo. ' +
      'Esto garantiza la validación de los parches oficiales y actualizaciones firmadas por LiebeBlack Systems.';
  end;
end;
