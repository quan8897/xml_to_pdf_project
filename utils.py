import os
import xml.etree.ElementTree as ET
import io
import re
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, BaseDocTemplate, Frame,
                                PageTemplate, Table, TableStyle,
                                Paragraph, Spacer, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
XMLNS = 'http://kekhaithue.gdt.gov.vn/TKhaiThue'
NS    = {'ns': XMLNS}

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

# ── 1. XPath tuyệt đối ───────────────────────────────────────────────
def fnd(root, *path_parts):
    """
    Lấy text theo XPath tuyệt đối có namespace.
    Ví dụ: fnd(root, 'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct23')
    """
    ns_path = '/'.join(f'{{{XMLNS}}}{p}' for p in path_parts)
    elem = root.find(f'.//{ns_path}')
    if elem is not None:
        t = elem.text
        return t.strip() if t and t.strip() else ""
    # Fallback: tìm không namespace (dùng khi XML đã được strip)
    fallback = path_parts[-1]
    for e in root.iter():
        if strip_ns(e.tag) == fallback:
            t = e.text
            if t and t.strip(): return t.strip()
    return ""

def fnd_parent(root, parent_tag, child_tag):
    """Lấy text từ thẻ con của thẻ cha cụ thể — tránh lấy nhầm từ nơi khác."""
    for p in root.iter():
        if strip_ns(p.tag) == parent_tag:
            for c in p:
                if strip_ns(c.tag) == child_tag:
                    t = c.text
                    return t.strip() if t and t.strip() else ""
    return ""

def get_all(root, tag):
    return [e for e in root.iter() if strip_ns(e.tag) == tag]

def chk(val):
    return "X" if val and val.lower() == 'true' else " "

