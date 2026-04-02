"""Patch utils.py: replace rendering section (from HEADER comment to end of signature) with new clean version."""
import re

NEW_RENDERING = '''    # ─── RENDERING HELPERS ───────────────────────────────────────────
    U  = colors.HexColor('#888888')
    BG = colors.HexColor('#F2F2F2')

    def clean(v):
        return '' if not v or str(v).lower() in ('false','true','0','none') else str(v).strip()

    def pv(v):
        v = clean(v)
        return Paragraph(f'<b>{v}</b>', s9) if v else Paragraph('', s9)

    def lp(txt, bold=False):
        return Paragraph(txt, s9b if bold else s9)

    def mk2(items, widths, ul_cols=None):
        t = Table([items], colWidths=widths)
        st = [('VALIGN',(0,0),(-1,-1),'MIDDLE'),
              ('TOPPADDING',(0,0),(-1,-1),2),
              ('BOTTOMPADDING',(0,0),(-1,-1),2),
              ('LEFTPADDING',(0,0),(-1,-1),0),
              ('RIGHTPADDING',(0,0),(-1,-1),2)]
        if ul_cols:
            for c in ul_cols:
                st.append(('LINEBELOW',(c,0),(c,0), 0.5, U))
        t.setStyle(TableStyle(st))
        return t

    def frow(code, label, val, lw=195, vw=320):
        v = clean(val)
        val_p = Paragraph(f'<b>{v}</b>', s9) if v else Paragraph('', s9)
        t = Table([[lp(f'[{code}] {label}'), val_p]], colWidths=[lw, vw])
        t.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),2),
            ('BOTTOMPADDING',(0,0),(-1,-1),2),
            ('LEFTPADDING',(0,0),(-1,-1),0),
            ('RIGHTPADDING',(0,0),(-1,-1),2),
            ('LINEBELOW',(1,0),(1,0), 0.5, U),
        ]))
        return t

    def hdr_row(text):
        t = Table([[Paragraph(f'<b>{text}</b>', s9b)]], colWidths=[W])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1), BG),
            ('TOPPADDING',(0,0),(-1,-1),3),
            ('BOTTOMPADDING',(0,0),(-1,-1),3),
            ('LEFTPADDING',(0,0),(-1,-1),4),
        ]))
        return t

    ky_nam = ''; ky_thang = ''
    if kyTuNgay:
        parts = kyTuNgay.replace('/','').replace('-','').strip()
        parts = kyTuNgay.replace('/','-').split('-')
        if len(parts) >= 3:
            ky_nam   = parts[0] if len(parts[0])==4 else parts[2]
            ky_thang = parts[1].lstrip('0')

    # ── 1. HEADER ──────────────────────────────────────────────────
    hdr_tbl = Table([[
        Paragraph("<b>CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>"
                  "Độc lập – Tự do – Hạnh phúc<br/>"
                  "─────────────────────────────", s10c),
        Table([[Paragraph("<b>Mẫu số: 01/TTS</b>", s8bc)],
               [Paragraph("(Ban hành kèm theo Thông tư số<br/>"
                          "40/2021/TT-BTC ngày 01/6/2021<br/>"
                          "của Bộ trưởng Bộ Tài Chính)", s7c)]],
              colWidths=[162],
              style=[('BOX',(0,0),(-1,-1),0.5,colors.black),
                     ('TOPPADDING',(0,0),(-1,-1),3),
                     ('BOTTOMPADDING',(0,0),(-1,-1),3),
                     ('LEFTPADDING',(0,0),(-1,-1),3)])
    ]], colWidths=[353, 162])
    hdr_tbl.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP')]))
    elements.append(hdr_tbl)
    elements.append(sp(5))

    # ── 2. TIÊU ĐỀ ────────────────────────────────────────────────
    s12b_c = B('s12bc', fontSize=12, leading=16, alignment=1)
    s8c_i  = N('s8ci',  fontSize=8,  leading=11, alignment=1)
    elements.append(Paragraph('TỜ KHAI THUẾ ĐỐI VỚI HOẠT ĐỘNG CHO THUÊ TÀI SẢN', s12b_c))
    elements.append(Paragraph(
        '(Áp dụng đối với cá nhân có hoạt động cho thuê tài sản trực tiếp khai thuế '
        'với cơ quan thuế và tổ chức khai thay cho cá nhân)', s8c_i))
    elements.append(sp(5))

    # ── CHECKBOXES ────────────────────────────────────────────────
    chk_st = [('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),
              ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]
    elements.append(Table([[
        Paragraph(is_ds, s9),
        Paragraph('Cá nhân cho thuê tài sản trực tiếp khai thuế/Tổ chức, cá nhân khai thuế thay, '
                  'nộp thuế thay cho cá nhân ủy quyền theo quy định của pháp luật dân sự', s9)
    ]], colWidths=[14, W-14], style=chk_st))
    elements.append(sp(2))
    elements.append(Table([[
        Paragraph(is_thue, s9),
        Paragraph('Doanh nghiệp, tổ chức kinh tế khai thuế thay, nộp thuế thay theo pháp luật thuế', s9)
    ]], colWidths=[14, W-14], style=chk_st))
    elements.append(sp(5))

    # ── [01][02][03] KỲ TÍNH THUẾ ─────────────────────────────────
    ky_tbl = Table([
        [lp('[01] Kỳ tính thuế:', bold=True), Paragraph('', s9)],
        [lp('  [01a] Năm:'), Paragraph(f'<b>{ky_nam}</b>', s9)],
        [lp('  [01b] Kỳ thanh toán:'),
         Paragraph(f'Từ ngày: <b>{kyTuNgay or "..."}</b>  &nbsp;&nbsp;  Đến ngày: <b>{kyDenNgay or "..."}</b>', s9)],
        [lp('  [01c] Tháng:'), Paragraph(f'<b>{ky_thang}</b> năm <b>{ky_nam}</b>', s9)],
        [lp('  [01d] Quý:'), Paragraph(f'năm <b>{ky_nam}</b>', s9)],
        [Paragraph(
            f'[02] Lần đầu: <b>{"☑" if loai=="C" else "☐"}</b>'
            f'  &nbsp;&nbsp;&nbsp;&nbsp;  '
            f'[03] Bổ sung lần thứ: <b>{soLan if soLan and soLan != "0" else ""}</b>', s9),
         Paragraph('', s9)],
    ], colWidths=[195, 320])
    ky_tbl.setStyle(TableStyle([
        ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    elements.append(ky_tbl)
    elements.append(sp(5))

    # ── [04]-[09] THÔNG TIN NGƯỜI NỘP THUẾ ───────────────────────
    elements.append(hdr_row('THÔNG TIN NGƯỜI NỘP THUẾ'))
    elements.append(sp(2))
    elements.append(mk2([lp('[04] Người nộp thuế:'), Paragraph(f'<b>{tenNNT}</b>', s9)],[145, 370]))
    elements.append(mk2([lp('[05] Mã số thuế:'), draw_mst_boxes(mst, fn)],[145, 370]))
    elements.append(mk2([lp('[06] Địa chỉ liên hệ:'), Paragraph(f'<b>{dchi}</b>', s9)],[145, 370], ul_cols=[1]))
    elements.append(mk2([lp('[07] Điện thoại:'), pv(dthoai),
                         lp('[08] Fax:'), pv(fax),
                         lp('[09] Email:'), Paragraph(f'<b>{email}</b>', s9)],
                        [85, 90, 40, 60, 45, 195], ul_cols=[1, 3, 5]))
    elements.append(sp(3))

    # ── [10][11] ──────────────────────────────────────────────────
    elements.append(frow('10', 'Số CMND (trường hợp cá nhân quốc tịch Việt Nam):', clean(ct10)))
    elements.append(frow('11', 'Hộ chiếu (trường hợp cá nhân không có quốc tịch Việt Nam):', clean(ct11)))
    elements.append(sp(3))

    # ── [12] THÔNG TIN BỔ SUNG ────────────────────────────────────
    elements.append(Paragraph(
        '<b>[12]</b> <i>Trường hợp cá nhân kinh doanh chưa đăng ký thuế '
        'thì khai thêm các thông tin sau:</i>', s9))
    elements.append(sp(2))
    elements.append(mk2([lp('[12a] Ngày sinh:'), pv(ct12a), lp('[12b] Quốc tịch:'), pv(ct12b)],
                        [90, 115, 80, 130], ul_cols=[1, 3]))
    elements.append(frow('12c', 'Số CMND/CCCD:', ct12c_so))
    elements.append(mk2([lp('[12c.1] Ngày cấp:'), pv(ct12c_ngay), lp('[12c.2] Nơi cấp:'), pv(ct12c_noi)],
                        [90, 115, 80, 130], ul_cols=[1, 3]))
    s8_i = N('s8i', fontSize=8, leading=10)
    elements.append(Paragraph(
        '<i>Trường hợp cá nhân kinh doanh thuộc đối tượng không có CMND/CCCD tại Việt Nam '
        'thì kê khai thông tin tại một trong các thông tin sau:</i>', s8_i))
    elements.append(mk2([lp('[12d] Số hộ chiếu:'), pv(ct12d_so), lp('[12d.1] Ngày cấp:'), pv(ct12d_ngay)],
                        [105, 115, 80, 115], ul_cols=[1, 3]))
    elements.append(frow('12d.2', 'Nơi cấp:', ct12d_noi))
    elements.append(mk2([lp('[12đ] Số giấy thông hành (đối với thương nhân nước ngoài):'), pv(ct12dd_so)],
                        [270, 245], ul_cols=[1]))
    elements.append(mk2([lp('[12đ.1] Ngày cấp:'), pv(ct12dd_ngay), lp('[12đ.2] Nơi cấp:'), pv(ct12dd_noi)],
                        [90, 115, 80, 130], ul_cols=[1, 3]))
    elements.append(mk2([lp('[12e] Số CMND biên giới (đối với thương nhân nước ngoài):'), pv(ct12e_so)],
                        [255, 260], ul_cols=[1]))
    elements.append(mk2([lp('[12e.1] Ngày cấp:'), pv(ct12e_ngay), lp('[12e.2] Nơi cấp:'), pv(ct12e_noi)],
                        [90, 115, 80, 130], ul_cols=[1, 3]))
    elements.append(mk2([lp('[12f] Số Giấy tờ chứng thực cá nhân khác:'), pv(ct12f_so)],
                        [225, 290], ul_cols=[1]))
    elements.append(mk2([lp('[12f.1] Ngày cấp:'), pv(ct12f_ngay), lp('[12f.2] Nơi cấp:'), pv(ct12f_noi)],
                        [90, 115, 80, 130], ul_cols=[1, 3]))
    elements.append(lp('[12g] Nơi đăng ký thường trú:'))
    elements.append(frow('12g.1', 'Số nhà, đường phố/xóm/ấp/thôn:', ct12g_nha))
    elements.append(mk2([lp('[12g.2] Phường/xã/Thị trấn:'), pv(ct12g_ph),
                         lp('[12g.3] Quận/Huyện/Thị xã:'), pv(ct12g_qu)],
                        [120, 130, 110, 155], ul_cols=[1, 3]))
    elements.append(frow('12g.4', 'Tỉnh/Thành phố:', ct12g_ti))
    elements.append(lp('[12h] Chỗ ở hiện tại:'))
    elements.append(frow('12h.1', 'Số nhà, đường phố/xóm/ấp/thôn:', ct12h_nha))
    elements.append(mk2([lp('[12h.2] Phường/xã/Thị trấn:'), pv(ct12h_ph),
                         lp('[12h.3] Quận/Huyện/Thị xã:'), pv(ct12h_qu)],
                        [120, 130, 110, 155], ul_cols=[1, 3]))
    elements.append(frow('12h.4', 'Tỉnh/Thành phố:', ct12h_ti))
    elements.append(mk2([lp('[12i] Giấy chứng nhận đăng ký hộ kinh doanh (nếu có): số:'), pv(ct12i_so)],
                        [280, 235], ul_cols=[1]))
    elements.append(mk2([lp('[12i.1] Ngày cấp:'), pv(ct12i_ngay), lp('[12i.2] Cơ quan cấp:'), pv(ct12i_cq)],
                        [90, 110, 100, 215], ul_cols=[1, 3]))
    _ct12k = clean(ct12k)
    elements.append(frow('12k', 'Vốn kinh doanh (đồng):', _ct12k if _ct12k and _ct12k != '0' else ''))
    elements.append(sp(3))

    # ── [13][14][15] ĐẠI LÝ THUẾ ─────────────────────────────────
    elements.append(frow('13', 'Tên đại lý thuế (nếu có):', ''))
    elements.append(mk2([lp('[14] Mã số thuế đại lý:'), draw_mst_boxes('', fn)],[130, 385]))
    elements.append(mk2([lp('[15] Hợp đồng đại lý thuế: số'), pv(''), lp('ngày'), pv('')],
                        [195, 150, 40, 130], ul_cols=[1, 3]))
    elements.append(sp(3))

    # ── [16]-[22] TỔ CHỨC KHAI/NỘP THUẾ THAY ────────────────────
    elements.append(frow('16', 'Tổ chức khai, nộp thuế thay (nếu có):', tc16))
    elements.append(mk2([lp('[17] Mã số thuế:'), draw_mst_boxes(tc17, fn)],[115, 400]))
    elements.append(frow('18', 'Địa chỉ:', tc18))
    elements.append(mk2([lp('[19] Điện thoại:'), pv(tc19), lp('[20] Fax:'), pv(tc20),
                         lp('[21] Email:'), pv(tc21)],
                        [75, 100, 40, 65, 40, 195], ul_cols=[1, 3, 5]))
    elements.append(mk2([lp('[22] Văn bản ủy quyền (nếu có): số'), pv(maHDong), lp('ngày'), pv('')],
                        [205, 140, 40, 130], ul_cols=[1, 3]))
    elements.append(sp(6))

    # ── 5. PHẦN A ─────────────────────────────────────────────────
    col_w = [28, 305, 72, 110]
    unit_t = Table([[Paragraph('Đơn vị tính: Đồng Việt Nam', s8)]], colWidths=[W])
    unit_t.setStyle(TableStyle([('ALIGN',(0,0),(0,0),'RIGHT')]))
    tax_hdr = [Paragraph(f'<b>{t}</b>', s8bc) for t in ['STT','Chỉ tiêu','Mã chỉ tiêu','Số tiền']]
    tax_body = [
        ['1','Tổng doanh thu phát sinh trong kỳ','[23]',ct23 or '0'],
        ['2','Tổng doanh thu tính thuế','[24]',ct24 or '0'],
        ['3','Tổng số thuế GTGT phải nộp','[25]',ct25 or '0'],
        ['4','Tổng số thuế TNCN phải nộp phát sinh trong kỳ','[26]',ct26 or '0'],
        ['5','Tiền phạt, bồi thường nhận được theo thỏa thuận tại hợp đồng (nếu có)','[27]',ct27 or '0'],
        ['6','Tổng số thuế TNCN từ bồi thường/phạt vi phạm hợp đồng (nếu có)','[28]',ct28 or '0'],
        ['7','Tổng số thuế TNCN phải nộp [29]=[26]+[28]','[29]',ct29 or '0'],
    ]
    rows = [tax_hdr] + [[Paragraph(r[0],s8c), Paragraph(r[1],s8),
                          Paragraph(r[2],s8c), Paragraph(fmt_num(r[3]),s8r)] for r in tax_body]
    t_tax = Table(rows, colWidths=col_w, repeatRows=1)
    t_tax.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),0.5,colors.black),
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#D9D9D9')),
        ('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#FFF2CC')),
        ('FONTNAME',(0,-1),(-1,-1),fb),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',(0,0),(0,-1),'CENTER'),
        ('ALIGN',(2,0),(2,-1),'CENTER'),
        ('ALIGN',(3,0),(3,-1),'RIGHT'),
        ('TOPPADDING',(0,0),(-1,-1),3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),3),
    ]))
    phần_a = KeepTogether([
        Paragraph('<b>A. PHẦN CÁ NHÂN KÊ KHAI NGHĨA VỤ THUẾ</b>', s9b),
        sp(2), unit_t, t_tax, sp(2),
        Paragraph('<i>(TNCN: Thu nhập cá nhân; GTGT: Giá trị gia tăng)</i>', s8),
    ])
    elements.append(phần_a)
    elements.append(sp(8))

    # ── 6. CAM KẾT + KÝ TÊN ──────────────────────────────────────
    elements.append(Paragraph(
        'Tôi cam đoan số liệu khai trên là đúng và chịu trách nhiệm trước pháp luật '
        'về những số liệu đã khai./.', s9))
    elements.append(sp(2))
    now = datetime.datetime.now()
    sig = Table([
        [Paragraph('<b>NHÂN VIÊN ĐẠI LÝ THUẾ</b>', s9bi),
         Paragraph(f'..., ngày {now.day:02d} tháng {now.month:02d} năm {now.year}<br/><br/>'
                   '<b>NGƯỜI NỘP THUẾ hoặc<br/>ĐẠI DIỆN HỢP PHÁP CỦA NGƯỜI NỘP THUẾ</b>', s9bi)],
        [Paragraph('Họ và tên:', s9), Paragraph('', s9)],
        [Paragraph('Chứng chỉ hành nghề số:', s9),
         Paragraph('<i>(Chữ ký, ghi rõ họ tên; chức vụ và đóng dấu (nếu có)/Ký điện tử)</i>', s8)],
    ], colWidths=[257, 258])
    sig.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    elements.append(sig)
'''

with open('utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find markers
START_MARKER = '    # ── 1. HEADER ───────────────────────────────────────────────────'
END_MARKER   = '    elements.append(sig)\n\n    # ── 7. PHỤ LỤC'

start_idx = content.find(START_MARKER)
end_idx   = content.find(END_MARKER)

if start_idx == -1:
    print("ERROR: START_MARKER not found!")
elif end_idx == -1:
    print("ERROR: END_MARKER not found!")
else:
    end_idx_final = end_idx + len('    elements.append(sig)\n')
    new_content = content[:start_idx] + NEW_RENDERING + '\n' + content[end_idx_final:]
    with open('utils.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS! utils.py patched.")
    print(f"  Replaced chars {start_idx} to {end_idx_final}")
    print(f"  Old size: {len(content)} | New size: {len(new_content)}")
