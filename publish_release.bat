@echo off
:: ============================================================
::  publish_release.bat — Build + Publish to GitHub Releases
::  Usage: publish_release.bat <version> <GH_TOKEN>
::  Example: publish_release.bat 1.0.0 ghp_xxxxxxxxxxxx
::
::  What it does:
::  1. Patch version in electron/package.json
::  2. Build Next.js frontend
::  3. (Optional) Build Python backend — skip with --no-backend
::  4. Build Electron installer
::  5. Create git tag vX.X.X
::  6. Upload installer to GitHub Releases via electron-builder
:: ============================================================
TITLE Publish OCR Report Automation
COLOR 0B
cd /d "%~dp0"

:: ── Arguments ───────────────────────────────────────────────
SET VERSION=%~1
SET GH_TOKEN_ARG=%~2
SET SKIP_BACKEND=0

IF "%VERSION%"=="" (
    echo [ERROR] Usage: publish_release.bat ^<version^> [gh_token] [--no-backend]
    echo   Example: publish_release.bat 1.0.0 ghp_xxxxx
    pause & exit /b 1
)

:: Accept --no-backend as 2nd or 3rd arg
IF "%~2"=="--no-backend" SET SKIP_BACKEND=1 & SET GH_TOKEN_ARG=
IF "%~3"=="--no-backend" SET SKIP_BACKEND=1

:: Use token from arg, then env, then ask
IF NOT "%GH_TOKEN_ARG%"=="" SET GH_TOKEN=%GH_TOKEN_ARG%
IF "%GH_TOKEN%"=="" (
    echo [INPUT] GitHub Personal Access Token not found.
    echo         Get one at: https://github.com/settings/tokens/new
    echo         Required scopes: repo
    echo.
    set /p GH_TOKEN=Paste your GH_TOKEN here: 
)
IF "%GH_TOKEN%"=="" (
    echo [ERROR] No GitHub token provided. Aborting.
    pause & exit /b 1
)

echo ===========================================================
echo   OCR Report Automation — Publish Release
echo   Version : v%VERSION%
echo   GitHub  : LevIlla76/report_automation_ma
echo ===========================================================
echo.

:: ── Pre-flight checks ───────────────────────────────────────
node --version >nul 2>&1 || (echo [ERROR] Node.js not found & pause & exit /b 1)
git --version >nul 2>&1  || (echo [ERROR] git not found & pause & exit /b 1)

:: ──────────────────────────────────────────
:: Step 1: Build Next.js frontend
:: ──────────────────────────────────────────
echo [1/5] Building Next.js frontend...
cd /d "%~dp0frontend"
call npm install --prefer-offline --silent
call npm run build
if %errorlevel% neq 0 (
    COLOR 0C & echo [ERROR] Frontend build failed! & cd /d "%~dp0" & pause & exit /b 1
)
cd /d "%~dp0"
echo       Done: frontend/out/
echo.

:: ──────────────────────────────────────────
:: Step 2: Build Python backend (skip if --no-backend)
:: ──────────────────────────────────────────
IF "%SKIP_BACKEND%"=="1" (
    echo [2/5] Skipping backend build ^(--no-backend^)
    echo       Using existing backend_dist/server/
) ELSE (
    echo [2/5] Building Python backend ^(PyInstaller^)...
    python -c "import PyInstaller" >nul 2>&1 || pip install pyinstaller -q
    pyinstaller server.spec --clean --noconfirm
    if %errorlevel% neq 0 (
        COLOR 0C & echo [ERROR] PyInstaller failed! & pause & exit /b 1
    )
    if exist backend_dist rmdir /S /Q backend_dist
    mkdir backend_dist
    xcopy /E /I /Q dist\server backend_dist\server
    echo       Done: backend_dist/server/
)
echo.

:: ──────────────────────────────────────────
:: Step 3: Patch version + build Electron
:: ──────────────────────────────────────────
echo [3/5] Building Electron ^(v%VERSION%^)...
cd /d "%~dp0electron"
call npm install --prefer-offline --silent

:: Patch version in package.json
powershell -Command "(Get-Content package.json -Raw) -replace '\"version\":\s*\"[\d.]+(-\w+)?\"', '\"version\": \"%VERSION%\"' | Set-Content package.json -NoNewline"
echo       Patched electron/package.json to version %VERSION%

:: Build only (no publish yet — we do that after tagging)
call npm run build:win
if %errorlevel% neq 0 (
    COLOR 0C & echo [ERROR] Electron build failed! & cd /d "%~dp0" & pause & exit /b 1
)
cd /d "%~dp0"
echo       Done: dist/OCR Report Automation Setup %VERSION%.exe
echo.

:: ──────────────────────────────────────────
:: Step 4: Git tag
:: ──────────────────────────────────────────
echo [4/5] Creating git tag v%VERSION%...
git tag v%VERSION% 2>nul
IF %errorlevel% neq 0 (
    echo       Tag v%VERSION% already exists — deleting and recreating...
    git tag -d v%VERSION%
    git push origin :refs/tags/v%VERSION% 2>nul
    git tag v%VERSION%
)
git push origin v%VERSION%
if %errorlevel% neq 0 (
    COLOR 0E
    echo [WARN] Could not push tag to remote. You may need to push manually:
    echo        git push origin v%VERSION%
    echo        Continuing with local publish...
)
echo       Tag v%VERSION% pushed.
echo.

:: ──────────────────────────────────────────
:: Step 5: Upload to GitHub Releases
:: ──────────────────────────────────────────
echo [5/5] Publishing to GitHub Releases...
cd /d "%~dp0electron"

:: electron-builder --publish always uploads installer + blockmap + latest.yml
call node_modules\.bin\electron-builder --win --x64 --publish always
if %errorlevel% neq 0 (
    COLOR 0C & echo [ERROR] Publish failed! Check GH_TOKEN permissions. & cd /d "%~dp0" & pause & exit /b 1
)
cd /d "%~dp0"
echo.

:: ──────────────────────────────────────────
:: Done
:: ──────────────────────────────────────────
COLOR 0A
echo ===========================================================
echo   PUBLISHED SUCCESSFULLY!
echo ===========================================================
echo.
echo   Version  : v%VERSION%
echo   Release  : https://github.com/LevIlla76/report_automation_ma/releases/tag/v%VERSION%
echo   Installer: OCR Report Automation Setup %VERSION%.exe
echo.
echo   Users can now download and install v%VERSION%.
echo   When you publish v%VERSION% + 1, existing apps will auto-update.
echo ===========================================================
pause
