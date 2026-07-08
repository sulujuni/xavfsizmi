"""
Phase 2 URL Checker — with caching, rate limiting, and structured logging.

All checker functions now:
1. Check cache first (avoid redundant API calls)
2. Use rate limiter with key rotation
3. Log metrics (latency, success/failure)
4. Store results in cache for future lookups
"""

import json
import time
import httpx
import logging
from datetime import datetime
from urllib.parse import urlparse

from config import VIRUSTOTAL_API_KEY, GOOGLE_SAFE_BROWSING_KEY, ALIENVAULT_API_KEY, URLSCAN_API_KEY
from cache_manager import cache
from api_limiter import rate_limiter
from logger import get_logger, metrics, health

logger = get_logger("checker")


# ─── VIRUSTOTAL ───────────────────────────────────────────────────────────────

async def check_virustotal(url: str) -> dict:
    """VirusTotal v3 API — with cache + rate limiting + key rotation."""
    # Check cache first
    cached = await cache.get_url_result(f"vt:{url}")
    if cached:
        logger.debug("VirusTotal cache hit for %s", url)
        return cached

    # Acquire key via rate limiter
    key = await rate_limiter.acquire("virustotal")
    if key is None:
        # Fallback: use primary key directly (best effort)
        key = VIRUSTOTAL_API_KEY
        if not key or "Sizning" in key:
            return {"malicious": 0, "total": 0}

    start_time = time.time()
    result = {"malicious": 0, "total": 0}

    try:
        import base64
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        headers = {"x-apikey": key}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://www.virustotal.com/api/v3/urls/{url_id}",
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                stats = response.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                result = {"malicious": stats.get("malicious", 0), "total": sum(stats.values())}
                await rate_limiter.release("virustotal", key, success=True)
                health.update("virustotal", True, "OK")
            elif response.status_code == 429:
                # Rate limited
                await rate_limiter.release("virustotal", key, success=False, is_rate_limit=True)
                logger.warning("VirusTotal rate limited")
                health.update("virustotal", False, "Rate limited")
            else:
                await rate_limiter.release("virustotal", key, success=False)
                logger.warning("VirusTotal returned status %d", response.status_code)

    except Exception as e:
        await rate_limiter.release("virustotal", key, success=False)
        logger.error("VirusTotal error: %s", e)
        health.update("virustotal", False, str(e))

    duration_ms = (time.time() - start_time) * 1000
    await metrics.record_scan("virustotal", duration_ms=duration_ms, success=result["total"] > 0)

    # Cache result (even empty ones to avoid re-querying bad URLs)
    if result["total"] > 0:
        await cache.set_url_result(f"vt:{url}", result)

    return result


# ─── GOOGLE SAFE BROWSING ─────────────────────────────────────────────────────

