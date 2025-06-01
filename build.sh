#!/usr/bin/env bash

# Cài Python3 và pip3
apt-get update && apt-get install -y python3 python3-pip

# Alias python → python3 (nếu chưa tồn tại)
ln -sf /usr/bin/python3 /usr/bin/python

# Cài easyocr (python)
pip3 install easyocr

# Cài node_modules và chạy patch
npm install