def register_fonts():
    paths = [
        (r"C:\Windows\Fonts\times.ttf",   r"C:\Windows\Fonts\timesbd.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        (r"C:\Windows\Fonts\arial.ttf",   r"C:\Windows\Fonts\arialbd.ttf"),
        ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
         "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]
    for reg, bold in paths:
        if os.path.exists(reg):
            try:
                pdfmetrics.registerFont(TTFont('VN',  reg))
                pdfmetrics.registerFont(TTFont('VNB', bold if os.path.exists(bold) else reg))
                return True
            except: continue
    return False

# ── 2. MST Boxes ────────────────────────────────────────────────────
def draw_mst_boxes(mst_str, fn):
    """Vẽ từng chữ số MST trong ô vuông riêng biệt."""
    chars = list((mst_str or "")[:13])
    if not chars: return Paragraph("", ParagraphStyle('empty'))
    # Pad đến 13 ô
    while len(chars) < 13:
        chars.append("")
    data = [[Paragraph(c, ParagraphStyle('mst_c', fontName=fn, fontSize=10,
                                          alignment=1, leading=13))
             for c in chars]]
    t = Table(data, colWidths=[5.5*mm]*13, rowHeights=[6.5*mm])
    t.setStyle(TableStyle([
        ('GRID',   (0,0),(-1,-1), 0.7, colors.black),
        ('ALIGN',  (0,0),(-1,-1), 'CENTER'),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ]))
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
            self.setFont("Helvetica", 8)
            self.drawRightString(A4[0] - 30, 15,
                                 f"{self._pageNumber}/{num_pages}")
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

# ─────────────────────────────────────────────
# TEMPLATE 01/TTS  (maTKhai = 470)
# ─────────────────────────────────────────────
def render_01TTS(root, elements, fn, fb):

    def N(name, **kw): return ParagraphStyle(name, fontName=fn, **kw)
    def B(name, **kw): return ParagraphStyle(name, fontName=fb, **kw)

    s7   = N('s7',  fontSize=7,  leading=9)
    s7c  = N('s7c', fontSize=7,  leading=9,  alignment=1)
    s8   = N('s8',  fontSize=8,  leading=11)
    s8r  = N('s8r', fontSize=8,  leading=11, alignment=2)
    s8c  = N('s8c', fontSize=8,  leading=11, alignment=1)
    s8b  = B('s8b', fontSize=8,  leading=11)
    s8bc = B('s8bc',fontSize=8,  leading=11, alignment=1)
    s9   = N('s9',  fontSize=9,  leading=12)
    s9r  = N('s9r', fontSize=9,  leading=12, alignment=2)
    s9c  = N('s9c', fontSize=9,  leading=12, alignment=1)
    s9b  = B('s9b', fontSize=9,  leading=12)
    s9bi = B('s9bi',fontSize=9,  leading=12, alignment=1)
    s10bc= B('s10bc',fontSize=10,leading=13, alignment=1)
    s10c = N('s10c', fontSize=10,leading=13, alignment=1)
    s13b = B('s13b',fontSize=13, leading=17, alignment=1)

    W = 515

    def sp(h=3): return Spacer(1, h)

    # ── ĐỌC DỮ LIỆU — XPath tuyệt đối ──────────────────────────────
    # Trang chính — Header
    tenTKhai   = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','tenTKhai')
    loai       = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','loaiTKhai')
    soLan      = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','soLan')
    kyTuNgay   = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','KyKKhaiThue','kyKKhaiTuNgay')
    kyDenNgay  = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','TKhaiThue','KyKKhaiThue','kyKKhaiDenNgay')

    # NNT
    mst    = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','mst')
    tenNNT = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','tenNNT')
    dchi   = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','dchiNNT')
    dthoai = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','dthoaiNNT')
    fax    = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','faxNNT')
    email  = fnd(root,'HSoKhaiThue','TTinChung','TTinTKhaiThue','NNT','emailNNT')

    # CTieuTKhaiChinh > Header
    theoPL_DS   = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','khaiTheoPLuatDanSu')
    theoPL_Thue = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','khaiTheoPLuatThue')
    ct10 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ct10')
    ct11 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ct11')
    ct12k= fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ct12k')
    maHDong = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','maHDong')

    # Header > CNKDChuaDangKyThue
    ct12a     = fnd_parent(root,'CNKDChuaDangKyThue','ct12a_ngaySinh')
    ct12b     = fnd_parent(root,'CNKDChuaDangKyThue','ct12b_tenQuocTich')
    ct12c_ma  = fnd_parent(root,'CNKDChuaDangKyThue','ct12c_ma')
    ct12c_ten = fnd_parent(root,'CNKDChuaDangKyThue','ct12c_ten')
    ct12c_so  = fnd_parent(root,'CNKDChuaDangKyThue','ct12c_soCMND_CCCD')
    ct12c_ngay= fnd_parent(root,'CNKDChuaDangKyThue','ct12c_1_ngayCap')
    ct12c_noi = fnd_parent(root,'CNKDChuaDangKyThue','ct12c_2_noiCap_ten')
    ct12c_loai= fnd_parent(root,'CNKDChuaDangKyThue','ct12c_2_noiCap_loai')

    # Header > CNKDKhongCoCMND_CCCD
    ct12d_so   = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12d_soHoChieu')
    ct12d_ten  = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12d_ten')
    ct12d_ngay = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12d_1_ngayCap')
    ct12d_noi  = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12d_2_noiCap_ten')
    ct12dd_so  = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12dd_soGiayThongHanh')
    ct12dd_ten = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12dd_ten')
    ct12dd_ngay= fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12dd_1_ngayCap')
    ct12dd_noi = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12dd_2_noiCap_ten')
    ct12e_so   = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12e_soCMNDBienGioi')
    ct12e_ten  = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12e_ten')
    ct12e_ngay = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12e_1_ngayCap')
    ct12e_noi  = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12e_2_noiCap_ten')
    ct12f_so   = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12f_soGiayToKhac')
    ct12f_ten  = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12f_ten')
    ct12f_ngay = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12f_1_ngayCap')
    ct12f_noi  = fnd_parent(root,'CNKDKhongCoCMND_CCCD','ct12f_2_noiCap_ten')

    # Header > CT12g/h/i
    ct12g_nha  = fnd_parent(root,'CT12g','ct12g_soNha')
    ct12g_ph   = fnd_parent(root,'CT12g','ct12g_tenPhuong')
    ct12g_qu   = fnd_parent(root,'CT12g','ct12g_tenQuan')
    ct12g_ti   = fnd_parent(root,'CT12g','ct12g_tenTinh')
    ct12h_nha  = fnd_parent(root,'CT12h','ct12h_soNha')
    ct12h_ph   = fnd_parent(root,'CT12h','ct12h_tenPhuong')
    ct12h_qu   = fnd_parent(root,'CT12h','ct12h_tenQuan')
    ct12h_ti   = fnd_parent(root,'CT12h','ct12h_tenTinh')
    ct12i_so   = fnd_parent(root,'CT12i','ct12i_soGiayTo')
    ct12i_ngay = fnd_parent(root,'CT12i','ct12i_ngayCap')
    ct12i_cq   = fnd_parent(root,'CT12i','ct12i_coQuanCap')

    # [16-21] CHỈ lấy từ ToChucNopThueThay — XPath tuyệt đối
    tc16 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct16')
    tc17 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct17')
    tc18 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct18')
    tc19 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct19')
    tc20 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct20')
    tc21 = fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','Header','ToChucNopThueThay','ct21')

    # CaNhanKeKhai — XPath tuyệt đối tránh lấy nhầm từ PLuc
    ct23 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct23'))
    ct24 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct24'))
    ct25 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct25'))
    ct26 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct26'))
    ct27 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct27'))
    ct28 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct28'))
    ct29 = fmt_num(fnd(root,'HSoKhaiThue','CTieuTKhaiChinh','CaNhanKeKhai','ct29'))

    is_ds   = chk(theoPL_DS); is_thue = chk(theoPL_Thue)
    is_dau  = "X" if loai == "C" else " "
    is_bs   = "X" if loai == "B" else " "

    # ── 1. HEADER ───────────────────────────────────────────────────
    hdr = Table([[
        Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>"
                  "Độc lập – Tự do – Hạnh phúc<br/>─────────────────────", s10c),
        Table([[Paragraph("<b>Mẫu số: 01/TTS</b>", s8bc)],
               [Paragraph("(Ban hành kèm theo Thông tư số 40/2021/TT-BTC<br/>"
                          "ngày 01/06/2021 của Bộ trưởng Bộ Tài chính)", s7c)]],
              colWidths=[162],
              style=[('BOX',(0,0),(-1,-1),0.5,colors.black),
                     ('TOPPADDING',(0,0),(-1,-1),3),
                     ('BOTTOMPADDING',(0,0),(-1,-1),3),
                     ('LEFTPADDING',(0,0),(-1,-1),3)])
    ]], colWidths=[353, 162])
    hdr.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    elements.append(hdr)
    elements.append(sp(4))

    # ── 2. TIÊU ĐỀ ─────────────────────────────────────────────────
    elements.append(Paragraph(
        tenTKhai.upper() or "TỜ KHAI ĐỐI VỚI HOẠT ĐỘNG CHO THUÊ TÀI SẢN(TT40/2021)", s13b))
    elements.append(Paragraph(
        "(Áp dụng đối với cá nhân có hoạt động cho thuê tài sản trực tiếp khai thuế với cơ quan thuế "
        "trừ cá nhân trực tiếp ký hợp đồng thuê với tổ chức kinh tế; thay cho cá nhân)", s8c))
    elements.append(sp(3))
    ky_rows = [
        [Paragraph("[01] Kỳ tính thuế:", s9),
         Paragraph(f"Từ ngày: <b>{kyTuNgay}</b> &nbsp;&nbsp;&nbsp; Đến ngày: <b>{kyDenNgay}</b>", s9)],
        [Paragraph("[02] Lần đầu:", s9),
         Paragraph(
             f"<b>{'☑' if loai=='C' else '☐'}</b> Lần đầu"
             f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
             f"<b>{'☑' if loai=='B' else '☐'}</b> Bổ sung lần thứ: "
             f"<b>{soLan if soLan and soLan != '0' else ''}</b>", s9)],
    ]
    t_ky = Table(ky_rows, colWidths=[140, 375])
    t_ky.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),1),
                               ('BOTTOMPADDING',(0,0),(-1,-1),1),
                               ('LEFTPADDING',(0,0),(-1,-1),0)]))
    elements.append(t_ky)
    elements.append(sp(4))

    # ── 3. THÔNG TIN NGƯỜI NỘP THUẾ ─────────────────────────────────
    basic = [
        [Paragraph("[04] Tên người nộp thuế:", s9), Paragraph(f"<b>{tenNNT}</b>", s9)],
        [Paragraph("[05] Mã số thuế:", s9),          draw_mst_boxes(mst, fn)],
        [Paragraph("[06] Địa chỉ:", s9),             Paragraph(f"<b>{dchi}</b>", s9)],
    ]
    t_basic = Table(basic, colWidths=[140, 375])
    t_basic.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                  ('TOPPADDING',(0,0),(-1,-1),1),
                                  ('BOTTOMPADDING',(0,0),(-1,-1),1),
                                  ('LEFTPADDING',(0,0),(-1,-1),0)]))
    elements.append(t_basic)

    tel = Table([[
        Paragraph("[07] Điện thoại:", s9), Paragraph(f"<b>{dthoai}</b>", s9),
        Paragraph("[08] Fax:", s9),        Paragraph(f"<b>{fax}</b>", s9),
        Paragraph("[09] Email:", s9),      Paragraph(f"<b>{email}</b>", s9),
    ]], colWidths=[90, 100, 45, 65, 50, 165])
    tel.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),1),
                              ('LEFTPADDING',(0,0),(-1,-1),0)]))
    elements.append(tel)
    elements.append(sp(3))

    # ── 4. TRƯỜNG [10]→[22] — STATIC TEMPLATE với 2 cột chính xác ──
    # Helper: dòng đơn
    def fld(code, label, val=""):
        return [Paragraph(f"[{code}] {label}", s9),
                Paragraph(f"<b>{val}</b>" if val else " ", s9)]

    # Helper: 2 trường trên 1 hàng — dùng Table 50/50 cố định
    def fld2(c1, l1, v1, c2, l2, v2, w1=120, w2=80, w3=120, w4=75):
        return [
            Paragraph(f"[{c1}] {l1}", s9),
            Table([[
                Paragraph(f"<b>{v1}</b>" if v1 else " ", s9),
                Paragraph(f"[{c2}] {l2}", s9),
                Paragraph(f"<b>{v2}</b>" if v2 else " ", s9)
            ]], colWidths=[w1, w2, w3],
            style=[('TOPPADDING',(0,0),(-1,-1),0),
                   ('BOTTOMPADDING',(0,0),(-1,-1),0),
                   ('LEFTPADDING',(0,0),(-1,-1),0)])
        ]

    dia_g = " ".join(filter(None,[ct12g_nha,ct12g_ph,ct12g_qu,ct12g_ti]))
    dia_h = " ".join(filter(None,[ct12h_nha,ct12h_ph,ct12h_qu,ct12h_ti]))

    ext = [
        fld("10","Số CMND (trường hợp cá nhân khai thuế tự tính thuế):", ct10),
        fld("11","Số CMND (trường hợp hộp cá nhân khai thuế chưa có thông tin sau):", ct11),
        fld2("12a","Ngày sinh:", ct12a, "12b","Quốc tịch:", ct12b),
        fld2("12c.1","Mã:", ct12c_ma, "12c.2","Tên:", ct12c_ten, w2=40, w3=155),
        fld("12c","Số CMND/CCCD:", ct12c_so),
        fld2("12c.3","Ngày cấp:", ct12c_ngay, "12c.4","Loại nơi cấp:", ct12c_loai),
        fld("12c.5","Nơi cấp:", ct12c_noi),
        fld2("12d","Số hộ chiếu:", ct12d_so, "12d.1","Tên:", ct12d_ten, w2=50, w3=140),
        fld2("12d.2","Ngày cấp:", ct12d_ngay, "12d.3","Nơi cấp:", ct12d_noi),
        fld2("12dd","Số giấy thông hành:", ct12dd_so, "12dd.1","Tên:", ct12dd_ten, w2=60, w3=120),
        fld2("12dd.2","Ngày cấp:", ct12dd_ngay, "12dd.3","Nơi cấp:", ct12dd_noi),
        fld2("12e","Số CMND biên giới:", ct12e_so, "12e.1","Tên:", ct12e_ten, w2=60, w3=120),
        fld2("12e.2","Ngày cấp:", ct12e_ngay, "12e.3","Nơi cấp:", ct12e_noi),
        fld2("12f","Số giấy tờ khác:", ct12f_so, "12f.1","Tên:", ct12f_ten, w2=60, w3=120),
        fld2("12f.2","Ngày cấp:", ct12f_ngay, "12f.3","Nơi cấp:", ct12f_noi),

        fld("12g","Địa chỉ nơi cho thuê:", dia_g),
        fld2("12g.1","Phường/xã:", ct12g_ph, "12g.2","Quận/huyện:", ct12g_qu),
        fld("12g.3","Tỉnh/Thành phố:", ct12g_ti),
        fld("12h","Địa chỉ đăng ký hộ chiếu/kinh doanh:", dia_h),
        fld2("12h.1","Phường/xã:", ct12h_ph, "12h.2","Quận/huyện:", ct12h_qu),
        fld("12h.3","Tỉnh/Thành phố:", ct12h_ti),
        [Paragraph("[12i] Số giấy tờ:", s9),
         Table([[Paragraph(f"<b>{ct12i_so}</b>",s9),
                 Paragraph("[12i.1] Ngày cấp:",s9), Paragraph(f"<b>{ct12i_ngay}</b>",s9),
                 Paragraph("[12i.2] Cơ quan:",s9),  Paragraph(f"<b>{ct12i_cq}</b>",s9)]],
               colWidths=[80,65,65,65,10],
               style=[('LEFTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),
                      ('BOTTOMPADDING',(0,0),(-1,-1),0)])],
        fld("12k","Vốn kinh doanh (đồng):", ct12k),
        fld("16","Tổ chức nộp thuế thay:", tc16),
        fld2("17","Mã số thuế:", tc17, "18","Địa chỉ:", tc18, w2=60, w3=140),
        [Paragraph("[19] Điện thoại:", s9),
         Table([[Paragraph(f"<b>{tc19}</b>",s9),
                 Paragraph("[20] Fax:",s9), Paragraph(f"<b>{tc20}</b>",s9),
                 Paragraph("[21] Email:",s9), Paragraph(f"<b>{tc21}</b>",s9)]],
               colWidths=[80,40,65,45,55],
               style=[('LEFTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),
                      ('BOTTOMPADDING',(0,0),(-1,-1),0)])],
        fld("22","Mã hợp đồng:", maHDong),
    ]

    t_ext = Table(ext, colWidths=[195, 320])
    t_ext.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),1),
        ('BOTTOMPADDING',(0,0),(-1,-1),1),
        ('LEFTPADDING',(0,0),(-1,-1),0),
    ]))
    elements.append(t_ext)
    elements.append(sp(5))

    # ── 5. PHẦN A — bọc KeepTogether để không bị cắt ngang trang ────
    col_w = [28, 302, 75, 110]

    tax_hdr = [Paragraph(f"<b>{t}</b>", s8bc) for t in
               ["STT","Chỉ tiêu","Mã chỉ tiêu","Số tiền"]]
    tax_body = [
        ["1","Tổng doanh thu phát sinh trong kỳ","[23]",    ct23 or "0"],
        ["2","Tổng doanh thu tính thuế",           "[24]",   ct24 or "0"],
        ["3","Tổng số thuế GTGT phải nộp",         "[25]",   ct25 or "0"],
        ["4","Tổng số phát sinh trong kỳ",         "[26]",   ct26 or "0"],
        ["5","Tiền phạt, bồi thường nhận được theo thỏa thuận tại hợp đồng (nếu có)","[27]", ct27 or "0"],
        ["6","Tổng số thuế TNCN phải nộp tính nhằm bồi thường, phạt vi phạm hợp đồng (nếu có)","[28]", ct28 or "0"],
        ["7","Tổng số thuế TNCN phải nộp [29]=[26]+[28]","[29]", ct29 or "0"],
    ]
    rows = [tax_hdr] + [
        [Paragraph(r[0],s8c), Paragraph(r[1],s8),
         Paragraph(r[2],s8c), Paragraph(fmt_num(r[3]),s8r)]
        for r in tax_body
    ]
    t_tax = Table(rows, colWidths=col_w, repeatRows=1)
    t_tax.setStyle(TableStyle([
        ('GRID',          (0,0),(-1,-1), 0.5, colors.black),
        ('BACKGROUND',    (0,0),(-1,0),  colors.lightgrey),
        ('BACKGROUND',    (0,-1),(-1,-1),colors.lightyellow),
        ('FONTNAME',      (0,-1),(-1,-1), fb),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('ALIGN',         (0,0),(0,-1),  'CENTER'),
        ('ALIGN',         (2,0),(2,-1),  'CENTER'),
        ('ALIGN',         (3,0),(3,-1),  'RIGHT'),
        ('TOPPADDING',    (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LEFTPADDING',   (0,0),(-1,-1), 3),
    ]))

    unit_t = Table([[Paragraph("Đơn vị tính: Đồng Việt Nam", s8)]], colWidths=[W])
    unit_t.setStyle(TableStyle([('ALIGN',(0,0),(0,0),'RIGHT')]))

    # KeepTogether: giữ toàn bộ Phần A trên cùng 1 trang
    phần_a = KeepTogether([
        Paragraph("<b>A. PHẦN CÁ NHÂN KÊ KHAI NGHĨA VỤ THUẾ</b>", s9b),
        sp(2), unit_t, t_tax, sp(2),
        Paragraph("<i>(TNCN: Thu nhập cá nhân; GTGT: Giá trị gia tăng)</i>", s8),
    ])
    elements.append(phần_a)
    elements.append(sp(6))

    # ── 6. CAM KẾT + KÝ TÊN ─────────────────────────────────────────
    elements.append(Paragraph(
        "Tôi cam đoan số liệu khai trên là đúng và chịu trách nhiệm trước pháp luật về số liệu đã khai...", s9))
    elements.append(sp(6))
    now = datetime.datetime.now()
    elements.append(Paragraph(f"Ngày {now.day:02d} tháng {now.month:02d} năm {now.year}", s9r))
    elements.append(sp(4))

    sig = Table([[
        Paragraph("<b>NHÂN VIÊN ĐẠI LÝ THUẾ</b>", s9bi),
        Paragraph("<b>NGƯỜI NỘP THUẾ hoặc<br/>ĐẠI DIỆN HỢP PHÁP CỦA NGƯỜI NỘP THUẾ</b>", s9bi),
    ],[
        Paragraph("Họ và tên:", s9),
        Paragraph("(Ký, ghi rõ họ tên, đóng dấu (nếu có))", s8),
    ],[
        Paragraph("Chứng chỉ hành nghề số:", s9), "",
    ]], colWidths=[257, 258])
    sig.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                              ('VALIGN',(0,0),(-1,-1),'TOP'),
                              ('TOPPADDING',(0,0),(-1,-1),3)]))
    elements.append(sig)

    # ── 7. PHỤ LỤC — A4 ngang (Landscape) ──────────────────────────
    hop_dong_list = get_all(root, 'CTietBKeHDongTTS')
    if hop_dong_list:
        elements.append(PageBreak())

        # Tiêu đề phụ lục
        elements.append(Paragraph(
            "<b>PHỤ LỤC BẢNG KÊ CHI TIẾT HỢP ĐỒNG CHO THUÊ TÀI SẢN (01/BK-TTS)</b>", s10bc))
        elements.append(Paragraph("(Kèm theo tờ khai 01/TTS)", N('subb',fontSize=9,leading=12,alignment=1)))
        elements.append(sp(5))

        # Cột phụ lục — sử dụng toàn bộ chiều rộng A4 landscape (giả lập bằng font nhỏ)
        PW = [22, 38, 55, 115, 60, 50, 50, 55, 45, 45, 80]
        ph = [Paragraph(f"<b>{t}</b>", s7c) for t in [
            "STT","Loại HĐ","MST bên thuê","Tên bên thuê","Số HĐ",
            "Ngày bắt đầu","Ngày kết thúc","Doanh thu tính thuế",
            "Thuế GTGT","Thuế TNCN","Địa chỉ BĐS"]]
        pdata = [ph]

        for hd in hop_dong_list:
            def gv(t):
                for c in hd:
                    if strip_ns(c.tag) == t:
                        return (c.text or "").strip()
                return ""
            stt_val = gv('ct06')
            # Indent dòng kỳ thanh toán (STT dạng x.y)
            is_sub = '.' in stt_val
            indent = "&nbsp;&nbsp;" if is_sub else ""
            s_row = s7  # font nhỏ cho bảng phụ lục

            pdata.append([
                Paragraph(stt_val,  s7c),
                Paragraph(gv('ct06a_ten'), s7),
                Paragraph(gv('ct08'),      s7c),
                Paragraph(f"{indent}{gv('ct07')}", s7),
                Paragraph(gv('ct11'),      s7),
                Paragraph(gv('ct17'),      s7c),
                Paragraph(gv('ct18'),      s7c),
                Paragraph(fmt_num(gv('ct24')), N('s7r',fontSize=7,leading=9,alignment=2)),
                Paragraph(fmt_num(gv('ct25')), N('s7r2',fontSize=7,leading=9,alignment=2)),
                Paragraph(fmt_num(gv('ct26')), N('s7r3',fontSize=7,leading=9,alignment=2)),
                Paragraph(gv('ct15_diaChi'),   s7),
            ])

        t_p = Table(pdata, colWidths=PW, repeatRows=1)
        t_p.setStyle(TableStyle([
            ('GRID',          (0,0),(-1,-1), 0.4, colors.black),
            ('BACKGROUND',    (0,0),(-1,0),  colors.lightgrey),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('TOPPADDING',    (0,0),(-1,-1), 2),
            ('BOTTOMPADDING', (0,0),(-1,-1), 2),
            ('LEFTPADDING',   (0,0),(-1,-1), 2),
            ('RIGHTPADDING',  (0,0),(-1,-1), 2),
        ]))
        elements.append(t_p)

