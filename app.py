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

import zipfile

# Lấy ngày hiện tại YYYYMMDD
today_str = datetime.datetime.now().strftime("%Y%m%d")

# Xử lý khi có file tải lên
if uploaded_files:
    selected_files_data = [] # Lưu trữ dữ liệu các file được chọn để ZIP
    
    st.write("### Danh sách hàng đợi:")
    for i, uploaded_file in enumerate(uploaded_files):
        orig_name = uploaded_file.name.replace('.xml', '').replace('.XML', '')
        new_pdf_name = f"{today_str}_{orig_name}.pdf"
        
        # Tạo khung bao quanh mỗi file kèm checkbox
        with st.container(border=True):
            col_check, col_info, col_btn = st.columns([1, 6, 2])
            
            # Checkbox để chọn file
            is_selected = col_check.checkbox("Chọn", value=True, key=f"check_{i}")
            col_info.write(f"📄 **{uploaded_file.name}** ➞ `{new_pdf_name}`")
            
            # Đọc dữ liệu và tạo PDF
            xml_data = uploaded_file.read()
            try:
                pdf_buffer = generate_tax_pdf(xml_data, title="HỒ SƠ THUẾ CHI TIẾT")
                
                # Nút tải riêng lẻ (giữ lại cho tiện)
                col_btn.download_button(
                    label="Tải riêng",
                    data=pdf_buffer,
                    file_name=new_pdf_name,
                    mime="application/pdf",
                    key=f"dl_{i}",
                    use_container_width=True
                )
                
                # Nếu được chọn, thêm vào danh sách ZIP
                if is_selected:
                    selected_files_data.append({"name": new_pdf_name, "content": pdf_buffer.getvalue()})
            except Exception as e:
                st.error(f"Lỗi file {uploaded_file.name}: {e}")

    # Nút Tải ZIP cho các file đã chọn
    if selected_files_data:
        st.divider()
        st.write(f"👉 Tổng cộng: **{len(selected_files_data)}** file đã được chọn.")
        
        # Tạo file ZIP trong bộ nhớ
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in selected_files_data:
                zf.writestr(file["name"], file["content"])
        
        st.download_button(
            label="📥 TẢI TRỌN BỘ FILE ĐÃ CHỌN (.ZIP)",
            data=zip_buffer.getvalue(),
            file_name=f"{today_str}_DS_Ho_So_Thue.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )

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
