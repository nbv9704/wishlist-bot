import discord
import re
from datetime import datetime

async def handle_embeds(message, current_processing, pending_lookups, pending_schedules, db):
    key_prefix = f'{message.channel.id}-'
    now = datetime.utcnow()

    valid_lookups = {k: t for k, t in pending_lookups.items() if k.startswith(key_prefix) and (now - t).total_seconds() < 10}
    valid_schedules = {k: t for k, t in pending_schedules.items() if k.startswith(key_prefix) and (now - t).total_seconds() < 10}

    if not valid_lookups and not valid_schedules:
        print("No valid lookups or schedules, skipping embed handling")
        return
    if not message.embeds:
        print("No embeds found in message")
        return

    embed = message.embeds[0]
    channel_id = str(message.channel.id)

    if embed.title == 'Character Results' and valid_lookups and embed.fields:
        print("Processing 'Character Results' embed")
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
                print(f"Inserted new character: {character} ({series})")
            elif existing['wishlist'] != wishlist:
                db.characters.update_one(
                    {'series': series, 'character': character},
                    {'$set': {'wishlist': wishlist, 'last_updated': now}}
                )
                updated += 1
                print(f"Updated character: {character} ({series})")

        current_processing['lookup'][channel_id] = {
            'embed_message_id': str(message.id),
            'report_message_id': current_processing['lookup'].get(channel_id, {}).get('report_message_id')
        }

        report_msg_id = current_processing['lookup'][channel_id].get('report_message_id')
        report_msg = None
        if report_msg_id:
            try:
                report_msg = await message.channel.fetch_message(report_msg_id)
            except:
                pass
        if not report_msg:
            report_msg = await message.channel.send('⏳ Character data is loading...')
            current_processing['lookup'][channel_id]['report_message_id'] = str(report_msg.id)

        await report_msg.edit(content=f'✅ Data imported successfully: {inserted} new, {updated} updated')
        print(f"Updated report message: {inserted} new, {updated} updated")

    elif embed.title == 'Character Lookup' and embed.description:
        print("Processing 'Character Lookup' embed")
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
            print("Incomplete character data in 'Character Lookup'")
            return

        wishlist_num = int(character_data['wishlisted'].replace(',', ''))
        if not wishlist_num:
            print("Invalid wishlist number in 'Character Lookup'")
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
            await message.channel.send(f"✅ Successfully added new data for **{character_data['character']}** ({character_data['series']})")
            print(f"Added new character: {character_data['character']} ({character_data['series']})")
        elif existing['wishlist'] != wishlist_num:
            db.characters.update_one(
                {'series': character_data['series'], 'character': character_data['character']},
                {'$set': {'wishlist': wishlist_num, 'last_updated': now}}
            )
            await message.channel.send(f"✅ Successfully updated wishlist for **{character_data['character']}** ({character_data['series']})")
            print(f"Updated wishlist for character: {character_data['character']} ({character_data['series']})")

    elif embed.title == 'Card Release Schedule' and valid_schedules and embed.description:
        print("Processing 'Card Release Schedule' embed")
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
                print(f"Inserted new character from schedule: {character} ({series})")
            elif existing['wishlist'] != wishlist:
                db.characters.update_one(
                    {'character': character, 'series': series},
                    {'$set': {'wishlist': wishlist, 'last_updated': now}}
                )
                updated += 1
                print(f"Updated character from schedule: {character} ({series})")

        current_processing['schedule'][channel_id] = {
            'embed_message_id': str(message.id),
            'report_message_id': current_processing['schedule'].get(channel_id, {}).get('report_message_id')
        }

        report_msg_id = current_processing['schedule'][channel_id].get('report_message_id')
        report_msg = None
        if report_msg_id:
            try:
                report_msg = await message.channel.fetch_message(report_msg_id)
            except:
                pass
        if not report_msg:
            report_msg = await message.channel.send('⏳ Schedule data is loading...')
            current_processing['schedule'][channel_id]['report_message_id'] = str(report_msg.id)

        await report_msg.edit(content=f'✅ Data imported successfully: {inserted} new, {updated} updated')
        print(f"Updated schedule report message: {inserted} new, {updated} updated")