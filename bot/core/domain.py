import whois
from urllib.parse import urlparse
from datetime import datetime

def get_domain_age(url: str) -> dict:
    """
    Returns domain age and creation date.
    Uses python-whois — free, no API key needed.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        if not domain:
            return {"success": False}

        w = whois.whois(domain)
        creation_date = w.creation_date

        # Sometimes it returns a list
        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if not creation_date:
            return {"success": False}

        # Calculate age
        now = datetime.now()
        age_days = (now - creation_date).days
        age_years = age_days // 365
        age_months = (age_days % 365) // 30

        # Format age string
        if age_years > 0:
            age_str = f"{age_years} yil" if age_years == 1 else f"{age_years} yil"
        elif age_months > 0:
            age_str = f"{age_months} oy"
        else:
            age_str = f"{age_days} kun"

        # Risk level based on age
        if age_days < 30:
            risk = "🔴 Juda yangi — Ehtiyot bo'ling!"
        elif age_days < 180:
            risk = "🟡 Nisbatan yangi"
        else:
            risk = "🟢 Eski domenlar odatda ishonchli"

        return {
            "success": True,
            "domain": domain,
            "created": creation_date.strftime("%Y-%m-%d"),
            "age_days": age_days,
            "age_str": age_str,
            "risk": risk
        }

    except Exception:
        return {"success": False}
