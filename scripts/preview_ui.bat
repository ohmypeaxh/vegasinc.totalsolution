@echo off
setlocal
cd /d "%~dp0.."
set QT_QPA_PLATFORM=offscreen
set VEGAS_CLOVA_INVOKE_URL=
set VEGAS_CLOVA_SECRET_KEY=
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\generate_ui_previews.py
) else (
  py -3.12 scripts\generate_ui_previews.py
)
if errorlevel 1 exit /b %errorlevel%
echo UI previews generated in artifacts\ui-previews
