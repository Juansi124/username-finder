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

def random_name() -> str:
    while True:
        name = "".join(random.choices(CHARS, k=4))
        if name not in generated:
            generated.add(name)
            return name

async def check_once(session, name) -> bool | None:
    """
    Retorna:
      True  → disponible
      False → tomado
      None  → error/rate limit (no contar como tomado)
    """
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    try:
        async with session.post(
            url,
            json={"username": name},
            headers={"Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=8)
        ) as r:
            if r.status == 429:
                retry_after = float(r.headers.get("Retry-After", "5"))
                print(f"[!] Rate limit — esperando {retry_after}s")
                await asyncio.sleep(retry_after)
                return None
            if r.status != 200:
                return None
            data = await r.json()
            taken = data.get("taken")
            if taken is None:
                return None
            return not taken
    except Exception as e:
        print(f"[!] Error: {e}")
        return None

async def is_available(name: str) -> bool:
    """Verifica dos veces — solo publica si ambas dicen disponible."""
    async with aiohttp.ClientSession() as session:
        first = await check_once(session, name)
        if first is not True:
            return False
        # Segunda verificación con pausa
        await asyncio.sleep(2)
        second = await check_once(session, name)
        return second is True

@tasks.loop(seconds=4)
async def generate_and_post():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return

    name = random_name()
    available = await is_available(name)

    if available:
        embed = discord.Embed(
            description=f"**`{name}`** is available ✅",
            color=0x57F287,
        )
        embed.set_footer(text=f"Checked: {len(generated)}")
        await channel.send(embed=embed)
        print(f"[✓] AVAILABLE: {name} | checked={len(generated)}")
    else:
        print(f"[✗] taken: {name} | checked={len(generated)}", end="\r")

@client.event
async def on_ready():
    print(f"[BOT] Online as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(embed=discord.Embed(
            title="🔍 Username Checker iniciado",
            description="4c/4l iniciado",
            color=0x5865F2,
        ))
    generate_and_post.start()

client.run(TOKEN)
