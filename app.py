import streamlit as st
import os
import io
from utils import generate_tax_pdf

# --- CẤU HÌNH GIAO DIỆN STREAMLIT ---
st.set_page_config(page_title="Tax XML to PDF Converter", page_icon="📄", layout="wide")

st.title("📄 Tax XML to PDF Converter")
st.markdown("Ứng dụng chuyên đổi XML hồ sơ thuế sang bản PDF chuyên nghiệp.")

tab1, tab2 = st.tabs(["📤 Tải file XML", "📝 Dán đoạn mã XML"])
# ... (giữ nguyên phần code xử lý bên trong)
xml_data = None
show_results = False

with tab1:
    st.subheader("1. Tải lên file XML")
    uploaded_file = st.file_uploader("Chọn file XML thuế (Vd: Tờ khai thuế GTGT, TNCN...)", type=['xml'])
    if uploaded_file is not None:
        xml_data = uploaded_file.read()
        show_results = True

with tab2:
    st.subheader("1. Dán nội dung XML")
    pasted_xml = st.text_area("Dán toàn bộ mã XML vào đây:", height=300, placeholder="<xml>...</xml>")
    if pasted_xml:
        xml_data = pasted_xml.encode('utf-8')
        show_results = True

st.divider()
st.subheader("2. Kết quả bản PDF")

pdf_filename = "Tax_Report.pdf"
if uploaded_file:
    pdf_filename = f"{uploaded_file.name.replace('.xml', '')}_Report.pdf"
else:
    pdf_filename = "Pasted_Tax_Report.pdf"

if show_results and xml_data:
    st.success("Đã sẵn sàng dữ liệu xử lý!")
    if st.button("🚀 Bắt đầu Chuyển đổi PDF", use_container_width=True):
        with st.spinner('Máy chủ đang phân tích dữ liệu và tạo PDF...'):
            try:
                pdf_buffer = generate_tax_pdf(xml_data, title="HỒ SƠ THUẾ CHI TIẾT")
                st.balloons()
                
                st.download_button(
                    label="📥 Tải xuống kết quả bản PDF",
                    data=pdf_buffer,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"⚠️ Có lỗi xảy ra trong quá trình xử lý: {e}")
else:
    st.info("Vui lòng tải file hoặc dán mã XML để bắt đầu.")

st.divider()
footer_html = """
<div style="text-align: center; color: #888; font-size: 0.9em; padding: 20px;">
    Mẫn Nhi mập ❤️ | <a href="https://github.com/quan8897" target="_blank" style="color: #4A90E2; text-decoration: none;">Phát triển bởi Quan8897</a>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
st.info("💡 Lưu ý: Nếu nội dung bị mất dấu Tiếng Việt trên bản PDF, hãy chắc chắn bạn đã upload file font Roboto-Regular.ttf lên GitHub.")
