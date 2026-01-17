import os
import cv2
from datetime import datetime

class StorageManager:
    """
    Quản lý việc tạo thư mục và lưu ảnh.
    """
    def __init__(self, base_dir="CapturedImages"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def create_session_folder(self, pid):
        """
        Tạo thư mục cho phiên làm việc theo PID.
        Nếu folder đã tồn tại, có thể thêm timestamp để tránh ghi đè (tùy requirements).
        Hiện tại sẽ dùng chính PID làm tên folder.
        """
        # Clean PID string để an toàn cho tên file
        clean_pid = "".join(c for c in pid if c.isalnum() or c in (' ', '-', '_')).strip()
        session_path = os.path.join(self.base_dir, clean_pid)
        
        if not os.path.exists(session_path):
            os.makedirs(session_path)
            
        return session_path

    def save_image(self, folder_path, image, index, side="top"):
        """
        Lưu ảnh xuống đĩa.
        Args:
            folder_path: Đường dẫn thư mục lưu
            image: Ảnh OpenCV BGR
            index: Số thứ tự ảnh (1-8)
            side: "top" hoặc "bot"
        Returns:
            str: Đường dẫn file đã lưu
        """
        filename = f"{index}_{side}.jpg"
        file_path = os.path.join(folder_path, filename)
        
        try:
            cv2.imwrite(file_path, image)
            return file_path
        except Exception as e:
            print(f"Error saving image: {e}")
            return None
