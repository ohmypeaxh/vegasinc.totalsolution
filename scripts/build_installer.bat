@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo [1/3] Verifying the PyInstaller distribution...
if not exist "dist\Vegas_Total_Solution_Doc\Vegas_Total_Solution_Doc.exe" (
  echo ERROR: Build the executable first with scripts\build_exe.bat.
  exit /b 1
)

echo [2/3] Locating Inno Setup 6...
if defined ISCC_PATH set "ISCC=%ISCC_PATH%"
if not defined ISCC set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo ERROR: Inno Setup 6 was not found. Set ISCC_PATH to ISCC.exe.
  exit /b 1
)

if not exist "dist\installer" mkdir "dist\installer"
for /f "delims=" %%V in ('.build-venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'src'); from vegas_doc.version import BUILD_INFO; print(BUILD_INFO.version)"') do set "APP_VERSION=%%V"
if not defined APP_VERSION (
  echo ERROR: Could not read the application version.
  exit /b 1
)

echo [3/3] Compiling Vegas Total Solution Doc %APP_VERSION% installer...
"%ISCC%" /DMyAppVersion=%APP_VERSION% "installer\Vegas_Total_Solution_Doc.iss" || exit /b 1
if not exist "dist\installer\Vegas_Total_Solution_Doc_Setup.exe" (
  echo ERROR: Inno Setup did not create the expected installer.
  exit /b 1
)
echo SUCCESS: dist\installer\Vegas_Total_Solution_Doc_Setup.exe
exit /b 0
