import os
import sys
import shutil
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.pdf_generator import PDFGenerator
from core.storage import StorageManager
import cv2
import numpy as np

def test_pdf_generation():
    print("Testing PDF Generation...")
    
    # 1. Setup mock data
    storage = StorageManager(base_dir="TestImages")
    pid = "TEST_PID_123"
    session_path = storage.create_session_folder(pid)
    
    # Create dummy images
    # 8 top, 8 bot
    for i in range(1, 9):
        # Top: Blue image
        img_top = np.zeros((480, 640, 3), dtype=np.uint8)
        img_top[:] = (255, 0, 0) 
        cv2.putText(img_top, f"Top {i}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 3)
        storage.save_image(session_path, img_top, i, "top")
        
        # Bot: Red image
        img_bot = np.zeros((480, 640, 3), dtype=np.uint8)
        img_bot[:] = (0, 0, 255)
        cv2.putText(img_bot, f"Bot {i}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 3)
        storage.save_image(session_path, img_bot, i, "bot")
        
    print(f"Created mock images in {session_path}")
    
    # 2. Generate PDF
    generator = PDFGenerator()
    pdf_path = generator.generate_report(pid, session_path)
    
    # 3. Verify
    if pdf_path and os.path.exists(pdf_path):
        print(f"SUCCESS: PDF generated at {pdf_path}")
        print(f"File size: {os.path.getsize(pdf_path)} bytes")
    else:
        print("FAILURE: PDF not found.")

if __name__ == "__main__":
    test_pdf_generation()
