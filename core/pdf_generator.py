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
        pass

    def generate_report(self, pid, session_path, model_name="N/A", inspector_name="N/A"):
        """
        Tạo file PDF báo cáo PCBA Quality Inspection Sheet.
        Form giống như ảnh mẫu.
        """
        pdf_filename = f"{pid}_Report.pdf"
        pdf_path = os.path.join(session_path, pdf_filename)
        
        # Setup page landscape A4
        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4),
                                rightMargin=10, leftMargin=10,
                                topMargin=5, bottomMargin=5)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # --- TITLE ---
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, spaceAfter=0)
        
        # Header Table (Info)
        # Format:
        # PCBA Quality Inspection Sheet               Date: ...
        # 1. Model(SMT): ...
        # 2. PID(SMT): ...
        # ...
        
        date_str = datetime.now().strftime("%d , %m , %Y")
        
        header_data = [
            [Paragraph("PCBA Quality Inspection Sheet", title_style), "", f"Date :  {date_str}"],
            ["1. Model(SMT) :", model_name, ""],
            ["2. PID(SMT) :", pid, ""],
            ["3. Inspector(SMT) :", inspector_name, ""],
            ["4. Inspection Points :", Paragraph("SMT – Flux Impurities, Pin Hole, Bridge, Via Hole, Impurities, Solder Ball<br/>PCBA – Solder Ball, Coating", styles['Normal']), ""]
        ]
        
        t_header = Table(header_data, colWidths=[2*inch, 5*inch, 3*inch])
        t_header.setStyle(TableStyle([
            ('SPAN', (0,0), (1,0)), # Span Title
            ('ALIGN', (2,0), (2,0), 'RIGHT'), # Date align right
            ('FONTSIZE', (0,0), (-1,-1), 9), # Reduce font size
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1), # Reduce padding
            ('TOPPADDING', (0,0), (-1,-1), 1),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 2)) # Smaller spacer

        # --- MAIN TABLE ---
        # Columns: Dept, Subject, Item, Criteria, NG Example, Inspection Point (4 cols), Result, Note
        # Headers spanning logic is complex, so we will build row by row.
        
        # Helper to get image or placeholder
        def get_image(filename):
            path = os.path.join(session_path, filename)
            if os.path.exists(path):
                img = Image(path)
                img.drawHeight = 0.55 * inch # Reduced height
                img.drawWidth = 0.85 * inch
                return img
            return "" # Empty if missing

        # Row Data Structure
        # 0: Dept, 1: Subject, 2: Item, 3: Criteria, 4: NG Ex, 5,6,7,8: Insp Pts, 9: Result, 10: Note
        
        # Define rows content
        # Cat 1: Surface
        row_surface = [
            "SMT\n\nMicroscope\nInspection", # Dept (will span)
            "Flux\nImpurities", "Surface of PCB", "No fallen Flux", "",
            get_image("1_Surface_of_PCB_1.jpg"), get_image("1_Surface_of_PCB_2.jpg"), 
            get_image("1_Surface_of_PCB_3.jpg"), get_image("1_Surface_of_PCB_4.jpg"),
            "PASS", ""
        ]
        
        # Cat 2: Chip
        row_chip = [
            "", # Spanned
            "Pin Hole", "Chip Part", "No Pin Hole", "",
            get_image("2_Chip_Part_1.jpg"), get_image("2_Chip_Part_2.jpg"), 
            get_image("2_Chip_Part_3.jpg"), get_image("2_Chip_Part_4.jpg"),
            "PASS", ""
        ]
        
        # Cat 3: Bridge
        row_bridge = [
            "", "Bridge", "QFP or\nConnector", "No Bridge", "",
            get_image("3_Connector_or_QFP_1.jpg"), get_image("3_Connector_or_QFP_2.jpg"), 
            get_image("3_Connector_or_QFP_3.jpg"), get_image("3_Connector_or_QFP_4.jpg"),
            "PASS", ""
        ]
        
        # Cat 4: Via Hole
        row_via = [
            "", "Via hole", "Boss Hole", "No Decolor-\nation\nNo Corrosion", "",
            get_image("4_Boss_Hole_1.jpg"), get_image("4_Boss_Hole_2.jpg"), 
            get_image("4_Boss_Hole_3.jpg"), get_image("4_Boss_Hole_4.jpg"),
            "PASS", ""
        ]
        
        # Cat 5: Impurities
        row_impur = [
            "", "Impurities", "BGA or QFP\nor Connector", "No Dirt, No Lint,\nNo Dross", "",
            get_image("5_BGA_QFP_Connector_1.jpg"), get_image("5_BGA_QFP_Connector_2.jpg"), 
            get_image("5_BGA_QFP_Connector_3.jpg"), get_image("5_BGA_QFP_Connector_4.jpg"),
            "PASS", ""
        ]
        
        # Cat 6: Solder Ball (Around PAD)
        row_ball1 = [
            "", "Solder Ball", "Around the PAD", "Size : < 0.13mm\nQty : < 5ea/600mm²", "",
            get_image("6_Around_the_PAD_1.jpg"), get_image("6_Around_the_PAD_2.jpg"), 
            get_image("6_Around_the_PAD_3.jpg"), get_image("6_Around_the_PAD_4.jpg"),
            "PASS", ""
        ]
        
        # Cat 7: Solder Ball (Handwork) - PCBA Dept starts here? No, in template PCBA starts later. 
        # Wait, template says "Non-Destructive Inspection" covers all.
        # But Dept column splits 'SMT' and 'PCBA'.
        # Let's adjust based on template row counts.
        # SMT covers row 1-6. PCBA covers row 7-9.
        
        # Cat 7 (Manual/Skipped): Around Handwork Parts
        row_handwork = [
            "PCBA\n\nMicroscope\nInspection", "Solder Ball", "Around the\nHandwork Parts", "Size : < 0.13mm\nQty : < 5ea/600mm²", "",
            "", "", "", "", # Empty images
            "N/A", "No\nhandwork\npart"
        ]
        
        # Cat 8 (Captures): Between IC Lead (Coating)
        row_coating = [
            "", "Coating", "Between IC\nLead\n(Ex : QFP)", "Bubble Dia < 50%\nof Clearance\n(20x Mag)", "",
            get_image("8_Between_IC_Lead_1.jpg"), get_image("8_Between_IC_Lead_2.jpg"), 
            get_image("8_Between_IC_Lead_3.jpg"), get_image("8_Between_IC_Lead_4.jpg"),
            "PASS", ""
        ]
        
        # Cat 9 (XRay): Hole Fill
        row_hole = [
            "X-Ray\nInspection", "Hole Fill", "Insertion Parts", "Filing Rate :\n75% or More", "",
            "", "", "", "",
            "PASS", ""
        ]

        # Table Header Row
        headers = ["Dept.", "Subject", "Item", "Criteria", "NG Example", "Inspection Point (4 Point)", "", "", "", "Result", "Note"]
        
        data = [headers, row_surface, row_chip, row_bridge, row_via, row_impur, row_ball1, row_handwork, row_coating, row_hole]
        
        # Column Widths
        # Total A4 Landscape Width ~ 11.7 inch. Margins 0.5 inch total. Usable ~11 inch.
        # Cols: 0.8, 0.8, 1.0, 1.5, 0.8, 0.9*4=3.6, 0.5, 1.0
        c_widths = [0.8*inch, 0.8*inch, 1.1*inch, 1.6*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.6*inch, 1.0*inch]
        
        t = Table(data, colWidths=c_widths)
        
        # Styles
        style = [
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            
            # Header
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('SPAN', (5,0), (8,0)), # Merge "Inspection Point (4 Point)" header
            
            # Spans for Dept 'SMT' (Rows 1-6) -> Index 1 to 6
            ('SPAN', (0,1), (0,6)), 
            # Spans for Dept 'PCBA' (Rows 7-8) -> Index 7 to 8
            ('SPAN', (0,7), (0,8)),
            
            # Merge Images cells into one block? No, keep separate 4 cells.
            
            # Text Wrap for Criteria
            # ('WORDWRAP', (3,1), (3,-1)), # Reportlab table auto wraps if Paragraph used, but str wraps on space.
        ]
        
        # Color specific cells (Note column green for N/A)
        # Row 7 (Handwork) Result N/A -> Note Green text?
        # Let's just keep simple text.
        
        t.setStyle(TableStyle(style))
        
        elements.append(t)
        
        # Footer
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Inspect periodically (AOI Inspector)", styles['Normal']))
        elements.append(Paragraph("Report any problems during inspection immediately (Managers / Supervisors)", styles['Normal']))

        try:
            doc.build(elements)
            print(f"PDF generated: {pdf_path}")
            return pdf_path
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
