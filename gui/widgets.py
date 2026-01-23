from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QDialog, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
import cv2

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class ZoomDialog(QDialog):
    def __init__(self, image_path, title="Zoom Image", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            img_label.setPixmap(pixmap)
            # Adjust window size if image is smaller
            if pixmap.width() < 800 and pixmap.height() < 600:
                self.resize(pixmap.width() + 50, pixmap.height() + 50)
        else:
            img_label.setText("Image not found")
            
        scroll_area.setWidget(img_label)
        layout.addWidget(scroll_area)

class ImageBox(QWidget):
    """
    Widget hiển thị một ô ảnh (thumbnail) với tiêu đề.
    """
    clicked = pyqtSignal(str) # Signal emit khi click vào box (optional hook)
    right_clicked = pyqtSignal(object) # Signal emit khi right click, send self

    def __init__(self, title="Image", parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(2)
        
        # Frame bao ngoài để tạo viền
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Shape.Box)
        self.frame.setFrameShadow(QFrame.Shadow.Plain)
        self.frame.setLineWidth(1)
        
        self.frame_layout = QVBoxLayout(self.frame)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame_layout.setSpacing(0)

        # Label hiển thị ảnh
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #e0e0e0;") # Placeholder color
        self.image_label.setMinimumSize(80, 60) # Kích thước tối thiểu
        self.image_label.setScaledContents(False) # Tắt auto-stretch làm méo ảnh


        # Label tiêu đề (VD: Top 1, Bot 1)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 10px;")

        self.frame_layout.addWidget(self.image_label, stretch=1)
        self.frame_layout.addWidget(self.title_label, stretch=0)

        self.layout.addWidget(self.frame)
        self.setLayout(self.layout)
        
        # FIX: Set fixed size to avoid ugly stretching when maximized
        self.setFixedSize(110, 90)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(self)
        super().mousePressEvent(event)
    
    def set_image(self, image_path=None, cv_img=None):
        """
        Hiển thị ảnh lên label. Hỗ trợ cả đường dẫn file hoặc ảnh OpenCV.
        """
        pixmap = None
        if cv_img is not None:
            # Convert OpenCV image (BGR) to QPixmap
            height, width, channel = cv_img.shape
            bytes_per_line = 3 * width
            q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
        elif image_path:
            pixmap = QPixmap(image_path)
        
        if pixmap and not pixmap.isNull():
            # Scale ảnh vừa khung nhưng giữ tỉ lệ
            scaled_pixmap = pixmap.scaled(self.image_label.size(), 
                                          Qt.AspectRatioMode.KeepAspectRatio, 
                                          Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.clear()
            self.image_label.setText("No Image")

    def reset(self):
        """Reset về trạng thái ban đầu"""
        self.image_label.clear()
        self.image_label.setStyleSheet("background-color: #e0e0e0;")
