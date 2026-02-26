# backend/endpoints.py

import base64
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from docx.shared import Cm
import shutil
import os
import uuid
import json
import io
from typing import Optional
from datetime import datetime

from ..core.analyzer import TemplateAnalyzer
from ..core.ocr_engine import OCROngine
from ..core.preprocessor import preprocess_image
from ..core.filler import DocumentFiller
from ..schemas.schemas import AnalysisResponse



router = APIRouter()

TEMP_DIR = "backend/temp"

os.makedirs(TEMP_DIR, exist_ok=True)


ocr_engine = OCROngine()

def cleanup_files(file_paths: list):
    for path in file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_template(file: UploadFile = File(...), bg_tasks: BackgroundTasks = BackgroundTasks()):
    file_id = str(uuid.uuid4())
    temp_path = os.path.join(TEMP_DIR, f"{file_id}_{file.filename}")
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    analyzer = TemplateAnalyzer(temp_path)
    slots = analyzer.analyze()

    bg_tasks.add_task(cleanup_files, [temp_path])

    return {"required_slots": slots}

@router.post("/process-ocr")
async def process_ocr(image: UploadFile = File(...), keyword: Optional[str] = Form(None)):
    content = await image.read()
    
    # ถ้า preprocess_image กิน CPU ด้วย แนะนำให้ใส่ run_in_threadpool ตรงนี้ด้วยครับ
    processed_img = await run_in_threadpool(preprocess_image, content) 
    
    if processed_img is None:
        raise HTTPException(status_code=400, detail="Invalid image data")
    
    try:
        kw_lower = keyword.lower() if keyword else ""

        if "f5" in kw_lower:
            # 🌟 โยนงานให้ Threadpool ทำ จะได้ไม่บล็อก Server
            extracted = await run_in_threadpool(ocr_engine.extract_f5_dashboard, processed_img)
            return {"success": True, "f5_data": extracted, "image_path": ""}
        
        elif "palo" in kw_lower or "firewall" in kw_lower:
            val = await run_in_threadpool(ocr_engine.process_palo_alto, processed_img, image.filename, label=kw_lower)
            return {"success": True, "result": val}
                
        else:
            result_text = await run_in_threadpool(ocr_engine.process, processed_img)
            return {"success": True, "result": result_text}
            
    except Exception as e:
        print(f"Error: {e}")
        return {"result": "Error", "detail": str(e)}

