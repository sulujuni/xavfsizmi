# Xavfsizmi? — Telegram Cybersecurity Bot

**Xavfsizmi?** (Uzbek for "Is it safe?") is a multi-layer security bot for Telegram that protects users from phishing, malware, and scams — in private chats, groups, and even as a business secretary connected to a personal account.

---

## What the Bot Does

### Core Scanning Engine
Every URL, file, or QR code sent to the bot is checked through **5 independent layers** simultaneously:

| Layer | Source | What It Detects |
|-------|--------|-----------------|
| VirusTotal | 70+ antivirus engines | Malware, phishing, spam URLs |
| Google Safe Browsing | Google's global blocklist | Social engineering, unwanted software |
| AlienVault OTX | Threat intelligence pulses | Known malicious domains |
| Urlscan.io | Behavioral sandbox | Drive-by downloads, redirects |
| Domain Age (RDAP) | WHOIS registration date | Brand-new phishing domains |

Results are combined into a single, easy-to-read report with a clear **safe/dangerous** verdict.

### Features

| Feature | Command | Description |
|---------|---------|-------------|
| URL Check | `/check` or send a link | Multi-layer scan of any URL |
| APK Scan | _(send an .apk file)_ | VirusTotal analysis of Android apps |
| QR Code Scan | _(send a photo)_ | Extracts URL from QR and checks it |
| Email Breach | `/breach` | Check if an email appeared in data leaks |
| Dark Web Check | `/darkweb` | Search dark web databases |
| Scammer Lookup | `/scammer` | Check phone/username against scam reports |
| AI Assistant | `/ask` | Ask cybersecurity questions (powered by Groq/Llama) |
| Message Analyzer | `/analyze` | Paste a suspicious message for AI scam detection |
| Phishing Simulator | `/phish` | Generate a safe training phish to educate friends |
| Email Monitoring | `/monitor` | (Premium) Daily breach alerts for saved emails |
| Referral Program | `/referral` | Earn free breach checks by inviting friends |
| Leaderboard | `/top` | Monthly top referrers |
| Daily Tips | `/tips` | Cybersecurity tips delivered daily |
| Premium | `/premium` | Unlimited checks, AI features, email monitoring |
| Weekly Report | _(automatic)_ | Personal security summary every Monday |

### Secretary Mode (Business Bot)
Connect the bot as your Telegram Business chatbot and it will:
- Silently scan all incoming messages for malicious URLs
- Detect APK malware sent by contacts
- Extract and check QR code links in photos
- Classify scam/phishing messages using regex + AI
- Alert you only when something dangerous is found

### Group Protection
Add the bot to any group and it will:
- Auto-delete messages containing malicious links
- Warn the group about the threat
- Support group-specific language settings
- Track blocked/warned statistics per group

---

## How to Run

### Prerequisites
- Python 3.10+ (tested on 3.11/3.12)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- At least a VirusTotal API key (free tier: 500 requests/day)

### 1. Clone the repository

```bash
git clone https://github.com/sulujuni/xavfsizmi.git
cd xavfsizmi
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and fill in your keys:

```bash
cp .env.example .env
```

**Required variables:**

| Variable | Where to Get |
|----------|-------------|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) on Telegram |
| `ADMIN_ID` | Your numeric Telegram ID (from [@userinfobot](https://t.me/userinfobot)) |

**Recommended (scanning won't work without at least one):**

| Variable | Where to Get |
|----------|-------------|
| `VIRUSTOTAL_API_KEY` | [virustotal.com](https://www.virustotal.com/gui/join-us) — free account |
| `GOOGLE_SAFE_BROWSING_KEY` | [Google Cloud Console](https://console.cloud.google.com) — enable Safe Browsing API |
| `URLSCAN_API_KEY` | [urlscan.io](https://urlscan.io/user/signup) — free account |
| `ALIENVAULT_API_KEY` | [otx.alienvault.com](https://otx.alienvault.com) — free account |

**Optional (AI features):**

| Variable | Where to Get |
|----------|-------------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) — free Llama 3 access |

**Optional (scaling):**

| Variable | Purpose |
|----------|---------|
| `REDIS_URL` | Redis URL for shared cache (required for multi-instance) |
| `USE_WEBHOOK=true` | Enable webhook mode instead of polling |
| `WEBHOOK_URL` | Public HTTPS URL for webhooks |
| `REQUIRED_CHANNEL_ID` | Force users to subscribe to your channel before using the bot |

### 5. Run the bot

```bash
python main.py
```

You should see:
```
INFO - safelink.main - Xavfsizmi? Bot ishga tushdi!
```

---

## Deploying Updates (Pull from GitHub to Your Server)

When a new pull request is merged, here's how to get those changes onto your running server:

### Quick update (most common)

```bash
cd ~/xavfsizmi              # go to your bot folder
git pull origin develop     # download the latest changes
pip install -r requirements.txt  # install any new dependencies
```

Then restart the bot:
```bash
# If using systemd:
sudo systemctl restart xavfsizmi

