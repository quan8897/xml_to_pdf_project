"""
utils_word.py — Engine XML → Word (docxtpl) → PDF (LibreOffice)
Thay thế hoàn toàn utils.py với độ chính xác 100% theo mẫu 01/TTS gốc.
"""
import os
import io
import re
import datetime
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from docxtpl import DocxTemplate

# ─────────────────────────────────────────────
# CONSTANTS & HELPERS
# ─────────────────────────────────────────────
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'mau-01-tts-template.docx')

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
    if not value: return ""
    s = str(value).strip()
    try:
        f = float(s.replace(',', '.'))
        if f == int(f):
            return "{:,}".format(int(f)).replace(',', '.')
        return "{:,.2f}".format(f)
    except:
        return s

def fnd(root, *path_parts):
    """Tìm text theo đường dẫn tag, hỗ trợ namespace."""
    XMLNS = 'http://kekhaithue.gdt.gov.vn/TKhaiThue'
    # Thử với namespace
    ns_path = '/'.join(f'{{{XMLNS}}}{p}' for p in path_parts)
    elem = root.find(f'.//{ns_path}')
    if elem is not None and elem.text and elem.text.strip():
        return elem.text.strip()
    # Fallback: tìm không namespace
    for tag in reversed(path_parts):
        for e in root.iter():
            if strip_ns(e.tag) == tag and e.text and e.text.strip():
                return e.text.strip()
    return ""

def fnd_parent(root, parent_tag, child_tag):
    """Lấy text từ thẻ con của thẻ cha cụ thể."""
    for p in root.iter():
        if strip_ns(p.tag) == parent_tag:
            for c in p:
                if strip_ns(c.tag) == child_tag:
                    return (c.text or "").strip()
    return ""

def chk_box(condition):
    """Trả về ký hiệu checkbox cho Word."""
    return "☑" if condition else "☐"

