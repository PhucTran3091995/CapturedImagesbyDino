from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QGridLayout, QMessageBox, QGroupBox, QComboBox, QLineEdit)
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
from core.storage import StorageManager
from core.pdf_generator import PDFGenerator
from core.dino_sdk import DNX64
from PyQt6.QtCore import QMetaObject, Q_ARG


# Custom Application to intercept ALL events
# Custom Application to intercept ALL events
class DinoApp(QApplication):
    def notify(self, receiver, event):
        # Removed Debug Prints to clean console
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
        pass # Removed Debug

    def on_scroll(self, x, y, dx, dy):
        pass # Removed Debug

    def on_press(self, key):
        pass # Removed Debug

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dino Capture App")
        self.setGeometry(100, 100, 1200, 800)
        
        # QC Categories Definition
        # Note: Index 0-6 are captured. Index 7 (Handwork) and 8 (Hole Fill) are manual/X-RAY.
        self.qc_categories = [
            "1. Surface of PCB",
            "2. Chip Part",
            "3. Connector or QFP",
            "4. Boss Hole",
            "5. BGA, QFP, Connector",
            "6. Around the PAD",
            "8. Between IC Lead",
            "Around the Handwork Parts", # Placeholder for PDF
            "Hole Fill (X-Ray)"          # Placeholder for PDF
        ]
        # Total images captured is still 7 categories * 4 = 28. (First 7 items)
        self.scan_categories_count = 7 
        self.total_images = self.scan_categories_count * 4 
        self.image_widgets = []

        
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
        
        # Start Global Input Debugger (Disabled for production)
        # self.input_listener = GlobalInputListener(self.handle_global_input)
        # self.input_listener.start()
        
        # Install Event Filter to catch clicks on the video label 
        # (Dino-Lite MicroTouch often acts as a mouse click)
        self.live_view_label.installEventFilter(self)
        
        # Init Camera - Sẽ do populate_cameras trigger hoặc gọi thủ công
        # self.camera_thread = CameraThread(camera_id=None) 
        # self.camera_thread.image_data.connect(self.update_live_view)
        # self.camera_thread.status_update.connect(self.update_status)
        # self.camera_thread.start()
        
        # Populate cameras (Will auto-select Dino if found and start camera)
        self.populate_cameras()

        # Init Dino-Lite MicroTouch SDK
        self.init_dino_sdk()

    def init_dino_sdk(self):
        """Initialize Dino-Lite SDK for MicroTouch"""
        try:
            self.dino = DNX64()
            if self.dino.dnx64:
                self.dino.Init()
                self.dino.EnableMicroTouch(True)
                self.dino.SetEventCallback(self.on_microtouch_press)
                print("Dino-Lite SDK Initialized.")
            else:
                print("Dino-Lite SDK not available (DLL missing).")
        except Exception as e:
            print(f"Failed to init Dino SDK: {e}")

    def on_microtouch_press(self):
        """Callback from ctypes thread when MicroTouch is pressed"""
        print("MicroTouch Pressed!")
        # Use invokeMethod to call capture_image on the GUI thread
        QMetaObject.invokeMethod(self, "capture_image", Qt.ConnectionType.QueuedConnection)


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
        
        # Camera Selection
        self.combo_cameras = QComboBox()
        self.combo_cameras.currentIndexChanged.connect(self.change_camera)
        
        # User Inputs (Model & Inspector)
        self.txt_model = QLineEdit()
        self.txt_model.setPlaceholderText("Enter Model Name")
        self.txt_inspector = QLineEdit()
        self.txt_inspector.setPlaceholderText("Enter Inspector Name")
        
        # Button to confirm info
        self.btn_set_info = QPushButton("Set Info")
        self.btn_set_info.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        self.btn_set_info.clicked.connect(self.set_info)

        # Status & PID
        info_layout.addWidget(self.lbl_pid)
        info_layout.addWidget(self.lbl_status)

        # Input Grid Layout
        input_grid = QGridLayout()
        input_grid.setContentsMargins(0, 5, 0, 5)
        
        input_grid.addWidget(QLabel("Camera:"), 0, 0)
        input_grid.addWidget(self.combo_cameras, 0, 1)
        
        input_grid.addWidget(QLabel("Model:"), 0, 2)
        input_grid.addWidget(self.txt_model, 0, 3)
        
        input_grid.addWidget(QLabel("Inspector:"), 0, 4)
        input_grid.addWidget(self.txt_inspector, 0, 5)
        
        input_grid.addWidget(self.btn_set_info, 0, 6)
        
        info_layout.addLayout(input_grid)
        
        info_group.setLayout(info_layout)
        # Fix height to minimal
        info_group.setMaximumHeight(150) 

        # Controls
        controls_layout = QHBoxLayout()
        self.btn_capture = QPushButton("Capture (Space)")
        self.btn_capture.setShortcut("Space") # Map phím Space
        self.btn_capture.clicked.connect(self.capture_image)
        self.btn_capture.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.btn_capture.setEnabled(False) # Disable initially until Info is set
        
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

        # --- RIGHT PANEL: IMAGE GRID (SCROLLABLE) ---
        from PyQt6.QtWidgets import QScrollArea
        right_layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        self.qc_categories = [
            "1. Surface of PCB",
            "2. Chip Part",
            "3. Connector or QFP",
            "4. Boss Hole",
            "5. BGA, QFP, Connector",
            "6. Around the PAD",
            "8. Between IC Lead"
        ]
        self.image_widgets = []
        
        for cat_idx in range(self.scan_categories_count):
            cat_name = self.qc_categories[cat_idx]
            group = QGroupBox(cat_name)
            grid = QGridLayout()
            grid.setSpacing(5)
            
            for i in range(4):
                # 4 images per category
                img_box = ImageBox(f"Pt {i+1}")
                # Store index in widget for easy access
                img_box.index = len(self.image_widgets)
                img_box.right_clicked.connect(self.handle_image_right_click)
                self.image_widgets.append(img_box)
                grid.addWidget(img_box, 0, i) # 1 row, 4 columns
            
            group.setLayout(grid)
            scroll_layout.addWidget(group)
            
        scroll_layout.addStretch() # Push everything up
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)

        right_layout.addWidget(scroll_area)

        # Add to Main Layout
        main_layout.addLayout(left_layout, stretch=6)
        main_layout.addLayout(right_layout, stretch=4)
    
    def eventFilter(self, source, event):
        """
        Catch mouse clicks specifically on the live view label.
        This helps if the MainWindow doesn't receive the event directly.
        """
        if source == self.live_view_label and event.type() == QEvent.Type.MouseButtonPress:
            # self.capture_image() # Disable mouse click capture
            return True
        return super().eventFilter(source, event)

    # ... (rest of code) ...

    def mousePressEvent(self, event):
        """Handle mouse clicks on the window background"""
        # Capture on ANY mouse button click on the background for now to test
        # self.capture_image() # Disable mouse click capture
        event.accept()

    def handle_global_input(self, info):
        """
        Xử lý sự kiện từ Global Listener.
        """
        # Nếu là Click Chuột Trái (nút Dino thường gửi Left Click)
        if "Mouse: Button.left" in info:
             # Sử dụng QMetaObject.invokeMethod để gọi hàm UI từ thread khác cho an toàn
             # Tuy nhiên capture_image khá đơn giản nên gọi trực tiếp cũng tạm ổn
             # Nhưng tốt nhất nên check cooldown ở đây hoặc trong capture_image
             # self.capture_image() # Disable Global Mouse capture
             pass

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
        if "OFFLINE" in msg:
             self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
             self.live_view_label.setText("DINO-LITE OFFLINE")
        else:
             self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")

    def populate_cameras(self):
        """Lấy danh sách camera và đưa vào ComboBox"""
        cameras = CameraThread.get_available_cameras()
        
        # Block signals to prevent triggering change_camera while populating
        self.combo_cameras.blockSignals(True)
        self.combo_cameras.clear()
        
        dino_index = -1
        for i, cam_name in enumerate(cameras):
            self.combo_cameras.addItem(cam_name, userData=i)
            if "Dino" in cam_name:
                dino_index = i
        
        # Nếu tìm thấy Dino thì chọn nó, nếu không thì để mặc định 0
        if dino_index != -1:
            self.combo_cameras.setCurrentIndex(dino_index)
        elif cameras:
             self.combo_cameras.setCurrentIndex(0)
        
        self.combo_cameras.blockSignals(False)
        
        # Trigger camera start explicitly once
        if self.combo_cameras.count() > 0:
            self.change_camera(self.combo_cameras.currentIndex())
             
    def change_camera(self, index):
        """Thay đổi camera khi user chọn từ ComboBox"""
        if index < 0: return
        
        camera_id = self.combo_cameras.currentData()
        print(f"Switching to camera index: {camera_id}")
        
        # Stop old thread
        if hasattr(self, 'camera_thread'):
            self.camera_thread.stop()
            self.camera_thread.wait() # Chờ thread tắt hẳn
        
        # Start new thread
        self.camera_thread = CameraThread(camera_id=camera_id)
        self.camera_thread.image_data.connect(self.update_live_view)
        self.camera_thread.status_update.connect(self.update_status)
        self.camera_thread.start()

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

    def set_info(self):
        """Khóa input và bắt đầu cho phép chụp"""
        if not self.txt_model.text().strip():
            QMessageBox.warning(self, "Warning", "Please enter Model Name!")
            self.txt_model.setFocus()
            return
            
        if not self.txt_inspector.text().strip():
             QMessageBox.warning(self, "Warning", "Please enter Inspector Name!")
             self.txt_inspector.setFocus()
             return

        # Disable inputs
        self.txt_model.setEnabled(False)
        self.txt_inspector.setEnabled(False)
        self.btn_set_info.setEnabled(False)
        self.btn_set_info.setText("Info Locked (Ready)")
        
        # Enable Capture
        self.btn_capture.setEnabled(True)
        # Move focus to capture button or main window to avoid spacebar issues
        self.btn_capture.setFocus()
        
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
        
        # Reset Widgets
        for box in self.image_widgets:
            box.reset()
            
        # Unlock inputs for new session
        self.txt_model.setEnabled(True)
        self.txt_inspector.setEnabled(True)
        self.btn_set_info.setEnabled(True)
        self.btn_set_info.setText("Start Inspection (Set Info)")
        self.btn_capture.setEnabled(False)

    def export_pdf(self):
        if not self.current_pid or not self.session_path:
             QMessageBox.warning(self, "Warning", "No active session to export!")
             return

        # Nhập thông tin bổ sung (Lấy từ UI)
        model_name = self.txt_model.text().strip()
        inspector_name = self.txt_inspector.text().strip()
        
        if not model_name: 
            model_name = "N/A"
        if not inspector_name:
            inspector_name = "N/A"

        try:
            generator = PDFGenerator()
            # Pass extra info to generator
            pdf_path = generator.generate_report(self.current_pid, self.session_path, model_name, inspector_name)
            
            if pdf_path:
                QMessageBox.information(self, "Success", f"PDF Exported successfully:\n{pdf_path}")
                os.startfile(pdf_path)
            else:
                QMessageBox.critical(self, "Error", "Failed to generate PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def capture_image(self):
        if not hasattr(self, 'current_frame') or self.current_frame is None:
            return

        if self.current_pid is None:
            QMessageBox.warning(self, "Warning", "Please scan a PID first!")
            return
        
        # Check cooldown 1.0s
        import time
        current_time = time.time()
        if hasattr(self, 'last_capture_time') and (current_time - self.last_capture_time < 1.0):
            return

        # Find first empty slot
        target_idx = -1
        for i in range(self.total_images):
            # Check if widget has an image. 
            # Note: reset() clears pixmap so it should be None.
            box = self.image_widgets[i]
            if box.image_label.pixmap() is None or box.image_label.pixmap().isNull():
                target_idx = i
                break
        
        if target_idx == -1:
             QMessageBox.warning(self, "Full", "Session is Full (28 images). Please Export or start New Session.")
             return

        # Use target_idx instead of current_image_count logic for position
        idx = target_idx
        
        # Determine Category and Point Index
        cat_idx = idx // 4
        point_idx = (idx % 4) + 1
        cat_name_raw = self.qc_categories[cat_idx]
        
        # Clean category name for filename
        parts = cat_name_raw.split(". ", 1)
        cat_num = parts[0]
        cat_text = parts[-1] if len(parts) > 1 else parts[0]
        cat_name_clean = cat_text.replace(" ", "_").replace(",", "")
        
        file_suffix = f"{cat_num}_{cat_name_clean}"
        
        saved_path = self.storage.save_image(self.session_path, self.current_frame, file_suffix, point_idx)
        
        if saved_path:
            winsound.Beep(2000, 100)
            self.image_widgets[idx].set_image(image_path=saved_path)
            # Store path in widget for deletion reference
            self.image_widgets[idx].current_image_path = saved_path
        
        # Recalculate count based on filled slots for status
        filled_count = sum(1 for w in self.image_widgets if w.image_label.pixmap() is not None and not w.image_label.pixmap().isNull())
        self.current_image_count = filled_count # Sync counter
        
        self.update_status(f"Captured: {cat_name_raw} - Pt {point_idx} ({filled_count}/{self.total_images})")
        
        self.last_capture_time = current_time
        
        if filled_count == self.total_images:
            QMessageBox.information(self, "Finished", "Session Completed! Auto-exporting PDF...")
            self.export_pdf()

    def handle_image_right_click(self, widget):
        if not widget.image_label.pixmap() or widget.image_label.pixmap().isNull():
            return # Ignore empty widgets

        reply = QMessageBox.question(self, "Delete Image", 
                                     f"Delete image at {widget.title_label.text()}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear widget
            widget.reset()
            # Also try to delete file if we stored path
            if hasattr(widget, 'current_image_path') and widget.current_image_path:
                try:
                    os.remove(widget.current_image_path)
                except OSError:
                    pass
                widget.current_image_path = None
            
            # Update status count
            filled_count = sum(1 for w in self.image_widgets if w.image_label.pixmap() is not None and not w.image_label.pixmap().isNull())
            self.current_image_count = filled_count
            self.update_status(f"Image Deleted. ({filled_count}/{self.total_images})")

    def closeEvent(self, event):
        self.camera_thread.stop()
        if hasattr(self, 'input_listener'):
            self.input_listener.stop()
        event.accept()
