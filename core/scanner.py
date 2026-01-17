import zxingcpp
import cv2
import numpy as np

class Scanner:
    """
    Class wrapper cho việc đọc barcode/QR code từ ảnh OpenCV.
    """
    def scan(self, frame):
        """
        Quét mã từ frame ảnh.
        Args:
            frame: Ảnh numpy array (BGR từ OpenCV)
        Returns:
            str: Nội dung mã detect được hoặc None
        """
        try:
            # zxing-cpp hỗ trợ đọc trực tiếp từ numpy array (nếu bản mới), 
            # hoặc cần convert sang grayscale. Thử grayscale cho an toàn.
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Đọc barcodes
            results = zxingcpp.read_barcodes(gray)
            
            if not results:
                return None
            
            # Trả về kết quả đầu tiên tìm thấy
            for result in results:
                if result.text:
                    return result.text
            
            return None
            
        except Exception as e:
            print(f"Scanner Error: {e}")
            return None
