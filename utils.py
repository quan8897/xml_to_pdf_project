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

def extract_tax_metadata(xml_content):
    try:
        root = ET.fromstring(pre_process_xml(xml_content))
        mst = "Unknown"
        ky_thue = "Unknown"
        ten_tk = "TỜ KHAI THUẾ"
        mau_so = "01/TTS" # Mặc định theo yêu cầu của bạn, có thể parse thêm
        
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

def pre_process_xml(xml_content):
    if isinstance(xml_content, bytes):
        xml_str = xml_content.decode('utf-8', errors='ignore')
    else:
        xml_str = xml_content
    xml_str = re.sub(r'&(?!(?:amp|lt|gt|quot|apos);)', '&amp;', xml_str)
    return xml_str.encode('utf-8')

def format_value(value):
    if value is None: return ""
    val_str = str(value)
    if val_str.replace('.', '', 1).isdigit() and len(val_str) < 15:
        try:
            val_num = float(val_str)
            return "{:,}".format(int(val_num)).replace(',', '.')
        except: pass
    return val_str.replace('\n', '<br/>')

def register_fonts():
    font_paths = ["Roboto-Regular.ttf", "arial.ttf", r"C:\Windows\Fonts\arial.ttf"]
    for f in font_paths:
        if os.path.exists(f):
            pdfmetrics.registerFont(TTFont('VN-Font', f))
            # Bold fallback
            pdfmetrics.registerFont(TTFont('VN-Font-Bold', f))
            return True
    return False

def xml_to_dict(element):
    result = {}
    for child in element:
        tag = strip_ns(child.tag)
        value = xml_to_dict(child) if len(child) > 0 else child.text
        if tag in result:
            if not isinstance(result[tag], list): result[tag] = [result[tag]]
            result[tag].append(value)
        else: result[tag] = value
    return result

def generate_tax_pdf(xml_content, title="BÁO CÁO THUẾ"):
    meta = extract_tax_metadata(xml_content)
    root = ET.fromstring(pre_process_xml(xml_content))
    data_dict = xml_to_dict(root)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=30, bottomMargin=30)
    
    register_fonts()
    f_name, f_bold = 'VN-Font', 'VN-Font-Bold'
    
    # Styles
    s_normal = ParagraphStyle(name='Normal', fontName=f_name, fontSize=10, leading=14)
    s_bold = ParagraphStyle(name='Bold', fontName=f_bold, fontSize=10, leading=14)
    s_title = ParagraphStyle(name='Title', fontName=f_bold, fontSize=14, alignment=1, spaceAfter=10)
    s_motto = ParagraphStyle(name='Motto', fontName=f_bold, fontSize=10, alignment=1)
    s_box = ParagraphStyle(name='Box', fontName=f_name, fontSize=8, alignment=1, borderPadding=5)

    elements = []

    # 1. HEADER CHÍNH QUY (Phần mẫu số góc phải)
    header_table_data = [
        [Paragraph("<b>CỘNG HÀA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>Độc lập - Tự do - Hạnh phúc", s_motto), 
         Table([[Paragraph(f"<b>Mẫu số: {meta['form']}</b><br/><font size=7>(Ban hành kèm theo Thông tư số 40/2021/TT-BTC)</font>", s_box)]], 
               style=[('GRID', (0,0), (-1,-1), 0.5, colors.black), ('ALIGN', (0,0), (-1,-1), 'CENTER')])
        ]
    ]
    t_header = Table(header_table_data, colWidths=[350, 150])
    elements.append(t_header)
    elements.append(Spacer(1, 15))

    # 2. TIÊU ĐỀ
    elements.append(Paragraph(meta['name'].upper(), s_title))
    elements.append(Paragraph(f"Kỳ tính thuế: {meta['period']}", ParagraphStyle(name='Sub', fontName=f_name, fontSize=10, alignment=1, spaceAfter=20)))

    # 3. DỰNG BIỂU MẪU DẠNG CHỈ TIÊU (FIELDS)
    def render_fields(data, prefix=""):
        idx = 1
        table_data = []
        for k, v in data.items():
            if isinstance(v, (dict, list)): continue # Xử lý bảng sau
            label = f"[{idx:02d}] {k}"
            table_data.append([Paragraph(label, s_normal), Paragraph(f": <b>{format_value(v)}</b>", s_normal)])
            idx += 1
        
        if table_data:
            t = Table(table_data, colWidths=[200, 300])
            t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
            elements.append(t)
            elements.append(Spacer(1, 10))

    # Tách dữ liệu thành 2 phần: Thông tin chung và Bảng số liệu
    info_data = {}
    complex_data = []
    
    def separate_data(d):
        for k, v in d.items():
            if isinstance(v, dict): separate_data(v)
            elif isinstance(v, list): complex_data.append((k, v))
            else: info_data[k] = v

    separate_data(data_dict)
    
    # Render các trường thông tin đơn giản
    render_fields(info_data)
    
    # 4. RENDER CÁC BẢNG SỐ LIỆU (GRID CHUẨN)
    for title_tab, rows in complex_data:
        elements.append(Paragraph(f"<b>PHẦN: {title_tab.upper()}</b>", s_bold))
        header = []
        # Tự tạo header từ keys của dòng đầu tiên
        if rows and isinstance(rows[0], dict):
            header = [Paragraph(f"<b>{strip_ns(k).upper()}</b>", s_bold) for k in rows[0].keys()]
            data_rows = [header]
            for r in rows:
                data_rows.append([Paragraph(format_value(val), s_normal) for val in r.values()])
            
            t_complex = Table(data_rows, hAlign='LEFT', repeatRows=1)
            t_complex.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(t_complex)
            elements.append(Spacer(1, 20))

    # 5. CHÂN TRANG KÝ TÊN
    elements.append(Spacer(1, 30))
    sig_data = [
        [Paragraph(f"Hôm nay, ngày {datetime.datetime.now().day} tháng {datetime.datetime.now().month} năm {datetime.datetime.now().year}", ParagraphStyle(name='Date', fontName=f_name, fontSize=10, alignment=2))],
        [Paragraph("<b>NHÂN VIÊN ĐẠI LÝ THUẾ</b>", s_bold), Paragraph("<b>NGƯỜI NỘP THUẾ</b>", s_bold)],
        ["(Ký, ghi rõ họ tên)", "(Ký, đóng dấu, ghi rõ họ tên)"]
    ]
    t_sig = Table(sig_data, colWidths=[250, 250])
    t_sig.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('SPAN', (0,0), (1,0))]))
    elements.append(t_sig)

    doc.build(elements)
    buffer.seek(0)
    return buffer
