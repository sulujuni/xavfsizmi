"""
Generic file scanner via VirusTotal API v3.
Scans any file type (PDF, DOC, ZIP, EXE, APK, etc.) up to 32 MB.
"""
import aiohttp
import asyncio
from config import VIRUSTOTAL_API_KEY

# Allowed file extensions and their friendly type names
SCANNABLE_EXTENSIONS = {
    ".apk": "Android App",
    ".exe": "Windows Program",
    ".msi": "Windows Installer",
    ".pdf": "PDF Document",
    ".doc": "Word Document",
    ".docx": "Word Document",
    ".xls": "Excel Spreadsheet",
    ".xlsx": "Excel Spreadsheet",
    ".ppt": "PowerPoint",
    ".pptx": "PowerPoint",
    ".zip": "ZIP Archive",
    ".rar": "RAR Archive",
    ".7z": "7-Zip Archive",
    ".js": "JavaScript File",
    ".jar": "Java Archive",
    ".bat": "Batch Script",
    ".sh": "Shell Script",
    ".dmg": "macOS Image",
    ".iso": "Disk Image",
    ".scr": "Screensaver (often malware!)",
    ".vbs": "VBScript (often malware!)",
}

MAX_FILE_SIZE = 32 * 1024 * 1024  # 32 MB


def get_file_type(filename: str) -> str:
    """Return friendly file type name, or empty string if not scannable."""
    name = (filename or "").lower()
    for ext, type_name in SCANNABLE_EXTENSIONS.items():
        if name.endswith(ext):
            return type_name
    return ""


def is_scannable(filename: str) -> bool:
    """Check if a file extension is supported for scanning."""
    return bool(get_file_type(filename))


async def scan_file(file_bytes: bytes, filename: str) -> dict:
    """
    Uploads a file to VirusTotal and waits for the scan result.
    Works for any file type. Returns malicious/suspicious/total counts.
    """
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}

    async with aiohttp.ClientSession() as session:
        # Step 1 — Upload the file
        form = aiohttp.FormData()
        form.add_field("file", file_bytes, filename=filename)

        try:
            async with session.post(
                "https://www.virustotal.com/api/v3/files",
                headers=headers, data=form,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status != 200:
                    return {"success": False}
                data = await resp.json()
                analysis_id = data["data"]["id"]
        except Exception:
            return {"success": False}

        # Step 2 — Poll for results
        for _ in range(12):
            await asyncio.sleep(10)
            try:
                async with session.get(
                    f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    result = await resp.json()
                    attrs = result["data"]["attributes"]
                    status = attrs["status"]

                    if status == "completed":
                        stats = attrs["stats"]
                        meta = result.get("meta", {}).get("file_info", {})
                        return {
                            "success": True,
                            "malicious": stats.get("malicious", 0),
                            "suspicious": stats.get("suspicious", 0),
                            "harmless": stats.get("harmless", 0),
                            "undetected": stats.get("undetected", 0),
                            "total": sum(stats.values()),
                            "sha256": meta.get("sha256", ""),
                        }
            except Exception:
                continue

        return {"success": False, "timeout": True}