# ─────────────────────────────────────────────
# PARSE XML → CONTEXT DICT
# ─────────────────────────────────────────────
def parse_xml_to_context(xml_content):
    """Parse XML tờ khai thành dict để điền vào template Word."""
    clean  = pre_process_xml(xml_content)
    root   = ET.fromstring(clean)

    # Thông tin chung
    loai     = fnd(root, 'loaiTKhai')
    soLan    = fnd(root, 'soLan')
    kyTuNgay = fnd(root, 'kyKKhaiTuNgay')
    kyDenNgay= fnd(root, 'kyKKhaiDenNgay')
    mst      = fnd(root, 'mst')
    tenNNT   = fnd(root, 'tenNNT')
    dchi     = fnd(root, 'dchiNNT')
    dthoai   = fnd(root, 'dthoaiNNT')
    fax_val  = fnd(root, 'faxNNT')
    email    = fnd(root, 'emailNNT')

    theoPL_DS   = fnd(root, 'khaiTheoPLuatDanSu')
    theoPL_Thue = fnd(root, 'khaiTheoPLuatThue')

    # Header
    ct10 = fnd(root, 'ct10')
    ct11 = fnd(root, 'ct11')

    ct12a = fnd_parent(root, 'CNKDChuaDangKyThue', 'ct12a_ngaySinh')
    ct12b = fnd_parent(root, 'CNKDChuaDangKyThue', 'ct12b_tenQuocTich')
    ct12c_so   = fnd_parent(root, 'CNKDChuaDangKyThue', 'ct12c_soCMND_CCCD')
    ct12c_ngay = fnd_parent(root, 'CNKDChuaDangKyThue', 'ct12c_1_ngayCap')
    ct12c_noi  = fnd_parent(root, 'CNKDChuaDangKyThue', 'ct12c_2_noiCap_ten')

    ct12d_so   = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12d_soHoChieu')
    ct12d_ngay = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12d_1_ngayCap')
    ct12d_noi  = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12d_2_noiCap_ten')
    ct12dd_so  = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12dd_soGiayThongHanh')
    ct12dd_ngay= fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12dd_1_ngayCap')
    ct12dd_noi = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12dd_2_noiCap_ten')
    ct12e_so   = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12e_soCMNDBienGioi')
    ct12e_ngay = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12e_1_ngayCap')
    ct12e_noi  = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12e_2_noiCap_ten')
    ct12f_so   = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12f_soGiayToKhac')
    ct12f_ngay = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12f_1_ngayCap')
    ct12f_noi  = fnd_parent(root, 'CNKDKhongCoCMND_CCCD', 'ct12f_2_noiCap_ten')

    ct12g_1 = fnd_parent(root, 'CT12g', 'ct12g_soNha')
    ct12g_2 = fnd_parent(root, 'CT12g', 'ct12g_tenPhuong')
    ct12g_3 = fnd_parent(root, 'CT12g', 'ct12g_tenQuan')
    ct12g_4 = fnd_parent(root, 'CT12g', 'ct12g_tenTinh')

    ct12h_1 = fnd_parent(root, 'CT12h', 'ct12h_soNha')
    ct12h_2 = fnd_parent(root, 'CT12h', 'ct12h_tenPhuong')
    ct12h_3 = fnd_parent(root, 'CT12h', 'ct12h_tenQuan')
    ct12h_4 = fnd_parent(root, 'CT12h', 'ct12h_tenTinh')
    ct12h   = " ".join(filter(None, [ct12h_1, ct12h_2, ct12h_3, ct12h_4]))

    ct12i_so   = fnd_parent(root, 'CT12i', 'ct12i_soGiayTo')
    ct12i_ngay = fnd_parent(root, 'CT12i', 'ct12i_ngayCap')
    ct12i_cq   = fnd_parent(root, 'CT12i', 'ct12i_coQuanCap')
    ct12k      = fnd(root, 'ct12k')

    # [16-22] từ ToChucNopThueThay
    tc16 = fnd_parent(root, 'ToChucNopThueThay', 'ct16')
    tc17 = fnd_parent(root, 'ToChucNopThueThay', 'ct17')
    tc18 = fnd_parent(root, 'ToChucNopThueThay', 'ct18')
    tc19 = fnd_parent(root, 'ToChucNopThueThay', 'ct19')
    tc20 = fnd_parent(root, 'ToChucNopThueThay', 'ct20')
    tc21 = fnd_parent(root, 'ToChucNopThueThay', 'ct21')
    ct22_so = fnd(root, 'maHDong')

    # Số liệu tính thuế — chỉ lấy từ CaNhanKeKhai
    ct23 = fmt_num(fnd_parent(root, 'CaNhanKeKhai', 'ct23'))
    ct24 = fmt_num(fnd_parent(root, 'CaNhanKeKhai', 'ct24'))
    ct25 = fmt_num(fnd_parent(root, 'CaNhanKeKhai', 'ct25'))
    ct26 = fmt_num(fnd_parent(root, 'CaNhanKeKhai', 'ct26'))
    ct27 = fmt_num(fnd_parent(root, 'CaNhanKeKhai', 'ct27'))
    ct28 = fmt_num(fnd_parent(root, 'CaNhanKeKhai', 'ct28'))
    ct29 = fmt_num(fnd_parent(root, 'CaNhanKeKhai', 'ct29'))

    now = datetime.datetime.now()
    ngay_ky = f"{now.day:02d} tháng {now.month:02d} năm {now.year}"

    # Kỳ tính thuế
    ky_thang = ky_tu_ngay_parsed = ""
    ky_nam = ""
    if kyTuNgay:
        parts = kyTuNgay.replace('/', '-').split('-')
        if len(parts) >= 3:
            ky_nam = parts[0] if len(parts[0]) == 4 else parts[2]
            ky_thang = parts[1] if len(parts[1]) <= 2 else ""

    ctx = {
        # Checkbox loại khai
        'chk_ds':    chk_box(theoPL_DS.lower() == 'true' if theoPL_DS else False),
        'chk_thue':  chk_box(theoPL_Thue.lower() == 'true' if theoPL_Thue else False),

        # [01] Kỳ tính thuế
        'ky_nam':      ky_nam,
        'ky_tu_ngay':  kyTuNgay,
        'ky_den_ngay': kyDenNgay,
        'ky_thang':    ky_thang,
        'ky_quy':      "",  # có thể thêm logic tính quý

        # [02][03]
        'chk_lan_dau': chk_box(loai == 'C'),
        'chk_bo_sung': chk_box(loai == 'B'),
        'so_lan':       soLan if soLan and soLan != '0' else "",

        # [04]-[09]
        'ten_nnt': tenNNT,
        'mst':     mst,
        'dchi':    dchi,
        'dthoai':  dthoai,
        'fax':     fax_val,
        'email':   email,

        # [10][11]
        'ct10': ct10,
        'ct11': ct11,

        # [12]
        'ct12a': ct12a, 'ct12b': ct12b,
        'ct12c_so': ct12c_so, 'ct12c_ngay': ct12c_ngay, 'ct12c_noi': ct12c_noi,
        'ct12d_so': ct12d_so, 'ct12d_ngay': ct12d_ngay, 'ct12d_noi': ct12d_noi,
        'ct12dd_so': ct12dd_so, 'ct12dd_ngay': ct12dd_ngay, 'ct12dd_noi': ct12dd_noi,
        'ct12e_so': ct12e_so, 'ct12e_ngay': ct12e_ngay, 'ct12e_noi': ct12e_noi,
        'ct12f_so': ct12f_so, 'ct12f_ngay': ct12f_ngay, 'ct12f_noi': ct12f_noi,
        'ct12g_1': ct12g_1, 'ct12g_2': ct12g_2, 'ct12g_3': ct12g_3, 'ct12g_4': ct12g_4,
        'ct12h': ct12h,
        'ct12h_1': ct12h_1, 'ct12h_2': ct12h_2, 'ct12h_3': ct12h_3, 'ct12h_4': ct12h_4,
        'ct12i_so': ct12i_so, 'ct12i_ngay': ct12i_ngay, 'ct12i_cq': ct12i_cq,
        'ct12k': ct12k,

        # [13][14][15] đại lý (thường không có trong XML cá nhân)
        'ct13': "", 'ct15_so': "", 'ct15_ngay': "",

        # [16-22]
        'tc16': tc16, 'tc17': tc17, 'tc18': tc18,
        'tc19': tc19, 'tc20': tc20, 'tc21': tc21,
        'ct22_so': ct22_so, 'ct22_ngay': "",

        # Số liệu [23]-[29]
        'ct23': ct23 or "0", 'ct24': ct24 or "0", 'ct25': ct25 or "0",
        'ct26': ct26 or "0", 'ct27': ct27 or "0", 'ct28': ct28 or "0",
        'ct29': ct29 or "0",

        'ngay_ky': ngay_ky,
    }
    return ctx, root

