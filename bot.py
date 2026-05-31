import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel is None:
        return

    joined = before.channel is None and after.channel is not None
    left = before.channel is not None and after.channel is None
    switched = (
        before.channel is not None
        and after.channel is not None
        and before.channel != after.channel
    )

    if joined:
        await log_channel.send(
            f"👋 Welcome **{member.display_name}** joined **{after.channel.name}**!"
        )
    elif left:
        await log_channel.send(
            f"👋 Bye **{member.display_name}** left **{before.channel.name}**!"
        )
    elif switched:
        await log_channel.send(
            f"🔀 **{member.display_name}** moved from **{before.channel.name}** to **{after.channel.name}**."
        )


bot.run(TOKEN)
