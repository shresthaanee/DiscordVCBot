import discord
from discord.ext import commands
import os
import asyncio
import tinytuya
from dotenv import load_dotenv

load_dotenv()

TOKEN          = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
DEVICE_ID      = os.getenv("TUYA_DEVICE_ID")
DEVICE_IP      = os.getenv("TUYA_DEVICE_IP")
LOCAL_KEY      = os.getenv("TUYA_LOCAL_KEY")
DEVICE_VERSION = os.getenv("TUYA_VERSION", "3.3")

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ── Light helpers ─────────────────────────────────────────────────────────────

def _light_on():
    try:
        d = tinytuya.BulbDevice(
            dev_id=DEVICE_ID,
            address=DEVICE_IP,
            local_key=LOCAL_KEY,
            version=float(DEVICE_VERSION),
        )
        d.set_socketTimeout(5)
        d.turn_on()
        print("💡 Light ON")
    except Exception as e:
        print(f"⚠️  Light ON failed: {e}")


def _light_off():
    try:
        d = tinytuya.BulbDevice(
            dev_id=DEVICE_ID,
            address=DEVICE_IP,
            local_key=LOCAL_KEY,
            version=float(DEVICE_VERSION),
        )
        d.set_socketTimeout(5)
        d.turn_off()
        print("🌑 Light OFF")
    except Exception as e:
        print(f"⚠️  Light OFF failed: {e}")


async def light_on():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _light_on)


async def light_off():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _light_off)


def anyone_in_voice():
    """Return True if at least one human is in any voice channel."""
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            if any(not m.bot for m in vc.members):
                return True
    return False


# ── Bot events ────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return  # ignore other bots

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
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
        # Turn light off only when voice channel is completely empty
        if not anyone_in_voice():
            await light_off()
            await log_channel.send("💡 No one left in voice — light turned off.")

    elif switched:
        await log_channel.send(
            f"🔀 **{member.display_name}** moved from **{before.channel.name}** to **{after.channel.name}**."
        )


bot.run(TOKEN)
