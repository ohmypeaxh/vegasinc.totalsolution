@echo off
setlocal
cd /d "%~dp0.."
call scripts\build_exe.bat || exit /b 1
call scripts\build_installer.bat || exit /b 1
python scripts\report_package_size.py --label optimized --distribution dist\Vegas_Total_Solution_Doc --installer dist\installer\Vegas_Total_Solution_Doc_Setup.exe --output artifacts\package_size_after.txt || exit /b 1
