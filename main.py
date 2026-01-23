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

# RAPID API SETUP
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

def extract_user_and_code(url):
    try:
        clean_url = url.split('?')[0].rstrip('/')
        parts = clean_url.split('/')
        shortcode = parts[-1]
        username = None
        if 'reel' in parts:
            idx = parts.index('reel')
            username = parts[idx-1]
        elif 'p' in parts:
            idx = parts.index('p')
            username = parts[idx-1]
        return username, shortcode
    except:
        return None, None

def download_video_data(url):
    print(f"⬇️ Processing: {url}")
    
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    # 1. Info extraction
    username, target_code = extract_user_and_code(url)
    if not username or not target_code:
        print("❌ Error: Invalid URL format.")
        return None
    
    print(f"🔍 Searching Video: User='{username}', ID='{target_code}'")

    # 2. Call API
    api_url = f"https://{RAPID_HOST}/api/instagram/posts"
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": RAPID_HOST,
        "Content-Type": "application/json"
    }
    payload = {"username": username, "maxId": ""}

    try:
        print("📡 Fetching Profile Posts via API...")
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ API Error ({response.status_code}): {response.text}")
            return None

        api_data = response.json()
        posts_list = []

        # --- FIX: SMART PARSING LOGIC ---
        # Data ko dhoondh kar nikalna chahe wo kahin bhi chhupa ho
        if isinstance(api_data, list):
            posts_list = api_data
        elif isinstance(api_data, dict):
            # Check Result -> Items
            if 'result' in api_data:
                res = api_data['result']
                if isinstance(res, list): posts_list = res
                elif isinstance(res, dict) and 'items' in res: posts_list = res['items']
                elif isinstance(res, dict) and 'feed_items' in res: posts_list = res['feed_items']
            
            # Check Data -> Items
            elif 'data' in api_data:
                dat = api_data['data']
                if isinstance(dat, list): posts_list = dat
                elif isinstance(dat, dict) and 'items' in dat: posts_list = dat['items']
            
            # Direct Items
            elif 'items' in api_data:
                posts_list = api_data['items']

        print(f"📂 Scanning {len(posts_list)} posts...")

        # 3. Search Loop
        video_download_url = None
        title = "Instagram Reel"
        
        for post in posts_list:
            # Safety check: agar post dictionary nahi hai to skip karo
            if not isinstance(post, dict):
                continue

            # Keys check karna
            post_code = post.get('code') or post.get('shortcode') or post.get('pk')
            
            # ID Match logic (Strings compare karna safe rehta hai)
            if str(post_code) == str(target_code):
                print("✅ Match Found!")
                
                # Video URL Extraction
                if 'video_url' in post:
                    video_download_url = post['video_url']
                elif 'video_versions' in post and len(post['video_versions']) > 0:
                    video_download_url = post['video_versions'][0]['url']
                
                # Title Extraction
                if 'caption' in post:
                    cap = post['caption']
                    if isinstance(cap, dict): title = cap.get('text', '')
                    else: title = str(cap)
                break
        
        if not video_download_url:
            print(f"⚠️ Video ID '{target_code}' not found in recent list.")
            # Debugging ke liye structure print karna (optional)
            # print(f"DEBUG DATA: {api_data}") 
            return None

        # 4. Download
        print("📥 Downloading Video File...")
        file_headers = {'User-Agent': 'Mozilla/5.0'}
        video_res = requests.get(video_download_url, headers=file_headers, stream=True)
        
        dl_filename = "temp_video.mp4"
        with open(dl_filename, 'wb') as f:
            for chunk in video_res.iter_content(chunk_size=1024):
                if chunk: f.write(chunk)
        
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
        print(f"❌ System Error: {e}")
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
