import httpx
import logging
from datetime import datetime
from urllib.parse import urlparse
# config.py faylidan barcha API kalitlarini olamiz
from config import VIRUSTOTAL_API_KEY, GOOGLE_SAFE_BROWSING_KEY, ALIENVAULT_API_KEY, URLSCAN_API_KEY
 
logging.basicConfig(level=logging.INFO)
 
async def check_virustotal(url: str) -> dict:
    """VirusTotal v3 API orqali havolani tekshirish"""
    if not VIRUSTOTAL_API_KEY or "Sizning" in VIRUSTOTAL_API_KEY:
        return {"malicious": 0, "total": 0}
    
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    async with httpx.AsyncClient() as client:
        try:
            # Havolani tahlilga yuborish (Base64 encoding talab qilinishi mumkin, soddalashtirilgan)
            import base64
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            response = await client.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers, timeout=10)
            if response.status_code == 200:
                stats = response.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                return {"malicious": stats.get("malicious", 0), "total": sum(stats.values())}
        except Exception as e:
            logging.error(f"VirusTotal error: {e}")
    return {"malicious": 0, "total": 0}
 
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
            res = await client.post(endpoint, json=payload, timeout=10)
            if res.status_code == 200 and "matches" in res.json():
                return {"dangerous": True}
        except Exception as e:
            logging.error(f"Google Safe Browsing error: {e}")
    return {"dangerous": False}
 
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
            res = await client.get(endpoint, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                pulses = data.get("pulse_info", {}).get("pulses", [])
                # Agar ushbu domen kiber-tahdidlar ro'yxatida (Pulse) bo'lsa, xavfli deb hisoblaymiz
                return {"pulses_count": len(pulses), "dangerous": len(pulses) > 0}
        except Exception as e:
            logging.error(f"AlienVault error: {e}")
    return {"pulses_count": 0, "dangerous": False}
 
async def check_urlscan(url: str) -> dict:
    """Urlscan.io API orqali saytning chuqur xatti-harakatini tekshirish"""
    if not URLSCAN_API_KEY or "Sizning" in URLSCAN_API_KEY:
        return {"verdict": "unknown", "score": 0}
        
    headers = {"API-Key": URLSCAN_API_KEY, "Content-Type": "application/json"}
    payload = {"url": url, "visibility": "public"}
    
    async with httpx.AsyncClient() as client:
        try:
            # Urlscan biroz sekin ishlaydi, shuning uchun tezkor qidiruv xizmatidan foydalanamiz
            domain = urlparse(url).netloc
            search_endpoint = f"https://urlscan.io/api/v1/search/?q=domain:{domain}"
            res = await client.get(search_endpoint, headers=headers, timeout=10)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    # Oxirgi tahlil natijasidagi xavflilik darajasini tekshiramiz
                    verdict = results[0].get("verdict", {}).get("overall", {})
                    return {"verdict": "malicious" if verdict.get("malicious") else "clean", "score": verdict.get("score", 0)}
        except Exception as e:
            logging.error(f"Urlscan error: {e}")
    return {"verdict": "unknown", "score": 0}
 
async def get_domain_age(url: str) -> dict:
    """Soddalashtirilgan domen yoshi tekshiruvi (Whois API o'rniga bepul xizmatdan so'rov)"""
    domain = urlparse(url).netloc
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"https://rdap.org/domain/{domain}", timeout=5)
            if res.status_code == 200:
                events = res.json().get("events", [])
                for event in events:
                    if event.get("eventAction") == "registration":
                        reg_date_str = event.get("eventDate", "")[:10]
                        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
                        age_days = (datetime.now() - reg_date).days
                        return {"age_days": age_days, "created": reg_date_str}
        except Exception:
            pass
    return {"age_days": 365, "created": "Noma'lum"}
 
async def check_url_complete(url: str, lang: str) -> tuple:
    """Barcha 4 ta himoya qatlamini birlashtiruvchi bosh funksiya"""
    vt = await check_virustotal(url)
    gsb = await check_google_safe_browsing(url)
    alien = await check_alienvault(url)
    uscan = await check_urlscan(url)
    age_info = await get_domain_age(url)
    
    # Umumiy xavflilik xulosasi
    is_dangerous = (
        gsb.get("dangerous") or 
        vt.get("malicious", 0) > 0 or 
        alien.get("dangerous") or 
        uscan.get("verdict") == "malicious"
    )
    
    # Chiroyli Markdown hisobot matnini tuzamiz
    status_emoji = "🔴 ZARARLI / MALICIOUS" if is_dangerous else "✅ XAVFSIZ / CLEAN"
    
    report = f"🛡 *SafeLink Ko'p Qatlamli Havola Tahlili:*\n\n"
    report += f"🔗 *URL:* `{url}`\n"
    report += f"📊 *Yakuniy Xulosa:* *{status_emoji}*\n\n"
    
    report += f"🔍 *VirusTotal:* `{vt.get('malicious', 0)}` ta antivirus xavf aniqladi.\n"
    report += f"🌐 *Google Safe Browsing:* {'❌ Fishing/Tahdid bor' if gsb.get('dangerous') else '✅ Toza'}\n"
    report += f"👽 *AlienVault OTX:* `{alien.get('pulses_count', 0)}` ta global kiber-tahdid guruhida topildi.\n"
    report += f"📸 *Urlscan.io Tahlili:* Verdict: `{uscan.get('verdict', 'clear').upper()}` (Score: {uscan.get('score', 0)}/100)\n"
    report += f"📅 *Domen Yoshi:* `{age_info.get('age_days', 'X')} kun` (Ochilgan sana: {age_info.get('created')})\n"
    
    if age_info.get("age_days", 365) < 30:
        report += f"\n⚠️ *DIQQAT:* Ushbu domen juda yangi ochilgan! Fishing sayt bo'lish ehtimoli juda yuqori, ma'lumot kiritmang!"
        
    return report, is_dangerous
 
# ─── COMPATIBILITY WRAPPERS (used by main.py) ─────────────────────────────────
 
async def check_url(url: str, lang: str = "uz") -> str:
    """Simple wrapper — returns formatted report string."""
    report, _ = await check_url_complete(url, lang)
    return report
 
async def check_url_with_domain_age(url: str) -> dict:
    """Returns domain age dict — used by main.py for separate age display."""
    return await get_domain_age(url)
 