# If using screen:
screen -r xavfsizmi         # reattach
# Press Ctrl+C to stop the bot
python main.py              # start it again
# Press Ctrl+A then D to detach
```

### If you have local changes that conflict

```bash
cd ~/xavfsizmi
git stash                   # save your local changes aside
git pull origin develop     # get the latest
git stash pop               # re-apply your local changes on top
```

### Pulling a specific PR branch (to test before merging)

```bash
cd ~/xavfsizmi

# Fetch and checkout the PR branch
git fetch origin
git checkout fix/secretary-business-connection-attribute  # or whatever branch name

# Test it, and if it works, merge into develop:
git checkout develop
git merge fix/secretary-business-connection-attribute
```

### First-time setup on a new server

```bash
# 1. Clone
git clone https://github.com/sulujuni/xavfsizmi.git
cd xavfsizmi

# 2. Switch to the develop branch (main working branch)
git checkout develop

# 3. Set up Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env
nano .env  # fill in your keys

# 5. Run
python main.py
```

---

## Keep It Running 24/7

### Using systemd (recommended for production)

```bash
sudo tee /etc/systemd/system/xavfsizmi.service <<EOF
[Unit]
Description=Xavfsizmi Telegram Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=/home/$USER/xavfsizmi
ExecStart=/home/$USER/xavfsizmi/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now xavfsizmi

# Check status:
sudo systemctl status xavfsizmi

# View logs:
journalctl -u xavfsizmi -f
```

### Using screen (quick testing)

```bash
screen -S xavfsizmi
python main.py
# Press Ctrl+A then D to detach

# To reattach later:
screen -r xavfsizmi
```

---

## Project Structure

```
xavfsizmi/
├── main.py                     # Entry point (delegates to bot/)
├── bot/
│   ├── app.py                  # Application builder + handler registration
│   ├── config.py               # Environment variable loader
│   ├── menu.py                 # Bot command menus (8 public + 6 admin)
│   ├── i18n.py                 # Translations (uz, ru, en)
│   ├── error_handler.py        # Global error handler → reports to admin
│   ├── scheduler.py            # APScheduler jobs (tips, reports, monitoring)
│   ├── core/                   # Business logic (no Telegram dependency)
│   │   ├── database.py         # SQLite key-value store + cache-backed rate limiting
│   │   ├── cache.py            # Redis/in-memory cache layer
│   │   ├── scanner.py          # Multi-layer URL scanning (VT, GSB, AV, Urlscan, RDAP)
│   │   ├── apk.py             # APK file scanning via VirusTotal
│   │   ├── qr.py             # QR code URL extraction (OpenCV)
│   │   ├── breach.py          # Email breach lookups
│   │   ├── domain.py          # Domain reputation utilities
│   │   ├── files.py           # Generic file type detection + scanning
│   │   ├── reputation.py      # Website trust score calculation
│   │   ├── trust.py           # Trust score, typosquat, homoglyphs, SSL, tech detection
│   │   └── rate_limiter.py    # API rate limit monitoring
│   └── handlers/               # Thin Telegram handler glue
│       ├── start.py            # /start, /help, /language
│       ├── scan.py             # Private URL/APK/QR scanning
│       ├── group.py            # Group auto-moderation
│       ├── secretary.py        # Business connection (secretary mode)
│       ├── premium.py          # /premium, promo codes, payments
│       ├── breach.py           # /breach, /darkweb, /monitor
│       ├── ai.py              # /ask, /analyze
│       ├── social.py           # /referral, /top, /tips, /phish, /feedback, /report, /scammer
│       ├── admin.py            # /admin, /broadcast, /stats, /ratelimit, /dbinfo
│       └── callbacks.py        # All callback query routing
├── tests/                      # pytest test suite (26 tests)
├── .github/workflows/ci.yml    # GitHub Actions: ruff + pytest
├── migrate_json_to_sqlite.py   # One-time migration script
├── requirements.txt
├── .env.example
├── ruff.toml
└── pytest.ini
```

---

## Running Tests

```bash
pip install pytest pytest-asyncio ruff
pytest -q          # Run all tests
ruff check bot/    # Lint
```

---

## Tech Stack

- **python-telegram-bot** 21+ (async, webhook-capable)
- **httpx** — async HTTP client for API calls (with retry/backoff)
- **SQLite** — persistent storage (key-value document model)
- **Redis** — optional L2 cache (in-memory fallback built in)
- **APScheduler** — daily tips, weekly reports, breach monitoring
- **OpenCV** — QR code extraction from photos
- **Groq (Llama 3)** — AI chatbot and scam analysis

---

## License

This project is private. Contact the repository owner for usage rights.
