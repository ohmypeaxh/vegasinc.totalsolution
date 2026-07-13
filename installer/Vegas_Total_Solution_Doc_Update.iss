#define MyAppName "Vegas Total Solution Doc"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.1"
#endif
#define MyAppPublisher "Vegas Inc."
#define MyAppExeName "Vegas_Total_Solution_Doc.exe"
#define MyAppMutex "VegasTotalSolutionDoc.SingleInstance"
#define BaseUninstallKey "Software\Microsoft\Windows\CurrentVersion\Uninstall\{1DAD13F1-148D-4B95-8D15-F4FEBD49676A}_is1"

[Setup]
AppId={{7C9D1F72-4A31-4E54-B61C-8F2475B5E162}
AppName={#MyAppName} Lightweight Update
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} Cumulative Update {#MyAppVersion}
AppPublisher={#MyAppPublisher}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Cumulative Update
VersionInfoProductName={#MyAppName} Cumulative Update
VersionInfoProductVersion={#MyAppVersion}
DefaultDirName={code:GetBaseInstallDir}
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir=..\dist\update
OutputBaseFilename=Vegas_Total_Solution_Doc_Update
SetupIconFile=..\assets\app.ico
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
Uninstallable=no
CreateUninstallRegKey=no

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\Vegas_Total_Solution_Doc\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Vegas_Total_Solution_Doc\_internal\vegas_doc\resources\*"; DestDir: "{app}\_internal\vegas_doc\resources"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: files; Name: "{app}\{#MyAppExeName}"

[Registry]
Root: HKLM64; Subkey: "Software\Vegas Inc\Vegas Total Solution Doc"; ValueType: string; ValueName: "CurrentVersion"; ValueData: "{#MyAppVersion}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{#MyAppName} 실행"; Flags: nowait postinstall skipifsilent

[Code]
function FindBaseInstallDir(var InstallDir: String): Boolean;
var
  DefaultInstallDir: String;
begin
  Result := RegQueryStringValue(HKLM64, '{#BaseUninstallKey}', 'InstallLocation', InstallDir);
  if (not Result) or (not FileExists(AddBackslash(InstallDir) + '{#MyAppExeName}')) then
  begin
    Result := RegQueryStringValue(HKLM32, '{#BaseUninstallKey}', 'InstallLocation', InstallDir);
  end;

  if Result and FileExists(AddBackslash(InstallDir) + '{#MyAppExeName}') then
    Exit;

  DefaultInstallDir := ExpandConstant('{autopf}\Vegas Inc\Vegas Total Solution Doc');
  if FileExists(AddBackslash(DefaultInstallDir) + '{#MyAppExeName}') then
  begin
    InstallDir := DefaultInstallDir;
    Result := True;
  end
  else
    Result := False;
end;

function GetBaseInstallDir(Param: String): String;
begin
  if not FindBaseInstallDir(Result) then
    Result := ExpandConstant('{autopf}\Vegas Inc\Vegas Total Solution Doc');
end;

function InitializeSetup(): Boolean;
var
  InstallDir: String;
begin
  Result := FindBaseInstallDir(InstallDir);
  if not Result then
  begin
    MsgBox(
      'Vegas Total Solution Doc 기본 설치본을 찾지 못했습니다.' + #13#10 +
      '먼저 전체 설치파일(Vegas_Total_Solution_Doc_Setup.exe)을 설치해 주세요.',
      mbError,
      MB_OK
    );
  end;
end;