# ─────────────────────────────────────────────
# CONVERT DOCX → PDF
# ─────────────────────────────────────────────
def docx_to_pdf_bytes(docx_path):
    """
    Chuyển .docx → .pdf bytes.
    - Windows: dùng Microsoft Word (qua docx2pdf)
    - Linux/Cloud: dùng LibreOffice (qua docx2pdf hoặc subprocess)
    """
    import tempfile

    pdf_path = docx_path.replace('.docx', '.pdf')

    # Phương án 1: docx2pdf (Windows dùng Word, Linux dùng LibreOffice)
    try:
        from docx2pdf import convert
        convert(docx_path, pdf_path)
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                data = f.read()
            os.remove(pdf_path)
            return data
    except Exception as e1:
        pass

    # Phương án 2: LibreOffice trực tiếp (fallback cho Linux/Cloud)
    out_dir = os.path.dirname(docx_path) or '.'
    lo_commands = [
        'libreoffice', 'soffice',
        r'C:\Program Files\LibreOffice\program\soffice.exe',
        r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
        '/usr/bin/libreoffice', '/usr/bin/soffice',
    ]
    for cmd in lo_commands:
        try:
            result = subprocess.run(
                [cmd, '--headless', '--convert-to', 'pdf', '--outdir', out_dir, docx_path],
                capture_output=True, timeout=60
            )
            if os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    data = f.read()
                os.remove(pdf_path)
                return data
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    raise RuntimeError(
        "Không thể chuyển sang PDF. Vui lòng cài:\n"
        "• Windows: Microsoft Word (thường đã có)\n"
        "• Linux/Server: apt-get install libreoffice"
    )

# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def extract_tax_metadata(xml_content):
    try:
        root = ET.fromstring(pre_process_xml(xml_content))
        mst, ten_tk, ma_tk, ky = "Unknown", "TỜ KHAI THUẾ", "", ""
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
    """
    Entry point chính: nhận XML → trả về PDF bytes.
    Pipeline ưu tiên:
      1. XML → Word template (docxtpl) → LibreOffice/Word → PDF  (chất lượng 100%)
      2. Fallback: XML → ReportLab → PDF  (khi không có LibreOffice/Word)
    """
    meta  = extract_tax_metadata(xml_content)
    ma_tk = meta.get("form", "")

    # Với form 01/TTS (maTKhai=470): thử dùng Word template trước
    if ma_tk == "470" and os.path.exists(TEMPLATE_PATH):
        ctx, root = parse_xml_to_context(xml_content)
        tpl = DocxTemplate(TEMPLATE_PATH)
        tpl.render(ctx)

        # Lưu .docx tạm — dùng named temp file với delete=False
        tmp_fd, tmp_docx = tempfile.mkstemp(suffix='.docx')
        os.close(tmp_fd)  # đóng file descriptor để tránh PermissionError
        try:
            tpl.save(tmp_docx)
            pdf_bytes = docx_to_pdf_bytes(tmp_docx)
            return io.BytesIO(pdf_bytes)
        except RuntimeError:
            # LibreOffice / Word không có → fallback ReportLab
            pass
        except Exception:
            pass
        finally:
            try:
                os.remove(tmp_docx)
            except Exception:
                pass

    # Fallback: ReportLab (luôn hoạt động, mọi platform)
    from utils import generate_tax_pdf as fallback
    return fallback(xml_content, title)

def generate_tax_docx(xml_content):
    """
    Trả về file .docx đã điền dữ liệu (để người dùng tự in/chuyển PDF).
    Hữu ích khi không có LibreOffice.
    """
    meta  = extract_tax_metadata(xml_content)
    ma_tk = meta.get("form", "")

    if ma_tk == "470" and os.path.exists(TEMPLATE_PATH):
        ctx, _ = parse_xml_to_context(xml_content)
        tpl = DocxTemplate(TEMPLATE_PATH)
        tpl.render(ctx)
        buf = io.BytesIO()
        tpl.save(buf)
        buf.seek(0)
        return buf
    return None
