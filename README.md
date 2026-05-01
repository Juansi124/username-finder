# 🔍 Discord Username Finder

Bot de Discord que genera nombres aleatorios de 4 letras y publica en un canal los que parecen interesantes, para que los revises manualmente.

---

## 📁 Archivos

```
discord-username-checker/
├── bot.py            ← código del bot
├── requirements.txt  ← dependencias
├── render.yaml       ← config para Render.com
└── README.md
```

---

## 🚀 Setup paso a paso

### 1. Crear el Bot en Discord Developer Portal

1. Ve a https://discord.com/developers/applications
2. Click **New Application** → ponle nombre → **Create**
3. Ve a la sección **Bot** (menú izquierdo)
4. Click **Add Bot** → confirma
5. Click **Reset Token** → copia el token (lo necesitarás después)
6. Activa **Message Content Intent** (en la misma página)

### 2. Invitar el bot a tu servidor

1. Ve a **OAuth2 → URL Generator**
2. En *Scopes* marca: `bot`
3. En *Bot Permissions* marca: `Send Messages`, `Embed Links`, `View Channels`
4. Copia la URL generada → ábrela en el navegador → invita el bot a tu servidor

### 3. Obtener el ID del canal

1. En Discord, ve a **Ajustes → Avanzado → Activa Modo Desarrollador**
2. Click derecho en el canal donde quieres que postee
3. Click **Copiar ID del canal**

### 4. Subir a GitHub

1. Crea un repo nuevo en https://github.com/new (ponlo en privado)
2. Sube los 4 archivos (`bot.py`, `requirements.txt`, `render.yaml`, `README.md`)

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

### 5. Deployar en Render.com (gratis)

1. Ve a https://render.com → regístrate gratis con tu cuenta de GitHub
2. Click **New → Background Worker**
3. Conecta tu repo de GitHub
4. En la configuración:
   - **Name**: discord-username-finder
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. En **Environment Variables** agrega:
   - `DISCORD_TOKEN` → el token que copiaste en el paso 1
   - `CHANNEL_ID` → el ID del canal que copiaste en el paso 3
   - `DELAY_SECONDS` → `2` (cada cuántos segundos genera uno)
6. Click **Create Background Worker**

¡Listo! El bot se prenderá solo y empezará a postear nombres.

---

## ⚙️ Personalizar el filtro

En `bot.py`, la función `is_potentially_available()` decide qué nombres se publican.

Puedes editarla a tu gusto. Por ejemplo:

```python
# Solo nombres que empiecen con vocal
return name[0] in "aeiou"

# Solo nombres que tengan exactamente 2 vocales
vowels = sum(1 for c in name if c in "aeiou")
return vowels == 2

# Solo nombres que sean "pronunciables" (vocal-consonante alternados)
# ... personaliza como quieras
```

### Variable `DELAY_SECONDS`
- `1` → 1 nombre por segundo (rápido)
- `2` → 1 nombre cada 2 segundos (recomendado)
- `5` → más lento, menos spam en el canal

---

## ⚠️ Importante

Este bot **no verifica** la disponibilidad real en Discord — eso requeriría violar los Términos de Servicio. Lo que hace es:

1. Generar combinaciones de 4 letras al azar
2. Filtrar las que parecen más "usables" (tienen vocales, son pronunciables)
3. Publicarlas en tu canal para que **tú las revises manualmente** en Discord

Para verificar si un nombre está disponible en Discord, intenta cambiarlo en **Ajustes → Mi Cuenta → Editar → Username**.

---

## 🎨 Ejemplo de output en Discord

```
✅  "vale" podría estar disponible — revísalo en Discord
✅  "niko" podría estar disponible — revísalo en Discord
✅  "axel" podría estar disponible — revísalo en Discord
```
