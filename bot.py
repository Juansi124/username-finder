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

def random_name(length=4) -> str:
    while True:
        name = "".join(random.choices(CHARS, k=length))
        if name not in generated:
            generated.add(name)
            return name

async def check_one(name: str) -> bool:
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    try:
        async with session.post(url, json={"username": name}, timeout=aiohttp.ClientTimeout(total=8)) as r:
            if r.status == 429:
                retry_after = float(r.headers.get("Retry-After", 5))
                print(f"[!] Rate limited. Esperando {retry_after}s...")
                await asyncio.sleep(retry_after)
                return False
            if r.status != 200:
                return False
            data = await r.json()
            return data.get("taken") == False
    except Exception as e:
        print(f"[ERR] {name}: {e}")
        return False

async def check_batch(batch_size=20):
    names = [random_name() for _ in range(batch_size)]
    results = await asyncio.gather(*[check_one(n) for n in names])
    return list(zip(names, results))

@tasks.loop(seconds=2)
async def generate_and_post():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return

    results = await check_batch(batch_size=20)
    available_found = []

    for name, available in results:
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
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(embed=discord.Embed(
            title="🔍 Username Checker iniciado",
            description="Chequeando **20 nombres por ciclo** cada 2 segundos 🚀",
            color=0x5865F2,
        ))
    generate_and_post.start()

@client.event
async def on_disconnect():
    if session:
        await session.close()

client.run(TOKEN)
