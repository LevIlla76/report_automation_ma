# OCR Engine ที่ใช้ PaddleOCR ในการดึงข้อมูลจากภาพ โดยมี Logic พิเศษสำหรับจัดการกับรูปแบบของข้อมูลที่แตกต่างกันในแต่ละ Vendor (Cisco, Palo Alto, F5)
import threading
import os
import logging
import uuid
from paddleocr import PaddleOCR
import numpy as np
import re
import cv2
import tempfile
import shutil

# ปิด Log ของ PaddleOCR เพื่อไม่ให้รก Console
logging.getLogger("ppocr").setLevel(logging.ERROR)

class OCROngine:
    def __init__(self):
        # Initialize PaddleOCR
        # ใช้โมเดลภาษาอังกฤษ V4 ที่แม่นยำเรื่องตัวเลข
        self.lock = threading.Lock()

        self.ocr = PaddleOCR(
            use_angle_cls=False, 
            lang='en', 
            ocr_version='PP-OCRv4',
            enable_mkldnn=False
        )

        # สร้างโฟลเดอร์เก็บรูป Debug
        self.debug_dir = "debug_output"
        if os.path.exists(self.debug_dir):
            shutil.rmtree(self.debug_dir)
        os.makedirs(self.debug_dir, exist_ok=True)
        print(f"📂 Debug images will be saved to: {os.path.abspath(self.debug_dir)}")

    def process(self, image_np):
        """
        image_np: Preprocessed image (numpy array)
        Returns: String with extracted value (e.g. "17.06 Mbps / 573.52 Kbps")
        """
        if image_np is None:
            return ""
        
        # Upscale เล็กน้อยสำหรับ Cisco/Palo (Width ~2000 is sweet spot)
        h, w = image_np.shape[:2]
        target_width = 2000
        if w < target_width:
            scale = 1.5
            image_np = cv2.resize(image_np, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            
        # HACK: ใช้ Temp file เพื่อความเสถียรสูงสุดบน Windows
        temp_path = os.path.join(tempfile.gettempdir(), f"ocr_temp_{uuid.uuid4().hex}.png")
        try:
            cv2.imwrite(temp_path, image_np)
            with self.lock:
                result = self.ocr.ocr(temp_path)
        except Exception as e:
            print(f"[OCR Error] Failed to process image: {e}")
            return ""
        finally:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
                
        if not result or not result[0]:
            return ""

        # --- 1. Universal Result Parsing (แปลงผลลัพธ์ให้อยู่ในรูปแบบมาตรฐาน) ---
        raw_lines = []
        res_data = result[0]
        
        # รองรับทั้ง List แบบเก่าและแบบใหม่
        if isinstance(res_data, list):
            for item in res_data:
                if isinstance(item, list) and len(item) == 2:
                    box, content = item
                    text, score = content
                    raw_lines.append({'box': box, 'text': text, 'score': score})
                elif isinstance(item, dict):
                    raw_lines.append({
                        'box': item.get('points', item.get('dt_polys', [])),
                        'text': item.get('transcription', item.get('rec_text', '')),
                        'score': item.get('score', item.get('rec_score', 0.0))
                    })
        elif hasattr(res_data, 'get') or 'Result' in str(type(res_data)):
            # รองรับ Paddlex format
            texts = getattr(res_data, 'rec_texts', getattr(res_data, 'rec_text', []))
            boxes = getattr(res_data, 'dt_polys', [])
            scores = getattr(res_data, 'rec_scores', getattr(res_data, 'rec_score', []))
            
            if not texts and hasattr(res_data, 'get'):
                texts = res_data.get('rec_texts', [])
                boxes = res_data.get('dt_polys', [])
                scores = res_data.get('rec_scores', [])

            for i in range(len(texts)):
                raw_lines.append({
                    'text': str(texts[i]),
                    'box': boxes[i].tolist() if hasattr(boxes[i], 'tolist') else boxes[i],
                    'score': float(scores[i]) if i < len(scores) else 1.0
                })

        # --- 2. Geometric Processing (คำนวณตำแหน่ง) ---
        processed_boxes = []
        for line in raw_lines:
            box = line['box']
            text = line['text']
            score = line['score']
            
            if not isinstance(box, (list, tuple)) or len(box) < 4:
                continue

            try:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                center_x = sum(xs) / len(xs)
                center_y = sum(ys) / len(ys)
                
                processed_boxes.append({
                    'text': text,
                    'score': score,
                    'center_x': center_x,
                    'center_y': center_y,
                    'min_x': min(xs),
                    'max_x': max(xs),
                    'raw_box': box
                })
            except Exception:
                continue

        # Sort: บนลงล่าง (Y) แล้วซ้ายไปขวา (X)
        processed_boxes.sort(key=lambda b: (int(b['center_y'] / 10), b['center_x']))

        # --- 3. Row Clustering (จัดบรรทัด) ---
        rows = []
        if processed_boxes:
            current_row = [processed_boxes[0]]
            for i in range(1, len(processed_boxes)):
                box = processed_boxes[i]
                last_box = current_row[-1]
                
                # ถ้าระดับความสูงต่างกันน้อยกว่า 15px ให้ถือว่าบรรทัดเดิม
                if abs(box['center_y'] - last_box['center_y']) < 15:
                    current_row.append(box)
                else:
                    current_row.sort(key=lambda b: b['center_x'])
                    rows.append(current_row)
                    current_row = [box]
            
            current_row.sort(key=lambda b: b['center_x'])
            rows.append(current_row)

        # --- 4. Smart Merging (รวมคำที่ขาด เช่น "1" "5.91") ---
        final_lines = []
        for row in rows:
            if not row: continue
            
            merged_parts = []
            current_cluster = [row[0]]
            
            for i in range(1, len(row)):
                box = row[i]
                last_box = current_cluster[-1]
                
                # ถ้าระยะห่างแนวนอนน้อยกว่า 25px ให้รวมกัน
                dist = box['min_x'] - last_box['max_x']
                
                if dist < 25:
                    current_cluster.append(box)
                else:
                    merged_parts.append(" ".join([b['text'] for b in current_cluster]))
                    current_cluster = [box]
            
            merged_parts.append(" ".join([b['text'] for b in current_cluster]))
            final_lines.append(" ".join(merged_parts))

        # --- 5. Extract Values (ขั้นตอนสำคัญ: ดึงค่าจราจรจากบรรทัดที่รวมแล้ว) ---
        return self._extract_traffic_values(final_lines)

    def _extract_traffic_values(self, lines):
        # Regex: รองรับจุดตรงกลาง (. หรือ - หรือ _) เช่น "17.06.Mbps"
        # และรองรับ unit ที่อาจจะติดกัน หรือห่างกัน
        token_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*[\._-]?\s*([MmGgKk]bps|[MmGgKk]b/s|bps)', re.IGNORECASE)
        
        candidates = []

        # วนจากล่างขึ้นบน (Bottom-up) เพื่อหาค่า Summary ก่อน
        for line in reversed(lines):
            clean_line = re.sub(r'[^\x00-\x7F]+', '', line)
            clean_line = line.replace('O', '0').replace('o', '0').strip()
            
            # Skip noise
            if "2026" in clean_line or "Custom" in clean_line: continue
            
            matches = token_pattern.findall(clean_line)
            
            # กรอง matches ในบรรทัดนี้ก่อนเอาไปใช้
            valid_matches = []
            for val, unit in matches:
                try:
                    num_val = float(val)
                    # --- ZERO FILTER (จุดสำคัญ) ---
                    # ถ้าค่าเป็น 0 และหน่วยเป็น bps (เลขแกนกราฟ) -> ทิ้งทันที!
                    # แต่ถ้าเป็น 0 Mbps (อาจจะเป็นค่าจริงแต่น้อยมาก) -> เก็บไว้ได้ (แต่ปกติน้อยมาก)
                    if num_val == 0 and 'bps' in unit.lower() and 'k' not in unit.lower() and 'm' not in unit.lower():
                        continue 
                    valid_matches.append(f"{val} {unit}")
                except:
                    continue

            # ถ้าหลังจากกรอง 0 bps แล้วเหลือคู่ (Rx/Tx) -> จบงานทันที
            if len(valid_matches) >= 2:
                return f"{valid_matches[0]} / {valid_matches[1]}"
            
            # ถ้าเหลือค่าเดียว -> เก็บเข้า candidates ไว้ก่อน
            elif len(valid_matches) == 1:
                candidates.insert(0, valid_matches[0])

        # สรุปจาก candidates ที่สะสมมา (กรณี Rx บรรทัดนึง Tx อีกบรรทัดนึง)
        if len(candidates) >= 2:
            return f"{candidates[-2]} / {candidates[-1]}"
        elif len(candidates) == 1:
            return candidates[0]

        return "Not Found"
    
    def extract_f5_dashboard(self, image_np):
        print("\n" + "="*40)
        print("   F5 EXTRACTION (SMART RADIUS SEARCH)")
        print("="*40)

        if image_np is None: return {}

        # 1. Image Preprocessing (ส่วนเดิม)
        if len(image_np.shape) == 3:
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_np

        h, w = gray.shape[:2]
        roi = gray[int(h * 0.4):h, int(w * 0.6):w] # Crop ครึ่งขวาล่าง
        
        target_w = 2000
        roi_h, roi_w = roi.shape[:2]
        scale = target_w / roi_w
        roi_resized = cv2.resize(roi, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        img_final = clahe.apply(roi_resized)
        
        # 2. สั่ง OCR
        all_detected_text = self._run_debug_ocr(img_final, "f5_right")

        if not all_detected_text:
            return {"cpu_avg": "N/A", "mem_avg": "N/A", "traffic_avg": "N/A"}

        data = {"cpu_avg": "Not Found", "mem_avg": "Not Found", "traffic_avg": "Not Found"}

        # --- 3. SMART RADIUS SEARCH LOGIC ---
        for i, text in enumerate(all_detected_text):
            clean_text = text.lower().strip()
            
            # กรอบการค้นหา (ตรวจสอบ 3 ช่องถัดไปจาก Keyword)
            search_limit = min(i + 4, len(all_detected_text))

            # A. ค้นหา CPU
            if clean_text == "cpu":
                for j in range(i + 1, search_limit):
                    if "%" in all_detected_text[j]:
                        data["cpu_avg"] = all_detected_text[j]
                        break

            # B. ค้นหา Memory
            elif clean_text == "memory":
                for j in range(i + 1, search_limit):
                    if "%" in all_detected_text[j]:
                        # ใช้ Regex ดึงเอาเฉพาะเลข % (เช่น 12% จาก "12% (of 15.6GB/s)")
                        match = re.search(r'\d+%', all_detected_text[j])
                        data["mem_avg"] = match.group(0) if match else all_detected_text[j]
                        break

            # C. ค้นหา Traffic (Total)
            elif clean_text == "total":
                # สำหรับ Traffic เราจะหาทั้ง "ก่อนหน้า" และ "ถัดไป" เพราะจาก Log มันอยู่ใกล้กันมาก
                traffic_range_start = max(0, i - 3)
                traffic_range_end = min(len(all_detected_text), i + 4)
                
                for j in range(traffic_range_start, traffic_range_end):
                    val = all_detected_text[j]
                    # หาค่าที่มีหน่วยความเร็ว
                    if re.search(r'\d+.*(?:MB/s|KB/s|Gbps|Mbps|b/s)', val, re.IGNORECASE):
                        data["traffic_avg"] = val
                        break

        print(f"\n📊 Extracted Data: {data}")
        return data
    
    def _extract_f5_traffic(self, lines):
        """ 
        Extract Traffic สำหรับ F5 โดยเฉพาะ (อิงตาม Index จาก Log)
        [14] Client -> [15] In / [16] Out
        """
        for i, line in enumerate(lines):
            if "client" in line.lower():
                # ตรวจสอบว่าบรรทัดถัดไปมีหน่วยความเร็วหรือไม่
                if i + 2 < len(lines):
                    in_val = lines[i+1]
                    out_val = lines[i+2]
                    # ตรวจสอบ Format (ต้องมีหน่วย KB/s, MB/s หรือ Gb/s)
                    if any(u in in_val.upper() for u in ['B/S', 'BPS']):
                        return f"{in_val} / {out_val}"
        return "Not Found"

    def extract_f5_specific(self, lines, keywords):
        """ 
        ค้นหาตัวเลข % ที่สัมพันธ์กับ Keyword โดยมองเฉพาะบรรทัด 'ถัดไป'
        เพื่อป้องกันการไปหยิบเลขของหัวข้อก่อนหน้ามาใช้
        """
        for i, line in enumerate(lines):
            text_clean = line.lower().replace(" ", "")
            if any(k in text_clean for k in keywords):
                # ตรวจดูเฉพาะบรรทัดปัจจุบัน และ 2 บรรทัดถัดไปเท่านั้น (ไม่เอาบรรทัดก่อนหน้า)
                end_idx = min(len(lines), i + 3)
                search_zone = lines[i : end_idx]
                
                print(f"[SEARCH] Target '{keywords[0]}' found. Checking zone: {search_zone}")

                for zone_line in search_zone:
                    # ค้นหาเลข % ที่ไม่ใช่เลข 0 (ป้องกัน Noise)
                    matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', zone_line)
                    if matches:
                        # ถ้าเป็น Memory และเจอ (of 15.6GB/s) ให้ข้ามไปเอาเลข % จริงๆ
                        val = matches[0]
                        print(f"   >> Match found: {val} %")
                        return f"{val} %"
                            
        return "Not Found"

    def _save_debug_img(self, name, img):
        path = os.path.join(self.debug_dir, name)
        cv2.imwrite(path, img)

    def _run_debug_ocr(self, img, prefix):
        self._save_debug_img(f"{prefix}_input.png", img)
        temp_path = os.path.join(self.debug_dir, f"temp_ocr_{uuid.uuid4().hex}.png")
        cv2.imwrite(temp_path, img)
        
        try:
            with self.lock:
                result = self.ocr.ocr(temp_path)
            if isinstance(result, list) and len(result) > 0:
                res_dict = result[0]
            else:
                return []
        except Exception as e:
            print(f"   ❌ OCR Error: {e}")
            return []
        finally:
            # 🌟 เพิ่มส่วนนี้เข้าไป เพื่อลบไฟล์ temp ของ debug ทิ้งหลังใช้เสร็จ
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass

        vis_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        found_texts = []
        
        texts = res_dict.get('rec_texts', [])
        boxes = res_dict.get('dt_polys', [])

        print(f"\n--- [DEBUG] All Detected Texts in {prefix} ---")
        for i in range(len(texts)):
            txt = str(texts[i]).strip()
            found_texts.append(txt)
            
            # พิมพ์ค่าทั้งหมดที่ detect ได้ออกมาดู
            print(f"[{i:02d}] {txt}") 

            if i < len(boxes):
                box = np.array(boxes[i]).astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(vis_img, [box], True, (0, 0, 255), 2)

        self._save_debug_img(f"{prefix}_RESULT.png", vis_img)
        print("-------------------------------------------\n")
        
        return found_texts
    
    def process_palo_alto(self, image_np, filename, label=""):
        """
        Logic รวมสำหรับ Palo Alto:
        - รองรับ Output Format ทั้งแบบ List และ Dict ของ PaddleOCR
        - ปรับปรุงการ Debug และ Logic การดึงค่า CPU/Memory
        """
        if image_np is None: return "NOT FOUND"

        # 1. OCR RUN
        temp_path = os.path.join(tempfile.gettempdir(), f"palo_temp_{uuid.uuid4().hex}.png")
        try:
            cv2.imwrite(temp_path, image_np)
            with self.lock:
                result = self.ocr.ocr(temp_path)
        except Exception as e:
            print(f"OCR Error: {e}")
            return "Error"
        finally:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass

        # --- 2. PARSE RESULTS ---
        all_texts = []
        if result:
            if isinstance(result, list):
                for block in result:
                    if isinstance(block, list):
                        for line in block:
                            if isinstance(line, list) and len(line) >= 2:
                                if isinstance(line[1], (list, tuple)):
                                    all_texts.append(line[1][0])
                    elif isinstance(block, dict):
                        if 'rec_texts' in block:
                            all_texts.extend(block['rec_texts'])
                        elif 'transcription' in block:
                            all_texts.append(block['transcription'])
            elif isinstance(result, dict):
                if 'rec_texts' in result:
                    all_texts.extend(result['rec_texts'])

        full_blob = " ".join(all_texts)
        extracted = "NOT FOUND"

        print(f"\n🔍 [Palo Logic DEBUG] Label: '{label}'")
        print(f"📄 Full Blob: {full_blob}")  # ปริ้นท์ข้อความทั้งหมดที่ OCR อ่านได้

        # --- STEP 3: Determine Mode ---
        is_bandwidth = any(x in (filename + label).lower() for x in ["bandwidth", "bw", "traffic"])
        if not is_bandwidth:
            has_speed = bool(re.search(r'[MmGg][Bb]ps', full_blob, re.IGNORECASE))
            has_cpu = "cpu" in full_blob.lower()
            if has_speed and not has_cpu:
                is_bandwidth = True

        # --- STEP 4: Extract Data ---
        if is_bandwidth:
            # (คง Logic Bandwidth เดิมไว้ ถ้าไม่มีปัญหา)
            anchor_pattern = r'None\s+None\s+(\d+(?:\.\d+)?)\s*([MmGgKkCc][Bb]?)'
            anchor_match = re.search(anchor_pattern, full_blob, re.IGNORECASE)
            
            if anchor_match:
                val = anchor_match.group(1)
                unit = anchor_match.group(2).upper().replace('C', 'G')
                extracted = f"{val} {unit}"
            else:
                pattern = r'(\d+(?:\.\d+)?)\s*([MmGgKkCc][Bb]ps|[GgMmKkCc][Bb]?)'
                matches = re.findall(pattern, full_blob, re.IGNORECASE)
                print(f"   Bandwidth Matches found: {matches}") # Debug Bandwidth Matches
                if matches:
                    def get_size(m):
                        try:
                            v = float(m[0])
                            u = m[1].lower()
                            if 'g' in u or 'c' in u: return v * 1e9
                            if 'm' in u: return v * 1e6
                            return v * 1e3
                        except: return 0
                    best = max(matches, key=get_size)
                    val = best[0]
                    unit = best[1].upper().replace('C', 'G')
                    extracted = f"{val} {unit}"

        else:
            # --- Logic CPU/Mem (Final Robust Version) ---
            
            # 1. Cleaning: ลบปี ค.ศ. และเวลา ออกก่อนเพื่อลด Noise
            # ลบ 2020-2029 และ ตัวเลขเวลาเช่น 8:00, 12:00
            clean_blob = re.sub(r'202\d', '', full_blob) 
            clean_blob = re.sub(r'\d{1,2}:\d{2}', '', clean_blob)
            
            print(f"   🧹 Clean Blob: {clean_blob[-100:]}...") # ดู 100 ตัวอักษรสุดท้าย

            # 2. Strategy A: "The Last Two Floats" (แม่นยำที่สุดสำหรับ Palo Alto)
            # หาตัวเลขที่มีทศนิยมเท่านั้น (เช่น 1.61, 33.83) ไม่เอาเลขจำนวนเต็ม (เช่น 2, 9, 100)
            # เพราะค่า Average มักมีทศนิยม ส่วนเลขแกนกราฟมักเป็นจำนวนเต็ม
            float_matches = re.findall(r'(\d+\.\d+)', clean_blob)
            
            print(f"   🔢 Float Matches found: {float_matches}")
            
            if len(float_matches) >= 2:
                # ตัวรองสุดท้ายคือ CPU, ตัวสุดท้ายคือ Memory (ตามลำดับใน Report)
                cpu_val = float_matches[-2]
                mem_val = float_matches[-1]
                extracted = f"CPU: {cpu_val}%, Mem: {mem_val}%"
                print(f"   ✅ Strategy A (Last 2 Floats) Hit!")
                
            # 3. Strategy B: Specific Full Header (กรณีเป็นจำนวนเต็ม หรือไม่เจอทศนิยม)
            # ต้องใช้คำเต็มว่า "AVERAGE CPU LOAD" เท่านั้น ห้ามใช้แค่ "CPU" เฉยๆ
            else:
                print("   ⚠️ Strategy A Failed, trying strict headers...")
                # ค้นหาตัวเลขที่ตามหลัง Header เป๊ะๆ
                cpu_match = re.search(r'AVERAGE\s+CPU\s+LOAD.*?(\d+(?:\.\d+)?)', clean_blob, re.IGNORECASE)
                mem_match = re.search(r'AVERAGE\s+PERCENT\s+MEMORY\s*USED.*?(\d+(?:\.\d+)?)', clean_blob, re.IGNORECASE)
                
                if cpu_match and mem_match:
                     extracted = f"CPU: {cpu_match.group(1)}%, Mem: {mem_match.group(1)}%"
                     print(f"   ✅ Strategy B (Strict Headers) Hit!")
                else:
                     # Fallback สุดท้าย: ลองหาเลขที่มี % ติดอยู่ 2 ตัวสุดท้าย
                     pc_matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', clean_blob)
                     # กรองเลข 0, 1, 2, 5, 10... ที่น่าจะเป็นแกนกราฟออก (เอาเฉพาะ > 0)
                     valid_pc = [x for x in pc_matches if float(x) > 0]
                     
                     if len(valid_pc) >= 2:
                         extracted = f"CPU: {valid_pc[-2]}%, Mem: {valid_pc[-1]}%"
                         print(f"   ✅ Strategy C (Last valid %) Hit!")

        print(f"✅ [Final Palo Result]: {extracted}")
        return extracted

    def extract_value(self, lines, keyword, fallback=""):
        """
        Extractor สำหรับ F5 หรืออื่นๆ (Secondary Extractor)
        """
        keyword_clean = keyword.lower().strip()
        # Regex แบบยืดหยุ่นกว่าสำหรับ Table ในไฟล์ F5
        val_pattern = r'(\d+(?:\.\d+)?)\s*([MmGgKk]bps|%|GB|MB)?'
        
        candidates = []
        
        for idx, line in enumerate(lines):
            line_clean = line.strip()
            
            if keyword_clean in line_clean.lower():
                matches = re.findall(val_pattern, line_clean)
                valid_matches = []
                for num, unit in matches:
                    if len(num) == 4 and num.startswith('20'): continue # Skip Year
                    score = 10
                    if unit: score += 20
                    valid_matches.append({'val': num, 'unit': unit, 'score': score})
                
                if valid_matches:
                    best = max(valid_matches, key=lambda x: x['score'])
                    candidates.append({
                        'val': f"{best['val']} {best['unit']}".strip(),
                        'score': best['score'] + 10
                    })

        if not candidates:
            return fallback
            
        best_candidate = max(candidates, key=lambda x: x['score'])
        return best_candidate['val']