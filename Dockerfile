# Image chính dùng Node 18 và Python
FROM node:18-slim

# Cài các gói cần thiết
RUN apt-get update && \
    apt-get install -y python3-pip && \
    pip3 install easyocr && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Tạo thư mục app
WORKDIR /app

# Copy file vào container
COPY . .

# Cài node_modules và chạy patch
RUN npm install

# Chạy bot
CMD ["npm", "start"]
