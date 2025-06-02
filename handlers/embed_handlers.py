const Character = require('../models/Character');

module.exports = async (message, currentProcessing, pendingLookups, pendingSchedules) => {
    const keyPrefix = `${message.channel.id}-`;
    const now = Date.now();

    const validLookups = [...pendingLookups.entries()]
        .filter(([key, time]) => key.startsWith(keyPrefix) && (now - time < 10000));
    const validSchedules = [...pendingSchedules.entries()]
        .filter(([key, time]) => key.startsWith(keyPrefix) && (now - time < 10000));

    if (validLookups.length === 0 && validSchedules.length === 0) return;
    if (message.embeds.length === 0) return;

    if (message.embeds[0].title === 'Character Results' && validLookups.length > 0) {
        const embed = message.embeds[0];
        if (!embed.fields || embed.fields.length === 0) return;

        const rawText = embed.fields[0].value;
        const allLines = rawText.split('\n');

        const channelId = message.channel.id;
        const embedMsgId = message.id;

        currentProcessing.lookup.set(channelId, { embedMessageId: embedMsgId, reportMessageId: null });

        let updated = 0, inserted = 0;
        for (const line of allLines) {
            const match = line.match(/`(\d+)`\.\s+`♡(\d+)`\s+·\s+(.*?)\s+·\s+\*\*(.+?)\*\*/);
            if (!match) continue;
            const [, , wishlistStr, series, character] = match;
            const wishlist = parseInt(wishlistStr);
            const nowDate = new Date();

            const existing = await Character.findOne({ series, character });
            if (!existing) {
                await Character.create({ series, character, wishlist, lastUpdated: nowDate });
                inserted++;
            } else if (existing.wishlist !== wishlist) {
                existing.wishlist = wishlist;
                existing.lastUpdated = nowDate;
                await existing.save();
                updated++;
            }
        }

        let reportMsgId = currentProcessing.lookup.get(channelId).reportMessageId;
        let reportMsg = null;
        if (reportMsgId) {
            reportMsg = await message.channel.messages.fetch(reportMsgId).catch(() => null);
        }
        if (!reportMsg) {
            reportMsg = await message.channel.send('⏳ Character data is loading...');
            currentProcessing.lookup.set(channelId, { embedMessageId: embedMsgId, reportMessageId: reportMsg.id });
        }

        await reportMsg.edit(`✅ Data imported successfully: ${inserted} new, ${updated} updated`);
    } else if (message.embeds[0].title === 'Character Lookup') {
        const embed = message.embeds[0];
        if (!embed.description) return;

        const lines = embed.description.split('\n').map(l => l.trim()).filter(l => l);
        let characterData = {};

        for (const line of lines) {
            const parts = line.split('·').map(p => p.trim());
            if (parts.length === 2) {
                const key = parts[0];
                let value = parts[1];
                value = value.replace(/^\*\*(.+)\*\*$/, '$1');

                if (['Character', 'Series', 'Wishlisted'].includes(key)) {
                    characterData[key.toLowerCase()] = value;
                }
            }
        }

        if (!characterData.character || !characterData.series || !characterData.wishlisted) return;

        const wishlistNum = parseInt(characterData.wishlisted.replace(/,/g, ''));
        if (isNaN(wishlistNum)) return;

        const nowDate = new Date();

        const existing = await Character.findOne({ series: characterData.series, character: characterData.character });
        if (!existing) {
            await Character.create({
                series: characterData.series,
                character: characterData.character,
                wishlist: wishlistNum,
                lastUpdated: nowDate
            });
            await message.channel.send(`✅ Successfully added new data for **${characterData.character}** (${characterData.series})`);
        } else {
            if (existing.wishlist !== wishlistNum) {
                existing.wishlist = wishlistNum;
                existing.lastUpdated = nowDate;
                await existing.save();
                await message.channel.send(`✅ Successfully updated wishlist for **${characterData.character}** (${characterData.series})`);
            }
        }
    } else if (message.embeds[0].title === 'Card Release Schedule' && validSchedules.length > 0) {
        const embed = message.embeds[0];
        if (!embed.description) return;

        const lines = embed.description.split('\n').map(l => l.trim()).filter(l => l);
        let inserted = 0, updated = 0;

        for (const line of lines) {
            const parts = line.split('·').map(p => p.trim());
            if (parts.length < 5) continue;

            const wishlistStr = parts[0].replace(/[^0-9]/g, '');
            const wishlist = parseInt(wishlistStr);

            const characterMatch = parts[3].match(/^\*\*(.+)\*\*$/);
            const character = characterMatch ? characterMatch[1] : parts[3];
            const series = parts[4];

            if (!character || !series || isNaN(wishlist)) continue;

            const nowDate = new Date();

            const existing = await Character.findOne({ character, series });
            if (!existing) {
                await Character.create({ character, series, wishlist, lastUpdated: nowDate });
                inserted++;
            } else if (existing.wishlist !== wishlist) {
                existing.wishlist = wishlist;
                existing.lastUpdated = nowDate;
                await existing.save();
                updated++;
            }
        }

        const channelId = message.channel.id;
        const embedMsgId = message.id;
        currentProcessing.schedule.set(channelId, { embedMessageId: embedMsgId, reportMessageId: null });

        let reportMsgId = currentProcessing.schedule.get(channelId).reportMessageId;
        let reportMsg = null;
        if (reportMsgId) {
            reportMsg = await message.channel.messages.fetch(reportMsgId).catch(() => null);
        }
        if (!reportMsg) {
            reportMsg = await message.channel.send('⏳ Schedule data is loading...');
            currentProcessing.schedule.set(channelId, { embedMessageId: embedMsgId, reportMessageId: reportMsg.id });
        }

        await reportMsg.edit(`✅ Data imported successfully: ${inserted} new, ${updated} updated`);
    }
};