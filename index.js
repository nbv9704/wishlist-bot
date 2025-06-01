const { Client, GatewayIntentBits } = require('discord.js');
const mongoose = require('mongoose');
const { EasyOCR } = require('node-easyocr');
const express = require('express');
require('dotenv').config();

const imageDropHandler = require('./handlers/imageDropHandler');
const embedHandlers = require('./handlers/embedHandlers');
const commandHandlers = require('./handlers/commandHandlers');
const messageUpdateHandler = require('./handlers/messageUpdateHandler');
const importCharacters = require('./utils/importCharacters');

const KARUTA_ID = '646937666251915264';

// Khởi tạo EasyOCR
const ocr = new EasyOCR();

// Khởi tạo Discord client
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers
    ]
});

const pendingLookups = new Map();
const pendingSchedules = new Map();

// Lưu trạng thái embed hiện đang xử lý theo channel
const currentProcessing = {
    lookup: new Map(),
    schedule: new Map()
};

let botStartTime = null;

// EXPRESS SERVER - để giữ bot luôn hoạt động
const app = express();
const PORT = process.env.PORT || 9704;

app.get('/', (req, res) => {
    res.send('🤖 Wishlist Bot is running!');
});

app.listen(PORT, () => {
    console.log(`🌐 Express server is listening on port ${PORT}`);
});

// Khi bot Discord sẵn sàng
client.once('ready', async () => {
    console.log(`🤖 Bot online as ${client.user.tag}`);
    botStartTime = new Date();
    await mongoose.connect(process.env.MONGO_URI);
    console.log('✅ Connected to MongoDB');
    await importCharacters();
    try {
        await ocr.init(['en']);
        console.log('✅ EasyOCR initialized');
    } catch (error) {
        console.error('❌ Failed to initialize EasyOCR:', error.message);
        process.exit(1);
    }
});

client.on('messageCreate', async (message) => {
    if (message.author.bot && message.author.id === KARUTA_ID) {
        if (message.createdTimestamp > botStartTime.getTime()) {
            await imageDropHandler(message, ocr);
            await embedHandlers(message, currentProcessing, pendingLookups, pendingSchedules);
        }
    } else {
        commandHandlers(message, pendingLookups, pendingSchedules);
    }
});

client.on('messageUpdate', async (oldMessage, newMessage) => {
    if (newMessage.createdTimestamp > botStartTime.getTime()) {
        await messageUpdateHandler(newMessage, currentProcessing);
    }
});

process.on('SIGINT', async () => {
    try {
        await ocr.close();
        console.log('✅ EasyOCR closed');
    } catch (error) {
        console.error('❌ Error closing EasyOCR:', error.message);
    }
    process.exit();
});

client.login(process.env.BOT_TOKEN);
