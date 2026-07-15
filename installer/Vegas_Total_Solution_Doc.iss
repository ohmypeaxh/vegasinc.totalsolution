#define MyAppName "Vegas Total Solution Doc"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.3"
#endif
#define MyAppPublisher "Vegas Inc."
#define MyAppExeName "Vegas_Total_Solution_Doc.exe"
#define MyAppMutex "VegasTotalSolutionDoc.SingleInstance"

[Setup]
AppId={{1DAD13F1-148D-4B95-8D15-F4FEBD49676A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
DefaultDirName={autopf}\Vegas Inc\Vegas Total Solution Doc
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=Vegas_Total_Solution_Doc_Setup
SetupIconFile=..\assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
AppMutex={#MyAppMutex}

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\Vegas_Total_Solution_Doc\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Remove runtime files from older full installations before copying the new build.
; User settings, credentials, projects, and generated documents live outside {app}.
[InstallDelete]
Type: files; Name: "{app}\{#MyAppExeName}"
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\plugins"
Type: filesandordirs; Name: "{app}\src"

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 바로가기를 만드시겠습니까?"; GroupDescription: "추가 아이콘:"; Flags: unchecked

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{#MyAppName} 실행"; Flags: nowait postinstall skipifsilent
