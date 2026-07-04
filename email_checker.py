import aiohttp

async def check_email_breach(email: str) -> dict:
    """
    Checks if email has been in a data breach using XposedOrNot API.
    100% Free API, no authentication needed!
    """
    url = f"https://api.xposedornot.com/v1/check-email/{email}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    breaches = data.get("breaches", [[]])[0]
                    return {
                        "success": True,
                        "compromised": True,
                        "breaches": breaches,
                        "count": len(breaches)
                    }
                elif resp.status == 404:
                    # 404 means the email was NOT found in any breaches (Safe)
                    return {"success": True, "compromised": False}
                else:
                    return {"success": False}
    except Exception:
        return {"success": False}
