import os
import requests
import yt_dlp
import sys
import glob
import re
import time
import random
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
VIDEO_LIST_FILE = 'videos.txt'
HISTORY_FILE = 'history.txt'

# Secrets
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

SEO_TAGS = ["#reels", "#trending", "#viral", "#explore", "#love", "#shayari", "#instagram", "#instagood", "#india"]
FORBIDDEN_WORDS = ["virtualaarvi", "aarvi", "video by", "uploaded by", "subscribe", "channel"]

# --- 🌎 DEVICE PROFILES ---
DEVICE_PROFILES = [
    {"name": "Samsung S24 Ultra", "type": "android", "ua": "Instagram 315.0.0.25.108 Android (34/14; 560dpi; 1440x3120; samsung; SM-S928B; e3q; qcom; en_US; 523410000)"},
    {"name": "iPhone 15 Pro Max", "type": "ios", "ua": "Instagram 315.0.0.25.105 iPhone16,2 iOS 17_1_1"},
    {"name": "Google Pixel 8 Pro", "type": "android", "ua": "Instagram 315.0.0.25.108 Android (34/14; 480dpi; 1344x2992; Google; Pixel 8 Pro; husky; google; en_US; 534500100)"},
    {"name": "Xiaomi 14 Pro", "type": "android", "ua": "Instagram 315.0.0.22.115 Android (34/14; 560dpi; 1440x3200; Xiaomi; 23116PN5BC; shennong; qcom; en_US; 534500300)"},
    {"name": "Vivo X90 Pro", "type": "android", "ua": "Instagram 300.0.0.18.110 Android (33/13; 480dpi; 1260x2800; vivo; V2219; PD2242; mt6985; en_US; 512300100)"}
]

def clean_url(url):
    return url.strip().strip('"').strip("'").strip(',')

def get_next_video():
    processed_urls = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            processed_urls = [clean_url(line) for line in f.readlines()]

    if not os.path.exists(VIDEO_LIST_FILE):
        print("❌ Error: videos.txt missing!")
        return None

    with open(VIDEO_LIST_FILE, 'r') as f:
        all_urls = [clean_url(line) for line in f.readlines() if line.strip()]

    for url in all_urls:
        if url not in processed_urls:
            return url
    return None

def translate_and_shorten(text):
    try:
        if not text or not text.strip(): return None
        translated = GoogleTranslator(source='auto', target='hi').translate(text)
        if any(word in translated.lower() for word in FORBIDDEN_WORDS): return None
        words = translated.split()
        return " ".join(words[:5])
    except: return None

def generate_hashtags(original_tags):
    final_tags = ["#reels"]
    if original_tags:
        for tag in original_tags:
            clean_tag = tag.replace(" ", "").lower()
            if clean_tag not in FORBIDDEN_WORDS and f"#{clean_tag}" not in final_tags:
                final_tags.append(f"#{clean_tag}")
    for seo in SEO_TAGS:
        if len(final_tags) < 8:
            if seo not in final_tags: final_tags.append(seo)
        else: break
    return " ".join(final_tags[:8])

# --- 🛡️ PROXY FINDER (The Key Solution) ---
def get_proxies():
    print("🛡️ Searching for safe paths (Proxies)...")
    # Fetching fresh public proxies
    try:
        url = "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            proxies = r.text.strip().splitlines()
            # Sirf pehle 20 try karenge taaki time waste na ho
            return [p.strip() for p in proxies if p.strip()][:20]
    except: pass
    return []

def download_video_data(url):
    print(f"⬇️ Processing: {url}")
    
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    # Get Proxies
    proxy_list = get_proxies()
    # Add 'None' at last to try direct connection as last resort
    proxy_list.append(None) 

    dl_filename = None
    title = "Instagram Reel"
    final_hindi_text = ""
    hashtags = ""

    # Try downloading using different proxies
    for i, proxy in enumerate(proxy_list):
        device = random.choice(DEVICE_PROFILES)
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': 'temp_video.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extractor_args': {'instagram': {'impersonate': [device['type']]}},
            'http_headers': {'User-Agent': device['ua'], 'Accept-Language': 'en-US'}
        }
        
        if proxy:
            print(f"🔄 Attempt {i+1}: Trying via Proxy {proxy}...")
            ydl_opts['proxy'] = f"http://{proxy}"
        else:
            print("⚠️ Proxies exhausted. Trying Direct Connection...")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    title = info.get('title') or info.get('description') or "Reel"
                    hashtags = generate_hashtags(info.get('tags', []))
                    found_files = glob.glob("temp_video*")
                    video_files = [f for f in found_files if not f.endswith('.vtt')]
                    if video_files: 
                        dl_filename = video_files[0]
                        final_hindi_text = translate_and_shorten(title) or "देखिए आज का वीडियो ✨"
                        print("✅ Download Success via Proxy!")
                        break # Stop trying, we got it
        except Exception:
            continue # Try next proxy

    if not dl_filename: 
        print("❌ All connection paths failed.")
        return None

    return {
        "filename": dl_filename,
        "title": title,
        "hindi_text": final_hindi_text,
        "hashtags": hashtags,
        "original_url": url
    }

def upload_to_catbox(filepath):
    print("🚀 Uploading to Catbox...")
    try:
        with open(filepath, "rb") as f:
            response = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=120)
            if response.status_code == 200: return response.text.strip()
    except: pass
    return None

def send_notifications(video_data, catbox_url):
    print("\n--- Sending Notifications ---")
    tg_caption = f"{video_data['hindi_text']}\n.\n.\n.\n{video_data['hashtags']}"
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
        try:
            with open(video_data['filename'], 'rb') as video_file:
                payload = {"chat_id": str(TELEGRAM_CHAT_ID), "caption": tg_caption}
                requests.post(tg_url, data=payload, files={'video': video_file}, timeout=120)
                print("✅ Telegram Sent!")
        except Exception as e: print(f"❌ Telegram Fail: {e}")

    if WEBHOOK_URL and catbox_url:
        payload = {"content": tg_caption, "video_url": catbox_url, "original_post": video_data['original_url']}
        try:
            requests.post(WEBHOOK_URL, json=payload, timeout=30)
            print("✅ Webhook Sent!")
        except Exception as e: print(f"❌ Webhook Fail: {e}")

def update_history(url):
    with open(HISTORY_FILE, 'a') as f: f.write(url + '\n')

if __name__ == "__main__":
    max_retries = 10 
    attempt = 0
    
    while attempt < max_retries:
        next_url = get_next_video()
        if not next_url:
            print("💤 No new videos found.")
            sys.exit(0)

        data = download_video_data(next_url)
        
        if data and data['filename']:
            catbox_link = upload_to_catbox(data['filename'])
            send_notifications(data, catbox_link)
            update_history(next_url)
            if os.path.exists(data['filename']): os.remove(data['filename'])
            print("🎉 Task Finished Successfully.")
            sys.exit(0)
        else:
            print(f"⚠️ Video failed: {next_url}")
            print("🔄 Skipping & Retrying next in 10s...")
            update_history(next_url) 
            attempt += 1
            time.sleep(10)

    print("❌ Too many failures. Exiting.")
    sys.exit(1)
