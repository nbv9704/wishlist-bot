# Sử dụng image Python Slim để đảm bảo tương thích với torch và torchvision
FROM python:3.10-slim

# Cài đặt các phụ thuộc hệ thống cho EasyOCR và OpenCV
RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libpng16-16 \
    libjpeg62-turbo \
    libfreetype6 \
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
ENV PORT=8080
EXPOSE 8080

# Chạy bot
CMD ["python", "main.py"]