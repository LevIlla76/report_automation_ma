import os
import zipfile

# 1. ตั้งชื่อไฟล์ Zip ที่จะได้ผลลัพธ์
ZIP_FILENAME = "Project_Release.zip"

# 2. กำหนดโฟลเดอร์และไฟล์ที่ต้องการนำไปรวม
ALLOWED_DIRS = ["backend", "frontend", "tests"]
ALLOWED_FILES = ["Report_app.bat", "run.py"]

# 3. กำหนดโฟลเดอร์และ "ไฟล์" ที่ "ไม่ต้องการ" นำไปรวม (ข้อยกเว้น)
IGNORE_DIRS = {"__pycache__", "temp", "debug_output", ".next", "node_modules", "venv"} # <--- เพิ่ม venv แล้ว
IGNORE_FILES = {".req_installed"} # <--- เพิ่มตัวกรองไฟล์เฉพาะเจาะจงแล้ว

print("=================================================")
print("             📦 PROJECT ZIPPER TOOL")
print("=================================================")
print(f" [*] Destination : {ZIP_FILENAME}")
print(" [*] Packing files... Please wait.")
print("-------------------------------------------------")

try:
    with zipfile.ZipFile(ZIP_FILENAME, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # จัดการโฟลเดอร์ (backend, frontend, tests)
        for folder in ALLOWED_DIRS:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    # กรองโฟลเดอร์ขยะทิ้ง (ถ้าเจอชื่อตรงกับ IGNORE_DIRS จะข้ามทันที)
                    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                    
                    for file in files:
                        # กรองไฟล์ขยะทิ้ง (ถ้าเป็น .req_installed จะไม่ถูกเอาไป Zip ด้วย)
                        if file not in IGNORE_FILES:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, file_path)
                        
        # จัดการไฟล์เดี่ยว (Report_app.bat, run.py)
        for file in ALLOWED_FILES:
            if os.path.exists(file):
                zipf.write(file, file)

    print("\n [OK] SUCCESS! Project has been zipped safely.")
    print(f"      File saved as: {ZIP_FILENAME}")

except Exception as e:
    print(f"\n [ERROR] Something went wrong: {e}")

print("=================================================")
input(" Press ENTER to exit...")