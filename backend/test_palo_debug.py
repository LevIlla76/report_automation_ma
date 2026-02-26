# backend/test_palo_debug.py

import os
import cv2
import re
import logging
import numpy as np
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from paddleocr import PaddleOCR

# --- 1. SETUP OCR ---
logging.getLogger("ppocr").setLevel(logging.ERROR)
print("⏳ Initializing OCR engine (Super Debug Mode)...")

# ลองถอยกลับไปตั้งค่าแบบพื้นฐานที่สุด เพื่อดูว่าปัญหาเกิดจาก Parameter หรือไม่
ocr_engine = PaddleOCR(use_angle_cls=False, lang='en')

def preprocess_simple(img, debug_name):
    if img is None: return None
    h, w = img.shape[:2]
    
    # --- ปรับขนาดให้เหมาะสม (Dynamic Resizing) ---
    target_w = w
    if w < 2000:
        # ถ้าภาพเล็กเกินไป (เช่น ตารางเล็กๆ) ให้ขยาย 2 เท่า
        target_w = w * 2
    elif w > 5000:
        # ถ้าภาพใหญ่เกินไป (เช่น Dashboard กว้างๆ) ให้ย่อลงมาเหลือ 4000-5000px
        # เพื่อไม่ให้เกิน limit ของ OCR และป้องกันตัวหนังสือแตกจากการบีบของ Engine
        target_w = 4000 
    
    if target_w != w:
        scale = target_w / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)
    
    # --- ส่วนขาวดำเหมือนเดิม ---
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    final = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    cv2.imwrite(f"debug_input_{debug_name}.jpg", final)
    return final

def test_palo_extraction(image_path):
    filename = os.path.basename(image_path)
    print(f"\n{'='*70}\n📂 ANALYZING: {filename}")

    img = cv2.imread(image_path)
    if img is None: return

    proc_img = preprocess_simple(img, filename)

    # 2. OCR RUN
    result = ocr_engine.ocr(proc_img)
    
    all_texts = []
    
    if result and isinstance(result, list):
        for block in result:
            # ตรวจสอบว่าผลลัพธ์เป็นโครงสร้างใหม่ (Dictionary) หรือไม่
            if isinstance(block, dict) and 'rec_texts' in block:
                all_texts.extend(block['rec_texts'])
                # Debug ดูว่าดึงอะไรออกมาได้บ้าง
                print(f"   📦 Found {len(block['rec_texts'])} text elements via Dict Key")
            
            # ตรวจสอบโครงสร้างแบบมาตรฐาน [ [box], (text, conf) ]
            elif isinstance(block, list):
                for line in block:
                    if isinstance(line, list) and len(line) > 1:
                        all_texts.append(line[1][0])

    full_blob = " ".join(all_texts)
    print(f"\n🔍 [ASSEMBLY]\n   Blob: {full_blob}")

    # 3. EXTRACTION (ส่วนเดิมของคุณ)
    extracted = "NOT FOUND"
    full_blob = " ".join(all_texts)
    # ใช้ Regex ที่ยืดหยุ่นขึ้นตามที่แนะนำก่อนหน้า
    pc_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', full_blob)
    
    if "bandwidth" not in filename.lower():
        if len(pc_matches) >= 2:
            # ปกติ Palo Alto Table: [ค่า CPU] [ค่า Memory]
            cpu_val = pc_matches[-2]
            mem_val = pc_matches[-1]
            extracted = f"CPU: {cpu_val}%, Mem: {mem_val}%"
        elif pc_matches:
            extracted = f"{pc_matches[-1]}%"
    else:
        # Logic Bandwidth
        anchor_pattern = r'None\s+None\s+(\d+(?:\.\d+)?)\s*([MmGgKkCc][Bb]?)'
        anchor_match = re.search(anchor_pattern, full_blob, re.IGNORECASE)
        
        if anchor_match:
            val = anchor_match.group(1)
            unit = anchor_match.group(2).upper().replace('C', 'G')
            extracted = f"{val} {unit} (Found via Anchor)"
        else:
            # 2. Fallback: ถ้าไม่เจอ None None ให้หาค่าที่มากที่สุด (Logic เดิมที่เคยแนะนำ)
            pattern = r'(\d+(?:\.\d+)?)\s*([MmGgKkCc][Bb]ps|[GgMmKkCc][Bb]?)'
            matches = re.findall(pattern, full_blob, re.IGNORECASE)
            if matches:
                # ใช้ฟังก์ชันช่วยคำนวณหาค่าสูงสุด (ป้องกันไปหยิบเลขแกนกราฟ)
                def get_size(m):
                    try:
                        v = float(m[0])
                        u = m[1].lower()
                        if 'g' in u or 'c' in u: return v * 1e9
                        if 'm' in u: return v * 1e6
                        return v * 1e3
                    except: return 0
                
                best_match = max(matches, key=get_size)
                val = best_match[0]
                unit = best_match[1].upper().replace('C', 'G')
                extracted = f"{val} {unit}"
            else:
                extracted = "NOT FOUND"

    print(f"\n✅ [RESULT]: {extracted}\n")

if __name__ == "__main__":
    imgs = ["AVG cpu_memory.png", "MAX cpu_memory.png", 
            "Internet zone Total Bandwidth Used.png", "Intranet zone Total Bandwidth Used.png"]
    for i in imgs:
        if os.path.exists(i): test_palo_extraction(i)