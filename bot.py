import discord
from discord.ext import commands
from aiohttp import web
import os
import asyncio
import tinytuya
from dotenv import load_dotenv

load_dotenv()

TOKEN          = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
DEVICE_ID      = os.getenv("TUYA_DEVICE_ID")
LOCAL_KEY      = os.getenv("TUYA_LOCAL_KEY")
REGION         = os.getenv("TUYA_REGION", "eu")
ACCESS_ID      = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET  = os.getenv("TUYA_ACCESS_SECRET")
API_SECRET     = os.getenv("API_SECRET", "changeme")   # secret token to protect your endpoints
PORT           = int(os.getenv("PORT", 8080))

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ── Light helpers ─────────────────────────────────────────────────────────────

def _get_cloud():
    return tinytuya.Cloud(
        apiRegion=REGION,
        apiKey=ACCESS_ID,
        apiSecret=ACCESS_SECRET,
        apiDeviceID=DEVICE_ID,
    )

def _light_on():
    try:
        _get_cloud().sendcommand(DEVICE_ID, [{"code": "switch_led", "value": True}])
        print("💡 Light ON")
    except Exception as e:
        print(f"⚠️  Light ON failed: {e}")

def _light_off():
    try:
        _get_cloud().sendcommand(DEVICE_ID, [{"code": "switch_led", "value": False}])
        print("🌑 Light OFF")
    except Exception as e:
        print(f"⚠️  Light OFF failed: {e}")

async def light_on():
    await asyncio.get_event_loop().run_in_executor(None, _light_on)

async def light_off():
    await asyncio.get_event_loop().run_in_executor(None, _light_off)

def anyone_in_voice():
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            if any(not m.bot for m in vc.members):
                return True
    return False


# ── Helper — find member in any voice channel ─────────────────────────────────

def find_member_in_voice(user_id: int):
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for member in vc.members:
                if member.id == user_id:
                    return member
    return None


# ── Web API (called by phone widget) ─────────────────────────────────────────

def check_auth(request):
    return request.headers.get("X-Secret") == API_SECRET

async def handle_mute(request):
    if not check_auth(request):
        return web.Response(status=401, text="Unauthorized")
    data    = await request.json()
    user_id = int(data.get("user_id", 0))
    mute    = data.get("mute", True)          # true = mute, false = unmute
    member  = find_member_in_voice(user_id)
    if member is None:
        return web.Response(status=404, text="User not in voice")
    await member.edit(mute=mute)
    action = "muted" if mute else "unmuted"
    print(f"🔇 {member.display_name} {action} via widget")
    return web.Response(text=f"{member.display_name} {action}")

async def handle_light(request):
    if not check_auth(request):
        return web.Response(status=401, text="Unauthorized")
    data   = await request.json()
    action = data.get("action", "on")
    if action == "on":
        await light_on()
    else:
        await light_off()
    return web.Response(text=f"Light {action}")

async def handle_vcwho(request):
    if not check_auth(request):
        return web.Response(status=401, text="Unauthorized")
    result = []
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            members = [m.display_name for m in vc.members if not m.bot]
            if members:
                result.append(f"{vc.name}: {', '.join(members)}")
    text = "\n".join(result) if result else "Nobody in voice"
    return web.Response(text=text)

async def start_web_server():
    app = web.Application()
    app.router.add_post("/mute",  handle_mute)
    app.router.add_post("/light", handle_light)
    app.router.add_get("/vcwho",  handle_vcwho)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🌐 Web API running on port {PORT}")


# ── Bot events ────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await start_web_server()


@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

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
        if not anyone_in_voice():
            await light_off()
            await log_channel.send("💡 No one left in voice — light turned off.")

    elif switched:
        await log_channel.send(
            f"🔀 **{member.display_name}** moved from **{before.channel.name}** to **{after.channel.name}**."
        )


bot.run(TOKEN)
