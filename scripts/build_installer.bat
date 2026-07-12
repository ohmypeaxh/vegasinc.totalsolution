@echo off
setlocal
cd /d "%~dp0.."
if not exist "dist\Vegas_Total_Solution_Doc\Vegas_Total_Solution_Doc.exe" exit /b 1
if not exist "dist\installer" mkdir "dist\installer"
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" exit /b 1
"%ISCC%" "installer\Vegas_Total_Solution_Doc.iss"
if errorlevel 1 exit /b %errorlevel%
