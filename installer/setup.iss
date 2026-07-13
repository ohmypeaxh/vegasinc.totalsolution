
#define MyAppName "GreenMetal Automation Suite"
#define MyAppVersion "0.1.2"
#define MyAppExeName "GreenMetalAutomationSuite.exe"

[Setup]
AppId={{4D3D5861-89C1-4877-B35F-D9D273F9F32A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\GreenMetal Automation Suite
DefaultGroupName={#MyAppName}
OutputDir=..\release
OutputBaseFilename=GreenMetal_Automation_Suite_Setup
SetupIconFile=..\assets\app.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 바로가기를 만드시겠습니까?"; GroupDescription: "추가 아이콘:"; Flags: unchecked

[Files]
Source: "..\dist\GreenMetalAutomationSuite.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "프로그램 실행"; Flags: nowait postinstall skipifsilent
