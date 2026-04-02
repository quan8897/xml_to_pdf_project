import streamlit as st
import os
import io
from utils import generate_tax_pdf

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>Mẫn Nhi mập ❤️</h1>", unsafe_allow_html=True)
st.title("📄 Tax XML to PDF Converter")
st.markdown("<p style='text-align: center;'>Ứng dụng chuyên đổi XML hồ sơ thuế sang bản PDF chuyên nghiệp.</p>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📤 Tải file XML", "📝 Dán đoạn mã XML"])
# ... (giữ nguyên phần code xử lý bên trong)
xml_data = None
show_results = False

import datetime

# ... (sau phần tabs)
with tab1:
    st.subheader("1. Tải lên danh sách file XML")
    uploaded_files = st.file_uploader("Chọn tối đa các file XML thuế (Hỗ trợ nhiều file cùng lúc):", type=['xml'], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"Đã tải lên {len(uploaded_files)} file thành công!")

with tab2:
    st.subheader("1. Dán nội dung XML")
    pasted_xml = st.text_area("Dán toàn bộ mã XML vào đây:", height=300, placeholder="<xml>...</xml>")
    
st.divider()
st.subheader("2. Kết quả bản PDF")

# Lấy ngày hiện tại YYYYMMDD
today_str = datetime.datetime.now().strftime("%Y%m%d")

# Xử lý khi có file tải lên
if uploaded_files:
    for uploaded_file in uploaded_files:
        # Tạo tên file mới: YYYYMMDD_TênFile.pdf
        orig_name = uploaded_file.name.replace('.xml', '').replace('.XML', '')
        new_pdf_name = f"{today_str}_{orig_name}.pdf"
        
        with st.expander(f"📄 Xử lý: {uploaded_file.name}", expanded=True):
            col_info, col_btn = st.columns([3, 1])
            col_info.write(f"Tên file đích: **{new_pdf_name}**")
            
            # Đọc dữ liệu từng file
            xml_data = uploaded_file.read()
            try:
                pdf_buffer = generate_tax_pdf(xml_data, title="HỒ SƠ THUẾ CHI TIẾT")
                col_btn.download_button(
                    label="📥 Tải PDF",
                    data=pdf_buffer,
                    file_name=new_pdf_name,
                    mime="application/pdf",
                    key=f"btn_{uploaded_file.name}" # Khóa duy nhất cho mỗi nút
                )
            except Exception as e:
                st.error(f"Lỗi file {uploaded_file.name}: {e}")

# Xử lý khi dán XML
elif pasted_xml:
    new_pdf_name = f"{today_str}_Pasted_Report.pdf"
    st.info(f"Đã sẵn sàng dán mã. Tên file đích: **{new_pdf_name}**")
    if st.button("🚀 Chuyển đổi mã dán", use_container_width=True):
        try:
            pdf_buffer = generate_tax_pdf(pasted_xml.encode('utf-8'), title="HỒ SƠ THUẾ CHI TIẾT")
            st.download_button(
                label="📥 Tải xuống kết quả PDF",
                data=pdf_buffer,
                file_name=new_pdf_name,
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Lỗi: {e}")
else:
    st.info("Chào bạn! Hãy tải file XML hoặc dán mã để bắt đầu xử lý nhé.")

st.divider()
footer_html = """
<div style="text-align: center; color: #888; font-size: 0.9em; padding: 20px;">
    Mẫn Nhi mập ❤️ | <a href="https://github.com/quan8897" target="_blank" style="color: #4A90E2; text-decoration: none;">Phát triển bởi Quan8897</a>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
st.info("💡 Lưu ý: Nếu nội dung bị mất dấu Tiếng Việt trên bản PDF, hãy chắc chắn bạn đã upload file font Roboto-Regular.ttf lên GitHub.")
