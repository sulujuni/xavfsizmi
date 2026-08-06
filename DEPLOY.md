# Deploying xavfsizmi to Railway

The repo ships a `Dockerfile` and `railway.json`, so Railway builds the image
directly — no Nixpacks guesswork.

---

## Before you start: stop the local bot

Telegram allows exactly one consumer per bot token. The copy running on this
machine (started at boot by `~/autostart_bots.sh` via an `@reboot` cron entry)
will fight the deployed one: whichever polls second gets

```
telegram.error.Conflict: terminated by other getUpdates request
```

and updates get split unpredictably between them. So before the first deploy:

```bash
pkill -f '/home/sulujuni/xavfsizmi/main.py'     # stop the running copy
crontab -e                                      # comment out the @reboot line
```

Keep the local copy stopped for as long as the Railway one is live. Use a
**separate bot token** from @BotFather if you want to keep a local instance for
development.

---

## 1. Create the service

1. Railway → **New Project** → **Deploy from GitHub repo** → `sulujuni/xavfsizmi`.
2. Pick the branch you want to deploy (`deploy/railway`, or `main` once merged).

Railway reads `railway.json`, builds the `Dockerfile`, and starts
`python3 main.py`.

## 2. Attach a volume — required

The bot stores **everything** in SQLite: users, languages, scan counts, premium
subscriptions, history, reports. A container filesystem is wiped on every
redeploy, so without a volume all of it disappears the moment you push a change.

Service → **Variables** tab → **+ Volume**:

| Setting     | Value   |
|-------------|---------|
| Mount path  | `/data` |

`bot/core/database.py` picks up `/data/safelink.db` automatically. If the volume
is missing, the bot logs a loud `WARNING` at startup saying the data is
ephemeral — if you see that line in the deploy logs, the volume is not attached.

## 3. Set the variables

Service → **Variables** → **Raw Editor**. Copy the values from your local `.env`:

```bash
BOT_TOKEN=                  # @BotFather
ADMIN_ID=                   # your numeric Telegram id
VIRUSTOTAL_API_KEY=
GOOGLE_SAFE_BROWSING_KEY=
URLSCAN_API_KEY=
ALIENVAULT_API_KEY=
GROQ_API_KEY=
REQUIRED_CHANNEL_ID=
CHANNEL_INVITE_LINK=
CACHE_TTL_HOURS=24
FREE_SCANS_BEFORE_SUB=3
```

Never commit these — `.env` is gitignored and `.dockerignore` keeps it out of
the image as well.

## 4. Redis (optional)

`bot/core/cache.py` falls back to a bounded in-memory cache when `REDIS_URL` is
unset, so the bot runs fine without it. Redis only matters if you scale past one
replica, where an in-process cache stops being shared.

To add it: Railway → **+ New** → **Database** → **Redis**, then set

```bash
REDIS_URL=${{Redis.REDIS_URL}}
```

(That `${{...}}` reference syntax is Railway's — it resolves to the private URL.)

## 5. Polling or webhook

Polling is the default and needs no public domain — good enough well past this
bot's current traffic. Leave `USE_WEBHOOK` unset.

For webhook mode, generate a domain under **Settings → Networking → Generate
Domain**, then set:

```bash
USE_WEBHOOK=true
```

`WEBHOOK_URL` is derived from Railway's `RAILWAY_PUBLIC_DOMAIN` automatically,
and the listener binds the injected `$PORT`. Set `WEBHOOK_URL` explicitly only
if you put a custom domain in front.

---

## Verifying a deploy

Deploy logs should show:

```
✅ Bot menyulari muvaffaqiyatli yuklandi!
🚀 Xavfsizmi? Bot ishga tushdi!
🌐 Webhook mode: https://...     (webhook mode only)
```

A `WARNING ... ephemeral container storage` line means step 2 was skipped —
fix it before users start writing data you are going to lose.

## Rollback

Railway keeps every previous deployment. **Deployments** tab → pick the last
good one → **Redeploy**. The volume is untouched by a rollback.
