"""
APK Malware Scanner via VirusTotal API v3.
Includes behavioral/sandbox analysis: permissions, network calls, file activity.
"""
import aiohttp
import asyncio
from bot.config import VIRUSTOTAL_API_KEY


async def scan_apk(file_bytes: bytes, filename: str) -> dict:
    """
    Uploads an APK to VirusTotal and waits for the scan result.
    Returns a dict with malicious, suspicious, harmless counts
    plus behavioral data (permissions, network calls).
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
        file_sha256 = None
        for _ in range(12):
            await asyncio.sleep(10)
            async with session.get(
                f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                headers=headers
            ) as resp:
                result = await resp.json()
                attrs = result["data"]["attributes"]
                status = attrs["status"]

                if status == "completed":
                    stats = attrs["stats"]
                    # Try to get the file hash for behavioral lookup
                    meta = result.get("meta", {}).get("file_info", {})
                    file_sha256 = meta.get("sha256", "")

                    base_result = {
                        "success": True,
                        "malicious": stats.get("malicious", 0),
                        "suspicious": stats.get("suspicious", 0),
                        "harmless": stats.get("harmless", 0),
                        "undetected": stats.get("undetected", 0),
                        "total": sum(stats.values()),
                    }

                    # Try to get behavioral data
                    if file_sha256:
                        behavior = await _get_behavior_report(session, headers, file_sha256)
                        base_result.update(behavior)

                    return base_result

        # Timed out
        return {"success": False, "timeout": True}


async def _get_behavior_report(session: aiohttp.ClientSession, headers: dict, sha256: str) -> dict:
    """
    Fetches behavioral/sandbox analysis from VirusTotal.
    Returns permissions, network calls, file operations.
    """
    behavior_data = {
        "permissions": [],
        "network_calls": [],
        "files_dropped": [],
        "sandbox_verdicts": [],
    }

    try:
        # Get file details (includes Android-specific info)
        async with session.get(
            f"https://www.virustotal.com/api/v3/files/{sha256}",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                attrs = data.get("data", {}).get("attributes", {})

                # Android permissions
                android_info = attrs.get("androguard", {})
                if android_info:
                    perms = android_info.get("permission_details", {})
                    for perm_name, perm_info in list(perms.items())[:15]:
                        short_name = perm_name.split(".")[-1] if "." in perm_name else perm_name
                        behavior_data["permissions"].append({
                            "name": short_name,
                            "full": perm_name,
                            "level": perm_info.get("permission_type", "normal"),
                        })

                # Sandbox verdicts
                sandbox = attrs.get("sandbox_verdicts", {})
                for engine, verdict in list(sandbox.items())[:5]:
                    behavior_data["sandbox_verdicts"].append({
                        "engine": engine,
                        "verdict": verdict.get("category", "unknown"),
                    })

        # Get behavior summary (network, files)
        async with session.get(
            f"https://www.virustotal.com/api/v3/files/{sha256}/behaviour_summary",
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                bdata = data.get("data", {})

                # Network calls (DNS, HTTP)
                dns = bdata.get("dns_lookups", [])
                http = bdata.get("http_conversations", [])
                behavior_data["network_calls"] = [
                    {"type": "dns", "host": d.get("hostname", "")}
                    for d in dns[:5]
                ] + [
                    {"type": "http", "url": h.get("url", "")}
                    for h in http[:5]
                ]

                # Files dropped/created
                files = bdata.get("files_dropped", []) or bdata.get("files_written", [])
                behavior_data["files_dropped"] = files[:5]

    except Exception:
        pass  # Behavioral data is optional, don't fail the scan

    return behavior_data
