#define MyAppName "Vegas Total Solution Doc"
#define MyAppVersion "0.1.0"
#define MyAppExeName "Vegas_Total_Solution_Doc.exe"

[Setup]
AppId={{1DAD13F1-148D-4B95-8D15-F4FEBD49676A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Vegas Total Solution Doc
DefaultGroupName={#MyAppName}
OutputDir=..\dist\installer
OutputBaseFilename=Vegas_Total_Solution_Doc_Setup
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\Vegas_Total_Solution_Doc\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
