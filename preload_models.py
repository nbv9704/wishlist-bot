import easyocr

# Tải trước mô hình EasyOCR
reader = easyocr.Reader(['en'], verbose=False)
print("EasyOCR models preloaded successfully")