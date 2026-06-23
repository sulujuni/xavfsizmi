"""
Website reputation scoring — Phase 2 aligned.

Combines Google Safe Browsing + AlienVault OTX signals into a single
0-100 reputation score. Uses the cached, rate-limited checker functions.
"""

from urllib.parse import urlparse
from checker import check_alienvault, check_google_safe_browsing
from logger import get_logger

logger = get_logger("reputation")


async def get_domain_reputation(url: str) -> dict:
    """
    Returns a reputation profile for a domain:
      - domain: the parsed domain
      - score: 0-100 (100 = clean, lower = riskier)
      - suspicious_indicators: list of triggered flags
      - success: whether the lookup completed
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

        # Google Safe Browsing returns {"dangerous": bool, "threats": [...]}
        if gsb_res.get("dangerous"):
            score -= 50
            threats = gsb_res.get("threats", [])
            label = ", ".join(threats) if threats else "Flagged"
            indicators.append(f"Google Safe Browsing: {label}")

        # AlienVault returns {"pulses_count": int, "dangerous": bool}
        if av_res.get("dangerous"):
            score -= 40
            indicators.append(f"AlienVault OTX ({av_res.get('pulses_count', 0)} threat feeds)")

        return {
            "success": True,
            "domain": domain,
            "suspicious_indicators": indicators,
            "score": max(score, 0),
        }
    except Exception as e:
        logger.error("Reputation lookup failed for %s: %s", url, e)
        return {"success": False}
