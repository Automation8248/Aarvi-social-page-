import os
import requests
import sys
import glob
import re
import random
import time
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
VIDEO_LIST_FILE = 'videos.txt'
HISTORY_FILE = 'history.txt'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# --- UPDATED WORKING SERVER LIST (2026) ---
# Ye list abhi active servers ki hai
COBALT_INSTANCES = [
    "https://api.cobalt.tools",       # Official Main Server
    "https://cobalt.arms.nu",         # Mirror 1
    "https://cobalt.rudart.cm",       # Mirror 2
    "https://cobalt.moscow.btn.moe",  # Mirror 3
    "https://hyp.cobalt.tools",       # Mirror 4
]

SEO_TAGS = ["#reels", "#trending", "#viral", "#explore", "#love", "#shayari"]
FORBIDDEN_WORDS = ["virtualaarvi", "aarvi", "video by", "uploaded by", "subscribe", "channel"]

def get_next_video():
    processed_urls = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            processed_urls = [line.strip() for line in f.readlines()]

    if not os.path.exists(VIDEO_LIST_FILE):
        print("❌ Error: videos.txt missing!")
        return None

    with open(VIDEO_LIST_FILE, 'r') as f:
        all_urls = [line.strip() for line in f.readlines() if line.strip()]

    for url in all_urls:
        if url not in processed_urls:
            return url
    return None

def is_text_safe(text):
    lower_text = text.lower()
    for word in FORBIDDEN_WORDS:
        if word in lower_text:
            return False
    return True

def translate_and_shorten(text):
    try:
        if not text or not text.strip(): return None
        translated = GoogleTranslator(source='auto', target='hi').translate(text)
        if not is_text_safe(translated) or not is_text_safe(text): return None
        words = translated.split()
        return " ".join(words[:4])
    except: return None

def download_video_data(url):
    print(f"⬇️ Processing URL via Cobalt: {url}")
    
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    # --- COBALT API LOGIC ---
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    }
    
    payload = {
        "url": url,
        "vCodec": "h264",
        "vQuality": "720",
        "filenamePattern": "basic"
    }

    download_url = None
    
    # Randomize server order
    random.shuffle(COBALT_INSTANCES)

    for instance in COBALT_INSTANCES:
        try:
            # Correct Endpoint Structure
            api_url = f"{instance}/api/json"
            print(f"📡 Trying Server: {instance} ...")
            
            resp = requests.post(api_url, json=payload, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                if 'url' in data:
                    download_url = data['url']
                    print("✅ Video Link Found!")
                    break
                elif 'status' in data and data['status'] == 'error':
                    print(f"⚠️ API Error: {data.get('text')}")
            else:
                print(f"⚠️ Failed (Status: {resp.status_code})")
                
        except Exception as e:
            print(f"⚠️ Connection Error: {str(e)[:50]}")
            continue

    if not download_url:
        print("❌ All Cobalt servers failed. Instagram might be blocking them.")
        return None

    # Download the file
    try:
        print("📥 Downloading video file...")
        video_res = requests.get(download_url, stream=True)
        dl_filename = "temp_video.mp4"
        with open(dl_filename, 'wb') as f:
            for chunk in video_res.iter_content(chunk_size=1024):
                if chunk: f.write(chunk)
        
        # Generic Metadata (Since API doesn't allow scraping text easily without login)
        title = "Instagram Reel"
        hashtags = "#reels #trending #viral " + " ".join(SEO_TAGS[:2])
        final_hindi_text = "देखिए आज का वीडियो ✨"

        return {
            "filename": dl_filename,
            "title": title,
            "hindi_text": final_hindi_text,
            "hashtags": hashtags,
            "original_url": url
        }

    except Exception as e:
        print(f"❌ File Download Error: {e}")
        return None

def upload_to_catbox(filepath):
    print("🚀 Uploading to Catbox...")
    try:
        with open(filepath, "rb") as f:
            response = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f})
            if response.status_code == 200:
                return response.text.strip()
            else: return None
    except: return None

def send_notifications(video_data, catbox_url):
    print("\n--- Sending Notifications ---")
    tg_caption = f"{video_data['hindi_text']}\n.\n.\n.\n.\n.\n{video_data['hashtags']}"
    
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        print("📤 Telegram Video Sending...")
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
        try:
            with open(video_data['filename'], 'rb') as video_file:
                payload = {"chat_id": str(TELEGRAM_CHAT_ID), "caption": tg_caption, "parse_mode": "Markdown"}
                files = {'video': video_file}
                requests.post(tg_url, data=payload, files=files)
                print("✅ Telegram Sent!")
        except Exception as e: print(f"❌ Telegram Error: {e}")

    if WEBHOOK_URL:
        if catbox_url and "catbox.moe" in catbox_url:
            print(f"📤 Webhook Sending...")
            payload = {
                "content": tg_caption, 
                "video_url": catbox_url,
                "title_original": video_data['title']
            }
            try: requests.post(WEBHOOK_URL, json=payload)
            except: pass

def update_history(url):
    with open(HISTORY_FILE, 'a') as f: f.write(url + '\n')

if __name__ == "__main__":
    next_url = get_next_video()
    if not next_url:
        print("💤 No new videos.")
        sys.exit(0)
    
    data = download_video_data(next_url)
    if data and data['filename']:
        catbox_link = upload_to_catbox(data['filename'])
        send_notifications(data, catbox_link)
        update_history(next_url)
        if os.path.exists(data['filename']): os.remove(data['filename'])
        print("✅ Task Done.")
    else: sys.exit(1)
