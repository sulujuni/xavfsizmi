import aiohttp
from urllib.parse import urlparse
from checker import check_alienvault, check_google_safe_browsing

async def get_domain_reputation(url: str) -> dict:
    """
    Gets live localized reputation status data metrics for a domain profiles.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        if not domain:
            return {"success": False}
            
        gsb_res = await check_google_safe_browsing(url)
        av_res = await check_alienvault(url)
        
        score = 100
        indicators = []
        
        if gsb_res.get("success") and gsb_res.get("dangerous"):
            score -= 50
            indicators.append("Google Safe Browsing Flag")
            
        if av_res.get("success") and av_res.get("malicious"):
            score -= 40
            indicators.append(f"OTX Feeds Profile ({av_res.get('pulses', 1)})")

        return {
            "domain": domain,
            "suspicious_indicators": indicators,
            "score": max(score, 0)
        }
    except Exception:
        return {"success": False}
