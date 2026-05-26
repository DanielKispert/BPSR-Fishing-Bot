; bpsr-fishing-bot.iss -- Inno Setup 6+ installer for BPSR Fishing Bot
; Prerequisites: run build.bat first to produce ..\dist\BPSR-Fishing-Bot\
; Compile: open in Inno Setup IDE and press F9, or: ISCC.exe bpsr-fishing-bot.iss

#define AppVersion "0.1.1"
#define AppName    "BPSR Fishing Bot"
#define AppPublisher "https://github.com/DanielKispert/"
#define AppURL       "https://github.com/DanielKispert/BPSR-Fishing-Bot"
#define AppSupportURL "https://github.com/DanielKispert/BPSR-Fishing-Bot/issues"
#define AppExeName "BPSR-Fishing-Bot.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppSupportURL}
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
MinVersion=10.0
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=Output
OutputBaseFilename=BPSR-Fishing-Bot-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra64
WizardStyle=modern
ShowLanguageDialog=no
; SetupIconFile=bpsr-fishing-bot.ico
; UninstallDisplayIcon={app}\BPSR-Fishing-Bot.exe
; LicenseFile=..\LICENSE.rtf
AlwaysRestart=no
CloseApplications=yes
CloseApplicationsFilter=BPSR-Fishing-Bot.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";   Description: "Create a &desktop shortcut";    GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startmenuicon"; Description: "Create a &Start Menu shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
Source: "..\dist\BPSR-Fishing-Bot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox(
    'Delete your saved BPSR Fishing Bot settings?' + #13#10 +
      '(' + ExpandConstant('{localappdata}\{#AppName}\config.toml') + ')' + #13#10#13#10 +
      'Yes = remove settings. No = keep them.',
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{localappdata}\{#AppName}'), True, True, True);
    end;
  end;
end;
