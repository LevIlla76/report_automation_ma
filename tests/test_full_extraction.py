import sys
import os
import cv2
import numpy as np

# Disable check
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

# Add backend to path (เพื่อให้ import app.core ได้)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'backend'))

try:
    from app.core.ocr_engine import OCROngine
    from app.core.preprocessor import preprocess_image
except ImportError as e:
    print("Error: Could not import backend modules.")
    print(f"Please ensure 'backend' folder exists in: {current_dir}")
    print(f"Error detail: {e}")
    sys.exit(1)

def test_full_extraction():
    print("--- Initializing OCR Engine ---")
    engine = OCROngine()
    
    # รายชื่อไฟล์รูปภาพที่ต้องการทดสอบ
    images = [
        "Cisco C1300 AverageTraffic.png",
        "Cisco C1300 Maximum Traffic.png",
        "Leaf 1201 Average Traffic Chart.png",
        "Leaf 1201 MaximumTraffic Chart.png"
    ]
    
    print("\n--- Starting Test ---\n")

    for img_name in images:
        img_path = os.path.join(current_dir, img_name)
        
        if not os.path.exists(img_path):
            print(f"❌ File not found: {img_name}")
            continue
            
        # 1. อ่านไฟล์เป็น Bytes (จำลองเหมือนรับจาก API)
        with open(img_path, "rb") as f:
            content = f.read()
            
        # 2. Preprocess (Resize & Padding)
        proc_img = preprocess_image(content)
        
        if proc_img is None:
            print(f"❌ Failed to preprocess: {img_name}")
            continue

        # 3. Process & Extract
        # แก้ไข: ไม่ต้องวนลูปแล้ว เพราะ engine.process คืนค่า "ผลลัพธ์สุดท้าย" มาเลย
        try:
            result = engine.process(proc_img)
            
            print(f"📄 Image: {img_name}")
            print(f"✅ Result: {result}")  # นี่คือค่าที่คุณต้องการ!
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Error processing {img_name}: {e}")

if __name__ == "__main__":
    test_full_extraction()