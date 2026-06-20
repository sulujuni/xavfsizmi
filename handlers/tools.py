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


def trust_score_emoji(score: int, lang: str = "uz") -> str:
    """Returns appropriate emoji + label for a trust score in user's language."""
    labels = {
        "uz": ("Ishonchli", "Ehtiyot bo'ling", "Xavfli", "Juda xavfli!"),
        "ru": ("Надёжно", "Будьте осторожны", "Опасно", "Очень опасно!"),
        "en": ("Trusted", "Be careful", "Dangerous", "Very dangerous!"),
    }
    l = labels.get(lang, labels["en"])
    if score >= 80:
        return f"🟢 {score}/100 ({l[0]})"
    elif score >= 50:
        return f"🟡 {score}/100 ({l[1]})"
    elif score >= 25:
        return f"🟠 {score}/100 ({l[2]})"
    else:
        return f"🔴 {score}/100 ({l[3]})"


# ─── WEBSITE SCREENSHOT ───────────────────────────────────────────────────────

async def get_website_screenshot(url: str) -> str:
    """
    Gets a website screenshot by downloading it first, then returning the bytes path.
    Uses pikwy.com free screenshot API.
    Returns URL string or empty string if fails.
    """
    if not url.startswith("http"):
        url = f"https://{url}"

    from urllib.parse import quote
    encoded = quote(url, safe="")

    # Use multiple free screenshot services, try until one works
    services = [
        f"https://api.pikwy.com/web/screenshot?url={encoded}&w=1280&h=800&format=png",
        f"https://shot.screenshotapi.net/screenshot?url={encoded}&output=image&file_type=png&wait_for_event=load",
    ]

    async with aiohttp.ClientSession() as session:
        for service_url in services:
            try:
                async with session.get(
                    service_url,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get("content-type", "")
                        if "image" in content_type:
                            # Download image bytes and save temporarily
                            image_data = await resp.read()
                            if len(image_data) > 5000:  # Valid image should be > 5KB
                                import tempfile, os
                                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                                tmp.write(image_data)
                                tmp.close()
                                return tmp.name
            except Exception:
                continue

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

async def check_privacy_score(profile_url: str, lang: str = "uz") -> dict:
    """
    Checks basic public exposure of a social media profile.
    Uses multiple signals: page accessibility, meta tags, visible text.
    Avoids false positives from JavaScript/CSS code.
    """
    PRIVACY_TEXTS = {
        "uz": {
            "profile_public": "Profil hammaga ochiq (login talab qilinmaydi)",
            "profile_private": "Profil yopiq yoki login talab qiladi",
            "username_visible": "Username/nom ommaviy ko'rinadi",
            "bio_has_contacts": "Bio/tavsifda aloqa ma'lumotlari bor",
            "bio_clean": "Bio/tavsifda shaxsiy ma'lumot ko'rinmaydi",
            "rec_private": "Profilni yopiq (private) rejimga o'tkazing",
            "rec_remove_contacts": "Bio'dan telefon/email ni olib tashlang",
            "rec_good": "Profilingiz yaxshi himoyalangan!",
            "access_error": "Profilga kirish imkoni bo'lmadi",
            "posts_public": "Postlar/kontentlar ommaviy",
            "rec_limit_posts": "Postlar ko'rinishini faqat do'stlarga cheklang",
        },
        "ru": {
            "profile_public": "Профиль публичный (вход не требуется)",
            "profile_private": "Профиль закрыт или требует входа",
            "username_visible": "Имя пользователя публично видно",
            "bio_has_contacts": "В био есть контактные данные",
            "bio_clean": "В био нет личных данных",
            "rec_private": "Переключите профиль в приватный режим",
            "rec_remove_contacts": "Уберите телефон/email из био",
            "rec_good": "Ваш профиль хорошо защищён!",
            "access_error": "Не удалось получить доступ к профилю",
            "posts_public": "Публикации видны всем",
            "rec_limit_posts": "Ограничьте видимость постов только для друзей",
        },
        "en": {
            "profile_public": "Profile is public (no login required)",
            "profile_private": "Profile is private or requires login",
            "username_visible": "Username/name is publicly visible",
            "bio_has_contacts": "Bio contains contact information",
            "bio_clean": "Bio has no exposed personal data",
            "rec_private": "Switch your profile to private mode",
            "rec_remove_contacts": "Remove phone/email from your bio",
            "rec_good": "Your profile is well-protected!",
            "access_error": "Could not access profile",
            "posts_public": "Posts/content are publicly visible",
            "rec_limit_posts": "Limit post visibility to friends only",
        },
    }

    pt = PRIVACY_TEXTS.get(lang, PRIVACY_TEXTS["en"])
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
                timeout=aiohttp.ClientTimeout(total=10),
                allow_redirects=True,
            ) as resp:
                final_url = str(resp.url)
                if resp.status != 200:
                    return {"score": -1, "error": pt["access_error"]}
                html = await resp.text()
        except Exception:
            return {"score": -1, "error": pt["access_error"]}

    # ── Check 1: Is profile publicly accessible? ──────────────────────────────
    # If we got a 200 and the page has real content (not a login redirect)
    login_indicators = ["login", "sign in", "log in", "accounts/login", "kirish"]
    is_login_page = any(indicator in html.lower()[:5000] for indicator in login_indicators)
    # Also check for redirect to login
    is_redirected_to_login = "login" in final_url.lower() or "accounts" in final_url.lower()

    if is_login_page or is_redirected_to_login:
        # Profile is likely private
        score -= 0  # No penalty for private
        findings.append(pt["profile_private"])
    else:
        # Profile is public
        score -= 20
        findings.append(pt["profile_public"])
        recommendations.append(pt["rec_private"])

    # ── Check 2: Extract ONLY visible text content (not JavaScript/CSS) ───────
    # Remove script and style tags
    import re as _re
    clean_html = _re.sub(r'<script[^>]*>.*?</script>', '', html, flags=_re.DOTALL | _re.IGNORECASE)
    clean_html = _re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=_re.DOTALL | _re.IGNORECASE)
    # Remove all HTML tags to get just text
    visible_text = _re.sub(r'<[^>]+>', ' ', clean_html)
    # Only look at first 3000 chars of visible text (bio area)
    visible_text = visible_text[:3000]

    # ── Check 3: Contact info in visible bio text ─────────────────────────────
    # Real email pattern (not in URLs/code)
    emails_in_text = _re.findall(r'\b[A-Za-z0-9._%+-]+@(?:gmail|yahoo|mail|outlook|hotmail|icloud)\.[a-z]{2,}\b', visible_text)
    # Real phone pattern (starts with + or country code, not random numbers)
    phones_in_text = _re.findall(r'[\+]?[0-9]{1,3}[-\s]?[(]?[0-9]{2,3}[)]?[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}', visible_text)

    if emails_in_text or phones_in_text:
        score -= 25
        findings.append(pt["bio_has_contacts"])
        recommendations.append(pt["rec_remove_contacts"])
    else:
        findings.append(pt["bio_clean"])

    # ── Check 4: Are posts/content visible? ───────────────────────────────────
    # Check for content indicators (images, posts, media counts)
    content_indicators = ["data-media-count", "edge_owner_to_timeline", "posts", "postlar", "публикации"]
    has_public_content = any(ind in html.lower() for ind in content_indicators)

    if has_public_content and not is_login_page:
        score -= 15
        findings.append(pt["posts_public"])
        recommendations.append(pt["rec_limit_posts"])

    # ── Final ─────────────────────────────────────────────────────────────────
    if not recommendations:
        recommendations.append(pt["rec_good"])

    return {
        "score": max(0, min(100, score)),
        "findings": findings,
        "recommendations": recommendations,
        "url": profile_url,
    }



