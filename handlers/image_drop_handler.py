import discord
import requests
import os
import shutil
from PIL import Image
import easyocr
import logging
import gc

# Khởi tạo EasyOCR Reader toàn cục để tránh tải lại mô hình nhiều lần
logging.getLogger('easyocr').setLevel(logging.WARNING)  # Tắt log từ easyocr
READER = easyocr.Reader(['en'], verbose=False, gpu=False)  # Tắt GPU để giảm bộ nhớ

# Kiểm tra biến môi trường DEBUG để bật/tắt log
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

def log(message):
    if DEBUG:
        print(message)

async def handle_image_drop(message, db, bot_start_time):
    # Kiểm tra điều kiện tin nhắn
    log(f"Checking message: author_id={message.author.id}, created_at={message.created_at}, bot_start_time={bot_start_time}")
    if not message.attachments:
        log("No attachments found in message")
        return
    if not (message.author.bot and message.author.id == 646937666251915264):
        log(f"Message not from Karuta bot: author_id={message.author.id}")
        return
    if message.created_at <= bot_start_time:
        log(f"Message too old: created_at={message.created_at}, bot_start_time={bot_start_time}")
        return

    log("Message meets all conditions, proceeding to process attachment")

    try:
        temp_dir = os.path.join(os.path.dirname(__file__), '../temp')
        os.makedirs(temp_dir, exist_ok=True)
        original_file_path = os.path.join(temp_dir, 'karuta_drop.png')

        # Tải hình ảnh
        attachment = message.attachments[0]
        log(f"Downloading image from URL: {attachment.url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(attachment.url, stream=True, timeout=10, headers=headers)
        if response.status_code != 200:
            log(f"Failed to download image: status_code={response.status_code}")
            return

        with open(original_file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        log(f"Image downloaded and saved to: {original_file_path}")

        # Kiểm tra kích thước ảnh trước khi xử lý
        with Image.open(original_file_path) as img:
            img_width, img_height = img.size
            log(f"Image size: width={img_width}, height={img_height}")
            if img_width < 600 or img_height < 100:
                log("Image too small to process")
                os.unlink(original_file_path)
                return

        # Vùng cắt cho 3 nhân vật (trái → giữa → phải)
        crops = [
            {'name': 'left (Character 1)', 'left': 40, 'top': 60, 'width': 210, 'height': 50},
            {'name': 'middle (Character 2)', 'left': 310, 'top': 60, 'width': 205, 'height': 50},
            {'name': 'right (Character 3)', 'left': 590, 'top': 60, 'width': 205, 'height': 50}
        ]

        embed = discord.Embed(title='📊 Wishlist Stats', color=0x0000FF)
        description_lines = []

        for i, crop in enumerate(crops, 1):
            crop_file_path = os.path.join(temp_dir, f'cropped_{crop["name"].replace(" ", "_")}.png')
            log(f"Cropping image for {crop['name']}: left={crop['left']}, top={crop['top']}, width={crop['width']}, height={crop['height']}")
            try:
                with Image.open(original_file_path) as img:
                    # Kiểm tra kích thước ảnh
                    if (crop['left'] + crop['width'] > img_width) or (crop['top'] + crop['height'] > img_height):
                        log(f"Invalid crop dimensions for {crop['name']}: exceeds image size")
                        description_lines.extend([f"Character {i}: `None`", ''])
                        continue

                    # Crop và giảm kích thước ảnh (resize xuống 75% để tiết kiệm bộ nhớ mà vẫn đảm bảo đọc được)
                    cropped = img.crop((crop['left'], crop['top'], crop['left'] + crop['width'], crop['top'] + crop['height']))
                    cropped = cropped.convert('L').point(lambda x: 0 if x < 128 else 255, '1')  # Nhị phân hóa
                    cropped = cropped.resize((int(crop['width'] * 0.75), int(crop['height'] * 0.75)), Image.Resampling.LANCZOS)
                    cropped.save(crop_file_path)
                log(f"Cropped image saved to: {crop_file_path}")

                # Đọc văn bản bằng EasyOCR
                log(f"Reading text from cropped image: {crop_file_path}")
                result = READER.readtext(crop_file_path, detail=0, paragraph=True)
                log(f"OCR result for {crop['name']}: {result}")
                texts = [text.strip() for text in result if text.strip()]
                texts = [text for text in texts if not text.isdigit() or len(text) < 4]
                texts = [text.replace(char, '') for text in texts for char in [')', '»', '|', '}', ';', '©', '~', '—']]
                texts = [text for text in texts if text]

                # Nếu không đọc được với ảnh resize, thử lại với ảnh gốc
                if not texts:
                    log(f"Retrying OCR with original size for {crop['name']}")
                    with Image.open(original_file_path) as img:
                        cropped = img.crop((crop['left'], crop['top'], crop['left'] + crop['width'], crop['top'] + crop['height']))
                        cropped = cropped.convert('L').point(lambda x: 0 if x < 128 else 255, '1')
                        cropped.save(crop_file_path)
                    result = READER.readtext(crop_file_path, detail=0, paragraph=True)
                    texts = [text.strip() for text in result if text.strip()]
                    texts = [text for text in texts if not text.isdigit() or len(text) < 4]
                    texts = [text.replace(char, '') for text in texts for char in [')', '»', '|', '}', ';', '©', '~', '—']]
                    texts = [text for text in texts if text]

                # Xóa ảnh ngay sau khi đọc
                os.unlink(crop_file_path)
                log(f"Cropped image deleted: {crop_file_path}")

                if not texts:
                    log(f"Character {i}: No text found, adding 'None'")
                    description_lines.extend([f"Character {i}: `None`", ''])
                    continue

                character = ' '.join(texts).strip()
                log(f"Character {i} name extracted: {character}")

                # Truy vấn database
                cursor = db.characters.find({'character': {'$regex': f'^{character}$', '$options': 'i'}})
                results = list(cursor)
                cursor.close()  # Đóng cursor ngay sau khi dùng
                log(f"Database query result for Character {i} ('{character}'): {results}")

                found = False
                for result in results:
                    description_lines.append(f"Character {i} - {character} (**{result['series']}**): `{result['wishlist']} Wishlist`")
                    found = True
                    log(f"Character {i}: Found match in database: {character} ({result['series']})")

                if not found:
                    description_lines.append(f"Character {i} - {character}: `None`")
                    log(f"Character {i}: No match found in database for character: {character}")
                description_lines.append('')

                # Giải phóng bộ nhớ sau mỗi lần xử lý
                gc.collect()

            except Exception as crop_err:
                log(f"Error processing crop {crop['name']}: {crop_err}")
                description_lines.extend([f"Character {i}: `None`", ''])
                continue

        # Xóa ảnh gốc ngay sau khi crop
        os.unlink(original_file_path)
        log(f"Original image deleted: {original_file_path}")

        if not description_lines:
            log('⚠️ No valid characters found from OCR')
            return

        # Gửi embed
        embed.description = '\n'.join(description_lines)
        await message.channel.send(embed=embed)
        log("Embed 'Wishlist Stats' sent successfully")

    except Exception as err:
        log(f'❌ Error processing drop image: {err}')
        temp_dir = os.path.join(os.path.dirname(__file__), '../temp')
        original_file_path = os.path.join(temp_dir, 'karuta_drop.png')
        crop_files = [os.path.join(temp_dir, f'cropped_{name.replace(" ", "_")}.png') for name in ['left_Character_1', 'middle_Character_2', 'right_Character_3']]
        if os.path.exists(original_file_path):
            os.unlink(original_file_path)
            log(f"Cleaned up original image: {original_file_path}")
        for file in crop_files:
            if os.path.exists(file):
                os.unlink(file)
                log(f"Cleaned up cropped image: {file}")