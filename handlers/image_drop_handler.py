import discord
import requests
import os
import shutil
from PIL import Image
import easyocr

async def handle_image_drop(message, db):
    if not message.attachments:
        return

    try:
        temp_dir = os.path.join(os.path.dirname(__file__), '../temp')
        os.makedirs(temp_dir, exist_ok=True)
        original_file_path = os.path.join(temp_dir, 'karuta_drop.png')

        # Tải hình ảnh
        attachment = message.attachments[0]
        response = requests.get(attachment.url, stream=True)
        with open(original_file_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

        # Vùng cắt
        crops = [
            {'name': 'part1', 'left': 40, 'top': 60, 'width': 210, 'height': 50},
            {'name': 'part2', 'left': 310, 'top': 60, 'width': 205, 'height': 50},
            {'name': 'part3', 'left': 590, 'top': 60, 'width': 205, 'height': 50}
        ]

        reader = easyocr.Reader(['en'])
        results_by_part = []

        for crop in crops:
            crop_file_path = os.path.join(temp_dir, f'cropped_{crop["name"]}.png')
            with Image.open(original_file_path) as img:
                cropped = img.crop((crop['left'], crop['top'], crop['left'] + crop['width'], crop['top'] + crop['height']))
                cropped = cropped.convert('L').point(lambda x: 0 if x < 128 else 255, '1')  # Nhị phân hóa
                cropped.save(crop_file_path)

            result = reader.readtext(crop_file_path, detail=0, paragraph=True)
            texts = [text.strip() for text in result if text.strip()]
            texts = [text for text in texts if not text.isdigit() or len(text) < 4]
            texts = [text.replace(char, '') for text in texts for char in [')', '»', '|', '}', ';', '©', '~', '—']]
            texts = [text for text in texts if text]

            results_by_part.append(texts)
            os.unlink(crop_file_path)

        os.unlink(original_file_path)

        lines = []
        for texts in results_by_part:
            if not texts:
                lines.extend(['None', ''])
                continue

            character = ' '.join(texts).strip()
            # Truy cập trực tiếp collection 'characters' thay vì sử dụng class Character
            results = db.characters.find({'character': {'$regex': f'^{character}$', '$options': 'i'}})

            found = False
            for result in results:
                lines.append(f"{character} (**{result['series']}**): `{result['wishlist']} Wishlist`")
                found = True

            if not found:
                lines.append(f"{character}: `None`")
            lines.append('')

        if lines and lines[-1] == '':
            lines.pop()

        if not lines:
            print('⚠️ No valid characters found from OCR')
            return

        embed = discord.Embed(title='📊 Wishlist Stats', description='\n'.join(lines), color=0x0000FF)
        await message.channel.send(embed=embed)

    except Exception as err:
        print(f'❌ Error processing drop image: {err}')
        temp_dir = os.path.join(os.path.dirname(__file__), '../temp')
        original_file_path = os.path.join(temp_dir, 'karuta_drop.png')
        crop_files = [os.path.join(temp_dir, f'cropped_part{i}.png') for i in range(1, 4)]
        if os.path.exists(original_file_path):
            os.unlink(original_file_path)
        for file in crop_files:
            if os.path.exists(file):
                os.unlink(file)