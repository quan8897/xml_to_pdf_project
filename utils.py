import os
import xml.etree.ElementTree as ET
import io
import re
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
XMLNS = 'http://kekhaithue.gdt.gov.vn/TKhaiThue'

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

def fmt_num(value):
    if value is None: return ""
    s = str(value).strip()
    if not s or s.lower() == 'none': return ""
    try:
        f = float(s.replace(',', '.'))
        if f == int(f):
            return "{:,}".format(int(f)).replace(',', '.')
        return "{:,.2f}".format(f).replace(',', '.')
    except:
        return s

def fnd(root, *path_parts):
    ns_path = '/'.join(f'{{{XMLNS}}}{p}' for p in path_parts)
    elem = root.find(f'.//{ns_path}')
    if elem is not None:
        t = elem.text
        return t.strip() if t and t.strip() else ""
    fallback = path_parts[-1]
    for e in root.iter():
        if strip_ns(e.tag) == fallback:
            t = e.text
            if t and t.strip(): return t.strip()
    return ""

def fnd_parent(root, parent_tag, child_tag):
    for p in root.iter():
        if strip_ns(p.tag) == parent_tag:
            for c in p:
                if strip_ns(c.tag) == child_tag:
                    t = c.text
                    return t.strip() if t and t.strip() else ""
    return ""

def get_all(root, tag):
    return [e for e in root.iter() if strip_ns(e.tag) == tag]

def register_fonts():
    paths = [
        (r"C:\Windows\Fonts\times.ttf",   r"C:\Windows\Fonts\timesbd.ttf", r"C:\Windows\Fonts\timesi.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"),
    ]
    for reg, bold, italic in paths:
        if os.path.exists(reg):
            try:
                pdfmetrics.registerFont(TTFont('VN', reg))
                pdfmetrics.registerFont(TTFont('VNB', bold if os.path.exists(bold) else reg))
                pdfmetrics.registerFont(TTFont('VNI', italic if os.path.exists(italic) else reg))
                return True
            except: continue
    return False

# ── MST BOXES (iTaxViewer 10-3 structure) ───────────────────────────
def draw_mst_boxes(mst_str, fn):
    mst = (mst_str or "").replace("-", "").strip()
    # iTaxViewer uses 10 main boxes and 3 sub boxes
    chars = list(mst[:13])
    while len(chars) < 13: chars.append("")
    
    # 10 boxes for main MST
    box_data = [[Paragraph(c, ParagraphStyle('c', fontName=fn, fontSize=10, alignment=1)) for c in chars[:10]]]
    # Splitter dash
    box_data[0].append(Paragraph("-", ParagraphStyle('c', fontName=fn, fontSize=10, alignment=1)))
    # 3 boxes for branch
    for c in chars[10:13]:
        box_data[0].append(Paragraph(c, ParagraphStyle('c', fontName=fn, fontSize=10, alignment=1)))
        
    widths = [5.5*mm]*10 + [3*mm] + [5.5*mm]*3
    t = Table(box_data, colWidths=widths, rowHeights=[6.5*mm])
    # Style only for the character boxes (skip the dash at index 10)
    grid_style = [
        ('ALIGN',  (0,0),(-1,-1), 'CENTER'),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ]
    for i in range(10): 
        grid_style.append(('GRID', (i,0), (i,0), 0.7, colors.black))
    for i in range(11, 14):
        grid_style.append(('GRID', (i,0), (i,0), 0.7, colors.black))
        
    t.setStyle(TableStyle(grid_style))
    return t

# ─────────────────────────────────────────────
# PAGE NUMBER CANVAS
# ─────────────────────────────────────────────
class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.setFont("VN", 8)
            self.drawRightString(A4[0] - 40, 20, f"Trang {self._pageNumber}/{num_pages}")
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

