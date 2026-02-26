#backend/app/core/analyzer.py

from docx import Document
from ..schemas.schemas import SlotRequest

class TemplateAnalyzer:
    def __init__(self, doc_path):
        self.doc = Document(doc_path)
        self.slots = []

    def analyze(self):
        self.slots = []
        for i, table in enumerate(self.doc.tables):
            table_text = self._get_table_text(table)
            
            # 1. Cisco
            if "Network Equipment" in table_text and "Traffic AVG" in table_text:
                self._analyze_cisco_table(table, i)
            
            # 2. Palo Alto (ต้องมาก่อน F5 เพราะมี key ที่ซ้ำกันคือ CPU % AVG)
            elif "Firewall Palo Alto" in table_text:
                self._analyze_palo_alto_table(table, i)
            
            # 3. F5 (เอาไว้ทีหลัง)
            elif "F5 load balance" in table_text or "CPU % AVG" in table_text:
                self._analyze_f5_table(table, i)

        return self.slots

    def _get_table_text(self, table):
        text = ""
        for row in table.rows:
            for cell in row.cells:
                text += cell.text + " "
        return text

    def _analyze_cisco_table(self, table, table_idx):
        for row_idx, row in enumerate(table.rows):
            cell_text = row.cells[0].text.lower()
            if "cisco c1300" in cell_text:
                self.slots.append(SlotRequest(id=f"cisco_c1300_avg_{table_idx}_{row_idx}", type="image", label="Cisco C1300 (Average Traffic)"))
                self.slots.append(SlotRequest(id=f"cisco_c1300_max_{table_idx}_{row_idx}", type="image", label="Cisco C1300 (Maximum Traffic)"))
            elif "cisco leaf" in cell_text:
                self.slots.append(SlotRequest(id=f"cisco_leaf_avg_{table_idx}_{row_idx}", type="image", label="Cisco Leaf (Average Traffic)"))
                self.slots.append(SlotRequest(id=f"cisco_leaf_max_{table_idx}_{row_idx}", type="image", label="Cisco Leaf (Maximum Traffic)"))
            elif "cisco" in cell_text and "switch" in cell_text:
                # Fallback
                self.slots.append(SlotRequest(id=f"cisco_avg_{table_idx}_{row_idx}", type="image", label=f"Cisco Row {row_idx} (AVG)"))
                
    def _analyze_f5_table(self, table, table_idx):
        target_labels = ["Internet", "Intranet"]
        label_index = 0
        
        for row_idx, row in enumerate(table.rows):
            # อ่านข้อมูลทั้งแถว
            row_content = "".join([c.text for c in row.cells]).strip()
            
            # 1. ถ้าเป็นแถวว่าง ให้ข้าม
            if not row_content: continue

            # 2. ถ้าเป็นหัวตาราง (มีคำว่า Zone และ CPU) ให้ข้าม
            # แก้ปัญหาเรื่อง row_idx < 2 หรือ < 1 โดยเช็คจาก content จริง
            if "Zone" in row_content and "CPU" in row_content:
                continue
            if "Network Equipment" in row_content:
                continue
                
            # 3. ถ้าไม่ใช่หัวตาราง แสดงว่าเป็นข้อมูลแล้ว -> สร้าง Slot ตามลำดับ
            if label_index < len(target_labels):
                zone_label = target_labels[label_index]
                
                self.slots.append(SlotRequest(
                    id=f"f5_{zone_label.lower()}_{table_idx}_{row_idx}",
                    type="image",
                    label=f"F5 {zone_label} zone Dashboard",
                    value=""
                ))
                
                label_index += 1 # ขยับไปลำดับถัดไป
            

    def _analyze_palo_alto_table(self, table, table_idx):
        # ตัวแปรกันไม่ให้สร้าง CPU/Mem ซ้ำ (เพราะวน Loop หลายแถว)
        cpumem_slots_created = False
        
        # เก็บ Slot ของ Bandwidth ไว้ชั่วคราวก่อน เพื่อเอาไปต่อท้ายทีหลัง
        bw_slots = []

        for row_idx, row in enumerate(table.rows):
            row_text = " ".join([c.text.lower() for c in row.cells])
            row_text = row_text.replace('\u00a0', ' ').replace('  ', ' ')
            
            is_internet = "internet" in row_text and "zone" in row_text
            is_intranet = "intranet" in row_text and "zone" in row_text
            
            # --- 1. สร้าง CPU & Memory (AVG ก่อน MAX) ---
            # ทำแค่ครั้งเดียวเมื่อเจอแถวแรกของ Palo Alto
            if (is_internet or is_intranet) and not cpumem_slots_created:
                self.slots.append(SlotRequest(
                    id=f"pa_avg_cpumem_{table_idx}", 
                    type="image", 
                    label="Palo Alto Average CPU & Memory"
                ))
                self.slots.append(SlotRequest(
                    id=f"pa_max_cpumem_{table_idx}", 
                    type="image", 
                    label="Palo Alto Maximum CPU & Memory"
                ))
                cpumem_slots_created = True

            # --- 2. เก็บ Bandwidth เข้า List ชั่วคราว (Internet ก่อน Intranet ตามลำดับตาราง) ---
            if is_internet:
                 bw_slots.append(SlotRequest(
                    id=f"pa_internet_bw_{table_idx}_{row_idx}", 
                    type="image", 
                    label="Palo Alto Internet Zone (Bandwidth)"
                ))
            elif is_intranet:
                 bw_slots.append(SlotRequest(
                    id=f"pa_intranet_bw_{table_idx}_{row_idx}", 
                    type="image", 
                    label="Palo Alto Intranet Zone (Bandwidth)"
                ))

        # --- 3. นำ Bandwidth ไปต่อท้ายสุด ---
        # เพื่อให้ลำดับเป็น AVG -> MAX -> Internet BW -> Intranet BW
        self.slots.extend(bw_slots)