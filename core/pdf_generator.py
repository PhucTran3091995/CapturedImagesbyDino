import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class PDFGenerator:
    """
    Class tạo báo cáo PDF từ các ảnh đã chụp.
    """
    def __init__(self):
        pass

    def generate_report(self, pid, session_path):
        """
        Tạo file PDF báo cáo tại session_path.
        Args:
            pid (str): Mã sản phẩm
            session_path (str): Đường dẫn folder chứa ảnh
        Returns:
            str: Đường dẫn file PDF đã tạo
        """
        pdf_filename = f"{pid}.pdf"
        pdf_path = os.path.join(session_path, pdf_filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4),
                                rightMargin=30, leftMargin=30,
                                topMargin=30, bottomMargin=30)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # 1. Header: PID Info
        title_style = ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            alignment=1, # Center
            spaceAfter=20
        )
        elements.append(Paragraph(f"Inspection Report: {pid}", title_style))
        elements.append(Paragraph(f"Date: {os.path.basename(session_path)}", styles['Normal'])) # Giả sử tên folder có info date hoặc dùng datetime
        elements.append(Spacer(1, 20))

        # 2. Prepare Images Logic
        # Chúng ta cần hiển thị 16 ảnh: 8 Top (Row 1+2?), 8 Bot.
        # Layout bảng: 
        # Row 1: Header "Top Surface"
        # Row 2: 4 ảnh Top 1-4
        # Row 3: 4 ảnh Top 5-8
        # Row 4: Header "Bottom Surface"
        # Row 5: 4 ảnh Bot 1-4
        # Row 6: 4 ảnh Bot 5-8
        
        # Helper để load ảnh resize
        def get_image(filename):
            path = os.path.join(session_path, filename)
            if os.path.exists(path):
                img = Image(path)
                img.drawHeight = 1.8 * inch # Chiều cao cố định
                img.drawWidth = 2.4 * inch  # Chiều rộng cố định (tỉ lệ 4:3)
                return img
            return Paragraph("Missing", styles['Normal'])

        # --- Top Section ---
        elements.append(Paragraph("Top Surface", styles['Heading2']))
        
        data_top_1 = [get_image(f"{i}_top.jpg") for i in range(1, 5)]
        data_top_2 = [get_image(f"{i}_top.jpg") for i in range(5, 9)]
        
        table_top = Table([data_top_1, data_top_2])
        table_top.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BottomPadding', (0,0), (-1,-1), 5),
            ('TopPadding', (0,0), (-1,-1), 5),
        ]))
        elements.append(table_top)
        elements.append(Spacer(1, 20))

        # --- Bot Section ---
        elements.append(Paragraph("Bottom Surface", styles['Heading2']))
        
        data_bot_1 = [get_image(f"{i}_bot.jpg") for i in range(1, 5)]
        data_bot_2 = [get_image(f"{i}_bot.jpg") for i in range(5, 9)]
        
        table_bot = Table([data_bot_1, data_bot_2])
        table_bot.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BottomPadding', (0,0), (-1,-1), 5),
            ('TopPadding', (0,0), (-1,-1), 5),
        ]))
        elements.append(table_bot)

        # Build PDF
        try:
            doc.build(elements)
            return pdf_path
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
