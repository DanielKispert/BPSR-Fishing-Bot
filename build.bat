@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo FishBuddy build
echo.

python --version >nul 2>&1 || (echo [ERROR] Python not found on PATH. & exit /b 1)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (set PY_MAJOR=%%a & set PY_MINOR=%%b)
if %PY_MAJOR% LSS 3 (echo [ERROR] Python 3.9+ required. Found %PYVER%. & exit /b 1)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 9 (echo [ERROR] Python 3.9+ required. Found %PYVER%. & exit /b 1)
echo [OK] Python %PYVER%

echo Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet || (echo [ERROR] pip install failed. & exit /b 1)
python -m pip install "pyinstaller>=5.13,<7.0" --quiet || (echo [ERROR] PyInstaller install failed. & exit /b 1)
echo [OK] Dependencies ready

echo Building with PyInstaller...
python -m PyInstaller fishbuddy.spec --clean --noconfirm || (echo [ERROR] Build failed. See output above. & exit /b 1)

echo.
echo Build complete: %CD%\dist\FishBuddy\
echo Next: run installer\fishbuddy.iss with Inno Setup 6+
echo.

endlocal
exit /b 0
