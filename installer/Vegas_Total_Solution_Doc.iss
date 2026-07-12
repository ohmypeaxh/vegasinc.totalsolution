#ifndef SourceDir
  #define SourceDir "..\dist\Vegas_Total_Solution_Doc"
#endif
#ifndef OutputBase
  #define OutputBase "Vegas_Total_Solution_Doc_Setup"
#endif

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
OutputBaseFilename={#OutputBase}
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.pdb,*.map,__pycache__\*,tests\*,test\*,.pytest_cache\*"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
