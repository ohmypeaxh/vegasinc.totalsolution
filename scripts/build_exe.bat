@echo off
setlocal
cd /d "%~dp0.."
python -m PyInstaller --noconfirm --clean Vegas_Total_Solution_Doc.spec
if errorlevel 1 exit /b %errorlevel%
