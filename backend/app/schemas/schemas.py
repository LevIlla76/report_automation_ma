from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SlotRequest(BaseModel):
    id: str
    type: str  # 'image' or 'text'
    label: str
    value: Optional[str] = None
    status: Optional[str] = "Normal"

class AnalysisResponse(BaseModel):
    required_slots: List[SlotRequest]

# Mapping configuration as requested
# Format: { "TableKeyword": { "RowKeyword": { "col": index, "label": "description" } } }
REPORT_CELL_MAPPING = {
    "Cisco": {
        "Cisco C1300": {
            "AVG": {"col": 1, "label": "Traffic AVG", "target": "receive/transmit"},
            "MAX": {"col": 2, "label": "Traffic MAX", "target": "receive/transmit"}
        },
        "Cisco Leaf": {
            "AVG": {"col": 1, "label": "Traffic AVG"},
            "MAX": {"col": 2, "label": "Traffic MAX"}
        }
    },
    "F5": {
        "Internet zone": {
            "Dashboard": {"col": 1, "label": "Dashboard Image"},
            "CPU": {"col": 2, "label": "CPU % MAX (Manual)"},
            "Mem": {"col": 3, "label": "Memory % MAX (Manual)"}
        },
        "Intranet zone": {
            "Dashboard": {"col": 1, "label": "Dashboard Image"}
        }
    },
    "Palo Alto": {
        "Internet zone": {
            "BW": {"col": 1, "label": "Bandwidth"},
            "CPU_MEM": {"col": 2, "label": "CPU/Memory"}
        },
        "Intranet zone": {
            "BW": {"col": 1, "label": "Bandwidth"}
        }
    }
}
