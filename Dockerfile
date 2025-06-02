# Sử dụng image Python
FROM python:3.10-slim

# Cài đặt các phụ thuộc hệ thống
RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép mã nguồn
COPY . .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Tải trước mô hình EasyOCR
RUN python preload_models.py

# Mở cổng cho Render
ENV PORT=9704
EXPOSE 9704

# Chạy bot
CMD ["python", "main.py"]