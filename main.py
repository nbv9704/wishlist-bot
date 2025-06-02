import discord
from discord.ext import commands
import pymongo
from dotenv import load_dotenv
import os
from aiohttp import web
import asyncio
from handlers.image_drop_handler import handle_image_drop
from handlers.embed_handlers import handle_embeds
from handlers.command_handlers import handle_commands
from handlers.message_update_handler import handle_message_update
from utils.import_characters import import_characters

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
pending_lookups = {}
pending_schedules = {}
current_processing = {
    'lookup': {},
    'schedule': {}
}

# Kết nối MongoDB
mongo_client = pymongo.MongoClient(os.getenv('MONGO_URI'))
db = mongo_client['wishlist_bot']

# HTTP server cho Render
async def health_check(request):
    return web.Response(text="🤖 Wishlist Bot is running!")

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
        if message.created_at > bot_start_time:
            await handle_image_drop(message, db)
            await handle_embeds(message, current_processing, pending_lookups, pending_schedules, db)
    else:
        await handle_commands(message, pending_lookups, pending_schedules)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    if after.created_at > bot_start_time:
        await handle_message_update(after, current_processing, db)

# Chạy bot và HTTP server
async def main():
    # Khởi động HTTP server
    await start_http_server()
    # Chạy bot
    await bot.start(os.getenv('BOT_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())