import urllib.request
import json
import threading
import os

VERSION = "1.0.0"
REPO = "ghostintheprompt/da-bklyn-bridge"

def check_for_updates():
    """
    Asynchronously checks for updates from GitHub releases.
    Fails silently on connection errors.
    """
    if os.environ.get("SENTINEL_CHECK_UPDATES") != "1":
        return

    def _check():
        try:
            url = f"https://api.github.com/repos/{REPO}/releases/latest"
            headers = {"User-Agent": "MDRN-Corp-Update-Checker"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get("tag_name", "").replace("v", "")
                if latest_version and latest_version > VERSION:
                    print(f"\n[!] UPDATE AVAILABLE: v{latest_version} is now available.")
                    print(f"[!] Download at: https://github.com/{REPO}/releases/latest\n")
        except:
            # Silent failure (no internet or API rate limit)
            pass

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()
