import os
import time
import threading
import requests
from datetime import datetime
import yt_dlp
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "YouTube Scraper is running!"

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

CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID")
CF_NAMESPACE_ID = os.environ.get("CF_NAMESPACE_ID")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def setup_cookies():
    cookies_content = os.environ.get("YOUTUBE_COOKIES")
    if cookies_content:
        # Bersihkan format jika ada tanda petunjuk berlebihan
        cookies_content = cookies_content.strip()
        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(cookies_content)
        log("cookies.txt successfully created from environment variable.")
    else:
        log("WARNING: YOUTUBE_COOKIES environment variable is empty!")

def get_manifest(url, retries=2):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }
    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                manifest = info.get('url') or info.get('manifest_url')
                if manifest:
                    return manifest
        except Exception as e:
            log(f"Extraction attempt {attempt+1} failed: {e}")
    return None

def get_current_value(key):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}/values/{key}"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
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

def scraper_loop():
    setup_cookies()
    time.sleep(5)
    while True:
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
        time.sleep(300)

if __name__ == "__main__":
    t = threading.Thread(target=scraper_loop)
    t.daemon = True
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
