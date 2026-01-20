from PyQt6.QtCore import QThread, pyqtSignal, Qt
import cv2
import time

class CameraThread(QThread):
    """
    Thread riêng để đọc dữ liệu từ Camera, tránh làm đơ UI.
    """
    image_data = pyqtSignal(object) # Gửi ảnh OpenCV (numpy array) ra UI
    status_update = pyqtSignal(str) # Gửi thông báo trạng thái

    def __init__(self, camera_id=None):
        super().__init__()
        self.camera_id = camera_id
        self.is_running = False
        self.cap = None

    @staticmethod
    def get_available_cameras():
        """
        Trả về danh sách tất cả camera tìm thấy.
        """
        try:
            from pygrabber.dshow_graph import FilterGraph
            graph = FilterGraph()
            return graph.get_input_devices()
        except Exception as e:
            print(f"Error listing cameras: {e}")
            return []

    def find_dino_camera(self):
        """
        Tìm index của camera có tên chứa 'Dino'.
        """
        try:
            devices = CameraThread.get_available_cameras()
            print(f"Available cameras: {devices}")
            
            for i, device_name in enumerate(devices):
                # Dino-Lite (Strict mode: Only "Dino" keyword)
                if "Dino" in device_name:
                    print(f"Found Dino-Lite at index {i}: {device_name}")
                    return i
            
            print("Dino-Lite not found. Strict mode enabled.")
            return None
        except Exception as e:
            print(f"Error listing cameras: {e}")
            return None

    def run(self):
        self.is_running = True
        
        # Auto-detect nếu không chỉ định ID cụ thể hoặc ID=0 (mặc định)
        if self.camera_id is None:
            target_id = self.find_dino_camera()
            if target_id is None:
                 self.status_update.emit("OFFLINE: Dino-Lite camera not found!")
                 self.is_running = False
                 return
            # Cập nhật camera_id thực tế
            self.camera_id = target_id
            
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            self.status_update.emit("Error: Could not open camera.")
            self.is_running = False
            return

        self.status_update.emit("Camera connected.")
        
        # Cấu hình camera (nếu cần)
        # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                self.image_data.emit(frame)
            else:
                self.status_update.emit("Error: Failed to read frame.")
                time.sleep(1) # Chờ 1 chút để tránh spam lỗi
            
            # Giới hạn FPS để giảm tải CPU (khoảng 30fps)
            time.sleep(0.03)

        self.cap.release()
        self.status_update.emit("Camera disconnected.")

    def stop(self):
        self.is_running = False
        self.wait()
