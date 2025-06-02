# Sử dụng image Python Alpine nhẹ hơn
FROM python:3.10-alpine

# Cài đặt các phụ thuộc hệ thống
RUN apk add --no-cache \
    libgl1-mesa-glx \
    libglib \
    && rm -rf /var/cache/apk/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép mã nguồn
COPY . .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir -r requirements.txt

# Tải trước mô hình EasyOCR
RUN python preload_models.py

# Mở cổng cho Render
ENV PORT=8080
EXPOSE 8080

# Chạy bot
CMD ["python", "main.py"]