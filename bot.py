import asyncio
import random
import string
import os
import aiohttp

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
LENGTH = int(os.environ.get("LENGTH", "4"))
THREADS = int(os.environ.get("THREADS", "10"))
DELAY = float(os.environ.get("DELAY", "1"))

CHARS = string.ascii_lowercase + string.digits
generated = set()
checked = 0
found = 0

def random_name() -> str:
    while True:
        name = "".join(random.choices(CHARS, k=LENGTH))
        if name not in generated:
            generated.add(name)
            return name

async def check_one(session, name, retries=3):
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    for _ in range(retries):
        try:
            async with session.post(
                url,
                json={"username": name},
                timeout=aiohttp.ClientTimeout(total=8)
            ) as r:
                if r.status == 429:
                    retry_after = float(r.headers.get("Retry-After", "3"))
                    print(f"[!] Rate limit {retry_after}s")
                    await asyncio.sleep(retry_after)
                    continue
                if r.status != 200:
                    await asyncio.sleep(1)
                    continue
                data = await r.json()
                taken = data.get("taken")
                if taken is None:
                    await asyncio.sleep(1)
                    continue
                return not taken
        except:
            await asyncio.sleep(1)
    generated.discard(name)
    return None

async def send_webhook(session, name):
    if not WEBHOOK_URL:
        return
    payload = {
        "content": f"`{name}` is available ✅",
        "username": "Username Finder"
    }
    try:
        async with session.post(WEBHOOK_URL, json=payload) as r:
            if r.status == 429:
                retry_after = float(r.headers.get("Retry-After", "2"))
                await asyncio.sleep(retry_after)
    except:
        pass

async def worker(session):
    global checked, found
    name = random_name()
    result = await check_one(session, name)
    checked += 1
    if result:
        found += 1
        print(f"[✓] AVAILABLE: {name} | checked={checked} found={found}")
        await send_webhook(session, name)
    elif result is False:
        print(f"[✗] taken: {name}", end="\r")
    else:
        print(f"[?] no response: {name}", end="\r")

async def main():
    print(f"[*] Starting username checker | length={LENGTH} threads={THREADS}")
    connector = aiohttp.TCPConnector(limit=THREADS)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            tasks = [worker(session) for _ in range(THREADS)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(DELAY)

if __name__ == "__main__":
    asyncio.run(main())
