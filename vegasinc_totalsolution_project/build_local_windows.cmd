
@echo off
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller GreenMetalAutomationSuite.spec
if errorlevel 1 pause & exit /b 1

set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" (
  echo Inno Setup 6 is required.
  pause
  exit /b 1
)
"%ISCC%" installer\setup.iss
pause
