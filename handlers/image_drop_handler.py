import discord
import requests
import os
import shutil
from PIL import Image
import easyocr
import logging

# Khởi tạo EasyOCR Reader toàn cục để tránh tải lại mô hình nhiều lần
logging.getLogger('easyocr').setLevel(logging.WARNING)  # Tắt log từ easyocr
READER = easyocr.Reader(['en'], verbose=False)  # Tắt log từ EasyOCR

async def handle_image_drop(message, db, bot_start_time):
    # Kiểm tra điều kiện tin nhắn
    print(f"Checking message: author_id={message.author.id}, created_at={message.created_at}, bot_start_time={bot_start_time}")
    if not message.attachments:
        print("No attachments found in message")
        return
    if not (message.author.bot and message.author.id == 646937666251915264):
        print(f"Message not from Karuta bot: author_id={message.author.id}")
        return
    if message.created_at <= bot_start_time:
        print(f"Message too old: created_at={message.created_at}, bot_start_time={bot_start_time}")
        return

    print("Message meets all conditions, proceeding to process attachment")

    try:
        temp_dir = os.path.join(os.path.dirname(__file__), '../temp')
        os.makedirs(temp_dir, exist_ok=True)
        original_file_path = os.path.join(temp_dir, 'karuta_drop.png')

        # Tải hình ảnh
        attachment = message.attachments[0]
        print(f"Downloading image from URL: {attachment.url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(attachment.url, stream=True, timeout=10, headers=headers)
        if response.status_code != 200:
            print(f"Failed to download image: status_code={response.status_code}")
            return

        with open(original_file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        print(f"Image downloaded and saved to: {original_file_path}")

        # Vùng cắt cho 3 nhân vật (trái → giữa → phải)
        crops = [
            {'name': 'left (Character 1)', 'left': 40, 'top': 60, 'width': 210, 'height': 50},
            {'name': 'middle (Character 2)', 'left': 310, 'top': 60, 'width': 205, 'height': 50},
            {'name': 'right (Character 3)', 'left': 590, 'top': 60, 'width': 205, 'height': 50}
        ]

        results_by_part = []

        for crop in crops:
            crop_file_path = os.path.join(temp_dir, f'cropped_{crop["name"].replace(" ", "_")}.png')
            print(f"Cropping image for {crop['name']}: left={crop['left']}, top={crop['top']}, width={crop['width']}, height={crop['height']}")
            try:
                with Image.open(original_file_path) as img:
                    # Kiểm tra kích thước ảnh
                    img_width, img_height = img.size
                    print(f"Image size: width={img_width}, height={img_height}")
                    if (crop['left'] + crop['width'] > img_width) or (crop['top'] + crop['height'] > img_height):
                        print(f"Invalid crop dimensions for {crop['name']}: exceeds image size")
                        results_by_part.append([])
                        continue

                    cropped = img.crop((crop['left'], crop['top'], crop['left'] + crop['width'], crop['top'] + crop['height']))
                    cropped = cropped.convert('L').point(lambda x: 0 if x < 128 else 255, '1')  # Nhị phân hóa để tăng độ chính xác OCR
                    cropped.save(crop_file_path)
                print(f"Cropped image saved to: {crop_file_path}")

                # Đọc văn bản bằng EasyOCR
                print(f"Reading text from cropped image: {crop_file_path}")
                result = READER.readtext(crop_file_path, detail=0, paragraph=True)
                print(f"OCR result for {crop['name']}: {result}")
                texts = [text.strip() for text in result if text.strip()]
                texts = [text for text in texts if not text.isdigit() or len(text) < 4]
                texts = [text.replace(char, '') for text in texts for char in [')', '»', '|', '}', ';', '©', '~', '—']]
                texts = [text for text in texts if text]

                results_by_part.append(texts)
                os.unlink(crop_file_path)
                print(f"Cropped image deleted: {crop_file_path}")
            except Exception as crop_err:
                print(f"Error processing crop {crop['name']}: {crop_err}")
                results_by_part.append([])
                continue

        os.unlink(original_file_path)
        print(f"Original image deleted: {original_file_path}")

        # Xử lý kết quả và truy vấn database
        lines = []
        for i, texts in enumerate(results_by_part, 1):
            if not texts:
                print(f"Character {i}: No text found, adding 'None'")
                lines.extend([f"Character {i}: `None`", ''])
                continue

            character = ' '.join(texts).strip()
            print(f"Character {i} name extracted: {character}")
            # Truy vấn database
            results = list(db.characters.find({'character': {'$regex': f'^{character}$', '$options': 'i'}}))
            print(f"Database query result for Character {i} ('{character}'): {results}")

            found = False
            for result in results:
                lines.append(f"Character {i} - {character} (**{result['series']}**): `{result['wishlist']} Wishlist`")
                found = True
                print(f"Character {i}: Found match in database: {character} ({result['series']})")

            if not found:
                lines.append(f"Character {i} - {character}: `None`")
                print(f"Character {i}: No match found in database for character: {character}")
            lines.append('')

        if lines and lines[-1] == '':
            lines.pop()

        if not lines:
            print('⚠️ No valid characters found from OCR')
            return

        # Gửi embed
        print(f"Preparing to send embed with content:\n{lines}")
        embed = discord.Embed(title='📊 Wishlist Stats', description='\n'.join(lines), color=0x0000FF)
        await message.channel.send(embed=embed)
        print("Embed 'Wishlist Stats' sent successfully")

    except Exception as err:
        print(f'❌ Error processing drop image: {err}')
        temp_dir = os.path.join(os.path.dirname(__file__), '../temp')
        original_file_path = os.path.join(temp_dir, 'karuta_drop.png')
        crop_files = [os.path.join(temp_dir, f'cropped_{name.replace(" ", "_")}.png') for name in ['left_Character_1', 'middle_Character_2', 'right_Character_3']]
        if os.path.exists(original_file_path):
            os.unlink(original_file_path)
            print(f"Cleaned up original image: {original_file_path}")
        for file in crop_files:
            if os.path.exists(file):
                os.unlink(file)
                print(f"Cleaned up cropped image: {file}")