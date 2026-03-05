@echo off
:: ============================================================
::  build_release.bat — Dev build script
::  Builds the full Electron .exe locally for testing
::  Usage: build_release.bat [version]
::  Example: build_release.bat 1.0.1
:: ============================================================
TITLE Build OCR Report Automation
COLOR 0B
cd /d "%~dp0"

SET VERSION=%~1
IF "%VERSION%"=="" SET VERSION=1.0.0

echo ===========================================================
echo   OCR Report Automation — Local Build
echo   Target version: %VERSION%
echo ===========================================================
echo.

:: ── Pre-flight checks ───────────────────────────────────────
if not exist "backend\venv\Scripts\activate.bat" (
    COLOR 0C
    echo [ERROR] backend\venv not found.
    echo Run the Report_app.bat first to create the venv, or:
    echo   cd backend ^&^& python -m venv venv ^&^& venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause & exit /b 1
)
node --version >nul 2>&1
if %errorlevel% neq 0 (
    COLOR 0C
    echo [ERROR] Node.js is not installed or not in PATH.
    pause & exit /b 1
)

:: ──────────────────────────────────────────
:: Step 1: Build Next.js frontend
:: ──────────────────────────────────────────
echo [1/4] Building Next.js frontend (static export)...
cd /d "%~dp0frontend"
call npm install --prefer-offline
call npm run build
if %errorlevel% neq 0 (
    COLOR 0C
    echo [ERROR] Frontend build failed!
    cd /d "%~dp0" & pause & exit /b 1
)
cd /d "%~dp0"
echo       Frontend built ^→ frontend/out/
echo.

:: ──────────────────────────────────────────
:: Step 2: Build Python backend with PyInstaller
:: ──────────────────────────────────────────
echo [2/4] Building Python backend (PyInstaller)...
call backend\venv\Scripts\activate

:: Install pyinstaller into venv if missing
backend\venv\Scripts\python.exe -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo       Installing PyInstaller into venv...
    pip install pyinstaller -q
)

pyinstaller server.spec --clean --noconfirm
if %errorlevel% neq 0 (
    COLOR 0C
    echo [ERROR] PyInstaller build failed! See above for details.
    pause & exit /b 1
)

:: Move to expected location
if exist backend_dist rmdir /S /Q backend_dist
mkdir backend_dist
xcopy /E /I /Q dist\server backend_dist\server
echo       Backend built ^→ backend_dist/server/
echo.

:: ──────────────────────────────────────────
:: Step 3: Patch Electron version & build installer
:: ──────────────────────────────────────────
echo [3/4] Building Electron installer (NSIS)...
cd /d "%~dp0electron"
call npm install --prefer-offline

:: Patch version in package.json
powershell -Command "(Get-Content package.json -Raw) -replace '\"version\":\s*\"[\d.]+(-\w+)?\"', '\"version\": \"%VERSION%\"' | Set-Content package.json -NoNewline"

call npm run build:win
if %errorlevel% neq 0 (
    COLOR 0C
    echo [ERROR] Electron build failed!
    cd /d "%~dp0" & pause & exit /b 1
)
cd /d "%~dp0"
echo       Installer built ^→ dist/
echo.

:: ──────────────────────────────────────────
:: Step 4: Done
:: ──────────────────────────────────────────
COLOR 0A
echo ===========================================================
echo   [4/4] Build complete!
echo ===========================================================
echo.
echo   Installer : dist\OCR Report Automation Setup %VERSION%.exe
echo   Test it   : double-click the installer above
echo.
echo   To publish to GitHub Releases:
echo     git tag v%VERSION%
echo     git push origin v%VERSION%
echo ===========================================================
pause
