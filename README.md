# 📄 Tax XML to PDF Converter (VN)

Ứng dụng chuyển đổi hồ sơ thuế (Tờ khai thuế) từ định dạng **XML** sang **PDF** chuyên nghiệp, hỗ trợ hoàn toàn tiếng Việt (Unicode).

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Tính năng chính

- [x] **Giao diện Web thân thiện:** Sử dụng Streamlit để tải lên và tải xuống file nhanh chóng.
- [x] **Hỗ trợ Tiếng Việt:** Xử lý triệt để vấn đề font chữ Unicode trên PDF (với font Roboto/Arial).
- [x] **Cấu trúc linh hoạt:** Tự động phân tích cấu trúc XML lồng nhau sang bảng dữ liệu PDF dễ đọc.
- [x] **Xử lý lô (Batch):** Có sẵn công cụ chạy qua CLI để chuyển đổi hàng loạt file trong thư mục.
- [x] **Dockerized:** Sẵn sàng triển khai trên các nền tảng Cloud hoặc Server riêng.

---

## 🚀 Hướng dẫn nhanh

### 1. Cài đặt trực tiếp (Local)

Yêu cầu Python 3.9 trở lên.

```bash
# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 2. Chạy ứng dụng Web (Streamlit)

```bash
streamlit run app.py
```
Sau đó truy cập địa chỉ: `http://localhost:8501`

### 3. Triển khai với Docker

```bash
# Build image
docker build -t xml-to-pdf-converter .

# Chạy container
docker run -p 8501:8501 xml-to-pdf-converter
```

---

## 🛠 Cấu trúc dự án

- **`app.py`**: Điểm khởi đầu của ứng dụng Web (Streamlit UI).
- **`utils.py`**: Chứa logic cốt lõi (Đăng ký font, parse XML, render PDF qua ReportLab).
- **`tax_handler.py`**: Công cụ CLI để chuyển đổi hàng loạt file XML thuế.
- **`convert_xml_to_pdf.py`**: Mẫu chuyển đổi cho các định dạng XML sản phẩm/danh mục khác.
- **`requirements.txt`**: Danh sách thư viện Python (Streamlit, ReportLab, Pandas).
- **`Dockerfile`**: Cấu hình để chạy dự án trong container.

---

## 📝 Lưu ý về Font chữ

Để hiển thị tốt nhất tiếng Việt, hãy đảm bảo bạn có file font `.ttf` (như Roboto-Regular.ttf hoặc Arial.ttf) trong thư mục gốc. Ứng dụng sẽ tự động ưu tiên:
1. `Roboto-Regular.ttf` trong thư mục dự án.
2. `arial.ttf` từ hệ thống (Windows/Linux).

Nếu triển khai trên Linux Server, hãy kiểm tra cài đặt font Unicode (như `ttf-mscorefonts-installer`) để tránh lỗi mất dấu.

---

## 🤝 Đóng góp

Mọi ý kiến đóng góp hoặc báo lỗi xin vui lòng tạo **Issue** hoặc **Pull Request**. Chúc bạn có trải nghiệm làm việc với hồ sơ thuế nhẹ nhàng hơn!

---
*Phát triển bởi Antigravity AI Assistant.*