async def check_google_safe_browsing(url: str) -> dict:
    """Google Safe Browsing v4 API — with cache + rate limiting."""
    # Check cache
    cached = await cache.get_url_result(f"gsb:{url}")
    if cached:
        logger.debug("Google SB cache hit for %s", url)
        return cached

    key = await rate_limiter.acquire("google_safe_browsing")
    if key is None:
        key = GOOGLE_SAFE_BROWSING_KEY
        if not key or "Sizning" in key:
            return {"dangerous": False}

    start_time = time.time()
    result = {"dangerous": False}

    try:
        endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={key}"
        payload = {
            "client": {"clientId": "safelinkbot", "clientVersion": "2.0.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(endpoint, json=payload, timeout=10)

            if res.status_code == 200:
                data = res.json()
                if "matches" in data:
                    result = {"dangerous": True, "threats": [m.get("threatType", "") for m in data["matches"]]}
                await rate_limiter.release("google_safe_browsing", key, success=True)
                health.update("google_safe_browsing", True, "OK")
            elif res.status_code == 429:
                await rate_limiter.release("google_safe_browsing", key, success=False, is_rate_limit=True)
                logger.warning("Google Safe Browsing rate limited")
                health.update("google_safe_browsing", False, "Rate limited")
            else:
                await rate_limiter.release("google_safe_browsing", key, success=False)

    except Exception as e:
        await rate_limiter.release("google_safe_browsing", key, success=False)
        logger.error("Google Safe Browsing error: %s", e)
        health.update("google_safe_browsing", False, str(e))

    duration_ms = (time.time() - start_time) * 1000
    await metrics.record_scan("google_safe_browsing", duration_ms=duration_ms, success=True)

    # Cache result
    await cache.set_url_result(f"gsb:{url}", result)
    return result


# ─── ALIENVAULT OTX ───────────────────────────────────────────────────────────

async def check_alienvault(url: str) -> dict:
    """AlienVault OTX API — with cache + rate limiting."""
    # Check cache
    cached = await cache.get_url_result(f"av:{url}")
    if cached:
        logger.debug("AlienVault cache hit for %s", url)
        return cached

    key = await rate_limiter.acquire("alienvault")
    if key is None:
        key = ALIENVAULT_API_KEY
        if not key or "Sizning" in key:
            return {"pulses_count": 0, "dangerous": False}

    start_time = time.time()
    result = {"pulses_count": 0, "dangerous": False}

    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        endpoint = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/general"
        headers = {"X-OTX-API-KEY": key}

        async with httpx.AsyncClient() as client:
            res = await client.get(endpoint, headers=headers, timeout=10)

            if res.status_code == 200:
                data = res.json()
                pulses = data.get("pulse_info", {}).get("pulses", [])
                result = {"pulses_count": len(pulses), "dangerous": len(pulses) > 0}
                await rate_limiter.release("alienvault", key, success=True)
                health.update("alienvault", True, "OK")
            elif res.status_code == 429:
                await rate_limiter.release("alienvault", key, success=False, is_rate_limit=True)
                logger.warning("AlienVault rate limited")
                health.update("alienvault", False, "Rate limited")
            else:
                await rate_limiter.release("alienvault", key, success=False)

    except Exception as e:
        await rate_limiter.release("alienvault", key, success=False)
        logger.error("AlienVault error: %s", e)
        health.update("alienvault", False, str(e))

    duration_ms = (time.time() - start_time) * 1000
    await metrics.record_scan("alienvault", duration_ms=duration_ms, success=True)

    # Cache result
    await cache.set_url_result(f"av:{url}", result)
    return result


# ─── URLSCAN.IO ───────────────────────────────────────────────────────────────

async def check_urlscan(url: str) -> dict:
    """URLScan.io API — with cache + rate limiting."""
    # Check cache
    cached = await cache.get_url_result(f"us:{url}")
    if cached:
        logger.debug("URLScan cache hit for %s", url)
        return cached

    key = await rate_limiter.acquire("urlscan")
    if key is None:
        key = URLSCAN_API_KEY
        if not key or "Sizning" in key:
            return {"verdict": "unknown", "score": 0}

    start_time = time.time()
    result = {"verdict": "unknown", "score": 0}

    try:
        domain = urlparse(url).netloc
        headers = {"API-Key": key, "Content-Type": "application/json"}
        search_endpoint = f"https://urlscan.io/api/v1/search/?q=domain:{domain}"

        async with httpx.AsyncClient() as client:
            res = await client.get(search_endpoint, headers=headers, timeout=10)

            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    verdict = results[0].get("verdict", {}).get("overall", {})
                    result = {
                        "verdict": "malicious" if verdict.get("malicious") else "clean",
                        "score": verdict.get("score", 0)
                    }
                await rate_limiter.release("urlscan", key, success=True)
                health.update("urlscan", True, "OK")
            elif res.status_code == 429:
                await rate_limiter.release("urlscan", key, success=False, is_rate_limit=True)
                logger.warning("URLScan rate limited")
                health.update("urlscan", False, "Rate limited")
            else:
                await rate_limiter.release("urlscan", key, success=False)

    except Exception as e:
        await rate_limiter.release("urlscan", key, success=False)
        logger.error("URLScan error: %s", e)
        health.update("urlscan", False, str(e))

    duration_ms = (time.time() - start_time) * 1000
    await metrics.record_scan("urlscan", duration_ms=duration_ms, success=True)

    # Cache result
    await cache.set_url_result(f"us:{url}", result)
    return result


# ─── DOMAIN AGE ───────────────────────────────────────────────────────────────

async def get_domain_age(url: str) -> dict:
    """Domain age check via RDAP (free, no key needed)."""
    # Check cache
    cached = await cache.get_url_result(f"age:{url}")
    if cached:
        return cached

    domain = urlparse(url).netloc
    result = {"age_days": 365, "created": "Noma'lum"}

    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"https://rdap.org/domain/{domain}", timeout=5)
            if res.status_code == 200:
                events = res.json().get("events", [])
                for event in events:
                    if event.get("eventAction") == "registration":
                        reg_date_str = event.get("eventDate", "")[:10]
                        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
                        age_days = (datetime.now() - reg_date).days
                        result = {"age_days": age_days, "created": reg_date_str}
                        break
    except Exception:
        pass

    # Cache domain age for longer (7 days)
    await cache.set_url_result(f"age:{url}", result, ttl_hours=168)
    return result


# ─── COMBINED CHECK (used by main handlers) ──────────────────────────────────

async def check_url_complete(url: str, lang: str) -> tuple:
    """
    Run all 4 security checks + domain age in parallel.
    Returns (report_text, is_dangerous).
    Uses cache — repeated URLs return instantly.
    """
    import asyncio

    # Check if we have a full combined result cached
    full_cache_key = f"full:{url}"
    cached_full = await cache.get_url_result(full_cache_key)
    if cached_full:
        logger.info("Full scan cache hit for %s", url)
        return cached_full.get("report", ""), cached_full.get("is_dangerous", False)

    # Run all checks in parallel
    vt, gsb, alien, uscan, age_info = await asyncio.gather(
        check_virustotal(url),
        check_google_safe_browsing(url),
        check_alienvault(url),
        check_urlscan(url),
        get_domain_age(url),
    )

    # Determine danger level
    is_dangerous = (
        gsb.get("dangerous") or
        vt.get("malicious", 0) > 0 or
        alien.get("dangerous") or
        uscan.get("verdict") == "malicious"
    )

    # Build report
    status_emoji = "🔴 ZARARLI / MALICIOUS" if is_dangerous else "✅ XAVFSIZ / CLEAN"

    report = f"🛡 *SafeLink Ko'p Qatlamli Havola Tahlili:*\n\n"
    report += f"🔗 *URL:* `{url}`\n"
    report += f"📊 *Yakuniy Xulosa:* *{status_emoji}*\n\n"
    report += f"🔍 *VirusTotal:* `{vt.get('malicious', 0)}` ta antivirus xavf aniqladi.\n"
    report += f"🌐 *Google Safe Browsing:* {'❌ Fishing/Tahdid bor' if gsb.get('dangerous') else '✅ Toza'}\n"
    report += f"👽 *AlienVault OTX:* `{alien.get('pulses_count', 0)}` ta global kiber-tahdid guruhida topildi.\n"
    report += f"📸 *Urlscan.io Tahlili:* Verdict: `{uscan.get('verdict', 'unknown').upper()}` (Score: {uscan.get('score', 0)}/100)\n"
    report += f"📅 *Domen Yoshi:* `{age_info.get('age_days', 'X')} kun` (Ochilgan sana: {age_info.get('created')})\n"

    if age_info.get("age_days", 365) < 30:
        report += f"\n⚠️ *DIQQAT:* Ushbu domen juda yangi ochilgan! Fishing sayt bo'lish ehtimoli juda yuqori!"

    # Cache the full result
    await cache.set_url_result(full_cache_key, {"report": report, "is_dangerous": is_dangerous})

    logger.info("URL scan complete: %s → %s", url, "DANGEROUS" if is_dangerous else "SAFE")
    return report, is_dangerous


# ─── COMPATIBILITY WRAPPERS ───────────────────────────────────────────────────

async def check_url(url: str, lang: str = "uz") -> str:
    """Simple wrapper — returns formatted report string."""
    report, _ = await check_url_complete(url, lang)
    return report


async def check_url_with_domain_age(url: str) -> dict:
    """Returns domain age dict — used by main.py for separate age display."""
    return await get_domain_age(url)
