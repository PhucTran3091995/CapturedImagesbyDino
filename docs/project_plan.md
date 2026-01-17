# Kế hoạch Triển khai Ứng dụng Chụp ảnh Dino-Lite

## Mục tiêu
Xây dựng ứng dụng desktop cho Windows để hỗ trợ quy trình chụp hình QC (Quality Control) sản phẩm. Ứng dụng sẽ kết nối với kính hiển vi Dino-Lite (hoặc webcam tương đương), tự động đọc mã PID qua barcode/QR code, và hỗ trợ chụp 16 ảnh (mặt Top/Bot) lưu vào thư mục định danh theo PID.

## Yêu cầu Người dùng
> [!IMPORTANT]
> 1. Sử dụng Camera Dino-Lite.
> 2. Đọc PID bằng thư viện ZXing.
> 3. Giao diện chia 16 ô nhỏ (8 Top, 8 Bot).
> 4. Lưu ảnh vào folder tên PID.
> 5. Nút chụp trên thiết bị Dino sẽ kích hoạt chụp (sẽ mô phỏng bằng phím tắt nếu không có SDK chuyên dụng).
> 6. Nút Export PDF: Xuất file `{PID}.pdf` chứa bảng ảnh Top/Bot.

## Đề xuất Thay đổi

### Công nghệ
- **Ngôn ngữ**: Python 3.10+
- **Giao diện (UI)**: PyQt6 (Hiện đại, mượt mà, dễ tùy biến layout lưới).
- **Xử lý ảnh**: OpenCV (cv2).
- **Đọc Barcode**: `zxing-cpp` (Binding Python hiệu năng cao của thư viện ZXing C++).
- **Tạo PDF**: `reportlab`.
- **Cấu trúc thư mục**:
  ```text
  app/
  ├── main.py            # Entry point
  ├── gui/
  │   ├── main_window.py # Giao diện chính
  │   └── widgets.py     # Các custom widget (ô ảnh)
  ├── core/
  │   ├── camera.py      # Class xử lý luồng camera OpenCV
  │   ├── scanner.py     # Wrapper cho zxing-cpp
  │   ├── storage.py     # Quản lý lưu file ảnh
  │   └── pdf_generator.py # [MỚI] Module tạo file PDF
  └── requirements.txt
  ```

### Giao diện Người dùng (UI Design)
- **Bố cục chính**: 
    - **Bên Trái (hoặc Giữa)**: Live View từ Camera (Kích thước lớn để dễ soi).
    - **Bên Phải**: Lưới 2x8 hoặc 4x4 chia làm 2 nhóm:
        - Group "Mặt Top": 8 ô.
        - Group "Mặt Bot": 8 ô.
- **Trạng thái**:
    - Label hiển thị "PID: [Đang chờ quét...]" hoặc "PID: ABC12345".
    - Progress bar hoặc chỉ số đếm số ảnh đã chụp (Ví dụ: 3/16).

### Luồng Hoạt động (Workflow)
1. **Khởi động**: Mở app, camera tự động bật.
2. **Quét PID**: 
    - Người dùng đưa mã code vào camera.
    - Hệ thống tự động detect PID (ZXing).
    - Khi detect thành công: Phát âm thanh beep (option), khóa PID, tạo folder `Images/{PID}/`.
3. **Chụp ảnh**:
    - Người dùng di chuyển Dino soi vị trí lỗi/chi tiết.
    - Ấn nút chụp (Spacebar hoặc nút trên UI).
    - Ảnh được lưu ngay lập tức vào `Images/{PID}/1_top.jpg`, `2_top.jpg`...
    - Thumbnail hiện lên ô tương ứng trên UI.
4. **Xuất báo cáo (Tùy chọn)**:
    - Ấn nút "Export PDF".
    - Tạo file `{PID}.pdf` trong cùng thư mục (hoặc thư mục Reports).
    - File PDF chứa thông tin PID và bảng 2 dòng (Top/Bot) các ảnh đã chụp.
5. **Hoàn tất/Reset**:
    - Sau khi đủ 16 ảnh hoặc người dùng ấn "New Session", reset lại trạng thái PID để quét mã mới.

### Xử lý Nút chụp Dino-Lite
> [!NOTE]
> Các thiết bị Dino-Lite thường đi kèm phần mềm DinoCapture. Để nút cứng trên thiết bị hoạt động với phần mềm thứ 3, thông thường cần MicroTouch driver hoặc dùng SDK.
> Trong phạm vi Python đơn thuần, chúng ta sẽ map phím **Space** hoặc **Enter** làm phím chụp (Trigger). Nếu nút trên Dino có thể map thành phím bấm hệ thống, nó sẽ hoạt động plug-and-play.