# ─────────────────────────────────────────────
# TEMPLATE 01/TTS
# ─────────────────────────────────────────────
def render_01TTS(root, elements, fn, fb, fi):
    def N(name, **kw): return ParagraphStyle(name, fontName=fn, **kw)
    def B(name, **kw): return ParagraphStyle(name, fontName=fb, **kw)
    def I(name, **kw): return ParagraphStyle(name, fontName=fi, **kw)

    s7   = N('s7',  fontSize=7,  leading=9)
    s7c  = N('s7c', fontSize=7,  leading=9,  alignment=1)
    s8   = N('s8',  fontSize=8,  leading=11)
    s8r  = N('s8r', fontSize=8,  leading=11, alignment=2)
    s8c  = N('s8c', fontSize=8,  leading=11, alignment=1)
    s8bc = B('s8bc',fontSize=8,  leading=11, alignment=1)
    s9   = N('s9',  fontSize=10, leading=13)
    s9b  = B('s9b', fontSize=10, leading=13)
    s9bc = B('s9bc',fontSize=10, leading=13, alignment=1)
    s9bi = B('s9bi',fontSize=10, leading=13, alignment=1)
    s12bc = B('s12bc',fontSize=12, leading=16, alignment=1)

    W = 515
    def sp(h=3): return Spacer(1, h)
    def clean(v): return '' if not v or str(v).lower() in ('false','true','0','none') else str(v).strip()

    # --- DATA READING ---
    tenTKhai = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','tenTKhai')
    loai = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','loaiTKhai')
    soLan = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','soLan')
    kyTuNgay = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','KyKKhaiThue','kyKKhaiTuNgay')
    kyDenNgay = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','KyKKhaiThue','kyKKhaiDenNgay')
    mst = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','mst')
    tenNNT = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','tenNNT')
    dchi = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','dchiNNT')
    dthoai = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','dthoaiNNT')
    fax = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','faxNNT')
    email = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','emailNNT')
    theoPL_DS = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','khaiTheoPLuatDanSu')
    theoPL_Thue = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','khaiTheoPLuatThue')
    ct10 = clean(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ct10'))
    ct11 = clean(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ct11'))
    ct12k = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ct12k')
    maHDong = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','maHDong')
    tc16 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct16')
    tc17 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct17')
    tc18 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct18')
    tc19 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct19')
    tc20 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct20')
    tc21 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct21')
    ct23 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct23'))
    ct24 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct24'))
    ct25 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct25'))
    ct26 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct26'))
    ct27 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct27'))
    ct28 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct28'))
    ct29 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct29'))

    # Helper for layout
    def frow(code, label, val, lw=195, vw=320):
        t = Table([[Paragraph(f'[{code}] {label}', s9), Paragraph(f'<b>{val}</b>', s9)]], colWidths=[lw, vw])
        t.setStyle(TableStyle([('LINEBELOW',(1,0),(1,0),0.5,colors.black),('VALIGN',(0,0),(-1,-1),'BOTTOM')]))
        return t

    # Header 01/TTS
    hdr = Table([[
        Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>Độc lập – Tự do – Hạnh phúc<br/>─────────────────────", s9bi),
        Table([[Paragraph("<b>Mẫu số: 01/TTS</b>", s8bc)],
               [Paragraph("(Ban hành kèm theo Thông tư số 40/2021/TT-BTC ngày 01/06/2021 của Bộ trưởng Bộ Tài chính)", s7c)]],
              colWidths=[162], style=[('BOX',(0,0),(-1,-1),0.5,colors.black),('TOPPADDING',(0,0),(-1,-1),3),('LEFTPADDING',(0,0),(-1,-1),3)])
    ]], colWidths=[353, 162])
    elements.append(hdr); elements.append(sp(8))

    elements.append(Paragraph('TỜ KHAI THUẾ ĐỐI VỚI HOẠT ĐỘNG CHO THUÊ TÀI SẢN', s12bc))
    elements.append(Paragraph('(Áp dụng đối với cá nhân có hoạt động cho thuê tài sản trực tiếp khai thuế với cơ quan thuế và tổ chức khai thay cho cá nhân)', s8c))
    elements.append(sp(6))

    is_ds = "X" if clean(theoPL_DS) else " "
    is_thue = "X" if clean(theoPL_Thue) else " "
    elements.append(Table([[Paragraph(f"[{is_ds}]", s9), Paragraph("Cá nhân cho thuê tài sản trực tiếp khai thuế/Tổ chức, cá nhân khai thuế thay, nộp thuế thay cho cá nhân ủy quyền theo quy định của pháp luật dân sự", s9)]], colWidths=[20, 495]))
    elements.append(Table([[Paragraph(f"[{is_thue}]", s9), Paragraph("Doanh nghiệp, tổ chức kinh tế khai thuế thay, nộp thuế thay theo pháp luật thuế", s9)]], colWidths=[20, 495]))
    elements.append(sp(5))

    ky_nam = kyTuNgay.split('/')[-1] if kyTuNgay and '/' in kyTuNgay else ""
    ky_thang = kyTuNgay.split('/')[1] if kyTuNgay and '/' in kyTuNgay else ""
    
    elements.append(Paragraph(f"<b>[01] Kỳ tính thuế:</b>", s9))
    elements.append(Table([[Paragraph(f"  [01a] Năm: <b>{ky_nam}</b>", s9), Paragraph(f"  [01b] Kỳ thanh toán: Từ ngày: <b>{kyTuNgay or '...'}</b> Đến ngày: <b>{kyDenNgay or '...'}</b>", s9)]], colWidths=[120, 395]))
    elements.append(Table([[Paragraph(f"  [01c] Tháng: <b>{ky_thang}</b> năm <b>{ky_nam}</b>", s9), Paragraph(f"  [01d] Quý: ......... năm <b>{ky_nam}</b>", s9)]], colWidths=[200, 315]))
    elements.append(Table([[Paragraph(f"[02] Lần đầu: [<b>{'X' if loai=='C' else ' '}</b>]", s9), Paragraph(f"[03] Bổ sung lần thứ: [<b>{soLan if soLan and soLan!='0' else ' '}</b>]", s9)]], colWidths=[140, 375]))
    elements.append(sp(5))

    # NNT Section
    elements.append(frow('04', 'Tên người nộp thuế:', tenNNT.upper()))
    elements.append(Table([[Paragraph("[05] Mã số thuế:", s9), draw_mst_boxes(mst, fn)]], colWidths=[145, 370]))
    elements.append(frow('06', 'Địa chỉ liên hệ:', dchi))
    elements.append(Table([[Paragraph("[07] Điện thoại:", s9), Paragraph(f"<b>{dthoai}</b>", s9), Paragraph("[08] Fax:", s9), Paragraph(f"<b>{fax}</b>", s9), Paragraph("[09] Email:", s9), Paragraph(f"<b>{email}</b>", s9)]], colWidths=[90, 80, 45, 60, 50, 190]))
    elements.append(frow('10', 'Số CMND (trường hợp cá nhân quốc tịch Việt Nam):', ct10))
    elements.append(frow('11', 'Hộ chiếu (trường hợp cá nhân không có quốc tịch Việt Nam):', ct11))
    elements.append(sp(5))

    # [13-15] Tax Agent
    elements.append(frow('13', 'Tên đại lý thuế (nếu có):', ''))
    elements.append(Table([[Paragraph("[14] Mã số thuế:", s9), draw_mst_boxes('', fn)]], colWidths=[145, 370]))
    elements.append(frow('15', 'Hợp đồng đại lý thuế: số:', ''))
    elements.append(frow('16', 'Tổ chức khai, nộp thuế thay (nếu có):', tc16))
    elements.append(Table([[Paragraph("[17] Mã số thuế:", s9), draw_mst_boxes(tc17, fn)]], colWidths=[145, 370]))
    elements.append(frow('18', 'Địa chỉ:', tc18))
    elements.append(Table([[Paragraph("[19] Điện thoại:", s9), Paragraph(f"<b>{tc19}</b>", s9), Paragraph("[20] Fax:", s9), Paragraph(f"<b>{tc20}</b>", s9), Paragraph("[21] Email:", s9), Paragraph(f"<b>{tc21}</b>", s9)]], colWidths=[90, 80, 45, 60, 50, 190]))
    elements.append(frow('22', 'Văn bản ủy quyền (nếu có): số:', maHDong))
    elements.append(sp(8))

    # Tax Table
    header = [Paragraph(f"<b>{t}</b>", s8bc) for t in ["STT", "Chỉ tiêu", "Mã chỉ tiêu", "Đơn vị tính", "Số tiền tiền"]]
    data = [header]
    body = [
        ["1", "Tổng doanh thu phát sinh trong kỳ", "[23]", "Đồng", ct23 or "0"],
        ["2", "Doanh thu tính thuế GTGT", "[24]", "Đồng", ct24 or "0"],
        ["3", "Doanh thu tính thuế TNCN", "[25]", "Đồng", ct24 or "0"], # Usually same for 01/TTS
        ["4", "Số thuế GTGT phải nộp", "[26]", "Đồng", ct25 or "0"],
        ["5", "Số thuế TNCN phải nộp phát sinh trong kỳ", "[27]", "Đồng", ct26 or "0"],
        ["6", "Tiền phạt, bồi thường (nếu có)", "[28]", "Đồng", ct27 or "0"],
        ["7", "Tổng số thuế TNCN phải nộp", "[29]", "Đồng", ct29 or "0"],
    ]
    for r in body:
        data.append([Paragraph(r[0], s8c), Paragraph(r[1], s8), Paragraph(r[2], s8c), Paragraph(r[3], s8c), Paragraph(f"<b>{r[4]}</b>", s8r)])
    
    table = Table(data, colWidths=[30, 245, 75, 70, 95])
    table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(Paragraph("<b>A. PHẦN CÁ NHÂN KÊ KHAI NGHĨA VỤ THUẾ</b>", s9b))
    elements.append(sp(3)); elements.append(table); elements.append(sp(10))

    # Signature
    now = datetime.datetime.now()
    sig_date = Paragraph(f"<i>........., ngày {now.day:02d} tháng {now.month:02d} năm {now.year}</i>", s8c)
    sig_label = Paragraph("<b>NGƯỜI NỘP THUẾ hoặc ĐẠI DIỆN HỢP PHÁP CỦA NGƯỜI NỘP THUẾ</b>", s9bi)
    sig_hint = Paragraph("(Ký, ghi rõ họ tên; chức vụ và đóng dấu (nếu có))", s8c)
    
    sig_table = Table([[Paragraph("", s9), Table([[sig_date], [sig_label], [Spacer(1, 20)], [sig_hint]], colWidths=[250])]], colWidths=[250, 265])
    elements.append(sig_table)

def generate_tax_pdf(xml_content):
    register_fonts()
    fn, fb, fi = 'VN', 'VNB', 'VNI'
    clean_xml = pre_process_xml(xml_content)
    root = ET.fromstring(clean_xml)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    render_01TTS(root, elements, fn, fb, fi)
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
