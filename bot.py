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
rate_limited_until: float = 0

def random_name(length=4) -> str:
    while True:
        name = "".join(random.choices(CHARS, k=length))
        if name not in generated:
            generated.add(name)
            return name

async def check_one(name: str) -> bool:
    global rate_limited_until
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    try:
        async with session.post(url, json={"username": name}, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status == 429:
                retry_after = float(r.headers.get("Retry-After", 60))
                rate_limited_until = asyncio.get_event_loop().time() + retry_after
                print(f"[!] Rate limited. Pausando {retry_after}s...")
                return False
            if r.status != 200:
                return False
            data = await r.json()
            return data.get("taken") == False
    except Exception as e:
        print(f"[ERR] {name}: {e}")
        return False

@tasks.loop(seconds=15)  # Más lento para no quemar la IP
async def generate_and_post():
    global rate_limited_until
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return

    # Si estamos en rate limit, esperar
    now = asyncio.get_event_loop().time()
    if now < rate_limited_until:
        wait = int(rate_limited_until - now)
        print(f"[~] En rate limit, faltan {wait}s...")
        return

    names = [random_name() for _ in range(5)]  # Menos por ciclo, más sostenible
    results = await asyncio.gather(*[check_one(n) for n in names])

    available_found = []
    for name, available in zip(names, results):
        if available:
            available_found.append(name)
            print(f"[✓] DISPONIBLE: {name}")
        else:
            print(f"[✗] Tomado: {name}")

    if available_found:
        description = "\n".join([f"**`{n}`** ✅" for n in available_found])
        embed = discord.Embed(
            title="🎉 Usernames disponibles",
            description=description,
            color=0x57F287,
        )
        embed.set_footer(text=f"Total chequeados: {len(generated)}")
        await channel.send(embed=embed)

    print(f"[~] Total chequeados: {len(generated)}")

@client.event
async def on_ready():
    global session
    session = aiohttp.ClientSession()
    print(f"[BOT] Online as {client.user}")
    generate_and_post.start()

client.run(TOKEN)
