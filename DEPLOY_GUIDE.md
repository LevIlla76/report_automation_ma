# 🚀 คู่มือ First Build & Deploy + ทดสอบ Auto-Update

## สถานะปัจจุบัน

| สิ่งที่มีอยู่แล้ว | สถานะ |
|---|---|
| Python 3.11 + venv (`backend/venv`) | ✅ พร้อม |
| Node.js 20 | ✅ พร้อม |
| Git remote → GitHub | ✅ พร้อม |
| PyInstaller ใน venv | ❌ ยังไม่ติดตั้ง (script จัดการให้อัตโนมัติ) |
| Electron deps (`electron/node_modules`) | ✅ ติดตั้งแล้ว |

---

## PART 1 — First Build (Local, บนเครื่อง Dev)

### ขั้นตอนที่ 1 — Commit code ทั้งหมดขึ้น GitHub ก่อน

เปิด **PowerShell** ที่ root ของโปรเจกต์:

```powershell
cd D:\Github\report_automation_ma

git add .
git commit -m "feat: Add Electron shell with auto-updater"
git push origin main
```

> ⚠️ ต้อง push ก่อน เพราะ `electron-builder --publish always`
> จะอ่าน `GH_TOKEN` และสร้าง Release บน GitHub

---

### ขั้นตอนที่ 2 — สร้าง GitHub Personal Access Token (PAT)

> **ทำครั้งเดียว** สำหรับ Local Build เท่านั้น
> GitHub Actions ใช้ `GITHUB_TOKEN` อัตโนมัติ ไม่ต้องสร้าง

1. ไปที่ https://github.com/settings/tokens/new
2. ตั้งชื่อ: `OCR Release Token`
3. Expiration: `90 days` (หรือ No expiration)
4. ✅ เลือก scope: **`write:packages`** + **`repo`** (ทั้งหมดใน repo)
5. คลิก **Generate token** → **Copy token** ทันที

```powershell
# Set token ใน environment (ใช้ใน PowerShell session นี้)
$env:GH_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

---

### ขั้นตอนที่ 3 — รัน Local Build Script

```powershell
cd D:\Github\report_automation_ma

