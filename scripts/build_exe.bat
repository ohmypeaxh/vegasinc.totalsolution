@echo off
setlocal
cd /d "%~dp0.."
python -m PyInstaller --noconfirm --clean Vegas_Total_Solution_Doc.spec || exit /b 1
python scripts\optimize_distribution.py dist\Vegas_Total_Solution_Doc || exit /b 1
if not exist dist\Vegas_Total_Solution_Doc\Vegas_Total_Solution_Doc.exe exit /b 1
