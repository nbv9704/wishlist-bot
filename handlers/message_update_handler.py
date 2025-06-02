import discord
import re
from datetime import datetime

KARUTA_ID = 646937666251915264

async def handle_message_update(new_message, current_processing, db):
    if not (new_message.author.bot and new_message.author.id == KARUTA_ID):
        return
    if not new_message.embeds:
        return
    embed = new_message.embeds[0]
    if embed.title not in ['Character Results', 'Character Lookup', 'Card Release Schedule']:
        return

    channel_id = str(new_message.channel.id)
    now = datetime.utcnow()

    if embed.title == 'Character Results' and embed.fields:
        state = current_processing['lookup'].get(channel_id, {})
        if not state or state.get('embed_message_id') != str(new_message.id):
            return

        raw_text = embed.fields[0].value
        all_lines = raw_text.split('\n')
        inserted, updated = 0, 0

        for line in all_lines:
            match = re.match(r'`\d+`.\s+`♡(\d+)`\s+·\s+(.+?)\s+·\s+\*\*(.+?)\*\*', line)
            if not match:
                continue
            wishlist = int(match.group(1))
            series = match.group(2)
            character = match.group(3)

            existing = db.characters.find_one({'series': series, 'character': character})
            if not existing:
                db.characters.insert_one({
                    'series': series,
                    'character': character,
                    'wishlist': wishlist,
                    'last_updated': now
                })
                inserted += 1
            elif existing['wishlist'] != wishlist:
                db.characters.update_one(
                    {'series': series, 'character': character},
                    {'$set': {'wishlist': wishlist, 'last_updated': now}}
                )
                updated += 1

        if inserted or updated:
            report_msg_id = state.get('report_message_id')
            report_msg = None
            if report_msg_id:
                try:
                    report_msg = await new_message.channel.fetch_message(report_msg_id)
                except:
                    pass
            if not report_msg:
                report_msg = await new_message.channel.send('⏳ Character data is loading...')
                current_processing['lookup'][channel_id] = {
                    'embed_message_id': str(new_message.id),
                    'report_message_id': str(report_msg.id)
                }
            await report_msg.edit(content=f'✅ Data imported successfully: {inserted} new, {updated} updated')

    elif embed.title == 'Character Lookup' and embed.description:
        lines = [line.strip() for line in embed.description.split('\n') if line.strip()]
        character_data = {}

        for line in lines:
            parts = [p.strip() for p in line.split('·')]
            if len(parts) == 2:
                key, value = parts
                value = re.sub(r'^\*\*(.+)\*\*$', r'\1', value)
                if key in ['Character', 'Series', 'Wishlisted']:
                    character_data[key.lower()] = value

        if not all(k in character_data for k in ['character', 'series', 'wishlisted']):
            return

        wishlist_num = int(character_data['wishlisted'].replace(',', ''))
        if not wishlist_num:
            return

        existing = db.characters.find_one({
            'series': character_data['series'],
            'character': character_data['character']
        })
        if not existing:
            db.characters.insert_one({
                'series': character_data['series'],
                'character': character_data['character'],
                'wishlist': wishlist_num,
                'last_updated': now
            })
        elif existing['wishlist'] != wishlist_num:
            db.characters.update_one(
                {'series': character_data['series'], 'character': character_data['character']},
                {'$set': {'wishlist': wishlist_num, 'last_updated': now}}
            )

    elif embed.title == 'Card Release Schedule' and embed.description:
        state = current_processing['schedule'].get(channel_id, {})
        if not state or state.get('embed_message_id') != str(new_message.id):
            return

        lines = [line.strip() for line in embed.description.split('\n') if line.strip()]
        inserted, updated = 0, 0

        for line in lines:
            parts = [p.strip() for p in line.split('·')]
            if len(parts) < 5:
                continue

            wishlist = int(parts[0].replace(',', ''))
            character_match = re.match(r'^\*\*(.+)\*\*$', parts[3])
            character = character_match.group(1) if character_match else parts[3]
            series = parts[4]

            if not character or not series or not wishlist:
                continue

            existing = db.characters.find_one({'character': character, 'series': series})
            if not existing:
                db.characters.insert_one({
                    'character': character,
                    'series': series,
                    'wishlist': wishlist,
                    'last_updated': now
                })
                inserted += 1
            elif existing['wishlist'] != wishlist:
                db.characters.update_one(
                    {'character': character, 'series': series},
                    {'$set': {'wishlist': wishlist, 'last_updated': now}}
                )
                updated += 1

        if inserted or updated:
            report_msg_id = state.get('report_message_id')
            report_msg = None
            if report_msg_id:
                try:
                    report_msg = await new_message.channel.fetch_message(report_msg_id)
                except:
                    pass
            if not report_msg:
                report_msg = await new_message.channel.send('⏳ Schedule data is loading...')
                current_processing['schedule'][channel_id] = {
                    'embed_message_id': str(new_message.id),
                    'report_message_id': str(report_msg.id)
                }
            await report_msg.edit(content=f'✅ Data imported successfully: {inserted} new, {updated} updated')