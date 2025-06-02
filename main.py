import discord
from discord.ext import commands
import pymongo
from dotenv import load_dotenv
import os
from aiohttp import web
import asyncio
import logging
from handlers.image_drop_handler import handle_image_drop
from utils.import_characters import import_characters

# Cấu hình logging để tắt log không mong muốn
logging.basicConfig(level=logging.WARNING)  # Chỉ hiển thị log từ WARNING trở lên
logging.getLogger('discord').setLevel(logging.WARNING)  # Tắt log INFO từ discord.py
logging.getLogger('aiohttp').setLevel(logging.WARNING)  # Tắt log INFO từ aiohttp
logging.getLogger('pymongo').setLevel(logging.WARNING)  # Tắt log INFO từ pymongo
logging.getLogger('easyocr').setLevel(logging.WARNING)  # Tắt log từ easyocr

# Tải biến môi trường
load_dotenv()

# Cấu hình bot
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

KARUTA_ID = 646937666251915264
bot_start_time = None

# Kết nối MongoDB với giới hạn số kết nối
mongo_client = pymongo.MongoClient(
    os.getenv('MONGO_URI'),
    maxPoolSize=5,  # Giới hạn số kết nối tối đa
    connectTimeoutMS=30000,
    socketTimeoutMS=30000
)
db = mongo_client['wishlist_bot']

# HTTP server cho Render
async def health_check(request):
    return web.Response(text="🤖 Wishlist Bot (kd) is running!")

async def start_http_server():
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv('PORT', 8080))  # Lấy PORT từ biến môi trường, mặc định là 8080
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 HTTP server is running on port {port}")

@bot.event
async def on_ready():
    global bot_start_time
    print(f'🤖 Bot online as {bot.user}')
    bot_start_time = discord.utils.utcnow()
    await import_characters(db)
    print('✅ MongoDB connected and characters imported')

@bot.event
async def on_message(message):
    if message.author.bot and message.author.id == KARUTA_ID:
        if bot_start_time is not None:  # Đảm bảo bot_start_time đã được khởi tạo
            await handle_image_drop(message, db, bot_start_time)
    await bot.process_commands(message)

# Đóng kết nối MongoDB khi bot dừng
@bot.event
async def on_disconnect():
    mongo_client.close()
    print("MongoDB connection closed")

# Chạy bot và HTTP server
async def main():
    # Khởi động HTTP server
    await start_http_server()
    # Chạy bot
    await bot.start(os.getenv('BOT_TOKEN'))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        mongo_client.close()
        print("Bot stopped, MongoDB connection closed")