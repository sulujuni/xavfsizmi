import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN                = os.getenv("BOT_TOKEN", "")
VIRUSTOTAL_API_KEY       = os.getenv("VIRUSTOTAL_API_KEY", "")
GOOGLE_SAFE_BROWSING_KEY = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "")
URLSCAN_API_KEY          = os.getenv("URLSCAN_API_KEY", "")
ALIENVAULT_API_KEY       = os.getenv("ALIENVAULT_API_KEY", "")
UZS_PROVIDER_TOKEN       = os.getenv("UZS_PROVIDER_TOKEN", "")

REQUIRED_CHANNEL_ID  = int(os.getenv("REQUIRED_CHANNEL_ID", "0"))
CHANNEL_INVITE_LINK  = os.getenv("CHANNEL_INVITE_LINK", "")

# ─── AI CHATBOT (Groq — free llama3) ──────────────────────────────────────────
GROQ_API_KEY         = os.getenv("GROQ_API_KEY", "")

DAILY_FREE_LIMIT = 5
ADMIN_ID         = int(os.getenv("ADMIN_ID", "0"))

# ─── WEBHOOK SETTINGS ─────────────────────────────────────────────────────────
WEBHOOK_URL      = os.getenv("WEBHOOK_URL", "")  # e.g. https://yourapp.railway.app
WEBHOOK_PORT     = int(os.getenv("PORT", "8443"))
USE_WEBHOOK      = os.getenv("USE_WEBHOOK", "false").lower() == "true"

# ─── API RATE LIMITS (free tier daily caps) ───────────────────────────────────
API_LIMITS = {
    "virustotal": 500,
    "google_safe_browsing": 10000,
    "urlscan": 100,
    "alienvault": 10000,
    "groq": 14400,  # 30/min * 60 * 8h
}

# ─── PERSONAL PREMIUM PRICING ─────────────────────────────────────────────────
PERSONAL_1M_STARS = 25        # 1 month — 25 Stars
PERSONAL_3M_STARS = 65        # 3 months — 65 Stars
PERSONAL_1M_UZS   = 999000    # 1 month — 9,990 UZS (in tiyin)
PERSONAL_3M_UZS   = 2499000   # 3 months — 24,990 UZS (in tiyin)

# ─── GROUP PREMIUM PRICING ────────────────────────────────────────────────────
GROUP_1M_STARS = 50           # 1 month — 50 Stars
GROUP_3M_STARS = 130          # 3 months — 130 Stars
GROUP_1M_UZS   = 1999000      # 1 month — 19,990 UZS (in tiyin)
GROUP_3M_UZS   = 4999000      # 3 months — 49,990 UZS (in tiyin)
