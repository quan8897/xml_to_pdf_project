# 🌐 Hướng dẫn triển khai ứng dụng XML to PDF Converter

Để bạn bè của bạn có thể sử dụng ứng dụng này qua internet, bạn có 2 cách phổ biến và dễ nhất:

---

## 🚀 Cách 1: Triển khai qua Streamlit Cloud (Miễn phí & Nhanh nhất)

Đây là cách tốt nhất nếu bạn muốn có một đường link (ví dụ: `xml-to-pdf.streamlit.app`) để gửi cho bạn bè ngay lập tức.

### Bước 1: Đưa code lên GitHub
1. Tạo một Repository mới trên GitHub (nên để chế độ Public nếu muốn dùng bản miễn phí thoải mái).
2. Tải toàn bộ mã nguồn của bạn lên đó (bao gồm: `app.py`, `utils.py`, `requirements.txt`, `packages.txt`).
3. **Lưu ý quan trọng về Font:** Bạn **NÊN** bỏ một file font hỗ trợ Tiếng Việt (ví dụ: `Roboto-Regular.ttf`) vào thẳng thư mục gốc của repo này để đảm bảo PDF tạo ra không bị lỗi dấu trên server Linux của Streamlit.

### Bước 2: Kết nối với Streamlit Cloud
1. Truy cập [share.streamlit.io](https://share.streamlit.io/) và đăng nhập bằng tài khoản GitHub.
2. Nhấn nút **"New app"**.
3. Chọn Repository bạn vừa tạo, chọn nhánh (thường là `main`), và chọn file chính là `app.py`.
4. Nhấn **"Deploy!"**. Đợi khoảng 1-2 phút, bạn sẽ có một link ứng dụng để gửi cho bạn bè.

---

## 🐳 Cách 2: Triển khai bằng Docker trên VPS (Tự chủ & Bảo mật)

Nếu bạn đã có Server riêng (VPS) và muốn cài trên đó:

### Bước 1: Cài đặt Docker trên VPS
(Nếu chưa có) Hãy chạy lệnh:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Bước 2: Build và Chạy ứng dụng
Copy thư mục code lên server, sau đó chạy:
```bash
# Xây dựng image
docker build -t xml-pdf-app .

# Chạy container ở chế độ nền (background)
docker run -d -p 80:8501 --name my-tax-app xml-pdf-app
```
*Lưu ý: `-p 80:8501` giúp bạn truy cập thẳng qua địa chỉ IP của server (ví dụ: `http://123.45.67.89`) mà không cần gõ cổng :8501.*

---

## 🛠 Những việc cần kiểm tra kỹ trước khi triển khai

1.  **File Font:** Vì môi trường Cloud (Linux) không có sẵn font `Arial` như Windows, hãy chắc chắn repo GitHub của bạn có file `Roboto-Regular.ttf` hoặc tương tự.
2.  **requirements.txt:** Đảm bảo file này có đầy đủ các thư viện (`streamlit`, `reportlab`, `pandas`).
3.  **packages.txt:** File này cực kỳ quan trọng cho Streamlit Cloud vì nó cài đặt các thư viện hệ thống cần thiết cho ReportLab xử lý PDF. (Tôi đã kiểm tra, nội dung hiện tại của bạn đã ổn).

> [!TIP]
> Nếu bạn muốn ứng dụng trông chuyên nghiệp hơn, hãy đổi tên link (URL) trong phần cài đặt của Streamlit Cloud thành một cái tên dễ nhớ như `cong-cu-tra-cuu-thue.streamlit.app`.

Chúc bạn triển khai thành công! Nếu gặp lỗi trong quá trình Deploy, hãy gửi thông báo lỗi cho tôi.
