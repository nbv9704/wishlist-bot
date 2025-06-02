import os

async def import_characters(db):
    file_path = os.path.join(os.path.dirname(__file__), '../characters.txt')
    if not os.path.exists(file_path):
        print('⚠️ File characters.txt does not exist')
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip().rstrip(',') for line in f if line.strip()]

    inserted, updated = 0, 0

    for line in lines:
        parts = [part.strip() for part in line.split('·')]
        if len(parts) != 3:
            print(f'❌ Invalid line: {line}')
            continue

        wishlist_str = parts[0].replace('♡', '').replace(',', '').strip()
        wishlist = int(wishlist_str)
        series = parts[1]
        character = parts[2]

        if not character or not series or not wishlist:
            print(f'⚠️ Missing or invalid data: {line}')
            continue

        existing = db.characters.find_one({'character': character, 'series': series})
        if existing:
            if existing['wishlist'] != wishlist:
                db.characters.update_one(
                    {'character': character, 'series': series},
                    {'$set': {'wishlist': wishlist, 'last_updated': datetime.utcnow()}}
                )
                print(f'🔁 Updated wishlist: {character} ({series})')
                updated += 1
            else:
                print(f'✔️ Already exists, no update needed: {character} ({series})')
        else:
            db.characters.insert_one({
                'character': character,
                'series': series,
                'wishlist': wishlist,
                'last_updated': datetime.utcnow()
            })
            print(f'✅ Successfully added: {character} ({series})')
            inserted += 1

    print(f'🎉 Import completed: {inserted} added, {updated} updated')