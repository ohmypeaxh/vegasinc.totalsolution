@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo [1/4] Verifying the packaged base runtime...
if not exist "dist\Vegas_Total_Solution_Doc\Vegas_Total_Solution_Doc.exe" (
  echo ERROR: Build the application first with scripts\build_exe.bat.
  exit /b 1
)
if not exist "dist\Vegas_Total_Solution_Doc\_internal\vegas_doc\resources" (
  echo ERROR: Packaged Vegas resource files are missing.
  exit /b 1
)

echo [2/4] Locating Python and Inno Setup 6...
if defined PYTHON_EXE (
  set "UPDATE_PYTHON=%PYTHON_EXE%"
) else if exist ".build-venv\Scripts\python.exe" (
  set "UPDATE_PYTHON=%CD%\.build-venv\Scripts\python.exe"
) else (
  set "UPDATE_PYTHON=python"
)
"%UPDATE_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" || (
  echo ERROR: Python 3.12 is required.
  exit /b 1
)

if defined ISCC_PATH set "ISCC=%ISCC_PATH%"
if not defined ISCC set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%CD%\.tools\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo ERROR: Inno Setup 6 was not found. Set ISCC_PATH to ISCC.exe.
  exit /b 1
)

for /f "delims=" %%V in ('%UPDATE_PYTHON% -c "import sys; sys.path.insert(0, 'src'); from vegas_doc.version import BUILD_INFO; print(BUILD_INFO.version)"') do set "APP_VERSION=%%V"
if not defined APP_VERSION (
  echo ERROR: Could not read the application version.
  exit /b 1
)

echo [3/4] Compiling cumulative lightweight update %APP_VERSION%...
if not exist "dist\update" mkdir "dist\update"
if exist "dist\update\Vegas_Total_Solution_Doc_Update.exe" del /q "dist\update\Vegas_Total_Solution_Doc_Update.exe"
"%ISCC%" /DMyAppVersion=%APP_VERSION% "installer\Vegas_Total_Solution_Doc_Update.iss" || exit /b 1

echo [4/4] Generating checksums and update manifest...
"%UPDATE_PYTHON%" scripts\generate_update_metadata.py || exit /b 1
if not exist "dist\update\Vegas_Total_Solution_Doc_Update.exe" (
  echo ERROR: Lightweight update executable was not created.
  exit /b 1
)
echo SUCCESS: dist\update\Vegas_Total_Solution_Doc_Update.exe
exit /b 0
