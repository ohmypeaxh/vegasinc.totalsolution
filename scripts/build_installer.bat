@echo off
setlocal
cd /d "%~dp0.."
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" echo Inno Setup 6 not found. && exit /b 1
"%ISCC%" installer\Vegas_Total_Solution_Doc.iss || exit /b 1
if not exist dist\installer\Vegas_Total_Solution_Doc_Setup.exe exit /b 1
