@echo off
:: ============================================================================
:: build.bat  --  FishBuddy Windows build script
::
:: Run from the repo root:
::   build.bat
::
:: What it does:
::   1. Verifies Python 3.10+ is available
::   2. Installs / upgrades all Python dependencies from requirements.txt
::   3. Installs PyInstaller if not already present
::   4. Runs PyInstaller with fishbuddy.spec
::   5. Prints the location of the finished build
::
:: Idempotent: safe to run multiple times.  Each run overwrites dist\FishBuddy.
:: ============================================================================

setlocal EnableDelayedExpansion

:: ----------------------------------------------------------------------------
:: 0. Move to the directory containing this script (repo root)
:: ----------------------------------------------------------------------------
cd /d "%~dp0"

echo.
echo ============================================================
echo  FishBuddy -- Windows build
echo ============================================================
echo.

:: ----------------------------------------------------------------------------
:: 1. Check Python version (requires 3.10+)
:: ----------------------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found on PATH.
    echo         Install Python 3.10+ from https://python.org and ensure
    echo         "Add Python to PATH" was checked during installation.
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER% found.

:: Extract major.minor for a basic version check
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PY_MAJOR=%%a
    set PY_MINOR=%%b
)
if %PY_MAJOR% LSS 3 (
    echo [ERROR] Python 3.10+ required. Found %PYVER%.
    exit /b 1
)
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 (
    echo [ERROR] Python 3.10+ required. Found %PYVER%.
    exit /b 1
)

:: ----------------------------------------------------------------------------
:: 2. Install / upgrade dependencies
:: ----------------------------------------------------------------------------
echo.
echo [STEP 1/3] Installing Python dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.  Check requirements.txt and your internet connection.
    exit /b 1
)
echo [OK] Dependencies installed.

:: ----------------------------------------------------------------------------
:: 3. Install PyInstaller
:: ----------------------------------------------------------------------------
echo.
echo [STEP 2/3] Installing PyInstaller...
python -m pip install pyinstaller --upgrade --quiet
if errorlevel 1 (
    echo [ERROR] Could not install PyInstaller.
    exit /b 1
)
echo [OK] PyInstaller ready.

:: ----------------------------------------------------------------------------
:: Optional: Bundle Tesseract OCR
:: ----------------------------------------------------------------------------
:: To include Tesseract in the installer:
::
::   a) Download the Windows installer from:
::        https://github.com/UB-Mannheim/tesseract/wiki
::      (tested with tesseract-ocr-w64-setup-5.x.x.exe)
::
::   b) Install it (or extract the portable version) into:
::        vendor\tesseract\
::      so that vendor\tesseract\tesseract.exe exists.
::
::   c) Copy the required language data:
::        vendor\tesseract\essdata\eng.traineddata   (English)
::
::   d) In fishbuddy.spec, uncomment the two Tesseract sections in
::      added_datas and added_binaries.
::
::   e) Re-run this script.
::
:: Without Tesseract bundled the app will attempt to use a locally installed
:: copy on the user's machine (via PATH / registry lookup in tesseract_finder.py).
:: ----------------------------------------------------------------------------

:: ----------------------------------------------------------------------------
:: 4. Run PyInstaller
:: ----------------------------------------------------------------------------
echo.
echo [STEP 3/3] Building with PyInstaller...
echo            Spec: fishbuddy.spec
echo            Output: dist\FishBuddy\
echo.

:: --clean removes any leftover build cache from previous runs (idempotent)
python -m PyInstaller fishbuddy.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller build failed.
    echo         Review the output above for import errors or missing files.
    exit /b 1
)

:: ----------------------------------------------------------------------------
:: 5. Done
:: ----------------------------------------------------------------------------
echo.
echo ============================================================
echo  Build complete!
echo  Output folder: %CD%\dist\FishBuddy\
echo  Run:           dist\FishBuddy\FishBuddy.exe
echo ============================================================
echo.
echo Next step: run installer\fishbuddy.iss with Inno Setup 6+
echo            to produce FishBuddy-Setup-1.0.0.exe
echo.

endlocal
exit /b 0
