@echo off
setlocal
py -3.12 -m venv .venv || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
python -m pip install --upgrade pip || exit /b 1
python -m pip install -e .[dev] || exit /b 1
echo Development environment ready.
