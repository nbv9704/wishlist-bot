const Character = require('../models/Character');

const KARUTA_ID = '646937666251915264';

module.exports = async (newMessage, currentProcessing) => {
    if (!(newMessage.author?.bot && newMessage.author.id === KARUTA_ID)) return;
    if (!newMessage.embeds || newMessage.embeds.length === 0) return;
    if (!['Character Results', 'Character Lookup', 'Card Release Schedule'].includes(newMessage.embeds[0].title)) return;

    const embed = newMessage.embeds[0];
    const channel = newMessage.channel;

    if (embed.title === 'Character Results' && embed.fields && embed.fields.length > 0) {
        const state = currentProcessing.lookup.get(channel.id);
        if (!state || state.embedMessageId !== newMessage.id) return;

        const rawText = embed.fields[0].value;
        const allLines = rawText.split('\n');

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

        if (inserted || updated) {
            let reportMsg = null;
            if (state.reportMessageId) {
                reportMsg = await channel.messages.fetch(state.reportMessageId).catch(() => null);
            }
            if (!reportMsg) {
                reportMsg = await channel.send('⏳ Character data is loading...');
                currentProcessing.lookup.set(channel.id, { embedMessageId: newMessage.id, reportMessageId: reportMsg.id });
            }
            await reportMsg.edit(`✅ Data imported successfully: ${inserted} new, ${updated} updated`);
        }
    } else if (embed.title === 'Character Lookup' && embed.description) {
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
        } else {
            if (existing.wishlist !== wishlistNum) {
                existing.wishlist = wishlistNum;
                existing.lastUpdated = nowDate;
                await existing.save();
            }
        }
    } else if (embed.title === 'Card Release Schedule' && embed.description) {
        const state = currentProcessing.schedule.get(channel.id);
        if (!state || state.embedMessageId !== newMessage.id) return;

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

        if (inserted || updated) {
            let reportMsg = null;
            if (state.reportMessageId) {
                reportMsg = await channel.messages.fetch(state.reportMessageId).catch(() => null);
            }
            if (!reportMsg) {
                reportMsg = await channel.send('⏳ Schedule data is loading...');
                currentProcessing.schedule.set(channel.id, { embedMessageId: newMessage.id, reportMessageId: reportMsg.id });
            }
            await reportMsg.edit(`✅ Data imported successfully: ${inserted} new, ${updated} updated`);
        }
    }
};