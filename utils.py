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
                                Paragraph, Spacer, PageBreak)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas

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

def get(root, *tags):
    for tag in tags:
        for elem in root.iter():
            if strip_ns(elem.tag) == tag:
                t = elem.text
                return t.strip() if t and t.strip() else ""
    return ""

def gs(root, tag_parent, tag_child):
    """Lấy text từ thẻ con của một thẻ cha cụ thể."""
    for p in root.iter():
        if strip_ns(p.tag) == tag_parent:
            for c in p:
                if strip_ns(c.tag) == tag_child:
                    return (c.text or "").strip()
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
            except:
                continue
    return False

# ─────────────────────────────────────────────
# PAGE NUMBER CALLBACK
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
            self.draw_page_number(num_pages)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 8)
        self.drawRightString(
            A4[0] - 40, 20,
            f"{self._pageNumber}/{page_count}"
        )

# ─────────────────────────────────────────────
# TEMPLATE 01/TTS  (maTKhai = 470)
# ─────────────────────────────────────────────
def render_01TTS(root, elements, fn, fb):

    # Styles
    def N(name, **kw): return ParagraphStyle(name, fontName=fn, **kw)
    def B(name, **kw): return ParagraphStyle(name, fontName=fb, **kw)

    s8   = N('s8',   fontSize=8,  leading=11)
    s8r  = N('s8r',  fontSize=8,  leading=11, alignment=2)
    s8c  = N('s8c',  fontSize=8,  leading=11, alignment=1)
    s8b  = B('s8b',  fontSize=8,  leading=11)
    s8bc = B('s8bc', fontSize=8,  leading=11, alignment=1)
    s9   = N('s9',   fontSize=9,  leading=12)
    s9r  = N('s9r',  fontSize=9,  leading=12, alignment=2)
    s9c  = N('s9c',  fontSize=9,  leading=12, alignment=1)
    s9b  = B('s9b',  fontSize=9,  leading=12)
    s9bi = B('s9bi', fontSize=9,  leading=12, alignment=1)
    s10  = N('s10',  fontSize=10, leading=13)
    s10b = B('s10b', fontSize=10, leading=13)
    s10c = N('s10c', fontSize=10, leading=13, alignment=1)
    s10bc= B('s10bc',fontSize=10, leading=13, alignment=1)
    s13b = B('s13b', fontSize=13, leading=17, alignment=1)

    W   = 515  # usable width
    PAD = [('LEFTPADDING',(0,0),(-1,-1),0),
           ('RIGHTPADDING',(0,0),(-1,-1),2),
           ('TOPPADDING',(0,0),(-1,-1),1),
           ('BOTTOMPADDING',(0,0),(-1,-1),1)]

    def row(label, value, lw=200, vw=315):
        """Tạo 1 dòng thông tin label: value."""
        t = Table([[Paragraph(label, s9), Paragraph(value, s9b)]],
                  colWidths=[lw, vw])
        t.setStyle(TableStyle(PAD))
        return t

    def spacer(h=3): return Spacer(1, h)

    # ── ĐỌC DỮ LIỆU XML ──────────────────────────────────────────────
    tenTKhai  = get(root, 'tenTKhai')
    loai      = get(root, 'loaiTKhai')
    soLan     = get(root, 'soLan')
    kyTuNgay  = get(root, 'kyKKhaiTuNgay')
    kyDenNgay = get(root, 'kyKKhaiDenNgay')
    mst       = get(root, 'mst')
    tenNNT    = get(root, 'tenNNT')
    dchi      = get(root, 'dchiNNT')
    dthoai    = get(root, 'dthoaiNNT')
    fax       = get(root, 'faxNNT')
    email     = get(root, 'emailNNT')

    theoPL_DS   = get(root, 'khaiTheoPLuatDanSu')
    theoPL_Thue = get(root, 'khaiTheoPLuatThue')
    is_ds   = chk(theoPL_DS)
    is_thue = chk(theoPL_Thue)
    is_dau  = "X" if loai == "C" else " "
    is_bs   = "X" if loai == "B" else " "

    ct10 = get(root, 'ct10')
    ct11 = get(root, 'ct11')

    ct12a = gs(root,'CNKDChuaDangKyThue','ct12a_ngaySinh')
    ct12b = gs(root,'CNKDChuaDangKyThue','ct12b_tenQuocTich')
    ct12c_ma    = gs(root,'CNKDChuaDangKyThue','ct12c_ma')
    ct12c_ten   = gs(root,'CNKDChuaDangKyThue','ct12c_ten')
    ct12c_so    = gs(root,'CNKDChuaDangKyThue','ct12c_soCMND_CCCD')
    ct12c_ngay  = gs(root,'CNKDChuaDangKyThue','ct12c_1_ngayCap')
    ct12c_noi   = gs(root,'CNKDChuaDangKyThue','ct12c_2_noiCap_ten')
    ct12c_loai  = gs(root,'CNKDChuaDangKyThue','ct12c_2_noiCap_loai')

    ct12d_ma    = gs(root,'CNKDKhongCoCMND_CCCD','ct12d_ma')
    ct12d_ten   = gs(root,'CNKDKhongCoCMND_CCCD','ct12d_ten')
    ct12d_so    = gs(root,'CNKDKhongCoCMND_CCCD','ct12d_soHoChieu')
    ct12d_ngay  = gs(root,'CNKDKhongCoCMND_CCCD','ct12d_1_ngayCap')
    ct12d_noi   = gs(root,'CNKDKhongCoCMND_CCCD','ct12d_2_noiCap_ten')

    ct12dd_ma   = gs(root,'CNKDKhongCoCMND_CCCD','ct12dd_ma')
    ct12dd_ten  = gs(root,'CNKDKhongCoCMND_CCCD','ct12dd_ten')
    ct12dd_so   = gs(root,'CNKDKhongCoCMND_CCCD','ct12dd_soGiayThongHanh')
    ct12dd_ngay = gs(root,'CNKDKhongCoCMND_CCCD','ct12dd_1_ngayCap')
    ct12dd_noi  = gs(root,'CNKDKhongCoCMND_CCCD','ct12dd_2_noiCap_ten')

    ct12e_ma    = gs(root,'CNKDKhongCoCMND_CCCD','ct12e_ma')
    ct12e_ten   = gs(root,'CNKDKhongCoCMND_CCCD','ct12e_ten')
    ct12e_so    = gs(root,'CNKDKhongCoCMND_CCCD','ct12e_soCMNDBienGioi')
    ct12e_ngay  = gs(root,'CNKDKhongCoCMND_CCCD','ct12e_1_ngayCap')
    ct12e_noi   = gs(root,'CNKDKhongCoCMND_CCCD','ct12e_2_noiCap_ten')

    ct12f_ma    = gs(root,'CNKDKhongCoCMND_CCCD','ct12f_ma')
    ct12f_ten   = gs(root,'CNKDKhongCoCMND_CCCD','ct12f_ten')
    ct12f_so    = gs(root,'CNKDKhongCoCMND_CCCD','ct12f_soGiayToKhac')
    ct12f_ngay  = gs(root,'CNKDKhongCoCMND_CCCD','ct12f_1_ngayCap')
    ct12f_noi   = gs(root,'CNKDKhongCoCMND_CCCD','ct12f_2_noiCap_ten')

    ct12g_nha   = gs(root,'CT12g','ct12g_soNha')
    ct12g_phuong= gs(root,'CT12g','ct12g_tenPhuong')
    ct12g_quan  = gs(root,'CT12g','ct12g_tenQuan')
    ct12g_tinh  = gs(root,'CT12g','ct12g_tenTinh')

    ct12h_nha   = gs(root,'CT12h','ct12h_soNha')
    ct12h_phuong= gs(root,'CT12h','ct12h_tenPhuong')
    ct12h_quan  = gs(root,'CT12h','ct12h_tenQuan')
    ct12h_tinh  = gs(root,'CT12h','ct12h_tenTinh')

    ct12i_so    = gs(root,'CT12i','ct12i_soGiayTo')
    ct12i_ngay  = gs(root,'CT12i','ct12i_ngayCap')
    ct12i_cq    = gs(root,'CT12i','ct12i_coQuanCap')

    ct12k  = get(root,'ct12k')
    maHDong= get(root,'maHDong')

    # [16-21] PHẢI lấy từ ToChucNopThueThay
    tc16 = gs(root,'ToChucNopThueThay','ct16')
    tc17 = gs(root,'ToChucNopThueThay','ct17')
    tc18 = gs(root,'ToChucNopThueThay','ct18')
    tc19 = gs(root,'ToChucNopThueThay','ct19')
    tc20 = gs(root,'ToChucNopThueThay','ct20')
    tc21 = gs(root,'ToChucNopThueThay','ct21')

    # Chỉ tiêu tính thuế
    ct23 = fmt_num(get(root,'ct23')); ct24 = fmt_num(get(root,'ct24'))
    ct25 = fmt_num(get(root,'ct25')); ct26 = fmt_num(get(root,'ct26'))
    ct27 = fmt_num(get(root,'ct27')); ct28 = fmt_num(get(root,'ct28'))
    ct29 = fmt_num(get(root,'ct29'))

    # ── 1. HEADER ────────────────────────────────────────────────────
    hdr = Table([[
        Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>"
                  "Độc lập – Tự do – Hạnh phúc<br/>─────────────────────", s10c),
        Table([[Paragraph("<b>Mẫu số: 01/TTS</b>", s8bc)],
               [Paragraph("(Ban hành kèm theo Thông tư số 40/2021/TT-BTC<br/>"
                          "ngày 01/06/2021 của Bộ trưởng Bộ Tài chính)", s8c)]],
              colWidths=[160],
              style=[('BOX',(0,0),(-1,-1),0.5,colors.black),
                     ('TOPPADDING',(0,0),(-1,-1),3),
                     ('BOTTOMPADDING',(0,0),(-1,-1),3),
                     ('LEFTPADDING',(0,0),(-1,-1),3)])
    ]], colWidths=[355, 160])
    hdr.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    elements.append(hdr)
    elements.append(spacer(5))

    # ── 2. TIÊU ĐỀ ──────────────────────────────────────────────────
    elements.append(Paragraph(tenTKhai.upper() or
        "TỜ KHAI ĐỐI VỚI HOẠT ĐỘNG CHO THUÊ TÀI SẢN(TT40/2021)", s13b))
    elements.append(Paragraph(
        "(Áp dụng đối với cá nhân có hoạt động cho thuê tài sản trực tiếp khai thuế với cơ quan thuế "
        "trừ cá nhân trực tiếp ký hợp đồng thuê với tổ chức kinh tế; thay cho cá nhân)", s8c))
    elements.append(spacer(3))

    elements.append(Paragraph(
        f"Cá nhân cho thuê tài sản trực tiếp khai thuế: Tổ chức, cá nhân khai thuế thay, nộp thuế thay "
        f"cho cá nhân ký quyền theo quy định của pháp luật dân sự(*): [<b>{is_ds}</b>]", s9))
    elements.append(Paragraph(
        f"Doanh nghiệp, tổ chức có tư cách pháp nhân khai thuế thay, nộp thuế thay cho cá nhân: [<b>{is_thue}</b>]", s9))
    elements.append(spacer(2))
    elements.append(Paragraph(
        f"[<b>{is_dau}</b>] Kỳ tính thuế: "
        f"<u>Từ ngày:</u> <b>{kyTuNgay}</b>   "
        f"<u>Đến ngày:</u> <b>{kyDenNgay}</b>", s9))
    elements.append(Paragraph(
        f"[<b>{is_bs}</b>] Lần đầu: [<b>{'X' if soLan=='0' else ' '}</b>]   "
        f"Bổ sung lần thứ [<b>{soLan if soLan!='0' else ''}</b>]", s9))
    elements.append(spacer(4))

    # ── 3. THÔNG TIN NGƯỜI NỘP THUẾ [04]→[09] ──────────────────────
    def frow(code, label, val, lw=190, vw=325):
        return [Paragraph(f"[{code}] {label}", s9),
                Paragraph(f"<b>{val}</b>", s9)]

    basic = [
        frow("04","Tên người nộp thuế:",  tenNNT),
        frow("05","Mã số thuế:",           mst),
        frow("06","Địa chỉ:",              dchi),
    ]
    t_basic = Table(basic, colWidths=[190, 325])
    t_basic.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),
                                  ('TOPPADDING',(0,0),(-1,-1),1),
                                  ('BOTTOMPADDING',(0,0),(-1,-1),1)]))
    elements.append(t_basic)

    # [07][08][09] trên 1 dòng
    tel_row = Table([[
        Paragraph("[07] Điện thoại:", s9),
        Paragraph(f"<b>{dthoai}</b>", s9),
        Paragraph("[08] Fax:", s9),
        Paragraph(f"<b>{fax}</b>", s9),
        Paragraph("[09] Email:", s9),
        Paragraph(f"<b>{email}</b>", s9),
    ]], colWidths=[80, 100, 45, 70, 50, 170])
    tel_row.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),1),
                                  ('LEFTPADDING',(0,0),(-1,-1),0)]))
    elements.append(tel_row)
    elements.append(spacer(3))

    # ── 4. CÁC TRƯỜNG [10]→[22] — STATIC TEMPLATE ──────────────────
    # Helper tạo dòng thông tin với indent
    def fld(code, label, *vals, indent=0):
        pad = "&nbsp;" * (indent * 4)
        val_str = "   ".join(f"<b>{v}</b>" for v in vals if v is not None)
        return [Paragraph(f"{pad}[{code}] {label}", s9),
                Paragraph(val_str or " ", s9b)]

    def fld2(code1, lbl1, val1, code2, lbl2, val2):
        """2 fields trên cùng 1 dòng."""
        return [
            Paragraph(f"[{code1}] {lbl1}", s9),
            Table([[Paragraph(f"<b>{val1}</b>", s9),
                    Paragraph(f"[{code2}] {lbl2}", s9),
                    Paragraph(f"<b>{val2}</b>", s9)]],
                  colWidths=[100, 90, 135],
                  style=[('LEFTPADDING',(0,0),(-1,-1),0),
                         ('TOPPADDING',(0,0),(-1,-1),0),
                         ('BOTTOMPADDING',(0,0),(-1,-1),0)])
        ]

    dia_g = " ".join(filter(None,[ct12g_nha, ct12g_phuong, ct12g_quan, ct12g_tinh]))
    dia_h = " ".join(filter(None,[ct12h_nha, ct12h_phuong, ct12h_quan, ct12h_tinh]))

    ext = [
        fld("10", "Số CMND (trường hợp cá nhân khai thuế tự tính thuế):", ct10),
        fld("11", "Số CMND (trường hợp hộp cá nhân khai thuế chưa có thông tin sau):", ct11),
        fld2("12a","Ngày sinh:", ct12a, "12b","Quốc tịch:", ct12b),

        # [12.1] Trường hợp cá nhân kinh doanh chưa đăng ký thuế
        [Paragraph("[+] [12.1] Trường hợp cá nhân kinh doanh chưa đăng ký thuế:", s9b), Paragraph("", s9)],
        fld2("12c.1","Mã:", ct12c_ma, "12c.2","Tên:", ct12c_ten, ),
        fld("12c", "Số CMND/CCCD:", ct12c_so, indent=1),
        fld2("12c.3","Ngày cấp:", ct12c_ngay, "12c.4","Loại nơi cấp:", ct12c_loai),
        fld("12c.5","Nơi cấp:", ct12c_noi, indent=1),

        # [12.2] Trường hợp cá nhân kinh doanh không có CMND/CCCD
        [Paragraph("[+] [12.2] Trường hợp cá nhân kinh doanh không có CMND/CCCD:", s9b), Paragraph("", s9)],
        fld2("12d","Số hộ chiếu:", ct12d_so, "12d.1","Tên:", ct12d_ten),
        fld2("12d.2","Ngày cấp:", ct12d_ngay, "12d.3","Nơi cấp:", ct12d_noi),

        fld2("12dd","Số giấy thông hành:", ct12dd_so, "12dd.1","Tên:", ct12dd_ten),
        fld2("12dd.2","Ngày cấp:", ct12dd_ngay, "12dd.3","Nơi cấp:", ct12dd_noi),

        fld2("12e","Số CMND biên giới:", ct12e_so, "12e.1","Tên:", ct12e_ten),
        fld2("12e.2","Ngày cấp:", ct12e_ngay, "12e.3","Nơi cấp:", ct12e_noi),

        fld2("12f","Số giấy tờ khác:", ct12f_so, "12f.1","Tên:", ct12f_ten),
        fld2("12f.2","Ngày cấp:", ct12f_ngay, "12f.3","Nơi cấp:", ct12f_noi),

        # [12g] [12h] địa chỉ
        [Paragraph("[12g] Số nhà, đường phố/thôn/xóm/phum/sóc/Tỉnh Thành Phố nơi cho thuê:", s9),
         Paragraph(f"<b>{dia_g}</b>", s9b)],
        [Paragraph("[12g.1] Phường/xã/Thị trấn:", s9), Paragraph(f"<b>{ct12g_phuong}</b>", s9b)],
        [Paragraph("[12g.2] Phường/xã/Thị trấn:", s9), Paragraph(f"<b>{ct12g_quan}</b>", s9b)],
        [Paragraph("[12g.3] Tỉnh/ Thành phố:", s9), Paragraph(f"<b>{ct12g_tinh}</b>", s9b)],

        [Paragraph("[12h] Số nhà, đường phố/thôn/xóm/phum/sóc nơi đăng ký hộ chiếu/KD:", s9),
         Paragraph(f"<b>{dia_h}</b>", s9b)],
        [Paragraph("[12h.1] Phường/xã/Thị trấn:", s9), Paragraph(f"<b>{ct12h_phuong}</b>", s9b)],
        [Paragraph("[12h.2] Quận/Huyện/Thị xã/Thành phố thuộc tỉnh:", s9), Paragraph(f"<b>{ct12h_quan}</b>", s9b)],
        [Paragraph("[12h.3] Tỉnh/ Thành phố:", s9), Paragraph(f"<b>{ct12h_tinh}</b>", s9b)],

        [Paragraph("[12i] Số giấy tờ:", s9),
         Table([[Paragraph(f"<b>{ct12i_so}</b>", s9),
                 Paragraph("[12i.1] Ngày cấp:", s9),
                 Paragraph(f"<b>{ct12i_ngay}</b>", s9),
                 Paragraph("[12i.2] Cơ quan cấp:", s9),
                 Paragraph(f"<b>{ct12i_cq}</b>", s9)]],
               colWidths=[80,70,70,80,25],
               style=[('LEFTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0)])],

        fld("12k", "Vốn kinh doanh (đồng):", ct12k),

        # [16-21] Tổ chức nộp thuế thay
        [Paragraph("[16] Tổ chức nộp thay:", s9), Paragraph(f"<b>{tc16}</b>", s9b)],
        [Paragraph("[17] Mã số thuế:", s9),        Paragraph(f"<b>{tc17}</b>", s9b)],
        [Paragraph("[18] Địa chỉ:", s9),           Paragraph(f"<b>{tc18}</b>", s9b)],
        [Paragraph("[19] Điện thoại:", s9),
         Table([[Paragraph(f"<b>{tc19}</b>",s9),
                 Paragraph("[20] Fax:",s9),Paragraph(f"<b>{tc20}</b>",s9),
                 Paragraph("[21] Email:",s9),Paragraph(f"<b>{tc21}</b>",s9)]],
               colWidths=[80,45,60,45,95],
               style=[('LEFTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0)])],
        fld("22", "Mã hợp đồng:", maHDong),
    ]

    t_ext = Table(ext, colWidths=[230, 285])
    t_ext.setStyle(TableStyle([
        ('VALIGN',        (0,0),(-1,-1),'TOP'),
        ('TOPPADDING',    (0,0),(-1,-1), 1),
        ('BOTTOMPADDING', (0,0),(-1,-1), 1),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 2),
    ]))
    elements.append(t_ext)
    elements.append(spacer(5))

    # ── 5. PHẦN A: BẢNG SỐ LIỆU ────────────────────────────────────
    elements.append(Paragraph("<b>A. PHẦN CÁ NHÂN KÊ KHAI NGHĨA VỤ THUẾ</b>", s9b))
    elements.append(spacer(2))

    unit_t = Table([[Paragraph("Đơn vị tính: Đồng Việt Nam", s8)]], colWidths=[W])
    unit_t.setStyle(TableStyle([('ALIGN',(0,0),(0,0),'RIGHT')]))
    elements.append(unit_t)

    col_w = [28, 300, 75, 112]
    tax_hdr = [Paragraph("<b>STT</b>",s8bc), Paragraph("<b>Chỉ tiêu</b>",s8bc),
               Paragraph("<b>Mã chỉ tiêu</b>",s8bc), Paragraph("<b>Số tiền</b>",s8bc)]
    tax_body = [
        ["1","Tổng doanh thu phát sinh trong kỳ","[23]", ct23 or "0"],
        ["2","Tổng doanh thu tính thuế",           "[24]", ct24 or "0"],
        ["3","Tổng số thuế GTGT phải nộp",         "[25]", ct25 or "0"],
        ["4","Tổng số phát sinh trong kỳ",         "[26]", ct26 or "0"],
        ["5","Tiền phạt, bồi thường nhận được theo thỏa thuận tại hợp đồng (nếu có)","[27]", ct27 or "0"],
        ["6","Tổng số thuế TNCN phải nộp tính nhằm bồi thường, phạt vi phạm hợp đồng (nếu có)","[28]", ct28 or "0"],
        ["7","Tổng số thuế TNCN phải nộp [29]+[26]+[28]","[29]", ct29 or "0"],
    ]
    rows = [tax_hdr] + [
        [Paragraph(r[0], s8c), Paragraph(r[1], s8),
         Paragraph(r[2], s8c), Paragraph(fmt_num(r[3]) if r[3] else "0", s8r)]
        for r in tax_body
    ]
    t_tax = Table(rows, colWidths=col_w, repeatRows=1, splitByRow=0)
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
        ('RIGHTPADDING',  (0,0),(-1,-1), 3),
    ]))
    elements.append(t_tax)
    elements.append(spacer(3))
    elements.append(Paragraph("<i>(TNCN: Thu nhập cá nhân; GTGT: Giá trị gia tăng)</i>", s8))

    # ── 6. CAM KẾT + KÝ TÊN ──────────────────────────────────────────
    elements.append(spacer(6))
    elements.append(Paragraph(
        "Tôi cam đoan số liệu khai trên là đúng và chịu trách nhiệm trước pháp luật về số liệu đã khai...", s9))
    elements.append(spacer(6))
    now = datetime.datetime.now()
    elements.append(Paragraph(
        f"Ngày {now.day:02d} tháng {now.month:02d} năm {now.year}", s9r))
    elements.append(spacer(4))

    sig = Table([[
        Paragraph("<b>NHÂN VIÊN ĐẠI LÝ THUẾ</b>", s9bi),
        Paragraph("<b>NGƯỜI NỘP THUẾ hoặc<br/>ĐẠI DIỆN HỢP PHÁP CỦA NGƯỜI NỘP THUẾ</b>", s9bi)
    ],[
        Paragraph("Họ và tên:", s9), Paragraph("(Ký, ghi rõ họ tên, đóng dấu (nếu có))", s8)
    ],[
        Paragraph("Chứng chỉ hành nghề số:", s9), ""
    ]], colWidths=[257, 258])
    sig.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                              ('VALIGN',(0,0),(-1,-1),'TOP'),
                              ('TOPPADDING',(0,0),(-1,-1),3)]))
    elements.append(sig)

    # ── 7. PHỤ LỤC TRANG 2+ ───────────────────────────────────────────
    hop_dong_list = get_all(root, 'CTietBKeHDongTTS')
    if hop_dong_list:
        elements.append(PageBreak())
        elements.append(Paragraph(
            "<b>PHỤ LỤC BẢNG KÊ CHI TIẾT HỢP ĐỒNG CHO THUÊ TÀI SẢN</b>", s10bc))
        elements.append(Paragraph("(Kèm theo tờ khai thuế 01/TTS)", s9c))
        elements.append(spacer(6))

        pw = [22, 38, 60, 110, 60, 45, 45, 48, 48, 39]
        ph = [Paragraph(f"<b>{t}</b>", s8bc) for t in [
            "STT","Loại HĐ","MST bên thuê","Tên bên thuê",
            "Số HĐ","Ngày bắt đầu","Ngày kết thúc",
            "Doanh thu tính thuế","Thuế GTGT","Thuế TNCN"]]
        pdata = [ph]
        for i, hd in enumerate(hop_dong_list):
            def gv(t):
                for c in hd:
                    if strip_ns(c.tag) == t:
                        return (c.text or "").strip()
                return ""
            pdata.append([
                Paragraph(gv('ct06'),          s8c),
                Paragraph(gv('ct06a_ten'),     s8),
                Paragraph(gv('ct08'),          s8c),
                Paragraph(gv('ct07'),          s8),
                Paragraph(gv('ct11'),          s8),
                Paragraph(gv('ct17'),          s8c),
                Paragraph(gv('ct18'),          s8c),
                Paragraph(fmt_num(gv('ct24')), s8r),
                Paragraph(fmt_num(gv('ct25')), s8r),
                Paragraph(fmt_num(gv('ct26')), s8r),
            ])

        t_p = Table(pdata, colWidths=pw, repeatRows=1)
        t_p.setStyle(TableStyle([
            ('GRID',          (0,0),(-1,-1), 0.5, colors.black),
            ('BACKGROUND',    (0,0),(-1,0),  colors.lightgrey),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('TOPPADDING',    (0,0),(-1,-1), 2),
            ('BOTTOMPADDING', (0,0),(-1,-1), 2),
            ('LEFTPADDING',   (0,0),(-1,-1), 2),
            ('RIGHTPADDING',  (0,0),(-1,-1), 2),
        ]))
        elements.append(t_p)

# ─────────────────────────────────────────────
# GENERIC RENDERER (fallback)
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
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(strip_ns(root.tag).upper(), sT))
    elements.append(Spacer(1,10))
    data = xml_to_dict(root)
    info_data, complex_data = {}, []
    def split(d):
        for k, v in d.items():
            if isinstance(v, dict): split(v)
            elif isinstance(v, list): complex_data.append((k,v))
            else: info_data[k] = v
    split(data)
    rows = [[Paragraph(f"[{i+1:02d}] {k}", sN), Paragraph(f"<b>{fmt_num(v) if v else ''}</b>", sN)]
            for i,(k,v) in enumerate(info_data.items())]
    if rows:
        t = Table(rows, colWidths=[200,315])
        t.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),2)]))
        elements.append(t); elements.append(Spacer(1,10))
    for title, rws in complex_data:
        dict_rows = [r for r in rws if isinstance(r, dict)]
        if not dict_rows: continue
        elements.append(Paragraph(f"<b>{title.upper()}</b>", sB))
        keys = list(dict_rows[0].keys())
        body = [[Paragraph(fmt_num(r.get(k,"")), sN) for k in keys] for r in dict_rows]
        t = Table([[Paragraph(f"<b>{k.upper()}</b>", sB) for k in keys]]+body, repeatRows=1)
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
