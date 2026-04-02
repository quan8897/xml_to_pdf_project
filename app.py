import streamlit as st
import os
import io
import datetime
import zipfile
from utils import generate_tax_pdf, extract_tax_metadata
from utils_word import generate_tax_docx

# --- SEO & CONFIG ---
st.set_page_config(
    page_title="Phần mềm Chuyển đổi XML sang PDF Hồ sơ Thuế Miễn phí | Tax XML Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://github.com',
        'Report a bug': 'https://github.com',
        'About': "# Giải pháp chuyển đổi XML Thuế sang PDF chuẩn iTaxViewer chuyên nghiệp."
    }
)

# Thêm SEO Metadata vào mã nguồn (cho các bot quét)
st.markdown("""
    <head>
        <meta name="description" content="Chuyển đổi file XML hồ sơ thuế sang bản PDF chuyên nghiệp, giống hệt iTaxViewer. Tích hợp đầy đủ các mẫu 01/TTS, 02/TTS chuẩn Thông tư 40/2021/TT-BTC.">
        <meta name="keywords" content="xml to pdf, thue, gdt, itaxviewer, chuyen doi xml sang pdf, khai thue online">
        <meta name="author" content="Tax XML Solutions">
    </head>
""", unsafe_allow_html=True)

# --- CUSTOM CSS (PREMIUM AESTHETICS) ---
st.markdown("""
<style>
    /* Gradient Background cho Header */
    .stAppHeader { background: transparent; }
    .main {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Thiết kế Header chuẩn SEO & Đẹp */
    .header-container {
        padding: 40px 20px;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }
    .header-container h1 {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        margin-bottom: 10px !important;
        color: #ffffff !important;
    }
    .header-container p {
        font-size: 1.2rem !important;
        opacity: 0.9;
        max-width: 800px;
        margin: 0 auto !important;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 10px 10px 0 0;
        padding: 10px 25px;
        font-weight: 600;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #2a5298 !important;
        color: white !important;
    }
    
    /* Card Container */
    .css-1r6slb0 {
        padding: 2rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 40px;
        color: #6c757d;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown("""
<div class="header-container">
    <h1>📄 Chuyển đổi Hồ sơ Thuế XML sang PDF</h1>
    <p>Giải pháp tối ưu chuyển đổi dữ liệu XML từ hệ thống Thuế (iCaNhan, HTKK) sang bản PDF in ấn chuyên nghiệp, đẹp mắt và chuẩn xác 100% theo Thông tư Bộ Tài chính.</p>
</div>
""", unsafe_allow_html=True)

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
            col_check, col_info, col_view, col_pdf, col_docx = st.columns([1, 4, 1.5, 1.5, 1.5])
            is_selected = col_check.checkbox("Chọn", value=True, key=f"check_{i}")
            col_info.write(f"📄 **{uploaded_file.name}** ➞ `{new_pdf_name}`")

            xml_data = uploaded_file.read()
            try:
                pdf_buffer = generate_tax_pdf(xml_data, title="HỒ SƠ THUẾ CHI TIẾT")
                
                # Nút xem trước
                if col_view.button("👁️ Xem", key=f"preview_{i}", use_container_width=True):
                    import base64
                    base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border-radius:10px; border:1px solid #ddd;"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)

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
<div class="footer">
    © 2024 Tax XML Solutions | Liên hệ: <b>quan98wptu@gmail.com</b> | 
    <a href="https://github.com/quan8897" target="_blank" style="color: #2a5298; text-decoration: none; font-weight: 600;">Phát triển bởi Quan8897</a>
</div>
""", unsafe_allow_html=True)
