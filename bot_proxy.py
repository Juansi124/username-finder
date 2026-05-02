import asyncio
import random
import string
import os
import aiohttp
import itertools

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
LENGTH = int(os.environ.get("LENGTH", "4"))
THREADS = int(os.environ.get("THREADS", "20"))
DELAY = float(os.environ.get("DELAY", "0.5"))
PROXIES_ENV = os.environ.get("PROXIES", "")

CHARS = string.ascii_lowercase + string.digits
generated = set()
checked = 0
found = 0

# Cargar proxies
if PROXIES_ENV:
    proxy_list = [p.strip() for p in PROXIES_ENV.split(",") if p.strip()]
else:
    proxy_list = []

proxy_cycle = itertools.cycle(proxy_list) if proxy_list else None

def get_proxy():
    if proxy_cycle is None:
        return None, None
    raw = next(proxy_cycle)
    # formato: user:pass@host:port
    if "@" in raw:
        auth, hostport = raw.rsplit("@", 1)
        user, password = auth.split(":", 1)
        proxy_url = f"http://{hostport}"
        proxy_auth = aiohttp.BasicAuth(user, password)
        return proxy_url, proxy_auth
    else:
        return f"http://{raw}", None

def random_name() -> str:
    while True:
        name = "".join(random.choices(CHARS, k=LENGTH))
        if name not in generated:
            generated.add(name)
            return name

async def check_one(session, name, retries=3):
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    for _ in range(retries):
        proxy_url, proxy_auth = get_proxy()
        try:
            async with session.post(
                url,
                json={"username": name},
                timeout=aiohttp.ClientTimeout(total=8),
                proxy=proxy_url,
                proxy_auth=proxy_auth
            ) as r:
                if r.status == 429:
                    retry_after = float(r.headers.get("Retry-After", "2"))
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
            await asyncio.sleep(0.5)
    generated.discard(name)
    return None

async def send_webhook(name):
    if not WEBHOOK_URL:
        return
    payload = {
        "content": f"`{name}` is available ✅",
        "username": "Username Finder"
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(WEBHOOK_URL, json=payload) as r:
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
        await send_webhook(name)
    elif result is False:
        print(f"[✗] taken: {name} | checked={checked}", end="\r")

async def main():
    print(f"[*] Checker iniciado | length={LENGTH} threads={THREADS} proxies={len(proxy_list)}")
    connector = aiohttp.TCPConnector(limit=THREADS * 2)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            tasks = [worker(session) for _ in range(THREADS)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(DELAY)

if __name__ == "__main__":
    asyncio.run(main())
