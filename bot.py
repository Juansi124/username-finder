import discord
import asyncio
import random
import string
import os
import aiohttp
from discord.ext import tasks

TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

CHARS = string.ascii_lowercase + string.digits
generated = set()
session: aiohttp.ClientSession = None

def random_name() -> str:
    while True:
        name = "".join(random.choices(CHARS, k=4))
        if name not in generated:
            generated.add(name)
            return name

async def check_one(name: str) -> bool | None:
    """
    Retorna True = disponible, False = tomado, None = rate limited
    """
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    try:
        async with session.post(
            url,
            json={"username": name},
            timeout=aiohttp.ClientTimeout(total=10)
        ) as r:
            if r.status == 429:
                retry_after = float(r.headers.get("Retry-After", 60))
                print(f"[!] Rate limit: esperando {retry_after}s")
                await asyncio.sleep(retry_after)
                return None
            if r.status != 200:
                return False
            data = await r.json()
            return data.get("taken") == False
    except Exception as e:
        print(f"[ERR] {e}")
        return False

@tasks.loop(seconds=20)
async def finder_loop():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    # Checkeamos de a 1 por vez con pausa entre requests
    for _ in range(
