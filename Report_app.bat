@echo off

:: ==========================================
:: CONFIGURATION & UI SETUP
:: ==========================================
TITLE OCR Application Control Panel
COLOR 0B
cd /d "%~dp0"

CLS
echo ===========================================================
echo.
echo               ____________     _________   ________
echo              /  ________  \   /  ______/  /  ____  \
echo             /  /       /  /  /  /        /  /    \  \
echo            /  /       /  /  /  /        /  /_____/  /
echo           /  /       /  /  /  /        /  ____   __/
echo          /   \ _____/  /  /  /_____   /  /    \  \
echo          \____________/   \_______/  /__/      \__\
echo                
echo.
echo                 OCR SYSTEM - AUTO LAUNCHER
echo ===========================================================
echo.

:: === 1. Check & Install Python ===
echo  [ 1 / 5 ] Checking Python Installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo            - Python is NOT installed on this system.
    echo            - Downloading Python 3.11 installer...
    
    :: โหลดตัวติดตั้ง Python อัตโนมัติ
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe >nul 2>&1
    
    COLOR 0C
    echo.
    echo  ===========================================================
    echo   ⚠️ IMPORTANT ACTION REQUIRED ⚠️
    echo  -----------------------------------------------------------
    echo   The Python installer is opening. Before clicking install,
    echo   YOU MUST CHECK THE BOX AT THE BOTTOM:
    echo   "[X] Add python.exe to PATH"
    echo  ===========================================================
    echo.
    echo            - Opening installer...
    start /wait python_installer.exe
    
    :: ลบไฟล์ติดตั้งทิ้งเมื่อใช้เสร็จ
    del python_installer.exe
    
    echo.
    echo            [!] Installation complete.
    echo            [!] Please CLOSE this window and RUN this file again.
    pause
    exit
) else (
    echo            - Python is already installed and ready.
)
echo.

:: === 2. Python Virtual Environment (VENV) ===
echo  [ 2 / 5 ] Initializing Python Virtual Environment...
cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
    echo            - Creating Virtual Environment ^(venv^)...
    python -m venv venv
)

call venv\Scripts\activate

if exist "requirements.txt" (
    if not exist "venv\.venv_ready" (
        echo            - Installing packages inside venv...
        
        :: *** ลบคำสั่งอัปเดต pip ออก ป้องกัน WinError 32 บน Windows ***
        python -m pip install -r requirements.txt
        
        if %errorlevel% equ 0 (
            echo. > "venv\.venv_ready"
            echo            - Python dependencies ready.
        ) else (
            COLOR 0C
            echo.
            echo [!] ERROR: Failed to install some packages.
            echo Please check the red text above to see what went wrong.
            pause
            exit
        )
    ) else (
        echo            - Python dependencies already installed in venv.
    )
)
cd /d "%~dp0"
echo.

:: === 3. Node.js ===
echo  [ 3 / 5 ] Initializing Node.js Environment...
if exist "frontend\package.json" (
    cd frontend
    if not exist "node_modules" (
        echo            - Installing NPM packages...
        call npm install >nul 2>&1
    )
    cd ..
    echo            - Node.js ready.
)
echo.

:: === 4. Start Servers ===
echo  [ 4 / 5 ] Booting up Servers...

start "OCR_Backend_Service" cmd /k "color 0D & call backend\venv\Scripts\activate & python run.py"

cd /d "%~dp0frontend"
start "OCR_Frontend_Service" cmd /k "color 0E & npm run dev"

cd /d "%~dp0"
echo            - Servers are running.
echo.

:: === 5. Open Browser ===
echo  [ 5 / 5 ] Opening Web Browser...
timeout /t 5 >nul
start http://localhost:3000

:: === 6. Running State ===
CLS
COLOR 0A
echo ===========================================================
echo.
echo                     SYSTEM IS ONLINE
echo.
echo ===========================================================
echo.
echo    Web Interface : http://localhost:3000
echo    API Dashboard : http://localhost:8000/docs
echo.
echo -----------------------------------------------------------
echo    PRESS ANY KEY HERE TO SAFELY SHUTDOWN EVERYTHING
echo -----------------------------------------------------------
pause >nul

:: === 7. Safe Shutdown ===
CLS
COLOR 0E
echo ===========================================================
echo                 SHUTTING DOWN SYSTEM...
echo ===========================================================
taskkill /FI "WINDOWTITLE eq OCR_Backend_Service*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq OCR_Frontend_Service*" /T /F >nul 2>&1
echo  [OK] All processes closed successfully.
timeout /t 3 >nul
exit