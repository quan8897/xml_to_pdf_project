import streamlit as st
import os
import io
from utils import generate_tax_pdf

# --- CẤU HÌNH GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Tax XML to PDF Converter", page_icon="📄", layout="wide")

st.title("📄 Tax XML to PDF Converter")
st.markdown("""
Ứng dụng chuyên đổi XML hồ sơ thuế sang bản PDF chuyên nghiệp.  
*Dành riêng cho Mẫn Nhi mập ❤️*
""")

col1, col2 = st.columns([1, 1])

# ... (giữ nguyên phần col1, col2 cũ)
with col1:
    st.subheader("1. Tải lên file XML")
    uploaded_file = st.file_uploader("Chọn file XML thuế (Vd: Tờ khai thuế GTGT, TNCN...)", type=['xml'])

with col2:
    st.subheader("2. Kết quả bản PDF")
    if uploaded_file is not None:
        st.success(f"Đã tải file thành công: {uploaded_file.name}")
        xml_data = uploaded_file.read()
        
        if st.button("🚀 Bắt đầu Chuyển đổi PDF"):
            with st.spinner('Máy chủ đang phân tích dữ liệu và tạo PDF...'):
                try:
                    pdf_buffer = generate_tax_pdf(xml_data, title="HỒ SƠ THUẾ CHI TIẾT")
                    st.balloons()
                    
                    st.download_button(
                        label="📥 Tải xuống kết quả bản PDF",
                        data=pdf_buffer,
                        file_name=f"{uploaded_file.name.replace('.xml', '')}_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"⚠️ Có lỗi xảy ra trong quá trình xử lý: {e}")

st.divider()
footer_html = """
<div style="text-align: center; color: #888; font-size: 0.9em; padding: 20px;">
    Mẫn Nhi mập và trái tim ❤️ | <a href="https://github.com/quan8897" target="_blank" style="color: #4A90E2; text-decoration: none;">Phát triển bởi Quan8897</a>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
st.info("💡 Lưu ý: Nếu nội dung bị mất dấu Tiếng Việt trên bản PDF, hãy chắc chắn bạn đã upload file font Roboto-Regular.ttf lên GitHub.")
