import streamlit as st
import os
import io
import datetime
import zipfile
from utils_word import generate_tax_pdf, extract_tax_metadata, generate_tax_docx

# PHẢI là lệnh Streamlit đầu tiên
st.set_page_config(page_title="Tax XML to PDF Converter", page_icon="📄", layout="wide")

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>Mẫn Nhi mập ❤️</h1>", unsafe_allow_html=True)
st.title("📄 Tax XML to PDF Converter")
st.markdown("<p style='text-align: center;'>Ứng dụng chuyên đổi XML hồ sơ thuế sang bản PDF chuyên nghiệp.</p>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2 = st.tabs(["📤 Tải file XML", "📝 Dán đoạn mã XML"])

uploaded_files = []
pasted_xml = ""

with tab1:
    st.subheader("1. Tải lên danh sách file XML")
    uploaded_files = st.file_uploader(
        "Chọn các file XML thuế (Hỗ trợ nhiều file cùng lúc):",
        type=['xml'],
        accept_multiple_files=True
    )
    if uploaded_files:
        st.success(f"Đã tải lên {len(uploaded_files)} file thành công!")

with tab2:
    st.subheader("1. Dán nội dung XML")
    pasted_xml = st.text_area(
        "Dán toàn bộ mã XML vào đây:",
        height=300,
        placeholder="<xml>...</xml>"
    )

# --- KẾT QUẢ ---
st.divider()
st.subheader("2. Kết quả bản PDF")

today_str = datetime.datetime.now().strftime("%Y%m%d")

# Xử lý khi có file tải lên
if uploaded_files:
    selected_files_data = []
    st.write("### Danh sách hàng đợi:")

    for i, uploaded_file in enumerate(uploaded_files):
        orig_name = uploaded_file.name.replace('.xml', '').replace('.XML', '')
        new_pdf_name = f"{today_str}_{orig_name}.pdf"

        with st.container(border=True):
            col_check, col_info, col_pdf, col_docx = st.columns([1, 5, 2, 2])
            is_selected = col_check.checkbox("Chọn", value=True, key=f"check_{i}")
            col_info.write(f"📄 **{uploaded_file.name}** ➞ `{new_pdf_name}`")

            xml_data = uploaded_file.read()
            try:
                pdf_buffer = generate_tax_pdf(xml_data, title="HỒ SƠ THUẾ CHI TIẾT")
                col_pdf.download_button(
                    label="📥 PDF",
                    data=pdf_buffer,
                    file_name=new_pdf_name,
                    mime="application/pdf",
                    key=f"dl_{i}",
                    use_container_width=True
                )
                if is_selected:
                    selected_files_data.append({"name": new_pdf_name, "content": pdf_buffer.getvalue()})
            except Exception as e:
                st.error(f"Lỗi file {uploaded_file.name}: {e}")

            # Nút tải DOCX — bản Word đã điền dữ liệu (đẹp hơn khi in)
            try:
                docx_buf = generate_tax_docx(xml_data)
                if docx_buf:
                    docx_name = new_pdf_name.replace('.pdf', '.docx')
                    col_docx.download_button(
                        label="📝 DOCX",
                        data=docx_buf,
                        file_name=docx_name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_docx_{i}",
                        use_container_width=True,
                        help="Tải file Word đã điền dữ liệu — mở bằng Microsoft Word để in PDF chất lượng cao"
                    )
            except Exception:
                pass


    # Nút tải ZIP
    if selected_files_data:
        st.divider()
        st.write(f"👉 Tổng cộng: **{len(selected_files_data)}** file đã được chọn.")
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

# --- FOOTER ---
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9em; padding: 20px;">
    Mẫn Nhi mập ❤️ | <a href="https://github.com/quan8897" target="_blank" style="color: #4A90E2; text-decoration: none;">Phát triển bởi Quan8897</a>
</div>
""", unsafe_allow_html=True)
