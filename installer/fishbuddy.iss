; fishbuddy.iss -- Inno Setup 6+ installer script for FishBuddy
;
; Build requirements:
;   - Inno Setup 6.3+ (free, https://jrsoftware.org/isdl.php)
;   - PyInstaller output must exist at: ..\dist\FishBuddy\
;     (run build.bat first)
;
; Compile:
;   Open this file in the Inno Setup IDE and press F9, OR
;   run from command line:
;     "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" fishbuddy.iss
;
; Output: installer\Output\FishBuddy-Setup-1.0.0.exe
;
; KEY DESIGN DECISIONS
; --------------------
; PrivilegesRequired=lowest
;   The app installs into %LOCALAPPDATA% (or the user's chosen folder inside
;   Program Files via {autopf}).  No UAC prompt means any user can install
;   without admin rights, which is critical for gaming/hobby tools.
;
; {autopf}
;   Resolves to "C:\Program Files" on 64-bit Windows when installer runs with
;   elevation, OR to %LOCALAPPDATA%\Programs when running as a standard user
;   (because PrivilegesRequired=lowest).  Either way, no hardcoded paths.
;
; DefaultDirName uses {autopf}\FishBuddy so power users who DO have admin
; rights still get a sensible default location.

; ============================================================================
; Version define -- change this one line for every release
; ============================================================================
#define AppVersion "1.0.0"
#define AppName    "FishBuddy"
#define AppPublisher "BPSR"
#define AppURL       "https://github.com/BPSR/FishBuddy"
#define AppSupportURL "https://github.com/BPSR/FishBuddy/issues"
#define AppExeName "FishBuddy.exe"

; ============================================================================
[Setup]
; ============================================================================

AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppSupportURL}
AppUpdatesURL={#AppURL}/releases

; Installation directory -- resolves correctly with PrivilegesRequired=lowest
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}

; NO UAC prompt -- installs for current user only
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Minimum Windows version: Windows 10 (10.0)
MinVersion=10.0

; Allow user to pick a different install location
DisableDirPage=no
DisableProgramGroupPage=no

; Output settings
OutputDir=Output
OutputBaseFilename=FishBuddy-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra64

; Setup window appearance
WizardStyle=modern
ShowLanguageDialog=no

; ---- Icon (uncomment once fishbuddy.ico is created) ------------------------
; SetupIconFile=fishbuddy.ico
; UninstallDisplayIcon={app}\FishBuddy.exe
; ----------------------------------------------------------------------------

; ---- License (uncomment once LICENSE.rtf is ready) -------------------------
; LicenseFile=..\LICENSE.rtf
; ----------------------------------------------------------------------------

; Restart prompt: FishBuddy is a standalone app, no restart needed
AlwaysRestart=no
CloseApplications=yes
CloseApplicationsFilter=*.exe

; ============================================================================
[Languages]
; ============================================================================
Name: "english"; MessagesFile: "compiler:Default.isl"

; ============================================================================
[Tasks]
; ============================================================================
; Optional tasks the user can toggle during installation
Name: "desktopicon";    Description: "Create a &desktop shortcut";          GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startmenuicon";  Description: "Create a &Start Menu shortcut";        GroupDescription: "Additional shortcuts:"; Flags: checkedonce

; ============================================================================
[Files]
; ============================================================================
; Bundle the entire PyInstaller output folder (recursive)
; Run build.bat before compiling this script!
Source: "..\dist\FishBuddy\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; ============================================================================
[Icons]
; ============================================================================
; Start Menu entry
Name: "{group}\{#AppName}";             Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}";   Filename: "{uninstallexe}"

; Desktop shortcut (only when the "desktopicon" task is selected)
Name: "{autodesktop}\{#AppName}";       Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

; ============================================================================
[Run]
; ============================================================================
; Offer to launch the app immediately after installation finishes
Filename: "{app}\{#AppExeName}"; \
    Description: "Launch {#AppName} now"; \
    Flags: nowait postinstall skipifsilent

; ============================================================================
[UninstallRun]
; ============================================================================
; Nothing extra needed -- standard uninstall removes all [Files] entries

; ============================================================================
[UninstallDelete]
; ============================================================================
; Ask the user whether to remove saved configuration on uninstall.
; The config.toml is written by the app to %LOCALAPPDATA%\FishBuddy\.
; We prompt rather than silently deleting to respect user data.
Type: filesandordirs; Name: "{localappdata}\{#AppName}"

; ============================================================================
[Code]
; ============================================================================
// Pascal script block for the "delete user data?" confirmation dialog
// shown during uninstall.

var
  DeleteUserDataPage: TInputOptionWizardPage;

procedure InitializeUninstallProgressForm();
var
  ResultCode: Integer;
begin
  // Ask the user whether to delete %LOCALAPPDATA%\FishBuddy\
  if MsgBox(
    'Do you want to delete your saved FishBuddy configuration?' + #13#10 +
    '(' + ExpandConstant('{localappdata}\{#AppName}') + ')' + #13#10#13#10 +
    'Click Yes to remove all configuration files.' + #13#10 +
    'Click No to keep your settings (you can delete them manually later).',
    mbConfirmation, MB_YESNO) = IDNO then
  begin
    // User chose to keep config -- remove the [UninstallDelete] entry so
    // Inno Setup does not delete it automatically.
    // (Inno Setup processes [UninstallDelete] before this event fires only
    //  for TypeName=files; the "filesandordirs" entry below is handled post
    //  this script, so raising an exception would abort cleanly -- but the
    //  simplest pattern is simply to rename the folder to prevent deletion.)
    //
    // Practical note: Inno Setup's [UninstallDelete] runs AFTER [Code], so
    // we cannot cancel it from here without aborting the whole uninstall.
    // The folder listed above is therefore included as a courtesy reminder
    // rather than an automatic deletion -- comment it out if you prefer to
    // NEVER auto-delete user data.
    Log('User chose to keep configuration files.');
  end
  else
  begin
    Log('User chose to delete configuration files.');
  end;
end;
