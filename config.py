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

DAILY_FREE_LIMIT = 5
ADMIN_ID         = int(os.getenv("ADMIN_ID", "0"))

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
