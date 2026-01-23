import os
import requests
import yt_dlp
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

# RapidAPI Key (Isse GitHub Secrets mein add karna behtar hai)
RAPID_API_KEY = "1d87db308dmshd21171d762615b5p1368bejsnabb286989baf"

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

def get_smart_caption_text(vtt_file_path, description, title):
    if vtt_file_path and os.path.exists(vtt_file_path):
        try:
            with open(vtt_file_path, 'r', encoding='utf-8') as f: content = f.read()
            lines = content.splitlines()
            spoken_text = []
            for line in lines:
                if '-->' in line or line.strip() == '' or line.startswith('WEBVTT') or line.isdigit(): continue
                clean = re.sub(r'<[^>]+>', '', line).strip()
                clean = re.sub(r'\[.*?\]', '', clean)
                if clean and clean not in spoken_text: spoken_text.append(clean)
            
            full_speech = " ".join(spoken_text[:3])
            hindi_audio = translate_and_shorten(full_speech)
            if hindi_audio: return hindi_audio
        except Exception as e: print(f"⚠️ VTT Error: {e}")

    if description:
        clean_desc = description.split('\n')[0]
        clean_desc = re.sub(r'#\w+', '', clean_desc).strip()
        if is_text_safe(clean_desc):
            hindi_desc = translate_and_shorten(clean_desc)
            if hindi_desc: return hindi_desc

    clean_title = re.sub(r'#\w+', '', title).strip()
    if is_text_safe(clean_title):
        hindi_title = translate_and_shorten(clean_title)
        if hindi_title: return hindi_title

    return "देखिए आज का वीडियो"

def generate_hashtags(original_tags):
    final_tags = ["#aarvi"]
    forbidden = ["virtualaarvi", "aarvi"]
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
    print(f"⬇️ Fetching via RapidAPI: {url}")
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    # --- RAPID API INTEGRATION ---
    rapid_url = "https://instagram120.p.rapidapi.com/api/instagram/post" # Single post info endpoint
    querystring = {"code": url.split("/")[-2]} # Link se shortcode nikalna
    
    headers = {
        "x-rapidapi-key": RAPID_API_KEY,
        "x-rapidapi-host": "instagram120.p.rapidapi.com"
    }

    try:
        response = requests.get(rapid_url, headers=headers, params=querystring)
        res_data = response.json()
        
        # RapidAPI se video link aur info nikalna
        video_download_url = res_data.get('result', {}).get('video_url')
        title = res_data.get('result', {}).get('caption_text', 'Instagram Video')
        
        if not video_download_url:
            print("❌ RapidAPI could not find video URL")
            return None

        # Video download karna
        print("📥 Downloading file...")
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
        print(f"❌ RapidAPI Error: {e}")
        return None

def upload_to_catbox(filepath):
    print("🚀 Uploading to Catbox...")
    try:
        with open(filepath, "rb") as f:
            response = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": f})
            if response.status_code == 200:
                return response.text.strip()
            else:
                return None
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
            print(f"📤 Webhook Sending (Link: {catbox_url})...")
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
