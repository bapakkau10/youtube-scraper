import os
import subprocess
import requests
import time
import sys
from datetime import datetime

# ================= CONFIG =================

CHANNELS = {
    "makkah_live": "https://www.youtube.com/watch?v=cvjtLTv5FLU",
    "madinah_live": "https://www.youtube.com/watch?v=9nZ53zD5N5Y",
    "uai_live": "https://www.youtube.com/watch?v=gArvbbi8LyQ",
    "poker_live": "https://www.youtube.com/watch?v=qx2M5qnxKj4",
    "warner_live": "https://www.youtube.com/watch?v=G43NInZfoPE",
    "hp_live": "https://www.youtube.com/watch?v=WVwP298MU7I",
    "nat_live": "https://www.youtube.com/watch?v=78LSssVa6cs",
    "laugh_live": "https://www.youtube.com/watch?v=400k2SKoeh4",
    "mc_live": "https://www.youtube.com/watch?v=XghNs0Cx6JQ",
    "rayaa_live": "https://www.youtube.com/watch?v=HgIeyAENfas",
}

# Ambil nilai selamat daripada GitHub Secrets
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_NAMESPACE_ID = os.environ.get("CF_NAMESPACE_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")

LOG_FILE = "update_log.txt"

# ===========================================

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_manifest(url, retries=2):
    for attempt in range(retries):
        try:
            result = subprocess.check_output(
                [sys.executable, "-m", "yt_dlp", "--print", "manifest_url", url],
                text=True
            ).strip()
            return result
        except Exception as e:
            log(f"Extraction attempt {attempt+1} failed: {e}")
            time.sleep(3)
    return None

def get_current_value(key):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}/values/{key}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    return None

def update_kv(key, manifest_url):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}/values/{key}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "text/plain"
    }
    response = requests.put(url, headers=headers, data=manifest_url)
    if response.status_code == 200:
        log(f"{key} updated successfully.")
    else:
        log(f"{key} update failed: {response.text}")

# ================= MAIN ====================

if __name__ == "__main__":
    log("===== START UPDATE CYCLE =====")

    for key, youtube_url in CHANNELS.items():
        log(f"Checking {key}...")
        manifest = get_manifest(youtube_url)

        if not manifest:
            log(f"{key} FAILED extraction.")
            continue

        current_value = get_current_value(key)

        if current_value == manifest:
            log(f"{key} unchanged. Skipping write.")
        else:
            update_kv(key, manifest)

    log("===== END UPDATE CYCLE =====\n")
