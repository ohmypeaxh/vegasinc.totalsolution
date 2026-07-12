@echo off
setlocal
if not exist .venv\Scripts\activate.bat echo Run scripts\setup_dev.bat first. && exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
python -m vegas_doc.app.main