# ─────────────────────────────────────────────
# GENERIC RENDERER (Fallback)
# ─────────────────────────────────────────────
def xml_to_dict(element):
    result = {}
    for child in element:
        tag = strip_ns(child.tag)
        value = xml_to_dict(child) if len(child) > 0 else (
            child.text.strip() if child.text and child.text.strip() else "")
        if tag in result:
            if not isinstance(result[tag], list): result[tag] = [result[tag]]
            result[tag].append(value)
        else:
            result[tag] = value
    return result

def render_generic(root, elements, fn, fb):
    sN  = ParagraphStyle('gN',  fontName=fn, fontSize=9,  leading=13)
    sB  = ParagraphStyle('gB',  fontName=fb, fontSize=9,  leading=13)
    sT  = ParagraphStyle('gT',  fontName=fb, fontSize=13, leading=18, alignment=1)
    sMo = ParagraphStyle('gMo', fontName=fb, fontSize=10, leading=14, alignment=1)
    elements.append(Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b>", sMo))
    elements.append(Paragraph("Độc lập – Tự do – Hạnh phúc", sMo))
    elements.append(Spacer(1,8))
    elements.append(Paragraph(strip_ns(root.tag).upper(), sT))
    elements.append(Spacer(1,10))
    data = xml_to_dict(root)
    info, comp = {}, []
    def split(d):
        for k,v in d.items():
            if isinstance(v, dict): split(v)
            elif isinstance(v, list): comp.append((k,v))
            else: info[k] = v
    split(data)
    rows = [[Paragraph(f"[{i+1:02d}] {k}", sN),
             Paragraph(f"<b>{fmt_num(v) if v else ''}</b>", sN)]
            for i,(k,v) in enumerate(info.items())]
    if rows:
        t = Table(rows, colWidths=[200,315])
        t.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),2)]))
        elements.append(t); elements.append(Spacer(1,10))
    for title, rws in comp:
        dict_rows = [r for r in rws if isinstance(r, dict)]
        if not dict_rows: continue
        elements.append(Paragraph(f"<b>{title.upper()}</b>", sB))
        keys = list(dict_rows[0].keys())
        body = [[Paragraph(fmt_num(r.get(k,"")),sN) for k in keys] for r in dict_rows]
        t = Table([[Paragraph(f"<b>{k.upper()}</b>",sB) for k in keys]]+body,repeatRows=1)
        t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),
                                ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
                                ('FONTSIZE',(0,0),(-1,-1),8)]))
        elements.append(t); elements.append(Spacer(1,10))

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def extract_tax_metadata(xml_content):
    try:
        root = ET.fromstring(pre_process_xml(xml_content))
        mst, ten_tk, ma_tk, ky = "Unknown","TỜ KHAI THUẾ","","Unknown"
        for elem in root.iter():
            t = strip_ns(elem.tag)
            if t == 'mst' and elem.text: mst = elem.text.strip()
            if t == 'tenTKhai' and elem.text: ten_tk = elem.text.strip()
            if t == 'maTKhai' and elem.text: ma_tk = elem.text.strip()
            if t == 'kyKKhaiTuNgay' and elem.text: ky = elem.text.strip()
        return {"name": ten_tk, "mst": mst, "period": ky, "form": ma_tk}
    except:
        return {"name":"TỜ KHAI THUẾ","mst":"","period":"","form":""}

def generate_tax_pdf(xml_content, title="BÁO CÁO THUẾ"):
    clean = pre_process_xml(xml_content)
    root  = ET.fromstring(clean)
    meta  = extract_tax_metadata(xml_content)
    ma_tk = meta.get("form","")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=25,   bottomMargin=25)

    font_ok = register_fonts()
    fn = 'VN'  if font_ok else 'Helvetica'
    fb = 'VNB' if font_ok else 'Helvetica-Bold'

    elements = []
    if ma_tk == "470":
        render_01TTS(root, elements, fn, fb)
    else:
        render_generic(root, elements, fn, fb)

    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