@router.post("/generate")
async def generate_report(file: UploadFile = File(...), slots: UploadFile = File(...), bg_tasks: BackgroundTasks = BackgroundTasks()): 
    files_to_delete = []
    
    file_id = str(uuid.uuid4())
    template_path = os.path.join(TEMP_DIR, f"template_{file_id}_{file.filename}")
    with open(template_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

        files_to_delete.append(template_path)

    slots_content = await slots.read()
    slots_data = json.loads(slots_content)
    
    filler = DocumentFiller(template_path)
    
    for slot in slots_data:
        try:
            img_base64 = slot.get('image_base64')
            if img_base64:
                try:
                    # แปลง Base64 กลับเป็นรูป
                    if "," in img_base64:
                        img_base64 = img_base64.split(",")[1]
                    img_data = base64.b64decode(img_base64)
                    
                    # เซฟรูปชั่วคราว
                    img_path = os.path.join(TEMP_DIR, f"img_{slot['id']}.png")
                    with open(img_path, "wb") as f:
                        f.write(img_data)

                        files_to_delete.append(img_path)
                    
                    # สร้างชื่อตัวแปรที่แม่นยำขึ้นจาก Label
                    placeholder = ""
                    slot_id = slot['id'].lower()
                    label_lower = slot.get('label', '').lower()

                    if "f5" in slot_id:
                        if "internet" in label_lower:
                            placeholder = "{{image_f5_internet}}"
                        elif "intranet" in label_lower:
                            placeholder = "{{image_f5_intranet}}"
                    elif "pa_" in slot_id:
                        if "avg_cpumem" in slot_id:
                            placeholder = "{{image_pa_avg_cpumem}}"
                        elif "max_cpumem" in slot_id:
                            placeholder = "{{image_pa_max_cpumem}}"
                        elif "internet" in label_lower and "bw" in slot_id:
                            placeholder = "{{image_pa_internet_bw}}"
                        elif "intranet" in label_lower and "bw" in slot_id:
                            placeholder = "{{image_pa_intranet_bw}}"
                            
                    # 🌟 [แก้ไขใหม่] รองรับ Cisco แยก 4 รูป
                    elif "cisco" in slot_id or "cisco" in label_lower: 
                        if "c1300" in slot_id or "c1300" in label_lower:
                            if "avg" in slot_id or "average" in label_lower:
                                placeholder = "{{image_cisco_c1300_avg}}"
                            elif "max" in slot_id or "maximum" in label_lower:
                                placeholder = "{{image_cisco_c1300_max}}"
                        elif "leaf" in slot_id or "leaf" in label_lower:
                            if "avg" in slot_id or "average" in label_lower:
                                placeholder = "{{image_cisco_leaf_avg}}"
                            elif "max" in slot_id or "maximum" in label_lower:
                                placeholder = "{{image_cisco_leaf_max}}"

                    # 🌟 ตั้งค่าความกว้างรูปภาพที่นี่ (หน่วยเป็นเซนติเมตร)
                    image_width = Cm(18.0) # ค่าเริ่มต้น 16 ซม.

                    if "cisco" in placeholder:
                        image_width = Cm(17.5) # กราฟ Cisco 
                    elif "f5" in placeholder:
                        image_width = Cm(20.0) # กราฟ F5
                    elif "pa" in placeholder:
                        image_width = Cm(20.0) # กราฟ Palo Alto

                    # เรียกใช้ฟังก์ชันแทนที่ข้อความด้วยรูป พร้อมยัดขนาดลงไป
                    if placeholder:
                        filler.replace_text_with_image(placeholder, img_path, width=image_width)

                except Exception as img_err:
                    print(f"Failed to process image for {slot['id']}: {img_err}")
            parts = slot['id'].split('_')
            prefix = parts[0]
            
            # Extract Table Index
            if "cpumem" in slot['id'] and "pa" in prefix:
                 table_idx = int(parts[-1])
            else:
                 table_idx = int(parts[-2])
            
            val = slot.get('value')
            label = slot.get('label', '').lower()
            
            # --- 1. SMART ROW FINDER ---
            actual_row_idx = -1
            
            # Global Slot ของ Palo Alto ไม่ต้องหาบรรทัดที่นี่
            if not ("pa" in prefix and "cpumem" in slot['id']):
                table = filler.doc.tables[table_idx]
                target_keywords = []
                if "cisco c1300" in label: target_keywords = ["cisco", "c1300"]
                elif "cisco leaf" in label: target_keywords = ["cisco", "leaf"]
                elif "internet" in label: target_keywords = ["internet"]
                elif "intranet" in label: target_keywords = ["intranet"]

                for r_i, row in enumerate(table.rows):
                    if r_i == 0: continue
                    row_text = "".join([c.text.lower() for c in row.cells])
                    
                    if target_keywords:
                        # ตรวจสอบว่ามี Keyword ครบหรือไม่
                        if all(k in row_text for k in target_keywords):
                            # สำหรับ F5/Palo ต้องแน่ใจว่าไม่ใช่ Header (ไม่มีคำว่า CPU)
                            if ("f5" in prefix or "pa" in prefix) and "cpu" in row_text:
                                continue
                            actual_row_idx = r_i
                            break
                    else:
                        # Fallback: ถ้าไม่มี keyword เฉพาะ ให้ใช้ logic เดิม
                        if ("f5" in prefix or "pa" in prefix) and "cpu" not in row_text:
                             actual_row_idx = r_i
                             break
                
                # Fallback: ใช้ row index จาก ID หากหาไม่เจอ
                if actual_row_idx == -1:
                    try:
                        orig_row = int(parts[-1])
                        actual_row_idx = orig_row 
                    except: pass

            # --- 2. FILL DATA BY DEVICE TYPE ---

            # >>> STATUS <<<
            if "status" in prefix.lower():
                if val:
                    col_idx = len(table.rows[0].cells) - 1
                    filler.fill_slot(table_idx, actual_row_idx, col_idx, val)

            # >>> F5 MULTI-FIELD (UPDATED LOGIC) <<<
            elif "f5" in prefix.lower():
                # Format: (field_key, [keywords_strict], (fallback_keyword, occurrence_n))
                # occurrence_n: 1=CPU, 2=Mem, 3=Traffic (โดยประมาณสำหรับ Template นี้)
                field_map = [
                    ('cpu_avg', ['cpu', 'avg'], ('avg', 1)),
                    ('cpu_max', ['cpu', 'max'], ('max', 1)),
                    ('mem_avg', ['mem', 'avg'], ('avg', 2)),
                    ('mem_max', ['mem', 'max'], ('max', 2)),
                    ('traffic_avg', ['traffic', 'avg'], ('avg', 3)), 
                    ('traffic_max', ['traffic', 'max'], ('max', 3)),
                ]
                
                for field, keywords, (fb_kw, fb_n) in field_map:
                    f_val = slot.get(field)
                    if f_val and actual_row_idx != -1:
                        # 1. ลองหาแบบตรงๆ ก่อน (เช่น "CPU % AVG")
                        col_idx = filler.find_column_index(table_idx, 0, keywords)
                        
                        # 2. ถ้าไม่เจอ ให้ใช้ Fallback (เช่น หาคำว่า "AVG" คำที่ 3)
                        if col_idx == -1:
                             col_idx = filler.find_nth_column_index(table_idx, 0, fb_kw, fb_n)
                        
                        if col_idx != -1: 
                            filler.fill_slot(table_idx, actual_row_idx, col_idx, f_val)

            # >>> PALO ALTO <<<
            elif "pa" in prefix.lower():
                import re

                # CASE A: CPU & MEMORY (Global for Table)
                if "cpumem" in slot['id'] and val:
                    matches = re.search(r'CPU:\s*([\d.]+%?),\s*Mem:\s*([\d.]+%?)', str(val))
                    if matches:
                        cpu_val = matches.group(1)
                        mem_val = matches.group(2)
                        
                        is_avg = "avg" in slot['id']
                        col_key = "avg" if is_avg else "max"
                        
                        # เติมลงทุกแถวที่มี Internet หรือ Intranet
                        table = filler.doc.tables[table_idx]
                        for r_i, row in enumerate(table.rows):
                            r_text = "".join([c.text.lower() for c in row.cells])
                            if ("internet" in r_text or "intranet" in r_text) and "zone" in r_text:
                                c_cpu = filler.find_column_index(table_idx, 0, ["cpu", col_key])
                                if c_cpu != -1: filler.fill_slot(table_idx, r_i, c_cpu, cpu_val)
                                
                                c_mem = filler.find_column_index(table_idx, 0, ["mem", col_key])
                                if c_mem != -1: filler.fill_slot(table_idx, r_i, c_mem, mem_val)

                # CASE B: BANDWIDTH (Row Specific)
                elif "bw" in slot['id'] and val:
                    if actual_row_idx != -1:
                        c_bw = filler.find_column_index(table_idx, 0, ["bandwidth"])
                        if c_bw != -1: 
                            filler.fill_slot(table_idx, actual_row_idx, c_bw, val)

            # >>> CISCO & GENERAL <<<
            else:
                if actual_row_idx == -1 or not val: continue

                rx_val = val
                tx_val = ""
                if "/" in str(val):
                    parts_val = str(val).split("/")
                    rx_val = parts_val[0].strip()
                    if len(parts_val) > 1: tx_val = parts_val[1].strip()

                c_rx, c_tx = -1, -1
                if table_idx == 0:
                    if "avg" in label or "average" in label:
                        c_rx = 2; c_tx = 4
                    else:
                        c_rx = 3; c_tx = 5
                else:
                    n_occurence = 1 if "avg" in label else 2
                    c_rx = filler.find_nth_column_index(table_idx, 0, "receive", n_occurence)
                    c_tx = filler.find_nth_column_index(table_idx, 0, "transmit", n_occurence)

                if c_rx != -1: filler.fill_slot(table_idx, actual_row_idx, c_rx, rx_val)
                if c_tx != -1 and tx_val: filler.fill_slot(table_idx, actual_row_idx, c_tx, tx_val)

        except Exception as e:
            print(f"Error processing slot {slot.get('id')}: {e}")

    current_date = datetime.now().strftime("%d%m%Y")
    report_name = f"Network_Report_{current_date}_(08.00-15.00).docx"
    
    # 1. สร้าง Buffer ในหน่วยความจำ (RAM) แทนการเซฟลงฮาร์ดดิสก์
    file_stream = io.BytesIO()
    
    # 2. สั่งให้ python-docx เซฟข้อมูลลง Buffer
    filler.save(file_stream)
    
    # 3. รีเซ็ตตำแหน่งอ่านไฟล์กลับไปที่จุดเริ่มต้น (สำคัญมาก ไม่งั้นไฟล์จะว่างเปล่า)
    file_stream.seek(0)
    
    # 4. ยิงสตรีมไฟล์ตรงเข้าเบราว์เซอร์ให้ดาวน์โหลดเลย (ไม่ทิ้งไฟล์ไว้ในเครื่อง Server)
    bg_tasks.add_task(cleanup_files, files_to_delete)
    
    return StreamingResponse(
        file_stream, 
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={report_name}"}
    )