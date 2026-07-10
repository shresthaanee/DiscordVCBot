import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import voice
import api

load_dotenv()

TOKEN          = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
API_SECRET     = os.getenv("API_SECRET", "changeme")
PORT           = int(os.getenv("PORT", 8080))

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Register voice events and web API
voice.setup(bot, LOG_CHANNEL_ID)
start_api = api.setup(bot, API_SECRET, PORT)


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await start_api()


bot.run(TOKEN)
