import os
import requests
import yt_dlp
import sys
import glob
import re
import time
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
VIDEO_LIST_FILE = 'videos.txt'
HISTORY_FILE = 'history.txt'

# Secrets Load Karna
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

SEO_TAGS = ["#reels", "#trending", "#viral", "#explore", "#love", "#shayari", "#instagram"]
FORBIDDEN_WORDS = ["virtualaarvi", "aarvi", "video by", "uploaded by", "subscribe", "channel"]

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

def download_video_data(url):
    print(f"⬇️ Processing: {url}")
    
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    # Android Fake ID (Taaki login na maange)
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'temp_video.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extractor_args': {'instagram': {'impersonate': ['android']}},
        'http_headers': {'User-Agent': 'Instagram 219.0.0.12.117 Android', 'Accept-Language': 'en-US'}
    }
    
    dl_filename = None
    title = "Instagram Reel"
    final_hindi_text = ""
    hashtags = ""

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                title = info.get('title') or info.get('description') or "Reel"
                hashtags = generate_hashtags(info.get('tags', []))
                
                found_files = glob.glob("temp_video*")
                video_files = [f for f in found_files if not f.endswith('.vtt')]
                if video_files: dl_filename = video_files[0]
                
                final_hindi_text = translate_and_shorten(title) or "देखिए आज का वीडियो ✨"
            else:
                print("❌ Download Failed (Content Unavailable/Private)")
                return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

    if not dl_filename: return None

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
            response = requests.post(
                "https://catbox.moe/user/api.php", 
                data={"reqtype": "fileupload"}, 
                files={"fileToUpload": f}, 
                timeout=120
            )
            if response.status_code == 200:
                link = response.text.strip()
                print(f"✅ Catbox Link: {link}")
                return link
    except Exception as e:
        print(f"⚠️ Catbox Upload Failed: {e}")
    return None

def send_notifications(video_data, catbox_url):
    print("\n--- Sending Notifications ---")
    tg_caption = f"{video_data['hindi_text']}\n.\n.\n.\n{video_data['hashtags']}"
    
    # 1. Telegram Check
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram skipped: Token or Chat ID missing in Secrets.")
    else:
        print("📤 Sending Video to Telegram...")
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
        try:
            with open(video_data['filename'], 'rb') as video_file:
                payload = {"chat_id": str(TELEGRAM_CHAT_ID), "caption": tg_caption}
                resp = requests.post(tg_url, data=payload, files={'video': video_file}, timeout=120)
                if resp.status_code == 200: print("✅ Telegram Sent!")
                else: print(f"❌ Telegram Error {resp.status_code}: {resp.text}")
        except Exception as e: print(f"❌ Telegram Exception: {e}")

    # 2. Webhook Check
    if not WEBHOOK_URL:
        print("⚠️ Webhook skipped: URL missing in Secrets.")
    elif not catbox_url:
        print("⚠️ Webhook skipped: Catbox URL failed.")
    else:
        print("📤 Sending to Webhook...")
        payload = {
            "content": tg_caption, 
            "video_url": catbox_url,
            "original_post": video_data['original_url']
        }
        try:
            resp = requests.post(WEBHOOK_URL, json=payload, timeout=30)
            if resp.status_code in [200, 204]: print("✅ Webhook Sent!")
            else: print(f"❌ Webhook Error {resp.status_code}: {resp.text}")
        except Exception as e: print(f"❌ Webhook Exception: {e}")

def update_history(url):
    with open(HISTORY_FILE, 'a') as f: f.write(url + '\n')

# --- MAIN LOOP (AUTO-SKIP LOGIC) ---
if __name__ == "__main__":
    max_retries = 5  # Maximum 5 videos try karega
    attempt = 0
    
    while attempt < max_retries:
        next_url = get_next_video()
        if not next_url:
            print("💤 No new videos found in list.")
            sys.exit(0)

        # Download Try Karo
        data = download_video_data(next_url)
        
        if data and data['filename']:
            # --- SUCCESS ---
            # 1. Upload
            catbox_link = upload_to_catbox(data['filename'])
            # 2. Notify
            send_notifications(data, catbox_link)
            # 3. Save & Cleanup
            update_history(next_url)
            if os.path.exists(data['filename']): os.remove(data['filename'])
            
            print("🎉 Task Finished Successfully.")
            sys.exit(0) # Kaam khatam, exit
        else:
            # --- FAILURE (Skip & Retry) ---
            print(f"⚠️ Video failed: {next_url}")
            print("🔄 Marking as skipped and trying next video...")
            update_history(next_url) # Isko history me daal do taaki dubara na aaye
            attempt += 1
            time.sleep(2)

    print("❌ Too many failures. Exiting.")
    sys.exit(1)
