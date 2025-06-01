# Sử dụng image node có sẵn Python
FROM node:18-slim

# Cài Python và pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv && \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install easyocr && \
    ln -sf /opt/venv/bin/python /usr/bin/python

# Thiết lập thư mục dự án
WORKDIR /app

# Copy code vào container
COPY . .

# Cài Node packages và chạy patch
RUN npm install

# Chạy bot
CMD ["npm", "start"]
