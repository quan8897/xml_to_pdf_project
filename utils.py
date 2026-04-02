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
# CONSTANTS & HELPERS
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
    if not s or s.lower() in ('none','false','true'): return ""
    try:
        f = float(s.replace(',', '.'))
        if f == int(f): return "{:,}".format(int(f)).replace(',', '.')
        return "{:,.2f}".format(f).replace(',', '.')
    except: return s

def fnd(root, *parts):
    ns_path = '/'.join(f'{{{XMLNS}}}{p}' for p in parts)
    e = root.find(f'.//{ns_path}')
    if e is not None: return (e.text or "").strip()
    fallback = parts[-1]
    for e in root.iter():
        if strip_ns(e.tag) == fallback: return (e.text or "").strip()
    return ""

def fnd_p(root, p_tag, c_tag):
    for p in root.iter():
        if strip_ns(p.tag) == p_tag:
            for c in p:
                if strip_ns(c.tag) == c_tag: return (c.text or "").strip()
    return ""

def register_fonts():
    paths = [(r"C:\Windows\Fonts\times.ttf", r"C:\Windows\Fonts\timesbd.ttf", r"C:\Windows\Fonts\timesi.ttf"),
             ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf")]
    for r, b, i in paths:
        if os.path.exists(r):
            try:
                pdfmetrics.registerFont(TTFont('T', r))
                pdfmetrics.registerFont(TTFont('TB', b if os.path.exists(b) else r))
                pdfmetrics.registerFont(TTFont('TI', i if os.path.exists(i) else r))
                return True
            except: continue
    return False

class NumberedCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        n = len(self._saved_page_states)
        for s in self._saved_page_states:
            self.__dict__.update(s)
            self.setFont("T", 8)
            self.drawRightString(A4[0]-40, 20, f"{self._pageNumber}/{n}")
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

# ─────────────────────────────────────────────
# RENDERER
# ─────────────────────────────────────────────
def render_01TTS(root, elements, fn, fb, fi):
    def N(name, **kw): return ParagraphStyle(name, fontName=fn, **kw)
    def B(name, **kw): return ParagraphStyle(name, fontName=fb, **kw)
    def I(name, **kw): return ParagraphStyle(name, fontName=fi, **kw)

    s7c = N('s7c', fontSize=7, leading=9, alignment=1)
    s8  = N('s8', fontSize=8, leading=10)
    s8c = N('s8c', fontSize=8, leading=10, alignment=1)
    s8r = N('s8r', fontSize=8, leading=10, alignment=2)
    s8bc = B('s8bc', fontSize=8, leading=10, alignment=1)
    s9  = N('s9', fontSize=9, leading=11)
    s9b = B('s9b', fontSize=9, leading=11)
    s9bc = B('s9bc', fontSize=9, leading=12, alignment=1)
    s11bc = B('s11bc', fontSize=11, leading=14, alignment=1)

    def clean(v): return '' if not v or str(v).lower() in ('false','true','0','none') else str(v).strip()
    def sp(h=2): return Spacer(1, h)

    # XML DATA
    tenNNT = fnd(root,'NNT','tenNNT')
    mst = fnd(root,'NNT','mst')
    dchi = fnd(root,'NNT','dchiNNT')
    dthoai = fnd(root,'NNT','dthoaiNNT')
    fax = fnd(root,'NNT','faxNNT')
    email = fnd(root,'NNT','emailNNT')
    kyTu = fnd(root,'TKhaiThue','KyKKhaiThue','kyKKhaiTuNgay')
    kyDen = fnd(root,'TKhaiThue','KyKKhaiThue','kyKKhaiDenNgay')
    loai = fnd(root,'TKhaiThue','loaiTKhai')
    soLan = fnd(root,'TKhaiThue','soLan')
    
    ct23 = fmt_num(fnd(root,'CaNhanKeKhai','ct23'))
    ct24 = fmt_num(fnd(root,'CaNhanKeKhai','ct24'))
    ct25 = fmt_num(fnd(root,'CaNhanKeKhai','ct25'))
    ct26 = fmt_num(fnd(root,'CaNhanKeKhai','ct26'))
    ct27 = fmt_num(fnd(root,'CaNhanKeKhai','ct27'))
    ct28 = fmt_num(fnd(root,'CaNhanKeKhai','ct28'))
    ct29 = fmt_num(fnd(root,'CaNhanKeKhai','ct29'))

    # HEADER
    h_data = [[
        Paragraph("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>Độc lập-Tự do-Hạnh phúc<br/>─────────────────────", s9bc),
        Table([[Paragraph("<b>Mẫu số: 01/TTS</b>", s8bc)],
               [Paragraph("(Ban hành kèm theo Thông tư số 40/2021/TT-BTC ngày 01/6/2021 của Bộ trưởng Bộ Tài Chính)", s7c)]],
              colWidths=[150], style=[('BOX',(0,0),(-1,-1),0.5,colors.black),('TOPPADDING',(0,0),(-1,-1),2),('LEFTPADDING',(0,0),(-1,-1),2)])
    ]]
    elements.append(Table(h_data, colWidths=[365, 150])); elements.append(sp(4))

    elements.append(Paragraph('<b>TỜ KHAI ĐỐI VỚI HOẠT ĐỘNG CHO THUÊ TÀI SẢN(TT40/2021)</b>', s11bc))
    elements.append(Paragraph('(Áp dụng đối với cá nhân có hoạt động cho thuê tài sản trực tiếp khai thuế với cơ quan thuế và tổ chức khai thay cho cá nhân)', s8c))
    elements.append(sp(4))

    is_ds = "[x]" if clean(fnd(root,'Header','khaiTheoPLuatDanSu')) else "[ ]"
    is_th = "[x]" if clean(fnd(root,'Header','khaiTheoPLuatThue')) else "[ ]"
    elements.append(Paragraph(f"{is_ds} Cá nhân cho thuê tài sản trực tiếp khai thuế/ Tổ chức, cá nhân khai thuế thay, nộp thuế thay cho cá nhân ủy quyền theo quy định của pháp luật dân sự", s9))
    elements.append(Paragraph(f"{is_th} Doanh nghiệp, tổ chức kinh tế khai thuế thay, nộp thuế thay theo pháp luật thuế", s9))
    elements.append(sp(2))

    elements.append(Paragraph(f"<b>[01] Kỳ tính thuế:</b> Kỳ thanh toán: Từ ngày: {kyTu or '...'}   Đến ngày: {kyDen or '...'}", s9))
    elements.append(Paragraph(f"<b>[02] Lần đầu:</b> [{'x' if loai=='C' else ' '}]    <b>[03] Bổ sung lần thứ:</b> [ {soLan if soLan and soLan!='0' else ''} ]", s9))
    elements.append(sp(3))

    def rowplain(c, l, v): return Paragraph(f"<b>[{c}] {l}</b> {v}", s9)

    elements.append(rowplain('04', 'Tên người nộp thuế:', tenNNT.upper()))
    elements.append(rowplain('05', 'Mã số thuế:', mst))
    elements.append(rowplain('06', 'Địa chỉ liên hệ:', dchi))
    elements.append(Paragraph(f"<b>[07] Điện thoại:</b> {dthoai}   <b>[08] Fax:</b> {fax}   <b>[09] E-mail:</b> {email}", s9))
    elements.append(rowplain('10', 'Số CMND (trường hợp cá nhân quốc tịch Việt Nam):', clean(fnd(root,'Header','ct10'))))
    elements.append(rowplain('11', 'Hộ chiếu (trường hợp cá nhân không có quốc tịch Việt Nam):', clean(fnd(root,'Header','ct11'))))
    
    elements.append(Paragraph("<b>[12] Trường hợp cá nhân kinh doanh chưa đăng ký thuế thì khai thêm các thông tin sau:</b>", s9))
    elements.append(Paragraph(f"<b>[12a] Ngày sinh:</b> {fnd_p(root,'CNKDChuaDangKyThue','ct12a_ngaySinh')}   <b>[12b] Quốc tịch:</b> {fnd_p(root,'CNKDChuaDangKyThue','ct12b_tenQuocTich')}", s9))
    elements.append(Paragraph(f"<b>[12c] Số CMND/CCCD:</b> {fnd_p(root,'CNKDChuaDangKyThue','ct12c_soCMND_CCCD')}  <b>[12c.1] Ngày cấp:</b> {fnd_p(root,'CNKDChuaDangKyThue','ct12c_1_ngayCap')}  <b>[12c.2] Nơi cấp:</b> {fnd_p(root,'CNKDChuaDangKyThue','ct12c_2_noiCap_ten')}", s9))
    
    # 12 sub-fields detail
    elements.append(Paragraph("Trường hợp cá nhân kinh doanh thuộc đối tượng không có CMND/CCCD tại Việt Nam thì kê khai thông tin tại một trong các thông tin sau:", s8))
    elements.append(Paragraph(f"<b>[12d] Số hộ chiếu:</b> {fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12d_soHoChieu')}  <b>[12d.1] Ngày cấp:</b> {fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12d_1_ngayCap')}  <b>[12d.2] Nơi cấp:</b> {fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12d_2_noiCap_ten')}", s9))
    elements.append(rowplain('12đ', 'Số giấy thông hành (đối với thương nhân nước ngoài):', fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12dd_soGiayThongHanh')))
    elements.append(Paragraph(f"<b>[12đ.1] Ngày cấp:</b> {fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12dd_1_ngayCap')}  <b>[12đ.2] Nơi cấp:</b> {fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12dd_2_noiCap_ten')}", s9))
    elements.append(rowplain('12e', 'Số CMND biên giới (đối với thương nhân nước ngoài):', fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12e_soCMNDBienGioi')))
    elements.append(Paragraph(f"<b>[12e.1] Ngày cấp:</b> {fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12e_1_ngayCap')}  <b>[12e.2] Nơi cấp:</b> {fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12e_2_noiCap_ten')}", s9))
    elements.append(rowplain('12f', 'Số Giấy tờ chứng thực cá nhân khác:', fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12f_soGiayToKhac')))
    elements.append(Paragraph(f"<b>[12f.1] Ngày cấp:</b> {fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12f_1_ngayCap')}  <b>[12f.2] Nơi cấp:</b> {fnd_p(root,'CNKDKhongCoCMND_CCCD','ct12f_2_noiCap_ten')}", s9))
    
    elements.append(Paragraph("<b>[12g] Nơi đăng ký thường trú:</b>", s9))
    elements.append(rowplain('12g.1', 'Số nhà, đường phố/xóm/ấp/thôn:', fnd_p(root,'CT12g','ct12g_soNha')))
    elements.append(rowplain('12g.2', 'Phường/Xã/Thị trấn:', fnd_p(root,'CT12g','ct12g_tenPhuong')))
    elements.append(rowplain('12g.3', 'Quận/Huyện/Thị xã/Thành phố thuộc tỉnh:', fnd_p(root,'CT12g','ct12g_tenQuan')))
    elements.append(rowplain('12g.4', 'Tỉnh/ Thành phố:', fnd_p(root,'CT12g','ct12g_tenTinh')))
    
    elements.append(Paragraph("<b>[12h] Chỗ ở hiện tại:</b>", s9))
    elements.append(rowplain('12h.1', 'Số nhà, đường phố/xóm/ấp/thôn:', fnd_p(root,'CT12h','ct12h_soNha')))
    elements.append(rowplain('12h.2', 'Phường/Xã/Thị trấn:', fnd_p(root,'CT12h','ct12h_tenPhuong')))
    elements.append(rowplain('12h.3', 'Quận/Huyện/Thị xã/Thành phố thuộc tỉnh:', fnd_p(root,'CT12h','ct12h_tenQuan')))
    elements.append(rowplain('12h.4', 'Tỉnh/Thành phố:', fnd_p(root,'CT12h','ct12h_tenTinh')))
    
    elements.append(Paragraph(f"<b>[12i] Giấy chứng nhận đăng ký hộ kinh doanh (nếu có): Số:</b> {fnd_p(root,'CT12i','ct12i_soGiayTo')}", s9))
    elements.append(Paragraph(f"<b>[12i.1] Ngày cấp:</b> {fnd_p(root,'CT12i','ct12i_ngayCap')}  <b>[12i.2] Cơ quan cấp:</b> {fnd_p(root,'CT12i','ct12i_coQuanCap')}", s9))
    _vun = fmt_num(fnd(root,'Header','ct12k'))
    elements.append(rowplain('12k', 'Vốn kinh doanh (đồng):', _vun if _vun and _vun!='0' else '0'))
    
    elements.append(rowplain('13', 'Tên đại lý thuế (nếu có):', ''))
    elements.append(rowplain('14', 'Mã số thuế:', ''))
    elements.append(rowplain('15', 'Hợp đồng đại lý thuế: Số:', ''))
    elements.append(rowplain('16', 'Tổ chức nộp thuế thay (nếu có):', clean(fnd(root,'ToChucNopThueThay','ct16'))))
    elements.append(rowplain('17', 'Mã số thuế:', clean(fnd(root,'ToChucNopThueThay','ct17'))))
    elements.append(rowplain('18', 'Địa chỉ:', clean(fnd(root,'ToChucNopThueThay','ct18'))))
    elements.append(Paragraph(f"<b>[19] Điện thoại:</b> {fnd(root,'ToChucNopThueThay','ct19')}  <b>[20] Fax:</b> {fnd(root,'ToChucNopThueThay','ct20')}  <b>[21] Email:</b> {fnd(root,'ToChucNopThueThay','ct21')}", s9))
    elements.append(rowplain('22', 'Văn bản ủy quyền (nếu có): Số: ngày tháng năm', fnd(root,'Header','maHDong')))
    elements.append(sp(5))

    # TABLE
    elements.append(Paragraph("<b>A. PHẦN CÁ NHÂN KÊ KHAI NGHĨA VỤ THUẾ</b>", s9b))
    elements.append(Table([[Paragraph("<i>Đơn vị tiền: Đồng Việt Nam</i>", s8r)]], colWidths=[W]))
    h = [Paragraph(f"<b>{t}</b>", s8bc) for t in ["STT", "Chỉ tiêu", "Mã chỉ tiêu", "Số tiền"]]
    tdata = [h]
    body = [("1","Tổng doanh thu phát sinh trong kỳ","[23]",ct23),
            ("2","Tổng doanh thu tính thuế","[24]",ct24),
            ("3","Tổng số thuế GTGT phải nộp","[25]",ct25),
            ("4","Tổng số thuế TNCN phải nộp phát sinh trong kỳ","[26]",ct26),
            ("5","Tiền phạt, bồi thường mà bên cho thuê nhận được theo thoả thuận tại hợp đồng (nếu có)","[27]",ct27),
            ("6","Tổng số thuế TNCN phải nộp từ tiền nhận bồi thường, phạt vi phạm hợp đồng (nếu có)","[28]",ct28),
            ("7","Tổng số thuế TNCN phải nộp [29]=[26]+[28]","[29]",ct29)]
    for r in body:
        tdata.append([Paragraph(r[0],s8c), Paragraph(r[1],s8), Paragraph(r[2],s8c), Paragraph(f"<b>{r[3] or '0'}</b>",s8r)])
    
    tbl = Table(tdata, colWidths=[30, 290, 80, 115])
    tbl.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.black),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('BACKGROUND',(0,0),(-1,0),colors.whitesmoke)]))
    elements.append(tbl); elements.append(sp(2))
    elements.append(Paragraph("<i>(TNCN: Thu nhập cá nhân; GTGT: Giá trị gia tăng)</i>", s8))
    elements.append(sp(4))
    elements.append(Paragraph("Tôi cam đoan số liệu khai trên là đúng và chịu trách nhiệm trước pháp luật về số liệu đã khai./...", s9))
    
    # SIGNATURE
    now = datetime.datetime.now()
    elements.append(sp(6))
    elements.append(Table([[Paragraph("", s9), Paragraph(f"<i>Ngày {now.day:02d} tháng {now.month:02d} năm {now.year}</i>", s9bc)]], colWidths=[250, 265], style=[('ALIGN',(1,0),(1,0),'CENTER')]))
    sig = Table([
        [Paragraph("<b>NHÂN VIÊN ĐẠI LÝ THUẾ</b>", s9), Paragraph("<b>NGƯỜI NỘP THUẾ hoặc</b>", s9bc)],
        [Paragraph("Họ và tên:", s9), Paragraph("<b>ĐẠI DIỆN HỢP PHÁP CỦA NGƯỜI NỘP THUẾ</b>", s9bc)],
        [Paragraph("Chứng chỉ hành nghề số:", s9), Paragraph("<i>(Chữ ký, ghi rõ họ tên; chức vụ và đóng dấu (nếu có)/Ký điện tử)</i>", s8c)],
        [Paragraph("", s9), Paragraph("", s9)],
        [Paragraph("---", s9), Paragraph("", s9)],
    ], colWidths=[240, 275])
    elements.append(sig)

def extract_tax_metadata(xml_content):
    try:
        root = ET.fromstring(pre_process_xml(xml_content))
        return {"name": fnd(root,'TKhaiThue','tenTKhai'), "mst": fnd(root,'NNT','mst'), "period": fnd(root,'TKhaiThue','KyKKhaiThue','kyKKhaiTuNgay')}
    except: return {"name":"TỜ KHAI","mst":"","period":""}

def generate_tax_pdf(xml_content, title="BÁO CÁO THUẾ"):
    register_fonts(); fn, fb, fi = 'T', 'TB', 'TI'
    root = ET.fromstring(pre_process_xml(xml_content))
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    render_01TTS(root, elements, fn, fb, fi)
    doc.build(elements, canvasmaker=NumberedCanvas)
    buf.seek(0); return buf
