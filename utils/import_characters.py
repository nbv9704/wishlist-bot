const fs = require('fs');
const path = require('path');
const Character = require('../models/Character');

module.exports = async () => {
    const filePath = path.join(__dirname, '../characters.txt');
    if (!fs.existsSync(filePath)) {
        console.error('⚠️ File characters.txt does not exist');
        return;
    }

    const lines = fs.readFileSync(filePath, 'utf-8')
        .split('\n')
        .map(line => line.trim().replace(/,+$/, ''))
        .filter(line => line);

    let inserted = 0, updated = 0;

    for (const line of lines) {
        const parts = line.split('·').map(part => part.trim());
        if (parts.length !== 3) {
            console.warn(`❌ Invalid line: ${line}`);
            continue;
        }

        const wishlistStr = parts[0].replace(/^♡/, '').replace(/,/g, '').trim();
        const wishlist = parseInt(wishlistStr);
        const series = parts[1];
        const character = parts[2];

        if (!character || !series || isNaN(wishlist)) {
            console.warn(`⚠️ Missing or invalid data: ${line}`);
            continue;
        }

        const existing = await Character.findOne({ character, series });
        if (existing) {
            if (existing.wishlist !== wishlist) {
                existing.wishlist = wishlist;
                await existing.save();
                console.log(`🔁 Updated wishlist: ${character} (${series})`);
                updated++;
            } else {
                console.log(`✔️ Already exists, no update needed: ${character} (${series})`);
            }
        } else {
            await Character.create({ character, series, wishlist });
            console.log(`✅ Successfully added: ${character} (${series})`);
            inserted++;
        }
    }

    console.log(`🎉 Import completed: ${inserted} added, ${updated} updated`);
};