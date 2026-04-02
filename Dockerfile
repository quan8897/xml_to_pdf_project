# Sử dụng Python image mỏng
FROM python:3.9-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết (nếu có)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Sao chép file requirements.txt vào container
COPY requirements.txt .

# Cài đặt các thư viện Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn vào container
COPY . .

# Expose cổng mà Streamlit sử dụng
EXPOSE 8501

# Lệnh kiểm tra sức sống (Healthcheck) cho Streamlit
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Lệnh chạy ứng dụng
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
