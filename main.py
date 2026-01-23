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
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

SEO_TAGS = ["#reels", "#trending", "#viral", "#explore", "#love", "#shayari"]
FORBIDDEN_WORDS = ["virtualaarvi", "aarvi", "video by", "uploaded by", "subscribe", "channel"]

# --- HUMAN EMULATION LOGIC ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
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

# --- PROXY & IP MASKING LOGIC ---
def get_free_proxies():
    print("🛡️ Finding a working Proxy to hide GitHub IP...")
    # Hum ek free list se proxies nikalenge
    try:
        resp = requests.get("https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=all&ssl=all&anonymity=all")
        if resp.status_code == 200:
            proxies = resp.text.splitlines()
            print(f"✅ Found {len(proxies)} proxies. Trying to find a live one...")
            return proxies[:10] # Top 10 try karenge
    except:
        print("⚠️ Could not fetch proxy list.")
    return []

def download_video_data(url):
    print(f"⬇️ Processing: {url}")
    
    for f in glob.glob("temp_video*"):
        try: os.remove(f)
        except: pass

    # Get Proxies
    proxy_list = get_free_proxies()
    # Add 'None' at the end to try Direct connection as last resort
    proxy_list.append(None) 
    
    dl_filename = None
    title = "Instagram Reel"
    final_hindi_text = ""
    hashtags = ""

    # Loop to try proxies until one works
    for proxy in proxy_list:
        if proxy:
            print(f"🔄 Trying to mask IP with Proxy: {proxy}")
        else:
            print("⚠️ All proxies failed. Trying Direct Connection (Last Hope)...")

        # Fake Browser Headers (Human Emulation)
        user_agent = random.choice(USER_AGENTS)
        
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'temp_video.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            
            # --- HUMAN LOGIC START ---
            'user_agent': user_agent,
            'referer': 'https://www.instagram.com/',
            'http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
            },
            # Artificial Delay (Insaan turant click nahi karta)
            'sleep_interval': random.randint(2, 5), 
            # --- HUMAN LOGIC END ---
        }
        
        # Proxy Add karna
        if proxy:
            ydl_opts['proxy'] = f"http://{proxy}"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if info:
                    # Success!
                    print("✅ Download Successful!")
                    title = info.get('title', '')
                    desc = info.get('description', '')
                    hashtags = generate_hashtags(info.get('tags', []))
                    
                    found_files = glob.glob("temp_video*")
                    video_files = [f for f in found_files if not f.endswith('.vtt')]
                    if video_files:
                        dl_filename = video_files[0]
                        
                        # Caption Logic
                        clean_title = re.sub(r'#\w+', '', title).strip()
                        final_hindi_text = translate_and_shorten(clean_title)
                        if not final_hindi_text and desc:
                            clean_desc = desc.split('\n')[0]
                            final_hindi_text = translate_and_shorten(clean_desc)
                        
                        if not final_hindi_text: final_hindi_text = "देखिए आज का वीडियो ✨"
                        
                        break # Loop tod do, kaam ho gaya
        except Exception as e:
            # print(f"❌ Failed with this IP: {e}")
            pass # Agla proxy try karo
            
    if not dl_filename:
        print("❌ Failed to download even after IP rotation.")
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
        for f in glob.glob("temp_video*.vtt"):
            try: os.remove(f)
            except: pass
        print("✅ Task Done.")
    else: sys.exit(1)
