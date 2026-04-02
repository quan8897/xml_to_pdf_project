import os
import xml.etree.ElementTree as ET
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 1. ĐĂNG KÝ FONT TIẾNG VIỆT (Sử dụng font hệ thống Windows)
FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont('Arial-VN', FONT_PATH))
    pdfmetrics.registerFont(TTFont('Arial-Bold-VN', r"C:\Windows\Fonts\arialbd.ttf"))
else:
    print("Warning: Arial font not found, using default (Unicode might fail).")

def xml_to_dict(element):
    """Chuyển XML thành dictionary để dễ xử lý định dạng"""
    result = {}
    for child in element:
        if len(child) > 0:
            value = xml_to_dict(child)
        else:
            value = child.text
        
        if child.tag in result:
            if isinstance(result[child.tag], list):
                result[child.tag].append(value)
            else:
                result[child.tag] = [result[child.tag], value]
        else:
            result[child.tag] = value
    return result

def create_tax_pdf(xml_path, output_pdf):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return

    doc = SimpleDocTemplate(output_pdf, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Định dạng style Tiếng Việt
    vn_style = ParagraphStyle(
        name='Vietnamese',
        fontName='Arial-VN',
        fontSize=10,
        leading=12
    )
    vn_title = ParagraphStyle(
        name='VietnameseTitle',
        fontName='Arial-Bold-VN',
        fontSize=18,
        alignment=1,
        spaceAfter=20
    )

    elements = []

    # Tiêu đề hồ sơ thuế
    title_text = root.tag.upper().replace('_', ' ')
    elements.append(Paragraph(f"BÁO CÁO DỮ LIỆU THUẾ: {title_text}", vn_title))
    elements.append(Spacer(1, 10))

    # Hàm đệ quy để vẽ các bảng dữ liệu giữ nguyên cấu trúc XML
    def build_structure(data, level=0):
        table_data = []
        for key, value in data.items():
            display_key = key.upper()
            if isinstance(value, dict):
                elements.append(Paragraph(f"<b>{'  ' * level}[+] {display_key}</b>", vn_style))
                build_structure(value, level + 1)
            elif isinstance(value, list):
                elements.append(Paragraph(f"<b>{'  ' * level}[List] {display_key}</b>", vn_style))
                for item in value:
                    if isinstance(item, dict):
                        build_structure(item, level + 1)
                        elements.append(Spacer(1, 5))
            else:
                table_data.append([Paragraph(f"<b>{display_key}</b>", vn_style), Paragraph(str(value) if value else "", vn_style)])

        if table_data:
            t = Table(table_data, colWidths=[150, 350])
            t.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
                ('LEFTPADDING', (0,0), (-1,-1), 5),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 10))

    # Bắt đầu dựng cấu trúc
    data_dict = xml_to_dict(root)
    build_structure(data_dict)

    doc.build(elements)
    print(f"--- Đã tạo thành công hồ sơ thuế Việt Nam: {output_pdf} ---")

if __name__ == "__main__":
    # Thay đổi đường dẫn này tới file XML thuế của bạn
    INPUT_DIR = r'C:\Users\ACER\.gemini\antigravity\scratch\xml_to_pdf_project\input'
    OUTPUT_DIR = r'C:\Users\ACER\.gemini\antigravity\scratch\xml_to_pdf_project\output'
    
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    for f in os.listdir(INPUT_DIR):
        if f.endswith('.xml'):
            print(f"Đang xử lý hồ sơ thuế: {f}...")
            create_tax_pdf(os.path.join(INPUT_DIR, f), os.path.join(OUTPUT_DIR, f.replace('.xml', '.pdf')))
