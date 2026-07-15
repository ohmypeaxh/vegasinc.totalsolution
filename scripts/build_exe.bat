@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo [1/7] Checking Windows and Python 3.12...
if /I not "%OS%"=="Windows_NT" (
  echo ERROR: This production build script requires Windows.
  exit /b 1
)
if defined PYTHON_EXE (
  set "RELEASE_PYTHON=%PYTHON_EXE%"
) else (
  set "RELEASE_PYTHON=python"
  where python >nul 2>nul || (
    echo ERROR: Python 3.12 was not found on PATH. Set PYTHON_EXE to python.exe.
    exit /b 1
  )
)
"%RELEASE_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" || (
  echo ERROR: Python 3.12 is required for release builds.
  exit /b 1
)

echo [2/7] Creating or reusing the isolated build environment...
if not exist ".build-venv\Scripts\python.exe" "%RELEASE_PYTHON%" -m venv .build-venv || exit /b 1
set "BUILD_PYTHON=%CD%\.build-venv\Scripts\python.exe"

echo [3/7] Installing pinned build dependencies...
"%BUILD_PYTHON%" -m pip install --upgrade pip || exit /b 1
"%BUILD_PYTHON%" -m pip install -e ".[dev]" || exit /b 1

echo [4/7] Running automated tests...
set "QT_QPA_PLATFORM=offscreen"
"%BUILD_PYTHON%" -m pytest -q || exit /b 1

echo [5/7] Generating Windows version metadata...
"%BUILD_PYTHON%" scripts\generate_version_info.py || exit /b 1

echo [6/7] Cleaning product-specific stale output and building the EXE...
if exist "dist\Vegas_Total_Solution_Doc" rmdir /s /q "dist\Vegas_Total_Solution_Doc"
if exist "build\Vegas_Total_Solution_Doc" rmdir /s /q "build\Vegas_Total_Solution_Doc"
"%BUILD_PYTHON%" -m PyInstaller --noconfirm --clean Vegas_Total_Solution_Doc.spec || exit /b 1

echo [7/7] Verifying packaged application files...
if not exist "dist\Vegas_Total_Solution_Doc\Vegas_Total_Solution_Doc.exe" (
  echo ERROR: PyInstaller did not create the expected executable.
  exit /b 1
)
if not exist "dist\Vegas_Total_Solution_Doc\_internal\vegas_doc\resources\branding\app.ico" (
  echo ERROR: The packaged application icon resource is missing.
  exit /b 1
)
echo SUCCESS: dist\Vegas_Total_Solution_Doc\Vegas_Total_Solution_Doc.exe
exit /b 0
