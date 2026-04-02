import os
import xml.etree.ElementTree as ET
import io
import re
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def strip_ns(tag):
    if tag is not None and '}' in tag:
        return tag.split('}')[-1]
    return tag

def pre_process_xml(xml_content):
    if isinstance(xml_content, bytes):
        xml_str = xml_content.decode('utf-8', errors='ignore')
    else:
        xml_str = xml_content
    xml_str = re.sub(r'&(?!(?:amp|lt|gt|quot|apos);)', '&amp;', xml_str)
    return xml_str.encode('utf-8')

def extract_tax_metadata(xml_content):
    try:
        root = ET.fromstring(pre_process_xml(xml_content))
        mst = "Unknown"
        ky_thue = "Unknown"
        ten_tk = "TỜ KHAI THUẾ"
        mau_so = "01/TTS"
        
        for elem in root.iter():
            tag_name = strip_ns(elem.tag).upper()
            if tag_name in ['MAMST', 'MST']: mst = elem.text or mst
            if tag_name == 'THANGKKHAI' and elem.text: ky_thue = f"T{elem.text}"
            elif tag_name == 'QUYKKHAI' and elem.text: ky_thue = f"Q{elem.text}"
            elif tag_name == 'NAMKKHAI' and elem.text:
                ky_thue = f"{ky_thue}/{elem.text}" if 'Unknown' not in ky_thue else elem.text
            if tag_name in ['TENTKHAI', 'TEN_LOAI_HDON']: ten_tk = elem.text or ten_tk

        return {"name": ten_tk, "mst": mst, "period": ky_thue, "form": mau_so}
    except:
        return {"name": "TỜ KHAI THUẾ", "mst": "Unknown", "period": "Unknown", "form": "01/TTS"}

def format_value(value):
    if value is None: return ""
    val_str = str(value).strip()
    if not val_str: return ""
    
    # Kiểm tra xem có phải định dạng số không (để thêm dấu chấm hàng nghìn)
    if val_str.replace('.', '', 1).replace('-', '', 1).isdigit() and len(val_str) < 15:
        try:
            val_num = float(val_str)
            if val_num == int(val_num):
                return "{:,}".format(int(val_num)).replace(',', '.')
            else:
                return "{:,.2f}".format(val_num).replace(',', 'X').replace('.', ',').replace('X', '.')
        except: pass
    return val_str.replace('\n', '<br/>')

def register_fonts():
    font_paths = ["Roboto-Regular.ttf", "arial.ttf", r"C:\Windows\Fonts\arial.ttf"]
    for f in font_paths:
        if os.path.exists(f):
            try:
                pdfmetrics.registerFont(TTFont('VN-Font', f))
                pdfmetrics.registerFont(TTFont('VN-Font-Bold', f))
                return True
            except: continue
    return False

def xml_to_dict(element):
    result = {}
    for child in element:
        tag = strip_ns(child.tag)
        # Sửa lỗi: Nếu len(child) == 0 nhưng child.text cũng None
        value = xml_to_dict(child) if len(child) > 0 else (child.text if child.text is not None else "")
        if tag in result:
            if not isinstance(result[tag], list): result[tag] = [result[tag]]
            result[tag].append(value)
        else: result[tag] = value
    return result

def generate_tax_pdf(xml_content, title="BÁO CÁO THUẾ"):
    clean_xml = pre_process_xml(xml_content)
    root = ET.fromstring(clean_xml)
    meta = extract_tax_metadata(xml_content)
    data_dict = xml_to_dict(root)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
    
    register_fonts()
    f_name, f_bold = 'VN-Font', 'VN-Font-Bold'
    
    # Styles
    s_normal = ParagraphStyle(name='Normal', fontName=f_name, fontSize=9, leading=12)
    s_bold = ParagraphStyle(name='Bold', fontName=f_bold, fontSize=9, leading=12)
    s_title = ParagraphStyle(name='Title', fontName=f_bold, fontSize=14, alignment=1, spaceAfter=10)
    s_motto = ParagraphStyle(name='Motto', fontName=f_bold, fontSize=10, alignment=1)
    s_box = ParagraphStyle(name='Box', fontName=f_name, fontSize=8, alignment=1)

    elements = []

    # 1. HEADER
    t_header = Table([
        [Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>Độc lập - Tự do - Hạnh phúc", s_motto), 
         Table([[Paragraph(f"<b>Mẫu số: {meta['form']}</b>", s_box)]], style=[('GRID', (0,0), (-1,-1), 0.5, colors.black)])]
    ], colWidths=[350, 150])
    elements.append(t_header)
    elements.append(Spacer(1, 15))

    # 2. TITLE
    elements.append(Paragraph(meta['name'].upper(), s_title))
    elements.append(Paragraph(f"Kỳ tính thuế: {meta['period']}", ParagraphStyle(name='Sub', fontName=f_name, fontSize=10, alignment=1, spaceAfter=15)))

    # 3. RENDER FIELDS (THÔNG TIN CHUNG)
    info_data = {}
    complex_data = []
    
    def process_data(d):
        for k, v in d.items():
            if isinstance(v, dict): process_data(v)
            elif isinstance(v, list): complex_data.append((k, v))
            else: info_data[k] = v

    process_data(data_dict)
    
    field_rows = []
    idx = 1
    for k, v in info_data.items():
        field_rows.append([Paragraph(f"[{idx:02d}] {k}", s_normal), Paragraph(f": {format_value(v)}", s_bold)])
        idx += 1
    
    if field_rows:
        t_fields = Table(field_rows, colWidths=[200, 300])
        t_fields.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 2)]))
        elements.append(t_fields)
        elements.append(Spacer(1, 15))

    # 4. RENDER TABLES (DỮ LIỆU BẢNG)
    for t_title, rows in complex_data:
        elements.append(Paragraph(f"<b>PHẦN: {t_title.upper()}</b>", s_bold))
        if rows and isinstance(rows[0], dict):
            header = [Paragraph(f"<b>{strip_ns(k).upper()}</b>", s_bold) for k in rows[0].keys()]
            data_rows = [header]
            for r in rows:
                data_rows.append([Paragraph(format_value(v), s_normal) for v in r.values()])
            
            t_grid = Table(data_rows, hAlign='LEFT', repeatRows=1)
            t_grid.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(t_grid)
            elements.append(Spacer(1, 15))

    # 5. FOOTER
    elements.append(Spacer(1, 20))
    sig_data = [
        [Paragraph(f"Ngày {datetime.datetime.now().day} tháng {datetime.datetime.now().month} năm {datetime.datetime.now().year}", ParagraphStyle(name='D', fontName=f_name, fontSize=10, alignment=2))],
        [Paragraph("<b>NHÂN VIÊN ĐẠI LÝ THUẾ</b>", s_bold), Paragraph("<b>NGƯỜI NỘP THUẾ</b>", s_bold)],
        ["(Ký, ghi rõ họ tên)", "(Ký, đóng dấu, ghi rõ họ tên)"]
    ]
    t_sig = Table(sig_data, colWidths=[250, 250])
    t_sig.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('SPAN', (0,0), (1,0))]))
    elements.append(t_sig)

    doc.build(elements)
    buffer.seek(0)
    return buffer
