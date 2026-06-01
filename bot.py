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
LOCAL_KEY      = os.getenv("TUYA_LOCAL_KEY")
REGION         = os.getenv("TUYA_REGION", "eu")       # us / eu / cn / in
ACCESS_ID      = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET  = os.getenv("TUYA_ACCESS_SECRET")

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ── Light helpers (Tuya Cloud — works from Railway) ───────────────────────────

def _get_cloud():
    return tinytuya.Cloud(
        apiRegion=REGION,
        apiKey=ACCESS_ID,
        apiSecret=ACCESS_SECRET,
        apiDeviceID=DEVICE_ID,
    )


def _light_on():
    try:
        cloud = _get_cloud()
        cloud.sendcommand(DEVICE_ID, [{"code": "switch_led", "value": True}])
        print("💡 Light ON")
    except Exception as e:
        print(f"⚠️  Light ON failed: {e}")


def _light_off():
    try:
        cloud = _get_cloud()
        cloud.sendcommand(DEVICE_ID, [{"code": "switch_led", "value": False}])
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

    joined = before.channel is None and after.channel is not None
    left   = before.channel is not None and after.channel is None
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
        if not anyone_in_voice():
            await light_off()
            await log_channel.send("💡 No one left in voice — light turned off.")

    elif switched:
        await log_channel.send(
            f"🔀 **{member.display_name}** moved from **{before.channel.name}** to **{after.channel.name}**."
        )


bot.run(TOKEN)
