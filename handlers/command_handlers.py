from datetime import datetime

async def handle_commands(message, pending_lookups, pending_schedules):
    if message.author.bot:
        return

    content_lower = message.content.lower()
    key = f'{message.channel.id}-{message.author.id}'

    if content_lower.startswith(('klu', 'k!lookup')):
        if not message.author.permissions_in(message.channel).create_instant_invite:
            return
        pending_lookups[key] = datetime.utcnow()
        bot.loop.call_later(15, lambda: pending_lookups.pop(key, None))

    elif content_lower.startswith(('kschedule', 'k!schedule')):
        if not message.author.permissions_in(message.channel).create_instant_invite:
            return
        pending_schedules[key] = datetime.utcnow()
        bot.loop.call_later(15, lambda: pending_schedules.pop(key, None))