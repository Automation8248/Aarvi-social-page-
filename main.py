import os
import requests
import sys
import glob
import re
import time
import random
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---
VIDEO_LIST_FILE = 'videos.txt'
HISTORY_FILE = 'history.txt'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

SEO_TAGS = ["#reels", "#trending", "#viral", "#explore", "#love", "#shayari"]
FORBIDDEN_WORDS = ["virtualaarvi", "aarvi", "video by", "uploaded by", "subscribe", "channel"]

# Real Browser Headers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

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

def extract_shortcode(url):
    try:
        clean_url = url.split('?')[0].rstrip('/')
        parts = clean_url.split('/')
        if 'reel' in parts: return parts[parts.index('reel') + 1]
        if 'p' in parts: return parts[parts.index('p') + 1]
        return parts[-1]
    except: return None

# --- STRATEGY 1: EMBED PAGE BYPASS (Pure Logic) ---
def fetch_via_embed(shortcode):
    print("🔄 Strategy 1: Attempting Embed Logic (Bypassing Main Page)...")
    
    # Instagram Embed URL (Ye aksar blocked nahi hota)
    embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://www.instagram.com/",
    }

    try:
        resp = requests.get(embed_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ Embed Page Blocked (Status: {resp.status_code})")
            return None, None

        # HTML mein video link dhoondhna
        html = resp.text
        
        # Pattern 1: video_url inside JSON config
        match = re.search(r'"video_url":"([^"]+)"', html)
        if match:
            video_url = match.group(1).replace("\\u0026", "&")
            print("✅ Found video in Embed Code!")
            return video_url, "Instagram Reel"
            
        # Pattern 2: mp4 in regular href
        match_mp4 = re.search(r'href="([^"]+\.mp4[^"]*)"', html)
        if match_mp4:
            video_url = match_mp4.group(1).replace("&amp;", "&")
            print("✅ Found mp4 link in Embed HTML!")
            return video_url, "Instagram Reel"
            
        print("⚠️ Embed page loaded but no video found.")
    except Exception as e:
        print(f"⚠️ Embed Logic Error: {e}")
    
    return None, None

# --- STRATEGY 2: CLEAN VIEWER (Imginn) ---
def fetch_via_viewer(shortcode):
    print("🔄 Strategy 2: Fetching via Clean Viewer (Imginn)...")
    # Imginn ek downloader nahi, viewer hai. GitHub IP ispe chalta hai.
    url = f"https://imginn.com/p/{shortcode}/"
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None, None
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Download button dhoondhna
        video_url = None
        
        # Method A: Class 'download-btn'
        btn = soup.find('a', {'class': 'download-btn'})
        if btn and btn.get('href'):
            video_url = btn['href']
            
        # Method B: Video Tag
        if not video_url:
            vid = soup.find('video')
            if vid and vid.get('src'):
                video_url = vid['src']
        
        if video_url:
            print("✅ Success via Viewer Logic!")
            # Caption
            caption = "Instagram Reel"
            desc = soup.find('p', {'class': 'desc'})
            if desc: caption = desc.get_text().strip()
            return video_url, caption
            
    except Exception as e:
        print(f"⚠️ Viewer Logic Failed: {e}")
        
    return None, None

def download_video_data(url):
    print(f"⬇️ Processing: {url}")
    
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    shortcode = extract_shortcode(url)
    if not shortcode:
        print("❌ Invalid URL format")
        return None

    # Step 1: Try Embed Logic (Pure Instagram)
    video_download_url, title = fetch_via_embed(shortcode)
    
    # Step 2: Try Viewer Logic (If Step 1 fails)
    if not video_download_url:
        video_download_url, title = fetch_via_viewer(shortcode)

    if not video_download_url:
        print("❌ Both Logic Strategies Failed. GitHub IP is severely restricted.")
        return None
    
    # Download File
    try:
        print("📥 Downloading Video File...")
        file_headers = {"User-Agent": random.choice(USER_AGENTS)}
        
        video_res = requests.get(video_download_url, headers=file_headers, stream=True)
        
        dl_filename = "temp_video.mp4"
        with open(dl_filename, 'wb') as f:
            for chunk in video_res.iter_content(chunk_size=1024):
                if chunk: f.write(chunk)
        
        # Validate File
        if os.path.getsize(dl_filename) < 1000:
            print("❌ Downloaded file is corrupted/empty.")
            return None
        
        hashtags = generate_hashtags([])
        final_hindi_text = translate_and_shorten(title) or "देखिए आज का वीडियो ✨"

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
            response = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f}, timeout=120)
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
