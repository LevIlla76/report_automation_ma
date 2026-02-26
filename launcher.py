import webview
import os
import sys
import time
import urllib.request
import urllib.error
import threading
import subprocess
import requests  # สำหรับเช็คอัปเดตจาก GitHub
import uvicorn   # สำหรับรัน FastAPI ในตัว

# ==========================================
# 🌟 1. ตั้งค่า Auto-Update (GitHub Releases)
# ==========================================
CURRENT_VERSION = "v2.0"
GITHUB_REPO = "USERNAME/REPO_NAME" # 🛑 แก้ไขให้เป็นชื่อ GitHub ของคุณ (เช่น "myname/Reportautomation")

def check_and_update():
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(api_url, timeout=5).json()
        latest_version = response.get('tag_name')
        
        if latest_version and latest_version > CURRENT_VERSION:
            print(f"Found new version: {latest_version}. Downloading...")
            assets = response.get('assets', [])
            if not assets:
                return
            
            download_url = assets[0]['browser_download_url']
            new_exe_name = "NetworkApp_update.exe"
            
            # ดาวน์โหลดไฟล์เวอร์ชันใหม่
            exe_data = requests.get(download_url).content
            with open(new_exe_name, 'wb') as f:
                f.write(exe_data)
                
            # สร้างสคริปต์สลับไฟล์ .exe
            current_exe = sys.executable
            bat_script = f"""@echo off
timeout /t 2 /nobreak > NUL
del "{current_exe}"
ren "{new_exe_name}" "NetworkApp.exe"
start "" "NetworkApp.exe"
del "%~f0"
"""
            with open("updater.bat", "w") as f:
                f.write(bat_script)
                
            # สั่งรันสคริปต์สลับไฟล์และปิดตัวเองทันที
            subprocess.Popen(["updater.bat"], creationflags=0x08000000)
            sys.exit() 
    except Exception as e:
        print("Update check failed (No internet or API error). Skipping update.")

# ==========================================
# 🌟 2. โลจิกรัน Backend (FastAPI + หน้าเว็บ)
# ==========================================
def run_server():
    # ปรับ Path ให้ Python หาโฟลเดอร์ backend เจอ
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    backend_path = os.path.join(base_dir, "backend")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
        
    # นำเข้า app จากไฟล์ backend/app/main.py (ที่เราเพิ่มโค้ดเสิร์ฟเว็บไว้)
    from app.main import app 
    
    # รัน Uvicorn เซิร์ฟเวอร์ใน Thread นี้ (ใช้ Port 8000 พอร์ตเดียวจบ!)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

# ==========================================
# 🌟 3. โลจิกตรวจสอบเซิร์ฟเวอร์ก่อนเปิดหน้าเว็บ
# ==========================================
def check_server_and_redirect(window, url, timeout=120):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url)
            window.load_url(url)
            return
        except urllib.error.URLError:
            time.sleep(1)
            
    window.evaluate_js('document.body.innerHTML = "<h2 style=\'color:#ef4444;text-align:center;margin-top:20vh;\'>Error: Server timeout. Please restart the app.</h2>"')

# ==========================================
# 🌟 4. จุดเริ่มต้นโปรแกรมหลัก
# ==========================================
if __name__ == '__main__':
    # 1. เช็คอัปเดตก่อนเลยเป็นอันดับแรก (เฉพาะตอนที่ถูกรันเป็น .exe)
    if getattr(sys, 'frozen', False):
        check_and_update()
        
    # 2. เริ่มรัน Backend เซิร์ฟเวอร์ใน Background Thread (ตั้ง daemon=True เพื่อให้มันปิดพร้อมแอป)
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # คราวนี้เราใช้ Port 8000 อย่างเดียว ไม่พึ่ง Node.js (Port 3000) แล้วครับ
    target_url = 'http://127.0.0.1:8000'

    webview.settings['ALLOW_DOWNLOADS'] = True
    
    # 3. โค้ด HTML สำหรับหน้า Loading
    loading_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
            .spinner { border: 6px solid #1e293b; border-top: 6px solid #38bdf8; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite; margin-bottom: 25px; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            h2 { margin: 0 0 10px 0; font-weight: 500; letter-spacing: 0.5px; }
            p { margin: 0; color: #94a3b8; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="spinner"></div>
        <h2>Starting Network Report System...</h2>
        <p>Loading application data.</p>
    </body>
    </html>
    """
    
    # 4. สร้างหน้าต่างโปรแกรม และแสดงหน้า Loading ทันที
    window = webview.create_window('Network Utilization Report', html=loading_html, width=1280, height=800)
    
    # 5. สั่ง Thread ให้คอยเช็คว่า Server พร้อมหรือยัง
    checker_thread = threading.Thread(target=check_server_and_redirect, args=(window, target_url))
    checker_thread.daemon = True
    checker_thread.start()
    
    # 6. เปิดหน้าต่างโปรแกรม (โค้ดจะรันค้างอยู่บรรทัดนี้จนกว่าผู้ใช้จะกดกากบาทปิดแอป)
    webview.start()
    
    # พอปิดหน้าต่าง ทุกอย่างที่เป็น daemon thread จะถูก Kill เองโดยอัตโนมัติ ไม่ต้องทำอะไรเพิ่มครับ!
    sys.exit()