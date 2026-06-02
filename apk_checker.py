import aiohttp
import asyncio
from config import VIRUSTOTAL_API_KEY

async def scan_apk(file_bytes: bytes, filename: str) -> dict:
    """
    Uploads an APK to VirusTotal and waits for the scan result.
    Returns a dict with malicious, suspicious, harmless counts.
    """
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}

    async with aiohttp.ClientSession() as session:

        # Step 1 — Upload the file
        form = aiohttp.FormData()
        form.add_field(
            "file", file_bytes,
            filename=filename,
            content_type="application/vnd.android.package-archive"
        )
        async with session.post(
            "https://www.virustotal.com/api/v3/files",
            headers=headers,
            data=form
        ) as resp:
            if resp.status != 200:
                return {"success": False}
            data = await resp.json()
            analysis_id = data["data"]["id"]

        # Step 2 — Poll for results (scan takes 20-60 seconds)
        for _ in range(12):
            await asyncio.sleep(10)
            async with session.get(
                f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                headers=headers
            ) as resp:
                result = await resp.json()
                status = result["data"]["attributes"]["status"]

                if status == "completed":
                    stats = result["data"]["attributes"]["stats"]
                    return {
                        "success": True,
                        "malicious": stats.get("malicious", 0),
                        "suspicious": stats.get("suspicious", 0),
                        "harmless": stats.get("harmless", 0),
                        "undetected": stats.get("undetected", 0),
                        "total": sum(stats.values())
                    }

        # Timed out
        return {"success": False, "timeout": True}
