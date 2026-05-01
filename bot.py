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

async def check_one(session, name):
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    try:
        async with session.post(url, json={"username": name}, timeout=aiohttp.ClientTimeout(total=5)) as r:
            if r.status == 429:
                await asyncio.sleep(15)
                return False
            data = await r.json()
            return data.get("taken") == False
    except:
        return False

async def check_with_retry(session, name):
    first = await check_one(session, name)
    if first:
        await asyncio.sleep(1)
        second = await check_one(session, name)
        return second
    return False

@tasks.loop(seconds=3)
async def generate_and_post():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return

    names = [random_name() for _ in range(5)]
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[check_with_retry(session, n) for n in names])

    for name, available in zip(names, results):
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
            description="Chequeando 5 nombres a la vez cada 3s ✅",
            color=0x5865F2,
        ))
    generate_and_post.start()

client.run(TOKEN)
