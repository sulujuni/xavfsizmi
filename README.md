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
| URL Check | _(just send a link)_ | Multi-layer scan of any URL |
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

### Keep it running (Linux/VPS)

Using **systemd** (recommended for production):

```bash
sudo tee /etc/systemd/system/xavfsizmi.service <<EOF
[Unit]
Description=Xavfsizmi Telegram Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=5
Environment=PATH=$(pwd)/venv/bin

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now xavfsizmi
```

Or using **screen** (quick testing):

```bash
screen -S xavfsizmi
python main.py
# Press Ctrl+A then D to detach
```

---

## Project Structure

```
xavfsizmi/
├── main.py                 # Entry point, handler registration, scheduler
├── config.py               # Environment variable loader
├── checker.py              # Multi-layer URL scanning engine (VT, GSB, AV, Urlscan, RDAP)
├── database.py             # SQLite key-value store + cache-backed rate limiting
├── cache.py                # Redis/in-memory cache layer
├── menu.py                 # Single source of truth for bot command menus
├── admin.py                # Admin panel, broadcast, user management
├── languages.py            # Translations (uz, ru, en)
├── error_handler.py        # Global error handler → reports to admin
├── rate_tracker.py         # API rate limit monitoring
├── apk_checker.py          # APK file scanning via VirusTotal
├── qr_checker.py           # QR code URL extraction (OpenCV)
├── email_checker.py        # HaveIBeenPwned-style breach lookups
├── domain_checker.py       # Domain reputation utilities
├── file_scanner.py         # Generic file type detection + scanning
├── website_reputation.py   # Website trust score calculation
├── handlers/
│   ├── __init__.py         # Re-exports all handler functions
│   ├── commands.py         # /start, /help, /language, /history, etc.
│   ├── conversations.py    # Multi-step conversations (scammer, report, feedback, darkweb)
│   ├── private_messages.py # URL/APK/QR handling in private chat
│   ├── group_messages.py   # URL/APK/QR handling in groups (auto-delete)
│   ├── secretary.py        # Business Connection handlers (secretary mode)
│   ├── premium.py          # Premium purchase, promo codes, Paynet
│   ├── breach.py           # /breach conversation
│   ├── monitor.py          # /monitor — email breach monitoring
│   ├── ai.py               # /ask, /analyze — AI-powered features (Groq)
│   ├── daily_tips.py       # /tips — scheduled cybersecurity tips
│   ├── leaderboard.py      # /top — referral leaderboard
│   ├── weekly_report.py    # Automated weekly security digest
│   ├── bulk_check.py       # Bulk URL checking
│   └── tools.py            # Trust score, typosquat detection, utilities
├── tests/                  # pytest test suite (26 tests)
├── .github/workflows/ci.yml # GitHub Actions: ruff + pytest
├── ruff.toml               # Linter configuration
├── pytest.ini              # Test runner configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Template environment file
└── SETUP_ARM.md            # Legacy ARM setup guide
```

---

## Running Tests

```bash
pip install pytest pytest-asyncio ruff
pytest -q          # Run all tests
ruff check .       # Lint
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