# ─── SECURITY HEADERS CHECK ───────────────────────────────────────────────────

IMPORTANT_HEADERS = {
    "strict-transport-security": "HSTS",
    "content-security-policy": "CSP",
    "x-frame-options": "X-Frame-Options",
    "x-content-type-options": "X-Content-Type",
    "x-xss-protection": "XSS Protection",
    "referrer-policy": "Referrer-Policy",
    "permissions-policy": "Permissions-Policy",
}


async def check_security_headers(url: str) -> dict:
    """
    Checks website security headers.
    Returns a dict with score, present headers, missing headers.
    """
    if not url.startswith("http"):
        url = f"https://{url}"

    result = {
        "success": False,
        "https": False,
        "headers_present": [],
        "headers_missing": [],
        "score": 0,
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(url)
            response_headers = {k.lower(): v for k, v in resp.headers.items()}

            # Check HTTPS
            result["https"] = str(resp.url).startswith("https")
            score = 30 if result["https"] else 0

            # Check important security headers
            for header_key, header_name in IMPORTANT_HEADERS.items():
                if header_key in response_headers:
                    result["headers_present"].append(header_name)
                    score += 10
                else:
                    result["headers_missing"].append(header_name)

            result["score"] = min(100, score)
            result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


def format_security_headers(headers_result: dict, lang: str = "uz") -> str:
    """Formats the security headers result for the URL report."""
    if not headers_result.get("success"):
        return ""

    labels = {
        "uz": "Xavfsizlik Headerlari",
        "ru": "Заголовки Безопасности",
        "en": "Security Headers",
    }
    title = labels.get(lang, labels["en"])

    total = len(IMPORTANT_HEADERS) + 1  # +1 for HTTPS
    present = len(headers_result["headers_present"]) + (1 if headers_result["https"] else 0)
    text = f"\n🔒 *{title}:* `{present}/{total}`\n"

    # HTTPS
    if headers_result["https"]:
        text += f"  ✅ HTTPS\n"
    else:
        text += f"  ❌ HTTPS\n"

    # Missing headers
    for h in headers_result["headers_missing"][:4]:
        text += f"  ❌ {h}\n"

    # Present headers (first 2)
    for h in headers_result["headers_present"][:2]:
        text += f"  ✅ {h}\n"

    if len(headers_result["headers_present"]) > 2:
        text += f"  ✅ +{len(headers_result['headers_present']) - 2}\n"

    return text


# ─── TECHNOLOGY DETECTION ─────────────────────────────────────────────────────

TECH_SIGNATURES = {
    "wp-content": "WordPress", "wp-includes": "WordPress",
    "Joomla": "Joomla", "drupal": "Drupal",
    "wix.com": "Wix", "squarespace": "Squarespace", "shopify": "Shopify",
    "next/static": "Next.js", "__next": "Next.js", "nuxt": "Nuxt.js",
    "react": "React", "angular": "Angular", "vue": "Vue.js",
    "cloudflare": "Cloudflare",
    "google-analytics": "Google Analytics", "gtag": "Google Analytics",
    "facebook.net/en_US/fbevents": "Facebook Pixel",
    "mc.yandex.ru/metrika": "Yandex Metrika",
}


async def detect_technologies(url: str) -> list:
    """Detects technologies used by a website."""
    if not url.startswith("http"):
        url = f"https://{url}"

    detected = set()

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(url)
            html = resp.text.lower()

            for signature, tech_name in TECH_SIGNATURES.items():
                if signature.lower() in html:
                    detected.add(tech_name)

            server = resp.headers.get("server", "").lower()
            if "nginx" in server:
                detected.add("Nginx")
            elif "apache" in server:
                detected.add("Apache")
            elif "cloudflare" in server:
                detected.add("Cloudflare")

            powered_by = resp.headers.get("x-powered-by", "").lower()
            if "php" in powered_by:
                detected.add("PHP")
            elif "express" in powered_by:
                detected.add("Express.js")
            elif "asp.net" in powered_by:
                detected.add("ASP.NET")

    except Exception:
        pass

    return list(detected)[:6]


def format_technologies(techs: list, lang: str = "uz") -> str:
    """Formats detected technologies for the URL report."""
    if not techs:
        return ""

    labels = {"uz": "Texnologiyalar", "ru": "Технологии", "en": "Technologies"}
    title = labels.get(lang, labels["en"])
    tech_str = ", ".join([f"`{t}`" for t in techs])
    return f"🛠 *{title}:* {tech_str}\n"



# ─── HOMOGLYPH DETECTOR ──────────────────────────────────────────────────────

# Map of Unicode characters that look like ASCII but aren't
HOMOGLYPHS = {
    '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
    '\u0441': 'c', '\u0443': 'y', '\u0445': 'x', '\u0455': 's',
    '\u0456': 'i', '\u0458': 'j', '\u0501': 'd', '\u0261': 'g',
    '\u03bd': 'v', '\u1d0d': 'm', '\u1d0f': 'o', '\u1d1b': 't',
    '\u2113': 'l', '\u2170': 'i',
    '\u200b': '', '\u200c': '', '\u200d': '', '\ufeff': '',
}


def check_homoglyphs(url: str) -> dict:
    """Detects Unicode lookalike characters in URLs (homoglyph attack)."""
    parsed = urlparse(url if url.startswith("http") else f"https://{url}")
    domain = (parsed.netloc or parsed.path).lower()

    found_homoglyphs = []
    has_zero_width = False
    cleaned_domain = ""

    for char in domain:
        if char in HOMOGLYPHS:
            replacement = HOMOGLYPHS[char]
            if replacement == "":
                has_zero_width = True
            else:
                found_homoglyphs.append({"char": char, "looks_like": replacement, "unicode": f"U+{ord(char):04X}"})
            cleaned_domain += replacement
        else:
            cleaned_domain += char

    return {
        "is_homoglyph": len(found_homoglyphs) > 0 or has_zero_width,
        "domain": domain,
        "cleaned_domain": cleaned_domain if (found_homoglyphs or has_zero_width) else domain,
        "found": found_homoglyphs[:5],
        "has_zero_width": has_zero_width,
    }


def format_homoglyph_warning(result: dict, lang: str = "uz") -> str:
    """Formats homoglyph detection result for the URL report."""
    if not result.get("is_homoglyph"):
        return ""
    labels = {
        "uz": ("YASHIRIN BELGILAR ANIQLANDI", "Soxta belgilar ishlatilgan", "Aslida", "Ko'rinmas belgilar bor"),
        "ru": ("СКРЫТЫЕ СИМВОЛЫ ОБНАРУЖЕНЫ", "Использованы поддельные символы", "На самом деле", "Есть невидимые символы"),
        "en": ("HIDDEN CHARACTERS DETECTED", "Fake lookalike characters used", "Actually", "Contains invisible chars"),
    }
    l = labels.get(lang, labels["en"])
    text = f"\n🚨 *{l[0]}!*\n⚠️ {l[1]}!\n"
    if result["found"]:
        text += f"🔤 {l[2]}: `{result['cleaned_domain']}`\n"
    if result["has_zero_width"]:
        text += f"👻 {l[3]}!\n"
    return text


# ─── DARK WEB MENTION CHECKER ─────────────────────────────────────────────────

async def check_dark_web_mentions(query: str) -> dict:
    """Checks if email/username appears in dark web databases."""
    results = {"query": query, "found_in": [], "total_mentions": 0, "sources_checked": 0}

    async with aiohttp.ClientSession() as session:
        # XposedOrNot breach + paste check
        if "@" in query:
            try:
                async with session.get(
                    f"https://api.xposedornot.com/v1/breach-analytics?email={query}",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    results["sources_checked"] += 1
                    if resp.status == 200:
                        data = await resp.json()
                        breaches = data.get("BreachesSummary", {}).get("site", "")
                        if breaches:
                            results["found_in"].append("Data Breaches")
                            results["total_mentions"] += len(breaches.split(";")) if breaches else 0
                        pastes = data.get("PastesSummary", {}).get("cnt", 0)
                        if pastes and int(pastes) > 0:
                            results["found_in"].append("Paste Sites")
                            results["total_mentions"] += int(pastes)
            except Exception:
                pass

        # LeakCheck public API
        try:
            async with session.get(
                f"https://leakcheck.io/api/public?check={query}",
                timeout=aiohttp.ClientTimeout(total=8),
            ) as resp:
                results["sources_checked"] += 1
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("found"):
                        results["found_in"].append("Leak Databases")
                        results["total_mentions"] += data.get("found", 0)
        except Exception:
            pass

    return results


# ─── APK PERMISSION EXPLAINER (Premium) ───────────────────────────────────────

DANGEROUS_PERMISSIONS = {
    "READ_CONTACTS", "CAMERA", "RECORD_AUDIO", "READ_SMS", "SEND_SMS",
    "ACCESS_FINE_LOCATION", "READ_PHONE_STATE", "READ_EXTERNAL_STORAGE",
    "SYSTEM_ALERT_WINDOW", "REQUEST_INSTALL_PACKAGES",
    "BIND_ACCESSIBILITY_SERVICE", "BIND_DEVICE_ADMIN", "READ_CALL_LOG",
}

PERMISSION_EXPLANATIONS = {
    "uz": {
        "INTERNET": ("🌐 Internet", "Internetga ulanadi — normal"),
        "READ_CONTACTS": ("📇 Kontaktlar", "Barcha kontaktlaringizni ko'radi!"),
        "CAMERA": ("📷 Kamera", "Kamerangizni yoqishi mumkin!"),
        "RECORD_AUDIO": ("🎙 Mikrofon", "Tinglashi mumkin!"),
        "READ_SMS": ("💬 SMS o'qish", "SMS larni o'qiydi!"),
        "SEND_SMS": ("📤 SMS yuborish", "Nomingizdan SMS yuboradi!"),
        "ACCESS_FINE_LOCATION": ("📍 Aniq joy", "GPS joylashuvingizni biladi!"),
        "ACCESS_COARSE_LOCATION": ("📍 Taxminiy joy", "Taxminiy joylashuvni biladi"),
        "READ_PHONE_STATE": ("📱 Telefon", "Raqam va IMEI ni o'qiydi!"),
        "WRITE_EXTERNAL_STORAGE": ("💾 Yozish", "Fayllar yozadi"),
        "READ_EXTERNAL_STORAGE": ("💾 O'qish", "Barcha fayllarni ko'radi!"),
        "RECEIVE_BOOT_COMPLETED": ("🔄 Avtostart", "O'zi ishga tushadi"),
        "SYSTEM_ALERT_WINDOW": ("🪟 Ustidan", "Boshqa ilovalar ustida!"),
        "REQUEST_INSTALL_PACKAGES": ("📦 O'rnatish", "Boshqa ilovalar o'rnatadi!"),
        "BIND_ACCESSIBILITY_SERVICE": ("♿ Accessibility", "Hammani o'qiydi!"),
        "BIND_DEVICE_ADMIN": ("🔐 Admin", "Telefonni boshqaradi!"),
        "READ_CALL_LOG": ("📞 Qo'ng'iroqlar", "Kim bilan gaplashganingizni biladi!"),
    },
    "ru": {
        "INTERNET": ("🌐 Интернет", "Подключается к интернету — нормально"),
        "READ_CONTACTS": ("📇 Контакты", "Видит все контакты!"),
        "CAMERA": ("📷 Камера", "Может включить камеру!"),
        "RECORD_AUDIO": ("🎙 Микрофон", "Может слушать!"),
        "READ_SMS": ("💬 Чтение SMS", "Читает все SMS!"),
        "SEND_SMS": ("📤 Отправка SMS", "Отправляет SMS от вас!"),
        "ACCESS_FINE_LOCATION": ("📍 Точное место", "Знает GPS координаты!"),
        "ACCESS_COARSE_LOCATION": ("📍 Примерное место", "Знает примерное место"),
        "READ_PHONE_STATE": ("📱 Телефон", "Читает номер и IMEI!"),
        "WRITE_EXTERNAL_STORAGE": ("💾 Запись", "Записывает файлы"),
        "READ_EXTERNAL_STORAGE": ("💾 Чтение", "Видит все файлы!"),
        "RECEIVE_BOOT_COMPLETED": ("🔄 Автозапуск", "Запускается сам"),
        "SYSTEM_ALERT_WINDOW": ("🪟 Поверх", "Поверх других приложений!"),
        "REQUEST_INSTALL_PACKAGES": ("📦 Установка", "Устанавливает другие приложения!"),
        "BIND_ACCESSIBILITY_SERVICE": ("♿ Accessibility", "Читает всё на экране!"),
        "BIND_DEVICE_ADMIN": ("🔐 Админ", "Управляет телефоном!"),
        "READ_CALL_LOG": ("📞 Звонки", "Знает кому вы звонили!"),
    },
    "en": {
        "INTERNET": ("🌐 Internet", "Connects to internet — normal"),
        "READ_CONTACTS": ("📇 Contacts", "Can see all contacts!"),
        "CAMERA": ("📷 Camera", "Can activate camera!"),
        "RECORD_AUDIO": ("🎙 Microphone", "Can listen through mic!"),
        "READ_SMS": ("💬 Read SMS", "Reads all your texts!"),
        "SEND_SMS": ("📤 Send SMS", "Sends SMS as you!"),
        "ACCESS_FINE_LOCATION": ("📍 Exact Location", "Knows GPS location!"),
        "ACCESS_COARSE_LOCATION": ("📍 Approx Location", "Knows approximate location"),
        "READ_PHONE_STATE": ("📱 Phone State", "Reads number and IMEI!"),
        "WRITE_EXTERNAL_STORAGE": ("💾 Write Storage", "Writes files"),
        "READ_EXTERNAL_STORAGE": ("💾 Read Storage", "Sees all files!"),
        "RECEIVE_BOOT_COMPLETED": ("🔄 Auto-start", "Starts on boot"),
        "SYSTEM_ALERT_WINDOW": ("🪟 Overlay", "Displays over other apps!"),
        "REQUEST_INSTALL_PACKAGES": ("📦 Install", "Installs other apps!"),
        "BIND_ACCESSIBILITY_SERVICE": ("♿ Accessibility", "Reads everything on screen!"),
        "BIND_DEVICE_ADMIN": ("🔐 Device Admin", "Controls your phone!"),
        "READ_CALL_LOG": ("📞 Call Log", "Knows who you called!"),
    },
}


def explain_permissions(permissions: list, lang: str = "uz") -> tuple:
    """Premium: explains what each APK permission actually does. Returns (text, dangerous_count)."""
    explanations = PERMISSION_EXPLANATIONS.get(lang, PERMISSION_EXPLANATIONS["en"])
    text = ""
    dangerous_count = 0

    for perm in permissions[:12]:
        perm_name = perm.get("name", "").upper()
        if perm_name in explanations:
            label, desc = explanations[perm_name]
            is_dangerous = perm_name in DANGEROUS_PERMISSIONS
            emoji = "🔴" if is_dangerous else "🟢"
            text += f"  {emoji} *{label}*\n      {desc}\n"
            if is_dangerous:
                dangerous_count += 1
        else:
            text += f"  ⚪ `{perm.get('name', perm_name)}`\n"

    return text, dangerous_count
