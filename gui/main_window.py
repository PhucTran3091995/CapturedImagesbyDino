from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGridLayout, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSlot, QEvent
from PyQt6.QtGui import QImage, QPixmap
import cv2
import datetime
import os
import winsound # For sound effects
import threading
from pynput import mouse, keyboard

from gui.widgets import ImageBox
from core.camera import CameraThread
from core.scanner import Scanner
from core.storage import StorageManager
from core.pdf_generator import PDFGenerator

# Custom Application to intercept ALL events
class DinoApp(QApplication):
    def notify(self, receiver, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            print(f"DEBUG: GLOBAL MOUSE PRESS: {event.button()} on {receiver}")
        elif event.type() == QEvent.Type.KeyPress:
            print(f"DEBUG: GLOBAL KEY PRESS: {event.key()} on {receiver}")
        elif event.type() == QEvent.Type.TabletPress:
            print(f"DEBUG: TABLET PRESS on {receiver}")
        return super().notify(receiver, event)

class GlobalInputListener:
    """
    Class chạy thread riêng để lắng nghe toàn bộ sự kiện chuột/phím của hệ thống.
    """
    def __init__(self, callback_func):
        self.callback = callback_func
        self.mouse_listener = mouse.Listener(on_click=self.on_click, on_scroll=self.on_scroll)
        self.key_listener = keyboard.Listener(on_press=self.on_press)
    
    def start(self):
        self.mouse_listener.start()
        self.key_listener.start()
        
    def stop(self):
        self.mouse_listener.stop()
        self.key_listener.stop()

    def on_click(self, x, y, button, pressed):
        if pressed:
            print(f"DEBUG PYNPUT: Mouse Click {button} at ({x}, {y})")
            self.callback(f"Mouse: {button}")

    def on_scroll(self, x, y, dx, dy):
        print(f"DEBUG PYNPUT: Scroll {dx}, {dy}")
        self.callback(f"Scroll: {dx},{dy}")

    def on_press(self, key):
        try:
            print(f"DEBUG PYNPUT: Key Press {key.char}")
            self.callback(f"Key: {key.char}")
        except AttributeError:
            print(f"DEBUG PYNPUT: Key Press {key}")
            self.callback(f"Key: {key}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dino Capture App")
        self.setGeometry(100, 100, 1200, 800)
        
        # Core modules
        self.scanner = Scanner()
        self.storage = StorageManager()

        # State variables
        self.current_pid = None
        self.session_path = None # Đường dẫn lưu ảnh hiện tại
        self.current_image_count = 0
        self.is_scanning = True # Mặc định ban đầu là chế độ scan
        
        # Debounce scan
        self.last_scan_time = 0
        self.scan_cooldown = 2.0 # Giây

        
        # Init UI
        self.init_ui()
        
        # Start Global Input Debugger
        self.input_listener = GlobalInputListener(self.handle_global_input)
        self.input_listener.start()
        
        # Install Event Filter to catch clicks on the video label 
        # (Dino-Lite MicroTouch often acts as a mouse click)
        self.live_view_label.installEventFilter(self)
        
        # Init Camera
        self.camera_thread = CameraThread(camera_id=None) # Auto-detect Dino-Lite
        self.camera_thread.image_data.connect(self.update_live_view)
        self.camera_thread.status_update.connect(self.update_status)
        self.camera_thread.start()

    def init_ui(self):
        # Main Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- LEFT PANEL: CAMERA VIEW ---
        left_layout = QVBoxLayout()
        
        # Live View Label
        self.live_view_label = QLabel("Camera Offline")
        self.live_view_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.live_view_label.setStyleSheet("background-color: black; color: white;")
        self.live_view_label.setMinimumSize(640, 480)
        self.live_view_label.setScaledContents(True) # Scale ảnh fit label
        
        # Info Panel
        info_group = QGroupBox("Session Info")
        info_layout = QVBoxLayout()
        self.lbl_pid = QLabel("PID: N/A")
        self.lbl_pid.setStyleSheet("font-size: 16px; font-weight: bold; color: blue;")
        self.lbl_status = QLabel("Status: Ready")
        info_layout.addWidget(self.lbl_pid)
        info_layout.addWidget(self.lbl_status)
        info_group.setLayout(info_layout)

        # Controls
        controls_layout = QHBoxLayout()
        self.btn_capture = QPushButton("Capture (Space)")
        self.btn_capture.setShortcut("Space") # Map phím Space
        self.btn_capture.clicked.connect(self.capture_image)
        self.btn_capture.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        
        self.btn_reset = QPushButton("New Session")
        self.btn_reset.clicked.connect(self.reset_session)
        
        self.btn_export = QPushButton("Export PDF")
        self.btn_export.clicked.connect(self.export_pdf)
        
        controls_layout.addWidget(self.btn_capture)
        controls_layout.addWidget(self.btn_reset)
        controls_layout.addWidget(self.btn_export)

        left_layout.addWidget(info_group)
        left_layout.addWidget(self.live_view_label, stretch=1)
        left_layout.addLayout(controls_layout)

        # --- RIGHT PANEL: IMAGE GRID ---
        right_layout = QVBoxLayout()
        
        # Top Images Grid
        top_group = QGroupBox("Top Surface (1-8)")
        top_grid = QGridLayout()
        self.top_boxes = []
        for i in range(8):
            box = ImageBox(f"Top {i+1}")
            self.top_boxes.append(box)
            # Layout 2 hàng, 4 cột
            top_grid.addWidget(box, i // 4, i % 4)
        top_group.setLayout(top_grid)
        
        # Bot Images Grid
        bot_group = QGroupBox("Bottom Surface (1-8)")
        bot_grid = QGridLayout()
        self.bot_boxes = []
        for i in range(8):
            box = ImageBox(f"Bot {i+1}")
            self.bot_boxes.append(box)
            bot_grid.addWidget(box, i // 4, i % 4)
        bot_group.setLayout(bot_grid)

        right_layout.addWidget(top_group)
        right_layout.addWidget(bot_group)

        # Add to Main Layout
        main_layout.addLayout(left_layout, stretch=6)
        main_layout.addLayout(right_layout, stretch=4)
    
    def eventFilter(self, source, event):
        """
        Catch mouse clicks specifically on the live view label.
        This helps if the MainWindow doesn't receive the event directly.
        """
        if source == self.live_view_label and event.type() == QEvent.Type.MouseButtonPress:
            self.capture_image()
            return True
        return super().eventFilter(source, event)

    @pyqtSlot(object)
    def update_live_view(self, cv_img):
        """Nhận frame từ thread và hiển thị lên UI"""
        # Lưu frame hiện tại vào biến tạm để dùng khi chụp
        self.current_frame = cv_img.copy()
        
        # Logic SCAN PID
        if self.is_scanning and self.current_pid is None:
            # Throttle scan để không lag UI
            import time
            if time.time() - self.last_scan_time > 0.5: # Scan mỗi 0.5s
                pid = self.scanner.scan(cv_img)
                if pid:
                    # Sound: Success Scan
                    winsound.Beep(1000, 200) # 1000Hz, 200ms
                    self.start_session(pid)
                self.last_scan_time = time.time()

        # Vẽ hình chữ nhật định hướng chụp nếu cần (Optional)
        
        # Convert để hiển thị
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_img.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.live_view_label.setPixmap(QPixmap.fromImage(q_img))

    def start_session(self, pid):
        """Bắt đầu phiên làm việc mới khi scan được PID"""
        self.current_pid = pid
        self.is_scanning = False # Dừng scan
        self.lbl_pid.setText(f"PID: {pid}")
        self.update_status("PID Detected! Ready to Capture.")
        
        # Tạo folder
        self.session_path = self.storage.create_session_folder(pid)
        print(f"Session folder: {self.session_path}")

    @pyqtSlot(str)
    def update_status(self, msg):
        self.lbl_status.setText(f"Status: {msg}")

    def capture_image(self):
        if not hasattr(self, 'current_frame') or self.current_frame is None:
            return

        if self.current_pid is None:
            QMessageBox.warning(self, "Warning", "Please scan a PID first!")
            return

        if self.current_image_count < 16:
            # 0-7: Top, 8-15: Bot
            idx = self.current_image_count
            is_top = idx < 8
            
            # Logic index và side
            img_index = (idx + 1) if is_top else (idx - 8 + 1)
            side = "top" if is_top else "bot"

            # Lưu ảnh
            saved_path = self.storage.save_image(self.session_path, self.current_frame, img_index, side)
            
            # Update UI Widget
            if saved_path:
                # Sound: Capture shutter
                winsound.Beep(2000, 100) # 2000Hz, 100ms
                if is_top:
                    self.top_boxes[idx].set_image(image_path=saved_path)
                else:
                    self.bot_boxes[idx - 8].set_image(image_path=saved_path)
            
            self.current_image_count += 1
            self.update_status(f"Captured {side.upper()} {img_index} ({self.current_image_count}/16)")
            
            if self.current_image_count == 16:
                QMessageBox.information(self, "Finished", "Session Completed! You can Export PDF now.")
        else:
             QMessageBox.warning(self, "Full", "Completed 16 images. Please Export or start New Session.")

    def reset_session(self):
        confirm = QMessageBox.question(self, "Reset", "Start new session? Current images will be cleared from view.", 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.No:
            return

        self.current_image_count = 0
        self.current_pid = None
        self.session_path = None
        self.is_scanning = True # Bật lại scan
        
        self.lbl_pid.setText("PID: [Scanning...]")
        self.update_status("Waiting for PID scan...")
        
        for box in self.top_boxes + self.bot_boxes:
            box.reset()

    def export_pdf(self):
        if not self.current_pid or not self.session_path:
             QMessageBox.warning(self, "Warning", "No active session to export!")
             return

        try:
            generator = PDFGenerator()
            pdf_path = generator.generate_report(self.current_pid, self.session_path)
            
            if pdf_path:
                QMessageBox.information(self, "Success", f"PDF Exported successfully:\n{pdf_path}")
                # Optional: Open file automatically
                os.startfile(pdf_path)
            else:
                QMessageBox.critical(self, "Error", "Failed to generate PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def keyPressEvent(self, event):
        """Handle key presses"""
        key = event.key()
        print(f"Debug: Key Pressed: {key}")
        
        # Accepted keys for capture
        accepted_keys = [
            Qt.Key.Key_Return, Qt.Key.Key_Enter, 
            Qt.Key.Key_Space,
            Qt.Key.Key_F11, Qt.Key.Key_F12,
            Qt.Key.Key_Camera, Qt.Key.Key_Print, 
            Qt.Key.Key_Snapshot
        ]
        
        if key in accepted_keys:
            self.capture_image()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse clicks on the window background"""
        print(f"Debug: Window Mouse Click: {event.button()}")
        # Capture on ANY mouse button click on the background for now to test
        self.capture_image()
        event.accept()

    def handle_global_input(self, info):
        """
        Xử lý sự kiện từ Global Listener.
        Nếu nhận bất kỳ tín hiệu nào (chuột/phím), ta sẽ thử chụp ảnh.
        Lưu ý: Vì chạy thread khác nên cần dùng invokeMethod hoặc cẩn thận với UI.
        Ở đây ta chỉ gọi capture_image() vì hàm này thread-safe cơ bản (check var).
        """
        # Bỏ qua các sự kiện chuột trái thông thường nếu muốn tránh duplicate?
        # Nhưng để test nút Dino, ta cứ bắt hết.
        pass # Đã print log ở class Listener
        
        # Chỉ trigger capture nếu là sự kiện đặc biệt? 
        # Tạm thời trigger luôn để test.
        # self.capture_image() 
        # -> COMMENT LẠI, CHỈ IN LOG THÔI ĐỂ XÁC ĐỊNH TÍN HIỆU TRƯỚC.
        # Nếu anh muốn test chụp luôn thì uncomment dòng dưới:
        # self.capture_image()

    def closeEvent(self, event):
        self.camera_thread.stop()
        if hasattr(self, 'input_listener'):
            self.input_listener.stop()
        event.accept()
