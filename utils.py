import os
import xml.etree.ElementTree as ET
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_fonts():
    """Đăng ký font Unicode hỗ trợ Tiếng Việt."""
    font_paths = [
        "Roboto-Regular.ttf", # Ưu tiên font trong project
        "arial.ttf",
        r"C:\Windows\Fonts\arial.ttf", # Windows fallback
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", # Debian/Ubuntu fallback
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", # Linux fallback
    ]
    font_bold_paths = [
        "Roboto-Bold.ttf",
        "arialbd.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    
    selected_font = None
    for f in font_paths:
        if os.path.exists(f):
            selected_font = f
            break
            
    selected_bold = None
    for fb in font_bold_paths:
        if os.path.exists(fb):
            selected_bold = fb
            break

    if selected_font:
        pdfmetrics.registerFont(TTFont('VN-Font', selected_font))
        if selected_bold:
            pdfmetrics.registerFont(TTFont('VN-Font-Bold', selected_bold))
        else:
            pdfmetrics.registerFont(TTFont('VN-Font-Bold', selected_font))
        return True
    return False

def strip_ns(tag):
    """Loại bỏ phần Namespace {http://...} lằng nhằng khỏi tên thẻ."""
    if tag is not None and '}' in tag:
        return tag.split('}')[-1]
    return tag

def xml_to_dict(element):
    """Chuyển XML thành dictionary và làm sạch Namespace."""
    result = {}
    for child in element:
        tag_cleaned = strip_ns(child.tag)
        if len(child) > 0:
            value = xml_to_dict(child)
        else:
            value = child.text
            
        if tag_cleaned in result:
            if isinstance(result[tag_cleaned], list): result[tag_cleaned].append(value)
            else: result[tag_cleaned] = [result[tag_cleaned], value]
        else:
            result[tag_cleaned] = value
    return result

def generate_tax_pdf(xml_content, title="BÁO CÁO THUẾ"):
    if isinstance(xml_content, bytes):
        root = ET.fromstring(xml_content)
    else:
        tree = ET.parse(xml_content)
        root = tree.getroot()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    
    font_ready = register_fonts()
    font_name = 'VN-Font' if font_ready else 'Helvetica'
    font_bold = 'VN-Font-Bold' if font_ready else 'Helvetica-Bold'

    vn_style = ParagraphStyle(name='VN', fontName=font_name, fontSize=10, leading=12)
    vn_title = ParagraphStyle(name='VNTitle', fontName=font_bold, fontSize=18, alignment=1, spaceAfter=20)

    elements = []
    # Làm sạch Root tag cho tiêu đề
    root_tag_cleaned = strip_ns(root.tag).upper()
    header_text = f"{title}: {root_tag_cleaned}"
    elements.append(Paragraph(header_text, vn_title))
    
    def build_structure(data, level=0):
        table_data = []
        for key, value in data.items():
            display_key = key.upper()
            if isinstance(value, dict):
                elements.append(Paragraph(f"<b>{'&nbsp;'*level*4}[+] {display_key}</b>", vn_style))
                build_structure(value, level + 1)
            elif isinstance(value, list):
                elements.append(Paragraph(f"<b>{'&nbsp;'*level*4}[List] {display_key}</b>", vn_style))
                for item in value:
                    if isinstance(item, dict):
                        build_structure(item, level + 1)
                        elements.append(Spacer(1, 5))
            else:
                table_data.append([
                    Paragraph(f"<b>{display_key}</b>", vn_style), 
                    Paragraph(str(value) if value is not None else "", vn_style)
                ])
        
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

    build_structure(xml_to_dict(root))
    doc.build(elements)
    buffer.seek(0)
    return buffer
