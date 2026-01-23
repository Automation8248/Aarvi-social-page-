import os
import requests
import sys
import glob
import re
import time
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
VIDEO_LIST_FILE = 'videos.txt'
HISTORY_FILE = 'history.txt'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

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
    if not text: return False
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

def generate_hashtags(original_tags):
    final_tags = ["#reels"]
    forbidden = ["virtualaarvi", "aarvi"]
    if original_tags:
        for tag in original_tags:
            clean_tag = tag.replace(" ", "").lower()
            if clean_tag not in forbidden and f"#{clean_tag}" not in final_tags:
                final_tags.append(f"#{clean_tag}")
    for seo in SEO_TAGS:
        if len(final_tags) < 6:
            if seo not in final_tags: final_tags.append(seo)
        else: break
    return " ".join(final_tags[:6])

# --- NEW: INDOWN SCRAPER (More Stable) ---
def fetch_from_indown(url):
    print("🔄 Connecting to Indown.io (Bypassing Instagram)...")
    
    session = requests.Session()
    
    # Headers are critical for scraping
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://indown.io/",
        "Origin": "https://indown.io",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        # Step 1: Initial Handshake (Cookies lene ke liye)
        session.get("https://indown.io", headers=headers, timeout=10)
        
        # Step 2: POST Request (Link bhejna)
        post_url = "https://indown.io/download"
        data = {
            "link": url,
            "referer": "https://indown.io"
        }
        
        print("📡 Sending link to Indown server...")
        response = session.post(post_url, data=data, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"⚠️ Server returned status: {response.status_code}")
            return None
        
        # Step 3: Extract Video Link from HTML
        html = response.text
        
        # Regex to find .mp4 link inside the response
        # Indown usually puts link in <source src="..."> or <a href="...">
        video_match = re.search(r'src="([^"]+\.mp4[^"]*)"', html)
        
        if not video_match:
            # Fallback regex search
            video_match = re.search(r'href="([^"]+\.mp4[^"]*)"', html)
            
        if video_match:
            video_url = video_match.group(1).replace("&amp;", "&")
            print("✅ Video Link Extracted Successfully!")
            return video_url
        else:
            print("❌ Could not find video link in HTML. Indown might be blocked or changed layout.")
            # Debug: print(html[:500])
            return None

    except Exception as e:
        print(f"❌ Scraping Failed: {e}")
        return None

def download_video_data(url):
    print(f"⬇️ Processing: {url}")
    
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    # --- USE INDOWN SCRAPER ---
    video_download_url = fetch_from_indown(url)
    
    if not video_download_url:
        print("❌ Failed to fetch video link.")
        return None
    
    # Download File
    try:
        print("📥 Downloading Video File...")
        # Headers needed to avoid 403
        file_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        
        video_res = requests.get(video_download_url, headers=file_headers, stream=True)
        
        dl_filename = "temp_video.mp4"
        with open(dl_filename, 'wb') as f:
            for chunk in video_res.iter_content(chunk_size=1024):
                if chunk: f.write(chunk)
        
        # Generic Metadata
        title = "Instagram Reel"
        hashtags = generate_hashtags([])
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
            response = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=60)
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
