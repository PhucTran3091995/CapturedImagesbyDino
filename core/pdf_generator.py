import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class PDFGenerator:
    """
    Class tạo báo cáo PDF từ các ảnh đã chụp.
    """
    def __init__(self):
        # Base path for static resources
        self.base_path = os.getcwd() # Assumption: running from app root
        self.pdf_image_path = os.path.join(self.base_path, "pdf image")

    def generate_report(self, pid, session_path, model_name="N/A", inspector_name="N/A"):
        """
        Tạo file PDF báo cáo Socket Inspection Report.
        Format: 2 hàng x 4 cột ảnh cho mỗi mục. Full A4 page height.
        """
        # Register Font
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        font_name = 'Helvetica'
        try:
            font_path = "C:\\Windows\\Fonts\\arial.ttf"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                font_name = 'Arial'
        except Exception:
            pass

        pdf_filename = f"{pid}_Report.pdf"
        pdf_path = os.path.join(session_path, pdf_filename)
        
        # A4 Landscape: 297mm x 210mm (~11.7 x 8.3 inch)
        # Margins: 0.2 inch
        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4),
                                rightMargin=0.2*inch, leftMargin=0.2*inch,
                                topMargin=0.2*inch, bottomMargin=0.2*inch)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName=font_name, fontSize=20, spaceAfter=5)
        info_style = ParagraphStyle('Info', parent=styles['Normal'], fontName=font_name, fontSize=11, leading=14)
        
        # --- TITLE ---
        date_str = datetime.now().strftime("%d , %m , %Y")
        
        header_table_data = [
            [Paragraph("Socket Inspection Report", title_style), 
             Paragraph(f"Date :  {date_str}", ParagraphStyle('Date', parent=styles['Normal'], fontName=font_name, fontSize=12, alignment=2))]
        ]
        t_title = Table(header_table_data, colWidths=[8*inch, 3.2*inch])
        t_title.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(t_title)
        elements.append(Spacer(1, 0.1*inch))
        
        # --- INFO ---
        elements.append(Paragraph(f"1.&nbsp;&nbsp;&nbsp;Socket Infor : &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{pid}", info_style))
        elements.append(Paragraph(f"2.&nbsp;&nbsp;&nbsp;Inspector(IQC) : &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{inspector_name}", info_style))
        # Shorten text to fit line if needed or keep full
        inspection_points_text = "Linh kiện của adapter, Bụi bẩn, Các chân tiếp xúc của socket, Các điểm tiếp nối"
        elements.append(Paragraph(f"3.&nbsp;&nbsp;&nbsp;Inspection Points : &nbsp;&nbsp;&nbsp;{inspection_points_text}", info_style))
        
        elements.append(Spacer(1, 0.15*inch))

        # --- MAIN TABLE ---
        # Structure:
        # Dept(3) | Item | Criteria | NGEx | P1 | P2 | P3 | P4 | Result | Note
        # 12 Columns Total
        
        def get_captured_image(cat_idx, point_idx):
            cat_names = [
                "1_Linh_kiện_của_adapter", "2_Bụi_bẩn",
                "3_Các_chân_tiếp_xúc_của_socket", "4_Các_điểm_tiếp_nối"
            ]
            if cat_idx < 0 or cat_idx >= len(cat_names): return ""
            target_suffix = f"{cat_names[cat_idx]}_{point_idx}.jpg"
            
            # Find file
            found_file = None
            if os.path.exists(session_path):
                for f in os.listdir(session_path):
                    if f.endswith(target_suffix):
                        found_file = os.path.join(session_path, f)
                        break
            
            if found_file:
                # Resize logic: 
                # Cell size is roughly 1.3 inch width, 0.65 inch height (reduced to fit page)
                img = Image(found_file)
                img.drawHeight = 0.58 * inch 
                img.drawWidth = 1.0 * inch # Slightly narrower to be safe
                return img
            return ""

        def get_static_image(filename):
            path = os.path.join(self.pdf_image_path, filename)
            if os.path.exists(path):
                img = Image(path)
                img.drawHeight = 1.15 * inch # Fit within 2 rows of 0.65 (1.3 total)
                img.drawWidth = 1.1 * inch 
                return img
            return "Image not found"

        # Headers
        # Span Pts 1-4 (cols 6-9)
        header_row = [
            "Dept.", "", "", 
            "Item", "Criteria", "NG Example", 
            "Inspection Point (8 Point)", "", "", "", 
            "Result", "Note"
        ]
        
        # We have 4 Categories (Items). Each Item has 2 Rows.
        # Total Data Rows: 8 rows.
        # Plus Header: 1 row.
        # Total Table Rows: 9 rows.
        
        # Dept text only on first row, will span down 8 rows.
        
        data = [header_row]
        
        categories_info = [
            ("Linh kiện của\nadapter", "Không vỡ,\nkhông cầu", "Adapter Components.png"),
            ("Bụi bẩn", "Không có dị\nvật, không có\nbụi bẩn", "Foreign material.png"),
            ("Các chân tiếp xúc\ncủa socket", "Không biến\ndạng, không\nxước, không\nhỏng", "Pin.png"),
            ("Các điểm tiếp nối", "Không biến\ndạng, không\nxước, không\nhỏng", "Pad.png")
        ]
        
        dept_texts = ["Non-\nDestructive\nInspection", "IQC", "Microscope\nInspection"]
        
        for cat_idx, (item, criteria, ng_img) in enumerate(categories_info):
            # Row 1 of Item
            row1 = [
                dept_texts[0] if cat_idx == 0 else "",
                dept_texts[1] if cat_idx == 0 else "",
                dept_texts[2] if cat_idx == 0 else "",
                item, criteria, get_static_image(ng_img),
                # Images 1-4
                get_captured_image(cat_idx, 1), get_captured_image(cat_idx, 2),
                get_captured_image(cat_idx, 3), get_captured_image(cat_idx, 4),
                "PASS", ""
            ]
            
            # Row 2 of Item
            row2 = [
                "", "", "", 
                "", "", "", # Spanned cells
                # Images 5-8
                get_captured_image(cat_idx, 5), get_captured_image(cat_idx, 6),
                get_captured_image(cat_idx, 7), get_captured_image(cat_idx, 8),
                "", "" # Spanned Result/Note
            ]
            data.append(row1)
            data.append(row2)

        # Column Widths
        # Page usable width ~11.3 inch
        # Dept(3): 0.6, 0.4, 0.7 = 1.7
        # Item: 1.1
        # Criteria: 1.1
        # NGEx: 1.3
        # Pt(4): 1.2 * 4 = 4.8
        # Result: 0.6
        # Note: 0.7
        # Total: 11.3 -> Perfect
        
        col_widths = [
            0.6*inch, 0.4*inch, 0.7*inch,
            1.1*inch, 1.1*inch, 1.3*inch,
            1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch,
            0.6*inch, 0.7*inch
        ]
        
        # Row Heights
        # Reduce rows to fit one page.
        # Header 0.4.
        # Rows: 0.65 * 8 = 5.2.
        # Total = 5.6 inch Table.
        row_heights = [0.4*inch] + [0.65*inch]*8 
        
        t = Table(data, colWidths=col_widths, rowHeights=row_heights)
        
        # Styling
        style = [
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('FONTNAME', (0,0), (-1,-1), font_name),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            
            # Header
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('SPAN', (0,0), (2,0)), # Merge Dept Header
            ('SPAN', (6,0), (9,0)), # Merge Inspection Point Header (cols 6,7,8,9)
            
            # Dept Vertical Spans (All 8 data rows: 1 to 8)
            ('SPAN', (0,1), (0,8)),
            ('SPAN', (1,1), (1,8)),
            ('SPAN', (2,1), (2,8)),
        ]
        
        # Loop to add spans for each Category (2 rows each)
        # Cat 0: Rows 1-2
        # Cat 1: Rows 3-4
        # ...
        for i in range(4):
            start_row = 1 + i*2
            end_row = start_row + 1
            # Item
            style.append(('SPAN', (3, start_row), (3, end_row)))
            # Criteria
            style.append(('SPAN', (4, start_row), (4, end_row)))
            # NG Example
            style.append(('SPAN', (5, start_row), (5, end_row)))
            # Result
            style.append(('SPAN', (10, start_row), (10, end_row)))
            # Note
            style.append(('SPAN', (11, start_row), (11, end_row)))
        
        t.setStyle(TableStyle(style))
        elements.append(t)
        
        # Footer
        elements.append(Spacer(1, 0.1*inch)) # Reduced spacer
        elements.append(Paragraph("Inspect periodically (IQC Inspector)", 
                                  ParagraphStyle('Footer', parent=styles['Normal'], fontName=font_name, fontSize=10)))
        elements.append(Paragraph("Report any problems during inspection immediately (Managers / Supervisors)", 
                                  ParagraphStyle('Footer2', parent=styles['Normal'], fontName=font_name, fontSize=10)))

        try:
            doc.build(elements)
            print(f"PDF generated: {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
