import discord
import asyncio
import random
import string
import os
import aiohttp
from discord.ext import tasks

TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))
DELAY_SECONDS = float(os.environ.get("DELAY_SECONDS", "3"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

CHARS = string.ascii_lowercase + string.digits
generated = set()

def random_name() -> str:
    while True:
        name = "".join(random.choices(CHARS, k=3))
        if name not in generated:
            generated.add(name)
            return name

async def check_discord_available(name: str) -> bool:
    url = f"https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    payload = {"username": name}
    headers = {"Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
                data = await r.json()
                return data.get("taken") == False
    except:
        return False

@tasks.loop(seconds=DELAY_SECONDS)
async def generate_and_post():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return

    name = random_name()
    available = await check_discord_available(name)

    if available:
        embed = discord.Embed(
            description=f"**`{name}`** is available ✅",
            color=0x57F287,
        )
        embed.set_footer(text=f"Checked: {len(generated)}")
        await channel.send(embed=embed)
        print(f"[✓] Available: {name}")
    else:
        print(f"[✗] Taken: {name}")

@client.event
async def on_ready():
    print(f"[BOT] Online as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(embed=discord.Embed(
            title="🔍 Username Checker iniciado",
            description="Buscando usernames de 4 caracteres disponibles...",
            color=0x5865F2,
        ))
    generate_and_post.start()

client.run(TOKEN)
