@echo off
setlocal
call "%~dp0build_exe.bat" || exit /b %errorlevel%
call "%~dp0build_installer.bat" || exit /b %errorlevel%
python "%~dp0package_size_report.py" --after
