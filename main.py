import os
import requests
import yt_dlp
import sys
import glob
import time
import random
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
VIDEO_LIST_FILE = 'videos.txt'
HISTORY_FILE = 'history.txt'

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

SEO_TAGS = ["#reels", "#trending", "#viral", "#explore", "#love", "#shayari", "#instagram"]
FORBIDDEN_WORDS = ["virtualaarvi", "aarvi", "video by", "uploaded by", "subscribe", "channel"]

# --- 🎭 ADVANCED IDENTITY ROTATION ---
DEVICE_PROFILES = [
    {"type": "android", "ua": "Instagram 315.0.0.25.108 Android (34/14; 560dpi; 1440x3120; samsung; SM-S928B; e3q; qcom; en_US; 523410000)"},
    {"type": "ios", "ua": "Instagram 315.0.0.25.105 iPhone16,2 iOS 17_1_1"},
    {"type": "android", "ua": "Instagram 300.0.0.18.110 Android (33/13; 480dpi; 1260x2800; vivo; V2219; PD2242; mt6985; en_US; 512300100)"}
]

def clean_url(url):
    return url.strip().strip('"').strip("'").strip(',')

def get_next_video():
    processed = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            processed = [clean_url(l) for l in f.readlines()]
    if not os.path.exists(VIDEO_LIST_FILE): return None
    with open(VIDEO_LIST_FILE, 'r') as f:
        all_urls = [clean_url(l) for l in f.readlines() if l.strip()]
    for url in all_urls:
        if url not in processed: return url
    return None

def translate_and_shorten(text):
    try:
        if not text or not text.strip(): return "Reel ✨"
        translated = GoogleTranslator(source='auto', target='hi').translate(text)
        if any(word in translated.lower() for word in FORBIDDEN_WORDS): return "New Reel ✨"
        words = translated.split()
        return " ".join(words[:5])
    except: return "Reel ✨"

def download_video_data(url):
    print(f"⬇️ Attempting Direct Download: {url}")
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                found_files = glob.glob("temp_video*")
                video_files = [f for f in found_files if not f.endswith('.vtt')]
                if video_files:
                    title = info.get('title') or info.get('description') or "Reel"
                    return {
                        "filename": video_files[0],
                        "hindi_text": translate_and_shorten(title),
                        "original_url": url
                    }
    except Exception as e:
        print(f"❌ Error: {e}")
    return None

if __name__ == "__main__":
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        target_url = get_next_video()
        if not target_url:
            print("💤 No new videos.")
            sys.exit(0)
            
        data = download_video_data(target_url)
        if data:
            # Send Notifications
            caption = f"{data['hindi_text']}\n.\n#reels #trending #viral"
            
            # Telegram
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
                with open(data['filename'], 'rb') as v:
                    requests.post(tg_url, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}, files={'video': v})
            
            # Webhook
            if WEBHOOK_URL:
                requests.post(WEBHOOK_URL, json={"content": caption, "url": data['original_url']})

            # Save & Cleanup
            with open(HISTORY_FILE, 'a') as h: h.write(target_url + "\n")
            if os.path.exists(data['filename']): os.remove(data['filename'])
            print("🎉 Success!")
            sys.exit(0)
        else:
            print(f"⚠️ Skipping: {target_url}")
            with open(HISTORY_FILE, 'a') as h: h.write(target_url + "\n")
            attempt += 1
            time.sleep(5)
