const { PermissionsBitField } = require('discord.js');

module.exports = (message, pendingLookups, pendingSchedules) => {
    if (message.author.bot) return;

    const contentLower = message.content.toLowerCase();
    if (contentLower.startsWith('klu') || contentLower.startsWith('k!lookup')) {
        const member = message.member ?? message.guild.members.fetch(message.author.id);
        if (!member.permissions.has(PermissionsBitField.Flags.CreateInstantInvite)) return;

        const key = `${message.channel.id}-${message.author.id}`;
        pendingLookups.set(key, Date.now());
        setTimeout(() => pendingLookups.delete(key), 15000);
    } else if (contentLower.startsWith('kschedule') || contentLower.startsWith('k!schedule')) {
        const member = message.member ?? message.guild.members.fetch(message.author.id);
        if (!member.permissions.has(PermissionsBitField.Flags.CreateInstantInvite)) return;

        const key = `${message.channel.id}-${message.author.id}`;
        pendingSchedules.set(key, Date.now());
        setTimeout(() => pendingSchedules.delete(key), 15000);
    }
};