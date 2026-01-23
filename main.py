import os
import requests
import sys
import glob
import re
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
VIDEO_LIST_FILE = 'videos.txt'
HISTORY_FILE = 'history.txt'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# RapidAPI Key (Jo aapne di thi)
RAPID_API_KEY = "1d87db308dmshd21171d762615b5p1368bejsnabb286989baf"
RAPID_HOST = "instagram120.p.rapidapi.com"

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

def generate_hashtags(original_tags):
    final_tags = ["#aarvi"]
    forbidden = ["virtualaarvi", "aarvi"]
    if original_tags:
        for tag in original_tags:
            clean_tag = tag.replace(" ", "").lower()
            if clean_tag not in forbidden and f"#{clean_tag}" not in final_tags:
                final_tags.append(f"#{clean_tag}")
    for seo in SEO_TAGS:
        if len(final_tags) < 5:
            if seo not in final_tags: final_tags.append(seo)
        else: break
    return " ".join(final_tags[:5])

def download_video_data(url):
    print(f"⬇️ Processing URL via RapidAPI: {url}")
    
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    # --- RAPID API LOGIC (Fixed Endpoints) ---
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": RAPID_HOST
    }

    # Hum do alag-alag endpoints try karenge agar ek fail hua to
    endpoints = [
        "https://instagram120.p.rapidapi.com/download-video",  # Try 1
        "https://instagram120.p.rapidapi.com/media/download",  # Try 2
    ]
    
    video_download_url = None
    title = "Instagram Reel"

    for api_url in endpoints:
        try:
            print(f"📡 Trying Endpoint: {api_url} ...")
            querystring = {"url": url} # Yeh API usually full URL leti hai
            
            response = requests.get(api_url, headers=headers, params=querystring)
            
            if response.status_code == 200:
                data = response.json()
                
                # Response se video link nikalna (Flexible logic)
                if 'video_url' in data:
                    video_download_url = data['video_url']
                elif 'data' in data and 'video_url' in data['data']:
                    video_download_url = data['data']['video_url']
                elif 'result' in data and 'video_url' in data['result']:
                    video_download_url = data['result']['video_url']
                elif 'url' in data: # Kabhi kabhi direct url key hoti hai
                    video_download_url = data['url']

                # Agar URL mil gaya to loop break karo
                if video_download_url:
                    print("✅ Video Link Found!")
                    # Title nikalna
                    if 'caption' in data: title = data['caption']
                    elif 'title' in data: title = data['title']
                    break
            else:
                print(f"⚠️ Endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Connection Error: {e}")
            continue

    if not video_download_url:
        print("❌ RapidAPI Failed to find video URL. Key might be wrong or API endpoint changed.")
        return None

    # Download File
    try:
        print("📥 Downloading video file...")
        video_res = requests.get(video_download_url, stream=True)
        dl_filename = "temp_video.mp4"
        with open(dl_filename, 'wb') as f:
            for chunk in video_res.iter_content(chunk_size=1024):
                if chunk: f.write(chunk)
        
        hashtags = generate_hashtags([])
        final_hindi_text = translate_and_shorten(title) or "देखिए आज का वीडियो"

        return {
            "filename": dl_filename,
            "title": title,
            "hindi_text": final_hindi_text,
            "hashtags": hashtags,
            "original_url": url
        }

    except Exception as e:
        print(f"❌ File Save Error: {e}")
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
