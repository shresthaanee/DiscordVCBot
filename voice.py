from light import light_on, light_off


def anyone_in_voice(bot):
    """Return True if at least one human is in any voice channel."""
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            if any(not m.bot for m in vc.members):
                return True
    return False


def find_member_in_voice(bot, user_id: int):
    """Find a member by ID across all voice channels."""
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for member in vc.members:
                if member.id == user_id:
                    return member
    return None


def setup(bot, log_channel_id: int):

    @bot.event
    async def on_voice_state_update(member, before, after):
        if member.bot:
            return

        log_channel = bot.get_channel(log_channel_id)
        if log_channel is None:
            return

        joined   = before.channel is None and after.channel is not None
        left     = before.channel is not None and after.channel is None
        switched = (
            before.channel is not None
            and after.channel is not None
            and before.channel != after.channel
        )

        if joined:
            await log_channel.send(
                f"👋 Welcome **{member.display_name}** joined **{after.channel.name}**!"
            )
            await light_on()

        elif left:
            await log_channel.send(
                f"👋 Bye **{member.display_name}** left **{before.channel.name}**!"
            )
            if not anyone_in_voice(bot):
                await light_off()
                await log_channel.send("💡 No one left in voice — light turned off.")

        elif switched:
            await log_channel.send(
                f"🔀 **{member.display_name}** moved from **{before.channel.name}** to **{after.channel.name}**."
            )
