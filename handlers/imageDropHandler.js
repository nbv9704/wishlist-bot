const { EmbedBuilder } = require('discord.js');
const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));
const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const tesseract = require('node-tesseract-ocr');
const Character = require('../models/Character');

module.exports = async (message) => {
    if (message.attachments.size > 0) {
        try {
            const tempDir = path.join(__dirname, '../temp');
            if (!fs.existsSync(tempDir)) {
                fs.mkdirSync(tempDir);
            }

            const attachment = message.attachments.first();
            const originalFilePath = path.join(tempDir, 'karuta_drop.png');

            const response = await fetch(attachment.url);
            const buffer = await response.buffer();
            fs.writeFileSync(originalFilePath, buffer);

            const crops = [
                { name: 'part1', left: 40, top: 60, width: 210, height: 50 },
                { name: 'part2', left: 310, top: 60, width: 205, height: 50 },
                { name: 'part3', left: 590, top: 60, width: 205, height: 50 }
            ];

            const resultsByPart = [];

            for (const crop of crops) {
                const cropFilePath = path.join(tempDir, `cropped_${crop.name}.png`);

                await sharp(originalFilePath)
                    .extract({ left: crop.left, top: crop.top, width: crop.width, height: crop.height })
                    .toFile(cropFilePath);

                const ocrData = await tesseract.recognize(cropFilePath, {
                    lang: 'eng',
                    oem: 3, // LSTM OCR engine
                    psm: 7 // Treat as a single text line
                });

                // Lọc bỏ các ký tự không mong muốn và xử lý văn bản
                const texts = ocrData
                    .split('\n')
                    .map(text => text.trim())
                    .filter(text => text && !/^\d{4,}$/.test(text))
                    .map(text => text.replace(/[)\»\|\}]/g, '')) // Loại bỏ ), », |, }
                    .filter(text => text); // Loại bỏ các chuỗi rỗng sau khi lọc

                resultsByPart.push(texts);

                fs.unlinkSync(cropFilePath);
            }

            fs.unlinkSync(originalFilePath);

            const lines = [];

            for (const texts of resultsByPart) {
                if (texts.length === 0) {
                    lines.push('None', '');
                    continue;
                }

                const character = texts.join(' ').trim(); // Gộp văn bản và loại bỏ khoảng trắng thừa

                // Tìm nhân vật với tên đã được làm sạch
                const results = await Character.find({ 
                    character: { $regex: `^${character}$`, $options: 'i' } // Tìm kiếm không phân biệt hoa thường
                });

                if (results.length > 0) {
                    for (const result of results) {
                        lines.push(`${character} (**${result.series}**): \`${result.wishlist} Wishlist\``);
                    }
                } else {
                    lines.push(`${character}: \`None\``);
                }
                lines.push('');
            }

            if (lines[lines.length - 1] === '') {
                lines.pop();
            }

            if (lines.length === 0) {
                console.log('⚠️ No valid characters found from OCR');
                return;
            }

            const embed = new EmbedBuilder()
                .setTitle('📊 Wishlist Stats')
                .setDescription(lines.join('\n'))
                .setColor('Blue');

            await message.channel.send({ embeds: [embed] });

        } catch (err) {
            console.error('❌ Error processing drop image:', err.stack);
            const tempDir = path.join(__dirname, '../temp');
            const originalFilePath = path.join(tempDir, 'karuta_drop.png');
            const cropFiles = ['part1', 'part2', 'part3'].map(name => path.join(tempDir, `cropped_${name}.png`));
            if (fs.existsSync(originalFilePath)) fs.unlinkSync(originalFilePath);
            cropFiles.forEach(file => {
                if (fs.existsSync(file)) fs.unlinkSync(file);
            });
        }
    }
};