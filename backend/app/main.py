import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 1. ตั้งค่า Environment สำหรับ PaddlePaddle OCR (ต้องอยู่บนสุด)
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_enable_pir_in_executor"] = "0"
os.environ["FLAGS_enable_pir"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_enable_new_executor"] = "0"

from .api import endpoints

app = FastAPI(title="Network Report Automation Gen 2")

# 2. Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount API Router (Backend)
app.include_router(endpoints.router, prefix="/api")

# ==============================================================
# 🌟 4. โค้ดส่วน Production (ทำหน้าที่เสิร์ฟหน้าเว็บ Frontend แทน Node.js)
# ==============================================================
if getattr(sys, 'frozen', False):
    # ถ้าเป็น .exe
    base_path = Path(sys._MEIPASS)
else:
    # ถ้าเป็น .py ปกติ
    base_path = Path(__file__).parent.parent.parent / "frontend"

frontend_dir = base_path / "out"

# เพิ่มบรรทัดนี้เพื่อเช็คว่า Path ถูกต้องไหม (ถ้าไม่เจอแอปจะฟ้อง Error ชัดขึ้น)
if frontend_dir.exists():
    app.mount("/_next", StaticFiles(directory=str(frontend_dir / "_next")), name="next")

# ตรวจสอบว่ามีโฟลเดอร์ out (ที่ Build จาก Next.js) หรือไม่
if os.path.exists(frontend_dir):
    # Mount ไฟล์ประกอบเว็บ (JS, CSS, รูปภาพ)
    next_dir = os.path.join(frontend_dir, "_next")
    if os.path.exists(next_dir):
        app.mount("/_next", StaticFiles(directory=next_dir), name="next")
    
    # หน้าแรก (Home)
    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
        
    # Catch-all สำหรับรองรับระบบเปลี่ยนหน้าของ Next.js (Routing)
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        # ป้องกันไม่ให้ไปทับกับเส้นทางของ /api
        if full_path.startswith("api/"):
            return
            
        file_path = os.path.join(frontend_dir, full_path)
        if os.path.exists(file_path):
            return FileResponse(file_path)
        
        html_path = os.path.join(frontend_dir, f"{full_path}.html")
        if os.path.exists(html_path):
            return FileResponse(html_path)
            
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

# 5. จุดรันโปรแกรม
if __name__ == "__main__":
    import uvicorn
    # สร้างโฟลเดอร์เผื่อไว้ถ้ายังไม่มี
    os.makedirs("backend/temp", exist_ok=True)
    os.makedirs("backend/output", exist_ok=True)
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=False)