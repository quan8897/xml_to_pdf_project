import os
import xml.etree.ElementTree as ET
import io
import re
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
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
    """Format số có dấu chấm hàng nghìn. Trả về chuỗi rỗng nếu None/rỗng."""
    if value is None: return ""
    s = str(value).strip()
    if not s: return ""
    try:
        f = float(s.replace(',', '.'))
        if f == int(f):
            return "{:,}".format(int(f)).replace(',', '.')
        return "{:,.2f}".format(f)
    except:
        return s

def get(root, *tags):
    """Lấy text của thẻ đầu tiên tìm thấy trong cây XML."""
    for tag in tags:
        for elem in root.iter():
            if strip_ns(elem.tag) == tag:
                t = elem.text
                return t.strip() if t and t.strip() else ""
    return ""

def register_fonts():
    paths = [
        ("Roboto-Regular.ttf", "Roboto-Bold.ttf"),
        ("arial.ttf", "arialbd.ttf"),
        (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\arialbd.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for reg, bold in paths:
        if os.path.exists(reg):
            try:
                pdfmetrics.registerFont(TTFont('VN', reg))
                pdfmetrics.registerFont(TTFont('VNB', bold if os.path.exists(bold) else reg))
                return True
            except: continue
    return False

# ─────────────────────────────────────────────
# TEMPLATE 01/TTS  (maTKhai = 470)
# ─────────────────────────────────────────────
def render_01TTS(root, elements, fn, fb):
    """Render form Mẫu 01/TTS – Tờ khai cho thuê tài sản (TT40/2021)."""

    N  = lambda t, **kw: ParagraphStyle(t, fontName=fn, **kw)
    B  = lambda t, **kw: ParagraphStyle(t, fontName=fb, **kw)

    sN   = N('n',  fontSize=9,  leading=13)
    sNc  = N('nc', fontSize=9,  leading=13, alignment=1)
    sB   = B('b',  fontSize=9,  leading=13)
    sBc  = B('bc', fontSize=10, leading=14, alignment=1)
    sT   = B('t',  fontSize=13, leading=18, alignment=1)
    sMo  = B('mo', fontSize=10, leading=14, alignment=1)
    sSub = N('su', fontSize=9,  leading=13, alignment=1)
    sSm  = N('sm', fontSize=8,  leading=11)
    sBsm = B('bsm',fontSize=8,  leading=11)
    sR   = N('r',  fontSize=9,  leading=13, alignment=2)

    W = 515  # usable width (A4 minus margins)

    # -- đọc dữ liệu -------------------------------------------------
    tenTKhai   = get(root, 'tenTKhai')
    mauSo      = "Mẫu số: 01/TTS"
    loai       = get(root, 'loaiTKhai')      # C = lần đầu, B = bổ sung
    soLan      = get(root, 'soLan')
    kyTuNgay   = get(root, 'kyKKhaiTuNgay')
    kyDenNgay  = get(root, 'kyKKhaiDenNgay')
    ngayLap    = get(root, 'ngayLapTKhai')
    tenCQT     = get(root, 'tenCQTNoiNop')
    mst        = get(root, 'mst')
    tenNNT     = get(root, 'tenNNT')
    dchi       = get(root, 'dchiNNT')
    dthoai     = get(root, 'dthoaiNNT')
    fax        = get(root, 'faxNNT')
    email      = get(root, 'emailNNT')

    # chỉ tiêu tính thuế
    ct23 = fmt_num(get(root, 'ct23'))
    ct24 = fmt_num(get(root, 'ct24'))
    ct25 = fmt_num(get(root, 'ct25'))
    ct26 = fmt_num(get(root, 'ct26'))
    ct27 = fmt_num(get(root, 'ct27'))
    ct28 = fmt_num(get(root, 'ct28'))
    ct29 = fmt_num(get(root, 'ct29'))

    # ── 1. HEADER ────────────────────────────────────────────────────
    box_style = [
        ('GRID',       (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING',(0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]
    hdr = Table([
        [
            Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>Độc lập – Tự do – Hạnh phúc<br/>─────────────────", sMo),
            Table([
                [Paragraph(f"<b>{mauSo}</b>", sBc)],
                [Paragraph(f"(Ban hành kèm theo Thông tư số<br/>40/2021/TT-BTC ngày 01/06/2021<br/>của Bộ trưởng Bộ Tài chính)", sSm)],
            ], colWidths=[165], style=box_style)
        ]
    ], colWidths=[350, 165])
    hdr.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    elements.append(hdr)
    elements.append(Spacer(1, 6))

    # ── 2. TIÊU ĐỀ ──────────────────────────────────────────────────
    elements.append(Paragraph(tenTKhai.upper() if tenTKhai else "TỜ KHAI ĐỐI VỚI HOẠT ĐỘNG CHO THUÊ TÀI SẢN", sT))
    elements.append(Paragraph("(Áp dụng đối với cá nhân có hoạt động cho thuê tài sản trực tiếp khai thuế với cơ quan thuế trừ cá nhân trực tiếp ký hợp đồng thuê với tổ chức kinh tế; thay cho cá nhân)", sSub))
    elements.append(Spacer(1, 5))

    # Loại tờ khai check-boxes
    is_dau = "X" if loai == "C" else " "
    is_bs  = "X" if loai == "B" else " "
    elements.append(Paragraph(
        f"Cá nhân cho thuê tài sản trực tiếp khai thuế: Tổ chức, cá nhân khai thuế thay, nộp thuế thay cho cá nhân ký "
        f"quyền theo quy định của pháp luật dân sự(*):", sN))
    elements.append(Paragraph(
        f"Doanh nghiệp, tổ chức có tư cách pháp nhân khai thuế thay, nộp thuế thay cho cá nhân:", sN))
    elements.append(Spacer(1, 3))

    # kỳ khai
    elements.append(Paragraph(
        f"[<b>{is_dau}</b>] Kỳ tính thuế: Từ ngày: <b>{kyTuNgay}</b>   Đến ngày: <b>{kyDenNgay}</b>", sN))
    elements.append(Paragraph(
        f"[<b>{is_bs}</b>] Lần đầu:  [<b>{'X' if soLan=='0' else ' '}</b>] Bổ sung lần thứ [<b>{soLan if soLan!='0' else ''}</b>]", sN))
    elements.append(Spacer(1, 6))

    # ── 3. THÔNG TIN CÁ NHÂN ────────────────────────────────────────
    def field(code, label, value, bold_val=True):
        val_para = Paragraph(f"<b>{value}</b>" if bold_val else value, sN)
        return [Paragraph(f"[{code}] {label}", sN), val_para]

    info_rows = [
        field("04", "Tên người nộp thuế:", tenNNT),
        field("05", "Mã số thuế:", mst),
        field("06", "Địa chỉ:", dchi),
        field("07", "Điện thoại:", dthoai),
        ["", Paragraph(f"[08] Fax: <b>{fax}</b>   [09] Email: <b>{email}</b>", sN)],
    ]
    t_info = Table(info_rows, colWidths=[160, 355])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 8))

    # ── 4. PHẦN A: BẢNG SỐ LIỆU ─────────────────────────────────────
    elements.append(Paragraph("<b>A. PHẦN CÁ NHÂN KÊ KHAI NGHĨA VỤ THUẾ</b>", sB))
    elements.append(Spacer(1, 4))

    unit_row = [["", "", "", Paragraph("Đơn vị tính: Đồng Việt Nam", sSm)]]
    t_unit = Table(unit_row, colWidths=[30, 270, 100, 115])
    t_unit.setStyle(TableStyle([('ALIGN',(3,0),(3,0),'RIGHT')]))
    elements.append(t_unit)

    tax_header = [
        Paragraph("<b>STT</b>", sBsm),
        Paragraph("<b>Chỉ tiêu</b>", sBsm),
        Paragraph("<b>Mã chỉ tiêu</b>", sBsm),
        Paragraph("<b>Số tiền</b>", sBsm),
    ]
    tax_data = [
        ["1", "Tổng doanh thu phát sinh trong kỳ",               "[23]", ct23],
        ["2", "Tổng doanh thu tính thuế",                        "[24]", ct24],
        ["3", "Tổng số thuế GTGT phải nộp",                     "[25]", ct25],
        ["4", "Tổng số phát sinh trong kỳ",                     "[26]", ct26],
        ["5", "Tiền phạt, bồi thường mua bởi cho thuê nhận được theo thỏa thuận tại hợp đồng (nếu có)", "[27]", ct27],
        ["6", "Tổng số thuế TNCN phải nộp tính nhằm bồi thường, phạt vi phạm hợp đồng (nếu có)",       "[28]", ct28],
    ]

    rows = [tax_header] + [
        [Paragraph(str(r[0]), sNc),
         Paragraph(r[1], sSm),
         Paragraph(r[2], sNc),
         Paragraph(fmt_num(r[3]) if r[3] else "0", sR)]
        for r in tax_data
    ]

    col_w = [30, 270, 100, 115]
    t_tax = Table(rows, colWidths=col_w, repeatRows=1)
    t_tax.setStyle(TableStyle([
        ('GRID',        (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND',  (0,0), (-1,0),  colors.lightgrey),
        ('ALIGN',       (0,0), (0,-1),  'CENTER'),
        ('ALIGN',       (2,0), (2,-1),  'CENTER'),
        ('ALIGN',       (3,0), (3,-1),  'RIGHT'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t_tax)

    # Dòng tổng thuế TNCN
    elements.append(Spacer(1, 4))
    total_row = [[
        Paragraph("7", sNc),
        Paragraph("Tổng số thuế TNCN phải nộp [29]+[26]+[28]", sSm),
        Paragraph("[29]", sNc),
        Paragraph(ct29 if ct29 else "0", sBsm)
    ]]
    t_total = Table(total_row, colWidths=col_w)
    t_total.setStyle(TableStyle([
        ('GRID',   (0,0),(-1,-1), 0.5, colors.black),
        ('ALIGN',  (0,0),(0,-1),  'CENTER'),
        ('ALIGN',  (2,0),(2,-1),  'CENTER'),
        ('ALIGN',  (3,0),(3,-1),  'RIGHT'),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
    ]))
    elements.append(t_total)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(
        "<i>(TNCN: Thu nhập cá nhân; GTGT: Giá trị gia tăng)</i>", sSm))

    # ── 5. CAM KẾT ──────────────────────────────────────────────────
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "Tôi cam đoan số liệu khai trên là đúng và chịu trách nhiệm trước pháp luật về số liệu đã khai...", sN))

    # ── 6. CHỮ KÝ ────────────────────────────────────────────────────
    elements.append(Spacer(1, 15))
    now = datetime.datetime.now()
    elements.append(Paragraph(
        f"Ngày {now.day:02d} tháng {now.month:02d} năm {now.year}", sR))
    elements.append(Spacer(1, 5))

    sig = Table([
        [Paragraph("<b>NHÂN VIÊN ĐẠI LÝ THUẾ</b>", sBc),
         Paragraph("<b>NGƯỜI NỘP THUẾ hoặc<br/>ĐẠI DIỆN HỢP PHÁP CỦA NGƯỜI NỘP THUẾ</b>", sBc)],
        [Paragraph("Họ và tên:", sN),
         Paragraph("(Ký, ghi rõ họ tên, đóng dấu (nếu có))", sSm)],
        [Paragraph("Chứng chỉ hành nghề số:", sN), ""],
    ], colWidths=[257, 258])
    sig.setStyle(TableStyle([
        ('ALIGN', (0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),3),
    ]))
    elements.append(sig)

# ─────────────────────────────────────────────
# GENERIC RENDERER (fallback cho các form khác)
# ─────────────────────────────────────────────
def xml_to_dict(element):
    result = {}
    for child in element:
        tag = strip_ns(child.tag)
        if len(child) > 0:
            value = xml_to_dict(child)
        else:
            text = child.text
            value = text.strip() if text and text.strip() else ""
        if tag in result:
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
            result[tag].append(value)
        else:
            result[tag] = value
    return result

def render_generic(root, elements, fn, fb):
    sN  = ParagraphStyle('gN',  fontName=fn, fontSize=9,  leading=13)
    sB  = ParagraphStyle('gB',  fontName=fb, fontSize=9,  leading=13)
    sT  = ParagraphStyle('gT',  fontName=fb, fontSize=14, leading=18, alignment=1)
    sMo = ParagraphStyle('gMo', fontName=fb, fontSize=10, leading=14, alignment=1)

    elements.append(Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b>", sMo))
    elements.append(Paragraph("Độc lập – Tự do – Hạnh phúc", sMo))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(strip_ns(root.tag).upper(), sT))
    elements.append(Spacer(1, 10))

    data = xml_to_dict(root)

    info_data, complex_data = {}, []
    def split(d):
        for k, v in d.items():
            if isinstance(v, dict): split(v)
            elif isinstance(v, list): complex_data.append((k, v))
            else: info_data[k] = v
    split(data)

    rows = [[Paragraph(f"[{i+1:02d}] {k}", sN), Paragraph(f"<b>{fmt_num(v) if v else ''}</b>", sN)]
            for i, (k, v) in enumerate(info_data.items())]
    if rows:
        t = Table(rows, colWidths=[200, 315])
        t.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),2)]))
        elements.append(t)
        elements.append(Spacer(1, 10))

    for title, rws in complex_data:
        dict_rows = [r for r in rws if isinstance(r, dict)]
        if not dict_rows: continue
        elements.append(Paragraph(f"<b>{title.upper()}</b>", sB))
        keys = list(dict_rows[0].keys())
        header = [Paragraph(f"<b>{k.upper()}</b>", sB) for k in keys]
        body = [[Paragraph(fmt_num(r.get(k,"")), sN) for k in keys] for r in dict_rows]
        t = Table([header]+body, repeatRows=1)
        t.setStyle(TableStyle([
            ('GRID',(0,0),(-1,-1),0.5,colors.black),
            ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('FONTSIZE',(0,0),(-1,-1),8),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 10))

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def extract_tax_metadata(xml_content):
    try:
        root = ET.fromstring(pre_process_xml(xml_content))
        mst, ten_tk, ma_tk = "Unknown", "TỜ KHAI THUẾ", ""
        ky = "Unknown"
        for elem in root.iter():
            t = strip_ns(elem.tag)
            if t == 'mst' and elem.text: mst = elem.text.strip()
            if t == 'tenTKhai' and elem.text: ten_tk = elem.text.strip()
            if t == 'maTKhai' and elem.text: ma_tk = elem.text.strip()
            if t == 'kyKKhaiTuNgay' and elem.text: ky = elem.text.strip()
        return {"name": ten_tk, "mst": mst, "period": ky, "form": ma_tk}
    except:
        return {"name": "TỜ KHAI THUẾ", "mst": "", "period": "", "form": ""}

def generate_tax_pdf(xml_content, title="BÁO CÁO THUẾ"):
    clean = pre_process_xml(xml_content)
    root  = ET.fromstring(clean)
    meta  = extract_tax_metadata(xml_content)

    # Xác định form type
    ma_tk = meta.get("form", "")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=30,   bottomMargin=30
    )

    font_ok = register_fonts()
    fn = 'VN'  if font_ok else 'Helvetica'
    fb = 'VNB' if font_ok else 'Helvetica-Bold'

    elements = []

    # Dispatch theo loại form
    if ma_tk == "470":          # Mẫu 01/TTS
        render_01TTS(root, elements, fn, fb)
    else:
        render_generic(root, elements, fn, fb)

    doc.build(elements)
    buffer.seek(0)
    return buffer
