import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")  # Load from Railway secrets
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))  # Put your channel ID in Railway secrets

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def fetch_menu():
    url = "https://www.hasdhawks.org/o/hahs/dining"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Convert to plain text for searching
    text = soup.get_text(separator="\n")

    today = datetime.now().strftime("%A, %b %d").upper()
    # Example: "MONDAY, AUG 25"

    if today in text:
        start = text.find(today)
        next_day_index = min(
            [
                text.find(day, start + 1)
                for day in ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
                if text.find(day, start + 1) != -1
            ]
            or [len(text)]
        )
        menu = text[start:next_day_index].strip()
        return menu
    return "Menu not found for today."

@tasks.loop(hours=24)
async def send_menu():
    channel = bot.get_channel(CHANNEL_ID)
    menu = fetch_menu()
    await channel.send(f"📅 **Today's Menu**\n{menu}")

@send_menu.before_loop
async def before_send_menu():
    await bot.wait_until_ready()
    now = datetime.now()
    target_time = now.replace(hour=7, minute=0, second=0, microsecond=0)
    if now > target_time:
        from datetime import timedelta
        target_time = target_time + timedelta(days=1)
    await discord.utils.sleep_until(target_time)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    send_menu.start()

bot.run(TOKEN)
