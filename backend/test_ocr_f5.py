import os
import sys
import cv2

# Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from app.core.ocr_engine import OCROngine
except ImportError:
    # Fallback กรณีวางไฟล์คนละที่
    sys.path.append(os.path.join(current_dir, 'backend'))
    from app.core.ocr_engine import OCROngine

def test_debug():
    # ระบุชื่อไฟล์รูปภาพ F5 ของคุณตรงนี้
    image_path = "F5 Internet zone.png" 
    
    if not os.path.exists(image_path):
        # ลองหาไฟล์ png ในโฟลเดอร์ปัจจุบัน
        files = [f for f in os.listdir('.') if f.endswith('.png') and 'F5' in f]
        if files:
            image_path = files[0]
        else:
            print(f"❌ หาไฟล์รูปไม่เจอ: {image_path}")
            return

    print(f"Testing Image: {image_path}")
    
    # Load Image
    img = cv2.imread(image_path)
    
    # Run Engine
    ocr = OCROngine()
    ocr.extract_f5_dashboard(img)
    
    print("\n✅ เสร็จสิ้น! กรุณาเปิดดูรูปในโฟลเดอร์ 'debug_output'")
    print("   ดูไฟล์ที่ลงท้ายด้วย _RESULT.png เพื่อดูว่ามันตีกรอบตรงไหน")

if __name__ == "__main__":
    test_debug()