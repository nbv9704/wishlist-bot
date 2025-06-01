# Sử dụng image node
FROM node:18-slim

# Cài Tesseract
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-eng && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục dự án
WORKDIR /app

# Copy code vào container
COPY . .

# Cài Node packages
RUN npm install

# Chạy bot
CMD ["npm", "start"]