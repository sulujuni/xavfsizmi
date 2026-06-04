"""
Advanced security tool utilities:
- Website screenshot (via urlscan.io)
- Short URL expander
- SSL certificate checker
- Redirect chain tracker
- Typosquatting detector
- Social media scam checker
- Privacy score analyzer
- Trust score calculator
"""
import ssl
import socket
import re
import asyncio
import logging
from urllib.parse import urlparse
from datetime import datetime

import httpx
import aiohttp

from config import URLSCAN_API_KEY, VIRUSTOTAL_API_KEY

# ─── POPULAR DOMAINS for typosquatting detection ──────────────────────────────

POPULAR_DOMAINS = [
    "google.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "amazon.com", "netflix.com", "paypal.com", "apple.com",
    "microsoft.com", "linkedin.com", "whatsapp.com", "telegram.org",
    "tiktok.com", "reddit.com", "wikipedia.org", "yahoo.com", "bing.com",
    "github.com", "stackoverflow.com", "twitch.tv", "discord.com",
    "spotify.com", "zoom.us", "dropbox.com", "icloud.com", "outlook.com",
    "gmail.com", "bank.com", "chase.com", "wellsfargo.com",
    "olx.uz", "uzum.uz", "payme.uz", "click.uz", "kapitalbank.uz",
]


# ─── TRUST SCORE CALCULATOR ──────────────────────────────────────────────────

def calculate_trust_score(vt_res: dict, gsb_res: dict, alien_res: dict,
                          uscan_res: dict, domain_age_days: int) -> int:
    """
    Calculates a 0-100 trust score based on multiple signals.
    100 = completely safe, 0 = extremely dangerous.
    """
    score = 100

    # VirusTotal: each malicious engine = -8 points
    mal = vt_res.get("malicious", 0)
    score -= mal * 8

    # Google Safe Browsing: dangerous = -30
    if gsb_res.get("dangerous"):
        score -= 30

    # AlienVault: each pulse = -5
    pulses = alien_res.get("pulses_count", 0)
    score -= min(pulses * 5, 25)

    # URLScan: malicious verdict = -20
    if uscan_res.get("verdict") == "malicious":
        score -= 20

    # Domain age: very new domains lose points
    if domain_age_days < 7:
        score -= 25
    elif domain_age_days < 30:
        score -= 15
    elif domain_age_days < 90:
        score -= 5

    return max(0, min(100, score))


def trust_score_emoji(score: int) -> str:
    """Returns appropriate emoji + label for a trust score."""
    if score >= 80:
        return f"🟢 {score}/100 (Ishonchli)"
    elif score >= 50:
        return f"🟡 {score}/100 (Ehtiyot bo'ling)"
    elif score >= 25:
        return f"🟠 {score}/100 (Xavfli)"
    else:
        return f"🔴 {score}/100 (Juda xavfli!)"


# ─── WEBSITE SCREENSHOT ───────────────────────────────────────────────────────

