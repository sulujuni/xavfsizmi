import base64
import asyncio
import httpx
import logging
from datetime import datetime
from urllib.parse import urlparse
# config.py faylidan barcha API kalitlarini olamiz
from bot.config import VIRUSTOTAL_API_KEY, GOOGLE_SAFE_BROWSING_KEY, ALIENVAULT_API_KEY, URLSCAN_API_KEY
from bot.core.rate_limiter import track_api_call

logger = logging.getLogger("safelink.checker")

# Default request timeout (seconds) for external APIs
DEFAULT_TIMEOUT = 10
# How many times to retry a transient failure (timeout / 5xx / network error)
MAX_RETRIES = 2
# Base backoff delay (seconds); grows exponentially per retry
BACKOFF_BASE = 0.5

# VirusTotal analysis polling (for freshly submitted, never-seen URLs)
VT_POLL_ATTEMPTS = 4
VT_POLL_DELAY = 2  # seconds between polls

# HTTP status codes worth retrying on
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


# ─── Shared HTTP helper with retry + exponential backoff ─────────────────────

async def _request_with_retry(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    """
    Perform an HTTP request with retry + exponential backoff on transient
    failures (timeouts, connection errors, and 429/5xx responses).

    Returns the httpx.Response, or None if all attempts failed.
    """
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = await client.request(method, url, **kwargs)
            if resp.status_code in _RETRYABLE_STATUS and attempt < MAX_RETRIES:
                await asyncio.sleep(BACKOFF_BASE * (2 ** attempt))
                continue
            return resp
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_exc = e
            if attempt < MAX_RETRIES:
                await asyncio.sleep(BACKOFF_BASE * (2 ** attempt))
                continue
    if last_exc:
        logger.warning("Request to %s failed after retries: %s", url, last_exc)
    return None


# ─── VirusTotal ──────────────────────────────────────────────────────────────

async def check_virustotal(url: str) -> dict:
    """
    VirusTotal v3 API orqali havolani tekshirish.

    If the URL has never been analyzed by VirusTotal (common for fresh phishing
    links), we submit it for analysis and poll the result instead of silently
    treating an unknown URL as clean.

    Returns: {"malicious": int, "total": int, "found": bool}
    """
    if not VIRUSTOTAL_API_KEY or "Sizning" in VIRUSTOTAL_API_KEY:
        return {"malicious": 0, "total": 0, "found": False}

    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")

    async with httpx.AsyncClient() as client:
        try:
            resp = await _request_with_retry(
                client, "GET",
                f"https://www.virustotal.com/api/v3/urls/{url_id}",
                headers=headers,
            )
            track_api_call("virustotal")

            if resp is not None and resp.status_code == 200:
                stats = (
                    resp.json()
                    .get("data", {})
                    .get("attributes", {})
                    .get("last_analysis_stats", {})
                )
                return {
                    "malicious": stats.get("malicious", 0),
                    "total": sum(stats.values()),
                    "found": True,
                }

            # 404 → URL unknown to VirusTotal. Submit it and poll the analysis.
            if resp is not None and resp.status_code == 404:
                return await _vt_submit_and_poll(client, headers, url)

        except Exception as e:
            logger.error("VirusTotal error: %s", e)

    return {"malicious": 0, "total": 0, "found": False}


async def _vt_submit_and_poll(client: httpx.AsyncClient, headers: dict, url: str) -> dict:
    """Submit a new URL to VirusTotal and poll for the analysis verdict."""
    try:
        submit = await _request_with_retry(
            client, "POST",
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data={"url": url},
        )
        track_api_call("virustotal")
        if submit is None or submit.status_code not in (200, 201):
            return {"malicious": 0, "total": 0, "found": False}

        analysis_id = submit.json().get("data", {}).get("id")
        if not analysis_id:
            return {"malicious": 0, "total": 0, "found": False}

        for _ in range(VT_POLL_ATTEMPTS):
            await asyncio.sleep(VT_POLL_DELAY)
            poll = await _request_with_retry(
                client, "GET",
                f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                headers=headers,
            )
            track_api_call("virustotal")
            if poll is None or poll.status_code != 200:
                continue
            attrs = poll.json().get("data", {}).get("attributes", {})
            if attrs.get("status") == "completed":
                stats = attrs.get("stats", {})
                return {
                    "malicious": stats.get("malicious", 0),
                    "total": sum(stats.values()),
                    "found": True,
                }
    except Exception as e:
        logger.error("VirusTotal submit/poll error: %s", e)

    return {"malicious": 0, "total": 0, "found": False}


# ─── Google Safe Browsing ────────────────────────────────────────────────────

async def check_google_safe_browsing(url: str) -> dict:
    """Google Safe Browsing v4 API orqali tekshirish"""
    if not GOOGLE_SAFE_BROWSING_KEY or "Sizning" in GOOGLE_SAFE_BROWSING_KEY:
        return {"dangerous": False}

    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_KEY}"
    payload = {
        "client": {"clientId": "safelinkbot", "clientVersion": "1.0.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    async with httpx.AsyncClient() as client:
        try:
            res = await _request_with_retry(client, "POST", endpoint, json=payload)
            track_api_call("google_safe_browsing")
            if res is not None and res.status_code == 200 and "matches" in res.json():
                return {"dangerous": True}
        except Exception as e:
            logger.error("Google Safe Browsing error: %s", e)
    return {"dangerous": False}


# ─── AlienVault OTX ──────────────────────────────────────────────────────────

async def check_alienvault(url: str) -> dict:
    """AlienVault OTX API orqali URL reputatsiyasini tekshirish"""
    if not ALIENVAULT_API_KEY or "Sizning" in ALIENVAULT_API_KEY:
        return {"pulses_count": 0, "dangerous": False}

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    endpoint = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/general"
    headers = {"X-OTX-API-KEY": ALIENVAULT_API_KEY}

    async with httpx.AsyncClient() as client:
        try:
            res = await _request_with_retry(client, "GET", endpoint, headers=headers)
            track_api_call("alienvault")
            if res is not None and res.status_code == 200:
                data = res.json()
                pulses = data.get("pulse_info", {}).get("pulses", [])
                # Agar ushbu domen kiber-tahdidlar ro'yxatida (Pulse) bo'lsa, xavfli deb hisoblaymiz
                return {"pulses_count": len(pulses), "dangerous": len(pulses) > 0}
        except Exception as e:
            logger.error("AlienVault error: %s", e)
    return {"pulses_count": 0, "dangerous": False}


# ─── Urlscan.io ──────────────────────────────────────────────────────────────

async def check_urlscan(url: str) -> dict:
    """Urlscan.io API orqali saytning chuqur xatti-harakatini tekshirish"""
    if not URLSCAN_API_KEY or "Sizning" in URLSCAN_API_KEY:
        return {"verdict": "unknown", "score": 0}

    headers = {"API-Key": URLSCAN_API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        try:
            # Urlscan biroz sekin ishlaydi, shuning uchun tezkor qidiruv xizmatidan foydalanamiz
            domain = urlparse(url).netloc
            search_endpoint = f"https://urlscan.io/api/v1/search/?q=domain:{domain}"
            res = await _request_with_retry(client, "GET", search_endpoint, headers=headers)
            track_api_call("urlscan")
            if res is not None and res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    # Oxirgi tahlil natijasidagi xavflilik darajasini tekshiramiz
                    verdict = results[0].get("verdict", {}).get("overall", {})
                    return {"verdict": "malicious" if verdict.get("malicious") else "clean", "score": verdict.get("score", 0)}
        except Exception as e:
            logger.error("Urlscan error: %s", e)
    return {"verdict": "unknown", "score": 0}


# ─── Domain age ──────────────────────────────────────────────────────────────

async def get_domain_age(url: str) -> dict:
    """
    Soddalashtirilgan domen yoshi tekshiruvi (RDAP orqali).

    Returns age_days=None when the age can't be determined, so callers don't
    mistakenly treat an unknown domain as an established (safe) one.
    """
    domain = urlparse(url).netloc
    # rdap.org is a router: it answers 302 to the registry that actually holds
    # the domain (e.g. rdap.verisign.com for .com). Without following that
    # redirect every lookup returns 302, never 200, and the age is always
    # unknown — which made this check dead for every domain.
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            res = await _request_with_retry(
                client, "GET", f"https://rdap.org/domain/{domain}", timeout=5
            )
            if res is not None and res.status_code == 200:
                events = res.json().get("events", [])
                for event in events:
                    if event.get("eventAction") == "registration":
                        reg_date_str = event.get("eventDate", "")[:10]
                        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
                        age_days = (datetime.now() - reg_date).days
                        return {"age_days": age_days, "created": reg_date_str}
        except Exception:
            pass
    return {"age_days": None, "created": "Noma'lum"}


# ─── Combined multi-layer scan ───────────────────────────────────────────────

async def check_url_complete(url: str, lang: str) -> tuple:
    """Barcha himoya qatlamlarini birlashtiruvchi bosh funksiya (parallel)."""
    # Run all independent checks concurrently for a big latency win.
    vt, gsb, alien, uscan, age_info = await asyncio.gather(
        check_virustotal(url),
        check_google_safe_browsing(url),
        check_alienvault(url),
        check_urlscan(url),
        get_domain_age(url),
        return_exceptions=True,
    )

    # If any check raised, fall back to its safe default and log it.
    def _safe(result, default, name):
        if isinstance(result, Exception):
            logger.error("%s check failed: %s", name, result)
            return default
        return result

    vt = _safe(vt, {"malicious": 0, "total": 0, "found": False}, "VirusTotal")
    gsb = _safe(gsb, {"dangerous": False}, "GoogleSafeBrowsing")
    alien = _safe(alien, {"pulses_count": 0, "dangerous": False}, "AlienVault")
    uscan = _safe(uscan, {"verdict": "unknown", "score": 0}, "Urlscan")
    age_info = _safe(age_info, {"age_days": None, "created": "Noma'lum"}, "DomainAge")

    # Umumiy xavflilik xulosasi
    is_dangerous = (
        gsb.get("dangerous") or
        vt.get("malicious", 0) > 0 or
        alien.get("dangerous") or
        uscan.get("verdict") == "malicious"
    )

    # Chiroyli Markdown hisobot matnini tuzamiz
    status_emoji = "🔴 ZARARLI / MALICIOUS" if is_dangerous else "✅ XAVFSIZ / CLEAN"

    report = "🛡 *SafeLink Ko'p Qatlamli Havola Tahlili:*\n\n"
    report += f"🔗 *URL:* `{url}`\n"
    report += f"📊 *Yakuniy Xulosa:* *{status_emoji}*\n\n"

    report += f"🔍 *VirusTotal:* `{vt.get('malicious', 0)}` ta antivirus xavf aniqladi.\n"
    report += f"🌐 *Google Safe Browsing:* {'❌ Fishing/Tahdid bor' if gsb.get('dangerous') else '✅ Toza'}\n"
    report += f"👽 *AlienVault OTX:* `{alien.get('pulses_count', 0)}` ta global kiber-tahdid guruhida topildi.\n"
    report += f"📸 *Urlscan.io Tahlili:* Verdict: `{uscan.get('verdict', 'clear').upper()}` (Score: {uscan.get('score', 0)}/100)\n"

    age_days = age_info.get("age_days")
    age_display = f"{age_days} kun" if age_days is not None else "Noma'lum"
    report += f"📅 *Domen Yoshi:* `{age_display}` (Ochilgan sana: {age_info.get('created')})\n"

    if age_days is not None and age_days < 30:
        report += "\n⚠️ *DIQQAT:* Ushbu domen juda yangi ochilgan! Fishing sayt bo'lish ehtimoli juda yuqori, ma'lumot kiritmang!"

    return report, is_dangerous


# ─── COMPATIBILITY WRAPPERS (used by main.py) ─────────────────────────────────

async def check_url(url: str, lang: str = "uz") -> str:
    """Simple wrapper — returns formatted report string."""
    report, _ = await check_url_complete(url, lang)
    return report


async def check_url_with_domain_age(url: str) -> dict:
    """Returns domain age dict — used by main.py for separate age display."""
    return await get_domain_age(url)
