# Preprocessor สำหรับปรับภาพให้เหมาะสมกับการ OCR โดยเฉพาะสำหรับภาพที่มีตัวหนังสือเล็กและมีแสงเงา

import cv2
import numpy as np

def preprocess_image(image_path_or_bytes):
    # 1. Load Image
    if isinstance(image_path_or_bytes, str):
        img = cv2.imread(image_path_or_bytes)
    else:
        nparr = np.frombuffer(image_path_or_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return None

    # 2. Resize Logic (ปรับให้เหมาะสมกับภาพใหญ่)
    h, w = img.shape[:2]
    target_width = 2500  # ขยับขึ้นเป็น 2500 เพื่อเก็บรายละเอียดตัวหนังสือเล็ก
    
    if w > target_width:
        scale = target_width / w
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) # INTER_AREA ดีสำหรับย่อภาพ

    # 3. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 4. Contrast Enhancement (Thresholding) **สำคัญมาก**
    # ใช้ Adaptive Threshold เพื่อจัดการกับแสงเงาหรือตัวหนังสือจาง
    # หรือใช้ Binary Threshold ธรรมดาถ้าพื้นหลังขาวสะอาด
    # สูตรนี้: ทำให้ตัวหนังสือเข้มขึ้น ตัดพื้นหลังขาว
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

    # 5. Add Padding (เน้นขอบล่างเยอะๆ)
    # top=20, bottom=100 (เผื่อที่ให้บรรทัดสุดท้าย), left=20, right=20
    padded = cv2.copyMakeBorder(thresh, 20, 100, 20, 20, cv2.BORDER_CONSTANT, value=[255, 255, 255])

    return padded