async def get_website_screenshot(url: str) -> str:
    """
    Submits URL to urlscan.io and returns the screenshot URL.
    Returns empty string if fails.
    """
    if not URLSCAN_API_KEY:
        return ""

    headers = {"API-Key": URLSCAN_API_KEY, "Content-Type": "application/json"}
    payload = {"url": url, "visibility": "public"}

    async with aiohttp.ClientSession() as session:
        try:
            # Submit scan
            async with session.post(
                "https://urlscan.io/api/v1/scan/",
                headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return ""
                data = await resp.json()
                scan_uuid = data.get("uuid", "")

            if not scan_uuid:
                return ""

            # Wait for scan to complete (max 30s)
            await asyncio.sleep(15)

            # Get result
            async with session.get(
                f"https://urlscan.io/api/v1/result/{scan_uuid}/",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("task", {}).get("screenshotURL", "")
        except Exception as e:
            logging.error(f"Screenshot error: {e}")

    return ""


# ─── SHORT URL EXPANDER ───────────────────────────────────────────────────────

SHORT_URL_SERVICES = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "adf.ly", "shorte.st", "tiny.cc", "cutt.ly", "rb.gy",
    "shorturl.at", "t.me", "rebrand.ly", "bl.ink",
]


def is_short_url(url: str) -> bool:
    """Check if URL is from a known URL shortener."""
    parsed = urlparse(url if url.startswith("http") else f"https://{url}")
    domain = parsed.netloc.lower().replace("www.", "")
    return domain in SHORT_URL_SERVICES


async def expand_short_url(url: str) -> dict:
    """
    Follows redirects to expand a shortened URL.
    Returns dict with final_url, redirect_count, all hops.
    """
    if not url.startswith("http"):
        url = f"https://{url}"

    hops = [url]
    final_url = url

    async with httpx.AsyncClient(follow_redirects=False, timeout=10) as client:
        try:
            current = url
            for _ in range(15):  # max 15 redirects
                resp = await client.get(current)
                if resp.status_code in (301, 302, 303, 307, 308):
                    location = resp.headers.get("location", "")
                    if not location:
                        break
                    # Handle relative redirects
                    if location.startswith("/"):
                        parsed = urlparse(current)
                        location = f"{parsed.scheme}://{parsed.netloc}{location}"
                    hops.append(location)
                    current = location
                else:
                    final_url = current
                    break
            else:
                final_url = current
        except Exception:
            pass

    return {
        "original": url,
        "final_url": final_url if len(hops) > 1 else url,
        "hops": hops,
        "redirect_count": len(hops) - 1,
    }


# ─── SSL CERTIFICATE CHECKER ─────────────────────────────────────────────────

async def check_ssl_certificate(url: str) -> dict:
    """
    Checks SSL certificate of a domain.
    Returns issuer, expiry, days_remaining, is_valid.
    """
    parsed = urlparse(url if url.startswith("http") else f"https://{url}")
    hostname = parsed.netloc or parsed.path
    hostname = hostname.split(":")[0]  # remove port

    try:
        # Run in executor since ssl is blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _get_ssl_info, hostname)
        return result
    except Exception as e:
        return {"valid": False, "error": str(e)}


def _get_ssl_info(hostname: str) -> dict:
    """Blocking function to get SSL certificate info."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        # Parse cert info
        issuer_parts = dict(x[0] for x in cert.get("issuer", []))
        issuer = issuer_parts.get("organizationName", "Unknown")

        # Expiry
        not_after = cert.get("notAfter", "")
        expiry_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        days_remaining = (expiry_date - datetime.now()).days

        # Subject
        subject_parts = dict(x[0] for x in cert.get("subject", []))
        common_name = subject_parts.get("commonName", hostname)

        return {
            "valid": True,
            "issuer": issuer,
            "common_name": common_name,
            "expiry": not_after,
            "days_remaining": days_remaining,
            "expired": days_remaining < 0,
        }
    except ssl.SSLCertVerificationError as e:
        return {"valid": False, "error": f"SSL verification failed: {e}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


# ─── REDIRECT CHAIN TRACKER ──────────────────────────────────────────────────

async def get_redirect_chain(url: str) -> dict:
    """Same as expand_short_url but works for any URL."""
    return await expand_short_url(url)


# ─── TYPOSQUATTING DETECTOR ───────────────────────────────────────────────────

def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def check_typosquatting(url: str) -> dict:
    """
    Checks if a URL's domain is suspiciously similar to a popular domain.
    Returns matched domain and similarity info if detected.
    """
    parsed = urlparse(url if url.startswith("http") else f"https://{url}")
    domain = (parsed.netloc or parsed.path).lower().replace("www.", "")

    # Remove port if present
    domain = domain.split(":")[0]

    # Extract base domain (without TLD)
    parts = domain.split(".")
    if len(parts) < 2:
        return {"is_typosquat": False}

    results = []
    for popular in POPULAR_DOMAINS:
        # Exact match = not typosquat
        if domain == popular:
            return {"is_typosquat": False, "exact_match": popular}

        distance = _levenshtein_distance(domain, popular)

        # If edit distance is 1-2, it's likely typosquatting
        if 0 < distance <= 2:
            results.append({
                "similar_to": popular,
                "distance": distance,
            })

    if results:
        # Sort by distance (closest first)
        results.sort(key=lambda x: x["distance"])
        return {
            "is_typosquat": True,
            "matches": results[:3],
            "domain": domain,
        }

    return {"is_typosquat": False, "domain": domain}


# ─── SOCIAL MEDIA SCAM CHECKER ────────────────────────────────────────────────

async def check_social_account(username: str) -> dict:
    """
    Checks a username/phone against community scam databases.
    Uses multiple open APIs.
    """
    # Clean input
    username = username.strip().lstrip("@")

    results = {
        "username": username,
        "reports_found": 0,
        "sources_checked": 0,
        "warnings": [],
    }

    async with aiohttp.ClientSession() as session:
        # Check against SpamWatch API (Telegram anti-spam)
        try:
            async with session.get(
                f"https://api.spamwat.ch/banlist/{username}",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                results["sources_checked"] += 1
                if resp.status == 200:
                    results["reports_found"] += 1
                    results["warnings"].append("SpamWatch: Banned for spam/scam")
        except Exception:
            pass

        # Check if account is very new (Telegram-specific check via bot API isn't available)
        # We'll do a basic web check
        try:
            async with session.get(
                f"https://t.me/{username}",
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=True,
            ) as resp:
                results["sources_checked"] += 1
                text = await resp.text()
                if "tgme_page_extra" not in text and resp.status == 200:
                    results["warnings"].append("Telegram: Account may not exist or is restricted")
        except Exception:
            pass

    return results


# ─── PRIVACY SCORE ANALYZER ──────────────────────────────────────────────────

async def check_privacy_score(profile_url: str) -> dict:
    """
    Checks what info is publicly visible on a social media profile.
    Returns a privacy score 0-100 and recommendations.
    """
    score = 100
    findings = []
    recommendations = []

    async with aiohttp.ClientSession() as session:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            async with session.get(
                profile_url, headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    return {"score": -1, "error": "Could not access profile"}
                text = await resp.text()
        except Exception as e:
            return {"score": -1, "error": str(e)}

    # Check for exposed personal info patterns
    # Email patterns
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if emails:
        score -= 20
        findings.append(f"Email exposed: {len(emails)} found")
        recommendations.append("Hide your email from public view")

    # Phone patterns
    phones = re.findall(r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}', text)
    if phones:
        score -= 25
        findings.append(f"Phone numbers exposed: {len(phones)} found")
        recommendations.append("Remove phone number from public profile")

    # Location/address patterns
    location_keywords = ["street", "avenue", "city", "address", "location",
                         "район", "город", "адрес", "ko'cha", "shahar"]
    for kw in location_keywords:
        if kw.lower() in text.lower():
            score -= 10
            findings.append("Location/address info may be visible")
            recommendations.append("Consider hiding your exact location")
            break

    # Birth date patterns
    date_patterns = re.findall(r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b', text)
    if date_patterns:
        score -= 15
        findings.append("Birth date may be visible")
        recommendations.append("Hide your date of birth")

    # Full name in title/meta
    if '<title>' in text:
        score -= 5  # Profile is public
        findings.append("Profile is publicly accessible")

    if not findings:
        findings.append("No obvious personal data exposure detected")

    if not recommendations:
        recommendations.append("Your profile looks well-protected!")

    return {
        "score": max(0, score),
        "findings": findings,
        "recommendations": recommendations,
        "url": profile_url,
    }
