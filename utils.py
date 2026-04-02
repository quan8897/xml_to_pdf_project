import os
import xml.etree.ElementTree as ET
import io
import re
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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

def get_all(root, tag):
    """Lấy tất cả elements có tên tag."""
    return [e for e in root.iter() if strip_ns(e.tag) == tag]

def chk(val):
    """Chuyển true/false thành [X] hay [ ]."""
    if val and val.lower() == 'true':
        return "X"
    return " "

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
# TEMPLATE 01/TTS  (maTKhai = 470)
# ─────────────────────────────────────────────
def render_01TTS(root, elements, fn, fb):

    def sty(name, **kw):
        return ParagraphStyle(name, fontName=fn, **kw)
    def styB(name, **kw):
        return ParagraphStyle(name, fontName=fb, **kw)

    sN  = sty('n',  fontSize=9,  leading=13)
    sNc = sty('nc', fontSize=9,  leading=13, alignment=1)
    sNr = sty('nr', fontSize=9,  leading=13, alignment=2)
    sB  = styB('b', fontSize=9,  leading=13)
    sBc = styB('bc',fontSize=9,  leading=13, alignment=1)
    sT  = styB('t', fontSize=13, leading=18, alignment=1)
    sMo = styB('mo',fontSize=10, leading=14, alignment=1)
    sSm = sty('sm', fontSize=8,  leading=11)
    sBsm= styB('bsm',fontSize=8, leading=11)
    sBsmc=styB('bsmc',fontSize=8,leading=11, alignment=1)
    sSmr= sty('smr',fontSize=8,  leading=11, alignment=2)

    W = 515

    # ── ĐỌC DỮ LIỆU ──────────────────────────────────────────────────
    tenTKhai  = get(root, 'tenTKhai')
    loai      = get(root, 'loaiTKhai')
    soLan     = get(root, 'soLan')
    kyTuNgay  = get(root, 'kyKKhaiTuNgay')
    kyDenNgay = get(root, 'kyKKhaiDenNgay')
    ngayLap   = get(root, 'ngayLapTKhai')
    mst       = get(root, 'mst')
    tenNNT    = get(root, 'tenNNT')
    dchi      = get(root, 'dchiNNT')
    dthoai    = get(root, 'dthoaiNNT')
    fax       = get(root, 'faxNNT')
    email     = get(root, 'emailNNT')

    # Header fields
    theoPL_DS  = get(root, 'khaiTheoPLuatDanSu')
    theoPL_Thue= get(root, 'khaiTheoPLuatThue')
    ct10       = get(root, 'ct10')
    ct11       = get(root, 'ct11')
    ct12k      = get(root, 'ct12k')
    maHDong    = get(root, 'maHDong')

    # CaNhanKeKhai (chỉ tiêu tính thuế)
    ct23 = fmt_num(get(root, 'ct23'))
    ct24 = fmt_num(get(root, 'ct24'))
    ct25 = fmt_num(get(root, 'ct25'))
    ct26 = fmt_num(get(root, 'ct26'))
    ct27 = fmt_num(get(root, 'ct27'))
    ct28 = fmt_num(get(root, 'ct28'))
    ct29 = fmt_num(get(root, 'ct29'))

    # ── 1. HEADER ────────────────────────────────────────────────────
    box_st = [
        ('GRID',   (0,0),(-1,-1), 0.5, colors.black),
        ('ALIGN',  (0,0),(-1,-1), 'CENTER'),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1), 4),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('RIGHTPADDING',(0,0),(-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
    ]
    hdr = Table([[
        Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>Độc lập – Tự do – Hạnh phúc<br/>─────────────────────", sMo),
        Table([[
            Paragraph("<b>Mẫu số: 01/TTS</b>", sBc)
        ],[
            Paragraph("(Ban hành kèm theo Thông tư số 40/2021/TT-BTC<br/>ngày 01/06/2021 của Bộ trưởng Bộ Tài chính)", sSm)
        ]], colWidths=[165], style=box_st)
    ]], colWidths=[350, 165])
    hdr.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    elements.append(hdr)
    elements.append(Spacer(1, 6))

    # ── 2. TIÊU ĐỀ ──────────────────────────────────────────────────
    elements.append(Paragraph(tenTKhai.upper() or "TỜ KHAI ĐỐI VỚI HOẠT ĐỘNG CHO THUÊ TÀI SẢN", sT))
    elements.append(Paragraph(
        "(Áp dụng đối với cá nhân có hoạt động cho thuê tài sản trực tiếp khai thuế với cơ quan thuế "
        "trừ cá nhân trực tiếp ký hợp đồng thuê với tổ chức kinh tế; thay cho cá nhân)", sSm))
    elements.append(Spacer(1, 4))

    # Loại khai
    is_ds  = chk(theoPL_DS)
    is_thue= chk(theoPL_Thue)
    is_dau = "X" if loai == "C" else " "
    is_bs  = "X" if loai == "B" else " "

    elements.append(Paragraph(
        f"Cá nhân cho thuê tài sản trực tiếp khai thuế: Tổ chức, cá nhân khai thuế thay, nộp thuế thay "
        f"cho cá nhân ký quyền theo quy định của pháp luật dân sự(*): [<b>{is_ds}</b>]", sN))
    elements.append(Paragraph(
        f"Doanh nghiệp, tổ chức có tư cách pháp nhân khai thuế thay, nộp thuế thay cho cá nhân: [<b>{is_thue}</b>]", sN))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        f"[<b>{is_dau}</b>] Kỳ tính thuế: Từ ngày: <b>{kyTuNgay}</b>   Đến ngày: <b>{kyDenNgay}</b>", sN))
    elements.append(Paragraph(
        f"[<b>{is_bs}</b>] Lần đầu:   [<b>{'X' if soLan=='0' else ' '}</b>] Bổ sung lần thứ [<b>{soLan if soLan!='0' else ''}</b>]", sN))
    elements.append(Spacer(1, 6))

    # ── 3. THÔNG TIN NGƯỜI NỘP THUẾ ─────────────────────────────────
    info_rows = [
        [Paragraph("[04] Tên người nộp thuế:", sN), Paragraph(f"<b>{tenNNT}</b>", sN)],
        [Paragraph("[05] Mã số thuế:", sN),          Paragraph(f"<b>{mst}</b>", sN)],
        [Paragraph("[06] Địa chỉ:", sN),             Paragraph(f"<b>{dchi}</b>", sN)],
        [Paragraph("[07] Điện thoại:", sN),           Paragraph(f"<b>{dthoai}</b>   [08] Fax: <b>{fax}</b>   [09] Email: <b>{email}</b>", sN)],
    ]
    t_info = Table(info_rows, colWidths=[160, 355])
    t_info.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),2),
        ('BOTTOMPADDING',(0,0),(-1,-1),2),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 6))

    # ── 4. CÁC TRƯỜNG [10] → [22] — LUÔN VẼ, có dữ liệu thì điền ──
    def gs(tag_parent, tag_child):
        """Lấy text từ thẻ con, trả về '' nếu không có."""
        for p in root.iter():
            if strip_ns(p.tag) == tag_parent:
                for c in p:
                    if strip_ns(c.tag) == tag_child:
                        return (c.text or "").strip()
        return ""

    # Đọc tất cả giá trị (rỗng cũng giữ lại)
    ct10 = get(root, 'ct10')
    ct11 = get(root, 'ct11')

    ct12a_ngaySinh  = gs('CNKDChuaDangKyThue', 'ct12a_ngaySinh')
    ct12b_tenQuocTich= gs('CNKDChuaDangKyThue','ct12b_tenQuocTich')
    ct12c_so        = gs('CNKDChuaDangKyThue', 'ct12c_soCMND_CCCD')
    ct12c_ten       = gs('CNKDChuaDangKyThue', 'ct12c_ten')
    ct12c_ma        = gs('CNKDChuaDangKyThue', 'ct12c_ma')
    ct12c_ngayCap   = gs('CNKDChuaDangKyThue', 'ct12c_1_ngayCap')
    ct12c_noiCap    = gs('CNKDChuaDangKyThue', 'ct12c_2_noiCap_ten')

    ct12d_so        = gs('CNKDKhongCoCMND_CCCD','ct12d_soHoChieu')
    ct12d_ten       = gs('CNKDKhongCoCMND_CCCD','ct12d_ten')
    ct12d_ngayCap   = gs('CNKDKhongCoCMND_CCCD','ct12d_1_ngayCap')
    ct12d_noiCap    = gs('CNKDKhongCoCMND_CCCD','ct12d_2_noiCap_ten')

    ct12dd_so       = gs('CNKDKhongCoCMND_CCCD','ct12dd_soGiayThongHanh')
    ct12dd_ten      = gs('CNKDKhongCoCMND_CCCD','ct12dd_ten')

    ct12e_so        = gs('CNKDKhongCoCMND_CCCD','ct12e_soCMNDBienGioi')
    ct12e_ten       = gs('CNKDKhongCoCMND_CCCD','ct12e_ten')

    ct12f_so        = gs('CNKDKhongCoCMND_CCCD','ct12f_soGiayToKhac')
    ct12f_ten       = gs('CNKDKhongCoCMND_CCCD','ct12f_ten')

    ct12g_soNha     = gs('CT12g','ct12g_soNha')
    ct12g_phuong    = gs('CT12g','ct12g_tenPhuong')
    ct12g_quan      = gs('CT12g','ct12g_tenQuan')
    ct12g_tinh      = gs('CT12g','ct12g_tenTinh')

    ct12h_soNha     = gs('CT12h','ct12h_soNha')
    ct12h_phuong    = gs('CT12h','ct12h_tenPhuong')
    ct12h_quan      = gs('CT12h','ct12h_tenQuan')
    ct12h_tinh      = gs('CT12h','ct12h_tenTinh')

    ct12i_so        = gs('CT12i','ct12i_soGiayTo')
    ct12i_ngayCap   = gs('CT12i','ct12i_ngayCap')
    ct12i_coQuanCap = gs('CT12i','ct12i_coQuanCap')

    ct12k           = get(root, 'ct12k')
    maHDong         = get(root, 'maHDong')

    # [16-21] Lấy ĐÚNG từ khối ToChucNopThueThay (không dùng get() chung vì sẽ lấy nhầm từ Phục lục)
    ct16 = gs('ToChucNopThueThay', 'ct16')
    ct17 = gs('ToChucNopThueThay', 'ct17')
    ct18 = gs('ToChucNopThueThay', 'ct18')
    ct19 = gs('ToChucNopThueThay', 'ct19')
    ct20 = gs('ToChucNopThueThay', 'ct20')
    ct21 = gs('ToChucNopThueThay', 'ct21')

    dia_chi_g = ", ".join(filter(None, [ct12g_soNha, ct12g_phuong, ct12g_quan, ct12g_tinh]))
    dia_chi_h = ", ".join(filter(None, [ct12h_soNha, ct12h_phuong, ct12h_quan, ct12h_tinh]))

    # LUÔN VẼ TẤT CẢ — không dùng if kiểm tra dữ liệu
    ext_rows = [
        [Paragraph("[10] Số CMND (trường hợp hợp cá nhân khai thuế):", sN),
         Paragraph(f"<b>{ct10}</b>", sN)],

        [Paragraph("[11] Số CMND (kỳ khai trước không có CMND):", sN),
         Paragraph(f"<b>{ct11}</b>", sN)],

        # [12a] và [12b] dùng bảng 2 cột riêng để tão hoàng đàn
        [Paragraph("[12a] Ngày sinh:", sN),
         Table([[
             Paragraph(f"<b>{ct12a_ngaySinh}</b>", sN),
             Paragraph("[12b] Quốc tịch:", sN),
             Paragraph(f"<b>{ct12b_tenQuocTich}</b>", sN),
         ]], colWidths=[100, 90, 95],
         style=[('LEFTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0)])],

        [Paragraph("[12c] Số CMND/CCCD:", sN),
         Paragraph(f"<b>{ct12c_so}</b>    Tên: <b>{ct12c_ten}</b>    Mã: <b>{ct12c_ma}</b>", sN)],

        [Paragraph("[12c.1] Ngày cấp:", sN),
         Paragraph(f"<b>{ct12c_ngayCap}</b>    [12c.2] Nơi cấp: <b>{ct12c_noiCap}</b>", sN)],

        [Paragraph("[12d] Số hộ chiếu:", sN),
         Paragraph(f"<b>{ct12d_so}</b>    Tên: <b>{ct12d_ten}</b>", sN)],

        [Paragraph("[12d.1] Ngày cấp:", sN),
         Paragraph(f"<b>{ct12d_ngayCap}</b>    [12d.2] Nơi cấp: <b>{ct12d_noiCap}</b>", sN)],

        [Paragraph("[12dd] Số giấy thông hành:", sN),
         Paragraph(f"<b>{ct12dd_so}</b>    Tên: <b>{ct12dd_ten}</b>", sN)],

        [Paragraph("[12e] Số CMND biên giới:", sN),
         Paragraph(f"<b>{ct12e_so}</b>    Tên: <b>{ct12e_ten}</b>", sN)],

        [Paragraph("[12f] Số giấy tờ khác:", sN),
         Paragraph(f"<b>{ct12f_so}</b>    Tên: <b>{ct12f_ten}</b>", sN)],

        [Paragraph("[12g] Địa chỉ nơi cho thuê (số nhà/đường phố/phường-xã/quận-huyện/tỉnh-tp):", sN),
         Paragraph(f"<b>{dia_chi_g}</b>", sN)],

        [Paragraph("[12h] Địa chỉ đăng ký kinh doanh:", sN),
         Paragraph(f"<b>{dia_chi_h}</b>", sN)],

        [Paragraph("[12i] Số giấy tờ:", sN),
         Paragraph(f"<b>{ct12i_so}</b>    Ngày cấp: <b>{ct12i_ngayCap}</b>    Cơ quan: <b>{ct12i_coQuanCap}</b>", sN)],

        [Paragraph("[12k] Vốn kinh doanh (đồng):", sN),
         Paragraph(f"<b>{ct12k}</b>", sN)],

        [Paragraph("[16] Tổ chức nộp thuế:", sN),
         Paragraph(f"<b>{ct16}</b>    [17] Mã số: <b>{ct17}</b>", sN)],

        [Paragraph("[18] Địa chỉ:", sN),
         Paragraph(f"<b>{ct18}</b>", sN)],

        [Paragraph("[19] Mã số thuế:", sN),
         Paragraph(f"<b>{ct19}</b>    [20] Fax: <b>{ct20}</b>    [21] Email: <b>{ct21}</b>", sN)],

        [Paragraph("[22] Mã hợp đồng:", sN),
         Paragraph(f"<b>{maHDong}</b>", sN)],
    ]

    t_ext = Table(ext_rows, colWidths=[230, 285])
    t_ext.setStyle(TableStyle([
        ('VALIGN',         (0,0),(-1,-1),'TOP'),
        ('TOPPADDING',     (0,0),(-1,-1), 2),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 2),
        ('LINEBELOW',      (0,-1),(-1,-1), 0.3, colors.lightgrey),
    ]))
    elements.append(t_ext)
    elements.append(Spacer(1, 8))

    # ── 5. PHẦN A: BẢNG SỐ LIỆU ─────────────────────────────────────
    elements.append(Paragraph("<b>A. PHẦN CÁ NHÂN KÊ KHAI NGHĨA VỤ THUẾ</b>", sB))
    elements.append(Spacer(1, 3))

    unit_t = Table([[Paragraph("Đơn vị tính: Đồng Việt Nam", sSm)]], colWidths=[W])
    unit_t.setStyle(TableStyle([('ALIGN',(0,0),(0,0),'RIGHT')]))
    elements.append(unit_t)

    col_w = [30, 295, 80, 110]
    tax_hdr = [
        Paragraph("<b>STT</b>", sBsmc),
        Paragraph("<b>Chỉ tiêu</b>", sBsmc),
        Paragraph("<b>Mã chỉ tiêu</b>", sBsmc),
        Paragraph("<b>Số tiền</b>", sBsmc),
    ]
    tax_body = [
        ["1", "Tổng doanh thu phát sinh trong kỳ",    "[23]", ct23 or "0"],
        ["2", "Tổng doanh thu tính thuế",              "[24]", ct24 or "0"],
        ["3", "Tổng số thuế GTGT phải nộp",            "[25]", ct25 or "0"],
        ["4", "Tổng số phát sinh trong kỳ",            "[26]", ct26 or "0"],
        ["5", "Tiền phạt, bồi thường mua bởi cho thuê nhận được theo thỏa thuận tại hợp đồng (nếu có)", "[27]", ct27 or "0"],
        ["6", "Tổng số thuế TNCN phải nộp tính nhằm bồi thường, phạt vi phạm hợp đồng (nếu có)",       "[28]", ct28 or "0"],
    ]
    rows = [tax_hdr] + [
        [Paragraph(r[0], sNc),
         Paragraph(r[1], sSm),
         Paragraph(r[2], sNc),
         Paragraph(fmt_num(r[3]), sSmr)]
        for r in tax_body
    ]
    t_tax = Table(rows, colWidths=col_w, repeatRows=1, splitByRow=0)
    t_tax.setStyle(TableStyle([
        ('GRID',        (0,0),(-1,-1), 0.5, colors.black),
        ('BACKGROUND',  (0,0),(-1,0),  colors.lightgrey),
        ('VALIGN',      (0,0),(-1,-1), 'MIDDLE'),
        ('ALIGN',       (0,0),(0,-1),  'CENTER'),
        ('ALIGN',       (2,0),(2,-1),  'CENTER'),
        ('ALIGN',       (3,0),(3,-1),  'RIGHT'),
        ('TOPPADDING',  (0,0),(-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING', (0,0),(-1,-1), 4),
        ('RIGHTPADDING',(0,0),(-1,-1), 4),
    ]))
    elements.append(t_tax)

    # Dòng tổng [29] — keep với bảng phía trên
    t_total = Table([[
        Paragraph("7", sNc),
        Paragraph("Tổng số thuế TNCN phải nộp [29]=[26]+[28]", sSm),
        Paragraph("[29]", sNc),
        Paragraph(f"<b>{ct29 or '0'}</b>", sSmr)
    ]], colWidths=col_w, splitByRow=0)
    t_total.setStyle(TableStyle([
        ('GRID',  (0,0),(-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0),(0,-1),  'CENTER'),
        ('ALIGN', (2,0),(2,-1),  'CENTER'),
        ('ALIGN', (3,0),(3,-1),  'RIGHT'),
        ('VALIGN',(0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1), 4),
    ]))
    elements.append(t_total)
    elements.append(Spacer(1, 3))
    elements.append(Paragraph("<i>(TNCN: Thu nhập cá nhân; GTGT: Giá trị gia tăng)</i>", sSm))

    # ── 6. CAM KẾT + KÝ TÊN ─────────────────────────────────────────
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Tôi cam đoan số liệu khai trên là đúng và chịu trách nhiệm trước pháp luật về số liệu đã khai...", sN))
    elements.append(Spacer(1, 8))
    now = datetime.datetime.now()
    elements.append(Paragraph(
        f"Ngày {now.day:02d} tháng {now.month:02d} năm {now.year}", sNr))
    elements.append(Spacer(1, 5))
    sig = Table([[
        Paragraph("<b>NHÂN VIÊN ĐẠI LÝ THUẾ</b>", sBc),
        Paragraph("<b>NGƯỜI NỘP THUẾ hoặc<br/>ĐẠI DIỆN HỢP PHÁP CỦA NGƯỜI NỘP THUẾ</b>", sBc)
    ],[
        Paragraph("Họ và tên:", sN),
        Paragraph("(Ký, ghi rõ họ tên, đóng dấu (nếu có))", sSm)
    ],[
        Paragraph("Chứng chỉ hành nghề số:", sN), ""
    ]], colWidths=[257, 258])
    sig.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),3),
    ]))
    elements.append(sig)

    # ── 7. PHỤ LỤC 01/BK-TTS (Trang 2+) ──────────────────────────
    hop_dong_list = get_all(root, 'CTietBKeHDongTTS')
    if hop_dong_list:
        elements.append(PageBreak())
        elements.append(Paragraph("<b>PHỤ LỤC BẢNG KÊ CHI TIẾT HỢP ĐỒNG CHO THUÊ TÀI SẢN</b>", sBc))
        elements.append(Paragraph("(Kèm theo tờ khai 01/TTS)", sNc))
        elements.append(Spacer(1, 8))

        pluc_col_w = [25,40,50,130,70,45,45,50,50,55]
        pluc_hdr = [
            Paragraph("<b>STT</b>", sBsmc),
            Paragraph("<b>Loại hợp đồng</b>", sBsmc),
            Paragraph("<b>Bên thuê<br/>(MST)</b>", sBsmc),
            Paragraph("<b>Tên bên thuê</b>", sBsmc),
            Paragraph("<b>Số hợp đồng</b>", sBsmc),
            Paragraph("<b>Ngày bắt đầu</b>", sBsmc),
            Paragraph("<b>Ngày kết thúc</b>", sBsmc),
            Paragraph("<b>Giá thuê/tháng</b>", sBsmc),
            Paragraph("<b>Doanh thu tính thuế</b>", sBsmc),
            Paragraph("<b>Thuế TNCN phải nộp</b>", sBsmc),
        ]

        pluc_data = [pluc_hdr]
        for hd in hop_dong_list:
            def gv(t):
                for c in hd:
                    if strip_ns(c.tag) == t:
                        return (c.text or "").strip()
                return ""
            pluc_data.append([
                Paragraph(gv('ct06')         or "", sSm),
                Paragraph(gv('ct06a_ten')    or "", sSm),
                Paragraph(gv('ct08')         or "", sSm),
                Paragraph(gv('ct07')         or "", sSm),
                Paragraph(gv('ct11')         or "", sSm),
                Paragraph(gv('ct17')         or "", sSm),
                Paragraph(gv('ct18')         or "", sSm),
                Paragraph(fmt_num(gv('ct19')) or "0", sSm),
                Paragraph(fmt_num(gv('ct24')) or "0", sSm),
                Paragraph(fmt_num(gv('ct26')) or "0", sSm),
            ])

        t_pluc = Table(pluc_data, colWidths=pluc_col_w, repeatRows=1)
        t_pluc.setStyle(TableStyle([
            ('GRID',       (0,0),(-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0),(-1,0),  colors.lightgrey),
            ('VALIGN',     (0,0),(-1,-1), 'TOP'),
            ('ALIGN',      (0,0),(0,-1),  'CENTER'),
            ('TOPPADDING', (0,0),(-1,-1), 3),
            ('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('FONTSIZE',   (0,0),(-1,-1), 7),
        ]))
        elements.append(t_pluc)

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
            if not isinstance(result[tag], list):
                result[tag] = [result[tag]]
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
        mst, ten_tk, ma_tk, ky = "Unknown", "TỜ KHAI THUẾ", "", "Unknown"
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
    ma_tk = meta.get("form", "")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=30,   bottomMargin=30)

    font_ok = register_fonts()
    fn = 'VN'  if font_ok else 'Helvetica'
    fb = 'VNB' if font_ok else 'Helvetica-Bold'

    elements = []
    if ma_tk == "470":
        render_01TTS(root, elements, fn, fb)
    else:
        render_generic(root, elements, fn, fb)

    doc.build(elements)
    buffer.seek(0)
    return buffer
