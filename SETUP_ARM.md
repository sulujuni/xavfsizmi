# SafeLink Bot — ARM Setup Guide

## Files You Need
All these files must be in the same folder:
- `main.py`
- `checker.py`
- `apk_checker.py`
- `email_checker.py`
- `qr_checker.py`
- `domain_checker.py`
- `website_reputation.py`
- `admin.py`
- `database.py`
- `languages.py`
- `config.py`
- `requirements.txt`
- `.env` (you create this)

---

## Step 1 — Create `.env` File

In the same folder as the files above, create a new file called `.env` with this content:

```
BOT_TOKEN=
VIRUSTOTAL_API_KEY=
GOOGLE_SAFE_BROWSING_KEY=
ADMIN_ID=
```

Replace the values with your actual keys.

---

## Step 2 — Install Python Dependencies

Open terminal in your bot folder and run:

```bash
pip3 install -r requirements.txt
```

(On some systems it might be `pip` instead of `pip3`)

---

## Step 3 — Run the Bot

```bash
python3 main.py
```

Or on some systems:

```bash
python main.py
```

You should see:
```
🤖 SafeLink Bot ishga tushdi...
```

---

## Step 4 — Keep It Running 24/7

To keep the bot running even after you close the terminal, use `screen`:

```bash
# Install screen (if not there)
sudo apt install screen

# Start a new session
screen -S safelink

# Run the bot
python3 main.py
```

Press **Ctrl+A** then **D** to detach. Bot keeps running.

**To check on it later:**
```bash
screen -r safelink
```

**To stop the bot:**
```bash
screen -X -S safelink quit
```

---

## Troubleshooting

**"No module named 'telegram'"**
→ Run: `pip3 install -r requirements.txt` again

**"No module named 'whois'"**
→ Run: `pip3 install python-whois`

**Bot not responding to messages**
→ Check that your BOT_TOKEN is correct in `.env`

**"users.json: No such file or directory"**
→ This is normal — it creates on first run

---

## API Keys — Where to Get Them

**BOT_TOKEN:**
- Open @BotFather on Telegram → `/start` → `/newbot` → follow steps → copy token

**VIRUSTOTAL_API_KEY:**
- Go to https://www.virustotal.com/gui/join-us → Create account → Profile → API Key

**GOOGLE_SAFE_BROWSING_KEY:**
- Go to https://console.cloud.google.com → Create project → Enable Safe Browsing API → Create API Key

**ADMIN_ID:**
- Message @userinfobot on Telegram → it replies with your ID (a number)

