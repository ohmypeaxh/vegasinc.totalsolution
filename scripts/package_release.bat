@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo === Vegas Total Solution Doc production release ===
call scripts\build_exe.bat || exit /b %errorlevel%
call scripts\build_installer.bat || exit /b %errorlevel%

echo Generating SHA-256 checksums and build manifest...
".build-venv\Scripts\python.exe" scripts\generate_release_metadata.py || exit /b 1
".build-venv\Scripts\python.exe" scripts\package_size_report.py --after || exit /b 1

echo.
echo Release artifacts:
echo   dist\Vegas_Total_Solution_Doc\Vegas_Total_Solution_Doc.exe
echo   dist\installer\Vegas_Total_Solution_Doc_Setup.exe
echo   dist\installer\checksums.txt
echo   dist\installer\build_manifest.json
echo   artifacts\package_size_after.txt
exit /b 0
