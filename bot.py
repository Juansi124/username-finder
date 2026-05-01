import discord
import asyncio
import random
import string
import os
from discord.ext import tasks

# ── Config ──────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))
DELAY_SECONDS = float(os.environ.get("DELAY_SECONDS", "2"))  # entre cada nombre
# ────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
client = discord.Client(intents=intents)

LETTERS = string.ascii_lowercase
generated = set()  # evitar repetir nombres


def random_4_letter_name() -> str:
    """Genera un username aleatorio de 4 letras (a-z)."""
    while True:
        name = "".join(random.choices(LETTERS, k=4))
        if name not in generated:
            generated.add(name)
            return name


def is_potentially_available(name: str) -> bool:
    """
    Heurística simple: marca como 'disponible para revisar' si el nombre
    tiene una combinación interesante (no es spam de consonantes difíciles,
    tiene vocales, etc.).
    
    Puedes ajustar estas reglas a tu gusto.
    """
    vowels = set("aeiou")
    has_vowel = any(c in vowels for c in name)
    
    # Filtros de calidad — ajusta a tu gusto
    hard_clusters = ["xkq", "qqq", "zzz", "xxx", "www"]
    has_hard_cluster = any(h in name for h in hard_clusters)
    
    # Consideramos "disponible para revisar" si tiene al menos una vocal
    # y no tiene clusters muy feos
    return has_vowel and not has_hard_cluster


@tasks.loop(seconds=DELAY_SECONDS)
async def generate_and_post():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"[ERROR] No se encontró el canal con ID {CHANNEL_ID}")
        return

    name = random_4_letter_name()

    if is_potentially_available(name):
        embed = discord.Embed(
            description=f"**`{name}`** podría estar disponible — revísalo en Discord",
            color=0x57F287,  # verde Discord
        )
        embed.set_footer(text=f"Generados hasta ahora: {len(generated)}")
        await channel.send(embed=embed)
        print(f"[✓] Publicado: {name}")
    else:
        print(f"[–] Saltado:   {name}")


@client.event
async def on_ready():
    print(f"[BOT] Conectado como {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(
            embed=discord.Embed(
                title="🔍 Username Finder iniciado",
                description=(
                    "Buscando nombres de 4 letras interesantes...\n"
                    "Cuando aparezca uno, revísalo manualmente en Discord para ver si está libre."
                ),
                color=0x5865F2,
            )
        )
    generate_and_post.start()


client.run(TOKEN)