# Build version 1.0.0
.\build_release.bat 1.0.0
```

**Script จะทำตามลำดับ:**

```
[1/4] Next.js build  →  frontend/out/          (~2 นาที)
[2/4] PyInstaller    →  backend_dist/server/    (~10-20 นาที) ← ครั้งแรกนานหน่อย
[3/4] Electron NSIS  →  dist/*.exe              (~3 นาที)
[4/4] Done!
```

**Output ที่ได้:**
```
dist/
├── OCR Report Automation Setup 1.0.0.exe   ← ไฟล์ติดตั้งสำหรับ User
├── OCR Report Automation Setup 1.0.0.exe.blockmap
└── latest.yml                               ← สำหรับ auto-updater
```

---

### ขั้นตอนที่ 4 — ทดสอบ Installer บนเครื่อง Dev

```powershell
# ดับเบิลคลิก หรือรันผ่าน terminal
Start-Process "dist\OCR Report Automation Setup 1.0.0.exe"
```

**สิ่งที่ต้องเห็น:**
1. NSIS installer window เปิดขึ้น → กด Install
2. Splash screen animate (📊 logo + progress bar)
3. หน้าจอหลักเปิดขึ้น มี **Custom Title Bar** ด้านบน
4. แถบบนซ้าย: `📊 OCR Report Automation`
5. ปุ่ม −  □  ✕ มุมขวาบน (ทดสอบคลิก)
6. ลาก Title Bar → window เคลื่อนได้
7. ทดสอบ Upload .docx และ OCR ตามปกติ

---

### ขั้นตอนที่ 5 — Publish Release v1.0.0 ไปที่ GitHub

```powershell
cd D:\Github\report_automation_ma

# สร้าง tag และ push → GitHub Actions จะ build อัตโนมัติ
git tag v1.0.0
git push origin v1.0.0
```

ไปดูที่ https://github.com/LevIlla76/report_automation_ma/actions
จะเห็น workflow **"Build & Release"** กำลังรัน (~20-30 นาที)

เมื่อเสร็จ → ไปดูที่ https://github.com/LevIlla76/report_automation_ma/releases
จะมี **Release v1.0.0** พร้อมไฟล์:
- `OCR Report Automation Setup 1.0.0.exe` (installer สำหรับแจก User)
- `latest.yml` (auto-updater manifest)

---

## PART 2 — ทดสอบระบบ Auto-Update

### วิธีทดสอบ (ทำ 4 ขั้นตอน)

#### Step A — ติดตั้ง v1.0.0 บนเครื่อง Test

ให้มี App **v1.0.0** ติดตั้งอยู่บนเครื่อง (จาก Part 1)

---

#### Step B — สร้าง Version ใหม่ (v1.0.1) พร้อม Tag

แก้ไขอะไรสักอย่างเล็กน้อย เช่น แก้ไขเวอร์ชันใน `BUILD.md`:

```powershell
cd D:\Github\report_automation_ma

# แก้ไขอะไรก็ได้ (เพื่อให้ commit ได้)
Add-Content BUILD.md "`n<!-- v1.0.1 -->"

git add .
git commit -m "fix: Update to v1.0.1"
git push origin main

# Push tag → trigger GitHub Actions build
git tag v1.0.1
git push origin v1.0.1
```

รอ GitHub Actions build เสร็จ (~20-30 นาที)
ตรวจสอบที่: https://github.com/LevIlla76/report_automation_ma/releases

---

#### Step C — ตรวจสอบว่า App ที่รัน v1.0.0 ตรวจเจอ Update

เปิด App v1.0.0 ที่ติดตั้งไว้:

**Auto-check (รอ 3 วินาที):** App จะ check อัตโนมัติหลังเปิด 3 วินาที

**สิ่งที่ต้องเห็นบน Title Bar:**
```
ขั้นตอน:
1. (ไม่มีอะไร) — กำลัง checking
2. [↓ v1.0.1 downloading…]   ← Badge สีน้ำเงินกระพริบ
3. Progress bar เส้นบางๆ ใต้ title bar เลื่อนจาก 0% → 100%
4. [✓ v1.0.1 ready — Click to restart & install]  ← Badge สีเขียว
```

**คลิกที่ Badge สีเขียว** → App จะ:
1. ปิดตัวเอง
2. รัน installer v1.0.1 แบบ silent
3. เปิด App ใหม่เป็น v1.0.1 อัตโนมัติ

---

#### Step D — ตรวจสอบ Log ไฟล์

Log ของ Electron อยู่ที่:
```
%APPDATA%\report-automation\logs\main.log
```

เปิดดูบรรทัดที่เกี่ยวกับ updater:
```
[Updater] Checking for updates...
[Updater] Update available: 1.0.1
[Updater] Download progress: 45%
[Updater] Update downloaded: 1.0.1
```

---

## PART 3 — ขั้นตอน Release ในการทำงานจริง (หลังจากนี้)

```
Dev แก้โค้ด
    ↓
git push origin main          ← push ปกติ (ไม่ trigger build)
    ↓
ทดสอบบนเครื่อง Dev ผ่าน Report_app.bat
    ↓
พอพร้อม release:
git tag v1.x.x
git push origin v1.x.x        ← trigger GitHub Actions
    ↓
GitHub Actions build ~25 นาที
    ↓
GitHub Release พร้อม .exe ให้ download
    ↓
User ที่รัน App อยู่ → ได้รับ notification ใน Title Bar
User คลิก → update อัตโนมัติ
```

---

## Troubleshooting

| ปัญหา | สาเหตุ | วิธีแก้ |
|---|---|---|
| PyInstaller build นาน 20+ นาที | ปกติสำหรับ PaddleOCR | รอ, ครั้งต่อไปเร็วขึ้น (cache) |
| `ModuleNotFoundError: No module named 'backend'` | ลืมใส่ `backend` ใน `datas` | อยู่ใน `server.spec` แล้ว ✅ |
| App เปิดแล้ว error "Backend failed" | server.exe ถูก AV บล็อก | เพิ่ม exclusion ใน Windows Defender |
| Auto-update ไม่ทำงาน (dev mode) | ตั้งใจ — ปิดใน `--dev` mode | ทดสอบจาก installed app เท่านั้น |
| `GH_TOKEN` error ตอน local build | Token หมดอายุหรือไม่มี permission | สร้าง token ใหม่ตาม Step 2 |
| GitHub Actions ล้มเหลว | ดู log ใน Actions tab | แก้ตาม error message |
